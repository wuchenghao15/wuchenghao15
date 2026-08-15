#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

def add_listening_categories(conn):
    cursor = conn.cursor()
    categories = [
        ('日语听力', 'JapaneseListening', '日语听力专项', 21, 1),
        ('英语听力', 'EnglishListening', '英语听力专项', 22, 1),
        ('语文听力', 'ChineseListening', '语文听力专项', 23, 1),
    ]
    
    for cat in categories:
        try:
            cursor.execute("INSERT OR IGNORE INTO question_categories (name, code, description, sort_order, status) VALUES (?, ?, ?, ?, ?)", cat)
            print(f"  添加分类: {cat[0]}")
        except Exception as e:
            print(f"  添加分类 {cat[0]} 失败: {e}")
    
    conn.commit()

def add_listening_tags(conn):
    cursor = conn.cursor()
    tags = [
        ('听力', '听力理解专项', 31),
        ('日语听力', '日语听力练习', 32),
        ('英语听力', '英语听力练习', 33),
        ('语文听力', '语文听力练习', 34),
        ('N1听力', '日语N1级听力', 35),
        ('N2听力', '日语N2级听力', 36),
        ('N3听力', '日语N3级听力', 37),
        ('N4听力', '日语N4级听力', 38),
        ('N5听力', '日语N5级听力', 39),
        ('美音', '美式英语发音', 40),
        ('英音', '英式英语发音', 41),
        ('对话', '对话类听力', 42),
        ('短文', '短文类听力', 43),
        ('新闻', '新闻类听力', 44),
        ('古诗文', '古诗文朗诵', 45),
    ]
    
    for tag in tags:
        try:
            cursor.execute("INSERT OR IGNORE INTO question_tags (name, description, sort_order) VALUES (?, ?, ?)", tag)
            print(f"  添加标签: {tag[0]}")
        except Exception as e:
            print(f"  添加标签 {tag[0]} 失败: {e}")
    
    conn.commit()

