#!/usr/bin/env python3
"""
扩充英语日常对话类简答题题库
解决生成题目重复的问题
"""

import sys
import os
import random
from app.models.question import Question
from app.utils.logging import logger

class EnglishDialogQuestionExpander:
    """英语日常对话题目扩充器"""
    
    def __init__(self):
        self.language = 'english'
        self.category = '日常对话'
        self.question_type = 'short_answer'
        self.level = 'beginner'
        
        # 英语日常对话类简答题模板
        self.question_templates = [
            {
                'content': 'How do you greet someone in English when you meet them for the first time?',
                'correct_answer': 'Hello, nice to meet you.',
                'explanation': 'This is a common greeting used when meeting someone for the first time.'
            },
            {
                'content': 'What do you say in English when you want to ask someone\'s name?',
                'correct_answer': 'What\'s your name?',
                'explanation': 'This is the standard way to ask someone for their name in English.'
            },
            {
                'content': 'How do you respond when someone says "Thank you" to you?',
                'correct_answer': 'You\'re welcome.',
                'explanation': 'This is the most common response to "Thank you" in English.'
            },
            {
                'content': 'What do you say when you want to apologize to someone?',
                'correct_answer': 'I\'m sorry.',
                'explanation': 'This is a basic apology phrase in English.'
            },
            {
                'content': 'How do you ask someone how they are feeling today?',
                'correct_answer': 'How are you today?',
                'explanation': 'This is a common way to ask about someone\'s well-being.'
            },
            {
                'content': 'What do you say when you want to say goodbye to someone?',
                'correct_answer': 'Goodbye.',
                'explanation': 'This is a standard farewell in English.'
            },
            {
                'content': 'How do you ask someone where they are from?',
                'correct_answer': 'Where are you from?',
                'explanation': 'This is how you ask about someone\'s place of origin.'
            },
            {
                'content': 'What do you say when you want to invite someone to do something?',
                'correct_answer': 'Would you like to...?',
                'explanation': 'This is a polite way to extend an invitation.'
            },
            {
                'content': 'How do you ask someone for help in English?',
                'correct_answer': 'Can you help me, please?',
                'explanation': 'This is a polite way to request assistance.'
            },
            {
                'content': 'What do you say when you want to agree with someone?',
                'correct_answer': 'I agree.',
                'explanation': 'This is how you express agreement with someone\'s statement.'
            },
            {
                'content': 'How do you ask someone what time it is?',
                'correct_answer': 'What time is it?',
                'explanation': 'This is the standard way to ask for the current time.'
            },
            {
                'content': 'What do you say when you want to introduce yourself to someone?',
                'correct_answer': 'My name is...',
                'explanation': 'This is how you tell someone your name when introducing yourself.'
            },
            {
                'content': 'How do you ask someone if they understand?',
                'correct_answer': 'Do you understand?',
                'explanation': 'This is how you check if someone comprehends what you\'ve said.'
            },
            {
                'content': 'What do you say when you want to wish someone good luck?',
                'correct_answer': 'Good luck!',
                'explanation': 'This is a common way to wish someone success.'
            },
            {
                'content': 'How do you ask someone about their hobbies?',
                'correct_answer': 'What are your hobbies?',
                'explanation': 'This is how you ask someone about their leisure activities.'
            },
            {
                'content': 'What do you say when you want to congratulate someone?',
                'correct_answer': 'Congratulations!',
                'explanation': 'This is how you express joy for someone\'s achievement.'
            },
            {
                'content': 'How do you ask someone what they are doing?',
                'correct_answer': 'What are you doing?',
                'explanation': 'This is how you ask about someone\'s current activity.'
            },
            {
                'content': 'What do you say when you want to express surprise?',
                'correct_answer': 'Wow!',
                'explanation': 'This is a common exclamation of surprise.'
            },
            {
                'content': 'How do you ask someone for their phone number?',
                'correct_answer': 'What\'s your phone number?',
                'explanation': 'This is how you request someone\'s contact information.'
            },
            {
                'content': 'What do you say when you want to thank someone politely?',
                'correct_answer': 'Thank you very much.',
                'explanation': 'This is a more formal way to express gratitude.'
            }
        ]
    
    def expand_questions(self):
        """扩充英语日常对话类简答题"""
        logger.info(f"开始扩充英语日常对话类简答题题库")
        
        added_count = 0
        
        for template in self.question_templates:
            # 检查题目是否已存在
            if Question.is_duplicate_question(template['content'], self.language, self.category):
                logger.info(f"题目已存在，跳过: {template['content']}")
                continue
            
            # 创建题目对象
            question = Question(
                language=self.language,
                level=self.level,
                category=self.category,
                content=template['content'],
                options=[],  # 简答题不需要选项
                correct_answer=template['correct_answer'],
                explanation=template['explanation'],
                source='manual_expansion',
                question_type=self.question_type
            )
            
            # 保存到数据库
            question_id = question.save()
            
            if question_id:
                logger.info(f"成功添加题目: {template['content']}")
                added_count += 1
            else:
                logger.error(f"保存题目失败: {template['content']}")
        
        logger.info(f"英语日常对话类简答题扩充完成，新增 {added_count} 道题目")
        return added_count

if __name__ == "__main__":
    expander = EnglishDialogQuestionExpander()
    added = expander.expand_questions()
    sys.exit(0 if added > 0 else 1)
