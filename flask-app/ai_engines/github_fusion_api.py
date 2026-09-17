# -*- coding: utf-8 -*-
"""GitHub Fusion API 蓝图 — /api/ai/github-fusion/*
仙女座 v6.2: GitHub 开源发现+融合管理
"""
from flask import Blueprint, jsonify, request

github_fusion_bp = Blueprint('github_fusion', __name__, url_prefix='/api/ai/github-fusion')


def _engine():
    from engines.ai_github_fusion_engine import (
        run_cycle, run_scan_stage, run_evaluate_stage,
        list_proposals, approve_proposal, reject_proposal, run_fusion,
        _ensure_tables,
    )
    _ensure_tables()
    return {
        'run_cycle': run_cycle,
        'scan': run_scan_stage,
        'evaluate': run_evaluate_stage,
        'list': list_proposals,
        'approve': approve_proposal,
        'reject': reject_proposal,
        'fuse': run_fusion,
    }


@github_fusion_bp.route('/health')
def health():
    return jsonify({'status': 'ok', 'engine': 'github_fusion', 'version': '6.2'})


@github_fusion_bp.route('/scan', methods=['POST'])
def scan():
    """手动触发 Stage 1 扫描"""
    e = _engine()
    try:
        result = e['scan']()
        return jsonify({'success': True, 'result': result})
    except Exception as ex:
        return jsonify({'success': False, 'error': str(ex)}), 500


@github_fusion_bp.route('/evaluate', methods=['POST'])
def evaluate():
    """手动触发 Stage 2 评估"""
    e = _engine()
    try:
        result = e['evaluate']()
        return jsonify({'success': True, 'result': result})
    except Exception as ex:
        return jsonify({'success': False, 'error': str(ex)}), 500


@github_fusion_bp.route('/cycle', methods=['POST'])
def cycle():
    """完整扫描+评估"""
    e = _engine()
    try:
        result = e['run_cycle']()
        return jsonify({'success': True, 'result': result})
    except Exception as ex:
        return jsonify({'success': False, 'error': str(ex)}), 500


@github_fusion_bp.route('/proposals', methods=['GET'])
def proposals():
    """列出融合提案"""
    status = request.args.get('status')
    limit = int(request.args.get('limit', 20))
    e = _engine()
    items = e['list'](status=status, limit=limit)
    return jsonify({'success': True, 'count': len(items), 'items': items})


@github_fusion_bp.route('/proposals/<int:pid>/approve', methods=['POST'])
def approve(pid):
    """批准提案"""
    e = _engine()
    e['approve'](pid)
    return jsonify({'success': True, 'proposal_id': pid, 'status': 'APPROVED'})


@github_fusion_bp.route('/proposals/<int:pid>/reject', methods=['POST'])
def reject(pid):
    """拒绝提案"""
    reason = (request.get_json() or {}).get('reason', '')
    e = _engine()
    e['reject'](pid, reason)
    return jsonify({'success': True, 'proposal_id': pid, 'status': 'REJECTED'})


@github_fusion_bp.route('/proposals/<int:pid>/fuse', methods=['POST'])
def fuse(pid):
    """执行融合 (必须已 APPROVED)"""
    e = _engine()
    result = e['fuse'](pid)
    if result.get('error'):
        return jsonify({'success': False, 'error': result['error']}), 400
    return jsonify({'success': True, **result})


# ============================================================
# v6.2 深度集成端点 — SimpleMem + Ollama embedding + semantica Pipeline
# ============================================================

def _fusion_adapter():
    """懒加载 fusion_adapter (避免 Flask 启动时 import 重型依赖)"""
    from ai_engines import fusion_adapter
    return fusion_adapter


@github_fusion_bp.route('/deep/health')
def deep_health():
    """深度集成健康检查 — Ollama + 向量存储 + 所有 adapter"""
    fa = _fusion_adapter()
    return jsonify({
        'status': 'ok',
        'ollama': fa.ollama_status(),
        'adapters': fa.health_check_all(),
        'available': fa.available_count(),
        'importable': fa.importable_count(),
    })


