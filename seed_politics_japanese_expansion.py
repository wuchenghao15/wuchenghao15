#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

def add_politics_category(conn):
    cursor = conn.cursor()
    categories = [
        ('政治', 'Politics', '思想政治学科', 16, 1),
        ('党中央精神', 'PartySpirit', '党中央重要精神专项', 17, 1),
        ('时事政治', 'CurrentAffairs', '国内外时事政治', 18, 1),
        ('日语新闻', 'JapaneseNews', '日语新闻播报专项', 19, 1),
        ('日语政治', 'JapanesePolitics', '日语政治内容专项', 20, 1),
    ]
    
    for cat in categories:
        try:
            cursor.execute("INSERT OR IGNORE INTO question_categories (name, code, description, sort_order, status) VALUES (?, ?, ?, ?, ?)", cat)
            print(f"  添加分类: {cat[0]}")
        except Exception as e:
            print(f"  添加分类 {cat[0]} 失败: {e}")
    
    conn.commit()

def add_politics_tags(conn):
    cursor = conn.cursor()
    tags = [
        ('政治', '思想政治学科', 17),
        ('马克思主义', '马克思主义基本原理', 18),
        ('毛泽东思想', '毛泽东思想概论', 19),
        ('中国特色社会主义', '中国特色社会主义理论', 20),
        ('习近平新时代', '习近平新时代中国特色社会主义思想', 21),
        ('党中央精神', '党中央重要会议精神', 22),
        ('时事政治', '国内外时事政治', 23),
        ('二十大精神', '党的二十大精神', 24),
        ('四个全面', '四个全面战略布局', 25),
        ('五位一体', '五位一体总体布局', 26),
        ('新发展理念', '新发展理念', 27),
        ('中国式现代化', '中国式现代化', 28),
        ('日语新闻', '日语新闻播报', 29),
        ('日语政治', '日语政治内容', 30),
    ]
    
    for tag in tags:
        try:
            cursor.execute("INSERT OR IGNORE INTO question_tags (name, description, sort_order) VALUES (?, ?, ?)", tag)
            print(f"  添加标签: {tag[0]}")
        except Exception as e:
            print(f"  添加标签 {tag[0]} 失败: {e}")
    
    conn.commit()

