# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import json
import random
import os
from datetime import datetime
import sys

class ListeningQuestionBankExpander:
    
    def __init__(self, db_path="app.db"):
        self.db_path = db_path
        self.conn = None
        self.japanese_id = 10001
        self.english_id = 10001
    
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def init_question_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                exam_id TEXT,
                type TEXT NOT NULL DEFAULT 'single_choice',
                content TEXT NOT NULL,
                options TEXT NOT NULL DEFAULT '[]',
                correct_answer TEXT NOT NULL DEFAULT '',
                difficulty INTEGER NOT NULL DEFAULT 1,
                points REAL NOT NULL DEFAULT 1.0,
                audio_url TEXT,
                tags TEXT NOT NULL DEFAULT '[]',
                explanation TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        self.conn.commit()
        
        cursor.execute('SELECT COUNT(*) FROM questions')
        count = cursor.fetchone()[0]
        
        cursor.execute('SELECT MAX(CAST(SUBSTR(id, 3) AS INTEGER)) FROM questions WHERE id LIKE "JL%"')
        max_jl = cursor.fetchone()[0] or 0
        self.japanese_id = max_jl + 1
        
        cursor.execute('SELECT MAX(CAST(SUBSTR(id, 3) AS INTEGER)) FROM questions WHERE id LIKE "EL%"')
        max_el = cursor.fetchone()[0] or 0
        self.english_id = max_el + 1
        
        print(f"当前题库数量: {count}")
        print(f"日语听力ID起始: JL{self.japanese_id:05d}")
        print(f"英语听力ID起始: EL{self.english_id:05d}")
    
    def generate_japanese_question_id(self):
        qid = f"JL{self.japanese_id:05d}"
        self.japanese_id += 1
        return qid
    
    def generate_english_question_id(self):
        qid = f"EL{self.english_id:05d}"
        self.english_id += 1
        return qid
    
    def generate_japanese_listening_n5(self, count=200):
        """生成N5级别日语听力题目"""
        dialogues = [
            {
                'text': '田中:こんにちは、田中です.佐藤さんは学生ですか.佐藤:はい、大学的生です.田中:そうですか.どこですか.佐藤:東京大学です.',
                'q': '佐藤さんはどこに住んでいますか.',
                'opts': ['大学', '東京大学', '学校', '病院'],
                'ans': 'B'
            },
            {
                'text': '店員:いらっしゃいませ.何を買いますか.客人:この本をください.店員:はい、300円です.客人:はい.',
                'q': '本の値段は何円ですか.',
                'opts': ['100円', '200円', '300円', '400円'],
                'ans': 'C'
            },
            {
                'text': '田中:明日会議がありますか.佐藤:はい、午前10時からです.田中:どこですか.佐藤:3階の会议室です.',
                'q': '会議はいつありますか.',
                'opts': ['今日', '明日', '明後日', '今日ではない'],
                'ans': 'B'
            },
            {
                'text': '母:今日は何を食べますか.子:寿司を食べたいです.母:好啊、どこで食べますか.子:駅の前の店です.',
                'q': '子は今日何を食べたいですか.',
                'opts': ['ラーメン', '寿司', 'カレー', 'そば'],
                'ans': 'B'
            },
            {
                'text': '先生:日本の四季について话しましょう.春は花が咲きます.夏は暑いです.秋は涼しいです.冬は雪が降ります.',
                'q': '冬に何が降りますか.',
                'opts': ['花', '雨', '雪', '風'],
                'ans': 'C'
            },
        ]
        
        questions = []
        for i in range(count):
            d = random.choice(dialogues)
            qid = self.generate_japanese_question_id()
            tags = json.dumps(['日语', 'N5', '听力', '选择题'], ensure_ascii=False)
            
            options_list = [
                {'A': d['opts'][0]},
                {'B': d['opts'][1]},
                {'C': d['opts'][2]},
                {'D': d['opts'][3]}
            ]
            
            questions.append({
                'id': qid,
                'type': 'listening',
                'content': f'听录音并回答问题:\n\n{d["text"]}\n\n问题:{d["q"]}',
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': d['ans'],
                'difficulty': 1,
                'points': 2.0,
                'audio_url': f'/static/audio/japanese/n5/listening_{i+1}.mp3',
                'tags': tags,
                'explanation': f'听力原文:{d["text"]}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_japanese_listening_n4(self, count=200):
        """生成N4级别日语听力题目"""
        dialogues = [
            {
                'text': '田中さんは毎朝6時に起きます.地铁で会社に通勤します.午饭は会社の食堂で食べます.晚上は有时与朋友喝酒,有时在家看电视.',
                'q': '田中さんは怎么去公司?',
                'opts': ['バス', '電車', '車', '自転車'],
                'ans': 'B'
            },
            {
                'text': '先月、日本に行きました.友達の家に泊まりました.旅游业行った.お寺や神社を見学しました.温泉にも入りました.',
                'q': '話者はどこ泊まりましたか.',
                'opts': ['ホテル', '友達の家', '民宿', '旅馆'],
                'ans': 'B'
            },
            {
                'text': '日本の四季について话しましょう.春は花が咲いて、很漂亮です.夏は暑くて、湿气が高いです.秋は涼しくて、红葉が美しいです.冬は寒くて、雪が降ります.',
                'q': '冬はどうですか.',
                'opts': ['暑くて湿度が高い', '涼しくて红葉が美しい', '寒くて雪が降る', '暖かく花の季節'],
                'ans': 'C'
            },
        ]
        
        questions = []
        for i in range(count):
            d = random.choice(dialogues)
            qid = self.generate_japanese_question_id()
            tags = json.dumps(['日语', 'N4', '听力', '选择题'], ensure_ascii=False)
            
            options_list = [
                {'A': d['opts'][0]},
                {'B': d['opts'][1]},
                {'C': d['opts'][2]},
                {'D': d['opts'][3]}
            ]
            
            questions.append({
                'id': qid,
                'type': 'listening',
                'content': f'听录音并回答问题:\n\n{d["text"]}\n\n问题:{d["q"]}',
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': d['ans'],
                'difficulty': 2,
                'points': 2.5,
                'audio_url': f'/static/audio/japanese/n4/listening_{i+1}.mp3',
                'tags': tags,
                'explanation': f'听力原文:{d["text"]}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_japanese_listening_n3(self, count=150):
        """生成N3级别日语听力题目"""
        dialogues = [
            {
                'text': '最近、若者の読書離れが深刻になっている이라는報道がありました.調査によると、20代の約半分が月1冊も本を読まないという結果になりました.理由は「時間がない」「其他の娱乐が多い」などが挙げられています.',
                'q': '若者が本を読まない理由として最も適切なものは?',
                'opts': ['本屋が少ない', '時間がなく、他の娯楽が多い', '本に興味がない', 'お金がない'],
                'ans': 'B'
            },
            {
                'text': '環境問題について话しましょう.地球温暖化のせいで、海面が上昇しています.异常気象も増えています.私たちにできることは、CO2排出を減らすことです.省エネルギーや再エネの利用が重要です.',
                'q': '環境問題解決のために重要なことは?',
                'opts': ['海面上昇を止める', 'CO2排出を減らす', '工場を閉じる', '車を禁止する'],
                'ans': 'B'
            },
        ]
        
        questions = []
        for i in range(count):
            d = random.choice(dialogues)
            qid = self.generate_japanese_question_id()
            tags = json.dumps(['日语', 'N3', '听力', '选择题'], ensure_ascii=False)
            
            options_list = [
                {'A': d['opts'][0]},
                {'B': d['opts'][1]},
                {'C': d['opts'][2]},
                {'D': d['opts'][3]}
            ]
            
            questions.append({
                'id': qid,
                'type': 'listening',
                'content': f'听录音并回答问题:\n\n{d["text"]}\n\n问题:{d["q"]}',
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': d['ans'],
                'difficulty': 3,
                'points': 3.0,
                'audio_url': f'/static/audio/japanese/n3/listening_{i+1}.mp3',
                'tags': tags,
                'explanation': f'听力原文:{d["text"]}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_english_listening_basic(self, count=200):
        """生成基础级英语听力题目"""
        dialogues = [
            {
                'text': 'A: Hello, how are you today? B: I\'m fine, thank you. And you? A: I\'m good too. Thank you for asking.',
                'q': 'How is Person A today?',
                'opts': ['Tired', 'Good', 'Sad', 'Sick'],
                'ans': 'B'
            },
            {
                'text': 'A: What time is it? B: It\'s three o\'clock. A: Thank you. I have a meeting at four.',
                'q': 'When is the meeting?',
                'opts': ['At two', 'At three', 'At four', 'At five'],
                'ans': 'C'
            },
            {
                'text': 'A: Where are you from? B: I\'m from Japan. A: That\'s nice. I\'ve never been there.',
                'q': 'Where is Person B from?',
                'opts': ['China', 'Japan', 'Korea', 'America'],
                'ans': 'B'
            },
            {
                'text': 'A: Would you like some coffee? B: Yes, please. A: How do you take it? B: Black, please.',
                'q': 'How does Person B take their coffee?',
                'opts': ['With milk', 'With sugar', 'Black', 'With cream'],
                'ans': 'C'
            },
            {
                'text': 'A: What did you do last weekend? B: I went to the movies. A: What did you see? B: I saw a comedy movie.',
                'q': 'What kind of movie did Person B see?',
                'opts': ['Action movie', 'Comedy', 'Drama', 'Horror'],
                'ans': 'B'
            },
        ]
        
        questions = []
        for i in range(count):
            d = random.choice(dialogues)
            qid = self.generate_english_question_id()
            tags = json.dumps(['英语', '基础', '听力', '选择题'], ensure_ascii=False)
            
            options_list = [
                {'A': d['opts'][0]},
                {'B': d['opts'][1]},
                {'C': d['opts'][2]},
                {'D': d['opts'][3]}
            ]
            
            questions.append({
                'id': qid,
                'type': 'listening',
                'content': f'Listen and answer the question:\n\n{d["text"]}\n\nQuestion: {d["q"]}',
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': d['ans'],
                'difficulty': 1,
                'points': 2.0,
                'audio_url': f'/static/audio/english/basic/listening_{i+1}.mp3',
                'tags': tags,
                'explanation': f'Audio transcript: {d["text"]}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_english_listening_intermediate(self, count=200):
        """生成中级英语听力题目"""
        dialogues = [
            {
                'text': 'Professor: Today we\'ll discuss climate change and its impact on global ecosystems. Students: What can individuals do to help? Professor: There are several things: reducing energy consumption, using public transportation, and recycling are all effective ways to reduce your carbon footprint.',
                'q': 'According to the professor, what is NOT mentioned as an individual action?',
                'opts': ['Reducing energy consumption', 'Using public transportation', 'Planting trees', 'Recycling'],
                'ans': 'C'
            },
            {
                'text': 'Interviewer: Can you tell me about your work experience? Candidate: Certainly. I worked at ABC Company for five years as a project manager. I was responsible for leading teams of 10-15 people and managing budgets of up to $500,000.',
                'q': 'What was the candidate\'s role at ABC Company?',
                'opts': ['Software Engineer', 'Project Manager', 'Marketing Director', 'Sales Representative'],
                'ans': 'B'
            },
            {
                'text': 'Guide: Welcome to our museum. This building is over 100 years old. We have three main sections: the natural history wing, the art collection, and the interactive science center. Please feel free to ask any questions.',
                'q': 'How many main sections does the museum have?',
                'opts': ['Two', 'Three', 'Four', 'Five'],
                'ans': 'B'
            },
        ]
        
        questions = []
        for i in range(count):
            d = random.choice(dialogues)
            qid = self.generate_english_question_id()
            tags = json.dumps(['英语', '中级', '听力', '选择题'], ensure_ascii=False)
            
            options_list = [
                {'A': d['opts'][0]},
                {'B': d['opts'][1]},
                {'C': d['opts'][2]},
                {'D': d['opts'][3]}
            ]
            
            questions.append({
                'id': qid,
                'type': 'listening',
                'content': f'Listen and answer the question:\n\n{d["text"]}\n\nQuestion: {d["q"]}',
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': d['ans'],
                'difficulty': 2,
                'points': 2.5,
                'audio_url': f'/static/audio/english/intermediate/listening_{i+1}.mp3',
                'tags': tags,
                'explanation': f'Audio transcript: {d["text"]}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_english_listening_advanced(self, count=150):
        """生成高级英语听力题目"""
        dialogues = [
            {
                'text': 'News anchor: Breaking news from the international climate summit. World leaders have agreed to new emission reduction targets. The agreement requires all participating nations to cut their carbon emissions by 50% by 2035. This is considered a significant step forward in the global fight against climate change.',
                'q': 'What is the main point of this news report?',
                'opts': ['Climate summit failed to reach agreement', 'New emission reduction targets were set', 'All nations refused to participate', 'Carbon emissions increased'],
                'ans': 'B'
            },
            {
                'text': 'Professor: Let\'s analyze this case study. A tech company launched an AI product that quickly gained market share but faced criticism over privacy concerns. The company had to balance innovation with regulatory compliance. This highlights the ethical challenges in emerging technologies.',
                'q': 'What does this case study illustrate?',
                'opts': ['AI is harmful to society', 'Ethical challenges in emerging technologies', 'Tech companies should avoid innovation', 'Privacy is not important'],
                'ans': 'B'
            },
        ]
        
        questions = []
        for i in range(count):
            d = random.choice(dialogues)
            qid = self.generate_english_question_id()
            tags = json.dumps(['英语', '高级', '听力', '选择题'], ensure_ascii=False)
            
            options_list = [
                {'A': d['opts'][0]},
                {'B': d['opts'][1]},
                {'C': d['opts'][2]},
                {'D': d['opts'][3]}
            ]
            
            questions.append({
                'id': qid,
                'type': 'listening',
                'content': f'Listen and answer the question:\n\n{d["text"]}\n\nQuestion: {d["q"]}',
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': d['ans'],
                'difficulty': 3,
                'points': 3.0,
                'audio_url': f'/static/audio/english/advanced/listening_{i+1}.mp3',
                'tags': tags,
                'explanation': f'Audio transcript: {d["text"]}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_ielts_listening(self, count=100):
        """生成雅思听力题目"""
        dialogues = [
            {
                'text': 'You will hear a conversation between a student and a university admissions officer. Officer: Good morning. How can I help you? Student: Good morning. I\'d like to inquire about the application process for the Computer Science program. Officer: Certainly. I\'ll need your academic transcripts, two letters of recommendation, and a personal statement of about 500 words.',
                'q': 'What documents does the officer ask for?',
                'opts': ['Transcripts and ID only', 'Transcripts, recommendation letters, and personal statement', 'Only recommendation letters', 'Application fee and transcripts'],
                'ans': 'B'
            },
            {
                'text': 'You will hear a radio announcement about a community event. Attention shoppers. Maplewood Mall is hosting its annual charity fundraiser next Saturday from 10 AM to 4 PM. There will be live music, food vendors, and a silent auction. All proceeds will go to the local children\'s hospital.',
                'q': 'When and where is the charity fundraiser?',
                'opts': ['Sunday at City Park', 'Saturday at Maplewood Mall', 'Saturday at City Hall', 'Weekday at Maplewood Mall'],
                'ans': 'B'
            },
        ]
        
        questions = []
        for i in range(count):
            d = random.choice(dialogues)
            qid = self.generate_english_question_id()
            tags = json.dumps(['英语', '雅思', '听力', '选择题'], ensure_ascii=False)
            
            options_list = [
                {'A': d['opts'][0]},
                {'B': d['opts'][1]},
                {'C': d['opts'][2]},
                {'D': d['opts'][3]}
            ]
            
            questions.append({
                'id': qid,
                'type': 'listening',
                'content': f'IELTS Listening Practice:\n\n{d["text"]}\n\nQuestion: {d["q"]}',
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': d['ans'],
                'difficulty': 3,
                'points': 3.5,
                'audio_url': f'/static/audio/english/ielts/listening_{i+1}.mp3',
                'tags': tags,
                'explanation': f'Audio transcript: {d["text"]}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_toefl_listening(self, count=100):
        """生成托福听力题目"""
        dialogues = [
            {
                'text': 'Listen to a conversation between a student and a professor. Professor: I noticed you missed the last two lectures. Student: I\'m sorry, professor. I\'ve been dealing with some health issues. Professor: I understand. Would you like me to provide the lecture notes? Student: That would be very helpful, thank you.',
                'q': 'Why did the student miss the lectures?',
                'opts': ['He was traveling', 'He had health issues', 'He forgot about the class', 'He had a family emergency'],
                'ans': 'B'
            },
            {
                'text': 'Listen to part of a lecture in a biology class. Professor: Today we\'ll discuss the process of photosynthesis. Plants convert sunlight into chemical energy through this process. The key inputs are sunlight, water, and carbon dioxide. The outputs are glucose and oxygen.',
                'q': 'What are the outputs of photosynthesis?',
                'opts': ['Water and oxygen', 'Glucose and oxygen', 'Carbon dioxide and water', 'Sunlight and glucose'],
                'ans': 'B'
            },
        ]
        
        questions = []
        for i in range(count):
            d = random.choice(dialogues)
            qid = self.generate_english_question_id()
            tags = json.dumps(['英语', '托福', '听力', '选择题'], ensure_ascii=False)
            
            options_list = [
                {'A': d['opts'][0]},
                {'B': d['opts'][1]},
                {'C': d['opts'][2]},
                {'D': d['opts'][3]}
            ]
            
            questions.append({
                'id': qid,
                'type': 'listening',
                'content': f'TOEFL Listening Practice:\n\n{d["text"]}\n\nQuestion: {d["q"]}',
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': d['ans'],
                'difficulty': 4,
                'points': 4.0,
                'audio_url': f'/static/audio/english/toefl/listening_{i+1}.mp3',
                'tags': tags,
                'explanation': f'Audio transcript: {d["text"]}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def insert_questions(self, questions):
        cursor = self.conn.cursor()
        
        for q in questions:
            cursor.execute('''
                INSERT INTO questions 
                (id, exam_id, type, content, options, correct_answer, difficulty, points, audio_url, tags, explanation, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                q['id'],
                q.get('exam_id', ''),
                q['type'],
                q['content'],
                q['options'],
                q['correct_answer'],
                q['difficulty'],
                q['points'],
                q.get('audio_url', ''),
                q['tags'],
                q['explanation'],
                q['created_at'],
                q['updated_at']
            ))
        
        self.conn.commit()
        print(f"  成功插入 {len(questions)} 道题目")
    
    def expand_listening_question_bank(self):
        print("=" * 60)
        print("开始扩充听力题库")
        print("=" * 60)
        
        all_questions = []
        
        print("\n📚 生成日语听力题目...")
        all_questions.extend(self.generate_japanese_listening_n5(200))
        all_questions.extend(self.generate_japanese_listening_n4(200))
        all_questions.extend(self.generate_japanese_listening_n3(150))
        
        print("\n📚 生成英语听力题目...")
        all_questions.extend(self.generate_english_listening_basic(200))
        all_questions.extend(self.generate_english_listening_intermediate(200))
        all_questions.extend(self.generate_english_listening_advanced(150))
        all_questions.extend(self.generate_ielts_listening(100))
        all_questions.extend(self.generate_toefl_listening(100))
        
        print(f"\n总计生成 {len(all_questions)} 道听力题目")
        
        batch_size = 300
        for i in range(0, len(all_questions), batch_size):
            batch = all_questions[i:i+batch_size]
            self.insert_questions(batch)
        
        print("\n" + "=" * 60)
        print("听力题库扩充完成!")
        print("=" * 60)
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM questions WHERE type = 'listening'")
        total = cursor.fetchone()[0]
        print(f"\n听力题目总数: {total}")
        
        cursor.execute("SELECT COUNT(*) FROM questions WHERE tags LIKE '%日语%' AND type = 'listening'")
        japanese = cursor.fetchone()[0]
        print(f"日语听力: {japanese}")
        
        cursor.execute("SELECT COUNT(*) FROM questions WHERE tags LIKE '%英语%' AND type = 'listening'")
        english = cursor.fetchone()[0]
        print(f"英语听力: {english}")

def main():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
    print(f"数据库路径: {db_path}")
    
    expander = ListeningQuestionBankExpander(db_path)
    expander.connect()
    expander.init_question_table()
    
    expander.expand_listening_question_bank()
    
    expander.close()
    print("\n听力题库扩充任务完成!")

if __name__ == '__main__':
    main()
