#!/usr/bin/env python3
"""
MTSCOS AI 工作流编排服务 (v14.5.0)
====================================
AI 工作流编排引擎，支持 DAG 任务编排、节点执行、状态追踪、错误重试。

核心能力：
1. 工作流定义 - YAML/JSON 风格声明式 DAG
2. 节点编排 - 顺序/并行/分支/合并
3. 状态机管理 - pending/running/success/failed/skipped
4. 重试机制 - 可配置重试次数和退避策略
5. 上下文传递 - 节点间数据流转
6. 持久化 - 工作流实例和执行历史入库
7. 调度策略 - 立即/延迟/定时
"""
import os
import json
import sqlite3
import random
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_workflow.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIWorkflow')


# ========== 内置节点处理器 ==========

def _node_log_input(context: Dict, params: Dict) -> Dict:
    """日志记录节点"""
    logger.info(f"[WorkflowNode:log] {params.get('message', '')} context={list(context.keys())}")
    return {'logged': True, 'message': params.get('message', '')}


def _node_transform(context: Dict, params: Dict) -> Dict:
    """数据转换节点：从context提取字段并重命名"""
    mapping = params.get('mapping', {})
    result = {}
    for src_key, dst_key in mapping.items():
        if src_key in context:
            result[dst_key] = context[src_key]
    return result


def _node_condition(context: Dict, params: Dict) -> Dict:
    """条件判断节点：返回分支标识"""
    field = params.get('field', '')
    operator = params.get('operator', '==')
    value = params.get('value')
    actual = context.get(field)

    try:
        if operator == '==':
            matched = actual == value
        elif operator == '!=':
            matched = actual != value
        elif operator == '>':
            matched = actual is not None and float(actual) > float(value)
        elif operator == '<':
            matched = actual is not None and float(actual) < float(value)
        elif operator == '>=':
            matched = actual is not None and float(actual) >= float(value)
        elif operator == '<=':
            matched = actual is not None and float(actual) <= float(value)
        elif operator == 'in':
            matched = actual in (value if isinstance(value, list) else [value])
        elif operator == 'contains':
            matched = actual is not None and value in actual
        else:
            matched = False
    except (TypeError, ValueError):
        matched = False

    return {'branch': 'true' if matched else 'false', 'matched': matched}


def _node_delay(context: Dict, params: Dict) -> Dict:
    """延迟节点"""
    seconds = float(params.get('seconds', 0))
    if seconds > 0:
        time.sleep(min(seconds, 30))  # 上限30秒避免阻塞
    return {'delayed': seconds}


def _node_aggregate(context: Dict, params: Dict) -> Dict:
    """聚合节点：合并多个上游节点结果"""
    keys = params.get('keys', [])
    aggregated = {}
    for k in keys:
        if k in context:
            aggregated[k] = context[k]
    return {'aggregated': aggregated, 'count': len(aggregated)}


def _node_notify(context: Dict, params: Dict) -> Dict:
    """通知节点（占位实现，实际可对接通知系统）"""
    channel = params.get('channel', 'log')
    message = params.get('message', '')
    logger.info(f"[Notify:{channel}] {message}")
    return {'notified': True, 'channel': channel}


BUILTIN_HANDLERS: Dict[str, Callable] = {
    'log': _node_log_input,
    'transform': _node_transform,
    'condition': _node_condition,
    'delay': _node_delay,
    'aggregate': _node_aggregate,
    'notify': _node_notify,
}


# ========== 工作流定义 ==========