def add_additional_fields(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(questions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'transcript' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN transcript TEXT")
            print("  添加 transcript 列")
        
        if 'language' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN language TEXT")
            print("  添加 language 列")
        
        if 'accent' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN accent TEXT")
            print("  添加 accent 列")
        
        if 'voice' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN voice TEXT")
            print("  添加 voice 列")
        
        conn.commit()
    except Exception as e:
        print(f"  更新表结构失败: {e}")

def insert_politics_questions(conn):
    cursor = conn.cursor()
    questions = [
        ('马克思主义哲学认为，_____是世界的本原。', 'single', '政治', 'easy', '物质', 'A|物质|B|意识|C|精神|D|理念', '马克思主义哲学坚持物质第一性，意识第二性，认为物质是世界的本原。', '2026', 'politics_marxism', 'system', 16),
        ('唯物辩证法的实质和核心是_____。', 'single', '政治', 'medium', '对立统一规律', 'A|对立统一规律|B|质量互变规律|C|否定之否定规律|D|联系和发展', '对立统一规律揭示了事物发展的源泉和动力，是唯物辩证法的实质和核心。', '2026', 'politics_marxism', 'system', 16),
        ('实践是检验真理的唯一标准，这是由_____决定的。', 'single', '政治', 'medium', '真理的本性和实践的特点', 'A|真理的本性和实践的特点|B|真理的相对性|C|真理的绝对性|D|真理的具体性', '实践是检验真理的唯一标准，这是由真理的本性和实践的特点所决定的。', '2026', 'politics_marxism', 'system', 16),
        ('新民主主义革命的三大法宝是_____。', 'single', '政治', 'easy', '统一战线、武装斗争、党的建设', 'A|统一战线、武装斗争、党的建设|B|实事求是、群众路线、独立自主|C|理论联系实际、密切联系群众、批评与自我批评|D|解放思想、实事求是、与时俱进', '毛泽东把统一战线、武装斗争、党的建设比作党在中国革命中战胜敌人的三个法宝。', '2026', 'politics_mao', 'system', 16),
        ('毛泽东思想活的灵魂是_____。', 'single', '政治', 'easy', '实事求是、群众路线、独立自主', 'A|实事求是、群众路线、独立自主|B|武装斗争、统一战线、党的建设|C|解放思想、实事求是、与时俱进|D|理论联系实际、密切联系群众、批评与自我批评', '毛泽东思想活的灵魂是贯穿于毛泽东思想各个组成部分的立场、观点和方法，有三个基本方面，即实事求是、群众路线、独立自主。', '2026', 'politics_mao', 'system', 16),
        ('邓小平理论的精髓是_____。', 'single', '政治', 'easy', '解放思想、实事求是', 'A|解放思想、实事求是|B|什么是社会主义、怎样建设社会主义|C|一个中心、两个基本点|D|社会主义本质理论', '解放思想、实事求是是邓小平理论的精髓和灵魂。', '2026', 'politics_socialism', 'system', 16),
        ('"三个代表"重要思想的本质是_____。', 'single', '政治', 'easy', '立党为公、执政为民', 'A|立党为公、执政为民|B|解放思想、实事求是|C|与时俱进、开拓创新|D|发展是党执政兴国的第一要务', '立党为公、执政为民是"三个代表"重要思想的本质。', '2026', 'politics_socialism', 'system', 16),
        ('科学发展观的核心是_____。', 'single', '政治', 'easy', '以人为本', 'A|以人为本|B|全面协调可持续|C|统筹兼顾|D|发展', '科学发展观第一要义是发展，核心是以人为本。', '2026', 'politics_socialism', 'system', 16),
        ('习近平新时代中国特色社会主义思想的核心要义是_____。', 'single', '政治', 'easy', '坚持和发展中国特色社会主义', 'A|坚持和发展中国特色社会主义|B|实现中华民族伟大复兴|C|全面建设社会主义现代化国家|D|推进国家治理体系现代化', '坚持和发展中国特色社会主义，是习近平新时代中国特色社会主义思想的核心要义。', '2026', 'politics_xijinping', 'system', 17),
        ('新时代我国社会主要矛盾是_____。', 'single', '政治', 'medium', '人民日益增长的美好生活需要和不平衡不充分的发展之间的矛盾', 'A|人民日益增长的美好生活需要和不平衡不充分的发展之间的矛盾|B|人民日益增长的物质文化需要同落后的社会生产之间的矛盾|C|无产阶级和资产阶级的矛盾|D|社会主义和资本主义的矛盾', '党的十九大报告指出，新时代我国社会主要矛盾是人民日益增长的美好生活需要和不平衡不充分的发展之间的矛盾。', '2026', 'politics_xijinping', 'system', 17),
        ('中国共产党的根本宗旨是_____。', 'single', '政治', 'easy', '全心全意为人民服务', 'A|全心全意为人民服务|B|实现共产主义|C|建设社会主义|D|实现国家富强', '全心全意为人民服务是中国共产党的根本宗旨。', '2026', 'politics_party', 'system', 17),
        ('"四个全面"战略布局是指_____。', 'multiple', '政治', 'medium', 'ABCD', 'A|全面建设社会主义现代化国家|B|全面深化改革|C|全面依法治国|D|全面从严治党', '"四个全面"战略布局包括全面建设社会主义现代化国家、全面深化改革、全面依法治国、全面从严治党。', '2026', 'politics_party', 'system', 17),
        ('"五位一体"总体布局包括_____。', 'multiple', '政治', 'medium', 'ABCDE', 'A|经济建设|B|政治建设|C|文化建设|D|社会建设|E|生态文明建设', '"五位一体"总体布局包括经济建设、政治建设、文化建设、社会建设、生态文明建设。', '2026', 'politics_party', 'system', 17),
        ('新发展理念包括_____。', 'multiple', '政治', 'easy', 'ABCDE', 'A|创新|B|协调|C|绿色|D|开放|E|共享', '新发展理念包括创新、协调、绿色、开放、共享五大发展理念。', '2026', 'politics_party', 'system', 17),
        ('中国式现代化是_____的现代化。', 'single', '政治', 'medium', '人口规模巨大', 'A|人口规模巨大|B|少数人富裕|C|照搬西方模式|D|忽视生态环境', '中国式现代化是人口规模巨大的现代化、全体人民共同富裕的现代化、物质文明和精神文明相协调的现代化、人与自然和谐共生的现代化、走和平发展道路的现代化。', '2026', 'politics_xijinping', 'system', 17),
        ('社会主义核心价值观在国家层面的价值目标是_____。', 'single', '政治', 'easy', '富强、民主、文明、和谐', 'A|富强、民主、文明、和谐|B|自由、平等、公正、法治|C|爱国、敬业、诚信、友善|D|独立、自主、和平、发展', '社会主义核心价值观包括三个层面：国家层面的价值目标是富强、民主、文明、和谐。', '2026', 'politics_values', 'system', 16),
        ('社会主义核心价值观在社会层面的价值取向是_____。', 'single', '政治', 'easy', '自由、平等、公正、法治', 'A|富强、民主、文明、和谐|B|自由、平等、公正、法治|C|爱国、敬业、诚信、友善|D|独立、自主、和平、发展', '社会主义核心价值观包括三个层面：社会层面的价值取向是自由、平等、公正、法治。', '2026', 'politics_values', 'system', 16),
        ('社会主义核心价值观在公民层面的价值准则是_____。', 'single', '政治', 'easy', '爱国、敬业、诚信、友善', 'A|富强、民主、文明、和谐|B|自由、平等、公正、法治|C|爱国、敬业、诚信、友善|D|独立、自主、和平、发展', '社会主义核心价值观包括三个层面：公民层面的价值准则是爱国、敬业、诚信、友善。', '2026', 'politics_values', 'system', 16),
        ('中国共产党领导是中国特色社会主义_____的特征。', 'single', '政治', 'easy', '最本质', 'A|最本质|B|重要|C|基本|D|一般', '中国共产党领导是中国特色社会主义最本质的特征，是中国特色社会主义制度的最大优势。', '2026', 'politics_party', 'system', 17),
        ('"两个维护"是指_____。', 'single', '政治', 'easy', '维护习近平总书记党中央的核心、全党的核心地位，维护党中央权威和集中统一领导', 'A|维护习近平总书记党中央的核心、全党的核心地位，维护党中央权威和集中统一领导|B|维护党的领导、维护人民利益|C|维护国家安全、维护社会稳定|D|维护国家统一、维护民族团结', '"两个维护"是指坚决维护习近平总书记党中央的核心、全党的核心地位，坚决维护党中央权威和集中统一领导。', '2026', 'politics_party', 'system', 17),
        ('党的二十大报告指出，从现在起，中国共产党的中心任务就是团结带领全国各族人民全面建成社会主义现代化强国、实现第二个百年奋斗目标，以_____全面推进中华民族伟大复兴。', 'single', '政治', 'easy', '中国式现代化', 'A|中国式现代化|B|社会主义现代化|C|改革开放|D|科技创新', '党的二十大报告指出，从现在起，中国共产党的中心任务就是团结带领全国各族人民全面建成社会主义现代化强国、实现第二个百年奋斗目标，以中国式现代化全面推进中华民族伟大复兴。', '2026', 'politics_20da', 'system', 17),
        ('党的二十大报告指出，高质量发展是全面建设社会主义现代化国家的_____。', 'single', '政治', 'easy', '首要任务', 'A|首要任务|B|重要任务|C|基本任务|D|核心任务', '党的二十大报告指出，高质量发展是全面建设社会主义现代化国家的首要任务。', '2026', 'politics_20da', 'system', 17),
        ('全过程人民民主是_____。', 'single', '政治', 'medium', '最广泛、最真实、最管用的民主', 'A|最广泛、最真实、最管用的民主|B|形式上的民主|C|少数人的民主|D|西方模式的民主', '全过程人民民主是最广泛、最真实、最管用的民主，是全链条、全方位、全覆盖的民主。', '2026', 'politics_xijinping', 'system', 17),
        ('总体国家安全观的宗旨是_____。', 'single', '政治', 'easy', '人民安全', 'A|人民安全|B|政治安全|C|经济安全|D|军事安全', '总体国家安全观以人民安全为宗旨，以政治安全为根本，以经济安全为基础。', '2026', 'politics_party', 'system', 17),
        ('"一带一路"倡议的核心精神是_____。', 'single', '政治', 'medium', '和平合作、开放包容、互学互鉴、互利共赢', 'A|和平合作、开放包容、互学互鉴、互利共赢|B|霸权主义、强权政治|C|零和博弈|D|单边主义', '"一带一路"倡议秉持和平合作、开放包容、互学互鉴、互利共赢的核心精神。', '2026', 'politics_current', 'system', 18),
        ('我国的根本政治制度是_____。', 'single', '政治', 'easy', '人民代表大会制度', 'A|人民代表大会制度|B|中国共产党领导的多党合作和政治协商制度|C|民族区域自治制度|D|基层群众自治制度', '人民代表大会制度是我国的根本政治制度。', '2026', 'politics_basic', 'system', 16),
        ('我国的基本政治制度包括_____。', 'multiple', '政治', 'medium', 'BCD', 'A|人民代表大会制度|B|中国共产党领导的多党合作和政治协商制度|C|民族区域自治制度|D|基层群众自治制度', '我国的基本政治制度包括中国共产党领导的多党合作和政治协商制度、民族区域自治制度、基层群众自治制度。', '2026', 'politics_basic', 'system', 16),
        ('中国近代史的开端是_____。', 'single', '政治', 'easy', '鸦片战争', 'A|鸦片战争|B|甲午战争|C|辛亥革命|D|五四运动', '1840年鸦片战争爆发，标志着中国近代史的开端。', '2026', 'politics_history', 'system', 16),
        ('中华人民共和国成立的时间是_____。', 'single', '政治', 'easy', '1949年10月1日', 'A|1949年10月1日|B|1945年8月15日|C|1949年1月1日|D|1956年1月1日', '1949年10月1日，中华人民共和国中央人民政府成立，标志着新中国的诞生。', '2026', 'politics_history', 'system', 16),
    ]
    
    for q in questions:
        try:
            cursor.execute("INSERT INTO questions (question_text, question_type, subject, difficulty, answer, options, explanation, year, special_type, source, category_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", q)
        except Exception as e:
            print(f"  插入政治题目失败: {e}")
    
    conn.commit()
    print("  政治题目已插入")

def insert_japanese_news_questions(conn):
    cursor = conn.cursor()
    questions = [
        ('次のニュースの内容と合っているものはどれですか。\n【原文】日本政府は、新しい経済対策を発表しました。消費税の軽減や給付金の支給などが含まれています。', 'single', '日语', 'medium', '経済対策には消費税の軽減が含まれている', 'A|経済対策には消費税の軽減が含まれている|B|経済対策は環境問題に関するものだった|C|給付金は支給されない|D|政府は何も発表していない', 'ニュースによると、経済対策に消費税の軽減や給付金の支給などが含まれているとのことです。', '2026', 'japanese_news', 'system', 19, '日本政府は、新しい経済対策を発表しました。消費税の軽減や給付金の支給などが含まれています。', 'japanese', 'kanto', 'female'),
        ('次のニュースの内容と合っているものはどれですか。\n【原文】東京オリンピックの準備は順調に進んでいます。各国の選手団が東京に到着し始めています。', 'single', '日语', 'easy', 'オリンピックの準備は順調だ', 'A|オリンピックは中止された|B|オリンピックの準備は順調だ|C|選手団はまだ到着していない|D|東京で開催されない', 'ニュースによると、東京オリンピックの準備は順調に進んでおり、各国の選手団が到着し始めているとのことです。', '2026', 'japanese_news', 'system', 19, '東京オリンピックの準備は順調に進んでいます。各国の選手団が東京に到着し始めています。', 'japanese', 'kanto', 'male'),
        ('次のニュースの内容と合っているものはどれですか。\n【原文】気象庁は、台風が日本列島に接近していると発表しました。関東地方では大雨の可能性があります。', 'single', '日语', 'easy', '台風が接近している', 'A|台風は遠くにいる|B|台風が接近している|C|晴れの予報だ|D|北海道に影響はない', '気象庁の発表によると、台風が日本列島に接近しており、関東地方では大雨の可能性があるとのことです。', '2026', 'japanese_news', 'system', 19, '気象庁は、台風が日本列島に接近していると発表しました。関東地方では大雨の可能性があります。', 'japanese', 'kansai', 'female'),
        ('次のニュースの内容と合っているものはどれですか。\n【原文】科学技術の進歩により、人工知能が様々な分野で活用されるようになりました。医療や教育の現場でもAIが導入されています。', 'single', '日语', 'medium', 'AIが医療や教育にも導入されている', 'A|AIはまだ開発されていない|B|AIが医療や教育にも導入されている|C|AIは危険だと言われている|D|科学技術は進歩していない', 'ニュースによると、科学技術の進歩によりAIが様々な分野で活用され、医療や教育の現場でも導入されているとのことです。', '2026', 'japanese_news', 'system', 19, '科学技術の進歩により、人工知能が様々な分野で活用されるようになりました。医療や教育の現場でもAIが導入されています。', 'japanese', 'kanto', 'male'),
        ('次のニュースの内容と合っているものはどれですか。\n【原文】環境問題への関心が高まっています。多くの企業がCO2削減を目指しています。', 'single', '日语', 'medium', '企業がCO2削減を目指している', 'A|環境問題への関心は低い|B|企業がCO2削減を目指している|C|CO2は問題になっていない|D|企業は何もしていない', 'ニュースによると、環境問題への関心が高まっており、多くの企業がCO2削減を目指しているとのことです。', '2026', 'japanese_news', 'system', 19, '環境問題への関心が高まっています。多くの企業がCO2削減を目指しています。', 'japanese', 'kansai', 'male'),
        ('次のニュースの内容と合っているものはどれですか。\n【原文】新型コロナウイルスの感染状況が改善しています。政府は緊急事態宣言を解除する方針です。', 'single', '日语', 'easy', '感染状況が改善している', 'A|感染状況が悪化している|B|感染状況が改善している|C|緊急事態宣言が延長される|D|政府は何も決めていない', 'ニュースによると、新型コロナウイルスの感染状況が改善しており、政府は緊急事態宣言を解除する方針だとのことです。', '2026', 'japanese_news', 'system', 19, '新型コロナウイルスの感染状況が改善しています。政府は緊急事態宣言を解除する方針です。', 'japanese', 'kanto', 'female'),
        ('次のニュースの内容と合っているものはどれですか。\n【原文】日本の経済成長率が予想を上回りました。輸出が好調だったことが要因の一つです。', 'single', '日语', 'medium', '経済成長率が予想を上回った', 'A|経済は衰退している|B|経済成長率が予想を上回った|C|輸出が低迷している|D|何も変わっていない', 'ニュースによると、日本の経済成長率が予想を上回り、輸出が好調だったことが要因の一つだとのことです。', '2026', 'japanese_news', 'system', 19, '日本の経済成長率が予想を上回りました。輸出が好調だったことが要因の一つです。', 'japanese', 'kanto', 'male'),
        ('次のニュースの内容と合っているものはどれですか。\n【原文】教育改革が進められています。授業時間の短縮や新しいカリキュラムの導入が検討されています。', 'single', '日语', 'medium', '教育改革が進められている', 'A|教育改革は中止された|B|教育改革が進められている|C|授業時間は延長される|D|カリキュラムは変わらない', 'ニュースによると、教育改革が進められており、授業時間の短縮や新しいカリキュラムの導入が検討されているとのことです。', '2026', 'japanese_news', 'system', 19, '教育改革が進められています。授業時間の短縮や新しいカリキュラムの導入が検討されています。', 'japanese', 'kansai', 'female'),
        ('次のニュースの内容と合っているものはどれですか。\n【原文】自動車メーカーが電気自動車の開発を加速しています。環境負荷の少ない車両への転換が進んでいます。', 'single', '日语', 'medium', '電気自動車の開発が加速している', 'A|電気自動車の開発は遅れている|B|電気自動車の開発が加速している|C|環境問題は気にしていない|D|従来の車両が好まれている', 'ニュースによると、自動車メーカーが電気自動車の開発を加速し、環境負荷の少ない車両への転換が進んでいるとのことです。', '2026', 'japanese_news', 'system', 19, '自動車メーカーが電気自動車の開発を加速しています。環境負荷の少ない車両への転換が進んでいます。', 'japanese', 'kanto', 'male'),
        ('次のニュースの内容と合っているものはどれですか。\n【原文】少子高齢化が深刻化しています。政府は年金制度の改革を検討しています。', 'single', '日语', 'medium', '少子高齢化が深刻化している', 'A|少子高齢化は改善している|B|少子高齢化が深刻化している|C|年金制度は変わらない|D|若い人が増えている', 'ニュースによると、少子高齢化が深刻化しており、政府は年金制度の改革を検討しているとのことです。', '2026', 'japanese_news', 'system', 19, '少子高齢化が深刻化しています。政府は年金制度の改革を検討しています。', 'japanese', 'kansai', 'male'),
    ]
    
    for q in questions:
        try:
            cursor.execute("INSERT INTO questions (question_text, question_type, subject, difficulty, answer, options, explanation, year, special_type, source, category_id, transcript, language, accent, voice) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", q)
        except Exception as e:
            print(f"  插入日语新闻题目失败: {e}")
    
    conn.commit()
    print("  日语新闻题目已插入")

def insert_japanese_politics_questions(conn):
    cursor = conn.cursor()
    questions = [
        ('日本の国会はどのような役割を持っていますか。', 'single', '日语', 'medium', '法律の制定と政府の監督', 'A|法律の制定と政府の監督|B|行政事務の執行|C|司法裁判の実施|D|軍隊の指揮', '日本の国会は最高立法機関であり、法律の制定、予算の審議、政府の監督などを行います。', '2026', 'japanese_politics', 'system', 20),
        ('日本の首相はどこで選出されますか。', 'single', '日语', 'easy', '国会', 'A|国会|B|国民投票|C|天皇|D|最高法院', '日本の首相は国会議員の中から選出されます。', '2026', 'japanese_politics', 'system', 20),
        ('日本の憲法で定められている基本的人権にはどれが含まれますか。', 'multiple', '日语', 'medium', 'ABC', 'A|平等権|B|言論の自由|C|信仰の自由|D|独裁権', '日本国憲法では、平等権、言論の自由、信仰の自由などの基本的人権が保障されています。', '2026', 'japanese_politics', 'system', 20),
        ('日本の政治体制はどのようなものですか。', 'single', '日语', 'medium', '議会制民主主義', 'A|独裁体制|B|議会制民主主義|C|君主専制|D|軍事独裁', '日本は議会制民主主義の国家であり、国会が最高権力機関となっています。', '2026', 'japanese_politics', 'system', 20),
        ('日本の政党政治において、最大の政党はどれですか。', 'single', '日语', 'medium', '自由民主党', 'A|自由民主党|B|立憲民主党|C|公明党|D|日本共産党', '現在の日本政治において、自由民主党が最大の政党となっています。', '2026', 'japanese_politics', 'system', 20),
        ('日本の地方自治体にはどれが含まれますか。', 'multiple', '日语', 'medium', 'ABCD', 'A|都道府県|B|市町村|C|特別区|D|政令指定都市', '日本の地方自治体には、都道府県、市町村、特別区、政令指定都市などが含まれます。', '2026', 'japanese_politics', 'system', 20),
        ('日本の選挙制度で、衆議院議員はどのように選ばれますか。', 'single', '日语', 'medium', '小選挙区比例代表並立制', 'A|小選挙区比例代表並立制|B|完全比例代表制|C|大選挙区制|D|間接選挙', '日本の衆議院議員選挙は、小選挙区比例代表並立制という制度で行われます。', '2026', 'japanese_politics', 'system', 20),
        ('日本の外交政策の基本は何ですか。', 'single', '日语', 'medium', '日米安保条約を基軸とする', 'A|日米安保条約を基軸とする|B|軍事同盟を結ばない|C|孤立主義|D|対米敵対', '日本の外交政策は日米安保条約を基軸としており、アメリカとの同盟関係を重視しています。', '2026', 'japanese_politics', 'system', 20),
        ('日本の環境政策において、政府が掲げている目標は何ですか。', 'single', '日语', 'medium', 'カーボンニュートラル', 'A|カーボンニュートラル|B|CO2排出量の増加|C|原子力発電の全廃|D|環境保護を放棄', '日本政府は、2050年までにカーボンニュートラルを達成することを目標としています。', '2026', 'japanese_politics', 'system', 20),
        ('日本の社会保障制度にはどれが含まれますか。', 'multiple', '日语', 'medium', 'ABC', 'A|年金制度|B|医療保険制度|C|介護保険制度|D|無料教育制度', '日本の社会保障制度には、年金制度、医療保険制度、介護保険制度などが含まれます。', '2026', 'japanese_politics', 'system', 20),
    ]
    
    for q in questions:
        try:
            cursor.execute("INSERT INTO questions (question_text, question_type, subject, difficulty, answer, options, explanation, year, special_type, source, category_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", q)
        except Exception as e:
            print(f"  插入日语政治题目失败: {e}")
    
    conn.commit()
    print("  日语政治题目已插入")

def audit_expansion(conn):
    cursor = conn.cursor()
    print("\n=== 扩展审计 ===")
    
    cursor.execute("SELECT COUNT(*) FROM questions")
    total = cursor.fetchone()[0]
    print(f"题目总数: {total}")
    
    cursor.execute("SELECT subject, COUNT(*) FROM questions GROUP BY subject")
    result = cursor.fetchall()
    print("\n按科目分布:")
    for row in result:
        print(f"  {row[0]}: {row[1]} 道")
    
    cursor.execute("SELECT special_type, COUNT(*) FROM questions GROUP BY special_type")
    result = cursor.fetchall()
    print("\n按专项类型分布:")
    for row in result:
        print(f"  {row[0] or '普通'}: {row[1]} 道")

def main():
    print("=== MTSCOS AI 政治与日语题库扩展 ===")
    print("时间:", datetime.now())
    
    conn = sqlite3.connect(DATABASE_PATH)
    
    print("\n1. 添加政治和日语分类...")
    add_politics_category(conn)
    
    print("\n2. 添加政治和日语标签...")
    add_politics_tags(conn)
    
    print("\n3. 扩展题目表结构...")
    add_additional_fields(conn)
    
    print("\n4. 插入政治题目...")
    insert_politics_questions(conn)
    
    print("\n5. 插入日语新闻题目...")
    insert_japanese_news_questions(conn)
    
    print("\n6. 插入日语政治题目...")
    insert_japanese_politics_questions(conn)
    
    conn.close()
    
    print("\n=== 扩展完成 ===")
    conn = sqlite3.connect(DATABASE_PATH)
    audit_expansion(conn)
    conn.close()

if __name__ == '__main__':
    main()