# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
初始化发音素材数据
包含英语26字母、日语50音图等基础发音素材
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.sound_engineer_ai import SoundEngineerAI
from scripts.init_pronunciation_db import init_pronunciation_database

def init_basic_pronunciation_data():
    print("================================================")
    print("初始化基础发音素材数据")
    print("================================================")
    
    # 初始化数据库
    init_pronunciation_database()
    
    ai = SoundEngineerAI()
    
    # 创建音频目录结构
    create_audio_directories()
    
    # 添加英语发音素材
    print("\n1. 添加英语发音素材...")
    add_english_pronunciation(ai)
    
    # 添加日语发音素材
    print("\n2. 添加日语发音素材...")
    add_japanese_pronunciation(ai)
    
    # 添加音频组合规则
    print("\n3. 添加音频组合规则...")
    add_composition_rules(ai)
    
    # 统计信息
    stats = ai.get_statistics()
    print("\n================================================")
    print("初始化完成!")
    print(f"英语发音素材: {stats['english_pronunciation_count']}")
    print(f"日语发音素材: {stats['japanese_pronunciation_count']}")
    print(f"组合规则: {stats['active_rules_count']}")
    print("================================================")

def create_audio_directories():
    """创建音频文件目录结构"""
    directories = [
        'audio/materials/english/uk/female',
        'audio/materials/english/uk/male',
        'audio/materials/english/us/female',
        'audio/materials/english/us/male',
        'audio/materials/english/africa/female',
        'audio/materials/english/africa/male',
        'audio/materials/english/india/female',
        'audio/materials/english/india/male',
        'audio/materials/japanese/kanto/female',
        'audio/materials/japanese/kanto/male',
        'audio/materials/japanese/kansai/female',
        'audio/materials/japanese/kansai/male',
        'audio/composed/english',
        'audio/composed/japanese'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # 创建占位文件
        placeholder = os.path.join(directory, '.placeholder')
        with open(placeholder, 'w') as f:
            f.write('')

def add_english_pronunciation(ai):
    """添加英语发音素材"""
    accents = ['uk', 'us', 'africa', 'india']
    voices = ['female', 'male']
    
    # 英语26字母
    letters = 'abcdefghijklmnopqrstuvwxyz'
    
    for accent in accents:
        for voice in voices:
            for letter in letters:
                file_path = f"audio/materials/english/{accent}/{voice}/{letter}.wav"
                ai.add_pronunciation_material(
                    language='english',
                    type_='letter',
                    content=letter,
                    accent=accent,
                    voice=voice,
                    file_path=file_path,
                    phonetic=f"/{letter}/"
                )
    
    print(f"  ✓ 26字母发音素材 ({len(accents)}口音 × {len(voices)}音色)")
    
    # 常用单词
    common_words = [
        'hello', 'world', 'thank', 'you', 'good', 'morning', 'afternoon', 'evening',
        'yes', 'no', 'please', 'sorry', 'welcome', 'goodbye', 'see', 'you',
        'how', 'are', 'you', 'what', 'is', 'your', 'name', 'my', 'name', 'is'
    ]
    
    for accent in accents:
        for voice in voices:
            for word in common_words:
                file_path = f"audio/materials/english/{accent}/{voice}/{word}.wav"
                ai.add_pronunciation_material(
                    language='english',
                    type_='word',
                    content=word,
                    accent=accent,
                    voice=voice,
                    file_path=file_path
                )
    
    print(f"  ✓ {len(common_words)}常用单词发音素材")
    
    # 数字
    numbers = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
    
    for accent in accents:
        for voice in voices:
            for num in numbers:
                file_path = f"audio/materials/english/{accent}/{voice}/{num}.wav"
                ai.add_pronunciation_material(
                    language='english',
                    type_='number',
                    content=num,
                    accent=accent,
                    voice=voice,
                    file_path=file_path
                )
    
    print(f"  ✓ {len(numbers)}数字发音素材")

def add_japanese_pronunciation(ai):
    """添加日语发音素材"""
    accents = ['kanto', 'kansai']
    voices = ['female', 'male']
    
    # 日语50音图 - 平假名
    hiragana = [
        'あ', 'い', 'う', 'え', 'お',
        'か', 'き', 'く', 'け', 'こ',
        'さ', 'し', 'す', 'せ', 'そ',
        'た', 'ち', 'つ', 'て', 'と',
        'な', 'に', 'ぬ', 'ね', 'の',
        'は', 'ひ', 'ふ', 'へ', 'ほ',
        'ま', 'み', 'む', 'め', 'も',
        'や', 'ゆ', 'よ',
        'ら', 'り', 'る', 'れ', 'ろ',
        'わ', 'を', 'ん'
    ]
    
    # 片假名
    katakana = [
        'ア', 'イ', 'ウ', 'エ', 'オ',
        'カ', 'キ', 'ク', 'ケ', 'コ',
        'サ', 'シ', 'ス', 'セ', 'ソ',
        'タ', 'チ', 'ツ', 'テ', 'ト',
        'ナ', 'ニ', 'ヌ', 'ネ', 'ノ',
        'ハ', 'ヒ', 'フ', 'ヘ', 'ホ',
        'マ', 'ミ', 'ム', 'メ', 'モ',
        'ヤ', 'ユ', 'ヨ',
        'ラ', 'リ', 'ル', 'レ', 'ロ',
        'ワ', 'ヲ', 'ン'
    ]
    
    # 拗音
    youon_hiragana = [
        'きゃ', 'きゅ', 'きょ',
        'しゃ', 'しゅ', 'しょ',
        'ちゃ', 'ちゅ', 'ちょ',
        'にゃ', 'にゅ', 'にょ',
        'ひゃ', 'ひゅ', 'ひょ',
        'みゃ', 'みゅ', 'みょ',
        'りゃ', 'りゅ', 'りょ',
        'ぎゃ', 'ぎゅ', 'ぎょ',
        'じゃ', 'じゅ', 'じょ',
        'びゃ', 'びゅ', 'びょ',
        'ぴゃ', 'ぴゅ', 'ぴょ'
    ]
    
    # 促音(单独处理)
    sokuon = ['っ']
    
    for accent in accents:
        for voice in voices:
            # 添加50音图平假名
            for i, char in enumerate(hiragana):
                file_path = f"audio/materials/japanese/{accent}/{voice}/{char}.wav"
                ai.add_pronunciation_material(
                    language='japanese',
                    type_='hiragana',
                    content=char,
                    accent=accent,
                    voice=voice,
                    file_path=file_path,
                    hiragana=char,
                    katakana=katakana[i] if i < len(katakana) else '',
                    romaji=get_romaji(char)
                )
            
            # 添加片假名
            for char in katakana:
                file_path = f"audio/materials/japanese/{accent}/{voice}/{char}.wav"
                ai.add_pronunciation_material(
                    language='japanese',
                    type_='katakana',
                    content=char,
                    accent=accent,
                    voice=voice,
                    file_path=file_path,
                    katakana=char
                )
            
            # 添加拗音
            for char in youon_hiragana:
                file_path = f"audio/materials/japanese/{accent}/{voice}/{char}.wav"
                ai.add_pronunciation_material(
                    language='japanese',
                    type_='youon',
                    content=char,
                    accent=accent,
                    voice=voice,
                    file_path=file_path,
                    hiragana=char
                )
            
            # 添加促音
            for char in sokuon:
                file_path = f"audio/materials/japanese/{accent}/{voice}/{char}.wav"
                ai.add_pronunciation_material(
                    language='japanese',
                    type_='sokuon',
                    content=char,
                    accent=accent,
                    voice=voice,
                    file_path=file_path,
                    hiragana=char
                )
    
    print(f"  ✓ 50音图发音素材 ({len(accents)}口音 × {len(voices)}音色)")
    print(f"  ✓ {len(youon_hiragana)}拗音发音素材")
    print(f"  ✓ 促音发音素材")
    
    # 添加常用日语词汇
    common_japanese_words = [
        ('こんにちは', 'コンニチハ', 'konnichiwa'),
        ('ありがとう', 'アリガトウ', 'arigatou'),
        ('すみません', 'スミマセン', 'sumimasen'),
        ('はい', 'ハイ', 'hai'),
        ('いいえ', 'イイエ', 'iie'),
        ('おはよう', 'オハヨウ', 'ohayou'),
        ('こんばんは', 'コンバンハ', 'konbanwa'),
        ('さようなら', 'サヨウナラ', 'sayounara'),
        ('おやすみ', 'オヤスミ', 'oyasumi'),
        ('あお', 'アオ', 'ao'),
        ('きいろ', 'キイロ', 'kiiro'),
        ('あか', 'アカ', 'aka'),
        ('くろ', 'クロ', 'kuro'),
        ('しろ', 'シロ', 'shiro')
    ]
    
    for accent in accents:
        for voice in voices:
            for hiragana, katakana, romaji in common_japanese_words:
                file_path = f"audio/materials/japanese/{accent}/{voice}/{hiragana}.wav"
                ai.add_pronunciation_material(
                    language='japanese',
                    type_='word',
                    content=hiragana,
                    accent=accent,
                    voice=voice,
                    file_path=file_path,
                    hiragana=hiragana,
                    katakana=katakana,
                    romaji=romaji
                )
    
    print(f"  ✓ {len(common_japanese_words)}常用日语词汇发音素材")

def get_romaji(hiragana):
    """获取平假名对应的罗马音"""
    romaji_map = {
        'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
        'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
        'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
        'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
        'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
        'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
        'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
        'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
        'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
        'わ': 'wa', 'を': 'o', 'ん': 'n'
    }
    return romaji_map.get(hiragana, '')

def add_composition_rules(ai):
    """添加音频组合规则"""
    # 英语组合规则
    english_rules = [
        ('word_segmentation', r'[\w]+', 1, '单词分割规则'),
        ('punctuation_pause', r'[.,!?;]', 2, '标点符号停顿规则'),
        ('capitalization_stress', r'^[A-Z]', 3, '首字母大写重读规则'),
        ('plural_form', r's$|es$', 4, '复数形式发音规则'),
        ('past_tense', r'ed$', 5, '过去式发音规则')
    ]
    
    for name, pattern, priority, desc in english_rules:
        ai.add_composition_rule('english', name, pattern, priority, desc)
    
    # 日语组合规则
    japanese_rules = [
        ('youon_detection', r'[きしちにひみりぎじぢびみ][ゃゅょ]', 1, '拗音检测规则'),
        ('sokuon_detection', r'っ[かきくけこさしすせそたちつてとはひふへほ]', 2, '促音检测规则'),
        ('chouon_detection', r'ああ|いい|うう|ええ|おお', 3, '长音检测规则'),
        ('particle_rules', r'は|が|を|に|で|と|から|まで', 4, '助词发音规则'),
        ('katakana_emphasis', r'[アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン]+', 5, '片假名强调规则')
    ]
    
    for name, pattern, priority, desc in japanese_rules:
        ai.add_composition_rule('japanese', name, pattern, priority, desc)
    
    print(f"  ✓ {len(english_rules)}条英语组合规则")
    print(f"  ✓ {len(japanese_rules)}条日语组合规则")

if __name__ == '__main__':
    init_basic_pronunciation_data()