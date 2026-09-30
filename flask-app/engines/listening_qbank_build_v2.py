#!/usr/bin/env python3
"""
英语/日语听力题库 v2 — 修复版 (显式 transcript + 完整对话)
========================================================

修复: Python dict 重复 key 导致多轮对话被覆盖的问题.
每道题显式提供 transcript 字段, TTS 用它.

依赖: say (macOS 自带), edge_tts (已装)
"""
import asyncio, json, os, re, sqlite3, subprocess, uuid
from pathlib import Path
from datetime import datetime

_here = Path(__file__).resolve().parent
if (_here.parent / "database" / "app.db").exists():
    DB = _here.parent / "database" / "app.db"
else:
    DB = Path(__file__).resolve().parent.parent.parent / "flask-app" / "database" / "app.db"
ROOT = _here.parent
AUDIO_EN = ROOT / "static" / "audio" / "listening" / "en"
AUDIO_JA = ROOT / "static" / "audio" / "listening" / "ja"
print(f"DB: {DB} (exists={DB.exists()})")
for d in [AUDIO_EN, AUDIO_JA]:
    d.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# 1. 声音画像矩阵 (13男:15女 = 28 个画像)
# ═══════════════════════════════════════════════════════════════
VOICE_PROFILES = [
    # ══════ 英语 美式 AM (4M+4F=8) ══════
    {"id":"AM-M-01","gender":"M","accent":"AM","age_group":"young","profession":"engineer",
     "say_voice":"Eddy (英语（美国）)","edge_voice":"en-US-GuyNeural",
     "persona":"28岁硅谷软件工程师, 语速快, tech术语多"},
    {"id":"AM-M-02","gender":"M","accent":"AM","age_group":"middle","profession":"doctor",
     "say_voice":"Fred","edge_voice":"en-US-GregNeural",
     "persona":"45岁纽约医生, 稳重清晰"},
    {"id":"AM-M-03","gender":"M","accent":"AM","age_group":"senior","profession":"teacher",
     "say_voice":"Grandpa (英语（美国）)","edge_voice":"en-US-KevinNeural",
     "persona":"62岁退休历史教师, 语速慢有故事感"},
    {"id":"AM-M-04","gender":"M","accent":"AM","age_group":"teen","profession":"student",
     "say_voice":"Junior","edge_voice":"en-US-GuyNeural",
     "persona":"14岁美国初中生, 语速快, 俚语"},
    {"id":"AM-F-01","gender":"F","accent":"AM","age_group":"young","profession":"anchor",
     "say_voice":"Flo (英语（美国）)","edge_voice":"en-US-AvaNeural",
     "persona":"26岁CNN新闻主播, 标准清晰"},
    {"id":"AM-F-02","gender":"F","accent":"AM","age_group":"middle","profession":"housewife",
     "say_voice":"Kathy","edge_voice":"en-US-JennyNeural",
     "persona":"38岁家庭主妇, 温暖亲切"},
    {"id":"AM-F-03","gender":"F","accent":"AM","age_group":"young","profession":"sales",
     "say_voice":"Samantha","edge_voice":"en-US-SaraNeural",
     "persona":"29岁亚马逊客服, 友好高效"},
    {"id":"AM-F-04","gender":"F","accent":"AM","age_group":"senior","profession":"teacher",
     "say_voice":"Grandma (英语（美国）)","edge_voice":"en-US-AriaNeural",
     "persona":"58岁高中英语老师, 语速稍慢清晰"},

    # ══════ 英语 英式 BM (3M+3F=6) ══════
    {"id":"BM-M-01","gender":"M","accent":"BM","age_group":"young","profession":"engineer",
     "say_voice":"Daniel (英语（英国）)","edge_voice":"en-GB-RyanNeural",
     "persona":"30岁伦敦程序员, 清晰 RP 口音"},
    {"id":"BM-M-02","gender":"M","accent":"BM","age_group":"middle","profession":"doctor",
     "say_voice":"Reed (英语（英国）)","edge_voice":"en-GB-OliverNeural",
     "persona":"48岁NHS医生, 稳重"},
    {"id":"BM-M-03","gender":"M","accent":"BM","age_group":"senior","profession":"teacher",
     "say_voice":"Grandpa (英语（英国）)","edge_voice":"en-GB-AlfieNeural",
     "persona":"65岁退休牛津教授"},
    {"id":"BM-F-01","gender":"F","accent":"BM","age_group":"young","profession":"anchor",
     "say_voice":"Flo (英语（英国）)","edge_voice":"en-GB-SoniaNeural",
     "persona":"25岁BBC主播, 标准RP"},
    {"id":"BM-F-02","gender":"F","accent":"BM","age_group":"middle","profession":"teacher",
     "say_voice":"Shelley (英语（英国）)","edge_voice":"en-GB-MiaNeural",
     "persona":"42岁伦敦中学老师"},
    {"id":"BM-F-03","gender":"F","accent":"BM","age_group":"senior","profession":"housewife",
     "say_voice":"Grandma (英语（英国）)","edge_voice":"en-GB-ElizabethNeural",
     "persona":"60岁退休护士, 温暖"},

    # ══════ 英语 澳式 AU (2M+2F=4) ══════
    {"id":"AU-M-01","gender":"M","accent":"AU","age_group":"young","profession":"driver",
     "say_voice":"Karen","edge_voice":"en-AU-WilliamMultilingualNeural",
     "persona":"32岁悉尼出租车司机, 澳式口音明显"},
    {"id":"AU-M-02","gender":"M","accent":"AU","age_group":"middle","profession":"engineer",
     "say_voice":"Karen","edge_voice":"en-AU-WilliamMultilingualNeural",
     "persona":"41岁墨尔本工程师"},
    {"id":"AU-F-01","gender":"F","accent":"AU","age_group":"young","profession":"sales",
     "say_voice":"Karen","edge_voice":"en-AU-NatashaNeural",
     "persona":"27岁布里斯班销售员"},
    {"id":"AU-F-02","gender":"F","accent":"AU","age_group":"middle","profession":"doctor",
     "say_voice":"Karen","edge_voice":"en-AU-NatashaNeural",
     "persona":"45岁悉尼医生"},

    # ══════ 英语 印度 IN (2M+2F=4) ══════
    {"id":"IN-M-01","gender":"M","accent":"IN","age_group":"young","profession":"engineer",
     "say_voice":"Aman (英语（印度）)","edge_voice":"en-IN-PrabhatNeural",
     "persona":"29岁班加罗尔软件工程师, 印度英语口音"},
    {"id":"IN-M-02","gender":"M","accent":"IN","age_group":"middle","profession":"teacher",
     "say_voice":"Rishi","edge_voice":"en-IN-PrabhatNeural",
     "persona":"40岁新德里英语老师"},
    {"id":"IN-F-01","gender":"F","accent":"IN","age_group":"young","profession":"anchor",
     "say_voice":"Tara","edge_voice":"en-IN-NeerjaNeural",
     "persona":"26岁孟买电台主播"},
    {"id":"IN-F-02","gender":"F","accent":"IN","age_group":"middle","profession":"doctor",
     "say_voice":"Tara","edge_voice":"en-IN-NeerjaNeural",
     "persona":"42岁阿格拉医生"},

    # ══════ 日语 关东 KANTO (1M+2F=3) ══════
    {"id":"JA-M-01","gender":"M","accent":"KANTO","age_group":"young","profession":"engineer",
     "say_voice":"Eddy (日语（日本）)","edge_voice":"ja-JP-KeitaNeural",
     "persona":"28岁东京IT工程师, 标准关东腔"},
    {"id":"JA-F-01","gender":"F","accent":"KANTO","age_group":"young","profession":"teacher",
     "say_voice":"Flo (日语（日本）)","edge_voice":"ja-JP-NanamiNeural",
     "persona":"25岁东京中学老师"},
    {"id":"JA-F-02","gender":"F","accent":"KANTO","age_group":"middle","profession":"doctor",
     "say_voice":"Kyoko","edge_voice":"ja-JP-NanamiNeural",
     "persona":"45岁东京医院医生"},

    # ══════ 日语 关西 KANSAI (1M+2F=3) ══════
    {"id":"JA-M-02","gender":"M","accent":"KANSAI","age_group":"young","profession":"driver",
     "say_voice":"Rocko (日语（日本）)","edge_voice":"ja-JP-KeitaNeural",
     "persona":"30岁大阪出租车司机, 关西腔"},
    {"id":"JA-F-03","gender":"F","accent":"KANSAI","age_group":"young","profession":"sales",
     "say_voice":"Sandy (日语（日本）)","edge_voice":"ja-JP-NanamiNeural",
     "persona":"26岁大阪百货销售员"},
    {"id":"JA-F-04","gender":"F","accent":"KANSAI","age_group":"middle","profession":"housewife",
     "say_voice":"Shelley (日语（日本）)","edge_voice":"ja-JP-NanamiNeural",
     "persona":"42岁京都家庭主妇"},
]

