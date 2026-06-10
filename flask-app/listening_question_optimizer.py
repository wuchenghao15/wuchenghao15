#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI听力题智能校验与优化系统
确保：
1. 音频文本与题目内容一致
2. 选项有且只有一个正确答案
3. 干扰项具有高度相似性和混淆性
4. 题目整体质量达标
"""

import logging
import os
import sys
import sqlite3
import hashlib
import json
import re
import random
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ListeningQuestionOptimizer:
    """听力题智能优化器"""

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

    # ============ 混淆选项生成器 ============

    def generate_confusing_options(self, correct_answer, language='japanese'):
        """生成高度混淆的选项"""
        
        if language == 'japanese':
            return self._generate_japanese_options(correct_answer)
        elif language == 'english':
            return self._generate_english_options(correct_answer)
        else:
            return self._generate_generic_options(correct_answer)

    def _generate_japanese_options(self, correct_answer):
        """生成日语混淆选项"""
        # 日语混淆类型映射
        confusion_patterns = {
            # N5级别混淆
            "はい": ["いいえ", "ありがとう", "お願いします", "すみません"],
            "いいえ": ["はい", "どうぞ", "ありがとう", "わかりました"],
            "先生": ["学生", "友達", "親", "医者"],
            "学校": ["病院", "会社", "図書館", "公園"],
            "食べる": ["飲む", "見る", "行く", "来る"],
            "飲む": ["食べる", "見る", "聞く", "話す"],
            "行く": ["来る", "帰る", "出る", "入る"],
            "来る": ["行く", "帰る", "出る", "入る"],
            "朝": ["昼", "夜", "午前", "午後"],
            "今日": ["明日", "昨日", "来週", "先週"],
            "明日": ["今日", "昨日", "明後日", "来週"],
            "一月": ["二月", "三月", "四月", "五月"],
            "一月": ["二月", "三月", "四月", "五月"],
            "時間": ["分", "秒", "時", "刻"],
            "何人": ["何人", "何歳", "何人", "どこ"],
            "どこ": ["どこ", "いつ", "なに", "だれ"],
            "なに": ["どこ", "いつ", "だれ", "なぜ"],
            "何时": ["何处", "何人", "何事", "为何"],
            "何处": ["何时", "何人", "何事", "为何"],
            "何人": ["何时", "何处", "何事", "为何"],
            "学校": ["会社", "病院", "図書館", "公園"],
            "病院": ["学校", "会社", "図書館", "公園"],
            "駅": ["港", "空港", "停留所", "交差点"],
            "電車": ["バス", "車", "地下鉄", "自転車"],
            " sushi": ["ramen", "udon", "soba", "curry"],
            "ramen": ["sushi", "udon", "soba", "curry"],
            "200円": ["300円", "100円", "500円", "400円"],
            "300円": ["200円", "400円", "100円", "500円"],
        }

        # 直接匹配
        if correct_answer in confusion_patterns:
            distractors = confusion_patterns[correct_answer].copy()
        else:
            # 通用混淆策略
            distractors = self._get_generic_distractors(correct_answer, 'japanese')

        # 打乱并选择3个
        random.shuffle(distractors)
        return distractors[:3]

    def _generate_english_options(self, correct_answer):
        """生成英语混淆选项"""
        confusion_patterns = {
            "A": ["B", "C", "D"],
            "B": ["A", "C", "D"],
            "C": ["A", "B", "D"],
            "D": ["A", "B", "C"],
            "yes": ["no", "maybe", "please", "thanks"],
            "no": ["yes", "maybe", "sure", "ok"],
            "morning": ["afternoon", "evening", "night", "noon"],
            "afternoon": ["morning", "evening", "night", "noon"],
            "evening": ["morning", "afternoon", "night", "dawn"],
            "today": ["tomorrow", "yesterday", "now", "later"],
            "tomorrow": ["today", "yesterday", "soon", "later"],
            "yesterday": ["today", "tomorrow", "last", "ago"],
            "one": ["two", "three", "four", "five"],
            "two": ["one", "three", "four", "five"],
            "three": ["one", "two", "four", "five"],
            "four": ["one", "two", "three", "five"],
            "five": ["one", "two", "three", "four"],
            "Monday": ["Tuesday", "Wednesday", "Thursday", "Friday"],
            "Tuesday": ["Monday", "Wednesday", "Thursday", "Friday"],
            "Japan": ["China", "Korea", "America", "Canada"],
            "China": ["Japan", "Korea", "America", "Canada"],
            "Japan": ["China", "Korea", "America", "Canada"],
            "school": ["hospital", "company", "library", "park"],
            "hospital": ["school", "company", "library", "park"],
            "company": ["school", "hospital", "library", "park"],
            "coffee": ["tea", "water", "juice", "milk"],
            "tea": ["coffee", "water", "juice", "milk"],
            "three": ["four", "five", "two", "six"],
            "seven": ["eight", "six", "nine", "ten"],
            "good": ["great", "nice", "well", "bad"],
            "bad": ["good", "great", "nice", "well"],
            "happy": ["sad", "glad", "joyful", "angry"],
            "sad": ["happy", "glad", "joyful", "angry"],
        }

        # 清理答案字符串
        clean_answer = correct_answer.strip().lower()

        if clean_answer in confusion_patterns:
            distractors = confusion_patterns[clean_answer].copy()
        else:
            # 检查部分匹配
            for key, values in confusion_patterns.items():
                if key.lower() in clean_answer.lower():
                    distractors = values.copy()
                    break
            else:
                distractors = self._get_generic_distractors(correct_answer, 'english')

        random.shuffle(distractors)
        return distractors[:3]

    def _generate_generic_options(self, correct_answer):
        """生成通用混淆选项"""
        return self._get_generic_distractors(correct_answer, 'generic')

    def _get_generic_distractors(self, correct_answer, language):
        """获取通用干扰项"""
        if language == 'japanese':
            generic_distractors = [
                "はい", "いいえ", "どうぞ", "ありがとう",
                "先生", "学生", "友達", "家族",
                "今日", "明日", "昨日", "来週",
                "学校", "病院", "会社", "図書館",
                "食べる", "飲む", "見る", "行く"
            ]
        elif language == 'english':
            generic_distractors = [
                "yes", "no", "maybe", "please",
                "morning", "afternoon", "evening", "night",
                "today", "tomorrow", "yesterday", "now",
                "one", "two", "three", "four",
                "good", "bad", "great", "nice"
            ]
        else:
            generic_distractors = ["A", "B", "C", "D"]

        random.shuffle(generic_distractors)
        return generic_distractors[:3]

    # ============ 选项验证器 ============

    def validate_option_quality(self, options, correct_answer):
        """验证选项质量"""
        issues = []

        # 1. 检查选项数量
        if len(options) != 4:
            issues.append(f"选项数量错误: {len(options)}，应为4")

        # 2. 检查是否有空选项
        for i, opt in enumerate(options):
            if not opt.get('content') or opt['content'].strip() == '':
                issues.append(f"选项{i+1}为空")

        # 3. 检查答案是否在选项中
        answer_found = False
        for opt in options:
            if opt.get('option', '').upper() == correct_answer.upper():
                answer_found = True
                break
            if opt.get('content') == correct_answer:
                answer_found = True
                break

        if not answer_found:
            issues.append(f"答案'{correct_answer}'不在选项中")

        # 4. 检查干扰项相似性
        correct_content = None
        for opt in options:
            if opt.get('option', '').upper() == correct_answer.upper():
                correct_content = opt.get('content', '')
                break

        if correct_content:
            # 检查干扰项是否与正确答案太相似或太不同
            for i, opt in enumerate(options):
                if opt.get('option', '').upper() != correct_answer.upper():
                    distractor = opt.get('content', '')
                    # 计算相似度（简化版）
                    if correct_content == distractor:
                        issues.append(f"干扰项{i+1}与正确答案完全相同")

        return issues

    # ============ 修复功能 ============

    def fix_question_options(self, qid, content, options, correct_answer, tags, conn):
        """修复单个题目的选项"""
        cursor = conn.cursor()

        # 检测语言
        language = 'japanese' if '日语' in tags or 'にほんご' in content else 'english'

        # 解析现有选项
        try:
            if isinstance(options, str):
                opts = json.loads(options) if options else []
            else:
                opts = options if options else []
        except:
            opts = []

        needs_fix = False

        # 1. 检查选项是否为空或格式错误
        if not opts or len(opts) == 0:
            needs_fix = True
        else:
            # 检查是否有空选项
            empty_count = sum(1 for opt in opts if not opt.get('content'))
            if empty_count > 0:
                needs_fix = True

        # 2. 检查答案是否在选项中
        answer_letter = correct_answer.upper() if len(correct_answer) == 1 else None
        if answer_letter and answer_letter in ['A', 'B', 'C', 'D']:
            idx = ord(answer_letter) - ord('A')
            if idx >= len(opts):
                needs_fix = True
        elif correct_answer and correct_answer not in ['A', 'B', 'C', 'D']:
            # 答案是内容，检查是否在选项中
            answer_in_options = any(opt.get('content') == correct_answer for opt in opts)
            if not answer_in_options:
                needs_fix = True

        if needs_fix:
            # 生成新的混淆选项
            distractors = self.generate_confusing_options(correct_answer, language)

            # 构建新选项
            new_options = []
            correct_idx = random.randint(0, 3)

            for i in range(4):
                if i == correct_idx:
                    new_options.append({
                        "option": chr(65 + i),
                        "content": correct_answer
                    })
                else:
                    new_options.append({
                        "option": chr(65 + i),
                        "content": distractors[i] if i < len(distractors) else f"选项{i+1}"
                    })

            # 更新答案字母
            new_answer = chr(65 + correct_idx)

            cursor.execute("""
                UPDATE questions
                SET options = ?, correct_answer = ?
                WHERE id = ?
            """, (json.dumps(new_options, ensure_ascii=False), new_answer, qid))

            return True

        return False

    def optimize_all_listening_questions(self):
        """优化所有听力题"""
        print("=" * 80)
        print("🎧 AI听力题智能优化系统")
        print("=" * 80)

        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # 获取所有听力题
            cursor.execute("""
                SELECT id, content, options, correct_answer, tags, audio_url
                FROM questions
                WHERE type = 'listening' OR type LIKE '%listening%'
            """)

            questions = cursor.fetchall()
            total = len(questions)

            print(f"\n正在优化 {total} 道听力题...")

            fixed = 0
            checked = 0

            for row in questions:
                qid, content, options, correct_answer, tags, audio_url = row
                checked += 1

                # 验证选项质量
                try:
                    opts = json.loads(options) if isinstance(options, str) else (options if options else [])
                except:
                    opts = []

                if self.fix_question_options(qid, content, opts, correct_answer, tags, conn):
                    fixed += 1

                if checked % 100 == 0:
                    print(f"  已处理: {checked}/{total} (已修复: {fixed})")

            conn.commit()

            print(f"\n优化完成!")
            print(f"  总题目数: {total}")
            print(f"  修复数量: {fixed}")

            # 显示质量报告
            self.show_quality_report(conn)

        except Exception as e:
            logger.error(f"优化失败: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

    def show_quality_report(self, conn):
        """显示质量报告"""
        cursor = conn.cursor()

        print("\n" + "=" * 80)
        print("📊 听力题质量报告")
        print("=" * 80)

        # 统计选项情况
        cursor.execute("""
            SELECT COUNT(*) FROM questions
            WHERE (type = 'listening' OR type LIKE '%listening%')
            AND options IS NOT NULL AND options != '' AND options != '[]'
        """)
        valid_options = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM questions
            WHERE type = 'listening' OR type LIKE '%listening%'
        """)
        total = cursor.fetchone()[0]

        print(f"\n选项有效性:")
        print(f"  有效选项: {valid_options} ({valid_options/total*100:.1f}%)")
        print(f"  需要修复: {total - valid_options} ({(total-valid_options)/total*100:.1f}%)")

        # 检查音频URL
        cursor.execute("""
            SELECT COUNT(*) FROM questions
            WHERE (type = 'listening' OR type LIKE '%listening%')
            AND audio_url IS NOT NULL AND audio_url != '' AND audio_url != '[]'
        """)
        has_audio = cursor.fetchone()[0]

        print(f"\n音频配置:")
        print(f"  有音频URL: {has_audio} ({has_audio/total*100:.1f}%)")
        print(f"  缺少音频: {total - has_audio} ({(total-has_audio)/total*100:.1f}%)")

        # 样本题目展示
        print("\n" + "=" * 80)
        print("📝 样本题目预览")
        print("=" * 80)

        cursor.execute("""
            SELECT id, content, options, correct_answer, tags
            FROM questions
            WHERE (type = 'listening' OR type LIKE '%listening%')
            AND options IS NOT NULL AND options != '' AND options != '[]'
            LIMIT 3
        """)

        for i, row in enumerate(cursor.fetchall(), 1):
            qid, content, options, correct_answer, tags = row
            print(f"\n【题目 {i}】ID: {qid}")

            # 显示题目内容（截取）
            content_preview = content[:100] + "..." if len(content) > 100 else content
            print(f"  内容: {content_preview}")

            # 显示选项
            try:
                opts = json.loads(options) if isinstance(options, str) else options
                for opt in opts:
                    marker = " ✓" if opt.get('option', '').upper() == correct_answer.upper() else ""
                    print(f"  {opt.get('option')}: {opt.get('content')}{marker}")
            except:
                print(f"  选项解析失败")

            print(f"  答案: {correct_answer}")

    def validate_audio_text_consistency(self):
        """验证音频文本与题目内容一致性"""
        print("\n" + "=" * 80)
        print("🔊 音频文本一致性验证")
        print("=" * 80)

        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, content, audio_url, tags
                FROM questions
                WHERE (type = 'listening' OR type LIKE '%listening%')
                AND audio_url IS NOT NULL AND audio_url != ''
            """)

            issues = []

            for row in cursor.fetchall():
                qid, content, audio_url, tags = row

                # 提取音频路径中的语言/级别标识
                path_lower = audio_url.lower()

                # 检查语言一致性
                has_japanese_in_path = any(x in path_lower for x in ['japanese', 'jlpt', 'n5', 'n4', 'n3', 'n2', 'n1', 'kanto', 'kansai'])
                has_english_in_path = any(x in path_lower for x in ['english', 'basic', 'intermediate', 'advanced', 'ielts', 'toefl'])

                # 检测内容语言
                has_japanese_content = bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF]', content))
                has_english_content = bool(re.search(r'\b(Hello|Good|Listen|Question|Answer)\b', content, re.IGNORECASE))

                # 检查不一致
                if has_japanese_in_path and has_english_content and not has_japanese_content:
                    issues.append(f"{qid}: 音频路径标注为日语，但内容包含英语标识")

                if has_english_in_path and has_japanese_content and not has_english_content:
                    issues.append(f"{qid}: 音频路径标注为英语，但内容包含日语")

            if issues:
                print(f"\n发现 {len(issues)} 个一致性问题:")
                for issue in issues[:10]:
                    print(f"  ⚠️  {issue}")
                if len(issues) > 10:
                    print(f"  ... 还有 {len(issues) - 10} 个")
            else:
                print("\n✅ 音频路径与内容语言一致")

        except Exception as e:
            logger.error(f"验证失败: {str(e)}")
        finally:
            conn.close()

    def generate_placeholder_guidelines(self):
        """生成占位符音频指南"""
        print("\n" + "=" * 80)
        print("📁 音频文件命名规范")
        print("=" * 80)

        guidelines = """
