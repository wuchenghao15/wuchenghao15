#!/usr/bin/env python3
"""
简单的AI题库载录脚本
不依赖复杂的app模块初始化，只实现核心功能
"""

import os
import sys
import json
import sqlite3
import time
import logging
import random

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_ai_question_loader.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('simple_ai_question_loader')

# 尝试导入AI服务模块
try:
    from ai_service import ai_service_manager
    ai_service_available = True
    logger.info("成功导入AI服务模块")
except Exception as e:
    logger.warning(f"无法导入AI服务模块，将使用模拟数据: {str(e)}")
    ai_service_available = False

# 尝试导入智能选项生成器
try:
    from intelligent_option_generator import IntelligentOptionGenerator
    option_generator_available = True
    logger.info("成功导入智能选项生成器")
except Exception as e:
    logger.warning(f"无法导入智能选项生成器，将使用简单选项生成: {str(e)}")
    option_generator_available = False

class SimpleAIQuestionBankLoader:
    """简单的AI题库载录器"""
    
    def __init__(self, db_path='app.db'):
        """初始化
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self.languages = ['japanese', 'english']
        self.categories = ['词汇', '语法', '阅读', '听力']
        self.difficulties = [1, 2, 3, 4, 5]
        
        # 初始化选项生成器
        if option_generator_available:
            self.option_generator = IntelligentOptionGenerator()
        
        logger.info("初始化简单AI题库载录器")
    
    def init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 创建题库表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS question_bank (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    language TEXT NOT NULL,
                    category TEXT NOT NULL,
                    difficulty INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    options TEXT NOT NULL,
                    correct_answer TEXT NOT NULL,
                    explanation TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("成功初始化数据库表")
            return True
        except Exception as e:
            logger.error(f"初始化数据库表失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_db_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def _generate_question_content(self, language, category, difficulty):
        """生成题目内容
        
        Args:
            language: 语言
            category: 类别
            difficulty: 难度
            
        Returns:
            题目内容和正确答案
        """
        if ai_service_available:
            # 使用AI生成题目
            prompt = f"生成一个{language}的{category}题，难度为{difficulty}级，格式清晰，包含题目内容和正确答案。"
            result = ai_service_manager.infer('default_text_gen', prompt)
            
            if result['success']:
                generated_text = result['result']
                logger.info(f"AI生成题目: {generated_text[:50]}...")
                
                # 解析生成的题目和答案
                lines = generated_text.split('\n')
                question_content = ""
                correct_answer = ""
                
                for line in lines:
                    if "题目：" in line or "问题：" in line:
                        question_content = line.replace("题目：", "").replace("问题：", "").strip()
                    elif "正确答案：" in line or "答案：" in line:
                        correct_answer = line.replace("正确答案：", "").replace("答案：", "").strip()
                
                if question_content and correct_answer:
                    return question_content, correct_answer
        
        # 使用模拟数据
        logger.info(f"使用模拟数据生成{language} {category} 难度{difficulty}的题目")
        
        if language == 'japanese':
            if category == '词汇':
                vocab_questions = {
                    1: [('「こんにちは」の正しい意味はどれですか？', '你好')],
                    2: [('「友達」の正しい意味はどれですか？', '朋友')],
                    3: [('「勉強」の正しい意味はどれですか？', '学习')],
                    4: [('「喧嘩」の正しい意味はどれですか？', '吵架')],
                    5: [('「懐かしい」の正しい意味はどれですか？', '怀念的')]
                }
                return random.choice(vocab_questions[difficulty])
            elif category == '语法':
                grammar_questions = {
                    1: [('私は学生____です。', 'で')],
                    2: [('私は朝ごはん____食べます。', 'を')],
                    3: [('私は昨日映画____見ました。', 'を')],
                    4: [('雨が降っている____、外出しませんでした。', 'ので')],
                    5: [('私は日本へ行く____、日本語を勉強しています。', 'ために')]
                }
                return random.choice(grammar_questions[difficulty])
            elif category == '阅读':
                reading_questions = {
                    1: [('私は李です。日本語が好きです。毎日日本語を勉強します。\nQ: 李さんは何が好きですか？', '日本語')],
                    2: [('昨日は雨でした。私は家で本を読みました。友達と映画を見に行きませんでした。\nQ: 昨日私は何をしましたか？', '本を読みました')],
                    3: [('今日は晴れです。公園に行きました。子供たちが遊んでいました。桜の花が咲いていて、とても美しかったです。\nQ: 今日の天気はどうでしたか？', '晴れ')],
                    4: [('日本の首都は東京です。東京は人口が多く、物価が高いです。しかし、交通が便利で、様々な文化があります。\nQ: 東京の特徴はどれですか？', '人口が多い')],
                    5: [('私は毎朝ジョギングをします。ジョギングは健康に良いです。体が丈夫になります。また、ストレスを解消することができます。\nQ: ジョギングの効果はどれですか？', '健康に良い')]
                }
                return random.choice(reading_questions[difficulty])
            elif category == '听力':
                listening_questions = {
                    1: [('听力材料：\nA: こんにちは。お名前は何ですか？\nB: はい、私は佐藤です。\nQ: 佐藤さんは何と言いましたか？', '私は佐藤です')],
                    2: [('听力材料：\n店員: いらっしゃいませ。何をお探しですか？\nお客: すみません、ペンを買いたいです。\nQ: お客は何を買いたいですか？', 'ペン')],
                    3: [('听力材料：\n先生: 今日の授業では、日本の歴史について勉強します。特に江戸時代の社会構造に焦点を当てます。\nQ: 今日の授業のテーマは何ですか？', '日本の歴史')],
                    4: [('听力材料：\nアナウンサー: こんにちは、東京の天気予報です。今日は午前中は晴れですが、午後から曇りになり、夕方には小雨が降る予定です。\nQ: 今日の午後の天気はどうですか？', '曇り')],
                    5: [('听力材料：\n学者: 日本語の特徴の一つは、敬語の体系が非常に発達していることです。敬語は、相手との関係、場面の正式さなどに応じて使い分けられます。\nQ: 日本語の特徴は何ですか？', '敬語の体系が非常に発達していること')]
                }
                return random.choice(listening_questions[difficulty])
        
        # 默认返回模拟数据
        return f"模拟{language} {category} 难度{difficulty}的题目", f"正确答案{difficulty}"
    
    def _generate_options(self, question_content, category, language, correct_answer):
        """生成选项
        
        Args:
            question_content: 题目内容
            category: 类别
            language: 语言
            correct_answer: 正确答案
            
        Returns:
            选项列表
        """
        if option_generator_available:
            # 使用智能选项生成器
            question_info = {
                'content': question_content,
                'category': category,
                'language': language
            }
            return self.option_generator.generate_options(question_info, correct_answer, 6)
        
        # 简单的选项生成
        options = []
        option_ids = ['A', 'B', 'C', 'D', 'E', 'F']
        
        # 确保正确答案在选项中
        options.append({
            'id': 'A',
            'content': correct_answer
        })
        
        # 生成干扰选项
        for i in range(1, 6):
            options.append({
                'id': option_ids[i],
                'content': f"干扰选项{i}: {correct_answer}的干扰项"
            })
        
        # 随机打乱选项顺序
        random.shuffle(options)
        
        return options
    
    def _save_to_database(self, language, category, difficulty, content, options, correct_answer):
        """保存题目到数据库"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 将选项转换为JSON字符串
            options_json = json.dumps(options)
            
            # 查找正确答案对应的选项ID
            correct_answer_id = ""
            for option in options:
                if option['content'] == correct_answer:
                    correct_answer_id = option['id']
                    break
            
            if not correct_answer_id:
                correct_answer_id = options[0]['id']
            
            # 插入数据库
            cursor.execute('''
                INSERT INTO question_bank (language, category, difficulty, content, options, correct_answer)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (language, category, difficulty, content, options_json, correct_answer_id))
            
            conn.commit()
            logger.info(f"成功保存题目到数据库，ID: {cursor.lastrowid}")
            return True
        except Exception as e:
            logger.error(f"保存题目到数据库失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def load_question_bank(self, num_questions=10):
        """载录题库
        
        Args:
            num_questions: 要生成的题目数量
        """
        # 初始化数据库
        if not self.init_db():
            logger.error("初始化数据库失败，无法继续")
            return False
        
        logger.info(f"开始载录题库，计划生成{num_questions}道题目")
        
        generated_count = 0
        attempts = 0
        max_attempts = num_questions * 2
        
        while generated_count < num_questions and attempts < max_attempts:
            attempts += 1
            
            # 随机选择语言、类别和难度
            language = random.choice(self.languages)
            category = random.choice(self.categories)
            difficulty = random.choice(self.difficulties)
            
            logger.info(f"正在生成第{generated_count+1}道题目: {language} {category} 难度{difficulty}")
            
            # 生成题目内容和答案
            content, correct_answer = self._generate_question_content(language, category, difficulty)
            
            if not content or not correct_answer:
                logger.warning("生成题目内容失败，跳过")
                continue
            
            # 生成选项
            options = self._generate_options(content, category, language, correct_answer)
            
            if not options or len(options) < 4:
                logger.warning("生成选项失败，跳过")
                continue
            
            # 保存到数据库
            if self._save_to_database(language, category, difficulty, content, options, correct_answer):
                generated_count += 1
            
            # 避免过于频繁的操作
            time.sleep(0.5)
        
        logger.info(f"题库载录完成，成功生成{generated_count}道题目")
        return True
    
    def verify_question_bank(self):
        """验证题库"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 查询所有题目
            cursor.execute('SELECT id, content, options, correct_answer FROM question_bank')
            questions = cursor.fetchall()
            
            logger.info(f"共查询到{len(questions)}道题目")
            
            # 验证每道题目的选项和正确答案对应关系
            invalid_questions = []
            
            for question in questions:
                question_id = question[0]
                content = question[1]
                options_json = question[2]
                correct_answer = question[3]
                
                try:
                    # 解析选项
                    options = json.loads(options_json)
                    
                    # 检查选项是否包含正确答案
                    option_ids = [opt['id'] for opt in options]
                    if correct_answer not in option_ids:
                        invalid_questions.append({
                            'id': question_id,
                            'error': f'正确答案ID {correct_answer} 不在选项中'
                        })
                        logger.warning(f"题目ID {question_id} 验证失败: {invalid_questions[-1]['error']}")
                    else:
                        logger.info(f"题目ID {question_id} 验证通过")
                        
                except Exception as e:
                    invalid_questions.append({
                        'id': question_id,
                        'error': f'解析选项失败: {str(e)}'
                    })
                    logger.error(f"题目ID {question_id} 解析失败: {str(e)}")
            
            logger.info(f"题库验证完成，共发现{len(invalid_questions)}道无效题目")
            return True
        except Exception as e:
            logger.error(f"验证题库失败: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    # 创建简单AI题库载录器实例
    loader = SimpleAIQuestionBankLoader()
    
    # 载录题库
    loader.load_question_bank(num_questions=20)
    
    # 验证题库
    loader.verify_question_bank()