#!/usr/bin/env python3
"""
扩展听力题库 — 覆盖全部 28 个声音画像
=======================================
在 listening_qbank_build_v2.py 的基础上批量添加新题.
"""
import asyncio, json, sqlite3, subprocess, uuid
from pathlib import Path

_here = Path(__file__).resolve().parent
ROOT = _here.parent
DB = ROOT / "database" / "app.db"
AUDIO_EN = ROOT / "static" / "audio" / "listening" / "en"
AUDIO_JA = ROOT / "static" / "audio" / "listening" / "ja"

# 复用 v2 的 TTS 函数
from listening_qbank_build_v2 import (
    VOICE_PROFILES, tts_say, tts_edge, synthesize
)

print(f"DB: {DB}")
print(f"声音画像: {len(VOICE_PROFILES)}")

# ── 新增英语题 (覆盖剩余画像) ──
# 每个画像至少 1 道, 确保 4 口音 × 男女 全覆盖
MORE_EN = [
    # AM-M-02 (middle/doctor) — 医疗场景
    {"profile_id":"AM-M-02","level":"advanced","type":"short_dialogue","difficulty":4,
     "k12_curriculum":"人教版 高中英语必修三 Unit 2 Healthy Eating",
     "education_reform":"2024 新课标: 生活场景 + 健康话题",
     "transcript":"Good morning Mrs. Johnson. What brings you in today? I've been having persistent headaches for about two weeks now. They seem to get worse in the afternoon. Have you been experiencing any dizziness or blurred vision? No dizziness, but my vision has been slightly blurry when I read for long periods. Let me run a quick neurological exam and order some blood work to rule out any underlying issues.",
     "question":"What symptom prompted Mrs. Johnson to visit the doctor?",
     "options":["A) Dizziness and fainting","B) Persistent headaches for two weeks","C) Blurred vision while driving","D) High blood pressure"],
     "answer":"B","explanation":"'persistent headaches for about two weeks'"},

    # AM-M-03 (senior/teacher) — 历史课独白
    {"profile_id":"AM-M-03","level":"advanced","type":"monologue","difficulty":4,
     "k12_curriculum":"人教版 高中英语选修三 Unit 3 The Million Pound Bank Note",
     "education_reform":"2024 新课标: 文化理解 + 人文素养",
     "transcript":"Good afternoon class. Today we're going to discuss the Industrial Revolution and its impact on American society. The Industrial Revolution began in Great Britain in the late 1700s and gradually spread to the United States by the early 1800s. Before this period, most Americans lived in rural areas and worked as farmers. By 1900, however, nearly 40 percent of Americans lived in cities. This dramatic shift transformed every aspect of American life — from how people worked and lived to how they thought about society and government.",
     "question":"What percentage of Americans lived in cities by 1900?",
     "options":["A) Less than 10 percent","B) About 20 percent","C) Nearly 40 percent","D) Over 60 percent"],
     "answer":"C","explanation":"'nearly 40 percent of Americans lived in cities by 1900'"},

    # AM-M-04 (teen/student) — 校园短对话
    {"profile_id":"AM-M-04","level":"beginner","type":"short_dialogue","difficulty":2,
     "k12_curriculum":"人教版 初中英语七年级 Unit 4 My Day",
     "education_reform":"2024 新课标: 日常交际 + 校园生活",
     "transcript":"Yo Jake, what are you doing this weekend? I'm gonna hit the skate park with some guys from the team. Wanna come? Dude, I'd love to but I got a huge math test on Monday. Mr. Wilson is brutal with algebra. No way to get out of it. That's too bad. We're gonna try that new bowl section. Maybe next weekend then. For sure. Good luck with the test man!",
     "question":"Why can't Jake go to the skate park?",
     "options":["A) He's visiting family","B) He has a math test to study for","C) He's injured","D) His parents won't let him"],
     "answer":"B","explanation":"'I got a huge math test on Monday'"},

    # AM-F-03 (young/sales) — 客服场景
    {"profile_id":"AM-F-03","level":"intermediate","type":"short_dialogue","difficulty":3,
     "k12_curriculum":"人教版 高中英语必修一 Unit 1 Friendship",
     "education_reform":"2024 新课标: 职场场景 + 商务口语",
     "transcript":"Hi there, this is Sarah from Amazon customer service. How can I help you today? Yes, I received a damaged item in my order yesterday. The package looked fine but when I opened it, the product inside was scratched. I'm so sorry to hear that. Let me look up your order. Can I have your order number please? Sure, it's AZW-78234591. Got it. I'll arrange a free replacement to be shipped tomorrow. You can keep the damaged item or dispose of it however you like.",
     "question":"What happened to the customer's order?",
     "options":["A) It was lost in transit","B) It arrived late","C) The product was damaged and scratched","D) The wrong item was sent"],
     "answer":"C","explanation":"'the product inside was scratched'"},

    # AM-F-04 (senior/teacher) — 教学独白
    {"profile_id":"AM-F-04","level":"intermediate","type":"monologue","difficulty":3,
     "k12_curriculum":"人教版 高中英语必修四 Unit 5 Theme Parks",
     "education_reform":"2024 新课标: 教学设计 + 口语教学法",
     "transcript":"Good morning everyone. Before we begin today's lesson, I want to remind you about our speaking activity tomorrow. You'll be working in pairs to give a one minute presentation about your favorite hobby. Remember the three key points we discussed last class: speak clearly, make eye contact, and don't be afraid to make mistakes. The goal is not perfection but communication. I'll be grading you on effort and creativity, not on how many big words you use. Let's start with a warm up exercise.",
     "question":"What will the students do tomorrow?",
     "options":["A) A written exam","B) A one minute pair presentation about hobbies","C) A listening comprehension test","D) A group vocabulary game"],
     "answer":"B","explanation":"'one minute presentation about your favorite hobby'"},

    # BM-M-03 (senior/teacher) — 学术独白
    {"profile_id":"BM-M-03","level":"advanced","type":"monologue","difficulty":5,
     "k12_curriculum":"外研版 高中英语选修九 Unit 1 Biology",
     "education_reform":"2024 新课标: 学术英语 + 批判性思维",
     "transcript":"Good morning ladies and gentlemen. Today I'd like to present the findings of our recent research into climate change and its effects on ocean acidification. As you know, the oceans absorb approximately 30 percent of the carbon dioxide that humans release into the atmosphere. When carbon dioxide dissolves in seawater, it forms carbonic acid, which lowers the pH level of the water. Since the beginning of the Industrial Revolution, ocean pH has dropped by 0.1 on the pH scale, which represents a 26 percent increase in acidity. This has serious implications for marine life, particularly organisms that build shells or skeletons from calcium carbonate.",
     "question":"By how much has ocean pH dropped since the Industrial Revolution?",
     "options":["A) 0.01","B) 0.1","C) 1.0","D) 0.5"],
     "answer":"B","explanation":"'ocean pH has dropped by 0.1'"},

    # BM-F-02 (middle/teacher) — 学校场景
    {"profile_id":"BM-F-02","level":"intermediate","type":"long_dialogue","difficulty":4,
     "k12_curriculum":"外研版 高中英语必修四 Unit 1 Women of Achievement",
     "education_reform":"2024 新课标: 教育场景 + 跨文化交际",
     "transcript":"Morning Helen, how was your half term? Absolutely lovely thank you. We went up to the Lake District for a few days. Did you get much reading done? Actually I did manage to finish that novel we were discussing in the staff book club. What did you think? I absolutely loved it. The ending was so unexpected. I won't spoil it for you but the protagonist's journey is fascinating. I'm glad you enjoyed it. I've only got through chapter three so far. The start is a bit slow but I'm getting into it now.",
     "question":"Where did Helen go during half term?",
     "options":["A) Brighton seaside","B) The Lake District","C) Edinburgh","D) Cornwall"],
     "answer":"B","explanation":"'We went up to the Lake District'"},

    # BM-F-03 (senior/housewife) — 家庭场景
    {"profile_id":"BM-F-03","level":"beginner","type":"short_dialogue","difficulty":2,
     "k12_curriculum":"外研版 初中英语八年级 Module 5 Shopping and Population",
     "education_reform":"2024 新课标: 生活化场景 + 日常交际",
     "transcript":"Dear, could you pop to the shop on your way home? Of course love, what do we need? We're out of bread and milk. Could you also get some eggs and a packet of biscuits for the children? No problem. Anything else? Let me think. Oh yes, a newspaper if they have the evening edition. Right you are. I'll be back around six. Cheerio.",
     "question":"What does the wife ask her husband to buy?",
     "options":["A) Bread, milk, eggs, biscuits, newspaper","B) Just bread and milk","C) Milk, eggs, and bread only","D) A newspaper and some biscuits"],
     "answer":"A","explanation":"bread, milk, eggs, biscuits, newspaper all mentioned"},

    # AU-M-02 (middle/engineer) — 工程场景
    {"profile_id":"AU-M-02","level":"advanced","type":"long_dialogue","difficulty":4,
     "k12_curriculum":"译林版 高中英语必修二 Unit 1 Tales of the Unexplained",
     "education_reform":"2024 新课标: 科技英语 + 职业场景",
     "transcript":"Hey Dave, how's the bridge project going? Bloody hot mate, the concrete's curing slower than expected with this weather. We should have specified a heat resistant mix. Tell me about it. The client is breathing down our necks. They want the northern span done by Friday. No way we'll make that. We're looking at Monday at the earliest. Should I call the client and explain? Yeah, better to be upfront. Offer them a five percent discount on the final bill as compensation. That should smooth things over.",
     "question":"Why is the bridge project delayed?",
     "options":["A) Shortage of workers","B) Weather is too hot, concrete curing slowly","C) Design changes","D) Material delivery problems"],
     "answer":"B","explanation":"'concrete's curing slower than expected with this weather'"},

    # AU-F-02 (middle/doctor) — 医疗场景
    {"profile_id":"AU-F-02","level":"advanced","type":"monologue","difficulty":4,
     "k12_curriculum":"译林版 高中英语选修六 Unit 4 Helping People",
     "education_reform":"2024 新课标: 健康话题 + 公共卫生",
     "transcript":"Good morning everyone. Today I'd like to talk about the importance of regular exercise for maintaining good health. Studies show that adults should aim for at least 150 minutes of moderate physical activity per week. This can include activities like brisk walking, cycling, swimming, or even gardening. Regular exercise helps reduce the risk of heart disease, stroke, type 2 diabetes, and certain types of cancer. It also improves mental health by reducing stress and anxiety. Even small changes like taking the stairs instead of the lift or walking to the local shops can make a significant difference over time.",
     "question":"How much exercise should adults aim for per week?",
     "options":["A) 60 minutes","B) 100 minutes","C) 150 minutes","D) 300 minutes"],
     "answer":"C","explanation":"'at least 150 minutes of moderate physical activity per week'"},

    # IN-M-02 (middle/teacher) — 教育场景
    {"profile_id":"IN-M-02","level":"intermediate","type":"monologue","difficulty":3,
     "k12_curriculum":"人教版 高中英语必修二 Unit 2 The Olympic Games",
     "education_reform":"2024 新课标: 国际理解 + 多元文化",
     "transcript":"Good morning students. Today we will discuss the importance of education in India's development. Did you know that India has the largest education system in the world? With over 1.5 million schools and more than 900 universities, we produce some of the world's largest numbers of engineers, doctors, and scientists. However, we still face challenges. Many rural areas lack access to quality education, and girls' enrollment rates remain lower than boys. The government has launched several initiatives to address these issues, including scholarships and digital learning programs.",
     "question":"What challenge does India still face in education?",
     "options":["A) Too few universities","B) Lack of interest in STEM subjects","C) Rural areas lack quality education and lower girls' enrollment","D) Not enough teachers"],
     "answer":"C","explanation":"'rural areas lack access to quality education, and girls enrollment rates remain lower'"},

    # AU-M-01 (young/driver) — 司机场景
    {"profile_id":"AU-M-01","level":"intermediate","type":"long_dialogue","difficulty":3,
     "k12_curriculum":"译林版 高中英语必修一 Unit 3 Travel Journal",
     "education_reform":"2024 新课标: 服务行业 + 口语多样性",
     "transcript":"G'day mate, where are you headed today? The Opera House please. Got a show to catch. No worries, I'll take the Harbour Bridge route. Should be about 20 minutes with this traffic. How much will that cost ya? About 35 bucks mate. Surge pricing kicked in an hour ago thanks to the soccer match. Fair enough. Hey, is the Opera House walkable from where you drop me? Yeah, I'll drop you right at the entrance. Can't miss it. Thanks cobber, appreciate it.",
     "question":"How much will the taxi ride cost approximately?",
     "options":["A) 20 dollars","B) 35 dollars","C) 50 dollars","D) 15 dollars"],
     "answer":"B","explanation":"'about 35 bucks mate'"},

    # ══ 听写题补充 ══
    {"profile_id":"BM-F-03","level":"beginner","type":"dictation","difficulty":2,
     "k12_curriculum":"外研版 初中英语九年级 Module 4 Home",
     "education_reform":"2024 新课标: 听写能力 + 家庭场景",
     "transcript":"Question one: What time does the film start? Answer: It starts at half past seven. Question two: Where shall we meet? Answer: Let's meet outside the cinema entrance.",
     "question":"Dictation: Write down the two Q and A pairs.",
     "options":[],"answer":"It starts at half past seven. Let's meet outside the cinema entrance.","explanation":"听写完整句子"},
]

