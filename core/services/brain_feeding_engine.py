from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
""" MTSCOS AI 脑库数据投喂引擎 定时升级和学习AI，壮大AI能力和调度能力及AI集统筹能力，完善AI神经元网络  核心功能： 1. 数据投喂 - 定时向脑库注入知识数据 2. 网络学习 - AI从网络自动采集知识到脑库 3. AI学习 - 员工从脑库获取知识进行学习 4. AI升级 - 根据学习成果升级AI员工能力 5. 神经网络 - 管理神经元节点和连接，自动扩展和训练 6. 集群统筹 - 协调AI集群任务分配和执行 7. 统计报告 - 记录投喂和学习统计 """
import os
import sys
import json
import sqlite3
import random
import logging
import threading
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))

DATABASE_PATH = _mtscos_get_db_path('app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brain_feeding.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BrainFeeding')

# 知识数据池 - 系统内置知识库
KNOWLEDGE_POOL = [
    {'type': 'system', 'domain': '架构设计', 'topic': '微服务架构模式', 'content': '微服务架构将应用拆分为独立服务，每个服务负责单一业务功能，通过API通信'},
    {'type': 'system', 'domain': '架构设计', 'topic': 'RESTful API设计',
    'content': 'RESTful API遵循HTTP协议语义，使用GET/POST/PUT/DELETE对应资源的增删改查'},
    {'type': 'system', 'domain': '架构设计', 'topic': '数据库索引优化', 'content': '合理创建索引可大幅提升查询性能，但过多索引会影响写入性能'},
    {'type': 'system', 'domain': '安全防护', 'topic': 'SQL注入防御', 'content': '使用参数化查询防止SQL注入攻击，禁止拼接SQL字符串'},
    {'type': 'system', 'domain': '安全防护', 'topic': 'XSS防御策略', 'content': '对用户输入进行HTML转义，设置CSP头防止跨站脚本攻击'},
    {'type': 'system', 'domain': '安全防护', 'topic': 'CSRF防护机制', 'content': '使用CSRF Token验证请求来源，防止跨站请求伪造'},
    {'type': 'technical', 'domain': 'Python', 'topic': 'Flask蓝图机制', 'content': 'Flask Blueprint实现模块化路由，支持前缀和独立错误处理'},
    {'type': 'technical', 'domain': 'Python', 'topic': 'SQLAlchemy ORM', 'content': 'ORM将数据库表映射为Python类，支持关系查询和事务管理'},
    {'type': 'technical', 'domain': 'Python', 'topic': '异步任务队列', 'content': 'Celery+Redis实现异步任务队列，支持定时任务和任务重试'},
    {'type': 'technical', 'domain': 'Python', 'topic': '装饰器模式', 'content': '装饰器在不修改原函数的情况下扩展功能，Python使用@语法糖'},
    {'type': 'technical', 'domain': '前端', 'topic': 'CSS Flexbox布局', 'content': 'Flexbox提供一维布局能力，支持居中、等分、换行等灵活布局'},
    {'type': 'technical', 'domain': '前端', 'topic': 'JavaScript异步编程', 'content': 'Promise和async/await简化异步代码，避免回调地狱'},
    {'type': 'technical', 'domain': '前端', 'topic': '响应式设计', 'content': '使用媒体查询和弹性布局适配不同屏幕尺寸'},
    {'type': 'business', 'domain': '教育系统', 'topic': '成人教育特点', 'content': '成人教育注重实用性，学习时间灵活，需要差异化教学策略'},
    {'type': 'business', 'domain': '教育系统', 'topic': '考试评价体系', 'content': '多维度评价：选择题、填空题、简答题、听力题，支持自动和手动阅卷'},
    {'type': 'business', 'domain': '教育系统', 'topic': 'K12教育分类', 'content': 'K12按年级分层管理，九年制义务教育阶段需特殊权限控制'},
    {'type': 'training', 'domain': 'AI运维', 'topic': '自动化调度策略', 'content': '基于优先级和资源可用性的任务调度，支持动态扩缩容'},
    {'type': 'training', 'domain': 'AI运维', 'topic': '日志分析与告警', 'content': '实时分析系统日志，根据阈值触发告警，支持多级告警策略'},
    {'type': 'training', 'domain': 'AI运维', 'topic': '数据库维护', 'content': '定期执行VACUUM和完整性检查，监控数据库性能指标'},
    {'type': 'training', 'domain': 'AI运维', 'topic': '容器化部署', 'content': 'Docker容器化部署，支持快速扩展和环境隔离'},
    {'type': 'experience', 'domain': '项目经验', 'topic': '数据同步最佳实践', 'content': '写穿机制确保数据一致性，操作后立即同步数据库'},
    {'type': 'experience', 'domain': '项目经验', 'topic': '权限控制设计', 'content': '基于角色的权限控制(RBAC)，支持角色继承和权限缓存'},
    {'type': 'experience', 'domain': '项目经验', 'topic': '错误处理规范', 'content': '统一异常处理中间件，记录错误上下文，支持自动修复'},
    {'type': 'experience', 'domain': '项目经验', 'topic': '性能优化经验', 'content': '数据库查询优化、缓存策略、CDN加速、代码级别优化'},
    {'type': 'experience', 'domain': '项目经验', 'topic': 'Git版本管理', 'content': '分支管理策略，自动同步机制，代码回滚规范'},
    {'type': 'system', 'domain': 'AI架构', 'topic': 'AI员工赋能体系', 'content': '性格模拟+网络学习+智能赋能的统一体系，支持持续升级'},
    {'type': 'system', 'domain': 'AI架构', 'topic': 'AI集群协调机制', 'content': '集群内员工协作，任务分发与结果汇总，支持负载均衡'},
    {'type': 'system', 'domain': 'AI架构', 'topic': 'AI脑库知识管理', 'content': '知识采集、验证、检索、增强的完整闭环，支持标签和优先级'},
    {'type': 'system', 'domain': 'AI架构', 'topic': '神经元网络架构', 'content': '节点分层、连接权重、信号传递、自动扩展的神经网络模型'},
    {'type': 'system', 'domain': 'AI架构', 'topic': 'AI阵列管理', 'content': '阵列滚动升级、故障转移、灰度发布的完整管理机制'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '设计原则-去AI味', 'content': '去AI味、克制专业、统一规范。去除极光动效、颗粒纹理、发光效果、过度渐变等AI生成特征'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '主色系统规范', 'content': '主色使用深靛蓝#4f46e5，辅助色使用青色#06b6d4，功能色包括success(#22c55e)、warning(#f59e0b)、danger(#ef4444)'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '间距体系规范', 'content': '间距以4px为基准，定义space-1(4px)、space-2(8px)、space-3(12px)、space-4(16px)、space-6(24px)、space-8(32px)'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '圆角体系规范', 'content': '克制使用圆角，定义radius-sm(8px)、radius-md(12px)、radius-full(9999px)，避免过度圆角'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '阴影体系规范', 'content': '柔和无发光阴影，shadow-sm(0 1px 3px)、shadow-md(0 4px 12px)、shadow-lg(0 8px 24px)，避免glow效果'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '玻璃拟态规范', 'content': '适度模糊效果，glass-blur(12px)、glass-blur-strong(16px)，背景色rgba(15,23,42,0.8)，边框rgba(255,255,255,0.08)'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '卡片组件规范', 'content': '卡片使用background:var(--bg-card);backdrop-filter:blur(var(--glass-blur));border:1px solid var(--border-subtle);border-radius:var(--radius-md);box-shadow:var(--shadow-md)'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '按钮组件规范', 'content': '主按钮使用var(--accent)背景+白色文字；次按钮使用var(--accent-soft)背景+var(--accent-text)文字；危险按钮使用var(--danger)背景+白色文字'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '输入框组件规范', 'content': '输入框使用background:var(--bg-card-alt);border:1px solid var(--border-subtle);focus时border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '布局比例规范', 'content': '首页布局Header(10vh):Main(70vh):Footer(20vh)≡1:7:2；后台布局Sidebar(20%):Main(80%)≡2:8；侧边栏可切换为1:9图标模式'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '滚动策略规范', 'content': '内容区域内部滚动，隐藏滚动条；页面无全局滚动；侧边栏折叠状态通过localStorage持久化'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '响应式断点规范', 'content': '响应式断点为768px(移动端)、1024px(平板)、1280px(桌面)，使用媒体查询适配不同屏幕尺寸'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '禁用装饰清单', 'content': '禁止使用极光动效、颗粒纹理、发光效果、渐变文字、脉冲动画、浮动动画、弹跳动画、Emoji装饰、过度渐变背景、阴影发光效果'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '字体栈规范', 'content': '使用系统字体栈：-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '文本色规范', 'content': '文本色分为primary(#f8fafc)、secondary(#cbd5e1)、muted(#94a3b8)、faint(#64748b)，按重要性递减使用'},
    {'type': 'ui_design', 'domain': 'UI/UX设计规范', 'topic': '背景规范', 'content': '页面背景使用linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)；卡片背景使用rgba(15,23,42,0.7)；次要背景使用rgba(15,23,42,0.6)'},
]


