#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI Project - 更新题库和脑库脚本
根据AI建议自动更新题库和脑库数据

import os
import sys
# JSON import removed - using database
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask-app'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_banks.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('update_banks')

class BankUpdater:
    """题库和脑库更新器"""

    def __init__(self):
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.brain_dir = os.path.join(self.project_dir, 'app', 'data', 'ai_brain')
        self.question_bank_dir = os.path.join(self.project_dir, 'app', 'data', 'question_bank')

        os.makedirs(self.brain_dir, exist_ok=True)
        os.makedirs(self.question_bank_dir, exist_ok=True)

        logger.info("题库和脑库更新器初始化完成")

    def update_question_bank(self):
        """更新题库"""
        logger.info("开始更新题库...")

        new_questions = self._generate_new_questions()

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        question_file = os.path.join(self.question_bank_dir, f'questions_{timestamp}.json')

        with open(question_file, 'w', encoding='utf-8') as f:
            json.dump(new_questions, f, ensure_ascii=False, indent=2)

        # 保存到数据库
        self._save_to_database(new_questions)

        logger.info(f"题库更新完成，新增 {len(new_questions)} 道题目")
        return len(new_questions)

    def _generate_new_questions(self):
        """生成新题目"""
        questions = []

        # 中文题目
        chinese_questions = [
            {
                "id": f"zh_{i}",
                "language": "中文",
                "type": "阅读理解",
                "level": "初级",
                "content": f"阅读以下短文并回答问题。短文主要讲述了{['春天的景色', '科技的发展', '文化的传承', '环境保护', '人际关系'][i%5]}的重要性。",
                "options": ["A. 选项一", "B. 选项二", "C. 选项三", "D. 选项四"],
                "answer": ["A", "B", "C", "D"][i%4],
                "analysis": "本题考查对文章主旨的理解能力。",
                "difficulty": 1 + (i % 3),
                "category": "语文",
                "created_at": datetime.now().isoformat()
            } for i in range(20)
        ]
        # 数学题目
        math_questions = [
            {
                "id": f"math_{i}",
                "type": "计算题",
                "level": ["初级", "中级", "高级"][i%3],
                "options": [str((i*10 + 5) + (i*5 + 3)), str((i*10 + 5) * (i*5 + 3)), str((i*10 + 5) - (i*5 + 3)), str((i*10 + 5) / (i*5 + 3))],
                "answer": "A",
                "analysis": "本题考查基本的数学运算能力。",
                "difficulty": 1 + (i % 3),
                "category": "数学",
                "created_at": datetime.now().isoformat()
            } for i in range(20)
        # 英语题目
        english_questions = [
                "id": f"en_{i}",
                "level": ["初级", "中级", "高级"][i%3],
                "content": f"Choose the correct word: The weather is ____ today.",
                "options": ["sunny", "sun", "sunnily", "sunshine"],
                "answer": "A",
                "analysis": "本题考查形容词的用法。",
                "difficulty": 1 + (i % 3),
                "category": "英语",
                "created_at": datetime.now().isoformat()
            } for i in range(20)
        # 日语题目
            {
                "id": f"jp_{i}",
                "content": f"次の単語の正しい意味を選んでください: 「{['春', '夏', '秋', '冬'][i%4]}」",
                "options": ["Spring", "Summer", "Autumn", "Winter"],
                "analysis": "この問題は日本語の単語の意味をテストします。",
                "difficulty": 1 + (i % 3),
                "category": "日语",
                "created_at": datetime.now().isoformat()
            } for i in range(10)
        ]
        # 综合题目
            {
                "id": f"gen_{i}",
                "type": ["常识", "逻辑推理", "数据分析"][i%3],
                "options": ["A. 选项一", "B. 选项二", "C. 选项三", "D. 选项四"],
                "difficulty": 2 + (i % 3),
                "category": "综合",
            } for i in range(15)
        ]
        questions.extend(chinese_questions)
        questions.extend(math_questions)
        questions.extend(english_questions)
        questions.extend(general_questions)
        return questions

    def _save_to_database(self, questions):
        """保存到数据库"""
        try:
            import sqlite3

            cursor = conn.cursor()

            for q in questions:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO exam_questions
                        (question_id, language, type, level, content, options, answer, analysis, difficulty, category, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        q['id'],
                        q['language'],
                        q['type'],
                        q['level'],
                        q['content'],
                        str(q['options']),
                        q['answer'],
                        q['analysis'],
                        q['difficulty'],
                        q['category'],
                        q['created_at']
                    ))
                except Exception as e:
                    logger.warning(f"保存题目失败 {q['id']}: {str(e)}")

            conn.commit()
            conn.close()
            logger.info("题库已保存到数据库")
        except Exception as e:
            logger.warning(f"数据库保存失败: {str(e)}")

    def update_brain_database(self):
        """更新脑库"""

        new_knowledge = self._generate_new_knowledge()

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        brain_file = os.path.join(self.brain_dir, f'brain_update_{timestamp}.json')

        with open(brain_file, 'w', encoding='utf-8') as f:
            json.dump(new_knowledge, f, ensure_ascii=False, indent=2)

        self._merge_to_brain_database(new_knowledge)

        logger.info(f"脑库更新完成，新增 {len(new_knowledge)} 条知识")
        return len(new_knowledge)

    def _generate_new_knowledge(self):
        """生成新知识"""
        knowledge_items = []

        # AI相关知识
        ai_knowledge = [
            {
                "id": f"ai_{i}",
                "category": "AI知识",
                "subcategory": ["机器学习", "深度学习", "自然语言处理", "计算机视觉", "强化学习"][i%5],
                "content": f"这是关于{['神经网络', '深度学习', '自然语言处理', '计算机视觉', '强化学习'][i%5]}的详细知识内容，包括核心概念、算法原理和应用场景。",
                "metadata": {
                    "confidence": 0.95,
                    "relevance": 0.88,
                    "tags": ["AI", "机器学习", "技术"]
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            } for i in range(15)
        ]
        # 安全知识
        security_knowledge = [
            {
                "id": f"sec_{i}",
                "category": "安全知识",
                "subcategory": ["网络安全", "数据保护", "身份认证", "攻击防护", "安全策略"][i%5],
                "title": f"{['网络安全基础', '数据加密技术', '身份认证方法', '攻击检测', '安全合规'][i%5]}",
                "content": f"这是关于{['网络安全', '数据保护', '身份认证', '攻击防护', '安全策略'][i%5]}的详细知识内容，包括安全原理、防护方法和最佳实践。",
                "metadata": {
                    "source": "安全知识库",
                    "relevance": 0.85,
                    "tags": ["安全", "网络安全", "防护"]
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            } for i in range(10)
        ]
        # 系统知识
        system_knowledge = [
            {
                "id": f"sys_{i}",
                "category": "系统知识",
                "subcategory": ["系统架构", "性能优化", "故障排查", "运维管理", "自动化"][i%5],
                "title": f"{['系统架构设计', '性能调优技巧', '故障诊断方法', '运维最佳实践', '自动化部署'][i%5]}",
                "content": f"这是关于{['系统架构', '性能优化', '故障排查', '运维管理', '自动化'][i%5]}的详细知识内容，包括设计原则、优化策略和实践经验。",
                "metadata": {
                    "source": "系统知识库",
                    "confidence": 0.90,
                    "tags": ["系统", "运维", "架构"]
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            } for i in range(10)
        ]
        # 规则知识
        rule_knowledge = [
            {
                "id": f"rule_{i}",
                "category": "规则知识",
                "subcategory": ["业务规则", "安全规则", "系统规则", "策略规则", "合规规则"][i%5],
                "title": f"{['业务规则引擎', '安全规则配置', '系统规则管理', '策略规则制定', '合规规则遵循'][i%5]}",
                "content": f"这是关于{['业务规则', '安全规则', '系统规则', '策略规则', '合规规则'][i%5]}的详细知识内容，包括规则定义、执行引擎和管理方法。",
                "metadata": {
                    "confidence": 0.93,
                    "relevance": 0.86,
                },
                "created_at": datetime.now().isoformat(),
            } for i in range(10)
        ]
        learning_knowledge = [
                "id": f"learn_{i}",
                "category": "学习知识",
                "subcategory": ["学习方法", "知识管理", "技能提升", "持续学习", "知识分享"][i%5],
                "title": f"{['高效学习方法', '知识管理技巧', '技能提升策略', '持续学习计划', '知识分享机制'][i%5]}",
                "content": f"这是关于{['学习方法', '知识管理', '技能提升', '持续学习', '知识分享'][i%5]}的详细知识内容，包括学习策略、知识组织和分享方法。",
                "metadata": {
                    "source": "学习知识库",
                    "confidence": 0.88,
                    "relevance": 0.80,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            } for i in range(10)
        knowledge_items.extend(ai_knowledge)
        knowledge_items.extend(security_knowledge)
        knowledge_items.extend(system_knowledge)
        knowledge_items.extend(rule_knowledge)

        return knowledge_items
    def _merge_to_brain_database(self, knowledge):
        """合并到脑库数据库"""
        try:
            import sqlite3
            db_path = os.path.join(self.project_dir, 'flask-app', 'app.db')

            conn = sqlite3.connect(db_path)

            # 创建表（如果不存在）
                CREATE TABLE IF NOT EXISTS ai_brain (
                    id TEXT PRIMARY KEY,
                    category TEXT,
                    subcategory TEXT,
                    title TEXT,
                    content TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )

            for item in knowledge:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO ai_brain
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        item['id'],
                        item['subcategory'],
                        item['title'],
                        item['content'],
                        str(item['metadata']),
                        item['created_at'],
                        item['updated_at']
                    ))
                    logger.warning(f"保存知识失败 {item['id']}: {str(e)}")

            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"脑库数据库保存失败: {str(e)}")

        """运行完整的更新流程"""
        logger.info("="*60)
        logger.info("="*60)
        print("\n" + "="*60)
        print("           更新题库和脑库")

        question_count = self.update_question_bank()

        print("正在更新脑库...")

        print("\n" + "-"*40)
        print("更新结果:")
        print("-"*40)
        print(f"题库新增题目: {question_count} 道")
        print(f"脑库新增知识: {knowledge_count} 条")

        print("题库和脑库更新完成")
        print("="*60)

        # 生成更新报告
        self._generate_report(question_count, knowledge_count)

    def _generate_report(self, question_count, knowledge_count):
        report = {
            'timestamp': datetime.now().isoformat(),
            'type': '题库和脑库更新报告',
            'question_bank_update': {
                'new_questions': question_count,
                'file': f'questions_{datetime.now().strftime("%Y%m%d%H%M%S")}.json'
            },
            'brain_database_update': {
                'new_knowledge': knowledge_count,
                'categories': ['AI知识', '安全知识', '系统知识', '规则知识', '学习知识'],
                'file': f'brain_update_{datetime.now().strftime("%Y%m%d%H%M%S")}.json'
            },
            'summary': {
                'total_new_items': question_count + knowledge_count,
                'brain_database_items': knowledge_count
        }

        report_path = os.path.join(self.project_dir, f"bank_update_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
        logger.info(f"更新报告已保存: {report_path}")
def main():
    """主函数"""
    updater = BankUpdater()
    updater.run_update()

if __name__ == "__main__":
    main()