MALE = sum(1 for v in VOICE_PROFILES if v["gender"] == "M")
FEMALE = sum(1 for v in VOICE_PROFILES if v["gender"] == "F")
print(f"声音画像: {len(VOICE_PROFILES)} 个 (男 {MALE}:女 {FEMALE} = {MALE/FEMALE:.2f}:1)")

# ═══════════════════════════════════════════════════════════════
# 2. 建表 (同 v1, 不重复)
# ═══════════════════════════════════════════════════════════════
SCHEMA_EN = """
CREATE TABLE IF NOT EXISTS en_listening (
    listening_id       TEXT PRIMARY KEY,
    title              TEXT NOT NULL,
    level              TEXT NOT NULL,
    listening_type     TEXT NOT NULL,
    accent             TEXT NOT NULL,
    speaker_gender     TEXT NOT NULL,
    speaker_age_group  TEXT NOT NULL,
    speaker_profession TEXT NOT NULL,
    voice_profile_id   TEXT NOT NULL,
    audio_path         TEXT NOT NULL,
    duration_sec       INTEGER DEFAULT 0,
    transcript         TEXT NOT NULL,
    transcript_cn      TEXT,
    questions_json     TEXT NOT NULL,
    tags_json          TEXT,
    difficulty         INTEGER DEFAULT 3,
    source             TEXT DEFAULT "ai_generated",
    quality_score      REAL DEFAULT 0,
    k12_curriculum     TEXT,
    education_reform   TEXT,
    created_at         TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_en_listening_accent ON en_listening(accent);
CREATE INDEX IF NOT EXISTS idx_en_listening_level ON en_listening(level);
CREATE INDEX IF NOT EXISTS idx_en_listening_gender ON en_listening(speaker_gender);

CREATE TABLE IF NOT EXISTS jp_listening (
    listening_id       TEXT PRIMARY KEY,
    title              TEXT NOT NULL,
    level              TEXT NOT NULL,
    listening_type     TEXT NOT NULL,
    accent             TEXT NOT NULL,
    speaker_gender     TEXT NOT NULL,
    speaker_age_group  TEXT NOT NULL,
    speaker_profession TEXT NOT NULL,
    voice_profile_id   TEXT NOT NULL,
    audio_path         TEXT NOT NULL,
    duration_sec       INTEGER DEFAULT 0,
    transcript         TEXT NOT NULL,
    transcript_cn      TEXT,
    questions_json     TEXT NOT NULL,
    tags_json          TEXT,
    difficulty         INTEGER DEFAULT 3,
    source             TEXT DEFAULT "ai_generated",
    quality_score      REAL DEFAULT 0,
    k12_curriculum     TEXT,
    education_reform   TEXT,
    created_at         TEXT DEFAULT (datetime('now','localtime')),
    audio_url          TEXT,
    transcript_jp      TEXT
);
CREATE INDEX IF NOT EXISTS idx_jp_listening_accent ON jp_listening(accent);
"""

