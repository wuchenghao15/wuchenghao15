#!/usr/bin/env python3
import os
import json
import time
import sqlite3
import threading
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin

version_unified_api = Bluelogger.info('version_api', __name__)

class VersionUnifiedManager:
    SUBSYSTEMS = [
        {'id': 'ai_self_learning', 'name': 'AI自学习系统', 'description': '系统模式分析、性能跟踪、洞察生成'},
        {'id': 'ai_skill_evolution', 'name': 'AI技能进化系统', 'description': '技能跟踪、能力评分、思维焦点进化'},
        {'id': 'ai_collaboration', 'name': 'AI协作系统', 'description': '多AI员工协同工作、任务分配、知识共享'},
        {'id': 'ai_decision_support', 'name': '智能决策支持系统', 'description': '数据驱动决策、趋势预测、风险评估'},
        {'id': 'ai_learning', 'name': 'AI智能学习系统', 'description': '智能学习路径、自适应学习'},
        {'id': 'ai_tutor', 'name': 'AI辅导助手系统', 'description': '个性化辅导、学习建议'},
        {'id': 'ai_warning', 'name': 'AI预警干预系统', 'description': '异常检测、风险预警、自动干预'},
        {'id': 'ai_knowledge_graph', 'name': 'AI知识图谱系统', 'description': '知识关联、语义搜索、智能问答'},
        {'id': 'ai_question_generation', 'name': 'AI题目生成系统', 'description': '智能出题、题目质量评估'},
        {'id': 'ai_learning_planning', 'name': 'AI学习规划系统', 'description': '艾宾浩斯遗忘曲线、复习计划'},
        {'id': 'mobile_app', 'name': '移动端管理系统', 'description': '设备管理、推送通知、移动端适配'},
        {'id': 'exam_system', 'name': '考试系统', 'description': '在线考试、智能监考、成绩分析'},
        {'id': 'learning_system', 'name': '学习系统', 'description': '学习进度、课程管理、学习记录'},
        {'id': 'course_management', 'name': '课程管理系统', 'description': '课程创建、章节管理、学员报名'},
        {'id': 'homework_system', 'name': '作业系统', 'description': '作业布置、作业提交、AI批改'},
        {'id': 'notification_system', 'name': '消息通知系统', 'description': '站内消息、邮件通知、推送服务'},
        {'id': 'resource_management', 'name': '资源管理系统', 'description': '文件上传、资源分类、权限控制'},
        {'id': 'data_analysis', 'name': '数据分析系统', 'description': '数据可视化、智能报表、趋势分析'},
        {'id': 'security_monitor', 'name': '安全监控系统', 'description': '入侵检测、威胁分析、安全审计'},
        {'id': 'user_auth', 'name': '用户认证系统', 'description': '多因素认证、权限矩阵、用户分组'}
    ]
    
    def __init__(self):
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('version_unified.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subsystem_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subsystem_id TEXT NOT NULL UNIQUE,
                    subsystem_name TEXT NOT NULL,
                    current_version TEXT DEFAULT '1.0.0',
                    latest_version TEXT DEFAULT '1.0.0',
                    status TEXT DEFAULT 'up_to_date',
                    last_update TEXT DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    upgrade_notes TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS version_upgrades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    upgrade_id TEXT NOT NULL UNIQUE,
                    subsystem_id TEXT NOT NULL,
                    from_version TEXT NOT NULL,
                    to_version TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    upgrade_time TEXT,
                    completion_time TEXT,
                    operator TEXT,
                    notes TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS version_locks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subsystem_id TEXT NOT NULL UNIQUE,
                    locked_version TEXT,
                    locked_by TEXT,
                    locked_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT,
                    expires_at TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS version_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subsystem_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    change_type TEXT,
                    changes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    operator TEXT
                )
            ''')
            
            conn.commit()
            
            for subsystem in self.SUBSYSTEMS:
                cursor.execute('SELECT COUNT(*) FROM subsystem_versions WHERE subsystem_id = ?', (subsystem['id'],))
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO subsystem_versions
                        (subsystem_id, subsystem_name, description)
                        VALUES (?, ?, ?)
                    ''', (subsystem['id'], subsystem['name'], subsystem['description']))
            
            conn.commit()
            conn.close()
            logger.info("[Version Unified API] 数据库表创建完成")
        except Exception as e:
            logger.info(f"[Version Unified API] 创建表失败: {e}")
    
    def get_all_subsystem_versions(self):
        try:
            conn = sqlite3.connect('version_unified.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM subsystem_versions ORDER BY subsystem_name')
            rows = cursor.fetchall()
            conn.close()
            
            versions = []
            for row in rows:
                versions.append({
                    'subsystem_id': row[1],
                    'subsystem_name': row[2],
                    'current_version': row[3],
                    'latest_version': row[4],
                    'status': row[5],
                    'last_update': row[6],
                    'description': row[7],
                    'upgrade_notes': row[8]
                })
            
            return versions
        except Exception as e:
            logger.info(f"[Version Unified API] 获取所有子系统版本失败: {e}")
            return []
    
    def get_subsystem_version(self, subsystem_id):
        try:
            conn = sqlite3.connect('version_unified.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM subsystem_versions WHERE subsystem_id = ?', (subsystem_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'subsystem_id': row[1],
                    'subsystem_name': row[2],
                    'current_version': row[3],
                    'latest_version': row[4],
                    'status': row[5],
                    'last_update': row[6],
                    'description': row[7],
                    'upgrade_notes': row[8]
                }
            return None
        except Exception as e:
            logger.info(f"[Version Unified API] 获取子系统版本失败: {e}")
            return None
    
    def update_subsystem_version(self, subsystem_id, new_version, upgrade_notes='', operator='system'):
        try:
            conn = sqlite3.connect('version_unified.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT current_version FROM subsystem_versions WHERE subsystem_id = ?', (subsystem_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return {'error': '子系统不存在'}
            
            from_version = row[0]
            
            cursor.execute('''
                UPDATE subsystem_versions 
                SET current_version = ?, latest_version = ?, status = ?, 
                    last_update = ?, upgrade_notes = ?
                WHERE subsystem_id = ?
            ''', (new_version, new_version, 'up_to_date', datetime.now().isoformat(), upgrade_notes, subsystem_id))
            
            cursor.execute('''
                INSERT INTO version_upgrades
                (upgrade_id, subsystem_id, from_version, to_version, status, 
                 upgrade_time, completion_time, operator, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"UPG{datetime.now().strftime('%Y%m%d%H%M%S')}",
                subsystem_id,
                from_version,
                new_version,
                'completed',
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                operator,
                upgrade_notes
            ))
            
            cursor.execute('''
                INSERT INTO version_history
                (subsystem_id, version, change_type, changes, operator)
                VALUES (?, ?, ?, ?, ?)
            ''', (subsystem_id, new_version, 'upgrade', upgrade_notes, operator))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'subsystem_id': subsystem_id,
                'from_version': from_version,
                'to_version': new_version,
                'upgrade_notes': upgrade_notes
            }
        except Exception as e:
            logger.info(f"[Version Unified API] 更新子系统版本失败: {e}")
            return {'error': str(e)}
    
    def batch_upgrade(self, subsystem_ids, new_version, upgrade_notes='', operator='system'):
        results = []
        
        for subsystem_id in subsystem_ids:
            result = self.update_subsystem_version(subsystem_id, new_version, upgrade_notes, operator)
            results.append(result)
        
        return {
            'total': len(subsystem_ids),
            'success': sum(1 for r in results if r.get('success')),
            'failed': sum(1 for r in results if 'error' in r),
            'results': results
        }
    
    def rollback_subsystem(self, subsystem_id, target_version, operator='system'):
        try:
            conn = sqlite3.connect('version_unified.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT current_version FROM subsystem_versions WHERE subsystem_id = ?', (subsystem_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return {'error': '子系统不存在'}
            
            current_version = row[0]
            
            cursor.execute('''
                UPDATE subsystem_versions 
                SET current_version = ?, status = ?, last_update = ?
                WHERE subsystem_id = ?
            ''', (target_version, 'rollback', datetime.now().isoformat(), subsystem_id))
            
            cursor.execute('''
                INSERT INTO version_upgrades
                (upgrade_id, subsystem_id, from_version, to_version, status, 
                 upgrade_time, completion_time, operator, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"RLB{datetime.now().strftime('%Y%m%d%H%M%S')}",
                subsystem_id,
                current_version,
                target_version,
                'completed',
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                operator,
                '版本回滚'
            ))
            
            cursor.execute('''
                INSERT INTO version_history
                (subsystem_id, version, change_type, changes, operator)
                VALUES (?, ?, ?, ?, ?)
            ''', (subsystem_id, target_version, 'rollback', f'回滚至 {target_version}', operator))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'subsystem_id': subsystem_id,
                'from_version': current_version,
                'to_version': target_version
            }
        except Exception as e:
            logger.info(f"[Version Unified API] 回滚子系统版本失败: {e}")
            return {'error': str(e)}
    
    def lock_subsystem(self, subsystem_id, locked_version, reason='', operator='system'):
        try:
            conn = sqlite3.connect('version_unified.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO version_locks
                (subsystem_id, locked_version, locked_by, locked_at, reason, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                subsystem_id,
                locked_version,
                operator,
                datetime.now().isoformat(),
                reason,
                (datetime.now() + __import__('datetime').timedelta(days=30)).isoformat()
            ))
            
            cursor.execute('UPDATE subsystem_versions SET status = "locked" WHERE subsystem_id = ?', (subsystem_id,))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'subsystem_id': subsystem_id, 'locked_version': locked_version}
        except Exception as e:
            logger.info(f"[Version Unified API] 锁定子系统失败: {e}")
            return {'error': str(e)}
    
    def unlock_subsystem(self, subsystem_id):
        try:
            conn = sqlite3.connect('version_unified.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM version_locks WHERE subsystem_id = ?', (subsystem_id,))
            cursor.execute('UPDATE subsystem_versions SET status = "up_to_date" WHERE subsystem_id = ?', (subsystem_id,
            ))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'subsystem_id': subsystem_id}
        except Exception as e:
            logger.info(f"[Version Unified API] 解锁子系统失败: {e}")
            return {'error': str(e)}
    
    def get_subsystem_locks(self):
        try:
            conn = sqlite3.connect('version_unified.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM version_locks')
            rows = cursor.fetchall()
            conn.close()
            
            locks = []
            for row in rows:
                locks.append({
                    'subsystem_id': row[1],
                    'locked_version': row[2],
                    'locked_by': row[3],
                    'locked_at': row[4],
                    'reason': row[5],
                    'expires_at': row[6]
                })
            
            return locks
        except Exception as e:
            logger.info(f"[Version Unified API] 获取子系统锁定状态失败: {e}")
            return []
    
    def get_version_upgrade_history(self, subsystem_id=None):
        try:
            conn = sqlite3.connect('version_unified.db')
            cursor = conn.cursor()
            
            if subsystem_id:
                cursor.execute('SELECT * FROM version_upgrades WHERE subsystem_id = ? ORDER BY upgrade_time DESC',
                (subsystem_id,))
            else:
                cursor.execute('SELECT * FROM version_upgrades ORDER BY upgrade_time DESC')
            
            rows = cursor.fetchall()
            conn.close()
            
            history = []
            for row in rows:
                history.append({
                    'upgrade_id': row[1],
                    'subsystem_id': row[2],
                    'from_version': row[3],
                    'to_version': row[4],
                    'status': row[5],
                    'upgrade_time': row[6],
                    'completion_time': row[7],
                    'operator': row[8],
                    'notes': row[9]
                })
            
            return history
        except Exception as e:
            logger.info(f"[Version Unified API] 获取版本升级历史失败: {e}")
            return []
    
    def get_version_summary(self):
        try:
            conn = sqlite3.connect('version_unified.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM subsystem_versions')
            total_subsystems = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM subsystem_versions WHERE status = "up_to_date"')
            up_to_date = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM subsystem_versions WHERE status = "locked"')
            locked = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM version_upgrades')
            total_upgrades = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM version_upgrades WHERE status = "completed"')
            completed_upgrades = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_subsystems': total_subsystems,
                'up_to_date': up_to_date,
                'locked': locked,
                'total_upgrades': total_upgrades,
                'completed_upgrades': completed_upgrades,
                'upgrade_success_rate': (completed_upgrades / total_upgrades * 100) if total_upgrades > 0 else 0
            }
        except Exception as e:
            logger.info(f"[Version Unified API] 获取版本摘要失败: {e}")
            return {}

