"""
core/adaptive_learning.py — 仙女座跨领域自适应学习引擎
=======================================================
从日语 (_pick_adaptive_levels) 抽象出来的通用多领域版本。

设计:
  - 每个领域有自己的 grading scale (beginner → advanced 有序列表)
  - 每个领域映射到对应的内容表 (table + level_column)
  - 用户级别推断优先级: 显式参数 > USER_LEVEL_OVERRIDES > progress 表众数 > 兜底
  - 返回 "上级 + 本级" (不给下级) — caopw N2 用户不看 N3/N4/N5

领域映射 (education_type → grading scale):
  japanese    → N6, N5, N4, N3, N2, N1, N0      (JLPT)
  english     → A1, A2, B1, B2, C1               (CEFR, 由 difficulty 1-5 映射)
  k12         → G1, G2, G3, G4, G5, G6, G7, G8, G9
  higher      → university_1..4, graduate_1..2
  continuing  → beginner, intermediate, advanced  (再教育)

用法:
  from core.adaptive_learning import pick_adaptive_levels, get_domain_scale

  levels, primary = pick_adaptive_levels(
      user={'username':'caopw'},
      education_type='japanese',
      explicit_level=None
  )
  # → ['N2', 'N1'], 'N2'
"""
import os
import sqlite3
from typing import Optional, Tuple, List, Dict, Any


# ============================================================================
# 1) 各领域 grading scale (BEGINNER → ADVANCED 有序)
# ============================================================================

DOMAIN_SCALES: Dict[str, List[str]] = {
    'japanese':   ['N6', 'N5', 'N4', 'N3', 'N2', 'N1', 'N0'],  # JLPT
    'english':    ['A1', 'A2', 'B1', 'B2', 'C1'],              # CEFR
    'k12':        ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9'],
    'higher':     ['university_1', 'university_2', 'university_3', 'university_4',
                   'graduate_1', 'graduate_2'],
    'continuing': ['beginner', 'intermediate', 'advanced'],
    # === 新增 6 领域 (difficulty 1-5 映射) ===
    'steam':      ['G7', 'G8', 'G9', 'adult', 'university_1', 'university_2'],
    'arts':       ['G5', 'G6', 'G7', 'G8', 'G9', 'adult'],
    'mind':       ['adult'],
    'business':   ['adult', 'university_3', 'university_4', 'graduate_1', 'graduate_2'],
    'medical':    ['adult', 'university_1', 'university_2', 'university_3', 'university_4', 'graduate_1'],
    'law':        ['adult', 'university_2', 'university_3', 'university_4', 'graduate_1', 'graduate_2'],
}

# 领域中文显示名
DOMAIN_LABELS: Dict[str, str] = {
    'japanese':   '日本語教育',
    'english':    '成人英語',
    'k12':        'K12 中小学',
    'higher':     '高等教育',
    'continuing': '再教育·终身学习',
    'steam':      'STEAM · AI',
    'arts':       '艺术与人文',
    'mind':       '心理与健康',
    'business':   '商科与创业',
    'medical':    '医学与生命',
    'law':        '法律与公共',
}


# ============================================================================
# 2) ENGLISH: difficulty (1-5) ↔ CEFR (A1-C1) 双向映射
# ============================================================================

DIFFICULTY_TO_CEFR: Dict[int, str] = {1: 'A1', 2: 'A2', 3: 'B1', 4: 'B2', 5: 'C1'}
CEFR_TO_DIFFICULTY: Dict[str, int] = {v: k for k, v in DIFFICULTY_TO_CEFR.items()}


# ============================================================================
# 3) USER_LEVEL_OVERRIDES — 特殊用户的领域级别映射 (多领域)
# ============================================================================

# 每个用户可以在不同领域有不同级别
# {username: {education_type: {'target': str, 'allow': [str], 'weights': {str: float}}}}
USER_LEVEL_OVERRIDES: Dict[str, Dict[str, Dict[str, Any]]] = {
    'caopw': {
        'japanese':  {'target': 'N2', 'allow': ['N2', 'N1'],          'weights': {'N2': 0.75, 'N1': 0.25}},
        'english':   {'target': 'B1', 'allow': ['B1', 'B2'],          'weights': {'B1': 0.70, 'B2': 0.30}},
        'continuing':{'target': 'intermediate', 'allow': ['intermediate','advanced'], 'weights': {'intermediate': 0.70, 'advanced': 0.30}},
    },
}