@github_fusion_bp.route('/deep/vectorize', methods=['POST'])
def deep_vectorize():
    """手动向量化一批文本 (用于测试或小批量记忆)"""
    fa = _fusion_adapter()
    data = request.get_json() or {}
    texts = data.get('texts', [])
    if isinstance(texts, str):
        texts = [texts]
    if not texts:
        return jsonify({'success': False, 'error': 'texts 不能为空'}), 400

    vecs = fa.ollama_embed_batch(texts)
    return jsonify({
        'success': True,
        'count': len(texts),
        'dim': len(vecs[0]) if vecs and vecs[0] else 0,
        'ollama_ok': all(v is not None for v in vecs),
        # 不返回完整向量 (太大), 只返回维度和前 3 个值预览
        'previews': [v[:3] if v else None for v in vecs],
    })


@github_fusion_bp.route('/deep/brain-boost', methods=['POST'])
def deep_brain_boost():
    """
    触发 AI 脑库批量向量化:
      从 ai_brain_enhanced_knowledge 取数据 → Ollama embedding → 写本地向量存储
    请求体: {db_path, limit, offset, source_table}
    """
    fa = _fusion_adapter()
    data = request.get_json() or {}
    db_path = data.get('db_path')
    if not db_path:
        # 尝试自动找 app.db
        import os
        candidates = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db'),
        ]
        for c in candidates:
            if os.path.exists(c):
                db_path = c
                break
    if not db_path or not os.path.exists(db_path):
        return jsonify({'success': False, 'error': f'找不到数据库: {db_path}'}), 400

    limit = int(data.get('limit', 50))
    offset = int(data.get('offset', 0))
    source_table = data.get('source_table', 'ai_brain_enhanced_knowledge')

    sm = fa.get_adapter('simplemem')
    result = sm.boost_ai_brain(
        db_path=db_path, limit=limit, offset=offset,
        source_table=source_table,
    )
    return jsonify({'success': True, **result})


@github_fusion_bp.route('/deep/semantic-search', methods=['POST'])
def deep_semantic_search():
    """
    语义检索 AI 脑库向量:
      {query: '...', top_k: 10, source_table: '...'}
    """
    fa = _fusion_adapter()
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'success': False, 'error': 'query 不能为空'}), 400

    top_k = int(data.get('top_k', 10))
    source_table = data.get('source_table') or None

    results = fa.semantic_search_brain(query, top_k=top_k)
    return jsonify({
        'success': True,
        'query': query,
        'count': len(results),
        'results': results,
    })


@github_fusion_bp.route('/deep/vector-stats')
def deep_vector_stats():
    """向量存储统计"""
    fa = _fusion_adapter()
    return jsonify(fa.vector_store_stats())


@github_fusion_bp.route('/deep/verify-pipeline', methods=['POST'])
def deep_verify_pipeline():
    """
    用 semantica PipelineValidator 验证 daemon DAG 编排:
      {daemon_graph: {name: {depends_on: [...]}, ...}}
    """
    fa = _fusion_adapter()
    data = request.get_json() or {}
    daemon_graph = data.get('daemon_graph', {})
    if not daemon_graph:
        return jsonify({'success': False, 'error': 'daemon_graph 不能为空'}), 400

    result = fa.verify_daemon_pipeline(daemon_graph)
    return jsonify({'success': True, **result})


@github_fusion_bp.route('/deep/ollama-status')
def deep_ollama_status():
    """Ollama embedding 快速检查"""
    fa = _fusion_adapter()
    return jsonify(fa.ollama_status())


# ============================================================
# v6.2 七阶段自演化引擎 API
# ============================================================

def _evolution_engine():
    """懒加载自演化引擎"""
    import os, sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from engines import andromeda_auto_evolution
    return andromeda_auto_evolution


