#!/usr/bin/env python3
"""
将现有题库从代码导入到数据库中
"""

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
            "content": "「きれい」の反対語は何ですか？",
            "options": ["漂亮", "脏", "大", "小"],
            "correct_answer": "B",
            "section": "词汇",
            "explanation": "「きれい」の反対語は「汚い」です。"
        },
        {
            "content": "次の文で正しい助詞を選んでください。「私は昨日＿＿映画を見ました。」",
            "options": ["に", "で", "を", "へ"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "過去の時間を表す場合は助詞「に」を使います。"
        },
        {
            "content": "「食べる」のて形は何ですか？",
            "options": ["食べる", "食べた", "食べて", "食べよう"],
            "correct_answer": "C",
            "section": "语法",
            "explanation": "「食べる」のて形は「食べて」です。"
        },
        {
            "content": "以下の文章を読んで、質問に答えてください。「私は毎朝7時に起きて、朝ご飯を食べます。それから、学校に行きます。」質問：私は毎朝何時に起きますか？",
            "options": ["7時", "8時", "9時", "10時"],
            "correct_answer": "A",
            "section": "阅读",
            "explanation": "文章の中で「私は毎朝7時に起きて」と言っています。"
        },
        {
            "content": "「学校」の発音はどれですか？",
            "options": ["がっこう", "しゃかい", "せいかつ", "にほんご"],
            "correct_answer": "A",
            "section": "词汇",
            "explanation": "「学校」の発音は「がっこう」です。"
        }
    ],
    "N4": [
        {
            "content": "「勉強する」の敬語形は何ですか？",
            "options": ["勉強する", "勉強します", "勉強される", "勉強せていただく"],
            "correct_answer": "C",
            "section": "语法",
            "explanation": "「勉強する」の敬語形は「勉強される」です。"
        },
        {
            "content": "次の文で正しい動詞形を選んでください。「彼は毎日30分＿＿。」",
            "options": ["走る", "走って", "走った", "走ろう"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "毎日の習慣を表す場合は現在形を使います。"
        },
        {
            "content": "「〜てください」の正しい使い方はどれですか？",
            "options": ["食べるください", "食べてください", "食べたください", "食べようください"],
            "correct_answer": "B",
            "section": "语法",
            "explanation": "命令形の丁寧な形は「〜てください」です。"
        },
        {
            "content": "「昨日、友達と映画を見ました。」の意味は何ですか？",
            "options": ["昨天我和朋友看了电影。", "明天我和朋友去看电影。", "今天我和朋友在看电影。", "经常我和朋友看电影。"],
            "correct_answer": "A",
            "section": "阅读",
            "explanation": "「昨日」は過去の時間を表します。"
        },
        {
            "content": "「大きい」の比較級は何ですか？",
            "options": ["大きい", "大きく", "大きな", "大きいです"],
            "correct_answer": "B",
            "section": "语法",
            "explanation": "「大きい」の比較級は「大きく」です。"
        },
        {
            "content": "「猫」の単語は何ですか？",
            "options": ["犬", "猫", "鳥", "魚"],
            "correct_answer": "B",
            "section": "词汇",
            "explanation": "「猫」の日本語は「ねこ」です。"
        }
    ],
    "N3": [
        {
            "content": "「〜たら」の使い方はどれですか？",
            "options": ["雨が降ったら、家にいます。", "雨が降ったら、家にいた。", "雨が降ったら、家にいる。", "雨が降ったら、家にいます。"],
            "correct_answer": "D",
            "section": "语法",
            "explanation": "「〜たら」は条件を表す接続助詞です。"
        },
        {
            "content": "「彼は日本語が話せます。」の意味は何ですか？",
            "options": ["他会说日语。", "他在说日语。", "他想说日语。", "他说了日语。"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「〜ができる」は能力を表します。"
        },
        {
            "content": "次の文章を読んで、質問に答えてください。「この店は毎日午前10時から午後8時まで営業しています。日曜日は休みです。」質問：この店は何日休みですか？",
            "options": ["月曜日", "火曜日", "水曜日", "日曜日"],
            "correct_answer": "D",
            "section": "阅读",
            "explanation": "文章の中で「日曜日は休みです」と言っています。"
        },
        {
            "content": "「する」の尊敬語は何ですか？",
            "options": ["する", "します", "なさる", "せていただく"],
            "correct_answer": "C",
            "section": "语法",
            "explanation": "「する」の尊敬語は「なさる」です。"
        },
        {
            "content": "「難しい」の反意語は何ですか？",
            "options": ["簡単", "大きい", "小さい", "早い"],
            "correct_answer": "A",
            "section": "词汇",
            "explanation": "「難しい」の反意語は「簡単」です。"
        },
        {
            "content": "「昨日は雨が降ったので、外に出ませんでした。」の意味は何ですか？",
            "options": ["因为昨天下雨，所以没有外出。", "因为昨天晴天，所以外出了。", "因为昨天刮风，所以没有外出。", "因为昨天多云，所以外出了。"],
            "correct_answer": "A",
            "section": "阅读",
            "explanation": "「ので」は理由を表します。"
        }
    ],
    "N2": [
        {
            "content": "「〜にとって」の使い方はどれですか？",
            "options": ["私にとって、日本語は難しいです。", "私にとって、日本語を勉強します。", "私にとって、日本語を話します。", "私にとって、日本語を読みます。"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「〜にとって」は立場を表します。"
        },
        {
            "content": "「彼は遅刻したことを謝りました。」の意味は何ですか？",
            "options": ["他因为迟到而道歉。", "他因为迟到而生气。", "他因为迟到而高兴。", "他因为迟到而悲伤。"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「〜たことを」は事実を表します。"
        },
        {
            "content": "次の文章を読んで、質問に答えてください。「近年、インターネットの普及により、人々の生活スタイルは大きく変わりました。」質問：生活スタイルが変わった理由は何ですか？",
            "options": ["テレビの普及", "インターネットの普及", "新聞の普及", "ラジオの普及"],
            "correct_answer": "B",
            "section": "阅读",
            "explanation": "文章の中で「インターネットの普及により」と言っています。"
        },
        {
            "content": "「〜ばかり」の正しい使い方はどれですか？",
            "options": ["彼は本ばかり読んでいます。", "彼は本ばかり読みます。", "彼は本ばかり読んだ。", "彼は本ばかり読もう。"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「〜ばかり」は頻繁に起こることを表します。"
        },
        {
            "content": "「環境保護」の日本語は何ですか？",
            "options": ["かんきょうほご", "しゃかいほご", "せいかつほご", "にほんごほご"],
            "correct_answer": "A",
            "section": "词汇",
            "explanation": "「環境保護」の日本語は「かんきょうほご」です。"
        },
        {
            "content": "「彼女は音楽が好きなので、毎日練習しています。」の意味は何ですか？",
            "options": ["因为她喜欢音乐，所以每天练习。", "因为她不喜欢音乐，所以不练习。", "因为她喜欢音乐，所以不练习。", "因为她不喜欢音乐，所以练习。"],
            "correct_answer": "A",
            "section": "阅读",
            "explanation": "「ので」は理由を表します。"
        }
    ],
    "N1": [
        {
            "content": "「〜につれて」の正しい使い方はどれですか？",
            "options": ["年をとるにつれて、体が弱くなります。", "年をとるにつれて、体が強くなります。", "年をとるにつれて、体が大きくなります。", "年をとるにつれて、体が小さくなります。"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「〜につれて」は変化を表します。"
        },
        {
            "content": "「彼はその問題について深く考えているようです。」の意味は何ですか？",
            "options": ["他似乎正在深入思考那个问题。", "他似乎已经思考了那个问题。", "他似乎不想思考那个问题。", "他似乎无法思考那个问题。"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「ようです」は推測を表します。"
        },
        {
            "content": "次の文章を読んで、質問に答えてください。「現代社会において、情報技術の発展は人々の生活を便利にする一方で、プライバシーの問題も生じています。」質問：情報技術の発展によって生じた問題は何ですか？",
            "options": ["健康問題", "教育問題", "プライバシー問題", "環境問題"],
            "correct_answer": "C",
            "section": "阅读",
            "explanation": "文章の中で「プライバシーの問題も生じています」と言っています。"
        },
        {
            "content": "「〜を通じて」の正しい使い方はどれですか？",
            "options": ["インターネットを通じて、世界中の情報を得ることができます。", "インターネットを通じて、世界中の情報を得ました。", "インターネットを通じて、世界中の情報を得ようとしています。", "インターネットを通じて、世界中の情報を得たことがあります。"],
            "correct_answer": "A",
            "section": "语法",
            "explanation": "「〜を通じて」は手段を表します。"
        },
        {
            "content": "「全球化」の日本語は何ですか？",
            "options": ["ぜんきゅうか", "ぜんきゅうかか", "ぜんきゅうかか", "ぜんきゅうかか"],
            "correct_answer": "A",
            "section": "词汇",
            "explanation": "「全球化」の日本語は「ぜんきゅうか」です。"
        },
        {
            "content": "「この研究は将来の技術開発に大きな影響を与えると考えられています。」の意味は何ですか？",
            "options": ["这项研究被认为将对未来的技术开发产生重大影响。", "这项研究已经对未来的技术开发产生了重大影响。", "这项研究不会对未来的技术开发产生影响。", "这项研究可能不会对未来的技术开发产生影响。"],
            "correct_answer": "A",
            "section": "阅读",
            "explanation": "「と考えられています」は一般的な考えを表します。"
        }
    ]
}

# 等级到难度的映射
difficulty_map = {
    "N5": "easy",
    "N4": "medium",
    "N3": "medium",
    "N2": "hard",
    "N1": "hard"
}

def get_id_by_name(conn, table, name_column, value):
    """根据名称获取ID"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM {table} WHERE {name_column} = ?", (value,))
    result = cursor.fetchone()
    return result[0] if result else None

def main():
    """主函数"""
    try:
        # 连接数据库
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        print("连接数据库成功")
        
        # 获取日语ID
        japanese_id = get_id_by_name(conn, "question_languages", "language_code", "japanese")
        if not japanese_id:
            print("日语未找到，退出")
            return
        
        # 获取日语题库ID
        cursor.execute("SELECT id FROM question_banks WHERE language_id = ?", (japanese_id,))
        bank_result = cursor.fetchone()
        if not bank_result:
            print("日语题库未找到，退出")
            return
        bank_id = bank_result[0]
        
        print(f"获取日语题库ID成功: {bank_id}")
        
        # 导入题目
        for level_code, questions in existing_japanese_questions.items():
            print(f"导入{level_code}等级题目...")
            
            # 获取等级ID
            cursor.execute("SELECT id FROM question_levels WHERE language_id = ? AND level_code = ?", (japanese_id, level_code))
            level_result = cursor.fetchone()
            if not level_result:
                print(f"等级{level_code}未找到，跳过")
                continue
            level_id = level_result[0]
            
            # 获取难度ID
            difficulty = difficulty_map.get(level_code, "medium")
            difficulty_id = get_id_by_name(conn, "question_difficulties", "difficulty_level", difficulty)
            if not difficulty_id:
                print(f"难度{difficulty}未找到，跳过")
                continue
            
            # 导入每个题目
            for idx, question_data in enumerate(questions):
                # 获取章节ID
                section_id = get_id_by_name(conn, "question_sections", "section_name", question_data["section"])
                if not section_id:
                    print(f"章节{question_data['section']}未找到，跳过")
                    continue
                
                # 插入题目
                cursor.execute("""
                    INSERT INTO questions (question_bank_id, level_id, section_id, difficulty_id, question_content, correct_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (bank_id, level_id, section_id, difficulty_id, 
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
