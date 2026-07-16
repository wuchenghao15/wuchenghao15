#!/usr/bin/env python3
"""
AI员工数据同步模块 - 将内存中的AI员工数据全部持久化到数据库
包括：员工基本信息、赋能数据（性格/学习/认证）、Agent注册、任务日志
"""
import logging
logger = logging.getLogger(__name__)
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List

DATABASE_PATH = 'app.db'


def ensure_empowerment_tables(conn):
    """创建赋能数据持久化表"""
    cursor = conn.cursor()

    # AI员工赋能数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_employee_empowerment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            employee_name TEXT,
            employee_type TEXT,
            personality_type TEXT,
            personality_traits TEXT,
            communication_style TEXT,
            current_emotion TEXT,
            energy_level REAL,
            interaction_count INTEGER DEFAULT 0,
            success_streak INTEGER DEFAULT 0,
            decision_count INTEGER DEFAULT 0,
            empowerment_enabled INTEGER DEFAULT 1,
            last_updated TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # AI员工学习数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_employee_learning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            domain TEXT,
            total_topics INTEGER,
            mastered_topics INTEGER,
            avg_proficiency REAL,
            total_learning_hours REAL,
            learning_streak INTEGER,
            last_learning_time TEXT,
            knowledge_base TEXT,
            learning_history TEXT,
            upgrade_status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(employee_id)
        )
    ''')

    # AI员工认证表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_employee_certifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            certification_name TEXT NOT NULL,
            avg_proficiency REAL,
            obtained_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(employee_id, certification_name)
        )
    ''')

    # AI员工情绪历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_employee_emotion_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            event TEXT,
            success INTEGER,
            old_emotion TEXT,
            new_emotion TEXT,
            energy REAL,
            timestamp TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    logger.info("✓ 赋能数据表已确保创建")


def sync_employee_to_db(conn, emp_id: str, emp: Any):
    """同步单个AI员工到数据库"""
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    # 1. 同步到 ai_employees 表
    emp_name = getattr(emp, 'name', '未知')
    emp_type = getattr(emp, 'type', getattr(emp, 'employee_type', getattr(emp, 'role', 'general')))
    emp_status = getattr(emp, 'status', 'active')
    emp_level = getattr(emp, 'level', getattr(emp, 'skill_level', 1))

    # 检查是否已存在
    cursor.execute('SELECT id FROM ai_employees WHERE name = ? OR employee_code = ?', (emp_name, emp_id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE ai_employees SET
                employee_code = ?, description = ?, capabilities = ?,
                status = ?, skill_level = ?, model_version = ?,
                is_enabled = 1, updated_at = ?
            WHERE id = ?
        ''', (
            emp_id, f'{emp_type} AI员工', json.dumps({'type': emp_type}, ensure_ascii=False),
            emp_status, emp_level, '2.0.0', now, existing[0]
        ))
    else:
        cursor.execute('''
            INSERT INTO ai_employees (
                name, employee_code, description, capabilities, specialties,
                status, accuracy, total_tasks, successful_fixes, failed_fixes,
                learning_rate, knowledge_base_size, last_training, model_version,
                is_enabled, priority, max_concurrent_tasks, skill_level, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            emp_name, emp_id, f'{emp_type} AI员工',
            json.dumps({'type': emp_type}, ensure_ascii=False),
            json.dumps([], ensure_ascii=False),
            emp_status, 0.95, 0, 0, 0, 0.8, 0, now, '2.0.0',
            1, 5, 3, emp_level, now, now
        ))

    # 2. 同步赋能数据
    if hasattr(emp, 'empowerment_enabled') and emp.empowerment_enabled:
        personality = getattr(emp, 'personality', None)
        learning_engine = getattr(emp, 'learning_engine', None)

        if personality:
            profile = personality.get_personality_profile()
            traits_json = json.dumps(profile.get('traits', {}), ensure_ascii=False)

            cursor.execute('''
                INSERT OR REPLACE INTO ai_employee_empowerment (
                    employee_id, employee_name, employee_type, personality_type,
                    personality_traits, communication_style, current_emotion,
                    energy_level, interaction_count, success_streak, decision_count,
                    empowerment_enabled, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                emp_id, emp_name, emp_type,
                profile.get('type', 'analytical'),
                traits_json,
                profile.get('communication_style', 'precise'),
                profile.get('current_emotion', {}).get('label', '平静'),
                profile.get('energy_level', 1.0),
                profile.get('interaction_count', 0),
                profile.get('success_streak', 0),
                len(getattr(emp, 'decision_history', [])),
                1, now
            ))

            # 同步情绪历史
            emotion_history = getattr(personality, 'emotion_history', [])
            for eh in emotion_history[-20:]:  # 最近20条
                cursor.execute('''
                    INSERT INTO ai_employee_emotion_log (
                        employee_id, event, success, old_emotion, new_emotion, energy, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    emp_id, eh.get('event', ''), 1 if eh.get('success') else 0,
                    eh.get('old_emotion', ''), eh.get('new_emotion', ''),
                    eh.get('energy', 1.0), eh.get('timestamp', now)
                ))

        if learning_engine:
            stats = learning_engine.get_learning_stats()
            knowledge_base = learning_engine.get_knowledge_base()
            history = learning_engine.get_learning_history(20)
            upgrade = learning_engine.auto_upgrade_check()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_employee_learning (
                    employee_id, domain, total_topics, mastered_topics,
                    avg_proficiency, total_learning_hours, learning_streak,
                    last_learning_time, knowledge_base, learning_history, upgrade_status, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                emp_id, stats.get('domain', 'general'),
                stats.get('total_topics', 0), stats.get('mastered_topics', 0),
                stats.get('avg_proficiency', 0), stats.get('total_learning_hours', 0),
                stats.get('learning_streak', 0), stats.get('last_learning_time'),
                json.dumps(knowledge_base, ensure_ascii=False),
                json.dumps(history, ensure_ascii=False),
                json.dumps(upgrade, ensure_ascii=False),
                now
            ))

            # 同步认证
            certs = getattr(learning_engine, 'certifications', [])
            for cert in certs:
                cursor.execute('''
                    INSERT OR IGNORE INTO ai_employee_certifications (
                        employee_id, certification_name, avg_proficiency, obtained_at
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    emp_id, cert.get('name', ''),
                    cert.get('avg_proficiency', 0), cert.get('obtained_at', now)
                ))

    conn.commit()


def sync_agent_to_db(conn, agent_id: str, agent_data: Dict):
    """同步AI Agent到agent_registry表"""
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    cursor.execute('''
        INSERT OR REPLACE INTO agent_registry (
            agent_id, agent_type, name, config_json, status, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        agent_id,
        agent_data.get('type', 'general'),
        agent_data.get('name', agent_id),
        json.dumps(agent_data.get('config', {}), ensure_ascii=False),
        agent_data.get('status', 'active'),
        now
    ))

    conn.commit()


