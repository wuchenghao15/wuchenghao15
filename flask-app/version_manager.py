#!/usr/bin/env python3
import os
import json
import time
import sqlite3
from datetime import datetime
from db_manager import connect

VERSION_DATA = {
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

CURRENT_VERSION = '7.0.0'

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