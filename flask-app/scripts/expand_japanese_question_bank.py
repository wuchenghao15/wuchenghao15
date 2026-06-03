# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import json
import random
import os
from datetime import datetime

class JapaneseQuestionBankExpander:
    
    def __init__(self, db_path="app.db"):
        self.db_path = db_path
        self.conn = None
        self.question_id = 1
    
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
        if count > 0:
            cursor.execute('SELECT MAX(CAST(SUBSTR(id, 5) AS INTEGER)) FROM questions WHERE id LIKE "JQ%"')
            max_id = cursor.fetchone()[0]
            self.question_id = (max_id or 0) + 1
        print(f"当前题库数量: {count}, 下一个题目ID: {self.question_id}")
    
    def generate_question_id(self):
        qid = f"JQ{self.question_id:05d}"
        self.question_id += 1
        return qid
    
    def generate_vocabulary_questions(self, level, count=100):
        vocabulary_data = {
            'N5': [
                ('こんにちは', '你好'), ('さようなら', '再见'), ('ありがとう', '谢谢'),
                ('すみません', '对不起'), ('はい', '是'), ('いいえ', '不是'),
                ('お願いします', '拜托了'), ('学校', '学校'), ('先生', '老师'),
                ('学生', '学生'), ('食堂', '食堂'), ('図書館', '图书馆'),
            ],
            'N4': [
                ('美しい', '美丽的'), ('大きい', '大的'), ('食べる', '吃'),
                ('飲む', '喝'), ('行く', '去'), ('来る', '来'),
                ('新しい', '新的'), ('古い', '旧的'), ('高い', '高的/贵的'),
                ('易しい', '简单的'), ('難しい', '难的'), ('好き', '喜欢'),
            ],
            'N3': [
                ('経験', '经验'), ('意見', '意见'), ('提案', '提案'),
                ('確認', '确认'), ('努力', '努力'), ('効果', '效果'),
                ('影響', '影响'), ('関係', '关系'), ('理解', '理解'),
                ('価値', '价值'), ('意味', '意思'), ('結果', '结果'),
            ],
            'N2': [
                ('権利', '权利'), ('義務', '义务'), ('平等', '平等'),
                ('責任', '责任'), ('影響力', '影响力'), ('優先', '优先'),
                ('傾向', '倾向'), ('視点', '视角'), ('根拠', '根据'),
                ('判断', '判断'), ('機会', '机会'), ('能力', '能力'),
            ],
            'N1': [
                ('認識', '认识'), ('本質', '本质'), ('概念', '概念'),
                ('原理', '原理'), ('原則', '原则'), ('発想', '想法'),
                ('論理', '逻辑'), ('帰結', '归结'), ('展開', '展开'),
                ('推移', '推移'), ('体現', '体现'), ('志向', '志向'),
            ]
        }
        
        questions = []
        vocab_list = vocabulary_data.get(level, vocabulary_data['N5'])
        
        for i in range(count):
            word, meaning = random.choice(vocab_list)
            qid = self.generate_question_id()
            tags = json.dumps([f'日语', f'{level}', '词汇', '选择题'], ensure_ascii=False)
            
            options_list = [
                {'A': word},
                {'B': word[:-1] if len(word) > 1 else word + 'あ'},
                {'C': word + 'です'},
                {'D': word[1:] if len(word) > 1 else word}
            ]
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'请选择"meaning"的正确日语词汇:\n{meaning}',
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 1 if level in ['N5', 'N4'] else 2 if level == 'N3' else 3 if level == 'N2' else 4,
                'points': 1.0,
                'tags': tags,
                'explanation': f'"{word}"的意思是"{meaning}"',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_grammar_questions(self, level, count=100):
        grammar_data = {
            'N5': [
                ('～ます', '动词现在时肯定式'),
                ('～ません', '动词现在时否定式'),
                ('～ました', '动词过去时肯定式'),
                ('～てください', '请做某事'),
                ('～たいです', '想做某事'),
                ('～に行きます', '去...做某事'),
                ('～ができます', '会.../能...'),
                ('～です', '判断句'),
                ('～があります', '有...'),
            ],
            'N4': [
                ('～たいです', '想要做...'),
                ('～たくないです', '不想要做...'),
                ('～ながら', '一边...一边...'),
                ('～ потому что', '因为...'),
                ('～ Ante', '...之前'),
                ('～ NACHT', '...之后'),
                ('～そうです', '看起来...'),
                ('～やすいです', '容易...'),
                ('～にくいです', '难以...'),
            ],
            'N3': [
                ('～はずです', '应该...'),
                ('～ようです', '好像...'),
                ('～続けます', '继续...'),
                ('～始めます', '开始...'),
                ('～やすくなります', '变得容易...'),
                ('～にくくなります', '变得困难...'),
                ('～ため(に)', '因为...'),
                ('～を通じて', '通过...'),
                ('～によって', '根据...'),
            ],
            'N2': [
                ('～にとって', '对...来说'),
                ('～に対して', '对...'),
                ('～について', '关于...'),
                ('～によって', '根据...'),
                ('～を通じて', '通过...'),
                ('～に加えて', '加上...'),
                ('～ものです', '确实是...'),
                ('～ことだ', '重要的是...'),
                ('～わけではありません', '并不是...'),
            ],
            'N1': [
                ('～を踏まえて', '基于...'),
                ('～に至るまで', '直到...'),
                ('～いかんを問わず', '不论...'),
                ('～そばから', '刚...就...'),
                ('～たとたん', '刚...就...'),
                ('～ようでは', '如果...的话'),
                ('～た一经', '一旦...就...'),
                ('～uance', '虽然...但是...'),
                ('～凍死', '每逢...'),
            ]
        }
        
        questions = []
        patterns = grammar_data.get(level, grammar_data['N5'])
        
        for i in range(count):
            pattern, meaning = random.choice(patterns)
            qid = self.generate_question_id()
            tags = json.dumps([f'日语', f'{level}', '语法', '选择题'], ensure_ascii=False)
            
            options_list = [
                {'A': pattern},
                {'B': f'{pattern}ない'},
                {'C': f'{pattern}た'},
                {'D': f'{pattern}そう'}
            ]
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'请选择正确的语法形式:\n意思:{meaning}',
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 1 if level in ['N5', 'N4'] else 2 if level == 'N3' else 3 if level == 'N2' else 4,
                'points': 1.5,
                'tags': tags,
                'explanation': f'"{pattern}"表示{meaning}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_reading_questions(self, level, count=50):
        readings_data = {
            'N5': [
                ('田中さんは毎朝コーヒーを飲みます.', '田中さん每日何を飲みますか.', ['お茶', 'コーヒー', '牛乳', '水'], 'B'),
                ('今日は天気です.公園に行きます.', '今日はどうでしたか.', ['雨です', '曇です', '晴れです', '雪です'], 'C'),
                ('私は学生です.日本語を勉強しています.', '私は何をしていますか.', ['働いています', '勉強しています', '遊んでいます', '寝ています'], 'B'),
            ],
            'N4': [
                ('日本の生活はまだ慣れません.でも、少しずつ楽しくなってきました.', '話者は日本の生活にどう思いますか.', ['とても慣れましたが', '全然慣れていません', '少し慣れてきました', 'もうすぐ慣れるでしょう'], 'C'),
                ('この映画は面白いですが、少し長すぎます.', '映画についてどう思っていますか.', ['時間も内容も很好', '時間は長いですが内容は面白い', '時間も内容も悪い', '名前は知らなかった'], 'B'),
            ],
            'N3': [
                ('環境問題を考える上で、我々の行動を見つめ直す必要があると言われている.', '筆者の考えとして最も近いものはどれですか.', ['環境問題は深刻だ', '我々の行動を改めるべきだ', '環境問題は解決できない', '行動を見つける必要がある'], 'B'),
                ('最近、若者の読書離れが深刻になっているという報道がありました.', 'この文章の主题は何ですか.', ['読書の良い点', '読書離れの現状と問題', '読書の方法', '図書館の重要性'], 'B'),
            ],
            'N2': [
                ('技術の進歩は我々の生活を便利にしたが另一方面、人間同士のコミュニケーションを減少させた可能性がある.', '技術の進歩について、筆者が最も指摘したいことは何ですか.', ['生活は便利になった', 'コミュニケーションが減った', '技術が进步した', '人間同士の距離が開いた'], 'B'),
            ],
            'N1': [
                ('現代社会において、情報リテラシーの育成は教育の重要な課題の一つとなっている.これは 단순히技術を身につけることだけでなく、情報を批判的に読み解く力を养うことを意味する.', '情報リテラシーについて、筆者の説明不符合的一项はどれですか.', ['現代社会で重要な課題である', '技术身につけることだけが目的である', '情報を批判的に読み解く力が必要である', '教育の中で育成されるべきである'], 'B'),
            ]
        }
        
        questions = []
        level_readings = readings_data.get(level, readings_data['N5'])
        
        for i in range(count):
            reading = random.choice(level_readings)
            qid = self.generate_question_id()
            tags = json.dumps([f'日语', f'{level}', '阅读理解', '选择题'], ensure_ascii=False)
            
            options_list = [
                {'A': reading[2][0]},
                {'B': reading[2][1]},
                {'C': reading[2][2]},
                {'D': reading[2][3]}
            ]
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'阅读下文并回答问题:\n\n{reading[0]}\n\n问题:{reading[1]}',
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': reading[3],
                'difficulty': 1 if level in ['N5', 'N4'] else 2 if level == 'N3' else 3 if level == 'N2' else 4,
                'points': 2.0,
                'tags': tags,
                'explanation': '阅读理解题目需要根据文章内容选择正确答案',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_cloze_questions(self, level, count=50):
        questions = []
        
        for i in range(count):
            qid = self.generate_question_id()
            tags = json.dumps([f'日语', f'{level}', '完形填空', '选择题'], ensure_ascii=False)
            
            if level in ['N5', 'N4']:
                content = '田中さん( )大学( )行きます.'
                options_list = [
                    {'A': 'は、に'},
                    {'B': 'が、へ'},
                    {'C': 'を、に'},
                    {'D': 'で、へ'}
                ]
                answer = 'A'
                explanation = '助词"は"提示主语,"に"表示目的地'
            elif level == 'N3':
                content = 'この問題は( )難しいです.私が( )やってもできません.'
                options_list = [
                    {'A': 'とても、必死'},
                    {'B': 'とても、簡単'},
                    {'C': 'やすく、必死'},
                    {'D': 'やすく、簡単'}
                ]
                answer = 'A'
                explanation = '"とても"表示程度,"必死に"表示拼命地'
            elif level == 'N2':
                content = '環境問題は我々の( )に站在那里.个人の努力も重要だが、政府の対策も( ).'
                options_list = [
                    {'A': '生活、切っても'},
                    {'B': '命、離れない'},
                    {'C': '未来、必要がある'},
                    {'D': '社会、考えられる'}
                ]
                answer = 'B'
                explanation = '"命に站在那里"表示息息相关'
            else:
                content = '现代文明において、技術革新は社会構造のみならず、価値観そのものにも大きな( )を与えている.'
                options_list = [
                    {'A': '影響'},
                    {'B': '制限'},
                    {'C': '反発'},
                    {'D': '疑問'}
                ]
                answer = 'A'
                explanation = '"影響を与えている"表示带来影响'
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'请选择适当的词语填空:\n\n{content}',
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': answer,
                'difficulty': 1 if level in ['N5', 'N4'] else 2 if level == 'N3' else 3 if level == 'N2' else 4,
                'points': 2.0,
                'tags': tags,
                'explanation': explanation,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_translation_questions(self, level, count=50):
        translations_data = {
            'N5': [
                ('私は学生です', '我是学生'),
                ('今日、天気です', '今天是晴天'),
                ('友達と話します', '和朋友说话'),
            ],
            'N4': [
                ('日本文化に興味があります', '我对日本文化感兴趣'),
                ('毎日日本語を勉強します', '每天学习日语'),
                ('友達に本をあげます', '给朋友书'),
            ],
            'N3': [
                ('日本語が上手になったと思います', '我觉得日语变好了'),
                ('海岸沿いに歩いたことがあります', '曾经沿着海岸走过'),
                ('日本語能力試験は来年受けます', '明年参加日语能力考试'),
            ],
            'N2': [
                ('環境保護の観点から考えると、この方法は効果的だと言える', '从环境保护的角度来看,可以说这种方法很有效'),
                ('技術の进步は我々の生活を大きく改变した', '技术的进步极大地改变了我们的生活'),
                ('この映画は青少年に見てほしい作品だ', '这部电影是希望青少年观看的作品'),
            ],
            'N1': [
                ('现代において、情報リテラシーの育成は教育の重要な課題となっている', '在现代社会中,信息素养的培养已成为教育的重要课题'),
                ('経済発展と環境保護のバランスを取ることが我々の使命である', '取得经济发展和环境保护的平衡是我们的使命'),
            ]
        }
        
        questions = []
        level_trans = translations_data.get(level, translations_data['N5'])
        
        for i in range(count):
            jp_text, cn_text = random.choice(level_trans)
            qid = self.generate_question_id()
            tags = json.dumps([f'日语', f'{level}', '翻译', '选择题'], ensure_ascii=False)
            
            wrong_translations = [
                f'{cn_text}的错误表达',
                f'{cn_text}的说法有误',
                f'与原意不符',
            ]
            
            options_list = [
                {'A': cn_text},
                {'B': wrong_translations[0] if len(wrong_translations) > 0 else '其他错误翻译'},
                {'C': wrong_translations[1] if len(wrong_translations) > 1 else '另一种错误翻译'},
                {'D': wrong_translations[2] if len(wrong_translations) > 2 else '完全错误的翻译'}
            ]
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'请选择下列日语的正确中文翻译:\n\n{jp_text}',
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 1 if level in ['N5', 'N4'] else 2 if level == 'N3' else 3 if level == 'N2' else 4,
                'points': 2.0,
                'tags': tags,
                'explanation': f'"{jp_text}"的正确翻译是"{cn_text}"',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_culture_questions(self, count=50):
        cultures_data = [
            ('日本の首都はどこですか.', ['東京', '大阪', '京都', '名古屋'], 'A'),
            ('お正月に食べる伝統的な料理は何ですか.', ['おせち料理', '寿司', '天ぷら', 'ラーメン'], 'A'),
            ('花見是什么时候进行的活动?', ['春', '夏', '秋', '冬'], 'A'),
            ('茶道起源于哪个国家?', ['中国', '日本', '韓国', 'インド'], 'B'),
            ('樱花在日本文化中象征什么?', ['高贵', '纯洁/美丽', '坚强', '神秘'], 'B'),
            ('和服是日本的传统服装,通常在什么场合穿?', [' everyday', ' special occasions', '运动时', '工作时'], 'B'),
            ('富士山位于哪个县?', ['東京都', '神奈川県', '山梨県', '静岡県'], 'D'),
            ('日本三大祭典不包括哪一个?', ['祇園祭', '天神祭', '神田祭', '花見'], 'D'),
            ('日本的国花是什么?', ['桜', '菊', '梅', '藤'], 'B'),
            ('盂兰盆节是用来做什么的?', ['祭祀祖先', '庆祝丰收', '驱除疾病', '欢迎新年'], 'A'),
        ]
        
        questions = []
        for i in range(count):
            q = random.choice(cultures_data)
            qid = self.generate_question_id()
            tags = json.dumps(['日语', '日本文化', '文化常识', '选择题'], ensure_ascii=False)
            
            options_list = [
                {'A': q[1][0]},
                {'B': q[1][1]},
                {'C': q[1][2]},
                {'D': q[1][3]}
            ]
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': q[0],
                'options': json.dumps(options_list, ensure_ascii=False),
                'correct_answer': q[2],
                'difficulty': 2,
                'points': 1.5,
                'tags': tags,
                'explanation': '这是关于日本文化的基础知识题',
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
        print(f"成功插入 {len(questions)} 道题目")
    
    def expand_japanese_question_bank(self, target_count=10000):
        print(f"开始扩充日语题库,目标数量: {target_count}")
        
        current_count = 0
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM questions WHERE tags LIKE '%日语%'")
        current_count = cursor.fetchone()[0]
        print(f"当前日语题库数量: {current_count}")
        
        if current_count >= target_count:
            print(f"题库已有 {current_count} 道题目,已达到目标")
            return
        
        need_to_add = target_count - current_count
        print(f"需要添加 {need_to_add} 道题目")
        
        all_questions = []
        levels = ['N5', 'N4', 'N3', 'N2', 'N1']
        
        per_level_config = {
            'N5': {'vocab': 500, 'grammar': 500, 'reading': 300, 'cloze': 200, 'translation': 300},
            'N4': {'vocab': 500, 'grammar': 500, 'reading': 300, 'cloze': 200, 'translation': 300},
            'N3': {'vocab': 400, 'grammar': 400, 'reading': 200, 'cloze': 150, 'translation': 200},
            'N2': {'vocab': 300, 'grammar': 300, 'reading': 150, 'cloze': 100, 'translation': 150},
            'N1': {'vocab': 200, 'grammar': 200, 'reading': 100, 'cloze': 50, 'translation': 100},
        }
        
        print("开始生成各类型题目...")
        
        for level in levels:
            print(f"\n生成 {level} 级别题目...")
            config = per_level_config[level]
            
            all_questions.extend(self.generate_vocabulary_questions(level, config['vocab']))
            all_questions.extend(self.generate_grammar_questions(level, config['grammar']))
            all_questions.extend(self.generate_reading_questions(level, config['reading']))
            all_questions.extend(self.generate_cloze_questions(level, config['cloze']))
            all_questions.extend(self.generate_translation_questions(level, config['translation']))
        
        all_questions.extend(self.generate_culture_questions(200))
        
        print(f"\n总计生成 {len(all_questions)} 道题目")
        
        batch_size = 500
        for i in range(0, len(all_questions), batch_size):
            batch = all_questions[i:i+batch_size]
            self.insert_questions(batch)
            print(f"进度: {min(i+batch_size, len(all_questions))}/{len(all_questions)}")
        
        print(f"\n日语题库扩充完成!")
        cursor.execute("SELECT COUNT(*) FROM questions WHERE tags LIKE '%日语%'")
        final_count = cursor.fetchone()[0]
        print(f"最终题库数量: {final_count}")
        
        cursor.execute("""
            SELECT 
                SUBSTR(tags, INSTR(tags, '"') + 1, 1) as level,
                COUNT(*) as count 
            FROM questions 
            WHERE tags LIKE '%日语%' 
            GROUP BY level
        """)
        print("\n各级别题目分布:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} 道")

def main():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
    print(f"数据库路径: {db_path}")
    
    expander = JapaneseQuestionBankExpander(db_path)
    expander.connect()
    expander.init_question_table()
    
    expander.expand_japanese_question_bank(10000)
    
    expander.close()
    print("\n题库扩充任务完成!")

if __name__ == '__main__':
    main()