version_manager = VersionUnifiedManager()

@version_unified_api.route('/api/version/subsystems', methods=['GET'])
@require_login
def get_subsystems():
    result = version_manager.get_all_subsystem_versions()
    return jsonify({'success': True, 'data': result})

@version_unified_api.route('/api/version/subsystems/<subsystem_id>', methods=['GET'])
@require_login
def get_subsystem(subsystem_id):
    result = version_manager.get_subsystem_version(subsystem_id)
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': '子系统不存在'}), 404

@version_unified_api.route('/api/version/subsystems/<subsystem_id>', methods=['PUT'])
@require_admin
def update_subsystem(subsystem_id):
    data = request.get_json() or {}
    new_version = data.get('version')
    upgrade_notes = data.get('notes', '')
    
    if not new_version:
        return jsonify({'success': False, 'error': '版本号不能为空'}), 400
    
    result = version_manager.update_subsystem_version(subsystem_id, new_version, upgrade_notes)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@version_unified_api.route('/api/version/batch_upgrade', methods=['POST'])
@require_admin
def batch_upgrade():
    data = request.get_json() or {}
    subsystem_ids = data.get('subsystem_ids', [])
    new_version = data.get('version')
    upgrade_notes = data.get('notes', '')
    
    if not subsystem_ids or not new_version:
        return jsonify({'success': False, 'error': '子系统列表和版本号不能为空'}), 400
    
    result = version_manager.batch_upgrade(subsystem_ids, new_version, upgrade_notes)
    return jsonify({'success': True, 'data': result})