DEFAULT_WORKFLOWS = [
    {
        'workflow_id': 'wf-data-pipeline',
        'name': '数据处理流水线',
        'description': '采集→清洗→转换→分析→输出',
        'version': '1.0.0',
        'nodes': [
            {'id': 'collect', 'name': '数据采集', 'type': 'log', 'params': {'message': '采集数据'}, 'next': ['clean']},
            {'id': 'clean', 'name': '数据清洗', 'type': 'transform', 'params': {'mapping': {'raw': 'cleaned'}}, 'next': ['branch']},
            {'id': 'branch', 'name': '质量检查', 'type': 'condition', 'params': {'field': 'cleaned', 'operator': '!=', 'value': None}, 'next': ['analyze', 'notify']},
            {'id': 'analyze', 'name': '数据分析', 'type': 'log', 'params': {'message': '执行分析'}, 'next': ['output']},
            {'id': 'output', 'name': '结果输出', 'type': 'notify', 'params': {'channel': 'log', 'message': '输出结果'}, 'next': []},
            {'id': 'notify', 'name': '异常通知', 'type': 'notify', 'params': {'channel': 'alert', 'message': '数据质量异常'}, 'next': []},
        ],
        'edges': [
            {'from': 'collect', 'to': 'clean'},
            {'from': 'clean', 'to': 'branch'},
            {'from': 'branch', 'to': 'analyze', 'condition': 'true'},
            {'from': 'branch', 'to': 'notify', 'condition': 'false'},
            {'from': 'analyze', 'to': 'output'},
        ]
    },
    {
        'workflow_id': 'wf-alert-response',
        'name': '告警自动响应',
        'description': '告警接收→分级→响应→恢复→复盘',
        'version': '1.0.0',
        'nodes': [
            {'id': 'receive', 'name': '告警接收', 'type': 'log', 'params': {'message': '接收告警'}, 'next': ['grade']},
            {'id': 'grade', 'name': '告警分级', 'type': 'condition', 'params': {'field': 'severity', 'operator': '>=', 'value': 3}, 'next': ['urgent', 'normal']},
            {'id': 'urgent', 'name': '紧急响应', 'type': 'notify', 'params': {'channel': 'sms', 'message': '紧急告警'}, 'next': ['recover']},
            {'id': 'normal', 'name': '常规响应', 'type': 'notify', 'params': {'channel': 'email', 'message': '常规告警'}, 'next': ['recover']},
            {'id': 'recover', 'name': '自动恢复', 'type': 'log', 'params': {'message': '执行恢复'}, 'next': ['review']},
            {'id': 'review', 'name': '复盘记录', 'type': 'log', 'params': {'message': '记录复盘'}, 'next': []},
        ],
        'edges': [
            {'from': 'receive', 'to': 'grade'},
            {'from': 'grade', 'to': 'urgent', 'condition': 'true'},
            {'from': 'grade', 'to': 'normal', 'condition': 'false'},
            {'from': 'urgent', 'to': 'recover'},
            {'from': 'normal', 'to': 'recover'},
            {'from': 'recover', 'to': 'review'},
        ]
    },
    {
        'workflow_id': 'wf-batch-inference',
        'name': '批量推理任务',
        'description': '加载数据→批量推理→汇总结果→生成报告',
        'version': '1.0.0',
        'nodes': [
            {'id': 'load', 'name': '加载数据', 'type': 'log', 'params': {'message': '加载数据集'}, 'next': ['infer']},
            {'id': 'infer', 'name': '批量推理', 'type': 'log', 'params': {'message': '执行推理'}, 'next': ['merge']},
            {'id': 'merge', 'name': '汇总结果', 'type': 'aggregate', 'params': {'keys': ['infer', 'load']}, 'next': ['report']},
            {'id': 'report', 'name': '生成报告', 'type': 'notify', 'params': {'channel': 'log', 'message': '报告已生成'}, 'next': []},
        ],
        'edges': [
            {'from': 'load', 'to': 'infer'},
            {'from': 'infer', 'to': 'merge'},
            {'from': 'merge', 'to': 'report'},
        ]
    },
]


