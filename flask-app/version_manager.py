#!/usr/bin/env python3
"""
MTSCOS 版本管理器

## 3级版本号规则 (Semantic Versioning)
    版本号格式: MAJOR.MINOR.PATCH (如 14.1.0)

### 递增规则:
    - MAJOR (主版本号): 不兼容的API变更或重大架构重构时递增 (预计每年0-1次)
    - MINOR (次版本号): 新增功能且向下兼容时递增 (每月最多1次)
    - PATCH (修订号):   Bug修复或小优化时递增 (可多次)

### 版本范围约束:
    - MAJOR: 1-99
    - MINOR: 0-99
    - PATCH: 0-999

### 注意事项:
    - 新增服务模块属于 MINOR 级别变更,不应递增 MAJOR
    - 仅当现有API发生破坏性变更时才递增 MAJOR
    - PATCH 级别不得包含新功能,仅用于修复
"""

import os
import json
import time
import sqlite3
import re
from datetime import datetime
from db_manager import connect

# 版本号格式正则
VERSION_PATTERN = re.compile(r'^(\d{1,2})\.(\d{1,2})\.(\d{1,3})$')

# 版本号范围约束
MAJOR_MAX = 99
MINOR_MAX = 99
PATCH_MAX = 999


def validate_version(version: str) -> bool:
    """验证版本号格式是否符合3级规范"""
    match = VERSION_PATTERN.match(version)
    if not match:
        return False
    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if major < 0 or major > MAJOR_MAX:
        return False
    if minor < 0 or minor > MINOR_MAX:
        return False
    if patch < 0 or patch > PATCH_MAX:
        return False
    return True


def parse_version(version: str) -> tuple:
    """解析版本号为 (major, minor, patch) 元组"""
    match = VERSION_PATTERN.match(version)
    if not match:
        return (0, 0, 0)
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def compare_versions(v1: str, v2: str) -> int:
    """比较两个版本号, 返回 1(v1>v2), -1(v1<v2), 0(相等)"""
    a = parse_version(v1)
    b = parse_version(v2)
    if a > b:
        return 1
    elif a < b:
        return -1
    return 0


def next_patch_version(version: str) -> str:
    """获取下一个PATCH版本号"""
    major, minor, patch = parse_version(version)
    patch = min(patch + 1, PATCH_MAX)
    return f"{major}.{minor}.{patch}"


def next_minor_version(version: str) -> str:
    """获取下一个MINOR版本号"""
    major, minor, _ = parse_version(version)
    minor = min(minor + 1, MINOR_MAX)
    return f"{major}.{minor}.0"


def next_major_version(version: str) -> str:
    """获取下一个MAJOR版本号"""
    major, _, _ = parse_version(version)
    major = min(major + 1, MAJOR_MAX)
    return f"{major}.0.0"


def suggest_version(current_version: str, change_type: str = 'patch') -> str:
    """
    根据变更类型建议下一个版本号

    Args:
        current_version: 当前版本号
        change_type: 变更类型 ('patch'|'minor'|'major')

    Returns:
        建议的下一个版本号
    """
    if not validate_version(current_version):
        return "1.0.0"

    if change_type == 'major':
        return next_major_version(current_version)
    elif change_type == 'minor':
        return next_minor_version(current_version)
    else:
        return next_patch_version(current_version)