@version_unified_api.route('/api/version/subsystems/<subsystem_id>/rollback', methods=['POST'])
@require_admin
def rollback_subsystem(subsystem_id):
    data = request.get_json() or {}
    target_version = data.get('target_version')
    
    if not target_version:
        return jsonify({'success': False, 'error': '目标版本号不能为空'}), 400
    
    result = version_manager.rollback_subsystem(subsystem_id, target_version)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@version_unified_api.route('/api/version/subsystems/<subsystem_id>/lock', methods=['POST'])
@require_admin
def lock_subsystem(subsystem_id):
    data = request.get_json() or {}
    locked_version = data.get('locked_version')
    reason = data.get('reason', '')
    
    if not locked_version:
        return jsonify({'success': False, 'error': '锁定版本号不能为空'}), 400
    
    result = version_manager.lock_subsystem(subsystem_id, locked_version, reason)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@version_unified_api.route('/api/version/subsystems/<subsystem_id>/unlock', methods=['POST'])
@require_admin
def unlock_subsystem(subsystem_id):
    result = version_manager.unlock_subsystem(subsystem_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@version_unified_api.route('/api/version/locks', methods=['GET'])
@require_login
def get_locks():
    result = version_manager.get_subsystem_locks()
    return jsonify({'success': True, 'data': result})

@version_unified_api.route('/api/version/history', methods=['GET'])
@require_login
def get_history():
    subsystem_id = request.args.get('subsystem_id')
    result = version_manager.get_version_upgrade_history(subsystem_id)
    return jsonify({'success': True, 'data': result})

@version_unified_api.route('/api/version/summary', methods=['GET'])
@require_login
def get_summary():
    result = version_manager.get_version_summary()
    return jsonify({'success': True, 'data': result})