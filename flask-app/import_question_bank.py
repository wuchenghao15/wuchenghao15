#!/usr/bin/env python3
"""
将现有题库从代码导入到数据库中

import sqlite3
import sys

# 现有日语题库数据
existing_japanese_questions = {
    "N5": [
        {
            "content": "この単語の正しい意味は何ですか？「ありがとう」",
            "options": ["谢谢", "再见", "早上好", "你好"],
            "correct_answer": "A",
            "section": "词汇",
            "explanation": "「ありがとう」は感謝の意味です。"
        },
        {
            "options": ["漂亮", "脏", "大", "小"],
            "correct_answer": "B",
            "section": "词汇",
            "explanation": "「きれい」の反対語は「汚い」です。"
        {
            "options": ["に", "で", "を", "へ"],
            "section": "语法",
            "explanation": "過去の時間を表す場合は助詞「に」を使います。"
        {
            "options": ["食べる", "食べた", "食べて", "食べよう"],
            "correct_answer": "C",
            "section": "语法",
        },
        {
            "options": ["7時", "8時", "9時", "10時"],
            "correct_answer": "A",
            "section": "阅读",
            "explanation": "文章の中で「私は毎朝7時に起きて」と言っています。"
            "correct_answer": "A",
            "section": "词汇",
            "explanation": "「学校」の発音は「がっこう」です。"
        }
    ],
            "options": ["勉強する", "勉強します", "勉強される", "勉強せていただく"],
            "correct_answer": "C",
            "section": "语法",
        },
        {
            "options": ["走る", "走って", "走った", "走ろう"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "毎日の習慣を表す場合は現在形を使います。"
        },
        {
            "options": ["食べるください", "食べてください", "食べたください", "食べようください"],
            "correct_answer": "B",
            "section": "语法",
        },
            "options": ["昨天我和朋友看了电影。", "明天我和朋友去看电影。", "今天我和朋友在看电影。", "经常我和朋友看电影。"],
            "correct_answer": "A",
        },
        {
            "correct_answer": "B",
            "section": "语法",
            "explanation": "「大きい」の比較級は「大きく」です。"
            "options": ["犬", "猫", "鳥", "魚"],
            "correct_answer": "B",
            "explanation": "「猫」の日本語は「ねこ」です。"
        }
    ],
        {
            "section": "语法",
            "explanation": "「〜たら」は条件を表す接続助詞です。"
        },
        {
            "options": ["他会说日语。", "他在说日语。", "他想说日语。", "他说了日语。"],
            "correct_answer": "A",
            "explanation": "「〜ができる」は能力を表します。"
        },
            "options": ["月曜日", "火曜日", "水曜日", "日曜日"],
            "correct_answer": "D",
            "section": "阅读",
        {
            "correct_answer": "C",
            "section": "语法",
        },
            "options": ["簡単", "大きい", "小さい", "早い"],
            "correct_answer": "A",
            "explanation": "「難しい」の反意語は「簡単」です。"
        },
        {
            "options": ["因为昨天下雨，所以没有外出。", "因为昨天晴天，所以外出了。", "因为昨天刮风，所以没有外出。", "因为昨天多云，所以外出了。"],
            "correct_answer": "A",
            "section": "阅读",
        }
    ],
    "N2": [
        {
            "correct_answer": "A",
        {
            "options": ["他因为迟到而道歉。", "他因为迟到而生气。", "他因为迟到而高兴。", "他因为迟到而悲伤。"],
            "correct_answer": "A",
            "section": "语法",
            "options": ["テレビの普及", "インターネットの普及", "新聞の普及", "ラジオの普及"],
            "section": "阅读",
            "explanation": "文章の中で「インターネットの普及により」と言っています。"
        },
        {
            "options": ["彼は本ばかり読んでいます。", "彼は本ばかり読みます。", "彼は本ばかり読んだ。", "彼は本ばかり読もう。"],
            "explanation": "「〜ばかり」は頻繁に起こることを表します。"
        },
        {
            "options": ["かんきょうほご", "しゃかいほご", "せいかつほご", "にほんごほご"],
            "correct_answer": "A",
            "section": "词汇",
        },
            "options": ["因为她喜欢音乐，所以每天练习。", "因为她不喜欢音乐，所以不练习。", "因为她喜欢音乐，所以不练习。", "因为她不喜欢音乐，所以练习。"],
            "section": "阅读",
        }
    ],
            "options": ["年をとるにつれて、体が弱くなります。", "年をとるにつれて、体が強くなります。", "年をとるにつれて、体が大きくなります。", "年をとるにつれて、体が小さくなります。"],
            "correct_answer": "A",
            "section": "语法",
        },
        {
            "options": ["他似乎正在深入思考那个问题。", "他似乎已经思考了那个问题。", "他似乎不想思考那个问题。", "他似乎无法思考那个问题。"],
            "section": "语法",
            "explanation": "「ようです」は推測を表します。"
        {
            "options": ["健康問題", "教育問題", "プライバシー問題", "環境問題"],
            "correct_answer": "C",
            "section": "阅读",
        },
            "options": ["インターネットを通じて、世界中の情報を得ることができます。", "インターネットを通じて、世界中の情報を得ました。", "インターネットを通じて、世界中の情報を得ようとしています。", "インターネットを通じて、世界中の情報を得たことがあります。"],
            "correct_answer": "A",
            "explanation": "「〜を通じて」は手段を表します。"
            "correct_answer": "A",
            "explanation": "「全球化」の日本語は「ぜんきゅうか」です。"
        },
        {
            "correct_answer": "A",
}

# 等级到难度的映射
difficulty_map = {
    "N5": "easy",
    "N4": "medium",
    "N3": "medium",
    "N2": "hard",
    "N1": "hard"
}

    cursor = conn.cursor()
    result = cursor.fetchone()
    return result[0] if result else None

    """主函数"""
        # 连接数据库
        cursor = conn.cursor()


        # 获取日语ID
        japanese_id = get_id_by_name(conn, "question_languages", "language_code", "japanese")
        if not japanese_id:
            return

        # 获取日语题库ID
        cursor.execute("SELECT id FROM question_banks WHERE language_id = ?", (japanese_id,))
        bank_result = cursor.fetchone()
        if not bank_result:
        bank_id = bank_result[0]

        print(f"获取日语题库ID成功: {bank_id}")
        # 导入题目
        for level_code, questions in existing_japanese_questions.items():

            # 获取等级ID
            level_result = cursor.fetchone()
                print(f"等级{level_code}未找到，跳过")
                continue
            level_id = level_result[0]

            # 获取难度ID
            difficulty = difficulty_map.get(level_code, "medium")
            if not difficulty_id:
                continue

            # 导入每个题目
            for idx, question_data in enumerate(questions):
                section_id = get_id_by_name(conn, "question_sections", "section_name", question_data["section"])
                if not section_id:
                    print(f"章节{question_data['section']}未找到，跳过")
                    continue

                cursor.execute("""
                    INSERT INTO questions (question_bank_id, level_id, section_id, difficulty_id, question_content, correct_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                       question_data["content"], question_data["correct_answer"], question_data["explanation"]))

                question_id = cursor.lastrowid

                # 插入选项
                options = question_data["options"]
                for opt_idx, opt_content in enumerate(options):
                    opt_label = chr(65 + opt_idx)  # A, B, C, D
                    cursor.execute("""
                        INSERT INTO question_options (question_id, option_label, option_content, option_order)
                        VALUES (?, ?, ?, ?)
                    """, (question_id, opt_label, opt_content, opt_idx + 1))

                print(f"  导入题目 {idx+1}/{len(questions)} 成功")

            print(f"{level_code}等级题目导入完成")

        # 提交事务
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
