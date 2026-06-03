# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
将现有题库从代码导入到数据库中
"""

import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import sys
import os

existing_japanese_questions = {
    "N5": [
        {
            "content": "この単語の正しい意味は何ですか?「ありがとう」",
            "options": ["谢谢", "再见", "早上好", "你好"],
            "correct_answer": "A",
            "section": "词汇",
            "explanation": "「ありがとう」は感謝の意味です."
        },
        {
            "content": "「きれい」の反対語は何ですか?",
            "options": ["漂亮", "脏", "大", "小"],
            "correct_answer": "B",
            "section": "词汇",
            "explanation": "「きれい」の反対語は「汚い」です."
        },
        {
            "content": "私は毎朝7時___起きます.",
            "options": ["に", "で", "を", "へ"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "過去の時間を表す場合は助詞「に」を使います."
        },
        {
            "content": "昨日、何を___か.",
            "options": ["食べる", "食べた", "食べて", "食べよう"],
            "correct_answer": "B",
            "section": "语法",
            "explanation": "過去の出来事を尋ねる場合は過去形を使います."
        },
        {
            "content": "文章の中で、主人公は毎朝何時に起きますか?",
            "options": ["7時", "8時", "9時", "10時"],
            "correct_answer": "A",
            "section": "阅读",
            "explanation": "文章の中で「私は毎朝7時に起きて」と言っています."
        },
        {
            "content": "「学校」の発音は何ですか?",
            "options": ["がっこう", "学校", "がくえん", "がこう"],
            "correct_answer": "A",
            "section": "词汇",
            "explanation": "「学校」の発音は「がっこう」です."
        }
    ],
    "N4": [
        {
            "content": "毎日、日本語を___しています.",
            "options": ["勉強する", "勉強します", "勉強される", "勉強せていただく"],
            "correct_answer": "B",
            "section": "语法",
            "explanation": "丁寧な表現では「ます」形を使います."
        },
        {
            "content": "私は毎朝公園を___ます.",
            "options": ["走る", "走って", "走った", "走ろう"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "毎日の習慣を表す場合は現在形を使います."
        },
        {
            "content": "ここで___ください.",
            "options": ["食べるください", "食べてください", "食べたください", "食べようください"],
            "correct_answer": "B",
            "section": "语法",
            "explanation": "「〜てください」は丁寧な依頼を表します."
        },
        {
            "content": "昨日は何をしましたか.",
            "options": ["昨天我和朋友看了电影.", "明天我和朋友去看电影.", "今天我和朋友在看电影.", "经常我和朋友看电影."],
            "correct_answer": "A",
            "section": "阅读",
            "explanation": "「昨日」は過去を表します."
        },
        {
            "content": "この問題は___です.",
            "options": ["難しい", "易しい", "大きい", "小さい"],
            "correct_answer": "B",
            "section": "语法",
            "explanation": "「大きい」の比較級は「大きく」です."
        },
        {
            "content": "「猫」の日本語は何ですか?",
            "options": ["犬", "猫", "鳥", "魚"],
            "correct_answer": "B",
            "section": "词汇",
            "explanation": "「猫」の日本語は「ねこ」です."
        }
    ],
    "N3": [
        {
            "content": "雨が降ったら、___行きません.",
            "options": ["行く", "行か", "行き", "行って"],
            "correct_answer": "B",
            "section": "语法",
            "explanation": "「〜たら」は条件を表す接続助詞です."
        },
        {
            "content": "彼は日本語が___そうです.",
            "options": ["他会说日语.", "他在说日语.", "他想说日语.", "他说了日语."],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「〜ができる」は能力を表します."
        },
        {
            "content": "文章の中で、試験は何曜日に行われますか?",
            "options": ["月曜日", "火曜日", "水曜日", "日曜日"],
            "correct_answer": "D",
            "section": "阅读",
            "explanation": "文章の中で「日曜日に試験があります」と言っています."
        },
        {
            "content": "この問題は___解決できます.",
            "options": ["簡単に", "難しく", "大きく", "小さく"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "副詞「簡単に」は方法を表します."
        },
        {
            "content": "「難しい」の反意語は何ですか?",
            "options": ["簡単", "大きい", "小さい", "早い"],
            "correct_answer": "A",
            "section": "词汇",
            "explanation": "「難しい」の反意語は「簡単」です."
        },
        {
            "content": "昨日は雨が降ったので、___.",
            "options": ["因为昨天下雨,所以没有外出.", "因为昨天晴天,所以外出了.", "因为昨天刮风,所以没有外出.", "因为昨天多云,所以外出了."],
            "correct_answer": "A",
            "section": "阅读",
            "explanation": "「〜ので」は原因を表します."
        }
    ],
    "N2": [
        {
            "content": "彼は遅刻した___謝りました.",
            "options": ["ので", "から", "ために", "ので"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「〜ので」は原因を表します."
        },
        {
            "content": "彼は遅刻して___しました.",
            "options": ["他因为迟到而道歉.", "他因为迟到而生气.", "他因为迟到而高兴.", "他因为迟到而悲伤."],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「〜て」は動作の連続を表します."
        },
        {
            "content": "文章によると、何が普及していますか?",
            "options": ["テレビの普及", "インターネットの普及", "新聞の普及", "ラジオの普及"],
            "correct_answer": "B",
            "section": "阅读",
            "explanation": "文章の中で「インターネットの普及により」と言っています."
        },
        {
            "content": "彼は本___読んでいます.",
            "options": ["彼は本ばかり読んでいます.", "彼は本ばかり読みます.", "彼は本ばかり読んだ.", "彼は本ばかり読もう."],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「〜ばかり」は頻繁に起こることを表します."
        },
        {
            "content": "「環境保護」の読み方は何ですか?",
            "options": ["かんきょうほご", "しゃかいほご", "せいかつほご", "にほんごほご"],
            "correct_answer": "A",
            "section": "词汇",
            "explanation": "「環境保護」は「かんきょうほご」と読みます."
        },
        {
            "content": "彼女は音楽が好き___、毎日練習しています.",
            "options": ["因为她喜欢音乐,所以每天练习.", "因为她不喜欢音乐,所以不练习.", "因为她喜欢音乐,所以不练习.", "因为她不喜欢音乐,所以练习."],
            "correct_answer": "A",
            "section": "阅读",
            "explanation": "「〜ので」は原因を表します."
        }
    ],
    "N1": [
        {
            "content": "年をとる___、体が弱くなります.",
            "options": ["年をとるにつれて、体が弱くなります.", "年をとるにつれて、体が強くなります.", "年をとるにつれて、体が大きくなります.", "年をとるにつれて、体が小さくなります."],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「〜につれて」は変化を表します."
        },
        {
            "content": "彼はその問題について深く考えている___です.",
            "options": ["他似乎正在深入思考那个问题.", "他似乎已经思考了那个问题.", "他似乎不想思考那个问题.", "他似乎无法思考那个问题."],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「ようです」は推測を表します."
        },
        {
            "content": "文章によると、何が問題になっていますか?",
            "options": ["健康問題", "教育問題", "プライバシー問題", "環境問題"],
            "correct_answer": "C",
            "section": "阅读",
            "explanation": "文章の中で「プライバシーの問題が指摘されています」と言っています."
        },
        {
            "content": "インターネットを___、世界中の情報を得ることができます.",
            "options": ["インターネットを通じて、世界中の情報を得ることができます.", "インターネットを通じて、世界中の情報を得ました.", "インターネットを通じて、世界中の情報を得ようとしています.", "インターネットを通じて、世界中の情報を得たことがあります."],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「〜を通じて」は手段を表します."
        },
        {
            "content": "「全球化」の日本語の読み方は何ですか?",
            "options": ["ぜんきゅうか", "グローバル化", "せかいか", "こくさいか"],
            "correct_answer": "A",
            "section": "词汇",
            "explanation": "「全球化」の日本語は「ぜんきゅうか」です."
        },
        {
            "content": "この問題は___解決する必要があります.",
            "options": ["早急に", "ゆっくり", "時々", "常に"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「早急に」は緊急性を表します."
        }
    ]
}

difficulty_map = {
    "N5": "easy",
    "N4": "medium",
    "N3": "medium",
    "N2": "hard",
    "N1": "hard"
}

def get_id_by_name(conn, table, column, name):
    """根据名称获取ID"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM {table} WHERE {column} = ?", (name,))
    result = cursor.fetchone()
    return result[0] if result else None

