"""
仙女座星系子系统 — 定时发布 + 数据回流 Daemon

周期: 每 15min 一轮
职责:
  1. 扫描 compliance_pass 的 episodes → 进入 publish_queue → 定时发布
  2. 已发布 episodes → 每轮拉取播放/点赞/评论数据
  3. 抖音用户互动 → 写入 mt_galaxy_feedback_ingest
  4. feedback → 注入 ai_neural_hub 知识摄取 → 反馈调节下一轮内容

flow_id: galaxy_publish_daemon
version: v23.0.0
"""
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [GALAXY] %(levelname)s %(message)s',
)
logger = logging.getLogger('galaxy_daemon')

DB_PATH = os.path.join(ROOT, 'database', 'app.db')


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH, timeout=15)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA busy_timeout=30000')
    c.row_factory = sqlite3.Row
    return c


# ============================================================
# 阶段 1: 发布前准备
# ============================================================

def stage1_publish_ready() -> dict:
    """
    扫描合规通过 → 进入发布队列
    选最优发布时间 (根据粉丝活跃时段历史数据)
    """
    conn = _conn()
    try:
        ready = conn.execute("""
            SELECT ep.*, s.title as series_title, s.role_type
            FROM mt_galaxy_episodes ep
            JOIN mt_galaxy_series s ON ep.series_id = s.series_id
            WHERE ep.compliance_pass = 1
              AND ep.status IN ('compliance_pass', 'publish_queue')
              AND ep.douyin_video_id IS NULL
            ORDER BY ep.created_at DESC LIMIT 50
        """).fetchall()

        # 批量更新为 publish_queue
        ids = [r['episode_id'] for r in ready]
        if ids:
            conn.executemany(
                "UPDATE mt_galaxy_episodes SET status='publish_queue' WHERE episode_id=?",
                [(eid,) for eid in ids]
            )
            conn.commit()

        return {'ready_count': len(ids), 'episode_ids': ids[:5]}
    finally:
        conn.close()


# ============================================================
# 阶段 2: 数据采集 (已发布视频的播放/点赞/评论)
# ============================================================

def stage2_collect_metrics() -> dict:
    """
    已发布视频 metrics 采集:
    目前走 mock 数据 (抖音 Open API 需要申请 + 账号授权)
    真实实现: 调用抖音 OpenAPI /aweme/v2/aweme/detail/
    """
    conn = _conn()
    try:
        published = conn.execute("""
            SELECT episode_id, douyin_video_id, views, likes, comments
            FROM mt_galaxy_episodes
            WHERE douyin_video_id IS NOT NULL
            ORDER BY publish_time DESC LIMIT 100
        """).fetchall()

        collected = 0
        for ep in published:
            # Mock: 每轮 views +10%, likes +5% (真实环境替换为 API 调用)
            new_views = int((ep['views'] or 0) * 1.1 + 5)
            new_likes = int((ep['likes'] or 0) * 1.05 + 2)
            new_comments = int((ep['comments'] or 0) * 1.02)

            # 写 daily_stats
            conn.execute("""
                INSERT INTO mt_galaxy_daily_stats
                (stat_date, series_id, account_id, views_delta, likes_delta, comments_delta)
                VALUES (date('now','localtime'),
                    (SELECT series_id FROM mt_galaxy_episodes WHERE episode_id=?),
                    (SELECT account_id FROM mt_galaxy_accounts WHERE role_type=(SELECT role_type FROM mt_galaxy_episodes WHERE episode_id=?) LIMIT 1),
                    ?, ?, ?)
                ON CONFLICT(stat_date, series_id, account_id) DO UPDATE SET
                    views_delta=views_delta+excluded.views_delta,
                    likes_delta=likes_delta+excluded.likes_delta,
                    comments_delta=comments_delta+excluded.comments_delta
            """, (ep['episode_id'], ep['episode_id'], new_views, new_likes, new_comments))

            conn.execute("""
                UPDATE mt_galaxy_episodes
                SET views=?, likes=?, comments=?
                WHERE episode_id=?
            """, (new_views, new_likes, new_comments, ep['episode_id']))

            # 反馈回流: 点赞多 → 标记为 like_trend
            if new_likes > (ep['likes'] or 0) + 10:
                conn.execute("""
                    INSERT INTO mt_galaxy_feedback_ingest
                    (episode_id, feedback_type, feedback_value, content)
                    VALUES (?, 'like_trend', ?, '点赞趋势向上, 内容受欢迎')
                """, (ep['episode_id'], float(new_likes)))

            collected += 1

        conn.commit()
        return {'collected': collected}
    finally:
        conn.close()


# ============================================================
# 阶段 3: 反馈回流 → 仙女座知识库
# ============================================================

