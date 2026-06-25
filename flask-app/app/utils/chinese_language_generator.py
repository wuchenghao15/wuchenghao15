import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
语文题目生成器 - 专门生成古诗完形填空,文言文翻译,古文默写题目
"""

import sqlite3
import json
import random
import time
import hashlib
import os

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

class ChineseLanguageGenerator:
    """语文题目生成器"""
    
    def __init__(self):
        self.generated_count = 0
        self.duplicate_count = 0
        self.hash_set = set()
        
        # 古诗数据库
        self.ancient_poems = [
            {
                'title': '静夜思',
                'author': '李白',
                'dynasty': '唐',
                'content': ['床前明月光', '疑是地上霜', '举头望明月', '低头思故乡'],
                'tags': ['思乡', '月亮', '五言绝句']
            },
            {
                'title': '春晓',
                'author': '孟浩然',
                'dynasty': '唐',
                'content': ['春眠不觉晓', '处处闻啼鸟', '夜来风雨声', '花落知多少'],
                'tags': ['春天', '自然', '五言绝句']
            },
            {
                'title': '登鹳雀楼',
                'author': '王之涣',
                'dynasty': '唐',
                'content': ['白日依山尽', '黄河入海流', '欲穷千里目', '更上一层楼'],
                'tags': ['登高', '哲理', '五言绝句']
            },
            {
                'title': '望庐山瀑布',
                'author': '李白',
                'dynasty': '唐',
                'content': ['日照香炉生紫烟', '遥看瀑布挂前川', '飞流直下三千尺', '疑是银河落九天'],
                'tags': ['山水', '写景', '七言绝句']
            },
            {
                'title': '绝句',
                'author': '杜甫',
                'dynasty': '唐',
                'content': ['两个黄鹂鸣翠柳', '一行白鹭上青天', '窗含西岭千秋雪', '门泊东吴万里船'],
                'tags': ['写景', '对仗', '七言绝句']
            },
            {
                'title': '江雪',
                'author': '柳宗元',
                'dynasty': '唐',
                'content': ['千山鸟飞绝', '万径人踪灭', '孤舟蓑笠翁', '独钓寒江雪'],
                'tags': ['冬天', '孤独', '五言绝句']
            },
            {
                'title': '悯农',
                'author': '李绅',
                'dynasty': '唐',
                'content': ['锄禾日当午', '汗滴禾下土', '谁知盘中餐', '粒粒皆辛苦'],
                'tags': ['农民', '劳动', '五言绝句']
            },
            {
                'title': '咏鹅',
                'author': '骆宾王',
                'dynasty': '唐',
                'content': ['鹅鹅鹅', '曲项向天歌', '白毛浮绿水', '红掌拨清波'],
                'tags': ['动物', '写景', '古诗']
            },
            {
                'title': '出塞',
                'author': '王昌龄',
                'dynasty': '唐',
                'content': ['秦时明月汉时关', '万里长征人未还', '但使龙城飞将在', '不教胡马度阴山'],
                'tags': ['边塞', '战争', '七言绝句']
            },
            {
                'title': '枫桥夜泊',
                'author': '张继',
                'dynasty': '唐',
                'content': ['月落乌啼霜满天', '江枫渔火对愁眠', '姑苏城外寒山寺', '夜半钟声到客船'],
                'tags': ['羁旅', '夜景', '七言绝句']
            },
            {
                'title': '游子吟',
                'author': '孟郊',
                'dynasty': '唐',
                'content': ['慈母手中线', '游子身上衣', '临行密密缝', '意恐迟迟归', '谁言寸草心', '报得三春晖'],
                'tags': ['母爱', '亲情', '五言古诗']
            },
            {
                'title': '望天门山',
                'author': '李白',
                'dynasty': '唐',
                'content': ['天门中断楚江开', '碧水东流至此回', '两岸青山相对出', '孤帆一片日边来'],
                'tags': ['山水', '写景', '七言绝句']
            },
        ]
        
        # 文言文段落
        self.ancient_prose = [
            {
                'title': '论语.学而',
                'content': '子曰:学而时习之,不亦说乎?有朋自远方来,不亦乐乎?人不知而不愠,不亦君子乎?',
                'translation': '孔子说:学习并且按时复习,不也是很愉快吗?有志同道合的人从远方来,不也是很快乐吗?别人不了解我,我却不生气,不也是君子吗?',
                'tags': ['论语', '学习', '修身']
            },
            {
                'title': '论语.为政',
                'content': '子曰:温故而知新,可以为师矣.',
                'translation': '孔子说:温习旧知识从而得知新的理解与体会,凭借这一点就可以成为老师了.',
                'tags': ['论语', '学习方法']
            },
            {
                'title': '论语.述而',
                'content': '子曰:三人行,必有我师焉.择其善者而从之,其不善者而改之.',
                'translation': '孔子说:几个人一起走路,其中必定有人可以做我的老师.我选择他好的方面向他学习,看到他不好的方面就对照自己改正自己的缺点.',
                'tags': ['论语', '学习态度']
            },
            {
                'title': '孟子.告子上',
                'content': '鱼,我所欲也;熊掌,亦我所欲也.二者不可得兼,舍鱼而取熊掌者也.',
                'translation': '鱼是我所想要的,熊掌也是我所想要的,如果这两种东西不能同时得到,那么我就只好放弃鱼而选取熊掌了.',
                'tags': ['孟子', '取舍', '选择']
            },
            {
                'title': '庄子.逍遥游',
                'content': '北冥有鱼,其名为鲲.鲲之大,不知其几千里也;化而为鸟,其名为鹏.',
                'translation': '北方的大海里有一条鱼,它的名字叫做鲲.鲲的体积,真不知道大到几千里;变化成为鸟,它的名字就叫鹏.',
                'tags': ['庄子', '逍遥游', '哲学']
            },
            {
                'title': '道德经.第一章',
                'content': '道可道,非常道;名可名,非常名.无名,天地之始;有名,万物之母.',
                'translation': '可以用言语表达的道,就不是永恒不变的道;可以用文字表述的名,就不是永恒不变的名.无,是天地的开端;有,是万物的根源.',
                'tags': ['道德经', '道家', '哲学']
            },
            {
                'title': '出师表',
                'content': '先帝创业未半而中道崩殂,今天下三分,益州疲弊,此诚危急存亡之秋也.',
                'translation': '先帝开创的事业还没有完成一半,就中途去世了.如今天下分为三国,我们蜀汉国力困乏,这确实是国家危急存亡的时刻啊.',
                'tags': ['诸葛亮', '出师表', '三国']
            },
            {
                'title': '桃花源记',
                'content': '晋太元中,武陵人捕鱼为业.缘溪行,忘路之远近.忽逢桃花林,夹岸数百步,中无杂树,芳草鲜美,落英缤纷.',
                'translation': '东晋太元年间,有个武陵人以捕鱼为生.他沿着溪水划船,忘记了路程的远近.忽然遇到一片桃花林,生长在溪水的两岸,长达几百步,中间没有别的树,花草鲜嫩美丽,落花纷纷的散在地上.',
                'tags': ['陶渊明', '桃花源记', '散文']
            },
        ]
        
        # 经典名句
        self.famous_quotes = [
            ('路漫漫其修远兮,吾将上下而求索.', '屈原', '离骚'),
            ('先天下之忧而忧,后天下之乐而乐.', '范仲淹', '岳阳楼记'),
            ('不以物喜,不以己悲.', '范仲淹', '岳阳楼记'),
            ('醉翁之意不在酒,在乎山水之间也.', '欧阳修', '醉翁亭记'),
            ('人生自古谁无死,留取丹心照汗青.', '文天祥', '过零丁洋'),
            ('海内存知己,天涯若比邻.', '王勃', '送杜少府之任蜀州'),
            ('落霞与孤鹜齐飞,秋水共长天一色.', '王勃', '滕王阁序'),
            ('大漠孤烟直,长河落日圆.', '王维', '使至塞上'),
            ('会当凌绝顶,一览众山小.', '杜甫', '望岳'),
            ('采菊东篱下,悠然见南山.', '陶渊明', '饮酒'),
            ('春蚕到死丝方尽,蜡炬成灰泪始干.', '李商隐', '无题'),
            ('沉舟侧畔千帆过,病树前头万木春.', '刘禹锡', '酬乐天扬州初逢席上见赠'),
        ]
    
    def generate_unique_hash(self, question_text):
        """生成唯一哈希值"""
        return hashlib.md5(question_text.encode()).hexdigest()
    
    def is_unique(self, question_text):
        """检查题目是否唯一"""
        h = self.generate_unique_hash(question_text)
        if h in self.hash_set:
            return False
        self.hash_set.add(h)
        return True
    
    def generate_poem_fill_blank(self):
        """生成古诗完形填空题"""
        poem = random.choice(self.ancient_poems)
        line_index = random.randint(0, len(poem['content']) - 1)
        blank_line = poem['content'][line_index]
        
        # 生成干扰选项
        wrong_choices = []
        while len(wrong_choices) < 3:
            other_poem = random.choice(self.ancient_poems)
            wrong_line = random.choice(other_poem['content'])
            if wrong_line != blank_line and wrong_line not in wrong_choices:
                wrong_choices.append(wrong_line)
        
        options = [blank_line] + wrong_choices
        random.shuffle(options)
        
        # 构建题目上下文
        context = []
        for i, line in enumerate(poem['content']):
            if i == line_index:
                context.append('________')
            else:
                context.append(line)
        
        question_text = f"语文 - 古诗填空: <{poem['title']}>({poem['author']}) 请填写空缺的诗句\n\n{chr(10).join(context)}\n\n空缺处应填入:"
        
        if not self.is_unique(question_text):
            return None
        
        return {
            'question_text': question_text,
            'options': options,
            'correct_answer': blank_line,
            'category': '语文',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_poem_word_fill(self):
        """生成古诗字词填空题"""
        poem = random.choice(self.ancient_poems)
        line = random.choice(poem['content'])
        
        # 选择一个字挖空
        words = list(line)
        if len(words) < 2:
            return None
        
        blank_index = random.randint(1, len(words) - 2)  # 避免首尾字
        blank_char = words[blank_index]
        
        # 生成干扰选项(同韵或同音)
        wrong_choices = []
        rhyme_chars = ['光', '霜', '乡', '望', '月', '明', '山', '水', '天', '云', '风', '雨', '花', '鸟', '春', '秋']
        while len(wrong_choices) < 3:
            wrong_char = random.choice(rhyme_chars)
            if wrong_char != blank_char and wrong_char not in wrong_choices:
                wrong_choices.append(wrong_char)
        
        options = [blank_char] + wrong_choices
        random.shuffle(options)
        
        # 构建题目
        words_copy = words.copy()
        words_copy[blank_index] = '___'
        filled_line = ''.join(words_copy)
        
        question_text = f"语文 - 古诗填字: <{poem['title']}>中 \"{filled_line}\" 空缺处应填入哪个字?"
        
        if not self.is_unique(question_text):
            return None
        
        return {
            'question_text': question_text,
            'options': options,
            'correct_answer': blank_char,
            'category': '语文',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_prose_translation(self):
        """生成文言文翻译题"""
        prose = random.choice(self.ancient_prose)
        
        # 提取句子
        sentences = prose['content'].split('.')
        sentence = random.choice([s for s in sentences if s.strip()]) + '.'
        
        # 生成干扰翻译
        wrong_translations = [
            prose['translation'][:-1] + '.',
            prose['translation'][:-1] + '吗?',
            '这句话的意思是:' + sentence
        ]
        
        options = [prose['translation']] + wrong_translations
        random.shuffle(options)
        
        question_text = f"语文 - 文言文翻译: 请选择 \"{sentence}\" 的正确翻译"
        
        if not self.is_unique(question_text):
            return None
        
        return {
            'question_text': question_text,
            'options': options,
            'correct_answer': prose['translation'],
            'category': '语文',
            'difficulty': self._get_difficulty(),
            'points': 20
        }
    
    def generate_prose_explanation(self):
        """生成文言文词语解释题"""
        prose = random.choice(self.ancient_prose)
        
        # 提取关键词
        keywords = [
            ('子曰', '孔子说'),
            ('习', '复习'),
            ('朋', '朋友'),
            ('君子', '品德高尚的人'),
            ('故', '旧知识'),
            ('新', '新理解'),
            ('师', '老师'),
            ('三人行', '几个人一起走路'),
            ('善者', '好的方面'),
            ('从', '跟随,学习'),
            ('欲', '想要'),
            ('兼', '同时'),
            ('舍', '放弃'),
            ('取', '选取'),
            ('道', '道理,规律'),
            ('名', '名称,概念'),
            ('诚', '确实'),
            ('秋', '时刻'),
        ]
        
        keyword, meaning = random.choice(keywords)
        
        # 生成干扰选项
        wrong_meanings = [k[1] for k in keywords if k[1] != meaning]
        wrong_choices = random.sample(wrong_meanings, 3)
        
        options = [meaning] + wrong_choices
        random.shuffle(options)
        
        question_text = f"语文 - 文言实词: 在文言文中,\"{keyword}\" 的含义是?"
        
        if not self.is_unique(question_text):
            return None
        
        return {
            'question_text': question_text,
            'options': options,
            'correct_answer': meaning,
            'category': '语文',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_poem_writing(self):
        """生成古诗默写题"""
        poem = random.choice(self.ancient_poems)
        
        # 选择前两句或后两句作为提示
        half_len = len(poem['content']) // 2
        if random.random() > 0.5:
            prompt_lines = poem['content'][:half_len]
            answer_lines = poem['content'][half_len:]
        else:
            prompt_lines = poem['content'][half_len:]
            answer_lines = poem['content'][:half_len]
        
        answer = ','.join(answer_lines)
        
        # 生成干扰选项
        wrong_choices = []
        while len(wrong_choices) < 3:
            other_poem = random.choice(self.ancient_poems)
            if other_poem['title'] != poem['title']:
                other_half = other_poem['content'][:half_len] if len(other_poem['content']) >= half_len else other_poem['content']
                wrong_answer = ','.join(other_half)
                if wrong_answer != answer and wrong_answer not in wrong_choices:
                    wrong_choices.append(wrong_answer)
        
        options = [answer] + wrong_choices
        random.shuffle(options)
        
        question_text = f"语文 - 古诗默写: <{poem['title']}>({poem['author']})\n\n请接出下文:\n{chr(10).join(prompt_lines)}"
        
        if not self.is_unique(question_text):
            return None
        
        return {
            'question_text': question_text,
            'options': options,
            'correct_answer': answer,
            'category': '语文',
            'difficulty': self._get_difficulty(),
            'points': 20
        }
    
    def generate_famous_quote_author(self):
        """生成名句作者选择题"""
        quote, author, source = random.choice(self.famous_quotes)
        
        # 生成干扰选项
        wrong_authors = [q[1] for q in self.famous_quotes if q[1] != author]
        wrong_choices = random.sample(wrong_authors, 3)
        
        options = [author] + wrong_choices
        random.shuffle(options)
        
        question_text = f"语文 - 名句作者: \"{quote}\" 的作者是?"
        
        if not self.is_unique(question_text):
            return None
        
        return {
            'question_text': question_text,
            'options': options,
            'correct_answer': author,
            'category': '语文',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_famous_quote_source(self):
        """生成名句出处选择题"""
        quote, author, source = random.choice(self.famous_quotes)
        
        # 生成干扰选项
        wrong_sources = [q[2] for q in self.famous_quotes if q[2] != source]
        wrong_choices = random.sample(wrong_sources, 3)
        
        options = [source] + wrong_choices
        random.shuffle(options)
        
        question_text = f"语文 - 名句出处: \"{quote}\" 出自哪部作品?"
        
        if not self.is_unique(question_text):
            return None
        
        return {
            'question_text': question_text,
            'options': options,
            'correct_answer': source,
            'category': '语文',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_poem_rhyme(self):
        """生成古诗押韵题"""
        poem = random.choice(self.ancient_poems)
        
        # 找到押韵的字
        last_chars = [line[-1] for line in poem['content']]
        rhyme_char = last_chars[0]
        
        # 生成干扰选项
        wrong_chars = ['风', '花', '雪', '月', '山', '水', '天', '云']
        wrong_choices = [c for c in wrong_chars if c != rhyme_char][:3]
        
        options = [rhyme_char] + wrong_choices
        random.shuffle(options)
        
        question_text = f"语文 - 古诗押韵: <{poem['title']}>的押韵字是?"
        
        if not self.is_unique(question_text):
            return None
        
        return {
            'question_text': question_text,
            'options': options,
            'correct_answer': rhyme_char,
            'category': '语文',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _get_difficulty(self):
        """获取难度"""
        return random.choice(['入门', '基础', '提高', '拓展'])
    
    def generate_question(self):
        """生成单个题目"""
        generators = [
            self.generate_poem_fill_blank,
            self.generate_poem_word_fill,
            self.generate_prose_translation,
            self.generate_prose_explanation,
            self.generate_poem_writing,
            self.generate_famous_quote_author,
            self.generate_famous_quote_source,
            self.generate_poem_rhyme,
        ]
        
        attempts = 0
        while attempts < 10:
            generator = random.choice(generators)
            q = generator()
            if q:
                return q
            attempts += 1
        
        return None
    
    def generate_batch(self, count=100):
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
                ''', (
                    q['question_text'],
                    'multiple_choice',
                    json.dumps(q['options']),
                    q['correct_answer'],
                    f"{q['category']}知识点解析",
                    q['difficulty'],
                    q['category'],
                    q['points']
                ))
                added += 1
            
            conn.commit()
        
        self.generated_count += added
        return added
    
    def generate_mass_questions(self, target_count=5000):
        """大规模生成题目"""
        print(f"🚀 开始生成 {target_count} 道语文题目...")
        start_time = time.time()
        
        while self.generated_count < target_count:
            remaining = target_count - self.generated_count
            current_batch = min(100, remaining)
            
            questions = self.generate_batch(current_batch)
            added = self.save_to_database(questions)
            
            elapsed = time.time() - start_time
            rate = self.generated_count / elapsed if elapsed > 0 else 0
            
            print(f"\r📊 生成进度: {self.generated_count}/{target_count} | 新增: {added} | 重复: {self.duplicate_count} | 速度: {rate:.2f}题/秒", end='')
        
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

if __name__ == "__main__":
    generator = ChineseLanguageGenerator()
    result = generator.generate_mass_questions(target_count=2000)
    logger.info("\n📊 结果:", result)
