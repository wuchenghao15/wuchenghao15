#!/usr/bin/env python3
"""ai_suggested_repair_engine.py
=================================================================================
AI建议驱动的扫描检测轮巡 + 智能修复 + 自动上传 引擎 (Suggested Repair Engine v1.0.0)
=================================================================================
由 daemon sys_ai_suggested_repair 每600s轮巡调用（once 模式），六步闭环：
  1. ABSORB  - 吸收AI建议: mt_patrol_eigenflux_suggestions(PENDING+REPAIR_FAILED失败重试)
               按updated_at FIFO轮转限量(失败的建议刷新updated_at后排到队尾,公平轮询)
  2. DECIDE   - 处置决策(纯函数 decide_action): 路径安全→Python文件→类型白名单→质量门槛
  3. RECHECK  - 现场复核: py_compile 已通过 → 建议过时 STALE_CLOSED（文件缺失同）
  4. FIX+VERIFY - 智能修复: 复用 AutoPatrolEngine 修复策略(缩进/括号)；修复前磁盘备份；
                py_compile 验证失败必须回滚（fail-safe：不弄得更坏）
  5. UPLOAD   - git自动上传: 本轮 fixed+verified 文件 → _runtime/git_push_ws/mtscos_push
                隔离仓 commit + push origin MTSCOS
  6. PERSIST  - 落库: 建议状态更新 + mt_suggested_repair_log 明细 + mt_ai_brain_feed_log 投喂

安全约束（硬）:
  - 修复范围仅 flask-app/**/*.py 确定性错误（syntax_error/indentation_error）
  - SKIP 高危路径: Database_Backups / recovery_snapshots / backups / git_push_ws / 备份目录等
  - 修复失败回滚后必须与原始字节一致
  - push 失败不阻塞落库（uploaded=0 记录，下轮不重试已 FIXED 建议）
"""
from __future__ import annotations
import hashlib
import json
import os
import py_compile
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
FLASK_APP_DIR = os.path.dirname(ENGINE_DIR)
PROJECT_ROOT = os.path.dirname(FLASK_APP_DIR)
APP_DB = os.path.join(PROJECT_ROOT, '_runtime', 'databases', 'Database', 'app.db')
ISOLATED_GIT = os.path.join(PROJECT_ROOT, '_runtime', 'git_push_ws', 'mtscos_push')
BACKUP_DIR = os.path.join(PROJECT_ROOT, '_runtime', 'suggested_repair_backups')
GIT_AUTHOR_NAME = 'Mr.W'
GIT_AUTHOR_EMAIL = 'wuchenghao15@users.noreply.github.com'
LOG = 'SUG-REPAIR'

# ─────────────────────── 决策常量（1:1 真源，AST 提取做千轮测试） ───────────────────────
_FIXABLE_TYPES = ('syntax_error', 'indentation_error')
_MIN_QUALITY = 0.0
_REPAIR_ROOT = 'flask-app'
_REPAIR_SKIP_DIRS = ('backups', '_migration_backups', '_migration_reports', 'Database_Backups',
                     'recovery_snapshots', '__pycache__', '.git', 'node_modules', 'venv',
                     '.venv', '_tmp', 'tmp', 'git_push_ws', 'suggested_repair_backups',
                     'Database', '_output')


def decide_action(finding_type, quality_score, path):
    """建议处置决策（纯函数，便于 §14 千轮测试）。
    入参 path 为项目相对路径（正斜杠）。
    返回 (action, reason)；action ∈ 'fix' | 'skip_nonfixable'。
    判定顺序（硬优先级）：
      1) 非 .py → skip
      2) 路径含 SKIP 目录段 → skip（防备份/数据库/隔离仓文件被改）
      3) 不在 flask-app 修复根内 → skip
      4) 类型不在白名单 → skip（仅确定性可修复类型）
      5) 质量分低于门槛 → skip
      6) → fix
    """
    p = (path or '').replace('\\', '/').strip()
    if not p.endswith('.py'):
        return ('skip_nonfixable', 'non-python')
    for seg in p.split('/'):
        if seg in _REPAIR_SKIP_DIRS:
            return ('skip_nonfixable', 'skip-path:' + seg)
    if not (p == _REPAIR_ROOT or p.startswith(_REPAIR_ROOT + '/')):
        return ('skip_nonfixable', 'outside-repair-root')
    if finding_type not in _FIXABLE_TYPES:
        return ('skip_nonfixable', 'non-fixable-type:' + str(finding_type))
    if quality_score is not None and float(quality_score) < _MIN_QUALITY:
        return ('skip_nonfixable', 'low-quality')
    return ('fix', 'deterministic-repair')


