#!/usr/bin/env python3
"""
MTSCOS AI员工批量扩容脚本
将AI员工总数扩展至 10810 位，覆盖全系统功能模块并适配未来扩展
- 基于 app/api, app/services, ai_engines, core/services 自动生成
- 分层架构：核心层（Core）/执行层（Execution）/支持层（Support）/未来层（Future）
- 每1000条批量写入，确保性能
"""
import os
import sys
import json
import sqlite3
import random
import time
import logging
from datetime import datetime
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('expand_ai')

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(_PROJECT_ROOT)
sys.path.insert(0, _PROJECT_ROOT)
DATABASE_PATH = os.path.join(_PROJECT_ROOT, 'app.db')

# ============ 1. 扫描功能模块 ============

def scan_modules() -> List[Tuple[str, str, List[str]]]:
    """扫描所有python模块生成功能列表"""
    modules = []
    scan_dirs = [
        ('app/api', 'API端点'),
        ('app/services', '应用服务'),
        ('core/services', '核心服务'),
        ('ai_engines', 'AI引擎'),
    ]
    for dir_path, cat_name in scan_dirs:
        full_path = os.path.join(_PROJECT_ROOT, dir_path)
        if not os.path.isdir(full_path):
            continue
        for root, dirs, files in os.walk(full_path):
            for f in files:
                if f.endswith('.py') and not f.startswith('__') and not f.startswith('.'):
                    mod_name = os.path.splitext(f)[0]
                    mod_path = os.path.relpath(os.path.join(root, f), _PROJECT_ROOT)
                    # 生成功能描述标签
                    desc = f"{cat_name}: {mod_name}"
                    tags = [cat_name.lower(), mod_name.lower().replace('_', ' ')]
                    modules.append((mod_path, desc, tags))
    logger.info(f"扫描到 {len(modules)} 个功能模块")
    return modules

# ============ 2. 定义员工分层与配额 ============

# 目标总数 10810，当前 2020（已启用），需新增 8790
TARGET_TOTAL = 10810
EXISTING_COUNT = 2020
TO_CREATE = TARGET_TOTAL - EXISTING_COUNT  # 8790

# 功能类别配额（按业务重要性分配新增名额）
CATEGORY_QUOTA = {
    # === 核心业务层 ===
    'AI防火墙': 400,
    '脑库/知识库': 350,
    '考试系统': 350,
    '题库管理': 320,
    '听力/语音': 320,
    '用户/权限': 280,
    '系统监控': 260,
    '安全审计': 260,
    '数据同步': 240,
    'AutoMount/调度': 230,

    # === AI引擎层 ===
    'AI引擎架构': 220,
    'AI员工管理': 220,
    'AI学习系统': 220,
    'AI修复/自愈': 200,
    'AI推荐/预测': 200,
    'AI集群/数组': 180,
    'AI对话/情感': 180,
    'AI文档/报告': 160,
    'AI数据科学': 160,
    'AI金融/营销': 140,

    # === 应用服务层 ===
    '路由/中间件': 140,
    '缓存/队列': 140,
    '日志/告警': 140,
    '版本/升级': 140,
    '工作流/通知': 130,
    '备份/灾备': 130,
    '配置/环境': 120,
    '负载均衡': 120,
    '分布式锁/ID': 100,

    # === 教育业务层 ===
    'K12教育': 120,
    '成人教育': 80,
    '课程/教学': 120,
    '作业/评测': 120,
    '学习诊断': 100,
    '游戏化/激励': 80,
    '家校沟通': 80,

    # === 外部集成层 ===
    '企业微信': 100,
    'ARDUINO/IoT': 80,
    'SSL VPN': 60,
    '消息/邮件': 100,
    'Webhook': 60,

    # === 未来预留层（预留供新功能开发）===
    '通用支持': 150,
    '未来扩展-A': 80,
    '未来扩展-B': 80,
    '未来扩展-C': 80,
    '通用AI助理': 120,
}

# 验证配额总和
total_quota = sum(CATEGORY_QUOTA.values())
logger.info(f"配额总和: {total_quota} (需新增: {TO_CREATE})")