@github_fusion_bp.route('/deep/evolution-cycle', methods=['POST'])
def deep_evolution_cycle():
    """手动触发仙女座七阶段自演化 cycle"""
    try:
        evo = _evolution_engine()
        result = evo.run_cycle()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@github_fusion_bp.route('/deep/evolution-status')
def deep_evolution_status():
    """自演化引擎状态 — checkpoint + DB 统计 + Ollama"""
    try:
        evo = _evolution_engine()
        return jsonify({'success': True, **evo.get_status()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@github_fusion_bp.route('/deep/evolution-stage', methods=['POST'])
def deep_evolution_stage():
    """手动触发单个演化阶段 — {stage: 'detect|retrieve|associate|derive|reinforce|expand'}"""
    data = request.get_json() or {}
    stage = data.get('stage', '').strip()
    valid = {'detect', 'retrieve', 'associate', 'derive', 'reinforce', 'expand'}
    if stage not in valid:
        return jsonify({'success': False, 'error': f'stage 必须是 {sorted(valid)} 之一'}), 400
    try:
        evo = _evolution_engine()
        result = evo.run_single_stage(stage)
        return jsonify({'success': True, 'stage': stage, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@github_fusion_bp.route('/deep/bulk-ingest', methods=['POST'])
def deep_bulk_ingest():
    """
    🆕 全量 EigenFlux 批量摄入 — 后台线程异步跑
    POST body: {max_batches: 100, batch_size: 1000}
    """
    import threading
    data = request.get_json() or {}
    max_batches = int(data.get('max_batches', 50))
    batch_size = int(data.get('batch_size', 500))
    sleep_s = float(data.get('sleep', 3.0))

    # 异步后台线程跑 (不阻塞 Flask)
    def _run():
        try:
            evo = _evolution_engine()
            evo.bulk_ingest(max_batches=max_batches, batch_size=batch_size,
                            sleep_between_batches=sleep_s)
        except Exception as e:
            logger.error(f'bulk_ingest crash: {e}')

    t = threading.Thread(target=_run, name='bulk-ingest', daemon=True)
    t.start()
    return jsonify({
        'success': True,
        'message': f'bulk_ingest started: max_batches={max_batches}, batch_size={batch_size}',
        'thread_id': t.ident,
    })


@github_fusion_bp.route('/deep/bulk-status')
def deep_bulk_status():
    """bulk 摄入进度 (从 checkpoint 推断)"""
    try:
        evo = _evolution_engine()
        return jsonify({'success': True, **evo.bulk_status()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@github_fusion_bp.route('/deep/sync-status')
def deep_sync_status():
    """🆕 仙女座双向同步状态 (自动发现 Mac mini → 双向 rsync + DB 合并)"""
    try:
        import os as _os
        import sys as _sys
        _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
        import autosync_andromeda as _sync
        return jsonify({'success': True, **_sync.get_status_json()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@github_fusion_bp.route('/deep/sync-now', methods=['POST'])
def deep_sync_now():
    """🆕 手动触发一次双向同步 (后台线程)"""
    import threading, sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import autosync_andromeda as _sync

    def _run():
        try:
            host, source = _sync.discover_mini()
            if not host:
                _sync.log("warn", "手动同步: 没发现 Mac mini")
                return
            if not _sync.ssh_ok(host):
                _sync.log("warn", f"手动同步: SSH 不通 {host}")
                return
            remote_db = _sync.probe_remote_db(host)
            _sync.log("info", f"手动触发双向同步 → {host} ({source})")
            _sync.sync_directories(host)
            if remote_db:
                _sync.sync_db_tables(host, remote_db)
            _sync.log("info", "手动双向同步完成")
        except Exception as e:
            _sync.log("error", f"手动同步 crash: {e}")

    t = threading.Thread(target=_run, name='manual-sync', daemon=True)
    t.start()
    return jsonify({
        'success': True,
        'message': '手动双向同步已触发 (后台线程)',
        'thread_id': t.ident,
    })