def main():
    """主函数"""
    try:
        conn = sqlite3.connect('data/mtscos_ai_project.db')
        cursor = conn.cursor()

        japanese_id = get_id_by_name(conn, "question_languages", "language_code", "japanese")
        if not japanese_id:
            print("日语语言未找到,跳过")
            return

        cursor.execute("SELECT id FROM question_banks WHERE language_id = ?", (japanese_id,))
        bank_result = cursor.fetchone()
        if not bank_result:
            print("日语题库未找到,跳过")
            return
        bank_id = bank_result[0]

        print(f"获取日语题库ID成功: {bank_id}")

        for level_code, questions in existing_japanese_questions.items():
            cursor.execute("SELECT id FROM question_levels WHERE level_code = ?", (level_code,))
            level_result = cursor.fetchone()
            if not level_result:
                print(f"等级{level_code}未找到,跳过")
                continue
            level_id = level_result[0]

            difficulty = difficulty_map.get(level_code, "medium")
            difficulty_id = get_id_by_name(conn, "question_difficulties", "difficulty_name", difficulty)
            if not difficulty_id:
                print(f"难度{difficulty}未找到,跳过")
                continue

            for idx, question_data in enumerate(questions):
                section_id = get_id_by_name(conn, "question_sections", "section_name", question_data["section"])
                if not section_id:
                    print(f"章节{question_data['section']}未找到,跳过")
                    continue

                cursor.execute("""
                    INSERT INTO questions (question_bank_id, level_id, section_id, difficulty_id, question_content, correct_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (bank_id, level_id, section_id, difficulty_id, question_data["content"], question_data["correct_answer"], question_data["explanation"]))

                question_id = cursor.lastrowid

                options = question_data["options"]
                for opt_idx, opt_content in enumerate(options):
                    opt_label = chr(65 + opt_idx)
                    cursor.execute("""
                        INSERT INTO question_options (question_id, option_label, option_content, option_order)
                        VALUES (?, ?, ?, ?)
                    """, (question_id, opt_label, opt_content, opt_idx + 1))

                print(f"  导入题目 {idx+1}/{len(questions)} 成功")

            print(f"{level_code}等级题目导入完成")

        conn.commit()
        print("\n所有题目导入成功")
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        conn.rollback()
    except Exception as e:
        print(f"导入错误: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