VERSION_DATA = {
    '14.0.0': {
        'major': 14,
        'minor': 0,
        'patch': 0,
        'build_number': '20260718a',
        'build_date': '2026-07-18',
        'codename': 'AI Employee Orchestration & Integration Edition',
        'status': 'stable',
        'description': 'AI员工编排与集成版本，创建AI员工编排层连接专业角色→技能进化→独立思考→网络学习的自动化成长周期，实现14个子系统统一集成与仪表盘监控',
        'features': [
            'AI员工编排层（ai_orchestrator.py）- 连接专业角色→技能进化→独立思考→网络学习的完整成长周期',
            '统一AI仪表盘API（ai_dashboard_api.py）- 聚合14个子系统数据的统一监控端点',
            '成长周期管理（growth_cycles表）- 记录每个AI员工的完整成长周期历程',
            '员工绩效统计（employee_performance表）- 定期统计员工思考次数/学习时长/知识获取/技能提升',
            '批量成长触发 - 支持多员工批量执行成长周期',
            '4个语言听力报读员注册到AI员工管理器（关西腔/关东腔/美式英语/英式英语）',
            '成长监控线程 - 后台定时监控和处理成长周期',
            '仪表盘概览端点（/api/ai/dashboard/overview）- 总览所有AI员工和子系统状态',
            '员工列表端点（/api/ai/dashboard/employees）- 查看所有员工详细信息',
            '员工详情端点（/api/ai/dashboard/employee/{id}）- 查看单个员工完整档案',
            '成长触发端点（/api/ai/dashboard/growth/trigger）- 手动触发成长周期',
            '批量成长端点（/api/ai/dashboard/growth/batch）- 批量触发员工成长',
            '统计端点（/api/ai/dashboard/stats）- 汇总统计数据',
            '角色统计端点（/api/ai/dashboard/roles）- 按角色分组统计',
            '全子系统数据聚合 - 统一展示职业角色/技能进化/自学习/决策支持等子系统状态',
            '数据库锁死锁修复 - 审核并修复嵌套锁模式，确保并发安全',
            '系统扩展性增强 - 标准化编排接口，支持新增AI员工类型快速集成',
            '性能优化 - 异步监控线程，避免阻塞主流程'
        ],
        'upgrade_notes': '从v13.1.0升级：新增AI员工编排层和统一仪表盘API，实现所有AI子系统的集成与监控，支持自动化成长周期和批量管理'
    },
    '13.1.0': {
        'major': 13,
        'minor': 1,
        'patch': 0,
        'build_number': '20260717a',
        'build_date': '2026-07-17',
        'codename': 'AI Professional Role & Personality Edition',
        'status': 'stable',
        'description': 'AI职业角色与性格版本，为每位AI员工赋予职业角色特性和性格，实现独立思考、技能学习统计归纳与升级，自动从网络中自我完善并拓展专业能力',
        'features': [
            'AI职业角色配置系统（10种职业角色：软件工程师/数据科学家/系统架构师/DevOps工程师/AI研究员/数据库管理员/安全专家/质量保证工程师/产品经理/技术文档工程师）',
            'AI性格特质系统（20+性格特质：分析型/创造力/细节导向/逻辑性/好奇心/耐心/战略眼光/果断/协作/主动/坚持不懈/远见/务实/沟通/有条理/同理心/批判性思维/谨慎/有条不紊/行动导向）',
            '独立思考引擎（技能分析/学习计划生成/思考历史记录/自我反思/技能缺口识别/优先级排序）',
            '网络自我学习模块（模拟网页搜索/知识提取/知识库管理/学习历史记录/学习资源推荐）',
            'AI职业角色API（角色分配/独立思考触发/学习计划管理/网络学习触发/知识库查询/技能缺口管理/员工概览）',
            '职业角色配置（工作风格/专业领域/学习偏好/沟通风格/激励因素）',
            '技能学习闭环（分析→规划→执行→反思四阶段独立思考流程）',
            '网络知识获取（支持多种知识来源：GitHub/Stack Overflow/Medium/arXiv/Dev.to/YouTube/在线课程）',
            '知识库管理（按领域分类/置信度评估/访问计数/知识关联）',
            '学习进度跟踪（学习计划进度/技能缺口解决状态/学习时间统计）',
            '员工职业发展摘要（思考次数/学习时长/知识库大小/技能评分/计划进度）',
            '职业角色与性格融合分析（性格优势/劣势/工作风格匹配度/学习偏好适配）',
            '全子系统版本统一升级（30个子系统同步升级至v13.1.0）',
            '系统安全性增强（API权限控制/数据加密/访问审计）',
            '性能优化（数据库索引优化/缓存机制/异步处理）',
            '扩展性增强（标准化接口/灵活集成/插件化架构）'
        ],
        'upgrade_notes': '从v13.0.0升级：新增AI职业角色与性格系统，实现AI员工职业角色配置、独立思考引擎和网络自我学习能力，全面激发AI员工专业发展潜力'
    },
    '13.0.0': {
        'major': 13,
        'minor': 0,
        'patch': 0,
        'build_number': '20260716a',
        'build_date': '2026-07-16',
        'codename': 'AI Intelligent Decision & Prediction Edition',
        'status': 'stable',
        'description': 'AI智能决策与预测版本，实现AI智能决策推理系统、AI学习效果预测系统、AI智能资源推荐系统三大高级智能系统，全面升级决策能力、预测能力和资源推荐能力',
        'features': [
            'AI智能决策推理系统（学习路径决策/资源推荐决策/干预决策/目标设定/技能发展/决策规则管理/决策执行）',
            'AI学习效果预测系统（分数预测/完成度预测/辍学风险预测/技能增长预测/知识掌握度预测/预测验证/准确率评估）',
            'AI智能资源推荐系统（内容推荐/协同过滤/上下文感知/知识推荐/混合推荐/资源管理/交互记录）',
            'AI智能决策API（决策生成/规则管理/任务查询/决策执行/统计摘要）',
            'AI学习预测API（预测执行/任务查询/预测验证/统计摘要/特征提取）',
            'AI资源推荐API（推荐生成/资源管理/交互记录/用户档案/反馈提交/统计摘要）',
            '多维度决策支持（整合认知推理+自适应学习+智能问答三维数据）',
            '预测模型集成（基于学习行为数据的多维度预测分析）',
            '智能推荐策略（内容过滤/协同过滤/上下文感知/知识图谱四种策略）',
            '决策规则引擎（可配置决策规则/优先级排序/自动化执行）',
            '预测验证机制（实际结果验证/准确率计算/模型优化）',
            '资源库管理（多类型资源/难度分级/标签系统/评分机制）',
            '认知-决策-预测-推荐四维智能融合分析',
            '全子系统版本统一升级（29个子系统同步升级至v13.0.0）',
            '系统安全性增强（API权限控制/数据加密/访问审计）',
            '性能优化（数据库索引优化/缓存机制/异步处理）',
            '扩展性增强（标准化接口/灵活集成/插件化架构）'
        ],
        'upgrade_notes': '从v12.0.0升级：新增AI智能决策推理系统、AI学习效果预测系统、AI智能资源推荐系统三大高级智能系统，实现决策-预测-推荐三维智能融合'
    },
    '12.0.0': {
        'major': 12,
        'minor': 0,
        'patch': 0,
        'build_number': '20260715c',
        'build_date': '2026-07-15',
        'codename': 'AI Advanced Cognitive & Adaptive Edition',
        'status': 'stable',
        'description': 'AI高级认知与自适应版本，实现AI认知推理系统、AI自适应学习系统、AI智能问答系统三大核心智能系统，全面升级认知能力和自适应学习体验',
        'features': [
            'AI认知推理系统（演绎推理/归纳推理/溯因推理/类比推理/因果推理/知识库管理/推理任务记录）',
            'AI自适应学习系统（学习风格分析/个性化学习路径/学习进度跟踪/知识缺口检测/学习推荐）',
            'AI智能问答系统（基于知识库问答/Q&A会话管理/对话历史记录/反馈提交/问题分类）',
            'AI认知推理API（推理执行/知识库管理/任务查询/推理历史/统计摘要）',
            'AI自适应学习API（学习档案/学习路径/进度跟踪/知识缺口/学习推荐）',
            'AI智能问答API（问题回答/会话管理/对话历史/反馈提交/统计摘要）',
            '多种推理类型支持（演绎/归纳/溯因/类比/因果五种推理模式）',
            '学习风格识别（视觉型/听觉型/阅读型/动觉型四种学习风格）',
            '个性化学习路径（根据学习风格和知识水平动态生成）',
            '知识缺口检测（基于学习交互数据智能识别薄弱环节）',
            'Q&A会话管理（多轮对话/上下文理解/智能回答）',
            '认知数据深度分析（推理结果+学习行为+问答数据三维融合）',
            '全子系统版本统一升级（26个子系统同步升级至v12.0.0）',
            '系统安全性增强（API权限控制/数据加密/访问审计）',
            '性能优化（数据库索引优化/缓存机制/异步处理）',
            '扩展性增强（标准化接口/灵活集成/插件化架构）'
        ],
        'upgrade_notes': '从v11.0.0升级：新增AI认知推理系统、AI自适应学习系统、AI智能问答系统三大高级智能系统，实现认知-自适应-问答三维智能融合'
    },
    '11.0.0': {
        'major': 11,
        'minor': 0,
        'patch': 0,
        'build_number': '20260715b',
        'build_date': '2026-07-15',
        'codename': 'AI Cognitive Enhancement Edition',
        'status': 'stable',
        'description': 'AI认知增强版本，实现AI记忆管理、AI情感分析、AI智能评估三大核心认知系统，全面激发AI认知能力和系统潜力',
        'features': [
            'AI记忆管理系统（经验记忆存储/智能检索/记忆关系管理/记忆聚类/自动清理/洞察生成）',
            'AI情感分析系统（情感检测/情感趋势分析/情感档案/预警机制/干预建议/干预执行）',
            'AI智能评估系统（多维度评估/知识评估/技能评估/行为评估/进步评估/潜力评估/个性化反馈）',
            'AI记忆管理API（记忆增删改查/智能搜索/关系管理/统计摘要/自动清理/洞察生成）',
            'AI情感分析API（情感检测/历史查询/档案获取/干预生成/预警管理/统计摘要）',
            'AI智能评估API（评估执行/评估查询/趋势分析/统计摘要/评估标准管理）',
            '记忆关系网络（记忆关联/知识图谱整合/上下文理解/语义推理）',
            '情感预警系统（异常检测/多级预警/自动干预/干预效果跟踪）',
            '智能评估模型（加权评分/等级评定/个性化反馈/改进建议/趋势跟踪）',
            '认知数据融合（记忆+情感+评估三维数据整合/跨系统分析/深度洞察）',
            '全子系统版本统一升级（23个子系统同步升级至v11.0.0）',
            '系统安全加固（API权限控制/数据加密/访问审计/敏感信息保护）',
            '性能优化（数据库查询优化/缓存机制/异步处理/批量操作）',
            '扩展性增强（插件化架构/动态配置/灵活集成/标准化接口）'
        ],
        'upgrade_notes': '从v10.0.0升级：新增AI记忆管理系统、AI情感分析系统、AI智能评估系统三大认知核心系统，实现记忆-情感-评估三维数据融合分析'
    },
    '10.0.0': {
        'major': 10,
        'minor': 0,
        'patch': 0,
        'build_number': '20260715a',
        'build_date': '2026-07-15',
        'codename': 'AI Evolution & System Expansion Edition',
        'status': 'stable',
        'description': 'AI进化与系统扩展版本，实现AI智能决策支持、统一版本管理API、统一系统扩展API，全面升级所有子系统版本，激发AI和系统最大潜力',
        'features': [
            '智能决策支持系统（数据驱动决策/趋势预测/风险评估/决策建议/仪表板）',
            '统一版本管理API（20+子系统版本集中管理/批量升级/版本回滚/版本锁定/升级历史）',
            '统一系统扩展API（插件机制/动态加载/扩展注册/配置管理/插件扫描）',
            'AI自学习系统增强（实时系统数据收集/用户活动分析/AI性能跟踪/模式检测/洞察生成）',
            'AI员工技能进化系统增强（技能跟踪/能力评分/思维焦点进化/技能等级进阶/技能建议）',
            'AI协作系统增强（多AI员工协同/任务分配/知识共享/协作历史/最佳员工选择）',
            'AI知识图谱系统（5大学科/知识关系发现/学习路径推荐/语义搜索）',
            'AI智能题目生成系统（多题型支持/难度自适应/批量异步生成/题目质量评估）',
            'AI智能学习规划系统（艾宾浩斯遗忘曲线/复习计划/多计划类型/进度跟踪）',
            'AI辅导助手系统（个性化辅导/学习建议/问题解答/学习进度分析）',
            'AI预警干预系统（多维风险评估/四级预警/个性化干预/干预闭环管理）',
            'AI智能学习系统（智能学习路径/自适应学习/学习效果预测/学习质量评估）',
            '移动端管理系统（设备管理/推送通知/移动端适配/移动学习H5）',
            '学生分析系统（学习行为分析/成绩预测/学习风格识别/个性化推荐）',
            'Git自动同步系统（变更检测/自动提交/推送/版本控制）',
            '集群管理系统（多节点管理/负载均衡/故障转移/实时监控）',
            '数据库安全加固（硬编码密钥移除/环境变量配置/加密存储）',
            '安全漏洞修复（依赖包升级/代码安全审计/敏感信息保护）',
            '全子系统版本统一升级（20个子系统同步升级至v10.0.0）',
            '系统扩展市场（插件注册/安装/启用/禁用/卸载全生命周期管理）'
        ],
        'upgrade_notes': '从v9.0.0升级：新增智能决策支持系统、统一版本管理API、统一系统扩展API，全面升级20个子系统版本，实现系统扩展插件化机制'
    },
    '9.0.0': {
        'major': 9,
        'minor': 0,
        'patch': 0,
        'build_number': '20260714a',
        'build_date': '2026-07-14',
        'codename': 'AI Empowerment & Unified Version Edition',
        'status': 'stable',
        'description': 'AI赋能与统一版本管理版本，实现AI自学习、AI技能进化、统一版本管理、AI协作系统、智能决策支持，全面激发系统AI潜力',
        'features': [
            '统一版本管理系统（所有子系统版本集中管理/批量升级/版本回滚/版本锁定）',
            'AI自学习系统（系统模式分析/性能跟踪/洞察生成/从历史数据学习）',
            'AI员工技能进化系统（技能跟踪/能力评分/思维焦点进化/技能等级进阶）',
            '统一AI赋能API（AI系统状态监控/任务编排/能力评估/洞察中心）',
            'AI协作系统（多AI员工协同工作/任务分配/知识共享/协作历史）',
            '智能决策支持系统（数据驱动决策/趋势预测/风险评估/决策建议）',
            '统一系统扩展API（功能扩展管理/插件机制/动态加载/扩展市场）',
            'AI知识图谱系统（知识关联/语义搜索/智能问答/知识推理）',
            'AI辅导助手系统（个性化辅导/学习建议/问题解答/学习进度分析）',
            'AI预警干预系统（异常检测/风险预警/自动干预/干预记录）',
            'AI智能学习系统（智能学习路径/自适应学习/学习效果预测/学习质量评估）',
            'AI题目生成系统（智能出题/题目质量评估/知识点覆盖/难度自适应）',
            '移动端管理系统（设备管理/推送通知/移动端适配/移动学习H5）',
            '学生分析系统（学习行为分析/成绩预测/学习风格识别/个性化推荐）',
            'Git自动同步系统（变更检测/自动提交/推送/版本控制）',
            '集群管理系统（多节点管理/负载均衡/故障转移/实时监控）',
            '数据库安全加固（硬编码密钥移除/环境变量配置/加密存储）',
            '安全漏洞修复（依赖包升级/代码安全审计/敏感信息保护）'
        ],
        'upgrade_notes': '从v8.0.0升级：新增统一版本管理、AI自学习、AI技能进化、AI协作、智能决策支持等核心子系统，全面激发AI潜力'
    },
    '8.0.0': {
        'major': 8,
        'minor': 0,
        'patch': 0,
        'build_number': '20260713a',
        'build_date': '2026-07-13',
        'codename': 'Full Function Expansion Edition',
        'status': 'stable',
        'description': '全功能扩展版本，智能延展系统所有功能包括子功能和新建子系统',
        'features': [
            '用户认证增强系统（多因素认证MFA/权限矩阵/用户分组/登录尝试追踪）',
            '考试增强系统（考试预约/错题本/考试收藏/考试标签/成绩分析）',
            '学习增强系统（学习路径规划/学习进度追踪/成就系统/学习社区）',
            '课程管理系统（课程创建/章节管理/学员报名/学习进度/课程评价）',
            '作业系统（作业布置/作业提交/AI批改/作业统计/智能反馈）',
            '消息通知系统（站内消息/邮件通知/推送服务/通知模板/通知设置）',
            '资源管理系统（文件上传/资源分类/资源分享/权限控制/版本管理）',
            '数据分析系统（数据可视化/智能报表/趋势分析/预测模型/仪表盘）',
            '题库扩展系统（智能题目生成/题目质量评估/题库自动扩充/知识点关联）',
            '安全监控系统（入侵检测/威胁分析/安全审计/访问控制/异常行为监测）'
        ],
        'upgrade_notes': '从v7.2.0升级：全面扩展用户认证、考试、学习系统，新建课程、作业、通知、资源、数据分析子系统'
    },
    '7.2.0': {
        'major': 7,
        'minor': 2,
        'patch': 0,
        'build_number': '20260707b',
        'build_date': '2026-07-07',
        'codename': 'Comprehensive Enhanced Edition',
        'status': 'stable',
        'description': '全面增强版本，深度拓展数据库功能，完善移动端适配，强化AI集群和模型库，升级前端布局排版，完善权限规则，丰富题库体系，自动Git同步',
        'features': [
            '数据库全面增强（移动端配置表/通知推送队列/用户设备表）',
            '后端API增强（移动端检测/推送通知/题库拓展/设备管理）',
            '前端移动端适配（响应式设计/viewport/触摸优化）',
            'AI集群深度拓展（多节点管理/负载均衡/故障转移）',
            'AI模型库增强（20+模型/模型性能评分/自动注册）',
            '权限规则矩阵强化（50+规则/细粒度权限/动态规则）',
            '题库体系完善（成人教育/K12全科目/模拟题库/真题扩容）',
            '前端布局排版优化（响应式布局/多主题/组件升级）',
            '端口管理强化（多服务/动态分配/健康检查）',
            '集群管理增强（整列监控/多维度管理/实时状态）',
            '版本历史完整记录（9+版本）',
            'GitHub文档自动更新（README.md/SYSTEM_MANUAL.md）',
            'Git自动同步（变更检测/提交/推送/一键同步）',
            '跑马灯通知管理（默认关闭/管理员开启/AI自动推送）',
            '手机客户端适配（移动端管理端/触控优化）'
        ],
        'upgrade_notes': '从v7.1.0升级：全面增强数据库、前端移动端适配、AI集群/模型库、题库、权限规则、端口管理、集群管理，完善文档和Git同步'
    },
    '7.1.0': {
        'major': 7,
        'minor': 1,
        'patch': 0,
        'build_number': '20260707a',
        'build_date': '2026-07-07',
        'codename': 'Intelligent Modular Enhanced Edition',
        'status': 'stable',
        'description': '智能模块化增强版本，深度拓展十大功能模块，丰富AI模型库(15+)，完整权限矩阵(40+规则)，集群节点扩展，题库分类体系，前端仪表板增强',
        'features': [
            '系统综合增强管理器深度拓展（十大功能模块完整实现）',
            '增强管理器API蓝图（32+路由）',
            '增强管理器可视化仪表板（实时监控/操作面板）',
            'AI模型库扩展（15+模型：GPT-4/Claude-3/Qwen/Whisper/embedding等）',
            '完整权限规则矩阵（40+规则，覆盖10+角色）',
            '集群节点扩展（master/worker/backup多节点）',
            '题库分类体系（K12+成人教育全科目）',
            '端口管理强化（多服务端口分配）',
            '多维度性能监控（CPU/磁盘/内存/进程）',
            'Git自动同步（变更检测/提交/推送/一键同步）',
            '登录重定向修复（角色跳转/next参数）',
            '前端布局主题管理（多主题切换）',
            '版本历史完整记录（7+版本）',
            '系统说明书文档（SYSTEM_MANUAL.md）',
            'GitHub说明文档更新（README.md）'
        ],
        'upgrade_notes': '从v7.0.0升级：深度拓展十大功能模块，丰富AI模型库和权限规则矩阵，增强前端仪表板'
    },
    '7.0.0': {
        'major': 7,
        'minor': 0,
        'patch': 0,
        'build_number': '20260707',
        'build_date': '2026-07-07',
        'codename': 'Intelligent Modular Edition',
        'status': 'stable',
        'description': '智能模块化版本，模块化启动系统，590+检索模型，AI员工45+，API/路由数据库管理，多维度集群强化',
        'features': [
            '模块化启动系统（modular_start.py）',
            '8阶段数据库配置分段加载',
            '6阶段功能模块加载（API/蓝图/服务/AI引擎/中间件）',
            'AI智能检索查询模型系统（590+模型）',
            'AI智能API数据库管理（api_management.db）',
            'AI智能路由数据库管理（routes_management.db）',
            'AI员工和Agent数据库管理（45+员工，6+Agent）',
            '分布式数据库架构（16+独立数据库）',
            '智能数据库路由系统',
            '完整的权限管理体系（RBAC）',
            'AI集群和模型库管理强化',
            '题库升级和优化',
            '集群管理和多维度监控',
            '端口管理和整列强化',
            '前端布局排版优化',
            '系统资源监控API',
            '完善的API接口文档',
            'Git/GitHub自动同步'
        ],
        'upgrade_notes': '从v6.0.0升级：新增模块化启动系统、AI智能检索模型、API/路由数据库管理'
    },
    '6.0.0': {
        'major': 6,
        'minor': 0,
        'patch': 0,
        'build_number': '20260706',
        'build_date': '2026-07-06',
        'codename': 'Distributed Database Edition',
        'status': 'stable',
        'description': '分布式数据库版本，支持13个独立数据库，629+路由，460+API接口',
        'features': [
            '分布式数据库架构（13个独立数据库）',
            '智能数据库路由系统',
            '完整的权限管理体系',
            'AI集群和模型库管理',
            '题库升级和优化',
            '集群管理和多维度监控',
            '系统资源监控API',
            '完善的API接口文档'
        ],
        'upgrade_notes': '从v5.x升级：数据库自动拆分，需要重新配置数据库连接'
    },
    '5.0.0': {
        'major': 5,
        'minor': 0,
        'patch': 0,
        'build_number': '20260601',
        'build_date': '2026-06-01',
        'codename': 'AI Integration Edition',
        'status': 'stable',
        'description': 'AI集成版本，引入AI引擎和智能评估系统',
        'features': [
            'AI助教引擎',
            '智能评估系统',
            '知识图谱引擎',
            '错题本智能分析',
            '学习预测引擎'
        ],
        'upgrade_notes': '从v4.x升级：新增AI引擎依赖'
    },
    '4.0.0': {
        'major': 4,
        'minor': 0,
        'patch': 0,
        'build_number': '20260501',
        'build_date': '2026-05-01',
        'codename': 'Exam System Edition',
        'status': 'stable',
        'description': '考试系统版本，完善的在线考试和监考功能',
        'features': [
            '在线考试系统',
            '智能监考系统',
            '成绩分析报告',
            '题库管理系统',
            '考试安排和调度'
        ],
        'upgrade_notes': '从v3.x升级：新增考试相关表'
    },
    '3.0.0': {
        'major': 3,
        'minor': 0,
        'patch': 0,
        'build_number': '20260401',
        'build_date': '2026-04-01',
        'codename': 'Learning Edition',
        'status': 'stable',
        'description': '学习系统版本，完善的学习管理和进度追踪',
        'features': [
            '学习进度追踪',
            '课程管理系统',
            '学习记录分析',
            '知识点关联',
            '学习报告生成'
        ],
        'upgrade_notes': '从v2.x升级：新增学习相关功能'
    },
    '2.0.0': {
        'major': 2,
        'minor': 0,
        'patch': 0,
        'build_number': '20260301',
        'build_date': '2026-03-01',
        'codename': 'Admin Edition',
        'status': 'stable',
        'description': '管理系统版本，完善的权限和用户管理',
        'features': [
            '用户管理系统',
            '权限管理系统',
            '角色管理系统',
            '系统配置管理',
            '日志记录系统'
        ],
        'upgrade_notes': '从v1.x升级：新增管理功能'
    },
    '1.0.0': {
        'major': 1,
        'minor': 0,
        'patch': 0,
        'build_number': '20260201',
        'build_date': '2026-02-01',
        'codename': 'Initial Edition',
        'status': 'stable',
        'description': '初始版本，基础功能和框架',
        'features': [
            '基础用户认证',
            '系统框架搭建',
            '基础数据库设计',
            'API接口基础',
            '前端页面框架'
        ],
        'upgrade_notes': '初始版本'
    }
}

