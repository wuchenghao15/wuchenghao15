# -*- coding: utf-8 -*-
from app.models.question import Question

# 初始化题目模型
q = Question()

# 获取所有题目
questions = q.get_questions()

# 打印题库状态
print(f'当前题库共有 {len(questions)} 道题目')

# 打印前10道题目
print('\n前10道题目:')
for i, question in enumerate(questions[:10]):
    print(f'题目 {i+1}: {question.content}')
    print(f'  类型: {question.question_type}, 语言: {question.language_id}, 等级: {question.level_id}')