def insert_japanese_listening_questions(conn):
    cursor = conn.cursor()
    questions = [
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'easy', 'B', 'A|行きたくない|B|明日にします|C|今すぐ行きます|D|分かりません', '男性が「明日にしましょう」と言っているため、明日にするのが正解です。', '2026', 'japanese_listening_n5', 'system', 21, '男：今日はちょっと疲れたから、明日にしましょう。女：分かりました。', 'japanese', 'kanto', 'male'),
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'easy', 'A', 'A|コーヒーを飲む|B|お茶を飲む|C|ジュースを飲む|D|水を飲む', '女性が「コーヒーをください」と注文しているため、コーヒーを飲むのが正解です。', '2026', 'japanese_listening_n5', 'system', 21, '女：コーヒーをください。男：はい、かしこまりました。', 'japanese', 'kanto', 'female'),
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'easy', 'C', 'A|7時|B|8時|C|9時|D|10時', '「8時半に集まって、9時に出発」と言っているため、出発時間は9時です。', '2026', 'japanese_listening_n5', 'system', 21, '男：明日は8時半に駅前で集まって、9時に出発します。女：分かりました。', 'japanese', 'kansai', 'male'),
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'medium', 'D', 'A|デパート|B|スーパー|C|銀行|D|病院', '「頭が痛いので病院に行く」と言っているため、病院が正解です。', '2026', 'japanese_listening_n4', 'system', 21, '女：昨日から頭が痛いので、今日は病院に行こうと思います。男：お大事に。', 'japanese', 'kanto', 'female'),
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'medium', 'B', 'A|仕事を休む|B|仕事を続ける|C|旅行に行く|D|買い物に行く', '「大丈夫だから続ける」と言っているため、仕事を続けるのが正解です。', '2026', 'japanese_listening_n4', 'system', 21, '男：疲れているようだけど、大丈夫？女：大丈夫だから、仕事を続けます。', 'japanese', 'kansai', 'female'),
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'medium', 'A', 'A|雨が降る|B|晴れる|C|曇る|D|雪が降る', '「夕方から雨が降るだろう」と予報しているため、雨が降るのが正解です。', '2026', 'japanese_listening_n4', 'system', 21, '女：今日の天気予報、どう？男：午前は晴れるけど、夕方から雨が降るだろう。', 'japanese', 'kanto', 'male'),
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'medium', 'C', 'A|電車|B|バス|C|タクシー|D|自転車', '「タクシーで行った方が速い」と言っているため、タクシーが正解です。', '2026', 'japanese_listening_n3', 'system', 21, '男：時間がないから、タクシーで行った方が速いと思う。女：そうだね。', 'japanese', 'kanto', 'male'),
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'medium', 'B', 'A|友達と|B|家族と|C|同僚と|D|恋人と', '「家族と一緒に温泉に行く」と言っているため、家族とが正解です。', '2026', 'japanese_listening_n3', 'system', 21, '女：週末は何をするの？男：家族と一緒に温泉に行く予定です。', 'japanese', 'kansai', 'female'),
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'hard', 'A', 'A|プレゼンテーションをする|B|会議に参加する|C|出張に行く|D|研修を受ける', '「来週の月曜日にプレゼンテーションをする」と言っているため、プレゼンテーションをするのが正解です。', '2026', 'japanese_listening_n2', 'system', 21, '男：来週の月曜日に新製品のプレゼンテーションをすることになりました。女：頑張ってください。', 'japanese', 'kanto', 'male'),
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'hard', 'D', 'A|値段が高い|B|品質が悪い|C|納期が遅い|D|サービスが悪い', '「サービスが悪かった」と言っているため、サービスが悪いが正解です。', '2026', 'japanese_listening_n2', 'system', 21, '女：先日利用したレストラン、サービスが悪かったわ。男：本当に？次は違う店にしよう。', 'japanese', 'kansai', 'female'),
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'hard', 'B', 'A|市場調査をする|B|販売戦略を検討する|C|広告を出す|D|製品を開発する', '「販売戦略を検討する必要がある」と言っているため、販売戦略を検討するが正解です。', '2026', 'japanese_listening_n1', 'system', 21, '男：現在の販売状況を分析した結果、新たな販売戦略を検討する必要があると考えます。女：承知しました。', 'japanese', 'kanto', 'male'),
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'hard', 'C', 'A|環境問題|B|経済問題|C|教育問題|D|医療問題', '「教育問題に関する議論」と言っているため、教育問題が正解です。', '2026', 'japanese_listening_n1', 'system', 21, '女：今日のテレビ番組は、教育問題に関する議論が行われました。男：面白かったですね。', 'japanese', 'kanto', 'female'),
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'easy', 'D', 'A|ペン|B|ノート|C|消しゴム|D|本', '「本を借りに行く」と言っているため、本が正解です。', '2026', 'japanese_listening_n5', 'system', 21, '男：図書館に本を借りに行きます。女：いつ帰ってくるの？', 'japanese', 'kansai', 'male'),
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'medium', 'A', 'A|6月1日|B|6月5日|C|6月10日|D|6月15日', '「6月1日から始まる」と言っているため、6月1日が正解です。', '2026', 'japanese_listening_n4', 'system', 21, '女：セールはいつからですか？男：6月1日から始まります。', 'japanese', 'kanto', 'female'),
        ('次の内容に合っている選択肢を選んでください。', 'listening', '日语', 'medium', 'B', 'A|料理|B|音楽|C|映画|D|スポーツ', '「音楽を聴くのが好き」と言っているため、音楽が正解です。', '2026', 'japanese_listening_n3', 'system', 21, '男：趣味は何ですか？女：音楽を聴くのが好きです。', 'japanese', 'kansai', 'male'),
    ]
    
    for q in questions:
        try:
            cursor.execute("INSERT INTO questions (question_text, question_type, subject, difficulty, answer, options, explanation, year, special_type, source, category_id, transcript, language, accent, voice) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", q)
        except Exception as e:
            print(f"  插入日语听力题目失败: {e}")
    
    conn.commit()
    print("  日语听力题目已插入")

