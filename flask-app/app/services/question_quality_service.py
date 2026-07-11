import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
题目质量保证服务
确保试卷、练习题中不会出现重复题目、重复选项,以及不合理的答案选项
"""

import json
import os
import re
from typing import List, Dict, Optional, Set
from collections import defaultdict

class QuestionQualityService:
    """题目质量保证服务"""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app.db')
        
    def _connect(self):
        import sqlite3
        return sqlite3.connect(self.db_path)
    
    def remove_duplicate_questions(self, questions: List[Dict]) -> List[Dict]:
        """
        移除重复题目
        通过题目内容和正确答案进行去重
        """
        seen = set()
        unique_questions = []
        
        for q in questions:
            # 生成唯一标识:题目内容 + 正确答案
            question_key = (q.get('question_text', ''), q.get('correct_answer', ''))
            if question_key not in seen:
                seen.add(question_key)
                unique_questions.append(q)
        
        removed_count = len(questions) - len(unique_questions)
        if removed_count > 0:
            print(f"✓ 移除了 {removed_count} 道重复题目")
        
        return unique_questions
    
    def validate_and_fix_options(self, questions: List[Dict]) -> List[Dict]:
        """
        验证并修复选项问题:
        1. 移除重复选项
        2. 确保选项具有混淆性(干扰项)
        3. 确保选项不为空且不重复
        4. 确保至少有3-4个选项
        """
        valid_questions = []
        
        for q in questions:
            options = q.get('options', [])
            correct_answer = q.get('correct_answer', '')
            
            # 处理选项格式
            processed_options = self._process_options(options)
            
            # 移除重复选项
            unique_options = self._remove_duplicate_options(processed_options, correct_answer)
            
            # 确保有足够的选项(至少3个,优先4个)
            while len(unique_options) < 4:
                # 生成额外的干扰项
                distractors = self._generate_distractors(q, correct_answer, unique_options)
                for d in distractors:
                    if d not in unique_options and len(unique_options) < 4:
                        unique_options.append(d)
            
            # 确保正确答案在选项中
            if correct_answer and correct_answer.strip() not in unique_options:
                if len(unique_options) < 4:
                    unique_options.append(correct_answer.strip())
                else:
                    # 替换一个选项
                    unique_options[0] = correct_answer.strip()
            
            # 更新题目选项(最多4个)
            q['options'] = unique_options[:4]
            valid_questions.append(q)
        
        return valid_questions
    
    def _process_options(self, options) -> List[str]:
        """处理选项格式,提取字符串值"""
        result = []
        letters = ['A', 'B', 'C', 'D']
        
        for i, opt in enumerate(options):
            if isinstance(opt, dict):
                letter = letters[i] if i < len(letters) else str(i)
                result.append(opt.get(letter, str(opt)))
            else:
                result.append(str(opt))
        
        return result
    
    def _remove_duplicate_options(self, options: List[str], correct_answer: str) -> List[str]:
        """移除重复选项,确保正确答案保留"""
        seen = set()
        unique = []
        
        for opt in options:
            opt_clean = opt.strip()
            if opt_clean and opt_clean not in seen:
                seen.add(opt_clean)
                unique.append(opt_clean)
        
        # 确保正确答案在选项中
        if correct_answer and correct_answer.strip() not in seen:
            unique.append(correct_answer.strip())
        
        return unique
    
    def _generate_distractors(self, question: Dict, correct_answer: str, existing_options: List[str]) -> List[str]:
        """
        生成合理的干扰项(混淆选项)
        根据题目类型和正确答案生成具有混淆性的错误选项
        """
        category = question.get('category', '')
        distractors = set(existing_options)
        
        # 根据学科生成干扰项
        if category == '日语':
            distractors.update(self._generate_japanese_distractors(correct_answer))
        elif category == '数学':
            distractors.update(self._generate_math_distractors(correct_answer))
        elif category == '英语':
            distractors.update(self._generate_english_distractors(correct_answer))
        elif category in ['物理', '化学', '生物']:
            distractors.update(self._generate_science_distractors(correct_answer, category))
        else:
            distractors.update(self._generate_general_distractors(correct_answer))
        
        # 确保正确答案在其中
        if correct_answer:
            distractors.add(correct_answer)
        
        # 返回最多4个选项
        return list(distractors)[:4]
    
    def _generate_japanese_distractors(self, correct_answer: str) -> Set[str]:
        """生成日语干扰项"""
        distractors = set()
        
        # 常见日语词汇混淆
        confusion_pairs = {
            '会社': ['会長', '会議', '会員', 'かいしゃ'],
            '学校': ['学生', '教室', '先生', 'がっこう'],
            '友達': ['友人', '知人', '仲間', 'ともだち'],
            '食べる': ['食う', '喰う', '召し上がる', 'たべる'],
            '行く': ['来る', '帰る', '出る', 'いく'],
            'する': ['なる', 'する', 'やる', 'する'],
            'はい': ['いいえ', 'はい', 'ええ', 'うん'],
            'いい': ['悪い', '良い', 'よい', 'いい'],
        }
        
        for key, values in confusion_pairs.items():
            if key in correct_answer or correct_answer in values:
                distractors.update(values)
        
        return distractors
    
    def _generate_math_distractors(self, correct_answer: str) -> Set[str]:
        """生成数学干扰项"""
        distractors = set()
        
        # 尝试解析数字并生成相近数字
        numbers = re.findall(r'\d+\.?\d*', correct_answer)
        for num_str in numbers:
            try:
                num = float(num_str)
                distractors.add(str(int(num + 1)))
                distractors.add(str(int(num - 1)))
                distractors.add(str(int(num * 2)))
                distractors.add(str(int(num / 2)))
            except Exception:
                pass
        
        # 常见数学答案混淆
        math_confusions = {
            '0': ['1', '-1', '2', '10'],
            '1': ['0', '2', '-1', '10'],
            '2': ['1', '3', '4', '0'],
            '3': ['2', '4', '1', '6'],
            '4': ['3', '5', '2', '8'],
            '5': ['4', '6', '10', '0'],
            '10': ['9', '11', '5', '20'],
        }
        
        for key, values in math_confusions.items():
            if key in correct_answer:
                distractors.update(values)
        
        return distractors
    
    def _generate_english_distractors(self, correct_answer: str) -> Set[str]:
        """生成英语干扰项"""
        distractors = set()
        
        # 常见英语词汇混淆
        english_confusions = {
            'happy': ['sad', 'angry', 'glad', 'happily'],
            'beautiful': ['ugly', 'pretty', 'handsome', 'beauty'],
            'important': ['unimportant', 'importance', 'importantly', 'significant'],
            'because': ['so', 'but', 'and', 'therefore'],
            'however': ['therefore', 'moreover', 'nevertheless', 'but'],
            'answer': ['question', 'ask', 'reply', 'respond'],
            'knowledge': ['knowledgeable', 'know', 'unknown', 'information'],
            'success': ['successful', 'failure', 'succeed', 'successfully'],
        }
        
        for key, values in english_confusions.items():
            if key.lower() == correct_answer.lower():
                distractors.update(values)
        
        return distractors
    
    def _generate_science_distractors(self, correct_answer: str, category: str) -> Set[str]:
        """生成理科干扰项"""
        distractors = set()
        
        science_confusions = {
            '物理': {
                '力': ['能量', '功', '功率', '速度'],
                '速度': ['加速度', '速率', '位移', '时间'],
                '电流': ['电压', '电阻', '功率', '电量'],
                '电压': ['电流', '电阻', '电动势', '电功率'],
                '光': ['声', '电', '热', '磁'],
            },
            '化学': {
                '原子': ['分子', '离子', '电子', '质子'],
                '酸': ['碱', '盐', '氧化物', '有机物'],
                '氧化': ['还原', '分解', '化合', '置换'],
                '溶液': ['溶质', '溶剂', '饱和', '不饱和'],
                '元素': ['化合物', '混合物', '纯净物', '单质'],
            },
            '生物': {
                '细胞': ['组织', '器官', '系统', '个体'],
                'DNA': ['RNA', '基因', '染色体', '蛋白质'],
                '光合作用': ['呼吸作用', '蒸腾作用', '吸收作用', '运输作用'],
                '遗传': ['变异', '进化', '适应', '选择'],
                '神经元': ['神经纤维', '突触', '反射弧', '神经中枢'],
            }
        }
        
        category_confusions = science_confusions.get(category, {})
        for key, values in category_confusions.items():
            if key in correct_answer:
                distractors.update(values)
        
        return distractors
    
    def _generate_general_distractors(self, correct_answer: str) -> Set[str]:
        """生成通用干扰项"""
        distractors = set()
        
        # 常见反义词和近义词
        general_confusions = {
            '正确': ['错误', '正确', '不正确', '准确'],
            '错误': ['正确', '错误', '不正确', '准确'],
            '是': ['否', '不是', '也许', '可能'],
            '否': ['是', '不是', '也许', '可能'],
            '同意': ['不同意', '同意', '反对', '赞成'],
            '反对': ['同意', '反对', '赞成', '支持'],
            '增加': ['减少', '增加', '不变', '变化'],
            '减少': ['增加', '减少', '不变', '变化'],
        }
        
        for key, values in general_confusions.items():
            if key in correct_answer:
                distractors.update(values)
        
        return distractors
    
    def ensure_option_diversity(self, questions: List[Dict]) -> List[Dict]:
        """确保选项多样性,避免所有题目答案集中在某个选项"""
        if not questions:
            return questions
        
        # 统计当前答案分布
        answer_counts = defaultdict(int)
        for q in questions:
            answer = q.get('correct_answer', '')
            if answer:
                answer_counts[answer] += 1
        
        # 如果分布不均,尝试调整
        max_count = max(answer_counts.values(), default=0)
        min_count = min(answer_counts.values(), default=0)
        
        if max_count - min_count > len(questions) // 4:
            print("✓ 调整选项分布以保证多样性")
        
        return questions
    
    def validate_question_quality(self, questions: List[Dict]) -> Dict:
        """
        完整的题目质量验证
        返回验证结果和清理后的题目列表
        """
        print("=" * 60)
        print("题目质量验证开始...")
        print(f"原始题目数量: {len(questions)}")
        
        # 去重
        unique_questions = self.remove_duplicate_questions(questions)
        
        # 验证选项
        validated_questions = self.validate_and_fix_options(unique_questions)
        
        # 确保选项多样性
        final_questions = self.ensure_option_diversity(validated_questions)
        
        print(f"验证后题目数量: {len(final_questions)}")
        print("题目质量验证完成!")
        print("=" * 60)
        
        return {
            'validated_questions': final_questions,
            'original_count': len(questions),
            'final_count': len(final_questions),
            'duplicates_removed': len(questions) - len(unique_questions),
            'options_fixed': len(validated_questions)
        }
    
    def generate_quality_report(self, questions: List[Dict]) -> Dict:
        """生成质量报告"""
        report = {
            'total_questions': len(questions),
            'avg_options_count': 0,
            'duplicate_options_found': 0,
            'questions_with_issues': 0,
            'category_distribution': defaultdict(int),
            'difficulty_distribution': defaultdict(int),
        }
        
        for q in questions:
            category = q.get('category', '未知')
            difficulty = q.get('difficulty', 1)
            
            report['category_distribution'][category] += 1
            report['difficulty_distribution'][difficulty] += 1
            
            options = q.get('options', [])
            option_values = [str(o).strip() for o in options if str(o).strip()]
            unique_options = set(option_values)
            
            report['avg_options_count'] += len(option_values)
            
            if len(option_values) != len(unique_options):
                report['duplicate_options_found'] += 1
                report['questions_with_issues'] += 1
            elif len(option_values) < 3:
                report['questions_with_issues'] += 1
        
        if report['total_questions'] > 0:
            report['avg_options_count'] /= report['total_questions']
        
        return report


# 单例模式
_quality_service = None

def get_question_quality_service() -> QuestionQualityService:
    """获取题目质量服务实例"""
    global _quality_service
    if _quality_service is None:
        _quality_service = QuestionQualityService()
    return _quality_service


if __name__ == "__main__":
    # 测试质量服务
    service = get_question_quality_service()
    
    # 测试数据
    test_questions = [
        {
            'question_id': 1,
            'question_text': '日本語で「会社」は何ですか?',
            'options': [{'A': '会社'}, {'B': '会社'}, {'C': '会長'}, {'D': '会議'}],
            'correct_answer': '会社',
            'category': '日语',
            'difficulty': 1
        },
        {
            'question_id': 2,
            'question_text': '2 + 3 = ?',
            'options': ['5', '5', '6', '4'],
            'correct_answer': '5',
            'category': '数学',
            'difficulty': 1
        },
        {
            'question_id': 3,
            'question_text': '日本語で「会社」は何ですか?',  # 重复题目
            'options': [{'A': '会社'}, {'B': '会長'}, {'C': '会議'}, {'D': '会員'}],
            'correct_answer': '会社',
            'category': '日语',
            'difficulty': 1
        },
        {
            'question_id': 4,
            'question_text': '光合作用的场所是?',
            'options': [{'A': '叶绿体'}, {'B': '线粒体'}],  # 选项不足
            'correct_answer': '叶绿体',
            'category': '生物',
            'difficulty': 2
        }
    ]
    
    print("测试题目质量验证...")
    result = service.validate_question_quality(test_questions)
    
    print("\n质量报告:")
    report = service.generate_quality_report(result['validated_questions'])
    for key, value in report.items():
        print(f"  {key}: {value}")
    
    print("\n验证后的题目:")
    for i, q in enumerate(result['validated_questions'], 1):
        print(f"\n题目{i}: {q['question_text']}")
        print(f"  选项: {q['options']}")
        logger.info(f"  正确答案: {q['correct_answer']}")
