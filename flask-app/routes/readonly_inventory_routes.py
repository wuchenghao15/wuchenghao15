"""
只读盘点功能路由 (v22.19.0 新增, Phase1 T5 精确路径补齐)
=========================================================
§14.5 VIKEY 离线 SA 降级只读配套页面: 可查看不可修改
§14.1 路由权限覆盖真实盘点 (SSOT: DeepInspectionEngine 实扫, 禁止假数据)

权限: admin+ (@system_container(require_auth='admin') 装饰器级声明)
只读: 全部 GET, 无任何写操作端点
"""
import os
import threading
import time

from flask import jsonify, render_template

from . import readonly_inventory_bp
from app.middlewares.system_container import system_container

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_STATS_TTL = 60  # 秒: 与 §14.3 权限缓存时效口径一致

_cache_lock = threading.Lock()
_stats_cache = {'data': None, 'ts': 0.0}


def _get_stats_cached():
    """60s TTL 缓存的 §14.1 实扫统计 (扫描耗时, 不允许每请求全量扫)"""
    with _cache_lock:
        if _stats_cache['data'] is not None and time.time() - _stats_cache['ts'] < _STATS_TTL:
            return _stats_cache['data']
    from engines.deep_inspection_engine import DeepInspectionEngine
    engine = DeepInspectionEngine(scan_dir=_PROJECT_ROOT)
    data = engine.perm_route_stats()
    with _cache_lock:
        _stats_cache['data'] = data
        _stats_cache['ts'] = time.time()
    return data


@readonly_inventory_bp.route('/readonly_inventory', methods=['GET'])
@system_container(require_auth='admin')
def readonly_inventory_page():
    """只读盘点页面 (admin+ 只读, VIKEY离线SA降级可看)"""
    return render_template('readonly_inventory.html')


@readonly_inventory_bp.route('/api/readonly_inventory/stats', methods=['GET'])
@system_container(require_auth='admin')
def get_inventory_stats():
    """§14.1 路由权限覆盖实扫统计 (真实数据, 禁止假数据)"""
    try:
        s = _get_stats_cached()
        return jsonify({
            'success': True,
            'data': {
                'routes': {
                    'total': s['total_routes'],
                    'protected': s['protected'],
                    'unprotected': s['unprotected'],
                    'coverage_pct': round(s['protected'] * 100.0 / s['total_routes'], 2)
                                    if s['total_routes'] else 0.0,
                },
                'files_scanned': s['files_scanned'],
                'generated_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
            },
            'message': '盘点统计获取成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@readonly_inventory_bp.route('/api/readonly_inventory/modules', methods=['GET'])
@system_container(require_auth='admin')
def get_module_inventory():
    """按文件(模块)盘点: 每个文件的路由总数/已保护/未保护"""
    try:
        s = _get_stats_cached()
        modules = [
            {'file': rel, **stat}
            for rel, stat in sorted(s['by_file'].items())
        ]
        return jsonify({'success': True, 'data': modules, 'message': '模块盘点获取成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@readonly_inventory_bp.route('/api/readonly_inventory/gaps', methods=['GET'])
@system_container(require_auth='admin')
def get_inventory_gaps():
    """§14.1 缺口列表: 仍缺少权限装饰器的路由 (实扫)"""
    try:
        s = _get_stats_cached()
        return jsonify({'success': True, 'data': s['unprotected_items'],
                        'message': '缺口列表获取成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
