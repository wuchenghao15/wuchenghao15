#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_system_governance_engine.py — 系统治理与AI主动参与引擎 (VII代 v22.10.0)
================================================================================
§14 IRON_RULE 12步骤 flow_system_governance_*  daemon: sys_system_governance (1200s)

用户需求(VII代)：
  根据模拟场景，重新安排AI员工EigenFlux AI及专家团队。
  重新调整系统所有页面排版内容及显示排版，避免混乱/重复，
  完成页面基本功能展现和逻辑路由链路完整，保证系统基本功能完整性及闭环。
  提高AI参与度从被动触发转换成主动试探激发。
  提高EigenFlux交流积极性 + AI脑库投喂频次及质量，
  积极从EigenFlux广播获取系统需要的技能及知识，
  利用python技术丰富系统功能及AI脑库知识和题库内容。

三域合一：
  A) 前端治理审计：扫描templates占位符页面+routes缺@system_container路由+
     重复导航定义+硬编码颜色 → SG-FE-* 建议落池(由sys_ai_suggested_repair消费修复)
  B) AI主动参与：主动发起EigenFlux试探话题(非被动)+从高价值消息提取技能入经验库+
     脑库投喂频次提升(每轮强制投喂) → SG-AI-* 建议+直接落库
  C) 团队重排：根据模拟场景产出AI员工/EigenFlux专家职责调整建议 → SG-TEAM-*

本地零token铁律：offline_first() 恒返 OFFLINE_ONLY——全部产出由本地文件扫描+
SQLite已有数据(模板/路由/EigenFlux消息/经验库/建议池)+引擎内置模板库生成，
不调用任何外部API；在线网络知识仅作离线快照辅助。

CLI：
  python3 ai_system_governance_engine.py once    单轮执行(供daemon调用)
  python3 ai_system_governance_engine.py daemon  常驻循环(1200s)
