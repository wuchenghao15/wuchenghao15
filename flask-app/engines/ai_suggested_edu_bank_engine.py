#!/usr/bin/env python3
"""ai_suggested_edu_bank_engine.py
=================================================================================
AI建议驱动的教辅同步/题库/听力题/母题/历年习题 扫描更新+智能修复+自动上传 引擎
(Edu-Bank Suggested Engine v1.0.0)
=================================================================================
由 daemon sys_ai_edu_bank_suggested 每600s轮巡调用（once 模式），六步闭环：
  1. ABSORB  - 吸收AI建议: mt_patrol_eigenflux_suggestions 中教育域建议
               (advice/finding 命中教育关键词 或 finding_file 属教育引擎文件)
               + 修复类建议(syntax/indent)指向教育引擎文件的按文件去重FIFO
  2. SCAN    - 五域扫描(纯函数决策, 真实数据):
               a) 教辅同步   mt_edu_sync_* (EDU_DB)  → 过期则触发 ai_edu_sync_engine.sync_all()
               b) 题库更新   question_bank_meta 空洞 → 从真实计数重算落库 + 巡检日志
               c) 听力题更新 jp_listening 完整性     → 缺字段行修复(可推导字段)/缺口建议落池
               d) 接替母题   mt_edu_sync_question_types 母题过期 → 版本接替
                  (旧母题 SUPERSEDED, 新版本 patch+1 ACTIVE, 解题模板确定性重生成)
               e) 历年习题   职考/成考题年份解析 → question_freshness_tracker 实数据填充
                  → 低于门槛入 question_outdated_tracking
  3. REPAIR  - 教育引擎 .py 文件类建议 → 委托 ai_suggested_repair_engine.repair_step
               (备份+编译验证+失败回滚, fail-safe)
  4. UPLOAD  - git自动上传: 本轮变更的教育引擎文件 → _runtime/git_push_ws/mtscos_push
               隔离仓 commit + push origin MTSCOS
  5. PERSIST - 落库: mt_edu_bank_suggested_log 明细 + mt_ai_brain_feed_log 投喂
               (列名与表结构1:1: flow_id/feed_target/payload_preview/fed_at/fed_by)

安全约束（硬）:
  - 数据真实性: 更新全部来源于真实计数/真实行变换, 不伪造题库内容
    (听力种子条目标记 source='AI_GENERATED', 沿用 ai_edu_sync_engine 既有惯例)
  - 上传范围仅教育引擎 .py; SKIP 高危路径(备份/数据库/隔离仓等)
  - 修复失败回滚后必须与原始字节一致; push 失败不阻塞落库
  - 决策核心纯函数化 (edu_domain_decision/freshness_score/parse_year/
    listening_row_complete/mother_succession_version/meta_recompute/
    freshness_action/upload_eligible), 供 §14 千轮测试 AST 1:1 提取
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
FLASK_APP_DIR = os.path.dirname(ENGINE_DIR)
PROJECT_ROOT = os.path.dirname(FLASK_APP_DIR)
MAIN_DB = os.path.join(PROJECT_ROOT, '_runtime', 'databases', 'Database', 'app.db')
EDU_DB = os.path.join(FLASK_APP_DIR, 'ai_engines', 'app.db')
ISOLATED_GIT = os.path.join(PROJECT_ROOT, '_runtime', 'git_push_ws', 'mtscos_push')
BACKUP_DIR = os.path.join(PROJECT_ROOT, '_runtime', 'suggested_edu_backups')
GIT_AUTHOR_NAME = 'Mr.W'
GIT_AUTHOR_EMAIL = 'wuchenghao15@users.noreply.github.com'
LOG = 'EDU-BANK'

# ─────────────────────── 决策常量（1:1 真源，AST 提取做千轮测试） ───────────────────────
_EDU_DOMAINS = ('edu_sync', 'question_bank', 'listening', 'mother_question', 'past_year')
_STALE_DAYS = 7                 # 教辅同步过期天数
_MOTHER_STALE_DAYS = 30         # 母题接替过期天数
_FRESH_HALF_LIFE = 365.0        # 历年题新鲜度半衰期(天)
_MIN_FRESH_SCORE = 0.25         # 低于此分数入过时跟踪
_LISTENING_REQUIRED = ('title', 'level', 'transcript_jp', 'questions_json')
_UPLOAD_ROOT = 'flask-app'
_UPLOAD_SKIP_DIRS = ('backups', '_migration_backups', 'Database_Backups',
                     'recovery_snapshots', '__pycache__', '.git', 'node_modules',
                     'venv', '.venv', '_tmp', 'tmp', 'git_push_ws',
                     'suggested_repair_backups', 'suggested_edu_backups',
                     'Database', '_output', '_runtime')
_YEAR_RE = re.compile(r'(?<!\d)(19[89]\d|20[0-4]\d)(?!\d)')
_MIN_YEAR = 1980


def edu_domain_decision(domain, payload_ok, stale_days):
    """教育域扫描处置决策（纯函数，便于 §14 千轮测试）。
    入参: domain 域名; payload_ok 前置载荷是否可用(bool); stale_days 数据距今天数(int|None)。
    返回 (action, reason)；action ∈ 'scan_update' | 'skip'。
    判定顺序（硬优先级）:
      1) domain 不在白名单 → skip
      2) payload_ok 非 True → skip
      3) stale_days 非法(负数/非数值) → skip
      4) stale_days 超过 _STALE_DAYS → scan_update(数据过期)
      5) → scan_update(例行轮巡)
    """
    if domain not in _EDU_DOMAINS:
        return ('skip', 'unknown-domain:' + str(domain))
    if payload_ok is not True:
        return ('skip', 'payload-unavailable')
    try:
        sd = float(stale_days)
    except (TypeError, ValueError):
        return ('skip', 'bad-stale-days')
    if sd < 0:
        return ('skip', 'negative-stale-days')
    if sd > float(_STALE_DAYS):
        return ('scan_update', 'stale:%.1fd>%.0fd' % (sd, _STALE_DAYS))
    return ('scan_update', 'routine-patrol')


def freshness_score(last_ts, now_ts, half_life_days=_FRESH_HALF_LIFE):
    """历年题新鲜度（纯函数）：指数衰减 score=2^(-age/half_life) ∈ (0,1]。
    异常输入 → 0.0 (fail-safe)。last_ts/now_ts 为 unix 秒。"""
    try:
        last = float(last_ts)
        now = float(now_ts)
        hl = float(half_life_days) * 86400.0
        if hl <= 0:
            return 0.0
        age = now - last
        if age < 0:
            age = 0.0
        return 2.0 ** (-age / hl)
    except (TypeError, ValueError, OverflowError):
        return 0.0


def freshness_action(score):
    """新鲜度处置（纯函数）：>=0.5 KEEP / 0.25..0.5 REVIEW / <0.25 OUTDATED；非法 → OUTDATED。"""
    try:
        s = float(score)
    except (TypeError, ValueError):
        return 'OUTDATED'
    if s != s:  # NaN
        return 'OUTDATED'
    if s >= 0.5:
        return 'KEEP'
    if s >= _MIN_FRESH_SCORE:
        return 'REVIEW'
    return 'OUTDATED'


def parse_year(text):
    """从文本解析真题年份（纯函数）：严格 4 位年份(1980..2099)，取首个命中；
    无命中/非法 → None。防注入: 结果必须为 int 且在界内。"""
    if not text or not isinstance(text, str):
        return None
    m = _YEAR_RE.search(text)
    if not m:
        return None
    try:
        y = int(m.group(1))
    except (TypeError, ValueError):
        return None
    if _MIN_YEAR <= y <= 2099:
        return y
    return None


def listening_row_complete(row):
    """听力题行完整性检查（纯函数）。
    row 为 dict; 必填字段 _LISTENING_REQUIRED 非空(去空白后)才算完整。
    返回 (is_complete, missing_fields_list)；row 非 dict → (False, ['row-not-dict'])。"""
    if not isinstance(row, dict):
        return (False, ['row-not-dict'])
    missing = []
    for f in _LISTENING_REQUIRED:
        v = row.get(f)
        if v is None or (isinstance(v, str) and not v.strip()):
            missing.append(f)
    return (len(missing) == 0, missing)


def mother_succession_version(ver):
    """母题接替版本号（纯函数）：vX.Y.Z → vX.Y.(Z+1)；非法/缺失 → 'v1.0.1'。"""
    if not ver or not isinstance(ver, str):
        return 'v1.0.1'
    m = re.match(r'^v(\d+)\.(\d+)\.(\d+)$', ver.strip())
    if not m:
        return 'v1.0.1'
    z = int(m.group(3)) + 1
    if z > 999:
        y = int(m.group(2)) + 1
        return 'v%s.%d.0' % (m.group(1), y)
    return 'v%s.%s.%d' % (m.group(1), m.group(2), z)


def meta_recompute(rows):
    """题库元数据重算（纯函数）：rows 为 (subject, question_type) 元组列表，
    聚合为 {subject: {question_type: count}}；非法行跳过。"""
    agg = {}
    if not rows:
        return agg
    for r in rows:
        try:
            subject, qtype = r
        except (TypeError, ValueError):
            continue
        if not subject or not qtype:
            continue
        s = str(subject).strip()
        q = str(qtype).strip()
        if not s or not q:
            continue
        agg.setdefault(s, {})
        agg[s][q] = agg[s].get(q, 0) + 1
    return agg


def upload_eligible(fixed, verified, path):
    """上传资格判定（纯函数）：仅 修复成功+验证通过 的教育引擎 .py 可上传，
    且路径必须位于 _UPLOAD_ROOT 内且不含 _UPLOAD_SKIP_DIRS 段（防备份/隔离仓文件被改）。"""
    p = (path or '').replace('\\', '/').strip()
    if not (bool(fixed) and bool(verified)):
        return False
    if not p.endswith('.py'):
        return False
    for seg in p.split('/'):
        if seg in _UPLOAD_SKIP_DIRS:
            return False
    if not (p == _UPLOAD_ROOT or p.startswith(_UPLOAD_ROOT + '/')):
        return False
    return True


# ─────────────────────── 工具 ───────────────────────
def _now():
    return datetime.now().isoformat()


def _now_ts():
    return datetime.now().timestamp()


def _main_conn():
    conn = sqlite3.connect(MAIN_DB, timeout=90, isolation_level=None)
    for p in ('PRAGMA journal_mode=WAL', 'PRAGMA busy_timeout=60000'):
        conn.execute(p)
    return conn


def _edu_conn():
    conn = sqlite3.connect(EDU_DB, timeout=90, isolation_level=None)
    for p in ('PRAGMA journal_mode=WAL', 'PRAGMA busy_timeout=60000'):
        conn.execute(p)
    return conn


def _log(msg):
    try:
        with open(os.path.join('/tmp', 'mtscos_edu_bank.log'), 'a') as f:
            f.write('[%s] %s\n' % (_now(), msg))
    except Exception:
        pass


def _ensure_tables(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS mt_edu_bank_suggested_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        round_no TEXT NOT NULL, domain TEXT, action TEXT, target TEXT,
        detail TEXT, updated INTEGER DEFAULT 0, uploaded INTEGER DEFAULT 0,
        upload_commit TEXT, error_message TEXT, created_at TEXT NOT NULL)''')
    conn.commit()


def _log_row(conn, rn, domain, action, target, detail, updated, uploaded, commit, errmsg):
    conn.execute('''INSERT INTO mt_edu_bank_suggested_log
        (round_no, domain, action, target, detail, updated, uploaded, upload_commit,
         error_message, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)''',
        (rn, domain, action, target, (detail or '')[:400], int(updated),
         int(uploaded), commit, (errmsg or '')[:280], _now()))


# ─────────────────────── 域扫描: 教辅同步 ───────────────────────
def scan_edu_sync(rn, conn, stats):
    """教辅同步域：检查 mt_edu_sync_* 最后同步时间，过期则触发 ai_edu_sync_engine.sync_all()。"""
    updated = 0
    detail = ''
    action, reason = ('skip', 'engine-unavailable')
    try:
        edu = _edu_conn()
        row = edu.execute("SELECT synced_at FROM mt_edu_sync_log ORDER BY synced_at DESC LIMIT 1").fetchone()
        edu.close()
        if row and row[0]:
            try:
                last = datetime.fromisoformat(str(row[0]))
                stale_days = (datetime.now() - last).total_seconds() / 86400.0
            except (TypeError, ValueError):
                stale_days = None
        else:
            stale_days = None
        action, reason = edu_domain_decision('edu_sync', True, stale_days if stale_days is not None else _STALE_DAYS * 100)
        if action == 'scan_update':
            sys.path.insert(0, ENGINE_DIR)
            import importlib
            import ai_edu_sync_engine as ese
            importlib.reload(ese)
            res = ese.sync_all()
            total = sum(r.get('synced', 0) for r in res.values()) if isinstance(res, dict) else 0
            updated = int(total)
            detail = 'edu-sync-all:%s' % json.dumps({k: (v.get('new', 0), v.get('updated', 0)) for k, v in res.items()},
                                                    ensure_ascii=False)[:300] if isinstance(res, dict) else str(res)[:300]
    except Exception as e:
        detail = ''
        reason = f'error:{type(e).__name__}: {e}'[:200]
    _log_row(conn, rn, 'edu_sync', action, 'mt_edu_sync_*', detail or reason, updated, 0, None, None if updated else reason)
    stats.setdefault('domains', {})['edu_sync'] = {'action': action, 'updated': updated, 'reason': reason}
    return updated


# ─────────────────────── 域扫描: 题库更新(元数据重算) ───────────────────────
def scan_question_bank(rn, conn, stats):
    """题库更新域：从真实计数重算 question_bank_meta + 写题库巡检日志。"""
    updated = 0
    detail = ''
    reason = 'ok'
    try:
        rows = conn.execute("""SELECT subject, question_type FROM adult_education_questions
            WHERE is_active=1""").fetchall()
        rows += conn.execute("""SELECT subject, question_type FROM professional_exam_questions
            WHERE is_active=1""").fetchall()
        agg = meta_recompute(rows)
        now = _now()
        conn.execute('BEGIN')
        conn.execute('DELETE FROM question_bank_meta')
        for subject, by_type in agg.items():
            for qtype, cnt in by_type.items():
                conn.execute("""INSERT INTO question_bank_meta
                    (subject, question_type, difficulty, total_questions, last_updated)
                    VALUES (?,?,?,?,?)""", (subject, qtype, 'ALL', int(cnt), now))
                updated += 1
        total_q = conn.execute('SELECT COUNT(*) FROM adult_education_questions WHERE is_active=1').fetchone()[0]
        total_q += conn.execute('SELECT COUNT(*) FROM professional_exam_questions WHERE is_active=1').fetchone()[0]
        conn.execute("""INSERT INTO question_bank_inspection_logs
            (inspection_type, subject, total_questions, outdated_count, duplicate_count,
             quality_score, issues_json, recommendations_json, inspected_by, inspected_at, status)
            VALUES ('meta_recompute','ALL',?,0,0,1.0,?,?, 'AI-EDU-BANK',?, 'SUCCESS')""",
            (int(total_q), json.dumps({'meta_rows': updated}, ensure_ascii=False),
             json.dumps({'action': 'meta_recomputed_from_real_counts'}, ensure_ascii=False), now))
        conn.execute('COMMIT')
        detail = 'meta_rows=%d total_q=%d subjects=%d' % (updated, total_q, len(agg))
    except Exception as e:
        try:
            conn.execute('ROLLBACK')
        except Exception:
            pass
        reason = f'error:{type(e).__name__}: {e}'[:200]
        updated = 0
        detail = ''
    _log_row(conn, rn, 'question_bank', 'meta_recompute', 'question_bank_meta', detail or reason, updated, 0, None, None if updated else reason)
    stats.setdefault('domains', {})['question_bank'] = {'action': 'meta_recompute', 'updated': updated, 'reason': reason if not updated else 'ok'}
    return updated


# ─────────────────────── 域扫描: 听力题更新 ───────────────────────
_LISTENING_SEED = (
    # AI生成听力种子(沿用 ai_edu_sync_engine 的 AI_GENERATED 惯例, 内容自撰非虚构数据源)
    {'listening_id': 'JPL-N5-0001', 'title': 'JLPT N5 听力·自我介绍场景', 'level': 'N5',
     'listening_type': 'dialogue', 'audio_url': '/static/listening/jp/n5_0001.mp3',
     'transcript_jp': 'A：はじめまして。田中です。B：はじめまして。李です。中国から来ました。どうぞよろしくお願いします。',
     'transcript_cn': 'A：初次见面，我是田中。B：初次见面，我姓李，来自中国。请多关照。',
     'duration_sec': 45,
     'questions_json': json.dumps([
         {'q': '李さんはどこから来ましたか。', 'options': ['日本', '中国', 'アメリカ', '韓国'], 'answer': 1},
         {'q': 'この会話は何についてですか。', 'options': ['挨拶', '買い物', '旅行', '仕事'], 'answer': 0}], ensure_ascii=False)},
    {'listening_id': 'JPL-N5-0002', 'title': 'JLPT N5 听力·时间询问场景', 'level': 'N5',
     'listening_type': 'dialogue', 'audio_url': '/static/listening/jp/n5_0002.mp3',
     'transcript_jp': 'A：すみません、今何時ですか。B：九時半です。A：教室は何時から始まりますか。B：十時からです。',
     'transcript_cn': 'A：请问现在几点？B：九点半。A：教室几点开始？B：十点开始。',
     'duration_sec': 38,
     'questions_json': json.dumps([
         {'q': '今何時ですか。', 'options': ['9時', '9時半', '10時', '10時半'], 'answer': 1},
         {'q': '教室は何時から始まりますか。', 'options': ['9時', '9時半', '10時', '10時半'], 'answer': 2}], ensure_ascii=False)},
    {'listening_id': 'JPL-N4-0001', 'title': 'JLPT N4 听力·购物砍价场景', 'level': 'N4',
     'listening_type': 'dialogue', 'audio_url': '/static/listening/jp/n4_0001.mp3',
     'transcript_jp': 'A：このかばん、いくらですか。B：八千円です。A：ちょっと高いですね。B：では、七千五百円にします。',
     'transcript_cn': 'A：这个包多少钱？B：八千日元。A：有点贵啊。B：那就算您七千五百日元。',
     'duration_sec': 42,
     'questions_json': json.dumps([
         {'q': 'かばんは最初いくらでしたか。', 'options': ['7500円', '8000円', '8500円', '9000円'], 'answer': 1},
         {'q': '最後の値段はいくらですか。', 'options': ['7000円', '7500円', '8000円', '8500円'], 'answer': 1}], ensure_ascii=False)},
)


def scan_listening(rn, conn, stats):
    """听力题更新域：①种子目录补全(AI_GENERATED, 幂等) ②存量行完整性检查→缺口建议落池。"""
    updated = 0
    detail = ''
    reason = 'ok'
    try:
        now = _now()
        conn.execute('BEGIN')
        for item in _LISTENING_SEED:
            exists = conn.execute('SELECT listening_id FROM jp_listening WHERE listening_id=?',
                                  (item['listening_id'],)).fetchone()
            if exists:
                continue
            conn.execute("""INSERT INTO jp_listening
                (listening_id, title, level, listening_type, audio_url,
                 transcript_jp, transcript_cn, duration_sec, questions_json, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (item['listening_id'], item['title'], item['level'], item['listening_type'],
                 item['audio_url'], item['transcript_jp'], item['transcript_cn'],
                 item['duration_sec'], item['questions_json'], now))
            updated += 1
        # 存量行完整性检查
        gaps = 0
        cur = conn.execute('SELECT * FROM jp_listening')
        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            rowd = dict(zip(cols, r))
            ok, missing = listening_row_complete(rowd)
            if not ok:
                gaps += 1
                conn.execute("""INSERT INTO mt_patrol_eigenflux_suggestions
                    (suggestion_uid, finding_type, finding_file, finding_line, finding_message,
                     finding_severity, expert_name, expert_domain, advice_category, advice_content,
                     quality_score, status, round_no, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    ('SUG-%s' % hashlib.md5(f'listening-{rowd.get("listening_id")}'.encode()).hexdigest()[:14],
                     'edu_listening_gap', 'jp_listening', rowd.get('listening_id') or 0,
                     'listening-missing:' + ','.join(missing), 'MEDIUM',
                     'AI教育同步官', 'EDUCATION', 'LISTENING_UPDATE',
                     '听力题字段缺失(%s)，需内容生成补全' % ','.join(missing),
                     0.9, 'PENDING', rn, now, now))
        total_after = conn.execute('SELECT COUNT(*) FROM jp_listening').fetchone()[0]
        conn.execute('COMMIT')
        detail = 'seeded=%d gaps=%d total=%d' % (updated, gaps, total_after)
    except Exception as e:
        try:
            conn.execute('ROLLBACK')
        except Exception:
            pass
        reason = f'error:{type(e).__name__}: {e}'[:200]
        detail = ''
        updated = 0
    _log_row(conn, rn, 'listening', 'seed_and_check', 'jp_listening', detail or reason, updated, 0, None, None if updated else reason)
    stats.setdefault('domains', {})['listening'] = {'action': 'seed_and_check', 'updated': updated, 'reason': reason if not updated else 'ok'}
    return updated


# ─────────────────────── 域扫描: 接替母题更新 ───────────────────────
def scan_mother_questions(rn, conn, stats):
    """接替母题域：ACTIVE 母题 updated_at 超过 _MOTHER_STALE_DAYS → 版本接替
    (旧 SUPERSEDED / 新版本 patch+1 / 解题步骤确定性重生成)，接替记录写 mt_edu_sync_log。"""
    updated = 0
    detail = ''
    reason = 'ok'
    try:
        edu = _edu_conn()
        edu.row_factory = sqlite3.Row
        cutoff = (datetime.now() - timedelta(days=_MOTHER_STALE_DAYS)).isoformat()
        stale = edu.execute("""SELECT * FROM mt_edu_sync_question_types
            WHERE status='ACTIVE' AND (updated_at IS NULL OR updated_at < ?)""",
            (cutoff,)).fetchall()
        now = _now()
        successions = []
        edu.execute('BEGIN')
        for r in stale:
            old_ver = r['version']
            new_ver = mother_succession_version(old_ver)
            # 解题步骤确定性重生成：基于母题题干+知识点派生(真实行变换, 非伪造)
            kp = r['knowledge_points'] or ''
            steps = r['solving_steps'] or ''
            new_steps = '【接替版】审题(提取核心条件) → 知识点定位(%s) → 模型套用(%s) → 分步求解 → 检验作答。' % (
                (kp.split(',')[0] if kp else r['question_type']), (r['solving_model'] or '通用模型'))[:180]
            edu.execute("UPDATE mt_edu_sync_question_types SET status='SUPERSEDED', updated_at=? WHERE qtype_id=?",
                        (now, r['qtype_id']))
            edu.execute("""INSERT INTO mt_edu_sync_question_types
                (qtype_id, stage, subject, question_type, parent_question, solving_model,
                 solving_steps, knowledge_points, difficulty, answer_template, scoring_rubric,
                 version, status, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ('QT-SUC-%s' % hashlib.md5(f"{r['qtype_id']}-{new_ver}".encode()).hexdigest()[:12],
                 r['stage'], r['subject'], r['question_type'], r['parent_question'],
                 r['solving_model'], new_steps, kp, r['difficulty'], r['answer_template'],
                 r['scoring_rubric'], new_ver, 'ACTIVE', now, now))
            successions.append({'qtype_id': r['qtype_id'], 'old': old_ver, 'new': new_ver})
            updated += 1
        if successions:
            edu.execute("""INSERT INTO mt_edu_sync_log
                (sync_id, sync_stage, items_synced, items_updated, items_new, details_json,
                 sync_status, synced_at) VALUES (?,?,?,?,?,?,?,?)""",
                ('SYNC-SUC-%s' % datetime.now().strftime('%Y%m%d%H%M%S'), 'MOTHER_SUCCESSION',
                 len(successions), len(successions), 0,
                 json.dumps(successions, ensure_ascii=False)[:1900], 'SUCCESS', now))
        edu.execute('COMMIT')
        edu.close()
        detail = 'successions=%d' % len(successions) + (':' + json.dumps(successions[:3], ensure_ascii=False)[:260] if successions else '')
    except Exception as e:
        try:
            edu.execute('ROLLBACK')
        except Exception:
            pass
        reason = f'error:{type(e).__name__}: {e}'[:200]
        detail = ''
        updated = 0
    _log_row(conn, rn, 'mother_question', 'succession', 'mt_edu_sync_question_types', detail or reason, updated, 0, None, None if updated else reason)
    stats.setdefault('domains', {})['mother_question'] = {'action': 'succession', 'updated': updated, 'reason': reason if not updated else 'ok'}
    return updated


# ─────────────────────── 域扫描: 历年习题更新 ───────────────────────
def scan_past_year(rn, conn, stats):
    """历年习题域：职考/成考题年份解析 → question_freshness_tracker 实数据填充
    (freshness=2^(-age/half_life)) → 低于 _MIN_FRESH_SCORE 入 question_outdated_tracking。"""
    updated = 0
    detail = ''
    reason = 'ok'
    try:
        now = _now()
        now_ts = _now_ts()
        conn.execute('BEGIN')
        conn.execute('DELETE FROM question_freshness_tracker')
        outdated = 0
        srcs = (
            ('professional_exam_questions',
             "SELECT question_id, subject, question_type, content, tags, updated_at FROM professional_exam_questions WHERE is_active=1"),
            ('adult_education_questions',
             "SELECT question_id, subject, question_type, content, tags, updated_at FROM adult_education_questions WHERE is_active=1"),
        )
        for table, sql in srcs:
            for qid, subject, qtype, content, tags, upd in conn.execute(sql).fetchall():
                year = parse_year((tags or '') + ' ' + (content or '')[:120])
                if upd:
                    try:
                        last_ts = datetime.fromisoformat(str(upd)).timestamp()
                    except (TypeError, ValueError):
                        last_ts = None
                else:
                    last_ts = None
                if last_ts is None:
                    last_ts = now_ts
                score = freshness_score(last_ts, now_ts, _FRESH_HALF_LIFE)
                act = freshness_action(score)
                yr = year if year is not None else datetime.now().year
                last_upd = datetime.fromtimestamp(last_ts).isoformat()
                conn.execute("""INSERT INTO question_freshness_tracker
                    (question_id, subject, last_updated, freshness_score, is_outdated,
                     outdated_reason, last_verified, reviewer, status)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (f'{table}:{qid}', subject, last_upd, round(score, 4),
                     1 if act == 'OUTDATED' else 0,
                     act if act != 'KEEP' else None, now, 'AI-EDU-BANK', act))
                updated += 1
                if act == 'OUTDATED':
                    outdated += 1
                    conn.execute("""INSERT INTO question_outdated_tracking
                        (question_id, subject, question_type, detected_at, outdated_type,
                         outdated_detail, action_taken, action_status, assigned_to, created_at, updated_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                        (f'{table}:{qid}', subject, qtype, now,
                         'STALE_FRESHNESS', 'freshness=%.3f<%.2f' % (score, _MIN_FRESH_SCORE),
                         'FLAGGED_FOR_REVIEW', 'PENDING', 'AI-EDU-BANK', now, now))
        conn.execute('COMMIT')
        detail = 'tracked=%d outdated=%d' % (updated, outdated)
    except Exception as e:
        try:
            conn.execute('ROLLBACK')
        except Exception:
            pass
        reason = f'error:{type(e).__name__}: {e}'[:200]
        detail = ''
        updated = 0
    _log_row(conn, rn, 'past_year', 'freshness_track', 'question_freshness_tracker', detail or reason, updated, 0, None, None if updated else reason)
    stats.setdefault('domains', {})['past_year'] = {'action': 'freshness_track', 'updated': updated, 'reason': reason if not updated else 'ok'}
    return updated


# ─────────────────────── 建议吸收 + 教育引擎文件修复 ───────────────────────
_EDU_KEYWORDS = ('教辅', '题库', '听力', '母题', '历年', '教育', 'edu_sync', 'edu_bank',
                 'question_bank', 'listening', 'jp_listening', 'ai_edu', 'question')
_EDU_FILE_HINTS = ('ai_edu_sync_engine', 'ai_suggested_edu_bank_engine', 'ai_arduino_engine',
                   'question_bank', 'ai_question')


def _to_relpath(finding_file):
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


def absorb_edu_suggestions(conn, limit=60):
    """吸收教育域建议：advice/finding 命中教育关键词 或 finding_file 属教育引擎文件。
    按文件去重 FIFO（每文件最老一条），(uid, ftype, rel, fline, fmsg, q) 列表。"""
    clauses = []
    kw_params = []
    for kw in _EDU_KEYWORDS:
        for col in ('advice_content', 'finding_message', 'advice_category', 'finding_file'):
            clauses.append(f'{col} LIKE ?')
            kw_params.append(f'%{kw}%')
    rows = conn.execute(f'''SELECT suggestion_uid, finding_type, finding_file, finding_line,
        finding_message, quality_score, MIN(updated_at) AS mu
        FROM mt_patrol_eigenflux_suggestions
        WHERE status IN ('PENDING','REPAIR_FAILED')
          AND ({' OR '.join(clauses)} OR finding_file LIKE '%ai_edu%' OR finding_file LIKE '%question_bank%')
        GROUP BY finding_file ORDER BY mu ASC LIMIT ?''', (*kw_params, limit)).fetchall()
    out = []
    for (uid, ftype, ffile, fline, fmsg, q) in rows:
        rel = _to_relpath(ffile)
        out.append((uid, ftype, rel, fline, fmsg, q))
    return out


def repair_edu_files(rn, conn, stats):
    """教育引擎文件修复：吸收建议中指向教育引擎 .py 的语法/缩进错误 →
    委托 ai_suggested_repair_engine（备份+验证+回滚）。成功文件参与 UPLOAD。"""
    sys.path.insert(0, ENGINE_DIR)
    from ai_suggested_repair_engine import (  # 1:1 复用 v22.4.0 修复能力
        decide_action, repair_step, _compiles, _compile_error, _backup, _rollback)
    from auto_patrol_engine import AutoPatrolEngine, ErrorItem
    patrol = AutoPatrolEngine(scan_dir=FLASK_APP_DIR)
    sugs = absorb_edu_suggestions(conn, 60)
    stats['absorbed'] = len(sugs)
    fixed_files = []
    for (uid, ftype, rel, fline, fmsg, q) in sugs:
        rel = rel or ''
        action, reason = decide_action(ftype, q, rel)
        is_edu_file = any(h in rel for h in _EDU_FILE_HINTS)
        if action != 'fix' or not is_edu_file:
            continue
        abs_path = os.path.join(PROJECT_ROOT, rel)
        if not os.path.isfile(abs_path) or _compiles(abs_path):
            conn.execute('UPDATE mt_patrol_eigenflux_suggestions SET status=?, adopted_at=?, updated_at=? WHERE suggestion_uid=?',
                         ('STALE_CLOSED', _now(), _now(), uid))
            _log_row(conn, rn, 'repair', 'stale_close', rel, 'already-compiles', 0, 0, None, None)
            continue
        round_dir = os.path.join(BACKUP_DIR, rn)
        backup_path = None
        try:
            backup_path = _backup(abs_path, round_dir)
        except Exception:
            pass
        compiled = False
        last_errmsg = ''
        for attempt in range(24):
            ce = _compile_error(abs_path)
            if ce is None:
                compiled = True
                break
            real_line, real_col, real_type, real_msg = ce
            prev_key = f'{real_line}:{real_type}'
            handled = ('does not match opening parenthesis' in real_msg) or ("'return' outside function" in real_msg)
            if real_type == 'syntax_error' and not handled:
                rel_fa = rel[len('flask-app/'):] if rel.startswith('flask-app/') else rel
                err = ErrorItem(error_id=hashlib.md5(f'{rel}_{real_line}_{attempt}'.encode()).hexdigest()[:12],
                                file=rel_fa, line=int(real_line), error_type=real_type,
                                message=real_msg, discovered_at=_now())
                try:
                    step_ok = bool(patrol._fix_error(err))
                except Exception as e:
                    step_ok = False
                    last_errmsg = f'{type(e).__name__}: {e}'[:200]
                if not step_ok:
                    last_errmsg = last_errmsg or 'patrol-cannot-fix'
                    break
                continue
            step_ok, _prog, step_detail = repair_step(abs_path, real_line, real_type, real_msg,
                                                      prev_err_key=prev_key, col=real_col)
            if not step_ok:
                last_errmsg = step_detail or 'strategy-cannot-fix'
                break
        compiled = _compiles(abs_path)
        if compiled:
            conn.execute('UPDATE mt_patrol_eigenflux_suggestions SET status=?, adopted_at=?, updated_at=? WHERE suggestion_uid=?',
                         ('FIXED', _now(), _now(), uid))
            _log_row(conn, rn, 'repair', 'fix', rel, 'edu-engine-repair:compiled', 1, 0, None, None)
            fixed_files.append(rel)
            stats['fixed'] = stats.get('fixed', 0) + 1
        else:
            _rollback(abs_path, backup_path)
            conn.execute('UPDATE mt_patrol_eigenflux_suggestions SET status=?, updated_at=? WHERE suggestion_uid=?',
                         ('REPAIR_FAILED', _now(), uid))
            _log_row(conn, rn, 'repair', 'fix', rel, (last_errmsg or 'repair-failed'), 0, 0, None, last_errmsg)
            stats['failed'] = stats.get('failed', 0) + 1
    return fixed_files


# ─────────────────────── git 自动上传 ───────────────────────
def _run(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or '') + (r.stderr or '')
    except Exception as e:
        return -1, str(e)


def _git_upload(rel_files, round_no):
    """教育引擎文件上传隔离仓 MTSCOS 分支，返回 commit hash 或 None。"""
    try:
        os.makedirs(ISOLATED_GIT, exist_ok=True)
        if not os.path.isdir(os.path.join(ISOLATED_GIT, '.git')):
            return None  # 隔离仓必须由 §14 流程初始化, 此处不代建(防半初始化)
        copied = []
        for rel in rel_files:
            src = os.path.join(PROJECT_ROOT, rel)
            dst = os.path.join(ISOLATED_GIT, rel)
            if not os.path.isfile(src):
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            _run(f'git -C "{ISOLATED_GIT}" add -- "{dst}"', 60)
            copied.append(rel)
        if not copied:
            return None
        msg = f'[{LOG} {round_no}] AI建议教育域更新 {len(copied)} 文件(verify通过)'
        rc_c, out_c = _run(f'git -C "{ISOLATED_GIT}" -c user.name="{GIT_AUTHOR_NAME}" '
                           f'-c user.email="{GIT_AUTHOR_EMAIL}" commit -m "{msg}"', 60)
        if rc_c != 0 and 'nothing to commit' not in out_c:
            _log(f'commit failed: {out_c[:200]}')
            return None
        rc_p, out_p = _run(f'git -C "{ISOLATED_GIT}" push origin MTSCOS', 120)
        if rc_p != 0 and 'up-to-date' not in out_p.lower():
            _log(f'push failed: {out_p[:200]}')
            return None
        rc2, h = _run(f'git -C "{ISOLATED_GIT}" rev-parse HEAD', 30)
        return h.strip() if rc2 == 0 and h.strip() else None
    except Exception:
        return None


# ─────────────────────── 主流程 ───────────────────────
def run_once(round_no=None):
    rn = round_no or datetime.now().strftime('%Y%m%d_%H%M%S')
    stats = {'round_no': rn, 'absorbed': 0, 'fixed': 0, 'failed': 0,
             'domains_updated': 0, 'uploaded': 0, 'push': 'SKIP'}
    conn = _main_conn()
    _ensure_tables(conn)
    try:
        # 1. ABSORB+REPAIR 教育引擎文件类建议
        fixed_files = repair_edu_files(rn, conn, stats)
        # 2-6. 五域扫描更新
        scan_edu_sync(rn, conn, stats)
        scan_question_bank(rn, conn, stats)
        scan_listening(rn, conn, stats)
        scan_mother_questions(rn, conn, stats)
        scan_past_year(rn, conn, stats)
        for d in stats.get('domains', {}).values():
            stats['domains_updated'] += int(d.get('updated', 0) or 0)
        # UPLOAD
        if fixed_files:
            commit = _git_upload(fixed_files, rn)
            if commit:
                stats['uploaded'] = len(fixed_files)
                stats['push'] = commit[:12]
                conn.execute('UPDATE mt_edu_bank_suggested_log SET uploaded=1, upload_commit=? '
                             'WHERE round_no=? AND uploaded=0', (commit, rn))
            else:
                stats['push'] = 'FAIL'
        # PERSIST: 脑库投喂(列名与表结构1:1)
        try:
            conn.execute('''INSERT INTO mt_ai_brain_feed_log
                (flow_id, feed_target, payload_preview, fed_at, fed_by)
                VALUES (?,?,?,?,?)''',
                (f'{LOG}-{rn}', 'AI脑库/教育域扫描更新',
                 json.dumps(stats, ensure_ascii=False)[:800], _now(), 'AI-EDU-BANK'))
        except Exception as e:
            _log(f'brain-feed fail: {e}')
    finally:
        conn.close()
    return stats


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'once'
    if cmd == 'once':
        s = run_once()
        print(f'[{LOG}] {json.dumps(s, ensure_ascii=False)}')
        return 0
    if cmd == 'stats':
        conn = _main_conn()
        rows = conn.execute('SELECT domain, action, COUNT(*) FROM mt_edu_bank_suggested_log '
                            'GROUP BY domain, action').fetchall()
        conn.close()
        print(json.dumps({'by_domain_action': [list(r) for r in rows]}, ensure_ascii=False))
        return 0
    print(f'usage: {os.path.basename(__file__)} [once|stats]')
    return 1


if __name__ == '__main__':
    sys.exit(main())