def upload_eligible(fixed, verified, path):
    """上传资格判定（纯函数）：仅 修复成功+验证通过 的 .py 可上传。"""
    p = (path or '').replace('\\', '/').strip()
    return bool(fixed) and bool(verified) and p.endswith('.py')


# ─────────────────────── 工具 ───────────────────────
def _now():
    return datetime.now().isoformat()


def _compiles(abs_path):
    try:
        py_compile.compile(abs_path, doraise=True)
        return True
    except Exception:
        return False


def _compile_error(abs_path):
    """现场编译，返回 (line, col0, error_type, msg) 或 None（编译通过）。
    col0 为0基列号（SyntaxError.offset-1），用于括号失配的 caret 定位。
    用 fresh 行号/类型修复（建议里的行号可能因文件变更漂移）。"""
    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            src = f.read()
    except Exception as e:
        return (0, 0, 'compile_error', f'read-fail:{e}'[:200])
    try:
        compile(src, abs_path, 'exec')
        return None
    except IndentationError as e:
        return (e.lineno or 0, (e.offset or 1) - 1,
                'indentation_error', f'{type(e).__name__}: {e.msg}'[:200])
    except SyntaxError as e:
        return (e.lineno or 0, (e.offset or 1) - 1,
                'syntax_error', f'{type(e).__name__}: {e.msg}'[:200])
    except Exception as e:
        return (0, 0, 'compile_error', str(e)[:200])


def _indent_of(line):
    return line[:len(line) - len(line.lstrip())]


