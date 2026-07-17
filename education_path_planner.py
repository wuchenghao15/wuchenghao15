#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育路径规划服务 (v15.1.0)
===================================
为成人教育和K12学生提供个性化学习路径规划，基于知识点前置关系、
学习目标和学习进度生成最优学习路径。

核心能力：
1. 知识点前置关系图 - 学习顺序依赖管理
2. 个性化路径生成 - 基于目标和现状生成学习路径
3. 学习进度追踪 - 按里程碑追踪进度
4. 路径调整建议 - 根据表现动态调整路径
5. 多目标路径融合 - 同时支持多个学习目标的路径规划
6. 路径模板库 - 预设常见学习路径模板
7. 学习里程碑 - 关键节点检查和阶段评估
"""
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_path_planner.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationPathPlanner')


# ========== 路径模板 ==========

PATH_TEMPLATES = {
    # 成人教育路径模板
    'adult_japanese_n5_to_n3': {
        'name': '日语N5到N3进阶路径',
        'education_type': 'adult',
        'target': '通过JLPT N3',
        'estimated_weeks': 24,
        'milestones': [
            {'name': 'N5基础', 'weeks': 4, 'focus': '假名、基础语法'},
            {'name': 'N5词汇', 'weeks': 4, 'focus': '800词汇量'},
            {'name': 'N4语法', 'weeks': 6, 'focus': '中级语法'},
            {'name': 'N4词汇', 'weeks': 4, 'focus': '1500词汇量'},
            {'name': 'N3冲刺', 'weeks': 6, 'focus': '综合训练+模拟题'}
        ]
    },
    'adult_japanese_n3_to_n2': {
        'name': '日语N3到N2进阶路径',
        'education_type': 'adult',
        'target': '通过JLPT N2',
        'estimated_weeks': 20,
        'milestones': [
            {'name': 'N3巩固', 'weeks': 4, 'focus': '复习N3知识点'},
            {'name': 'N2语法', 'weeks': 6, 'focus': '高级语法'},
            {'name': 'N2词汇', 'weeks': 4, 'focus': '4000词汇量'},
            {'name': '阅读强化', 'weeks': 3, 'focus': '长文阅读理解'},
            {'name': '听力强化', 'weeks': 3, 'focus': '听力训练'}
        ]
    },
    'adult_math_upgrade': {
        'name': '成人数学提升路径',
        'education_type': 'adult',
        'target': '达到高中数学水平',
        'estimated_weeks': 16,
        'milestones': [
            {'name': '基础运算', 'weeks': 3, 'focus': '四则运算、分数、小数'},
            {'name': '代数基础', 'weeks': 4, 'focus': '方程、不等式'},
            {'name': '函数', 'weeks': 4, 'focus': '一次/二次函数'},
            {'name': '几何', 'weeks': 3, 'focus': '平面几何基础'},
            {'name': '综合应用', 'weeks': 2, 'focus': '综合题训练'}
        ]
    },
    # K12路径模板
    'k12_junior_math': {
        'name': '初中数学完整路径',
        'education_type': 'k12',
        'target': '初中数学全部知识点',
        'estimated_weeks': 36,
        'milestones': [
            {'name': '七年级上', 'weeks': 10, 'focus': '有理数、一元一次方程'},
            {'name': '七年级下', 'weeks': 10, 'focus': '二元一次方程组、不等式'},
            {'name': '八年级上', 'weeks': 8, 'focus': '三角形、一次函数'},
            {'name': '八年级下', 'weeks': 8, 'focus': '二次根式、四边形'}
        ]
    },
    'k12_junior_english': {
        'name': '初中英语完整路径',
        'education_type': 'k12',
        'target': '初中英语全部知识点',
        'estimated_weeks': 36,
        'milestones': [
            {'name': '七年级词汇', 'weeks': 10, 'focus': '基础800词'},
            {'name': '七年级语法', 'weeks': 8, 'focus': '时态、句型'},
            {'name': '八年级词汇', 'weeks': 10, 'focus': '扩展1500词'},
            {'name': '八年级语法', 'weeks': 8, 'focus': '从句、被动语态'}
        ]
    },
    'k12_senior_physics': {
        'name': '高中物理路径',
        'education_type': 'k12',
        'target': '高中物理核心知识点',
        'estimated_weeks': 32,
        'milestones': [
            {'name': '运动学', 'weeks': 6, 'focus': '直线运动、牛顿定律'},
            {'name': '力学', 'weeks': 8, 'focus': '万有引力、功和能'},
            {'name': '电磁学', 'weeks': 10, 'focus': '电场、磁场、电磁感应'},
            {'name': '光学热学', 'weeks': 4, 'focus': '几何光学、热力学'},
            {'name': '近代物理', 'weeks': 4, 'focus': '波粒二象性、原子物理'}
        ]
    }
}

# 路径状态
PATH_STATUS = {
    'planning': '规划中',
    'active': '进行中',
    'paused': '已暂停',
    'completed': '已完成',
    'abandoned': '已放弃'
}


class EducationPathPlanner:
    """教育路径规划服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 学习路径表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_paths (
                        path_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        education_type TEXT NOT NULL,
                        path_name TEXT,
                        target TEXT,
                        template_id TEXT,
                        estimated_weeks INTEGER,
                        current_milestone INTEGER DEFAULT 0,
                        total_milestones INTEGER DEFAULT 0,
                        progress REAL DEFAULT 0,
                        status TEXT DEFAULT 'planning',
                        start_date TEXT,
                        expected_end_date TEXT,
                        actual_end_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 路径里程碑表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS path_milestones (
                        milestone_id TEXT PRIMARY KEY,
                        path_id TEXT NOT NULL,
                        order_index INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        focus TEXT,
                        estimated_weeks INTEGER,
                        status TEXT DEFAULT 'pending',
                        started_at TEXT,
                        completed_at TEXT,
                        accuracy REAL,
                        notes TEXT
                    )
                ''')
                # 知识点前置关系表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_prerequisites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        point_id TEXT NOT NULL,
                        prerequisite_point_id TEXT NOT NULL,
                        required_mastery REAL DEFAULT 0.6,
                        UNIQUE(point_id, prerequisite_point_id)
                    )
                ''')
                # 路径调整记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS path_adjustments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        path_id TEXT NOT NULL,
                        adjustment_type TEXT,
                        reason TEXT,
                        old_value TEXT,
                        new_value TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育路径规划服务数据库初始化完成')
        except Exception as e:
            logger.error(f'初始化数据库失败: {e}')

    # ========== 路径创建 ==========

    def create_path_from_template(self, user_id: int, education_type: str,
                                    template_id: str,
                                    path_name: str = None) -> Dict[str, Any]:
        """从模板创建学习路径"""
        with self._lock:
            template = PATH_TEMPLATES.get(template_id)
            if not template:
                return {'success': False, 'error': f'未知模板: {template_id}'}
            if template['education_type'] != education_type:
                return {'success': False, 'error': '模板教育类型不匹配'}

            path_id = f'path_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}'
            now = datetime.now().isoformat()
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(weeks=template['estimated_weeks'])).strftime('%Y-%m-%d')

            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    # 创建路径
                    cursor.execute('''
                        INSERT INTO education_paths
                        (path_id, user_id, education_type, path_name, target,
                         template_id, estimated_weeks, current_milestone, total_milestones,
                         progress, status, start_date, expected_end_date, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, 0, 'active', ?, ?, ?, ?)
                    ''', (path_id, user_id, education_type,
                          path_name or template['name'],
                          template['target'],
                          template_id,
                          template['estimated_weeks'],
                          len(template['milestones']),
                          start_date, end_date, now, now))

                    # 创建里程碑
                    for idx, milestone in enumerate(template['milestones']):
                        milestone_id = f'ms_{path_id}_{idx}'
                        cursor.execute('''
                            INSERT INTO path_milestones
                            (milestone_id, path_id, order_index, name, focus,
                             estimated_weeks, status)
                            VALUES (?, ?, ?, ?, ?, ?, 'pending')
                        ''', (milestone_id, path_id, idx,
                              milestone['name'], milestone['focus'],
                              milestone['weeks']))
                    conn.commit()

                logger.info(f'创建学习路径: {path_id} (用户 {user_id}, 模板 {template_id})')
                return {
                    'success': True,
                    'path_id': path_id,
                    'path_name': path_name or template['name'],
                    'target': template['target'],
                    'estimated_weeks': template['estimated_weeks'],
                    'total_milestones': len(template['milestones']),
                    'start_date': start_date,
                    'expected_end_date': end_date,
                    'milestones': template['milestones']
                }
            except Exception as e:
                logger.error(f'创建路径失败: {e}')
                return {'success': False, 'error': str(e)}

    def create_custom_path(self, user_id: int, education_type: str,
                             path_name: str, target: str,
                             milestones: List[Dict]) -> Dict[str, Any]:
        """创建自定义学习路径"""
        with self._lock:
            if not milestones:
                return {'success': False, 'error': '里程碑不能为空'}

            path_id = f'path_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}'
            now = datetime.now().isoformat()
            total_weeks = sum(m.get('weeks', 1) for m in milestones)
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(weeks=total_weeks)).strftime('%Y-%m-%d')

            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_paths
                        (path_id, user_id, education_type, path_name, target,
                         template_id, estimated_weeks, current_milestone, total_milestones,
                         progress, status, start_date, expected_end_date, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, NULL, ?, 0, ?, 0, 'active', ?, ?, ?, ?)
                    ''', (path_id, user_id, education_type, path_name, target,
                          total_weeks, len(milestones),
                          start_date, end_date, now, now))

                    for idx, milestone in enumerate(milestones):
                        milestone_id = f'ms_{path_id}_{idx}'
                        cursor.execute('''
                            INSERT INTO path_milestones
                            (milestone_id, path_id, order_index, name, focus,
                             estimated_weeks, status)
                            VALUES (?, ?, ?, ?, ?, ?, 'pending')
                        ''', (milestone_id, path_id, idx,
                              milestone.get('name', f'阶段{idx+1}'),
                              milestone.get('focus', ''),
                              milestone.get('weeks', 1)))
                    conn.commit()

                logger.info(f'创建自定义路径: {path_id}')
                return {
                    'success': True,
                    'path_id': path_id,
                    'path_name': path_name,
                    'target': target,
                    'estimated_weeks': total_weeks,
                    'total_milestones': len(milestones),
                    'start_date': start_date,
                    'expected_end_date': end_date
                }
            except Exception as e:
                logger.error(f'创建自定义路径失败: {e}')
                return {'success': False, 'error': str(e)}

    # ========== 里程碑管理 ==========

    def start_milestone(self, path_id: str, milestone_index: int) -> Dict[str, Any]:
        """开始里程碑"""
        with self._lock:
            try:
                now = datetime.now().isoformat()
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    # 标记里程碑为进行中
                    cursor.execute('''
                        UPDATE path_milestones
                        SET status = 'in_progress', started_at = ?
                        WHERE path_id = ? AND order_index = ? AND status = 'pending'
                    ''', (now, path_id, milestone_index))
                    if cursor.rowcount == 0:
                        return {'success': False, 'error': '里程碑不存在或状态不允许'}

                    # 更新路径当前里程碑
                    cursor.execute('''
                        UPDATE education_paths
                        SET current_milestone = ?, updated_at = ?
                        WHERE path_id = ?
                    ''', (milestone_index, now, path_id))
                    conn.commit()

                logger.info(f'路径 {path_id} 开始里程碑 {milestone_index}')
                return {
                    'success': True,
                    'path_id': path_id,
                    'milestone_index': milestone_index,
                    'started_at': now
                }
            except Exception as e:
                logger.error(f'开始里程碑失败: {e}')
                return {'success': False, 'error': str(e)}

    def complete_milestone(self, path_id: str, milestone_index: int,
                             accuracy: float = 0.0,
                             notes: str = '') -> Dict[str, Any]:
        """完成里程碑"""
        with self._lock:
            try:
                now = datetime.now().isoformat()
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    # 标记里程碑完成
                    cursor.execute('''
                        UPDATE path_milestones
                        SET status = 'completed', completed_at = ?, accuracy = ?, notes = ?
                        WHERE path_id = ? AND order_index = ? AND status IN ('pending', 'in_progress')
                    ''', (now, accuracy, notes, path_id, milestone_index))
                    if cursor.rowcount == 0:
                        return {'success': False, 'error': '里程碑不存在或状态不允许'}

                    # 获取总里程碑数
                    cursor.execute('SELECT total_milestones FROM education_paths WHERE path_id = ?',
                                    (path_id,))
                    row = cursor.fetchone()
                    total = row[0] if row else 1

                    # 计算进度
                    cursor.execute('''
                        SELECT COUNT(*) FROM path_milestones
                        WHERE path_id = ? AND status = 'completed'
                    ''', (path_id,))
                    completed = cursor.fetchone()[0]
                    progress = completed / total if total > 0 else 0

                    # 更新路径
                    next_milestone = milestone_index + 1
                    status = 'completed' if progress >= 1.0 else 'active'
                    actual_end = now if status == 'completed' else None
                    cursor.execute('''
                        UPDATE education_paths
                        SET progress = ?, status = ?,
                            actual_end_date = COALESCE(?, actual_end_date),
                            updated_at = ?
                        WHERE path_id = ?
                    ''', (progress, status, actual_end, now, path_id))
                    conn.commit()

                logger.info(f'路径 {path_id} 完成里程碑 {milestone_index} (进度: {progress:.0%})')
                return {
                    'success': True,
                    'path_id': path_id,
                    'milestone_index': milestone_index,
                    'completed_at': now,
                    'progress': round(progress, 4),
                    'path_status': status,
                    'next_milestone': next_milestone if status != 'completed' else None
                }
            except Exception as e:
                logger.error(f'完成里程碑失败: {e}')
                return {'success': False, 'error': str(e)}

    # ========== 路径查询 ==========

    def get_path_detail(self, path_id: str) -> Dict[str, Any]:
        """获取路径详情"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT path_id, user_id, education_type, path_name, target,
                           template_id, estimated_weeks, current_milestone,
                           total_milestones, progress, status, start_date,
                           expected_end_date, actual_end_date, created_at
                    FROM education_paths WHERE path_id = ?
                ''', (path_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '路径不存在'}

                cursor.execute('''
                    SELECT milestone_id, order_index, name, focus, estimated_weeks,
                           status, started_at, completed_at, accuracy, notes
                    FROM path_milestones
                    WHERE path_id = ?
                    ORDER BY order_index
                ''', (path_id,))
                ms_rows = cursor.fetchall()

            milestones = []
            for ms_row in ms_rows:
                milestones.append({
                    'milestone_id': ms_row[0],
                    'order_index': ms_row[1],
                    'name': ms_row[2],
                    'focus': ms_row[3],
                    'estimated_weeks': ms_row[4],
                    'status': ms_row[5],
                    'started_at': ms_row[6],
                    'completed_at': ms_row[7],
                    'accuracy': ms_row[8],
                    'notes': ms_row[9]
                })

            return {
                'success': True,
                'path': {
                    'path_id': row[0],
                    'user_id': row[1],
                    'education_type': row[2],
                    'path_name': row[3],
                    'target': row[4],
                    'template_id': row[5],
                    'estimated_weeks': row[6],
                    'current_milestone': row[7],
                    'total_milestones': row[8],
                    'progress': row[9],
                    'status': row[10],
                    'status_name': PATH_STATUS.get(row[10], row[10]),
                    'start_date': row[11],
                    'expected_end_date': row[12],
                    'actual_end_date': row[13],
                    'created_at': row[14]
                },
                'milestones': milestones
            }
        except Exception as e:
            logger.error(f'获取路径详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_user_paths(self, user_id: int, status: str = None) -> Dict[str, Any]:
        """列出用户路径"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                sql = '''SELECT path_id, education_type, path_name, target,
                                estimated_weeks, current_milestone, total_milestones,
                                progress, status, start_date, expected_end_date
                         FROM education_paths WHERE user_id = ?'''
                params = [user_id]
                if status:
                    sql += ' AND status = ?'
                    params.append(status)
                sql += ' ORDER BY created_at DESC'
                cursor.execute(sql, params)
                rows = cursor.fetchall()

            paths = []
            for row in rows:
                paths.append({
                    'path_id': row[0],
                    'education_type': row[1],
                    'path_name': row[2],
                    'target': row[3],
                    'estimated_weeks': row[4],
                    'current_milestone': row[5],
                    'total_milestones': row[6],
                    'progress': row[7],
                    'status': row[8],
                    'status_name': PATH_STATUS.get(row[8], row[8]),
                    'start_date': row[9],
                    'expected_end_date': row[10]
                })
            return {'success': True, 'paths': paths, 'count': len(paths)}
        except Exception as e:
            logger.error(f'列出用户路径失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 路径调整 ==========

    def adjust_path(self, path_id: str, adjustment_type: str,
                      reason: str, old_value: Any, new_value: Any) -> Dict[str, Any]:
        """记录路径调整"""
        with self._lock:
            now = datetime.now().isoformat()
            try:
                with self._get_connection() as conn:
                    conn.execute('''
                        INSERT INTO path_adjustments
                        (path_id, adjustment_type, reason, old_value, new_value, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (path_id, adjustment_type, reason,
                          json.dumps(old_value, ensure_ascii=False),
                          json.dumps(new_value, ensure_ascii=False), now))
                    conn.commit()
                logger.info(f'路径 {path_id} 调整: {adjustment_type} ({reason})')
                return {'success': True, 'path_id': path_id, 'adjustment_type': adjustment_type}
            except Exception as e:
                logger.error(f'记录调整失败: {e}')
                return {'success': False, 'error': str(e)}

    def get_adjustment_suggestions(self, path_id: str) -> Dict[str, Any]:
        """获取路径调整建议"""
        try:
            path_detail = self.get_path_detail(path_id)
            if not path_detail['success']:
                return path_detail

            path = path_detail['path']
            milestones = path_detail['milestones']

            suggestions = []
            current_idx = path['current_milestone']
            current_milestone = next((m for m in milestones if m['order_index'] == current_idx), None)

            if current_milestone:
                accuracy = current_milestone.get('accuracy', 0) or 0
                if accuracy > 0 and accuracy < 0.5:
                    suggestions.append({
                        'type': 'extend_time',
                        'priority': 'high',
                        'message': f'当前里程碑准确率({accuracy:.0%})偏低，建议延长学习时间',
                        'action': '增加1-2周学习时间'
                    })
                elif accuracy > 0.9:
                    suggestions.append({
                        'type': 'accelerate',
                        'priority': 'medium',
                        'message': f'当前里程碑准确率({accuracy:.0%})优秀，可考虑加速',
                        'action': '缩短下一里程碑时间'
                    })

            # 检查进度
            progress = path['progress']
            elapsed_days = (datetime.now() - datetime.fromisoformat(path['start_date'])).days
            expected_days = path['estimated_weeks'] * 7
            if expected_days > 0:
                expected_progress = elapsed_days / expected_days
                if progress < expected_progress - 0.1:
                    suggestions.append({
                        'type': 'behind_schedule',
                        'priority': 'high',
                        'message': f'进度落后(实际{progress:.0%} vs 预期{expected_progress:.0%})',
                        'action': '调整里程碑或增加学习强度'
                    })

            if not suggestions:
                suggestions.append({
                    'type': 'on_track',
                    'priority': 'low',
                    'message': '路径进度正常，按计划继续',
                    'action': '继续保持'
                })

            return {
                'success': True,
                'path_id': path_id,
                'current_progress': progress,
                'suggestions': suggestions
            }
        except Exception as e:
            logger.error(f'获取调整建议失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 模板查询 ==========

    def list_templates(self, education_type: str = None) -> Dict[str, Any]:
        """列出路径模板"""
        templates = []
        for tid, template in PATH_TEMPLATES.items():
            if education_type and template['education_type'] != education_type:
                continue
            templates.append({
                'template_id': tid,
                'name': template['name'],
                'education_type': template['education_type'],
                'target': template['target'],
                'estimated_weeks': template['estimated_weeks'],
                'milestone_count': len(template['milestones'])
            })
        return {
            'success': True,
            'templates': templates,
            'count': len(templates)
        }

    # ========== 统计 ==========

    def get_statistics(self) -> Dict[str, Any]:
        """获取路径规划统计"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM education_paths')
                total_paths = cursor.fetchone()[0]
                cursor.execute('SELECT status, COUNT(*) FROM education_paths GROUP BY status')
                status_stats = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.execute('SELECT education_type, COUNT(*) FROM education_paths GROUP BY education_type')
                type_stats = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM path_milestones WHERE status = "completed"')
                completed_milestones = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM path_milestones WHERE status = "in_progress"')
                active_milestones = cursor.fetchone()[0]
                cursor.execute('SELECT AVG(progress) FROM education_paths WHERE status = "active"')
                avg_progress = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM path_adjustments')
                total_adjustments = cursor.fetchone()[0]

            return {
                'success': True,
                'total_paths': total_paths,
                'by_status': status_stats,
                'by_education_type': type_stats,
                'completed_milestones': completed_milestones,
                'active_milestones': active_milestones,
                'avg_active_progress': round(avg_progress, 4),
                'total_adjustments': total_adjustments,
                'available_templates': len(PATH_TEMPLATES)
            }
        except Exception as e:
            logger.error(f'获取统计失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    planner = EducationPathPlanner()
    print('=' * 60)
    print('MTSCOS 教育路径规划服务 v15.1.0 测试')
    print('=' * 60)

    print('\n1. 列出模板...')
    r = planner.list_templates('adult')
    print(f'   成人模板数: {r.get("count", 0)}')
    for t in r.get('templates', []):
        print(f'   - {t["name"]} ({t["estimated_weeks"]}周)')

    print('\n2. 从模板创建路径...')
    r = planner.create_path_from_template(1001, 'adult', 'adult_japanese_n5_to_n3')
    print(f'   结果: {r["success"]} 路径ID: {r.get("path_id")}')
    path_id = r.get('path_id', '')

    print('\n3. 开始里程碑0...')
    r = planner.start_milestone(path_id, 0)
    print(f'   结果: {r["success"]}')

    print('\n4. 完成里程碑0...')
    r = planner.complete_milestone(path_id, 0, accuracy=0.85, notes='基础扎实')
    print(f'   结果: {r["success"]} 进度: {r.get("progress")}')

    print('\n5. 开始里程碑1...')
    r = planner.start_milestone(path_id, 1)
    print(f'   结果: {r["success"]}')

    print('\n6. 获取路径详情...')
    r = planner.get_path_detail(path_id)
    print(f'   里程碑数: {len(r.get("milestones", []))}')
    for ms in r.get('milestones', []):
        print(f'   - {ms["name"]}: {ms["status"]}')

    print('\n7. 获取调整建议...')
    r = planner.get_adjustment_suggestions(path_id)
    for s in r.get('suggestions', []):
        print(f'   - [{s["priority"]}] {s["message"]}')

    print('\n8. 创建自定义路径...')
    r = planner.create_custom_path(2001, 'k12', '初二数学冲刺', '期末考试',
                                     [{'name': '函数复习', 'weeks': 3, 'focus': '一次函数'},
                                      {'name': '几何证明', 'weeks': 2, 'focus': '三角形'},
                                      {'name': '综合模拟', 'weeks': 2, 'focus': '模拟题'}])
    print(f'   结果: {r["success"]} 路径ID: {r.get("path_id")}')

    print('\n9. 列出用户路径...')
    r = planner.list_user_paths(1001)
    print(f'   路径数: {r.get("count", 0)}')

    print('\n10. 统计...')
    stats = planner.get_statistics()
    print(f'   总路径: {stats.get("total_paths")} 已完成里程碑: {stats.get("completed_milestones")}')
    print(f'   平均进度: {stats.get("avg_active_progress")}')
    print('\n' + '=' * 60)
    print('测试完成')
    print('=' * 60)
