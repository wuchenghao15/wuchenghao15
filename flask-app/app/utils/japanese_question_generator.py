import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import json
import random
import time
import os

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

class JapaneseQuestionGenerator:
    """日语题目生成器"""
    
    def __init__(self):
        self.generated_count = 0
        self.duplicate_count = 0
        
        # 日语基础词汇
        self.japanese_vocab = [
            ('猫', 'ねこ', 'neko', '猫'),
            ('犬', 'いぬ', 'inu', '狗'),
            ('本', 'ほん', 'hon', '书'),
            ('机', 'つくえ', 'tsukue', '桌子'),
            ('椅子', 'いす', 'isu', '椅子'),
            ('窓', 'まど', 'mado', '窗户'),
            ('ドア', 'どあ', 'doa', '门'),
            ('電話', 'でんわ', 'denwa', '电话'),
            ('時計', 'とけい', 'tokei', '时钟'),
            ('眼鏡', 'めがね', 'megane', '眼镜'),
            ('傘', 'かさ', 'kasa', '伞'),
            ('鞄', 'かばん', 'kaban', '包'),
            ('靴', 'くつ', 'kutsu', '鞋子'),
            ('帽子', 'ぼうし', 'boushi', '帽子'),
            ('手袋', 'てぶくろ', 'tebukuro', '手套'),
            ('ペン', 'ぺん', 'pen', '笔'),
            ('ノート', 'のーと', 'nooto', '笔记本'),
            ('鉛筆', 'えんぴつ', 'enpitsu', '铅笔'),
            ('消しゴム', 'けしごむ', 'keshigomu', '橡皮'),
            ('定規', 'じょうぎ', 'jougi', '尺子'),
            ('机', 'つくえ', 'tsukue', '书桌'),
            ('椅子', 'いす', 'isu', '椅子'),
            ('パソコン', 'ぱそこん', 'pasokon', '电脑'),
            ('テレビ', 'てれび', 'terebi', '电视'),
            ('ラジオ', 'らじお', 'rajio', '收音机'),
            ('冷蔵庫', 'れいぞうこ', 'reizouko', '冰箱'),
            ('洗濯機', 'せんたくき', 'sentakuki', '洗衣机'),
            ('エアコン', 'えあこん', 'eakon', '空调'),
            ('電子レンジ', 'でんしれんじ', 'denshirenji', '微波炉'),
            ('時計', 'とけい', 'tokei', '手表'),
            ('カメラ', 'かめら', 'kamera', '相机'),
            ('スマホ', 'すまほ', 'sumaho', '手机'),
            ('ヘッドフォン', 'へっどふぉん', 'heddofon', '耳机'),
            ('バッテリー', 'ばってりー', 'batterii', '电池'),
            ('充電器', 'じゅうでんき', 'juudenki', '充电器'),
            ('USB', 'ゆーえすびー', 'yuuesubii', 'USB'),
            ('メモリーカード', 'めもりーかーど', 'memoriikaado', '存储卡'),
            ('キーボード', 'きーぼーど', 'kiiboodo', '键盘'),
            ('マウス', 'まうす', 'mausu', '鼠标'),
            ('モニター', 'もにたー', 'monitaa', '显示器'),
        ]
        
        # 日语动词
        self.japanese_verbs = [
            ('食べる', 'たべる', 'taberu', '吃'),
            ('飲む', 'のむ', 'nomu', '喝'),
            ('話す', 'はなす', 'hanasu', '说话'),
            ('聞く', 'きく', 'kiku', '听'),
            ('見る', 'みる', 'miru', '看'),
            ('行く', 'いく', 'iku', '去'),
            ('来る', 'くる', 'kuru', '来'),
            ('する', 'する', 'suru', '做'),
            ('考える', 'かんがえる', 'kangaeru', '思考'),
            ('勉強する', 'べんきょうする', 'benkyousuru', '学习'),
            ('働く', 'はたらく', 'hataraku', '工作'),
            ('休む', 'やすむ', 'yasumu', '休息'),
            ('寝る', 'ねる', 'neru', '睡觉'),
            ('起きる', 'おきる', 'okiru', '起床'),
            ('歩く', 'あるく', 'aruku', '步行'),
            ('走る', 'はしる', 'hashiru', '跑'),
            ('泳ぐ', 'およぐ', 'oyogu', '游泳'),
            ('飛ぶ', 'とぶ', 'tobu', '飞'),
            ('跳ぶ', 'とぶ', 'tobu', '跳'),
            ('泣く', 'なく', 'naku', '哭'),
            ('笑う', 'わらう', 'warau', '笑'),
            ('怒る', 'おこる', 'okoru', '生气'),
            ('喜ぶ', 'よろこぶ', 'yorokobu', '高兴'),
            ('悲しむ', 'かなしむ', 'kanashimu', '悲伤'),
            ('待つ', 'まつ', 'matsu', '等待'),
            ('探す', 'さがす', 'sagasu', '寻找'),
            ('探る', 'さぐる', 'saguru', '探寻'),
            ('持つ', 'もつ', 'motsu', '持有'),
            ('取る', 'とる', 'toru', '取'),
            ('放す', 'はなす', 'hanasu', '放开'),
        ]
        
        # 日语形容词
        self.japanese_adjectives = [
            ('美味しい', 'おいしい', 'oishii', '美味的'),
            ('辛い', 'からい', 'karai', '辣的'),
            ('甘い', 'あまい', 'amai', '甜的'),
            ('酸っぱい', 'すっぱい', 'suppai', '酸的'),
            ('塩辛い', 'しおからい', 'shiokarai', '咸的'),
            ('苦い', 'にがい', 'nigai', '苦的'),
            ('冷たい', 'つめたい', 'tsumetai', '冷的'),
            ('熱い', 'あつい', 'atsui', '热的'),
            ('温かい', 'あたたかい', 'atatakai', '温暖的'),
            ('寒い', 'さむい', 'samui', '寒冷的'),
            ('暑い', 'あつい', 'atsui', '热的'),
            ('暖かい', 'あたたかい', 'atatakai', '暖和的'),
            ('涼しい', 'すずしい', 'suzushii', '凉爽的'),
            ('硬い', 'かたい', 'katai', '硬的'),
            ('柔らかい', 'やわらかい', 'yawarakai', '柔软的'),
            ('重い', 'おもい', 'omoi', '重的'),
            ('軽い', 'かるい', 'karui', '轻的'),
            ('大きい', 'おおきい', 'ookii', '大的'),
            ('小さい', 'ちいさい', 'chiisai', '小的'),
            ('長い', 'ながい', 'nagai', '长的'),
            ('短い', 'みじかい', 'mijikai', '短的'),
            ('高い', 'たかい', 'takai', '高的'),
            ('低い', 'ひくい', 'hikui', '低的'),
            ('速い', 'はやい', 'hayai', '快的'),
            ('遅い', 'おそい', 'osoii', '慢的'),
        ]
        
        # 日语问候语
        self.japanese_greetings = [
            ('こんにちは', 'konnichiwa', '你好'),
            ('こんばんは', 'konbanwa', '晚上好'),
            ('おはようございます', 'ohayougozaimasu', '早上好'),
            ('おやすみなさい', 'oyasuminasai', '晚安'),
            ('ありがとうございます', 'arigatougozaimasu', '谢谢'),
            ('すみません', 'sumimasen', '对不起/打扰一下'),
            ('ごめんなさい', 'gomennasai', '对不起'),
            ('さようなら', 'sayounara', '再见'),
            ('また明日', 'mataashita', '明天见'),
            ('よろしくお願いします', 'yoroshikuonegaishimasu', '请多关照'),
        ]
        
        # 日语数字
        self.japanese_numbers = [
            ('一', 'いち', 'ichi', '1'),
            ('二', 'に', 'ni', '2'),
            ('三', 'さん', 'san', '3'),
            ('四', 'よん/し', 'yon/shi', '4'),
            ('五', 'ご', 'go', '5'),
            ('六', 'ろく', 'roku', '6'),
            ('七', 'しち/なな', 'shichi/nana', '7'),
            ('八', 'はち', 'hachi', '8'),
            ('九', 'きゅう/く', 'kyuu/ku', '9'),
            ('十', 'じゅう', 'juu', '10'),
            ('百', 'ひゃく', 'hyaku', '100'),
            ('千', 'せん', 'sen', '1000'),
            ('万', 'まん', 'man', '10000'),
        ]
        
        # 日语文化问题
        self.japanese_culture = [
            {'question': '日本の首都はどこですか?', 'options': ['東京', '大阪', '京都', '札幌'], 'answer': '東京'},
            {'question': '日本の貨幣単位は何ですか?', 'options': ['円', 'ドル', 'ユーロ', 'ウォン'], 'answer': '円'},
            {'question': '日本の伝統的な衣装は何ですか?', 'options': ['着物', '洋服', 'コート', 'ジャケット'], 'answer': '着物'},
            {'question': '日本の伝統的な食べ物で,魚を米にのせたものは何ですか?', 'options': ['寿司', 'ラーメン', 'うどん', '天ぷら'], 'answer': '寿司'},
            {'question': '日本の最高峰は何ですか?', 'options': ['富士山', '北アルプス', '白山', '霧島山'], 'answer': '富士山'},
            {'question': '日本の伝統的な茶道のことを何と言いますか?', 'options': ['茶道', 'コーヒー', '紅茶', '抹茶'], 'answer': '茶道'},
            {'question': '日本の伝統的な演劇は何ですか?', 'options': ['能', '歌舞伎', '狂言', 'すべて'], 'answer': 'すべて'},
            {'question': '日本の三大都市は東京,大阪,何ですか?', 'options': ['名古屋', '京都', '神戸', '福岡'], 'answer': '名古屋'},
        ]
        
        # 日语语法问题模板
        self.japanese_grammar = [
            {
                'template': '"{verb}" の否定形は何ですか?',
                'verb_data': [('食べる', '食べない'), ('行く', '行かない'), ('見る', '見ない'), ('する', 'しない')],
                'options_func': lambda ans: [ans, ans.replace('ない', 'ます'), ans.replace('ない', 'た'), ans.replace('ない', 'て')]
            },
            {
                'template': '"{verb}" の過去形は何ですか?',
                'verb_data': [('食べる', '食べた'), ('行く', '行った'), ('見る', '見た'), ('する', 'した')],
                'options_func': lambda ans: [ans, ans.replace('た', 'ない'), ans.replace('た', 'ます'), ans.replace('た', 'て')]
            },
            {
                'template': '"{adj}" の否定形は何ですか?',
                'verb_data': [('美味しい', '美味しくない'), ('高い', '高くない'), ('大きい', '大きくない'), ('速い', '速くない')],
                'options_func': lambda ans: [ans, ans.replace('くない', 'い'), ans.replace('くない', 'かった'), ans.replace('くない', 'くて')]
            },
        ]

    def generate_vocab_question(self):
        """生成日语词汇题目"""
        kanji, hiragana, romaji, meaning = random.choice(self.japanese_vocab)
        
        # 生成干扰选项
        wrong_choices = []
        while len(wrong_choices) < 3:
            _, _, _, wrong = random.choice(self.japanese_vocab)
            if wrong != meaning and wrong not in wrong_choices:
                wrong_choices.append(wrong)
        
        options = [meaning] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - 単語: '{kanji} ({hiragana})' の意味は何ですか?",
            'options': options,
            'correct_answer': meaning,
            'category': '日语',
            'difficulty': self._get_random_difficulty(),
            'points': 10
        }
    
    def generate_hiragana_question(self):
        """生成日语假名题目"""
        kanji, hiragana, romaji, meaning = random.choice(self.japanese_vocab)
        
        wrong_choices = []
        while len(wrong_choices) < 3:
            _, wrong, _, _ = random.choice(self.japanese_vocab)
            if wrong != hiragana and wrong not in wrong_choices:
                wrong_choices.append(wrong)
        
        options = [hiragana] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - ひらがな: '{kanji}' のひらがなは何ですか?",
            'options': options,
            'correct_answer': hiragana,
            'category': '日语',
            'difficulty': self._get_random_difficulty(),
            'points': 10
        }
    
    def generate_romaji_question(self):
        """生成日语罗马音题目"""
        kanji, hiragana, romaji, meaning = random.choice(self.japanese_vocab)
        
        wrong_choices = []
        while len(wrong_choices) < 3:
            _, _, wrong, _ = random.choice(self.japanese_vocab)
            if wrong != romaji and wrong not in wrong_choices:
                wrong_choices.append(wrong)
        
        options = [romaji] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - ローマ字: '{kanji} ({hiragana})' のローマ字は何ですか?",
            'options': options,
            'correct_answer': romaji,
            'category': '日语',
            'difficulty': self._get_random_difficulty(),
            'points': 10
        }
    
    def generate_verb_question(self):
        """生成日语动词题目"""
        kanji, hiragana, romaji, meaning = random.choice(self.japanese_verbs)
        
        wrong_choices = []
        while len(wrong_choices) < 3:
            _, _, _, wrong = random.choice(self.japanese_verbs)
            if wrong != meaning and wrong not in wrong_choices:
                wrong_choices.append(wrong)
        
        options = [meaning] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - 動詞: '{kanji} ({hiragana})' の意味は何ですか?",
            'options': options,
            'correct_answer': meaning,
            'category': '日语',
            'difficulty': self._get_random_difficulty(),
            'points': 10
        }
    
    def generate_adjective_question(self):
        """生成日语形容词题目"""
        kanji, hiragana, romaji, meaning = random.choice(self.japanese_adjectives)
        
        wrong_choices = []
        while len(wrong_choices) < 3:
            _, _, _, wrong = random.choice(self.japanese_adjectives)
            if wrong != meaning and wrong not in wrong_choices:
                wrong_choices.append(wrong)
        
        options = [meaning] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - 形容詞: '{kanji} ({hiragana})' の意味は何ですか?",
            'options': options,
            'correct_answer': meaning,
            'category': '日语',
            'difficulty': self._get_random_difficulty(),
            'points': 10
        }
    
    def generate_greeting_question(self):
        """生成日语问候语题目"""
        japanese, romaji, meaning = random.choice(self.japanese_greetings)
        
        wrong_choices = []
        while len(wrong_choices) < 3:
            _, _, wrong = random.choice(self.japanese_greetings)
            if wrong != meaning and wrong not in wrong_choices:
                wrong_choices.append(wrong)
        
        options = [meaning] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - 挨拶: '{japanese}' の意味は何ですか?",
            'options': options,
            'correct_answer': meaning,
            'category': '日语',
            'difficulty': self._get_random_difficulty(),
            'points': 10
        }
    
    def generate_number_question(self):
        """生成日语数字题目"""
        kanji, hiragana, romaji, number = random.choice(self.japanese_numbers)
        
        wrong_choices = []
        while len(wrong_choices) < 3:
            _, _, _, wrong = random.choice(self.japanese_numbers)
            if wrong != number and wrong not in wrong_choices:
                wrong_choices.append(wrong)
        
        options = [number] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - 数字: '{kanji} ({hiragana})' は何を意味しますか?",
            'options': options,
            'correct_answer': number,
            'category': '日语',
            'difficulty': self._get_random_difficulty(),
            'points': 10
        }
    
    def generate_culture_question(self):
        """生成日语文化题目"""
        template = random.choice(self.japanese_culture)
        
        options = template['options'].copy()
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - 文化: {template['question']}",
            'options': options,
            'correct_answer': template['answer'],
            'category': '日语',
            'difficulty': self._get_random_difficulty(),
            'points': 15
        }
    
    def generate_grammar_question(self):
        """生成日语语法题目"""
        grammar_template = random.choice(self.japanese_grammar)
        word, answer = random.choice(grammar_template['verb_data'])
        
        options = grammar_template['options_func'](answer)
        random.shuffle(options)
        
        question_text = grammar_template['template'].format(verb=word, adj=word)
        
        return {
            'question_text': f"日本語 - 文法: {question_text}",
            'options': options,
            'correct_answer': answer,
            'category': '日语',
            'difficulty': self._get_random_difficulty(),
            'points': 15
        }
    
    def generate_translation_question(self):
        """生成中日翻译题目"""
        kanji, hiragana, romaji, meaning = random.choice(self.japanese_vocab)
        
        wrong_choices = []
        while len(wrong_choices) < 3:
            _, _, _, wrong = random.choice(self.japanese_vocab)
            if wrong != meaning and wrong not in wrong_choices:
                wrong_choices.append(wrong)
        
        options = [f'{kanji} ({hiragana})'] + [f'{random.choice(self.japanese_vocab)[0]} ({random.choice(self.japanese_vocab)[1]})' for _ in range(3)]
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - 翻訳: '{meaning}' の日本語訳は何ですか?",
            'options': options,
            'correct_answer': f'{kanji} ({hiragana})',
            'category': '日语',
            'difficulty': self._get_random_difficulty(),
            'points': 10
        }
    
    def _get_random_difficulty(self):
        """获取随机难度"""
        return random.choice(['入门', '基础', '提高', '拓展'])
    
    def generate_question(self):
        """生成单个题目"""
        generators = [
            self.generate_vocab_question,
            self.generate_hiragana_question,
            self.generate_romaji_question,
            self.generate_verb_question,
            self.generate_adjective_question,
            self.generate_greeting_question,
            self.generate_number_question,
            self.generate_culture_question,
            self.generate_grammar_question,
            self.generate_translation_question,
        ]
        
        generator = random.choice(generators)
        return generator()
    
    def generate_batch(self, count=1000):
        """批量生成题目"""
        questions = []
        for _ in range(count):
            q = self.generate_question()
            if q:
                questions.append(q)
        return questions
    
    def save_to_database(self, questions):
        """保存题目到数据库"""
        if not questions:
            return 0
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            added = 0
            
            for q in questions:
                cursor.execute("SELECT id FROM questions WHERE question_text = ?", (q['question_text'],))
                if cursor.fetchone():
                    self.duplicate_count += 1
                    continue
                
                cursor.execute('''
                    INSERT INTO questions 
                    (question_text, question_type, options, correct_answer, 
                     explanation, difficulty, category, points)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                def perform_action(**kwargs):
                ''', (
                    q['question_text'],
                    'multiple_choice',
                    json.dumps(q['options']),
                    q['correct_answer'],
                    f"日本語知识点解析",
                    q['difficulty'],
                    q['category'],
                    q['points']
                ))
                added += 1
            
            conn.commit()
        
        self.generated_count += added
        return added
    
    def generate_mass_questions(self, target_count=100000, batch_size=5000):
        """大规模生成题目"""
        print(f"🚀 开始生成 {target_count} 道日语题目...")
        start_time = time.time()
        
        while self.generated_count < target_count:
            remaining = target_count - self.generated_count
            current_batch = min(batch_size, remaining)
            
            print(f"\n📝 正在生成第 {self.generated_count+1}-{min(self.generated_count+current_batch, target_count)} 道题目...")
            
            questions = self.generate_batch(current_batch)
            added = self.save_to_database(questions)
            
            elapsed = time.time() - start_time
            rate = self.generated_count / elapsed if elapsed > 0 else 0
            remaining_time = (target_count - self.generated_count) / rate if rate > 0 else 0
            
            print(f"✅ 新增: {added} 道 | 总数: {self.generated_count} | 重复: {self.duplicate_count}")
            print(f"⏱️  耗时: {elapsed:.2f}秒 | 速度: {rate:.2f}题/秒 | 预计剩余: {remaining_time:.2f}秒")
            
            if added == 0:
                print("⚠️  连续多次未添加新题目,可能已达到生成极限")
                break
            
            if self.generated_count % 50000 == 0 and self.generated_count > 0:
                print(f"\n📌 已生成 {self.generated_count} 道题目,继续中...")
        
        elapsed_total = time.time() - start_time
        print(f"\n🎉 生成完成!")
        print(f"📊 最终统计:")
        print(f"   生成题目: {self.generated_count} 道")
        print(f"   重复跳过: {self.duplicate_count} 道")
        print(f"   总耗时: {elapsed_total:.2f} 秒")
        print(f"   平均速度: {self.generated_count/elapsed_total:.2f} 题/秒")
        
        return {
            'success': True,
            'generated': self.generated_count,
            'duplicates': self.duplicate_count,
            'time_elapsed': elapsed_total
        }

if __name__ == '__main__':
    generator = JapaneseQuestionGenerator()
    result = generator.generate_mass_questions(target_count=30000)
    logger.info("\n📊 结果:", result)