CURRENT_VERSION = '15.0.0'

def init_version_table():
    conn = connect('system')
    if conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                codename TEXT,
                status TEXT,
                description TEXT,
                build_date TEXT,
                build_number TEXT,
                upgrade_time TEXT DEFAULT CURRENT_TIMESTAMP,
                upgrade_type TEXT,
                notes TEXT
            )
        ''')
        conn.commit()
        
        cursor.execute('SELECT COUNT(*) FROM version_history')
        count = cursor.fetchone()[0]
        
        if count == 0:
            for version, data in VERSION_DATA.items():
                cursor.execute('''
                    INSERT INTO version_history 
                    (version, codename, status, description, build_date, build_number, upgrade_type, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    version,
                    data['codename'],
                    data['status'],
                    data['description'],
                    data['build_date'],
                    data['build_number'],
                    'initial',
                    data['upgrade_notes']
                ))
            conn.commit()
            print(f"[Version Manager] 版本历史表初始化完成，共 {len(VERSION_DATA)} 个版本")
        
        conn.close()

def get_current_version():
    return VERSION_DATA[CURRENT_VERSION]

def get_version(version):
    return VERSION_DATA.get(version)

def get_all_versions():
    return list(VERSION_DATA.values())

def get_version_history():
    conn = connect('system')
    if conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM version_history ORDER BY build_date DESC')
        history = []
        for row in cursor.fetchall():
            history.append({
                'id': row['id'],
                'version': row['version'],
                'codename': row['codename'],
                'status': row['status'],
                'description': row['description'],
                'build_date': row['build_date'],
                'build_number': row['build_number'],
                'upgrade_time': row['upgrade_time'],
                'upgrade_type': row['upgrade_type'],
                'notes': row['notes']
            })
        conn.close()
        return history
    return []