# ============================================================================
# 4) 内容表映射 — 每个领域对应的可查内容表
# ============================================================================

# (table_name, level_column, domain_scale_key)
CONTENT_TABLES: Dict[str, List[Tuple[str, str]]] = {
    'japanese': [
        ('jp_vocabulary',  'level'),
        ('jp_grammar',     'level'),
        ('jp_listening',   'level'),
        ('jp_reading',     'level'),
    ],
    'english': [
        ('lang_en_vocabulary', 'difficulty'),
        ('lang_en_grammar',    'difficulty'),
        ('lang_en_reading',    'difficulty'),
        ('lang_en_speaking',   'difficulty'),
        ('lang_en_writing',    'difficulty'),
    ],
    'k12': [
        ('question_bank', 'difficulty'),   # 1-5, 映射 G1-G9
    ],
    'higher': [
        ('question_bank', 'difficulty'),   # 1-5, 映射 university/graduate
    ],
    'continuing': [
        ('question_bank', 'difficulty'),   # 1-5, 映射 beginner/intermediate/advanced
    ],
}


# ============================================================================
# 5) DB 路径解析 (复用 db_path 模块)
# ============================================================================

def _get_mtscos_db() -> str:
    try:
        from core.db_path import get_db_path
        path = get_db_path('mtscos.db')
        if path and os.path.exists(path):
            return path
    except Exception:
        pass
    # fallback
    for cand in (
        os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
            '..', '_runtime', 'databases', 'Database', 'mtscos.db')),
        'mtscos.db',
    ):
        if os.path.exists(cand):
            return cand
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mtscos.db')


def _conn():
    c = sqlite3.connect(_get_mtscos_db(), timeout=30)
    c.execute("PRAGMA journal_mode=WAL")
    c.row_factory = sqlite3.Row
    return c


# ============================================================================
# 6) 核心 API — pick_adaptive_levels
# ============================================================================

def get_domain_scale(education_type: str) -> List[str]:
    """返回领域 grading scale (beginner → advanced)"""
    return DOMAIN_SCALES.get(education_type, [])


def pick_adaptive_levels(
    user: Optional[Dict[str, Any]],
    education_type: str,
    explicit_level: Optional[str] = None,
    allow_below: bool = False,
) -> Tuple[List[str], str]:
    """
    推断用户在指定领域的自适应级别列表。

    Args:
        user:            user dict (含 username / id / user_id)
        education_type:  领域 key ('japanese' / 'english' / 'k12' / 'higher' / 'continuing')
        explicit_level:  前端显式指定的级别 (None = 自适应)
        allow_below:     是否允许包含下级内容 (默认 False)

    Returns:
        (levels_list, primary_level)
        levels_list  用于 SQL WHERE level IN (?,?,...)
        primary_level 用于前端显示
    """
    scale = DOMAIN_SCALES.get(education_type)
    if not scale:
        # 未知领域 → 回退到仅显式或空
        return ([explicit_level], explicit_level) if explicit_level else ([], '')

    # --- Step 1: 显式指定 ---
    if explicit_level and explicit_level in scale:
        return [explicit_level], explicit_level

    # --- Step 2: USER_LEVEL_OVERRIDES (多领域) ---
    uname = (user or {}).get('username', '') or ''
    domain_overrides = USER_LEVEL_OVERRIDES.get(uname, {})
    if education_type in domain_overrides:
        ov = domain_overrides[education_type]
        return ov['allow'], ov['target']

    # --- Step 3: progress 表众数 (轻量推断) ---
    inferred = _infer_from_progress(user, education_type)
    if inferred and inferred in scale:
        primary = inferred
    else:
        primary = scale[0]  # 兜底: 最基础级别

    idx = scale.index(primary)

    if allow_below:
        lo = max(0, idx - 1)
        hi = min(len(scale), idx + 2)
    else:
        # 严格: 本级 + 向上 1 (不给下级)
        lo = idx
        hi = min(len(scale), idx + 2)

    return scale[lo:hi], primary


