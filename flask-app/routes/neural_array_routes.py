from flask import Blueprint, jsonify
"""neural_array_routes — 神经网络阵列矩阵 Blueprint

功能: 阵列节点/神经网络拓扑/集群节点/训练进度/心跳流水
表: neural_neurons / neural_layers / neural_synapses / ai_cluster_nodes
权限: 查询需登录
"""
from . import neural_array_bp
from ._governance_helpers import (
    _check_login, _query, _query_one, _count, _ok, _fail,
    _arg_int, _arg_str,
)
import json


@neural_array_bp.route('/stats', methods=['GET'])
def stats():
    """阵列统计 (节点/在线/训练/集群/吞吐)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    total = _count('neural_neurons')
    online = _count('neural_neurons', "status='firing'")
    training = _count('neural_neurons', "status IN ('firing','charging')")
    idle = _count('neural_neurons', "status='resting'")
    offline = _count('neural_neurons', "status='refractory'")
    clusters = _count('ai_cluster_nodes', "status='ONLINE'")
    online_clusters = _count('ai_cluster_nodes', "status='ONLINE'")
    # 吞吐: firing 神经元数 + cluster 在线数 (近似)
    throughput = online + online_clusters
    return _ok({
        'total': total,
        'online': online,
        'training': training,
        'idle': idle,
        'offline': offline,
        'active_clusters': clusters,
        'throughput': throughput,
    })


@neural_array_bp.route('/matrix', methods=['GET'])
def matrix():
    """阵列节点矩阵 (8×N 网格, 支持过滤)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    q = _arg_str('q')
    state = _arg_str('state')
    where_parts = []
    args = []
    if q:
        where_parts.append("(neuron_id LIKE ? OR employee_name LIKE ? OR neuron_type LIKE ?)")
        kw = f'%{q}%'
        args.extend([kw, kw, kw])
    if state:
        # 状态映射: online→firing, training→firing/charging, idle→resting, offline→refractory
        state_map = {
            'online': "status='firing'",
            'training': "status IN ('firing','charging')",
            'idle': "status='resting'",
            'offline': "status='refractory'",
        }
        cond = state_map.get(state)
        if cond:
            where_parts.append(cond)
    where = ('WHERE ' + ' AND '.join(where_parts)) if where_parts else ''
    sql = (f"SELECT neuron_id, employee_name, neuron_type, neuron_type_cn, layer, "
           f"status, current_potential, fire_count, "
           f"connections_out, connections_in, updated_at AS last_heartbeat "
           f"FROM neural_neurons {where} ORDER BY neuron_id LIMIT 200")
    rows = _query(sql, args)
    # 标准化 state 字段 (映射为前端期望的 online/training/idle/offline)
    state_back_map = {
        'firing': 'online',
        'charging': 'training',
        'resting': 'idle',
        'refractory': 'offline',
    }
    for r in rows:
        r['state'] = state_back_map.get(r.get('status'), 'idle')
        r['load'] = min(100, int((r.get('current_potential') or 0) * 100))
        r['node_id'] = r.get('neuron_id')
        r['cluster'] = r.get('layer')
    return _ok({'nodes': rows, 'count': len(rows)})


@neural_array_bp.route('/node', methods=['GET'])
def node_detail():
    """阵列节点详情"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    nid = _arg_str('id')
    if not nid:
        return _fail('缺少 id 参数', 400)
    r = _query_one(
        "SELECT neuron_id AS node_id, employee_name, neuron_type, neuron_type_cn, layer, "
        "activation_function, threshold, current_potential, fire_count, last_fired_at, "
        "connections_out, connections_in, plasticity, fatigue, status, updated_at AS last_heartbeat "
        "FROM neural_neurons WHERE neuron_id=?", [nid])
    if not r:
        return _fail('节点不存在', 404)
    state_map = {'firing': 'online', 'charging': 'training', 'resting': 'idle', 'refractory': 'offline'}
    r['state'] = state_map.get(r.get('status'), 'idle')
    r['cluster'] = r.get('layer')
    r['role'] = r.get('neuron_type_cn')
    r['load'] = min(100, int((r.get('current_potential') or 0) * 100))
    return _ok({'node': r})


@neural_array_bp.route('/topo', methods=['GET'])
def topo():
    """神经网络拓扑视图 (层+神经元+突触)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    # 获取层
    layers = _query(
        "SELECT layer_id, layer_name, layer_index, layer_type, neuron_count, "
        "avg_activation, is_active FROM neural_layers ORDER BY layer_index")
    # 获取神经元 (每层取最多 20 个, 避免过多)
    neurons = _query(
        "SELECT neuron_id, layer, neuron_type, status, current_potential, "
        "ROW_NUMBER() OVER (PARTITION BY layer ORDER BY fire_count DESC) AS rn "
        "FROM neural_neurons WHERE layer IS NOT NULL")
    # 限制每层最多 20 个神经元
    filtered = [n for n in neurons if (n.get('rn') or 0) <= 20]
    # 计算坐标
    layer_idx = {l.get('layer_id'): l.get('layer_index', i) for i, l in enumerate(layers)}
    if not layer_idx:
        # 退化为按 layer 字段分组
        all_layers = sorted(set(n.get('layer', 'L0') for n in filtered))
        layer_idx = {l: i for i, l in enumerate(all_layers)}
    layer_count = max(len(layer_idx), 1)
    # 按层分组神经元计算 y 坐标
    by_layer = {}
    for n in filtered:
        lk = n.get('layer') or 'L0'
        by_layer.setdefault(lk, []).append(n)
    W, H = 800, 320
    nodes = []
    for lk, ns in by_layer.items():
        li = layer_idx.get(lk, 0)
        x = (W / (layer_count + 1)) * (li + 1)
        for i, n in enumerate(ns):
            y = (H / (len(ns) + 1)) * (i + 1)
            state_map = {'firing': 'online', 'charging': 'training', 'resting': 'idle', 'refractory': 'offline'}
            nodes.append({
                'id': n.get('neuron_id'),
                'x': round(x, 1),
                'y': round(y, 1),
                'layer': lk,
                'state': state_map.get(n.get('status'), 'idle'),
            })
    # 获取突触 (边) — 最多 200 条
    edges_raw = _query(
        "SELECT pre_neuron_id AS from, post_neuron_id AS to, weight "
        "FROM neural_synapses WHERE weight > 0.1 ORDER BY weight DESC LIMIT 200")
    # 过滤: 只保留两端都在 nodes 中的边
    node_ids = {n['id'] for n in nodes}
    edges = [e for e in edges_raw if e.get('from') in node_ids and e.get('to') in node_ids]
    return _ok({'nodes': nodes, 'edges': edges, 'layers': layers})