def repair_step(abs_path, line, error_type, message, prev_err_key=None, col=None):
    """单步智能修复。返回 (step_ok, progressed, detail)。
    候选策略按序尝试（每个候选写入后立即编译验证）：
      - 编译通过            → 接受，(True, True)   完成
      - 错误键发生变化(行/类型) → 接受，(True, True)   有进展（复合损坏的中间态是正常的）
      - 错误键完全相同       → 弃用该候选，试下一个
    所有候选均无进展 → 恢复原文，(False, False)（fail-safe：不弄得更坏）。
    候选清单（硬优先级）：
      indentation_error: ①删除与相邻行完全重复的坏行 ②对齐前行 ③对齐后行 ④前行冒号+4
        （不提供 top-level/0 兜底 —— 防止把函数体级联降级到模块层造成运行时损坏）
      syntax_error(括号失配 'does not match opening parenthesis'): 删除 caret 指向的失配收尾括号
      其他 syntax_error: 委托 AutoPatrolEngine（其自带失败回滚）"""
    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            original = f.readlines()
    except Exception as e:
        return (False, False, f'read-fail:{e}'[:120])
    idx = int(line) - 1
    if idx < 0 or idx >= len(original):
        return (False, False, 'line-out-of-range')

    def _verify(modified):
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.writelines(modified)
        ce = _compile_error(abs_path)
        if ce is None:
            return ('compiled', '')
        new_key = f'{ce[0]}:{ce[1]}'
        if prev_err_key is not None and new_key == prev_err_key:
            return (None, new_key)
        return ('progress', new_key)

    candidates = []
    if error_type == 'indentation_error':
        bad = original[idx]
        stripped = bad.strip()
        prev_indent = _indent_of(original[idx - 1]) if idx > 0 and original[idx - 1].strip() else None
        next_indent = _indent_of(original[idx + 1]) if idx < len(original) - 1 and original[idx + 1].strip() else None
        nxt = original[idx + 1].strip() if idx < len(original) - 1 else None
        prv = original[idx - 1].strip() if idx > 0 else None
        if not stripped or stripped.startswith('#'):
            candidates.append(('clear-blank-comment', original[:idx] + [(stripped + '\n') if stripped else '\n'] + original[idx + 1:]))
        else:
            if (nxt == stripped) or (prv == stripped):
                candidates.append(('del-dup-line', original[:idx] + original[idx + 1:]))
            if prev_indent is not None and prev_indent != _indent_of(bad):
                candidates.append(('align-prev', original[:idx] + [prev_indent + stripped + '\n'] + original[idx + 1:]))
            if next_indent is not None and next_indent != _indent_of(bad):
                candidates.append(('align-next', original[:idx] + [next_indent + stripped + '\n'] + original[idx + 1:]))
            if prev_indent is not None and original[idx - 1].strip().endswith(':'):
                cand4 = prev_indent + '    '
                if cand4 != _indent_of(bad):
                    candidates.append(('prev-colon+4', original[:idx] + [cand4 + stripped + '\n'] + original[idx + 1:]))
    elif error_type == 'syntax_error' and (
            'does not match opening parenthesis' in (message or '')
            or "'return' outside function" in (message or '')):
        try:
            ci = int(col) if col is not None else -1
        except Exception:
            ci = -1
        target = original[idx]
        if 'does not match opening parenthesis' in (message or ''):
            # 括号失配: caret 指向多余的收尾括号 → 删除该字符
            if 0 <= ci < len(target) and target[ci] in ')]}':
                candidates.append((f'del-bracket({target[ci]})',
                                   original[:idx] + [target[:ci] + target[ci + 1:]] + original[idx + 1:]))
        else:
            # 模块级 return(顶层无缩进): 任何情况下都是非法语法(该文件从未运行成功)，
            # 删除是唯一确定性修复——典型为 sys_gap_discovery_engine 注入的尾部 `return bp`
            if not _indent_of(target).strip() and target.strip().startswith('return'):
                candidates.append(('del-return-module-level', original[:idx] + original[idx + 1:]))
    else:
        return (False, False, 'delegate-syntax-to-patrol')

    last_detail = ''
    for name, modified in candidates:
        try:
            verdict, new_key = _verify(modified)
        except Exception as e:
            last_detail = f'{name}-verify-fail:{e}'[:120]
            continue
        if verdict == 'compiled':
            return (True, True, name)
        if verdict == 'progress':
            return (True, True, f'{name}->next:{new_key}')
        last_detail = f'{name}:no-progress'
    with open(abs_path, 'w', encoding='utf-8') as f:
        f.writelines(original)
    return (False, False, last_detail or 'no-candidate')


def _to_relpath(finding_file):
    """绝对/相对路径 → 项目相对路径（正斜杠）；项目外返回 None。"""
    if not finding_file:
        return None
    f = finding_file.strip()
    if not os.path.isabs(f):
        cand = os.path.normpath(os.path.join(PROJECT_ROOT, f))
    else:
        cand = os.path.normpath(f)
    try:
        rel = os.path.relpath(cand, PROJECT_ROOT)
    except ValueError:
        return None
    if rel.startswith('..'):
        return None
    return rel.replace(os.sep, '/')


