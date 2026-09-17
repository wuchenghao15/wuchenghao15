"""
仙女座星系子系统 — 合规审查引擎 (C1~C7 硬约束代码化)

所有待发布内容必须过此 Pipeline, 返回 overall:
  PASS   → 可发布
  BLOCK  → 强制阻断 (直接 reject)
  REVIEW → 人工审批队列

flow_id: galaxy_compliance_engine
version: v23.1.0 (C5 平台差异化: 抖音/小红书/B站各自词库)
合规依据:
  C1 《著作权法》— 不搬运不抄袭 (原创性 4 层审查)
  C2 《著作权法》— 引用必须标注出处
  C3 《广告法》— 不使用极限词
  C4 《教育法》— 学科类内容走审批
  C5 平台社区规范 — 按平台差异化审查 (抖音/小红书/B站)
  C6 《个人信息保护法》— 不涉及隐私
  C7 内容来源授权 — 仅自有/授权/公有领域
"""
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, 'database', 'app.db')


# ============================================================
# C3 极限词词库 (广告法) — 精确词组, 避免单字误命中
# ============================================================
EXTREME_WORDS = [
    # 绝对化用语 (广告法第九条)
    '最高级', '最高档', '最佳', '最优', '最好', '最快', '最强', '最全',
    '最低', '最先进', '最低价', '最划算', '最畅销', '最热门', '最火',
    '顶级', '顶尖', '顶级', '极致', '极品', '完美', '绝对', '永久',
    # 排名/唯一性
    '第一', '第一流', '唯一', '独一无二', '首个', '首选', '首创',
    '全国第一', '全球第一', '世界第一', '排名第一', '领先', '遥遥领先',
    '全球领先', '国际领先', '业界领先', '市场领先',
    # 保证性用语
    '包教包会', '包治百病', '药到病除', '立竿见影', '无效退款',
    '保证', '稳赚不赔', '零风险', '无风险', '百分百', '100%',
    # 煽动性
    '必看', '必学', '必做', '必须', '不容错过', '错过后悔',
    '抢爆', '秒杀', '清仓', '甩卖', '吐血价', '跳楼价', '一折到底',
    '史无前例', '绝无仅有', '前无古人', '后无来者',
    # 虚假承诺
    '万能', '特效', '神效', '奇效', '根治', '包好', '包痊愈',
]

# C4 学科类关键词 (需人工审批)
SUBJECT_KEYWORDS = [
    '高考', '中考', '小升初', '数学竞赛', '物理竞赛',
    '英语四六级', '考研', '公务员', '教师资格',
    'K12', '义务教育', '学科培训', '课外辅导',
]

# C5 平台社区红线 — 按平台差异化 (v23.1.0)
# 通用红线 (所有平台都 BLOCK)
COMMON_RED_LINES = [
    '赌博', '博彩', '色情', '暴力', '恐怖',
    '毒品', '枪支', '管制刀', '违法犯罪',
    '虚假宣传', '骗局', '传销', '诈骗',
]

# 抖音社区特有红线 (内容安全/导流)
DOUYIN_RED_LINES = COMMON_RED_LINES + [
    '私信我', '加我微信', '微我', 'vx', '加QQ',
    '点击链接', '看主页', '链接在评论', '个人简介有福利',
    '秒杀', '限时抢购', '仅今天', '手慢无',
]

# 小红书社区特有红线 (种草/医美/导流)
XHS_RED_LINES = COMMON_RED_LINES + [
    '加我微信', '私信我要链接', '推荐加', 'vx',
    '点击链接', '看我主页', '链接放评论',
    '医美', '整容', '手术', '玻尿酸', '瘦脸针', '割双眼皮',
    '代购', '厂家直销', '清仓甩卖', '批发价',
    '最有效', '根治', '100%有效', '永不反弹',
]

# B站社区特有红线 (导流/版权/政治敏感)
BILI_RED_LINES = COMMON_RED_LINES + [
    '微信公众号', '加QQ', 'QQ群', '私信领资源',
    '微信扫描', '扫码加群', '跳转链接看完整版',
    '网盘链接', '提取码', '需要资源私信',
    '点赞过万更新', '投币过万做下一期',
    '全站最火', 'UP主必看', '新人必看',
]

# 平台限流词库统一访问
_PLATFORM_RESTRICT_MAP = {
    'douyin': DOUYIN_RED_LINES,
    'xiaohongshu': XHS_RED_LINES,
    'bilibili': BILI_RED_LINES,
    None: COMMON_RED_LINES,
}


