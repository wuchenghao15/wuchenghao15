#!/usr/bin/env python3
import os
import json
import time
import sqlite3
from datetime import datetime
from db_manager import connect

VERSION_DATA = {
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

CURRENT_VERSION = '9.0.0'

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