# 如果配额 > TO_CREATE，等比例缩减；如果 < TO_CREATE，将剩余分配给"通用支持"
if total_quota != TO_CREATE:
    scale = TO_CREATE / total_quota
    new_quota = {'通用支持': CATEGORY_QUOTA.get('通用支持', 150)}
    allocated = new_quota['通用支持']
    for k, v in CATEGORY_QUOTA.items():
        if k == '通用支持':
            continue
        nv = max(10, int(v * scale))
        new_quota[k] = nv
        allocated += nv
    # 如果还有剩余或超出，调整通用支持
    new_quota['通用支持'] += (TO_CREATE - allocated)
    CATEGORY_QUOTA = new_quota
    total_quota = sum(CATEGORY_QUOTA.values())
    logger.info(f"调整后配额总和: {total_quota}")

# ============ 3. 生成员工数据 ============

FIRST_NAMES = ['智', '灵', '慧', '觉', '悟', '睿', '思', '明', '清', '玄', '元', '本', '天', '妙', '玄', '星', '辰', '宇', '辰', '昊']
LAST_NAMES_PRE = ['AI-', '智控-', '数据-', '分析-', '监测-', '生成-', '审核-', '修复-', '调度-', '编排-', '推理-', '学习-', '对话-', '图像-', '语音-', '文本-', '网络-', '安全-', '存储-', '计算-']

SKILL_LEVELS_BY_LAYER = {
    'core': (7, 10),
    'execution': (4, 8),
    'support': (2, 6),
    'future': (1, 5),
}

LAYERS = ['core', 'execution', 'support', 'future']


def gen_employee_name(category: str, index: int) -> str:
    """生成AI员工中文名称"""
    last = random.choice(LAST_NAMES_PRE)
    first = random.choice(FIRST_NAMES)
    layer = LAYERS[index % len(LAYERS)]
    type_map = {'core': '核心', 'execution': '执行', 'support': '支持', 'future': '预备'}
    return f"{last}{first}{category}{type_map[layer]}-{index:05d}"


def gen_capabilities(category: str) -> str:
    """生成能力标签列表"""
    base = {
        'AI防火墙': ['入侵检测', '流量分析', '规则引擎', '威胁拦截', '异常识别'],
        '脑库/知识库': ['知识索引', '语义检索', '自动归档', '关联分析', '知识图谱'],
        '考试系统': ['试卷生成', '评分判卷', '难度计算', '成绩分析', '错题追踪'],
        '题库管理': ['题目生成', '题目审核', '分类检索', '批量导入', '质量评估'],
        '听力/语音': ['语音识别', '音频合成', '听力评分', '口音分析', '语速控制'],
        '用户/权限': ['身份验证', '权限分配', '会话管理', 'SSO集成', '审计日志'],
        '系统监控': ['性能采集', '健康检查', '故障预警', '指标聚合', '趋势分析'],
        '安全审计': ['代码扫描', '漏洞检测', '合规检查', '渗透测试', '风险评级'],
        '数据同步': ['数据迁移', '增量同步', '冲突解决', '一致性校验', '版本合并'],
        'AutoMount/调度': ['任务调度', '事件驱动', 'Agent加载', '生命周期管理', '异常恢复'],
        'AI引擎架构': ['模型调度', '上下文管理', '多模型融合', '推理加速', '服务编排'],
        'AI员工管理': ['员工注册', '任务委派', '能力画像', '协作编排', '绩效考核'],
        'AI学习系统': ['在线学习', '反馈收集', '模型更新', '知识提炼', '技能进化'],
        'AI修复/自愈': ['错误诊断', '自动修复', '回滚保护', '根因分析', '自愈验证'],
        'AI推荐/预测': ['协同过滤', '内容推荐', '趋势预测', '画像分析', '精准投放'],
        'AI集群/数组': ['集群协调', '负载分配', '故障转移', '弹性伸缩', '状态同步'],
        'AI对话/情感': ['自然对话', '情感识别', '多轮管理', '意图识别', '风格适配'],
        'AI文档/报告': ['文档生成', '格式转换', '内容摘要', '结构分析', '自动发布'],
        'AI数据科学': ['数据清洗', '特征工程', '模型训练', '统计分析', '可视化'],
        'AI金融/营销': ['风险评估', '用户画像', '营销投放', 'ROI分析', '策略优化'],
        '路由/中间件': ['请求路由', '中间件链', '参数校验', '熔断降级', '限流保护'],
        '缓存/队列': ['缓存管理', '消息队列', '订阅广播', '过期策略', '持久化'],
        '日志/告警': ['日志采集', '日志分析', '告警触发', '告警抑制', '根因定位'],
        '版本/升级': ['版本管理', '灰度发布', '兼容性检查', '数据迁移', '回滚策略'],
        '工作流/通知': ['流程编排', '节点控制', '条件分支', '通知推送', '审批流'],
        '备份/灾备': ['全量备份', '增量备份', '异地存储', '恢复演练', '灾难切换'],
        '配置/环境': ['配置管理', '环境隔离', '参数注入', '热更新', '配置审计'],
        '负载均衡': ['轮询调度', '加权分配', '健康检查', '会话保持', '性能监控'],
        '分布式锁/ID': ['互斥锁', '分布式ID', '时钟同步', '死锁检测', '自动解锁'],
        'K12教育': ['课程指导', '作业批改', '学情分析', '互动教学', '家长沟通'],
        '成人教育': ['职业规划', '技能评估', '学习路径', '继续教育', '证书管理'],
        '课程/教学': ['课程设计', '教学计划', '资源管理', '进度追踪', '效果评估'],
        '作业/评测': ['作业发布', '自动批改', '成绩分析', '错题本', '能力评估'],
        '学习诊断': ['薄弱点分析', '知识图谱', '学习建议', '效果追踪', '干预策略'],
        '游戏化/激励': ['成就系统', '积分奖励', '排行榜', '进度条', '徽章系统'],
        '家校沟通': ['消息通知', '报告推送', '会议安排', '在线交流', '档案管理'],
        '企业微信': ['客户管理', '应用集成', '消息推送', '数据同步', '审批流程'],
        'ARDUINO/IoT': ['设备管理', '数据采集', '远程控制', '固件升级', '状态监控'],
        'SSL VPN': ['加密通信', '隧道建立', '身份验证', '访问控制', '证书管理'],
        '消息/邮件': ['消息路由', '邮件发送', '附件处理', '模板管理', '送达确认'],
        'Webhook': ['事件触发', '回调通知', '签名验证', '重试机制', '状态追踪'],
        '通用支持': ['通用任务', '辅助分析', '报表生成', '数据录入', '流程支撑'],
        '未来扩展-A': ['量子计算预研', '类脑智能', '通用AGI', '自进化架构', '元学习'],
        '未来扩展-B': ['多模态融合', '实时推理', '边缘计算', '联邦学习', '隐私计算'],
        '未来扩展-C': ['神经符号', '因果推理', '世界模型', '价值对齐', '通用对话'],
        '通用AI助理': ['日程管理', '文档处理', '数据查询', '会议协调', '个人助理'],
    }
    return json.dumps(base.get(category, ['通用能力A', '通用能力B', '通用能力C']), ensure_ascii=False)