def get_platform_red_lines(platform: str = None) -> List[str]:
    """获取指定平台的限流词库 (含通用红线)"""
    return _PLATFORM_RESTRICT_MAP.get(platform, COMMON_RED_LINES)


def check_platform_rules(text: str, platform: str = None) -> Tuple[str, float, str]:
    """C5 平台差异化合规检查 (v23.1.0)"""
    lines = get_platform_red_lines(platform)
    found = []
    for w in lines:
        if w in text:
            found.append(w)
    if found:
        return 'BLOCK', 0.0, f'[{platform or "common"}] 限流词: {", ".join(found[:5])}'
    # 长度限制 (抖音 ≤ 300, 小红书 ≤ 1000, B站 ≤ 2000)
    max_len = {'douyin': 300, 'xiaohongshu': 1000, 'bilibili': 2000}.get(platform, 500)
    if len(text) > max_len:
        return 'REVIEW', 0.7, f'文本超长: {len(text)} > {max_len}'
    return 'PASS', 1.0, f'[{platform or "all"}] 平台规则通过'


# 兼容旧接口 (默认抖音)
def check_douyin_rules(text: str) -> Tuple[str, float, str]:
    return check_platform_rules(text, platform='douyin')

# C6 隐私相关词 (出现则标记 BLOCK)
PRIVACY_TRIGGERS = [
    '身份证号', '手机号', '家庭住址', '银行卡号',
    '密码', 'pin码', '社保号', '医保号',
    '个人隐私', '私生活', '未经允许',
]


# ============================================================
# C1 原创性检测 — SimHash
# ============================================================

def _simhash(text: str, f: int = 64) -> int:
    """文本 SimHash — 用于相似内容快速比对"""
    if not text:
        return 0
    v = [0] * f
    words = re.findall(r'[\u4e00-\u9fff]+|\w+', text.lower())
    for w in words:
        h = int(hashlib.md5(w.encode()).hexdigest(), 16)
        for i in range(f):
            v[i] += 1 if (h & (1 << i)) else -1
    fingerprint = 0
    for i in range(f):
        if v[i] >= 0:
            fingerprint |= (1 << i)
    return fingerprint


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count('1')


def check_originality(text: str, content_id: str = None) -> Tuple[str, float, str]:
    """
    C1 原创性检测:
    - SimHash vs 已知内容库
    - 与 question_content_hashes 表去重
    返回: (result, similarity_score, detail)
    """
    if not text or len(text) < 20:
        return 'REVIEW', 0.0, '内容过短, 建议人工审核'

    fp = _simhash(text)

    # 1. vs galaxy_compliance_log 里已审查过的内容
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    try:
        # 查已有 BLOCK/BLOCK 的高风险内容指纹
        existing = conn.execute("""
            SELECT content_id, check_type, score, detail
            FROM mt_galaxy_compliance_log
            WHERE check_type='C1_originality'
            ORDER BY log_id DESC LIMIT 500
        """).fetchall()

        min_dist = 64
        close_match = None
        for row in existing:
            try:
                stored_fp = int(row['detail'].split('fp=')[1].split()[0]) if row['detail'] and 'fp=' in row['detail'] else 0
                if stored_fp:
                    dist = _hamming(fp, stored_fp)
                    if dist < min_dist:
                        min_dist = dist
                        close_match = row['content_id']
            except (IndexError, ValueError):
                continue

        # 2. vs question_content_hashes (题库)
        try:
            q_rows = conn.execute("""
                SELECT content_hash FROM question_content_hashes LIMIT 200
            """).fetchall()
            for r in q_rows:
                try:
                    stored = int(r['content_hash'][:16], 16) if r['content_hash'] else 0
                    if stored:
                        dist = _hamming(fp, stored & 0xFFFFFFFFFFFFFFFF)
                        if dist < min_dist:
                            min_dist = dist
                            close_match = 'question_content_hashes'
                except (ValueError, TypeError):
                    continue
        except sqlite3.OperationalError:
            pass  # 表不存在

        # 判定: hamming < 10 → 相似度 > 20% → BLOCK
        similarity = max(0.0, 1.0 - min_dist / 64.0)
        detail = f"fp={fp} min_hamming={min_dist} similarity={similarity:.3f}"
        if close_match:
            detail += f" close_match={close_match}"

        if min_dist < 10:
            return 'BLOCK', similarity, detail + ' 内容与已有高风险条目高度相似'
        elif min_dist < 20:
            return 'REVIEW', similarity, detail + ' 存在可疑相似, 建议人工审核'
        return 'PASS', similarity, detail

    finally:
        conn.close()


