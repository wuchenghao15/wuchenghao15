#!/usr/bin/env python3
"""
MTSCOS AI 决策引擎服务 (v14.5.0)
==================================
基于规则的决策引擎，支持决策树、策略匹配、优先级排序和决策追溯。

核心能力：
1. 决策规则 - 条件表达式 + 动作
2. 决策树 - 层级化决策路径
3. 策略匹配 - 多规则并行评估
4. 优先级排序 - 高优先级规则先匹配
5. 决策追溯 - 完整决策路径记录
6. 规则版本管理 - 规则变更可回溯
7. 默认规则库 - 系统运维/安全/性能场景
"""
import os
import json
import re
import sqlite3
import random
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_decision.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIDecision')


# ========== 条件评估器 ==========

def evaluate_condition(condition: str, context: Dict) -> bool:
    """评估条件表达式（安全沙箱版）

    支持的语法：
    - field == value
    - field != value
    - field > value / field >= value / field < value / field <= value
    - field in [a, b, c]
    - field contains value
    - field exists
    - field regex pattern
    - 多条件用 AND / OR / NOT 连接
    """
    if not condition or not condition.strip():
        return True

    try:
        # 处理括号
        condition = condition.strip()
        if condition.startswith('(') and condition.endswith(')'):
            # 简单括号剥离
            depth = 0
            can_strip = True
            for i, c in enumerate(condition):
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0 and i < len(condition) - 1:
                        can_strip = False
                        break
            if can_strip:
                return evaluate_condition(condition[1:-1], context)

        # 处理 OR（最低优先级）
        or_parts = _split_logical(condition, ' OR ')
        if len(or_parts) > 1:
            return any(evaluate_condition(p, context) for p in or_parts)

        # 处理 AND
        and_parts = _split_logical(condition, ' AND ')
        if len(and_parts) > 1:
            return all(evaluate_condition(p, context) for p in and_parts)

        # 处理 NOT
        condition = condition.strip()
        if condition.startswith('NOT '):
            return not evaluate_condition(condition[4:], context)

        # 单条件评估
        return _evaluate_single(condition.strip(), context)
    except Exception as e:
        logger.warning(f"条件评估失败: {condition}, error={e}")
        return False


def _split_logical(condition: str, sep: str) -> List[str]:
    """按逻辑分隔符拆分（考虑括号嵌套）"""
    parts = []
    depth = 0
    current = ''
    i = 0
    while i < len(condition):
        if condition[i] == '(':
            depth += 1
            current += condition[i]
            i += 1
        elif condition[i] == ')':
            depth -= 1
            current += condition[i]
            i += 1
        elif depth == 0 and condition[i:i + len(sep)] == sep:
            parts.append(current)
            current = ''
            i += len(sep)
        else:
            current += condition[i]
            i += 1
    if current:
        parts.append(current)
    return parts


def _evaluate_single(expr: str, context: Dict) -> bool:
    """评估单条件"""
    expr = expr.strip()

    # exists
    m = re.match(r'^(\w+)\s+exists$', expr)
    if m:
        return m.group(1) in context

    # not exists
    m = re.match(r'^(\w+)\s+not\s+exists$', expr)
    if m:
        return m.group(1) not in context

    # in [...]
    m = re.match(r'^(\w+)\s+in\s+\[(.+)\]$', expr)
    if m:
        field, values = m.group(1), m.group(2)
        value_list = [v.strip().strip('\'"') for v in values.split(',')]
        actual = context.get(field)
        return str(actual) in value_list or actual in value_list

    # contains
    m = re.match(r'^(\w+)\s+contains\s+(.+)$', expr)
    if m:
        field, value = m.group(1), m.group(2).strip().strip('\'"')
        actual = context.get(field)
        if actual is None:
            return False
        return value in str(actual)

    # regex
    m = re.match(r'^(\w+)\s+regex\s+(.+)$', expr)
    if m:
        field, pattern = m.group(1), m.group(2).strip().strip('\'"')
        actual = context.get(field)
        if actual is None:
            return False
        try:
            return bool(re.search(pattern, str(actual)))
        except re.error:
            return False

    # 比较运算符
    for op in ['==', '!=', '>=', '<=', '>', '<']:
        idx = expr.find(f' {op} ')
        if idx > 0:
            field = expr[:idx].strip()
            value = expr[idx + len(op) + 2:].strip().strip('\'"')
            actual = context.get(field)
            try:
                if op == '==':
                    return str(actual) == value or actual == _coerce(value)
                elif op == '!=':
                    return not (str(actual) == value or actual == _coerce(value))
                else:
                    actual_num = float(actual) if actual is not None else None
                    value_num = float(value)
                    if actual_num is None:
                        return False
                    if op == '>':
                        return actual_num > value_num
                    elif op == '>=':
                        return actual_num >= value_num
                    elif op == '<':
                        return actual_num < value_num
                    elif op == '<=':
                        return actual_num <= value_num
            except (ValueError, TypeError):
                return False

    return False


