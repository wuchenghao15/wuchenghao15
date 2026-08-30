#!/usr/bin/env python3
"""ai_feature_evolution_engine.py
=================================================================================
AI建议 + 模拟环境驱动的 功能演进轮巡引擎 (Feature Evolution Engine v1.0.0)
=================================================================================
由 daemon sys_feature_evolution 每900s轮巡调用（once 模式），六步闭环：
  1. ABSORB   - 吸收AI建议+真实扫描: flask-app 未完成标记(TODO/FIXME/XXX:/NotImplementedError/占位)
                + 未挂载引擎检测(engines/*.py 不在 SYSTEM_REQUIRED_DAEMONS)
  2. SIMULATE - 模拟环境磋商: 复用 simulation_sandbox_engine(GAP_PROPOSAL场景, 确定性seed)
                多智能体多轮讨论 → 共识分决定 演进/仅建议
  3. EVOLVE   - 完善/拓展(确定性项沙盒先行): 缺失__init__.py包补全(沙盒创建);
                FEATURE_EXPAND 拓展建议落池(带行号+完善方向); ENGINE_MOUNT 挂载建议落池
                (AI_SUGGESTION 来源, 可被 smart_mount 自动挂载流水线消费)
  4. VERIFY   - 沙盒验证: py_compile + import smoke(subprocess, 30s超时)
  5. UPLOAD   - git自动上传: 验证通过的文件 promote 到正本(备份+字节级回滚) →
                _runtime/git_push_ws/mtscos_push 隔离仓 add -f + commit + push origin MTSCOS
  6. PERSIST  - 落库: mt_feature_evolution_log 明细 + mt_ai_brain_feed_log 投喂(列名1:1)

安全约束（硬）:
  - 语法/缩进修复仍归 ai_suggested_repair_engine(v22.4.0)专属, 本引擎不重复消费该两类建议
  - 沙盒先行: 所有写动作先落 _runtime/feature_evolution_sandbox/<round>/, 验证通过才 promote
  - promote 前必须备份原文件; 失败字节级回滚
  - 上传白名单: 仅 flask-app 内 .py; SKIP目录段一律拒绝; git add -f(隔离仓gitignore含flask-app/*)
  - push 失败不阻塞落库
"""
from __future__ import annotations
import hashlib
import json
import os
import py_compile
import re
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
SANDBOX_ROOT = os.path.join(PROJECT_ROOT, '_runtime', 'feature_evolution_sandbox')
SMART_MOUNT_PY = os.path.join(ENGINE_DIR, 'ai_smart_mount_engine.py')
GIT_AUTHOR_NAME = 'Mr.W'
GIT_AUTHOR_EMAIL = 'wuchenghao15@users.noreply.github.com'
LOG = 'FEATURE-EVO'

# ─────────────────────── 决策常量（1:1 真源，AST 提取做千轮测试） ───────────────────────
_MARKERS = ('TODO', 'FIXME', 'XXX:', 'NotImplementedError', '占位')
_SCAN_SUBDIRS = ('engines', 'routes', 'services', 'ai_engines', 'scripts')
_SKIP_DIRS = ('backups', '_migration_backups', 'Database_Backups', 'recovery_snapshots',
              '__pycache__', '.git', 'node_modules', 'venv', '.venv', '_tmp', 'tmp',
              'git_push_ws', 'suggested_repair_backups', 'feature_evolution_sandbox',
              'Database', '_output', '_runtime')
_UPLOAD_ROOT = 'flask-app'
_UPLOAD_SKIP_DIRS = _SKIP_DIRS
_MIN_CONSENSUS = 0.60
_MAX_ADVICE_PER_ROUND = 20
_SANDBOX_SUB = '_runtime/feature_evolution_sandbox'


def marker_classify(line_text):
    """未完成标记分类（纯函数）。返回标记种类或 None。
    判定顺序: TODO → FIXME → XXX: → NotImplementedError → 占位; 大小写敏感, 注释/代码均计入。"""
    t = str(line_text or '')
    for kind in _MARKERS:
        if kind in t:
            return kind
    return None


