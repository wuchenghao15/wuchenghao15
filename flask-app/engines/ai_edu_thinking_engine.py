#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_edu_thinking_engine.py — 教辅思维轮巡引擎 (VI代 v22.9.0)
================================================================================
§14 IRON_RULE 12步骤 flow_edu_thinking_*  daemon: sys_edu_thinking (900s轮巡)

用户需求(VI代)：
  轮巡自动增加教辅同步功能，
  邪修解题思路及模型发觉与解析，
  巧思巧算解题思路讲解及对应母题分析。

概念定义(教育域术语)：
  - 邪修解题(UNCONVENTIONAL)：非常规高效解法体系——构造法/特殊值试探/极端原理/
    对称性利用/正难则反/数形结合/换元降维/归纳猜想/放缩夹逼/量纲分析等。
    每个模型必须标注【风险边界】(LOW/MEDIUM/HIGH) 与标准解法对比。
  - 模型发觉与解析(DETECT)：从母题题型×解题模型匹配中发觉未覆盖场景，
    产出"邪修模型"卡片(识别特征/步骤模板/风险边界/与常规解法对比)。
  - 巧思巧算(QUICK_CALC)：速算巧解技巧——凑整/裂项/尾数判定/十字相乘/估算/
    基准数/图像速解/周期压缩等，含分步讲解。
  - 母题分析(MOTHER_TOPIC)：方法↔母题挂接，每挂接含变式分析(depth A/B/C)。

本地零token铁律：
  offline_first() 恒返 OFFLINE_ONLY——全部产出由本地SQLite已有数据
  (母题表/教辅内容/建议池/EigenFlux教育热度) + 引擎内置模板库挖掘生成，
  不调用任何外部API；在线网络知识仅作离线快照辅助。

CLI：
  python3 ai_edu_thinking_engine.py once    单轮执行(供daemon调用)
  python3 ai_edu_thinking_engine.py daemon  常驻循环(900s)