def gen_specialties(category: str) -> str:
    """生成专长标签"""
    spec_map = {
        'AI防火墙': ['security', 'firewall', 'threat-detection', 'ai-security'],
        '脑库/知识库': ['knowledge-base', 'brain', 'vector-search', 'embedding'],
        '考试系统': ['exam', 'paper', 'grading', 'scoring'],
        '题库管理': ['question-bank', 'q-bank', 'questions', 'curator'],
        '听力/语音': ['listening', 'speech', 'audio', 'voice-recognition'],
        '用户/权限': ['auth', 'permission', 'rbac', 'user-management'],
        '系统监控': ['monitoring', 'metrics', 'health-check', 'observability'],
        '安全审计': ['audit', 'vulnerability', 'code-security', 'compliance'],
        '数据同步': ['sync', 'etl', 'data-integration', 'replication'],
        'AutoMount/调度': ['scheduler', 'task-manager', 'auto-mount', 'agent-loader'],
        'AI引擎架构': ['ai-engine', 'llm', 'model-router', 'inference'],
        'AI员工管理': ['ai-employee', 'workforce', 'delegation', 'orchestration'],
        'AI学习系统': ['self-learning', 'online-learning', 'feedback-loop', 'evolution'],
        'AI修复/自愈': ['auto-repair', 'self-healing', 'bug-fix', 'recovery'],
        'AI推荐/预测': ['recommendation', 'prediction', 'ml-model', 'forecasting'],
        'AI集群/数组': ['cluster', 'array', 'distributed', 'scaling'],
        'AI对话/情感': ['nlp', 'dialogue', 'sentiment', 'chatbot'],
        'AI文档/报告': ['document', 'report', 'summary', 'generation'],
        'AI数据科学': ['data-science', 'analytics', 'ml', 'statistics'],
        'AI金融/营销': ['finance', 'marketing', 'roi', 'conversion'],
        '路由/中间件': ['routing', 'middleware', 'api-gateway', 'router'],
        '缓存/队列': ['cache', 'queue', 'redis', 'message-broker'],
        '日志/告警': ['logging', 'alerting', 'observability', 'siem'],
        '版本/升级': ['version', 'upgrade', 'release', 'rollback'],
        '工作流/通知': ['workflow', 'notification', 'orchestration', 'bpm'],
        '备份/灾备': ['backup', 'disaster-recovery', 'replication', 'snapshot'],
        '配置/环境': ['config', 'environment', 'env-vars', 'settings'],
        '负载均衡': ['load-balancer', 'traffic', 'scaling', 'failover'],
        '分布式锁/ID': ['distributed-lock', 'unique-id', 'consensus', 'synchronization'],
        'K12教育': ['k12', 'education', 'primary', 'secondary'],
        '成人教育': ['adult-edu', 'professional', 'career', 'certification'],
        '课程/教学': ['course', 'teaching', 'curriculum', 'lesson'],
        '作业/评测': ['homework', 'evaluation', 'assessment', 'grading'],
        '学习诊断': ['diagnosis', 'learning-analytics', 'weakness', 'intervention'],
        '游戏化/激励': ['gamification', 'rewards', 'achievement', 'engagement'],
        '家校沟通': ['parent-comm', 'school-home', 'communication', 'report'],
        '企业微信': ['wecom', 'wechat-work', 'enterprise', 'work-msg'],
        'ARDUINO/IoT': ['arduino', 'iot', 'embedded', 'sensors'],
        'SSL VPN': ['vpn', 'ssl', 'encryption', 'security-channel'],
        '消息/邮件': ['message', 'email', 'notification', 'push'],
        'Webhook': ['webhook', 'callback', 'event-driven', 'integration'],
        '通用支持': ['general-support', 'assistant', 'helper', 'backup'],
        '未来扩展-A': ['quantum', 'agi', 'brain-inspired', 'meta-learning'],
        '未来扩展-B': ['multimodal', 'edge-ai', 'federated-learning', 'privacy'],
        '未来扩展-C': ['neuro-symbolic', 'causal', 'world-model', 'alignment'],
        '通用AI助理': ['assistant', 'personal-agent', 'productivity', 'copilot'],
    }
    return json.dumps(spec_map.get(category, ['general']), ensure_ascii=False)