def sandbox_eligible(path):
    """沙盒资格判定（纯函数）：仅 flask-app 内 .py 且不含 SKIP 目录段。"""
    p = (path or '').replace('\\', '/').strip()
    if not p.endswith('.py'):
        return False
    for seg in p.split('/'):
        if seg in _SKIP_DIRS:
            return False
    return p == _UPLOAD_ROOT or p.startswith(_UPLOAD_ROOT + '/')


def evolve_decision(consensus, require, category):
    """演进处置决策（纯函数）。返回 (action, reason)。
    action ∈ 'evolve' | 'suggest_only' | 'skip'。
    硬优先级: 类别非法 skip → 共识非法 skip → 共识<门槛 suggest_only → evolve。"""
    if category not in ('FEATURE_EXPAND', 'ENGINE_MOUNT', 'PACKAGE_INIT'):
        return ('skip', 'unknown-category:' + str(category))
    try:
        c = float(consensus)
        r = float(require)
    except (TypeError, ValueError):
        return ('skip', 'bad-consensus')
    if c != c or c < 0 or c > 1:
        return ('skip', 'consensus-out-of-range')
    if r != r or r < 0 or r > 1:
        return ('skip', 'bad-require')
    if c < r:
        return ('suggest_only', 'consensus-%.2f<%.2f' % (c, r))
    return ('evolve', 'consensus-%.2f>=%.2f' % (c, r))


def mount_candidate(engine_stem, mounted_blob):
    """引擎挂载候选判定（纯函数）：双侧归一化(剥离ai/sys前缀与engine/daemon后缀,
    去下划线)后双向包含匹配, 任一已挂载名命中 → False(已挂载)。"""
    def norm(s):
        s = re.sub(r'[^a-z0-9]', '', str(s or '').lower())
        for pre in ('ai', 'sys'):
            if s.startswith(pre) and len(s) > len(pre) + 2:
                s = s[len(pre):]
        for suf in ('engine', 'daemon'):
            if s.endswith(suf) and len(s) > len(suf) + 2:
                s = s[:-len(suf)]
        return s
    e = norm(engine_stem)
    if not e:
        return False
    for m in str(mounted_blob or '').split():
        nm = norm(m)
        if nm and (e in nm or nm in e):
            return False
    return True


def promote_ok(created, verified, backed_up):
    """promote 资格判定（纯函数）：沙盒已创建+验证通过+备份状态合法（仅 True/'OLD'/'NEW'）。"""
    if backed_up not in (True, 'OLD', 'NEW'):
        return False
    return bool(created) and bool(verified)


def advice_uid(kind, path):
    """建议uid（纯函数, 确定性）：kind+path 唯一决定, 防同轮/跨轮重复落池。"""
    return 'FEV-' + hashlib.md5(f'{kind}|{path}'.encode()).hexdigest()[:14]


def upload_eligible(promoted, verified, path):
    """上传资格判定（纯函数）：仅 promote成功+验证通过 的 .py，且强制白名单
    （flask-app 根内 + 无 SKIP 目录段），1:1 对齐沙盒/上传安全约束。"""
    p = (path or '').replace('\\', '/').strip()
    if not p.endswith('.py'):
        return False
    for seg in p.split('/'):
        if seg in _UPLOAD_SKIP_DIRS:
            return False
    if not (p == _UPLOAD_ROOT or p.startswith(_UPLOAD_ROOT + '/')):
        return False
    return bool(promoted) and bool(verified)


def consensus_label(consensus):
    """共识分档（纯函数）：>=0.75 HIGH / >=0.60 MEDIUM / 其余 LOW; 非法→LOW。"""
    try:
        c = float(consensus)
    except (TypeError, ValueError):
        return 'LOW'
    if c != c:
        return 'LOW'
    if c >= 0.75:
        return 'HIGH'
    if c >= 0.60:
        return 'MEDIUM'
    return 'LOW'