def insert_english_listening_questions(conn):
    cursor = conn.cursor()
    questions = [
        ('What is the woman going to do?', 'listening', '英语', 'easy', 'B', 'A|Go shopping|B|See a doctor|C|Visit a friend|D|Go to work', 'The woman says she has a headache and is going to the hospital.', '2026', 'english_listening_conversation', 'system', 22, 'Woman: I have a bad headache. I need to see a doctor. Man: I hope you feel better soon.', 'english', 'american', 'female'),
        ('What time will the meeting start?', 'listening', '英语', 'easy', 'C', 'A|9:00 AM|B|9:30 AM|C|10:00 AM|D|10:30 AM', 'The man says the meeting is at 10 o\'clock.', '2026', 'english_listening_conversation', 'system', 22, 'Man: When is the meeting? Woman: It\'s at 10 o\'clock in the morning.', 'english', 'american', 'male'),
        ('Where is the man going?', 'listening', '英语', 'easy', 'A', 'A|To the airport|B|To the station|C|To the office|D|To the restaurant', 'The man says he needs to catch a flight.', '2026', 'english_listening_conversation', 'system', 22, 'Man: I need to go to the airport to catch my flight. Woman: Have a safe trip.', 'english', 'british', 'male'),
        ('What does the woman want to buy?', 'listening', '英语', 'medium', 'D', 'A|Books|B|Clothes|C|Food|D|A phone', 'The woman asks about the latest smartphone.', '2026', 'english_listening_conversation', 'system', 22, 'Woman: Can you show me the latest smartphone? Man: Sure, right this way.', 'english', 'american', 'female'),
        ('Why is the man late?', 'listening', '英语', 'medium', 'B', 'A|He overslept|B|Traffic was heavy|C|He missed the bus|D|He stopped for coffee', 'The man explains there was a lot of traffic.', '2026', 'english_listening_conversation', 'system', 22, 'Man: I\'m sorry I\'m late. The traffic was terrible this morning. Woman: No problem, we just started.', 'english', 'british', 'male'),
        ('What is the weather like today?', 'listening', '英语', 'medium', 'C', 'A|Sunny|B|Cloudy|C|Raining|D|Snowing', 'The woman says it\'s pouring outside.', '2026', 'english_listening_conversation', 'system', 22, 'Woman: Don\'t forget your umbrella. It\'s pouring outside. Man: Thanks for reminding me.', 'english', 'american', 'female'),
        ('How does the woman feel?', 'listening', '英语', 'medium', 'A', 'A|Excited|B|Sad|C|Angry|D|Tired', 'The woman expresses excitement about her vacation.', '2026', 'english_listening_conversation', 'system', 22, 'Woman: I\'m so excited! My vacation starts tomorrow. Man: That sounds wonderful.', 'english', 'british', 'female'),
        ('What are they talking about?', 'listening', '英语', 'medium', 'D', 'A|A movie|B|A restaurant|C|A book|D|A job interview', 'They discuss preparing for an interview.', '2026', 'english_listening_conversation', 'system', 22, 'Man: How was your job interview? Woman: It went well. I think I did a good job.', 'english', 'american', 'male'),
        ('What does the man suggest?', 'listening', '英语', 'hard', 'B', 'A|Take a break|B|Work together|C|Quit the project|D|Ask for help', 'The man suggests working together to finish the project.', '2026', 'english_listening_conversation', 'system', 22, 'Man: This project is too big for one person. Let\'s work together. Woman: That sounds like a good idea.', 'english', 'british', 'male'),
        ('What is the main topic of the conversation?', 'listening', '英语', 'hard', 'C', 'A|Travel plans|B|Business meeting|C|Environmental issues|D|Technology trends', 'They discuss environmental protection and recycling.', '2026', 'english_listening_conversation', 'system', 22, 'Woman: We need to do more to protect the environment. Man: I agree. Recycling is important, but we should also reduce waste.', 'english', 'american', 'female'),
        ('According to the news, what happened?', 'listening', '英语', 'hard', 'A', 'A|A new policy was announced|B|A natural disaster occurred|C|A famous person visited|D|A sports event was held', 'The news report is about a new government policy.', '2026', 'english_listening_news', 'system', 22, 'News Reporter: The government has announced a new policy to promote renewable energy. This initiative aims to reduce carbon emissions by 50% over the next decade.', 'english', 'american', 'male'),
        ('What is the speaker talking about?', 'listening', '英语', 'hard', 'D', 'A|Education reform|B|Healthcare system|C|Economic growth|D|Technology innovation', 'The speaker discusses technological advancements.', '2026', 'english_listening_talk', 'system', 22, 'Speaker: Today, I want to talk about the rapid advancement of artificial intelligence and its impact on various industries. AI is transforming how we work, learn, and interact.', 'english', 'british', 'male'),
        ('What does the woman recommend?', 'listening', '英语', 'medium', 'C', 'A|A hotel|B|A museum|C|A restaurant|D|A park', 'The woman recommends a new restaurant.', '2026', 'english_listening_conversation', 'system', 22, 'Woman: There\'s a new Italian restaurant downtown. You should try it. Man: I love Italian food. Thanks for the recommendation.', 'english', 'american', 'female'),
        ('How much does the item cost?', 'listening', '英语', 'easy', 'B', 'A|$10|B|$15|C|$20|D|$25', 'The man says the price is $15.', '2026', 'english_listening_conversation', 'system', 22, 'Woman: How much is this shirt? Man: It\'s $15. Woman: That\'s a good price.', 'english', 'british', 'male'),
        ('What is the man\'s opinion?', 'listening', '英语', 'hard', 'A', 'A|Positive|B|Negative|C|Neutral|D|Uncertain', 'The man expresses positive views about the new product.', '2026', 'english_listening_conversation', 'system', 22, 'Man: I tried the new software and it\'s amazing! It\'s much faster and easier to use. Woman: I\'m glad to hear that.', 'english', 'american', 'male'),
    ]
    
    for q in questions:
        try:
            cursor.execute("INSERT INTO questions (question_text, question_type, subject, difficulty, answer, options, explanation, year, special_type, source, category_id, transcript, language, accent, voice) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", q)
        except Exception as e:
            print(f"  插入英语听力题目失败: {e}")
    
    conn.commit()
    print("  英语听力题目已插入")

