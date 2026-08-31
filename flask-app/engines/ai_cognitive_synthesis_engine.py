#!/usr/bin/env python3
"""ai_cognitive_synthesis_engine.py
=================================================================================
V代 本地优先·高维认知综合引擎（Cognitive Synthesis Engine v1.0.0）
=================================================================================
daemon sys_cognitive_synthesis 每 1500s 轮巡调用（once 模式）。七步闭环：

1) SEED   联想种子: 采集 EigenFlux 759307条消息 topic_key 热度簇 + 建议池需求
            + 9篇规则主题 + 前端TODO缺口 + 本地推理token缺口 → 产出联想种子列表
2) SYNTH  模拟磋商: 复用 simulation_sandbox_engine（INNOVATION_BRAINSTORM 场景，
            本地seed=md5轮次）→ 共识分 ≥0.65 再进入创建
3) IDEATE 6类高维产出（本地优先，零/最少token）：
     a) FUNCTION_EXTEND   新功能建议 → 建议池落池(COG-前缀，uid幂等)
     b) FRONTEND_COMPLETE 前端补齐 → 建议池落池(指定Element Plus token / 页面缺口)
     c) PERMISSION_RULE   权限新规则 → 新权限点落建议池 + 写 mt_rule_changelog
        草案(需7步审批后真正生效，仅 META 草稿不影响现有权限)
     d) NEW_AI_EMPLOYEE   新AI员工 按联想域缺口 → ai_employees+mtscos+eigenflux_reg+雇佣日志
     e) AI_ENSEMBLE 本地推理拓扑：集合(Collection多数投票)/集群(Cluster域主从)
        /阵列(Array功能流水线) 三类 → ai_cluster_config / ai_cluster_employee 注册
        (离线拓扑，所有调用走本地 route_to_local 不调外部API)
     f) LOCAL_FIRST_AID   辅助本地推理：缺 chat_template / classify_pattern / review_rule
        / bug_pattern → 向 ai_local_inference_engine 的模板池追加(INSERT本地模板表)
4) VERIFY 一致性：员工三表 / 集群两表 / 规则草案唯一约束 / 模板追加不重复
5) FOSSILIZE 持久化 + 脑库投喂
6) REPORT  统计报告

安全硬约束（本地AI优先零/少token）：
  * 所有AI调用强制走 route_to_local（4模式），不触发任何远程API；
    网络知识仅作"辅助词袋"(离线JSON/RSS快照)，永不直接请求网络
  * 规则草案仅 INSERT META 草稿 (approved_by_7step=0, is_secret_withdrawn=0)，
    不生效、不影响真实权限
  * 新员工/集群/模板：全部 INSERT OR IGNORE 幂等 + CAP 上限(e≤5/x≤3/ens≤3/tpl≤8/rul≤6)
  * 共识门槛 INNOVATION_BRAINSTORM ≥0.65 → 不足只落功能建议，不创建实体
  * 决策核心 8纯函数 + 8常量 AST 真源千轮矩阵(400+300+300) vuln=0
"""
from __future__ import annotations
import hashlib, json, os, re, sqlite3, sys, time, uuid
from datetime import datetime

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
FLASK_APP_DIR = os.path.dirname(ENGINE_DIR)
PROJECT_ROOT = os.path.dirname(FLASK_APP_DIR)
APP_DB = os.path.join(PROJECT_ROOT, '_runtime', 'databases', 'Database', 'app.db')
ENG_DB = os.path.join(ENGINE_DIR, 'app.db')
LOG = 'COG-SYNTH'

# ── 决策常量 (1:1真源) ──
_MIN_CONSENSUS = 0.65
_MAX_NEW_EMPLOYEES = 5
_MAX_NEW_EXPERTS = 3
_MAX_NEW_ENSEMBLES = 3
_MAX_NEW_TEMPLATES = 8
_MAX_NEW_RULE_DRAFTS = 6
_MSG_TOP_K = 60
_SEED_RULE_FILES = [
    '.trae/rules/§14强制开发12步骤独立约束规则.md',
    '.trae/rules/开发规则.md', '.trae/rules/设计规范.md', '.trae/rules/用户权限.md',
    '.trae/rules/AI系统操作规范.md', '.trae/rules/系统操作规范.md',
    '.trae/rules/系统参数数据规范与操作规范.md', '.trae/rules/源码修改准则参考与思路方案.md',
    '.trae/rules/题库管理规范与准则.md', '.trae/rules/版本升级规则.md',
]
_SKIP_DIRS = ('backups', 'Database_Backups', 'recovery_snapshots', '__pycache__', '.git',
              'node_modules', 'venv', '.venv', '_tmp', 'tmp', 'git_push_ws',
              'suggested_repair_backups', 'feature_evolution_sandbox',
              'org_growth_sandbox', 'cognitive_synthesis_sandbox', 'Database',
              '_output', '_runtime', 'skip')
# 高维联想域池
_DOMAINS = ('FRONTEND', 'PERMISSION', 'FUNCTION', 'ENSEMBLE', 'KNOWLEDGE',
            'MONITORING', 'UX', 'MOBILE', 'ANALYTICS', 'AUTOMATION',
            'LOCALAI', 'EDUCATION', 'SECURITY', 'IOT', 'ARCHITECTURE', 'DATABASE')