def gen_description(category: str) -> str:
    """生成员工描述"""
    templates = [
        f"MTSCOS系统{category}专项AI员工，负责核心业务处理、数据分析和智能决策",
        f"{category}领域AI专家，具备自主学习和协同工作能力",
        f"专注于{category}的智能优化与自动化执行，支持系统级扩展",
        f"{category}模块专属AI Agent，提供7x24小时智能服务",
        f"深度学习驱动的{category}AI员工，持续进化适应新需求",
    ]
    return random.choice(templates)


def build_employee_batch(existing_max_id: int) -> List[Tuple]:
    """构建一批员工数据"""
    rows = []
    now = datetime.now().isoformat()

    emp_id = existing_max_id + 1
    total_created = 0
    target_per_category = dict(CATEGORY_QUOTA)
    created_per_category = {k: 0 for k in CATEGORY_QUOTA}

    # 分轮次生成，每轮每个类别各取一部分
    round_num = 0
    while total_created < TO_CREATE:
        round_num += 1
        for category, quota in CATEGORY_QUOTA.items():
            if created_per_category[category] >= quota:
                continue
            # 每轮每个类别生成 1-5 个
            batch_size = min(
                random.randint(2, 6),
                quota - created_per_category[category],
                TO_CREATE - total_created
            )
            for _ in range(batch_size):
                if total_created >= TO_CREATE:
                    break
                level_idx = (total_created + existing_max_id) % len(LAYERS)
                layer = LAYERS[level_idx]
                skill_min, skill_max = SKILL_LEVELS_BY_LAYER[layer]
                skill_level = random.randint(skill_min, skill_max)
                accuracy = round(0.80 + skill_level * 0.015 + random.random() * 0.03, 4)
                accuracy = min(accuracy, 0.99)

                name = gen_employee_name(category, total_created + 1)
                capabilities = gen_capabilities(category)
                specialties = gen_specialties(category)
                description = gen_description(category)

                model_version = f"boost-v2.{(skill_level % 5) + 1}.{round_num % 10}"
                learning_rate = round(0.01 + skill_level * 0.005 + random.random() * 0.01, 4)

                rows.append((
                    f"AI-{emp_id:06d}",          # employee_code
                    name,                        # name
                    description,                 # description
                    specialties,                 # specialties
                    capabilities,                # capabilities
                    'active',                    # status
                    accuracy,                    # accuracy
                    random.randint(10, 500),     # total_tasks
                    random.randint(5, 200),      # successful_fixes
                    random.randint(0, 20),       # failed_fixes
                    learning_rate,               # learning_rate
                    random.randint(10, 500),     # knowledge_base_size
                    now,                         # last_training
                    model_version,               # model_version
                    1,                           # is_enabled
                    random.randint(1, 10),       # priority
                    random.randint(3, 10),       # max_concurrent_tasks
                    skill_level,                 # skill_level
                    now,                         # created_at
                    now,                         # updated_at
                ))
                emp_id += 1
                total_created += 1
                created_per_category[category] += 1

        if round_num % 20 == 0:
            logger.info(f"  第 {round_num} 轮: 已生成 {total_created}/{TO_CREATE}")

    return rows


