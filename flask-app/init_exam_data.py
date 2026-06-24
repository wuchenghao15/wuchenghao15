import sqlite3
import uuid
from datetime import datetime

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

cursor.execute('DELETE FROM exams')

now = datetime.now().isoformat()

test_exams = [
    {
        'id': str(uuid.uuid4()),
        'title': '日语N5水平测试',
        'description': '面向初学者的日语能力测试，涵盖基础词汇和语法',
        'language': 'japanese',
        'level': 'beginner',
        'duration': 60,
        'question_count': 20,
        'total_points': 100.0,
        'passing_score': 60.0,
        'status': 'active',
        'shuffle_questions': 1,
        'shuffle_options': 1,
        'allow_retake': 1,
        'max_retakes': 3,
        'created_by': 'admin'
    },
    {
        'id': str(uuid.uuid4()),
        'title': '日语N4水平测试',
        'description': '面向初级学习者的日语能力测试，涵盖常用词汇和基础语法',
        'language': 'japanese',
        'level': 'beginner',
        'duration': 90,
        'question_count': 30,
        'total_points': 100.0,
        'passing_score': 60.0,
        'status': 'active',
        'shuffle_questions': 1,
        'shuffle_options': 1,
        'allow_retake': 1,
        'max_retakes': 3,
        'created_by': 'admin'
    },
    {
        'id': str(uuid.uuid4()),
        'title': '日语N3水平测试',
        'description': '面向中级学习者的日语能力测试，涵盖较复杂的语法和词汇',
        'language': 'japanese',
        'level': 'intermediate',
        'duration': 120,
        'question_count': 40,
        'total_points': 100.0,
        'passing_score': 60.0,
        'status': 'active',
        'shuffle_questions': 1,
        'shuffle_options': 1,
        'allow_retake': 1,
        'max_retakes': 3,
        'created_by': 'admin'
    },
    {
        'id': str(uuid.uuid4()),
        'title': '英语四级模拟测试',
        'description': '面向大学生的英语四级模拟考试，涵盖听力、阅读、写作等',
        'language': 'english',
        'level': 'intermediate',
        'duration': 130,
        'question_count': 50,
        'total_points': 710.0,
        'passing_score': 425.0,
        'status': 'active',
        'shuffle_questions': 1,
        'shuffle_options': 1,
        'allow_retake': 1,
        'max_retakes': 3,
        'created_by': 'admin'
    },
    {
        'id': str(uuid.uuid4()),
        'title': '日语N2水平测试',
        'description': '面向中高级学习者的日语能力测试，涵盖高级语法和词汇',
        'language': 'japanese',
        'level': 'advanced',
        'duration': 150,
        'question_count': 50,
        'total_points': 100.0,
        'passing_score': 60.0,
        'status': 'active',
        'shuffle_questions': 1,
        'shuffle_options': 1,
        'allow_retake': 1,
        'max_retakes': 3,
        'created_by': 'admin'
    },
    {
        'id': str(uuid.uuid4()),
        'title': '日语N1水平测试',
        'description': '面向高级学习者的日语能力测试，涵盖最难的语法和词汇',
        'language': 'japanese',
        'level': 'advanced',
        'duration': 180,
        'question_count': 60,
        'total_points': 100.0,
        'passing_score': 60.0,
        'status': 'active',
        'shuffle_questions': 1,
        'shuffle_options': 1,
        'allow_retake': 1,
        'max_retakes': 3,
        'created_by': 'admin'
    },
    {
        'id': str(uuid.uuid4()),
        'title': '中文普通话水平测试',
        'description': '普通话水平等级测试，涵盖发音、朗读、说话等',
        'language': 'chinese',
        'level': 'intermediate',
        'duration': 60,
        'question_count': 30,
        'total_points': 100.0,
        'passing_score': 60.0,
        'status': 'active',
        'shuffle_questions': 1,
        'shuffle_options': 1,
        'allow_retake': 1,
        'max_retakes': 3,
        'created_by': 'admin'
    },
    {
        'id': str(uuid.uuid4()),
        'title': '英语六级模拟测试',
        'description': '面向大学生的英语六级模拟考试，难度较高',
        'language': 'english',
        'level': 'advanced',
        'duration': 130,
        'question_count': 50,
        'total_points': 710.0,
        'passing_score': 425.0,
        'status': 'active',
        'shuffle_questions': 1,
        'shuffle_options': 1,
        'allow_retake': 1,
        'max_retakes': 3,
        'created_by': 'admin'
    }
]

cursor.executemany('''
INSERT INTO exams 
(id, title, description, language, level, duration, question_count, total_points, passing_score, status, shuffle_questions, shuffle_options, allow_retake, max_retakes, created_by, created_at, updated_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', [
    (e['id'], e['title'], e['description'], e['language'], e['level'],
     e['duration'], e['question_count'], e['total_points'], e['passing_score'],
     e['status'], e['shuffle_questions'], e['shuffle_options'], e['allow_retake'],
     e['max_retakes'], e['created_by'], now, now)
    for e in test_exams
])

conn.commit()

cursor.execute('SELECT COUNT(*) FROM exams')
count = cursor.fetchone()[0]
print(f'成功插入 {count} 条考试数据')

cursor.execute('SELECT id, title, language, level, duration FROM exams')
for row in cursor.fetchall():
    print(f'ID: {row[0][:8]}..., 标题: {row[1]}, 语言: {row[2]}, 难度: {row[3]}, 时长: {row[4]}')

conn.close()