def _backup(abs_path, round_dir):
    rel = os.path.relpath(abs_path, PROJECT_ROOT)
    dst = os.path.join(round_dir, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(abs_path, dst)
    return dst


def _rollback(abs_path, backup_path):
    if backup_path and os.path.isfile(backup_path):
        shutil.copy2(backup_path, abs_path)


def _ensure_tables(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS mt_suggested_repair_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        round_no TEXT NOT NULL, suggestion_uid TEXT, finding_type TEXT,
        file_path TEXT, line INTEGER, action TEXT, reason TEXT,
        fixed INTEGER DEFAULT 0, verified INTEGER DEFAULT 0, uploaded INTEGER DEFAULT 0,
        upload_commit TEXT, error_message TEXT, created_at TEXT NOT NULL)''')
    conn.commit()


def _log_row(conn, rn, uid, ftype, rel, line, action, reason, fixed, verified,
             uploaded, commit, errmsg):
    conn.execute('''INSERT INTO mt_suggested_repair_log
        (round_no, suggestion_uid, finding_type, file_path, line, action, reason,
         fixed, verified, uploaded, upload_commit, error_message, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (rn, uid, ftype, rel, line, action, reason, int(fixed), int(verified),
         int(uploaded), commit, errmsg, _now()))


def _set_suggestion(conn, uid, status):
    conn.execute('UPDATE mt_patrol_eigenflux_suggestions SET status=?, adopted_at=?, updated_at=? '
                 'WHERE suggestion_uid=?', (status, _now(), _now(), uid))


# ─────────────────────── git 自动上传 ───────────────────────
def _run(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or '') + (r.stderr or '')
    except Exception as e:
        return -1, str(e)


def _git_upload(rel_files, round_no):
    """把本轮修复文件上传到隔离仓 MTSCOS 分支，返回 commit hash 或 None。"""
    try:
        os.makedirs(ISOLATED_GIT, exist_ok=True)
        if not os.path.isdir(os.path.join(ISOLATED_GIT, '.git')):
            _run(f'git init -q "{ISOLATED_GIT}"')
            _run(f'git -C "{ISOLATED_GIT}" config user.name "{GIT_AUTHOR_NAME}"')
            _run(f'git -C "{ISOLATED_GIT}" config user.email "{GIT_AUTHOR_EMAIL}"')
            _run(f'git -C "{ISOLATED_GIT}" branch -M MTSCOS')
            _run(f'git -C "{ISOLATED_GIT}" commit --allow-empty -q -m "init [{LOG}]"')
        for rel in rel_files:
            src = os.path.join(PROJECT_ROOT, rel)
            dst = os.path.join(ISOLATED_GIT, rel)
            if not os.path.isfile(src):
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            _run(f'git -C "{ISOLATED_GIT}" add -- "{dst}"', 60)
        msg = f'[{LOG} {round_no}] AI建议自动修复 {len(rel_files)} 文件(verify通过)'
        # commit 用 -c 内联身份（隔离仓可能由其他流程创建、无持久 user 配置）
        rc_c, out_c = _run(f'git -C "{ISOLATED_GIT}" -c user.name="{GIT_AUTHOR_NAME}" '
                           f'-c user.email="{GIT_AUTHOR_EMAIL}" commit -m "{msg}"', 60)
        if rc_c != 0 and 'nothing to commit' not in out_c:
            print(f'[{LOG}] commit failed: {out_c[:200]}', file=sys.stderr)
            return None
        rc_p, out_p = _run(f'git -C "{ISOLATED_GIT}" push origin MTSCOS', 120)
        up_to_date = 'up-to-date' in out_p.lower()
        if rc_p != 0 and not up_to_date:
            print(f'[{LOG}] push failed: {out_p[:200]}', file=sys.stderr)
            return None
        rc2, h = _run(f'git -C "{ISOLATED_GIT}" rev-parse HEAD', 30)
        return h.strip() if rc2 == 0 and h.strip() else None
    except Exception:
        return None


# ─────────────────────── 主流程 ───────────────────────
def run_once(round_no=None, absorb_limit=100):
    rn = round_no or datetime.now().strftime('%Y%m%d_%H%M%S')
    round_dir = os.path.join(BACKUP_DIR, rn)
    stats = {'absorbed': 0, 'fixed': 0, 'failed': 0, 'stale': 0, 'skipped': 0,
             'uploaded': 0, 'push': 'SKIP', 'round_no': rn}
    sys.path.insert(0, ENGINE_DIR)
    from auto_patrol_engine import AutoPatrolEngine, ErrorItem
    patrol = AutoPatrolEngine(scan_dir=FLASK_APP_DIR)

    conn = sqlite3.connect(APP_DB, timeout=90, isolation_level=None)
    for p in ('PRAGMA journal_mode=WAL', 'PRAGMA busy_timeout=60000'):
        conn.execute(p)
    _ensure_tables(conn)

    # 两阶段吸收（按文件去重FIFO）: 建议池存在大量同文件重复建议(9000+行/30文件)，
    # 行级FIFO会被单文件副本堵死。GROUP BY finding_file 每文件取最老一条，一轮覆盖全部文件。
    # 70%预算给可修类型(修复吞吐), 30%给不可修类型(池清理关闭)。
    _fix_phase = max(1, absorb_limit * 7 // 10)
    rows = conn.execute('''SELECT suggestion_uid, finding_type, finding_file, finding_line,
        finding_message, quality_score, MIN(updated_at) AS mu
        FROM mt_patrol_eigenflux_suggestions
        WHERE status IN ('PENDING','REPAIR_FAILED')
          AND finding_type IN ('syntax_error','indentation_error')
        GROUP BY finding_file ORDER BY mu ASC LIMIT ?''',
        (_fix_phase,)).fetchall()
    rows = [r[:6] for r in rows]
    _seen = {r[0] for r in rows}
    if absorb_limit > len(rows):
        for r in conn.execute('''SELECT suggestion_uid, finding_type, finding_file, finding_line,
            finding_message, quality_score, MIN(updated_at) AS mu
            FROM mt_patrol_eigenflux_suggestions
            WHERE status IN ('PENDING','REPAIR_FAILED')
            GROUP BY finding_file ORDER BY mu ASC LIMIT ?''',
            (absorb_limit - len(rows),)).fetchall():
            if r[0] not in _seen:
                rows = rows + [r[:6]]
                _seen.add(r[0])
    stats['absorbed'] = len(rows)
    fixed_files = []

    # ── DECIDE: 按文件聚合 fix 类建议（一个文件的多条错误由修复循环统一处理）──
    skip_rows = []           # (uid, ftype, rel, fline, action, reason)
    file_suggestions = {}    # abs_path -> [(uid, ftype, rel, fline, fmsg, q)]
    for (uid, ftype, ffile, fline, fmsg, q) in rows:
        rel = _to_relpath(ffile)
        action, reason = decide_action(ftype, q, rel or '')
        if action != 'fix':
            skip_rows.append((uid, ftype, rel, fline, action, reason))
            continue
        abs_path = os.path.join(PROJECT_ROOT, rel)
        file_suggestions.setdefault(abs_path, []).append((uid, ftype, rel, fline, fmsg, q))
    for (uid, ftype, rel, fline, action, reason) in skip_rows:
        _set_suggestion(conn, uid, 'SKIP_NONFIXABLE')
        _log_row(conn, rn, uid, ftype, rel, fline, action, reason, 0, 0, 0, None, None)
        stats['skipped'] += 1

    # ── RECHECK + FIX loop（文件级） ──
    MAX_ATTEMPTS = 24   # 单文件修复循环上限（连环缩进错误需逐个消化）
    for abs_path, sug_list in file_suggestions.items():
        rel = sug_list[0][2]
        if not os.path.isfile(abs_path):
            for (uid, ftype, _, fline, _, _) in sug_list:
                _set_suggestion(conn, uid, 'STALE_CLOSED')
                _log_row(conn, rn, uid, ftype, rel, fline, 'stale_close', 'file-missing', 0, 0, 0, None, None)
                stats['stale'] += 1
            continue
        if _compiles(abs_path):
            for (uid, ftype, _, fline, _, _) in sug_list:
                _set_suggestion(conn, uid, 'STALE_CLOSED')
                _log_row(conn, rn, uid, ftype, rel, fline, 'stale_close', 'already-compiles', 0, 0, 0, None, None)
                stats['stale'] += 1
            continue
        # 备份（文件级，一次）
        backup_path = None
        try:
            backup_path = _backup(abs_path, round_dir)
        except Exception:
            pass
        # 修复循环：修一个错误 → 重编译 → 新错误行 → 继续
        # 进展语义：编译通过=完成；错误变化=保留修改继续；错误相同=回滚单步并停止（防震荡）
        compiled = False
        last_errmsg = ''
        for attempt in range(MAX_ATTEMPTS):
            ce = _compile_error(abs_path)
            if ce is None:
                compiled = True
                break
            real_line, real_col, real_type, real_msg = ce
            prev_err_key = f'{real_line}:{real_type}'
            if real_type not in _FIXABLE_TYPES or real_line <= 0:
                last_errmsg = f'non-repairable:{real_type}:{real_msg[:80]}'
                break
            _handled_syntax = ('does not match opening parenthesis' in real_msg
                               or "'return' outside function" in real_msg)
            if real_type == 'syntax_error' and not _handled_syntax:
                # 括号补齐/tab转换等 → 委托巡逻引擎（其验证失败自带回滚）
                rel_fa = rel[len('flask-app/'):] if rel.startswith('flask-app/') else rel
                err = ErrorItem(error_id=hashlib.md5(f'{rel}_{real_line}_{attempt}'.encode()).hexdigest()[:12],
                                file=rel_fa, line=int(real_line), error_type=real_type,
                                message=real_msg, discovered_at=_now())
                try:
                    step_ok = bool(patrol._fix_error(err))
                    step_detail = err.fix_detail or ''
                except Exception as e:
                    step_ok = False
                    step_detail = f'{type(e).__name__}: {e}'[:200]
            else:
                step_ok, _progressed, step_detail = repair_step(
                    abs_path, real_line, real_type, real_msg, prev_err_key=prev_err_key, col=real_col)
            if not step_ok:
                last_errmsg = step_detail or 'strategy-cannot-fix'
                break
        # 验证 + 回滚（fail-safe：不弄得更坏）
        compiled = _compiles(abs_path)
        if compiled:
            for (uid, ftype, _, fline, _, _) in sug_list:
                _set_suggestion(conn, uid, 'FIXED')
                _log_row(conn, rn, uid, ftype, rel, fline, 'fix', 'deterministic-repair', 1, 1, 0, None,
                         f'repair-loop:compiled[{len(sug_list)} sug]')
            fixed_files.append(rel)
            stats['fixed'] += len(sug_list)
        else:
            _rollback(abs_path, backup_path)
            for (uid, ftype, _, fline, _, _) in sug_list:
                _set_suggestion(conn, uid, 'REPAIR_FAILED')
                _log_row(conn, rn, uid, ftype, rel, fline, 'fix', 'deterministic-repair', 0, 0, 0, None,
                         (last_errmsg or 'repair-loop-failed')[:280])
            stats['failed'] += len(sug_list)

    # ── UPLOAD ──
    if fixed_files:
        commit = _git_upload(fixed_files, rn)
        if commit:
            stats['uploaded'] = len(fixed_files)
            stats['push'] = commit[:12]
            conn.execute('UPDATE mt_suggested_repair_log SET uploaded=1, upload_commit=? '
                         'WHERE round_no=? AND fixed=1 AND verified=1 AND uploaded=0', (commit, rn))
        else:
            stats['push'] = 'FAIL'
    conn.commit()
    try:
        conn.execute('INSERT INTO mt_ai_brain_feed_log(flow_id, feed_kind, feed_content, triggered_at) '
                     'VALUES (?,?,?,?)',
                     (f'{LOG}-{rn}', 'suggested_repair',
                      json.dumps(stats, ensure_ascii=False), _now()))
    except Exception:
        pass
    conn.commit()
    conn.close()
    return stats


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'once'
    if cmd == 'once':
        s = run_once()
        print(f'[{LOG}] {json.dumps(s, ensure_ascii=False)}')
        return 0
    if cmd == 'stats':
        conn = sqlite3.connect(APP_DB, timeout=30)
        rows = conn.execute('''SELECT action, COUNT(*) FROM mt_suggested_repair_log
            GROUP BY action''').fetchall()
        pend = conn.execute("SELECT COUNT(*) FROM mt_patrol_eigenflux_suggestions "
                            "WHERE status='PENDING'").fetchone()[0]
        conn.close()
        print(json.dumps({'by_action': dict(rows), 'pending': pend}, ensure_ascii=False))
        return 0
    print(f'usage: {os.path.basename(__file__)} [once|stats]')
    return 1


if __name__ == '__main__':
    sys.exit(main())