def _coerce(value: str):
    """尝试将字符串转为对应类型"""
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'
    if value.lower() in ('null', 'none'):
        return None
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


# ========== 默认规则 ==========

DEFAULT_RULES = [
    {
        'rule_id': 'DR-SEC-001',
        'name': '高风险登录拦截',
        'description': '连续失败登录超过5次触发账户锁定',
        'priority': 100,
        'condition': 'failed_login_count >= 5',
        'actions': [
            {'type': 'lock_account', 'duration': 900},
            {'type': 'notify', 'channel': 'security', 'message': '账户已被锁定'},
            {'type': 'log', 'level': 'warning'}
        ],
        'category': 'security',
        'enabled': True
    },
    {
        'rule_id': 'DR-SEC-002',
        'name': '异常IP访问告警',
        'description': '来自黑名单IP的访问触发告警',
        'priority': 95,
        'condition': 'client_ip in blacklist_ips',
        'actions': [
            {'type': 'block_request'},
            {'type': 'notify', 'channel': 'security', 'message': '黑名单IP访问'}
        ],
        'category': 'security',
        'enabled': True
    },
    {
        'rule_id': 'DR-PERF-001',
        'name': '高CPU使用率告警',
        'description': 'CPU使用率超过80%触发优化建议',
        'priority': 80,
        'condition': 'cpu_usage >= 80',
        'actions': [
            {'type': 'notify', 'channel': 'ops', 'message': 'CPU使用率过高'},
            {'type': 'trigger_action', 'action': 'scale_up'}
        ],
        'category': 'performance',
        'enabled': True
    },
    {
        'rule_id': 'DR-PERF-002',
        'name': '内存不足处理',
        'description': '内存使用率超过90%触发清理',
        'priority': 85,
        'condition': 'memory_usage >= 90',
        'actions': [
            {'type': 'trigger_action', 'action': 'cleanup_cache'},
            {'type': 'notify', 'channel': 'ops', 'message': '内存不足，触发清理'}
        ],
        'category': 'performance',
        'enabled': True
    },
    {
        'rule_id': 'DR-OPS-001',
        'name': '数据库慢查询告警',
        'description': '查询耗时超过1秒触发慢查询日志',
        'priority': 70,
        'condition': 'query_duration > 1000',
        'actions': [
            {'type': 'log', 'level': 'warning'},
            {'type': 'trigger_action', 'action': 'optimize_query'}
        ],
        'category': 'operation',
        'enabled': True
    },
    {
        'rule_id': 'DR-OPS-002',
        'name': '磁盘空间预警',
        'description': '磁盘使用率超过85%预警',
        'priority': 75,
        'condition': 'disk_usage >= 85',
        'actions': [
            {'type': 'notify', 'channel': 'ops', 'message': '磁盘空间不足'},
            {'type': 'trigger_action', 'action': 'cleanup_old_files'}
        ],
        'category': 'operation',
        'enabled': True
    },
    {
        'rule_id': 'DR-AI-001',
        'name': 'AI模型置信度不足',
        'description': '模型预测置信度低于0.6时触发人工审核',
        'priority': 60,
        'condition': 'confidence < 0.6',
        'actions': [
            {'type': 'trigger_action', 'action': 'human_review'},
            {'type': 'log', 'level': 'info'}
        ],
        'category': 'ai',
        'enabled': True
    },
    {
        'rule_id': 'DR-AI-002',
        'name': 'AI请求速率限制',
        'description': '单用户AI请求超过60次/分钟触发限流',
        'priority': 90,
        'condition': 'request_rate > 60',
        'actions': [
            {'type': 'trigger_action', 'action': 'rate_limit'},
            {'type': 'notify', 'channel': 'system', 'message': '触发AI限流'}
        ],
        'category': 'ai',
        'enabled': True
    },
]


# ========== 决策引擎 ==========