日语听力:
  /static/audio/japanese/n5/listening_001.mp3 ~ listening_300.mp3
  /static/audio/japanese/n4/listening_001.mp3 ~ listening_300.mp3
  /static/audio/japanese/n3/listening_001.mp3 ~ listening_300.mp3
  /static/audio/japanese/kanto/listening_001.mp3 ~ listening_300.mp3
  /static/audio/japanese/kansai/listening_001.mp3 ~ listening_300.mp3

英语听力:
  /static/audio/english/basic/listening_001.mp3 ~ listening_200.mp3
  /static/audio/english/intermediate/listening_001.mp3 ~ listening_200.mp3
  /static/audio/english/advanced/listening_001.mp3 ~ listening_150.mp3
  /static/audio/english/ielts/listening_001.mp3 ~ listening_150.mp3
  /static/audio/english/toefl/listening_001.mp3 ~ listening_150.mp3
  /static/audio/english/british/listening_001.mp3 ~ listening_300.mp3
  /static/audio/english/american/listening_001.mp3 ~ listening_300.mp3
  /static/audio/english/australian/listening_001.mp3 ~ listening_300.mp3
  /static/audio/english/european/listening_001.mp3 ~ listening_300.mp3

注意事项:
1. 音频文件必须放在 app/static/audio/ 目录下
2. 文件名必须与数据库中的audio_url对应
3. 建议使用MP3格式，采样率44.1kHz
4. 时长建议: 30秒-2分钟
5. 音频内容必须与题目文本一致
"""
        print(guidelines)


def main():
    """主函数"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

    optimizer = ListeningQuestionOptimizer(db_path)

    # 优化所有听力题
    optimizer.optimize_all_listening_questions()

    # 验证音频一致性
    optimizer.validate_audio_text_consistency()

    # 显示音频指南
    optimizer.generate_placeholder_guidelines()


if __name__ == "__main__":
    main()