@neural_array_bp.route('/clusters', methods=['GET'])
def clusters():
    """集群节点状态 (ai_cluster_nodes)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    limit = _arg_int('limit', 100, 1, 500)
    rows = _query(
        "SELECT node_id, node_name AS node_id_alias, node_name, node_type, host, port, "
        "gpu_info, status, health_score, total_inferences, avg_latency_ms, "
        "queue_depth, last_heartbeat, eigenflux_flag "
        "FROM ai_cluster_nodes ORDER BY last_heartbeat DESC LIMIT ?", [limit])
    state_map = {'ONLINE': 'online', 'OFFLINE': 'offline', 'BUSY': 'training', 'IDLE': 'idle'}
    for r in rows:
        r['node_id'] = r.get('node_name') or f"node_{r.get('node_id')}"
        r['cluster'] = r.get('node_type', 'INFERENCE')
        r['role'] = r.get('node_type')
        r['state'] = state_map.get((r.get('status') or '').upper(), 'idle')
        r['load'] = min(100, int((r.get('queue_depth') or 0) * 10))
        r['last_heartbeat'] = r.get('last_heartbeat')
    return _ok({'nodes': rows, 'count': len(rows)})


@neural_array_bp.route('/training', methods=['GET'])
def training():
    """训练进度 (从 neural_learning_events 派生)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    limit = _arg_int('limit', 20, 1, 100)
    # neural_learning_events 表可能不存在, 用 neurons 的 fire_count 近似
    rows = _query(
        "SELECT neuron_id AS task_id, neuron_type AS model, layer, "
        "fire_count AS epoch, fire_count AS total_epochs, "
        "current_potential AS loss, status AS state, "
        "CASE WHEN fire_count > 0 THEN CAST(fire_count AS REAL) / 100 ELSE 0 END AS progress, "
        "neuron_id AS node_id, updated_at "
        "FROM neural_neurons WHERE fire_count > 0 "
        "ORDER BY fire_count DESC LIMIT ?", [limit])
    items = []
    for r in rows:
        prog = min(1.0, float(r.get('progress') or 0))
        items.append({
            'task_id': r.get('task_id'),
            'model': r.get('model'),
            'node_id': r.get('node_id'),
            'epoch': r.get('epoch', 0),
            'total_epochs': max(r.get('epoch', 0), 100),
            'loss': round(float(r.get('loss') or 0), 4),
            'state': 'training' if r.get('state') == 'firing' else 'idle',
            'progress': prog,
        })
    return _ok({'items': items, 'count': len(items)})


@neural_array_bp.route('/heartbeat', methods=['GET'])
def heartbeat():
    """心跳流水 (最近 N 条)"""
    ok, u, err = _check_login()
    if not ok:
        return _fail(err[1], err[0])
    limit = _arg_int('limit', 50, 1, 200)
    rows = _query(
        "SELECT updated_at AS ts, neuron_id AS node_id, status AS state, "
        "current_potential AS load, last_fired_at AS message "
        "FROM neural_neurons WHERE updated_at IS NOT NULL "
        "ORDER BY updated_at DESC LIMIT ?", [limit])
    state_map = {'firing': 'online', 'charging': 'training', 'resting': 'idle', 'refractory': 'offline'}
    for r in rows:
        r['state'] = state_map.get(r.get('state'), 'idle')
        r['load'] = min(100, int((r.get('load') or 0) * 100))
    return _ok({'items': rows, 'count': len(rows)})


bp = Blueprint('neural_array_bp', __name__)

@bp.route('/stats/overview', methods=['GET'])
def stats_overview():
    return jsonify({'status':'ok','code':0,'data':{'module':'neural_array','routes_implemented':1}})