def record_upgrade(version, upgrade_type='manual', notes=''):
    conn = connect('system')
    if conn:
        cursor = conn.cursor()
        data = VERSION_DATA.get(version, {})
        cursor.execute('''
            INSERT INTO version_history 
            (version, codename, status, description, build_date, build_number, upgrade_time, upgrade_type, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            version,
            data.get('codename', ''),
            data.get('status', 'stable'),
            data.get('description', ''),
            data.get('build_date', datetime.now().isoformat()),
            data.get('build_number', ''),
            datetime.now().isoformat(),
            upgrade_type,
            notes
        ))
        conn.commit()
        conn.close()
        print(f"[Version Manager] 版本升级记录已保存: {version}")

def check_upgrade_available(current_version):
    versions = sorted(VERSION_DATA.keys(), reverse=True)
    latest_version = versions[0]
    
    if latest_version > current_version:
        return {
            'available': True,
            'latest_version': latest_version,
            'current_version': current_version,
            'data': VERSION_DATA[latest_version]
        }
    return {
        'available': False,
        'latest_version': latest_version,
        'current_version': current_version,
        'data': VERSION_DATA[current_version]
    }

def get_version_comparison(version1, version2):
    v1 = VERSION_DATA.get(version1)
    v2 = VERSION_DATA.get(version2)
    
    if not v1 or not v2:
        return None
    
    return {
        'version1': version1,
        'version2': version2,
        'v1_features': v1.get('features', []),
        'v2_features': v2.get('features', []),
        'new_features': list(set(v2.get('features', [])) - set(v1.get('features', []))) if v2 and v1 else [],
        'removed_features': list(set(v1.get('features', [])) - set(v2.get('features', []))) if v2 and v1 else []
    }

init_version_table()