def init_db():
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.executescript(SCHEMA_EN)
    conn.commit()
    conn.close()
    print(f"✅ DB schema 初始化完成")

init_db()

# ═══════════════════════════════════════════════════════════════
# 3. TTS Pipeline
# ═══════════════════════════════════════════════════════════════
def tts_say(text: str, voice: str, out_path: Path) -> float:
    """macOS say 生成 .m4a (AAC), 返回秒数"""
    raw_aac = out_path.with_suffix('.aac')
    result = subprocess.run(
        ["say", "-v", voice, "-o", str(raw_aac), text],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  ❌ say 失败 (voice={voice}): {result.stderr[:120]}")
        return 0.0
    if raw_aac.exists():
        raw_aac.rename(out_path)
    size = out_path.stat().st_size if out_path.exists() else 0
    return round(size / 16000, 1) if size > 0 else 0.0

async def tts_edge(text: str, voice: str, out_path: Path) -> float:
    """edge_tts 生成 MP3"""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_path))
    size = out_path.stat().st_size if out_path.exists() else 0
    return round(size / 16000, 1) if size > 0 else 0.0

def synthesize(profile: dict, text: str, out_dir: Path) -> tuple[Path, float]:
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{profile['id']}_{uuid.uuid4().hex[:6]}.m4a"
    out_path = out_dir / fname
    
    # 1. 优先 macOS say (离线零 token)
    dur = tts_say(text, profile['say_voice'], out_path)
    if dur > 0:
        return out_path, dur
    
    # 2. Fallback edge_tts
    try:
        dur = asyncio.run(tts_edge(text, profile['edge_voice'], out_path))
        if dur > 0:
            return out_path, dur
    except Exception as e:
        print(f"  ⚠️ edge_tts 也失败: {e}")
    
    return out_path, 0.0

print("\n✅ TTS pipeline 就绪")

# ═══════════════════════════════════════════════════════════════
# 4. 题目库 — 每道题显式提供 transcript (完整对话文本)
# ═══════════════════════════════════════════════════════════════
# 数据结构: transcript 是 TTS 和听力用的完整文本
#          conversations 是可选的对话分段 (用于前端分角色显示)