# ============================================================
# C2 引用标注检查
# ============================================================

def check_citation(text: str) -> Tuple[str, float, str]:
    """
    C2 引用必须标注:
    - 含引用词汇但没出处 → REVIEW
    - 有引用标注 → PASS
    """
    if not text:
        return 'PASS', 1.0, '空内容跳过'

    cite_keywords = ['参考', '引用', '来源', '出处', '摘自', '参考自', '转引自', '原文', '文献']
    has_cite_word = any(k in text for k in cite_keywords)

    if has_cite_word:
        # 有引用词汇 → 看有没有具体标注
        has_source_link = bool(re.search(r'https?://|\[.*?\]\(.*?\)|[（(]来源[:：].*?[)）]|出处[:：]', text))
        if has_source_link:
            return 'PASS', 1.0, '检测到引用标注'
        return 'REVIEW', 0.5, '含引用词汇但未标注出处, 建议补充'

    # 无引用词汇 → 原创内容 → PASS
    return 'PASS', 1.0, '未检测到引用需求'


# ============================================================
# C3 极限词
# ============================================================

def check_extreme_words(text: str) -> Tuple[str, float, str]:
    """C3 广告法极限词扫描 — 精确词组匹配"""
    if not text:
        return 'PASS', 1.0, '空内容跳过'
    found = []
    for w in EXTREME_WORDS:
        if w in text:
            found.append(w)
    if found:
        unique = list(set(found))[:5]
        return 'BLOCK', 0.0, f"检测到广告法极限词: {unique}"
    return 'PASS', 1.0, '无极限词'


# ============================================================
# C4 学科类内容
# ============================================================

def check_subject_compliance(text: str) -> Tuple[str, float, str]:
    """C4 教育法学科类走人工审批"""
    if not text:
        return 'PASS', 1.0, '空内容跳过'
    found = []
    for kw in SUBJECT_KEYWORDS:
        if kw in text:
            found.append(kw)
    if found:
        return 'REVIEW', 0.5, f"检测到学科类关键词 {list(set(found))[:3]}, 需人工审批"
    return 'PASS', 1.0, '非学科类内容'


# ============================================================
# C5 抖音社区红线
# ============================================================

def check_douyin_rules(text: str) -> Tuple[str, float, str]:
    """C5 抖音社区红线扫描"""
    if not text:
        return 'PASS', 1.0, '空内容跳过'
    found = []
    for kw in DOUYIN_RED_LINES:
        if kw in text:
            found.append(kw)
    if found:
        return 'BLOCK', 0.0, f"检测到抖音社区红线词: {list(set(found))[:5]}"
    return 'PASS', 1.0, '无违规内容'


# ============================================================
# C6 隐私
# ============================================================

def check_privacy(text: str) -> Tuple[str, float, str]:
    """C6 个人信息保护法"""
    if not text:
        return 'PASS', 1.0, '空内容跳过'
    found = []
    for kw in PRIVACY_TRIGGERS:
        if kw in text:
            found.append(kw)
    # 额外: 手机号/身份证号 pattern
    phone_pattern = r'1[3-9]\d{9}'
    id_pattern = r'\d{17}[\dXx]'
    if re.search(phone_pattern, text):
        found.append('手机号格式')
    if re.search(id_pattern, text):
        found.append('身份证号格式')
    if found:
        return 'BLOCK', 0.0, f"检测到隐私风险: {list(set(found))[:5]}"
    return 'PASS', 1.0, '无隐私风险'


# ============================================================
# C7 内容来源授权
# ============================================================

def check_source_auth(text: str, source_type: str = 'self_generated') -> Tuple[str, float, str]:
    """
    C7 来源授权:
      self_generated → AI 自生成 → PASS
      authorized     → 授权内容 → 需 auth_id → PASS/REVIEW
      public_domain  → 公有领域 → PASS
      unknown        → 不明来源 → REVIEW
    """
    valid = ['self_generated', 'authorized', 'public_domain']
    if source_type in valid:
        if source_type == 'authorized' and not text:
            return 'REVIEW', 0.5, '授权内容需提供授权凭证'
        return 'PASS', 1.0, f'来源: {source_type}'
    return 'REVIEW', 0.5, f'来源不明: {source_type}'


