#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日语方言听力题库自动扩充系统
支持：关东腔(Kanto)、关西腔(Kansai)
"""

import logging
import os
import sys
import sqlite3
import random
import hashlib
import uuid
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class JapaneseDialectExpander:
    """日语方言听力题库扩充器"""

    def __init__(self, db_path="app.db"):
        self.db_path = db_path
        self.batch_id = str(uuid.uuid4())[:12]

        # 方言配置
        self.dialect_config = {
            "kanto": {
                "name": "关东腔",
                "flag": "東京",
                "description": "Kanto Dialect (Tokyo standard)",
                "pronunciation": {
                    "ha": "は",
                    "wa": "わ",
                    "wo": "を",
                    "desu": "です",
                    "masu": "ます"
                },
                "vocabulary": {
                    "美味しい": "oishii",
                    "面白い": "omoshiroi",
                    "嬉しい": "ureshii",
                    "分かる": "wakaru",
                    "食べる": "taberu",
                    "行く": "iku",
                    "来る": "kuru",
                    "する": "suru"
                },
                "greetings": ["こんにちは", "こんばんは", "おはようございます", "ありがとうございます"],
                "particles": ["は", "を", "が", "に", "で", "と", "へ", "より"],
                "features": ["标准语", "平坦なイントネーション", "丁寧語多用"]
            },
            "kansai": {
                "name": "关西腔",
                "flag": "大阪",
                "description": "Kansai Dialect (Osaka/Kyoto)",
                "pronunciation": {
                    "ha": "はゃ",
                    "wa": "わ",
                    "wo": "お",
                    "desu": "ですわ",
                    "masu": "ますわ"
                },
                "vocabulary": {
                    "美味しい": "うまい",
                    "面白い": "おもろい",
                    "嬉しい": "よかった",
                    "分かる": "わかる",
                    "食べる": "たべる",
                    "行く": "いく",
                    "来る": "くる",
                    "する": "する"
                },
                "greetings": ["こんにちは", "こんばんは", "おはようさん", "おおきに"],
                "particles": ["は", "お", "が", "に", "で", "と", "へ", "より"],
                "features": ["抑揚が豊か", "「な」終わり", "関西弁特有の語彙"]
            }
        }

        # 方言对比词汇表
        self.dialect_vocabulary_map = [
            {"kanto": "美味しい", "kansai": "うまい", "english": "delicious"},
            {"kanto": "面白い", "kansai": "おもろい", "english": "interesting"},
            {"kanto": "嬉しい", "kansai": "よかった", "english": "happy"},
            {"kanto": "分かる", "kansai": "わかる", "english": "understand"},
            {"kanto": "大丈夫", "kansai": "だいじょうぶ", "english": "okay"},
            {"kanto": "ありがとう", "kansai": "おおきに", "english": "thank you"},
            {"kanto": "すみません", "kansai": "すまん", "english": "sorry"},
            {"kanto": "何", "kansai": "なに", "english": "what"},
            {"kanto": "どこ", "kansai": "どこ", "english": "where"},
            {"kanto": "いつ", "kansai": "いつ", "english": "when"},
            {"kanto": "だれ", "kansai": "だれ", "english": "who"},
            {"kanto": "食べる", "kansai": "たべる", "english": "to eat"},
            {"kanto": "行く", "kansai": "いく", "english": "to go"},
            {"kanto": "見る", "kansai": "みる", "english": "to see"},
            {"kanto": "する", "kansai": "する", "english": "to do"}
        ]

        # 方言对话模板
        self.dialect_dialogues = {
            "kanto": [
                {
                    "text": "A: こんにちは、元気ですか？ B: はい、元気です。ありがとう。 A: 今日はいい天気ですね。 B: はい、とてもいい天気です。",
                    "q": "Bの返事はどうですか？",
                    "opts": ["元気ではない", "元気です", "分かりません", "困っている"],
                    "ans": "B",
                    "vocabulary_used": ["こんにちは", "元気", "ありがとう", "天気"]
                },
                {
                    "text": "A: 何を食べますか？ B: 寿司を食べたいです。 A: どこの店に行きますか？ B: 駅前のお店です。",
                    "q": "Bは何を食べたいですか？",
                    "opts": ["ラーメン", "寿司", "カレー", "そば"],
                    "ans": "B",
                    "vocabulary_used": ["食べる", "寿司", "駅前"]
                },
                {
                    "text": "A: 明日は何をしますか？ B: 図書館に行きます。 A: 何をしに行きますか？ B: 本を借りに行きます。",
                    "q": "Bは何をしに図書館に行きますか？",
                    "opts": ["本を買いに", "本を借りに", "遊びに", "勉強しに"],
                    "ans": "B",
                    "vocabulary_used": ["図書館", "本", "借りる"]
                },
                {
                    "text": "A: このレストラン、美味しいですか？ B: はい、とても美味しいです。 A: 何がおすすめですか？ B: 寿司がおすすめです。",
                    "q": "何がおすすめですか？",
                    "opts": ["ラーメン", "寿司", "カレー", "うどん"],
                    "ans": "B",
                    "vocabulary_used": ["美味しい", "おすすめ", "寿司"]
                },
                {
                    "text": "A: すみません、トイレはどこですか？ B: あちらの角を曲がるとあります。 A: ありがとうございます。 B: どういたしまして。",
                    "q": "トイレはどこですか？",
                    "opts": ["ここ", "あちらの角を曲がると", "向こう", "隣"],
                    "ans": "B",
                    "vocabulary_used": ["すみません", "トイレ", "ありがとうございます"]
                }
            ],
            "kansai": [
                {
                    "text": "A: こんにちは、元気か？ B: うん、元気やで。おおきに。 A: 今日はいい天気やな。 B: うん、とてもいい天気や。",
                    "q": "Bの返事はどうですか？",
                    "opts": ["元気ではない", "元気やで", "分からん", "困っとる"],
                    "ans": "B",
                    "vocabulary_used": ["こんにちは", "元気", "おおきに", "天気"]
                },
                {
                    "text": "A: 何食う？ B: 寿司食いたいわ。 A: どこの店行く？ B: 駅前の店や。",
                    "q": "Bは何を食いたいですか？",
                    "opts": ["ラーメン", "寿司", "カレー", "そば"],
                    "ans": "B",
                    "vocabulary_used": ["食う", "寿司", "駅前"]
                },
                {
                    "text": "A: 明日何する？ B: 図書館行くわ。 A: 何しに行く？ B: 本借りに行くわ。",
                    "q": "Bは何をしに図書館に行きますか？",
                    "opts": ["本を買いに", "本を借りに", "遊びに", "勉強しに"],
                    "ans": "B",
                    "vocabulary_used": ["図書館", "本", "借りる"]
                },
                {
                    "text": "A: この店、うまい？ B: うん、とてもうまいわ。 A: 何がおすすめ？ B: 寿司がおすすめや。",
                    "q": "何がおすすめですか？",
                    "opts": ["ラーメン", "寿司", "カレー", "うどん"],
                    "ans": "B",
                    "vocabulary_used": ["うまい", "おすすめ", "寿司"]
                },
                {
                    "text": "A: すまん、トイレはどこ？ B: あっちの角曲がればあるで。 A: おおきに。 B: えええ。",
                    "q": "トイレはどこですか？",
                    "opts": ["ここ", "あっちの角曲がれば", "向こう", "隣"],
                    "ans": "B",
                    "vocabulary_used": ["すまん", "トイレ", "おおきに"]
                }
            ]
        }

    def connect(self):
        """连接数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except Exception as e:
            logger.error(f"连接数据库失败: {str(e)}")
            return None

    def _ensure_columns(self, conn):
        """确保必要的列存在"""
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(questions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'fingerprint' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN fingerprint TEXT")
        if 'batch_id' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN batch_id TEXT")
        if 'dialect_style' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN dialect_style TEXT")
        if 'vocabulary_notes' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN vocabulary_notes TEXT")
        
        conn.commit()

    def _generate_fingerprint(self, text, question, options, answer, dialect):
        """生成去重指纹"""
        content = f"{dialect}|{text}|{question}|{answer}|" + "|".join(sorted(options))
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _is_duplicate(self, fingerprint, conn):
        """检查是否重复"""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM questions WHERE fingerprint = ?", (fingerprint,))
        return cursor.fetchone()[0] > 0

    def _generate_dialect_questions(self, dialect, count, conn):
        """生成特定方言的题目"""
        dialogues = self.dialect_dialogues.get(dialect, [])
        config = self.dialect_config.get(dialect, {})
        
        if not dialogues:
            return []

        questions = []
        generated_count = 0
        attempts = 0
        max_attempts = count * 10

        while generated_count < count and attempts < max_attempts:
            dialogue = random.choice(dialogues)
            
            # 随机打乱选项
            opts = dialogue['opts'].copy()
            ans_index = ord(dialogue['ans']) - 65
            correct_answer = opts[ans_index]
            
            if random.random() > 0.5:
                random.shuffle(opts)
                new_ans_index = opts.index(correct_answer)
                ans = chr(65 + new_ans_index)
            else:
                ans = dialogue['ans']
            
            fingerprint = self._generate_fingerprint(dialogue['text'], dialogue['q'], opts, ans, dialect)
            
            if not self._is_duplicate(fingerprint, conn):
                qid = f"{dialect.upper()[:2]}{uuid.uuid4().hex[:8]}"
                
                options_list = [{"option": chr(65+i), "content": opts[i]} for i in range(4)]
                
                vocab_notes = dialogue.get('vocabulary_used', [])
                vocab_comment = f"方言: {config.get('name', dialect)}\n"
                vocab_comment += f"特色词汇: {', '.join(vocab_notes) if vocab_notes else '标准词汇'}\n"
                vocab_comment += f"特徴: {', '.join(config.get('features', []))}"
                
                questions.append({
                    'id': qid,
                    'type': 'listening',
                    'content': f'{config.get("flag", dialect)}方言を聴いて答えてください:\n\n{dialogue["text"]}\n\n問題: {dialogue["q"]}',
                    'options': json.dumps(options_list, ensure_ascii=False),
                    'correct_answer': ans,
                    'difficulty': 2,
                    'points': 2.5,
                    'audio_url': f'/static/audio/japanese/{dialect}/listening_{generated_count+1}.mp3',
                    'tags': json.dumps(['日语', dialect, config.get('name', dialect), '听力', '方言'], ensure_ascii=False),
                    'explanation': f'音声原文 ({config.get("name", dialect)}):\n{dialogue["text"]}\n\n{vocab_comment}',
                    'fingerprint': fingerprint,
                    'batch_id': self.batch_id,
                    'dialect_style': dialect,
                    'vocabulary_notes': json.dumps(vocab_notes, ensure_ascii=False),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
                generated_count += 1
            
            attempts += 1
        
        return questions

    def _insert_questions(self, questions, conn):
        """插入题目到数据库"""
        cursor = conn.cursor()
        
        for q in questions:
            cursor.execute('''
                INSERT INTO questions 
                (id, type, content, options, correct_answer, difficulty, points, 
                 audio_url, tags, explanation, fingerprint, batch_id, dialect_style, 
                 vocabulary_notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                q['id'], q['type'], q['content'], q['options'], q['correct_answer'],
                q['difficulty'], q['points'], q['audio_url'], q['tags'], q['explanation'],
                q['fingerprint'], q['batch_id'], q['dialect_style'], q['vocabulary_notes'],
                q['created_at'], q['updated_at']
            ))
        
        conn.commit()
        return len(questions)

    def expand_dialect_bank(self, target_per_dialect=200):
        """扩充方言听力题库"""
        print("=" * 80)
        print("日语方言听力题库自动扩充系统")
        print(f"批次ID: {self.batch_id}")
        print("=" * 80)

        conn = self.connect()
        if not conn:
            return
        
        self._ensure_columns(conn)

        total_added = 0

        for dialect, config in self.dialect_config.items():
            print(f"\n{config['flag']} 生成{config['name']}听力题目...")
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM questions WHERE dialect_style = ?", (dialect,))
            current_count = cursor.fetchone()[0]
            need_count = max(0, target_per_dialect - current_count)
            
            if need_count > 0:
                questions = self._generate_dialect_questions(dialect, need_count, conn)
                added = self._insert_questions(questions, conn)
                print(f"  {config['name']}: 新增 {added} 题 (总计: {current_count + added}题)")
                total_added += added
            else:
                print(f"  {config['name']}: 已达标 ({current_count}题)")

        conn.close()

        print("\n" + "=" * 80)
        print(f"日语方言听力题库扩充完成!")
        print(f"共新增 {total_added} 道听力题目")
        print("=" * 80)

        self.show_statistics()

    def show_statistics(self):
        """显示统计信息"""
        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            print("\n📊 日语方言听力题库统计:")
            
            for dialect, config in self.dialect_config.items():
                cursor.execute("SELECT COUNT(*) FROM questions WHERE dialect_style = ?", (dialect,))
                count = cursor.fetchone()[0]
                print(f"\n{config['flag']} {config['name']}: {count}题")
                print(f"   {config['description']}")

            cursor.execute("SELECT COUNT(*) FROM questions WHERE dialect_style IS NOT NULL")
            total = cursor.fetchone()[0]
            print(f"\n方言听力题目总计: {total}题")

            # 显示方言差异示例
            print("\n📚 方言词汇差异示例:")
            print("-" * 60)
            
            print(f"{'关东腔':<10} {'关西腔':<10} {'英语':<15}")
            print("-" * 60)
            
            for pair in self.dialect_vocabulary_map[:10]:
                print(f"{pair['kanto']:<10} {pair['kansai']:<10} {pair['english']:<15}")

        except Exception as e:
            logger.error(f"显示统计信息失败: {str(e)}")
        finally:
            conn.close()


def main():
    """主函数"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    
    expander = JapaneseDialectExpander(db_path)
    
    print("当前日语方言听力题库状态:")
    expander.show_statistics()
    
    # 扩充每种方言的题库
    expander.expand_dialect_bank(target_per_dialect=300)


if __name__ == "__main__":
    main()