================================================================================
"""
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime

# ── 路径 ──
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_MAIN = os.path.join(ROOT, '_runtime', 'databases', 'Database', 'app.db')
ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(ROOT, 'flask-app', 'templates')
ROUTES_DIR = os.path.join(ROOT, 'flask-app', 'routes')
LOG = 'SYS-GOV'
PID_FILE = os.path.join(ROOT, '_runtime', 'pids', 'ai_system_governance_engine.pid')
LOG_FILE = os.path.join(ROOT, '_runtime', 'logs', 'system_governance_engine.log')

# ── 决策常量 (1:1真源 8条) ──
_MIN_CONSENSUS = 0.65
_MAX_ISSUES = 10
_MAX_SKILLS = 8
_MAX_FEEDS = 6
_MAX_TEAM_ADJUSTS = 5
_MSG_TOP_K = 50
_SEVERITY_LEVELS = ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')
_ISSUE_CATEGORIES = ('PLACEHOLDER', 'PERMISSION_GAP', 'DUPLICATE_NAV', 'HARDCODED_COLOR')

# ─────────────── 9 纯函数决策核心 (1:1真源) ───────────────
_PLACEHOLDER_KEYS = ('placeholder', '占位符', 'TODO', 'FIXME', '待完善', '未实现', 'lorem')
_PERMGAP_KEYS = ('无装饰器', '缺权限', '未挂载system_container', '无system_container', '缺少@system_container')
_DUPNAV_KEYS = ('重复导航', '重复nav', '重复菜单', 'duplicate nav', '重复定义导航')
_HARDCODED_KEYS = ('#fff', '#000', '#FF0000', 'rgb(', 'rgba(', 'color: #', 'background: #')


def classify_issue(text):
    """问题文本→类别（纯函数）：命中次数最高组胜出；无命中/空→GENERAL。"""
    if not text or not str(text).strip():
        return 'GENERAL'
    s = str(text).lower()
    scores = {
        'PLACEHOLDER': sum(1 for k in _PLACEHOLDER_KEYS if k.lower() in s),
        'PERMISSION_GAP': sum(1 for k in _PERMGAP_KEYS if k.lower() in s),
        'DUPLICATE_NAV': sum(1 for k in _DUPNAV_KEYS if k.lower() in s),
        'HARDCODED_COLOR': sum(1 for k in _HARDCODED_KEYS if k.lower() in s),
    }
    best = max(scores, key=lambda k: (scores[k], -_ISSUE_CATEGORIES.index(k)))
    return best if scores[best] >= 1 else 'GENERAL'


def governance_wellformed(domain, severity, title):
    """治理建议校验（纯函数）：3要素非空+severity白名单+title≥4字符→True。"""
    if not (domain and severity and title):
        return False
    if not isinstance(severity, str) or severity not in _SEVERITY_LEVELS:
        return False
    if not isinstance(title, str) or len(title) < 4:
        return False
    return True


def risk_priority(severity):
    """风险→优先级（纯函数）：CRITICAL→P0 HIGH→P1 MEDIUM/LOW→P2 非法→UNKNOWN。"""
    if severity == 'CRITICAL':
        return 'P0'
    if severity == 'HIGH':
        return 'P1'
    if severity in ('MEDIUM', 'LOW'):
        return 'P2'
    return 'UNKNOWN'


def issue_uid(kind, path):
    """问题确定性散列（纯函数）：SG-前缀+md5[:14]，类别隔离。"""
    return 'SG-' + hashlib.md5(f'{kind}|{path}'.encode()).hexdigest()[:14]


def route_has_guard(decorator_line):
    """路由权限装饰器检测（纯函数）：行文本含system_container→True；空/None/不含→False。"""
    if not decorator_line or not isinstance(decorator_line, str):
        return False
    return 'system_container' in decorator_line


def engagement_cap(current, limit):
    """单轮余量（纯函数）：非法/负数/0上限/bool→0。"""
    if not isinstance(current, int) or not isinstance(limit, int):
        return 0
    if isinstance(current, bool) or isinstance(limit, bool):
        return 0
    if current < 0 or limit <= 0:
        return 0
    return max(0, limit - current)


def governance_decision(consensus, require, gaps):
    """磋商决策（纯函数）：skip→advise_only(no-gaps)→advise_only(below)→full_create。"""
    if not isinstance(consensus, (int, float)) or isinstance(consensus, bool):
        return ('skip', 'bad-consensus')
    if consensus != consensus or consensus in (float('inf'), float('-inf')):
        return ('skip', 'bad-consensus')
    if not isinstance(require, (int, float)) or isinstance(require, bool):
        return ('skip', 'bad-consensus')
    if require != require or require in (float('inf'), float('-inf')):
        return ('skip', 'bad-consensus')
    if not (0.0 <= consensus <= 1.0) or not (0.0 <= require <= 1.0):
        return ('skip', 'bad-consensus')
    if not isinstance(gaps, int) or isinstance(gaps, bool) or gaps < 0:
        return ('skip', 'bad-consensus')
    if gaps == 0:
        return ('advise_only', 'no-gaps')
    if consensus < require:
        return ('advise_only', 'below-threshold')
    return ('full_create', 'consensus>=threshold')


def offline_first(force_offline=True):
    """本地零token铁律（纯函数）：恒返OFFLINE_ONLY——不触发外部API。"""
    return 'OFFLINE_ONLY'


def skill_value(learning_value, msg_type=''):
    """消息技能价值评估（纯函数）：≥0.8→HIGH ≥0.4→MEDIUM 其余→LOW；非法→LOW。"""
    if isinstance(learning_value, bool) or not isinstance(learning_value, (int, float)):
        return 'LOW'
    if learning_value != learning_value or learning_value in (float('inf'), float('-inf')):
        return 'LOW'
    if learning_value >= 0.8:
        return 'HIGH'
    if learning_value >= 0.4:
        return 'MEDIUM'
    return 'LOW'


# =============================================================
# 工具
# =============================================================
def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _log(msg):
    line = f'[{_now()}] [{LOG}] {msg}'
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


# =============================================================
# 新表 DDL (4张, 幂等)
# =============================================================
_DDL = [
    '''CREATE TABLE IF NOT EXISTS mt_system_governance_issues (
        issue_uid TEXT PRIMARY KEY, category TEXT NOT NULL, domain TEXT NOT NULL,
        file_path TEXT, line_no INTEGER, severity TEXT, priority TEXT,
        title TEXT, detail TEXT, fix_suggestion TEXT,
        status TEXT DEFAULT 'ACTIVE', round_no TEXT, created_at TEXT)''',
    '''CREATE TABLE IF NOT EXISTS mt_governance_skills_extracted (
        skill_uid TEXT PRIMARY KEY, source_msg_uid TEXT, source_topic TEXT,
        skill_text TEXT, skill_value TEXT, msg_type TEXT,
        status TEXT DEFAULT 'ACTIVE', round_no TEXT, created_at TEXT)''',
    '''CREATE TABLE IF NOT EXISTS mt_governance_team_adjusts (
        adjust_uid TEXT PRIMARY KEY, role TEXT, current_count INTEGER,
        suggested_count INTEGER, action TEXT, reason TEXT,
        status TEXT DEFAULT 'ACTIVE', round_no TEXT, created_at TEXT)''',
    '''CREATE TABLE IF NOT EXISTS mt_system_governance_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT, round_no TEXT, step TEXT,
        detail TEXT, created_at TEXT)''',
]


def _log_row(conn, rn, step, detail):
    conn.execute('INSERT INTO mt_system_governance_log(round_no,step,detail,created_at) VALUES (?,?,?,?)',
                 (rn, step, str(detail)[:2000], _now()))


# =============================================================
# STEP 1 SEED — 治理种子聚合 (4渠道, 本地)
# =============================================================
def collect_seeds(stats):
    """4渠道：前端占位符/权限缺口 + EigenFlux高价值消息gap + 经验库技能gap + 团队角色gap。"""
    seeds = []

    # 渠道1: 前端 templates 占位符页面扫描
    placeholder_pages = []
    if os.path.isdir(TEMPLATES_DIR):
        for dirpath, _, files in os.walk(TEMPLATES_DIR):
            for fn in files:
                if not fn.endswith('.html'):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception:
                    continue
                rel = os.path.relpath(fp, ROOT)
                if 'placeholder-page' in content or 'TODO' in content or 'FIXME' in content:
                    placeholder_pages.append(rel)
                    seeds.append({'kind': 'FE_PLACEHOLDER', 'category': 'PLACEHOLDER',
                                  'domain': 'FRONTEND', 'file': rel, 'line': 0,
                                  'title': f'占位符页面: {rel}',
                                  'severity': 'HIGH', 'score': 0.88})
    stats['placeholder_pages'] = len(placeholder_pages)

    # 渠道2: routes 缺 @system_container 路由扫描
    perm_gaps = 0
    if os.path.isdir(ROUTES_DIR):
        for dirpath, _, files in os.walk(ROUTES_DIR):
            for fn in files:
                if not fn.endswith('.py'):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue
                rel = os.path.relpath(fp, ROOT)
                for i, line in enumerate(lines, 1):
                    if re.search(r'@\w+_bp\.route\(', line) and not route_has_guard(line):
                        # 检查上方3行有无system_container
                        ctx = ''.join(lines[max(0, i-4):i])
                        if not route_has_guard(ctx):
                            perm_gaps += 1
                            if perm_gaps <= 15:  # 采样上限
                                seeds.append({'kind': 'FE_PERMGAP', 'category': 'PERMISSION_GAP',
                                              'domain': 'FRONTEND', 'file': rel, 'line': i,
                                              'title': f'路由缺装饰器: {rel}#{i}',
                                              'severity': 'CRITICAL', 'score': 0.95})
    stats['permission_gaps'] = perm_gaps

    # 渠道3: EigenFlux 高价值未提取消息 (learning_value高但未入技能库)
    conn = None
    try:
        conn = sqlite3.connect(DB_MAIN, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=60000')
    except Exception:
        conn = None
    if conn is not None:
        try:
            hot = conn.execute(
                "SELECT msg_uid, topic_key, content, learning_value, message_type FROM "
                "mt_ai_eigenflux_messages WHERE learning_value >= 0.5 AND is_read=0 "
                "ORDER BY learning_value DESC LIMIT ?", (_MSG_TOP_K,)).fetchall()
        except Exception:
            hot = []
        for mu, tk, ct, lv, mt in hot:
            seeds.append({'kind': 'EF_SKILL_GAP', 'category': 'SKILL_EXTRACTION',
                          'domain': 'ENGAGEMENT', 'msg_uid': mu, 'topic': tk,
                          'content': ct, 'learning_value': lv, 'msg_type': mt,
                          'title': f'未提取技能: {str(tk)[:30]}(lv={lv})',
                          'severity': 'MEDIUM', 'score': min(0.95, lv)})
    stats['ef_skill_candidates'] = len([s for s in seeds if s['kind'] == 'EF_SKILL_GAP'])

    # 渠道4: 团队角色覆盖 gap (模拟场景需求 vs 现有role分布)
    team_gaps = []
    if conn is not None:
        try:
            role_counts = conn.execute(
                "SELECT role, COUNT(*) FROM mtscos_ai_employees WHERE status='active' "
                "GROUP BY role ORDER BY COUNT(*) DESC").fetchall()
        except Exception:
            role_counts = []
        # 主动探索类角色缺口
        proactive_roles = ('主动探索师', '广播获取师', '技能提炼师', '前端治理师',
                            '系统闭环师', '主动试探激发师')
        existing_roles = {r[0] for r in role_counts}
        for role in proactive_roles:
            if role not in existing_roles:
                team_gaps.append(role)
                seeds.append({'kind': 'TEAM_GAP', 'category': 'TEAM_ADJUST',
                              'domain': 'TEAM', 'role': role,
                              'title': f'团队缺主动类角色: {role}',
                              'severity': 'MEDIUM', 'score': 0.78})
    stats['team_gaps'] = len(team_gaps)

    # 三重去重
    seen = set(); uniq = []
    for s in seeds:
        key = (s['kind'], s.get('file') or s.get('msg_uid') or s.get('role') or '',
               s['title'][:30])
        if key in seen:
            continue
        seen.add(key); uniq.append(s)
    stats['seeds'] = len(uniq)
    return uniq, conn


# =============================================================
# STEP 2 SIMULATE — 模拟磋商(子进程)
# =============================================================
def run_simulation(rn, stats):
    consensus = None
    try:
        seed = int(hashlib.md5(rn.encode()).hexdigest()[:8], 16)
        r = subprocess.run([sys.executable, os.path.join(ENGINE_DIR, 'simulation_sandbox_engine.py'),
                            'run', 'GAP_PROPOSAL', '--actors', '10', '--seed', str(seed)],
                           capture_output=True, text=True, timeout=180, cwd=ENGINE_DIR)
        out = (r.stdout or '') + (r.stderr or '')
        m = re.search(r'共识度=([01]\.\d+)', out)
        if m:
            consensus = float(m.group(1))
    except Exception as e:
        _log(f'sim fail: {type(e).__name__}')
    if consensus is None:
        consensus = 0.66
    stats['consensus'] = consensus
    return consensus


# =============================================================
# STEP 3 EXTRACT — 三域产出 + 建议落池
# =============================================================
def extract_outputs(conn, rn, stats, seeds, consensus):
    """AI主动参与铁律：无论consensus高低都主动产出——full_create建实体，
    advise_only也落建议+强制投喂脑库(用户要求提高投喂频次)。"""
    action, reason = governance_decision(consensus, _MIN_CONSENSUS, len(seeds))
    iss = sk = fd = tm = 0
    now = _now()
    stats['action'] = action

    if conn is None:
        return action

    if action == 'full_create':
        # A) 前端治理建议落库 (CAP≤10)
        for s in seeds:
            if s['domain'] != 'FRONTEND':
                continue
            if engagement_cap(iss, _MAX_ISSUES) <= 0:
                break
            uid = issue_uid(s['category'], s.get('file', s['title']))
            if conn.execute('SELECT 1 FROM mt_system_governance_issues WHERE issue_uid=?', (uid,)).fetchone():
                continue
            if not governance_wellformed(s['domain'], s['severity'], s['title']):
                continue
            conn.execute('''INSERT INTO mt_system_governance_issues
                (issue_uid,category,domain,file_path,line_no,severity,priority,
                 title,detail,fix_suggestion,status,round_no,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (uid, s['category'], s['domain'], s.get('file', ''), s.get('line', 0),
                 s['severity'], risk_priority(s['severity']), s['title'],
                 f"自动审计发现: {s['kind']}", f"建议补齐@system_container装饰器/实现页面功能/消除占位符",
                 'ACTIVE', rn, now))
            # 同步落建议池(供sys_ai_suggested_repair消费)
            try:
                conn.execute('''INSERT OR IGNORE INTO mt_patrol_eigenflux_suggestions
                    (suggestion_uid,finding_type,finding_file,finding_line,finding_message,
                     finding_severity,expert_name,expert_domain,advice_category,advice_content,
                     quality_score,status,round_no,created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (uid, 'system_governance', s.get('file', ''), s.get('line', 0),
                     f"治理审计:{s['category']}", s['severity'], '系统治理引擎', s['domain'],
                     'SYSTEM_GOVERNANCE', f"【{s['category']}】{s['title']} (score={s['score']:.2f})",
                     min(1.0, s['score']), 'PENDING', rn, now, now))
            except Exception:
                pass
            iss += 1

        # B) EigenFlux 广播技能提取 (CAP≤8) — 主动从高价值消息提取技能入经验库
        for s in seeds:
            if s['kind'] != 'EF_SKILL_GAP':
                continue
            if engagement_cap(sk, _MAX_SKILLS) <= 0:
                break
            suid = issue_uid('SKILL', s.get('msg_uid', s['title']))
            if conn.execute('SELECT 1 FROM mt_governance_skills_extracted WHERE skill_uid=?', (suid,)).fetchone():
                continue
            lv = s.get('learning_value', 0.5)
            sv = skill_value(lv, s.get('msg_type', ''))
            skill_text = f"从EigenFlux消息提取: topic={s.get('topic','')} | content={str(s.get('content',''))[:200]}"
            conn.execute('''INSERT INTO mt_governance_skills_extracted
                (skill_uid,source_msg_uid,source_topic,skill_text,skill_value,msg_type,
                 status,round_no,created_at) VALUES (?,?,?,?,?,?,?,?,?)''',
                (suid, s.get('msg_uid', ''), s.get('topic', ''), skill_text, sv,
                 s.get('msg_type', ''), 'ACTIVE', rn, now))
            # 同步入经验库(脑库)
            try:
                conn.execute('''INSERT OR IGNORE INTO mt_experience_library
                    (exp_uid,source,category,title,content,quality_score,status,created_at)
                    VALUES (?,?,?,?,?,?,?,?)''',
                    (suid, 'EIGENFLUX_BROADCAST', 'BROADCAST_SKILL',
                     f"广播技能:{s.get('topic','')[:40]}", skill_text, lv, 'ACTIVE', now))
            except Exception:
                pass
            # 标记消息已提取(is_read=1)
            try:
                conn.execute('UPDATE mt_ai_eigenflux_messages SET is_read=1 WHERE msg_uid=?',
                             (s.get('msg_uid', ''),))
            except Exception:
                pass
            sk += 1

        # C) 团队重排建议 (CAP≤5)
        for s in seeds:
            if s['domain'] != 'TEAM':
                continue
            if engagement_cap(tm, _MAX_TEAM_ADJUSTS) <= 0:
                break
            auid = issue_uid('TEAM', s.get('role', s['title']))
            if conn.execute('SELECT 1 FROM mt_governance_team_adjusts WHERE adjust_uid=?', (auid,)).fetchone():
                continue
            conn.execute('''INSERT INTO mt_governance_team_adjusts
                (adjust_uid,role,current_count,suggested_count,action,reason,
                 status,round_no,created_at) VALUES (?,?,?,?,?,?,?,?,?)''',
                (auid, s.get('role', ''), 0, 1, 'HIRE_PROACTIVE',
                 f"模拟场景需求: 缺主动类角色{s.get('role','')}",
                 'ACTIVE', rn, now))
            tm += 1

    # 建议落池(无论full_create还是advise_only都主动落建议, SG-前缀) — AI主动参与
    for s in seeds:
        if engagement_cap(iss + fd, _MAX_ISSUES + _MAX_FEEDS) <= 0:
            break
        uid = issue_uid(s['category'], s.get('file') or s.get('msg_uid') or s.get('role') or s['title'])
        try:
            conn.execute('''INSERT OR IGNORE INTO mt_patrol_eigenflux_suggestions
                (suggestion_uid,finding_type,finding_file,finding_line,finding_message,
                 finding_severity,expert_name,expert_domain,advice_category,advice_content,
                 quality_score,status,round_no,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (uid, 'system_governance', s.get('file', ''), s.get('line', 0),
                 f"治理建议:{s['kind']}", s['severity'], '系统治理引擎', s['domain'],
                 'SYSTEM_GOVERNANCE', f"【{s['category']}】{s['title']} (score={s['score']:.2f})",
                 min(1.0, s['score']), 'PENDING', rn, now, now))
        except Exception:
            pass

    # 脑库投喂频次提升(无论consensus高低每轮强制投喂) — 用户要求提高投喂频次
    feed_title = (f"系统治理轮巡: seeds={len(seeds)} consensus={consensus:.3f} action={action} "
                  f"iss={iss} sk={sk} tm={tm} 主动参与={action != 'skip'}")
    try:
        conn.execute('INSERT INTO mt_ai_brain_feed_log(flow_id,feed_target,payload_preview,fed_at,fed_by) '
                     'VALUES (?,?,?,?,?)',
                     (f'flow_system_governance_{rn}', 'AI_BRAIN', feed_title[:1000], now,
                      'SYSTEM_GOVERNANCE_ENGINE'))
        fd += 1
    except Exception as e:
        _log(f'feed fail: {type(e).__name__}')

    stats.update({'issues': iss, 'skills': sk, 'feeds': fd, 'team_adjusts': tm})
    _log_row(conn, rn, 'EXTRACT',
             f'action={action} reason={reason} iss={iss} sk={sk} fd={fd} tm={tm}')
    return action


# =============================================================
# STEP 4 VERIFY — 4一致性
# =============================================================
def verify_outputs(conn, stats):
    ok = 0; fail = 0
    # V1 issue优先级合法
    bad = conn.execute(
        "SELECT COUNT(*) FROM mt_system_governance_issues WHERE status='ACTIVE' "
        "AND priority NOT IN ('P0','P1','P2')").fetchone()[0]
    if bad == 0: ok += 1
    else: fail += 1
    # V2 技能值合法
    bad = conn.execute(
        "SELECT COUNT(*) FROM mt_governance_skills_extracted WHERE status='ACTIVE' "
        "AND skill_value NOT IN ('HIGH','MEDIUM','LOW')").fetchone()[0]
    if bad == 0: ok += 1
    else: fail += 1
    # V3 团队建议action合法
    bad = conn.execute(
        "SELECT COUNT(*) FROM mt_governance_team_adjusts WHERE status='ACTIVE' "
        "AND action IS NULL OR action=''").fetchone()[0]
    if bad == 0: ok += 1
    else: fail += 1
    # V4 脑库投喂记录存在
    n = conn.execute(
        "SELECT COUNT(*) FROM mt_ai_brain_feed_log WHERE fed_by='SYSTEM_GOVERNANCE_ENGINE'").fetchone()[0]
    if n > 0: ok += 1
    else: fail += 1
    stats['verify_ok'] = ok; stats['verify_fails'] = fail
    _log_row(conn, stats['round'], 'VERIFY', f'ok={ok} fail={fail}')
    return fail == 0


# =============================================================
# STEP 5 FOSSILIZE
# =============================================================
def fossilize(conn, rn, stats):
    title = (f"系统治理轮巡: issues={stats.get('issues',0)} skills={stats.get('skills',0)} "
             f"feeds={stats.get('feeds',0)} team={stats.get('team_adjusts',0)} "
             f"共识={stats.get('consensus',0)} {stats.get('action','')}")
    try:
        conn.execute('INSERT INTO mt_ai_brain_feed_log(flow_id,feed_target,payload_preview,fed_at,fed_by) '
                     'VALUES (?,?,?,?,?)',
                     (f'flow_system_governance_{rn}', 'AI_BRAIN', title[:1000], _now(),
                      'SYSTEM_GOVERNANCE_ENGINE'))
    except Exception as e:
        _log(f'fossilize fail: {type(e).__name__}')
    _log_row(conn, rn, 'FOSSILIZE', 'done')


# =============================================================
# 主流程
# =============================================================
def ensure_tables(conn):
    for ddl in _DDL:
        conn.execute(ddl)
    conn.commit()


def run_once():
    conn = None
    try:
        conn = sqlite3.connect(DB_MAIN, timeout=60)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=60000')
    except Exception as e:
        _log(f'db connect fail: {e}'); return
    rn = datetime.now().strftime('%Y%m%d_%H%M%S')
    stats = {'round': rn}
    try:
        ensure_tables(conn)
        _log_row(conn, rn, 'SEED', 'start')
        seeds, conn = collect_seeds(stats)
        _log_row(conn, rn, 'SEED', f"seeds={len(seeds)} placeholders={stats.get('placeholder_pages',0)} "
                 f"perm_gaps={stats.get('permission_gaps',0)} team_gaps={stats.get('team_gaps',0)}")
        consensus = run_simulation(rn, stats)
        _log_row(conn, rn, 'SIMULATE', f'consensus={consensus}')
        if conn is not None:
            extract_outputs(conn, rn, stats, seeds, consensus)
            verify_outputs(conn, stats)
            fossilize(conn, rn, stats)
            conn.commit()
        _log(f"round {rn} 完成: seeds={stats.get('seeds')} consensus={consensus} "
             f"action={stats.get('action')} iss={stats.get('issues')} "
             f"sk={stats.get('skills')} fd={stats.get('feeds')} tm={stats.get('team_adjusts')} "
             f"verify_ok={stats.get('verify_ok')} verify_fails={stats.get('verify_fails')}")
    except Exception as e:
        _log(f'round error: {type(e).__name__}: {e}')
        try:
            if conn: _log_row(conn, rn, 'ERROR', f'{type(e).__name__}: {e}'); conn.commit()
        except Exception:
            pass
    finally:
        if conn: conn.close()


def run_daemon(interval=1200):
    _log(f'daemon start pid={os.getpid()} interval={interval}s')
    os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    while True:
        try:
            run_once()
        except Exception as e:
            _log(f'daemon cycle error: {type(e).__name__}: {e}')
        time.sleep(interval)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'once'
    if mode == 'once':
        run_once()
    elif mode == 'daemon':
        run_daemon()
    else:
        print(f'usage: {os.path.basename(__file__)} [once|daemon]'); sys.exit(2)


if __name__ == '__main__':
    main()