# ============================================================
# 主入口: 全量 Pipeline
# ============================================================

def run_compliance_pipeline(content_id: str, content_type: str, text: str,
                            source_type: str = 'self_generated',
                            platform: str = None) -> Dict:
    """
    跑 C1~C7 全量审查, 写入 mt_galaxy_compliance_log, 返回汇总

    platform: 'douyin' | 'xiaohongshu' | 'bilibili' | None (通用)
      → C5 和 C3 会根据平台差异化审查

    返回:
      {
        'overall': 'PASS'|'BLOCK'|'REVIEW',
        'checks': { 'C1_originality': {...}, ... },
        'logs_created': [log_ids]
      }
    """
    from engines.galaxy_db import log_compliance

    checks = {
        'C1_originality':  lambda: check_originality(text, content_id),
        'C2_citation':     lambda: check_citation(text),
        'C3_extremes':     lambda: check_extreme_words(text),
        'C4_edu_compliance': lambda: check_subject_compliance(text),
        'C5_douyin_rules': lambda: check_platform_rules(text, platform=platform),
        'C6_privacy':      lambda: check_privacy(text),
        'C7_source_auth':  lambda: check_source_auth(text, source_type),
    }

    results = {}
    log_ids = []
    overall = 'PASS'

    for check_type, func in checks.items():
        try:
            result, score, detail = func()
        except Exception as e:
            result, score, detail = 'REVIEW', 0.0, f'check exception: {e}'

        results[check_type] = {
            'result': result,
            'score': score,
            'detail': detail[:200],
        }

        if result == 'BLOCK':
            overall = 'BLOCK'
        elif result == 'REVIEW' and overall != 'BLOCK':
            overall = 'REVIEW'

        lid = log_compliance(content_id, content_type, check_type, result, score, detail[:500],
                             platform=platform)
        log_ids.append(lid)

    return {
        'overall': overall,
        'checks': results,
        'logs_created': log_ids,
        'content_id': content_id,
        'content_type': content_type,
        'platform': platform,
        'checked_at': datetime.now().isoformat(),
    }


# ============================================================
# 快速预检 (300ms 内) — 在内容生成时就扫极限词/红线
# ============================================================

def quick_precheck(text: str) -> Tuple[bool, List[str]]:
    """
    快速预检 (不查原创性/引用, 只扫即时阻断词):
    - C3 极限词 (BLOCK)
    - C5 抖音红线 (BLOCK)
    - C6 隐私 (BLOCK)
    """
    blockers = []

    # C3 — 精确词组
    for w in EXTREME_WORDS:
        if w in text:
            blockers.append(f"[C3] 极限词: {w}")
            break

    # C5
    for w in DOUYIN_RED_LINES:
        if w in text:
            blockers.append(f"[C5] 抖音红线: {w}")
            break

    # C6
    for w in PRIVACY_TRIGGERS:
        if w in text:
            blockers.append(f"[C6] 隐私风险: {w}")
            break

    # 手机号/身份证
    if re.search(r'1[3-9]\d{9}', text):
        blockers.append("[C6] 手机号格式")
    if re.search(r'\d{17}[\dXx]', text):
        blockers.append("[C6] 身份证号格式")

    return (len(blockers) == 0, blockers)


# ============================================================
# CLI 入口
# ============================================================

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: galaxy_compliance.py <precheck|full> [--text CONTENT]")
        sys.exit(1)

    cmd = sys.argv[1]

    # 从 --text 或 stdin 读
    text = ''
    if '--text' in sys.argv:
        idx = sys.argv.index('--text')
        text = ' '.join(sys.argv[idx+1:])
    else:
        text = sys.stdin.read().strip()

    if not text:
        text = "这是一条测试内容: 本课程是全球最好的教育内容, 包教包会无效退款"

    if cmd == 'precheck':
        ok, blockers = quick_precheck(text)
        print(f"✅ PASS" if ok else f"❌ BLOCKED ({len(blockers)} issues)")
        for b in blockers:
            print(f"  {b}")

    elif cmd == 'full':
        import json
        result = run_compliance_pipeline(
            content_id='cli_test',
            content_type='script',
            text=text,
            source_type='self_generated'
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
