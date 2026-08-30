#!/usr/bin/env python3
"""ai_org_growth_engine.py
=================================================================================
模拟环境驱动的 组织成长引擎（Organization Growth Engine v1.0.0）
=================================================================================
由 daemon sys_org_growth 每 1200s 轮巡调用（once 模式），六步闭环：
  1. HARVEST  吸收+采摘: 解析 mt_sandbox_outcomes（AI_SUGGESTION/CONSENSUS/RESOLUTION）
             + 读取 mt_patrol_eigenflux_suggestions 拓展类建议(FEATURE_EXPAND 已消费的复用 outcome)
             → 提炼「功能拓展域/团队配置」方案
  2. SIMULATE 模拟环境磋商: 复用 simulation_sandbox_engine（ARCH_UPGRADE 场景，
             共识 seed=轮次哈希）→ 共识分驱动 组织拓展 / 仅建议
  3. GROW 功能拓展+团队组建(双确定性创建):
             a) 功能拓展域 → 功能建议落池(带团队组建需求)
             b) 按域→对应AI员工模板 自动雇佣（INSERT ai_employees + mtscos_ai_employees
                + eigenflux_registrations + mt_ai_auto_hire_log，参考 ai_auto_hire_engine 模式）
             c) 按域→对应EigenFlux专家模板 自动邀请（INSERT eigenflux_experts
                + eigenflux_registrations(expert_type=eigenflux_expert) + mt_eigenflux_invite_log，
                领域缺员才招）
  4. VERIFY 组织一致性校验: 员工/专家唯一约束 + 注册完整性（各表记录对应） + 状态active
  5. PERSIST + FEED: mt_org_growth_log 六步留痕 + mt_ai_brain_feed_log 投喂(列名1:1)

安全约束（硬）:
  - 员工/专家创建 幂等: 雇员名+角色联合去重（唯一散列标识）
  - 邀请上限: 单轮 AI员工≤4人，EigenFlux专家≤3人，AI员工总数不超过模板池
  - 组织变更仅新增（INSERT/IGNORE），不 UPDATE/DELETE 既有员工/专家
  - 共识门槛: ARCH_UPGRADE 场景共识 ≥0.70 才真招人，否则只落建议
  - 模板池 1:1 对齐 ai_auto_hire_engine，禁止编造虚构数据源
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sqlite3
import sys
import uuid
from datetime import datetime

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
FLASK_APP_DIR = os.path.dirname(ENGINE_DIR)
PROJECT_ROOT = os.path.dirname(FLASK_APP_DIR)
APP_DB = os.path.join(PROJECT_ROOT, '_runtime', 'databases', 'Database', 'app.db')
ENG_DB = os.path.join(ENGINE_DIR, 'app.db')
GIT_AUTHOR_NAME = 'Mr.W'
GIT_AUTHOR_EMAIL = 'wuchenghao15@users.noreply.github.com'
LOG = 'ORG-GROWTH'

# ─────────────────────── 决策常量（1:1 真源，AST 提取做千轮测试） ───────────────────────
_MIN_CONSENSUS = 0.65
_MAX_EMPLOYEES_PER_ROUND = 4
_MAX_EXPERTS_PER_ROUND = 3
_OUTCOME_KINDS = ('AI_SUGGESTION', 'CONSENSUS', 'RESOLUTION', 'BRAIN_FEED')
_DOMAINS = ('ARCHITECTURE', 'SECURITY', 'EDUCATION', 'DATABASE', 'DEVOPS',
            'FRONTEND', 'BACKEND', 'IOT', 'ALGORITHM', 'DATA')
_DOMAIN_PATTERNS = {
    'ARCHITECTURE': ('架构', 'archi', '系统设计', '升级', 'flow', '部署'),
    'SECURITY': ('安全', 'secure', '权限', '加密', '防盗链', '绑定'),
    'EDUCATION': ('教育', '题库', '教辅', '听力', '母题', '学习', 'k12', 'tutor'),
    'DATABASE': ('数据库', 'db', 'sharding', 'migration', '备份', 'sql'),
    'DEVOPS': ('运维', 'devops', 'git', '监控', '巡检', 'daemon', '轮巡', '部署'),
    'FRONTEND': ('前端', 'ui', 'css', 'template', '页面', 'html'),
    'BACKEND': ('后端', 'api', '路由', 'service', 'flask', 'server'),
    'IOT': ('物联网', 'iot', 'arduino', '硬件', 'sensor', 'serial'),
    'ALGORITHM': ('算法', 'algorithm', '推理', '向量', '模型', 'ml'),
    'DATA': ('数据', 'data', '统计', '分析', '报表'),
}
_UPLOAD_SKIP_DIRS = ('backups', 'Database_Backups', 'recovery_snapshots', '__pycache__', '.git',
                     'node_modules', 'venv', '.venv', '_tmp', 'tmp', 'git_push_ws',
                     'suggested_repair_backups', 'feature_evolution_sandbox',
                     'org_growth_sandbox', 'Database', '_output', '_runtime')

# ────────── AI 员工模板池（扩展至覆盖 10 域 + 已有角色，1:1 对齐 ai_auto_hire_engine 风格） ──────────
AI_EMPLOYEE_TEMPLATES = [
    # 新域团队：新增
    {"role": "org_growth_officer",    "name": "组织成长官",
     "specialties": "功能拓展,团队组建,组织架构规划,人员编制,模拟环境决策",
     "description": "基于模拟环境磋商与拓展建议，规划功能拓展域并组建对应AI团队",
     "model_version": "OrgGrowth-1.0"},
    {"role": "architecture_planner",  "name": "架构规划师",
     "specialties": "系统架构设计,升级方案,模块解耦,接口契约,性能评估",
     "description": "架构域拓展方案输出与评审，对应EigenFlux架构专家协作",
     "model_version": "ArchPlanner-1.0"},
    {"role": "security_growth_auditor", "name": "安全扩展审查员",
     "specialties": "新功能安全审查,权限边界,加密策略,防盗链,合规审计",
     "description": "为新增功能域做 fail-safe 安全把关，对接安全专家团队",
     "model_version": "SecAudit-1.1"},
    {"role": "education_curricular",  "name": "教育课程官",
     "specialties": "课程设计,五域拓展,历年题策划,母题更新,听力题脚本",
     "description": "教育域功能拓展与教学团队扩展对接",
     "model_version": "EduCurric-1.0"},
    {"role": "database_evolution",    "name": "数据库演进官",
     "specialties": "schema演进,备份策略,分库分表,迁移脚本,索引优化",
     "description": "功能拓展后数据库结构与容量评估",
     "model_version": "DBEvo-1.0"},
    {"role": "devops_scheduler",      "name": "运维排程师",
     "specialties": "daemon挂载,轮巡周期调度,git上传流水线,隔离仓管理",
     "description": "新功能上线后的自动化部署与排程",
     "model_version": "DevOpsSch-1.0"},
    {"role": "frontend_experience",   "name": "前端体验官",
     "specialties": "UX流程,响应式布局,Element Plus扩展,动画,可视化",
     "description": "功能域对应的前端页面和交互扩展",
     "model_version": "FrontExp-1.0"},
    {"role": "backend_api_growth",    "name": "后端API扩展师",
     "specialties": "Flask蓝图,权限装饰器,API契约,中间件链路,返回格式",
     "description": "新增功能的后端路由与服务扩展",
     "model_version": "BackAPI-1.0"},
    {"role": "iot_integration",       "name": "IoT集成专员",
     "specialties": "Arduino扩展,硬件驱动,设备树,串口通信,传感器协议",
     "description": "IoT域功能拓展与硬件端扩展",
     "model_version": "IoTInt-1.0"},
    {"role": "algorithm_engineer",    "name": "算法工程师",
     "specialties": "决策算法,向量检索,推理调度,模型微调钩子,数据清洗",
     "description": "算法域功能扩展，对接本地推理引擎与脑库",
     "model_version": "AlgoEng-1.0"},
    {"role": "data_analyst",          "name": "数据分析师",
     "specialties": "五域数据透视,报表生成,统计分析,异常分布,新鲜度建模",
     "description": "数据域功能扩展，对接题库/用户/引擎遥测数据",
     "model_version": "DataAn-1.0"},
    # 基础角色（若缺员补全）
    {"role": "patrol_inspector",      "name": "代码巡检员",
     "specialties": "Python语法检查,代码质量扫描,安全漏洞检测",
     "description": "源码巡逻队核心成员（巡检岗）", "model_version": "Patrol-2.0"},
    {"role": "auto_repair",           "name": "自动修复工程师",
     "specialties": "Bug修复,代码重构,性能优化,回归测试",
     "description": "AI建议修复工程师（自动修复岗）", "model_version": "AutoRepair-2.0"},
    {"role": "deep_inspector",        "name": "深度巡检员",
     "specialties": "页面路由检查,API完整性验证,数据库一致性",
     "description": "深度巡检岗", "model_version": "DeepIns-2.0"},
]

# ────────── EigenFlux 专家模板池（10 域 × 等级：每个域 1 名首席专家） ──────────
EIGENFLUX_EXPERT_TEMPLATES = [
    {"domain": "architecture",  "role": "ARCHITECT", "role_cn": "架构专家",
     "domain_cn": "架构",  "name": "Eigen-架构首席", "level": "SENIOR",
     "skills": "系统架构,模块解耦,接口契约,性能调优,升级评估"},
    {"domain": "security",    "role": "SECURITY",   "role_cn": "安全专家",
     "domain_cn": "安全",  "name": "Eigen-安全首席", "level": "SENIOR",
     "skills": "权限体系,加密审计,防盗链,合规,注入防御"},
    {"domain": "education",   "role": "EDUCATION",  "role_cn": "教育专家",
     "domain_cn": "教育",  "name": "Eigen-教育首席", "level": "SENIOR",
     "skills": "课程体系,五域同步,母题接替,听力题,新鲜度模型"},
    {"domain": "database",    "role": "DATABASE",   "role_cn": "DBA专家",
     "domain_cn": "数据库", "name": "Eigen-DBA首席", "level": "SENIOR",
     "skills": "SQLite优化,分库分表,备份恢复,迁移审计,索引"},
    {"domain": "devops",      "role": "DEVOPS",     "role_cn": "运维专家",
     "domain_cn": "运维",  "name": "Eigen-运维首席", "level": "SENIOR",
     "skills": "daemon部署,cron保活,git流水线,隔离仓,监控健康度"},
    {"domain": "frontend",    "role": "FRONTEND",   "role_cn": "前端专家",
     "domain_cn": "前端",  "name": "Eigen-前端首席", "level": "SENIOR",
     "skills": "Element Plus扩展,模板,响应式,动画,性能"},
    {"domain": "backend",     "role": "BACKEND",    "role_cn": "后端专家",
     "domain_cn": "后端",  "name": "Eigen-后端首席", "level": "SENIOR",
     "skills": "Flask蓝图,中间件,权限装饰器,API契约,数据库服务层"},
    {"domain": "iot",         "role": "IOT",        "role_cn": "IoT专家",
     "domain_cn": "IoT",   "name": "Eigen-IoT首席",  "level": "SENIOR",
     "skills": "Arduino扩展,串口,VID:PID,板卡驱动,传感器协议"},
    {"domain": "algorithm",   "role": "AI_ALGO",    "role_cn": "AI算法专家",
     "domain_cn": "AI算法", "name": "Eigen-算法首席", "level": "SENIOR",
     "skills": "决策算法,向量检索,本地推理,模型微调,数据清洗"},
    {"domain": "ai_ml",       "role": "AI_ML",      "role_cn": "AI/ML专家",
     "domain_cn": "AI/ML", "name": "Eigen-AI/ML首席", "level": "SENIOR",
     "skills": "大模型训练,微调钩子,推理调度,提示工程,脑库投喂"},
    {"domain": "data",        "role": "DATA",       "role_cn": "数据专家",
     "domain_cn": "数据",  "name": "Eigen-数据首席", "level": "SENIOR",
     "skills": "统计分析,报表,异常检测,新鲜度评估,知识图谱"},
    {"domain": "governance",  "role": "GOVERNANCE", "role_cn": "治理专家",
     "domain_cn": "治理",  "name": "Eigen-治理首席", "level": "SENIOR",
     "skills": "规则治理,合规审计,§14流程审计,7步审批,版本管控"},
]


# ─────────────────────── 纯函数决策核心 ───────────────────────
def classify_domain(text):
    """域识别（纯函数，按关键词打分，取最高分域；无命中→ARCHITECTURE）。
    大小写不敏感；所有关键词为字符串片段匹配。"""
    if text is None:
        return 'ARCHITECTURE'
    s = str(text).lower()
    scores = {}
    for d, keys in _DOMAIN_PATTERNS.items():
        scores[d] = sum(1 for k in keys if k.lower() in s)
    best_d, best_s = 'ARCHITECTURE', 0
    for d, sc in scores.items():
        if sc > best_s:
            best_s = sc; best_d = d
    return best_d


def grow_decision(consensus, require, employee_gaps, expert_gaps):
    """组织拓展决策（纯函数）。返回 (action, reason)；action ∈ 'grow' | 'advise_only' | 'skip'。
    硬优先级: 共识合法性→门槛→双缺口均0只建议→grow。"""
    try:
        c = float(consensus); r = float(require)
    except (TypeError, ValueError):
        return ('skip', 'bad-consensus')
    if c != c or c < 0 or c > 1:
        return ('skip', 'consensus-out-of-range')
    if r != r or r < 0 or r > 1:
        return ('skip', 'bad-require')
    if c < r:
        return ('advise_only', 'consensus-%.2f<%.2f' % (c, r))
    try:
        eg = int(employee_gaps); xg = int(expert_gaps)
    except (TypeError, ValueError):
        return ('skip', 'bad-gaps')
    if eg <= 0 and xg <= 0:
        return ('advise_only', 'no-gaps')
    return ('grow', 'gaps=e%d/x%d consensus=%.2f>=%.2f' % (eg, xg, c, r))


def employee_identity(name, role):
    """员工身份确定性标识（纯函数）：name+role 哈希，INSERT OR IGNORE 去重。"""
    return 'EMP-%s' % hashlib.md5(f'{name}|{role}'.encode()).hexdigest()[:14]


def expert_identity(domain, role):
    """专家身份确定性标识（纯函数）：domain+role 哈希。"""
    return 'EXP-%s' % hashlib.md5(f'{domain}|{role}'.encode()).hexdigest()[:14]


def round_cap(current, limit):
    """单轮创建上限（纯函数）：已创建 current 后，本轮可新创建数量 = max(0, limit - current)
    负数/非法→0。"""
    try:
        cur = int(current); lim = int(limit)
    except (TypeError, ValueError):
        return 0
    if cur < 0 or lim < 0:
        return 0
    return max(0, lim - cur)


def eligibility_ok(target, name, role):
    """组织创建前置资格（纯函数）：目标在域白名单内；name/role 非空且无 SKIP 敏感目录段。"""
    if target not in _DOMAINS:
        return False
    n = (name or '').strip(); r = (role or '').strip()
    if not n or not r:
        return False
    for seg in (n + '/' + r).lower().split('/'):
        if seg in _UPLOAD_SKIP_DIRS:
            return False
    return True


def consensus_to_size_bucket(consensus):
    """共识分档→扩展规模桶（纯函数）：>=0.85→大型 / >=0.65→中型 / 其余→小型。
    非法→小型（fail-safe）。"""
    try:
        c = float(consensus)
    except (TypeError, ValueError):
        return 'SMALL'
    if c != c:
        return 'SMALL'
    if c >= 0.85:
        return 'LARGE'
    if c >= 0.65:
        return 'MEDIUM'
    return 'SMALL'


def hire_wellformed(name, role, specialties, status):
    """员工模板格式校验（纯函数）：四字段非空 + status=active/ACTIVE 之一。"""
    if not (name and role and specialties and status):
        return False
    return str(status).lower() == 'active'


def invite_wellformed(name, domain, role, level, skills):
    """专家模板格式校验（纯函数）：五字段非空。"""
    return bool(name and domain and role and level and skills)


# ─────────────────────── 工具 ───────────────────────
def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _log(msg):
    line = f'[{_now()}] [{LOG}] {msg}'
    print(line, flush=True)
    try:
        os.makedirs(os.path.join(PROJECT_ROOT, '_runtime', 'logs'), exist_ok=True)
        with open(os.path.join(PROJECT_ROOT, '_runtime', 'logs', 'org_growth_engine.log'),
                  'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def _main_conn():
    conn = sqlite3.connect(APP_DB, timeout=60, isolation_level=None)
    conn.execute('PRAGMA busy_timeout=60000')
    return conn


def _ensure_tables(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS mt_org_growth_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        round_no TEXT NOT NULL, step TEXT NOT NULL, target TEXT,
        detail TEXT, created_at TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS mt_org_growth_teams (
        team_id TEXT PRIMARY KEY, domain TEXT NOT NULL, size_bucket TEXT,
        employee_count INTEGER DEFAULT 0, expert_count INTEGER DEFAULT 0,
        round_no TEXT, consensus REAL, created_at TEXT, detail TEXT)''')


def _log_row(conn, rn, step, target, detail):
    try:
        conn.execute('INSERT INTO mt_org_growth_log(round_no,step,target,detail,created_at) VALUES (?,?,?,?,?)',
                     (rn, step, target or '', (detail or '')[:2000], _now()))
    except Exception as e:
        _log(f'log_row失败 {step}: {e}')


# ─────────────────────── 1. HARVEST 采摘模拟产出 + 建议 ───────────────────────
def harvest_growth_plans(conn, rn, stats):
    """解析模拟环境 outcome + 拓展建议，提炼「域-团队规模-需求」清单。"""
    plans = []
    detail = ''
    try:
        eng = sqlite3.connect(f'file:{ENG_DB}?mode=ro', uri=True, timeout=30)
        try:
            rows = eng.execute(
                """SELECT outcome_type, outcome_title, outcome_body_json, feasibility, value_score
                   FROM mt_sandbox_outcomes WHERE outcome_type IN (?,?,?,?) ORDER BY outcome_id DESC LIMIT 60""",
                _OUTCOME_KINDS).fetchall()
        finally:
            eng.close()
        # 拓展建议（即使已消费，也可作为域需求输入）
        fev_rows = conn.execute(
            """SELECT finding_file, advice_content FROM mt_patrol_eigenflux_suggestions
               WHERE suggestion_uid LIKE 'FEV-%' LIMIT 40""").fetchall()
        seen = set()
        for ot, title, body, feas, vs in rows:
            d = classify_domain((title or '') + ' ' + (body or ''))
            key = (d, ot, (title or '')[:40])
            if key in seen:
                continue
            seen.add(key)
            plans.append({'domain': d, 'source': f'sandbox:{ot}', 'title': (title or '')[:120],
                          'feasibility': feas, 'value_score': vs})
        for ff, content in fev_rows:
            d = classify_domain((ff or '') + ' ' + (content or ''))
            key = ('FEV', d, ff)
            if key in seen:
                continue
            seen.add(key)
            plans.append({'domain': d, 'source': 'fev-expand', 'title': ff,
                          'feasibility': 0.70, 'value_score': 0.70})
        # 汇总按域的建议数量
        import collections
        dcount = collections.Counter(p['domain'] for p in plans)
        detail = f'plans={len(plans)} domains_covered={len(dcount)} top={dcount.most_common(5)}'
    except Exception as e:
        detail = f'error:{type(e).__name__}: {e}'[:200]
    _log_row(conn, rn, 'HARVEST', 'growth_plans', detail)
    stats['harvest'] = {'plans': len(plans)}
    stats['plans'] = plans
    return plans


# ─────────────────────── 2. SIMULATE 模拟磋商 ARCH_UPGRADE ───────────────────────
def run_arch_upgrade_simulation(conn, rn, stats):
    """跑 ARCH_UPGRADE 场景，返回共识分。"""
    consensus = None; detail = ''
    try:
        sys.path.insert(0, ENGINE_DIR)
        from simulation_sandbox_engine import SimulationSandboxEngine
        seed = int(hashlib.md5(rn.encode()).hexdigest()[:8], 16)
        eng = SimulationSandboxEngine()
        r = eng.run('ARCH_UPGRADE', actor_count=8, seed=seed)
        consensus = float(r.get('consensus', 0.0))
        detail = f'session={r.get("session_id","")[:40]} consensus={consensus}'
    except SystemExit as e:
        detail = f'arch-upgrade exit:{e}'[:200]
    except Exception as e:
        detail = f'arch-upgrade error:{type(e).__name__}: {e}'[:200]
    _log_row(conn, rn, 'SIMULATE', 'ARCH_UPGRADE', detail)
    stats['consensus'] = consensus
    return consensus


# ─────────────────────── 3. GROW 功能拓展 + 团队组建 ───────────────────────
def grow_org(conn, rn, stats, plans, consensus):
    """按决策执行：功能建议落池 + AI员工雇佣 + EigenFlux专家邀请。"""
    action, reason = grow_decision(consensus, _MIN_CONSENSUS, 0, 0)
    # 真正缺口检测：基于 plans 的域需求 vs 模板池已存在员工/专家
    plan_domains = sorted({p['domain'] for p in plans})
    emp_gaps, exp_gaps = _detect_gaps(conn, plan_domains)
    action, reason = grow_decision(consensus, _MIN_CONSENSUS, len(emp_gaps), len(exp_gaps))
    hired = 0; invited = 0; expanded = 0; verify_fails = 0
    stats['teams'] = []
    try:
        # a) 功能拓展域 → 建议落池（uid幂等）
        for p in plans:
            if _write_domain_expansion_advice(conn, rn, p):
                expanded += 1
        if action == 'grow':
            now = _now()
            # b) AI员工雇佣（单轮上限，幂等）
            emp_targets = [t for t in AI_EMPLOYEE_TEMPLATES if t["role"] in emp_gaps]
            emp_limit = round_cap(hired, _MAX_EMPLOYEES_PER_ROUND)
            emp_targets = emp_targets[:max(0, _MAX_EMPLOYEES_PER_ROUND - hired)]
            for tpl in emp_targets:
                if not eligibility_ok(classify_domain(tpl["name"] + " " + tpl["specialties"]),
                                      tpl["name"], tpl["role"]):
                    continue
                if not hire_wellformed(tpl["name"], tpl["role"], tpl["specialties"], "active"):
                    continue
                ok = _hire_employee(conn, rn, tpl, now)
                if ok: hired += 1
                else: verify_fails += 1
            # c) EigenFlux专家邀请（单轮上限，幂等）
            exp_targets = [t for t in EIGENFLUX_EXPERT_TEMPLATES if t["domain"].upper() in exp_gaps]
            exp_targets = exp_targets[:_MAX_EXPERTS_PER_ROUND]
            for tpl in exp_targets:
                if not invite_wellformed(tpl["name"], tpl["domain"], tpl["role"], tpl["level"], tpl["skills"]):
                    continue
                ok = _invite_expert(conn, rn, tpl, now)
                if ok: invited += 1
                else: verify_fails += 1
        # 团队组建记录
        bucket = consensus_to_size_bucket(consensus)
        for d in plan_domains:
            try:
                tid = f'TEAM-{rn}-{d}-{hashlib.md5(d.encode()).hexdigest()[:6]}'
                conn.execute("""INSERT OR IGNORE INTO mt_org_growth_teams
                    (team_id,domain,size_bucket,employee_count,expert_count,round_no,consensus,created_at,detail)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (tid, d, bucket, 1 if d in _DEMAND_TO_ROLE else 0, 1, rn,
                     consensus or 0.0, now if action == 'grow' else _now(),
                     f'action={action} reason={reason}'))
                stats['teams'].append(tid)
            except Exception:
                pass
    except Exception as e:
        _log(f'grow异常: {e}')
    _log_row(conn, rn, 'GROW', 'team_expansion',
             f'action={action} reason={reason} expanded={expanded} hired={hired} invited={invited} verify_fails={verify_fails}')
    stats['action'] = action
    stats['hired'] = hired; stats['invited'] = invited; stats['expanded'] = expanded
    return hired + invited + expanded


