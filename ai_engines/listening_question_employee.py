#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
听力题库专业AI员工
专门负责日语、英语听力题目的生成、整理、更新，包括多口音多难度听力题
"""

import logging
import json
import uuid
import os
import sys
import time
import random
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.listening_service import listening_service

logger = logging.getLogger(__name__)


class ListeningQuestionEmployee:
    """听力题库专业AI员工"""

    def __init__(self, employee_id: str, name: str, level: int = 1):
        self.employee_id = employee_id
        self.name = name
        self.level = level
        self.type = "listening_question"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.performance_score = 80 + level * 2

        self.skills = [
            {"name": "japanese_listening", "level": 5 + level, "experience": 0.0},
            {"name": "english_listening", "level": 5 + level, "experience": 0.0},
            {"name": "chinese_dictation", "level": 5 + level, "experience": 0.0},
            {"name": "dialogue_creation", "level": 5 + level, "experience": 0.0},
            {"name": "accent_variation", "level": 4 + level, "experience": 0.0},
            {"name": "difficulty_control", "level": 4 + level, "experience": 0.0},
            {"name": "audio_script_generation", "level": 5 + level, "experience": 0.0},
            {"name": "comprehension_questions", "level": 4 + level, "experience": 0.0},
            {"name": "word_dictation", "level": 5 + level, "experience": 0.0},
            {"name": "idiom_dictation", "level": 4 + level, "experience": 0.0},
            {"name": "poetry_dictation", "level": 4 + level, "experience": 0.0},
            {"name": "passage_dictation", "level": 4 + level, "experience": 0.0}
        ]

        self._lock = threading.RLock()
        self._db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app.db'
        )

        self._languages = {
            "japanese": {
                "name": "日语",
                "accents": ["kanto", "kansai"],
                "accent_names": {"kanto": "关东腔", "kansai": "关西腔"},
                "voices": ["female", "male"],
                "voice_names": {"female": "女声", "male": "男声"},
                "levels": ["N5", "N4", "N3", "N2", "N1"],
                "topics": [
                    "日常生活", "学校生活", "工作职场", "购物消费",
                    "交通出行", "餐饮美食", "旅游观光", "健康医疗",
                    "天气气候", "新闻报道", "文化介绍", "科技发展"
                ]
            },
            "english": {
                "name": "英语",
                "accents": ["us", "uk", "australia", "canada", "india"],
                "accent_names": {
                    "us": "美式", "uk": "英式", "australia": "澳式",
                    "canada": "加拿大", "india": "印度"
                },
                "voices": ["female", "male"],
                "voice_names": {"female": "女声", "male": "男声"},
                "levels": ["初级", "中级", "高级", "专业级"],
                "topics": [
                    "Daily Life", "School & Education", "Work & Business",
                    "Shopping", "Transportation", "Food & Dining",
                    "Travel", "Health", "Weather", "News",
                    "Culture", "Science & Technology"
                ]
            },
            "chinese": {
                "name": "语文",
                "accents": ["mandarin"],
                "accent_names": {"mandarin": "普通话"},
                "voices": ["female", "male"],
                "voice_names": {"female": "女声", "male": "男声"},
                "levels": ["小学低年级", "小学高年级", "初中", "高中"],
                "topics": ["词语听写", "成语听写", "古诗词听写", "读文选段听写"],
                "dictation_types": ["word", "idiom", "poetry", "passage"]
            }
        }

        self._japanese_dialogues = {
            "easy": [
                {
                    "topic": "购物",
                    "transcript": "A：すみません、このりんごはいくらですか。\nB：一つ200円です。\nA：じゃ、三つください。",
                    "question": "女の人は何を買いますか。",
                    "options": ["りんご", "ばなな", "みかん", "ぶどう"],
                    "answer": 0
                },
                {
                    "topic": "天気",
                    "transcript": "A：今日はいい天気ですね。\nB：ええ、とても晴れています。\nA：明日も晴れるかな。",
                    "question": "今日の天気はどうですか。",
                    "options": ["晴れ", "雨", "曇り", "雪"],
                    "answer": 0
                }
            ],
            "medium": [
                {
                    "topic": "学校",
                    "transcript": "A：田中さん、明日の試験の準備はできましたか。\nB：まだです。数学が難しくて、なかなか勉強が進まないんです。\nA：そうですか。私も数学は苦手です。一緒に勉強しませんか。\nB：いいですね。じゃ、図書館で午後2時からどうですか。",
                    "question": "二人はどこで勉強しますか。",
                    "options": ["図書館", "教室", "田中さんの家", "カフェ"],
                    "answer": 0
                }
            ],
            "hard": [
                {
                    "topic": "社会問題",
                    "transcript": "近年、高齢化社会の進行に伴い、医療や介護の問題が深刻化しています。政府は様々な施策を講じていますが、問題の解決には時間がかかると見られています。特に、都市部と地方の格差が大きいことが課題となっています。",
                    "question": "この話の内容と合っているものはどれですか。",
                    "options": [
                        "高齢化社会の問題は深刻化している",
                        "医療問題はすでに解決した",
                        "都市部と地方の格差はない",
                        "介護の問題は存在しない"
                    ],
                    "answer": 0
                }
            ]
        }

        self._english_dialogues = {
            "easy": [
                {
                    "topic": "Greetings",
                    "transcript": "A: Good morning! How are you today?\nB: I'm fine, thank you. And you?\nA: I'm great, thanks for asking.",
                    "question": "How is person B feeling?",
                    "options": ["Fine", "Tired", "Sick", "Sad"],
                    "answer": 0
                },
                {
                    "topic": "Shopping",
                    "transcript": "A: How much is this shirt?\nB: It's $25.\nA: OK, I'll take it.",
                    "question": "What does the person want to buy?",
                    "options": ["A shirt", "A dress", "Shoes", "A hat"],
                    "answer": 0
                }
            ],
            "medium": [
                {
                    "topic": "Work",
                    "transcript": "A: Hi Sarah, did you finish the report for the meeting?\nB: Almost. I just need to add some data from last quarter.\nA: When do you think you'll be done?\nB: Probably by 3 PM. I'll send it to you as soon as it's ready.\nA: Great, thanks. The meeting is at 4, so we have time.",
                    "question": "When will Sarah finish the report?",
                    "options": ["By 3 PM", "By 4 PM", "By 5 PM", "Tomorrow"],
                    "answer": 0
                }
            ],
            "hard": [
                {
                    "topic": "Technology",
                    "transcript": "The rapid advancement of artificial intelligence has transformed various industries. From healthcare to finance, AI applications are improving efficiency and enabling new capabilities. However, this technological progress also raises important ethical questions about privacy, employment, and the future of work. Society must carefully consider how to harness these benefits while addressing potential challenges.",
                    "question": "What is the main topic of this passage?",
                    "options": [
                        "The impact of AI on society",
                        "Healthcare technology",
                        "Financial services",
                        "Employment statistics"
                    ],
                    "answer": 0
                }
            ]
        }

        self._chinese_word_bank = {
            "小学低年级": [
                {"word": "春天", "pinyin": "chūn tiān", "meaning": "四季之一，温暖的季节"},
                {"word": "花朵", "pinyin": "huā duǒ", "meaning": "花的统称"},
                {"word": "小鸟", "pinyin": "xiǎo niǎo", "meaning": "小型鸟类"},
                {"word": "蓝天", "pinyin": "lán tiān", "meaning": "蓝色的天空"},
                {"word": "白云", "pinyin": "bái yún", "meaning": "白色的云彩"},
                {"word": "太阳", "pinyin": "tài yáng", "meaning": "太阳系中心的恒星"},
                {"word": "月亮", "pinyin": "yuè liang", "meaning": "地球的卫星"},
                {"word": "星星", "pinyin": "xīng xing", "meaning": "夜晚天空中的发光天体"},
                {"word": "大树", "pinyin": "dà shù", "meaning": "高大的树木"},
                {"word": "小草", "pinyin": "xiǎo cǎo", "meaning": "细小的草本植物"},
                {"word": "河水", "pinyin": "hé shuǐ", "meaning": "河里的水"},
                {"word": "大山", "pinyin": "dà shān", "meaning": "高大的山脉"},
                {"word": "家人", "pinyin": "jiā rén", "meaning": "家庭成员"},
                {"word": "朋友", "pinyin": "péng yǒu", "meaning": "关系亲密的人"},
                {"word": "学校", "pinyin": "xué xiào", "meaning": "教育机构"},
                {"word": "老师", "pinyin": "lǎo shī", "meaning": "传授知识的人"},
                {"word": "同学", "pinyin": "tóng xué", "meaning": "同班学习的人"},
                {"word": "书本", "pinyin": "shū běn", "meaning": "书籍"},
                {"word": "铅笔", "pinyin": "qiān bǐ", "meaning": "书写工具"},
                {"word": "橡皮", "pinyin": "xiàng pí", "meaning": "擦除工具"}
            ],
            "小学高年级": [
                {"word": "美丽", "pinyin": "měi lì", "meaning": "好看，漂亮"},
                {"word": "勇敢", "pinyin": "yǒng gǎn", "meaning": "有胆量"},
                {"word": "智慧", "pinyin": "zhì huì", "meaning": "聪明才智"},
                {"word": "快乐", "pinyin": "kuài lè", "meaning": "愉快高兴"},
                {"word": "幸福", "pinyin": "xìng fú", "meaning": "生活美满"},
                {"word": "梦想", "pinyin": "mèng xiǎng", "meaning": "心中的愿望"},
                {"word": "希望", "pinyin": "xī wàng", "meaning": "心里盼着"},
                {"word": "努力", "pinyin": "nǔ lì", "meaning": "尽力去做"},
                {"word": "成功", "pinyin": "chéng gōng", "meaning": "达到目标"},
                {"word": "困难", "pinyin": "kùn nán", "meaning": "遇到的难题"},
                {"word": "挑战", "pinyin": "tiǎo zhàn", "meaning": "激励自己去做"},
                {"word": "成长", "pinyin": "chéng zhǎng", "meaning": "长大进步"},
                {"word": "学习", "pinyin": "xué xí", "meaning": "获取知识"},
                {"word": "知识", "pinyin": "zhī shi", "meaning": "学问认识"},
                {"word": "科学", "pinyin": "kē xué", "meaning": "关于自然社会的知识"},
                {"word": "技术", "pinyin": "jì shù", "meaning": "操作的技能"},
                {"word": "创造", "pinyin": "chuàng zào", "meaning": "做出新事物"},
                {"word": "创新", "pinyin": "chuàng xīn", "meaning": "革新改进"},
                {"word": "探索", "pinyin": "tàn suǒ", "meaning": "寻求发现"},
                {"word": "发现", "pinyin": "fā xiàn", "meaning": "找到新事物"}
            ],
            "初中": [
                {"word": "璀璨", "pinyin": "cuǐ càn", "meaning": "光彩夺目"},
                {"word": "憧憬", "pinyin": "chōng jǐng", "meaning": "向往期待"},
                {"word": "踌躇", "pinyin": "chóu chú", "meaning": "犹豫不决"},
                {"word": "蹒跚", "pinyin": "pán shān", "meaning": "走路缓慢摇摆"},
                {"word": "惆怅", "pinyin": "chóu chàng", "meaning": "伤感失意"},
                {"word": "睿智", "pinyin": "ruì zhì", "meaning": "聪明有远见"},
                {"word": "坚韧", "pinyin": "jiān rèn", "meaning": "坚强有韧性"},
                {"word": "执着", "pinyin": "zhí zhuó", "meaning": "坚持不放弃"},
                {"word": "谦逊", "pinyin": "qiān xùn", "meaning": "谦虚不骄傲"},
                {"word": "热忱", "pinyin": "rè chén", "meaning": "热情诚恳"},
                {"word": "浩瀚", "pinyin": "hào hàn", "meaning": "广阔无边"},
                {"word": "深邃", "pinyin": "shēn suì", "meaning": "深奥深远"},
                {"word": "细腻", "pinyin": "xì nì", "meaning": "细致入微"},
                {"word": "粗犷", "pinyin": "cū guǎng", "meaning": "豪放粗野"},
                {"word": "朦胧", "pinyin": "méng lóng", "meaning": "模糊不清"},
                {"word": "皎洁", "pinyin": "jiǎo jié", "meaning": "明亮洁白"},
                {"word": "凛冽", "pinyin": "lǐn liè", "meaning": "寒冷刺骨"},
                {"word": "和煦", "pinyin": "hé xù", "meaning": "温暖宜人"},
                {"word": "磅礴", "pinyin": "páng bó", "meaning": "气势雄伟"},
                {"word": "悠扬", "pinyin": "yōu yáng", "meaning": "声音婉转"}
            ],
            "高中": [
                {"word": "晦涩", "pinyin": "huì sè", "meaning": "难懂不流畅"},
                {"word": "隽永", "pinyin": "juàn yǒng", "meaning": "意味深长"},
                {"word": "缱绻", "pinyin": "qiǎn quǎn", "meaning": "情意缠绵"},
                {"word": "悱恻", "pinyin": "fěi cè", "meaning": "内心悲痛"},
                {"word": "寂寥", "pinyin": "jì liáo", "meaning": "寂寞空虚"},
                {"word": "氤氲", "pinyin": "yīn yūn", "meaning": "雾气弥漫"},
                {"word": "蹉跎", "pinyin": "cuō tuó", "meaning": "虚度光阴"},
                {"word": "峥嵘", "pinyin": "zhēng róng", "meaning": "不平凡"},
                {"word": "逶迤", "pinyin": "wēi yí", "meaning": "曲折绵延"},
                {"word": "磅礴", "pinyin": "páng bó", "meaning": "气势宏大"},
                {"word": "磅礴", "pinyin": "páng bó", "meaning": "气势宏大"},
                {"word": "璀璨", "pinyin": "cuǐ càn", "meaning": "光彩灿烂"},
                {"word": "深邃", "pinyin": "shēn suì", "meaning": "深奥"},
                {"word": "含蓄", "pinyin": "hán xù", "meaning": "不直接表达"},
                {"word": "委婉", "pinyin": "wěi wǎn", "meaning": "曲折婉转"},
                {"word": "炽热", "pinyin": "chì rè", "meaning": "极热"},
                {"word": "凛冽", "pinyin": "lǐn liè", "meaning": "寒冷"},
                {"word": "朦胧", "pinyin": "méng lóng", "meaning": "模糊"},
                {"word": "晦涩", "pinyin": "huì sè", "meaning": "难懂"},
                {"word": "隽永", "pinyin": "juàn yǒng", "meaning": "意味深长"}
            ]
        }

        self._chinese_idiom_bank = {
            "小学低年级": [
                {"idiom": "一心一意", "pinyin": "yī xīn yī yì", "meaning": "专心致志"},
                {"idiom": "三心二意", "pinyin": "sān xīn èr yì", "meaning": "犹豫不决"},
                {"idiom": "五颜六色", "pinyin": "wǔ yán liù sè", "meaning": "色彩丰富"},
                {"idiom": "七上八下", "pinyin": "qī shàng bā xià", "meaning": "心神不定"},
                {"idiom": "九牛一毛", "pinyin": "jiǔ niú yī máo", "meaning": "微不足道"},
                {"idiom": "十全十美", "pinyin": "shí quán shí měi", "meaning": "完美无缺"},
                {"idiom": "百发百中", "pinyin": "bǎi fā bǎi zhòng", "meaning": "技艺高超"},
                {"idiom": "千军万马", "pinyin": "qiān jūn wàn mǎ", "meaning": "声势浩大"},
                {"idiom": "千山万水", "pinyin": "qiān shān wàn shuǐ", "meaning": "路途遥远"},
                {"idiom": "万紫千红", "pinyin": "wàn zǐ qiān hóng", "meaning": "百花齐放"}
            ],
            "小学高年级": [
                {"idiom": "助人为乐", "pinyin": "zhù rén wéi lè", "meaning": "帮助别人感到快乐"},
                {"idiom": "勤学苦练", "pinyin": "qín xué kǔ liàn", "meaning": "努力学习刻苦练习"},
                {"idiom": "取长补短", "pinyin": "qǔ cháng bǔ duǎn", "meaning": "吸取长处弥补短处"},
                {"idiom": "实事求是", "pinyin": "shí shì qiú shì", "meaning": "从实际出发"},
                {"idiom": "团结友爱", "pinyin": "tuán jié yǒu ài", "meaning": "互相帮助互相关心"},
                {"idiom": "自强不息", "pinyin": "zì qiáng bù xī", "meaning": "努力向上不懈怠"},
                {"idiom": "持之以恒", "pinyin": "chí zhī yǐ héng", "meaning": "坚持不懈"},
                {"idiom": "精益求精", "pinyin": "jīng yì qiú jīng", "meaning": "追求更好"},
                {"idiom": "诚实守信", "pinyin": "chéng shí shǒu xìn", "meaning": "真诚守信用"},
                {"idiom": "尊老爱幼", "pinyin": "zūn lǎo ài yòu", "meaning": "尊敬老人爱护小孩"},
                {"idiom": "画蛇添足", "pinyin": "huà shé tiān zú", "meaning": "做多余的事"},
                {"idiom": "守株待兔", "pinyin": "shǒu zhū dài tù", "meaning": "抱着侥幸心理"},
                {"idiom": "井底之蛙", "pinyin": "jǐng dǐ zhī wā", "meaning": "见识狭隘"},
                {"idiom": "狐假虎威", "pinyin": "hú jiǎ hǔ wēi", "meaning": "仗势欺人"},
                {"idiom": "掩耳盗铃", "pinyin": "yǎn ěr dào líng", "meaning": "自欺欺人"}
            ],
            "初中": [
                {"idiom": "孜孜不倦", "pinyin": "zī zī bù juàn", "meaning": "勤奋学习不知疲倦"},
                {"idiom": "锲而不舍", "pinyin": "qiè ér bù shě", "meaning": "坚持不懈"},
                {"idiom": "精益求精", "pinyin": "jīng yì qiú jīng", "meaning": "追求完美"},
                {"idiom": "发愤图强", "pinyin": "fā fèn tú qiáng", "meaning": "努力奋斗"},
                {"idiom": "废寝忘食", "pinyin": "fèi qǐn wàng shí", "meaning": "专心致志"},
                {"idiom": "卧薪尝胆", "pinyin": "wò xīn cháng dǎn", "meaning": "刻苦自励"},
                {"idiom": "破釜沉舟", "pinyin": "pò fǔ chén zhōu", "meaning": "下定决心"},
                {"idiom": "乘风破浪", "pinyin": "chéng fēng pò làng", "meaning": "克服困难"},
                {"idiom": "高瞻远瞩", "pinyin": "gāo zhān yuǎn zhǔ", "meaning": "眼光远大"},
                {"idiom": "远见卓识", "pinyin": "yuǎn jiàn zhuó shí", "meaning": "见识高明"},
                {"idiom": "胸有成竹", "pinyin": "xiōng yǒu chéng zhú", "meaning": "心中有数"},
                {"idiom": "足智多谋", "pinyin": "zú zhì duō móu", "meaning": "智谋丰富"},
                {"idiom": "神机妙算", "pinyin": "shén jī miào suàn", "meaning": "计谋高明"},
                {"idiom": "未雨绸缪", "pinyin": "wèi yǔ chóu móu", "meaning": "提前准备"},
                {"idiom": "防患未然", "pinyin": "fáng huàn wèi rán", "meaning": "预防隐患"}
            ],
            "高中": [
                {"idiom": "博大精深", "pinyin": "bó dà jīng shēn", "meaning": "内容广博深奥"},
                {"idiom": "源远流长", "pinyin": "yuán yuǎn liú cháng", "meaning": "历史悠久"},
                {"idiom": "浩如烟海", "pinyin": "hào rú yān hǎi", "meaning": "数量极多"},
                {"idiom": "鳞次栉比", "pinyin": "lín cì zhì bǐ", "meaning": "排列密集"},
                {"idiom": "无与伦比", "pinyin": "wú yǔ lún bǐ", "meaning": "独一无二"},
                {"idiom": "举世瞩目", "pinyin": "jǔ shì zhǔ mù", "meaning": "受到关注"},
                {"idiom": "叹为观止", "pinyin": "tàn wéi guān zhǐ", "meaning": "赞美到极点"},
                {"idiom": "博大精深", "pinyin": "bó dà jīng shēn", "meaning": "内容广博深奥"},
                {"idiom": "源远流长", "pinyin": "yuán yuǎn liú cháng", "meaning": "历史悠久"},
                {"idiom": "浩如烟海", "pinyin": "hào rú yān hǎi", "meaning": "数量极多"},
                {"idiom": "鳞次栉比", "pinyin": "lín cì zhì bǐ", "meaning": "排列密集"},
                {"idiom": "无与伦比", "pinyin": "wú yǔ lún bǐ", "meaning": "独一无二"},
                {"idiom": "举世瞩目", "pinyin": "jǔ shì zhǔ mù", "meaning": "受到关注"},
                {"idiom": "叹为观止", "pinyin": "tàn wéi guān zhǐ", "meaning": "赞美到极点"},
                {"idiom": "相得益彰", "pinyin": "xiāng dé yì zhāng", "meaning": "互相配合"}
            ]
        }

        self._chinese_poetry_bank = {
            "小学低年级": [
                {"title": "咏鹅", "author": "骆宾王", "dynasty": "唐", "content": "鹅鹅鹅，曲项向天歌。白毛浮绿水，红掌拨清波。"},
                {"title": "春晓", "author": "孟浩然", "dynasty": "唐", "content": "春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。"},
                {"title": "静夜思", "author": "李白", "dynasty": "唐", "content": "床前明月光，疑是地上霜。举头望明月，低头思故乡。"},
                {"title": "悯农", "author": "李绅", "dynasty": "唐", "content": "锄禾日当午，汗滴禾下土。谁知盘中餐，粒粒皆辛苦。"},
                {"title": "登鹳雀楼", "author": "王之涣", "dynasty": "唐", "content": "白日依山尽，黄河入海流。欲穷千里目，更上一层楼。"},
                {"title": "望庐山瀑布", "author": "李白", "dynasty": "唐", "content": "日照香炉生紫烟，遥看瀑布挂前川。飞流直下三千尺，疑是银河落九天。"},
                {"title": "江雪", "author": "柳宗元", "dynasty": "唐", "content": "千山鸟飞绝，万径人踪灭。孤舟蓑笠翁，独钓寒江雪。"},
                {"title": "绝句", "author": "杜甫", "dynasty": "唐", "content": "两个黄鹂鸣翠柳，一行白鹭上青天。窗含西岭千秋雪，门泊东吴万里船。"},
                {"title": "游子吟", "author": "孟郊", "dynasty": "唐", "content": "慈母手中线，游子身上衣。临行密密缝，意恐迟迟归。谁言寸草心，报得三春晖。"},
                {"title": "早发白帝城", "author": "李白", "dynasty": "唐", "content": "朝辞白帝彩云间，千里江陵一日还。两岸猿声啼不住，轻舟已过万重山。"}
            ],
            "小学高年级": [
                {"title": "枫桥夜泊", "author": "张继", "dynasty": "唐", "content": "月落乌啼霜满天，江枫渔火对愁眠。姑苏城外寒山寺，夜半钟声到客船。"},
                {"title": "出塞", "author": "王昌龄", "dynasty": "唐", "content": "秦时明月汉时关，万里长征人未还。但使龙城飞将在，不教胡马度阴山。"},
                {"title": "望天门山", "author": "李白", "dynasty": "唐", "content": "天门中断楚江开，碧水东流至此回。两岸青山相对出，孤帆一片日边来。"},
                {"title": "送元二使安西", "author": "王维", "dynasty": "唐", "content": "渭城朝雨浥轻尘，客舍青青柳色新。劝君更尽一杯酒，西出阳关无故人。"},
                {"title": "凉州词", "author": "王翰", "dynasty": "唐", "content": "葡萄美酒夜光杯，欲饮琵琶马上催。醉卧沙场君莫笑，古来征战几人回。"},
                {"title": "别董大", "author": "高适", "dynasty": "唐", "content": "千里黄云白日曛，北风吹雁雪纷纷。莫愁前路无知己，天下谁人不识君。"},
                {"title": "题西林壁", "author": "苏轼", "dynasty": "宋", "content": "横看成岭侧成峰，远近高低各不同。不识庐山真面目，只缘身在此山中。"},
                {"title": "游山西村", "author": "陆游", "dynasty": "宋", "content": "莫笑农家腊酒浑，丰年留客足鸡豚。山重水复疑无路，柳暗花明又一村。"},
                {"title": "示儿", "author": "陆游", "dynasty": "宋", "content": "死去元知万事空，但悲不见九州同。王师北定中原日，家祭无忘告乃翁。"},
                {"title": "己亥杂诗", "author": "龚自珍", "dynasty": "清", "content": "九州生气恃风雷，万马齐喑究可哀。我劝天公重抖擞，不拘一格降人才。"}
            ],
            "初中": [
                {"title": "关雎", "author": "诗经", "dynasty": "周", "content": "关关雎鸠，在河之洲。窈窕淑女，君子好逑。参差荇菜，左右流之。窈窕淑女，寤寐求之。"},
                {"title": "蒹葭", "author": "诗经", "dynasty": "周", "content": "蒹葭苍苍，白露为霜。所谓伊人，在水一方。溯洄从之，道阻且长。溯游从之，宛在水中央。"},
                {"title": "观沧海", "author": "曹操", "dynasty": "汉", "content": "东临碣石，以观沧海。水何澹澹，山岛竦峙。树木丛生，百草丰茂。秋风萧瑟，洪波涌起。"},
                {"title": "次北固山下", "author": "王湾", "dynasty": "唐", "content": "客路青山外，行舟绿水前。潮平两岸阔，风正一帆悬。海日生残夜，江春入旧年。"},
                {"title": "泊秦淮", "author": "杜牧", "dynasty": "唐", "content": "烟笼寒水月笼沙，夜泊秦淮近酒家。商女不知亡国恨，隔江犹唱后庭花。"},
                {"title": "夜雨寄北", "author": "李商隐", "dynasty": "唐", "content": "君问归期未有期，巴山夜雨涨秋池。何当共剪西窗烛，却话巴山夜雨时。"},
                {"title": "相见欢", "author": "李煜", "dynasty": "五代", "content": "无言独上西楼，月如钩。寂寞梧桐深院锁清秋。剪不断，理还乱，是离愁。别是一般滋味在心头。"},
                {"title": "浣溪沙", "author": "晏殊", "dynasty": "宋", "content": "一曲新词酒一杯，去年天气旧亭台。夕阳西下几时回？无可奈何花落去，似曾相识燕归来。"},
                {"title": "水调歌头", "author": "苏轼", "dynasty": "宋", "content": "明月几时有？把酒问青天。不知天上宫阙，今夕是何年。我欲乘风归去，又恐琼楼玉宇，高处不胜寒。"},
                {"title": "破阵子", "author": "辛弃疾", "dynasty": "宋", "content": "醉里挑灯看剑，梦回吹角连营。八百里分麾下炙，五十弦翻塞外声，沙场秋点兵。"}
            ],
            "高中": [
                {"title": "离骚", "author": "屈原", "dynasty": "战国", "content": "帝高阳之苗裔兮，朕皇考曰伯庸。摄提贞于孟陬兮，惟庚寅吾以降。皇览揆余初度兮，肇锡余以嘉名。"},
                {"title": "蜀道难", "author": "李白", "dynasty": "唐", "content": "噫吁嚱，危乎高哉！蜀道之难，难于上青天！蚕丛及鱼凫，开国何茫然！尔来四万八千岁，不与秦塞通人烟。"},
                {"title": "登高", "author": "杜甫", "dynasty": "唐", "content": "风急天高猿啸哀，渚清沙白鸟飞回。无边落木萧萧下，不尽长江滚滚来。万里悲秋常作客，百年多病独登台。"},
                {"title": "琵琶行", "author": "白居易", "dynasty": "唐", "content": "浔阳江头夜送客，枫叶荻花秋瑟瑟。主人下马客在船，举酒欲饮无管弦。醉不成欢惨将别，别时茫茫江浸月。"},
                {"title": "锦瑟", "author": "李商隐", "dynasty": "唐", "content": "锦瑟无端五十弦，一弦一柱思华年。庄生晓梦迷蝴蝶，望帝春心托杜鹃。沧海月明珠有泪，蓝田日暖玉生烟。"},
                {"title": "念奴娇·赤壁怀古", "author": "苏轼", "dynasty": "宋", "content": "大江东去，浪淘尽，千古风流人物。故垒西边，人道是，三国周郎赤壁。乱石穿空，惊涛拍岸，卷起千堆雪。"},
                {"title": "永遇乐·京口北固亭怀古", "author": "辛弃疾", "dynasty": "宋", "content": "千古江山，英雄无觅孙仲谋处。舞榭歌台，风流总被雨打风吹去。斜阳草树，寻常巷陌，人道寄奴曾住。"},
                {"title": "声声慢", "author": "李清照", "dynasty": "宋", "content": "寻寻觅觅，冷冷清清，凄凄惨惨戚戚。乍暖还寒时候，最难将息。三杯两盏淡酒，怎敌他晚来风急！"},
                {"title": "虞美人", "author": "李煜", "dynasty": "五代", "content": "春花秋月何时了？往事知多少。小楼昨夜又东风，故国不堪回首月明中。雕栏玉砌应犹在，只是朱颜改。"},
                {"title": "雨霖铃", "author": "柳永", "dynasty": "宋", "content": "寒蝉凄切，对长亭晚，骤雨初歇。都门帐饮无绪，留恋处，兰舟催发。执手相看泪眼，竟无语凝噎。"}
            ]
        }

        self._chinese_passage_bank = {
            "小学低年级": [
                {
                    "title": "春天来了",
                    "content": "春天来了，小草绿了，花儿开了。小鸟在树上唱歌，蝴蝶在花丛中跳舞。小朋友们脱下厚厚的棉袄，在公园里快乐地玩耍。春天真是一个美丽的季节！",
                    "keywords": ["春天", "小草", "花儿", "小鸟", "蝴蝶"]
                },
                {
                    "title": "我的家人",
                    "content": "我有一个幸福的家。爸爸是一名工程师，妈妈是一名老师，我是一名小学生。每天早上，妈妈给我做早餐，爸爸送我上学。晚上，我们一家人一起吃饭，一起看电视。我爱我的家人！",
                    "keywords": ["爸爸", "妈妈", "工程师", "老师", "小学生"]
                },
                {
                    "title": "可爱的小猫",
                    "content": "我家有一只可爱的小猫。它的毛是白色的，眼睛像两颗蓝宝石。小猫喜欢吃鱼，喜欢在阳光下睡觉。它会捉老鼠，还会发出喵喵的声音。我非常喜欢这只小猫！",
                    "keywords": ["小猫", "白色", "眼睛", "鱼", "老鼠"]
                }
            ],
            "小学高年级": [
                {
                    "title": "我爱读书",
                    "content": "书是知识的海洋，书是智慧的源泉。我爱读书，因为读书可以让我学到很多知识，认识很多朋友。在书中，我可以和孙悟空一起大闹天宫，可以和林黛玉一起赏花，可以和福尔摩斯一起破案。读书让我的生活变得丰富多彩！",
                    "keywords": ["书", "知识", "智慧", "孙悟空", "林黛玉", "福尔摩斯"]
                },
                {
                    "title": "秋天的景色",
                    "content": "秋天来了，天空变得格外高远。树叶变黄了，一片片从树上飘落下来，像一只只蝴蝶在空中飞舞。田野里，稻穗金黄，高粱火红，棉花雪白。农民伯伯们忙着收割，脸上洋溢着丰收的喜悦。秋天真是一个丰收的季节！",
                    "keywords": ["秋天", "树叶", "稻穗", "高粱", "棉花", "农民"]
                },
                {
                    "title": "一次难忘的旅行",
                    "content": "去年暑假，我和爸爸妈妈一起去了黄山。黄山的景色真美啊！奇松、怪石、云海、温泉，被称为黄山四绝。我们爬了天都峰，看了迎客松，还在光明顶看了日出。这次旅行让我感受到了大自然的神奇和伟大。",
                    "keywords": ["黄山", "奇松", "怪石", "云海", "温泉", "天都峰"]
                }
            ],
            "初中": [
                {
                    "title": "生命的意义",
                    "content": "生命是宝贵的，每个人只有一次。生命的意义不在于长短，而在于奉献。雷锋叔叔虽然只活了二十二年，但他用有限的生命创造了无限的价值。他助人为乐，无私奉献，成为了我们学习的榜样。我们要珍惜生命，让生命绽放出绚丽的光彩！",
                    "keywords": ["生命", "奉献", "雷锋", "助人为乐", "榜样"]
                },
                {
                    "title": "大自然的启示",
                    "content": "大自然是人类的老师。从蝙蝠身上，科学家发明了雷达；从鱼身上，科学家发明了潜水艇；从鸟身上，科学家发明了飞机。大自然给我们带来了无穷的智慧和灵感，我们要爱护自然，保护自然，与自然和谐共处。",
                    "keywords": ["大自然", "蝙蝠", "雷达", "鱼", "潜水艇", "鸟", "飞机"]
                },
                {
                    "title": "诚信是金",
                    "content": "诚信是做人的根本，诚信是立业的基石。一个人如果失去了诚信，就失去了他人的信任；一个企业如果失去了诚信，就失去了市场；一个国家如果失去了诚信，就失去了国际地位。让我们都做一个诚实守信的人，让诚信之花在心中绽放！",
                    "keywords": ["诚信", "信任", "企业", "市场", "国家"]
                }
            ],
            "高中": [
                {
                    "title": "追求梦想",
                    "content": "梦想是人生的灯塔，指引我们前进的方向。每个人都有自己的梦想，有的想成为科学家，有的想成为艺术家，有的想成为医生。实现梦想的道路并不平坦，会遇到很多困难和挫折。但只要我们坚持不懈，努力奋斗，就一定能够实现自己的梦想。让我们一起追逐梦想，创造美好的未来！",
                    "keywords": ["梦想", "灯塔", "科学家", "艺术家", "医生", "坚持"]
                },
                {
                    "title": "科技改变生活",
                    "content": "科技的发展日新月异，深刻地改变着我们的生活。互联网让世界变得更小，智能手机让沟通变得更便捷，人工智能让生活变得更智能。科技给我们带来了很多便利，但也带来了一些问题，比如隐私泄露、网络安全等。我们要正确看待科技，让科技更好地服务于人类。",
                    "keywords": ["科技", "互联网", "智能手机", "人工智能", "隐私", "安全"]
                },
                {
                    "title": "文化传承",
                    "content": "中华文化博大精深，源远流长。从古老的诗词歌赋，到精美的传统工艺；从庄严的传统节日，到独特的风俗习惯，都是中华文化的瑰宝。我们要传承和弘扬中华文化，让中华文化走向世界，让世界了解中国。文化传承是我们每个人的责任和使命。",
                    "keywords": ["中华文化", "诗词歌赋", "传统工艺", "传统节日", "传承", "弘扬"]
                }
            ]
        }

        logger.info(f"[听力题库员工] 创建: {self.name} ({self.employee_id}) 级别: {self.level}")

    def start(self):
        """启动员工"""
        self.status = "active"
        logger.info(f"[听力题库员工] {self.name} 已启动")

    def get_status(self) -> Dict[str, Any]:
        """获取员工状态"""
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "status": self.status,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / max(self.task_count, 1) * 100,
            "performance_score": self.performance_score,
            "skills": self.skills,
            "supported_languages": list(self._languages.keys())
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        self.task_count += 1
        start_time = time.time()

        try:
            task_type = task_data.get("task_type", "generate_listening")

            if task_type == "generate_listening":
                result = self._generate_listening_questions(task_data)
            elif task_type == "generate_japanese":
                result = self._generate_japanese_listening(task_data)
            elif task_type == "generate_english":
                result = self._generate_english_listening(task_data)
            elif task_type == "generate_chinese":
                result = self._generate_chinese_dictation(task_data)
            elif task_type == "generate_word_dictation":
                result = self._generate_word_dictation(task_data)
            elif task_type == "generate_idiom_dictation":
                result = self._generate_idiom_dictation(task_data)
            elif task_type == "generate_poetry_dictation":
                result = self._generate_poetry_dictation(task_data)
            elif task_type == "generate_passage_dictation":
                result = self._generate_passage_dictation(task_data)
            elif task_type == "generate_by_difficulty":
                result = self._generate_by_difficulty(task_data)
            elif task_type == "generate_by_topic":
                result = self._generate_by_topic(task_data)
            elif task_type == "generate_mass":
                result = self._generate_mass_questions(task_data)
            elif task_type == "get_statistics":
                result = self._get_statistics()
            elif task_type == "get_languages":
                result = self._get_languages()
            else:
                result = {"success": False, "error": f"未知任务类型: {task_type}"}

            if result.get("success", False):
                self.success_count += 1
                self._update_performance(True, time.time() - start_time)
            else:
                self.failure_count += 1
                self._update_performance(False, time.time() - start_time)

            result["execution_time"] = time.time() - start_time
            result["employee_id"] = self.employee_id
            result["employee_name"] = self.name

            return result

        except Exception as e:
            self.failure_count += 1
            self._update_performance(False, time.time() - start_time)
            logger.error(f"[听力题库员工] 任务执行失败: {self.name}, 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "employee_id": self.employee_id,
                "employee_name": self.name
            }

    def _generate_listening_questions(self, task_data: Dict) -> Dict:
        """生成听力题目"""
        count = int(task_data.get("count", 50))
        language = task_data.get("language", "all")
        accent = task_data.get("accent", None)
        difficulty = task_data.get("difficulty", None)
        question_type = task_data.get("question_type", "dialogue")

        generated = []
        languages = ["japanese", "english"] if language == "all" else [language]

        try:
            from app.ai.question_bank_ai import get_question_bank_ai
            ai = get_question_bank_ai()

            per_language = max(1, count // len(languages))

            for lang in languages:
                for _ in range(per_language):
                    try:
                        lang_info = self._languages.get(lang, self._languages["english"])
                        ac = accent if accent and accent in lang_info["accents"] else random.choice(lang_info["accents"])
                        voice = random.choice(lang_info["voices"])
                        diff_level = random.randint(1, 4)
                        topic = random.choice(lang_info["topics"])

                        questions = ai.generate_listening_question(
                            language=lang,
                            accent=ac,
                            voice=voice,
                            difficulty=diff_level,
                            topic=self._topic_to_enum(topic, lang),
                            count=1
                        )

                        if questions:
                            generated.extend(questions)
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"[听力题库员工] AI生成听力题失败，使用本地生成: {e}")

        if len(generated) == 0:
            try:
                for i in range(count):
                    lang = random.choice(languages)
                    question = self._create_listening_question(lang)
                    if question:
                        generated.append(question)
            except Exception as e:
                logger.error(f"[听力题库员工] 本地生成听力题失败: {e}")
                return {"success": False, "error": str(e), "generated_count": 0}

        return {
            "success": True,
            "message": f"成功生成 {len(generated)} 道听力题",
            "generated_count": len(generated),
            "languages": languages,
            "questions": generated[:count]
        }

    def _create_listening_question(self, language: str) -> Optional[Dict]:
        """创建单个听力题（含自动入库与题库匹配）"""
        try:
            lang_info = self._languages.get(language, self._languages["english"])
            accent = random.choice(lang_info["accents"])
            voice = random.choice(lang_info["voices"])
            difficulty = random.choice(["easy", "medium", "hard"])
            topic = random.choice(lang_info["topics"])

            dialogues = self._japanese_dialogues if language == "japanese" else self._english_dialogues
            dialogue_list = dialogues.get(difficulty, dialogues["medium"])
            dialogue = random.choice(dialogue_list)

            special_type_map = {
                "japanese": "JapaneseListening",
                "english": "EnglishListening"
            }
            category_id_map = {
                "japanese": 21,
                "english": 22
            }
            
            question_id = f"ai_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
            
            question = {
                "id": question_id,
                "type": "single_choice",
                "category": "comprehension",
                "difficulty": difficulty,
                "content": dialogue["question"],
                "options": [{"key": chr(65 + i), "value": opt} for i, opt in enumerate(dialogue["options"])],
                "correct_answer": chr(65 + dialogue["answer"]),
                "explanation": f"听力原文：{dialogue['transcript'][:100]}...",
                "analysis": f"考点：{topic}听力理解",
                "tags": ["听力", language, accent, voice, topic, difficulty],
                "knowledge_points": ["听力理解", topic],
                "source": f"AI生成-{lang_info['name']}听力",
                "special_type": special_type_map.get(language, "EnglishListening"),
                "category_id": category_id_map.get(language, 22),
                "score": 2.0 if difficulty == "easy" else (5.0 if difficulty == "medium" else 10.0),
                "language": language,
                "accent": accent,
                "voice": voice,
                "transcript": dialogue["transcript"],
                "topic": topic,
                "source_file": f"ai://listening/{language}/{topic}/{difficulty}/{question_id}",
                "file_hash": "",
                "ai_metadata": {
                    "generator": self.name,
                    "generator_id": self.employee_id,
                    "generated_at": datetime.now().isoformat(),
                    "ai_model": "local_template",
                    "quality_score": 0.7 + random.uniform(0, 0.3),
                    "template_used": f"{language}_{difficulty}_{topic}"
                }
            }
            
            try:
                stored = listening_service.add_listening_question({
                    "id": question_id,
                    "subject": language,
                    "level": difficulty,
                    "dialogue": dialogue["transcript"],
                    "question": dialogue["question"],
                    "options": [opt["value"] for opt in question["options"]],
                    "correct_answer": question["correct_answer"],
                    "explanation": question["explanation"],
                    "audio_url": "",
                    "language": language,
                    "source_file": question["source_file"],
                    "file_hash": "",
                    "tags": question["tags"],
                    "ai_metadata": question["ai_metadata"],
                    "review_status": "pending",
                    "review_required": 1
                })
                if stored:
                    logger.info(f"[听力题库员工] 题目已自动入库并匹配: {question_id}")
                else:
                    logger.warning(f"[听力题库员工] 自动入库失败: {question_id}")
            except Exception as e:
                logger.warning(f"[听力题库员工] 自动入库异常（不影响生成）: {e}")

            return question

        except Exception as e:
            logger.error(f"[听力题库员工] 创建听力题失败: {e}")
            return None

    def _topic_to_enum(self, topic: str, language: str) -> str:
        """将主题转换为枚举值"""
        topic_map = {
            "japanese": {
                "日常生活": "daily", "学校生活": "campus", "工作职场": "business",
                "购物消费": "daily", "交通出行": "daily", "餐饮美食": "daily",
                "旅游观光": "culture", "健康医疗": "daily", "天气气候": "daily",
                "新闻报道": "news", "文化介绍": "culture", "科技发展": "science"
            },
            "english": {
                "Daily Life": "daily", "School & Education": "campus",
                "Work & Business": "business", "Shopping": "daily",
                "Transportation": "daily", "Food & Dining": "daily",
                "Travel": "culture", "Health": "daily", "Weather": "daily",
                "News": "news", "Culture": "culture", "Science & Technology": "science"
            }
        }

        lang_map = topic_map.get(language, topic_map["english"])
        return lang_map.get(topic, "daily")

    def _generate_japanese_listening(self, task_data: Dict) -> Dict:
        """生成日语听力题"""
        count = int(task_data.get("count", 50))
        task_data["language"] = "japanese"
        result = self._generate_listening_questions(task_data)
        result["message"] = f"成功生成 {result.get('generated_count', 0)} 道日语听力题"
        return result

    def _generate_english_listening(self, task_data: Dict) -> Dict:
        """生成英语听力题"""
        count = int(task_data.get("count", 50))
        task_data["language"] = "english"
        result = self._generate_listening_questions(task_data)
        result["message"] = f"成功生成 {result.get('generated_count', 0)} 道英语听力题"
        return result

    def _generate_by_difficulty(self, task_data: Dict) -> Dict:
        """按难度生成听力题"""
        count = int(task_data.get("count", 30))
        language = task_data.get("language", "all")
        difficulty = int(task_data.get("difficulty", 2))

        generated = []

        try:
            from app.ai.question_bank_ai import get_question_bank_ai
            ai = get_question_bank_ai()

            if language == "all":
                languages = ["japanese", "english"]
            else:
                languages = [language]

            per_language = max(1, count // len(languages))

            for lang in languages:
                lang_info = self._languages.get(lang, self._languages["english"])
                accent = random.choice(lang_info["accents"])
                voice = random.choice(lang_info["voices"])
                topic = random.choice(lang_info["topics"])

                questions = ai.generate_listening_question(
                    language=lang,
                    accent=accent,
                    voice=voice,
                    difficulty=difficulty,
                    topic=self._topic_to_enum(topic, lang),
                    count=per_language
                )

                if questions:
                    generated.extend(questions)

            return {
                "success": True,
                "message": f"成功生成 {len(generated)} 道难度{difficulty}的听力题",
                "generated_count": len(generated),
                "difficulty": difficulty
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_by_topic(self, task_data: Dict) -> Dict:
        """按主题生成听力题"""
        count = int(task_data.get("count", 20))
        language = task_data.get("language", "japanese")
        topic = task_data.get("topic", "daily")

        generated = []

        try:
            from app.ai.question_bank_ai import get_question_bank_ai
            ai = get_question_bank_ai()

            lang_info = self._languages.get(language, self._languages["japanese"])
            accent = random.choice(lang_info["accents"])
            voice = random.choice(lang_info["voices"])

            questions = ai.generate_listening_question(
                language=language,
                accent=accent,
                voice=voice,
                difficulty=2,
                topic=topic,
                count=count
            )

            if questions:
                generated.extend(questions)

            return {
                "success": True,
                "message": f"成功生成 {len(generated)} 道{topic}主题听力题",
                "generated_count": len(generated),
                "topic": topic
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_mass_questions(self, task_data: Dict) -> Dict:
        """批量生成海量听力题"""
        count = int(task_data.get("count", 200))
        languages = task_data.get("languages", ["japanese", "english"])
        accents = task_data.get("accents", ["kanto", "us"])
        voices = task_data.get("voices", ["female", "male"])
        difficulties = task_data.get("difficulties", [1, 2, 3])
        topics = task_data.get("topics", ["daily", "business", "campus"])

        generated = []

        try:
            from app.ai.question_bank_ai import get_question_bank_ai
            ai = get_question_bank_ai()

            per_lang = max(1, count // len(languages))

            for lang in languages:
                for i in range(per_lang):
                    try:
                        accent = random.choice(accents)
                        voice = random.choice(voices)
                        difficulty = random.choice(difficulties)
                        topic = random.choice(topics)

                        questions = ai.generate_listening_question(
                            language=lang,
                            accent=accent,
                            voice=voice,
                            difficulty=difficulty,
                            topic=topic,
                            count=1
                        )

                        if questions:
                            generated.extend(questions)
                    except Exception:
                        continue

            return {
                "success": True,
                "message": f"批量生成完成，共 {len(generated)} 道听力题",
                "generated_count": len(generated),
                "config": {
                    "languages": languages,
                    "accents": accents,
                    "voices": voices,
                    "difficulties": difficulties,
                    "topics": topics
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_statistics(self) -> Dict:
        """获取统计信息"""
        try:
            from app.ai.question_bank_ai import get_question_bank_ai
            ai = get_question_bank_ai()
            stats = ai.get_statistics()

            return {
                "success": True,
                "statistics": {
                    "total_questions": stats.total_questions,
                    "listening_questions": stats.listening_questions,
                    "by_language": stats.by_language,
                    "by_accent": stats.by_accent,
                    "by_difficulty": stats.by_difficulty,
                    "avg_correct_rate": stats.avg_correct_rate
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_languages(self) -> Dict:
        """获取语言配置"""
        return {
            "success": True,
            "languages": self._languages,
            "total_languages": len(self._languages)
        }

    def _generate_chinese_dictation(self, task_data: Dict) -> Dict:
        """生成中文听写题"""
        count = int(task_data.get("count", 20))
        level = task_data.get("level", "小学低年级")
        dictation_type = task_data.get("dictation_type", "word")

        generated = []

        if dictation_type == "word":
            generated = self._generate_word_dictation({"count": count, "level": level})["questions"]
        elif dictation_type == "idiom":
            generated = self._generate_idiom_dictation({"count": count, "level": level})["questions"]
        elif dictation_type == "poetry":
            generated = self._generate_poetry_dictation({"count": count, "level": level})["questions"]
        elif dictation_type == "passage":
            generated = self._generate_passage_dictation({"count": count, "level": level})["questions"]
        else:
            for _ in range(count):
                rand_type = random.choice(["word", "idiom", "poetry", "passage"])
                if rand_type == "word":
                    q = self._generate_word_dictation({"count": 1, "level": level})["questions"]
                elif rand_type == "idiom":
                    q = self._generate_idiom_dictation({"count": 1, "level": level})["questions"]
                elif rand_type == "poetry":
                    q = self._generate_poetry_dictation({"count": 1, "level": level})["questions"]
                else:
                    q = self._generate_passage_dictation({"count": 1, "level": level})["questions"]
                if q:
                    generated.extend(q)

        return {
            "success": True,
            "message": f"成功生成 {len(generated)} 道语文听写题",
            "generated_count": len(generated),
            "level": level,
            "dictation_type": dictation_type,
            "questions": generated[:count]
        }

    def _generate_word_dictation(self, task_data: Dict) -> Dict:
        """生成词语听写题"""
        count = int(task_data.get("count", 10))
        level = task_data.get("level", "小学低年级")

        word_bank = self._chinese_word_bank.get(level, self._chinese_word_bank["小学低年级"])
        generated = []

        for _ in range(min(count, len(word_bank))):
            word_item = random.choice(word_bank)
            
            question = {
                "type": "dictation",
                "category": "chinese_dictation",
                "sub_category": "word",
                "difficulty": level,
                "content": f"请听词语并写出：{word_item['pinyin']}",
                "correct_answer": word_item["word"],
                "explanation": f"词语：{word_item['word']}\n拼音：{word_item['pinyin']}\n释义：{word_item['meaning']}",
                "analysis": f"考察词语听写能力，难度：{level}",
                "tags": ["语文", "听写", "词语", level],
                "knowledge_points": ["词语听写", level],
                "source": f"AI生成-{level}词语听写",
                "special_type": "ChineseWordDictation",
                "category_id": 23,
                "score": 2.0 if level in ["小学低年级"] else (3.0 if level in ["小学高年级"] else (5.0 if level in ["初中"] else 8.0)),
                "language": "chinese",
                "accent": "mandarin",
                "voice": "female",
                "dictation_text": word_item["word"],
                "pinyin": word_item["pinyin"],
                "meaning": word_item["meaning"],
                "level": level
            }
            generated.append(question)

        return {
            "success": True,
            "message": f"成功生成 {len(generated)} 道词语听写题",
            "generated_count": len(generated),
            "level": level,
            "questions": generated
        }

    def _generate_idiom_dictation(self, task_data: Dict) -> Dict:
        """生成成语听写题"""
        count = int(task_data.get("count", 10))
        level = task_data.get("level", "小学低年级")

        idiom_bank = self._chinese_idiom_bank.get(level, self._chinese_idiom_bank["小学低年级"])
        generated = []

        for _ in range(min(count, len(idiom_bank))):
            idiom_item = random.choice(idiom_bank)
            
            question = {
                "type": "dictation",
                "category": "chinese_dictation",
                "sub_category": "idiom",
                "difficulty": level,
                "content": f"请听成语并写出：{idiom_item['pinyin']}",
                "correct_answer": idiom_item["idiom"],
                "explanation": f"成语：{idiom_item['idiom']}\n拼音：{idiom_item['pinyin']}\n释义：{idiom_item['meaning']}",
                "analysis": f"考察成语听写能力，难度：{level}",
                "tags": ["语文", "听写", "成语", level],
                "knowledge_points": ["成语听写", level],
                "source": f"AI生成-{level}成语听写",
                "special_type": "ChineseIdiomDictation",
                "category_id": 24,
                "score": 3.0 if level in ["小学低年级"] else (5.0 if level in ["小学高年级"] else (8.0 if level in ["初中"] else 10.0)),
                "language": "chinese",
                "accent": "mandarin",
                "voice": "female",
                "dictation_text": idiom_item["idiom"],
                "pinyin": idiom_item["pinyin"],
                "meaning": idiom_item["meaning"],
                "level": level
            }
            generated.append(question)

        return {
            "success": True,
            "message": f"成功生成 {len(generated)} 道成语听写题",
            "generated_count": len(generated),
            "level": level,
            "questions": generated
        }

    def _generate_poetry_dictation(self, task_data: Dict) -> Dict:
        """生成古诗词听写题"""
        count = int(task_data.get("count", 5))
        level = task_data.get("level", "小学低年级")
        line_count = int(task_data.get("line_count", 2))

        poetry_bank = self._chinese_poetry_bank.get(level, self._chinese_poetry_bank["小学低年级"])
        generated = []

        for _ in range(min(count, len(poetry_bank))):
            poetry_item = random.choice(poetry_bank)
            lines = poetry_item["content"].split("。")
            lines = [line.strip() + "。" for line in lines if line.strip()]
            
            selected_lines = lines[:line_count]
            dictation_text = "。".join([l.replace("。", "") for l in selected_lines]) + "。"
            
            question = {
                "type": "dictation",
                "category": "chinese_dictation",
                "sub_category": "poetry",
                "difficulty": level,
                "content": f"请听古诗词并写出：《{poetry_item['title']}》（{poetry_item['author']}）",
                "correct_answer": dictation_text,
                "explanation": f"诗名：《{poetry_item['title']}》\n作者：{poetry_item['dynasty']}·{poetry_item['author']}\n原文：{poetry_item['content']}",
                "analysis": f"考察古诗词听写能力，难度：{level}",
                "tags": ["语文", "听写", "古诗词", level, poetry_item["title"]],
                "knowledge_points": ["古诗词听写", poetry_item["title"]],
                "source": f"AI生成-{level}古诗词听写",
                "special_type": "ChinesePoetryDictation",
                "category_id": 25,
                "score": 5.0 if level in ["小学低年级"] else (8.0 if level in ["小学高年级"] else (10.0 if level in ["初中"] else 15.0)),
                "language": "chinese",
                "accent": "mandarin",
                "voice": "female",
                "dictation_text": dictation_text,
                "title": poetry_item["title"],
                "author": poetry_item["author"],
                "dynasty": poetry_item["dynasty"],
                "full_content": poetry_item["content"],
                "level": level
            }
            generated.append(question)

        return {
            "success": True,
            "message": f"成功生成 {len(generated)} 道古诗词听写题",
            "generated_count": len(generated),
            "level": level,
            "questions": generated
        }

    def _generate_passage_dictation(self, task_data: Dict) -> Dict:
        """生成读文选段听写题"""
        count = int(task_data.get("count", 5))
        level = task_data.get("level", "小学低年级")

        passage_bank = self._chinese_passage_bank.get(level, self._chinese_passage_bank["小学低年级"])
        generated = []

        for _ in range(min(count, len(passage_bank))):
            passage_item = random.choice(passage_bank)
            
            question = {
                "type": "dictation",
                "category": "chinese_dictation",
                "sub_category": "passage",
                "difficulty": level,
                "content": f"请听文章选段并写出：《{passage_item['title']}》",
                "correct_answer": passage_item["content"],
                "explanation": f"文章标题：《{passage_item['title']}》\n内容：{passage_item['content']}",
                "analysis": f"考察文章听写能力，难度：{level}\n关键词：{', '.join(passage_item.get('keywords', []))}",
                "tags": ["语文", "听写", "读文选段", level, passage_item["title"]],
                "knowledge_points": ["读文选段听写", passage_item["title"]],
                "source": f"AI生成-{level}读文选段听写",
                "special_type": "ChinesePassageDictation",
                "category_id": 26,
                "score": 10.0 if level in ["小学低年级"] else (15.0 if level in ["小学高年级"] else (20.0 if level in ["初中"] else 25.0)),
                "language": "chinese",
                "accent": "mandarin",
                "voice": "female",
                "dictation_text": passage_item["content"],
                "title": passage_item["title"],
                "keywords": passage_item.get("keywords", []),
                "level": level
            }
            generated.append(question)

        return {
            "success": True,
            "message": f"成功生成 {len(generated)} 道读文选段听写题",
            "generated_count": len(generated),
            "level": level,
            "questions": generated
        }

    def _update_performance(self, success: bool, duration: float):
        """更新绩效"""
        if success:
            self.performance_score = min(100, self.performance_score + 0.5)
            for skill in self.skills:
                skill["experience"] += 0.1
        else:
            self.performance_score = max(60, self.performance_score - 0.3)


def create_listening_question_employee(employee_id: str = None,
                                        name: str = "听力题库AI",
                                        level: int = 5) -> ListeningQuestionEmployee:
    """创建听力题库AI员工"""
    if not employee_id:
        employee_id = f"list_{uuid.uuid4().hex[:8]}"
    return ListeningQuestionEmployee(employee_id, name, level)