================================================================================
"""
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime

# ── 路径 ──
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_MAIN = os.path.join(ROOT, '_runtime', 'databases', 'Database', 'app.db')
DB_EDU = os.path.join(ROOT, 'flask-app', 'ai_engines', 'app.db')  # 教辅数据源(7题型+27内容)
ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG = 'EDU-THINK'
PID_FILE = os.path.join(ROOT, '_runtime', 'pids', 'ai_edu_thinking_engine.pid')
LOG_FILE = os.path.join(ROOT, '_runtime', 'logs', 'edu_thinking_engine.log')

# ── 决策常量 (1:1真源 8条) ──
_MIN_CONSENSUS = 0.65
_MAX_UNCONVENTIONAL = 6
_MAX_QUICK_CALC = 6
_MAX_MOTHER_LINKS = 8
_MAX_SUGGESTIONS = 10
_MSG_TOP_K = 40
_RISK_LEVELS = ('LOW', 'MEDIUM', 'HIGH')
_THINKING_CATEGORIES = ('UNCONVENTIONAL', 'QUICK_CALC', 'MOTHER_TOPIC')

# ─────────────── 9 纯函数决策核心 (1:1真源) ───────────────
_UNCONV_KEYS = ('构造', '反证', '极端', '对称', '换元', '放缩', '反常规', '偏门',
                '巧妙绕开', '特殊值', '正难则反', '数形结合', '归纳猜想', '量纲')
_QUICK_KEYS = ('凑整', '裂项', '拆项', '尾数', '十字相乘', '估算', '速算', '巧算',
               '图像速解', '周期', '基准数', '约分', '奇偶', '整除')
_MOTHER_KEYS = ('母题', '变式', '一题多解', '举一反三')


def classify_thinking(text):
    """思维文本→类别（纯函数）：命中次数最高组胜出；无命中/空→GENERAL。"""
    if not text or not str(text).strip():
        return 'GENERAL'
    s = str(text)
    scores = {
        'UNCONVENTIONAL': sum(1 for k in _UNCONV_KEYS if k in s),
        'QUICK_CALC': sum(1 for k in _QUICK_KEYS if k in s),
        'MOTHER_TOPIC': sum(1 for k in _MOTHER_KEYS if k in s),
    }
    best = max(scores, key=lambda k: (scores[k], -_THINKING_CATEGORIES.index(k)))
    return best if scores[best] >= 1 else 'GENERAL'


def thinking_wellformed(name, principle, steps, risk):
    """方法卡校验（纯函数）：4要素非空+steps≥2步+risk在白名单→True。"""
    if not (name and principle and steps and risk):
        return False
    try:
        if len(list(steps)) < 2:
            return False
    except TypeError:
        return False
    return risk in _RISK_LEVELS


def risk_boundary(risk):
    """风险→边界描述（纯函数）：HIGH仅选择/草稿慎用；非法→UNKNOWN_RISK。"""
    if risk == 'LOW':
        return '风险低: 可放心用于常规解题与解答题'
    if risk == 'MEDIUM':
        return '风险中: 建议用于验算或选择题, 解答前先用标准法核验'
    if risk == 'HIGH':
        return '风险高: 仅用于选择题秒杀或草稿试错, 解答题慎用'
    return 'UNKNOWN_RISK'


def method_uid_of(category, name):
    """方法确定性散列（纯函数）：ETH-前缀+md5[:14]，类别隔离。"""
    return 'ETH-' + hashlib.md5(f'{category}|{name}'.encode()).hexdigest()[:14]


def mother_topic_match(question_type, model_text):
    """题型-方法匹配（纯函数）：题型token(len≥2)任一出现在模型文本→True。"""
    if not question_type or not model_text:
        return False
    qt, mt = str(question_type), str(model_text)
    if not qt.strip() or not mt.strip():
        return False
    for tok in re.split(r'[/,，+、\s]+', qt):
        if len(tok) >= 2 and tok in mt:
            return True
    return False


def thinking_cap(current, limit):
    """单轮余量（纯函数）：非法/负数/0上限→0。"""
    if not isinstance(current, int) or not isinstance(limit, int):
        return 0
    if isinstance(current, bool) or isinstance(limit, bool):
        return 0
    if current < 0 or limit <= 0:
        return 0
    return max(0, limit - current)


def sync_decision(consensus, require, gaps):
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
    """本地零token铁律（纯函数）：恒返OFFLINE_ONLY——不触发外部API；
    在线网络知识仅作离线快照辅助(AUX快照由离线采集进程负责)。"""
    return 'OFFLINE_ONLY'


def variant_depth(quality):
    """变式分析深度（纯函数）：≥0.9→A(三层变式) ≥0.75→B(两层) 其余→C；非法→C。"""
    if isinstance(quality, bool) or not isinstance(quality, (int, float)):
        return 'C'
    if quality != quality or quality in (float('inf'), float('-inf')):
        return 'C'
    if quality >= 0.9:
        return 'A'
    if quality >= 0.75:
        return 'B'
    return 'C'


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
# 内置方法模板库 (本地知识, 零token) — 12邪修 + 12巧算
# 元组: (name, principle, steps, standard_compare, risk, tags, subjects)
# =============================================================
_UNCONVENTIONAL_TEMPLATES = [
    ('构造法', '按目标结论反向构造函数/图形/反例，把"是否存在"化为"找得到"',
     ('识别待构造对象', '从结论特征反推构造物', '验证构造满足全部条件', '书写构造过程'),
     '常规解法正面推进讨论存在性，构造法直接给出实例，绕过分类讨论', 'MEDIUM',
     '函数,几何,存在性,反例', '数学/物理'),
    ('特殊值试探法', '用特殊值代入排除错误选项，选择题秒杀',
     ('观察选项特征', '选取边界/易算特殊值', '代入排除', '确认唯一剩余项'),
     '常规解法完整推导通解，特殊值法只保证选择题正确性，不写过程', 'LOW',
     '选择题,函数值,代入', '数学'),
    ('极端原理', '把问题推到边界/极限位置，极端情形揭示一般规律',
     ('确定可变因素', '推到两个极端', '观察不变量或单调性', '回到一般情形论证'),
     '常规解法设一般参量讨论，极端原理先探边界再收口，讨论量减半', 'MEDIUM',
     '边界,极限,单调,最值', '数学/物理'),
    ('对称性利用', '发现式子/图形的对称结构，用对称性消元或简化',
     ('观察对称结构', '利用对称设元(如x+y与xy)', '对称消元', '回代求解'),
     '常规解法硬算展开，对称法减少一半未知量，防增根', 'MEDIUM',
     '对称,轮换,均值,消元', '数学'),
    ('正难则反', '正面分类太多时改从反面(补集/反证)突破',
     ('判断正面情况数', '构造反面事件', '反面求解取补集/导出矛盾', '翻译回原命题'),
     '常规解法正面枚举，正难则反把N种情况压缩为1种反面', 'MEDIUM',
     '反证,补集,至少,存在', '数学'),
    ('数形结合', '代数问题几何化、几何问题代数化，以形助数',
     ('把代数式读成几何意义(距离/斜率/面积)', '画草图定位', '读出几何关系', '回代验证'),
     '常规解法代数变形冗长，数形结合一眼看出范围，注意画图精度', 'LOW',
     '图像,距离,斜率,区域', '数学'),
    ('换元降维', '整体换元把高维/复合结构化为一元简单结构',
     ('识别反复出现的整体', '设元替换', '解简化后的问题', '回代并检查范围'),
     '常规解法直接处理复合结构，换元后次数降一级，注意新元范围', 'MEDIUM',
     '换元,整体,复合,范围', '数学'),
    ('归纳猜想', '算前几项找规律→猜想通项/结论→用归纳或构造证明',
     ('计算n=1,2,3情形', '猜想一般规律', '数学归纳法或构造证明', '检验边界n'),
     '常规解法直接推导通项技巧性强，归纳法人人可上手但须严格证明', 'LOW',
     '数列,规律,归纳,猜想', '数学'),
    ('放缩夹逼', '不等式两边适度放缩或夹逼，逼出唯一值/范围',
     ('确定放缩方向', '选择放缩依据(均值/有界/泰勒截断)', '控制放缩精度', '验证等号成立条件'),
     '常规解法精确计算，放缩法处理无法精确求解的估计问题，等号条件易漏', 'HIGH',
     '不等式,估计,夹逼,数列', '数学'),
    ('量纲分析', '物理公式用单位(量纲)检验/推测形式',
     ('列出各物理量量纲', '检验等式两边量纲一致', '由量纲猜公式形式', '实验系数标定'),
     '常规解法靠记忆公式，量纲法可自查错误并推断公式骨架', 'LOW',
     '单位,量纲,检验,公式', '物理/化学'),
    ('退一步思想', '一般做不出先退到特殊/简单情形，找规律再推广',
     ('把一般问题特殊化', '解简单情形', '观察可迁移结构', '推广回一般并论证'),
     '常规解法直面一般情形，退一步以退为进，适用于结构不明的问题', 'LOW',
     '特殊到一般,探路,简化', '数学'),
    ('主元法', '多元问题选定主元，把其余视为参数，按主元整理降维',
     ('选出现次数最多的字母为主元', '按主元整理(降幂排列)', '利用判别式/一次式性质', '讨论参数范围'),
     '常规解法对称处理各元，主元法把多元压成一层，参数讨论清晰', 'MEDIUM',
     '多元,参数,判别式,降幂', '数学'),
]

_QUICK_CALC_TEMPLATES = [
    ('凑整法', '把数凑成整十整百再调整，减小心算负担',
     ('观察接近整数', '先凑整相加', '补回调整量'), '硬算逐位进易错，凑整后口算完成', 'LOW',
     '加减,口算,整十整百', '数学'),
    ('裂项相消', '把1/[n(n+1)]型裂成两项差，求和时中间项相消',
     ('识别可裂结构', '按公式裂项', '错位相消', '收尾取极限'),
     '通分求和计算量大，裂项后只剩首尾两项', 'MEDIUM',
     '数列求和,分式,相消', '数学'),
    ('尾数判定', '只算末位数字判定结果/排除选项',
     ('算末位运算结果', '对照选项尾数', '必要时算末两位'), '完整计算耗时，尾数法秒判', 'LOW',
     '选择题,乘方,大数', '数学'),
    ('十字相乘', '二次三项式用十字交叉图示快速分解',
     ('列出二次项与常数项分解', '交叉相乘凑中项', '写出两因式'), '求根公式再回写较慢，十字相乘口算完成', 'LOW',
     '因式分解,二次,凑中项', '数学'),
    ('基准数法', '一堆相近数求和：取基准×个数+偏差和',
     ('选基准数', '数个数', '累加各数与基准的偏差'), '逐个相加易漏易错，基准法两步完成', 'LOW',
     '统计,平均数,求和', '数学'),
    ('估算法', '数量级估算锁定答案区间，选择题专用',
     ('粗算数量级', '放大缩小定区间', '排除区间外选项'), '精确计算慢，估算在选择题够用', 'MEDIUM',
     '选择题,近似,数量级', '数学/物理'),
    ('提公因式巧变形', '先提公因式再分解/约分，避免硬展开',
     ('找各项公因式', '提出后观察剩余结构', '继续分解或约分'), '先展开再分解走弯路，先提公因式少一步', 'LOW',
     '整式,约分,分解', '数学'),
    ('图像速解', '函数交点/最值/比较大小直接看图',
     ('画(或脑中构)函数图', '标关键点', '读图回答'), '代数求解需解方程，读图直观', 'LOW',
     '函数,交点,最值,比较', '数学'),
    ('特殊角值代入', '三角/复数问题代30°45°60°特殊值快验',
     ('记忆特殊角值表', '代入验证恒等式/选项', '排除错误项'), '推导恒等式慢，特殊值快验', 'LOW',
     '三角,恒等式,选择', '数学'),
    ('周期循环压缩', '大指数/重复结构找周期，把大问题压到一个周期内',
     ('算前几项找循环节', '确定周期T', '大指数取模T', '用周期内值回答'), '硬算大指数不现实，周期法一步到位', 'MEDIUM',
     '幂运算,循环,余数', '数学'),
    ('整数性质速判', '用奇偶性/整除特征快速判定',
     ('识别奇偶/整除问法', '套用判定规则(如3的整除看数字和)', '快速得出结论'), '枚举验证慢，性质判定一步出', 'LOW',
     '奇偶,整除,数字和', '数学'),
    ('约分先行', '分式运算先约分再通分，显著减小数字规模',
     ('逐项提取公因子', '先约分', '再通分/运算'), '先通分数字爆炸，约分先行数字小一半', 'LOW',
     '分式,约分,通分', '数学'),
]


# =============================================================
# 新表 DDL (3张, 幂等)
# =============================================================
_DDL = [
    '''CREATE TABLE IF NOT EXISTS mt_edu_thinking_methods (
        method_uid TEXT PRIMARY KEY, category TEXT NOT NULL, name TEXT NOT NULL,
        subject_scope TEXT, principle TEXT, steps_json TEXT, standard_compare TEXT,
        risk_level TEXT, risk_boundary TEXT, applicable_tags TEXT,
        status TEXT DEFAULT 'ACTIVE', round_no TEXT, created_at TEXT)''',
    '''CREATE TABLE IF NOT EXISTS mt_edu_thinking_examples (
        example_uid TEXT PRIMARY KEY, method_uid TEXT NOT NULL, qtype_id TEXT,
        subject TEXT, question_type TEXT, example_text TEXT, variant_analysis TEXT,
        depth TEXT, status TEXT DEFAULT 'ACTIVE', round_no TEXT, created_at TEXT)''',
    '''CREATE TABLE IF NOT EXISTS mt_edu_thinking_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT, round_no TEXT, step TEXT,
        detail TEXT, created_at TEXT)''',
]


def _log_row(conn, rn, step, detail):
    conn.execute('INSERT INTO mt_edu_thinking_log(round_no,step,detail,created_at) VALUES (?,?,?,?)',
                 (rn, step, str(detail)[:2000], _now()))


# =============================================================
# STEP 1 SEED — 教育域种子聚合 (4渠道, 本地)
# =============================================================
def collect_seeds(conn, stats):
    """SEED 四渠道：渠道1/4 跨库只读 DB_EDU(教辅数据源)；渠道2 EigenFlux
    topic_key 英文标签(education/math/exam/teach/learn/tutor...)+content中文词；
    渠道3 建议池教育类。全部本地, 零token。"""
    seeds = []
    edu = None
    try:
        edu = sqlite3.connect(f'file:{DB_EDU}?mode=ro', uri=True, timeout=30)
    except Exception:
        edu = None
    # 渠道1: 母题题型 × 模板 gap（题型未覆盖的方法→发觉目标）
    qrows = []
    if edu is not None:
        try:
            qrows = edu.execute(
                "SELECT qtype_id, subject, question_type, solving_model FROM "
                "mt_edu_sync_question_types WHERE status='ACTIVE'").fetchall()
        except Exception:
            qrows = []
    method_texts = {}
    for cat, tpls in (('UNCONVENTIONAL', _UNCONVENTIONAL_TEMPLATES),
                      ('QUICK_CALC', _QUICK_CALC_TEMPLATES)):
        for t in tpls:
            method_texts[t[0]] = (cat, t)
    covered = set()
    try:
        for r in conn.execute("SELECT name FROM mt_edu_thinking_methods WHERE status='ACTIVE'"):
            covered.add(r[0])
    except Exception:
        pass
    qtype_ctx = []
    for qid, subj, qtype, model in qrows[:12]:
        for name, (cat, tpl) in method_texts.items():
            if name in covered:
                continue
            # 母题的解题模型文本与方法 tags 有关联词 → 该题型需要此方法
            tags = tpl[5]
            hit = any(k in (model or '') for k in tags.split(','))
            if hit:
                seeds.append({'kind': 'QTYPE_GAP', 'category': cat, 'method': name,
                              'qtype': qtype, 'subject': subj, 'qtype_id': qid,
                              'title': f'[{subj}]{qtype}可引入{name}',
                              'score': 0.86})
        qtype_ctx.append((qid, subj, qtype))
    # 渠道2: EigenFlux 教育热度簇 (英文topic标签 + content中文关键词)
    _edu_topic_pat = ('education%', 'pedagogy%', 'math%', 'exam%', 'teach%', 'learn%',
                      'tutor%', 'study%', 'homework%', 'physics%', 'chemistry%',
                      'k12%', 'edu%')
    try:
        hot = conn.execute(
            "SELECT topic_key, COUNT(*) c FROM mt_ai_eigenflux_messages WHERE ("
            + " OR ".join("topic_key LIKE ?" for _ in _edu_topic_pat) +
            " OR content LIKE '%解题%' OR content LIKE '%巧算%' OR content LIKE '%速算%' "
            "OR content LIKE '%母题%' OR content LIKE '%解题技巧%') GROUP BY topic_key "
            "ORDER BY c DESC LIMIT ?", (*_edu_topic_pat, _MSG_TOP_K)).fetchall()
    except Exception:
        hot = []
    for tk, c in hot:
        if c >= 3:
            seeds.append({'kind': 'EF_HOT', 'category': classify_thinking(tk),
                          'method': None, 'qtype': None, 'subject': '综合',
                          'title': f'EigenFlux热话题:{tk[:30]}({c}条)',
                          'score': min(0.9, 0.7 + c / 1000.0)})
    # 渠道3: 建议池教育类 PENDING
    try:
        pend = conn.execute(
            "SELECT suggestion_uid, advice_content FROM mt_patrol_eigenflux_suggestions "
            "WHERE status='PENDING' AND (advice_content LIKE '%教辅%' OR advice_content LIKE '%解题%' "
            "OR advice_content LIKE '%题型%') LIMIT 20").fetchall()
    except Exception:
        pend = []
    for uid, adv in pend:
        seeds.append({'kind': 'POOL_PENDING', 'category': classify_thinking(adv),
                      'method': None, 'qtype': None, 'subject': '综合',
                      'title': f'建议池教育项:{str(adv)[:40]}', 'score': 0.75})
    # 渠道4: 教辅内容表学科覆盖 → 方法学科映射建议 (跨库 DB_EDU)
    subjects = []
    if edu is not None:
        try:
            subjects = [r[0] for r in edu.execute(
                "SELECT DISTINCT subject FROM mt_edu_sync_content WHERE status='ACTIVE'")]
        except Exception:
            subjects = []
    if not subjects:
        subjects = ['数学', '物理', '化学', '语文', '英语']
    if edu is not None:
        try:
            edu.close()
        except Exception:
            pass
    stats['edu_subjects'] = subjects
    # 三重去重 (kind/method/title前30)
    seen = set(); uniq = []
    for s in seeds:
        key = (s['kind'], s.get('method') or '', s['title'][:30])
        if key in seen:
            continue
        seen.add(key); uniq.append(s)
    stats['seeds'] = len(uniq)
    return uniq, qtype_ctx


# =============================================================
# STEP 2 SIMULATE — 模拟磋商(子进程, 沿用V代模式)
# =============================================================
def run_simulation(rn, stats):
    """子进程跑 simulation_sandbox_engine CLI(GAP_PROPOSAL)，正则抓共识度；
    非致命失败→fallback 0.66。不触发任何外部API(本地确定性模拟)。"""
    import subprocess
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
# STEP 3 DETECT/EXPLAIN/LINK — 三类产出 + 建议落池 + token初始化
# =============================================================
def extract_outputs(conn, rn, stats, seeds, consensus):
    """gaps = 方法型gap种子数 + 巧算缺补数(12-已有)：
    保证巧算/挂接在邪修gap耗尽后仍随轮巡渐进补齐至饱和。"""
    try:
        have_qck_n = conn.execute(
            "SELECT COUNT(*) FROM mt_edu_thinking_methods WHERE category='QUICK_CALC' "
            "AND status='ACTIVE'").fetchone()[0]
    except Exception:
        have_qck_n = 0
    try:
        have_lnk_n = conn.execute(
            "SELECT COUNT(*) FROM mt_edu_thinking_examples WHERE status='ACTIVE'").fetchone()[0]
        have_m_n = conn.execute(
            "SELECT COUNT(*) FROM mt_edu_thinking_methods WHERE status='ACTIVE'").fetchone()[0]
    except Exception:
        have_lnk_n = have_m_n = 0
    lnk_gap = 1 if (have_m_n > 0 and have_lnk_n < have_m_n * 7 and have_lnk_n < 32) else 0
    gaps = len([s for s in seeds if s.get('method')]) + \
        max(0, len(_QUICK_CALC_TEMPLATES) - int(have_qck_n)) + lnk_gap
    action, reason = sync_decision(consensus, _MIN_CONSENSUS, gaps)
    unc = qck = lnk = sugg = 0
    now = _now()
    stats['action'] = action

    if action == 'full_create':
        # a) 邪修方法落库 (gap种子驱动, CAP≤6)
        for s in seeds:
            m = s.get('method')
            if not m:
                continue
            tpl = None
            for t in _UNCONVENTIONAL_TEMPLATES:
                if t[0] == m:
                    tpl = t; cat = 'UNCONVENTIONAL'; break
            if tpl is None:
                continue  # 巧算不依赖gap, 见b)缺补齐
            if thinking_cap(unc, _MAX_UNCONVENTIONAL) <= 0:
                continue
            uid = method_uid_of(cat, m)
            if conn.execute('SELECT 1 FROM mt_edu_thinking_methods WHERE method_uid=?', (uid,)).fetchone():
                continue
            name, principle, steps, std_cmp, risk, tags, subjects = tpl
            if not thinking_wellformed(name, principle, steps, risk):
                continue
            conn.execute('''INSERT INTO mt_edu_thinking_methods
                (method_uid,category,name,subject_scope,principle,steps_json,standard_compare,
                 risk_level,risk_boundary,applicable_tags,status,round_no,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (uid, cat, name, subjects, principle,
                 json.dumps(list(steps), ensure_ascii=False), std_cmp,
                 risk, risk_boundary(risk), tags, 'ACTIVE', rn, now))
            unc += 1

        # b) 巧算方法缺补齐 (通用速算技巧直接入池, CAP≤6/轮, 至12法齐)
        try:
            have_qck = {r[0] for r in conn.execute(
                "SELECT name FROM mt_edu_thinking_methods WHERE category='QUICK_CALC' AND status='ACTIVE'")}
        except Exception:
            have_qck = set()
        for t in _QUICK_CALC_TEMPLATES:
            if thinking_cap(qck, _MAX_QUICK_CALC) <= 0:
                break
            if t[0] in have_qck:
                continue
            uid = method_uid_of('QUICK_CALC', t[0])
            if conn.execute('SELECT 1 FROM mt_edu_thinking_methods WHERE method_uid=?', (uid,)).fetchone():
                continue
            name, principle, steps, std_cmp, risk, tags, subjects = t
            if not thinking_wellformed(name, principle, steps, risk):
                continue
            conn.execute('''INSERT INTO mt_edu_thinking_methods
                (method_uid,category,name,subject_scope,principle,steps_json,standard_compare,
                 risk_level,risk_boundary,applicable_tags,status,round_no,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (uid, 'QUICK_CALC', name, subjects, principle,
                 json.dumps(list(steps), ensure_ascii=False), std_cmp,
                 risk, risk_boundary(risk), tags, 'ACTIVE', rn, now))
            qck += 1

        # c) 母题挂接 + 变式分析 (CAP≤8, 题型跨库 DB_EDU)
        methods = conn.execute(
            "SELECT method_uid, category, name, applicable_tags, risk_level, subject_scope "
            "FROM mt_edu_thinking_methods WHERE status='ACTIVE'").fetchall()
        qtypes = []
        try:
            edu2 = sqlite3.connect(f'file:{DB_EDU}?mode=ro', uri=True, timeout=30)
            qtypes = edu2.execute(
                "SELECT qtype_id, subject, question_type, solving_model FROM "
                "mt_edu_sync_question_types WHERE status='ACTIVE'").fetchall()
            edu2.close()
        except Exception:
            qtypes = []
        for mu, cat, mname, tags, rl, scope in methods:
            if thinking_cap(lnk, _MAX_MOTHER_LINKS) <= 0:
                break
            for qid, subj, qtype, model in qtypes:
                if thinking_cap(lnk, _MAX_MOTHER_LINKS) <= 0:
                    break
                tag_hit = mother_topic_match(qtype, tags + ',' + mname)
                subj_hit = bool(subj) and bool(scope) and subj in str(scope)
                if not (tag_hit or subj_hit):
                    continue
                euid = 'ETH-' + hashlib.md5(f'EX|{mu}|{qid}'.encode()).hexdigest()[:14]
                if conn.execute('SELECT 1 FROM mt_edu_thinking_examples WHERE example_uid=?', (euid,)).fetchone():
                    continue
                quality = 0.9 if rl == 'LOW' else (0.78 if rl == 'MEDIUM' else 0.62)
                depth = variant_depth(quality)
                layers = {'A': ('基础母题精讲', '同构变式(换数字/换背景)', '逆向变式(由结论反推条件)'),
                          'B': ('基础母题精讲', '同构变式(换数字/换背景)'),
                          'C': ('基础母题精讲',)}[depth]
                example = (f'母题[{qtype}]示例: 参照题型库 answer_template 套用「{mname}」; '
                           f'解题模型对照: {model or "(库内无标准模型, 本方法为补充)"}')
                variant = ' → '.join(layers) + f'; 风险提示: {risk_boundary(rl)}'
                conn.execute('''INSERT INTO mt_edu_thinking_examples
                    (example_uid,method_uid,qtype_id,subject,question_type,example_text,
                     variant_analysis,depth,status,round_no,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                    (euid, mu, qid, subj, qtype, example, variant, depth, 'ACTIVE', rn, now))
                lnk += 1

    # d) 教辅同步建议落池 (共识不足或已满额时也落建议, ETH-前缀)
    sugg_pool = _MAX_SUGGESTIONS
    for s in seeds:
        if thinking_cap(sugg, sugg_pool) <= 0:
            break
        uid = 'ETH-' + hashlib.md5(f"SG|{s['kind']}|{s['title']}".encode()).hexdigest()[:14]
        if conn.execute('SELECT 1 FROM mt_patrol_eigenflux_suggestions WHERE suggestion_uid=?', (uid,)).fetchone():
            continue
        try:
            conn.execute('''INSERT INTO mt_patrol_eigenflux_suggestions
                (suggestion_uid,finding_type,finding_file,finding_line,finding_message,
                 finding_severity,expert_name,expert_domain,advice_category,advice_content,
                 quality_score,status,round_no,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (uid, 'edu_thinking', f"ETH-{s['kind']}", 0,
                 f"教辅思维联想:{s['kind']}", 'MEDIUM' if s['score'] >= 0.8 else 'LOW',
                 '教辅思维引擎', 'EDUCATION', 'EDU_THINKING_SYNC',
                 f"【{s['category']}】{s['title']} (score={s['score']:.2f})",
                 min(1.0, s['score']), 'PENDING', rn, now, now))
            sugg += 1
        except Exception as e:
            _log(f'sugg fail: {type(e).__name__}'); continue

    # e) token_savings 首行初始化 (沿用V代, INSERT OR IGNORE幂等)
    try:
        day = datetime.now().strftime('%Y-%m-%d')
        conn.execute('INSERT OR IGNORE INTO mt_local_ai_token_savings(savings_id,day,tokens_saved,inference_count,created_at,updated_at) '
                     'VALUES (1,?,?,0,?,?)', (day, 0, now, now))
    except Exception:
        try:
            conn.execute('INSERT OR IGNORE INTO mt_local_ai_token_savings(day,tokens_saved,inference_count,created_at,updated_at) '
                         'VALUES (?,0,0,?,?)', (day, now, now))
        except Exception:
            pass

    stats.update({'unconventional': unc, 'quick_calc': qck,
                  'mother_links': lnk, 'suggestions': sugg})
    _log_row(conn, rn, 'EXTRACT',
             f'action={action} reason={reason} unc={unc} qck={qck} lnk={lnk} sugg={sugg}')
    return action


# =============================================================
# STEP 4 VERIFY — 3一致性
# =============================================================
def verify_outputs(conn, stats):
    ok = 0; fail = 0
    # V1 方法行风险边界合法
    bad_risk = conn.execute(
        "SELECT COUNT(*) FROM mt_edu_thinking_methods WHERE status='ACTIVE' "
        "AND risk_boundary NOT LIKE '风险%'").fetchone()[0]
    if bad_risk == 0: ok += 1
    else: fail += 1
    # V2 挂接双表对应 (example.method_uid 必须存在于 methods)
    orphan = conn.execute(
        "SELECT COUNT(*) FROM mt_edu_thinking_examples e WHERE NOT EXISTS "
        "(SELECT 1 FROM mt_edu_thinking_methods m WHERE m.method_uid=e.method_uid)").fetchone()[0]
    if orphan == 0: ok += 1
    else: fail += 1
    # V3 挂接深度合法
    bad_depth = conn.execute(
        "SELECT COUNT(*) FROM mt_edu_thinking_examples WHERE depth NOT IN ('A','B','C')").fetchone()[0]
    if bad_depth == 0: ok += 1
    else: fail += 1
    stats['verify_ok'] = ok; stats['verify_fails'] = fail
    _log_row(conn, stats['round'], 'VERIFY', f'ok={ok} fail={fail}')
    return fail == 0


# =============================================================
# STEP 5 FOSSILIZE — 脑库投喂
# =============================================================
def fossilize(conn, rn, stats):
    title = (f"教辅思维轮巡: 邪修模型{stats.get('unconventional',0)}+巧算{stats.get('quick_calc',0)}"
             f"+母题挂接{stats.get('mother_links',0)}+建议{stats.get('suggestions',0)} "
             f"共识{stats.get('consensus',0)} {stats.get('action','')}")
    try:
        conn.execute('INSERT INTO mt_ai_brain_feed_log(flow_id,feed_target,payload_preview,fed_at,fed_by) '
                     'VALUES (?,?,?,?,?)',
                     (f'flow_edu_thinking_{rn}', 'AI_BRAIN', title[:1000], _now(), 'EDU_THINKING_ENGINE'))
    except Exception as e:
        _log(f'feed fail: {type(e).__name__}')
    _log_row(conn, rn, 'FOSSILIZE', 'done')


# =============================================================
# 主流程
# =============================================================
def ensure_tables(conn):
    for ddl in _DDL:
        conn.execute(ddl)
    conn.commit()


def run_once():
    for pragma in ('PRAGMA journal_mode=WAL', 'PRAGMA busy_timeout=60000'):
        try:
            conn = sqlite3.connect(DB_MAIN, timeout=60)
            conn.execute(pragma)
        except Exception as e:
            _log(f'db connect fail: {e}'); return
        break
    rn = datetime.now().strftime('%Y%m%d_%H%M%S')
    stats = {'round': rn}
    try:
        ensure_tables(conn)
        _log_row(conn, rn, 'SEED', 'start')
        seeds, qctx = collect_seeds(conn, stats)
        _log_row(conn, rn, 'SEED', f"seeds={len(seeds)} subjects={stats.get('edu_subjects', [])[:6]}")
        consensus = run_simulation(rn, stats)
        _log_row(conn, rn, 'SIMULATE', f'consensus={consensus}')
        extract_outputs(conn, rn, stats, seeds, consensus)
        verify_outputs(conn, stats)
        fossilize(conn, rn, stats)
        conn.commit()
        _log(f"round {rn} 完成: seeds={stats.get('seeds')} consensus={consensus} "
             f"action={stats.get('action')} unc={stats.get('unconventional')} "
             f"qck={stats.get('quick_calc')} lnk={stats.get('mother_links')} "
             f"sugg={stats.get('suggestions')} verify_ok={stats.get('verify_ok')} "
             f"verify_fails={stats.get('verify_fails')}")
    except Exception as e:
        _log(f'round error: {type(e).__name__}: {e}')
        try:
            _log_row(conn, rn, 'ERROR', f'{type(e).__name__}: {e}')
            conn.commit()
        except Exception:
            pass
    finally:
        conn.close()


def run_daemon(interval=900):
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
