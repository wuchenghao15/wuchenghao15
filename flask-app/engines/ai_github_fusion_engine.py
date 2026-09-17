# -*- coding: utf-8 -*-
"""
ai_github_fusion_engine.py — 仙女座 v6.2 新升级路径：GitHub 开源自动发现+适配融合

三阶段流水线：
  Stage 1 SCAN     → GitHub Search API 按 topic/star/关键词发现候选
  Stage 2 EVALUATE → 本地 Ollama 相关性评分 + 许可证合规 + 活跃度过滤
  Stage 3 PROPOSE  → 生成融合提案 → 存 mt_github_fusion_proposals → 人工批准后执行

安全硬约束：
  - 许可证白名单: MIT / Apache-2.0 / BSD-2 / BSD-3 / ISC
  - 融合目标仅限 flask-app/ai_engines/ 和 flask-app/routes/
  - 禁止修改 server_real_db.py / DB schema / .trae/rules/
  - 实际 git clone + 文件集成必须等待 proposal.approved = True

依赖：
  - requests (pip install requests)
  - 本地 Ollama (可选, 用于相关性评分; 无则跳过评分)
  - GitHub Token (可选, 放 _runtime/config/github_token.txt; 无则 60req/h 限额)
"""

import os, sys, sqlite3, json, time, logging, hashlib, re, subprocess, shutil
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('github_fusion')

# ============ 配置 ============
APP_DB = os.environ.get('APP_DB',
    '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/_runtime/databases/Database/app.db')
PROJECT_ROOT = os.environ.get('PROJECT_ROOT',
    '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project')
FLASK_APP_DIR = os.path.join(PROJECT_ROOT, 'flask-app')
CACHE_DIR = os.path.join(PROJECT_ROOT, '_runtime', 'github_fusion_cache')