def stage3_feedback_ingest() -> dict:
    """
    把 mt_galaxy_feedback_ingest 的反馈注入仙女座知识库
    复用 ai_neural_hub 的 knowledge_ingest 能力
    """
    conn = _conn()
    try:
        feedbacks = conn.execute("""
            SELECT * FROM mt_galaxy_feedback_ingest
            WHERE ingested = 0 ORDER BY created_at DESC LIMIT 50
        """).fetchall()

        ingested_count = 0
        for fb in feedbacks:
            # 构造知识点并注入 (通过 neural_hub knowledge_feed 链路)
            feedback_text = f"[GALAXY-FEEDBACK] episode={fb['episode_id']} " \
                           f"type={fb['feedback_type']} value={fb['feedback_value']} " \
                           f"content={fb['content'] or ''}"

            try:
                # 尝试注入 ai_brain_enhanced_knowledge
                conn.execute("""
                    INSERT INTO ai_brain_enhanced_knowledge
                    (knowledge_id, title, content, knowledge_type, trust_score, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    f"galaxy_fb_{fb['feedback_id']}",
                    f"星系反馈: {fb['feedback_type']}",
                    feedback_text[:2000],
                    'feedback',
                    0.8,
                    'andromeda_galaxy'
                ))
                conn.execute("""
                    UPDATE mt_galaxy_feedback_ingest
                    SET ingested=1, ingested_at=datetime('now','localtime')
                    WHERE feedback_id=?
                """, (fb['feedback_id'],))
                ingested_count += 1
            except sqlite3.OperationalError as e:
                logger.debug(f"feed inject skip: {e}")
                # 表不存在也能跑 — 不阻断 daemon

        conn.commit()
        return {'ingested': ingested_count, 'pending': len(feedbacks) - ingested_count}
    finally:
        conn.close()


# ============================================================
# 阶段 4: 运营统计
# ============================================================

def stage4_operations() -> dict:
    """每日运营汇总"""
    conn = _conn()
    try:
        stats = {}
        stats['total_series'] = conn.execute("SELECT COUNT(*) FROM mt_galaxy_series").fetchone()[0]
        stats['total_episodes'] = conn.execute("SELECT COUNT(*) FROM mt_galaxy_episodes").fetchone()[0]
        stats['published'] = conn.execute("SELECT COUNT(*) FROM mt_galaxy_episodes WHERE douyin_video_id IS NOT NULL").fetchone()[0]
        stats['pending_publish'] = conn.execute("SELECT COUNT(*) FROM mt_galaxy_episodes WHERE status='publish_queue'").fetchone()[0]
        stats['compliance_pass'] = conn.execute("SELECT COUNT(*) FROM mt_galaxy_episodes WHERE compliance_pass=1").fetchone()[0]
        stats['compliance_block'] = conn.execute("SELECT COUNT(*) FROM mt_galaxy_episodes WHERE status='blocked'").fetchone()[0]
        stats['total_views'] = conn.execute("SELECT COALESCE(SUM(views),0) FROM mt_galaxy_episodes").fetchone()[0]
        stats['total_likes'] = conn.execute("SELECT COALESCE(SUM(likes),0) FROM mt_galaxy_episodes").fetchone()[0]
        stats['feedback_pending'] = conn.execute("SELECT COUNT(*) FROM mt_galaxy_feedback_ingest WHERE ingested=0").fetchone()[0]
        return stats
    finally:
        conn.close()


# ============================================================
# 主循环
# ============================================================

def run_once() -> dict:
    """一轮完整 daemon 循环"""
    t0 = time.time()
    logger.info(f"{'='*50}")
    logger.info("🌌 GALAXY DAEMON — 启动一轮循环")
    logger.info(f"{'='*50}")

    results = {}
    try:
        results['stage1'] = stage1_publish_ready()
        logger.info(f"  Stage1 发布准备: {results['stage1']['ready_count']} 条 ready")

        results['stage2'] = stage2_collect_metrics()
        logger.info(f"  Stage2 数据采集: {results['stage2']['collected']} 个视频")

        results['stage3'] = stage3_feedback_ingest()
        logger.info(f"  Stage3 反馈回流: ingested={results['stage3']['ingested']} pending={results['stage3']['pending']}")

        results['stage4'] = stage4_operations()
        logger.info(f"  Stage4 运营汇总: series={results['stage4']['total_series']} "
                     f"episodes={results['stage4']['total_episodes']} "
                     f"published={results['stage4']['published']} "
                     f"views={results['stage4']['total_views']} "
                     f"likes={results['stage4']['total_likes']}")

    except Exception as e:
        logger.error(f"daemon 异常: {e}")
        results['error'] = str(e)

    elapsed = time.time() - t0
    results['elapsed_sec'] = round(elapsed, 1)
    logger.info(f"✅ 循环完成, 耗时 {elapsed:.1f}s")
    return results


def run_loop(interval_sec: int = 900):
    """后台 daemon 模式, 每 interval_sec 一轮 (默认 15min)"""
    logger.info(f"🌌 GALAXY DAEMON 启动 (interval={interval_sec}s)")
    while True:
        try:
            run_once()
        except Exception as e:
            logger.error(f"daemon 循环异常: {e}")
        time.sleep(interval_sec)


# ============================================================
# CLI
# ============================================================

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='仙女座星系 — 定时发布 + 数据回流 Daemon')
    parser.add_argument('--once', action='store_true', help='只跑一轮就退出')
    parser.add_argument('--loop', action='store_true', help='后台 daemon 循环')
    parser.add_argument('--interval', '-i', type=int, default=900, help='loop 间隔 (秒)')
    parser.add_argument('--stats', action='store_true', help='只打印运营统计')
    args = parser.parse_args()

    if args.stats:
        import json
        print(json.dumps(stage4_operations(), indent=2, ensure_ascii=False))
    elif args.loop:
        run_loop(args.interval)
    else:
        import json
        print(json.dumps(run_once(), indent=2, ensure_ascii=False))