def _infer_from_progress(user: Optional[Dict], education_type: str) -> Optional[str]:
    """从 progress / 内容表推断用户级别 (简化版)"""
    if not user:
        return None
    uid = user.get('id') or user.get('user_id')
    if not uid:
        return None
    try:
        conn = _conn()
        cur = conn.cursor()

        # 通用: 查各领域 progress 表
        progress_tables = {
            'japanese': ['jp_vocabulary_progress', 'jp_grammar_progress',
                         'jp_kana_progress', 'jp_listening_records', 'jp_reading_records'],
            'english':  [],   # English 暂无 progress 表
            'k12':      [],   # K12 暂无 progress 表 (表全空)
            'higher':   [],
            'continuing': [],
        }
        tables = progress_tables.get(education_type, [])
        counts: Dict[str, int] = {}
        for tbl in tables:
            try:
                rows = cur.execute(
                    f"SELECT level, COUNT(*) c FROM {tbl} "
                    f"WHERE user_id=? GROUP BY level ORDER BY c DESC",
                    (uid,)).fetchall()
                for lv, c in rows:
                    counts[lv] = counts.get(lv, 0) + c
            except Exception:
                pass
        conn.close()
        if counts:
            return max(counts, key=counts.get)
    except Exception:
        pass
    return None


# ============================================================================
# 7) 构建 WHERE IN 子句辅助
# ============================================================================

def build_where_in(column: str, values: List[str]) -> Tuple[str, Tuple]:
    """
    生成 "WHERE column IN (?, ?, ...)" + params tuple。
    空 values 返回 ('', ()) — 调用方需自行检查。
    """
    if not values:
        return '', ()
    ph = ','.join(['?'] * len(values))
    return f"{column} IN ({ph})", tuple(values)


def build_sql_for_domain(
    education_type: str,
    levels: List[str],
    level_column: str = 'level',
    user: Optional[Dict] = None,
    extra_where: str = '',
    extra_params: Tuple = (),
    order_by: str = None,
) -> Tuple[str, Tuple]:
    """
    为指定领域构建自适应 SQL。

    English 特殊处理: difficulty 1-5 ↔ CEFR A1-C1
      输入 levels=['B1','B2'] → WHERE difficulty IN (3,4)
    """
    params = []

    # English: CEFR → difficulty 数字
    if education_type == 'english':
        diffs = [CEFR_TO_DIFFICULTY.get(l) for l in levels if l in CEFR_TO_DIFFICULTY]
        levels_sql, levels_params = build_where_in('difficulty', diffs)
        if levels_sql:
            sql = f"SELECT * FROM lang_en_vocabulary WHERE {levels_sql}"
            params = list(levels_params)
        else:
            sql = "SELECT * FROM lang_en_vocabulary WHERE 1=1"
    else:
        levels_sql, levels_params = build_where_in(level_column, levels)
        sql = "SELECT * FROM question_bank WHERE 1=1"  # 通用兜底
        if levels_sql:
            sql += f" AND {levels_sql}"
            params = list(levels_params)

    if extra_where:
        sql += f" AND {extra_where}"
        params += list(extra_params)

    if order_by:
        sql += f" ORDER BY {order_by}"
    else:
        sql += " ORDER BY rowid"

    return sql, tuple(params)


# ============================================================================
# 8) 便捷函数: 直接查某领域内容 (高级 API)
# ============================================================================