def sync_all_employees(employees_dict: Dict[str, Any], db_path: str = None) -> Dict[str, Any]:
    """同步所有AI员工到数据库"""
    db_path = db_path or DATABASE_PATH
    conn = sqlite3.connect(db_path)

    try:
        ensure_empowerment_tables(conn)

        synced_count = 0
        empowerment_count = 0
        errors = []

        for emp_id, emp in employees_dict.items():
            try:
                sync_employee_to_db(conn, emp_id, emp)
                synced_count += 1
                if getattr(emp, 'empowerment_enabled', False):
                    empowerment_count += 1
            except Exception as e:
                errors.append(f'{emp_id}: {str(e)}')
                logger.error(f"同步员工 {emp_id} 失败: {e}")

        # 同步Agent状态
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT agent_id, name, description FROM ai_agents")
            agents = cursor.fetchall()
            for row in agents:
                sync_agent_to_db(conn, f'agent_{row[0]}', {
                    'name': row[1],
                    'type': 'ai_agent',
                    'status': 'active',
                    'config': {'description': row[2] or ''}
                })
        except Exception as e:
            logger.error(f"同步Agent失败: {e}")

        logger.info(f"✓ 数据同步完成: {synced_count}名员工, {empowerment_count}名已赋能")

        return {
            'success': True,
            'synced_employees': synced_count,
            'empowered_employees': empowerment_count,
            'errors': errors,
            'timestamp': datetime.now().isoformat()
        }
    finally:
        conn.close()