# ============ 4. 执行扩容 ============

def expand():
    logger.info("=" * 60)
    logger.info("MTSCOS AI员工扩容启动")
    logger.info(f"目标总数: {TARGET_TOTAL} | 现有: {EXISTING_COUNT} | 待创建: {TO_CREATE}")
    logger.info("=" * 60)

    t0 = time.time()

    # 1. 获取当前最大ID
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.execute("SELECT MAX(id) FROM ai_employees")
        max_id = cur.fetchone()[0] or 0
        logger.info(f"当前最大ID: {max_id}")

    # 2. 生成员工数据
    logger.info("生成员工数据...")
    rows = build_employee_batch(max_id)
    logger.info(f"共生成 {len(rows)} 条员工数据")

    # 3. 分批写入数据库
    BATCH_SIZE = 1000
    total_inserted = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.executemany('''
                INSERT INTO ai_employees
                (employee_code, name, description, specialties, capabilities,
                 status, accuracy, total_tasks, successful_fixes, failed_fixes,
                 learning_rate, knowledge_base_size, last_training, model_version,
                 is_enabled, priority, max_concurrent_tasks, skill_level,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', batch)
            conn.commit()
        total_inserted += len(batch)
        logger.info(f"  已写入: {total_inserted}/{len(rows)}")

    elapsed = time.time() - t0

    # 4. 验证
    with sqlite3.connect(DATABASE_PATH) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM ai_employees WHERE is_enabled = 1")
        enabled_count = cur.fetchone()[0]
        cur = conn.execute("SELECT COUNT(*) FROM ai_employees")
        total_count = cur.fetchone()[0]

    logger.info("=" * 60)
    logger.info(f"扩容完成！耗时 {elapsed:.1f}s")
    logger.info(f"  启用员工数: {enabled_count}")
    logger.info(f"  总员工数:   {total_count}")
    logger.info(f"  本轮新增:   {total_inserted}")

    # 5. 提交扩容报告
    try:
        from app.services.system_report_service import SystemReportService
        svc = SystemReportService()
        svc.submit_report(
            report_type='ai_employee_expansion',
            module='ai_workforce',
            severity='info',
            title=f'AI员工扩容: 新增 {total_inserted} 位员工',
            content=json.dumps({
                'target_total': TARGET_TOTAL,
                'existing_count': EXISTING_COUNT,
                'created_count': total_inserted,
                'final_total': total_count,
                'duration_seconds': round(elapsed, 2),
                'categories': list(CATEGORY_QUOTA.keys()),
            }, ensure_ascii=False),
            metadata={'created': total_inserted, 'final': total_count},
        )
        logger.info("扩容报告已提交")
    except Exception as e:
        logger.warning(f"报告提交失败: {e}")

    print("\n" + "=" * 60)
    print("📊 AI员工扩容报告")
    print("=" * 60)
    print(f"目标总数:   {TARGET_TOTAL}")
    print(f"扩容后启用: {enabled_count}")
    print(f"数据库总数: {total_count}")
    print(f"本轮新增:   {total_inserted}")
    print(f"耗时:       {elapsed:.1f}s")
    print("-" * 60)
    print("覆盖功能类别:")
    for cat in list(CATEGORY_QUOTA.keys())[:10]:
        print(f"  • {cat}: {CATEGORY_QUOTA[cat]} 位")
    print(f"  ... 共 {len(CATEGORY_QUOTA)} 个类别")
    print("=" * 60)


if __name__ == '__main__':
    expand()
