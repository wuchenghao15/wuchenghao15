# -*- coding: utf-8 -*-
"""
系统版本管理模块
"""

VERSION = "7.6.0"
BUILD_NUMBER = "20260711001"
RELEASE_DATE = "2026-07-11"

VERSION_INFO = {
    'version': VERSION,
    'build_number': BUILD_NUMBER,
    'release_date': RELEASE_DATE,
    'api_version': 'v1',
    'codename': 'Mobile Adaptive & AI Enhancement Suite',
    'status': 'stable'
}

CHANGELOG = [
    {
        'version': '7.6.0',
        'date': '2026-07-11',
        'title': '移动端适配增强与AI全面升级套件',
        'changes': [
            '新增移动端响应式布局系统 - 768px/480px/360px三档断点，flexbox自适应，触摸优化',
            '新增移动端交互脚本 - MobileInteractions类，支持滑动手势识别、触摸事件、表单输入优化',
            '新增移动端菜单系统 - 左侧抽屉式菜单，触摸滑动打开/关闭，响应式导航切换',
            '新增移动端专用页面模板 - mobile/home.html、mobile/login.html、mobile/exam.html、mobile/profile.html',
            '新增PWA增强配置 - manifest.json升级、service-worker.js优化、离线缓存策略',
            '前端布局排版升级 - 统一CSS变量系统、AI玻璃态效果、发光动画、进度条样式',
            'AI集群全面升级 - 新增6个AI专用集群（教育/题库/分析/辅导/代码/图像），共13个集群',
            'AI模型库扩展至38个模型 - 覆盖GPT-4/Claude-3/Qwen/Llama-3/Gemini/Mistral等主流模型',
            'AI员工系统扩展 - 新增12个AI员工，共41个AI员工负责不同领域',
            '权限规则系统增强 - 扩展至16个系统角色，6级访问控制，审计日志系统完善',
            '系统版本统一管理 - VERSION文件、version.py、SYSTEM_DOC.md、CHANGELOG.md统一升级至v7.6.0',
            '系统说明书更新 - 新增移动端适配章节、AI集群管理章节、API接口文档完善',
            '系统功能统计更新 - 28个蓝图、98个API、138个服务、251个AI引擎、580个路由、20个数据库'
        ],
        'security_fixes': [],
        'breaking_changes': [],
        'contributors': ['Mobile AI', 'UI AI', 'AI Cluster AI', 'Permission AI', 'Documentation AI'],
        'highlights': ['移动端适配', 'AI集群升级', '模型库扩展', '权限增强', '文档完善']
    },
    {
        'version': '7.5.0',
        'date': '2026-07-10',
        'title': '成人教育与K12全学段题库拓展版',
        'changes': [
            '新增成人教育与K12题库服务 - adult_k12_question_bank_service.py，支持全学段题库管理',
            '新增9大教育阶段 - 小学/初中/高中/职业教育/专科/本科/成人高考/自学考试/职业资格',
            '新增14大科目题库 - 语文/数学/英语/物理/化学/生物/历史/地理/政治/计算机/经济/法律/管理/会计',
            '新增8种题型支持 - 单选/多选/判断/填空/简答/论述/计算/案例分析',
            '新增成人高考题库 - 覆盖语文、数学、英语、政治等成人高考科目',
            '新增自学考试题库 - 覆盖多专业核心课程',
            '新增职业资格题库 - 会计从业、法律职业、计算机等级、经济师等',
            '新增K12全学段题库 - 小学/初中/高中各科目，覆盖基础到高级知识点',
            '新增题库统计API - 按阶段/科目/题型/难度多维度统计',
            '新增adult_k12_api.py API模块 - 6个RESTful接口，支持题目CRUD和统计',
            '完善题库数据模型 - 知识点标签、难度分级、分数设置、题目解析',
            'SQLite数据库优化 - 启用WAL模式、30秒busy_timeout、NORMAL同步模式、10000缓存',
            '系统版本升级至v7.5.0 - 统一所有版本文件和配置',
            '系统功能统计更新 - 27个蓝图、94个API、132个服务、239个AI引擎、566个路由、19个数据库'
        ],
        'security_fixes': [],
        'breaking_changes': [],
        'contributors': ['Education AI', 'Question Bank AI', 'System AI'],
        'highlights': ['成人教育题库', 'K12全学段', '职业资格', '多维度统计', 'SQLite优化']
    },
    {
        'version': '7.4.0',
        'date': '2026-07-09',
        'title': 'Arduino AI增强版',
        'changes': [
            '新增Arduino AI IDE - 全新Web端代码编辑器，支持5种板型（Uno/Nano/Mega/ESP32/ESP8266）',
            '新增AI代码生成系统 - 根据功能描述自动生成Arduino代码，支持代码解释和复杂度分析',
            '新增项目管理系统 - 项目保存/加载、元数据管理、电路数据存储、标签筛选',
            '新增教学课程系统 - 6大分类（入门/基础/传感器/显示/通信/进阶），3级难度，代码示例',
            '新增元件库系统 - 5大类元件（基础/传感器/输出/通信/存储），图标展示和代码片段',
            '新增arduino.db独立数据库 - 4张核心表（projects/tutorials/ai_prompts/user_progress）',
            '新增18个API接口 - 代码生成/编译/上传/验证/项目/教程/元件库等完整RESTful API',
            '统一系统版本号至v7.4.0 - 修复version.py/config.py/version_service等版本不一致',
            '系统功能全面统计 - 25个蓝图、90个API、120个服务、200+AI引擎'
        ],
        'security_fixes': [],
        'breaking_changes': [],
        'contributors': ['Arduino AI', 'System AI'],
        'highlights': ['Arduino AI IDE', 'AI代码生成', '项目管理', '教学课程', '元件库']
    },
    {
        'version': '7.3.0',
        'date': '2026-07-08',
        'title': 'PWA移动端与AI学习套件版',
        'changes': [
            '新增PWA移动端适配 - manifest.json、service-worker.js，支持添加到主屏幕和离线缓存',
            '新增AI智能答疑系统 - 多科目问答、会话管理、知识库搜索',
            '新增智能错题本系统 - 错题收集、艾宾浩斯复习、薄弱知识点分析'
        ],
        'security_fixes': [],
        'breaking_changes': [],
        'contributors': ['PWA AI', 'Tutor AI'],
        'highlights': ['PWA适配', 'AI答疑', '智能错题本']
    },
    {
        'version': '7.2.0',
        'date': '2026-07-09',
        'title': '全面增强版',
        'changes': [
            '统一版本号至v7.2.0 - 修复config.py/version.py/SYSTEM_DOC.md版本不一致问题',
            '题库全面拓展 - 37个科目（成人教育9个+K12全科目28个），37,000+题目',
            '权限规则矩阵完善 - 12个角色，细粒度权限控制覆盖全系统功能',
            'AI集群升级 - 15个AI模型（GPT-4/Claude-3/Qwen/Llama-3/Gemini等），性能监控',
            '端口管理增强 - 21个端口配置，支持扫描/分配/预留/释放/自动修复',
            '集群多维度管理 - 4种负载均衡策略（轮询/最小连接/加权轮询/IP哈希），健康检查，自动故障转移',
            'Git自动同步 - 安全机制、保护分支、操作审计、定时同步',
            '手机管理端界面升级 - 新增端口管理和集群管理Tab，负载均衡策略切换',
            '系统说明书完善 - 16个章节，完整架构、API、部署指南',
            '版本历史记录 - 完整记录v1.0.0至v7.2.0所有版本变更',
            '数据库性能优化 - 索引优化、查询重构、分片架构',
            '前端布局优化 - 响应式设计、移动端适配、组件增强',
            'API管理增强 - 120+API接口，统一响应格式，安全认证',
            '自动化运维 - 每日健康检查、日志清理、数据库备份'
        ],
        'security_fixes': [],
        'breaking_changes': [],
        'contributors': ['System AI', 'Enhancement AI'],
        'highlights': ['题库拓展', '权限矩阵', 'AI集群', '端口管理', '集群管理']
    },
    {
        'version': '7.1.0',
        'date': '2026-07-08',
        'title': '仪表盘重构与AI拓展系统',
        'changes': [
            '超级管理员仪表盘完全重构 - 左侧标签栏(260px固定)+右侧Tab切换式内容区',
            '左侧标签栏 - Logo区+用户卡片(L{user_level}·{role})+4个导航分组+底部操作按钮',
            '右侧内容区 - 渐变欢迎横幅+4统计卡片+快捷操作网格+系统资源监控+最近活动日志',
            'Tab切换 - overview/resources/logs/engines/users/exam/routes/employees/backup/settings共10个标签页',
            '数据每30秒自动刷新 - 调用/api/super-admin/dashboard获取实时数据',
            'base_layout.html重构 - 删除aside侧边栏，各页面自带侧边栏',
            '新建AI自动完善拓展页面(ai_auto_expand.html) - 5个标签页，实时日志，统计卡片',
            '模块加载器新增API - /api/super-admin/dashboard, /api/routes/list, /api/routes/reload, /api/routes/check',
            'ROOT_REBOOT最高级初始化(Level 14) - 6步流程，14个数据库481张表，82条路由，41个AI员工'
        ],
        'security_fixes': [],
        'breaking_changes': [],
        'contributors': ['Dashboard AI', 'UI AI'],
        'highlights': ['仪表盘重构', 'AI拓展系统', '实时监控']
    },
    {
        'version': '7.0.0',
        'date': '2026-07-07',
        'title': '智能模块化启动版',
        'changes': [
            '模块化启动系统 - 8阶段配置加载+6阶段功能模块加载',
            'AI智能检索系统 - 智能搜索和数据查询',
            'API管理数据库化 - API配置存储到数据库',
            '路由管理数据库化 - 路由规则存储到数据库',
            '分布式数据库架构完善 - 16+独立数据库',
            'AI引擎矩阵扩展 - 20+核心引擎，60+AI员工'
        ],
        'security_fixes': [],
        'breaking_changes': [],
        'contributors': ['Modular AI', 'Integration AI'],
        'highlights': ['模块化启动', '智能检索', '数据库化管理']
    },
    {
        'version': '6.0.0',
        'date': '2026-07-06',
        'title': '分布式数据库架构版',
        'changes': [
            '分布式数据库架构 - 13个独立数据库分离',
            '智能数据库路由 - SQL查询自动路由到正确数据库',
            '数据分片策略 - 按功能模块、数据类型、热度分散',
            '数据库健康监控 - 实时监控分片健康状态',
            '数据迁移执行 - 安全分批迁移，MD5一致性校验',
            '查询路由优化 - 智能路由到最优分片'
        ],
        'security_fixes': [],
        'breaking_changes': [],
        'contributors': ['Database AI', 'Architecture AI'],
        'highlights': ['分布式数据库', '智能路由', '数据分片']
    },
    {
        'version': '5.3.0',
        'date': '2026-07-06',
        'title': '权限增强版',
        'changes': [
            '新增29项权限规则 - 覆盖AI功能、学习诊断、智能评估、知识库、审计等全功能',
            '新增权限常量定义 - VIEW_ONLY、USER_MANAGEMENT、SYSTEM_ADMIN、AI_FEATURES、AI_ADMIN、EXAM_FEATURES、LEARNING_FEATURES',
            '新增14种角色等级 - guest→user→student→student_vip→teacher→researcher→admin→super_admin→hardware_admin等',
            '新增6级访问控制 - NONE/VIEW/EDIT/MANAGE/ADMIN/SUPER_ADMIN',
            '新增审计日志系统 - 完整操作记录、实时审计、精准查询、可视化分析',
            '新增安全增强 - 强密码策略、会话安全、数据加密、威胁检测',
            '升级题库系统 - 覆盖初高中全学段，27道高质量题目',
            '优化前端页面 - 超级管理员仪表盘、学生仪表盘、登录页面、设置页面版本标识更新',
            '升级权限管理服务 - PermissionManager类增强，缓存机制优化',
            '同步所有版本文件 - VERSION文件统一更新至v5.3.0'
        ],
        'security_fixes': [],
        'breaking_changes': [],
        'contributors': ['System AI', 'Permission AI'],
        'highlights': ['权限管理', '审计日志', '安全增强']
    },
    {
        'version': '5.2.0',
        'date': '2026-07-04',
        'title': 'AI智能分散数据库与系统维护版本',
        'changes': [
            '新增AI智能分散数据库系统 - 按表类型、功能模块、数据热度三维维度分散数据库',
            '新增数据分散决策AI员工 - 智能决策数据迁移和分片策略',
            '新增数据迁移执行AI员工 - 安全分批迁移数据，支持MD5一致性校验',
            '新增查询路由优化AI员工 - 智能路由查询到最优分片',
            '新增数据库健康监控AI员工 - 实时监控分片健康状态',
            '创建独立元数据库ai_distributed_db.db - 管理分片元数据和迁移状态',
            '创建5个分片数据库 - logs.db、exam_behavior.db、ai_engine.db、knowledge.db、core.db',
            '迁移6张日志表到logs.db分片 - system_logs、access_logs、error_logs、operation_logs、security_audit_logs、change_logs',
            '优化SQL查询性能 - 替换COUNT(*)为MAX(rowid)避免全表扫描',
            '修复SQLite线程安全问题 - 所有连接添加check_same_thread=False',
            '修复SQL双引号陷阱 - 统一使用单引号作为字符串边界',
            '完善自动配置系统 - 从7步扩展到8步，整合分散数据库系统',
            '增强版本Agent AI - 版本规则引擎、触发条件、处罚规则',
            '增强自动化计划Agent - 功能覆盖分析、自动扩展、计划优化',
            '新增SQLite线程安全修复 - 版本代理和自动化计划代理添加check_same_thread=False',
            '新增数据库双备份机制 - primary/secondary路径备份',
            '更新影子系统和沙盒备份 - 保持与主数据库同步',
            '例行维护优化 - 数据库清理、日志清理、健康检查'
        ],
        'security_fixes': [],
        'breaking_changes': [],
        'contributors': ['System AI', 'Database AI'],
        'highlights': ['AI分散数据库', '分片架构', '数据迁移', '系统维护']
    },
    {
        'version': '5.1.0',
        'date': '2026-06-29',
        'title': '自动迭代更新版本',
        'changes': [
            '新增版本自动更新服务 - 支持版本号升级、Changelog更新、Git提交与GitHub同步',
            '新增灰度发布系统 - 支持百分比、用户组、IP范围、Cookie策略的灰度发布',
            '新增健康检查与自动回滚机制 - CPU/内存/错误率监控，连续3次不健康自动回滚',
            '新增人机协同审批系统 - 定义NORMAL/IMPORTANT/CRITICAL/DANGEROUS四级操作等级',
            '新增自动化测试框架 - 单元测试、接口测试、页面测试、压力测试',
            '新增Git源码自动操作模块 - 分支管理、代码修改、配置调整、安全推送',
            '新增依赖漏洞扫描器 - 定期扫描依赖包漏洞，高危漏洞自动创建升级任务',
            '新增主动迭代引擎 - 分析运行数据，自动生成优化需求，编写新功能代码',
            '新增运维报告生成器 - 每日自动生成运维报告并上传数据库',
            '新增考试系统拓展功能 - 考试预约、错题重做、考试笔记、考试收藏、成绩对比分析、考试标签',
            '新增学生仪表盘功能 - AI学习助手、学习计划管理、学习社区、学习成就系统、学习提醒、学习数据分析可视化',
            '修复硬编码绝对数据库路径问题 - 使用动态相对路径',
            '优化系统初始化流程 - 统一初始化模块，按依赖顺序加载',
            '修复Agent运行时数据库连接问题 - 使用项目统一db_manager'
        ],
        'security_fixes': [],
        'breaking_changes': [],
        'contributors': ['Auto Version Updater'],
        'highlights': ['版本自动更新', '灰度发布', '自动化测试', '考试系统拓展']
    },
    {
        'version': '1.8.0',
        'date': '2026-06-26',
        'title': 'AI维护员工与系统说明书版',
        'changes': [
            '新增AI维护员工 - 负责系统例行维护、健康检查、数据清理和版本升级',
            '新增数据库清理器 - 清理旧日志、旧会话、未验证用户，压缩和分析数据库',
            '新增日志清理器 - 定期清理过期日志文件，提供日志统计信息',
            '新增备份管理器 - 自动创建、管理和恢复数据库备份',
            '新增系统健康检查器 - 监控数据库、磁盘空间、日志和备份状态',
            '新增系统说明书页面 - 详细介绍系统功能和架构',
            '新增使用说明书页面 - 指导用户如何使用系统各项功能',
            '新增初次登录引导功能 - 非管理员用户首次登录时显示引导（可跳过）',
            '新增维护API接口 - 提供维护操作、健康检查、版本升级等接口',
            '优化版本升级流程 - 支持自动升级和手动升级两种模式'
        ],
        'security_fixes': [],
        'breaking_changes': [],
        'contributors': ['Maintenance AI'],
        'highlights': ['AI维护员工', '系统说明书', '初次登录引导']
    },
    {
        'version': '1.7.0',
        'date': '2026-06-26',
        'title': '系统架构优化与安全增强版',
        'changes': [
            '融合v2_systems全部功能到现有系统架构',
            '增强审计系统 - 多维度审计、实时监控、告警和报告生成',
            '增强权限管理系统 - 角色权限、资源权限、权限继承和动态分配',
            '新增主题配色系统 - 支持多主题管理、颜色系统、用户偏好',
            '增强线程/进程管理 - 线程池、任务调度、监控和资源管理',
            '新增沙盒系统 - 多类型隔离、文件操作、安全策略和资源限制',
            '增强环境管理系统 - 多环境配置、依赖管理、系统监控',
            '修复57个安全漏洞 - 升级所有Python依赖到安全版本',
            '精简系统根目录 - 从33个目录精简到21个（减少36%）',
            '释放4.5GB系统空间 - 清理日志和冗余文件',
            '强化异常登录页面 - CSS变量、无障碍属性、数据库上报',
            '自动挂载匹配Listening音频文件 - 1900个匹配率100%',
            '安全删除208个未引用文件 - Python文件从750减少到542',
            '精简Markdown文档 - 删除381个文件，精简率75.1%',
            '精简目录文件 - 删除1371个文件，5个目录'
        ],
        'security_fixes': [
            'Flask 2.0.1 -> 2.3.3 (修复多个安全漏洞)',
            'Werkzeug 2.0.1 -> 2.3.8 (修复路径遍历、SSRF等漏洞)',
            'Jinja2 3.0.1 -> 3.1.4 (修复SSTI等模板注入漏洞)',
            'requests 2.26.0 -> 2.32.3 (修复多个HTTP安全漏洞)',
            'SQLAlchemy 1.4.22 -> 1.4.54 (修复SQL注入等漏洞)',
            'numpy 1.21.2 -> 1.26.4 (修复多个数值计算安全漏洞)',
            'pandas 1.3.3 -> 2.0.3 (修复多个数据处理安全漏洞)',
            'scikit-learn 0.24.2 -> 1.3.2 (修复机器学习安全漏洞)',
            'matplotlib 3.4.3 -> 3.7.5 (修复图像渲染安全漏洞)',
            'React Native 0.74.3 -> 0.77.1 (修复移动端多个安全漏洞)',
            'React 18.2.0 -> 18.3.1 (修复XSS等前端安全漏洞)',
            'axios 1.6.8 -> 1.7.9 (修复HTTP请求安全漏洞)',
            'Babel 7.22.0 -> 7.26.7 (修复转译器安全漏洞)',
            'ESLint 8.45.0 -> 9.20.0 (修复代码检测工具漏洞)',
            '清理3个冗余依赖文件 - 消除误报漏洞来源',
            'GitHub Actions升级 - checkout v3->v4, setup-python v4->v5, upload-artifact v3->v4',
            'Docker镜像全面升级 - PostgreSQL 14/15->17, Redis 7->7.4, Nginx alpine->1.27',
            'Python基础镜像升级 - 3.10 -> 3.11',
            '清理8个冗余docker-compose文件 - 消除日志目录中的误报源'
        ],
        'breaking_changes': [],
        'contributors': ['System AI', 'Architecture AI'],
        'highlights': ['安全漏洞修复', '架构优化', '功能整合']
    },
    {
        'version': '1.6.5',
        'date': '2026-06-20',
        'title': 'AI员工系统增强版',
        'changes': [
            '新增架构工程师AI员工 - 系统文件架构优化',
            '增强代码修复系统 - 自动扫描和修复代码问题',
            '优化Auto API系统 - 统一响应所有auto开头的API',
            '完善音频管理系统 - 自动挂载和匹配音频文件',
            '增强日志管理系统 - 集成审计功能'
        ],
        'breaking_changes': [],
        'contributors': ['System AI'],
        'highlights': ['架构优化', 'AI员工增强']
    },
    {
        'version': '1.6.4',
        'date': '2026-06-15',
        'title': '安全审计增强版',
        'changes': [
            '增强异常登录检测 - 多维度风险评估',
            '完善审计日志系统 - 全操作记录可追溯',
            '优化权限验证机制 - 细粒度权限控制',
            '增强会话管理 - 安全会话生命周期管理',
            '修复安全漏洞 - 输入验证和输出编码增强'
        ],
        'breaking_changes': [],
        'contributors': ['System AI'],
        'highlights': ['安全增强', '审计完善']
    },
    {
        'version': '1.6.3',
        'date': '2026-06-10',
        'title': '数据库性能优化版',
        'changes': [
            '优化数据库查询性能 - 索引优化和查询重构',
            '增强数据库版本管理 - 完善变更追踪机制',
            '添加数据库监控系统 - 实时性能监控',
            '优化数据备份策略 - 增量备份和恢复',
            '增强数据加密机制 - 敏感数据保护'
        ],
        'breaking_changes': [],
        'contributors': ['System AI'],
        'highlights': ['性能优化', '数据安全']
    },
    {
        'version': '1.6.2',
        'date': '2026-06-08',
        'title': '前端界面优化版',
        'changes': [
            '优化响应式布局 - 多设备适配增强',
            '增强用户体验 - 动画和过渡效果优化',
            '完善主题系统 - 深色模式支持',
            '优化加载性能 - 资源懒加载和缓存策略',
            '增强可访问性 - WCAG 2.1标准兼容'
        ],
        'breaking_changes': [],
        'contributors': ['System AI'],
        'highlights': ['UX优化', '可访问性']
    },
    {
        'version': '1.6.1',
        'date': '2026-06-06',
        'title': 'Bug修复与性能优化版',
        'changes': [
            '修复硬件管理系统模板路径问题',
            '优化侧边栏导航性能',
            '修复通知系统消息丢失问题',
            '增强系统稳定性 - 异常处理完善',
            '优化内存使用 - 资源释放机制改进'
        ],
        'breaking_changes': [],
        'contributors': ['System AI'],
        'highlights': ['Bug修复', '性能优化']
    },
    {
        'version': '1.6.0',
        'date': '2026-06-05',
        'title': '硬件管理系统UI增强版',
        'changes': [
            '完善侧边栏功能 - 添加系统状态指示器、导航折叠、多级菜单、快捷操作面板',
            '拓展主内容区顶部栏 - 添加全局搜索增强、通知下拉面板、用户菜单、快捷操作按钮',
            '优化仪表盘主内容 - 添加实时数据图表、设备状态热力图、AI分析面板增强',
            '添加响应式设计和移动端适配',
            '修复模板路径配置问题 - 确保硬件管理系统模板正确加载',
            '完善所有硬件管理页面 - 仪表盘、设备管理、系统设置、性能监控、系统日志、API密钥管理',
            '增强用户体验 - 添加实时性能监控和智能分析功能'
        ],
        'breaking_changes': [],
        'contributors': ['System AI'],
        'highlights': ['硬件管理', 'UI增强']
    },
    {
        'version': '1.5.0',
        'date': '2024-04-30',
        'title': 'AI能力增强版',
        'changes': [
            '新增AI题库优化员工 - 智能分析和优化题库内容',
            '新增学生学习优化系统 - 个性化学习路径规划',
            '新增前端权限管理系统 - 动态权限检查和规则集成',
            '新增知识漏洞识别器 - 精准定位薄弱环节',
            '新增考试策略顾问 - 智能考试策略生成',
            '优化前端导航系统 - 基于角色的动态菜单',
            '增强规则引擎 - 支持更多规则类型',
            '改进数据库版本管理 - 完善变更追踪',
            '新增进度追踪功能 - 学习进步可视化',
            '性能优化和Bug修复'
        ],
        'breaking_changes': [],
        'contributors': ['System AI'],
        'highlights': ['AI增强', '学习优化']
    },
    {
        'version': '1.4.0',
        'date': '2024-04-25',
        'title': '数据库版本管理系统',
        'changes': [
            '创建数据库版本管理器',
            '添加版本历史记录',
            '实现变更追踪',
            '添加数据库优化功能',
            '创建索引分析系统',
            '添加版本报告生成'
        ],
        'breaking_changes': [],
        'contributors': ['System AI'],
        'highlights': ['数据库管理', '版本控制']
    },
    {
        'version': '1.3.0',
        'date': '2024-04-20',
        'title': '安全增强版本',
        'changes': [
            '添加私有数据交互协议',
            '实现端到端加密',
            '添加RSA签名验证',
            '实现数据压缩传输',
            '添加安全通道封装'
        ],
        'breaking_changes': [],
        'contributors': ['System AI'],
        'highlights': ['安全增强', '加密通信']
    },
    {
        'version': '1.2.0',
        'date': '2024-04-15',
        'title': '通讯协议集成版本',
        'changes': [
            '集成HTTP协议支持',
            '集成WebSocket实时通信',
            '集成MQTT消息队列',
            '集成gRPC远程调用',
            '添加协议管理器',
            '添加消息路由系统'
        ],
        'breaking_changes': [],
        'contributors': ['System AI'],
        'highlights': ['多协议', '实时通信']
    },
    {
        'version': '1.1.0',
        'date': '2024-04-10',
        'title': '数据库性能优化版本',
        'changes': [
            '添加数据库索引优化',
            '优化查询性能',
            '添加表关系优化',
            '改进数据完整性约束',
            '添加索引使用统计'
        ],
        'breaking_changes': [],
        'contributors': ['System AI'],
        'highlights': ['性能优化', '数据库']
    },
    {
        'version': '1.0.0',
        'date': '2024-04-01',
        'title': 'MTSCOS 9年教育系统初始版本',
        'changes': [
            '创建用户管理系统',
            '创建题库管理系统',
            '创建考试系统',
            '创建学习系统',
            '创建教学内容管理系统',
            '创建系统配置管理',
            '创建日志系统',
            '创建安全监控',
            '创建本地存储',
            '创建规则引擎'
        ],
        'breaking_changes': [],
        'contributors': ['System AI'],
        'highlights': ['初始版本', '完整功能']
    }
]


