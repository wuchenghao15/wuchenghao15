#!/usr/bin/env python3
import os
from gtts import gTTS
import hashlib

audio_dir = os.path.join(os.path.dirname(__file__), 'app', 'static', 'audio')
os.makedirs(audio_dir, exist_ok=True)

questions = [
    {
        'id': 'q1',
        'content': 'M: Good morning! How can I help you today? W: I would like to book a flight to New York.',
        'options': ['The man is booking a flight.', 'The woman wants to go to New York.', 'They are at the airport.',
        'It is afternoon now.'],
        'lang': 'en'
    },
    {
        'id': 'q2',
        'content': '私は鈴木です。大阪出身です。大学生です。',
        'options': ['鈴木さんは東京出身です。', '鈴木さんは大学生です。', '鈴木さんは仕事をしています。', '鈴木さんは絵を描くのが好きです。'],
        'lang': 'ja'
    },
    {
        'id': 'q3',
        'content': 'Good evening. Tomorrow will be sunny with a high of 28 degrees Celsius.',
        'options': ['Tomorrow will be rainy.', 'The high temperature is 28C.', 'Winds will be from the west.',
        'It is morning now.'],
        'lang': 'en'
    },
    {
        'id': 'q4',
        'content': '明日は晴れです。最高気温は二十五度です。',
        'options': ['明日は雨です。', '最高気温は30度です。', '最低気温は15度です。', '風が強いです。'],
        'lang': 'ja'
    },
    {
        'id': 'q5',
        'content': 'W: Hello, this is the restaurant. M: Yes, I would like to book a table for two.',
        'options': ['They are in a restaurant.', 'The man is booking a table.', 'The woman is a waiter.',
        'The man wants pizza.'],
        'lang': 'en'
    },
    {
        'id': 'q6',
        'content': '今は午後三時です。会議は午後四時からです。',
        'options': ['今は午後四時です。', '会議は三時からです。', 'まだ一時間あります。', '会議はもう終わりました。'],
        'lang': 'ja'
    },
    {
        'id': 'q7',
        'content': 'Scientists have discovered a new species of bird in the Amazon rainforest.',
        'options': ['The bird is black.', 'It was found in Africa.', 'The bird has blue feathers.',
        'Scientists found a new mammal.'],
        'lang': 'en'
    },
    {
        'id': 'q8',
        'content': '来週、東京に旅行に行きます。友達と一緒です。',
        'options': ['東京に一人で行きます。', 'バスで行きます。', '友達と一緒に行きます。', '今週旅行に行きます。'],
        'lang': 'ja'
    },
    {
        'id': 'q9',
        'content': 'M: Excuse me, where is the library? W: It is on the second floor, next to the computer lab.',
        'options': ['The library is on the first floor.', 'The library is next to the lab.', 'There is no elevator.',
        'They are in a mall.'],
        'lang': 'en'
    },
    {
        'id': 'q10',
        'content': 'M: Hello, this is John speaking. W: I am sorry, she is not in right now.',
        'options': ['John is calling Sarah.', 'Sarah is calling John.', 'John is leaving a message.',
        'Sarah is not available.'],
        'lang': 'en'
    }
]

generated_files = []

for q in questions:
    try:
        tts = gTTS(text=q['content'], lang=q['lang'], slow=False)
        content_hash = hashlib.md5(q['content'].encode()).hexdigest()[:10]
        content_file = f'audio_{q["id"]}_content.mp3'
        content_path = os.path.join(audio_dir, content_file)
        tts.save(content_path)
        generated_files.append(content_file)
        logger.info(f"✓ 生成 {content_file} ({q['lang']})")
    except Exception as e:
        logger.info(f"✗ 生成内容失败 {q['id']}: {e}")
    
    for i, opt in enumerate(q['options']):
        try:
            tts = gTTS(text=opt, lang=q['lang'], slow=False)
            opt_hash = hashlib.md5(opt.encode()).hexdigest()[:10]
            opt_file = f'audio_{q["id"]}_option_{chr(65+i)}.mp3'
            opt_path = os.path.join(audio_dir, opt_file)
            tts.save(opt_path)
            generated_files.append(opt_file)
            logger.info(f"  ✓ 选项 {chr(65+i)}")
        except Exception as e:
            logger.info(f"  ✗ 选项 {chr(65+i)} 失败: {e}")

logger.info(f"\n共生成 {len(generated_files)} 个音频文件")

with open(os.path.join(audio_dir, 'audio_list.json'), 'w', encoding='utf-8') as f:
    import json
    json.dump(generated_files, f, ensure_ascii=False, indent=2)

