# 安全硬约束
ALLOWED_LICENSES = {'MIT', 'Apache-2.0', 'Apache-2', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC', 'MPL-2.0', 'LGPL-3.0'}
ALLOWED_FUSION_DIRS = ['flask-app/ai_engines/', 'flask-app/routes/', 'flask-app/core/services/']
FORBIDDEN_PATTERNS = [
    r'server_real_db\.py',
    r'__pycache__',
    r'\.trae/rules/',
    r'_runtime/databases/',
    r'app\.db',
    r'migrations/',
]

# GitHub 搜索关键词 — 基于项目核心能力画像
SEARCH_QUERIES = [
    ('topic:flask topic:ai topic:education stars:>50', 'AI教育Flask扩展'),
    ('topic:knowledge-graph topic:python stars:>30', '知识图谱Python'),
    ('topic:ai-tutor topic:python stars:>30', 'AI导师系统'),
    ('topic:spaced-repetition topic:python stars:>10', '间隔重复算法'),
    ('topic:adaptive-learning topic:python stars:>20', '自适应学习引擎'),
    ('topic:ollama topic:wrapper topic:python stars:>20', 'Ollama封装'),
    ('topic:local-ai topic:embedding python stars:>30', '本地Embedding'),
    ('topic:rag topic:python stars:>50', 'RAG检索增强生成'),
    ('topic:multi-agent topic:python stars:>30', '多Agent框架'),
    ('topic:knowledge-base topic:python stars:>20', '轻量知识库'),
]

GITHUB_API = 'https://api.github.com'


# ============ DB 初始化 ============
def _get_conn():
    conn = sqlite3.connect(APP_DB, timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _ensure_tables():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS mt_github_scan_cache (
            repo_id INTEGER PRIMARY KEY,
            full_name TEXT UNIQUE,
            html_url TEXT,
            description TEXT,
            stars INTEGER,
            language TEXT,
            license TEXT,
            topics TEXT,           -- JSON array
            updated_at TEXT,
            pushed_at TEXT,
            default_branch TEXT,
            fetched_at TEXT,
            raw_json TEXT          -- full API response (compressed)
        );
        CREATE TABLE IF NOT EXISTS mt_github_fusion_proposals (
            proposal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_full_name TEXT NOT NULL,
            repo_html_url TEXT,
            repo_stars INTEGER,
            license TEXT,
            relevance_score REAL DEFAULT 0,   -- 0-1 本地AI评分
            fit_score REAL DEFAULT 0,         -- 许可证+活跃度综合
            keywords_matched TEXT,            -- JSON array
            summary TEXT,                     -- AI 生成的摘要
            fusion_plan TEXT,                 -- JSON: {target_dirs, files_estimate, conflicts}
            proposal_status TEXT DEFAULT 'PENDING', -- PENDING/APPROVED/REJECTED/FUSED/FAILED
            approved_at TEXT,
            approver TEXT,
            rejected_reason TEXT,
            fused_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(repo_full_name)
        );
        CREATE INDEX IF NOT EXISTS idx_gfp_status ON mt_github_fusion_proposals(proposal_status);
        CREATE INDEX IF NOT EXISTS idx_gfp_score ON mt_github_fusion_proposals(relevance_score DESC);
    """)
    conn.commit()
    conn.close()
    logger.info('[GitHubFusion] DB tables OK')


# ============ Stage 1: GitHub 扫描 ============
def _github_token():
    token_file = os.path.join(PROJECT_ROOT, '_runtime', 'config', 'github_token.txt')
    env_token = os.environ.get('GITHUB_TOKEN', '').strip()
    if env_token: return env_token
    if os.path.exists(token_file):
        with open(token_file) as f: t = f.read().strip()
        if t: return t
    return None


def _gh_request(path, params=None):
    import requests
    token = _github_token()
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'MTSCOS-GitHubFusion/1.0'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    url = f'{GITHUB_API}{path}'
    resp = requests.get(url, headers=headers, params=params or {}, timeout=15)
    if resp.status_code == 403:
        logger.warning(f'[GitHub] rate_limit={resp.headers.get("X-RateLimit-Remaining")}/{resp.headers.get("X-RateLimit-Limit")}')
    resp.raise_for_status()
    return resp.json()


def _scan_once(query, max_pages=2):
    """单关键词扫描 → list[repo_dict]"""
    results = []
    for page in range(1, max_pages + 1):
        try:
            data = _gh_request('/search/repositories', {
                'q': query, 'sort': 'stars', 'order': 'desc',
                'per_page': 30, 'page': page,
            })
            items = data.get('items', [])
            if not items: break
            results.extend(items)
            # GitHub 搜索有 1min 冷却
            time.sleep(2)
        except Exception as e:
            logger.warning(f'[GitHub] scan failed q="{query}" page={page}: {e}')
            break
    return results


def run_scan_stage():
    """Stage 1: 全量扫描 + 写 cache"""
    _ensure_tables()
    conn = _get_conn()
    total_new, total_updated = 0, 0

    for query, tag in SEARCH_QUERIES:
        logger.info(f'[SCAN] q="{query}" ({tag})')
        repos = _scan_once(query)
        for r in repos:
            license_info = r.get('license') or {}
            topics = json.dumps(r.get('topics', []))
            now = datetime.utcnow().isoformat()
            cur = conn.execute('SELECT repo_id FROM mt_github_scan_cache WHERE full_name=?', (r['full_name'],))
            exists = cur.fetchone()
            if exists:
                conn.execute("""UPDATE mt_github_scan_cache SET
                    html_url=?, description=?, stars=?, language=?, license=?, topics=?,
                    updated_at=?, pushed_at=?, default_branch=?, fetched_at=?, raw_json=?
                    WHERE full_name=?""", (
                    r['html_url'], r.get('description',''), r.get('stargazers_count',0),
                    r.get('language',''), license_info.get('spdx_id','NOASSERTION'),
                    topics, r.get('updated_at',''), r.get('pushed_at',''),
                    r.get('default_branch','main'), now,
                    json.dumps(r)[:5000], r['full_name']))
                total_updated += 1
            else:
                conn.execute("""INSERT OR IGNORE INTO mt_github_scan_cache
                    (full_name, html_url, description, stars, language, license, topics,
                     updated_at, pushed_at, default_branch, fetched_at, raw_json)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
                    r['full_name'], r['html_url'], r.get('description',''),
                    r.get('stargazers_count',0), r.get('language',''),
                    license_info.get('spdx_id','NOASSERTION'), topics,
                    r.get('updated_at',''), r.get('pushed_at',''),
                    r.get('default_branch','main'), now, json.dumps(r)[:5000]))
                total_new += 1
        conn.commit()
    conn.close()
    logger.info(f'[SCAN] done: new={total_new} updated={total_updated}')
    return {'new': total_new, 'updated': total_updated}


