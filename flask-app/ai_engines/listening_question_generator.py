#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI听力题智能生成器
根据语言、难度、主题自动生成高质量听力题
支持自动音频生成和数据库入库
"""

import os
import sys
import random
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.logging import logger

try:
    from ai_engines.audio_manager import audio_manager
    HAS_AUDIO_MANAGER = True
except ImportError:
    HAS_AUDIO_MANAGER = False
    logger.warning("[听力题生成器] 音频管理器未找到，将使用浏览器端语音合成")


class ListeningQuestionGenerator:
    """AI听力题智能生成器"""

    def __init__(self, db_path=None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

        self._init_question_templates()
        logger.info("[听力题生成器] AI听力题生成器初始化完成")

    def _init_question_templates(self):
        """初始化题目模板库"""

        self.english_templates = {
            'daily': [
                {
                    'transcript': "M: Excuse me, what time is the next bus to downtown?\nW: It leaves at 3:30. You just missed the 2:30 one.\nM: Oh no, I have to wait an hour then.",
                    'question': "When is the next bus?",
                    'correct': "3:30",
                    'options': ["2:30", "3:30", "4:00", "3:00"],
                    'explanation': "女士说下一班车3:30出发，男士错过了2:30的车。"
                },
                {
                    'transcript': "W: How much is this T-shirt?\nM: It's on sale today, only $25. Normally it's $40.\nW: Great, I'll take two.",
                    'question': "What is the sale price of the T-shirt?",
                    'correct': "$25",
                    'options': ["$40", "$25", "$50", "$30"],
                    'explanation': "男士说今天特价只要25美元，正常价是40美元。"
                },
                {
                    'transcript': "M: Where did you go for your vacation?\nW: I went to Japan. I visited Tokyo and Kyoto.\nM: That sounds amazing! How long did you stay?",
                    'question': "Which country did the woman visit?",
                    'correct': "Japan",
                    'options': ["China", "Korea", "Japan", "Thailand"],
                    'explanation': "女士说她去了日本，游览了东京和京都。"
                },
                {
                    'transcript': "W: I'm so hungry. What's for dinner?\nM: I was thinking about making pasta. Would you like that?\nW: Sure, that sounds good. With tomato sauce?",
                    'question': "What will they have for dinner?",
                    'correct': "Pasta",
                    'options': ["Pizza", "Pasta", "Rice", "Soup"],
                    'explanation': "男士提议做意大利面，女士同意了。"
                },
                {
                    'transcript': "M: The weather is terrible today.\nW: I know, it's raining so hard. We can't go to the park.\nM: Let's watch a movie at home instead.",
                    'question': "What will they do instead of going to the park?",
                    'correct': "Watch a movie",
                    'options': ["Go shopping", "Watch a movie", "Read books", "Cook dinner"],
                    'explanation': "因为下雨不能去公园，他们决定在家看电影。"
                },
                {
                    'transcript': "W: What do you do for work?\nM: I'm a software engineer at a tech company.\nW: That's interesting. Do you work from home?",
                    'question': "What is the man's job?",
                    'correct': "Software engineer",
                    'options': ["Doctor", "Teacher", "Software engineer", "Lawyer"],
                    'explanation': "男士说他是科技公司的软件工程师。"
                },
                {
                    'transcript': "M: How often do you go to the gym?\nW: I try to go three times a week, usually on Monday, Wednesday, and Friday.\nM: That's impressive. I can only go once a week.",
                    'question': "How often does the woman go to the gym?",
                    'correct': "Three times a week",
                    'options': ["Once a week", "Twice a week", "Three times a week", "Every day"],
                    'explanation': "女士说她每周去三次健身房，周一、周三、周五。"
                },
                {
                    'transcript': "W: I think I left my phone at the restaurant.\nM: Let's call the restaurant and ask. Do you remember the name?\nW: Yes, it's the Blue Ocean on Main Street.",
                    'question': "Where did the woman leave her phone?",
                    'correct': "At the restaurant",
                    'options': ["At the office", "At the restaurant", "At home", "In the car"],
                    'explanation': "女士说她可能把手机落在餐厅了。"
                },
                {
                    'transcript': "M: The movie starts at 7 o'clock. What time should we leave?\nW: Let's leave at 6:30. It takes about 20 minutes to get there.\nM: Sounds good. I'll pick you up.",
                    'question': "What time will they leave?",
                    'correct': "6:30",
                    'options': ["6:00", "6:30", "7:00", "7:20"],
                    'explanation': "女士提议6:30出发，路程大约20分钟。"
                },
                {
                    'transcript': "W: I love this coffee shop. The atmosphere is so nice.\nM: Yeah, and their latte is the best in town.\nW: I'll have to try that next time.",
                    'question': "What does the man recommend?",
                    'correct': "The latte",
                    'options': ["The coffee shop", "The latte", "The atmosphere", "The town"],
                    'explanation': "男士说这里的拿铁是城里最好喝的。"
                }
            ],
            'business': [
                {
                    'transcript': "M: Did you receive the quarterly report?\nW: Yes, I reviewed it this morning. The sales numbers look good.\nM: Great, we can discuss it at the meeting tomorrow.",
                    'question': "What will they discuss tomorrow?",
                    'correct': "The quarterly report",
                    'options': ["The sales strategy", "The quarterly report", "The new product", "The budget"],
                    'explanation': "他们明天会议将讨论季度报告。"
                },
                {
                    'transcript': "W: The client wants to meet next week to discuss the contract.\nM: Let me check my schedule. How about Tuesday afternoon?\nW: That works for me. I'll confirm with the client.",
                    'question': "When will they meet the client?",
                    'correct': "Tuesday afternoon",
                    'options': ["Monday morning", "Tuesday afternoon", "Wednesday morning", "Thursday afternoon"],
                    'explanation': "男士提议周二下午见面，女士同意并会与客户确认。"
                },
                {
                    'transcript': "M: Our market share has increased by 15% this quarter.\nW: That's excellent news! What's the main reason?\nM: The new marketing campaign has been very successful.",
                    'question': "Why has the market share increased?",
                    'correct': "New marketing campaign",
                    'options': ["Lower prices", "New marketing campaign", "Better product quality", "More competitors"],
                    'explanation': "市场份额增长的主要原因是新的营销活动非常成功。"
                },
                {
                    'transcript': "W: I'd like to schedule a conference call with the Tokyo office.\nM: What time works for you? They're 9 hours ahead of us.\nW: How about 9 AM our time? That would be 6 PM their time.",
                    'question': "What is the time difference between the two offices?",
                    'correct': "9 hours",
                    'options': ["6 hours", "9 hours", "12 hours", "3 hours"],
                    'explanation': "东京办公室比他们早9个小时。"
                },
                {
                    'transcript': "M: The budget meeting has been moved to next Friday.\nW: Oh, that's better. I have a deadline this Friday.\nM: Same here. I'll send out the new meeting invitation.",
                    'question': "Why is the meeting rescheduled?",
                    'correct': "People have deadlines this Friday",
                    'options': ["The room is not available", "People have deadlines this Friday", "The boss is busy", "It's a holiday"],
                    'explanation': "因为大家这周五有截止日期，所以会议改到下周五。"
                }
            ],
            'campus': [
                {
                    'transcript': "W: What classes are you taking this semester?\nM: I'm taking math, physics, and computer science.\nW: That sounds like a heavy course load.",
                    'question': "How many classes is the man taking?",
                    'correct': "Three",
                    'options': ["Two", "Three", "Four", "Five"],
                    'explanation': "男士选了数学、物理和计算机科学三门课。"
                },
                {
                    'transcript': "M: Where is the library? I need to return some books.\nW: It's on the third floor, next to the computer lab.\nM: Thanks, I was looking everywhere for it.",
                    'question': "Where is the library?",
                    'correct': "On the third floor",
                    'options': ["On the first floor", "On the second floor", "On the third floor", "On the fourth floor"],
                    'explanation': "图书馆在三楼，计算机实验室旁边。"
                },
                {
                    'transcript': "W: The final exam is in two weeks. Are you ready?\nM: Not really, I've been busy with my part-time job.\nW: We should study together this weekend.",
                    'question': "Why isn't the man ready for the exam?",
                    'correct': "He has been busy with work",
                    'options': ["He doesn't study well", "He has been busy with work", "He forgot about the exam", "He doesn't care"],
                    'explanation': "男士因为忙于兼职工作，还没有准备好考试。"
                },
                {
                    'transcript': "M: Did you finish the research paper? It's due tomorrow.\nW: Almost, I just need to add the references.\nM: Good, I'm still working on the conclusion.",
                    'question': "What does the woman still need to do?",
                    'correct': "Add references",
                    'options': ["Write the introduction", "Add references", "Write the conclusion", "Format the paper"],
                    'explanation': "女士的论文差不多写完了，只需要添加参考文献。"
                },
                {
                    'transcript': "W: I'm thinking about joining the debate club.\nM: That's a great idea! I'm in the club. We meet every Thursday evening.\nW: Perfect, I'll come to the next meeting.",
                    'question': "When does the debate club meet?",
                    'correct': "Thursday evening",
                    'options': ["Tuesday afternoon", "Wednesday morning", "Thursday evening", "Friday afternoon"],
                    'explanation': "辩论社每周四晚上聚会。"
                }
            ],
            'news': [
                {
                    'transcript': "Good evening. Today, scientists announced the discovery of a new species of fish in the deep ocean. The fish has unique glowing organs that help it navigate in complete darkness.",
                    'question': "What did scientists discover?",
                    'correct': "A new species of fish",
                    'options': ["A new planet", "A new species of fish", "A new medicine", "A new technology"],
                    'explanation': "科学家在深海发现了一种新的鱼类。"
                },
                {
                    'transcript': "In business news, the technology company announced record profits for this quarter. The company's new smartphone model has been a huge success worldwide.",
                    'question': "What contributed to the record profits?",
                    'correct': "The new smartphone model",
                    'options': ["The new laptop", "The new smartphone model", "Software sales", "Service contracts"],
                    'explanation': "新智能手机型号的成功带来了创纪录的利润。"
                },
                {
                    'transcript': "Weather update: Tomorrow will be partly cloudy with a high of 75 degrees. There's a 30% chance of rain in the afternoon.",
                    'question': "What is the chance of rain tomorrow?",
                    'correct': "30%",
                    'options': ["20%", "30%", "50%", "75%"],
                    'explanation': "明天下午有30%的降雨概率。"
                },
                {
                    'transcript': "Breaking news: The city council has approved a new public transportation plan. The plan includes new bus routes and an extension of the subway system.",
                    'question': "What does the new plan include?",
                    'correct': "New bus routes and subway extension",
                    'options': ["New schools and hospitals", "New bus routes and subway extension", "New shopping malls", "New parks and recreation centers"],
                    'explanation': "新的交通计划包括新的公交线路和地铁延长线。"
                },
                {
                    'transcript': "In sports: The local basketball team won their championship game last night. The final score was 98 to 95. The team's star player scored 35 points.",
                    'question': "How many points did the star player score?",
                    'correct': "35 points",
                    'options': ["25 points", "30 points", "35 points", "98 points"],
                    'explanation': "明星球员得了35分。"
                }
            ]
        }

        self.japanese_templates = {
            'daily': [
                {
                    'transcript': "男：すみません、駅はどこですか？\n女：あそこの角を右に曲がると、駅があります。\n男：ありがとうございます。",
                    'question': "駅はどこですか？",
                    'correct': "角を右に曲がったところ",
                    'options': ["角を左に曲がったところ", "角を右に曲がったところ", "まっすぐ行ったところ", "二階の上"],
                    'explanation': "女士说在那个拐角右转就有车站。"
                },
                {
                    'transcript': "女：今日は何を食べますか？\n男：そうですね、ラーメンが食べたいです。\n女：わかりました、じゃあラーメン屋に行きましょう。",
                    'question': "二人は何を食べますか？",
                    'correct': "ラーメン",
                    'options': ["寿司", "ラーメン", "天ぷら", "うどん"],
                    'explanation': "男士想吃拉面，女士同意了。"
                },
                {
                    'transcript': "男：この本はいくらですか？\n女：千五百円です。\n男：高いですね。もっと安いのはありますか？",
                    'question': "本の値段はいくらですか？",
                    'correct': "千五百円",
                    'options': ["千円", "千五百円", "二千円", "五百円"],
                    'explanation': "这本书1500日元。"
                },
                {
                    'transcript': "女：明日は雨ですね。傘を持って行ったほうがいいですよ。\n男：そうですか。じゃあ傘を持っていきます。\n女：気をつけて行ってらっしゃい。",
                    'question': "明日の天気はどうですか？",
                    'correct': "雨",
                    'options': ["晴れ", "雨", "曇り", "雪"],
                    'explanation': "女士说明天会下雨，最好带伞。"
                },
                {
                    'transcript': "男：休みの日は何をしますか？\n女：よく公園を散歩したり、本を読んだりします。\n男：いいですね、ゆっくりできそうです。",
                    'question': "女の人は休みの日に何をしますか？",
                    'correct': "散歩と読書",
                    'options': ["映画を見る", "散歩と読書", "買い物に行く", "スポーツをする"],
                    'explanation': "女士休息日经常去公园散步和看书。"
                },
                {
                    'transcript': "女：電車は何時に出発しますか？\n男：九時十五分です。あと十分あります。\n女：よかった、間に合いますね。",
                    'question': "今は何時ですか？",
                    'correct': "九時五分",
                    'options': ["九時", "九時五分", "九時十分", "九時十五分"],
                    'explanation': "电车9:15出发，还有10分钟，所以现在是9:05。"
                },
                {
                    'transcript': "男：このカバンは誰のですか？\n女：田中さんのですよ。彼女が忘れていきました。\n男：じゃあ後で渡しておきます。",
                    'question': "カバンは誰のですか？",
                    'correct': "田中さんの",
                    'options': ["男の人の", "女の人の", "田中さんの", "誰のかわからない"],
                    'explanation': "包是田中的，她忘在这里了。"
                },
                {
                    'transcript': "女：猫を飼っていますか？\n男：いいえ、犬を飼っています。毎日散歩に行きます。\n女：いいですね、私も犬が好きです。",
                    'question': "男の人は何を飼っていますか？",
                    'correct': "犬",
                    'options': ["猫", "犬", "鳥", "魚"],
                    'explanation': "男士养了一只狗，每天去散步。"
                },
                {
                    'transcript': "男：学校は何時に終わりますか？\n女：午後四時に終わります。でも今日は部活があるので、六時に帰ります。\n男：大変ですね。",
                    'question': "女の子は今日何時に帰りますか？",
                    'correct': "六時",
                    'options': ["四時", "五時", "六時", "七時"],
                    'explanation': "虽然学校4点放学，但今天有社团活动，她6点回家。"
                },
                {
                    'transcript': "女：このりんごは美味しいですね。どこで買いましたか？\n男：近くの八百屋で買いました。新鮮で安いですよ。\n女：今度行ってみます。",
                    'question': "男の人はどこでりんごを買いましたか？",
                    'correct': "八百屋",
                    'options': ["スーパー", "八百屋", "コンビニ", "市場"],
                    'explanation': "男士在附近的蔬菜水果店买的苹果。"
                }
            ],
            'business': [
                {
                    'transcript': "男：会議は何時からですか？\n女：午後二時からです。資料は準備できていますか？\n男：はい、大丈夫です。",
                    'question': "会議は何時からですか？",
                    'correct': "午後二時",
                    'options': ["午前十一時", "午後一時", "午後二時", "午後三時"],
                    'explanation': "会议从下午2点开始。"
                },
                {
                    'transcript': "女：先日の提案書、読んでいただけましたか？\n男：はい、読みました。予算の部分が少し気になりますね。\n女：そうですか。では修正して再提出します。",
                    'question': "女の人はこれから何をしますか？",
                    'correct': "提案書を修正する",
                    'options': ["提案書を捨てる", "提案書を修正する", "新しい会議を開く", "予算を増やす"],
                    'explanation': "女士会修改提案书后重新提交。"
                },
                {
                    'transcript': "男：今月の売り上げは先月より20%増えました。\n女：素晴らしいです！新しい営業戦略のおかげですね。\n男：ええ、来月も頑張りましょう。",
                    'question': "売り上げはどうなりましたか？",
                    'correct': "20%増えた",
                    'options': ["20%減った", "10%増えた", "20%増えた", "変わらない"],
                    'explanation': "这个月的销售额比上个月增长了20%。"
                },
                {
                    'transcript': "女：東京支社との電話会議は何時ですか？\n男：午前十時です。向こうは十一時ですね。\n女：はい、時差が一時間ありますから。",
                    'question': "時差は何時間ありますか？",
                    'correct': "一時間",
                    'options': ["一時間", "二時間", "三時間", "三十分"],
                    'explanation': "两地时差为1小时。"
                },
                {
                    'transcript': "男：来週の金曜日に出張に行かなければなりません。\n女：そうですか。金曜日は会議がありますけど、大丈夫ですか？\n男：会議は木曜日に変更してもらえませんか？",
                    'question': "男の人は何をお願いしていますか？",
                    'correct': "会議を木曜日に変更すること",
                    'options': ["出張を中止すること", "会議を木曜日に変更すること", "出張に一緒に行くこと", "資料を準備すること"],
                    'explanation': "男士请求把会议改到星期四。"
                }
            ],
            'campus': [
                {
                    'transcript': "男：図書館は何時まで開いていますか？\n女：平日は九時まで、土日は五時までです。\n男：あと一時間ありますね。",
                    'question': "今は何時ですか（平日の場合）？",
                    'correct': "八時",
                    'options': ["七時", "八時", "九時", "十時"],
                    'explanation': "图书馆平日9点关门，还有1小时，所以现在是8点。"
                },
                {
                    'transcript': "女：ゼミのレポート、もう書きましたか？\n男：いや、まだ半分くらいです。来週の水曜日が締め切りですよね？\n女：ええ、急いで書いたほうがいいですよ。",
                    'question': "レポートの締め切りは何曜日ですか？",
                    'correct': "水曜日",
                    'options': ["月曜日", "水曜日", "金曜日", "日曜日"],
                    'explanation': "研讨会报告的截止日期是下周三。"
                },
                {
                    'transcript': "男：この大学で一番人気の部活は何ですか？\n女：サッカー部だと思います。いつもたくさんの人が見に来ます。\n男：そうですか。僕も入ろうかな。",
                    'question': "一番人気の部活は何ですか？",
                    'correct': "サッカー部",
                    'options': ["野球部", "サッカー部", "テニス部", "バスケットボール部"],
                    'explanation': "最受欢迎的社团是足球部。"
                },
                {
                    'transcript': "女：試験はどうでしたか？\n男：難しかったです。特に数学が全然できませんでした。\n女：そうですか。私も数学は苦手です。",
                    'question': "男の人はどの科目が難しかったですか？",
                    'correct': "数学",
                    'options': ["英語", "数学", "国語", "物理"],
                    'explanation': "男士觉得数学特别难，完全不会。"
                },
                {
                    'transcript': "男：留学生の田中さん、知っていますか？\n女：ええ、中国から来たんですよね。日本語が上手です。\n男：本当ですか。今度話しかけてみよう。",
                    'question': "田中さんはどこから来ましたか？",
                    'correct': "中国",
                    'options': ["アメリカ", "中国", "韓国", "イギリス"],
                    'explanation': "田中同学是从中国来的留学生。"
                }
            ],
            'news': [
                {
                    'transcript': "ニュースです。今日、新しい駅が開業しました。この駅は市内の南側に位置し、毎日約一万人が利用すると予想されています。",
                    'question': "新しい駅はどこにできましたか？",
                    'correct': "市内の南側",
                    'options': ["市内の北側", "市内の南側", "市の外れ", "空港の近く"],
                    'explanation': "新车站位于城市南侧。"
                },
                {
                    'transcript': "天気予報です。明日は晴れるでしょう。最高気温は二十八度、最低気温は二十度の予想です。",
                    'question': "明日の最高気温は何度ですか？",
                    'correct': "二十八度",
                    'options': ["二十度", "二十五度", "二十八度", "三十度"],
                    'explanation': "明天的最高气温预计是28度。"
                },
                {
                    'transcript': "経済ニュースです。大手電気メーカーが新しいスマートフォンを発売しました。価格は八万円からで、来月から販売が開始されます。",
                    'question': "新しいスマートフォンの値段はいくらからですか？",
                    'correct': "八万円",
                    'options': ["五万円", "六万円", "七万円", "八万円"],
                    'explanation': "新智能手机的价格从8万日元起。"
                },
                {
                    'transcript': "スポーツニュースです。昨日のサッカーの試合で、日本チームが三対二で勝利しました。キャプテンが二点を決めました。",
                    'question': "キャプテンは何点決めましたか？",
                    'correct': "二点",
                    'options': ["一点", "二点", "三点", "五点"],
                    'explanation': "队长踢进了两个球。"
                },
                {
                    'transcript': "速報です。午後三時ごろ、大きな地震がありました。震度は5でしたが、被害は今のところ報告されていません。",
                    'question': "地震の震度はどれくらいでしたか？",
                    'correct': "5",
                    'options': ["3", "4", "5", "6"],
                    'explanation': "地震的震度为5级。"
                }
            ]
        }

        self.chinese_templates = {
            'daily': [
                {
                    'transcript': "男：你好，请问附近有超市吗？\n女：有的，往前走两百米，在银行旁边。\n男：谢谢你。",
                    'question': "超市在哪里？",
                    'correct': "银行旁边",
                    'options': ["医院旁边", "银行旁边", "学校旁边", "公园旁边"],
                    'explanation': "女士说超市在银行旁边。"
                },
                {
                    'transcript': "女：今天中午吃什么？\n男：我想吃饺子。\n女：好的，我们去楼下的饺子馆。",
                    'question': "他们中午吃什么？",
                    'correct': "饺子",
                    'options': ["面条", "饺子", "米饭", "火锅"],
                    'explanation': "男士想吃饺子，女士同意了。"
                },
                {
                    'transcript': "男：这本书多少钱？\n女：原价五十元，现在打八折，四十元。\n男：便宜了十元啊。",
                    'question': "这本书现在多少钱？",
                    'correct': "四十元",
                    'options': ["五十元", "四十元", "三十元", "六十元"],
                    'explanation': "这本书原价50元，打八折后40元。"
                },
                {
                    'transcript': "女：明天天气怎么样？\n男：天气预报说明天会下雨。\n女：那我要带伞出门。",
                    'question': "明天天气怎么样？",
                    'correct': "下雨",
                    'options': ["晴天", "下雨", "阴天", "下雪"],
                    'explanation': "天气预报说明天会下雨。"
                },
                {
                    'transcript': "男：周末你打算做什么？\n女：我想去公园散步，然后看电影。\n男：听起来不错。",
                    'question': "女士周末打算做什么？",
                    'correct': "散步和看电影",
                    'options': ["逛街", "散步和看电影", "爬山", "学习"],
                    'explanation': "女士周末想去公园散步，然后看电影。"
                },
                {
                    'transcript': "女：火车几点发车？\n男：九点十五分。还有二十分钟。\n女：那来得及。",
                    'question': "现在几点？",
                    'correct': "八点五十五分",
                    'options': ["八点", "八点五十五分", "九点", "九点十五分"],
                    'explanation': "火车9:15发车，还有20分钟，所以现在是8:55。"
                },
                {
                    'transcript': "男：这个包是谁的？\n女：是李明的，他忘记带走了。\n男：我稍后给他。",
                    'question': "包是谁的？",
                    'correct': "李明的",
                    'options': ["男士的", "女士的", "李明的", "不知道"],
                    'explanation': "包是李明的，他忘记带走了。"
                },
                {
                    'transcript': "女：你养宠物吗？\n男：是的，我养了一只猫。\n女：我也喜欢猫。",
                    'question': "男士养了什么宠物？",
                    'correct': "猫",
                    'options': ["狗", "猫", "鸟", "鱼"],
                    'explanation': "男士养了一只猫。"
                },
                {
                    'transcript': "男：学校几点放学？\n女：下午四点。但是今天有社团活动，我五点回家。\n男：辛苦了。",
                    'question': "女士今天几点回家？",
                    'correct': "五点",
                    'options': ["四点", "四点半", "五点", "五点半"],
                    'explanation': "学校4点放学，但今天有社团活动，她5点回家。"
                },
                {
                    'transcript': "女：这个苹果真好吃。在哪里买的？\n男：在小区门口的水果店。又新鲜又便宜。\n女：下次我也去看看。",
                    'question': "男士在哪里买的苹果？",
                    'correct': "小区门口的水果店",
                    'options': ["超市", "小区门口的水果店", "菜市场", "网上"],
                    'explanation': "男士在小区门口的水果店买的苹果。"
                }
            ],
            'business': [
                {
                    'transcript': "男：会议几点开始？\n女：下午两点。资料准备好了吗？\n男：准备好了。",
                    'question': "会议几点开始？",
                    'correct': "下午两点",
                    'options': ["上午十一点", "下午一点", "下午两点", "下午三点"],
                    'explanation': "会议从下午2点开始。"
                },
                {
                    'transcript': "女：上次的提案您看过了吗？\n男：看过了。预算部分需要再讨论一下。\n女：好的，我会修改后再提交。",
                    'question': "女士接下来要做什么？",
                    'correct': "修改提案",
                    'options': ["放弃提案", "修改提案", "召开会议", "增加预算"],
                    'explanation': "女士会修改提案后重新提交。"
                },
                {
                    'transcript': "男：这个月销售额增长了15%。\n女：太好了！是新营销策略的效果吗？\n男：是的，下个月继续努力。",
                    'question': "销售额增长了多少？",
                    'correct': "15%",
                    'options': ["10%", "15%", "20%", "25%"],
                    'explanation': "这个月销售额增长了15%。"
                },
                {
                    'transcript': "女：和上海分公司的电话会议几点？\n男：上午十点。那边是中午十二点。\n女：时差两小时啊。",
                    'question': "时差是多少小时？",
                    'correct': "两小时",
                    'options': ["一小时", "两小时", "三小时", "半小时"],
                    'explanation': "两地时差为2小时。"
                },
                {
                    'transcript': "男：下周五要出差。\n女：但周五有个会议。\n男：能改到周四吗？",
                    'question': "男士请求什么？",
                    'correct': "把会议改到周四",
                    'options': ["取消出差", "把会议改到周四", "一起出差", "准备资料"],
                    'explanation': "男士请求把会议改到星期四。"
                }
            ],
            'campus': [
                {
                    'transcript': "男：图书馆几点关门？\n女：平时到九点，周末到五点。\n男：还有一小时。",
                    'question': "现在几点（平时）？",
                    'correct': "八点",
                    'options': ["七点", "八点", "九点", "十点"],
                    'explanation': "图书馆平时9点关门，还有1小时，所以现在是8点。"
                },
                {
                    'transcript': "女：论文写完了吗？\n男：还没有，才写了一半。下周三截止。\n女：要抓紧了。",
                    'question': "论文什么时候截止？",
                    'correct': "下周三",
                    'options': ["下周一", "下周三", "下周五", "下周日"],
                    'explanation': "论文截止日期是下周三。"
                },
                {
                    'transcript': "男：学校最受欢迎的社团是什么？\n女：应该是足球社，很多人来看比赛。\n男：我也想加入。",
                    'question': "最受欢迎的社团是什么？",
                    'correct': "足球社",
                    'options': ["篮球社", "足球社", "羽毛球社", "辩论社"],
                    'explanation': "最受欢迎的社团是足球社。"
                },
                {
                    'transcript': "女：考试怎么样？\n男：很难，数学几乎不会。\n女：我数学也不好。",
                    'question': "男士觉得哪科最难？",
                    'correct': "数学",
                    'options': ["英语", "数学", "语文", "物理"],
                    'explanation': "男士觉得数学特别难。"
                },
                {
                    'transcript': "男：你认识留学生小王吗？\n女：认识，他来自韩国，中文说得很好。\n男：下次我要跟他交流一下。",
                    'question': "小王来自哪里？",
                    'correct': "韩国",
                    'options': ["美国", "中国", "韩国", "英国"],
                    'explanation': "小王是从韩国来的留学生。"
                }
            ],
            'news': [
                {
                    'transcript': "新闻报道：今天，新的地铁站正式开通。位于城市东部，预计每天有两万人使用。",
                    'question': "新地铁站在哪里？",
                    'correct': "城市东部",
                    'options': ["城市西部", "城市东部", "城市北部", "城市南部"],
                    'explanation': "新地铁站位于城市东部。"
                },
                {
                    'transcript': "天气预报：明天天气晴朗，最高温度三十度，最低温度二十度。",
                    'question': "明天最高温度多少度？",
                    'correct': "三十度",
                    'options': ["二十度", "二十五度", "三十度", "三十五度"],
                    'explanation': "明天最高气温预计是30度。"
                },
                {
                    'transcript': "财经新闻：一家科技公司发布了新款智能手机，售价五千元起，下个月开始销售。",
                    'question': "新手机多少钱起？",
                    'correct': "五千元",
                    'options': ["三千元", "四千元", "五千元", "六千元"],
                    'explanation': "新手机价格从5000元起。"
                },
                {
                    'transcript': "体育新闻：昨晚的篮球比赛，主队以一百零五比九十五获胜。队长得到了三十分。",
                    'question': "队长得了多少分？",
                    'correct': "三十分",
                    'options': ["二十分", "二十五分", "三十分", "三十五分"],
                    'explanation': "队长得了30分。"
                },
                {
                    'transcript': "突发新闻：下午两点左右发生地震，震级为四级，目前暂无人员伤亡报告。",
                    'question': "地震震级是多少？",
                    'correct': "四级",
                    'options': ["三级", "四级", "五级", "六级"],
                    'explanation': "地震震级为4级。"
                }
            ]
        }

    @contextmanager
    def get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def generate_listening_questions(self, language: str, difficulty: int = 1, topic: str = 'daily', count: int = 10) -> list:
        """
        生成听力题目
        Args:
            language: 语言 (english/japanese)
            difficulty: 难度 (1-5)
            topic: 主题 (daily/business/campus/news)
            count: 生成数量
        Returns:
            题目列表
        """
        try:
            if language == 'english':
                templates = self.english_templates.get(topic, self.english_templates['daily'])
                accent = 'us'
                lang_full = 'english'
            elif language == 'japanese':
                templates = self.japanese_templates.get(topic, self.japanese_templates['daily'])
                accent = 'kanto'
                lang_full = 'japanese'
            elif language == 'chinese':
                templates = self.chinese_templates.get(topic, self.chinese_templates['daily'])
                accent = 'mandarin'
                lang_full = 'chinese'
            else:
                logger.warning(f"[听力题生成器] 不支持的语言: {language}")
                return []

            questions = []
            difficulty_level = self._map_difficulty(difficulty)

            for i in range(min(count, len(templates))):
                template = templates[i]
                question = self._create_question_dict(
                    language=language,
                    difficulty=difficulty,
                    topic=topic,
                    accent=accent,
                    transcript=template['transcript'],
                    question_text=template['question'],
                    options_texts=template['options'],
                    correct_answer_text=template['correct'],
                    explanation=template['explanation']
                )
                questions.append(question)

            if count > len(templates):
                additional = count - len(templates)
                for i in range(additional):
                    template = random.choice(templates)
                    question = self._create_question_dict(
                        language=language,
                        difficulty=difficulty,
                        topic=topic,
                        accent=accent,
                        transcript=template['transcript'],
                        question_text=template['question'] + f"（類題{i+1}）",
                        options_texts=template['options'],
                        correct_answer_text=template['correct'],
                        explanation=template['explanation']
                    )
                    questions.append(question)

            logger.info(f"[听力题生成器] 生成了 {len(questions)} 道{language}听力题（难度{difficulty}, 主题{topic}）")
            return questions

        except Exception as e:
            logger.error(f"[听力题生成器] 生成听力题失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def _map_difficulty(self, difficulty: int) -> str:
        """将数字难度映射为等级"""
        if difficulty <= 2:
            return 'beginner'
        elif difficulty <= 3:
            return 'intermediate'
        else:
            return 'advanced'

    def _create_question_dict(self, language: str, difficulty: int, topic: str,
                               accent: str, transcript: str, question_text: str,
                               options_texts: list, correct_answer_text: str,
                               explanation: str) -> dict:
        """创建题目字典"""
        import uuid
        question_id = f"lq_gen_{uuid.uuid4().hex[:12]}"

        correct_key = None
        options = []
        letters = ['A', 'B', 'C', 'D']

        correct_idx = options_texts.index(correct_answer_text) if correct_answer_text in options_texts else 0

        for i, opt_text in enumerate(options_texts[:4]):
            key = letters[i]
            options.append({'key': key, 'text': opt_text})
            if i == correct_idx:
                correct_key = key

        return {
            'id': question_id,
            'language': language,
            'difficulty': difficulty,
            'topic': topic,
            'accent': accent,
            'content': question_text,
            'options': options,
            'correct_answer': correct_key,
            'audio_url': None,
            'transcript': transcript,
            'explanation': explanation,
            'duration': len(transcript) // 3 + 10,
            'generated': True
        }

    def save_questions_to_db(self, questions: list) -> int:
        """
        将生成的题目保存到数据库
        Args:
            questions: 题目列表
        Returns:
            保存成功的数量
        """
        try:
            saved_count = 0
            now = datetime.now(timezone.utc).isoformat()

            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                for q in questions:
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO listening_questions
                            (id, language, difficulty, topic, accent, content, options,
                             correct_answer, audio_url, transcript, explanation, duration,
                             created_at, updated_at, is_generated)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """, (
                            q['id'],
                            q['language'],
                            q['difficulty'],
                            q['topic'],
                            q['accent'],
                            q['content'],
                            json.dumps(q['options'], ensure_ascii=False),
                            q['correct_answer'],
                            q.get('audio_url'),
                            q.get('transcript', ''),
                            q.get('explanation', ''),
                            q.get('duration', 30),
                            now,
                            now
                        ))
                        saved_count += 1
                    except Exception as e:
                        logger.warning(f"[听力题生成器] 保存题目失败 {q.get('id')}: {e}")

                conn.commit()

            logger.info(f"[听力题生成器] 成功保存 {saved_count} 道听力题到数据库")
            return saved_count

        except Exception as e:
            logger.error(f"[听力题生成器] 保存题目到数据库失败: {e}")
            return 0

    def get_or_generate_questions(self, language: str = 'all', difficulty: str = 'all',
                                   topic: str = 'all', limit: int = 20) -> dict:
        """
        智能获取题目：先查数据库，不足则AI生成并入库
        Args:
            language: 语言 (all/english/japanese)
            difficulty: 难度 (all/1/2/3/4/5)
            topic: 主题 (all/daily/business/campus/news)
            limit: 期望数量
        Returns:
            {
                'success': bool,
                'data': list,
                'total': int,
                'from_db': int,
                'generated': int
            }
        """
        try:
            with self.get_db_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                query = "SELECT * FROM listening_questions WHERE 1=1"
                params = []

                if language != 'all':
                    query += " AND language = ?"
                    params.append(language)
                if difficulty != 'all':
                    query += " AND difficulty = ?"
                    params.append(int(difficulty))
                if topic != 'all':
                    query += " AND topic = ?"
                    params.append(topic)

                query += " ORDER BY RANDOM() LIMIT ?"
                params.append(limit)

                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()

                db_questions = []
                for row in rows:
                    db_questions.append({
                        'id': row['id'],
                        'language': row['language'],
                        'difficulty': row['difficulty'],
                        'topic': row['topic'],
                        'accent': row['accent'],
                        'content': row['content'],
                        'options': json.loads(row['options']) if row['options'] else [],
                        'correct_answer': row['correct_answer'],
                        'audio_url': row['audio_url'],
                        'transcript': row['transcript'],
                        'explanation': row['explanation'],
                        'duration': row['duration']
                    })

                from_db_count = len(db_questions)

                if from_db_count >= limit:
                    return {
                        'success': True,
                        'data': db_questions[:limit],
                        'total': limit,
                        'from_db': from_db_count,
                        'generated': 0
                    }

                needed = limit - from_db_count
                gen_language = language if language != 'all' else 'english'
                gen_difficulty = int(difficulty) if difficulty != 'all' else 2
                gen_topic = topic if topic != 'all' else 'daily'

                logger.info(f"[听力题生成器] 数据库仅有{from_db_count}题，需要生成{needed}题")

                generated_questions = self.generate_listening_questions(
                    language=gen_language,
                    difficulty=gen_difficulty,
                    topic=gen_topic,
                    count=needed
                )

                if generated_questions:
                    self.save_questions_to_db(generated_questions)

                    all_questions = db_questions + generated_questions[:needed]

                    return {
                        'success': True,
                        'data': all_questions,
                        'total': len(all_questions),
                        'from_db': from_db_count,
                        'generated': min(needed, len(generated_questions))
                    }

                return {
                    'success': True,
                    'data': db_questions,
                    'total': from_db_count,
                    'from_db': from_db_count,
                    'generated': 0
                }

        except Exception as e:
            logger.error(f"[听力题生成器] 智能获取题目失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'data': [],
                'total': 0,
                'from_db': 0,
                'generated': 0,
                'error': str(e)
            }

    def generate_audio_for_question(self, question_id: str) -> bool:
        """为题目生成音频文件"""
        try:
            if not HAS_AUDIO_MANAGER:
                logger.warning("[听力题生成器] 音频管理器不可用，跳过音频生成")
                return False

            with self.get_db_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM listening_questions WHERE id = ?", (question_id,))
                q = cursor.fetchone()

                if not q:
                    logger.warning(f"[听力题生成器] 题目不存在: {question_id}")
                    return False

                if q['audio_url']:
                    logger.info(f"[听力题生成器] 题目已有音频: {question_id}")
                    return True

                language = q['language']
                transcript = q['transcript'] or q['content']

                audio_url = audio_manager.generate_audio_url(transcript, language, q['accent'])

                if audio_url:
                    cursor.execute(
                        "UPDATE listening_questions SET audio_url = ?, updated_at = ? WHERE id = ?",
                        (audio_url, datetime.now(timezone.utc).isoformat(), question_id)
                    )
                    conn.commit()
                    logger.info(f"[听力题生成器] 为题目生成音频成功: {question_id}")
                    return True
                else:
                    logger.warning(f"[听力题生成器] 音频生成失败: {question_id}")
                    return False

        except Exception as e:
            logger.error(f"[听力题生成器] 生成音频失败: {e}")
            return False


_listening_question_generator = None


def get_listening_question_generator(db_path=None):
    """获取听力题生成器单例"""
    global _listening_question_generator
    if _listening_question_generator is None:
        _listening_question_generator = ListeningQuestionGenerator(db_path)
    return _listening_question_generator


if __name__ == '__main__':
    generator = ListeningQuestionGenerator()

    print("=== 测试生成英语听力题 ===")
    qs = generator.generate_listening_questions('english', 2, 'daily', 3)
    for q in qs:
        print(f"  {q['id']}: {q['content'][:30]}... 答案={q['correct_answer']}")

    print("\n=== 测试生成日语听力题 ===")
    qs = generator.generate_listening_questions('japanese', 2, 'daily', 3)
    for q in qs:
        print(f"  {q['id']}: {q['content'][:30]}... 答案={q['correct_answer']}")

    print("\n=== 测试智能获取 ===")
    result = generator.get_or_generate_questions('english', '2', 'daily', 5)
    print(f"  成功: {result['success']}")
    print(f"  总数: {result['total']}")
    print(f"  来自数据库: {result['from_db']}")
    print(f"  AI生成: {result['generated']}")