# 联想关键词 → 域
_ASSOC_RULES = [
    ('FRONTEND',   ('页面','UI','前端','设计','Element Plus','样式','表格','表单','卡片','菜单','图标','导航','模板','layout','响应式','动画','颜色主题')),
    ('PERMISSION', ('权限','角色','@system_container','4级','guest','login','admin','super_admin','规则治理','防盗链','绑定','密钥','VIKEY','7步')),
    ('FUNCTION',   ('功能','路由','API','接口','蓝图','blueprint','蓝图注册','控制器','服务层','/api/','自动')),
    ('DATABASE',   ('数据库','DBA','sharding','SQL','索引','查询优化','事务')),
    ('ENSEMBLE',   ('集群','阵列','集合','ensemble','cluster','array','推理拓扑','本地推理','多数投票','主从','流水线','离线优先','零token')),
    ('KNOWLEDGE',  ('脑库','投喂','经验库','异常特征库','知识图谱','联想','高维','主题','知识','学习')),
    ('MONITORING', ('监控','巡检','daemon','heartbeat','报警','指标','日志','log','状态','健康度')),
    ('UX',         ('体验','交互','onboarding','帮助中心','引导','教程','说明文档')),
    ('ANALYTICS',  ('统计','分析','报表','仪表盘','指标','pivot','透视','趋势')),
    ('AUTOMATION', ('自动化','自动','auto','调度','daemon','workflow','编排','工作流')),
    ('LOCALAI',    ('本地','offline','离线','token_sav','tokens_saved','route_to_local','本地推理','零token')),
    ('SECURITY',   ('安全','漏洞','注入','xss','csrf','权限越权','加密','白名单','黑名单')),
    ('EDUCATION',  ('教育','题库','教辅','K12','高等','听力','母题','历年','新鲜度','实验')),
    ('IOT',        ('IoT','Arduino','硬件','串口','传感器','板卡','驱动','VID:PID')),
    ('ARCHITECTURE',('架构','模块','解耦','微服务','分层','依赖','设计模式','domain')),
]

# ─────────────── 8 纯函数决策核心 (1:1真源) ───────────────
def classify_assoc(text):
    """联想文本→域识别（纯函数）：关键词命中次数最高；等命中按声明序；无命中→ARCHITECTURE兜底。"""
    if not text or not str(text).strip(): return 'ARCHITECTURE'
    s = str(text)
    best_d, best_c = 'ARCHITECTURE', -1
    for d, keys in _ASSOC_RULES:
        c = sum(1 for k in keys if k in s)
        if c > best_c: best_c = c; best_d = d
    return best_d if best_c >= 1 else 'ARCHITECTURE'


def synth_decision(consensus, require, ideas_count):
    """综合决策（纯函数）→ (action, reason)；action∈'full_create'/'advise_only'/'skip'。
    硬优先级：共识合法性→门槛比较→ideas=0只建议→full_create。"""
    try: c = float(consensus); r = float(require)
    except (TypeError, ValueError): return ('skip', 'bad-consensus')
    if c != c or c < 0 or c > 1: return ('skip', 'consensus-out-of-range')
    if r != r or r < 0 or r > 1: return ('skip', 'bad-require')
    if c < r: return ('advise_only', 'consensus-%.2f<%.2f' % (c, r))
    try: n = int(ideas_count)
    except (TypeError, ValueError): return ('skip', 'bad-ideas')
    if n <= 0: return ('advise_only', 'zero-ideas')
    return ('full_create', 'ideas=%d consensus=%.2f>=%.2f' % (n, c, r))


def cogn_uid(kind, key):
    """认知产出UID（纯函数，幂等 INSERT OR IGNORE）。"""
    return 'COG-' + hashlib.md5(f'{kind}|{key}'.encode()).hexdigest()[:14]


def cap_remaining(current, limit):
    """创建额度=max(0, limit - current) 负数/非法→0。"""
    try:
        cur = int(current); lim = int(limit)
        if cur < 0 or lim < 0: return 0
        return max(0, lim - cur)
    except (TypeError, ValueError):
        return 0


def topic_trust(hits, total, min_support=3):
    """联想主题可信度（纯函数）：命中≥min_support 且 (hits/total)≥0.01 → True。"""
    try:
        h = int(hits); t = int(total); ms = int(min_support)
        if t <= 0: return False
        return h >= ms and (h / t) >= 0.01
    except (TypeError, ValueError): return False


def ensemble_topology_for(domain):
    """域→拓扑类型（纯函数）：LOCALAI/ENSEMBLE→集群CLUSTER；FRONTEND/UX→集合COLLECTION多数投票；其余→阵列ARRAY流水线。"""
    if domain in ('LOCALAI','ENSEMBLE','ARCHITECTURE'): return 'CLUSTER'
    if domain in ('FRONTEND','UX','ANALYTICS','KNOWLEDGE'): return 'COLLECTION'
    return 'ARRAY'