def get_sync_status(db_path: str = None) -> Dict[str, Any]:
    """获取数据库同步状态"""
    db_path = db_path or DATABASE_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    status = {}

    # 各表数据量
    tables_to_check = [
        'ai_employees', 'ai_employee_empowerment', 'ai_employee_learning',
        'ai_employee_certifications', 'ai_employee_emotion_log',
        'agent_registry', 'agent_state', 'ai_task_logs',
        'ai_agents', 'ai_employee_config', 'ai_cluster_employee',
        'users', 'system_settings', 'system_params', 'system_rules',
        'courses', 'questions', 'exams', 'notifications',
    ]

    for table in tables_to_check:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            status[table] = cursor.fetchone()[0]
        except:
            status[table] = '表不存在'

    # 赋能统计
    try:
        cursor.execute('SELECT COUNT(DISTINCT employee_id) FROM ai_employee_empowerment WHERE empowerment_enabled = 1')
        status['empowered_in_db'] = cursor.fetchone()[0]
    except:
        status['empowered_in_db'] = 0

    try:
        cursor.execute('SELECT COUNT(DISTINCT employee_id) FROM ai_employee_certifications')
        status['certified_in_db'] = cursor.fetchone()[0]
    except:
        status['certified_in_db'] = 0

    conn.close()
    return status


# ==================== 写穿机制：操作后立即持久化 ====================

def write_through_sync(emp_id: str, emp: Any, db_path: str = None):
    """写穿同步 - 单个员工操作后立即同步到数据库"""
    db_path = db_path or DATABASE_PATH
    try:
        conn = sqlite3.connect(db_path)
        sync_employee_to_db(conn, emp_id, emp)
        conn.close()
        return True
    except Exception as e:
        logger.error(f"写穿同步失败 {emp_id}: {e}")
        return False


# ==================== 数据库读取函数（前端调取数据源） ====================