# ── 新增日语题 (覆盖剩余画像) ──
MORE_JA = [
    # JA-F-02 (middle/doctor, KANTO) — 医疗场景
    {"profile_id":"JA-F-02","level":"advanced","type":"long_dialogue","difficulty":4,
     "k12_curriculum":"人教版 高中日语选修一 Unit 2 病院",
     "education_reform":"2024 日语课标: 医疗场景 + 敬语",
     "transcript":"すみません、先生。最近、夜眠れなくて困っています。どのくらい続いていますか？三週間ほどです。仕事のストレスが原因かもしれませんね。まずは生活習慣を見直しましょう。毎日決まった時間に寝るようにしてください。また、寝る前にスマホを見るのは控えてください。わかりました。お酒は飲みますか？週に三、四回くらいです。できれば禁酒してみてください。睡眠の質が大きく変わりますよ。",
     "question":"先生はまず何を見直すように指示しましたか？",
     "options":["A) 食生活","B) 生活習慣","C) 仕事量","D) 運動量"],
     "answer":"B","explanation":"「まずは生活習慣を見直しましょう」"},

    # JA-F-04 (middle/housewife, KANSAI) — 关西家庭场景
    {"profile_id":"JA-F-04","level":"advanced","type":"monologue","difficulty":5,
     "k12_curriculum":"人教版 高中日语选修二 Unit 2 家庭",
     "education_reform":"2024 日语课标: 关西方言 + 家庭文化",
     "transcript":"みなさん、こんにちは。今日は京都の家庭料理、おばんざいについてお話しします。おばんざいは、京都の一般家庭で日常的に作られているお惣菜のことです。季節の野菜をたっぷり使って、薄味に仕上げるのが特徴です。代表的なものには、お煮しめ、きんぴらごぼう、ひじきの煮物などがあります。私も毎週日曜日にまとめて作って、一週間分のおかずにしています。体に優しくて、作り置きもできるので、忙しい主婦の強い味方ですわ。",
     "question":"おばんざいの特徴は何ですか？",
     "options":["A) 濃い味付け","B) 季節の野菜を使って薄味","C) 肉中心の料理","D) 冷凍食品"],
     "answer":"B","explanation":"「季節の野菜をたっぷり使って、薄味に仕上げるのが特徴」"},
]

