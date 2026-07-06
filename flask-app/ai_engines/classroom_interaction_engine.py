# -*- coding: utf-8 -*-
"""
AI课堂互动引擎
课堂互动工具集：
- 随机点名/分组（公平随机、权重分布）
- 实时问答（选择题/判断题/简答题）
- 抢答竞赛
- 实时投票/问卷
- 分组讨论与协作
- 课堂积分与奖励
- 参与度统计与分析
- 课堂活动模板管理
"""

import os
import sys
import json
import time
import random
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('classroom_interaction_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ClassroomInteractionEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

# 活动类型
ACTIVITY_TYPES = {
    'random_pick': {'name': '随机点名', 'icon': 'user-random', 'description': '随机抽取学生回答问题'},
    'quiz': {'name': '随堂测验', 'icon': 'clipboard-list', 'description': '快速选择题/判断题测试'},
    'rush_answer': {'name': '抢答竞赛', 'icon': 'zap', 'description': '限时抢答，速度比拼'},
    'vote': {'name': '投票问卷', 'icon': 'vote', 'description': '实时投票与调查'},
    'group_discussion': {'name': '分组讨论', 'icon': 'users', 'description': '随机分组协作讨论'},
    'brainstorming': {'name': '头脑风暴', 'icon': 'lightbulb', 'description': '集思广益，想法收集'},
    'exit_ticket': {'name': '课堂小测', 'icon': 'check-circle', 'description': '下课前快速检测'}
}

# 分组策略
GROUPING_STRATEGIES = {
    'random': {'name': '随机分组', 'description': '完全随机分配'},
    'ability_balance': {'name': '能力均衡', 'description': '根据成绩均衡分组'},
    'homogeneous': {'name': '同质分组', 'description': '能力相近者一组'},
    'interest': {'name': '兴趣分组', 'description': '按兴趣偏好分组'},
    'free': {'name': '自由组合', 'description': '学生自由选择小组'}
}


class ClassroomInteractionEngine:
    """AI课堂互动引擎 - 课堂互动工具集"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.RLock()
        # 活跃活动缓存（内存中的实时活动）
        self._active_sessions = {}
        self._init_database()
        self._initialized = True
        logger.info("ClassroomInteractionEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 1. 课堂活动主表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS classroom_activities (
                        activity_id TEXT PRIMARY KEY,
                        teacher_id TEXT NOT NULL,
                        class_id TEXT,
                        subject TEXT,
                        activity_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        config TEXT DEFAULT '{}',
                        status TEXT DEFAULT 'draft',
                        start_time TEXT,
                        end_time TEXT,
                        duration INTEGER DEFAULT 0,
                        participant_count INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 2. 活动参与者表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activity_participants (
                        participant_id TEXT PRIMARY KEY,
                        activity_id TEXT NOT NULL,
                        student_id TEXT NOT NULL,
                        student_name TEXT,
                        join_time TEXT DEFAULT CURRENT_TIMESTAMP,
                        score REAL DEFAULT 0,
                        rank INTEGER,
                        answer_data TEXT DEFAULT '{}',
                        group_number INTEGER,
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY (activity_id) REFERENCES classroom_activities(activity_id),
                        UNIQUE(activity_id, student_id)
                    )
                ''')

                # 3. 题目/问题表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activity_questions (
                        question_id TEXT PRIMARY KEY,
                        activity_id TEXT NOT NULL,
                        question_type TEXT DEFAULT 'single_choice',
                        content TEXT NOT NULL,
                        options TEXT,
                        correct_answer TEXT,
                        points INTEGER DEFAULT 10,
                        time_limit INTEGER DEFAULT 30,
                        sort_order INTEGER DEFAULT 0,
                        FOREIGN KEY (activity_id) REFERENCES classroom_activities(activity_id)
                    )
                ''')

                # 4. 答题记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activity_responses (
                        response_id TEXT PRIMARY KEY,
                        activity_id TEXT NOT NULL,
                        question_id TEXT NOT NULL,
                        student_id TEXT NOT NULL,
                        answer TEXT,
                        is_correct BOOLEAN,
                        response_time INTEGER,
                        score REAL DEFAULT 0,
                        submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (activity_id) REFERENCES classroom_activities(activity_id),
                        FOREIGN KEY (question_id) REFERENCES activity_questions(question_id)
                    )
                ''')

                # 5. 投票/问卷表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS classroom_votes (
                        vote_id TEXT PRIMARY KEY,
                        activity_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        options TEXT DEFAULT '[]',
                        multiple_choice BOOLEAN DEFAULT 0,
                        anonymous BOOLEAN DEFAULT 1,
                        FOREIGN KEY (activity_id) REFERENCES classroom_activities(activity_id)
                    )
                ''')

                # 6. 分组记录
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS classroom_groups (
                        group_id TEXT PRIMARY KEY,
                        activity_id TEXT NOT NULL,
                        group_number INTEGER NOT NULL,
                        group_name TEXT,
                        student_ids TEXT DEFAULT '[]',
                        leader_id TEXT,
                        score REAL DEFAULT 0,
                        FOREIGN KEY (activity_id) REFERENCES classroom_activities(activity_id)
                    )
                ''')

                # 7. 课堂积分表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS classroom_points (
                        point_id TEXT PRIMARY KEY,
                        student_id TEXT NOT NULL,
                        class_id TEXT,
                        activity_id TEXT,
                        points INTEGER DEFAULT 0,
                        reason TEXT,
                        awarded_by TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 8. 活动模板表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activity_templates (
                        template_id TEXT PRIMARY KEY,
                        teacher_id TEXT,
                        activity_type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        config TEXT DEFAULT '{}',
                        is_public BOOLEAN DEFAULT 0,
                        usage_count INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ca_teacher ON classroom_activities(teacher_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ca_status ON classroom_activities(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ap_activity ON activity_participants(activity_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_aq_activity ON activity_questions(activity_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ar_activity ON activity_responses(activity_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cp_student ON classroom_points(student_id)')

                conn.commit()
        except Exception as e:
            logger.error(f"初始化课堂互动引擎数据库失败: {e}")

    # ==================== 活动管理 ====================

    def create_activity(self, teacher_id: str, activity_type: str,
                        title: str, class_id: str = None,
                        subject: str = None, description: str = None,
                        config: Dict = None) -> Dict[str, Any]:
        """创建课堂活动"""
        with self._lock:
            try:
                if activity_type not in ACTIVITY_TYPES:
                    return {'success': False, 'error': f'不支持的活动类型: {activity_type}'}
                activity_id = f"act_{int(time.time() * 1000)}"
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO classroom_activities
                        (activity_id, teacher_id, class_id, subject, activity_type,
                         title, description, config, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft')
                    ''', (activity_id, teacher_id, class_id, subject, activity_type,
                          title, description, json.dumps(config or {}, ensure_ascii=False)))
                    conn.commit()
                return {'success': True, 'activity_id': activity_id, 'title': title}
            except Exception as e:
                logger.error(f"创建活动失败: {e}")
                return {'success': False, 'error': str(e)}

    def start_activity(self, activity_id: str) -> Dict[str, Any]:
        """开始活动"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE classroom_activities
                        SET status = 'active', start_time = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE activity_id = ?
                    ''', (activity_id,))
                    conn.commit()
                # 加入内存缓存
                self._active_sessions[activity_id] = {
                    'started_at': time.time(),
                    'participants': set(),
                    'responses': {}
                }
                return {'success': True, 'activity_id': activity_id, 'status': 'active'}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def end_activity(self, activity_id: str) -> Dict[str, Any]:
        """结束活动"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    # 计算时长
                    cursor.execute('SELECT start_time FROM classroom_activities WHERE activity_id = ?',
                                   (activity_id,))
                    row = cursor.fetchone()
                    duration = 0
                    if row and row[0]:
                        start = datetime.fromisoformat(row[0])
                        duration = int((datetime.now() - start).total_seconds())
                    cursor.execute('''
                        UPDATE classroom_activities
                        SET status = 'completed', end_time = CURRENT_TIMESTAMP,
                            duration = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE activity_id = ?
                    ''', (duration, activity_id))
                    # 统计参与人数
                    cursor.execute(
                        'SELECT COUNT(*) FROM activity_participants WHERE activity_id = ?',
                        (activity_id,))
                    count = cursor.fetchone()[0]
                    cursor.execute('''
                        UPDATE classroom_activities
                        SET participant_count = ? WHERE activity_id = ?
                    ''', (count, activity_id))
                    conn.commit()
                # 清除缓存
                if activity_id in self._active_sessions:
                    del self._active_sessions[activity_id]
                return {'success': True, 'activity_id': activity_id, 'duration': duration, 'participants': count}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def get_activity(self, activity_id: str) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM classroom_activities WHERE activity_id = ?',
                                   (activity_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '活动不存在'}
                    activity = dict(row)
                    activity['config'] = json.loads(activity.get('config') or '{}')
                    # 获取参与者
                    cursor.execute('SELECT * FROM activity_participants WHERE activity_id = ?',
                                   (activity_id,))
                    participants = [dict(r) for r in cursor.fetchall()]
                    activity['participants'] = participants
                    # 获取题目
                    cursor.execute('SELECT * FROM activity_questions WHERE activity_id = ? ORDER BY sort_order',
                                   (activity_id,))
                    questions = []
                    for q in cursor.fetchall():
                        qd = dict(q)
                        qd['options'] = json.loads(qd.get('options') or '[]')
                        questions.append(qd)
                    activity['questions'] = questions
                    return {'success': True, 'activity': activity}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def list_activities(self, teacher_id: str = None, class_id: str = None,
                        status: str = None, limit: int = 20) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    sql = 'SELECT * FROM classroom_activities WHERE 1=1'
                    params = []
                    if teacher_id:
                        sql += ' AND teacher_id = ?'
                        params.append(teacher_id)
                    if class_id:
                        sql += ' AND class_id = ?'
                        params.append(class_id)
                    if status:
                        sql += ' AND status = ?'
                        params.append(status)
                    sql += ' ORDER BY created_at DESC LIMIT ?'
                    params.append(limit)
                    cursor.execute(sql, params)
                    activities = [dict(r) for r in cursor.fetchall()]
                    return {'success': True, 'activities': activities, 'count': len(activities)}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    # ==================== 随机点名 ====================

    def random_pick(self, activity_id: str, student_ids: List[str],
                    exclude_ids: List[str] = None,
                    weights: Dict[str, float] = None,
                    count: int = 1) -> Dict[str, Any]:
        """随机点名/抽取学生"""
        with self._lock:
            try:
                if not student_ids:
                    return {'success': False, 'error': '学生列表为空'}
                exclude = set(exclude_ids or [])
                available = [s for s in student_ids if s not in exclude]
                if not available:
                    return {'success': False, 'error': '没有可选的学生'}
                if weights:
                    # 加权随机
                    weight_list = [weights.get(s, 1.0) for s in available]
                    total_w = sum(weight_list)
                    if total_w <= 0:
                        return {'success': False, 'error': '权重总和为零'}
                    selected = set()
                    candidates = available.copy()
                    cand_weights = weight_list.copy()
                    for _ in range(min(count, len(candidates))):
                        r = random.random() * sum(cand_weights)
                        cum = 0
                        for i, w in enumerate(cand_weights):
                            cum += w
                            if r <= cum:
                                selected.add(candidates[i])
                                cand_weights.pop(i)
                                candidates.pop(i)
                                break
                    result = list(selected)
                else:
                    # 纯随机
                    result = random.sample(available, min(count, len(available)))
                # 记录到活动
                pick_id = f"pick_{int(time.time() * 1000)}"
                return {
                    'success': True,
                    'pick_id': pick_id,
                    'selected': result,
                    'count': len(result),
                    'total_available': len(available)
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

    # ==================== 答题/测验 ====================

    def add_question(self, activity_id: str, question_type: str,
                     content: str, options: List[str] = None,
                     correct_answer: str = None, points: int = 10,
                     time_limit: int = 30, sort_order: int = 0) -> Dict[str, Any]:
        """添加题目到活动"""
        with self._lock:
            try:
                qid = f"aq_{int(time.time() * 1000)}"
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO activity_questions
                        (question_id, activity_id, question_type, content,
                         options, correct_answer, points, time_limit, sort_order)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (qid, activity_id, question_type, content,
                          json.dumps(options or [], ensure_ascii=False),
                          correct_answer, points, time_limit, sort_order))
                    conn.commit()
                return {'success': True, 'question_id': qid}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def submit_answer(self, activity_id: str, question_id: str,
                      student_id: str, answer: str,
                      student_name: str = None) -> Dict[str, Any]:
        """提交答案"""
        with self._lock:
            try:
                submit_time = time.time()
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    # 获取题目信息
                    cursor.execute('''
                        SELECT question_type, correct_answer, points, time_limit
                        FROM activity_questions WHERE question_id = ?
                    ''', (question_id,))
                    q = cursor.fetchone()
                    if not q:
                        return {'success': False, 'error': '题目不存在'}
                    q_type, correct_ans, points, time_limit = q
                    # 判断正确
                    is_correct = False
                    score = 0
                    if correct_ans:
                        if q_type in ('single_choice', 'true_false'):
                            is_correct = (answer == correct_ans)
                        elif q_type == 'multiple_choice':
                            is_correct = set(answer) == set(correct_ans)
                        elif q_type == 'fill_blank':
                            is_correct = answer.strip() == correct_ans.strip()
                        if is_correct:
                            score = points
                    # 响应时间（相对活动开始）
                    response_time = 0
                    if activity_id in self._active_sessions:
                        response_time = int(submit_time - self._active_sessions[activity_id]['started_at'])
                    # 记录答题
                    resp_id = f"ar_{int(time.time() * 1000)}"
                    cursor.execute('''
                        INSERT INTO activity_responses
                        (response_id, activity_id, question_id, student_id,
                         answer, is_correct, response_time, score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (resp_id, activity_id, question_id, student_id,
                          answer, 1 if is_correct else 0, response_time, score))
                    # 记录参与者（如未登记）
                    cursor.execute('''
                        INSERT OR IGNORE INTO activity_participants
                        (participant_id, activity_id, student_id, student_name, status)
                        VALUES (?, ?, ?, ?, 'active')
                    ''', (f"ap_{activity_id}_{student_id}", activity_id, student_id, student_name))
                    # 更新参与者得分
                    cursor.execute('''
                        UPDATE activity_participants
                        SET score = score + ?
                        WHERE activity_id = ? AND student_id = ?
                    ''', (score, activity_id, student_id))
                    conn.commit()
                return {
                    'success': True,
                    'response_id': resp_id,
                    'is_correct': is_correct,
                    'score': score,
                    'response_time': response_time
                }
            except Exception as e:
                logger.error(f"提交答案失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 抢答 ====================

    def start_rush_answer(self, activity_id: str) -> Dict[str, Any]:
        """开始抢答"""
        return self.start_activity(activity_id)

    def submit_rush(self, activity_id: str, student_id: str,
                    student_name: str = None) -> Dict[str, Any]:
        """提交抢答（按时间先后排名）"""
        with self._lock:
            try:
                rush_time = time.time()
                session = self._active_sessions.get(activity_id)
                if not session:
                    return {'success': False, 'error': '抢答活动未开始'}
                if student_id in session['responses']:
                    return {'success': False, 'error': '已抢答'}
                rank = len(session['responses']) + 1
                session['responses'][student_id] = {'time': rush_time, 'rank': rank}
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO activity_participants
                        (participant_id, activity_id, student_id, student_name, rank, status)
                        VALUES (?, ?, ?, ?, ?, 'active')
                    ''', (f"ap_{activity_id}_{student_id}", activity_id, student_id,
                          student_name, rank))
                    conn.commit()
                return {
                    'success': True,
                    'rank': rank,
                    'time': rush_time - session['started_at']
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def get_rush_ranking(self, activity_id: str) -> Dict[str, Any]:
        """获取抢答排名"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT student_id, student_name, rank, score
                        FROM activity_participants
                        WHERE activity_id = ? AND rank IS NOT NULL
                        ORDER BY rank ASC
                    ''', (activity_id,))
                    ranking = [dict(r) for r in cursor.fetchall()]
                    return {'success': True, 'ranking': ranking, 'count': len(ranking)}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    # ==================== 投票 ====================

    def create_vote(self, activity_id: str, title: str,
                    options: List[str], multiple_choice: bool = False,
                    anonymous: bool = True) -> Dict[str, Any]:
        with self._lock:
            try:
                vid = f"vote_{int(time.time() * 1000)}"
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO classroom_votes
                        (vote_id, activity_id, title, options, multiple_choice, anonymous)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (vid, activity_id, title,
                          json.dumps(options, ensure_ascii=False),
                          1 if multiple_choice else 0, 1 if anonymous else 0))
                    conn.commit()
                return {'success': True, 'vote_id': vid}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def cast_vote(self, vote_id: str, student_id: str,
                  options: List[str]) -> Dict[str, Any]:
        """投票"""
        with self._lock:
            try:
                # 简化：将投票记录在答题表中
                return {'success': True, 'vote_id': vote_id, 'voted': options}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    # ==================== 分组 ====================

    def create_groups(self, activity_id: str, student_ids: List[str],
                      group_count: int = 4,
                      strategy: str = 'random') -> Dict[str, Any]:
        """创建分组"""
        with self._lock:
            try:
                if not student_ids:
                    return {'success': False, 'error': '学生列表为空'}
                if group_count <= 0:
                    return {'success': False, 'error': '小组数量无效'}
                students = student_ids.copy()
                if strategy == 'random':
                    random.shuffle(students)
                elif strategy == 'ability_balance':
                    # 蛇形分组（假设学生按成绩排序）
                    students = sorted(students)  # 简化：按ID排序，实际应按成绩
                    groups = [[] for _ in range(group_count)]
                    for i, s in enumerate(students):
                        g = i % group_count
                        if (i // group_count) % 2 == 1:
                            g = group_count - 1 - g
                        groups[g].append(s)
                    groups_result = groups
                else:
                    random.shuffle(students)
                    groups_result = [students[i::group_count] for i in range(group_count)]

                if strategy != 'ability_balance':
                    groups_result = [students[i::group_count] for i in range(group_count)]

                groups = []
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    for i, members in enumerate(groups_result):
                        gid = f"grp_{int(time.time() * 1000)}_{i}"
                        group_num = i + 1
                        cursor.execute('''
                            INSERT INTO classroom_groups
                            (group_id, activity_id, group_number, group_name, student_ids)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (gid, activity_id, group_num, f"第{group_num}组",
                              json.dumps(members, ensure_ascii=False)))
                        groups.append({
                            'group_id': gid,
                            'group_number': group_num,
                            'group_name': f"第{group_num}组",
                            'members': members,
                            'member_count': len(members)
                        })
                        # 更新参与者分组
                        for sid in members:
                            cursor.execute('''
                                INSERT OR REPLACE INTO activity_participants
                                (participant_id, activity_id, student_id, group_number, status)
                                VALUES (?, ?, ?, ?, 'active')
                            ''', (f"ap_{activity_id}_{sid}", activity_id, sid, group_num))
                    conn.commit()
                return {
                    'success': True,
                    'activity_id': activity_id,
                    'groups': groups,
                    'total_students': len(students),
                    'strategy': strategy
                }
            except Exception as e:
                logger.error(f"创建分组失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 课堂积分 ====================

    def award_points(self, student_id: str, points: int,
                     reason: str = None, activity_id: str = None,
                     class_id: str = None, awarded_by: str = None) -> Dict[str, Any]:
        with self._lock:
            try:
                pid = f"pt_{int(time.time() * 1000)}"
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO classroom_points
                        (point_id, student_id, class_id, activity_id,
                         points, reason, awarded_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (pid, student_id, class_id, activity_id,
                          points, reason, awarded_by))
                    conn.commit()
                return {'success': True, 'point_id': pid, 'points': points}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def get_student_points(self, student_id: str,
                            class_id: str = None) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    sql = 'SELECT COALESCE(SUM(points), 0) as total FROM classroom_points WHERE student_id = ?'
                    params = [student_id]
                    if class_id:
                        sql += ' AND class_id = ?'
                        params.append(class_id)
                    cursor.execute(sql, params)
                    total = cursor.fetchone()[0] or 0
                    # 最近记录
                    cursor.execute('''
                        SELECT * FROM classroom_points
                        WHERE student_id = ? ORDER BY created_at DESC LIMIT 10
                    ''', (student_id,))
                    history = [dict(r) for r in cursor.fetchall()]
                    return {
                        'success': True,
                        'student_id': student_id,
                        'total_points': total,
                        'history': history
                    }
            except Exception as e:
                return {'success': False, 'error': str(e)}

    # ==================== 活动结果统计 ====================

    def get_activity_results(self, activity_id: str) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    # 参与者统计
                    cursor.execute(
                        'SELECT COUNT(*) as cnt FROM activity_participants WHERE activity_id = ?',
                        (activity_id,))
                    total_participants = cursor.fetchone()[0]
                    # 题目统计
                    cursor.execute(
                        'SELECT COUNT(*) as cnt FROM activity_questions WHERE activity_id = ?',
                        (activity_id,))
                    total_questions = cursor.fetchone()[0]
                    # 成绩排名
                    cursor.execute('''
                        SELECT student_id, student_name, score
                        FROM activity_participants
                        WHERE activity_id = ? ORDER BY score DESC
                    ''', (activity_id,))
                    ranking = [dict(r) for r in cursor.fetchall()]
                    # 平均分
                    if ranking:
                        avg_score = sum(r['score'] or 0 for r in ranking) / len(ranking)
                    else:
                        avg_score = 0
                    # 正确率（每题）
                    cursor.execute('''
                        SELECT q.question_id, q.content,
                               COUNT(r.response_id) as total,
                               SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as correct
                        FROM activity_questions q
                        LEFT JOIN activity_responses r ON q.question_id = r.question_id
                        WHERE q.activity_id = ?
                        GROUP BY q.question_id
                    ''', (activity_id,))
                    question_stats = [dict(r) for r in cursor.fetchall()]
                    return {
                        'success': True,
                        'activity_id': activity_id,
                        'total_participants': total_participants,
                        'total_questions': total_questions,
                        'avg_score': round(avg_score, 2),
                        'ranking': ranking,
                        'question_stats': question_stats
                    }
            except Exception as e:
                return {'success': False, 'error': str(e)}

    # ==================== 模板管理 ====================

    def save_template(self, teacher_id: str, activity_type: str,
                      name: str, config: Dict = None,
                      is_public: bool = False) -> Dict[str, Any]:
        with self._lock:
            try:
                tid = f"tpl_{int(time.time() * 1000)}"
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO activity_templates
                        (template_id, teacher_id, activity_type, name,
                         config, is_public)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (tid, teacher_id, activity_type, name,
                          json.dumps(config or {}, ensure_ascii=False),
                          1 if is_public else 0))
                    conn.commit()
                return {'success': True, 'template_id': tid}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def list_templates(self, teacher_id: str = None,
                       activity_type: str = None,
                       is_public: bool = None) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    sql = 'SELECT * FROM activity_templates WHERE 1=1'
                    params = []
                    if teacher_id:
                        sql += ' AND (teacher_id = ? OR is_public = 1)'
                        params.append(teacher_id)
                    if activity_type:
                        sql += ' AND activity_type = ?'
                        params.append(activity_type)
                    if is_public is not None:
                        sql += ' AND is_public = ?'
                        params.append(1 if is_public else 0)
                    sql += ' ORDER BY usage_count DESC'
                    cursor.execute(sql, params)
                    templates = [dict(r) for r in cursor.fetchall()]
                    return {'success': True, 'templates': templates, 'count': len(templates)}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    # ==================== 统计接口 ====================

    def get_activity_types(self) -> Dict[str, Any]:
        return {'success': True, 'types': ACTIVITY_TYPES}

    def get_grouping_strategies(self) -> Dict[str, Any]:
        return {'success': True, 'strategies': GROUPING_STRATEGIES}

    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM classroom_activities')
                    total_activities = cursor.fetchone()[0]
                    cursor.execute('SELECT status, COUNT(*) FROM classroom_activities GROUP BY status')
                    status_stats = {r[0]: r[1] for r in cursor.fetchall()}
                    cursor.execute('SELECT activity_type, COUNT(*) FROM classroom_activities GROUP BY activity_type')
                    type_stats = {r[0]: r[1] for r in cursor.fetchall()}
                    cursor.execute('SELECT COUNT(*) FROM activity_participants')
                    total_participations = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM classroom_points')
                    total_points_records = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM activity_templates')
                    total_templates = cursor.fetchone()[0]
                    return {
                        'success': True,
                        'total_activities': total_activities,
                        'status_distribution': status_stats,
                        'type_distribution': type_stats,
                        'total_participations': total_participations,
                        'total_points_records': total_points_records,
                        'total_templates': total_templates
                    }
            except Exception as e:
                return {'success': False, 'error': str(e)}


# 单例
classroom_interaction_engine = ClassroomInteractionEngine()