EN_QUESTIONS = [
    # 🗣️ 美式英语 · AM
    {"profile_id":"AM-M-01","level":"intermediate","type":"short_dialogue","difficulty":3,
     "k12_curriculum":"人教版 高中英语必修二 Unit 3 Travel Journal",
     "education_reform":"2024 新课标: 听说先行, 真实场景",
     "transcript":"(phone ringing) Hi, this is David from the engineering team. Hey David! I was just about to call you about the server migration. Perfect timing. We found a critical bug this morning. Can we push the deployment to next Tuesday? Tuesday works, but we need the QA sign off by Monday EOD. I'll email the team now. Thanks, you're a lifesaver.",
     "conversations":[("David (M)","(phone ringing) Hi, this is David from the engineering team."),
                      ("Team Lead (F)","Hey David! I was just about to call you about the server migration."),
                      ("David (M)","Perfect timing. We found a critical bug this morning. Can we push the deployment to next Tuesday?"),
                      ("Team Lead (F)","Tuesday works, but we need the QA sign off by Monday EOD. I'll email the team now."),
                      ("David (M)","Thanks, you're a lifesaver.")],
     "question":"Why are they delaying the server migration?",
     "options":["A) Budget cuts","B) Critical bug found","C) Team vacation","D) Hardware failure"],
     "answer":"B","explanation":"David says 'We found a critical bug this morning'"},

    {"profile_id":"AM-F-01","level":"advanced","type":"monologue","difficulty":4,
     "k12_curriculum":"人教版 高中英语选修六 Unit 2 News Media",
     "education_reform":"2024 新课标: 媒体素养 + 批判性听力",
     "transcript":"Breaking news from CNN headquarters. A major tech company announced layoffs of 12,000 employees worldwide, citing restructuring and AI automation as primary factors. The CEO stated this would streamline operations and make the company more competitive in the AI era. However, labor unions have already announced protests in three major cities. Share prices dropped 8 percent in after hours trading. We'll have live coverage from our correspondent in San Francisco at 7 PM Eastern.",
     "question":"What is the main reason for the layoffs according to the CEO?",
     "options":["A) Economic recession","B) AI automation and restructuring","C) Competition from rivals","D) Regulatory fines"],
     "answer":"B","explanation":"CEO cited 'restructuring and AI automation as primary factors'"},

    {"profile_id":"AM-M-02","level":"advanced","type":"long_dialogue","difficulty":4,
     "k12_curriculum":"人教版 高中英语必修四 Unit 4 Body Language",
     "education_reform":"2024 新课标: 职场真实场景 + 跨文化交际",
     "transcript":"Good morning everyone. Let me start with today's agenda. First, we need to review the Q3 sales figures. Second, the new product launch timeline. And third, customer feedback from last week's focus group. Before we dive in, I want to welcome Sarah who just joined our team from the Chicago office. Welcome Sarah! Thanks David. I'm excited to be here. I brought some initial thoughts on the product launch based on my experience with the Midwest market. Great, we'd love to hear those at the end. Let's begin with the sales numbers.",
     "conversations":[("David (M)","Good morning everyone. Let me start with today's agenda..."),
                      ("Sarah (F)","Thanks David. I'm excited to be here...")],
     "question":"What is the first item on the meeting agenda?",
     "options":["A) Product launch timeline","B) Q3 sales figures review","C) Customer feedback","D) Welcome new employee"],
     "answer":"B","explanation":"'First, we need to review the Q3 sales figures'"},

    {"profile_id":"AM-F-02","level":"intermediate","type":"monologue","difficulty":3,
     "k12_curriculum":"人教版 初中英语八年级 Unit 5 What are the shirts made of?",
     "education_reform":"2024 新课标: 生活化场景 + 家庭口语",
     "transcript":"Hi honey, I picked up the groceries on my way home. The store had a special on organic milk, so I got two cartons. Also, your favorite blueberry muffins were fresh today. I stopped at the dry cleaners too, your winter coat is ready. Oh and I met our new neighbor from across the street. She seems really nice, works at the elementary school down the road.",
     "question":"Where does the new neighbor work?",
     "options":["A) At a hospital","B) At an elementary school","C) At the grocery store","D) At the bank"],
     "answer":"B","explanation":"'works at the elementary school down the road'"},

    # 🗣️ 英式英语 · BM
    {"profile_id":"BM-M-01","level":"intermediate","type":"short_dialogue","difficulty":3,
     "k12_curriculum":"外研版 高中英语必修五 Unit 3 Life in the Future",
     "education_reform":"2024 新课标: 国际理解 + 跨文化交际",
     "transcript":"Cheers mate, fancy a pint after work? Sounds great, but I've got a report to finish for tomorrow's standup. No worries, how about Friday then? The new Wetherspoons just opened on Tottenham Court Road. Perfect, I'll book a table. What time? Let's say half past six. Bring your mate from HR too.",
     "conversations":[("Guy A (M)","Cheers mate, fancy a pint after work?"),
                      ("Guy B (M)","Sounds great, but I've got a report..."),
                      ("Guy A (M)","No worries, how about Friday then?")],
     "question":"When will they go to the pub?",
     "options":["A) Tonight","B) Tomorrow","C) Friday","D) Saturday"],
     "answer":"C","explanation":"'how about Friday then'"},

    {"profile_id":"BM-F-01","level":"advanced","type":"long_dialogue","difficulty":4,
     "k12_curriculum":"外研版 高中英语选修七 Unit 4 Public Transport",
     "education_reform":"2024 新课标: 环保话题 + 政策理解",
     "transcript":"Good evening Londoners. The Tube strikes are entering their third day. Which lines are affected today? Northern, Central and Piccadilly lines have severe delays. Overground services are running but expect disruptions. TfL recommends working from home if possible. What's the union's latest statement? They're demanding a 7 percent pay rise and better pensions. Talks are scheduled for tomorrow at ACAS. The Mayor has urged both sides to find a resolution. Thank you for that update. We'll bring you live reports throughout the evening.",
     "question":"What does the union primarily want?",
     "options":["A) Shorter working hours","B) 7 percent pay rise and better pensions","C) New uniforms","D) Longer holidays"],
     "answer":"B","explanation":"'demanding a 7 percent pay rise and better pensions'"},

    {"profile_id":"BM-M-02","level":"advanced","type":"long_dialogue","difficulty":4,
     "k12_curriculum":"外研版 高中英语选修六 Unit 1 Small Talk",
     "education_reform":"2024 新课标: 社交听力 + 真实语境",
     "transcript":"I say, did you catch the match last night? Absolutely thrilling! Couldn't watch it live unfortunately. What was the final score? Three two to United. They equalised in the 87th minute! Pandemonium at Old Trafford. Goodness gracious. Who scored the winner? Rashford, with a stunning volley. The lad's on fire this season. I must say, the refereeing was questionable throughout. Oh absolutely, but let's not sour the moment. That was vintage United.",
     "question":"Who scored the winning goal?",
     "options":["A) Fernandes","B) Rashford","C) Garnacho","D) Hojlund"],
     "answer":"B","explanation":"'Rashford, with a stunning volley'"},

    # 🗣️ 澳式英语 · AU
    {"profile_id":"AU-M-01","level":"intermediate","type":"short_dialogue","difficulty":3,
     "k12_curriculum":"译林版 高中英语必修三 Unit 3 Back to the Past",
     "education_reform":"2024 新课标: 地域文化 + 口语多样性",
     "transcript":"G'day mate, where's the nearest servo? I'm running low on petrol. Mate, there's one up the road about five clicks. Can't miss it, big red sign. Fair dinkum? Yeah sweet, cheers cobber. No worries, she'll be right. By the way, you from outta town? Yeah, just got here from Melbourne. First time in Sydney? Nah, been up a few times. Love it here.",
     "question":"What is a 'servo' in Australian English?",
     "options":["A) A restaurant","B) A gas station","C) A police station","D) A shopping mall"],
     "answer":"B","explanation":"澳洲英语 servo = service station = gas station"},

    {"profile_id":"AU-F-01","level":"advanced","type":"monologue","difficulty":4,
     "k12_curriculum":"译林版 高中英语选修八 Unit 1 The World of Our Senses",
     "education_reform":"2024 新课标: 环境话题 + 本土案例",
     "transcript":"Bushfire season has arrived early in Australia this year. The Rural Fire Service has issued a catastrophic fire danger warning for parts of New South Wales. Over two thousand firefighters are currently deployed. Residents in high risk areas have been told to prepare their bushfire survival plans. Authorities say temperatures could reach 42 degrees Celsius tomorrow with winds gusting to 60 kilometres per hour. Please stay safe and follow all evacuation orders.",
     "question":"What danger level has been issued for parts of NSW?",
     "options":["A) Warning","B) Watch and Act","C) Emergency","D) Catastrophic"],
     "answer":"D","explanation":"'catastrophic fire danger warning'"},

    # 🗣️ 印度英语 · IN
    {"profile_id":"IN-M-01","level":"intermediate","type":"short_dialogue","difficulty":3,
     "k12_curriculum":"人教版 高中英语必修一 Unit 1 Friendship",
     "education_reform":"2024 新课标: 全球化 + 多样性理解",
     "transcript":"Namaste Sir, I have completed the project report you asked for. Excellent work Rahul. The charts are very clear. Can you email it to the client by EOD? Sure Sir, I will send it right away. Should I follow up with a phone call? Yes please, and make sure to copy Priya from the design team. Very good Sir, I will do that now. Also Rahul, good job on the client meeting yesterday. The feedback was very positive. Thank you Sir, the team worked very hard on this.",
     "conversations":[("Rahul (M)","Namaste Sir, I have completed the project report..."),
                      ("Manager (M)","Excellent work Rahul..."),
                      ("Rahul (M)","Sure Sir...")],
     "question":"What should Rahul do after sending the email?",
     "options":["A) Go home","B) Call the client","C) Meet Priya","D) Print the report"],
     "answer":"B","explanation":"Manager says 'follow up with a phone call'"},

    {"profile_id":"IN-F-01","level":"advanced","type":"monologue","difficulty":4,
     "k12_curriculum":"人教版 高中英语选修九 Unit 2 India",
     "education_reform":"2024 新课标: 国际理解 + 多元文化",
     "transcript":"Welcome to today's India news. The Indian Space Research Organisation has successfully launched its Chandrayaan 3 mission to the Moon. The lander will touch down near the lunar south pole, a region where water ice deposits were recently discovered. This makes India the fourth nation to achieve a soft landing on the Moon. Prime Minister Modi congratulated the ISRO team, calling it a historic moment for the country. Thousands gathered at the ISRO headquarters in Bangalore to celebrate this milestone.",
     "question":"What makes Chandrayaan 3 significant?",
     "options":["A) First mission to Moon","B) First landing on lunar south pole","C) Fourth nation to soft land on Moon","D) Carries the heaviest payload"],
     "answer":"C","explanation":"'fourth nation to achieve a soft landing on the Moon'"},

    {"profile_id":"IN-F-02","level":"advanced","type":"monologue","difficulty":5,
     "k12_curriculum":"人教版 高中英语必修五 Unit 5 The Power of Nature",
     "education_reform":"2024 新课标: 环境 + 国际合作",
     "transcript":"The G20 summit concluded yesterday with a historic agreement on climate change. All 20 nations committed to tripling renewable energy capacity by 2030. India's Prime Minister highlighted that developing nations need technology transfer and financial support to meet these ambitious targets. The agreement also includes a 300 billion dollar fund for climate adaptation in vulnerable countries. This marks a major shift from previous summits where developed nations were reluctant to commit.",
     "question":"What did India request during the summit?",
     "options":["A) More trade deals","B) Technology transfer and financial support","C) Permanent UN seat","D) Reduction in carbon targets"],
     "answer":"B","explanation":"'developing nations need technology transfer and financial support'"},

    # 🗣️ 听写题
    {"profile_id":"AM-F-02","level":"intermediate","type":"dictation","difficulty":3,
     "k12_curriculum":"人教版 初中英语八年级 Unit 5 What are the shirts made of?",
     "education_reform":"2024 新课标: 听写能力 + 工业话题",
     "transcript":"Question one: What are the shirts made of? Answer: They are made of cotton. Question two: Where are they produced? Answer: They are produced in Thailand.",
     "question":"Dictation: Write down the two Q and A pairs you hear.",
     "options":[],"answer":"They are made of cotton. Produced in Thailand.","explanation":"听写完整句子"},
]