def insert_chinese_listening_questions(conn):
    cursor = conn.cursor()
    questions = [
        ('根据听力内容，说话人现在在哪里？', 'listening', '语文', 'easy', 'C', 'A|家里|B|学校|C|医院|D|商场', '说话人提到"医生"和"看病"，说明在医院。', '2026', 'chinese_listening_dialogue', 'system', 23, '女：医生，我最近总是头疼。男：先坐下，我给你检查一下。', 'chinese', 'mandarin', 'female'),
        ('根据听力内容，说话人想要做什么？', 'listening', '语文', 'easy', 'B', 'A|看书|B|借书|C|买书|D|还书', '说话人询问借书流程，说明想要借书。', '2026', 'chinese_listening_dialogue', 'system', 23, '男：您好，请问怎么借书？女：请出示您的借书证，然后在自助机上操作。', 'chinese', 'mandarin', 'male'),
        ('根据听力内容，天气怎么样？', 'listening', '语文', 'easy', 'D', 'A|晴天|B|阴天|C|刮风|D|下雨', '说话人提醒带伞，说明下雨了。', '2026', 'chinese_listening_dialogue', 'system', 23, '女：出门记得带伞，外面下雨了。男：好的，谢谢提醒。', 'chinese', 'mandarin', 'female'),
        ('根据听力内容，他们要去哪里？', 'listening', '语文', 'medium', 'A', 'A|火车站|B|机场|C|汽车站|D|码头', '说话人提到"火车"和"检票"，说明去火车站。', '2026', 'chinese_listening_dialogue', 'system', 23, '男：快点，火车还有半小时就要开了。女：知道了，马上就到检票口了。', 'chinese', 'mandarin', 'male'),
        ('根据听力内容，说话人的职业是什么？', 'listening', '语文', 'medium', 'C', 'A|教师|B|医生|C|服务员|D|警察', '说话人询问点餐，说明是服务员。', '2026', 'chinese_listening_dialogue', 'system', 23, '女：您好，请问要点什么菜？男：给我来一份红烧肉和米饭。', 'chinese', 'mandarin', 'female'),
        ('根据听力内容，这段对话发生在什么时间？', 'listening', '语文', 'medium', 'B', 'A|早上|B|中午|C|晚上|D|深夜', '说话人提到"吃午饭"，说明是中午。', '2026', 'chinese_listening_dialogue', 'system', 23, '男：现在几点了？我有点饿了。女：十二点了，该吃午饭了。', 'chinese', 'mandarin', 'male'),
        ('根据听力内容，说话人是什么关系？', 'listening', '语文', 'medium', 'D', 'A|同事|B|同学|C|朋友|D|师生', '说话人提到"老师"和"作业"，说明是师生关系。', '2026', 'chinese_listening_dialogue', 'system', 23, '女：老师，这是我的作业。男：好的，放这里吧，我等会儿看。', 'chinese', 'mandarin', 'female'),
        ('根据听力内容，说话人为什么迟到了？', 'listening', '语文', 'medium', 'A', 'A|堵车|B|起晚了|C|迷路了|D|有事耽误', '说话人提到"路上堵车"，说明迟到原因是堵车。', '2026', 'chinese_listening_dialogue', 'system', 23, '男：对不起，我迟到了，路上堵车很严重。女：没关系，下次早点出发。', 'chinese', 'mandarin', 'male'),
        ('根据新闻内容，今年的GDP增长目标是多少？', 'listening', '语文', 'hard', 'B', 'A|5%|B|5.5%|C|6%|D|6.5%', '新闻中明确提到今年GDP增长目标为5.5%左右。', '2026', 'chinese_listening_news', 'system', 23, '新闻播报：今年我国经济发展的主要预期目标是，国内生产总值增长5.5%左右；城镇新增就业1100万人以上，城镇调查失业率全年控制在5.5%以内。', 'chinese', 'mandarin', 'male'),
        ('根据新闻内容，我国将采取什么措施促进消费？', 'listening', '语文', 'hard', 'C', 'A|提高税收|B|减少补贴|C|发放消费券|D|限制购买', '新闻中提到将发放消费券促进消费。', '2026', 'chinese_listening_news', 'system', 23, '新闻播报：为了促进消费复苏，多地政府将发放消费券，涵盖餐饮、零售、文旅等多个领域，预计将有效带动居民消费。', 'chinese', 'mandarin', 'female'),
        ('根据短文内容，作者认为读书的意义是什么？', 'listening', '语文', 'hard', 'D', 'A|消磨时间|B|获取文凭|C|结交朋友|D|丰富内心', '作者提到读书可以丰富内心世界。', '2026', 'chinese_listening_passage', 'system', 23, '短文朗读：读书是一种心灵的旅行，它能带我们领略不同的世界，感受不同的人生。通过读书，我们可以丰富自己的内心世界，提升自己的精神境界。', 'chinese', 'mandarin', 'male'),
        ('根据短文内容，什么是成功的关键？', 'listening', '语文', 'hard', 'A', 'A|坚持|B|天赋|C|机遇|D|财富', '短文强调坚持是成功的关键。', '2026', 'chinese_listening_passage', 'system', 23, '短文朗读：成功并非一蹴而就，它需要日复一日的坚持和努力。天赋可以让你起步更快，但只有坚持才能让你走得更远。', 'chinese', 'mandarin', 'female'),
        ('根据古诗朗诵，这首诗的作者是谁？', 'listening', '语文', 'medium', 'B', 'A|李白|B|杜甫|C|王维|D|白居易', '朗诵的是杜甫的《春望》。', '2026', 'chinese_listening_poem', 'system', 23, '古诗朗诵：国破山河在，城春草木深。感时花溅泪，恨别鸟惊心。', 'chinese', 'mandarin', 'male'),
        ('根据古诗朗诵，这首诗表达了什么情感？', 'listening', '语文', 'hard', 'C', 'A|喜悦|B|闲适|C|忧伤|D|愤怒', '《春望》表达了诗人忧国忧民的忧伤情感。', '2026', 'chinese_listening_poem', 'system', 23, '古诗朗诵：大漠孤烟直，长河落日圆。萧关逢候骑，都护在燕然。', 'chinese', 'mandarin', 'female'),
        ('根据听力内容，说话人对这件事的态度是什么？', 'listening', '语文', 'hard', 'A', 'A|支持|B|反对|C|中立|D|怀疑', '说话人表示赞同和支持。', '2026', 'chinese_listening_dialogue', 'system', 23, '男：这个方案很不错，我完全支持。女：太好了，那我们就按照这个方案来实施。', 'chinese', 'mandarin', 'male'),
    ]
    
    for q in questions:
        try:
            cursor.execute("INSERT INTO questions (question_text, question_type, subject, difficulty, answer, options, explanation, year, special_type, source, category_id, transcript, language, accent, voice) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", q)
        except Exception as e:
            print(f"  插入语文听力题目失败: {e}")
    
    conn.commit()
    print("  语文听力题目已插入")

