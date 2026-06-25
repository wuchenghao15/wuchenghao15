# -*- coding: utf-8 -*-
"""
系统版本管理模块
"""

VERSION = "1.7.0"
BUILD_NUMBER = "20260626"
RELEASE_DATE = "2026-06-26"

VERSION_INFO = {
    'version': VERSION,
    'build_number': BUILD_NUMBER,
    'release_date': RELEASE_DATE,
    'api_version': 'v1',
    'codename': 'MTSCOS Phoenix Enhanced',
    'status': 'stable'
}

CHANGELOG = [
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
            '清理3个冗余依赖文件 - 消除误报漏洞来源'
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