def query_domain_content(
    user: Optional[Dict],
    education_type: str,
    table: str,
    explicit_level: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    一站式查询: 自动推断级别 → 构建 SQL → 返回 dict。

    Returns:
        {'success': True, 'data': [...], 'adaptive': {...}, 'sql': str, 'params': [...]}
    """
    scale = DOMAIN_SCALES.get(education_type, [])
    levels, primary = pick_adaptive_levels(user, education_type, explicit_level)

    # English 特殊: CEFR → difficulty
    if education_type == 'english':
        diffs = [CEFR_TO_DIFFICULTY.get(l) for l in levels if l in CEFR_TO_DIFFICULTY]
        level_col = 'difficulty'
        sql_levels = [str(d) for d in diffs]
    else:
        sql_levels = levels
        # 取表的 level 列 (默认 'level')
        level_col = 'level'
        tables = CONTENT_TABLES.get(education_type, [])
        for tname, lcol in tables:
            if tname == table:
                level_col = lcol
                break

    if not sql_levels:
        return {'success': False, 'error': f'no levels for {education_type}'}

    try:
        conn = _conn()
        cur = conn.cursor()
        sql, params = build_where_in(level_col, sql_levels)
        full_sql = f"SELECT * FROM {table} WHERE {sql} LIMIT {limit}" if sql else f"SELECT * FROM {table} LIMIT {limit}"
        rows = [dict(r) for r in cur.execute(full_sql, params).fetchall()]
        conn.close()

        return {
            'success': True,
            'data': rows,
            'adaptive': {
                'education_type': education_type,
                'primary_level': primary,
                'levels_served': levels,
                'explicit_level': explicit_level,
                'domain_label': DOMAIN_LABELS.get(education_type, education_type),
            },
            'sql': full_sql,
            'params': list(params),
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ============================================================================
# 9) progress 表名映射 (供外部导入使用)
# ============================================================================

PROGRESS_TABLES: Dict[str, List[str]] = {
    'japanese': ['jp_vocabulary_progress', 'jp_grammar_progress',
                 'jp_kana_progress', 'jp_listening_records', 'jp_reading_records'],
    'english':  [],
    'k12':      [],
    'higher':   [],
    'continuing': [],
}


# ============================================================================
# 10) 仙女座题库检测 — detect_andromeda_question_bank
# ============================================================================

# 仙女座 11 领域 → question_bank.category 映射
# (主 category, [备选 category])
ANDROMEDA_QB_CATEGORY_MAP: Dict[str, Tuple[str, List[str]]] = {
    'k12':        ('中小学',     ['小学', '初中', '高中', 'K12']),
    'higher':     ('考研',       ['大学', '研究生', '大学公共课']),
    'continuing': ('管理学',     ['管理学', '人力资源', '项目管理']),
    'japanese':   (None,        []),   # 独立 jp_* 表, question_bank 不承载
    'english':    (None,        []),   # 独立 lang_en_* 表
    'steam':      ('信息技术',   ['信息技术', '计算机', 'Python']),
    'arts':       ('艺术',       ['艺术', '音乐', '美术']),
    'mind':       ('心理学',     ['心理学']),
    'business':   ('金融',       ['金融', '管理学', '会计']),
    'medical':    ('医学',       ['医学', '护理学']),
    'law':        ('法律',       ['法律', '公务员']),
}

# 各领域目标难度分布 (difficulty 1-5)
TARGET_DIFFICULTY_DIST: Dict[str, List[int]] = {
    # 目标 [diff1_pct, diff2_pct, diff3_pct, diff4_pct, diff5_pct] — 总和 100
    'k12':        [15, 25, 30, 20, 10],   # 低龄段偏易
    'higher':     [5,  15, 35, 30, 15],   # 大学偏中高
    'continuing': [10, 20, 35, 25, 10],
    'steam':      [5,  15, 30, 30, 20],   # 技术类偏难
    'arts':       [15, 25, 30, 20, 10],
    'mind':       [10, 20, 35, 25, 10],
    'business':   [5,  15, 35, 30, 15],
    'medical':    [5,  15, 30, 30, 20],
    'law':        [5,  15, 30, 30, 20],
}


def detect_andromeda_question_bank() -> Dict[str, Any]:
    """
    仙女座 11 领域题库全景检测报告。

    Returns:
        {
            'summary': {total_questions, domains_covered, coverage_pct, ...},
            'domains': {
                'business': {
                    'domain': 'business', 'label': '商科与创业',
                    'primary_category': '金融',
                    'total': 300, 'coverage_pct': 100.0,
                    'difficulty_dist': {1: 32, 2: 72, 3: 111, 4: 66, 5: 19},
                    'difficulty_match': True,   # 分布是否接近目标
                    'missing_levels': [],
                    'quality_flags': ['ENCRYPTED_SUBJECT_IN_ITEMS'],
                    'categories_found': ['金融', '管理学'],
                },
                ...
            },
            'issues': [
                {'type': 'DOMAIN_NO_CATEGORY', 'domain': 'k12', 'message': 'K12 无题库 category, 需新建'},
                {'type': 'DOMAIN_NO_CATEGORY', 'domain': 'steam', ...},
                ...
            ],
            'recommendations': [
                '为 k12 领域新增 category=中小学 题库 seed (~300 题)',
                ...
            ],
        }
    """
    report: Dict[str, Any] = {
        'summary': {},
        'domains': {},
        'issues': [],
        'recommendations': [],
        'generated_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
    }

    conn = _conn()
    cur = conn.cursor()

    # --- 基础总数 ---
    total_qb = cur.execute('SELECT COUNT(*) FROM question_bank').fetchone()[0]
    report['summary']['total_questions'] = total_qb

    # 所有 category
    all_cats = {r[0] for r in cur.execute('SELECT DISTINCT category FROM question_bank').fetchall()}
    report['summary']['existing_categories'] = sorted(all_cats)
    report['summary']['num_existing_categories'] = len(all_cats)

    # --- 逐领域检测 ---
    domains_with_content = 0
    for edu_key in DOMAIN_SCALES.keys():
        cat_map = ANDROMEDA_QB_CATEGORY_MAP.get(edu_key)
        primary_cat, alt_cats = cat_map or (None, [])

        domain_report = {
            'domain': edu_key,
            'label': DOMAIN_LABELS.get(edu_key, edu_key),
            'codename': _CODES.get(edu_key, ''),
            'primary_category': primary_cat,
            'total': 0,
            'coverage_pct': 0.0,
            'difficulty_dist': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            'difficulty_match': False,
            'missing_levels': [],
            'quality_flags': [],
            'categories_found': [],
            'source_table': 'question_bank',
            'independent_tables': [],
        }

        # 1) 独立表检测 (日语/英语)
        independent = []
        if edu_key == 'japanese':
            for tbl in ['jp_vocabulary', 'jp_grammar', 'jp_listening', 'jp_reading']:
                try:
                    c = cur.execute(f'SELECT COUNT(*) FROM {tbl}').fetchone()[0]
                    if c > 0:
                        independent.append({'table': tbl, 'count': c})
                except Exception:
                    pass
        elif edu_key == 'english':
            for tbl in ['lang_en_vocabulary', 'lang_en_grammar', 'lang_en_reading',
                        'lang_en_speaking', 'lang_en_writing']:
                try:
                    c = cur.execute(f'SELECT COUNT(*) FROM {tbl}').fetchone()[0]
                    if c > 0:
                        independent.append({'table': tbl, 'count': c})
                except Exception:
                    pass
        domain_report['independent_tables'] = independent

        # 2) category 匹配 + 计数
        all_match_cats = [primary_cat] + alt_cats if primary_cat else []
        all_match_cats = [c for c in all_match_cats if c]  # 去 None
        found_cats = []
        if all_match_cats:
            placeholders = ','.join(['?'] * len(all_match_cats))
            try:
                rows = cur.execute(
                    f"SELECT category, difficulty, COUNT(*) c FROM question_bank "
                    f"WHERE category IN ({placeholders}) GROUP BY category, difficulty",
                    all_match_cats
                ).fetchall()
                total = 0
                for cat, diff, cnt in rows:
                    found_cats.append(cat)
                    domain_report['difficulty_dist'][diff] = \
                        domain_report['difficulty_dist'].get(diff, 0) + cnt
                    total += cnt
                domain_report['total'] = total
                domain_report['categories_found'] = sorted(set(found_cats))
            except Exception:
                pass

        # 3) coverage
        if independent:
            domain_report['total'] += sum(t['count'] for t in independent)
            domain_report['source_table'] = f'question_bank + {len(independent)} 独立表'
            domains_with_content += 1
        elif domain_report['total'] > 0:
            domains_with_content += 1

        # 4) difficulty match (与目标分布偏差 < 20%)
        target = TARGET_DIFFICULTY_DIST.get(edu_key)
        if target and sum(domain_report['difficulty_dist'].values()) >= 20:
            actual = [domain_report['difficulty_dist'].get(d, 0) for d in (1,2,3,4,5)]
            actual_total = sum(actual)
            if actual_total > 0:
                actual_pct = [a/actual_total*100 for a in actual]
                deviations = [abs(a - t) for a, t in zip(actual_pct, target)]
                domain_report['difficulty_match'] = max(deviations) < 20
            missing = [d for d in (1,2,3,4,5) if domain_report['difficulty_dist'].get(d, 0) == 0]
            domain_report['missing_levels'] = missing

        # 5) 质量检测: items 表 subject 被 MTENC 加密
        try:
            enc = cur.execute(
                "SELECT COUNT(*) FROM question_bank_items WHERE subject LIKE 'MTENC:%'"
            ).fetchone()[0]
            if enc > 0:
                domain_report['quality_flags'].append('ITEMS_SUBJECT_ENCRYPTED')
        except Exception:
            pass

        # 6) coverage % (以 150 题为基准目标)
        target_q = 150
        if independent:
            domain_report['coverage_pct'] = min(100.0, domain_report['total'] / target_q * 100)
        elif primary_cat:
            domain_report['coverage_pct'] = min(100.0, domain_report['total'] / target_q * 100)
        else:
            domain_report['coverage_pct'] = 100.0 if domain_report['total'] > 0 else 0.0

        # 7) issue 生成
        if not primary_cat and not independent:
            report['issues'].append({
                'type': 'NO_SOURCE',
                'domain': edu_key,
                'message': f"{DOMAIN_LABELS.get(edu_key, edu_key)} ({edu_key}) 无对应 category 也无独立表 — 题库缺口",
                'severity': 'HIGH',
            })
        elif domain_report['total'] == 0 and not independent:
            report['issues'].append({
                'type': 'EMPTY_DOMAIN',
                'domain': edu_key,
                'primary_category': primary_cat,
                'message': f"{DOMAIN_LABELS.get(edu_key, edu_key)} ({edu_key}) category='{primary_cat}' 不存在",
                'severity': 'HIGH',
            })
        if domain_report['missing_levels']:
            report['issues'].append({
                'type': 'MISSING_DIFFICULTY',
                'domain': edu_key,
                'message': f"缺少 difficulty={domain_report['missing_levels']}",
                'severity': 'MEDIUM',
            })

        report['domains'][edu_key] = domain_report

    # --- summary ---
    report['summary']['domains_with_content'] = domains_with_content
    report['summary']['total_domains'] = len(DOMAIN_SCALES)
    report['summary']['overall_coverage_pct'] = round(domains_with_content / len(DOMAIN_SCALES) * 100, 1)

    # --- recommendations ---
    for issue in report['issues']:
        if issue['type'] in ('NO_SOURCE', 'EMPTY_DOMAIN'):
            edu = issue['domain']
            rec = f"为 {DOMAIN_LABELS.get(edu, edu)} ({edu}) 新增 category 题库 seed (~300 题, difficulty 1-5 均匀)"
            report['recommendations'].append(rec)
        elif issue['type'] == 'MISSING_DIFFICULTY':
            edu = issue['domain']
            lvls = issue['message'].split('=')[1]
            rec = f"为 {DOMAIN_LABELS.get(edu, edu)} 补齐 difficulty={lvls} 难度的题目"
            report['recommendations'].append(rec)

    conn.close()
    return report


# constellation codename map (供检测报告引用)
_CODES = {
    'k12': '仙女座·昴星团', 'higher': '仙女座·壁宿二', 'continuing': '仙女座·M32',
    'japanese': '仙女座·奎宿九', 'english': '仙女座·天大将军',
    'steam': '仙女座·参宿四', 'arts': '仙女座·心宿二', 'mind': '仙女座·天津四',
    'business': '仙女座·五车二', 'medical': '仙女座·参宿七', 'law': '仙女座·轩辕十四',
}