JA_QUESTIONS = [
    # 🗣️ 关东腔 (标准日语)
    {"profile_id":"JA-M-01","level":"intermediate","type":"short_dialogue","difficulty":3,
     "k12_curriculum":"人教版 高中日语必修一 Unit 3 買い物",
     "education_reform":"2024 日语课标: 实用场景 + 购物会话",
     "transcript":"すみません、この靴はいくらですか？はい、これは29800円です。今日はセール中で20パーセントオフになっています。じゃあ、いくらになりますか？23840円です。ポイントカードはお持ちですか？あります。これでお願いします。ありがとうございました。また来てください。",
     "conversations":[("客 (M)","すみません、この靴はいくらですか？"),
                      ("店員 (F)","はい、これは29800円です..."),
                      ("客 (M)","じゃあ、いくらになりますか？"),
                      ("店員 (F)","23840円です...")],
     "question":"靴のセール価格はいくらですか？",
     "options":["A) 29800円","B) 23840円","C) 20000円","D) 5960円"],
     "answer":"B","explanation":"29800円 × 0.8 = 23840円"},

    {"profile_id":"JA-F-01","level":"advanced","type":"monologue","difficulty":4,
     "k12_curriculum":"人教版 高中日语选修一 Unit 5 環境問題",
     "education_reform":"2024 日语课标: 环境话题 + 国际理解",
     "transcript":"皆さん、本日は気候変動についてお話しします。日本の平均気温は過去100年で約1度上昇しました。このままでは、2050年までにさらに2度上昇すると予測されています。特に夏の猛暑日は年々増えており、熱中症による死亡者も増加傾向にあります。私たち一人ひとりが節電やごみの分別など、身近なことから始めることが大切です。政府も来年度から新しい環境対策を実施する予定です。",
     "question":"日本の平均気温は過去100年でどれだけ上昇しましたか？",
     "options":["A) 約0.5度","B) 約1度","C) 約2度","D) 約3度"],
     "answer":"B","explanation":"「過去100年で約1度上昇」"},

    # 🗣️ 关西腔 (大阪弁)
    {"profile_id":"JA-M-02","level":"intermediate","type":"short_dialogue","difficulty":4,
     "k12_curriculum":"人教版 高中日语必修二 Unit 4 食事",
     "education_reform":"2024 日语课标: 方言多样性 + 文化理解",
     "transcript":"おいおい、このラーメン屋、まだやってんのか？ああ、あの河童ラーメンか？あそこ、去年改装してめっちゃ綺麗になったで。ほう、そうなんか。味は変わってへんの？変わってへんで。いつものあっさり系。でも値上げして1杯850円になったわ。まあまあ、大阪やししゃあない。今度連れて行ってな。",
     "conversations":[("男A (M)","おいおい、このラーメン屋、まだやってんのか？"),
                      ("男B (M)","ああ、あの河童ラーメンか？..."),
                      ("男A (M)","ほう、そうなんか。味は変わってへんの？"),
                      ("男B (M)","変わってへんで...")],
     "question":"ラーメン屋の値段はいくらになった？",
     "options":["A) 650円","B) 750円","C) 850円","D) 950円"],
     "answer":"C","explanation":"「値上げして1杯850円になったわ」"},

    {"profile_id":"JA-F-03","level":"advanced","type":"long_dialogue","difficulty":5,
     "k12_curriculum":"人教版 高中日语选修二 Unit 3 ビジネス",
     "education_reform":"2024 日语课标: 商务日语 + 关西企业文化",
     "transcript":"すみません、田中さん。来月の出張の件ですが。ああ、京都の顧客訪問やな。例の老舗和菓子屋さんの件？はい。先方の社長さんが直接会いたいっておっしゃってて。ほな、俺も行くわ。やっぱり関西の商売は顔つなぎが大切やさかい。お願いします。交通費は会社で出しますので。あほか、交通費なんか自分で出すわ。そんなんで会社に請求するなんて恥ずかしいやろ。",
     "conversations":[("部下 (F)","すみません、田中さん。来月の出張の件ですが。"),
                      ("田中 (M)","ああ、京都の顧客訪問やな..."),
                      ("部下 (F)","はい。先方の社長さんが..."),
                      ("田中 (M)","ほな、俺も行くわ...")],
     "question":"出張先はどこですか？",
     "options":["A) 大阪","B) 京都","C) 神戸","D) 奈良"],
     "answer":"B","explanation":"「京都の顧客訪問やな」"},
]