# 域 → 对应角色映射（demand侧）
_DEMAND_TO_ROLE = {}  # 避免全局污染，本函数作用域初始化


def _detect_gaps(conn, domains):
    """真实缺口检测：员工缺口=模板中该域对应员工未存在；专家缺口=域缺EigenFlux专家。"""
    existing_roles = set()
    try:
        rows = conn.execute("SELECT role FROM mtscos_ai_employees WHERE status='ACTIVE'").fetchall()
        for r in rows:
            existing_roles.add(r[0])
    except Exception:
        pass
    try:
        rows = conn.execute("SELECT specialties FROM ai_employees WHERE status='active'").fetchall()
        for r in rows:
            sp = (r[0] or '').lower()
            for t in AI_EMPLOYEE_TEMPLATES:
                if t['role'].lower() in sp or t['name'] in (r[0] or ''):
                    existing_roles.add(t['role'])
    except Exception:
        pass
    dom_to_role = {
        'ARCHITECTURE': ['architecture_planner', 'org_growth_officer'],
        'SECURITY': ['security_growth_auditor'],
        'EDUCATION': ['education_curricular'],
        'DATABASE': ['database_evolution'],
        'DEVOPS': ['devops_scheduler'],
        'FRONTEND': ['frontend_experience'],
        'BACKEND': ['backend_api_growth'],
        'IOT': ['iot_integration'],
        'ALGORITHM': ['algorithm_engineer'],
        'DATA': ['data_analyst'],
    }
    emp_gaps = []
    for d in domains:
        for role in dom_to_role.get(d, []):
            if role not in existing_roles and role not in emp_gaps:
                emp_gaps.append(role)
            _DEMAND_TO_ROLE[d] = role  # 供团队记录用
    existing_domains = set()
    try:
        rows = conn.execute("SELECT domain FROM eigenflux_experts WHERE status='active'").fetchall()
        for r in rows:
            existing_domains.add((r[0] or '').upper())
    except Exception:
        pass
    exp_gaps = [d for d in domains if d not in existing_domains]
    return emp_gaps, exp_gaps