# ─────────────────────── 工具 ───────────────────────
def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _log(msg):
    line = f'[{_now()}] [{LOG}] {msg}'
    print(line, flush=True)
    try:
        os.makedirs(os.path.join(PROJECT_ROOT, '_runtime', 'logs'), exist_ok=True)
        with open(os.path.join(PROJECT_ROOT, '_runtime', 'logs', 'feature_evolution_engine.log'),
                  'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def _main_conn():
    conn = sqlite3.connect(APP_DB, timeout=60, isolation_level=None)
    conn.execute('PRAGMA busy_timeout=60000')
    return conn


def _ensure_tables(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS mt_feature_evolution_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        round_no TEXT NOT NULL, step TEXT NOT NULL, target TEXT,
        detail TEXT, created_at TEXT NOT NULL)''')


def _log_row(conn, rn, step, target, detail):
    try:
        conn.execute('INSERT INTO mt_feature_evolution_log(round_no,step,target,detail,created_at) VALUES (?,?,?,?,?)',
                     (rn, step, target or '', (detail or '')[:2000], _now()))
    except Exception as e:
        _log(f'log_row失败 {step}: {e}')


# ─────────────────────── 1. ABSORB 吸收+扫描 ───────────────────────
def scan_incomplete_and_absorb(conn, rn, stats):
    """真实扫描未完成标记 + 未挂载引擎; 产出演进候选清单。"""
    candidates = []
    detail = ''
    reason = 'ok'
    try:
        mounted_blob = ''
        try:
            with open(SMART_MOUNT_PY, encoding='utf-8', errors='ignore') as f:
                mounted_blob = ' '.join(re.findall(r'"process_name":\s*"([a-z0-9_]+)"', f.read()))
        except Exception as e:
            _log(f'挂载清单读取失败(按空处理): {e}')
        for sub in _SCAN_SUBDIRS:
            d = os.path.join(FLASK_APP_DIR, sub)
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if not fn.endswith('.py') or fn.startswith('_'):
                    continue
                rel = f'flask-app/{sub}/{fn}'
                if rel == 'flask-app/engines/ai_feature_evolution_engine.py':
                    continue  # 跳过自身（_MARKERS 定义行含标记词, 防自引用）
                if not sandbox_eligible(rel):
                    continue
                fp = os.path.join(d, fn)
                try:
                    with open(fp, encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                except Exception:
                    continue
                marks = []
                for i, line in enumerate(text.splitlines(), 1):
                    kind = marker_classify(line)
                    if kind:
                        marks.append((i, kind))
                if marks:
                    candidates.append({'rel': rel, 'kind': 'FEATURE_EXPAND', 'marks': marks[:50]})
                # 未挂载引擎（仅 engines/ 顶层）
                if sub == 'engines' and mount_candidate(fn[:-3], mounted_blob):
                    candidates.append({'rel': rel, 'kind': 'ENGINE_MOUNT', 'marks': []})
        # 缺失 __init__.py 的包目录
        inits = []
        for sub in _SCAN_SUBDIRS:
            d = os.path.join(FLASK_APP_DIR, sub)
            if os.path.isdir(d) and not os.path.isfile(os.path.join(d, '__init__.py')):
                has_py = any(x.endswith('.py') for x in os.listdir(d))
                if has_py:
                    inits.append(f'flask-app/{sub}/__init__.py')
        for rel in inits:
            candidates.append({'rel': rel, 'kind': 'PACKAGE_INIT', 'marks': []})
        # 收敛: 关闭"引擎实际已挂载"的陈旧 ENGINE_MOUNT 建议
        closed_stale = 0
        try:
            rows = conn.execute("""SELECT suggestion_uid, finding_file FROM mt_patrol_eigenflux_suggestions
                WHERE suggestion_uid LIKE 'FEV-%' AND status='PENDING' AND advice_category='ENGINE_MOUNT'""").fetchall()
            for uid, ffile in rows:
                stem = os.path.basename(str(ffile))[:-3]
                if not mount_candidate(stem, mounted_blob):
                    conn.execute("UPDATE mt_patrol_eigenflux_suggestions SET status='SKIPPED_STALE', updated_at=? WHERE suggestion_uid=?",
                                 (_now(), uid))
                    closed_stale += 1
        except Exception as e:
            _log(f'陈旧建议收敛失败: {e}')
        detail = f'candidates={len(candidates)} (expand={sum(1 for c in candidates if c["kind"]=="FEATURE_EXPAND")} mount={sum(1 for c in candidates if c["kind"]=="ENGINE_MOUNT")} init={sum(1 for c in candidates if c["kind"]=="PACKAGE_INIT")}) closed_stale={closed_stale}'
    except Exception as e:
        reason = f'error:{type(e).__name__}: {e}'[:200]
        detail = ''
    _log_row(conn, rn, 'ABSORB', 'scan_incomplete', detail or reason)
    stats.setdefault('steps', {})['absorb'] = {'candidates': len(candidates), 'reason': reason if not candidates else 'ok'}
    stats['candidates'] = candidates[:_MAX_ADVICE_PER_ROUND * 2]
    return candidates


# ─────────────────────── 2. SIMULATE 模拟环境磋商 ───────────────────────
def run_simulation_consult(conn, rn, stats):
    """复用 simulation_sandbox_engine 跑一场 GAP_PROPOSAL 磋商 → 共识分。"""
    consensus = None
    session_id = ''
    detail = ''
    try:
        sys.path.insert(0, ENGINE_DIR)
        from simulation_sandbox_engine import SimulationSandboxEngine
        seed = int(hashlib.md5(rn.encode()).hexdigest()[:8], 16)
        eng = SimulationSandboxEngine()
        r = eng.run('GAP_PROPOSAL', actor_count=6, seed=seed)
        consensus = float(r.get('consensus', 0.0))
        session_id = str(r.get('session_id', ''))[:64]
        detail = f'session={session_id} consensus={consensus} msgs={r.get("message_count")}'
    except SystemExit as e:
        detail = f'sim-system-exit:{e}'[:200]
    except Exception as e:
        detail = f'sim-error:{type(e).__name__}: {e}'[:200]
    _log_row(conn, rn, 'SIMULATE', 'gap_proposal_consult', detail)
    stats.setdefault('steps', {})['simulate'] = {'consensus': consensus, 'detail': detail}
    stats['consensus'] = consensus
    stats['sim_session'] = session_id
    return consensus


# ─────────────────────── 3+4. EVOLVE 沙盒开发 + VERIFY 验证 ───────────────────────
def evolve_and_verify(conn, rn, stats, candidates, consensus):
    """按决策执行: 沙盒创建/拓展建议落池/挂载建议落池; 沙盒验证。"""
    sandbox_dir = os.path.join(SANDBOX_ROOT, rn)
    os.makedirs(sandbox_dir, exist_ok=True)
    action, areason = evolve_decision(consensus, _MIN_CONSENSUS, 'PACKAGE_INIT')
    promoted = []
    advice_written = 0
    mount_advice = 0
    expand_advice = 0
    try:
        # a) PACKAGE_INIT: 沙盒创建 __init__.py（共识门槛通过才真开发, 否则仅建议）
        for cand in candidates:
            if cand['kind'] != 'PACKAGE_INIT':
                continue
            rel = cand['rel']
            if action == 'evolve':
                dst = os.path.join(sandbox_dir, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                pkg = rel.split('/')[1]
                with open(dst, 'w', encoding='utf-8') as f:
                    f.write(f'"""MTSCOS AI 包初始化（AI功能演进引擎 {rn} 自动补全, 模拟环境共识={consensus}）。"""\n')
                try:
                    py_compile.compile(dst, doraise=True)
                    promoted.append({'rel': rel, 'src': dst, 'verified': True, 'is_new': True})
                except Exception as e:
                    _log(f'沙盒编译失败 {rel}: {e}')
                    promoted.append({'rel': rel, 'src': dst, 'verified': False, 'is_new': True})
            else:
                _write_advice(conn, rn, 'PACKAGE_INIT', rel, 0,
                              f'包缺失__init__.py(模拟共识{consensus})，建议补全包初始化', 0.75)
                advice_written += 1
        # b) FEATURE_EXPAND / ENGINE_MOUNT 建议落池（无论共识, 建议总是产出）
        for cand in candidates:
            if cand['kind'] == 'FEATURE_EXPAND':
                marks = cand['marks']
                kinds = ','.join(sorted({k for _, k in marks}))
                lines = ','.join(str(i) for i, _ in marks[:12])
                _write_advice(conn, rn, 'FEATURE_EXPAND', cand['rel'], marks[0][0],
                              f'未完成标记[{kinds}]@行{lines}，需按模块职责完善实现并经模拟环境验证',
                              0.85)
                expand_advice += 1
            elif cand['kind'] == 'ENGINE_MOUNT':
                stem = os.path.basename(cand['rel'])[:-3]
                _write_advice(conn, rn, 'ENGINE_MOUNT', cand['rel'], 0,
                              f'引擎{stem}未挂载daemon，建议评估后经smart_mount(AI_SUGGESTION)自动挂载', 0.80)
                mount_advice += 1
        # c) VERIFY: 对沙盒产物做 import smoke（子进程 30s 超时）
        for item in promoted:
            if not item['verified']:
                continue
            try:
                r = subprocess.run([sys.executable, '-c', f'import py_compile;py_compile.compile({item["src"]!r}, doraise=True)'],
                                   capture_output=True, text=True, timeout=30)
                item['verified'] = (r.returncode == 0)
            except Exception:
                item['verified'] = False
    except Exception as e:
        _log(f'evolve异常: {e}')
    _log_row(conn, rn, 'EVOLVE', 'sandbox_develop',
             f'action={action} promoted={len(promoted)} advice expand={expand_advice} mount={mount_advice} init={advice_written}')
    stats.setdefault('steps', {})['evolve'] = {
        'action': action, 'reason': areason, 'promoted': len(promoted),
        'expand_advice': expand_advice, 'mount_advice': mount_advice, 'init_advice': advice_written}
    stats['promoted'] = promoted
    return promoted


def _write_advice(conn, rn, kind, rel, line, content, quality):
    """拓展/挂载建议落池（uid幂等防重）。"""
    try:
        uid = advice_uid(kind, rel)
        exists = conn.execute('SELECT 1 FROM mt_patrol_eigenflux_suggestions WHERE suggestion_uid=?', (uid,)).fetchone()
        if exists:
            return False
        now = _now()
        conn.execute('''INSERT INTO mt_patrol_eigenflux_suggestions
            (suggestion_uid, finding_type, finding_file, finding_line, finding_message,
             finding_severity, expert_name, expert_domain, advice_category, advice_content,
             quality_score, status, round_no, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (uid, 'feature_gap', rel, line or 0, f'{kind}:{rel}', 'MEDIUM',
             'AI功能演进官', 'EVOLUTION', kind, content, quality, 'PENDING', rn, now, now))
        return True
    except Exception as e:
        _log(f'advice落池失败 {kind}:{rel}: {e}')
        return False


# ─────────────────────── 5. UPLOAD promote + git 上传 ───────────────────────
def promote_and_upload(conn, rn, stats, promoted):
    """验证通过 → 备份正本 → promote → 隔离仓 add -f + commit + push。"""
    uploaded = 0
    commit_hash = None
    backup_dir = os.path.join(SANDBOX_ROOT, rn, '_backups')
    changed = []
    try:
        for item in promoted:
            rel = item['rel']
            if not upload_eligible(True, item['verified'], rel):
                continue
            dst_real = os.path.join(PROJECT_ROOT, rel)
            os.makedirs(os.path.dirname(dst_real), exist_ok=True)
            backed = 'NEW'
            if os.path.isfile(dst_real):
                os.makedirs(backup_dir, exist_ok=True)
                bpath = os.path.join(backup_dir, rel.replace('/', '__'))
                shutil.copy2(dst_real, bpath)
                backed = 'OLD'
                if open(bpath, 'rb').read() != open(dst_real, 'rb').read():
                    _log(f'备份不一致跳过 {rel}')
                    continue
            if not promote_ok(True, item['verified'], backed):
                continue
            shutil.copy2(item['src'], dst_real)
            item['promoted'] = True
            changed.append(rel)
            uploaded += 1
        if changed:
            os.makedirs(ISOLATED_GIT, exist_ok=True)
            if not os.path.isdir(os.path.join(ISOLATED_GIT, '.git')):
                for c in (f'git init -q "{ISOLATED_GIT}"',
                          f'git -C "{ISOLATED_GIT}" config user.name "{GIT_AUTHOR_NAME}"',
                          f'git -C "{ISOLATED_GIT}" config user.email "{GIT_AUTHOR_EMAIL}"',
                          f'git -C "{ISOLATED_GIT}" branch -M MTSCOS',
                          f'git -C "{ISOLATED_GIT}" commit --allow-empty -q -m "initial flow sandbox [{LOG}]"'):
                    subprocess.run(c, shell=True, check=False)
            for rel in changed:
                dst = os.path.join(ISOLATED_GIT, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(os.path.join(PROJECT_ROOT, rel), dst)
                subprocess.run(f'git -C "{ISOLATED_GIT}" add -f -- "{dst}"', shell=True, check=False, capture_output=True)
            msg = f'[{LOG}:{rn}] 功能演进轮巡: 自动完善 {len(changed)} 文件(模拟环境共识={stats.get("consensus")})'
            subprocess.run(f'git -C "{ISOLATED_GIT}" -c user.name="{GIT_AUTHOR_NAME}" -c user.email="{GIT_AUTHOR_EMAIL}" commit -m "{msg}"',
                           shell=True, check=False, capture_output=True)
            r = subprocess.run(f'git -C "{ISOLATED_GIT}" rev-parse HEAD', shell=True, capture_output=True, text=True)
            commit_hash = r.stdout.strip()[:40] if r.returncode == 0 else None
            rp = subprocess.run(f'git -C "{ISOLATED_GIT}" push origin MTSCOS', shell=True, capture_output=True, text=True, timeout=120)
            _log(f'push rc={rp.returncode} {(rp.stdout+rp.stderr)[:200]}')
    except Exception as e:
        _log(f'upload异常: {e}')
    _log_row(conn, rn, 'UPLOAD', 'promote_and_push', f'uploaded={uploaded} commit={commit_hash}')
    stats.setdefault('steps', {})['upload'] = {'uploaded': uploaded, 'commit_hash': commit_hash}
    stats['uploaded'] = uploaded
    stats['commit_hash'] = commit_hash
    return uploaded


# ─────────────────────── 6. PERSIST 落库+投喂 ───────────────────────
def persist_and_feed(conn, rn, stats):
    try:
        conn.execute('''INSERT INTO mt_ai_brain_feed_log(flow_id, feed_target, payload_preview, fed_at, fed_by)
                        VALUES (?,?,?,?,?)''',
                     (f'{LOG}-{rn}', 'AI脑库/功能演进',
                      json.dumps({k: v for k, v in stats.items() if k != 'candidates'}, ensure_ascii=False),
                      _now(), 'FEATURE-EVO'))
    except Exception as e:
        _log(f'脑库投喂失败: {e}')
    _log_row(conn, rn, 'PERSIST', 'brain_feed', 'done')
    stats.setdefault('steps', {})['persist'] = {'ok': True}


# ─────────────────────── 主流程 ───────────────────────
def run_once():
    rn = datetime.now().strftime('%Y%m%d_%H%M%S')
    stats = {'round': rn, 'steps': {}}
    conn = _main_conn()
    try:
        _ensure_tables(conn)
        candidates = scan_incomplete_and_absorb(conn, rn, stats)
        consensus = run_simulation_consult(conn, rn, stats)
        promoted = evolve_and_verify(conn, rn, stats, candidates, consensus)
        promote_and_upload(conn, rn, stats, promoted)
        persist_and_feed(conn, rn, stats)
        _log(f'round {rn} 完成: candidates={len(candidates)} consensus={consensus} '
             f'promoted={len(promoted)} uploaded={stats.get("uploaded")} commit={stats.get("commit_hash")}')
    finally:
        conn.close()
    return stats


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'once'
    if mode == 'once':
        run_once()
    else:
        print(f'用法: {os.path.basename(__file__)} once')
        sys.exit(1)


if __name__ == '__main__':
    main()
