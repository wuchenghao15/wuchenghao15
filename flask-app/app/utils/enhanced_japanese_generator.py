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

class EnhancedJapaneseQuestionGenerator:
    """增强版日语题目生成器"""
    
    def __init__(self):
        self.generated_count = 0
        self.duplicate_count = 0
        
        # 扩展日语词汇库
        self.vocab_lists = {
            '日常物品': [
                ('テーブル', 'てーぶる', 'teeburu', '桌子'),
                ('イス', 'いす', 'isu', '椅子'),
                ('本棚', 'ほんだな', 'hondana', '书架'),
                ('ランプ', 'らんぷ', 'ranpu', '台灯'),
                ('カーテン', 'かーてん', 'kaaten', '窗帘'),
                ('カーペット', 'かーぺっと', 'kaapetto', '地毯'),
                ('時計', 'とけい', 'tokei', '时钟'),
                ('鏡', 'かがみ', 'kagami', '镜子'),
                ('花瓶', 'かびん', 'kabin', '花瓶'),
                ('ベッド', 'べっど', 'beddo', '床'),
                ('クッション', 'くっしょん', 'kussyon', '靠垫'),
                ('ラグ', 'らぐ', 'ragu', '毯子'),
                ('ソファ', 'そふぁ', 'sofua', '沙发'),
                ('ダイニング', 'だいにんぐ', 'dainingu', '餐厅'),
                ('キッチン', 'きっちん', 'kicchin', '厨房'),
                ('バスルーム', 'ばするーむ', 'basuruumu', '浴室'),
                ('トイレ', 'といれ', 'toire', '厕所'),
                ('玄関', 'げんかん', 'genkan', '玄关'),
                ('窓', 'まど', 'mado', '窗户'),
                ('ドア', 'どあ', 'doa', '门'),
            ],
            '食品': [
                ('リンゴ', 'りんご', 'ringo', '苹果'),
                ('バナナ', 'ばなな', 'banana', '香蕉'),
                ('オレンジ', 'おれんじ', 'orenji', '橙子'),
                ('グレープ', 'ぐれーぷ', 'gureepu', '葡萄'),
                ('スイカ', 'すいか', 'suika', '西瓜'),
                ('メロン', 'めろん', 'meron', '哈密瓜'),
                ('パイナップル', 'ぱいなっぷる', 'painappuru', '菠萝'),
                ('ヨーグルト', 'よーぐると', 'yooguruto', '酸奶'),
                ('チーズ', 'ちーず', 'chiizu', '奶酪'),
                ('ハム', 'はむ', 'hamu', '火腿'),
                ('サラダ', 'さらだ', 'sarada', '沙拉'),
                ('スープ', 'すーぷ', 'suupu', '汤'),
                ('パン', 'ぱん', 'pan', '面包'),
                ('ケーキ', 'けーき', 'keeki', '蛋糕'),
                ('クッキー', 'くっきー', 'kukkii', '饼干'),
                ('チョコレート', 'ちょこれーと', 'chokoreeto', '巧克力'),
                ('アイスクリーム', 'あいすくりーむ', 'aisukuriimu', '冰淇淋'),
                ('コーヒー', 'こーひー', 'koohii', '咖啡'),
                ('紅茶', 'こうちゃ', 'koucha', '红茶'),
                ('ジュース', 'じゅーす', 'juusu', '果汁'),
            ],
            '动物': [
                ('犬', 'いぬ', 'inu', '狗'),
                ('猫', 'ねこ', 'neko', '猫'),
                ('鳥', 'とり', 'tori', '鸟'),
                ('魚', 'さかな', 'sakana', '鱼'),
                ('馬', 'うま', 'uma', '马'),
                ('牛', 'うし', 'ushi', '牛'),
                ('羊', 'ひつじ', 'hitsuji', '羊'),
                ('豚', 'ぶた', 'buta', '猪'),
                ('兎', 'うさぎ', 'usagi', '兔子'),
                ('熊', 'くま', 'kuma', '熊'),
                ('虎', 'とら', 'tora', '老虎'),
                ('豹', 'ひょう', 'hyou', '豹子'),
                ('象', 'ぞう', 'zou', '大象'),
                ('猿', 'さる', 'saru', '猴子'),
                ('狐', 'きつね', 'kitsune', '狐狸'),
                ('狸', 'たぬき', 'tanuki', '狸猫'),
                ('蛇', 'へび', 'hebi', '蛇'),
                ('蛙', 'かえる', 'kaeru', '青蛙'),
                ('蝶', 'ちょう', 'chou', '蝴蝶'),
                ('蜂', 'はち', 'hachi', '蜜蜂'),
            ],
            '交通工具': [
                ('自動車', 'じどうしゃ', 'jidousha', '汽车'),
                ('バス', 'ばす', 'basu', '公交车'),
                ('電車', 'でんしゃ', 'densha', '电车'),
                ('新幹線', 'しんかんせん', 'shinkansen', '新干线'),
                ('飛行機', 'ひこうき', 'hikouki', '飞机'),
                ('船', 'ふね', 'fune', '船'),
                ('タクシー', 'たくしー', 'takushii', '出租车'),
                ('自転車', 'じてんしゃ', 'jitensha', '自行车'),
                ('バイク', 'ばいく', 'baiku', '摩托车'),
                ('トラック', 'とらっく', 'torakku', '卡车'),
                ('貨物列車', 'かもつれっしゃ', 'kamotsuressha', '货运列车'),
                ('旅客機', 'りょかくき', 'ryokakuki', '客机'),
                ('ヘリコプター', 'へりこぷたー', 'herikoputaa', '直升机'),
                ('ロケット', 'ろけっと', 'roketto', '火箭'),
                ('潜水艦', 'せんすいかん', 'sensuikan', '潜水艇'),
            ],
            '职业': [
                ('教師', 'きょうし', 'kyoushi', '教师'),
                ('医師', 'いし', 'ishi', '医生'),
                ('看護師', 'かんごし', 'kangoshi', '护士'),
                ('警察', 'けいさつ', 'keisatsu', '警察'),
                ('消防士', 'しょうぼうし', 'shouboushi', '消防员'),
                ('弁護士', 'べんごし', 'bengoshi', '律师'),
                ('会計士', 'かいけいし', 'kaikeishi', '会计师'),
                ('建築家', 'けんちくか', 'kenchikuka', '建筑师'),
                ('エンジニア', 'えんじにあ', 'enjinia', '工程师'),
                ('プログラマー', 'ぷろぐらまー', 'puroguramaa', '程序员'),
                ('デザイナー', 'でざいなー', 'dezainaa', '设计师'),
                ('アーティスト', 'あーてぃすと', 'aatisuto', '艺术家'),
                ('音楽家', 'おんがくか', 'ongakuka', '音乐家'),
                ('作家', 'さっか', 'sakka', '作家'),
                ('記者', 'きしゃ', 'kisha', '记者'),
            ],
            '天气': [
                ('晴れ', 'はれ', 'hare', '晴天'),
                ('曇り', 'くもり', 'kumori', '阴天'),
                ('雨', 'あめ', 'ame', '雨'),
                ('雪', 'ゆき', 'yuki', '雪'),
                ('風', 'かぜ', 'kaze', '风'),
                ('雷', 'かみなり', 'kaminari', '雷'),
                ('霧', 'きり', 'kiri', '雾'),
                ('霜', 'しも', 'shimo', '霜'),
                ('雹', 'ひょう', 'hyou', '冰雹'),
                ('嵐', 'あらし', 'arashi', '暴风雨'),
            ],
        }
        
        # 日语动词
        self.verbs = [
            ('行く', 'いく', 'iku', '去'),
            ('来る', 'くる', 'kuru', '来'),
            ('する', 'する', 'suru', '做'),
            ('見る', 'みる', 'miru', '看'),
            ('聞く', 'きく', 'kiku', '听'),
            ('話す', 'はなす', 'hanasu', '说'),
            ('食べる', 'たべる', 'taberu', '吃'),
            ('飲む', 'のむ', 'nomu', '喝'),
            ('寝る', 'ねる', 'neru', '睡'),
            ('起きる', 'おきる', 'okiru', '起床'),
            ('歩く', 'あるく', 'aruku', '走'),
            ('走る', 'はしる', 'hashiru', '跑'),
            ('泳ぐ', 'およぐ', 'oyogu', '游泳'),
            ('飛ぶ', 'とぶ', 'tobu', '飞'),
            ('働く', 'はたらく', 'hataraku', '工作'),
            ('勉強する', 'べんきょうする', 'benkyousuru', '学习'),
            ('考える', 'かんがえる', 'kangaeru', '思考'),
            ('待つ', 'まつ', 'matsu', '等待'),
            ('探す', 'さがす', 'sagasu', '寻找'),
            ('持つ', 'もつ', 'motsu', '持有'),
        ]
        
        # 日语形容词
        self.adjectives = [
            ('大きい', 'おおきい', 'ookii', '大的'),
            ('小さい', 'ちいさい', 'chiisai', '小的'),
            ('高い', 'たかい', 'takai', '高的'),
            ('低い', 'ひくい', 'hikui', '低的'),
            ('長い', 'ながい', 'nagai', '长的'),
            ('短い', 'みじかい', 'mijikai', '短的'),
            ('広い', 'ひろい', 'hiroi', '宽的'),
            ('狭い', 'せまい', 'semai', '窄的'),
            ('速い', 'はやい', 'hayai', '快的'),
            ('遅い', 'おそい', 'osoii', '慢的'),
            ('早い', 'はやい', 'hayai', '早的'),
            ('遅い', 'おそい', 'osoii', '晚的'),
            ('強い', 'つよい', 'tsuyoi', '强的'),
            ('弱い', 'よわい', 'yowai', '弱的'),
            ('重い', 'おもい', 'omoi', '重的'),
            ('軽い', 'かるい', 'karui', '轻的'),
            ('暖かい', 'あたたかい', 'atatakai', '温暖的'),
            ('寒い', 'さむい', 'samui', '寒冷的'),
            ('暑い', 'あつい', 'atsui', '热的'),
            ('涼しい', 'すずしい', 'suzushii', '凉爽的'),
        ]

    def generate_vocab_question(self):
        """生成日语词汇题目"""
        category = random.choice(list(self.vocab_lists.keys()))
        kanji, hiragana, romaji, meaning = random.choice(self.vocab_lists[category])
        
        wrong_choices = []
        while len(wrong_choices) < 3:
            cat = random.choice(list(self.vocab_lists.keys()))
            _, _, _, wrong = random.choice(self.vocab_lists[cat])
            if wrong != meaning and wrong not in wrong_choices:
                wrong_choices.append(wrong)
        
        options = [meaning] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - 単語: '{kanji} ({hiragana})' の意味は?",
            'options': options,
            'correct_answer': meaning,
            'category': '日语',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_hiragana_question(self):
        """生成日语假名题目"""
        category = random.choice(list(self.vocab_lists.keys()))
        kanji, hiragana, romaji, meaning = random.choice(self.vocab_lists[category])
        
        wrong_choices = []
        while len(wrong_choices) < 3:
            cat = random.choice(list(self.vocab_lists.keys()))
            _, wrong, _, _ = random.choice(self.vocab_lists[cat])
            if wrong != hiragana and wrong not in wrong_choices:
                wrong_choices.append(wrong)
        
        options = [hiragana] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - ひらがな: '{kanji}' のひらがなは?",
            'options': options,
            'correct_answer': hiragana,
            'category': '日语',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_verb_question(self):
        """生成日语动词题目"""
        kanji, hiragana, romaji, meaning = random.choice(self.verbs)
        
        wrong_choices = []
        while len(wrong_choices) < 3:
            _, _, _, wrong = random.choice(self.verbs)
            if wrong != meaning and wrong not in wrong_choices:
                wrong_choices.append(wrong)
        
        options = [meaning] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - 動詞: '{kanji} ({hiragana})' の意味は?",
            'options': options,
            'correct_answer': meaning,
            'category': '日语',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_adjective_question(self):
        """生成日语形容词题目"""
        kanji, hiragana, romaji, meaning = random.choice(self.adjectives)
        
        wrong_choices = []
        while len(wrong_choices) < 3:
            _, _, _, wrong = random.choice(self.adjectives)
            if wrong != meaning and wrong not in wrong_choices:
                wrong_choices.append(wrong)
        
        options = [meaning] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - 形容詞: '{kanji} ({hiragana})' の意味は?",
            'options': options,
            'correct_answer': meaning,
            'category': '日语',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_number_question(self):
        """生成日语数字题目"""
        numbers = [
            (1, 'いち', 'ichi'), (2, 'に', 'ni'), (3, 'さん', 'san'),
            (4, 'よん', 'yon'), (5, 'ご', 'go'), (6, 'ろく', 'roku'),
            (7, 'しち', 'shichi'), (8, 'はち', 'hachi'), (9, 'きゅう', 'kyuu'),
            (10, 'じゅう', 'juu'), (100, 'ひゃく', 'hyaku'), (1000, 'せん', 'sen')
        ]
        
        num, hiragana, romaji = random.choice(numbers)
        
        wrong_choices = []
        while len(wrong_choices) < 3:
            w_num, _, _ = random.choice(numbers)
            if w_num != num and w_num not in wrong_choices:
                wrong_choices.append(str(w_num))
        
        options = [str(num)] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - 数字: '{hiragana}' は何?",
            'options': options,
            'correct_answer': str(num),
            'category': '日语',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_grammar_form_question(self):
        """生成日语语法变形题目"""
        verb_info = random.choice(self.verbs)
        kanji, hiragana, romaji, meaning = verb_info
        
        forms = [
            ('ます形', self._get_masu_form(hiragana)),
            ('て形', self._get_te_form(hiragana)),
            ('た形', self._get_ta_form(hiragana)),
            ('ない形', self._get_nai_form(hiragana)),
        ]
        
        form_name, answer = random.choice(forms)
        
        wrong_choices = []
        while len(wrong_choices) < 3:
            wrong_verb = random.choice(self.verbs)[1]
            wrong_form = random.choice([self._get_masu_form, self._get_te_form, self._get_ta_form, self._get_nai_form])(wrong_verb)
            if wrong_form != answer and wrong_form not in wrong_choices:
                wrong_choices.append(wrong_form)
        
        options = [answer] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - 文法: '{kanji} ({hiragana})' の{form_name}は?",
            'options': options,
            'correct_answer': answer,
            'category': '日语',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _get_masu_form(self, hiragana):
        """获取ます形"""
        if hiragana.endswith('る'):
            return hiragana[:-1] + 'ます'
        elif hiragana == 'する':
            return 'します'
        elif hiragana == 'くる':
            return 'きます'
        else:
            return hiragana + 'ます'
    
    def _get_te_form(self, hiragana):
        """获取て形"""
        if hiragana.endswith('る'):
            return hiragana[:-1] + 'て'
        elif hiragana.endswith('す'):
            return hiragana[:-1] + 'して'
        elif hiragana == 'する':
            return 'して'
        elif hiragana == 'くる':
            return 'きて'
        else:
            return hiragana + 'て'
    
    def _get_ta_form(self, hiragana):
        """获取た形"""
        if hiragana.endswith('る'):
            return hiragana[:-1] + 'た'
        elif hiragana.endswith('す'):
            return hiragana[:-1] + 'した'
        elif hiragana == 'する':
            return 'した'
        elif hiragana == 'くる':
            return 'きた'
        else:
            return hiragana + 'た'
    
    def _get_nai_form(self, hiragana):
        """获取ない形"""
        if hiragana.endswith('る'):
            return hiragana[:-1] + 'ない'
        elif hiragana == 'する':
            return 'しない'
        elif hiragana == 'くる':
            return 'こない'
        else:
            return hiragana + 'ない'
    
    def generate_culture_question(self):
        """生成日语文化题目"""
        culture_questions = [
            {'q': '日本の通貨は何ですか?', 'options': ['円', 'ドル', 'ユーロ', 'ウォン'], 'a': '円'},
            {'q': '日本の首都はどこですか?', 'options': ['東京', '大阪', '京都', '札幌'], 'a': '東京'},
            {'q': '日本の最高峰は何ですか?', 'options': ['富士山', '北アルプス', '白山', '霧島山'], 'a': '富士山'},
            {'q': '日本の伝統的な衣装は何ですか?', 'options': ['着物', '洋服', 'コート', 'ジャケット'], 'a': '着物'},
            {'q': '寿司の主な材料は何ですか?', 'options': ['魚', '肉', '野菜', '米'], 'a': '魚'},
            {'q': '日本の伝統的な茶道を何と言いますか?', 'options': ['茶道', 'コーヒー', '紅茶', '抹茶'], 'a': '茶道'},
            {'q': '日本の三大都市は東京,大阪,何ですか?', 'options': ['名古屋', '京都', '神戸', '福岡'], 'a': '名古屋'},
            {'q': '日本の伝統的な演劇は何ですか?', 'options': ['歌舞伎', '能', '狂言', 'すべて'], 'a': 'すべて'},
            {'q': '日本の伝統的な音楽楽器は何ですか?', 'options': ['三味線', 'ピアノ', 'ギター', 'フルート'], 'a': '三味線'},
            {'q': '日本の伝統的な行事で,正月に行われるのは何ですか?', 'options': ['おせち料理', 'ハロウィン', 'バレンタイン', 'クリスマス'], 'a': 'おせち料理'},
        ]
        
        q = random.choice(culture_questions)
        options = q['options'].copy()
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - 文化: {q['q']}",
            'options': options,
            'correct_answer': q['a'],
            'category': '日语',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_translation_question(self):
        """生成中日翻译题目"""
        category = random.choice(list(self.vocab_lists.keys()))
        kanji, hiragana, romaji, meaning = random.choice(self.vocab_lists[category])
        
        wrong_choices = []
        while len(wrong_choices) < 3:
            cat = random.choice(list(self.vocab_lists.keys()))
            w_kanji, w_hiragana, _, _ = random.choice(self.vocab_lists[cat])
            wrong = f'{w_kanji} ({w_hiragana})'
            if wrong != f'{kanji} ({hiragana})' and wrong not in wrong_choices:
                wrong_choices.append(wrong)
        
        options = [f'{kanji} ({hiragana})'] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"日本語 - 翻訳: '{meaning}' の日本語は?",
            'options': options,
            'correct_answer': f'{kanji} ({hiragana})',
            'category': '日语',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _get_difficulty(self):
        """获取难度"""
        return random.choice(['入门', '基础', '提高', '拓展'])
    
    def generate_question(self):
        """生成单个题目"""
        generators = [
            self.generate_vocab_question,
            self.generate_hiragana_question,
            self.generate_verb_question,
            self.generate_adjective_question,
            self.generate_number_question,
            self.generate_grammar_form_question,
            self.generate_culture_question,
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
                    "日本語知识点解析",
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
            
            questions = self.generate_batch(current_batch)
            added = self.save_to_database(questions)
            
            elapsed = time.time() - start_time
            rate = self.generated_count / elapsed if elapsed > 0 else 0
            remaining_time = (target_count - self.generated_count) / rate if rate > 0 else 0
            
            print(f"\r📊 生成进度: {self.generated_count}/{target_count} | 新增: {added} | 重复: {self.duplicate_count} | 速度: {rate:.2f}题/秒", end='')
            
            if added == 0:
                break
        
        elapsed_total = time.time() - start_time
        print(f"\n\n🎉 生成完成!")
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
    generator = EnhancedJapaneseQuestionGenerator()
    result = generator.generate_mass_questions(target_count=50000)
    logger.info("\n📊 结果:", result)