class AIDecisionEngine:
    """AI 决策引擎"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()
        self._register_defaults()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_decision_rules (
                        rule_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        priority INTEGER DEFAULT 50,
                        condition TEXT NOT NULL,
                        actions TEXT NOT NULL,
                        category TEXT,
                        enabled INTEGER DEFAULT 1,
                        version INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_decision_logs (
                        log_id TEXT PRIMARY KEY,
                        context TEXT,
                        matched_rules TEXT,
                        executed_actions TEXT,
                        decision_path TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_decision_trees (
                        tree_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        root_node TEXT,
                        nodes TEXT,
                        enabled INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_dec_rules_cat ON ai_decision_rules(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_dec_logs_time ON ai_decision_logs(created_at)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化决策引擎数据库失败: {e}")

    def _register_defaults(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for rule in DEFAULT_RULES:
                    cursor.execute('SELECT rule_id FROM ai_decision_rules WHERE rule_id = ?', (rule['rule_id'],))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO ai_decision_rules
                            (rule_id, name, description, priority, condition, actions,
                             category, enabled, version, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            rule['rule_id'], rule['name'], rule['description'],
                            rule['priority'], rule['condition'],
                            json.dumps(rule['actions'], ensure_ascii=False),
                            rule['category'], 1 if rule['enabled'] else 0,
                            1, datetime.now().isoformat(), datetime.now().isoformat()
                        ))
                conn.commit()
        except Exception as e:
            logger.error(f"注册默认决策规则失败: {e}")

    # ========== 规则管理 ==========

    def add_rule(self, rule_id: str, name: str, condition: str, actions: List[Dict],
                priority: int = 50, category: str = 'general',
                description: str = '', enabled: bool = True) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_decision_rules
                    (rule_id, name, description, priority, condition, actions,
                     category, enabled, version, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rule_id, name, description, priority, condition,
                    json.dumps(actions, ensure_ascii=False),
                    category, 1 if enabled else 0, 1,
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                conn.commit()
            return {'success': True, 'rule_id': rule_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_rule(self, rule_id: str, **kwargs) -> Dict:
        allowed_fields = {'name', 'description', 'priority', 'condition', 'actions', 'category', 'enabled'}
        updates = []
        values = []
        for k, v in kwargs.items():
            if k in allowed_fields:
                if k == 'actions':
                    v = json.dumps(v, ensure_ascii=False)
                if k == 'enabled':
                    v = 1 if v else 0
                updates.append(f'{k} = ?')
                values.append(v)
        if not updates:
            return {'success': False, 'error': '无可更新字段'}

        updates.append('updated_at = ?')
        values.append(datetime.now().isoformat())
        values.append(rule_id)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE ai_decision_rules
                    SET {', '.join(updates)}
                    WHERE rule_id = ?
                ''', values)
                conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_rule(self, rule_id: str) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM ai_decision_rules WHERE rule_id = ?', (rule_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False

    def list_rules(self, category: Optional[str] = None, enabled_only: bool = False) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                sql = 'SELECT rule_id, name, description, priority, condition, actions, category, enabled, version FROM ai_decision_rules'
                conditions = []
                params = []
                if category:
                    conditions.append('category = ?')
                    params.append(category)
                if enabled_only:
                    conditions.append('enabled = 1')
                if conditions:
                    sql += ' WHERE ' + ' AND '.join(conditions)
                sql += ' ORDER BY priority DESC, rule_id ASC'
                cursor.execute(sql, params)
                return [
                    {
                        'rule_id': r[0], 'name': r[1], 'description': r[2],
                        'priority': r[3], 'condition': r[4],
                        'actions': json.loads(r[5]) if r[5] else [],
                        'category': r[6], 'enabled': bool(r[7]), 'version': r[8]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    # ========== 决策执行 ==========

    def decide(self, context: Dict, category: Optional[str] = None,
               max_actions: int = 10, log_decision: bool = True) -> Dict:
        """根据上下文执行决策"""
        rules = self.list_rules(category=category, enabled_only=True)

        matched_rules = []
        executed_actions = []
        decision_path = []

        for rule in rules:
            matched = evaluate_condition(rule['condition'], context)
            decision_path.append({
                'rule_id': rule['rule_id'],
                'rule_name': rule['name'],
                'condition': rule['condition'],
                'matched': matched,
                'priority': rule['priority']
            })

            if matched:
                matched_rules.append({
                    'rule_id': rule['rule_id'],
                    'rule_name': rule['name'],
                    'priority': rule['priority']
                })
                for action in rule['actions']:
                    if len(executed_actions) < max_actions:
                        executed_actions.append({
                            **action,
                            'triggered_by': rule['rule_id'],
                            'rule_name': rule['name']
                        })

        result = {
            'matched_rules': matched_rules,
            'executed_actions': executed_actions,
            'decision_path': decision_path,
            'total_evaluated': len(rules),
            'total_matched': len(matched_rules)
        }

        # 记录决策日志
        if log_decision and (matched_rules or len(decision_path) > 0):
            log_id = f"DEC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ai_decision_logs
                        (log_id, context, matched_rules, executed_actions, decision_path, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        log_id,
                        json.dumps(context, ensure_ascii=False, default=str),
                        json.dumps(matched_rules, ensure_ascii=False),
                        json.dumps(executed_actions, ensure_ascii=False),
                        json.dumps(decision_path, ensure_ascii=False),
                        datetime.now().isoformat()
                    ))
                    conn.commit()
            except Exception as e:
                logger.error(f"记录决策日志失败: {e}")

        return result

    # ========== 决策树 ==========

    def create_decision_tree(self, tree_id: str, name: str, nodes: List[Dict],
                            root_node: str, description: str = '') -> Dict:
        """创建决策树

        nodes 格式: [
            {'id': 'n1', 'condition': 'x > 5', 'true_next': 'n2', 'false_next': 'n3', 'actions': [...]},
            {'id': 'n2', 'condition': '', 'actions': [{'type': 'approve'}]},
            {'id': 'n3', 'condition': '', 'actions': [{'type': 'reject'}]}
        ]
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_decision_trees
                    (tree_id, name, description, root_node, nodes, enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tree_id, name, description, root_node,
                    json.dumps(nodes, ensure_ascii=False), 1,
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                conn.commit()
            return {'success': True, 'tree_id': tree_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def evaluate_tree(self, tree_id: str, context: Dict) -> Dict:
        """执行决策树"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT root_node, nodes FROM ai_decision_trees WHERE tree_id = ? AND enabled = 1',
                              (tree_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '决策树不存在或未启用'}

                root_node = row[0]
                nodes = json.loads(row[1]) if row[1] else []
                nodes_by_id = {n['id']: n for n in nodes}

                path = []
                executed_actions = []
                current = root_node
                max_depth = 50  # 防止无限循环
                depth = 0

                while current and depth < max_depth:
                    node = nodes_by_id.get(current)
                    if not node:
                        break

                    path.append(current)
                    condition = node.get('condition', '')
                    matched = evaluate_condition(condition, context) if condition else True

                    # 执行节点动作
                    if matched:
                        executed_actions.extend(node.get('actions', []))

                    # 决定下一节点
                    next_key = 'true_next' if matched else 'false_next'
                    next_node = node.get(next_key)
                    if not next_node:
                        break
                    current = next_node
                    depth += 1

                return {
                    'success': True,
                    'tree_id': tree_id,
                    'path': path,
                    'executed_actions': executed_actions,
                    'depth': depth
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== 查询统计 ==========

    def get_decision_logs(self, limit: int = 20) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT log_id, context, matched_rules, executed_actions, decision_path, created_at
                    FROM ai_decision_logs
                    ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
                return [
                    {
                        'log_id': r[0],
                        'context': json.loads(r[1]) if r[1] else {},
                        'matched_rules': json.loads(r[2]) if r[2] else [],
                        'executed_actions': json.loads(r[3]) if r[3] else [],
                        'decision_path': json.loads(r[4]) if r[4] else [],
                        'created_at': r[5]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM ai_decision_rules')
                total_rules = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_decision_rules WHERE enabled = 1')
                enabled_rules = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_decision_logs')
                total_decisions = cursor.fetchone()[0]
                cursor.execute('SELECT category, COUNT(*) FROM ai_decision_rules GROUP BY category')
                cat_dist = {r[0]: r[1] for r in cursor.fetchall()}
                return {
                    'total_rules': total_rules,
                    'enabled_rules': enabled_rules,
                    'total_decisions': total_decisions,
                    'category_distribution': cat_dist
                }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    engine = AIDecisionEngine()
    print(f"规则总数: {engine.get_statistics()}")

    # 测试决策
    print("\n测试决策1: 高CPU场景")
    result = engine.decide({
        'cpu_usage': 85,
        'memory_usage': 50,
        'failed_login_count': 2,
        'request_rate': 30,
        'confidence': 0.9
    })
    print(f"匹配规则数: {result['total_matched']}")
    print(f"执行动作: {[a.get('type') for a in result['executed_actions']]}")

    print("\n测试决策2: 安全事件场景")
    result = engine.decide({
        'failed_login_count': 6,
        'client_ip': '1.2.3.4',
        'blacklist_ips': ['1.2.3.4', '5.6.7.8']
    })
    print(f"匹配规则数: {result['total_matched']}")
    for rule in result['matched_rules']:
        print(f"  - {rule['rule_name']} (优先级: {rule['priority']})")

    # 测试决策树
    print("\n测试决策树:")
    engine.create_decision_tree(
        'dt-approval', '审批决策树',
        nodes=[
            {'id': 'start', 'condition': 'amount > 10000', 'true_next': 'manager', 'false_next': 'auto', 'actions': []},
            {'id': 'manager', 'condition': '', 'actions': [{'type': 'require_manager_approval'}]},
            {'id': 'auto', 'condition': 'amount > 1000', 'true_next': 'verify', 'false_next': 'approve', 'actions': []},
            {'id': 'verify', 'condition': '', 'actions': [{'type': 'require_verification'}]},
            {'id': 'approve', 'condition': '', 'actions': [{'type': 'auto_approve'}]}
        ],
        root_node='start'
    )
    result = engine.evaluate_tree('dt-approval', {'amount': 500})
    print(f"路径: {result['path']}, 动作: {[a.get('type') for a in result['executed_actions']]}")