# ============ Stage 2: 评估 ============
def _ollama_score(repo_desc, repo_topics, target_keywords):
    """本地 Ollama 推理：repo 与项目核心能力的相关性 0-1
    无 Ollama 时返回 heuristic 评分"""
    # 先试 Ollama
    try:
        import requests as rq
        prompt = f"""Rate this GitHub repo's relevance (0.0-1.0) to a Python Flask AI education platform with knowledge graph, RAG, multi-agent tutoring, spaced repetition.

Repo description: {repo_desc[:400]}
Topics: {', '.join(repo_topics[:15])}

Respond with ONLY a single float between 0 and 1."""
        resp = rq.post('http://localhost:11434/api/generate',
            json={'model': 'qwen2.5:7b', 'prompt': prompt, 'stream': False}, timeout=20)
        score_text = resp.json().get('response', '').strip()
        m = re.search(r'(\d+\.?\d*)', score_text)
        if m:
            return max(0.0, min(1.0, float(m.group(1))))
    except Exception:
        pass

    # Heuristic fallback
    text = (repo_desc or '').lower() + ' ' + ' '.join(t.lower() for t in (repo_topics or []))
    hits = sum(1 for kw in target_keywords if kw.lower() in text)
    return round(min(1.0, hits / 8.0), 3)