# ═══════════════════════════════════════════════════════════════
# 5. 生成 Pipeline
# ═══════════════════════════════════════════════════════════════

def gen_en():
    print(f"\n{'═'*60}\n 英语题库生成 ({len(EN_QUESTIONS)} 道)\n{'═'*60}")
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    
    for i, q in enumerate(EN_QUESTIONS):
        profile = next(v for v in VOICE_PROFILES if v["id"] == q["profile_id"])
        tid = f"EN-{uuid.uuid4().hex[:10].upper()}"
        
        transcript = q["transcript"]
        audio_path, duration = synthesize(profile, transcript, AUDIO_EN)
        db_audio = f"/static/audio/listening/en/{audio_path.name}"
        
        questions_json = json.dumps({
            "q_type": q.get("type", "short_dialogue"),
            "question": q["question"],
            "conversations": q.get("conversations", []),
            "options": q.get("options", []),
            "answer": q["answer"],
            "explanation": q["explanation"]
        }, ensure_ascii=False)
        
        cur.execute("""
            INSERT OR REPLACE INTO en_listening
            (listening_id, title, level, listening_type, accent, speaker_gender,
             speaker_age_group, speaker_profession, voice_profile_id,
             audio_path, duration_sec, transcript, transcript_cn, questions_json,
             tags_json, difficulty, source, quality_score, k12_curriculum, education_reform)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            tid, f"{profile['persona'][:40]}", q["level"], q["type"],
            profile["accent"], profile["gender"], profile["age_group"], profile["profession"],
            profile["id"], db_audio, duration, transcript, "", questions_json,
            json.dumps(["K12", "英语课标", "教改2024"], ensure_ascii=False),
            q["difficulty"], "ai_generated+pipeline_v2", 0,
            q["k12_curriculum"], q["education_reform"]
        ))
        
        tag = "✅" if duration > 0 else "⚠️"
        print(f"  [{i+1}/{len(EN_QUESTIONS)}] {tag} {tid} {profile['id']:8s} {profile['accent']:4s} {profile['gender']} dur={duration:5.1f}s")
    
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM en_listening")
    cnt = cur.fetchone()[0]
    conn.close()
    print(f"\n✅ en_listening: {cnt} rows")

def gen_ja():
    print(f"\n{'═'*60}\n 日语题库生成 ({len(JA_QUESTIONS)} 道)\n{'═'*60}")
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    
    for i, q in enumerate(JA_QUESTIONS):
        profile = next(v for v in VOICE_PROFILES if v["id"] == q["profile_id"])
        tid = f"JA-{uuid.uuid4().hex[:10].upper()}"
        
        transcript = q["transcript"]
        audio_path, duration = synthesize(profile, transcript, AUDIO_JA)
        db_audio = f"/static/audio/listening/ja/{audio_path.name}"
        
        questions_json = json.dumps({
            "q_type": q.get("type", "short_dialogue"),
            "question": q["question"],
            "conversations": q.get("conversations", []),
            "options": q.get("options", []),
            "answer": q["answer"],
            "explanation": q["explanation"]
        }, ensure_ascii=False)
        
        cur.execute("""
            INSERT OR REPLACE INTO jp_listening
            (listening_id, title, level, listening_type, accent, speaker_gender,
             speaker_age_group, speaker_profession, voice_profile_id,
             audio_path, audio_url, duration_sec, transcript, transcript_jp, transcript_cn, questions_json,
             tags_json, difficulty, source, quality_score, k12_curriculum, education_reform)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            tid, f"{profile['persona'][:30]}", q["level"], q["type"],
            profile["accent"], profile["gender"], profile["age_group"], profile["profession"],
            profile["id"], db_audio, db_audio, duration, transcript, transcript, "", questions_json,
            json.dumps(["日本語", "日语课标", "教改2024"], ensure_ascii=False),
            q["difficulty"], "ai_generated+pipeline_v2", 0,
            q["k12_curriculum"], q["education_reform"]
        ))
        
        tag = "✅" if duration > 0 else "⚠️"
        print(f"  [{i+1}/{len(JA_QUESTIONS)}] {tag} {tid} {profile['id']:8s} {profile['accent']:6s} {profile['gender']} dur={duration:5.1f}s")
    
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM jp_listening")
    cnt = cur.fetchone()[0]
    conn.close()
    print(f"\n✅ jp_listening: {cnt} rows")

