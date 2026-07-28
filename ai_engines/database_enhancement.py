#!/usr/bin/env python3
"""
MTSCOS AI 数据库增强脚本 v7.2.0
====================================
为16个分库添加增强表结构：
- 移动端配置表
- 通知推送队列表
- 用户设备表
- 系统配置扩展表
"""

import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLIT_DB_DIR = os.path.join(BASE_DIR, 'split_databases')

def execute_sql(db_path, sql, params=None):
    """执行SQL语句"""
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"  ✗ SQL执行失败: {e}")
        return False

def enhance_system_db():
    """增强系统数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'system.db')
    print("\n[系统数据库增强]")
    
    # 移动端配置表
    print("  - 创建移动端配置表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS mobile_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE NOT NULL,
            config_value TEXT,
            description TEXT,
            category TEXT DEFAULT 'mobile',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 通知推送队列表
    print("  - 创建通知推送队列表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS notification_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_id INTEGER,
            recipient_type TEXT DEFAULT 'user',
            title TEXT,
            content TEXT,
            priority INTEGER DEFAULT 10,
            status TEXT DEFAULT 'pending',
            push_type TEXT DEFAULT 'system',
            device_id TEXT,
            sent_at TEXT,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 用户设备表
    print("  - 创建用户设备表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS user_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            device_id TEXT UNIQUE NOT NULL,
            device_type TEXT DEFAULT 'mobile',
            device_name TEXT,
            os_type TEXT,
            os_version TEXT,
            app_version TEXT,
            push_token TEXT,
            last_active_at TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 初始化移动端配置默认数据
    print("  - 初始化移动端配置默认数据...")
    default_configs = [
        ('mobile_enabled', '1', '是否启用移动端支持', 'mobile'),
        ('mobile_viewport', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no', '移动端viewport配置', 'mobile'),
        ('mobile_theme', 'default', '移动端默认主题', 'mobile'),
        ('mobile_push_enabled', '1', '是否启用移动端推送', 'mobile'),
        ('mobile_cache_timeout', '3600', '移动端缓存超时时间(秒)', 'mobile'),
        ('mobile_max_upload_size', '10485760', '移动端最大上传大小(字节)', 'mobile'),
        ('mobile_login_expire_days', '7', '移动端登录过期天数', 'mobile'),
        ('mobile_offline_mode', '1', '是否支持离线模式', 'mobile'),
    ]
    
    for key, value, desc, category in default_configs:
        execute_sql(db_path, '''
            INSERT OR IGNORE INTO mobile_config (config_key, config_value, description, category)
            VALUES (?, ?, ?, ?)
        ''', (key, value, desc, category))
    
    print("  ✓ 系统数据库增强完成")

def enhance_auth_db():
    """增强认证数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'auth.db')
    print("\n[认证数据库增强]")
    
    # 用户登录日志表
    print("  - 创建用户登录日志表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            ip_address TEXT,
            user_agent TEXT,
            device_type TEXT,
            login_status TEXT DEFAULT 'success',
            login_time TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 多因素认证表
    print("  - 创建多因素认证表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS mfa_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            mfa_type TEXT,
            secret TEXT,
            enabled INTEGER DEFAULT 0,
            verified INTEGER DEFAULT 0,
            backup_codes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("  ✓ 认证数据库增强完成")

def enhance_question_db():
    """增强题库数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'question.db')
    print("\n[题库数据库增强]")
    
    # 题库分类扩展表
    print("  - 创建题库分类扩展表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS question_categories_ext (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            category_name TEXT,
            parent_id INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            subject TEXT,
            education_stage TEXT DEFAULT 'k12',
            grade TEXT,
            semester TEXT,
            total_questions INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 题目标签表
    print("  - 创建题目标签表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS question_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_name TEXT UNIQUE NOT NULL,
            tag_color TEXT DEFAULT '#3B82F6',
            usage_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 题目标签关联表
    print("  - 创建题目标签关联表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS question_tag_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            tag_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(question_id, tag_id)
        )
    ''')
    
    # 语文听写词库表
    print("  - 创建语文听写词库表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS chinese_dictation_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL,
            pinyin TEXT,
            meaning TEXT,
            difficulty_level TEXT DEFAULT '小学低年级',
            frequency INTEGER DEFAULT 1,
            usage_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 语文成语词库表
    print("  - 创建语文成语词库表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS chinese_dictation_idioms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idiom TEXT UNIQUE NOT NULL,
            pinyin TEXT,
            meaning TEXT,
            difficulty_level TEXT DEFAULT '小学低年级',
            usage_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 语文古诗词库表
    print("  - 创建语文古诗词库表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS chinese_dictation_poetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            dynasty TEXT,
            content TEXT,
            difficulty_level TEXT DEFAULT '小学低年级',
            usage_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 语文读文选段表
    print("  - 创建语文读文选段表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS chinese_dictation_passages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            keywords TEXT,
            difficulty_level TEXT DEFAULT '小学低年级',
            word_count INTEGER DEFAULT 0,
            usage_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 语文听力题目表
    print("  - 创建语文听力题目表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS chinese_listening_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT UNIQUE,
            type TEXT,
            category TEXT,
            sub_category TEXT,
            difficulty TEXT,
            content TEXT,
            correct_answer TEXT,
            explanation TEXT,
            analysis TEXT,
            tags TEXT,
            knowledge_points TEXT,
            score REAL DEFAULT 5.0,
            language TEXT DEFAULT 'chinese',
            accent TEXT DEFAULT 'mandarin',
            voice TEXT DEFAULT 'female',
            dictation_text TEXT,
            pinyin TEXT,
            meaning TEXT,
            level TEXT,
            title TEXT,
            author TEXT,
            dynasty TEXT,
            full_content TEXT,
            keywords TEXT,
            is_active INTEGER DEFAULT 1,
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 初始化题库分类数据
    print("  - 初始化题库分类数据...")
    categories = [
        ('成人教育-语文', 0, 1, '语文', 'adult', '', '', 0),
        ('成人教育-数学', 0, 1, '数学', 'adult', '', '', 0),
        ('成人教育-英语', 0, 1, '英语', 'adult', '', '', 0),
        ('成人教育-政治', 0, 1, '政治', 'adult', '', '', 0),
        ('成人教育-历史', 0, 1, '历史', 'adult', '', '', 0),
        ('成人教育-地理', 0, 1, '地理', 'adult', '', '', 0),
        ('成人教育-物理', 0, 1, '物理', 'adult', '', '', 0),
        ('成人教育-化学', 0, 1, '化学', 'adult', '', '', 0),
        ('成人教育-生物', 0, 1, '生物', 'adult', '', '', 0),
        ('K12-语文-小学', 0, 1, '语文', 'k12', '小学', '', 0),
        ('K12-语文-初中', 0, 1, '语文', 'k12', '初中', '', 0),
        ('K12-语文-高中', 0, 1, '语文', 'k12', '高中', '', 0),
        ('K12-数学-小学', 0, 1, '数学', 'k12', '小学', '', 0),
        ('K12-数学-初中', 0, 1, '数学', 'k12', '初中', '', 0),
        ('K12-数学-高中', 0, 1, '数学', 'k12', '高中', '', 0),
        ('K12-英语-小学', 0, 1, '英语', 'k12', '小学', '', 0),
        ('K12-英语-初中', 0, 1, '英语', 'k12', '初中', '', 0),
        ('K12-英语-高中', 0, 1, '英语', 'k12', '高中', '', 0),
        ('K12-物理-初中', 0, 1, '物理', 'k12', '初中', '', 0),
        ('K12-物理-高中', 0, 1, '物理', 'k12', '高中', '', 0),
        ('K12-化学-初中', 0, 1, '化学', 'k12', '初中', '', 0),
        ('K12-化学-高中', 0, 1, '化学', 'k12', '高中', '', 0),
        ('K12-生物-初中', 0, 1, '生物', 'k12', '初中', '', 0),
        ('K12-生物-高中', 0, 1, '生物', 'k12', '高中', '', 0),
        ('K12-历史-初中', 0, 1, '历史', 'k12', '初中', '', 0),
        ('K12-历史-高中', 0, 1, '历史', 'k12', '高中', '', 0),
        ('K12-地理-初中', 0, 1, '地理', 'k12', '初中', '', 0),
        ('K12-地理-高中', 0, 1, '地理', 'k12', '高中', '', 0),
        ('K12-政治-初中', 0, 1, '政治', 'k12', '初中', '', 0),
        ('K12-政治-高中', 0, 1, '政治', 'k12', '高中', '', 0),
        ('语文听力-词语听写', 0, 1, '语文', 'k12', '', '', 0),
        ('语文听力-成语听写', 0, 1, '语文', 'k12', '', '', 0),
        ('语文听力-古诗词听写', 0, 1, '语文', 'k12', '', '', 0),
        ('语文听力-读文选段听写', 0, 1, '语文', 'k12', '', '', 0),
    ]
    
    for name, parent_id, level, subject, stage, grade, semester, count in categories:
        execute_sql(db_path, '''
            INSERT OR IGNORE INTO question_categories_ext (category_name, parent_id, level, subject, education_stage, grade, semester, total_questions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, parent_id, level, subject, stage, grade, semester, count))
    
    # 初始化语文听写词库数据
    print("  - 初始化语文听写词库数据...")
    words = [
        ('天空', 'tiān kōng', '地球周围的广阔空间', '小学低年级'),
        ('大海', 'dà hǎi', '广阔的海洋', '小学低年级'),
        ('高山', 'gāo shān', '高耸的山峰', '小学低年级'),
        ('河流', 'hé liú', '流水的河道', '小学低年级'),
        ('树木', 'shù mù', '木本植物的通称', '小学低年级'),
        ('花朵', 'huā duǒ', '花的总称', '小学低年级'),
        ('太阳', 'tài yáng', '太阳系的中心天体', '小学低年级'),
        ('月亮', 'yuè liàng', '地球的天然卫星', '小学低年级'),
        ('星星', 'xīng xīng', '夜空中闪烁发光的天体', '小学低年级'),
        ('彩虹', 'cǎi hóng', '雨后天空中的弧形光带', '小学低年级'),
        ('美丽', 'měi lì', '好看、漂亮', '小学低年级'),
        ('快乐', 'kuài lè', '感到幸福或满意', '小学低年级'),
        ('勇敢', 'yǒng gǎn', '有勇气、不怕困难', '小学低年级'),
        ('聪明', 'cōng ming', '智力发达、思维敏捷', '小学低年级'),
        ('善良', 'shàn liáng', '心地纯洁、待人友好', '小学低年级'),
        ('认真', 'rèn zhēn', '严肃对待、不马虎', '小学低年级'),
        ('努力', 'nǔ lì', '把力量尽量使出来', '小学低年级'),
        ('团结', 'tuán jié', '为了共同目标而联合', '小学低年级'),
        ('友爱', 'yǒu ài', '友好亲爱', '小学低年级'),
        ('诚实', 'chéng shí', '言行一致、不虚伪', '小学低年级'),
        ('清澈', 'qīng chè', '清净透明', '小学高年级'),
        ('挺拔', 'tǐng bá', '直立而高耸', '小学高年级'),
        ('茁壮', 'zhuó zhuàng', '健壮成长', '小学高年级'),
        ('绚丽', 'xuàn lì', '灿烂美丽', '小学高年级'),
        ('巍峨', 'wēi é', '高大雄伟', '小学高年级'),
        ('蜿蜒', 'wān yán', '曲折延伸', '小学高年级'),
        ('朦胧', 'méng lóng', '模糊不清', '小学高年级'),
        ('静谧', 'jìng mì', '安静祥和', '小学高年级'),
        ('奔腾', 'bēn téng', '奔跑跳跃', '小学高年级'),
        ('翱翔', 'áo xiáng', '在空中回旋地飞', '小学高年级'),
        ('智慧', 'zhì huì', '辨析判断、发明创造的能力', '初中'),
        ('毅力', 'yì lì', '坚强持久的意志', '初中'),
        ('信念', 'xìn niàn', '自己认为可以确信的看法', '初中'),
        ('奋斗', 'fèn dòu', '为了达到目标而努力', '初中'),
        ('拼搏', 'pīn bó', '使出全部力量搏斗', '初中'),
        ('进取', 'jìn qǔ', '努力向前', '初中'),
        ('创新', 'chuàng xīn', '创造新的', '初中'),
        ('探索', 'tàn suǒ', '多方寻求答案', '初中'),
        ('实践', 'shí jiàn', '实行、履行', '初中'),
        ('合作', 'hé zuò', '互相配合做某事', '初中'),
        ('卓越', 'zhuó yuè', '非常优秀、超出一般', '高中'),
        ('深邃', 'shēn suì', '深奥、深刻', '高中'),
        ('睿智', 'ruì zhì', '英明有远见', '高中'),
        ('坚毅', 'jiān yì', '坚定而有毅力', '高中'),
        ('豁达', 'huò dá', '心胸开阔、性格开朗', '高中'),
        ('谦逊', 'qiān xùn', '谦虚恭谨', '高中'),
        ('严谨', 'yán jǐn', '严密谨慎', '高中'),
        ('勤奋', 'qín fèn', '努力学习或工作', '高中'),
        ('专注', 'zhuān zhù', '集中注意力', '高中'),
        ('追求', 'zhuī qiú', '努力求索', '高中'),
    ]
    
    for word, pinyin, meaning, difficulty in words:
        execute_sql(db_path, '''
            INSERT OR IGNORE INTO chinese_dictation_words (word, pinyin, meaning, difficulty_level)
            VALUES (?, ?, ?, ?)
        ''', (word, pinyin, meaning, difficulty))
    
    # 初始化语文成语词库数据
    print("  - 初始化语文成语词库数据...")
    idioms = [
        ('一心一意', 'yī xīn yī yì', '专心致志，没有别的念头', '小学低年级'),
        ('五颜六色', 'wǔ yán liù sè', '形容色彩繁多', '小学低年级'),
        ('千军万马', 'qiān jūn wàn mǎ', '形容兵马众多，声势浩大', '小学低年级'),
        ('山清水秀', 'shān qīng shuǐ xiù', '形容山水风景优美', '小学低年级'),
        ('鸟语花香', 'niǎo yǔ huā xiāng', '形容春天美好景象', '小学低年级'),
        ('百花齐放', 'bǎi huā qí fàng', '形容百花盛开，丰富多彩', '小学低年级'),
        ('万紫千红', 'wàn zǐ qiān hóng', '形容百花齐放，色彩艳丽', '小学低年级'),
        ('春暖花开', 'chūn nuǎn huā kāi', '春天气候温暖，百花盛开', '小学低年级'),
        ('风和日丽', 'fēng hé rì lì', '形容天气晴朗暖和', '小学低年级'),
        ('欢天喜地', 'huān tiān xǐ dì', '形容非常高兴', '小学低年级'),
        ('津津有味', 'jīn jīn yǒu wèi', '形容兴味浓厚', '小学高年级'),
        ('孜孜不倦', 'zī zī bù juàn', '形容勤奋努力，不知疲倦', '小学高年级'),
        ('精益求精', 'jīng yì qiú jīng', '已经很好了，还要求更好', '小学高年级'),
        ('脚踏实地', 'jiǎo tà shí dì', '形容做事踏实认真', '小学高年级'),
        ('持之以恒', 'chí zhī yǐ héng', '长久坚持下去', '小学高年级'),
        ('勤学好问', 'qín xué hào wèn', '勤奋学习，乐于提问', '小学高年级'),
        ('诚实守信', 'chéng shí shǒu xìn', '言行一致，遵守信用', '小学高年级'),
        ('乐于助人', 'lè yú zhù rén', '乐于帮助别人', '小学高年级'),
        ('团结友爱', 'tuán jié yǒu ài', '互相团结，彼此友爱', '小学高年级'),
        ('自强不息', 'zì qiáng bù xī', '自己努力向上，永不停息', '小学高年级'),
        ('锲而不舍', 'qiè ér bù shě', '比喻有恒心，有毅力', '初中'),
        ('坚持不懈', 'jiān chí bù xiè', '坚持到底，毫不松懈', '初中'),
        ('迎难而上', 'yíng nán ér shàng', '面对困难不退缩', '初中'),
        ('勇攀高峰', 'yǒng pān gāo fēng', '勇敢攀登最高的山峰', '初中'),
        ('志存高远', 'zhì cún gāo yuǎn', '志向远大', '初中'),
        ('胸怀大志', 'xiōng huái dà zhì', '心中有远大的志向', '初中'),
        ('博学多才', 'bó xué duō cái', '学识渊博，多才多艺', '初中'),
        ('德才兼备', 'dé cái jiān bèi', '品德和才能都具备', '初中'),
        ('出类拔萃', 'chū lèi bá cuì', '超出同类之上', '初中'),
        ('开拓创新', 'kāi tuò chuàng xīn', '开辟新道路，创造新事物', '初中'),
        ('高瞻远瞩', 'gāo zhān yuǎn zhǔ', '眼光远大', '高中'),
        ('博大精深', 'bó dà jīng shēn', '形容思想和学识广博高深', '高中'),
        ('厚积薄发', 'hòu jī bó fā', '长期积累，突然爆发', '高中'),
        ('审时度势', 'shěn shí duó shì', '观察时机，估量形势', '高中'),
        ('运筹帷幄', 'yùn chóu wéi wò', '形容善于谋划', '高中'),
        ('决胜千里', 'jué shèng qiān lǐ', '形容指挥若定，取得胜利', '高中'),
        ('励精图治', 'lì jīng tú zhì', '振奋精神，努力治理', '高中'),
        ('求真务实', 'qiú zhēn wù shí', '追求真实，讲求实效', '高中'),
        ('与时俱进', 'yǔ shí jù jìn', '跟上时代的步伐', '高中'),
        ('再创辉煌', 'zài chuàng huī huáng', '再次创造辉煌成就', '高中'),
    ]
    
    for idiom, pinyin, meaning, difficulty in idioms:
        execute_sql(db_path, '''
            INSERT OR IGNORE INTO chinese_dictation_idioms (idiom, pinyin, meaning, difficulty_level)
            VALUES (?, ?, ?, ?)
        ''', (idiom, pinyin, meaning, difficulty))
    
    # 初始化语文古诗词库数据
    print("  - 初始化语文古诗词库数据...")
    poetry = [
        ('静夜思', '李白', '唐', '床前明月光，疑是地上霜。举头望明月，低头思故乡。', '小学低年级'),
        ('春晓', '孟浩然', '唐', '春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。', '小学低年级'),
        ('登鹳雀楼', '王之涣', '唐', '白日依山尽，黄河入海流。欲穷千里目，更上一层楼。', '小学低年级'),
        ('相思', '王维', '唐', '红豆生南国，春来发几枝。愿君多采撷，此物最相思。', '小学低年级'),
        ('悯农', '李绅', '唐', '锄禾日当午，汗滴禾下土。谁知盘中餐，粒粒皆辛苦。', '小学低年级'),
        ('咏鹅', '骆宾王', '唐', '鹅鹅鹅，曲项向天歌。白毛浮绿水，红掌拨清波。', '小学低年级'),
        ('江雪', '柳宗元', '唐', '千山鸟飞绝，万径人踪灭。孤舟蓑笠翁，独钓寒江雪。', '小学低年级'),
        ('绝句', '杜甫', '唐', '两个黄鹂鸣翠柳，一行白鹭上青天。窗含西岭千秋雪，门泊东吴万里船。', '小学高年级'),
        ('望庐山瀑布', '李白', '唐', '日照香炉生紫烟，遥看瀑布挂前川。飞流直下三千尺，疑是银河落九天。', '小学高年级'),
        ('早发白帝城', '李白', '唐', '朝辞白帝彩云间，千里江陵一日还。两岸猿声啼不住，轻舟已过万重山。', '小学高年级'),
        ('枫桥夜泊', '张继', '唐', '月落乌啼霜满天，江枫渔火对愁眠。姑苏城外寒山寺，夜半钟声到客船。', '小学高年级'),
        ('清明', '杜牧', '唐', '清明时节雨纷纷，路上行人欲断魂。借问酒家何处有，牧童遥指杏花村。', '小学高年级'),
        ('九月九日忆山东兄弟', '王维', '唐', '独在异乡为异客，每逢佳节倍思亲。遥知兄弟登高处，遍插茱萸少一人。', '小学高年级'),
        ('送元二使安西', '王维', '唐', '渭城朝雨浥轻尘，客舍青青柳色新。劝君更尽一杯酒，西出阳关无故人。', '小学高年级'),
        ('游子吟', '孟郊', '唐', '慈母手中线，游子身上衣。临行密密缝，意恐迟迟归。谁言寸草心，报得三春晖。', '初中'),
        ('出塞', '王昌龄', '唐', '秦时明月汉时关，万里长征人未还。但使龙城飞将在，不教胡马度阴山。', '初中'),
        ('凉州词', '王翰', '唐', '葡萄美酒夜光杯，欲饮琵琶马上催。醉卧沙场君莫笑，古来征战几人回。', '初中'),
        ('芙蓉楼送辛渐', '王昌龄', '唐', '寒雨连江夜入吴，平明送客楚山孤。洛阳亲友如相问，一片冰心在玉壶。', '初中'),
        ('山居秋暝', '王维', '唐', '空山新雨后，天气晚来秋。明月松间照，清泉石上流。竹喧归浣女，莲动下渔舟。随意春芳歇，王孙自可留。', '初中'),
        ('使至塞上', '王维', '唐', '单车欲问边，属国过居延。征蓬出汉塞，归雁入胡天。大漠孤烟直，长河落日圆。萧关逢候骑，都护在燕然。', '高中'),
        ('登高', '杜甫', '唐', '风急天高猿啸哀，渚清沙白鸟飞回。无边落木萧萧下，不尽长江滚滚来。万里悲秋常作客，百年多病独登台。艰难苦恨繁霜鬓，潦倒新停浊酒杯。', '高中'),
        ('蜀道难', '李白', '唐', '噫吁嚱，危乎高哉！蜀道之难，难于上青天！蚕丛及鱼凫，开国何茫然！尔来四万八千岁，不与秦塞通人烟。西当太白有鸟道，可以横绝峨眉巅。', '高中'),
        ('将进酒', '李白', '唐', '君不见黄河之水天上来，奔流到海不复回。君不见高堂明镜悲白发，朝如青丝暮成雪。人生得意须尽欢，莫使金樽空对月。天生我材必有用，千金散尽还复来。', '高中'),
        ('念奴娇·赤壁怀古', '苏轼', '宋', '大江东去，浪淘尽，千古风流人物。故垒西边，人道是，三国周郎赤壁。乱石穿空，惊涛拍岸，卷起千堆雪。江山如画，一时多少豪杰。', '高中'),
    ]
    
    for title, author, dynasty, content, difficulty in poetry:
        execute_sql(db_path, '''
            INSERT OR IGNORE INTO chinese_dictation_poetry (title, author, dynasty, content, difficulty_level)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, author, dynasty, content, difficulty))
    
    # 初始化语文读文选段数据
    print("  - 初始化语文读文选段数据...")
    passages = [
        ('春天来了', '春天来了，万物复苏。小草从土里探出头来，嫩嫩的，绿绿的。花儿也开了，红的像火，粉的像霞，白的像雪。小鸟在树上叽叽喳喳地唱歌，蝴蝶在花丛中翩翩起舞。', '春天,小草,花儿,小鸟,蝴蝶', '小学低年级', 85),
        ('美丽的校园', '我们的校园很美丽。走进校门，首先看到的是一个大花坛，里面种着各种各样的花。教学楼前有两棵高大的银杏树，秋天的时候，叶子变黄了，像一把把小扇子。操场旁边有一个小花园，里面有假山和小池塘，鱼儿在水里游来游去。', '校园,花坛,银杏树,花园,池塘', '小学低年级', 120),
        ('我的妈妈', '我的妈妈很勤劳。每天早上，妈妈早早地起床做饭。吃完饭后，妈妈还要洗衣服、打扫卫生。下午，妈妈去菜市场买菜，回来做晚饭。晚上，妈妈还要辅导我做作业。妈妈真辛苦啊！', '妈妈,勤劳,做饭,洗衣服,辅导', '小学低年级', 105),
        ('秋天的田野', '秋天来了，田野里一片丰收的景象。金黄的稻穗沉甸甸的，弯下了腰。红红的高粱像喝醉了酒一样，涨红了脸。棉花雪白雪白的，像天上的云朵。农民伯伯们忙着收割，脸上洋溢着丰收的喜悦。', '秋天,田野,丰收,稻穗,高粱', '小学高年级', 130),
        ('我爱读书', '读书是一件快乐的事情。书是知识的海洋，书是智慧的源泉。通过读书，我知道了很多有趣的故事，学到了很多有用的知识。读书可以开阔我的眼界，增长我的见识。我要养成读书的好习惯。', '读书,知识,智慧,故事,习惯', '小学高年级', 115),
        ('保护环境', '保护环境是我们每个人的责任。我们要爱护花草树木，不乱扔垃圾，不随地吐痰。我们要节约水电，减少浪费。我们要乘坐公共交通工具，减少空气污染。让我们一起行动起来，保护我们美丽的家园。', '环境,责任,节约,环保,家园', '小学高年级', 140),
        ('我的梦想', '每个人都有自己的梦想。我的梦想是成为一名科学家。我想发明很多有用的东西，帮助人们解决生活中的困难。我要努力学习，掌握更多的知识。我相信，只要我坚持不懈，我的梦想一定能够实现。', '梦想,科学家,发明,学习,坚持', '初中', 125),
        ('友谊', '友谊是人生中最珍贵的财富。真正的朋友会在你困难的时候帮助你，在你伤心的时候安慰你，在你成功的时候为你高兴。友谊需要真诚和信任，需要相互理解和支持。让我们珍惜身边的每一份友谊。', '友谊,朋友,真诚,信任,理解', '初中', 135),
        ('奋斗的青春', '青春是美好的，也是短暂的。在青春的岁月里，我们要努力奋斗，追逐梦想。奋斗的青春最美丽，奋斗的人生最精彩。不要浪费时间，不要虚度年华。让我们用汗水和努力，书写属于自己的青春篇章。', '青春,奋斗,梦想,时间,努力', '初中', 145),
        ('大自然的启示', '大自然是一位伟大的老师，给我们很多启示。水滴石穿告诉我们要坚持不懈，梅花傲雪告诉我们要坚强不屈，春蚕吐丝告诉我们要无私奉献。让我们用心观察大自然，从大自然中汲取智慧和力量。', '自然,启示,坚持,坚强,奉献', '初中', 130),
        ('人生的意义', '人生的意义在于奉献，而不在于索取。一个人的价值，不在于他拥有多少财富，而在于他为社会做出了多少贡献。让我们用自己的双手创造价值，用自己的智慧造福他人，让人生绽放出绚丽的光彩。', '人生,意义,奉献,价值,贡献', '高中', 150),
        ('成功的秘诀', '成功没有捷径，只有努力和坚持。每一个成功的人背后，都有无数的汗水和付出。成功需要目标明确，需要脚踏实地，需要不断学习。只要我们坚持不懈地努力，就一定能够到达成功的彼岸。', '成功,努力,坚持,目标,学习', '高中', 140),
    ]
    
    for title, content, keywords, difficulty, word_count in passages:
        execute_sql(db_path, '''
            INSERT OR IGNORE INTO chinese_dictation_passages (title, content, keywords, difficulty_level, word_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, content, keywords, difficulty, word_count))
    
    print("  ✓ 题库数据库增强完成")

def enhance_ai_db():
    """增强AI数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'ai.db')
    print("\n[AI数据库增强]")
    
    # AI模型性能表
    print("  - 创建AI模型性能表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS ai_model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT,
            model_name TEXT,
            provider TEXT,
            model_type TEXT,
            performance_score REAL DEFAULT 0,
            response_time_ms INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0,
            total_requests INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            last_test_at TEXT,
            status TEXT DEFAULT 'registered',
            config TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # AI节点状态表
    print("  - 创建AI节点状态表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS ai_node_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT UNIQUE NOT NULL,
            node_name TEXT,
            node_type TEXT DEFAULT 'worker',
            address TEXT,
            status TEXT DEFAULT 'offline',
            load REAL DEFAULT 0,
            capacity INTEGER DEFAULT 10,
            active_tasks INTEGER DEFAULT 0,
            total_tasks INTEGER DEFAULT 0,
            last_heartbeat TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # AI任务队列扩展表
    print("  - 创建AI任务队列扩展表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS ai_task_queue_ext (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE NOT NULL,
            task_type TEXT,
            priority INTEGER DEFAULT 10,
            status TEXT DEFAULT 'pending',
            node_id TEXT,
            input_data TEXT,
            output_data TEXT,
            error_message TEXT,
            progress INTEGER DEFAULT 0,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            started_at TEXT,
            completed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 初始化AI模型数据
    print("  - 初始化AI模型数据...")
    ai_models = [
        ('model_gpt4', 'GPT-4', 'openai', 'llm', 95.0, 800, 99.5, 0, 0),
        ('model_gpt35', 'GPT-3.5-Turbo', 'openai', 'llm', 88.0, 300, 99.8, 0, 0),
        ('model_gpt35_16k', 'GPT-3.5-Turbo-16K', 'openai', 'llm', 87.0, 400, 99.7, 0, 0),
        ('model_claude_3_opus', 'Claude-3-Opus', 'anthropic', 'llm', 96.0, 1000, 99.2, 0, 0),
        ('model_claude_3_sonnet', 'Claude-3-Sonnet', 'anthropic', 'llm', 92.0, 600, 99.6, 0, 0),
        ('model_claude_3_haiku', 'Claude-3-Haiku', 'anthropic', 'llm', 85.0, 200, 99.9, 0, 0),
        ('model_qwen_7b', 'Qwen-7B', 'alibaba', 'llm', 80.0, 500, 98.0, 0, 0),
        ('model_qwen_14b', 'Qwen-14B', 'alibaba', 'llm', 84.0, 800, 98.5, 0, 0),
        ('model_qwen_72b', 'Qwen-72B', 'alibaba', 'llm', 88.0, 1500, 98.0, 0, 0),
        ('model_llama_3_8b', 'Llama-3-8B', 'meta', 'llm', 82.0, 400, 98.5, 0, 0),
        ('model_llama_3_70b', 'Llama-3-70B', 'meta', 'llm', 90.0, 1200, 98.0, 0, 0),
        ('model_text_embedding_ada', 'text-embedding-ada-002', 'openai', 'embedding', 92.0, 100, 99.9, 0, 0),
        ('model_text_embedding_3_small', 'text-embedding-3-small', 'openai', 'embedding', 88.0, 80, 99.9, 0, 0),
        ('model_text_embedding_3_large', 'text-embedding-3-large', 'openai', 'embedding', 94.0, 150, 99.9, 0, 0),
        ('model_whisper', 'Whisper', 'openai', 'audio', 87.0, 5000, 99.0, 0, 0),
        ('model_whisper_large', 'Whisper-Large', 'openai', 'audio', 90.0, 8000, 99.2, 0, 0),
        ('model_dall_e_3', 'DALL-E-3', 'openai', 'image', 91.0, 5000, 98.0, 0, 0),
        ('model_stable_diffusion', 'Stable Diffusion', 'stability', 'image', 85.0, 10000, 97.0, 0, 0),
        ('model_gemini_pro', 'Gemini-Pro', 'google', 'llm', 89.0, 600, 99.0, 0, 0),
        ('model_gemini_pro_vision', 'Gemini-Pro-Vision', 'google', 'multimodal', 91.0, 800, 98.5, 0, 0),
    ]
    
    for model_id, name, provider, model_type, score, response_time, success_rate, requests, errors in ai_models:
        execute_sql(db_path, '''
            INSERT OR IGNORE INTO ai_model_performance (model_id, model_name, provider, model_type, performance_score, response_time_ms, success_rate, total_requests, error_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (model_id, name, provider, model_type, score, response_time, success_rate, requests, errors))
    
    print("  ✓ AI数据库增强完成")

def enhance_exam_db():
    """增强考试数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'exam.db')
    print("\n[考试数据库增强]")
    
    # 考试统计扩展表
    print("  - 创建考试统计扩展表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS exam_statistics_ext (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            total_students INTEGER DEFAULT 0,
            completed_students INTEGER DEFAULT 0,
            avg_score REAL DEFAULT 0,
            max_score INTEGER DEFAULT 0,
            min_score INTEGER DEFAULT 0,
            pass_rate REAL DEFAULT 0,
            avg_time INTEGER DEFAULT 0,
            difficulty REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 考试错题分析表
    print("  - 创建考试错题分析表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS exam_error_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            question_id INTEGER,
            error_count INTEGER DEFAULT 0,
            total_count INTEGER DEFAULT 0,
            error_rate REAL DEFAULT 0,
            common_wrong_answers TEXT,
            analysis TEXT,
            improvement_suggestion TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("  ✓ 考试数据库增强完成")

def enhance_user_db():
    """增强用户数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'user.db')
    print("\n[用户数据库增强]")
    
    # 用户学习进度扩展表
    print("  - 创建用户学习进度扩展表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS user_learning_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            course_id INTEGER,
            chapter_id INTEGER,
            progress REAL DEFAULT 0,
            completed INTEGER DEFAULT 0,
            last_accessed_at TEXT,
            total_time INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 用户偏好设置表
    print("  - 创建用户偏好设置表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            theme TEXT DEFAULT 'default',
            language TEXT DEFAULT 'zh',
            timezone TEXT DEFAULT 'Asia/Shanghai',
            notification_enabled INTEGER DEFAULT 1,
            email_notification INTEGER DEFAULT 1,
            push_notification INTEGER DEFAULT 1,
            daily_reminder INTEGER DEFAULT 0,
            reminder_time TEXT DEFAULT '09:00',
            difficulty_level TEXT DEFAULT 'medium',
            learning_goal TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("  ✓ 用户数据库增强完成")

def enhance_log_db():
    """增强日志数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'log.db')
    print("\n[日志数据库增强]")
    
    # 操作日志扩展表
    print("  - 创建操作日志扩展表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS operation_logs_ext (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT,
            resource TEXT,
            resource_id INTEGER,
            action_type TEXT,
            detail TEXT,
            ip_address TEXT,
            user_agent TEXT,
            device_type TEXT,
            success INTEGER DEFAULT 1,
            error_message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 性能日志表
    print("  - 创建性能日志表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS performance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_type TEXT,
            metric_name TEXT,
            value REAL,
            unit TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("  ✓ 日志数据库增强完成")

def enhance_admin_db():
    """增强管理数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'admin.db')
    print("\n[管理数据库增强]")
    
    # 系统操作日志表
    print("  - 创建系统操作日志表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS admin_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            admin_name TEXT,
            operation TEXT,
            target TEXT,
            target_id INTEGER,
            before_value TEXT,
            after_value TEXT,
            ip_address TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 系统配置变更表
    print("  - 创建系统配置变更表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS config_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT,
            old_value TEXT,
            new_value TEXT,
            changed_by INTEGER,
            changed_by_name TEXT,
            change_reason TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("  ✓ 管理数据库增强完成")

def run_all_enhancements():
    """运行所有数据库增强"""
    print("=" * 70)
    print("  MTSCOS AI 数据库增强脚本 v7.2.0")
    print("=" * 70)
    print(f"  执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    enhance_system_db()
    enhance_auth_db()
    enhance_question_db()
    enhance_ai_db()
    enhance_exam_db()
    enhance_user_db()
    enhance_log_db()
    enhance_admin_db()
    
    print("\n" + "=" * 70)
    print("  所有数据库增强完成！")
    print("=" * 70)

if __name__ == '__main__':
    run_all_enhancements()