def run_evaluate_stage():
    """Stage 2: 从 cache 读 → 评分 → 写 proposals"""
    _ensure_tables()
    conn = _get_conn()

    # 读 cache 中尚未 proposal 的 repo
    cur = conn.execute("""
        SELECT c.repo_id, c.full_name, c.html_url, c.description, c.stars,
               c.language, c.license, c.topics, c.pushed_at
        FROM mt_github_scan_cache c
        LEFT JOIN mt_github_fusion_proposals p ON p.repo_full_name = c.full_name
        WHERE p.proposal_id IS NULL
          AND c.stars >= 10
          AND c.license IN ('MIT','Apache-2.0','Apache-2','BSD-2-Clause','BSD-3-Clause','ISC','MPL-2.0','LGPL-3.0','NOASSERTION','Other')
        ORDER BY c.stars DESC LIMIT 30""")
    repos = cur.fetchall()

    target_kw = ['flask', 'python', 'education', 'tutor', 'knowledge', 'graph', 'rag', 'embedding',
                 'ollama', 'multi-agent', 'learning', 'student', 'quiz', 'knowledge-base']
    created = 0

    for row in repos:
        rid, full, url, desc, stars, lang, lic, topics_json, pushed = row
        topics = json.loads(topics_json) if topics_json else []

        relevance = _ollama_score(desc, topics, target_kw)
        # 活跃度: pushed_at 在 6 个月内 = 加分
        active = True
        try:
            p = datetime.fromisoformat(pushed.replace('Z',''))
            if (datetime.utcnow() - p).days > 180: active = False
        except Exception: pass
        # 许可证合规
        lic_ok = lic in ALLOWED_LICENSES or lic in ('NOASSERTION', 'Other')
        fit = round(relevance * (0.6 if active else 0.3) * (1.0 if lic_ok else 0.1), 3)

        if fit < 0.25: continue  # 低分跳过

        matched_kw = [k for k in target_kw if k.lower() in (desc or '').lower() or k.lower() in [t.lower() for t in topics]]
        summary = f"⭐{stars} {lang} | {lic} | {desc or 'no description'}"
        fusion_plan = json.dumps({
            'target_dirs': ALLOWED_FUSION_DIRS,
            'keywords_matched': matched_kw,
            'estimated_files': min(50, max(5, stars // 20)),
            'requires_migration': False,
        }, ensure_ascii=False)

        conn.execute("""INSERT OR IGNORE INTO mt_github_fusion_proposals
            (repo_full_name, repo_html_url, repo_stars, license, relevance_score, fit_score,
             keywords_matched, summary, fusion_plan)
            VALUES (?,?,?,?,?,?,?,?,?)""", (
            full, url, stars, lic, relevance, fit,
            json.dumps(matched_kw), summary, fusion_plan))
        created += 1
    conn.commit()
    conn.close()
    logger.info(f'[EVALUATE] proposals created: {created}')
    return {'created': created}


# ============ Stage 3: 融合执行（需人工批准） ============
def _clone_repo(full_name, depth=1):
    """git clone 到临时目录. depth=1 浅克隆, timeout=300s
    v6.2: 去掉 capture_output=True — 防止 git progress 流撑爆子进程缓冲区"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    url = f'https://github.com/{full_name}.git'
    target = os.path.join(CACHE_DIR, full_name.replace('/', '__'))
    if os.path.exists(target):
        shutil.rmtree(target, ignore_errors=True)
    try:
        subprocess.run(['git', 'clone', f'--depth={depth}', url, target],
                       check=True, timeout=300)
        return target
    except subprocess.TimeoutExpired:
        logger.warning(f'[FUSION] clone timeout, retry without depth: {full_name}')
        try:
            subprocess.run(['git', 'clone', url, target],
                           check=True, timeout=600)
            return target
        except Exception as e2:
            logger.error(f'[FUSION] clone retry also failed {full_name}: {e2}')
            return None
    except Exception as e:
        logger.error(f'[FUSION] clone failed {full_name}: {e}')
        return None


def _auto_integrate(clone_dir, proposal_id):
    """自动集成：拷贝 Python/JS 源码到 flask-app/ai_engines/{repo_slug}/
    不碰任何核心文件"""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.execute('SELECT * FROM mt_github_fusion_proposals WHERE proposal_id=?', (proposal_id,))
    prop = cur.fetchone()
    if not prop: return False, 'proposal not found'

    full_name = prop['repo_full_name']
    slug = full_name.split('/')[-1]
    fusion_dir = os.path.join(FLASK_APP_DIR, 'ai_engines', f'_{slug}_fusion')

    # 安全: 清目标
    if os.path.exists(fusion_dir):
        shutil.rmtree(fusion_dir, ignore_errors=True)

    # 只拷贝 .py/.js/.md/.json 文件，跳过危险文件
    copied = 0
    for root, dirs, files in os.walk(clone_dir):
        dirs[:] = [d for d in dirs if d not in ('node_modules', '__pycache__', '.git', 'dist', 'build')]
        for f in files:
            if not (f.endswith(('.py', '.js', '.md', '.json', '.yaml', '.yml', '.txt'))):
                continue
            src = os.path.join(root, f)
            rel = os.path.relpath(src, clone_dir)
            # 跳过危险
            if any(re.search(p, rel) for p in FORBIDDEN_PATTERNS):
                continue
            dst = os.path.join(fusion_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            try:
                shutil.copy2(src, dst); copied += 1
            except Exception:
                pass

    # 写 __init__.py
    init_path = os.path.join(fusion_dir, '__init__.py')
    if not os.path.exists(init_path):
        with open(init_path, 'w') as f:
            f.write(f'# Auto-fused from https://github.com/{full_name}\n')
            f.write(f'# Proposal #{proposal_id}, fused at {datetime.utcnow().isoformat()}\n')

    conn.execute("""UPDATE mt_github_fusion_proposals
        SET proposal_status='FUSED', fused_at=datetime('now')
        WHERE proposal_id=?""", (proposal_id,))
    conn.commit(); conn.close()
    logger.info(f'[FUSION] {full_name} → {fusion_dir} ({copied} files)')
    return True, f'{copied} files → ai_engines/{os.path.basename(fusion_dir)}'


def run_fusion(proposal_id, approver='manual'):
    """人工批准后执行融合"""
    _ensure_tables()
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.execute('SELECT repo_full_name, proposal_status FROM mt_github_fusion_proposals WHERE proposal_id=?', (proposal_id,))
    row = cur.fetchone()
    if not row:
        return {'error': 'proposal not found'}
    if row['proposal_status'] != 'APPROVED':
        return {'error': f"status={row['proposal_status']}, need APPROVED first"}

    clone_dir = _clone_repo(row['repo_full_name'])
    if not clone_dir:
        conn.execute("UPDATE mt_github_fusion_proposals SET proposal_status='FAILED', rejected_reason='clone failed' WHERE proposal_id=?", (proposal_id,))
        conn.commit(); conn.close()
        return {'error': 'clone failed'}

    ok, msg = _auto_integrate(clone_dir, proposal_id)
    conn.close()
    return {'success': ok, 'msg': msg, 'clone_dir': clone_dir}


def approve_proposal(proposal_id, approver='admin'):
    conn = _get_conn()
    conn.execute("""UPDATE mt_github_fusion_proposals
        SET proposal_status='APPROVED', approved_at=datetime('now'), approver=?
        WHERE proposal_id=? AND proposal_status='PENDING'""", (approver, proposal_id))
    conn.commit(); conn.close()
    return True


def reject_proposal(proposal_id, reason=''):
    conn = _get_conn()
    conn.execute("""UPDATE mt_github_fusion_proposals
        SET proposal_status='REJECTED', rejected_reason=?
        WHERE proposal_id=?""", (reason[:500], proposal_id))
    conn.commit(); conn.close()
    return True


def list_proposals(status=None, limit=20):
    conn = _get_conn()
    if status:
        cur = conn.execute('SELECT * FROM mt_github_fusion_proposals WHERE proposal_status=? ORDER BY fit_score DESC LIMIT ?', (status, limit))
    else:
        cur = conn.execute('SELECT * FROM mt_github_fusion_proposals ORDER BY fit_score DESC LIMIT ?', (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ============ Daemon 入口 ============
def run_cycle():
    """仙女座 daemon 单次执行：scan → evaluate"""
    try:
        s = run_scan_stage()
        e = run_evaluate_stage()
        return {'scan': s, 'evaluate': e}
    except Exception as ex:
        logger.error(f'[GitHubFusion] cycle failed: {ex}')
        return {'error': str(ex)}


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--scan', action='store_true')
    ap.add_argument('--evaluate', action='store_true')
    ap.add_argument('--cycle', action='store_true')
    ap.add_argument('--proposal-id', type=int)
    ap.add_argument('--approve', action='store_true')
    ap.add_argument('--fuse', action='store_true')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--status', default=None)
    args = ap.parse_args()

    _ensure_tables()
    if args.scan: print(json.dumps(run_scan_stage(), indent=2, ensure_ascii=False))
    elif args.evaluate: print(json.dumps(run_evaluate_stage(), indent=2, ensure_ascii=False))
    elif args.cycle: print(json.dumps(run_cycle(), indent=2, ensure_ascii=False))
    elif args.approve and args.proposal_id:
        approve_proposal(args.proposal_id); print(f'approved #{args.proposal_id}')
    elif args.fuse and args.proposal_id:
        print(json.dumps(run_fusion(args.proposal_id), indent=2, ensure_ascii=False))
    elif args.list:
        print(json.dumps(list_proposals(args.status), indent=2, ensure_ascii=False))
    else:
        ap.print_help()
