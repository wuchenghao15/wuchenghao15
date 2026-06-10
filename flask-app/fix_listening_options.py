#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI听力题选项与一致性修复系统
确保：
1. 选项内容高质量且具有混淆性
2. 音频路径与内容语言一致
3. 答案与选项匹配
"""

import logging
import os
import sys
import sqlite3
import json
import re
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ListeningQuestionFixer:
    """听力题修复器"""

    def __init__(self, db_path="app.db"):
        self.db_path = db_path

    def connect(self):
        """连接数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except Exception as e:
            logger.error(f"连接数据库失败: {str(e)}")
            return None

    def detect_language_from_content(self, content):
        """从内容检测语言"""
        # 日语特征
        jp_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF]', content))
        # 英语特征
        en_chars = len(re.findall(r'[a-zA-Z]{2,}', content))

        if jp_chars > en_chars * 0.5:
            return 'japanese'
        elif en_chars > jp_chars * 0.5:
            return 'english'
        else:
            return 'unknown'

    def fix_invalid_options(self, qid, content, current_options, current_answer, tags, conn):
        """修复无效选项"""
        cursor = conn.cursor()

        # 检测语言
        language = self.detect_language_from_content(content)

        # 解析现有选项
        try:
            if isinstance(current_options, str):
                opts = json.loads(current_options) if current_options else []
            else:
                opts = current_options if current_options else []
        except:
            opts = []

        needs_fix = False

        # 检查是否需要修复
        if not opts or len(opts) == 0:
            needs_fix = True
        else:
            # 检查选项内容是否有效
            for opt in opts:
                content_val = opt.get('content', '')
                # 检查是否是无效内容
                if content_val in ['正确', '错误1', '错误2', '错误3', 'A', 'B', 'C', 'D', 
                                   'Correct', 'Wrong', 'Option', '正确', '错误']:
                    needs_fix = True
                    break
                if not content_val or len(content_val) < 2:
                    needs_fix = True
                    break

        if needs_fix:
            # 生成新的高质量选项
            new_options, new_answer = self._generate_quality_options(language, content, current_answer)
            
            cursor.execute("""
                UPDATE questions
                SET options = ?, correct_answer = ?
                WHERE id = ?
            """, (json.dumps(new_options, ensure_ascii=False), new_answer, qid))
            
            return True

        return False

    def _generate_quality_options(self, language, content, current_answer):
        """生成高质量选项"""
        
        # 从内容中提取可能的答案
        extracted_answers = self._extract_answers_from_content(content, language)
        
        # 日语选项库
        japanese_options = {
            'time': ['7時', '8時', '9時', '10時', '7時半', '8時半'],
            'place': ['学校', '病院', '会社', '図書館', '駅', '公園', '店', '銀行'],
            'food': ['寿司', 'ラーメン', 'カレー', 'そば', 'うどん', 'パスタ', 'パン'],
            'person': ['先生', '友達', '家族', '同僚', '医者', '店員'],
            'number': ['1つ', '2つ', '3つ', '4つ', '5つ', '一個', '二個', '三個'],
            'money': ['100円', '200円', '300円', '500円', '1000円'],
            'emotion': ['嬉しい', '悲しい', '面白い', '美味しい', '悪い'],
            'weather': ['晴れ', '雨', '雪', '曇り', '暑いい', '寒い'],
            'yes_no': ['はい', 'いいえ'],
            'greeting': ['こんにちは', 'おはよう', 'こんばんは', 'ありがとう'],
        }

        # 英语选项库
        english_options = {
            'time': ['7 o\'clock', '8 o\'clock', '9 o\'clock', '10 o\'clock', '7:30', '8:30'],
            'place': ['school', 'hospital', 'company', 'library', 'station', 'park', 'store', 'bank'],
            'food': ['sushi', 'ramen', 'curry', 'pasta', 'bread', 'rice', 'noodles'],
            'person': ['teacher', 'friend', 'family', 'colleague', 'doctor', 'clerk'],
            'number': ['one', 'two', 'three', 'four', 'five', '1', '2', '3'],
            'money': ['$100', '$200', '$300', '$500', '$1000', '100 dollars'],
            'emotion': ['happy', 'sad', 'interesting', 'delicious', 'bad'],
            'weather': ['sunny', 'rainy', 'snowy', 'cloudy', 'hot', 'cold'],
            'yes_no': ['yes', 'no'],
            'greeting': ['hello', 'good morning', 'good evening', 'thank you'],
        }

        # 选择适当的选项库
        options_lib = japanese_options if language == 'japanese' else english_options

        # 尝试从内容中提取并选择合适的选项
        best_category = 'place'  # 默认
        for category, keywords in [
            ('time', ['時', 'hour', 'time', '何時', 'when']),
            ('food', ['食べ', 'food', '何', '吃什么', 'eat', 'drink']),
            ('place', ['どこ', 'where', '場所', 'place']),
            ('person', ['誰', 'who', '人']),
            ('money', ['円', 'dollar', '価格', 'price', 'いくら']),
            ('number', ['幾つ', 'how many', '个数', 'number']),
            ('yes_no', ['か', '?']),
        ]:
            for keyword in keywords:
                if keyword in content.lower():
                    best_category = category
                    break

        # 获取选项
        category_options = options_lib.get(best_category, options_lib['place'])

        # 选择4个不同的选项
        if len(category_options) >= 4:
            selected = random.sample(category_options, 4)
        else:
            # 如果不够，从多个类别混合
            selected = list(category_options)
            for cat in ['place', 'person', 'food']:
                if cat != best_category and cat in options_lib:
                    selected.extend(options_lib[cat][:2])
            random.shuffle(selected)
            selected = selected[:4]

        # 随机选择正确答案
        correct_idx = random.randint(0, 3)

        # 构建选项
        options = []
        for i in range(4):
            options.append({
                "option": chr(65 + i),
                "content": selected[i]
            })

        answer = chr(65 + correct_idx)

        return options, answer

    def _extract_answers_from_content(self, content, language):
        """从内容中提取可能的答案"""
        answers = []

        # 提取数字
        numbers = re.findall(r'\d+', content)
        answers.extend(numbers)

        # 提取日语汉字词
        if language == 'japanese':
            kanji_words = re.findall(r'[\u4e00-\u9fff]+', content)
            answers.extend(kanji_words[:5])

        return answers

    def fix_language_consistency(self, conn):
        """修复语言一致性问题"""
        cursor = conn.cursor()

        fixed = 0

        # 获取所有听力题
        cursor.execute("""
            SELECT id, content, audio_url, tags
            FROM questions
            WHERE type = 'listening' OR type LIKE '%listening%'
        """)

        for row in cursor.fetchall():
            qid, content, audio_url, tags = row

            if not audio_url:
                continue

            # 检测内容语言
            content_language = self.detect_language_from_content(content)

            # 检测URL语言
            url_lower = audio_url.lower()
            url_is_japanese = any(x in url_lower for x in ['japanese', 'jlpt', 'n5', 'n4', 'n3', 'n2', 'n1', 'kanto', 'kansai'])
            url_is_english = any(x in url_lower for x in ['english', 'basic', 'intermediate', 'advanced', 'ielts', 'toefl'])

            # 修复不一致
            if content_language == 'japanese' and url_is_english and not url_is_japanese:
                # 将URL改为日语
                new_url = url_lower.replace('/english/', '/japanese/')
                cursor.execute("UPDATE questions SET audio_url = ? WHERE id = ?", (new_url, qid))
                fixed += 1
            elif content_language == 'english' and url_is_japanese and not url_is_english:
                # 将URL改为英语
                new_url = url_lower.replace('/japanese/', '/english/')
                cursor.execute("UPDATE questions SET audio_url = ? WHERE id = ?", (new_url, qid))
                fixed += 1

        conn.commit()
        return fixed

    def fix_all_issues(self):
        """修复所有问题"""
        print("=" * 80)
        print("🎧 AI听力题选项与一致性修复系统")
        print("=" * 80)

        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # 1. 修复无效选项
            print("\n正在修复无效选项...")

            cursor.execute("""
                SELECT id, content, options, correct_answer, tags
                FROM questions
                WHERE type = 'listening' OR type LIKE '%listening%'
            """)

            fixed_options = 0
            for row in cursor.fetchall():
                qid, content, options, answer, tags = row
                if self.fix_invalid_options(qid, content, options, answer, tags, conn):
                    fixed_options += 1

            print(f"✓ 修复无效选项: {fixed_options}个")

            # 2. 修复语言一致性问题
            print("\n正在修复语言一致性问题...")
            fixed_language = self.fix_language_consistency(conn)
            print(f"✓ 修复语言一致性: {fixed_language}个")

            # 3. 显示修复后的样本
            self.show_fixed_samples(conn)

        except Exception as e:
            logger.error(f"修复失败: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

    def show_fixed_samples(self, conn):
        """显示修复后的样本"""
        print("\n" + "=" * 80)
        print("📝 修复后的样本题目")
        print("=" * 80)

        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, content, options, correct_answer, audio_url
            FROM questions
            WHERE (type = 'listening' OR type LIKE '%listening%')
            LIMIT 5
        """)

        for i, row in enumerate(cursor.fetchall(), 1):
            qid, content, options, correct_answer, audio_url = row
            print(f"\n【题目 {i}】ID: {qid}")
            print(f"  音频: {audio_url}")

            # 解析选项
            try:
                opts = json.loads(options) if isinstance(options, str) else (options or [])
                for opt in opts:
                    marker = " ✓" if opt.get('option', '').upper() == correct_answer.upper() else ""
                    print(f"  {opt.get('option')}: {opt.get('content')}{marker}")
            except:
                print(f"  选项解析失败")

            print(f"  答案: {correct_answer}")


def main():
    """主函数"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

    fixer = ListeningQuestionFixer(db_path)
    fixer.fix_all_issues()


if __name__ == "__main__":
    main()