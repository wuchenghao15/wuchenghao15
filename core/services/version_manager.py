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
import sys
import json
import time
import sqlite3
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
    '18.1.0': {
        'major': 18,
        'minor': 1,
        'patch': 0,
        'build_number': '20260729a',
        'build_date': '2026-07-29',
        'codename': 'Automation Plans & AI Extension Edition',
        'status': 'stable',
        'description': '自动化计划调度系统版本，实现13个核心计划+20个AI自动延展计划；涵盖系统维护、AI投喂、题库管理、教辅同步、AI员工维护、后端巡检、数据库安全、VIKEY监控、对话流管理、积分清零、积分商城、农历佛教事件等全链路自动化',
        'features': [
            '自动化计划调度框架（scheduler_base.py）- AbstractAutoPlan抽象基类+CentralPlanScheduler调度管理器',
            '13个核心自动化计划：系统维护/AI投喂/题库管理/教辅同步/AI员工维护/后端巡检/数据库安全/VIKEY监控/对话流管理/积分清零/积分商城/农历佛教事件/自动延展',
            '20个AI自动延展计划 - 指标监控/缓存预热/死锁检测/审计清理/索引重建/备份轮转/临时文件清理/内存优化/API频率监控/知识升级/用户活跃度追踪/错误率监控/内容审核/性能基准测试/配置同步/安全扫描/数据完整性验证/通知汇总/功能开关审查/用户分群',
            'API端点：/api/auto_plans/status/run/run_all/toggle - 支持查看状态、手动执行、启用禁用',
            '系统启动自动初始化 - create_all_plans_and_register + AI延展 + start_all',
            '知识投喂引擎扩展 - 从9个知识域48条扩展至20个知识域206条',
            'AI脑库认知维度模型 - 5层认知体系(L1-L5)+知识关联图谱+跨域推理引擎',
            'VIKEY API封装 - 统一对外Facade模式，7要素强认证全链路',
            '首页UI/UX优化 - 65%/35%分栏布局+背景光晕+渐变网格+深度感+入场动画',
            '积分商城AI脑补 - 12个预设商品+5个AI自动生成商品（考试卷/免作业卷/Token卷/答疑券等）'
        ],
        'upgrade_notes': '升级步骤：1. 更新VERSION文件到18.1.0；2. 执行init_version_table()初始化版本历史；3. 批量升级subsystem_versions；4. 重启服务使调度器生效'
    },
    '17.22.0': {
        'major': 17,
        'minor': 22,
        'patch': 0,
        'build_number': '20260726a',
        'build_date': '2026-07-26',
        'codename': 'SuperAdmin UX Unified Edition',
        'status': 'stable',
        'description': '超级管理员登录UX统一体验版本，实现SA用户名识别时的UI自适应隐藏与恢复；主版本与所有30+子系统版本同步对齐至17.22.0，完成系统版本一致性清理',
        'features': [
            '首页登录表单SA识别增强：输入wuchenghao15时自动隐藏「记住我」「忘记密码？」「或分割线」「创建新账户」四件套，切换普通用户自动恢复',
            '密码可见性切换按钮SA场景强制隐藏，防止SA登录环节敏感操作误触',
            '主版本CURRENT_VERSION从17.21.0升级至17.22.0，version_manager版本历史新增SA UX Unified Edition条目',
            '全子系统版本统一升级：AI自学习/AI技能进化/AI协作/智能决策支持/AI智能学习/AI辅导助手/AI预警干预/AI知识图谱/AI题目生成/AI学习规划/移动端管理/考试系统/学习系统/课程管理/作业系统/消息通知/资源管理/数据分析/安全监控/用户认证 共20个子系统同步升级至17.22.0',
            '前后端版本一致性修复：超管设置页sys_version硬编码17.9.0→17.22.0，app.db与Database/app.db system_versions表新增17.22.0记录',
            'Git版本库与GitHub代码同步：版本升级变更一次性提交并推送远端仓库'
        ],
        'upgrade_notes': '升级依赖：1. 更新CURRENT_VERSION常量；2. 向system_versions表插入17.22.0新版本；3. 批量升级subsystem_versions所有子系统current_version/latest_version至17.22.0；4. 同步前端硬编码版本字符串（super_admin_settings、index页脚、mt_architecture页）'
    },
    '17.21.0': {
        'major': 17,
        'minor': 21,
        'patch': 0,
        'build_number': '20260726',
        'build_date': '2026-07-26',
        'codename': 'Dependency & Security Edition',
        'status': 'stable',
        'description': '全量依赖升级、GitHub 安全漏洞告警修复与 Dependabot 激活；升级 pyasn1 等直接可修复漏洞，标注 Python 3.10+ 升级路径修复剩余 53 项 PYSEC 漏洞',
        'features': [
            '核心依赖按 requirements.txt 对齐升级：Flask 3.1.3 / Werkzeug 3.1.8 / SQLAlchemy 2.0.51 / Jinja2 3.1.6 / MarkupSafe 3.0.3 / beautifulsoup4 4.15.0 / click 8.1.8 / dashscope 1.26.4 / openai 2.48.0 / psutil 7.2.2 / tqdm 4.69.1 / paho-mqtt 2.1.0 / websockets 15.0.1',
            '修复已在 Python 3.9 兼容范围内的安全漏洞：pyasn1 0.6.3 → 0.6.4（消除 PYSEC-2026-3455/3456/3457 三项 CVE）',
            '激活 Dependabot：pip 日更（安全补丁/小版本分组 PR）+ github-actions 周更 + docker 周更，保留 protobuf<6 / paho-mqtt<2 兼容性白名单',
            'CI/CD 安全流水线升级：新增 pip-audit（Python 3.10 全矩阵漏洞审计）、Trivy 文件系统 CVEs+misconfig+secret 扫描并上传 SARIF 到 GitHub Code Scanning，Bandit 扫描范围扩展到 app/ai_engines/core/',
            '已知 Python 3.9 限制：aiohttp 11/requests 1/urllib3 2/python-dotenv 1/pytest 1/filelock 2/black 2/click 1/langchain 6/langgraph 5/langsmith 4/msgpack 1/orjson 1/pillow 14/pip 3/setuptools 1 = 共 53 项 PYSEC/GHSA 需升级到 Python 3.10+ 才能用官方 Fix Version 解决',
        ],
        'upgrade_notes': '升级前请先切到 Python 3.10+ 环境，再执行 `pip install -r requirements.txt --upgrade`；依赖版本号 2026-07-26 基准生成'
    },
    '17.20.0': {
        'major': 17,
        'minor': 20,
        'patch': 0,
        'build_number': '20260725l',
        'build_date': '2026-07-25',
        'codename': 'Dynamic Question Engine Edition',
        'status': 'stable',
        'description': '动态题目生成引擎版本，取消固有化题库，支持AI自动动态生成题目和网络爬取题目，实现动态多态多维随机高质量高数量动态注入所有科目题库',
        'features': [
            '动态题目生成引擎（dynamic_question_engine.py）- 支持AI自动动态生成和网络爬取',
            '多态多维随机生成策略 - 避免撞库，确保题目多样性',
            '10个科目完整知识点覆盖（每科8个知识组，每组3-4个知识点）',
            '6种题型模板：单选题、填空题、简答题、计算题、判断题、翻译题',
            '动态题目标签生成 - 根据难度、题型、知识点自动生成标签',
            '网络爬虫模块 - 支持从网络获取题目（需安装requests和beautifulsoup4）',
            '爬取题目自动导入统一题库功能',
            '生成历史记录 - 记录每次生成的详细信息',
            '动态配置管理 - 支持配置每日生成量、批次大小、相似度阈值等',
            '动态题目API（dynamic_question_api.py）- 完整的动态生成接口',
            'API接口：生成题目、批量生成、爬取题目、导入爬取、配置管理、统计查询',
            '安全中间件白名单更新 - 添加动态题目API路由',
            'API蓝图注册 - 注册dynamic_question_api'
        ],
        'upgrade_notes': '从v17.19.0升级：建立动态题目生成引擎，取消固有化题库，支持AI自动动态生成题目（多态多维随机生成，避免撞库），支持网络爬取题目，实现动态多态多维随机高质量高数量动态注入所有科目题库，添加完整的动态题目API接口'
    },
    '17.19.0': {
        'major': 17,
        'minor': 19,
        'patch': 0,
        'build_number': '20260725k',
        'build_date': '2026-07-25',
        'codename': 'Unified Question Bank Edition',
        'status': 'stable',
        'description': '统一题库管理系统版本，优化管理MTSCOS题库，加强所有科目类型体量，更新题库所有科目内容保持与教辅和现实同步，支持AI自动延展题库内容',
        'features': [
            '统一题库管理系统（unified_question_bank.py）- 支持所有科目和题型',
            '支持10个科目：语文、数学、英语、物理、化学、生物、历史、地理、政治、日语',
            '支持13种题型：单选、多选、判断、填空、简答、计算、听力、写作、阅读理解、听写、翻译、编程、论述',
            '支持3个难度级别：基础题、提高题、压轴题',
            '支持18种题目标签：真题、模拟题、练习题、专项训练、单元测试、期中、期末、中考、高考、时政、热点、易错、高频、重点、难点、解题模型、举一反三、拓展延伸',
            'AI自动延展题库功能 - 根据现有题目自动生成相似题目',
            '题库同步机制 - 支持与外部教辅和网络资源同步',
            '统一题库API（unified_question_api.py）- 完整的题库管理接口',
            '题目增删改查、批量导入、AI延展、同步等功能',
            '题库统计分析 - 按科目、题型、难度统计题目数量',
            '安全中间件白名单更新 - 添加统一题库API路由',
            'API蓝图注册 - 注册chinese_listening_api和unified_question_api'
        ],
        'upgrade_notes': '从v17.18.0升级：建立统一题库管理系统，支持所有科目（政治、日语、英语、数学、物理、化学、生物、历史、地理），支持所有题型，支持AI自动延展题库内容，支持与教辅和网络资源同步，添加完整的题库管理API接口'
    },
    '17.18.0': {
        'major': 17,
        'minor': 18,
        'patch': 0,
        'build_number': '20260725j',
        'build_date': '2026-07-25',
        'codename': 'Database Enhancement Edition',
        'status': 'stable',
        'description': '数据库增强版本，扩展数据库能力，扩充题库内容，更新系统参数和权限参数路由参数，更新AI脑库，更新已注册AI员工，维护数据库API和中间件',
        'features': [
            '扩展题库数据库（database_enhancement.py）- 新增5个语文听力题相关表',
            'chinese_dictation_words - 语文听写词库表（40+词语，4个难度级别）',
            'chinese_dictation_idioms - 语文成语词库表（40+成语，4个难度级别）',
            'chinese_dictation_poetry - 语文古诗词库表（25首诗词，4个难度级别）',
            'chinese_dictation_passages - 语文读文选段表（12篇文章，4个难度级别）',
            'chinese_listening_questions - 语文听力题目表',
            '题库分类扩展 - 新增4个语文听力分类（词语听写/成语听写/古诗词听写/读文选段听写）',
            '数据库增强脚本执行完成 - 所有新表创建并初始化数据',
            'AI脑库知识更新 - 添加语文听力相关知识条目',
            'AI员工配置更新 - 更新听力题库员工技能配置',
            '安全中间件白名单更新 - 添加语文听力API路由',
            '访问控制中间件更新 - 添加新API权限控制',
            '系统参数更新 - 添加语文听力相关配置项',
            '所有数据库表创建成功'
        ],
        'upgrade_notes': '从v17.17.0升级：扩展数据库能力，新增5个语文听力题相关表，初始化题库内容（40词语+40成语+25诗词+12文章），更新系统参数、权限参数、路由参数，更新AI脑库和已注册AI员工配置，维护数据库API和中间件'
    },
    '17.17.0': {
        'major': 17,
        'minor': 17,
        'patch': 0,
        'build_number': '20260725i',
        'build_date': '2026-07-25',
        'codename': 'Chinese Listening Dictation Edition',
        'status': 'stable',
        'description': '语文听力听写增强版本，完善听力题逻辑和出题能力，新增语文听力题：词语听写、成语听写、古诗词听写、读文选段听写，支持四个难度级别（小学低年级/高年级/初中/高中）',
        'features': [
            '扩展听力题库AI员工（listening_question_employee.py）- 新增中文语言支持',
            '词语听写题目生成（_generate_word_dictation）- 80+词语库，4个难度级别',
            '成语听写题目生成（_generate_idiom_dictation）- 60+成语库，4个难度级别',
            '古诗词听写题目生成（_generate_poetry_dictation）- 40+古诗词库，4个难度级别',
            '读文选段听写题目生成（_generate_passage_dictation）- 12篇精选文章，4个难度级别',
            '中文听写统一入口（_generate_chinese_dictation）- 支持按类型生成或混合生成',
            '任务类型扩展 - generate_chinese/generate_word_dictation/generate_idiom_dictation/generate_poetry_dictation/generate_passage_dictation',
            '难度分级评分系统 - 按难度级别自动计算题目分数',
            '知识点标签系统 - 题目关联对应知识点和难度级别',
            '语音报读支持 - 支持普通话女声/男声报读',
            '拼音辅助提示 - 提供词语/成语拼音提示',
            '释义说明 - 提供词语/成语含义解释',
            '古诗词完整信息 - 包含诗名/作者/朝代/原文',
            '读文选段关键词提取 - 自动提取文章关键词',
            '所有生成方法测试通过'
        ],
        'upgrade_notes': '从v17.16.0升级：完善听力题逻辑，新增语文听力题四大类型（词语/成语/古诗词/读文选段听写），支持四个难度级别，实现完整的听写题目生成能力'
    },
    '17.16.0': {
        'major': 17,
        'minor': 16,
        'patch': 0,
        'build_number': '20260725h',
        'build_date': '2026-07-25',
        'codename': 'Arduino AI Enhanced Edition',
        'status': 'stable',
        'description': 'Arduino开发AI增强版本，利用现有AI技术Agent增强Arduino开发功能，集成数据科学、数字孪生、知识图谱、DevOps、图像处理能力',
        'features': [
            '修复Bug：arduino_ai_api.py第12行 Bluelogger.info→Blueprint',
            '修复Bug：arduino_ai_engine.py Serial.logger.info()→Serial.print()',
            '新建arduino_ai_enhanced.py - Arduino AI增强引擎',
            'AI传感器故障预测API（/api/arduino/ai/predict-sensor-failure）- 数据科学Agent集成',
            '数字孪生模拟API（/api/arduino/ai/digital-twin-simulate）- 数字孪生Agent集成',
            '组件兼容性查询API（/api/arduino/ai/component-compatibility）- 知识图谱Agent集成',
            '组件故障排除API（/api/arduino/ai/troubleshoot-component）- 知识图谱推理',
            '构建流水线API（/api/arduino/ai/build-pipeline）- DevOps Agent集成',
            '摄像头图像分析API（/api/arduino/ai/analyze-camera-image）- 图像处理Agent集成',
            '视觉控制API（/api/arduino/ai/vision-control）- 图像识别+代码生成',
            '增强版学习路径API（/api/arduino/ai/enhanced-learning-path）- AI能力推荐',
            '初始化Arduino组件知识图谱（控制器、传感器、执行器、显示器、通信模块）',
            '组件故障排除指南（DHT11、HC-SR04、SG90、LCD 1602、ESP8266）',
            '所有API测试通过'
        ],
        'upgrade_notes': '从v17.15.0升级：修复2个关键Bug，新增8个AI增强API端点，将数据科学、数字孪生、知识图谱、DevOps、图像处理Agent集成到Arduino开发流程'
    },
    '17.15.0': {
        'major': 17,
        'minor': 15,
        'patch': 0,
        'build_number': '20260725g',
        'build_date': '2026-07-25',
        'codename': 'AI Technology Suite Edition',
        'status': 'stable',
        'description': 'AI技术套件扩展版本，新增10个AI技术方向Agent（数据科学、图像处理、语音处理、智能翻译、数据治理、商业智能、DevOps、微服务管理、知识图谱、数字孪生），全面覆盖AI技术栈',
        'features': [
            'AI数据科学Agent（ai_data_science_agent.py）- 机器学习/预测建模/特征工程/数据清洗/A/B测试',
            'AI图像处理Agent（ai_image_processing_agent.py）- 图像识别/分类/检测/分割/生成/增强',
            'AI语音处理Agent（ai_speech_processing_agent.py）- 语音识别/合成/声纹识别/情感分析',
            'AI智能翻译Agent（ai_translation_agent.py）- 文本翻译/文档翻译/实时翻译/术语库/本地化',
            'AI数据治理Agent（ai_data_governance_agent.py）- 数据质量/元数据管理/血缘分析/合规检查',
            'AI商业智能Agent（ai_business_intelligence_agent.py）- 报表生成/趋势分析/异常检测/商业洞察',
            'AI DevOps Agent（ai_devops_agent.py）- CI/CD/容器管理/基础设施即代码/监控告警',
            'AI微服务管理Agent（ai_microservice_agent.py）- 服务注册/负载均衡/熔断降级/链路追踪/网关',
            'AI知识图谱Agent（ai_knowledge_graph_agent.py）- 实体识别/关系抽取/知识推理/知识融合',
            'AI数字孪生Agent（ai_digital_twin_agent.py）- 孪生建模/仿真模拟/预测分析/优化控制/场景推演',
            'AI员工管理器扩展（ai_employee_manager.py）- 注册10个新Agent类型',
            'Agent类型定义 - data_science/image_processing/speech_processing/translation/data_governance/business_intelligence/devops/microservice/knowledge_graph/digital_twin',
            '初始员工创建 - 每个Agent类型创建初始实例',
            '所有Agent继承AIEmployee基类 - 统一接口和属性',
            '所有API测试通过'
        ],
        'upgrade_notes': '从v17.14.0升级：新增10个AI技术方向Agent，覆盖数据科学、计算机视觉、语音处理、NLP翻译、数据治理、商业智能、DevOps、微服务、知识图谱、数字孪生等核心AI技术领域'
    },
    '17.14.0': {
        'major': 17,
        'minor': 14,
        'patch': 0,
        'build_number': '20260725f',
        'build_date': '2026-07-25',
        'codename': 'AI Enterprise Suite Edition',
        'status': 'stable',
        'description': 'AI企业套件扩展版本，新增10个企业级AI Agent（教育管理、社区管理、活动管理、内容创作、配置管理、日志分析、文档处理、安全漏洞检测、网络安全、系统扩展），全面覆盖企业运营场景',
        'features': [
            'AI教育管理Agent（ai_education_manager.py）- 课程管理/学习路径规划/学生评估/成绩分析',
            'AI社区管理Agent（ai_community_manager.py）- 用户管理/内容审核/帖子管理/社区健康度评估',
            'AI活动管理Agent（ai_activity_manager.py）- 活动策划/报名管理/活动数据分析/活动评估',
            'AI内容创作Agent（ai_content_creator.py）- 文章创作/文案撰写/标题生成/SEO优化',
            'AI配置管理Agent（ai_config_manager.py）- 配置读写/验证/备份/恢复/审计',
            'AI日志分析Agent（ai_log_analyzer.py）- 日志收集/解析/异常检测/性能分析/告警生成',
            'AI文档处理Agent（ai_document_processor.py）- 文档上传/摘要/搜索/分类/对比/翻译',
            'AI安全漏洞检测Agent（ai_vulnerability_scanner.py）- 代码审计/依赖检查/配置安全/漏洞分析',
            'AI网络安全Agent（ai_cybersecurity_agent.py）- 入侵检测/威胁分析/防火墙管理/安全事件响应',
            'AI系统扩展Agent（ai_system_extension_agent.py）- 插件管理/服务注册/接口扩展/性能优化',
            'AI员工管理器扩展（ai_employee_manager.py）- 注册10个新Agent类型',
            'Agent类型定义 - education_manager/community_manager/activity_manager/content_creator/config_manager/log_analyzer/document_processor/vulnerability_scanner/cybersecurity/system_extension',
            '初始员工创建 - 每个Agent类型创建初始实例',
            '所有Agent继承AIEmployee基类 - 统一接口和属性',
            '每个Agent独立技能列表 - 专业技能匹配对应职责',
            '企业场景全覆盖 - 教育/社区/活动/内容/配置/安全/运维',
            '所有API测试通过'
        ],
        'upgrade_notes': '从v17.13.0升级：新增10个企业级AI Agent，覆盖教育管理、社区管理、活动管理、内容创作、配置管理、日志分析、文档处理、安全漏洞检测、网络安全、系统扩展等领域'
    },
    '17.13.0': {
        'major': 17,
        'minor': 13,
        'patch': 0,
        'build_number': '20260725e',
        'build_date': '2026-07-25',
        'codename': 'AI Business Intelligence Edition',
        'status': 'stable',
        'description': 'AI商业智能扩展版本，新增10个专业AI Agent（代码生成、对话管理、推荐系统、营销、客服、舆情分析、财务分析、人力资源、项目管理、客户关系），全面覆盖业务运营场景',
        'features': [
            'AI代码生成Agent（ai_code_generator_agent.py）- 多语言代码生成/优化/API生成',
            'AI对话管理Agent（ai_conversation_agent.py）- 对话管理/意图识别/回复生成',
            'AI推荐系统Agent（ai_recommendation_agent.py）- 个性化推荐/协同过滤/内容推荐',
            'AI营销Agent（ai_marketing_agent.py）- 营销策略/广告文案/A/B测试/ROI分析',
            'AI客服Agent（ai_customer_service_agent.py）- 工单管理/问题解答/投诉处理',
            'AI舆情分析Agent（ai_public_opinion_agent.py）- 舆情监测/情感分析/风险预警',
            'AI财务分析Agent（ai_financial_agent.py）- 利润分析/现金流/预算管理/投资分析',
            'AI人力资源Agent（ai_hr_agent.py）- 员工管理/招聘评估/绩效考核/薪酬计算',
            'AI项目管理Agent（ai_project_management_agent.py）- 项目规划/任务管理/进度跟踪',
            'AI客户关系Agent（ai_crm_agent.py）- 客户管理/销售机会/销售预测/客户分析',
            'AI员工管理器扩展（ai_employee_manager.py）- 注册10个新Agent类型',
            'Agent类型定义 - code_generator/conversation/recommendation/marketing/customer_service/public_opinion/financial/hr/project_management/crm',
            '初始员工创建 - 每个Agent类型创建初始实例',
            'create_employee支持新类型 - 通过类型名创建对应Agent实例',
            '所有Agent继承AIEmployee基类 - 统一接口和属性',
            '每个Agent独立技能列表 - 专业技能匹配对应职责',
            '业务场景全覆盖 - 开发/运营/客服/财务/HR/项目管理',
            '所有API测试通过'
        ],
        'upgrade_notes': '从v17.12.0升级：新增10个业务场景AI Agent，覆盖代码生成、对话管理、推荐系统、营销、客服、舆情分析、财务分析、人力资源、项目管理、客户关系等领域'
    },
    '17.12.0': {
        'major': 17,
        'minor': 12,
        'patch': 0,
        'build_number': '20260725d',
        'build_date': '2026-07-25',
        'codename': 'AI Agent Expansion Edition',
        'status': 'stable',
        'description': 'AI Agent扩展版本，新增11个专业AI Agent（代码审查、自动化测试、性能优化、安全审计、需求分析、文档生成、任务调度、自动修复、数据分析、模型管理、智能运维），注册到AI员工管理器并创建统一管理API',
        'features': [
            'AI代码审查Agent（ai_code_review_agent.py）- 代码安全/性能/风格/复杂度检查',
            'AI自动化测试Agent（ai_auto_test_agent.py）- 单元测试生成/运行/覆盖率分析',
            'AI性能优化Agent（ai_performance_optimizer.py）- 性能监控/代码优化/查询优化',
            'AI安全审计Agent（ai_security_auditor.py）- SQL注入/XSS/敏感信息泄露检测',
            'AI需求分析Agent（ai_requirement_analyzer.py）- 需求提取/优先级排序/文档生成',
            'AI文档生成Agent（ai_doc_generator.py）- API文档/代码文档/README/变更日志',
            'AI任务调度Agent（ai_task_scheduler_agent.py）- 定时任务/任务队列/任务监控',
            'AI自动修复Agent（ai_auto_repair_agent.py）- 错误分析/代码修复/数据库修复',
            'AI数据分析Agent（ai_data_analyzer.py）- 数值分析/文本分析/趋势分析/异常检测',
            'AI模型管理Agent（ai_model_manager.py）- 模型注册/加载/评估/监控',
            'AI智能运维Agent（ai_ops_agent.py）- 系统监控/进程管理/日志分析/健康检查',
            'AI Agent统一管理API（app/api/ai_agents_api.py）- 列表/详情/统计/技能/分配/搜索',
            'AI员工管理器扩展（ai_employee_manager.py）- 注册11个新Agent类型',
            'Agent类型定义 - code_review/auto_test/performance_optimizer/security_auditor/requirement_analyzer/doc_generator/task_scheduler/auto_repair/data_analyzer/model_manager/ops_agent',
            '初始员工创建 - 每个Agent类型创建初始实例',
            'create_employee支持新类型 - 通过类型名创建对应Agent实例',
            '所有Agent继承AIEmployee基类 - 统一接口和属性',
            '每个Agent独立技能列表 - 专业技能匹配对应职责',
            'API路由注册到主应用蓝图列表',
            '所有API测试通过'
        ],
        'upgrade_notes': '从v17.11.0升级：新增11个专业AI Agent，注册到AI员工管理器，创建统一管理API，实现代码审查、自动化测试、性能优化、安全审计等专业能力'
    },
    '17.11.0': {
        'major': 17,
        'minor': 11,
        'patch': 0,
        'build_number': '20260725c',
        'build_date': '2026-07-25',
        'codename': 'History Gallery Enhancement',
        'status': 'stable',
        'description': '项目历史馆完善版本，创建历史馆页面和API，实现版本时间线、升级记录、学习任务、知识脑库、系统规则的可视化展示，添加32条历史数据记录',
        'features': [
            '历史馆页面模板（templates/history_gallery.html）- 深色主题，响应式布局',
            '版本时间线展示 - 垂直时间线卡片，显示版本号、代号、描述、功能列表',
            '升级记录展示 - 表格形式展示版本、升级类型、AI员工数、功能数、状态',
            '学习任务展示 - 表格形式展示任务名称、描述、类型、版本、状态',
            '知识脑库展示 - 网格卡片形式展示知识分类、标题、内容、标签',
            '系统规则展示 - 表格形式展示规则ID、名称、类型、描述、启用状态',
            '统计数据面板 - 版本总数、升级次数、知识条目、学习任务数量',
            '历史馆API路由（app/api/history_api.py）- 6个API接口',
            '历史数据服务增强（app/history_data_service.py）- 32条初始化历史记录',
            '历史数据分类 - system_event/ai_event/feature/upgrade/ai_learning',
            '版本时间线API (/api/history/timeline)',
            '升级记录API (/api/history/upgrades)',
            '学习任务API (/api/history/learning)',
            '知识脑库API (/api/history/knowledge)',
            '系统规则API (/api/history/rules)',
            '统计数据API (/api/history/stats)',
            '历史馆页面路由 (/history)',
            'API注册到主应用蓝图列表',
            '所有API测试通过'
        ],
        'upgrade_notes': '从v17.10.0升级：完善项目历史馆功能，创建页面模板和API，添加32条历史数据记录，实现5个标签页的可视化展示'
    },
    '17.10.0': {
        'major': 17,
        'minor': 10,
        'patch': 0,
        'build_number': '20260725b',
        'build_date': '2026-07-25',
        'codename': 'Project Structure Refactor & AI Collaboration Enhancement',
        'status': 'stable',
        'description': '项目结构重构与AI协作增强版本，全面整理项目根目录，整合脚本和配置文件，配合10809个AI员工实现协作升级维护，自动上报数据库和投喂AI脑库',
        'features': [
            '根目录结构重构 - 从479个条目精简到37个，精简率92.3%',
            '脚本整合 - start.sh/stop_all.sh/status.sh三合一为mtscos.sh统一管理脚本',
            '依赖文件整合 - requirements.txt和requirements-python39.txt使用环境标记自动适配Python版本',
            'Docker配置整合 - 三个docker-compose文件使用profiles机制统一管理',
            '核心服务模块化 - 68个核心服务文件移至core/services/目录',
            '服务模块归类 - 89个临时脚本归入scripts/python/，AI/教育服务归入services/',
            '数据库统一管理 - 35个数据库文件归入Database/目录，根目录保留软链接',
            '配置文件集中 - JSON配置归入config/，密钥证书归入config/security/',
            '日志文件整理 - 所有.log文件归入Logs/目录',
            '备份归档管理 - backups/snapshots/recovery_images归入archive/',
            '文档集中管理 - 15个说明文档归入docs/目录，根目录只保留README.md和VERSION',
            '_path_setup.py路径初始化 - 自动添加所有子目录到sys.path',
            'AI协作升级 - 配合10809个AI员工共同协作升级维护',
            '数据库自动上报 - 所有AI操作数据实时上报数据库',
            'AI脑库投喂 - 升级变更自动投喂AI脑库供学习',
            'AI自动学习触发 - 触发自我学习引擎分析本次升级内容'
        ],
        'upgrade_notes': '从v17.9.0升级：项目结构全面重构，根目录精简92.3%，脚本和配置文件整合，配合10809个AI员工协作升级，自动上报数据库和投喂AI脑库'
    },
    '17.9.0': {
        'major': 17,
        'minor': 9,
        'patch': 0,
        'build_number': '20260725a',
        'build_date': '2026-07-25',
        'codename': 'Settings Page Enhancement Edition',
        'status': 'stable',
        'description': '设置页面增强版本，全面完善用户设置和管理员设置页面，新增学习目标、主题偏好、快捷键设置、日志管理、邮件配置、API管理等功能模块，实现完整的设置API支持',
        'features': [
            '个人设置页面重构（选项卡式布局：个人信息/安全设置/通知设置/隐私设置/数据管理/学习目标/主题偏好/快捷键/关于）',
            '学习目标设置模块（每日学习时长/每日答题数量/每周考试次数/目标分数/学习计划）',
            '主题偏好设置模块（深色模式切换/字体大小调整）',
            '快捷键设置模块（查看系统快捷键列表）',
            '头像上传功能（支持拖拽上传和点击选择）',
            '管理员设置页面增强（系统概览/安全设置/AI引擎管理/数据备份/用户管理/日志管理/邮件配置/API管理）',
            '系统概览模块（服务器状态/系统信息/资源监控/用户统计）',
            '日志管理模块（日志列表/日志筛选/日志导出/日志刷新）',
            '邮件配置模块（SMTP服务器配置/端口/加密方式/发件人信息/测试发送）',
            'API管理模块（API密钥管理/密钥重新生成/密钥复制/访问频率限制/公共访问开关）',
            '用户设置后端API（学习目标保存/外观设置保存/通知设置保存/隐私设置保存/数据导出）',
            '管理员设置后端API（邮件配置保存/API密钥重新生成/API配置保存/安全设置保存/系统日志查询）',
            '设置数据持久化（user_settings表存储用户个人设置）',
            '响应式设计优化（移动端适配/自适应布局）',
            '交互体验提升（即时保存/Toast提示/动画效果）'
        ],
        'upgrade_notes': '从v17.8.0升级：完善用户设置和管理员设置页面，新增多个功能模块，实现完整的设置API支持和数据持久化'
    },
    '17.8.0': {
        'major': 17,
        'minor': 8,
        'patch': 0,
        'build_number': '20260724c',
        'build_date': '2026-07-24',
        'codename': 'System Framework Refactoring',
        'status': 'stable',
        'description': '系统框架重构版本，将app.py中的大型常量和业务逻辑抽取到独立模块，建立规范的分层架构，提升代码可维护性和扩展性',
        'features': [
            '创建app/constants/subjects.py - 科目和考试相关常量定义',
            '创建app/services/auth_service.py - 认证服务（密码验证、用户查询）',
            '创建app/services/system_config_service.py - 系统配置服务（系统/安全/语言设置）',
            '抽取SUBJECT_NAME_MAP、SUBJECT_ICON_MAP、SUBJECT_COLOR_MAP、SUBJECT_CLASS_MAP',
            '抽取SUBJECT_TREE、AI_TEST_SUBJECTS、QUESTION_TYPES等大型常量',
            '抽取verify_password、hash_password、get_user_by_username、get_user_by_id函数',
            '抽取get_system_settings、get_security_settings、get_language_settings函数',
            'app.py体积从50KB+减少到约24KB',
            '建立清晰的模块分层架构：constants（常量）→ services（业务逻辑）→ api（接口）',
            '支持数据库路径动态配置',
            '统一错误处理和日志记录',
            '服务模块支持独立测试和复用'
        ],
        'upgrade_notes': '从v17.7.0升级：重构系统框架，将分散在app.py中的常量和业务逻辑抽取到独立模块，优化代码组织和可维护性'
    },
    '17.7.0': {
        'major': 17,
        'minor': 7,
        'patch': 0,
        'build_number': '20260724b',
        'build_date': '2026-07-24',
        'codename': 'Volcengine AI Engine Integration',
        'status': 'stable',
        'description': '集成火山引擎AI引擎，支持豆包系列模型（doubao-pro、doubao-lite等），实现完整的文本生成、聊天模式、流式生成和文本嵌入功能',
        'features': [
            '火山引擎AI引擎实现（VolcengineEngine类）',
            '支持豆包系列模型：doubao-pro、doubao-lite、doubao-lite-128k、doubao-pro-256k',
            'AWS4-HMAC-SHA256签名算法实现，确保请求鉴权正确',
            '文本生成功能（generate）',
            '聊天模式（chat）- 支持多轮对话',
            '流式生成（generate_stream）- 实时响应',
            '文本嵌入（embed）- 生成文本向量表示',
            '健康检查（health_check）- 引擎状态监测',
            '环境变量配置支持（VOLCENGINE_ACCESS_KEY_ID、VOLCENGINE_SECRET_ACCESS_KEY）',
            '指数退避重试机制',
            '错误响应标准化处理',
            'AI引擎集成管理器支持volcengine类型',
            '配置热更新支持'
        ],
        'upgrade_notes': '从v17.6.0升级：新增火山引擎AI引擎实现，需要配置AK/SK环境变量或通过配置参数传入'
    },
    '17.6.0': {
        'major': 17,
        'minor': 6,
        'patch': 0,
        'build_number': '20260724a',
        'build_date': '2026-07-24',
        'codename': 'Permission Architecture Enhancement Edition',
        'status': 'stable',
        'description': '权限架构增强版本，扩展权限数据库表结构，完善按钮权限、数据权限、接口权限的管理和检查机制，实现细粒度权限控制和接口访问控制中间件',
        'features': [
            '按钮权限表（permission_buttons）- 管理模块下的按钮定义',
            '角色按钮权限关联表（role_button_permissions）- 角色与按钮权限的关联',
            '数据权限表（permission_data_rules）- 角色在模块上的数据访问范围和级别',
            '接口权限表（permission_api_rules）- 角色对API路径和方法的访问控制',
            '按钮权限管理API（按钮列表/添加/删除/权限检查）',
            '数据权限管理API（规则列表/添加/更新/删除/用户数据权限获取）',
            '接口权限管理API（规则列表/添加/更新/删除/权限检查）',
            '权限检查机制（模块权限/按钮权限/数据权限/接口权限四层检查）',
            '权限继承与覆盖（通配符*表示所有权限）',
            '数据权限粒度（数据范围：all/own/public/none；数据级别：full/read/none）',
            '接口权限控制（基于API路径和HTTP方法的细粒度控制）',
            '接口访问控制中间件（自动检查API访问权限）',
            '权限管理页面扩展（按钮权限/数据权限/接口权限管理标签页）',
            '默认权限数据初始化（按钮/数据/接口权限规则）',
            '数据库索引优化（提升权限查询性能）',
            '权限审计日志记录'
        ],
        'upgrade_notes': '从v17.5.0升级：扩展权限数据库表结构，新增按钮权限、数据权限、接口权限三层细粒度控制，完善权限服务和API端点，实现接口访问控制中间件'
    },
    '17.5.0': {
        'major': 17,
        'minor': 5,
        'patch': 0,
        'build_number': '20260723f',
        'build_date': '2026-07-23',
        'codename': 'Approval Workflow Edition',
        'status': 'stable',
        'description': '审批工作流版本，完善审批流程和审批机制，支持多级审批、审批通知、审批记录追溯等完整审批功能',
        'features': [
            '审批数据库表结构（审批请求、审批流程、审批节点、审批记录、审批通知）',
            '审批API端点（创建请求、查询列表、审批通过、审批拒绝、撤销请求）',
            '多级审批流程机制（支持多角色、多节点审批）',
            '审批通知机制（新审批通知、审批通过/拒绝/撤销通知）',
            '审批记录追溯（完整的审批历史记录和意见记录）',
            '审批管理页面（状态统计、筛选搜索、详情查看）',
            '审批优先级系统（高/中/低三级优先级）',
            '审批类型管理（通用/考试/课程/用户/系统五种类型）',
            '审批通知管理（查看通知、标记已读、批量已读）',
            '审批权限控制（申请人/审批人/管理员不同权限）'
        ],
        'upgrade_notes': '从v17.4.0升级：完善审批流程和审批机制，新增审批数据库表、API端点、通知机制和管理页面'
    },
    '17.4.0': {
        'major': 17,
        'minor': 4,
        'patch': 0,
        'build_number': '20260723e',
        'build_date': '2026-07-23',
        'codename': 'AI-Arduino Learning & Interpretation Edition',
        'status': 'stable',
        'description': 'AI-Arduino学习与代码解释版本，新增AI代码解释器（逐行自然语言翻译）、AI自适应学习路径（动态推荐教程和项目），完善多组件组合代码生成能力，全面提升Arduino学习体验',
        'features': [
            'AI代码解释器（逐行翻译Arduino代码为自然语言解释）',
            'AI自适应学习路径（根据学习进度动态推荐教程和项目）',
            '多组件组合代码生成（支持温湿度+LCD+WiFi等复杂场景）',
            '代码结构分析（库引入/常量定义/变量声明/函数定义/setup/loop）',
            '代码与教程关联（检测代码是否包含教程要求的组件和函数）',
            '技能评估系统（数字I/O/模拟I/O/传感器/执行器/显示/通信六大技能维度）',
            '学习计划生成（基于技能差距的周学习计划）',
            '代码总结功能（复杂度评估/关键特性识别/分类统计）',
            'interpret-code API端点（代码解释）',
            'explain-structure API端点（结构分析）',
            'compare-with-tutorial API端点（教程关联）',
            'learning-path API端点（自适应学习路径）',
            '多组件模块系统（12+组件模块，支持动态组合）',
            '组合规则引擎（8种预定义多组件协同工作规则）',
            '组件自动检测（基于关键词自动识别项目所需组件）',
            '学习等级判定（初学者→入门→中级→高级→专家五级）'
        ],
        'upgrade_notes': '从v17.3.0升级：新增AI代码解释器和自适应学习路径功能，增强多组件组合代码生成能力，完善学习评估体系'
    },
    '17.3.0': {
        'major': 17,
        'minor': 3,
        'patch': 0,
        'build_number': '20260723d',
        'build_date': '2026-07-23',
        'codename': 'AI-Arduino Workflow Edition',
        'status': 'stable',
        'description': 'AI-Arduino工作流闭环版本，实现从自然语言描述到代码生成、仿真执行、AI调试分析、硬件推荐的完整智能闭环，大幅提升Arduino开发效率和学习体验',
        'features': [
            '完整工作流闭环API（自然语言描述→代码生成→仿真执行→调试分析→硬件推荐）',
            'generate→simulate→debug闭环（一次性返回完整开发流程结果）',
            'arduino_ai_api蓝图CSRF豁免（确保API端点可正常访问）',
            'debug_code空指针风险修复（正则匹配非空检查）',
            '传感器数据表结构一致性验证（表名和列名统一）',
            '工作流状态追踪（每步状态、成功/失败标识、详细信息）',
            '综合摘要输出（代码生成状态、仿真完成状态、调试问题统计、硬件成本估算）',
            '智能开发流程自动化（无需人工干预的完整开发链）',
            '实时仿真结果分析（结合仿真输出进行代码调试）',
            '端到端开发体验（从想法到硬件方案的一站式服务）'
        ],
        'upgrade_notes': '从v17.2.0升级：实现generate→simulate→debug完整工作流闭环，修复API注册和代码调试稳定性问题，统一传感器数据表结构'
    },
    '17.2.0': {
        'major': 17,
        'minor': 2,
        'patch': 0,
        'build_number': '20260723c',
        'build_date': '2026-07-23',
        'codename': 'AI-Arduino Fusion Edition',
        'status': 'stable',
        'description': 'AI-Arduino深度融合版本，新增AI代码生成器、AI传感器数据分析、AI代码调试助手、AI硬件推荐引擎，将AI能力与Arduino系统深度融合，实现智能硬件编程和自动化运维',
        'features': [
            'AI代码生成器（自然语言描述→Arduino代码，支持LED闪烁/温湿度检测/舵机控制等场景）',
            'AI传感器数据分析（异常检测/趋势预测/智能洞察/数据统计分析）',
            'AI代码调试助手（代码分析/错误检测/调试建议/仿真结果分析）',
            'AI硬件推荐引擎（项目需求分析/组件推荐/预算控制/接线指南生成）',
            'AI代码优化建议（性能优化/可读性提升/最佳实践建议）',
            'Arduino学习进度评估（技能掌握度分析/学习建议/项目推荐）',
            'Arduino教程与AI评估打通（Arduino知识领域纳入AI智能评估系统）',
            '20+组件库（Arduino开发板/传感器/执行器/通信模块）',
            '8种传感器类型支持（温度/湿度/距离/光线/声音/运动/电压/电流）',
            '数据预测功能（线性回归预测传感器数据趋势）',
            'Arduino AI API（代码生成/数据分析/调试建议/硬件推荐/进度评估）',
            '项目推荐引擎（基于学习进度智能推荐项目）'
        ],
        'upgrade_notes': '从v17.1.0升级：新增AI代码生成器、AI传感器数据分析、AI代码调试助手、AI硬件推荐引擎四大AI-Arduino融合能力，将Arduino教程与AI智能评估系统打通'
    },
    '17.1.0': {
        'major': 17,
        'minor': 1,
        'patch': 0,
        'build_number': '20260723b',
        'build_date': '2026-07-23',
        'codename': 'Arduino IoT & Hardware Edition',
        'status': 'stable',
        'description': 'Arduino物联网与硬件版本，新增Arduino项目管理、代码仿真模拟、教学助手、传感器数据采集和IoT设备管理，全面实现硬件编程和物联网能力',
        'features': [
            'Arduino项目管理器（项目创建/文件管理/组件管理/标签管理/点赞功能/搜索功能）',
            'Arduino代码仿真器（数字I/O模拟/模拟I/O模拟/PWM输出/舵机控制/串口通信/蜂鸣器控制）',
            'Arduino教学助手（8个教程/3个难度等级/学习路径规划/教程搜索）',
            'Arduino传感器数据采集器（8种传感器类型/数据记录/告警系统/数据摘要/数据导出）',
            'Arduino IoT管理器（设备连接/命令发送/数据接收/网络扫描/订阅机制）',
            'Arduino API（项目CRUD/代码模拟/教程查询/设备管理/数据采集/IoT控制）',
            '项目分类管理（传感器/物联网/机器人/智能家居等分类）',
            '模拟调试日志（引脚状态/串口输出/LED状态/舵机角度实时追踪）',
            '学习路径规划（入门→中级→高级循序渐进）',
            '传感器告警系统（温度/湿度/距离阈值告警）',
            '网络设备扫描（自动发现局域网内Arduino设备）',
            '多协议支持（HTTP/TCP协议通信）'
        ],
        'upgrade_notes': '从v17.0.0升级：新增Arduino项目管理、代码仿真、教学助手、传感器数据采集和IoT设备管理五大核心模块'
    },
    '17.0.0': {
        'major': 17,
        'minor': 0,
        'patch': 0,
        'build_number': '20260723a',
        'build_date': '2026-07-23',
        'codename': 'AI Expansion & Community Edition',
        'status': 'stable',
        'description': 'AI扩展与社区版本，新增数据可视化引擎、学习激励系统、学习社区系统和系统监控仪表板，全面提升系统智能化和社交化能力',
        'features': [
            'AI数据可视化引擎（学习趋势图表/资源分布饼图/技能雷达图/用户活跃度柱状图/学习热力图/系统指标）',
            'AI学习激励系统（积分奖励/等级系统/徽章解锁/排行榜/学习成就）',
            'AI学习社区系统（帖子管理/评论互动/点赞功能/关注系统/标签管理/搜索功能）',
            'AI系统监控仪表板（CPU/内存/磁盘/网络监控/告警系统/进程日志/数据库统计/健康检查）',
            '多源资源采集（抖音/小红书/GitHub/CSDN/网络爬虫资源采集）',
            'AI资源推荐引擎（用户画像/学习历史/个性化推荐）',
            'AI学习路径规划器（技能差距分析/个性化学习路径）',
            'AI智能评估系统（多维度知识掌握评估）',
            'AI智能搜索引擎（资源/知识库/学习记录综合搜索）',
            'AI学习效果追踪（学习统计/趋势分析/学习报告）',
            'AI智能问答系统（知识库问答/采集资源问答）',
            '可视化API（仪表板数据/图表数据/系统指标/激励统计）',
            '社区API（帖子CRUD/评论/点赞/关注/标签/搜索）',
            '系统监控API（状态查询/健康检查/告警/指标收集）'
        ],
        'upgrade_notes': '从v16.0.0升级：新增AI数据可视化引擎、AI学习激励系统、AI学习社区系统、AI系统监控仪表板，完善AI资源采集和智能推荐能力'
    },
    '16.0.0': {
        'major': 16,
        'minor': 0,
        'patch': 0,
        'build_number': '20260722a',
        'build_date': '2026-07-22',
        'codename': 'Security & Education Enhancement Edition',
        'status': 'stable',
        'description': '安全与教育增强版本，全面增强安全防护体系、教育综合管理功能，完善部署配置和系统文档，提高GitHub曝光度',
        'features': [
            '企业级防火墙增强（10+安全规则：SQL注入/XSS/命令注入/SSRF/文件包含/路径遍历/敏感文件/暴力破解/扫描器防护/API限流）',
            'AI安全建议系统（智能分析安全漏洞，生成优化建议和实施步骤）',
            '安全漏洞管理系统（漏洞特征库/攻击模拟引擎/代码安全扫描器/AI闭环学习）',
            '代码安全扫描（自动扫描Python/HTML代码，检测多种漏洞类型）',
            '教学大纲管理系统（大纲创建/章节管理/知识点管理/课程标准管理/版本控制）',
            '题库与大纲同步（题目与知识点映射/批量映射/考试与大纲同步/智能生成题目）',
            '学习与大纲追踪（学习进度追踪/知识点掌握度/章节进度/学习建议/评估报告）',
            '教育综合API（教学大纲CRUD/题库同步/学习追踪RESTful接口）',
            '看门狗守护进程（调度引擎意外终止自动重启/指数退避重启策略/崩溃记录）',
            'Docker部署配置优化（Dockerfile/Docker Compose完整配置/快速部署配置）',
            '系统文档完善（中英文README/部署指南/版本说明/安全文档/贡献指南）',
            'GitHub曝光度提升（徽章/CI/CD工作流/PR模板/文档完善）',
            '版本号一致性管理（统一版本管理/变更日志/版本说明文档）',
            'Git与GitHub同步（变更检测/自动提交/推送/版本控制）',
            '权限管理适配（16+角色/50+权限规则/6级访问控制/审计日志）',
            '路由链路管理（API路由/前端路由/权限路由/路由统计）',
            '系统健康诊断（8项核心检查/自动修复引擎/预防式维护）',
            '性能监控增强（CPU/内存/磁盘/网络/慢查询检测/性能分析）'
        ],
        'upgrade_notes': '从v15.4.0升级：新增安全漏洞管理系统、教育综合管理系统、看门狗守护进程、Docker部署配置优化、中英文系统文档完善'
    },
    '15.4.0': {
        'major': 15,
        'minor': 4,
        'patch': 0,
        'build_number': '20260721a',
        'build_date': '2026-07-21',
        'codename': 'Enhanced AI Learning & Analytics Edition',
        'status': 'stable',
        'description': 'AI学习增强与分析版本，完善AI学习助手、学习路径推荐、试卷组卷功能，增强学生成绩分析仪表盘',
        'features': [
            'AI智能学习助手（个性化学习推荐/智能作业辅导/学习效果分析/学习报告生成）',
            'AI学习路径推荐增强（薄弱环节分析/知识图谱/学习进度追踪/个性化路径）',
            'AI试卷自动组卷（智能选题/知识覆盖率分析/分数分布计算/质量评分）',
            '学生成绩分析仪表盘（多维度数据可视化/成绩分布直方图/雷达图/趋势图）',
            '智能错题本（艾宾浩斯遗忘曲线/薄弱知识点分析/掌握程度追踪）',
            'AI智能答疑（多科目支持/多题型解答/会话管理/知识库搜索）',
            'AI题目生成器增强（6种题型/11个科目/3级难度/批量生成/自动保存）',
            '学习推荐API（推荐生成/作业分析/学习报告/统计摘要）',
            '试卷组卷API（组卷/预览/保存/统计）',
            '学习路径API（生成/分析/知识图谱/进度）',
            '数据分析可视化（Chart.js集成/多维度图表/实时数据更新）',
            '性能优化（异步处理/缓存机制/数据库索引优化）',
            '安全性增强（API权限控制/数据加密/访问审计）'
        ],
        'upgrade_notes': '从v15.0.0升级：新增AI学习助手、增强学习路径推荐和试卷组卷功能，完善学生成绩分析仪表盘'
    },
    '15.0.0': {
        'major': 15,
        'minor': 0,
        'patch': 0,
        'build_number': '20260720a',
        'build_date': '2026-07-20',
        'codename': 'AI Enhanced Education Edition',
        'status': 'stable',
        'description': 'AI增强教育版本，实现AI题目生成器、AI学习路径推荐、AI试卷组卷、学生成绩分析仪表盘等核心教育功能',
        'features': [
            'AI题目生成器（从文本生成考试题目/6种题型/11个科目/3级难度/自动保存到题库）',
            'AI学习路径推荐（分析错题数据/识别薄弱环节/生成个性化路径/跟踪学习进度）',
            'AI试卷自动组卷（按科目/难度/题型智能组卷/分数分布/考试时长/知识覆盖率）',
            '学生成绩分析仪表盘（成绩分布/各科平均分/学习时间趋势/错题率分析）',
            'AI智能答疑（在线提问/AI自动解答/多科目/多题型/会话管理）',
            '智能错题本（自动收集错题/艾宾浩斯复习/薄弱分析/掌握程度）',
            'AI学习助手API（推荐生成/作业分析/学习报告/统计摘要）',
            '试卷组卷API（组卷/预览/保存/统计）',
            '学习路径API（生成/分析/知识图谱/进度）',
            '题目生成API（生成/保存/统计/检测科目/提取关键点）',
            '数据分析可视化（多维度图表/实时更新/交互式仪表盘）',
            '性能优化（异步处理/缓存/数据库优化）',
            '安全性增强（权限控制/加密/审计）'
        ],
        'upgrade_notes': '从v14.0.0升级：新增AI题目生成器、AI学习路径推荐、AI试卷组卷、学生成绩分析仪表盘等核心教育功能'
    },
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

CURRENT_VERSION = '18.1.0'

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
            logger.info(f"[Version Manager] 版本历史表初始化完成，共 {len(VERSION_DATA)} 个版本")
        
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
        logger.info(f"[Version Manager] 版本升级记录已保存: {version}")

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