def _write_domain_expansion_advice(conn, rn, plan):
    """功能拓展域建议落池（uid幂等）。"""
    try:
        d = plan['domain']
        title = str(plan.get('title', ''))[:80]
        uid = 'GROW-' + hashlib.md5(f'{d}|{title}'.encode()).hexdigest()[:14]
        if conn.execute('SELECT 1 FROM mt_patrol_eigenflux_suggestions WHERE suggestion_uid=?', (uid,)).fetchone():
            return False
        now = _now()
        msg = f'{d}域功能拓展({plan.get("source")})'
        content = f'基于模拟环境磋商(可行性={plan.get("feasibility")} 价值分={plan.get("value_score")})，需拓展{title}并组建对应AI团队'
        conn.execute("""INSERT INTO mt_patrol_eigenflux_suggestions
            (suggestion_uid, finding_type, finding_file, finding_line, finding_message,
             finding_severity, expert_name, expert_domain, advice_category, advice_content,
             quality_score, status, round_no, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (uid, 'domain_expansion', f'GROW-{d}', 0, msg,
             'LOW', 'AI组织成长官', d, 'DOMAIN_EXPANSION', content,
             min(1.0, (plan.get('feasibility') or 0.7) * 0.5 + (plan.get('value_score') or 0.7) * 0.5),
             'PENDING', rn, now, now))
        return True
    except Exception as e:
        _log(f'domain advice落池失败: {e}')
        return False


def _hire_employee(conn, rn, tpl, now):
    """AI员工四表写入（幂等，AI员工+MTS员工+Eigen注册+雇佣日志）。"""
    uid_prefix = employee_identity(tpl["name"], tpl["role"])
    emp_id = uid_prefix
    uid = f'MTS:{emp_id}'
    try:
        conn.execute("""INSERT OR IGNORE INTO ai_employees
            (name, employee_code, description, capabilities, specialties, status,
             accuracy, total_tasks, successful_fixes, failed_fixes,
             knowledge_base_size, model_version, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (tpl["name"], uid, tpl["description"], tpl["specialties"],
             tpl["role"] + "," + tpl["specialties"], "active", 0.85, 0, 0, 0, 100,
             tpl["model_version"], now, now))
        conn.execute("""INSERT OR IGNORE INTO mtscos_ai_employees
            (uid, name, role, status, created_at, specialties, description, model_version, registered_via, is_active)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (uid, tpl["name"], tpl["role"], "ACTIVE", now,
             tpl["specialties"], tpl["description"], tpl["model_version"],
             "ORG_GROWTH_ENGINE", 1))
        conn.execute("""INSERT OR IGNORE INTO eigenflux_registrations
            (employee_id, employee_name, employee_type, registration_status,
             last_heartbeat, created_at, updated_at, expert_domain)
            VALUES (?,?,?,?,?,?,?,?)""",
            (uid, tpl["name"], "mtscos_ai_employee", "active", now, now, now,
             classify_domain(tpl["name"] + " " + tpl["specialties"]).lower()))
        hire_id = "HIRE-%s" % uuid.uuid4().hex[:10]
        conn.execute("""INSERT OR IGNORE INTO mt_ai_auto_hire_log
            (hire_id, hire_type, employee_name, employee_role, source, details_json, hired_at)
            VALUES (?,?,?,?,?,?,?)""",
            (hire_id, "AI_EMPLOYEE", tpl["name"], tpl["role"],
             "ORG_GROWTH_ENGINE",
             json.dumps({"specialties": tpl["specialties"], "model": tpl["model_version"]}, ensure_ascii=False),
             now))
        # 一致性校验（三表都存在）
        r1 = conn.execute("SELECT COUNT(*) FROM ai_employees WHERE employee_code=?", (uid,)).fetchone()[0]
        r2 = conn.execute("SELECT COUNT(*) FROM mtscos_ai_employees WHERE uid=?", (uid,)).fetchone()[0]
        r3 = conn.execute("SELECT COUNT(*) FROM eigenflux_registrations WHERE employee_id=?", (uid,)).fetchone()[0]
        if r1 < 1 or r2 < 1 or r3 < 1:
            return False
        return True
    except Exception as e:
        _log(f'hire失败 {tpl["name"]}: {e}')
        return False


def _invite_expert(conn, rn, tpl, now):
    """EigenFlux专家 两表写入 + 邀请日志（幂等）。"""
    eid = expert_identity(tpl["domain"], tpl["role"])
    try:
        conn.execute("""INSERT OR IGNORE INTO eigenflux_experts
            (expert_id, name, role, role_cn, domain, domain_cn, level, skills, status, created_at, last_heartbeat)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (eid, tpl["name"], tpl["role"], tpl["role_cn"],
             tpl["domain"], tpl["domain_cn"], tpl["level"], tpl["skills"],
             "active", now, now))
        conn.execute("""INSERT OR IGNORE INTO eigenflux_registrations
            (employee_id, employee_name, employee_type, registration_status,
             last_heartbeat, created_at, updated_at, expert_domain, expert_level)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (eid, tpl["name"], "eigenflux_expert", "active", now, now, now,
             tpl["domain"], tpl["level"]))
        conn.execute("""INSERT OR IGNORE INTO mt_eigenflux_invite_log
            (invite_id, expert_name, expert_domain, expert_level, source, details_json, invited_at)
            VALUES (?,?,?,?,?,?,?)""",
            ("INVITE-" + uuid.uuid4().hex[:10], tpl["name"], tpl["domain"], tpl["level"],
             "ORG_GROWTH_ENGINE",
             json.dumps({"role_cn": tpl["role_cn"], "domain_cn": tpl["domain_cn"], "skills": tpl["skills"]}, ensure_ascii=False),
             now))
        r1 = conn.execute("SELECT COUNT(*) FROM eigenflux_experts WHERE expert_id=?", (eid,)).fetchone()[0]
        r2 = conn.execute("SELECT COUNT(*) FROM eigenflux_registrations WHERE employee_id=?", (eid,)).fetchone()[0]
        return r1 >= 1 and r2 >= 1
    except Exception as e:
        _log(f'invite失败 {tpl["name"]}: {e}')
        return False


# ─────────────────────── 4. VERIFY 一致性校验 ───────────────────────
def verify_consistency(conn, rn, stats):
    """校验员工/专家 三表/两表一致性，返回通过数量。"""
    ok = 0
    try:
        # 员工三表一致性：mtscos 存在的 active 员工 → eigenflux_registration 注册
        for r in conn.execute("SELECT uid, name FROM mtscos_ai_employees WHERE status='ACTIVE' AND registered_via='ORG_GROWTH_ENGINE'"):
            cnt = conn.execute("SELECT COUNT(*) FROM eigenflux_registrations WHERE employee_id=? AND registration_status='active'", (r[0],)).fetchone()[0]
            if cnt >= 1:
                ok += 1
        # 专家两表一致性
        for r in conn.execute("SELECT expert_id FROM eigenflux_experts WHERE status='active'"):
            cnt = conn.execute("SELECT COUNT(*) FROM eigenflux_registrations WHERE employee_id=? AND registration_status='active'", (r[0],)).fetchone()[0]
            if cnt >= 1:
                ok += 1
    except Exception as e:
        _log(f'verify异常: {e}')
    _log_row(conn, rn, 'VERIFY', 'org_consistency', f'consistent_rows={ok}')
    stats['verify'] = ok
    return ok


# ─────────────────────── 5+6. PERSIST 投喂 ───────────────────────
def persist_and_feed(conn, rn, stats):
    try:
        conn.execute("""INSERT INTO mt_ai_brain_feed_log(flow_id, feed_target, payload_preview, fed_at, fed_by)
                        VALUES (?,?,?,?,?)""",
                     (f'{LOG}-{rn}', 'AI脑库/组织成长',
                      json.dumps({k: v for k, v in stats.items() if k != 'plans'}, ensure_ascii=False),
                      _now(), 'ORG-GROWTH'))
    except Exception as e:
        _log(f'脑库投喂失败: {e}')
    _log_row(conn, rn, 'PERSIST', 'brain_feed', 'done')


# ─────────────────────── 主流程 ───────────────────────
def run_once():
    rn = datetime.now().strftime('%Y%m%d_%H%M%S')
    stats = {'round': rn}
    conn = _main_conn()
    try:
        _ensure_tables(conn)
        plans = harvest_growth_plans(conn, rn, stats)
        consensus = run_arch_upgrade_simulation(conn, rn, stats)
        created = grow_org(conn, rn, stats, plans, consensus)
        verify_consistency(conn, rn, stats)
        persist_and_feed(conn, rn, stats)
        _log(f'round {rn} 完成: plans={len(plans)} consensus={consensus} action={stats.get("action")} '
             f'expanded={stats.get("expanded")} hired={stats.get("hired")} invited={stats.get("invited")} verify_ok={stats.get("verify")}')
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