def get_version():
    """获取版本号"""
    return VERSION


def get_version_info():
    """获取版本信息"""
    return VERSION_INFO


def get_changelog():
    """获取更新日志"""
    return CHANGELOG


def get_latest_version():
    """获取最新版本"""
    return CHANGELOG[0]


def get_changelog_by_version(version):
    """根据版本号获取更新日志"""
    for entry in CHANGELOG:
        if entry['version'] == version:
            return entry
    return None


def check_for_updates(current_version):
    """检查更新"""
    latest = get_latest_version()
    if latest['version'] > current_version:
        return {
            'has_update': True,
            'latest_version': latest['version'],
            'current_version': current_version,
            'changes': latest['changes'],
            'highlights': latest.get('highlights', [])
        }
    return {
        'has_update': False,
        'latest_version': latest['version'],
        'current_version': current_version
    }


def get_version_range(start_version, end_version=None):
    """获取版本范围内的更新记录"""
    result = []
    found_start = False
    
    for entry in CHANGELOG:
        if entry['version'] == start_version:
            found_start = True
        
        if found_start:
            result.append(entry)
            
            if end_version and entry['version'] == end_version:
                break
    
    return result


def get_major_versions():
    """获取所有主版本"""
    majors = []
    seen = set()
    
    for entry in CHANGELOG:
        major = entry['version'].split('.')[0]
        if major not in seen:
            seen.add(major)
            majors.append({
                'major_version': major,
                'first_release': entry['date'],
                'title': entry['title'],
                'version_count': 0
            })
    
    for entry in CHANGELOG:
        major = entry['version'].split('.')[0]
        for m in majors:
            if m['major_version'] == major:
                m['version_count'] += 1
                break
    
    return majors


def get_version_stats():
    """获取版本统计信息"""
    total_versions = len(CHANGELOG)
    major_versions = len(set(v['version'].split('.')[0] for v in CHANGELOG))
    total_changes = sum(len(v.get('changes', [])) for v in CHANGELOG)
    total_contributors = set()
    for v in CHANGELOG:
        for c in v.get('contributors', []):
            total_contributors.add(c)
    
    return {
        'total_versions': total_versions,
        'major_versions': major_versions,
        'total_changes': total_changes,
        'total_contributors': len(total_contributors),
        'first_release': CHANGELOG[-1]['date'] if CHANGELOG else None,
        'latest_release': CHANGELOG[0]['date'] if CHANGELOG else None,
        'current_version': VERSION
    }