# ── 批量生成 ──
def batch_gen(lang: str, questions: list, table: str):
    import sqlite3 as _sq3, json as _json
    conn = _sq3.connect(str(DB))
    cur = conn.cursor()
    tag_col = "audio_url" if table == "jp_listening" else ""
    jp_extra = ", audio_url, transcript_jp" if table == "jp_listening" else ""
    jp_vals = ", db_audio, transcript" if table == "jp_listening" else ""
    
    print(f"\n{'═'*60}\n 扩展 {lang} ({len(questions)} 道新题)\n{'═'*60}")
    
    for i, q in enumerate(questions):
        profile = next(v for v in VOICE_PROFILES if v["id"] == q["profile_id"])
        tid = f"{lang.upper()}-{uuid.uuid4().hex[:10].upper()}"
        
        transcript = q["transcript"]
        out_dir = AUDIO_EN if lang == "en" else AUDIO_JA
        audio_path, duration = synthesize(profile, transcript, out_dir)
        db_audio = f"/static/audio/listening/{'en' if lang=='en' else 'ja'}/{audio_path.name}"
        
        questions_json = _json.dumps({
            "q_type": q.get("type", "short_dialogue"),
            "question": q["question"],
            "options": q.get("options", []),
            "answer": q["answer"],
            "explanation": q["explanation"]
        }, ensure_ascii=False)
        
        if table == "jp_listening":
            cur.execute("""
                INSERT INTO jp_listening
                (listening_id, title, level, listening_type, accent, speaker_gender,
                 speaker_age_group, speaker_profession, voice_profile_id,
                 audio_path, audio_url, duration_sec, transcript, transcript_jp, transcript_cn, questions_json,
                 tags_json, difficulty, source, quality_score, k12_curriculum, education_reform)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                tid, f"{profile['persona'][:30]}", q["level"], q["type"],
                profile["accent"], profile["gender"], profile["age_group"], profile["profession"],
                profile["id"], db_audio, db_audio, duration, transcript, transcript, "", questions_json,
                _json.dumps(["英语","日语课标","教改2024","扩展"], ensure_ascii=False),
                q["difficulty"], "ai_generated+ext", 0,
                q["k12_curriculum"], q["education_reform"]
            ))
        else:
            cur.execute("""
                INSERT INTO en_listening
                (listening_id, title, level, listening_type, accent, speaker_gender,
                 speaker_age_group, speaker_profession, voice_profile_id,
                 audio_path, duration_sec, transcript, transcript_cn, questions_json,
                 tags_json, difficulty, source, quality_score, k12_curriculum, education_reform)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                tid, f"{profile['persona'][:40]}", q["level"], q["type"],
                profile["accent"], profile["gender"], profile["age_group"], profile["profession"],
                profile["id"], db_audio, duration, transcript, "", questions_json,
                _json.dumps(["K12","英语课标","教改2024","扩展"], ensure_ascii=False),
                q["difficulty"], "ai_generated+ext", 0,
                q["k12_curriculum"], q["education_reform"]
            ))
        
        status = "✅" if duration > 0 else "⚠️"
        print(f"  [{i+1}/{len(questions)}] {status} {tid} {profile['id']:8s} {profile['accent']} {profile['gender']} dur={duration:.1f}s")
    
    conn.commit()
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    cnt = cur.fetchone()[0]
    conn.close()
    print(f"✅ {table}: {cnt} rows total")

print("\n" + "="*60)
print(" 扩展听力题库 — 覆盖所有声音画像")
print("="*60)
batch_gen("en", MORE_EN, "en_listening")
batch_gen("ja", MORE_JA, "jp_listening")

# 最终统计
print(f"\n{'═'*60}\n 最终统计\n{'═'*60}")
import sqlite3 as _sq
conn = _sq.connect(str(DB))
cur = conn.cursor()
for t in ["en_listening", "jp_listening"]:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    total = cur.fetchone()[0]
    cur.execute(f"SELECT accent, speaker_gender, COUNT(*) FROM {t} GROUP BY accent, speaker_gender")
    print(f"\n{t}: {total} 道")
    for r in cur.fetchall(): print(f"  {r[0]:8s} {r[1]}: {r[2]}")
conn.close()
print("\n✅ 扩展完成!")
