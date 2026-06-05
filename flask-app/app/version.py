# -*- coding: utf-8 -*-
"""
系统版本管理模块
"""

VERSION = "1.6.0"
BUILD_NUMBER = "20260605"
RELEASE_DATE = "2026-06-05"

VERSION_INFO = {
    'version': VERSION,
    'build_number': BUILD_NUMBER,
    'release_date': RELEASE_DATE,
    'api_version': 'v1',
    'codename': 'MTSCOS Phoenix',
    'status': 'stable'
}

CHANGELOG = [
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
        'contributors': ['System AI']
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
        'contributors': ['System AI']
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
        'contributors': ['System AI']
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
        'contributors': ['System AI']
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
        'contributors': ['System AI']
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
        'contributors': ['System AI']
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
        'contributors': ['System AI']
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
            'changes': latest['changes']
        }
    return {
        'has_update': False,
        'latest_version': latest['version'],
        'current_version': current_version
    }