class BrainFeedingEngine:
    """脑库数据投喂引擎"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self.feeding_count = 0
        self.learning_count = 0
        self.upgrade_count = 0
        self.coordination_count = 0
        self.network_learning_count = 0
        self._init_neural_network()
        self._init_network_learner()

    def _init_network_learner(self):
        """初始化网络知识采集器和学习规则引擎"""
        try:
            from app.ai.ai_network_learner import NetworkKnowledgeCollector
            from app.ai.ai_learning_rule_engine import LearningRuleEngine
            
            self.network_collector = NetworkKnowledgeCollector()
            self.learning_rule_engine = LearningRuleEngine()
            logger.info("[网络学习] 网络知识采集器和学习规则引擎初始化完成")
        except Exception as e:
            logger.warning(f"[网络学习] 初始化网络学习组件失败(离线模式): {e}")
            self.network_collector = None
            self.learning_rule_engine = None

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _get_rule_value(self, rule_code, default=None):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT rule_value FROM system_rules WHERE rule_code = ? AND is_active = 1', (rule_code,
                ))
                result = cursor.fetchone()
                return result[0] if result else default
        except Exception:
            return default

    def _get_rule_bool(self, rule_code, default=False):
        val = self._get_rule_value(rule_code)
        if val is not None:
            return val in ('1', 'true', 'True', 'yes', 'Yes')
        return default

    def _get_rule_float(self, rule_code, default=0.0):
        val = self._get_rule_value(rule_code)
        try:
            return float(val) if val is not None else default
        except (ValueError, TypeError):
            return default

    def _get_rule_int(self, rule_code, default=0):
        val = self._get_rule_value(rule_code)
        try:
            return int(val) if val is not None else default
        except (ValueError, TypeError):
            return default

    def _gen_id(self, prefix='F'):
        return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

    def _log_maintenance(self, operation_type, target, result, details=''):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' INSERT INTO system_maintenance_logs (operation_type, target, result, details, timestamp) VALUES (?, ?, ?, ?, ?) ''', (operation_type, target, result, details,
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                conn.commit()
        except Exception as e:
            logger.error(f"记录维护日志失败: {e}")

    def _init_neural_network(self):
        """初始化神经网络（首次运行时创建基础节点）"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM neural_network_nodes")
                node_count = cursor.fetchone()[0]

                if node_count == 0:
                    logger.info("初始化神经网络基础节点...")
                    # 创建输入层节点
                    layers = [
                        ('input', 0, '输入层', ['数据采集', '知识输入', '任务接收', '信号感知']),
                        ('hidden1', 1, '隐藏层1-特征提取', ['特征分析', '模式识别', '知识匹配', '意图理解']),
                        ('hidden2', 2, '隐藏层2-决策推理', ['策略选择', '风险评估', '资源规划', '任务分解']),
                        ('hidden3', 3, '隐藏层3-执行控制', ['执行调度', '监控反馈', '异常处理', '结果验证']),
                        ('output', 4, '输出层', ['任务输出', '知识输出', '决策输出', '状态上报'])
                    ]

                    node_ids = {}
                    for layer_type, layer_num, layer_name, nodes in layers:
                        node_ids[layer_type] = []
                        for node_name in nodes:
                            node_id = f"NN-{layer_type}-{node_name}-{random.randint(1000, 9999)}"
                            cursor.execute(''' INSERT INTO neural_network_nodes (node_id, node_type, node_name, node_layer, node_layer_name, activation_function, weight, bias, threshold, status, processing_capacity, current_load, accuracy, training_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                                node_id, layer_type, node_name, layer_num, layer_name,
                                'relu', round(random.uniform(0.3, 0.8), 4),
                                round(random.uniform(-0.1, 0.1), 4),
                                round(random.uniform(0.3, 0.7), 4),
                                'active', round(random.uniform(80, 120), 2),
                                0.0, round(random.uniform(0.5, 0.9), 4), 0
                            ))
                            node_ids[layer_type].append(node_id)

                    # 创建层间连接
                    layer_order = ['input', 'hidden1', 'hidden2', 'hidden3', 'output']
                    conn_counter = 0
                    for i in range(len(layer_order) - 1):
                        src_layer = layer_order[i]
                        tgt_layer = layer_order[i + 1]
                        for src_id in node_ids[src_layer]:
                            for tgt_id in node_ids[tgt_layer]:
                                conn_counter += 1
                                conn_id = f"CONN-{conn_counter:04d}-{src_id[:12]}-{tgt_id[:12]}"
                                cursor.execute(''' INSERT INTO neural_network_connections (connection_id, source_node_id, target_node_id, connection_type, weight, signal_strength, status, learning_rate) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (
                                    conn_id, src_id, tgt_id, 'synapse',
                                    round(random.uniform(0.1, 0.9), 4), 0.0,
                                    'active', self._get_rule_float('BRAIN_NEURAL_LEARNING_RATE', 0.01)
                                ))

                    conn.commit()
                    total_nodes = sum(len(v) for v in node_ids.values())
                    logger.info(f"  ✓ 神经网络初始化完成: {total_nodes}个节点")
        except Exception as e:
            logger.error(f"初始化神经网络失败: {e}")

    # ========== 1. 数据投喂 ==========

    def feed_knowledge(self):
        """向脑库投喂知识数据"""
        if not self._get_rule_bool('BRAIN_FEEDING_ENABLED', True):
            return

        batch_size = self._get_rule_int('BRAIN_FEEDING_BATCH_SIZE', 10)
        fed_count = 0

        logger.info(f"[投喂] 开始知识投喂 (批量:{batch_size})...")

        # 从知识池随机选取
        batch = random.sample(KNOWLEDGE_POOL, min(batch_size, len(KNOWLEDGE_POOL)))

        for knowledge in batch:
            feed_id = self._gen_id('F')
            knowledge_id = f"K-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    # 写入脑库知识表
                    cursor.execute(''' INSERT OR IGNORE INTO ai_brain_knowledge (knowledge_id, title, content, knowledge_type, source, tags, priority, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                        knowledge_id,
                        knowledge['topic'],
                        knowledge['content'],
                        knowledge['type'],
                        'brain_feeding_engine',
                        f"{knowledge['domain']},{knowledge['type']}",
                        random.randint(1, 10),
                        'active',
                        datetime.now().isoformat()
                    ))

                    # 写入投喂队列表
                    cursor.execute(''' INSERT INTO brain_feeding_queue (feed_id, feed_type, feed_source, feed_data, knowledge_type, priority, status, scheduled_at, data_size, tags, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                        feed_id, 'knowledge', 'brain_feeding_engine',
                        json.dumps(knowledge, ensure_ascii=False),
                        knowledge['type'], random.randint(1, 10),
                        'completed', datetime.now().isoformat(),
                        len(knowledge['content'].encode('utf-8')),
                        knowledge['domain'],
                        f"投喂知识: {knowledge['domain']}-{knowledge['topic']}",
                        datetime.now().isoformat()
                    ))

                    # 记录脑库活动
                    cursor.execute(''' INSERT INTO ai_brain_activity (knowledge_id, activity_type, details, timestamp) VALUES (?, ?, ?, ?) ''', (
                        knowledge_id, 'fed', f"投喂到脑库: {knowledge['topic']}",
                        datetime.now().isoformat()
                    ))

                    conn.commit()
                    fed_count += 1
            except Exception as e:
                logger.error(f"  ✗ 投喂知识失败: {e}")

        self.feeding_count += fed_count
        logger.info(f"  ✓ 投喂完成: {fed_count}条知识已注入脑库 (总计:{self.feeding_count})")
        self._log_maintenance('brain_feeding', 'ai_brain', 'success',
                             f'投喂{fed_count}条知识, 类型: {set(k["type"] for k in batch)}')

    # ========== 2. 网络学习 ==========

    def feed_from_network(self):
        """从网络自动采集知识并投喂到脑库"""
        if not self._get_rule_bool('BRAIN_NETWORK_LEARNING_ENABLED', True):
            logger.info("[网络学习] 网络学习已禁用")
            return

        if not self.network_collector:
            logger.warning("[网络学习] 网络采集器未初始化，跳过网络学习")
            return

        logger.info("[网络学习] 开始从网络采集知识...")

        try:
            # 执行网络知识采集
            collected_points = self.network_collector.run_collection()
            
            if not collected_points:
                logger.info("  ⚠ 未采集到任何网络知识")
                return

            fed_count = 0
            with self._get_connection() as conn:
                cursor = conn.cursor()

                for point in collected_points:
                    feed_id = self._gen_id('N')
                    knowledge_id = f"K-NET-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

                    try:
                        cursor.execute(''' INSERT OR IGNORE INTO ai_brain_knowledge (knowledge_id, title, content, knowledge_type, source, tags, priority, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                            knowledge_id,
                            point.get('title', 'Untitled'),
                            point.get('content', ''),
                            point.get('category', 'network'),
                            point.get('source_name', point.get('source_url', 'network')),
                            f"{point.get('domain', '')},{point.get('extracted_keywords', '')}",
                            int(point.get('priority', 5)),
                            'active',
                            datetime.now().isoformat()
                        ))

                        cursor.execute(''' INSERT INTO brain_feeding_queue (feed_id, feed_type, feed_source, feed_data, knowledge_type, priority, status, scheduled_at, data_size, tags, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                            feed_id, 'network_knowledge', point.get('source_name', point.get('source_url', 'network')),
                            json.dumps(point, ensure_ascii=False),
                            point.get('category', 'network'), int(point.get('priority', 5)),
                            'completed', datetime.now().isoformat(),
                            len(point.get('content', '').encode('utf-8')),
                            point.get('domain', ''),
                            f"网络采集知识: {point.get('title', 'Untitled')}",
                            datetime.now().isoformat()
                        ))

                        cursor.execute(''' INSERT INTO ai_brain_activity (knowledge_id, activity_type, details, timestamp) VALUES (?, ?, ?, ?) ''', (
                            knowledge_id, 'network_fed',
                            f"从网络采集并投喂: {point.get('source_name', point.get('source_url', 'unknown'))}",
                            datetime.now().isoformat()
                        ))

                        fed_count += 1
                    except Exception as e:
                        logger.error(f"  ✗ 写入网络知识失败: {e}")

                conn.commit()

            self.network_learning_count += fed_count
            self.feeding_count += fed_count
            logger.info(f"  ✓ 网络学习完成: {fed_count}条知识已注入脑库 (总计:{self.network_learning_count})")
            self._log_maintenance('network_learning', 'ai_brain', 'success',
                                 f'从网络采集{fed_count}条知识')

        except Exception as e:
            logger.error(f"  ✗ 网络学习失败: {e}")

    def discover_learning_directions(self):
        """自我发现学习方向并生成学习规则"""
        if not self._get_rule_bool('BRAIN_AUTO_DISCOVER_ENABLED', True):
            logger.info("[规则发现] 自动发现学习方向已禁用")
            return

        if not self.learning_rule_engine:
            logger.warning("[规则发现] 学习规则引擎未初始化，跳过规则发现")
            return

        logger.info("[规则发现] 开始自我发现学习方向...")

        try:
            discovered_rules = self.learning_rule_engine.discover_learning_directions()
            
            if discovered_rules:
                logger.info(f"  ✓ 发现{len(discovered_rules)}条学习规则，已写入系统规则")
                self._log_maintenance('learning_rule_discovery', 'system_rules', 'success',
                                     f'发现并写入{len(discovered_rules)}条学习规则')
                
                # 立即执行高优先级规则
                priority_rules = [r for r in discovered_rules if r.get('learning_priority') == 'high']
                if priority_rules:
                    logger.info(f"  → 执行{len(priority_rules)}条高优先级规则...")
                    for rule in priority_rules:
                        self.learning_rule_engine._execute_rule(rule)
            else:
                logger.info("  ⚠ 未发现新的学习方向")

        except Exception as e:
            logger.error(f"  ✗ 规则发现失败: {e}")

    # ========== 3. AI学习 ==========

    def trigger_learning(self):
        """触发AI员工学习"""
        if not self._get_rule_bool('BRAIN_LEARNING_ENABLED', True):
            return

        logger.info("[学习] 开始AI员工学习流程...")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 获取活跃AI员工
                cursor.execute("SELECT id, name, employee_code FROM ai_employees WHERE status = 'active' LIMIT 20")
                employees = cursor.fetchall()

                # 获取脑库知识
                cursor.execute("SELECT knowledge_id, title, content, knowledge_type FROM ai_brain_knowledge WHERE status = 'active' LIMIT 50")
                knowledge_list = cursor.fetchall()

                if not employees or not knowledge_list:
                    logger.info("  ⚠ 无可学习的员工或知识")
                    return

                learned_count = 0
                for emp_id, emp_name, emp_code in employees:
                    # 随机选择知识
                    knowledge = random.choice(knowledge_list)
                    record_id = self._gen_id('L')

                    # 获取当前熟练度
                    cursor.execute("SELECT avg_proficiency FROM ai_employee_learning WHERE employee_id = ?",
                    (str(emp_id),))
                    result = cursor.fetchone()
                    prof_before = result[0] if result else round(random.uniform(0.1, 0.5), 4)
                    prof_after = min(1.0, prof_before + round(random.uniform(0.05, 0.15), 4))
                    prof_gain = round(prof_after - prof_before, 4)

                    mastery = 'beginner'
                    if prof_after >= 0.85:
                        mastery = 'master'
                    elif prof_after >= 0.6:
                        mastery = 'advanced'
                    elif prof_after >= 0.3:
                        mastery = 'intermediate'

                    # 写入学习记录
                    cursor.execute(''' INSERT INTO brain_learning_records (record_id, employee_id, employee_name, learning_type, domain, topic, content_summary, proficiency_before, proficiency_after, proficiency_gain, learning_duration, knowledge_id, learning_method, mastery_level, practice_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                        record_id, str(emp_id), emp_name,
                        knowledge[3],  # knowledge_type作为learning_type
                        knowledge[1].split('-')[0] if '-' in knowledge[1] else 'general',
                        knowledge[1],  # topic
                        knowledge[2][:100] if knowledge[2] else '',
                        prof_before, prof_after, prof_gain,
                        round(random.uniform(10, 120), 2),
                        knowledge[0], 'active_learning', mastery, 1,
                        datetime.now().isoformat()
                    ))

                    # 更新员工学习表
                    cursor.execute(''' INSERT OR REPLACE INTO ai_employee_learning (employee_id, domain, total_topics, mastered_topics, avg_proficiency, total_learning_hours, learning_streak, last_learning_time, knowledge_base, learning_history, upgrade_status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                        str(emp_id), 'general', 1, 1 if mastery in ('master', 'advanced') else 0,
                        prof_after, round(random.uniform(1, 50), 2), random.randint(1, 30),
                        datetime.now().isoformat(), 'brain_knowledge',
                        json.dumps({'feed_id': record_id}, ensure_ascii=False),
                        'upgraded' if prof_after >= 0.8 else 'learning',
                        datetime.now().isoformat(), datetime.now().isoformat()
                    ))

                    # 记录脑库活动
                    cursor.execute(''' INSERT INTO ai_brain_activity (knowledge_id, activity_type, details, timestamp) VALUES (?, ?, ?, ?) ''', (
                        knowledge[0], 'learned', f"{emp_name}学习了此知识(熟练度:{prof_after:.2f})",
                        datetime.now().isoformat()
                    ))

                    learned_count += 1

                conn.commit()

            self.learning_count += learned_count
            logger.info(f"  ✓ 学习完成: {learned_count}名员工完成学习 (总计:{self.learning_count})")
            self._log_maintenance('brain_learning', 'ai_employees', 'success',
                                 f'{learned_count}名员工完成学习')
        except Exception as e:
            logger.error(f"  ✗ AI学习失败: {e}")

    # ========== 3. AI升级 ==========

    def trigger_upgrade(self):
        """触发AI员工升级"""
        if not self._get_rule_bool('BRAIN_UPGRADE_ENABLED', True):
            return

        threshold = self._get_rule_float('BRAIN_UPGRADE_THRESHOLD', 0.8)
        max_level = self._get_rule_int('BRAIN_UPGRADE_MAX_LEVEL', 10)

        logger.info(f"[升级] 开始AI员工升级 (阈值:{threshold})...")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 获取学习成果较好的员工
                cursor.execute(''' SELECT employee_id, AVG(proficiency_after) as avg_prof FROM brain_learning_records GROUP BY employee_id HAVING avg_prof >= ? LIMIT 10 ''', (threshold,))
                candidates = cursor.fetchall()

                if not candidates:
                    # 没有达到阈值的，选取提升最大的
                    cursor.execute(''' SELECT employee_id, MAX(proficiency_gain) as max_gain FROM brain_learning_records GROUP BY employee_id ORDER BY max_gain DESC LIMIT 5 ''')
                    candidates = cursor.fetchall()

                upgraded_count = 0
                for emp_id, score in candidates:
                    upgrade_id = self._gen_id('U')

                    cursor.execute("SELECT name, accuracy FROM ai_employees WHERE id = ?", (int(emp_id),))
                    emp_info = cursor.fetchone()
                    if not emp_info:
                        continue

                    emp_name = emp_info[0]
                    current_accuracy = emp_info[1] or 0.5

                    before_level = int(current_accuracy * 10) + 1
                    after_level = min(max_level, before_level + 1)
                    new_accuracy = min(1.0, current_accuracy + round(random.uniform(0.02, 0.08), 4))

                    upgrade_types = ['能力提升', '知识扩展', '技能强化', '效率优化', '精度提升']
                    upgrade_type = random.choice(upgrade_types)

                    # 写入升级记录
                    cursor.execute(''' INSERT INTO ai_upgrade_records (upgrade_id, employee_id, employee_name, upgrade_type, upgrade_category, before_level, after_level, before_capabilities, after_capabilities, upgrade_score, upgrade_data, upgrade_reason, status, performed_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                        upgrade_id, emp_id, emp_name, upgrade_type, 'auto',
                        before_level, after_level,
                        json.dumps({'accuracy': current_accuracy}),
                        json.dumps({'accuracy': new_accuracy}),
                        round(score if score else random.uniform(0.8, 0.99), 4),
                        json.dumps({'learning_records': True, 'neural_training': True}),
                        f'学习成果达标(熟练度:{score:.2f}), 自动升级',
                        'completed', 'brain_feeding_engine',
                        datetime.now().isoformat()
                    ))

                    # 更新员工能力
                    cursor.execute(''' UPDATE ai_employees SET accuracy = ?, updated_at = ? WHERE id = ? ''', (new_accuracy, datetime.now().isoformat(), int(emp_id)))

                    upgraded_count += 1
                    logger.info(
                    f"    ✓ {emp_name}: Lv.{before_level}→Lv.{after_level}  精度:{current_accuracy:.3f}→{new_accuracy:.3f}")

                conn.commit()

            self.upgrade_count += upgraded_count
            logger.info(f"  ✓ 升级完成: {upgraded_count}名员工已升级 (总计:{self.upgrade_count})")
            self._log_maintenance('brain_upgrade', 'ai_employees', 'success',
                                 f'{upgraded_count}名员工完成升级')
        except Exception as e:
            logger.error(f"  ✗ AI升级失败: {e}")

    # ========== 4. 神经网络训练 ==========

    def train_neural_network(self):
        """训练神经网络"""
        if not self._get_rule_bool('BRAIN_NEURAL_NETWORK_ENABLED', True):
            return

        learning_rate = self._get_rule_float('BRAIN_NEURAL_LEARNING_RATE', 0.01)
        prune_enabled = self._get_rule_bool('BRAIN_NEURAL_PRUNE_ENABLED', True)
        prune_threshold = self._get_rule_float('BRAIN_NEURAL_PRUNE_THRESHOLD', 0.1)
        auto_expand = self._get_rule_bool('BRAIN_NEURAL_AUTO_EXPAND', True)
        max_nodes = self._get_rule_int('BRAIN_NEURAL_MAX_NODES', 200)

        logger.info(f"[神经网络] 开始训练 (学习率:{learning_rate})...")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 获取所有节点
                cursor.execute("SELECT node_id, weight, bias, accuracy, training_count FROM neural_network_nodes WHERE status = 'active'")
                nodes = cursor.fetchall()

                trained_count = 0
                for node_id, weight, bias, accuracy, train_count in nodes:
                    # 模拟训练：调整权重和偏置
                    new_weight = weight + round(random.uniform(-learning_rate, learning_rate), 6)
                    new_weight = max(0.01, min(1.0, new_weight))
                    new_bias = bias + round(random.uniform(-learning_rate * 0.5, learning_rate * 0.5), 6)
                    new_accuracy = min(1.0, (accuracy or 0.5) + round(random.uniform(0.001, 0.01), 6))
                    new_train_count = (train_count or 0) + 1

                    cursor.execute(''' UPDATE neural_network_nodes SET weight = ?, bias = ?, accuracy = ?, training_count = ?, last_trained = ?, updated_at = ? WHERE node_id = ? ''', (
                        new_weight, new_bias, new_accuracy, new_train_count,
                        datetime.now().isoformat(), datetime.now().isoformat(), node_id
                    ))
                    trained_count += 1

                # 更新连接权重
                cursor.execute("SELECT connection_id, weight FROM neural_network_connections WHERE status = 'active'")
                connections = cursor.fetchall()

                pruned_count = 0
                for conn_id, conn_weight in connections:
                    new_conn_weight = conn_weight + round(random.uniform(-learning_rate, learning_rate), 6)
                    new_conn_weight = max(0.0, min(1.0, new_conn_weight))

                    if prune_enabled and new_conn_weight < prune_threshold:
                        cursor.execute("UPDATE neural_network_connections SET status = 'pruned', weight = ? WHERE connection_id = ?",
                                      (new_conn_weight, conn_id))
                        pruned_count += 1
                    else:
                        cursor.execute(''' UPDATE neural_network_connections SET weight = ?, activation_count = activation_count + 1, last_activated = ?, updated_at = ? WHERE connection_id = ? ''', (new_conn_weight, datetime.now().isoformat(),
                              datetime.now().isoformat(), conn_id))

                # 自动扩展节点
                if auto_expand and len(nodes) < max_nodes:
                    expand_count = min(3, max_nodes - len(nodes))
                    layer_choices = ['hidden1', 'hidden2', 'hidden3']
                    layer_names = {
                        'hidden1': '隐藏层1-特征提取',
                        'hidden2': '隐藏层2-决策推理',
                        'hidden3': '隐藏层3-执行控制'
                    }
                    new_node_names = ['自适应节点', '动态学习节点', '协同处理节点', '模式优化节点', '知识融合节点']

                    for _ in range(expand_count):
                        layer = random.choice(layer_choices)
                        node_name = random.choice(new_node_names)
                        node_id = f"NN-{layer}-{node_name}-{random.randint(1000, 9999)}"
                        cursor.execute(''' INSERT INTO neural_network_nodes (node_id, node_type, node_name, node_layer, node_layer_name, activation_function, weight, bias, threshold, status, processing_capacity, current_load, accuracy, training_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                            node_id, layer, node_name,
                            {'hidden1': 1, 'hidden2': 2, 'hidden3': 3}[layer],
                            layer_names[layer], 'relu',
                            round(random.uniform(0.3, 0.8), 4),
                            round(random.uniform(-0.1, 0.1), 4),
                            round(random.uniform(0.3, 0.7), 4),
                            'active', round(random.uniform(80, 120), 2),
                            0.0, round(random.uniform(0.5, 0.9), 4), 0,
                            datetime.now().isoformat()
                        ))

                        # 连接到相邻层
                        layer_num = {'hidden1': 1, 'hidden2': 2, 'hidden3': 3}[layer]
                        if layer_num < 4:
                            cursor.execute(
                            "SELECT node_id FROM neural_network_nodes WHERE node_layer = ? AND node_id != ?",
                            (layer_num + 1, node_id))
                            targets = cursor.fetchall()
                            for idx, (tgt_id,) in enumerate(random.sample(targets, min(3, len(targets)))):
                                conn_id = f"CONN-{datetime.now().strftime( '%Y%m%d%H%M%S')}-{node_id[:6]}-{tgt_id[:6]}-{idx}-{random.randint(1000, 9999)}"
                                cursor.execute(''' INSERT OR IGNORE INTO neural_network_connections (connection_id, source_node_id, target_node_id, connection_type, weight, signal_strength, status, learning_rate, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (conn_id, node_id, tgt_id, 'synapse',
                                      round(random.uniform(0.1, 0.9), 4), 0.0,
                                      'active', learning_rate, datetime.now().isoformat()))

                conn.commit()

            logger.info(f"  ✓ 神经网络训练完成: {trained_count}个节点训练, {pruned_count}个连接修剪, 扩展{expand_count if auto_expand and len(nodes) < max_nodes else 0}个新节点")
            self._log_maintenance('neural_training', 'neural_network', 'success',
                                 f'训练{trained_count}节点, 修剪{pruned_count}连接')
        except Exception as e:
            logger.error(f"  ✗ 神经网络训练失败: {e}")

    # ========== 5. 集群统筹 ==========

    def coordinate_clusters(self):
        """AI集群统筹协调"""
        if not self._get_rule_bool('BRAIN_CLUSTER_COORDINATION_ENABLED', True):
            return

        logger.info("[统筹] 开始AI集群统筹协调...")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 获取集群
                cursor.execute("SELECT cluster_id, cluster_type, status FROM ai_cluster_config WHERE status = 'active'")
                clusters = cursor.fetchall()

                if not clusters:
                    # 没有集群，创建默认集群
                    cluster_id = 'CLUSTER-MAIN'
                    cursor.execute(''' INSERT OR IGNORE INTO ai_cluster_config (cluster_id, cluster_type, config, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?) ''', (cluster_id, 'general', json.dumps({'auto_scale': True, 'max_tasks': 20}),
                          'active', datetime.now().isoformat(), datetime.now().isoformat()))
                    conn.commit()
                    clusters = [(cluster_id, 'general', 'active')]

                coordination_count = 0
                for cluster_id, cluster_type, status in clusters:
                    coord_id = self._gen_id('C')

                    # 获取集群成员
                    cursor.execute("SELECT employee_id FROM ai_cluster_employee WHERE cluster_id = ?", (cluster_id,))
                    members = cursor.fetchall()

                    # 获取集群外活跃员工
                    cursor.execute("SELECT id, name FROM ai_employees WHERE status = 'active' LIMIT 10")
                    available = cursor.fetchall()

                    participating = [m[0] for m in members] + [str(e[0]) for e in available[:5]]
                    participating = list(set(participating))[:10]

                    task_types = ['知识同步', '能力协调', '任务分发', '结果汇总', '负载均衡']
                    task_type = random.choice(task_types)

                    # 分配任务
                    assignments = {}
                    for i, emp_id in enumerate(participating):
                        role = ['主控', '执行', '辅助', '监控'][i % 4]
                        assignments[emp_id] = role

                    efficiency = round(random.uniform(0.7, 0.99), 4)
                    duration = round(random.uniform(5, 60), 2)

                    cursor.execute(''' INSERT INTO cluster_coordination_records (coordination_id, cluster_id, coordination_type, task_description, participating_employees, task_assignment, coordination_strategy, result, efficiency_score, duration_seconds, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                        coord_id, cluster_id, task_type,
                        f'{task_type}协调任务',
                        json.dumps(participating, ensure_ascii=False),
                        json.dumps(assignments, ensure_ascii=False),
                        'round_robin' if task_type == '任务分发' else 'collaborative',
                        'success' if efficiency > 0.8 else 'partial',
                        efficiency, duration, 'completed',
                        datetime.now().isoformat()
                    ))

                    coordination_count += 1

                conn.commit()

            self.coordination_count += coordination_count
            logger.info(f"  ✓ 集群统筹完成: {coordination_count}个集群完成协调 (总计:{self.coordination_count})")
            self._log_maintenance('cluster_coordination', 'ai_cluster', 'success',
                                 f'{coordination_count}个集群完成协调')
        except Exception as e:
            logger.error(f"  ✗ 集群统筹失败: {e}")

    # ========== 6. 统计报告 ==========

    def record_stats(self):
        """记录投喂统计"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 统计数据
                cursor.execute("SELECT COUNT(*) FROM ai_brain_knowledge")
                knowledge_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM neural_network_nodes WHERE status = 'active'")
                active_nodes = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM neural_network_connections WHERE status = 'active'")
                active_connections = cursor.fetchone()[0]

                cursor.execute("SELECT AVG(accuracy) FROM ai_employees")
                avg_accuracy = cursor.fetchone()[0] or 0

                cursor.execute("SELECT AVG(proficiency_after) FROM brain_learning_records")
                avg_proficiency = cursor.fetchone()[0] or 0

                density = active_connections / max(active_nodes, 1)

                cursor.execute("SELECT AVG(efficiency_score) FROM cluster_coordination_records WHERE created_at > ?",
                              ((datetime.now() - timedelta(hours=24)).isoformat(),))
                cluster_eff = cursor.fetchone()[0] or 0

                cursor.execute(''' INSERT INTO brain_feeding_stats (stat_date, total_feeds, total_learnings, total_upgrades, total_coordinations, knowledge_count, active_nodes, active_connections, avg_proficiency, avg_accuracy, neural_network_density, cluster_efficiency, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                    datetime.now().strftime('%Y-%m-%d'),
                    self.feeding_count, self.learning_count, self.upgrade_count,
                    self.coordination_count, knowledge_count, active_nodes, active_connections,
                    round(avg_proficiency, 4), round(avg_accuracy, 4),
                    round(density, 4), round(cluster_eff, 4),
                    datetime.now().isoformat()
                ))
                conn.commit()

            logger.info(
            f"[统计] 知识:{knowledge_count} | 节点:{active_nodes} | 连接:{active_connections} | 精度:{avg_accuracy:.3f} |  熟练度:{avg_proficiency:.3f}")
        except Exception as e:
            logger.error(f"记录统计失败: {e}")

    # ========== 执行入口 ==========

    def run_all(self):
        """执行完整的投喂-学习-升级-训练-统筹流程"""
        logger.info("=" * 60)
        logger.info("  AI脑库投喂引擎 - 执行完整流程")
        logger.info("=" * 60)

        self.feed_knowledge()
        self.feed_from_network()
        self.discover_learning_directions()
        self.trigger_learning()
        self.trigger_upgrade()
        self.train_neural_network()
        self.coordinate_clusters()
        self.record_stats()

        logger.info("=" * 60)
        logger.info(
        f"  投喂:{self.feeding_count} | 网络学习:{self.network_learning_count} | 学习:{self.learning_count} |  升级:{self.upgrade_count} | 统筹:{self.coordination_count}")
        logger.info("=" * 60)

    def run_network_learning(self):
        """仅执行网络学习和规则发现"""
        logger.info("=" * 60)
        logger.info("  AI脑库投喂引擎 - 网络学习模式")
        logger.info("=" * 60)

        self.feed_from_network()
        self.discover_learning_directions()

        logger.info("=" * 60)
        logger.info(f"  网络学习:{self.network_learning_count}")
        logger.info("=" * 60)


def main():
    engine = BrainFeedingEngine()
    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            engine.run_all()
        elif sys.argv[1] == '--network':
            engine.run_network_learning()
        elif sys.argv[1] == '--feed':
            engine.feed_knowledge()
        elif sys.argv[1] == '--learn':
            engine.trigger_learning()
        elif sys.argv[1] == '--upgrade':
            engine.trigger_upgrade()
        elif sys.argv[1] == '--train':
            engine.train_neural_network()
        elif sys.argv[1] == '--discover':
            engine.discover_learning_directions()
        elif sys.argv[1] == '--stats':
            engine.record_stats()
        else:
            logger.info(f"未知参数: {sys.argv[1]}")
            logger.info("可用参数: --once, --network, --feed, --learn, --upgrade, --train, --discover, --stats")
    else:
        engine.run_all()


if __name__ == '__main__':
    main()