def audit_expansion(conn):
    cursor = conn.cursor()
    print("\n=== 听力题库扩展审计 ===")
    
    cursor.execute("SELECT COUNT(*) FROM questions WHERE question_type = 'listening'")
    total = cursor.fetchone()[0]
    print(f"听力题总数: {total}")
    
    cursor.execute("SELECT subject, COUNT(*) FROM questions WHERE question_type = 'listening' GROUP BY subject")
    result = cursor.fetchall()
    print("\n按科目分布:")
    for row in result:
        print(f"  {row[0]}: {row[1]} 道")
    
    cursor.execute("SELECT special_type, COUNT(*) FROM questions WHERE question_type = 'listening' GROUP BY special_type")
    result = cursor.fetchall()
    print("\n按专项类型分布:")
    for row in result:
        print(f"  {row[0] or '普通'}: {row[1]} 道")

def main():
    print("=== MTSCOS AI 听力题库扩展 ===")
    print("时间:", datetime.now())
    
    conn = sqlite3.connect(DATABASE_PATH)
    
    print("\n1. 添加听力分类...")
    add_listening_categories(conn)
    
    print("\n2. 添加听力标签...")
    add_listening_tags(conn)
    
    print("\n3. 插入日语听力题目...")
    insert_japanese_listening_questions(conn)
    
    print("\n4. 插入英语听力题目...")
    insert_english_listening_questions(conn)
    
    print("\n5. 插入语文听力题目...")
    insert_chinese_listening_questions(conn)
    
    conn.close()
    
    print("\n=== 扩展完成 ===")
    conn = sqlite3.connect(DATABASE_PATH)
    audit_expansion(conn)
    conn.close()

if __name__ == '__main__':
    main()