#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多发音风格英语听力题库自动扩充系统
支持：英式(British)、美式(American)、澳式(Australian)、欧式(European)
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


class MultiAccentListeningExpander:
    """多发音风格听力题库扩充器"""

    def __init__(self, db_path="app.db"):
        self.db_path = db_path
        self.batch_id = str(uuid.uuid4())[:12]

        # 发音风格配置
        self.accent_config = {
            "british": {
                "name": "英式发音",
                "flag": "🇬🇧",
                "description": "British English (RP - Received Pronunciation)",
                "vocabulary": {
                    "colour": "color",
                    "centre": "center",
                    "theatre": "theater",
                    "organise": "organize",
                    "realise": "realize",
                    "lorry": "truck",
                    "flat": "apartment",
                    "lift": "elevator",
                    "biscuit": "cookie",
                    "chips": "fries"
                },
                "greetings": ["Good morning", "Good afternoon", "How do you do", "Cheers"],
                "time_expressions": ["half past three", "quarter to four", "fortnight"]
            },
            "american": {
                "name": "美式发音",
                "flag": "🇺🇸",
                "description": "American English (General American)",
                "vocabulary": {
                    "color": "colour",
                    "center": "centre",
                    "theater": "theatre",
                    "organize": "organise",
                    "realize": "realise",
                    "truck": "lorry",
                    "apartment": "flat",
                    "elevator": "lift",
                    "cookie": "biscuit",
                    "fries": "chips"
                },
                "greetings": ["Hi there", "Hey", "How's it going", "What's up"],
                "time_expressions": ["three thirty", "three forty-five", "two weeks"]
            },
            "australian": {
                "name": "澳式发音",
                "flag": "🇦🇺",
                "description": "Australian English",
                "vocabulary": {
                    "colour": "color",
                    "centre": "center",
                    "ute": "pickup truck",
                    "arvo": "afternoon",
                    "brekkie": "breakfast",
                    "barbie": "barbecue",
                    "mate": "friend",
                    "servo": "service station",
                    "bottle-o": "liquor store",
                    "mozzie": "mosquito"
                },
                "greetings": ["G'day mate", "How's it going", "No worries", "She'll be right"],
                "time_expressions": ["arvo", "this arvo", "tomorrow arvo"]
            },
            "european": {
                "name": "欧式发音",
                "flag": "🇪🇺",
                "description": "European English (Euro-English)",
                "vocabulary": {
                    "colour": "color",
                    "centre": "center",
                    "mobile": "cellphone",
                    "timetable": "schedule",
                    "holiday": "vacation",
                    "university": "college",
                    "chemist": "pharmacy",
                    "cinema": "movie theater",
                    "motorway": "highway",
                    "rubber": "eraser"
                },
                "greetings": ["Hello", "Good day", "Welcome", "Pleased to meet you"],
                "time_expressions": ["half three", "quarter four", "two weeks"]
            }
        }

        # 发音风格特定的对话模板
        self.accent_dialogues = {
            "british": [
                {
                    "text": "A: Good morning, sir. How may I help you today? B: I'd like to book a table for two, please. A: Certainly. What time would you prefer? B: Half past seven, if that's convenient.",
                    "q": "What time does the customer want to book the table?",
                    "opts": ["7:00", "7:30", "8:00", "6:30"],
                    "ans": "B",
                    "vocabulary_used": ["half past seven"]
                },
                {
                    "text": "A: I'm taking the lift to the fifth floor. B: Oh, I'll join you. Which flat are you visiting? A: Number 503. It's my aunt's new place. B: Lovely. I'm in flat 504.",
                    "q": "What is the British term for 'elevator' used in the dialogue?",
                    "opts": ["elevator", "lift", "escalator", "stairs"],
                    "ans": "B",
                    "vocabulary_used": ["lift", "flat"]
                },
                {
                    "text": "A: Would you like some biscuits with your tea? B: Oh, yes please. These are lovely. A: They're from the local bakery. I got them this morning. B: They taste absolutely brilliant!",
                    "q": "What does 'biscuits' refer to in British English?",
                    "opts": ["crackers", "cookies", "bread", "cakes"],
                    "ans": "B",
                    "vocabulary_used": ["biscuits"]
                },
                {
                    "text": "A: The lorry is blocking the road. B: Yes, it's delivering goods to the shop. A: How long will it take? B: About a quarter of an hour, I should think.",
                    "q": "What vehicle is being discussed?",
                    "opts": ["car", "van", "truck", "bus"],
                    "ans": "C",
                    "vocabulary_used": ["lorry", "quarter of an hour"]
                },
                {
                    "text": "A: I'm going to the theatre tonight. B: Oh, which one? A: The West End. We're seeing a musical. B: How wonderful! I do hope you enjoy it.",
                    "q": "Where is the speaker going?",
                    "opts": ["cinema", "concert hall", "theatre", "opera house"],
                    "ans": "C",
                    "vocabulary_used": ["theatre"]
                }
            ],
            "american": [
                {
                    "text": "A: Hi there! How's it going? B: Pretty good, thanks. Just heading to work. A: Cool. Where do you work? B: Downtown, in that big office building on Main Street.",
                    "q": "How does Person A greet Person B?",
                    "opts": ["Good morning", "Hi there", "Hello", "How do you do"],
                    "ans": "B",
                    "vocabulary_used": ["Hi there"]
                },
                {
                    "text": "A: I need to take the elevator to the 10th floor. B: Sure, it's right over there. A: Thanks! Is that your apartment? B: No, I live in a house in the suburbs.",
                    "q": "What is the American term for 'lift'?",
                    "opts": ["lift", "escalator", "elevator", "stairs"],
                    "ans": "C",
                    "vocabulary_used": ["elevator", "apartment"]
                },
                {
                    "text": "A: Want some cookies? I just baked them. B: Oh wow, they smell amazing! A: Help yourself. They're chocolate chip. B: These are the best cookies I've ever had!",
                    "q": "What does 'cookies' refer to in American English?",
                    "opts": ["biscuits", "cookies", "crackers", "scones"],
                    "ans": "B",
                    "vocabulary_used": ["cookies"]
                },
                {
                    "text": "A: The truck is here with the delivery. B: Great! Where should they unload it? A: Around back, by the loading dock. B: I'll go direct them.",
                    "q": "What vehicle is being discussed?",
                    "opts": ["car", "van", "truck", "lorry"],
                    "ans": "C",
                    "vocabulary_used": ["truck"]
                },
                {
                    "text": "A: I'm going to the theater tonight. B: Which one? The multiplex downtown? A: Yeah, we're seeing the new action movie. B: Awesome! I heard it's really good.",
                    "q": "What is the American spelling of 'theatre'?",
                    "opts": ["theatre", "theater", "cinema", "hall"],
                    "ans": "B",
                    "vocabulary_used": ["theater"]
                }
            ],
            "australian": [
                {
                    "text": "A: G'day mate! How's it going? B: Not bad, mate. Just finished brekkie. A: Fair dinkum? What did you have? B: Just some toast and a cuppa. No worries!",
                    "q": "What Australian term is used for 'breakfast'?",
                    "opts": ["breakfast", "brekkie", "morning meal", "brekky"],
                    "ans": "B",
                    "vocabulary_used": ["G'day mate", "brekkie", "No worries"]
                },
                {
                    "text": "A: Coming to the barbie this arvo? B: You bet! Should I bring anything? A: Just some snags if you can. B: No worries, mate. I'll grab some from the servo on the way.",
                    "q": "What does 'barbie' mean in Australian English?",
                    "opts": ["doll", "barbecue", "party", "picnic"],
                    "ans": "B",
                    "vocabulary_used": ["barbie", "arvo", "servo"]
                },
                {
                    "text": "A: The mozzies are bad tonight. B: Yeah, better get the repellent. A: I'll light a citronella candle. B: Good idea. They're driving me crazy!",
                    "q": "What are 'mozzies'?",
                    "opts": ["flies", "bees", "mosquitoes", "ants"],
                    "ans": "C",
                    "vocabulary_used": ["mozzies"]
                },
                {
                    "text": "A: I'm heading to the bottle-o. Need anything? B: Yeah, grab us a slab of beer, thanks mate. A: No worries. Be back in a tick. B: She'll be right, take your time.",
                    "q": "Where is the speaker going?",
                    "opts": ["bar", "pub", "liquor store", "restaurant"],
                    "ans": "C",
                    "vocabulary_used": ["bottle-o", "No worries", "She'll be right"]
                },
                {
                    "text": "A: That ute is pretty handy for the farm. B: Yeah, can carry loads of gear in the back. A: Better than a regular car for sure. B: Absolutely, mate!",
                    "q": "What is a 'ute'?",
                    "opts": ["car", "pickup truck", "van", "motorcycle"],
                    "ans": "B",
                    "vocabulary_used": ["ute", "mate"]
                }
            ],
            "european": [
                {
                    "text": "A: Hello, I'd like to check the timetable for trains to Paris. B: Certainly. There's one at 14:30 and another at 18:45. A: Perfect. I'll book the 14:30. B: That will be 75 euros, please.",
                    "q": "What is the European term for 'schedule'?",
                    "opts": ["schedule", "timetable", "agenda", "plan"],
                    "ans": "B",
                    "vocabulary_used": ["timetable"]
                },
                {
                    "text": "A: I need to top up my mobile. B: You can do that at the chemist's. A: Oh, is that where? B: Yes, they have a top-up station there.",
                    "q": "What does 'mobile' refer to?",
                    "opts": ["car", "cellphone", "bicycle", "scooter"],
                    "ans": "B",
                    "vocabulary_used": ["mobile", "chemist"]
                },
                {
                    "text": "A: We're going on holiday to Spain next week. B: How exciting! How long will you stay? A: Two weeks. We're renting a villa. B: That sounds wonderful!",
                    "q": "What is the European term for 'vacation'?",
                    "opts": ["vacation", "holiday", "trip", "break"],
                    "ans": "B",
                    "vocabulary_used": ["holiday"]
                },
                {
                    "text": "A: Take the motorway north for about 50 kilometers. B: Which exit should I take? A: Exit 23, then follow signs to the centre. B: Got it, thanks!",
                    "q": "What is the European term for 'highway'?",
                    "opts": ["highway", "freeway", "motorway", "expressway"],
                    "ans": "C",
                    "vocabulary_used": ["motorway", "centre"]
                },
                {
                    "text": "A: I need to buy a rubber for my exam. B: Don't forget your calculator too. A: Right. And some pens. B: The university shop should have everything.",
                    "q": "What does 'rubber' mean in European English?",
                    "opts": ["balloon", "eraser", "gloves", "band"],
                    "ans": "B",
                    "vocabulary_used": ["rubber", "university"]
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
        if 'accent_style' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN accent_style TEXT")
        if 'vocabulary_notes' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN vocabulary_notes TEXT")
        
        conn.commit()

    def _generate_fingerprint(self, text, question, options, answer, accent):
        """生成去重指纹"""
        content = f"{accent}|{text}|{question}|{answer}|" + "|".join(sorted(options))
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _is_duplicate(self, fingerprint, conn):
        """检查是否重复"""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM questions WHERE fingerprint = ?", (fingerprint,))
        return cursor.fetchone()[0] > 0

    def _generate_accent_questions(self, accent, count, conn):
        """生成特定发音风格的题目"""
        dialogues = self.accent_dialogues.get(accent, [])
        config = self.accent_config.get(accent, {})
        
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
            
            fingerprint = self._generate_fingerprint(dialogue['text'], dialogue['q'], opts, ans, accent)
            
            if not self._is_duplicate(fingerprint, conn):
                # 使用UUID确保唯一性
                qid = f"{accent.upper()[:2]}{uuid.uuid4().hex[:8]}"
                
                options_list = [{"option": chr(65+i), "content": opts[i]} for i in range(4)]
                
                # 创建词汇注释
                vocab_notes = dialogue.get('vocabulary_used', [])
                vocab_comment = f"发音风格: {config.get('name', accent)}\n"
                vocab_comment += f"特色词汇: {', '.join(vocab_notes) if vocab_notes else '标准词汇'}"
                
                questions.append({
                    'id': qid,
                    'type': 'listening',
                    'content': f'Listen to the {config.get("name", accent)} speaker and answer:\n\n{dialogue["text"]}\n\nQuestion: {dialogue["q"]}',
                    'options': json.dumps(options_list, ensure_ascii=False),
                    'correct_answer': ans,
                    'difficulty': 2,
                    'points': 2.5,
                    'audio_url': f'/static/audio/english/{accent}/listening_{generated_count+1}.mp3',
                    'tags': json.dumps(['英语', accent, config.get('name', accent), '听力', '发音辨析'], ensure_ascii=False),
                    'explanation': f'Audio transcript ({config.get("name", accent)}):\n{dialogue["text"]}\n\n{vocab_comment}',
                    'fingerprint': fingerprint,
                    'batch_id': self.batch_id,
                    'accent_style': accent,
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
                 audio_url, tags, explanation, fingerprint, batch_id, accent_style, 
                 vocabulary_notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                q['id'], q['type'], q['content'], q['options'], q['correct_answer'],
                q['difficulty'], q['points'], q['audio_url'], q['tags'], q['explanation'],
                q['fingerprint'], q['batch_id'], q['accent_style'], q['vocabulary_notes'],
                q['created_at'], q['updated_at']
            ))
        
        conn.commit()
        return len(questions)

    def expand_multi_accent_bank(self, target_per_accent=200):
        """扩充多发音风格听力题库"""
        print("=" * 80)
        print("多发音风格英语听力题库自动扩充系统")
        print(f"批次ID: {self.batch_id}")
        print("=" * 80)

        conn = self.connect()
        if not conn:
            return
        
        self._ensure_columns(conn)

        total_added = 0

        for accent, config in self.accent_config.items():
            print(f"\n{config['flag']} 生成{config['name']}听力题目...")
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM questions WHERE accent_style = ?", (accent,))
            current_count = cursor.fetchone()[0]
            need_count = max(0, target_per_accent - current_count)
            
            if need_count > 0:
                questions = self._generate_accent_questions(accent, need_count, conn)
                added = self._insert_questions(questions, conn)
                print(f"  {config['name']}: 新增 {added} 题 (总计: {current_count + added}题)")
                total_added += added
            else:
                print(f"  {config['name']}: 已达标 ({current_count}题)")

        conn.close()

        print("\n" + "=" * 80)
        print(f"多发音风格听力题库扩充完成!")
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

            print("\n📊 多发音风格听力题库统计:")
            
            for accent, config in self.accent_config.items():
                cursor.execute("SELECT COUNT(*) FROM questions WHERE accent_style = ?", (accent,))
                count = cursor.fetchone()[0]
                print(f"\n{config['flag']} {config['name']}: {count}题")
                print(f"   {config['description']}")

            cursor.execute("SELECT COUNT(*) FROM questions WHERE accent_style IS NOT NULL")
            total = cursor.fetchone()[0]
            print(f"\n多发音风格听力题目总计: {total}题")

            # 显示词汇差异示例
            print("\n📚 词汇差异示例:")
            print("-" * 60)
            
            examples = [
                ("英式", "lift, flat, biscuit, lorry, theatre"),
                ("美式", "elevator, apartment, cookie, truck, theater"),
                ("澳式", "ute, arvo, brekkie, barbie, servo"),
                ("欧式", "mobile, timetable, holiday, motorway, rubber")
            ]
            
            for style, vocab in examples:
                print(f"{style}: {vocab}")

        except Exception as e:
            logger.error(f"显示统计信息失败: {str(e)}")
        finally:
            conn.close()

    def create_accent_comparison_questions(self, conn):
        """创建发音对比题目"""
        comparison_questions = [
            {
                "text": "Listen to four speakers and identify their accents:\n\nSpeaker A: 'I'll take the lift to my flat.'\nSpeaker B: 'I'll take the elevator to my apartment.'\nSpeaker C: 'G'day mate, how's it going?'\nSpeaker D: 'I need to check the timetable for the train.'",
                "q": "Match each speaker to their accent:",
                "opts": ["A-British, B-American, C-Australian, D-European",
                        "A-American, B-British, C-European, D-Australian",
                        "A-European, B-Australian, C-British, D-American",
                        "A-Australian, B-European, C-American, D-British"],
                "ans": "A",
                "explanation": "Speaker A uses British terms (lift, flat), Speaker B uses American terms (elevator, apartment), Speaker C uses Australian greeting (G'day mate), Speaker D uses European term (timetable)."
            }
        ]
        
        questions = []
        for i, q_data in enumerate(comparison_questions):
            qid = f"EL{random.randint(10000, 99999):05d}"
            
            options_list = [{"option": chr(65+j), "content": q_data['opts'][j]} for j in range(4)]
            
            questions.append({
                'id': qid,
                'type': 'listening',
                'content': f'Accent Comparison Exercise:\n\n{q_data["text"]}\n\nQuestion: {q_data["q"]}',
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': q_data['ans'],
                'difficulty': 3,
                'points': 3.0,
                'audio_url': f'/static/audio/english/comparison/accent_comparison_{i+1}.mp3',
                'tags': json.dumps(['英语', '发音对比', '听力', '多风格'], ensure_ascii=False),
                'explanation': q_data['explanation'],
                'fingerprint': self._generate_fingerprint(q_data['text'], q_data['q'], q_data['opts'], q_data['ans'], 'comparison'),
                'batch_id': self.batch_id,
                'accent_style': 'comparison',
                'vocabulary_notes': json.dumps(['accent comparison'], ensure_ascii=False),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions


def main():
    """主函数"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    
    expander = MultiAccentListeningExpander(db_path)
    
    print("当前多发音风格听力题库状态:")
    expander.show_statistics()
    
    # 扩充每种发音风格的题库
    expander.expand_multi_accent_bank(target_per_accent=300)


if __name__ == "__main__":
    main()