class AIWorkflowOrchestrator:
    """AI 工作流编排引擎"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()
        self._register_defaults()
        self._lock = threading.RLock()
        self._running_instances: Dict[str, Dict] = {}

    # ========== 数据库 ==========

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_workflows (
                        workflow_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        version TEXT DEFAULT '1.0.0',
                        definition TEXT NOT NULL,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_workflow_instances (
                        instance_id TEXT PRIMARY KEY,
                        workflow_id TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        context TEXT,
                        current_node TEXT,
                        started_at TEXT,
                        completed_at TEXT,
                        error_message TEXT,
                        triggered_by TEXT,
                        retry_count INTEGER DEFAULT 0
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_workflow_node_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        instance_id TEXT NOT NULL,
                        node_id TEXT NOT NULL,
                        node_name TEXT,
                        status TEXT,
                        started_at TEXT,
                        completed_at TEXT,
                        duration_ms INTEGER,
                        input_data TEXT,
                        output_data TEXT,
                        error_message TEXT,
                        retry_count INTEGER DEFAULT 0
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wf_inst ON ai_workflow_instances(workflow_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wf_hist ON ai_workflow_node_history(instance_id)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化工作流数据库失败: {e}")

    def _register_defaults(self):
        """注册默认工作流定义"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for wf in DEFAULT_WORKFLOWS:
                    cursor.execute('SELECT workflow_id FROM ai_workflows WHERE workflow_id = ?', (wf['workflow_id'],))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO ai_workflows
                            (workflow_id, name, description, version, definition, status, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            wf['workflow_id'], wf['name'], wf['description'], wf['version'],
                            json.dumps(wf, ensure_ascii=False), 'active',
                            datetime.now().isoformat(), datetime.now().isoformat()
                        ))
                conn.commit()
        except Exception as e:
            logger.error(f"注册默认工作流失败: {e}")

    # ========== 工作流管理 ==========

    def create_workflow(self, workflow_id: str, name: str, nodes: List[Dict],
                       edges: List[Dict], description: str = '', version: str = '1.0.0') -> Dict:
        """创建工作流"""
        # 校验DAG
        cycle = self._detect_cycle(nodes, edges)
        if cycle:
            return {'success': False, 'error': f'检测到循环依赖: {" -> ".join(cycle)}'}

        definition = {
            'workflow_id': workflow_id,
            'name': name,
            'description': description,
            'version': version,
            'nodes': nodes,
            'edges': edges,
        }
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_workflows
                    (workflow_id, name, description, version, definition, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    workflow_id, name, description, version,
                    json.dumps(definition, ensure_ascii=False), 'active',
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                conn.commit()
            logger.info(f"创建工作流成功: {workflow_id}")
            return {'success': True, 'workflow_id': workflow_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT definition FROM ai_workflows WHERE workflow_id = ?', (workflow_id,))
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return None
        except Exception:
            return None

    def list_workflows(self) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT workflow_id, name, description, version, status, updated_at FROM ai_workflows ORDER BY updated_at DESC')
                return [
                    {'workflow_id': r[0], 'name': r[1], 'description': r[2],
                     'version': r[3], 'status': r[4], 'updated_at': r[5]}
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def delete_workflow(self, workflow_id: str) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM ai_workflows WHERE workflow_id = ?', (workflow_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False

    # ========== DAG 校验 ==========

    def _detect_cycle(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """检测DAG循环，返回循环节点列表（无循环返回空）"""
        adj: Dict[str, List[str]] = {n['id']: [] for n in nodes}
        for e in edges:
            src, tgt = e['from'], e['to']
            if src in adj and tgt in adj:
                adj[src].append(tgt)

        WHITE, GRAY, BLACK = 0, 1, 2
        color = {n: WHITE for n in adj}
        path = []

        def dfs(node):
            color[node] = GRAY
            path.append(node)
            for neighbor in adj.get(node, []):
                if color[neighbor] == GRAY:
                    # 找到环
                    idx = path.index(neighbor)
                    return path[idx:] + [neighbor]
                if color[neighbor] == WHITE:
                    result = dfs(neighbor)
                    if result:
                        return result
            path.pop()
            color[node] = BLACK
            return None

        for node in adj:
            if color[node] == WHITE:
                cycle = dfs(node)
                if cycle:
                    return cycle
        return []

    def _topological_sort(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """拓扑排序"""
        adj: Dict[str, List[str]] = {n['id']: [] for n in nodes}
        in_degree: Dict[str, int] = {n['id']: 0 for n in nodes}
        for e in edges:
            src, tgt = e['from'], e['to']
            if src in adj and tgt in adj:
                adj[src].append(tgt)
                in_degree[tgt] += 1

        queue = [n for n in in_degree if in_degree[n] == 0]
        result = []
        while queue:
            node = queue.pop(0)
            result.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        return result

    # ========== 工作流执行 ==========

    def trigger(self, workflow_id: str, initial_context: Optional[Dict] = None,
                triggered_by: str = 'system') -> Dict:
        """触发工作流执行"""
        wf = self.get_workflow(workflow_id)
        if not wf:
            return {'success': False, 'error': f'工作流不存在: {workflow_id}'}

        instance_id = f"WF-INST-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        context = initial_context or {}

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_workflow_instances
                    (instance_id, workflow_id, status, context, current_node, started_at, triggered_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    instance_id, workflow_id, 'running',
                    json.dumps(context, ensure_ascii=False),
                    wf['nodes'][0]['id'] if wf['nodes'] else None,
                    datetime.now().isoformat(), triggered_by
                ))
                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        # 同步执行（生产环境可改为异步线程池）
        result = self._execute_instance(instance_id, wf, context)
        return result

    def _execute_instance(self, instance_id: str, workflow: Dict, context: Dict) -> Dict:
        """执行工作流实例"""
        nodes = workflow.get('nodes', [])
        edges = workflow.get('edges', [])
        nodes_by_id = {n['id']: n for n in nodes}
        max_retries = 3

        # 拓扑排序确定执行顺序
        order = self._topological_sort(nodes, edges)

        with self._lock:
            self._running_instances[instance_id] = {
                'workflow_id': workflow['workflow_id'],
                'started_at': datetime.now().isoformat(),
                'status': 'running'
            }

        try:
            for node_id in order:
                node = nodes_by_id.get(node_id)
                if not node:
                    continue

                # 检查条件边
                if not self._should_execute_node(node_id, edges, context):
                    self._record_node_history(instance_id, node, 'skipped', None, None, 0, None)
                    continue

                # 执行节点（带重试）
                node_result = None
                error = None
                for attempt in range(max_retries + 1):
                    start_ts = time.time()
                    try:
                        handler = BUILTIN_HANDLERS.get(node['type'])
                        if handler:
                            node_result = handler(context, node.get('params', {}))
                        else:
                            node_result = {'unknown_type': node['type']}
                        error = None
                        break
                    except Exception as e:
                        error = str(e)
                        logger.warning(f"节点 {node_id} 第{attempt+1}次执行失败: {e}")
                        if attempt < max_retries:
                            time.sleep(0.5 * (attempt + 1))

                duration_ms = int((time.time() - start_ts) * 1000)

                if error:
                    self._record_node_history(instance_id, node, 'failed', None, node_result, duration_ms, error)
                    # 标记实例失败
                    self._update_instance_status(instance_id, 'failed', error)
                    return {'success': False, 'instance_id': instance_id, 'failed_node': node_id, 'error': error}

                # 记录成功
                self._record_node_history(instance_id, node, 'success', None, node_result, duration_ms, None)

                # 合并结果到上下文
                if node_result:
                    context[node_id] = node_result
                    # 同时把结果中的字段提到顶层（如果是dict）
                    if isinstance(node_result, dict):
                        for k, v in node_result.items():
                            if k not in context and k not in [n['id'] for n in nodes]:
                                context[k] = v

                # 更新当前节点
                self._update_instance_progress(instance_id, node_id, context)

            # 完成
            self._update_instance_status(instance_id, 'success', None)
            return {
                'success': True,
                'instance_id': instance_id,
                'context': context,
                'completed_nodes': len(order)
            }
        finally:
            with self._lock:
                if instance_id in self._running_instances:
                    self._running_instances[instance_id]['status'] = 'completed'
                    self._running_instances[instance_id]['completed_at'] = datetime.now().isoformat()

    def _should_execute_node(self, node_id: str, edges: List[Dict], context: Dict) -> bool:
        """根据条件边判断节点是否应该执行"""
        incoming_conditions = [e for e in edges if e.get('to') == node_id and 'condition' in e]
        if not incoming_conditions:
            return True
        # 任一条件满足即执行（OR 语义）
        for e in incoming_conditions:
            src = e['from']
            src_result = context.get(src, {})
            branch = src_result.get('branch') if isinstance(src_result, dict) else None
            if branch == e['condition']:
                return True
        return False

    def _record_node_history(self, instance_id: str, node: Dict, status: str,
                            input_data: Any, output_data: Any, duration_ms: int, error: Optional[str]):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_workflow_node_history
                    (instance_id, node_id, node_name, status, started_at, completed_at,
                     duration_ms, input_data, output_data, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    instance_id, node['id'], node.get('name', ''),
                    status, datetime.now().isoformat(),
                    datetime.now().isoformat(), duration_ms,
                    json.dumps(input_data, ensure_ascii=False) if input_data else None,
                    json.dumps(output_data, ensure_ascii=False) if output_data else None,
                    error
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"记录节点历史失败: {e}")

    def _update_instance_status(self, instance_id: str, status: str, error: Optional[str]):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE ai_workflow_instances
                    SET status = ?, completed_at = ?, error_message = ?
                    WHERE instance_id = ?
                ''', (status, datetime.now().isoformat(), error, instance_id))
                conn.commit()
        except Exception as e:
            logger.error(f"更新实例状态失败: {e}")

    def _update_instance_progress(self, instance_id: str, node_id: str, context: Dict):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE ai_workflow_instances
                    SET current_node = ?, context = ?
                    WHERE instance_id = ?
                ''', (node_id, json.dumps(context, ensure_ascii=False), instance_id))
                conn.commit()
        except Exception as e:
            logger.error(f"更新实例进度失败: {e}")

    # ========== 查询统计 ==========

    def get_instance(self, instance_id: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_workflow_instances WHERE instance_id = ?', (instance_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'instance_id': row[0], 'workflow_id': row[1], 'status': row[2],
                    'context': json.loads(row[3]) if row[3] else {},
                    'current_node': row[4], 'started_at': row[5], 'completed_at': row[6],
                    'error_message': row[7], 'triggered_by': row[8], 'retry_count': row[9]
                }
        except Exception:
            return None

    def get_instance_history(self, instance_id: str) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT node_id, node_name, status, started_at, completed_at,
                           duration_ms, error_message
                    FROM ai_workflow_node_history
                    WHERE instance_id = ?
                    ORDER BY id ASC
                ''', (instance_id,))
                return [
                    {'node_id': r[0], 'node_name': r[1], 'status': r[2],
                     'started_at': r[3], 'completed_at': r[4], 'duration_ms': r[5],
                     'error_message': r[6]}
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM ai_workflows')
                total_workflows = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_workflow_instances')
                total_instances = cursor.fetchone()[0]
                cursor.execute("SELECT status, COUNT(*) FROM ai_workflow_instances GROUP BY status")
                status_dist = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM ai_workflow_node_history')
                total_node_exec = cursor.fetchone()[0]
                cursor.execute("SELECT status, COUNT(*) FROM ai_workflow_node_history GROUP BY status")
                node_status = {r[0]: r[1] for r in cursor.fetchall()}
                return {
                    'total_workflows': total_workflows,
                    'total_instances': total_instances,
                    'instance_status': status_dist,
                    'total_node_executions': total_node_exec,
                    'node_status': node_status,
                    'success_rate': (status_dist.get('success', 0) / total_instances * 100) if total_instances else 0
                }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    orchestrator = AIWorkflowOrchestrator()
    print(f"已注册工作流: {len(orchestrator.list_workflows())}")
    print("默认工作流列表:")
    for wf in orchestrator.list_workflows():
        print(f"  - {wf['workflow_id']}: {wf['name']}")

    # 触发测试
    print("\n触发数据处理流水线...")
    result = orchestrator.trigger('wf-data-pipeline', initial_context={'raw': 'sample data', 'severity': 2})
    print(f"执行结果: {result['success']}, 实例: {result.get('instance_id')}")

    stats = orchestrator.get_statistics()
    print(f"\n统计: {stats}")