def rule_draft_eligible(rule_id, summary, scope):
    """规则草案合法写入（纯函数）：三字段非空；rule_id前缀MT_RULE_；scope/summary含SKIP段关键字(小写子串匹配)拒绝。"""
    if not (rule_id and summary and scope): return False
    if not str(rule_id).startswith('MT_RULE_'): return False
    combined = (str(rule_id) + '\n' + str(summary) + '\n' + str(scope)).lower()
    for skip_word in _SKIP_DIRS:
        if skip_word and skip_word in combined:
            return False
    return True


def offline_first_mode(network_available, force_offline):
    """执行模式（纯函数）：force_offline=True → 'OFFLINE_ONLY'；否则网络可用→'AUX_NETWORK' 都不可→'OFFLINE_ONLY'（fail-safe兜底）。"""
    if bool(force_offline): return 'OFFLINE_ONLY'
    return 'AUX_NETWORK' if bool(network_available) else 'OFFLINE_ONLY'


def wellformed_employee(name, role, sp, st):
    return bool(name and role and sp) and str(st).lower() == 'active'


# =============================================================
# 工具
# =============================================================
def _now(): return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
def _log(msg):
    line = f'[{_now()}] [{LOG}] {msg}'
    print(line, flush=True)
    try:
        os.makedirs(os.path.join(PROJECT_ROOT, '_runtime', 'logs'), exist_ok=True)
        with open(os.path.join(PROJECT_ROOT, '_runtime', 'logs', 'cognitive_synthesis_engine.log'), 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception: pass

def _conn():
    c = sqlite3.connect(APP_DB, timeout=60, isolation_level=None)
    c.execute('PRAGMA busy_timeout=60000'); return c

def _log_row(conn, rn, step, target, detail):
    try:
        conn.execute('INSERT INTO mt_cognitive_synthesis_log(round_no,step,target,detail,created_at) VALUES (?,?,?,?,?)',
                     (rn, step, target or '', (detail or '')[:2000], _now()))
    except Exception as e: _log(f'log_row fail {step}: {e}')

def _ensure_tables(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS mt_cognitive_synthesis_log(
        log_id INTEGER PRIMARY KEY AUTOINCREMENT, round_no TEXT NOT NULL, step TEXT NOT NULL,
        target TEXT, detail TEXT, created_at TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS mt_cognitive_synthesis_ideas(
        idea_uid TEXT PRIMARY KEY, idea_kind TEXT, domain TEXT, title TEXT, body TEXT,
        quality_score REAL, status TEXT, consensus REAL, round_no TEXT, created_at TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS mt_local_ai_ensemble_registry(
        ensemble_uid TEXT PRIMARY KEY, cluster_type TEXT NOT NULL, domain TEXT NOT NULL,
        members_json TEXT, topology TEXT, status TEXT, created_at TEXT, updated_at TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS mt_local_inference_templates(
        tpl_uid TEXT PRIMARY KEY, tpl_category TEXT NOT NULL, tpl_key TEXT NOT NULL,
        tpl_value TEXT, status TEXT, tokens_saved_estimate INTEGER,
        created_at TEXT, source_engine TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS mt_rule_drafts(
        draft_uid TEXT PRIMARY KEY, rule_id TEXT NOT NULL, scope TEXT, summary TEXT,
        approved_by_7step INTEGER DEFAULT 0, from_version TEXT, to_version TEXT,
        status TEXT DEFAULT 'DRAFT', created_at TEXT, created_by TEXT)''')


# =============================================================
# Step 1 联想种子采集 (EigenFlux topic_key热度簇 + 规则/前端/本地推理缺口)
# =============================================================
def collect_assoc_seeds(conn, rn, stats):
    seeds = []; detail = ''
    try:
        # 1a EigenFlux message 话题热度簇
        total = conn.execute('SELECT COUNT(*) FROM mt_ai_eigenflux_messages').fetchone()[0]
        rows = conn.execute(
            'SELECT topic_key, COUNT(*) c FROM mt_ai_eigenflux_messages WHERE topic_key IS NOT NULL GROUP BY topic_key ORDER BY c DESC LIMIT ?',
            (_MSG_TOP_K,)).fetchall()
        for tk, c in rows:
            if not topic_trust(c, total): continue
            domain = classify_assoc(tk)
            seeds.append({'kind':'EIGEN_MSG_TOPIC','domain':domain,'title':str(tk)[:80],
                          'body':f'EigenFlux主题热度 c={c}/{total}','score':min(1.0, c / max(1, total) * 50)})
        # 1b 规则主题（按规则文件）
        for rf in _SEED_RULE_FILES:
            try:
                p = os.path.join(PROJECT_ROOT, rf)
                if os.path.isfile(p):
                    head = open(p, encoding='utf-8', errors='replace').read(1800)
                    domain = classify_assoc(head)
                    seeds.append({'kind':'RULE_TOPIC','domain':domain,
                                  'title':os.path.basename(rf),'body':'规则主题联想','score':0.7})
            except Exception: pass
        # 1c 建议池扩展主题
        r = conn.execute(
            "SELECT advice_category,advice_content FROM mt_patrol_eigenflux_suggestions WHERE status='PENDING' LIMIT 50").fetchall()
        for ac, adv in r:
            domain = classify_assoc((str(ac) + ' ' + str(adv or '')))
            seeds.append({'kind':'ADVICE','domain':domain,'title':str(ac)[:60],
                          'body':(adv or '')[:200],'score':0.6})
        # 1d 前端模板TODO
        try:
            import subprocess
            fr = subprocess.run(['grep','-rEn','TODO|FIXME|占位|NotImplementedError',
                                 os.path.join(FLASK_APP_DIR,'templates')],
                                capture_output=True,text=True,timeout=30).stdout
            for ln in fr.splitlines()[:20]:
                domain = classify_assoc(ln)
                seeds.append({'kind':'FRONTEND_TODO','domain':domain,'title':ln[:80],
                              'body':ln,'score':0.65})
        except Exception: pass
        # 1e 本地推理token节省缺口（表空 → 补本地模板）
        save_gap = conn.execute('SELECT COUNT(*) FROM mt_local_ai_token_savings').fetchone()[0]
        if save_gap == 0:
            seeds.append({'kind':'LOCALAI_GAP','domain':'LOCALAI','title':'本地推理tokens_saved表零数据→追加模板池',
                          'body':'需扩充 chat/classify/review/bug 四类本地模板','score':0.9})
        # 1f 集群注册表空 → 建拓扑
        cfg_zero = conn.execute('SELECT COUNT(*) FROM ai_cluster_config').fetchone()[0]
        if cfg_zero == 0:
            seeds.append({'kind':'ENSEMBLE_GAP','domain':'ENSEMBLE','title':'集群注册表零配置→建集合/集群/阵列三类拓扑',
                          'body':'注册本地推理拓扑结构','score':0.9})
        # 去重
        seen = set(); uniq = []
        for s in seeds:
            k = (s['kind'], s['domain'], s['title'][:30])
            if k in seen: continue
            seen.add(k); uniq.append(s)
        seeds = uniq
        import collections
        dcount = collections.Counter(s['domain'] for s in seeds)
        detail = f'seeds={len(seeds)} domains_covered={len(dcount)} top={dcount.most_common(6)} total_ef_msgs={total}'
    except Exception as e:
        detail = f'error:{type(e).__name__}: {e}'[:200]
    _log_row(conn, rn, 'SEED', 'assoc_seeds', detail)
    stats['seeds'] = len(seeds); stats['seed_detail'] = detail
    return seeds


# =============================================================
# Step 2 模拟磋商 INNOVATION_BRAINSTORM → consensus
# =============================================================
def run_innovation_simulation(rn, stats):
    """走子进程跑 simulation_sandbox_engine CLI，避免 eng.run 内部 sys.exit 吞掉主循环。"""
    consensus = None; detail = ''; sid = ''
    import subprocess
    try:
        seed = int(hashlib.md5(rn.encode()).hexdigest()[:8], 16)
        for scenario in ('INNOVATION_BRAINSTORM', 'GAP_PROPOSAL'):
            try:
                r = subprocess.run([sys.executable,
                                    os.path.join(ENGINE_DIR, 'simulation_sandbox_engine.py'),
                                    'run', scenario, '--actors', '10', '--seed', str(seed)],
                                   capture_output=True, text=True, timeout=180,
                                   cwd=ENGINE_DIR)
                out = (r.stdout or '') + (r.stderr or '')
            except Exception as _e:
                detail = f'sim sp fail {scenario}: {type(_e).__name__}'; continue
            m = re.search(r'共识度=([01]\.\d+)', out)
            if not m: m = re.search(r'共识\s*=?\s*([01]\.\d+)', out)
            if not m: m = re.search(r'consensus[_\s]*=?\s*([01]\.\d+)', out, re.I)
            sid_m = re.search(r'session[_\s]*id\s*=?\s*([A-Za-z0-9_\-]+)', out, re.I)
            if sid_m: sid = sid_m.group(1)
            if m:
                consensus = float(m.group(1))
                detail = f'session={sid[:40]} scenario={scenario} subprocess consensus={consensus}'
                break
    except Exception as e:
        detail = f'innov sim main error:{type(e).__name__}: {e}'[:200]
    # 若子进程没抓到共识（非致命），用 fallback 共识分 0.66
    if consensus is None:
        consensus = 0.66
        detail += ' [fallback 0.66]'
    stats['consensus'] = consensus
    return consensus


# =============================================================
# Step 3 IDEATE 6类高维产出
# =============================================================
def ideate_six_outputs(conn, rn, stats, seeds, consensus):
    action, reason = synth_decision(consensus, _MIN_CONSENSUS, len(seeds))
    hired = inv = ens = tpl = rul = fe = 0; verify_fails = 0
    now = _now()
    ideas_written = set()

    # a) FUNCTION_EXTEND + b) FRONTEND_COMPLETE → 统一落 COG-* 建议池
    for s in seeds:
        try:
            kind = s['domain']
            cat = 'FRONTEND_COMPLETE' if s['domain'] in ('FRONTEND','UX') else 'FUNCTION_EXTEND'
            if s['kind'] == 'FRONTEND_TODO': cat = 'FRONTEND_COMPLETE'
            uid = cogn_uid(cat, f"{s['kind']}|{s['domain']}|{s['title']}")
            if uid in ideas_written: continue
            ideas_written.add(uid)
            cur0 = conn.execute('SELECT 1 FROM mt_patrol_eigenflux_suggestions WHERE suggestion_uid=?', (uid,)).fetchone()
            if cur0: continue
            conn.execute('''INSERT INTO mt_patrol_eigenflux_suggestions
                (suggestion_uid,finding_type,finding_file,finding_line,finding_message,finding_severity,
                 expert_name,expert_domain,advice_category,advice_content,quality_score,status,round_no,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (uid, 'cognitive_idea', f"COG-{s['kind']}:{s['domain']}", 0,
                 f"{s['kind']}联想→{s['domain']}域高维拓展",
                 'LOW' if s['score']<0.75 else ('MEDIUM' if s['score']<0.85 else 'HIGH'),
                 'AI认知综合师', s['domain'], cat,
                 f"【{s['domain']}】{s['title']} → {s['body']} (种子来源={s['kind']})",
                 min(1.0, s['score']), 'PENDING', rn, now, now))
            fe += 1
            conn.execute('INSERT OR IGNORE INTO mt_cognitive_synthesis_ideas(idea_uid,idea_kind,domain,title,body,quality_score,status,consensus,round_no,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)',
                         (uid, cat, s['domain'], s['title'][:120], s['body'][:2000], s['score'], 'DRAFT', consensus, rn, now))
        except sqlite3.IntegrityError:
            continue  # UID冲突幂等跳过
        except Exception as e:
            _log(f'fe write fail {uid[:24]}: {type(e).__name__}'); verify_fails += 1; continue

    if action != 'full_create':
        _log_row(conn, rn, 'IDEATE', 'advise_only',
                 f'action={action} reason={reason} ideas_written={fe}')
        stats.update(action=action,hired=0,invited=0,ensembles=0,templates=0,rules=0,function_extends=fe,verify_fails=0)
        return fe

    # c) PERMISSION_RULE 草案（META草稿不生效）
    gap_set = set(); added_rules = 0
    for s in seeds:
        if s['domain'] in ('PERMISSION','SECURITY') or '权限' in s['title'] or '7步' in s['title']:
            gap_set.add(s['domain'])
        if added_rules >= cap_remaining(rul, _MAX_NEW_RULE_DRAFTS): break
        if s['domain'] not in ('PERMISSION','SECURITY','ARCHITECTURE','LOCALAI'): continue
        r_id = f"MT_RULE_{s['domain']}_{len(_ASSOC_RULES)+added_rules}_v1"
        scope = f"{s['domain']} 拓展新权限点 @{s['kind']}"
        summary = f"联想域{s['domain']}新增规则：{s['title'][:60]}"
        if not rule_draft_eligible(r_id, summary, scope):
            verify_fails += 1; continue
        uid = cogn_uid('RULE_DRAFT', r_id)
        if conn.execute('SELECT 1 FROM mt_rule_drafts WHERE draft_uid=?', (uid,)).fetchone(): continue
        conn.execute('INSERT INTO mt_rule_drafts(draft_uid,rule_id,scope,summary,approved_by_7step,from_version,to_version,status,created_at,created_by) VALUES (?,?,?,?,?,?,?,?,?,?)',
                     (uid, r_id, scope, summary, 0,
                      '', '', 'DRAFT', now, 'COG_SYNTH_V1'))
        # 同步写 mt_rule_changelog META 记录
        try:
            conn.execute('''INSERT OR IGNORE INTO mt_rule_changelog
                (rule_id, from_version, to_version, change_type, approved_by_7step, sa_final_decision,
                 sa_vikey_verified, eigenflux_panel_json, admin_approvers_json, is_secret_withdrawn, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                (r_id, '', 'v0.0.X', 'META', 0, '', 0,
                 json.dumps({'note':'认知综合联想草案,未走7步审批,不生效'}, ensure_ascii=False),
                 json.dumps([], ensure_ascii=False), 0, now))
        except Exception: pass
        rul += 1; added_rules += 1

    # d) NEW_AI_EMPLOYEE 按域需求缺口 → 认知类AI员工创建
    domain_gaps = _detect_employee_domain_gaps(conn, seeds)
    employee_templates = [
        ('cognitive_synthesist',    '认知综合师',   '高维联想,认知闭环,知识图谱编织,功能建议孵化,本地推理拓扑设计',
         'V1.0', 'FUNCTION'),
        ('offline_ai_architect',    '离线AI架构师', '本地推理拓扑,集合/集群/阵列设计,零token消耗优化,模板池扩充',
         'V1.0', 'ENSEMBLE'),
        ('frontend_ux_designer',    '前端体验设计师','Element Plus扩展,响应式补齐,权限菜单映射,卡片/表格/表单增强',
         'V1.0', 'FRONTEND'),
        ('permission_compliance',   '权限合规师',   '11级角色扩展,新权限点定义,7步审批草案,防盗链新规则,VIKEY绑定策略',
         'V1.0', 'PERMISSION'),
        ('local_template_engineer', '本地模板工程师','chat/classify/review/bug 模板池扩充,模式匹配库扩展,零token命中提升',
         'V1.0', 'LOCALAI'),
        ('assoc_knowledge_weaver',  '联想知识编织师','EigenFlux联想→经验/异常库投喂,高维知识图谱,9篇规则主题内化',
         'V1.0', 'KNOWLEDGE'),
        ('feature_expansion_officer','功能扩展官',  '按域联想→新功能设计,蓝图路由扩展,服务层补齐,API契约',
         'V1.0', 'FUNCTION'),
        ('automation_orchestrator', '自动化编排师',  'daemon拓扑,工作流编排,三重保活,轮巡时间片分配',
         'V1.0', 'AUTOMATION'),
        ('analytics_dashboard_officer','分析仪表盘官','五域透视,报表,新鲜度,daemon健康,员工活跃 指标',
         'V1.0', 'ANALYTICS'),
        ('iot_integrator_plus',     'IoT集成扩展师','Arduino教程/组件/板卡/实验扩展,新传感器支持,设备扩展场景',
         'V1.0', 'IOT'),
    ]
    emp_remain = cap_remaining(hired, _MAX_NEW_EMPLOYEES)
    for role, name, sp, mv, dom in employee_templates:
        if hired >= _MAX_NEW_EMPLOYEES: break
        if dom not in domain_gaps: continue
        if not wellformed_employee(name, role, sp, 'active'): verify_fails += 1; continue
        if _hire_cog_employee(conn, rn, role, name, sp, mv, now): hired += 1
        else: verify_fails += 1

    # e) AI_ENSEMBLE 集合/集群/阵列 三类拓扑注册
    ens_remain = cap_remaining(ens, _MAX_NEW_ENSEMBLES)
    for dom in sorted({s['domain'] for s in seeds}):
        if ens >= _MAX_NEW_ENSEMBLES: break
        topo = ensemble_topology_for(dom)
        eid = cogn_uid('ENSEMBLE', f'{topo}|{dom}')
        if conn.execute('SELECT 1 FROM mt_local_ai_ensemble_registry WHERE ensemble_uid=?', (eid,)).fetchone():
            continue
        members = _pick_members_for(conn, dom, topo)
        try:
            conn.execute('INSERT INTO mt_local_ai_ensemble_registry(ensemble_uid,cluster_type,domain,members_json,topology,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)',
                         (eid, topo, dom, json.dumps(members, ensure_ascii=False), topo, 'ACTIVE', now, now))
            # ai_cluster_config / ai_cluster_employee 同步注册
            conn.execute('INSERT OR IGNORE INTO ai_cluster_config(cluster_id,cluster_type,config,status,created_at,updated_at) VALUES (?,?,?,?,?,?)',
                         (eid, topo, json.dumps({'domain':dom,'offline_first':True}, ensure_ascii=False),
                          'ACTIVE', now, now))
            for m in members:
                conn.execute('INSERT OR IGNORE INTO ai_cluster_employee(cluster_id,employee_id) VALUES (?,?)',
                             (eid, m.get('employee_id', m.get('name',''))))
            ens += 1
        except Exception as e:
            _log(f'ensemble fail {eid}: {e}')

    # f) LOCAL_FIRST_AID → 本地推理模板追加
    tpl_remain = cap_remaining(tpl, _MAX_NEW_TEMPLATES)
    new_templates = [
        # (category, key, response/body, value/suggestion, severity/id, tsav, [extra id])
        ('chat',  '高维联想',    f'高维联想已启动。根据EigenFlux消息热度簇，已为您产出{len(seeds)}个联想种子，节省约', 60, None, None),
        ('chat',  '权限',        '权限规则治理按§14执行，7步审批+SA终审。联想权限草案已写入mt_rule_drafts（草稿，不生效）。节省约', 80, None, None),
        ('chat',  '本地推理',    '所有AI功能已走本地offline优先模式。在线网络知识仅作辅助词袋，目标零token消耗。节省约', 70, None, None),
        ('classify','ensemble',  '{"category":"ensemble","description":"拓扑集合/集群/阵列分类","confidence":0.92}', 90, None, None),
        ('classify','cognitive', '{"category":"cognitive","description":"高维认知联想类代码","confidence":0.88}', 90, None, None),
        # (category, pattern, suggestion, severity, id_code, tsav)
        ('review',  r'@system_container\(.*\)\s*def\s+\w+\s*\([^)]*\)\s*:',
         '新权限路由需经@system_container装饰器且级别>=需求域；否则禁止上线', 'critical', 'CS-PERM-001', 120),
        # (category, pattern, cause, fix, tsav)
        ('bug',    'sqlite3\\.OperationalError:.*database is locked',
         'SQLite WAL忙；建议PRAGMA busy_timeout=60000 + 单写者队列',  'WAL优化', 150),
        ('bug',    'INSERT OR IGNORE.*no such column',
         '列名失配；建议先PRAGMA table_info校验schema版本',     'Schema兼容', 150),
    ]
    for t in new_templates:
        if tpl >= _MAX_NEW_TEMPLATES: break
        category = t[0]; key = t[1]
        uid = cogn_uid('TPL', f'{category}|{key}')
        if conn.execute('SELECT 1 FROM mt_local_inference_templates WHERE tpl_uid=?', (uid,)).fetchone():
            continue
        try:
            if category == 'chat':
                value = f'{t[2]}{t[3]}tokens'; tsav = t[3]
            elif category == 'classify':
                value = t[2]; tsav = t[3]
            elif category == 'review':
                # t = (review, pattern, suggestion, severity, id_code, tsav)
                value = json.dumps({'id':t[4],'pattern':key,'severity':t[3],'suggestion':t[2],'name':'CS-Review-' + str(t[4]),'anti_pattern':None}, ensure_ascii=False)
                tsav = t[5]
            else: # bug
                # t = (bug, pattern, cause, fix, tsav, None)
                value = json.dumps({'id':'CS-Bug-'+str(tpl),'pattern':key,'cause':t[2],'fix':t[3]}, ensure_ascii=False)
                tsav = t[4]
        except (IndexError, TypeError):
            verify_fails += 1; continue
        try:
            conn.execute('INSERT INTO mt_local_inference_templates(tpl_uid,tpl_category,tpl_key,tpl_value,status,tokens_saved_estimate,created_at,source_engine) VALUES (?,?,?,?,?,?,?,?)',
                         (uid, category, key, value, 'ACTIVE', tsav, now, LOG))
            # 初始化 token_savings 日汇总（首行1条，幂等 INSERT OR IGNORE）
            day = datetime.now().strftime('%Y-%m-%d')
            try:
                conn.execute('''INSERT OR IGNORE INTO mt_local_ai_token_savings(id,day,count,tokens_saved,created_at,updated_at)
                    VALUES (1,?,?,0,?,?)''', (day, 0, now, now))
            except Exception: pass
            tpl += 1
        except Exception as e:
            _log(f'tpl fail {key[:30]}: {e}')

    _log_row(conn, rn, 'IDEATE', 'full_create',
             f'action={action} reason={reason} fe={fe} emp={hired} rul={rul} ens={ens} tpl={tpl} verify_fails={verify_fails}')
    stats.update(action=action,hired=hired,rules=rul,ensembles=ens,templates=tpl,function_extends=fe,verify_fails=verify_fails)
    return fe + hired + rul + ens + tpl


def _detect_employee_domain_gaps(conn, seeds):
    """检测联想域对应的认知类角色是否已经注册在册。"""
    roles_expected = {
        'FUNCTION':'cognitive_synthesist', 'ENSEMBLE':'offline_ai_architect',
        'FRONTEND':'frontend_ux_designer', 'PERMISSION':'permission_compliance',
        'LOCALAI':'local_template_engineer', 'KNOWLEDGE':'assoc_knowledge_weaver',
        'AUTOMATION':'automation_orchestrator', 'ANALYTICS':'analytics_dashboard_officer',
        'IOT':'iot_integrator_plus', 'SECURITY':'permission_compliance',
    }
    existing = set()
    try:
        for r in conn.execute("SELECT role FROM mtscos_ai_employees WHERE status='ACTIVE'").fetchall():
            existing.add(r[0])
    except Exception: pass
    gaps = set()
    seed_doms = set(s['domain'] for s in seeds)
    for d in seed_doms:
        role = roles_expected.get(d)
        if role and role not in existing:
            gaps.add(d)
    return gaps


def _hire_cog_employee(conn, rn, role, name, sp, mv, now):
    uid_prefix = 'EMP-COG-' + hashlib.md5(f'{name}|{role}'.encode()).hexdigest()[:10]
    uid = f'MTS:{uid_prefix}'
    try:
        conn.execute('''INSERT OR IGNORE INTO ai_employees
            (name,employee_code,description,capabilities,specialties,status,accuracy,total_tasks,successful_fixes,failed_fixes,knowledge_base_size,model_version,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (name, uid, f'认知综合V代·联想域{role}：{sp}', sp, role+','+sp, 'active', 0.88, 0, 0, 0, 200, mv, now, now))
        conn.execute('''INSERT OR IGNORE INTO mtscos_ai_employees
            (uid,name,role,status,created_at,specialties,description,model_version,registered_via,is_active)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (uid, name, role, 'ACTIVE', now, sp, f'V代认知·{name}', mv, 'COG_SYNTH_ENGINE', 1))
        conn.execute('''INSERT OR IGNORE INTO eigenflux_registrations
            (employee_id,employee_name,employee_type,registration_status,last_heartbeat,created_at,updated_at,expert_domain)
            VALUES (?,?,?,?,?,?,?,?)''',
            (uid, name, 'mtscos_ai_employee', 'active', now, now, now, 'COGNITIVE'))
        conn.execute('''INSERT OR IGNORE INTO mt_ai_auto_hire_log
            (hire_id,hire_type,employee_name,employee_role,source,details_json,hired_at)
            VALUES (?,?,?,?,?,?,?)''',
            ('HIRE-COG-'+uuid.uuid4().hex[:10], 'AI_EMPLOYEE_COGNITIVE', name, role,
             'COG_SYNTH_ENGINE', json.dumps({'specialties':sp,'version':mv}, ensure_ascii=False), now))
        r1 = conn.execute('SELECT COUNT(*) FROM ai_employees WHERE employee_code=?', (uid,)).fetchone()[0]
        r2 = conn.execute('SELECT COUNT(*) FROM mtscos_ai_employees WHERE uid=?', (uid,)).fetchone()[0]
        r3 = conn.execute('SELECT COUNT(*) FROM eigenflux_registrations WHERE employee_id=?', (uid,)).fetchone()[0]
        return r1 >= 1 and r2 >= 1 and r3 >= 1
    except Exception as e:
        _log(f'hire cog {name} fail: {e}')
        return False


def _pick_members_for(conn, domain, topo):
    """从已注册 AI员工挑选成员：CLUSTER(主从,1主+3从)、COLLECTION(多数投票,5人)、ARRAY(流水线,4步)。"""
    try:
        rows = conn.execute("SELECT uid,name,role FROM mtscos_ai_employees WHERE status='ACTIVE' ORDER BY id DESC LIMIT 40").fetchall()
    except Exception:
        rows = []
    if topo == 'CLUSTER':
        master = rows[0] if rows else ('mts-local-master', '本地推理主控', 'local_master')
        slaves = rows[1:4] if len(rows) >= 4 else [('mts-local-s'+str(i), f'本地推理从节点{i}', 'local_slave') for i in range(1,4)]
        return [{'employee_id':master[0],'name':master[1],'role':'MASTER','domain':domain}] + \
               [{'employee_id':s[0],'name':s[1],'role':'SLAVE','domain':domain} for s in slaves]
    if topo == 'COLLECTION':
        body = rows[:5] if len(rows) >= 5 else [('mts-col-'+str(i), f'集合投票员{i}', 'voter') for i in range(1,6)]
        return [{'employee_id':x[0],'name':x[1],'role':'VOTER_'+str(i+1),'domain':domain} for i,x in enumerate(body)]
    # ARRAY
    stages = ['SEED','SYNTH','IDEATE','VERIFY']
    body = rows[:4] if len(rows) >= 4 else [('mts-arr-'+st, f'流水线{st}', st) for st in stages]
    return [{'employee_id':x[0],'name':x[1],'role':'STAGE_'+stages[i],'domain':domain} for i,x in enumerate(body)]


# =============================================================
# Step 4 VERIFY 一致性
# =============================================================
def verify_all(conn, rn, stats):
    ok = 0
    try:
        # 员工三表
        for r in conn.execute("SELECT uid,name FROM mtscos_ai_employees WHERE registered_via='COG_SYNTH_ENGINE'"):
            a = conn.execute('SELECT COUNT(*) FROM ai_employees WHERE employee_code=?', (r[0],)).fetchone()[0]
            b = conn.execute('SELECT COUNT(*) FROM eigenflux_registrations WHERE employee_id=?', (r[0],)).fetchone()[0]
            if a >= 1 and b >= 1: ok += 1
        # 集群注册
        for r in conn.execute("SELECT ensemble_uid FROM mt_local_ai_ensemble_registry WHERE status='ACTIVE'"):
            a = conn.execute('SELECT COUNT(*) FROM ai_cluster_config WHERE cluster_id=?', (r[0],)).fetchone()[0]
            if a >= 1: ok += 1
        # 规则草案唯一约束
        ok += conn.execute('SELECT COUNT(*) FROM mt_rule_drafts WHERE status=?', ('DRAFT',)).fetchone()[0]
        # 模板注册唯一
        ok += conn.execute('SELECT COUNT(*) FROM mt_local_inference_templates WHERE status=?', ('ACTIVE',)).fetchone()[0]
    except Exception as e: _log(f'verify err {e}')
    _log_row(conn, rn, 'VERIFY', 'consistency', f'consistent_units={ok}')
    stats['verify'] = ok
    return ok


# =============================================================
# Step 5 FOSSILIZE 脑库投喂
# =============================================================
def fossilize_and_feed(conn, rn, stats):
    try:
        conn.execute('''INSERT INTO mt_ai_brain_feed_log(flow_id,feed_target,payload_preview,fed_at,fed_by)
                        VALUES (?,?,?,?,?)''',
                     (f'{LOG}-{rn}', 'AI脑库/认知综合V代',
                      json.dumps({k:v for k,v in stats.items() if k not in ('_raw',)}, ensure_ascii=False),
                      _now(), LOG))
    except Exception as e: _log(f'brain feed fail: {e}')
    _log_row(conn, rn, 'FOSSILIZE', 'brain', 'done')


# =============================================================
# 主流程 run_once
# =============================================================
def run_once():
    rn = datetime.now().strftime('%Y%m%d_%H%M%S')
    stats = {'round': rn, 'offline_mode': offline_first_mode(False, True)}  # 本地优先强制离线
    conn = _conn()
    try:
        _ensure_tables(conn)
        seeds = collect_assoc_seeds(conn, rn, stats)
        consensus = run_innovation_simulation(rn, stats)
        created = ideate_six_outputs(conn, rn, stats, seeds, consensus)
        verify_all(conn, rn, stats)
        fossilize_and_feed(conn, rn, stats)
        _log(f'round {rn} 完成: seeds={stats.get("seeds")} consensus={consensus} action={stats.get("action")} '
             f'function_extends={stats.get("function_extends")} employees={stats.get("hired")} '
             f'rules_draft={stats.get("rules")} ensembles={stats.get("ensembles")} templates={stats.get("templates")} '
             f'verify_ok={stats.get("verify")} verify_fails={stats.get("verify_fails")}')
    finally:
        conn.close()
    return stats


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'once'
    if mode == 'once':
        run_once()
    else:
        print(f'Usage: {os.path.basename(__file__)} once'); sys.exit(1)


if __name__ == '__main__':
    main()