def load_empowerment_overview_from_db(db_path: str = None) -> Dict[str, Any]:
    """从数据库读取所有AI员工赋能概览"""
    db_path = db_path or DATABASE_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT e.employee_id, e.employee_name, e.employee_type,
                   e.personality_type, e.current_emotion, e.energy_level,
                   e.interaction_count, e.success_streak, e.decision_count,
                   l.domain, l.total_topics, l.mastered_topics, l.avg_proficiency,
                   l.total_learning_hours, l.learning_streak, l.last_learning_time,
                   (SELECT COUNT(*) FROM ai_employee_certifications c WHERE c.employee_id = e.employee_id) as cert_count
            FROM ai_employee_empowerment e
            LEFT JOIN ai_employee_learning l ON e.employee_id = l.employee_id
            WHERE e.empowerment_enabled = 1
            ORDER BY e.employee_type, e.employee_name
        ''')
        rows = cursor.fetchall()

        profiles = []
        # 性格类型名称映射
        type_names = {
            'analytical': '分析型', 'creative': '创造型', 'supportive': '支持型',
            'driven': '进取型', 'cautious': '谨慎型',
        }
        type_emojis = {
            'analytical': '🔬', 'creative': '🎨', 'supportive': '🤝',
            'driven': '🚀', 'cautious': '🛡️',
        }

        for row in rows:
            ptype = row['personality_type'] or 'analytical'
            profiles.append({
                'enabled': True,
                'employee_id': row['employee_id'],
                'name': row['employee_name'],
                'type': row['employee_type'],
                'personality': {
                    'type': ptype,
                    'type_name': type_names.get(ptype, ptype),
                    'emoji': type_emojis.get(ptype, '🤖'),
                    'current_emotion': {'label': row['current_emotion'] or '平静'},
                    'energy_level': row['energy_level'] or 1.0,
                    'interaction_count': row['interaction_count'] or 0,
                    'success_streak': row['success_streak'] or 0,
                },
                'learning_stats': {
                    'domain': row['domain'] or 'general',
                    'total_topics': row['total_topics'] or 0,
                    'mastered_topics': row['mastered_topics'] or 0,
                    'avg_proficiency': row['avg_proficiency'] or 0,
                    'total_learning_hours': row['total_learning_hours'] or 0,
                    'learning_streak': row['learning_streak'] or 0,
                    'last_learning_time': row['last_learning_time'],
                },
                'knowledge_topics': row['total_topics'] or 0,
                'certifications': [],
                'cert_count': row['cert_count'] or 0,
                'decision_count': row['decision_count'] or 0,
            })

        total = len(profiles)
        total_certified = sum(p.get('cert_count', 0) for p in profiles)
        avg_energy = sum(p.get('personality', {}).get('energy_level', 0) for p in profiles) / total if total else 0
        total_knowledge = sum(p.get('knowledge_topics', 0) for p in profiles)

        return {
            'success': True,
            'total_employees': total,
            'total_registered': total,
            'total_certifications': total_certified,
            'avg_energy': round(avg_energy, 2),
            'total_knowledge_topics': total_knowledge,
            'profiles': profiles,
            'source': 'database',
        }
    except Exception as e:
        logger.error(f"从数据库读取赋能概览失败: {e}")
        return {'success': False, 'message': str(e), 'profiles': []}
    finally:
        conn.close()


def load_employee_detail_from_db(employee_id: str, db_path: str = None) -> Dict[str, Any]:
    """从数据库读取单个AI员工的完整赋能档案"""
    db_path = db_path or DATABASE_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 赋能数据
        cursor.execute('SELECT * FROM ai_employee_empowerment WHERE employee_id = ?', (employee_id,))
        emp_row = cursor.fetchone()
        if not emp_row:
            return {'success': False, 'message': '员工不存在'}

        # 学习数据
        cursor.execute('SELECT * FROM ai_employee_learning WHERE employee_id = ?', (employee_id,))
        learn_row = cursor.fetchone()

        # 认证数据
        cursor.execute('SELECT * FROM ai_employee_certifications WHERE employee_id = ?', (employee_id,))
        cert_rows = cursor.fetchall()

        # 情绪历史
        cursor.execute('SELECT * FROM ai_employee_emotion_log WHERE employee_id = ? ORDER BY id DESC LIMIT 20', (employee_id,))
        emotion_rows = cursor.fetchall()

        type_names = {
            'analytical': '分析型', 'creative': '创造型', 'supportive': '支持型',
            'driven': '进取型', 'cautious': '谨慎型',
        }
        type_emojis = {
            'analytical': '🔬', 'creative': '🎨', 'supportive': '🤝',
            'driven': '🚀', 'cautious': '🛡️',
        }

        ptype = emp_row['personality_type'] or 'analytical'
        traits = json.loads(emp_row['personality_traits'] or '{}')

        profile = {
            'enabled': True,
            'employee_id': emp_row['employee_id'],
            'name': emp_row['employee_name'],
            'type': emp_row['employee_type'],
            'personality': {
                'type': ptype,
                'type_name': type_names.get(ptype, ptype),
                'emoji': type_emojis.get(ptype, '🤖'),
                'traits': traits,
                'communication_style': emp_row['communication_style'],
                'current_emotion': {'label': emp_row['current_emotion']},
                'energy_level': emp_row['energy_level'],
                'interaction_count': emp_row['interaction_count'],
                'success_streak': emp_row['success_streak'],
            },
            'learning_stats': {},
            'knowledge_topics': 0,
            'certifications': [dict(c) for c in cert_rows],
            'decision_count': emp_row['decision_count'],
        }

        learning = {}
        if learn_row:
            knowledge_base = json.loads(learn_row['knowledge_base'] or '[]')
            history = json.loads(learn_row['learning_history'] or '[]')
            upgrade = json.loads(learn_row['upgrade_status'] or '{}')

            profile['knowledge_topics'] = learn_row['total_topics'] or 0
            profile['learning_stats'] = {
                'domain': learn_row['domain'],
                'total_topics': learn_row['total_topics'],
                'mastered_topics': learn_row['mastered_topics'],
                'avg_proficiency': learn_row['avg_proficiency'],
                'total_learning_hours': learn_row['total_learning_hours'],
                'learning_streak': learn_row['learning_streak'],
                'last_learning_time': learn_row['last_learning_time'],
            }

            learning = {
                'stats': profile['learning_stats'],
                'knowledge_base': knowledge_base,
                'recent_history': history,
                'upgrade_status': upgrade,
                'certifications': [dict(c) for c in cert_rows],
            }

        emotions = [dict(e) for e in emotion_rows]

        return {
            'success': True,
            'profile': profile,
            'personality': profile['personality'],
            'learning': learning,
            'emotion_history': emotions,
            'source': 'database',
        }
    except Exception as e:
        logger.error(f"从数据库读取员工详情失败: {e}")
        return {'success': False, 'message': str(e)}
    finally:
        conn.close()


def log_task_to_db(task_type: str, task_data: Dict, status: str, result: Dict, db_path: str = None):
    """记录任务日志到数据库"""
    db_path = db_path or DATABASE_PATH
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO ai_task_logs (task_type, task_data, status, result, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            task_type,
            json.dumps(task_data, ensure_ascii=False)[:2000],
            status,
            json.dumps(result, ensure_ascii=False)[:2000],
            now, now
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"任务日志写入失败: {e}")