# 跑之前先清空旧数据 (可选, 保留的话用 INSERT OR REPLACE)
if __name__ == '__main__':
    # ⚠️ 先删除旧的 v1 数据, 避免 ID 重复
    conn_cleanup = sqlite3.connect(str(DB))
    cur_cleanup = conn_cleanup.cursor()
    cur_cleanup.execute("DELETE FROM en_listening")
    cur_cleanup.execute("DELETE FROM jp_listening")
    conn_cleanup.commit()
    conn_cleanup.close()
    print("\n🧹 已清空旧数据, 重新生成...")

    gen_en()
    gen_ja()

    # 验证
    print(f"\n{'═'*60}\n 最终验证\n{'═'*60}")
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()

    cur.execute("SELECT accent, COUNT(*) FROM en_listening GROUP BY accent")
    print("\n英语 按口音分布:")
    for row in cur.fetchall(): print(f"  {row[0]:6s}: {row[1]}")
    cur.execute("SELECT speaker_gender, COUNT(*) FROM en_listening GROUP BY speaker_gender")
    print("英语 按性别分布:", dict(cur.fetchall()))
    cur.execute("SELECT listening_type, COUNT(*) FROM en_listening GROUP BY listening_type")
    print("英语 按题型分布:", dict(cur.fetchall()))

    cur.execute("SELECT accent, COUNT(*) FROM jp_listening GROUP BY accent")
    print("\n日语 按口音分布:")
    for row in cur.fetchall(): print(f"  {row[0]:6s}: {row[1]}")
    cur.execute("SELECT speaker_gender, COUNT(*) FROM jp_listening GROUP BY speaker_gender")
    print("日语 按性别分布:", dict(cur.fetchall()))
    cur.execute("SELECT listening_type, COUNT(*) FROM jp_listening GROUP BY listening_type")
    print("日语 按题型分布:", dict(cur.fetchall()))

    # Transcript 完整性检查
    cur.execute("SELECT accent, length(transcript), duration_sec FROM en_listening ORDER BY RANDOM() LIMIT 3")
    print("\nSample EN transcripts (accent | 长度 | 时长):")
    for r in cur.fetchall(): print(f"  {r[0]} | {r[1]} chars | {r[2]}s")

    cur.execute("SELECT accent, length(transcript), duration_sec FROM jp_listening ORDER BY RANDOM() LIMIT 3")
    print("\nSample JA transcripts:")
    for r in cur.fetchall(): print(f"  {r[0]} | {r[1]} chars | {r[2]}s")

    conn.close()

    print(f"\n音频文件:")
    print(f"  en: {len(list(AUDIO_EN.glob('*.m4a')))} 个")
    print(f"  ja: {len(list(AUDIO_JA.glob('*.m4a')))} 个")
    print("\n✅ Pipeline v2 完成!")
