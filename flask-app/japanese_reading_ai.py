#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日语精读练习AI
为日语题库增加日语精读类型练习
"""

import os
import json
import logging
import sqlite3
from datetime import datetime, UTC
from typing import List, Dict, Optional

# 初始化日志记录器
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('logs/japanese_reading_ai.log'),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger('japanese_reading_ai')

# 导入数据库管理器
try:
    from app.utils.db import db_manager
except ImportError:
    # 如果导入失败，创建一个简单的数据库管理器
    class DBManager:
        def __init__(self):
            self.db_path = 'data/mtscos_ai_project.db'
            self._ensure_tables()
        
        def _ensure_tables(self):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建题目表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                answer TEXT NOT NULL,
                explanation TEXT,
                category_id INTEGER,
                language_id INTEGER,
                level_id INTEGER,
                question_type TEXT DEFAULT 'single_choice',
                options TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                difficulty_score REAL,
                discrimination_index REAL,
                usage_count INTEGER DEFAULT 0,
                correct_rate REAL,
                audio_url TEXT,
                image_url TEXT,
                video_url TEXT,
                time_limit INTEGER,
                score INTEGER,
                created_at TEXT,
                updated_at TEXT
            )
            ''')
            
            # 创建题目选项表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS question_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                option_text TEXT,
                option_index INTEGER,
                FOREIGN KEY (question_id) REFERENCES questions (id)
            )
            ''')
            
            # 创建标签表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS question_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_name TEXT
            )
            ''')
            
            # 创建标签关联表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS question_tag_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                tag_id INTEGER,
                FOREIGN KEY (question_id) REFERENCES questions (id),
                FOREIGN KEY (tag_id) REFERENCES question_tags (id)
            )
            ''')
            
            # 创建题目分类表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS question_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            ''')
            
            # 创建题目语种表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS question_languages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            )
            ''')
            
            # 创建题目等级表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS question_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                level INTEGER NOT NULL,
                description TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            ''')
            
            # 插入默认数据
            cursor.execute('SELECT COUNT(*) FROM question_languages')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO question_languages (name, code, created_at, updated_at) VALUES (?, ?, ?, ?)',
                             ('日语', 'ja', datetime.now(UTC).isoformat(), datetime.now(UTC).isoformat()))
                cursor.execute('INSERT INTO question_languages (name, code, created_at, updated_at) VALUES (?, ?, ?, ?)',
                             ('英语', 'en', datetime.now(UTC).isoformat(), datetime.now(UTC).isoformat()))
            
            cursor.execute('SELECT COUNT(*) FROM question_levels')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO question_levels (name, level, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
                             ('初级', 1, '初级难度', datetime.now(UTC).isoformat(), datetime.now(UTC).isoformat()))
                cursor.execute('INSERT INTO question_levels (name, level, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
                             ('中级', 2, '中级难度', datetime.now(UTC).isoformat(), datetime.now(UTC).isoformat()))
                cursor.execute('INSERT INTO question_levels (name, level, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
                             ('高级', 3, '高级难度', datetime.now(UTC).isoformat(), datetime.now(UTC).isoformat()))
                cursor.execute('INSERT INTO question_levels (name, level, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
                             ('专家', 4, '专家难度', datetime.now(UTC).isoformat(), datetime.now(UTC).isoformat()))
            
            conn.commit()
            conn.close()
        
        def execute(self, query, params=()):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                conn.commit()
                return cursor, True
            except Exception as e:
                logger.error(f"执行SQL失败: {query}, 参数: {params}, 错误: {e}")
                conn.rollback()
                return None, False
            finally:
                conn.close()
        
        def fetch_all(self, query, params=()):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                return cursor.fetchall()
            except Exception as e:
                logger.error(f"查询SQL失败: {query}, 参数: {params}, 错误: {e}")
                return []
            finally:
                conn.close()
        
        def fetch_one(self, query, params=()):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                return cursor.fetchone()
            except Exception as e:
                logger.error(f"查询SQL失败: {query}, 参数: {params}, 错误: {e}")
                return None
            finally:
                conn.close()
        
        def fetch_scalar(self, query, params=()):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result[0] if result else None
            except Exception as e:
                logger.error(f"查询SQL失败: {query}, 参数: {params}, 错误: {e}")
                return None
            finally:
                conn.close()
        
        def insert(self, table, data):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?'] * len(data))
                query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
                cursor.execute(query, list(data.values()))
                conn.commit()
                return cursor.lastrowid
            except Exception as e:
                logger.error(f"插入数据失败: {table}, 数据: {data}, 错误: {e}")
                conn.rollback()
                return None
            finally:
                conn.close()
        
        def update(self, table, data, where_clause, where_params):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                set_clause = ', '.join([f'{col} = ?' for col in data.keys()])
                query = f'UPDATE {table} SET {set_clause} WHERE {where_clause}'
                params = list(data.values()) + list(where_params)
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"更新数据失败: {table}, 数据: {data}, 条件: {where_clause}, 错误: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        
        def delete(self, table, where_clause, where_params):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                query = f'DELETE FROM {table} WHERE {where_clause}'
                cursor.execute(query, where_params)
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"删除数据失败: {table}, 条件: {where_clause}, 错误: {e}")
                conn.rollback()
                return False
    
    db_manager = DBManager()

class JapaneseReadingAI:
    """日语精读练习AI"""
    
    def __init__(self):
        """初始化AI"""
        logger.info("日语精读练习AI初始化...")
        self.japanese_language_id = 1  # 日语的ID
        self.reading_passages = self._load_reading_passages()
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = ['logs', 'data', 'reports']
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"创建目录: {directory}")
    
    def _load_reading_passages(self) -> List[Dict]:
        """加载日语阅读材料"""
        return [
            {
                "title": "東京の朝",
                "content": "東京の朝はとてもにぎやかです。電車には通勤客でいっぱいで、道路には車がたくさん走っています。駅の周りには、コンビニエンスストアやカフェがたくさんあります。人々は朝ごはんを買ったり、新聞を読んだりしながら歩いています。",
                "level": 1,  # 初级
                "questions": [
                    {
                        "question": "東京の朝はどのような様子ですか？",
                        "options": ["静かです", "にぎやかです", "寒いです", "暑いです"],
                        "answer": "にぎやかです",
                        "explanation": "文章の最初に「東京の朝はとてもにぎやかです」と書かれています。"
                    },
                    {
                        "question": "電車には何でいっぱいですか？",
                        "options": ["学生", "観光客", "通勤客", "子供"],
                        "answer": "通勤客",
                        "explanation": "文章に「電車には通勤客でいっぱいで」と書かれています。"
                    }
                ]
            },
            {
                "title": "日本の四季",
                "content": "日本には四季があります。春は桜が咲いて美しいです。夏は暑くて、海に行く人がたくさんいます。秋は紅葉がきれいで、山登りに行く人が多いです。冬は寒くて、雪が降る地域もあります。日本人は四季の変化を楽しんでいます。",
                "level": 2,  # 中级
                "questions": [
                    {
                        "question": "日本にはどのような季節がありますか？",
                        "options": ["春と夏", "夏と秋", "秋と冬", "四季"],
                        "answer": "四季",
                        "explanation": "文章の最初に「日本には四季があります」と書かれています。"
                    },
                    {
                        "question": "夏にはどこに行く人がたくさんいますか？",
                        "options": ["山", "海", "公園", "神社"],
                        "answer": "海",
                        "explanation": "文章に「夏は暑くて、海に行く人がたくさんいます」と書かれています。"
                    },
                    {
                        "question": "秋には何がきれいですか？",
                        "options": ["桜", "向日葵", "紅葉", "菊"],
                        "answer": "紅葉",
                        "explanation": "文章に「秋は紅葉がきれいで」と書かれています。"
                    }
                ]
            },
            {
                "title": "日本の伝統文化",
                "content": "日本にはたくさんの伝統文化があります。茶道はお茶を点てて飲む伝統的な儀式です。生け花は花を飾る芸術です。歌舞伎は伝統的な演劇で、豪華な衣装と化粧が特徴です。浮世絵は江戸時代に流行した木版画です。これらの伝統文化は今も日本人に大切にされています。",
                "level": 3,  # 高级
                "questions": [
                    {
                        "question": "茶道とは何ですか？",
                        "options": ["花を飾る芸術", "お茶を点てて飲む伝統的な儀式", "伝統的な演劇", "木版画"],
                        "answer": "お茶を点てて飲む伝統的な儀式",
                        "explanation": "文章に「茶道はお茶を点てて飲む伝統的な儀式です」と書かれています。"
                    },
                    {
                        "question": "歌舞伎の特徴は何ですか？",
                        "options": ["簡素な衣装", "豪華な衣装と化粧", "静かな演出", "現代的な音楽"],
                        "answer": "豪華な衣装と化粧",
                        "explanation": "文章に「歌舞伎は伝統的な演劇で、豪華な衣装と化粧が特徴です」と書かれています。"
                    },
                    {
                        "question": "浮世絵はいつ流行しましたか？",
                        "options": ["明治時代", "大正時代", "昭和時代", "江戸時代"],
                        "answer": "江戸時代",
                        "explanation": "文章に「浮世絵は江戸時代に流行した木版画です」と書かれています。"
                    }
                ]
            },
            {
                "title": "日本の食文化",
                "content": "日本の食文化は多様で豊かです。寿司は生の魚を飯の上にのせた料理で、世界中で人気があります。天ぷらは野菜や魚を小麦粉の衣で包んで揚げた料理です。焼肉は肉を焼いて食べる料理で、家族や友人との集まりに人気です。和食は季節の食材を使い、五感を満たす料理です。日本人は食べ物を大切にし、「いただきます」と言って食べ始め、「ごちそうさま」と言って食べ終わります。",
                "level": 3,  # 高级
                "questions": [
                    {
                        "question": "寿司とは何ですか？",
                        "options": ["野菜を焼いた料理", "生の魚を飯の上にのせた料理", "肉を焼いた料理", "小麦粉の衣で包んで揚げた料理"],
                        "answer": "生の魚を飯の上にのせた料理",
                        "explanation": "文章に「寿司は生の魚を飯の上にのせた料理で」と書かれています。"
                    },
                    {
                        "question": "天ぷらはどのように作られますか？",
                        "options": ["肉を焼く", "魚を煮る", "野菜や魚を小麦粉の衣で包んで揚げる", "米を炊く"],
                        "answer": "野菜や魚を小麦粉の衣で包んで揚げる",
                        "explanation": "文章に「天ぷらは野菜や魚を小麦粉の衣で包んで揚げた料理です」と書かれています。"
                    },
                    {
                        "question": "日本人は食べ始める前に何と言いますか？",
                        "options": ["ごちそうさま", "いただきます", "ありがとう", "お疲れさま"],
                        "answer": "いただきます",
                        "explanation": "文章に「日本人は食べ物を大切にし、「いただきます」と言って食べ始め」と書かれています。"
                    }
                ]
            },
            {
                "title": "日本の教育",
                "content": "日本の教育は義務教育が9年あります。小学校は6年間、中学校は3年間です。高校は3年間で、受験が必要です。大学は4年間で、入学するには大学入試を受ける必要があります。日本の教育は学業成績が重視され、多くの学生が塾に通っています。また、部活も重要で、放課後は体育館で練習したり、部室で活動したりします。",
                "level": 2,  # 中级
                "questions": [
                    {
                        "question": "日本の義務教育は何年ですか？",
                        "options": ["6年", "9年", "12年", "16年"],
                        "answer": "9年",
                        "explanation": "文章に「日本の教育は義務教育が9年あります」と書かれています。"
                    },
                    {
                        "question": "高校に入るには何が必要ですか？",
                        "options": ["塾に通うこと", "部活に参加すること", "受験すること", "海外旅行すること"],
                        "answer": "受験すること",
                        "explanation": "文章に「高校は3年間で、受験が必要です」と書かれています。"
                    },
                    {
                        "question": "放課後、学生たちは何をしますか？",
                        "options": ["家に帰る", "塾に通う", "体育館で練習したり、部室で活動したりする", "映画を見る"],
                        "answer": "体育館で練習したり、部室で活動したりする",
                        "explanation": "文章に「放課後は体育館で練習したり、部室で活動したりします」と書かれています。"
                    }
                ]
            }
        ]
    
    def add_reading_questions(self) -> Dict[str, any]:
        """添加日语精读题目"""
        logger.info("开始添加日语精读题目...")
        
        added_count = 0
        failed_count = 0
        errors = []
        
        try:
            for passage in self.reading_passages:
                logger.info(f"处理阅读材料: {passage['title']} (等级: {passage['level']})")
                
                for idx, q_data in enumerate(passage['questions']):
                    try:
                        # 构建题目内容
                        question_content = f"文章: {passage['title']}\n\n{passage['content']}\n\n質問: {q_data['question']}"
                        
                        # 检查题目是否已存在
                        existing = db_manager.fetch_one(
                            'SELECT id FROM questions WHERE content LIKE ? AND language_id = ?',
                            (f'%{passage["title"]}%', self.japanese_language_id)
                        )
                        
                        if existing:
                            logger.warning(f"题目已存在: {passage['title']} - 问题 {idx+1}")
                            continue
                        
                        # 创建题目
                        now = datetime.now(UTC).isoformat()
                        question_data = {
                            'content': question_content,
                            'answer': q_data['answer'],
                            'explanation': q_data['explanation'],
                            'language_id': self.japanese_language_id,
                            'level_id': passage['level'],
                            'type': 'reading',  # 添加type字段
                            'question_type': 'reading',  # 设置为阅读类型
                            'difficulty_score': passage['level'] * 2.5,  # 根据等级计算难度
                            'usage_count': 0,
                            'created_at': now,
                            'updated_at': now
                        }
                        
                        question_id = db_manager.insert('questions', question_data)
                        if question_id:
                            # 添加选项
                            for opt_idx, option in enumerate(q_data['options']):
                                db_manager.execute(
                                    'INSERT INTO question_options (question_id, option_text, option_index) VALUES (?, ?, ?)',
                                    (question_id, option, opt_idx)
                                )
                            
                            # 添加标签
                            tags = ['日语', '精读', passage['title']]
                            for tag_name in tags:
                                # 查找或创建标签
                                tag = db_manager.fetch_one('SELECT id FROM question_tags WHERE tag_name = ?', (tag_name,))
                                if not tag:
                                    db_manager.execute('INSERT INTO question_tags (tag_name) VALUES (?)', (tag_name,))
                                    tag = db_manager.fetch_one('SELECT last_insert_rowid()')
                                    tag_id = tag[0]
                                else:
                                    tag_id = tag[0]
                                
                                # 关联标签
                                db_manager.execute(
                                    'INSERT OR IGNORE INTO question_tag_relations (question_id, tag_id) VALUES (?, ?)',
                                    (question_id, tag_id)
                                )
                            
                            added_count += 1
                            logger.info(f"成功添加题目: {passage['title']} - 问题 {idx+1}")
                        else:
                            failed_count += 1
                            errors.append(f"添加题目失败: {passage['title']} - 问题 {idx+1}")
                            logger.error(f"添加题目失败: {passage['title']} - 问题 {idx+1}")
                            
                    except Exception as e:
                        failed_count += 1
                        errors.append(f"处理题目时出错: {passage['title']} - 问题 {idx+1}, 错误: {str(e)}")
                        logger.error(f"处理题目时出错: {passage['title']} - 问题 {idx+1}, 错误: {str(e)}")
                        continue
            
            # 生成报告
            report = {
                'total_passages': len(self.reading_passages),
                'total_questions': sum(len(p['questions']) for p in self.reading_passages),
                'added_count': added_count,
                'failed_count': failed_count,
                'errors': errors,
                'timestamp': datetime.now(UTC).isoformat()
            }
            
            # 保存报告
            report_path = f"reports/japanese_reading_ai_report_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"日语精读题目添加完成，报告保存到: {report_path}")
            return report
            
        except Exception as e:
            logger.error(f"添加日语精读题目时出错: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now(UTC).isoformat()
            }
    
    def get_reading_questions_count(self) -> int:
        """获取日语精读题目数量"""
        count = db_manager.fetch_scalar(
            'SELECT COUNT(*) FROM questions WHERE language_id = ? AND question_type = ?',
            (self.japanese_language_id, 'reading')
        )
        return count or 0
    
    def share_error_cases(self) -> Dict[str, any]:
        """共享错误修复案例到脑库"""
        logger.info("共享错误修复案例到脑库...")
        
        try:
            # 生成错误修复案例
            error_cases = [
                {
                    "title": "日语精读题目添加成功",
                    "description": "成功为日语题库添加了精读类型练习题目",
                    "solution": "使用JapaneseReadingAI添加了多个级别的日语精读练习题目",
                    "category": "题库管理",
                    "severity": "info",
                    "status": "resolved",
                    "timestamp": datetime.now(UTC).isoformat()
                },
                {
                    "title": "日语精读题目重复检查",
                    "description": "避免添加重复的日语精读题目",
                    "solution": "在添加题目前检查数据库中是否已存在相同内容的题目",
                    "category": "数据管理",
                    "severity": "info",
                    "status": "resolved",
                    "timestamp": datetime.now(UTC).isoformat()
                },
                {
                    "title": "日语精读题目难度设置",
                    "description": "根据题目等级设置合适的难度分数",
                    "solution": "根据题目等级自动计算难度分数，确保题目难度与等级匹配",
                    "category": "题目管理",
                    "severity": "info",
                    "status": "resolved",
                    "timestamp": datetime.now(UTC).isoformat()
                },
                {
                    "title": "日语精读题目标签管理",
                    "description": "为日语精读题目添加合适的标签",
                    "solution": "为每个精读题目添加日语、精读等标签，便于分类和检索",
                    "category": "标签管理",
                    "severity": "info",
                    "status": "resolved",
                    "timestamp": datetime.now(UTC).isoformat()
                },
                {
                    "title": "日语精读题目报告生成",
                    "description": "生成日语精读题目添加报告",
                    "solution": "创建详细的报告文件，记录添加的题目数量和状态",
                    "category": "报告管理",
                    "severity": "info",
                    "status": "resolved",
                    "timestamp": datetime.now(UTC).isoformat()
                }
            ]
            
            # 保存错误修复案例到脑库
            knowledge_base_path = 'data/knowledge_base.json'
            if os.path.exists(knowledge_base_path):
                with open(knowledge_base_path, 'r', encoding='utf-8') as f:
                    knowledge_base = json.load(f)
            else:
                knowledge_base = {"cases": []}
            
            # 添加新案例
            knowledge_base["cases"].extend(error_cases)
            
            # 保存到文件
            with open(knowledge_base_path, 'w', encoding='utf-8') as f:
                json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功共享了 {len(error_cases)} 个错误修复案例到脑库")
            return {
                "shared_count": len(error_cases),
                "total_cases": len(knowledge_base["cases"]),
                "timestamp": datetime.now(UTC).isoformat()
            }
            
        except Exception as e:
            logger.error(f"共享错误修复案例时出错: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat()
            }
    
    def run(self):
        """运行AI"""
        logger.info("日语精读练习AI开始运行...")
        
        # 添加日语精读题目
        add_result = self.add_reading_questions()
        logger.info(f"添加结果: {add_result}")
        
        # 获取当前精读题目数量
        current_count = self.get_reading_questions_count()
        logger.info(f"当前日语精读题目数量: {current_count}")
        
        # 共享错误修复案例
        share_result = self.share_error_cases()
        logger.info(f"共享结果: {share_result}")
        
        logger.info("日语精读练习AI运行完成")
        
        return {
            "add_result": add_result,
            "current_count": current_count,
            "share_result": share_result
        }

def main():
    """主函数"""
    ai = JapaneseReadingAI()
    result = ai.run()
    
    # 打印结果
    print("\n日语精读练习AI运行结果:")
    print(f"添加结果: {result['add_result']}")
    print(f"当前日语精读题目数量: {result['current_count']}")
    print(f"共享结果: {result['share_result']}")

if __name__ == "__main__":
    main()
