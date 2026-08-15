#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI 题库与脑库综合投喂脚本
================================
功能：
1. 向题库投喂教育题目（K12、高等教育、职业教育、语言学习、IT技能）
2. 向脑库投喂知识数据（系统架构、AI运维、教育理论、技术知识、管理经验）
3. 自动创建缺失的表结构
4. 验证投喂结果
"""

import os
import sys
import json
import random
import sqlite3
import logging
from datetime import datetime

# ========== 路径配置 ==========
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'app.db')

# 备用数据库路径（如果主数据库不可用）
BACKUP_DB_PATHS = [
    os.path.join(PROJECT_ROOT, '..', '_runtime', 'db', 'app.db'),
    os.path.join(PROJECT_ROOT, '..', '_runtime', 'databases', 'Database', 'app.db'),
    os.path.join('/tmp', 'mtscos_feed.db'),
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(PROJECT_ROOT, 'feeding_script.log'), encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('FeedingScript')


def resolve_db_path():
    """解析可用的数据库路径"""
    if os.path.exists(DATABASE_PATH) and os.path.getsize(DATABASE_PATH) > 0:
        try:
            conn = sqlite3.connect(DATABASE_PATH, timeout=5)
            conn.execute("SELECT 1")
            conn.close()
            return DATABASE_PATH
        except:
            pass

    for path in BACKUP_DB_PATHS:
        if os.path.exists(os.path.dirname(path)):
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                conn = sqlite3.connect(path, timeout=5)
                conn.execute("SELECT 1")
                conn.close()
                logger.info(f"使用备用数据库: {path}")
                return path
            except:
                continue

    # 最后兜底：创建临时数据库
    fallback = os.path.join('/tmp', 'mtscos_feed_fallback.db')
    logger.warning(f"所有数据库不可用，创建临时数据库: {fallback}")
    return fallback


# ========== 题库数据 ==========

# K12 题库
K12_QUESTIONS = [
    # 语文
    {
        "subject": "语文", "question_type": "single_choice", "difficulty": 0.3,
        "stem": "下列词语中，加点字的读音全部正确的一项是？",
        "options": json.dumps([
            {"id": "A", "content": "酝酿(niàng) 黄晕(yùn) 发髻(jì) 贮蓄(zhù)"},
            {"id": "B", "content": "水藻(zhǎo) 看护(kān) 棱镜(léng) 碣石(jié)"},
            {"id": "C", "content": "菜畦(qí) 憔悴(qiáo) 匿笑(nì) 确凿(záo)"},
            {"id": "D", "content": "惭愧(kuì) 悔恨(huǐ) 蝉蜕(tuō) 锡箔(bó)"}
        ], ensure_ascii=False),
        "answer": "C",
        "analysis": "A项中'贮蓄'的'贮'应读zhù（正确），但此选项需结合完整题目判断；B项'水藻'的'藻'应读zǎo；D项'蝉蜕'的'蜕'应读tuì。C项全部正确。",
        "knowledge_points": "字音,汉字读音",
        "score": 5
    },
    {
        "subject": "语文", "question_type": "fill_blank", "difficulty": 0.4,
        "stem": "《论语》中阐述学习与思考辩证关系的句子是：'学而不思则罔，______。'",
        "options": json.dumps([], ensure_ascii=False),
        "answer": "思而不学则殆",
        "analysis": "此句出自《论语·为政》，强调学习与思考相结合的重要性。'罔'意为迷惑而无所得，'殆'意为精神疲倦而无所得。",
        "knowledge_points": "文言文,论语,名句默写",
        "score": 5
    },
    {
        "subject": "语文", "question_type": "single_choice", "difficulty": 0.5,
        "stem": "下列句子中，没有语病的一项是？",
        "options": json.dumps([
            {"id": "A", "content": "通过这次活动，使我明白了团结的重要性。"},
            {"id": "B", "content": "能否认真学习是取得好成绩的关键。"},
            {"id": "C", "content": "他那崇高的革命品质，经常浮现在我的脑海中。"},
            {"id": "D", "content": "我们要继承和发扬老一辈革命家的优良传统。"}
        ], ensure_ascii=False),
        "answer": "D",
        "analysis": "A项缺主语，删去'通过'或'使'；B项两面对一面，删去'能否'或在'取得'前加'能否'；C项搭配不当，'品质'不能'浮现'。",
        "knowledge_points": "病句辨析,语法",
        "score": 5
    },
    # 数学
    {
        "subject": "数学", "question_type": "single_choice", "difficulty": 0.3,
        "stem": "已知函数f(x)=x²-2x+1，则f(3)的值为？",
        "options": json.dumps([
            {"id": "A", "content": "2"},
            {"id": "B", "content": "4"},
            {"id": "C", "content": "6"},
            {"id": "D", "content": "8"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "f(3) = 3² - 2×3 + 1 = 9 - 6 + 1 = 4",
        "knowledge_points": "二次函数,函数求值",
        "score": 5
    },
    {
        "subject": "数学", "question_type": "fill_blank", "difficulty": 0.4,
        "stem": "等差数列{an}中，a₁=2，公差d=3，则a₁₀=______。",
        "options": json.dumps([], ensure_ascii=False),
        "answer": "29",
        "analysis": "等差数列通项公式：an = a₁ + (n-1)d，所以a₁₀ = 2 + (10-1)×3 = 2 + 27 = 29",
        "knowledge_points": "等差数列,通项公式",
        "score": 5
    },
    {
        "subject": "数学", "question_type": "single_choice", "difficulty": 0.6,
        "stem": "在△ABC中，若a=2，b=3，C=60°，则c的值为？",
        "options": json.dumps([
            {"id": "A", "content": "√7"},
            {"id": "B", "content": "√13"},
            {"id": "C", "content": "√19"},
            {"id": "D", "content": "7"}
        ], ensure_ascii=False),
        "answer": "A",
        "analysis": "由余弦定理：c² = a² + b² - 2ab·cosC = 4 + 9 - 2×2×3×cos60° = 13 - 12×0.5 = 13 - 6 = 7，所以c = √7",
        "knowledge_points": "余弦定理,解三角形",
        "score": 5
    },
    # 英语
    {
        "subject": "英语", "question_type": "single_choice", "difficulty": 0.3,
        "stem": "Choose the correct answer: She _____ to school every day.",
        "options": json.dumps([
            {"id": "A", "content": "go"},
            {"id": "B", "content": "goes"},
            {"id": "C", "content": "going"},
            {"id": "D", "content": "went"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "主语She是第三人称单数，一般现在时动词需加s/es，所以用goes。",
        "knowledge_points": "一般现在时,主谓一致,动词时态",
        "score": 5
    },
    {
        "subject": "英语", "question_type": "fill_blank", "difficulty": 0.4,
        "stem": "Complete the sentence: I have been learning English _____ I was 10 years old.",
        "options": json.dumps([], ensure_ascii=False),
        "answer": "since",
        "analysis": "现在完成进行时(have been doing)与since连用，表示从过去某一时间点开始持续到现在的动作。",
        "knowledge_points": "现在完成进行时,since用法",
        "score": 5
    },
    # 物理
    {
        "subject": "物理", "question_type": "single_choice", "difficulty": 0.4,
        "stem": "一物体从静止开始做匀加速直线运动，加速度为2m/s²，则2s末的速度为？",
        "options": json.dumps([
            {"id": "A", "content": "2 m/s"},
            {"id": "B", "content": "4 m/s"},
            {"id": "C", "content": "6 m/s"},
            {"id": "D", "content": "8 m/s"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "匀加速直线运动速度公式：v = v₀ + at = 0 + 2×2 = 4 m/s",
        "knowledge_points": "匀加速直线运动,运动学公式",
        "score": 5
    },
    {
        "subject": "物理", "question_type": "fill_blank", "difficulty": 0.5,
        "stem": "质量为2kg的物体，受到10N的水平推力作用，加速度为______m/s²（不计摩擦）。",
        "options": json.dumps([], ensure_ascii=False),
        "answer": "5",
        "analysis": "由牛顿第二定律F=ma，得a=F/m=10/2=5 m/s²",
        "knowledge_points": "牛顿第二定律,力与运动",
        "score": 5
    },
    # 化学
    {
        "subject": "化学", "question_type": "single_choice", "difficulty": 0.4,
        "stem": "下列物质中，属于电解质的是？",
        "options": json.dumps([
            {"id": "A", "content": "蔗糖"},
            {"id": "B", "content": "酒精"},
            {"id": "C", "content": "氯化钠"},
            {"id": "D", "content": "铜"}
        ], ensure_ascii=False),
        "answer": "C",
        "analysis": "电解质是在水溶液中或熔融状态下能导电的化合物。蔗糖、酒精是非电解质；铜是单质，既不是电解质也不是非电解质；氯化钠是强电解质。",
        "knowledge_points": "电解质,化合物分类",
        "score": 5
    },
    {
        "subject": "化学", "question_type": "fill_blank", "difficulty": 0.5,
        "stem": "水的化学式为______，其中氢元素和氧元素的质量比为______。",
        "options": json.dumps([], ensure_ascii=False),
        "answer": "H₂O;1:8",
        "analysis": "水分子由2个氢原子和1个氧原子构成，化学式为H₂O。质量比：(2×1):(1×16)=2:16=1:8",
        "knowledge_points": "化学式,元素质量比计算",
        "score": 5
    },
    # 生物
    {
        "subject": "生物", "question_type": "single_choice", "difficulty": 0.4,
        "stem": "细胞中含量最多的有机化合物是？",
        "options": json.dumps([
            {"id": "A", "content": "水"},
            {"id": "B", "content": "蛋白质"},
            {"id": "C", "content": "糖类"},
            {"id": "D", "content": "脂质"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "水是含量最多的无机化合物（占70%-90%）；蛋白质是含量最多的有机化合物（占7%-10%）。",
        "knowledge_points": "细胞化学成分,有机化合物",
        "score": 5
    },
    # 历史
    {
        "subject": "历史", "question_type": "single_choice", "difficulty": 0.3,
        "stem": "中国历史上第一个统一的中央集权封建国家是？",
        "options": json.dumps([
            {"id": "A", "content": "夏朝"},
            {"id": "B", "content": "商朝"},
            {"id": "C", "content": "秦朝"},
            {"id": "D", "content": "汉朝"}
        ], ensure_ascii=False),
        "answer": "C",
        "analysis": "公元前221年，秦始皇嬴政统一六国，建立了中国历史上第一个统一的中央集权封建国家——秦朝。",
        "knowledge_points": "中国古代史,秦朝建立",
        "score": 5
    },
    # 地理
    {
        "subject": "地理", "question_type": "single_choice", "difficulty": 0.3,
        "stem": "世界上面积最大的国家是？",
        "options": json.dumps([
            {"id": "A", "content": "中国"},
            {"id": "B", "content": "美国"},
            {"id": "C", "content": "加拿大"},
            {"id": "D", "content": "俄罗斯"}
        ], ensure_ascii=False),
        "answer": "D",
        "analysis": "俄罗斯面积约1709.8万平方千米，是世界上面积最大的国家，横跨亚欧大陆。",
        "knowledge_points": "世界地理,国家面积",
        "score": 5
    },
]

# 高等教育题库
HIGHER_EDU_QUESTIONS = [
    # 高等数学
    {
        "subject": "高等数学", "question_type": "single_choice", "difficulty": 0.6,
        "stem": "极限 lim(x→0) (sin x)/x 的值为？",
        "options": json.dumps([
            {"id": "A", "content": "0"},
            {"id": "B", "content": "1"},
            {"id": "C", "content": "∞"},
            {"id": "D", "content": "不存在"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "这是两个重要极限之一，可以用夹逼准则证明：lim(x→0)(sinx)/x = 1",
        "knowledge_points": "极限,重要极限,夹逼准则",
        "score": 10
    },
    {
        "subject": "高等数学", "question_type": "fill_blank", "difficulty": 0.7,
        "stem": "函数f(x) = ∫(0→x) sin(t²)dt，则f'(x) = ______。",
        "options": json.dumps([], ensure_ascii=False),
        "answer": "sin(x²)",
        "analysis": "由微积分基本定理（变上限积分求导）：d/dx ∫(a→x) f(t)dt = f(x)，所以f'(x) = sin(x²)",
        "knowledge_points": "微积分基本定理,变上限积分求导",
        "score": 10
    },
    # 线性代数
    {
        "subject": "线性代数", "question_type": "single_choice", "difficulty": 0.6,
        "stem": "设A为3阶方阵，且|A|=2，则|2A⁻¹|=？",
        "options": json.dumps([
            {"id": "A", "content": "1"},
            {"id": "B", "content": "2"},
            {"id": "C", "content": "4"},
            {"id": "D", "content": "8"}
        ], ensure_ascii=False),
        "answer": "C",
        "analysis": "|2A⁻¹| = 2³·|A⁻¹| = 8·(1/|A|) = 8·(1/2) = 4",
        "knowledge_points": "行列式,逆矩阵性质",
        "score": 10
    },
    # 数据结构
    {
        "subject": "数据结构", "question_type": "single_choice", "difficulty": 0.6,
        "stem": "在一个具有n个结点的二叉树中，所有结点的度数之和为？",
        "options": json.dumps([
            {"id": "A", "content": "n-1"},
            {"id": "B", "content": "n"},
            {"id": "C", "content": "n+1"},
            {"id": "D", "content": "2n-1"}
        ], ensure_ascii=False),
        "answer": "A",
        "analysis": "二叉树中边数等于结点度数之和，而n个结点的树有n-1条边，因此所有结点度数之和为n-1。",
        "knowledge_points": "二叉树,树的性质,结点度数",
        "score": 10
    },
    # 计算机网络
    {
        "subject": "计算机网络", "question_type": "single_choice", "difficulty": 0.5,
        "stem": "TCP/IP协议栈中，HTTP协议位于哪一层？",
        "options": json.dumps([
            {"id": "A", "content": "网络层"},
            {"id": "B", "content": "传输层"},
            {"id": "C", "content": "应用层"},
            {"id": "D", "content": "数据链路层"}
        ], ensure_ascii=False),
        "answer": "C",
        "analysis": "HTTP（超文本传输协议）是应用层协议，直接为用户的应用程序提供服务。",
        "knowledge_points": "TCP/IP协议栈,OSI七层模型,HTTP",
        "score": 10
    },
    {
        "subject": "计算机网络", "question_type": "fill_blank", "difficulty": 0.6,
        "stem": "IPv4地址由______位二进制数组成，默认子网掩码255.255.255.0对应的CIDR表示为______。",
        "options": json.dumps([], ensure_ascii=False),
        "answer": "32;/24",
        "analysis": "IPv4地址为32位二进制数。255.255.255.0转换为二进制是24个连续的1，因此CIDR表示为/24。",
        "knowledge_points": "IPv4地址,子网掩码,CIDR",
        "score": 10
    },
    # 操作系统
    {
        "subject": "操作系统", "question_type": "single_choice", "difficulty": 0.6,
        "stem": "下列进程调度算法中，可能出现饥饿现象的是？",
        "options": json.dumps([
            {"id": "A", "content": "先来先服务(FCFS)"},
            {"id": "B", "content": "短作业优先(SJF)"},
            {"id": "C", "content": "时间片轮转(RR)"},
            {"id": "D", "content": "多级反馈队列"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "SJF算法中，如果不断有短作业到达，长作业可能长期得不到调度，出现饥饿现象。",
        "knowledge_points": "进程调度算法,饥饿问题",
        "score": 10
    },
    # 数据库
    {
        "subject": "数据库原理", "question_type": "single_choice", "difficulty": 0.5,
        "stem": "关系数据库中，用来表示实体之间联系的是？",
        "options": json.dumps([
            {"id": "A", "content": "属性"},
            {"id": "B", "content": "关系"},
            {"id": "C", "content": "域"},
            {"id": "D", "content": "键"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "关系模型用二维表（关系）表示实体及实体间的联系，每个关系对应一张表。",
        "knowledge_points": "关系模型,E-R模型转换",
        "score": 10
    },
    # 宏观经济学
    {
        "subject": "宏观经济学", "question_type": "single_choice", "difficulty": 0.5,
        "stem": "GDP是指？",
        "options": json.dumps([
            {"id": "A", "content": "国民生产总值"},
            {"id": "B", "content": "国内生产总值"},
            {"id": "C", "content": "国民收入"},
            {"id": "D", "content": "个人可支配收入"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "GDP（Gross Domestic Product）即国内生产总值，是一国境内在一定时期内生产的所有最终产品和服务的市场价值。GNP是国民生产总值。",
        "knowledge_points": "国民收入核算,GDP定义",
        "score": 10
    },
]

# 职业教育题库
VOCATIONAL_QUESTIONS = [
    # 会计
    {
        "subject": "会计基础", "question_type": "single_choice", "difficulty": 0.4,
        "stem": "企业从银行取得短期借款，会引起？",
        "options": json.dumps([
            {"id": "A", "content": "资产增加，负债减少"},
            {"id": "B", "content": "资产增加，负债增加"},
            {"id": "C", "content": "资产减少，负债增加"},
            {"id": "D", "content": "资产减少，负债减少"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "取得借款：银行存款（资产）增加，短期借款（负债）增加，会计等式两边同时增加。",
        "knowledge_points": "会计等式,借贷记账法,经济业务影响",
        "score": 10
    },
    {
        "subject": "会计基础", "question_type": "fill_blank", "difficulty": 0.5,
        "stem": "会计的基本职能是______和______。",
        "options": json.dumps([], ensure_ascii=False),
        "answer": "核算;监督",
        "analysis": "会计的基本职能包括会计核算（反映职能）和会计监督（控制职能），核算是监督的基础，监督是核算的保障。",
        "knowledge_points": "会计基本职能,会计概述",
        "score": 10
    },
    # 市场营销
    {
        "subject": "市场营销", "question_type": "single_choice", "difficulty": 0.4,
        "stem": "4P营销组合理论不包括下列哪一项？",
        "options": json.dumps([
            {"id": "A", "content": "产品(Product)"},
            {"id": "B", "content": "价格(Price)"},
            {"id": "C", "content": "人员(People)"},
            {"id": "D", "content": "促销(Promotion)"}
        ], ensure_ascii=False),
        "answer": "C",
        "analysis": "4P理论包括：Product（产品）、Price（价格）、Place（渠道）、Promotion（促销）。People是7P服务营销理论中的要素。",
        "knowledge_points": "4P营销组合,营销策略",
        "score": 10
    },
    # 人力资源
    {
        "subject": "人力资源管理", "question_type": "single_choice", "difficulty": 0.4,
        "stem": "绩效考核的SMART原则中，'S'代表？",
        "options": json.dumps([
            {"id": "A", "content": "Special（特殊的）"},
            {"id": "B", "content": "Specific（具体的）"},
            {"id": "C", "content": "Simple（简单的）"},
            {"id": "D", "content": "Strategic（战略的）"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "SMART原则：S=Specific（具体明确）、M=Measurable（可衡量）、A=Achievable（可实现）、R=Relevant（相关性）、T=Time-bound（时限性）。",
        "knowledge_points": "绩效考核,SMART原则,目标管理",
        "score": 10
    },
    # 电工基础
    {
        "subject": "电工基础", "question_type": "single_choice", "difficulty": 0.5,
        "stem": "根据欧姆定律，电阻为10Ω的导体，两端电压为220V时，通过的电流为？",
        "options": json.dumps([
            {"id": "A", "content": "11A"},
            {"id": "B", "content": "22A"},
            {"id": "C", "content": "220A"},
            {"id": "D", "content": "0.045A"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "欧姆定律：I = U/R = 220V/10Ω = 22A",
        "knowledge_points": "欧姆定律,电路基础,电流计算",
        "score": 10
    },
    # 机械基础
    {
        "subject": "机械基础", "question_type": "single_choice", "difficulty": 0.5,
        "stem": "下列哪种传动方式可以实现两轴平行的传动？",
        "options": json.dumps([
            {"id": "A", "content": "锥齿轮传动"},
            {"id": "B", "content": "蜗杆蜗轮传动"},
            {"id": "C", "content": "直齿圆柱齿轮传动"},
            {"id": "D", "content": "交叉带传动"}
        ], ensure_ascii=False),
        "answer": "C",
        "analysis": "直齿圆柱齿轮传动用于两平行轴之间的传动；锥齿轮用于两相交轴；蜗杆蜗轮用于两交错轴；交叉带用于两交错轴。",
        "knowledge_points": "机械传动,齿轮传动类型",
        "score": 10
    },
    # 法律基础
    {
        "subject": "法律基础", "question_type": "single_choice", "difficulty": 0.4,
        "stem": "我国《民法典》规定，普通诉讼时效期间为？",
        "options": json.dumps([
            {"id": "A", "content": "1年"},
            {"id": "B", "content": "2年"},
            {"id": "C", "content": "3年"},
            {"id": "D", "content": "20年"}
        ], ensure_ascii=False),
        "answer": "C",
        "analysis": "《民法典》第188条规定，向人民法院请求保护民事权利的诉讼时效期间为3年。自知道或应当知道权利受到损害之日起计算。",
        "knowledge_points": "诉讼时效,民法典,民事权利",
        "score": 10
    },
]

# IT技能题库
IT_SKILLS_QUESTIONS = [
    # Python
    {
        "subject": "Python编程", "question_type": "single_choice", "difficulty": 0.3,
        "stem": "Python中，下列哪个不是不可变类型？",
        "options": json.dumps([
            {"id": "A", "content": "int"},
            {"id": "B", "content": "str"},
            {"id": "C", "content": "list"},
            {"id": "D", "content": "tuple"}
        ], ensure_ascii=False),
        "answer": "C",
        "analysis": "Python不可变类型：int、float、str、tuple、frozenset、bool；可变类型：list、dict、set、bytearray。",
        "knowledge_points": "Python数据类型,可变不可变",
        "score": 10
    },
    {
        "subject": "Python编程", "question_type": "fill_blank", "difficulty": 0.4,
        "stem": "Python列表推导式 [x**2 for x in range(5)] 的结果是______。",
        "options": json.dumps([], ensure_ascii=False),
        "answer": "[0, 1, 4, 9, 16]",
        "analysis": "range(5)产生0,1,2,3,4；x**2计算平方，结果为[0, 1, 4, 9, 16]",
        "knowledge_points": "列表推导式,range函数",
        "score": 10
    },
    # Java
    {
        "subject": "Java编程", "question_type": "single_choice", "difficulty": 0.4,
        "stem": "Java中，下列关于String类的说法正确的是？",
        "options": json.dumps([
            {"id": "A", "content": "String类是可变的"},
            {"id": "B", "content": "String类继承自StringBuilder"},
            {"id": "C", "content": "String类是final类，不可被继承"},
            {"id": "D", "content": "String对象只能通过new关键字创建"}
        ], ensure_ascii=False),
        "answer": "C",
        "analysis": "String类是final类，不可被继承；String是不可变对象（immutable）；字符串可以通过字面量直接创建。",
        "knowledge_points": "Java String类,不可变类,final关键字",
        "score": 10
    },
    # JavaScript
    {
        "subject": "JavaScript", "question_type": "single_choice", "difficulty": 0.4,
        "stem": "JavaScript中，typeof null 的结果是？",
        "options": json.dumps([
            {"id": "A", "content": "'null'"},
            {"id": "B", "content": "'undefined'"},
            {"id": "C", "content": "'object'"},
            {"id": "D", "content": "'number'"}
        ], ensure_ascii=False),
        "answer": "C",
        "analysis": "这是JavaScript的一个历史遗留bug，typeof null返回'object'。正确区分null需要用 === null。",
        "knowledge_points": "JS数据类型,typeof运算符,JS历史特性",
        "score": 10
    },
    # SQL
    {
        "subject": "SQL数据库", "question_type": "single_choice", "difficulty": 0.4,
        "stem": "下列SQL语句中，用于从表中删除数据的是？",
        "options": json.dumps([
            {"id": "A", "content": "DROP"},
            {"id": "B", "content": "DELETE"},
            {"id": "C", "content": "TRUNCATE"},
            {"id": "D", "content": "REMOVE"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "DELETE用于删除表中数据（可带WHERE条件，可回滚）；DROP删除整个表结构；TRUNCATE清空表数据（不可回滚）；REMOVE不是标准SQL。",
        "knowledge_points": "SQL DML,DELETE语句,数据操作",
        "score": 10
    },
    {
        "subject": "SQL数据库", "question_type": "fill_blank", "difficulty": 0.5,
        "stem": "查询学生表中成绩大于80分的学生姓名，SQL语句为：SELECT s_name FROM student ______ score > 80;",
        "options": json.dumps([], ensure_ascii=False),
        "answer": "WHERE",
        "analysis": "WHERE子句用于筛选满足条件的记录，放在FROM之后，GROUP BY之前。",
        "knowledge_points": "SQL查询,WHERE条件子句",
        "score": 10
    },
    # Linux
    {
        "subject": "Linux运维", "question_type": "single_choice", "difficulty": 0.4,
        "stem": "Linux中，查看当前目录下所有文件（包括隐藏文件）的命令是？",
        "options": json.dumps([
            {"id": "A", "content": "ls"},
            {"id": "B", "content": "ls -l"},
            {"id": "C", "content": "ls -a"},
            {"id": "D", "content": "ls -h"}
        ], ensure_ascii=False),
        "answer": "C",
        "analysis": "ls -a 显示所有文件包括隐藏文件；ls -l 显示详细信息；ls -h 人类可读格式；默认ls不显示隐藏文件。",
        "knowledge_points": "Linux命令,ls参数,文件查看",
        "score": 10
    },
    # Docker
    {
        "subject": "Docker容器", "question_type": "single_choice", "difficulty": 0.5,
        "stem": "Docker中，用于创建镜像的文件是？",
        "options": json.dumps([
            {"id": "A", "content": "docker-compose.yml"},
            {"id": "B", "content": "Dockerfile"},
            {"id": "C", "content": ".dockerignore"},
            {"id": "D", "content": "docker.env"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "Dockerfile是构建Docker镜像的脚本文件，包含构建指令；docker-compose.yml用于编排多容器服务；.dockerignore是忽略文件列表。",
        "knowledge_points": "Docker镜像构建,Dockerfile,容器技术",
        "score": 10
    },
    # Git
    {
        "subject": "Git版本控制", "question_type": "single_choice", "difficulty": 0.4,
        "stem": "Git中，用于查看提交历史的命令是？",
        "options": json.dumps([
            {"id": "A", "content": "git status"},
            {"id": "B", "content": "git log"},
            {"id": "C", "content": "git diff"},
            {"id": "D", "content": "git show"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "git log查看提交历史；git status查看工作区状态；git diff查看差异；git show查看某次提交详情。",
        "knowledge_points": "Git命令,提交历史,版本控制",
        "score": 10
    },
]

# 日语题库
JAPANESE_QUESTIONS = [
    {
        "subject": "日语", "question_type": "single_choice", "difficulty": 0.3,
        "stem": "「こんにちは」的中文意思是？",
        "options": json.dumps([
            {"id": "A", "content": "早上好"},
            {"id": "B", "content": "你好（白天）"},
            {"id": "C", "content": "晚上好"},
            {"id": "D", "content": "晚安"}
        ], ensure_ascii=False),
        "answer": "B",
        "analysis": "こんにちは（konnichiwa）：白天打招呼用的「你好」；早上好：おはようございます；晚上好：こんばんは；晚安：おやすみなさい。",
        "knowledge_points": "日语寒暄语,N5词汇,打招呼",
        "score": 5
    },
    {
        "subject": "日语", "question_type": "fill_blank", "difficulty": 0.4,
        "stem": "日语中，「ありがとう」的平假名是______，意思是______。",
        "options": json.dumps([], ensure_ascii=False),
        "answer": "ありがとう;谢谢",
        "analysis": "ありがとう（arigatou）：谢谢；敬体形式：ありがとうございます。",
        "knowledge_points": "日语常用语,N5词汇,感谢表达",
        "score": 5
    },
    {
        "subject": "日语", "question_type": "single_choice", "difficulty": 0.5,
        "stem": "下列动词中，属于五段动词（一类动词）的是？",
        "options": json.dumps([
            {"id": "A", "content": "食べる（たべる）"},
            {"id": "B", "content": "見る（みる）"},
            {"id": "C", "content": "飲む（のむ）"},
            {"id": "D", "content": "来る（くる）"}
        ], ensure_ascii=False),
        "answer": "C",
        "analysis": "五段动词：词尾在う段上，且倒数第二个假名不在い段或え段（特殊除外）。飲む（のむ）：五段动词；食べる、見る：一段动词；来る：カ变动词。",
        "knowledge_points": "日语动词分类,五段动词,一类动词",
        "score": 5
    },
]

# 汇总所有题库
ALL_QUESTIONS = K12_QUESTIONS + HIGHER_EDU_QUESTIONS + VOCATIONAL_QUESTIONS + IT_SKILLS_QUESTIONS + JAPANESE_QUESTIONS


# ========== 脑库知识数据 ==========

BRAIN_KNOWLEDGE = [
    # ===== 系统架构知识 =====
    {"type": "system", "domain": "系统架构", "topic": "MTSCOS系统分层架构", "content": "MTSCOS系统采用六层架构：1)表现层(Element Plus前端) 2)路由层(Flask Blueprint+权限装饰器) 3)服务层(140+业务服务) 4)引擎层(12核心引擎) 5)数据层(SQLite分库) 6)基础设施层(监控/日志/备份)。层间通过清晰接口解耦，支持独立演进。", "priority": 9},
    {"type": "system", "domain": "系统架构", "topic": "数据库分片策略", "content": "MTSCOS采用垂直分片策略：app.db(主业务)、question.db(题库)、ai.db(AI脑库)、learning.db(学习记录)、exam.db(考试数据)、log.db(日志)、user.db(用户)、auth.db(认证)。各分片通过core/db_path统一管理路由。", "priority": 8},
    {"type": "system", "domain": "系统架构", "topic": "12核心引擎列表", "content": "MTSCOS 12核心引擎：1)AI自学引擎 2)自动巡检引擎 3)巡检小队引擎 4)自动修复引擎 5)脑库投喂引擎 6)深度检查引擎 7)EigenFlux广播引擎 8)EigenFlux主动引擎 9)全域防御引擎 10)验证轮引擎 11)工作流引擎 12)自动开发团队引擎。", "priority": 9},
    {"type": "system", "domain": "系统架构", "topic": "AI员工赋能体系", "content": "AI员工赋能三级体系：L1基础层(性格模拟+任务执行)→L2增强层(网络学习+脑库学习+技能关联)→L3进化层(自我发现+自动升级+神经网络训练)。每升一级需要通过熟练度阈值(0.8)和能力评估。", "priority": 8},
    {"type": "system", "domain": "系统架构", "topic": "AI集群协调机制", "content": "AI集群采用Master-Worker架构：1)主控节点负责任务分发与结果汇总 2)执行节点承载具体任务 3)辅助节点提供资源支持 4)监控节点实时追踪进度。调度策略：轮询+优先级+负载均衡。", "priority": 7},

    # ===== AI运维知识 =====
    {"type": "training", "domain": "AI运维", "topic": "自动巡检闭环流程", "content": "自动巡检五步法闭环：1)发现问题(规则/AI检测)→2)诊断分析(日志/指标/上下文)→3)修复方案(模板/AI生成)→4)执行修复(安全沙箱+回滚)→5)验证确认(多维度检查+写入知识库)。失败自动升级到人工处理。", "priority": 9},
    {"type": "training", "domain": "AI运维", "topic": "数据库维护规范", "content": "SQLite数据库日常维护：1)每日VACUUM整理碎片 2)每日完整性检查PRAGMA integrity_check 3)每周索引优化REINDEX 4)慢查询日志分析 5)读写分离(只读副本) 6)WAL模式配置 7)连接池参数调优。", "priority": 8},
    {"type": "training", "domain": "AI运维", "topic": "日志分级与告警策略", "content": "日志五级分级：DEBUG(调试)<INFO(一般)<WARNING(警告)<ERROR(错误)<CRITICAL(致命)。告警策略：ERROR级5分钟内未处理升级，CRITICAL级立即短信+邮件+飞书三重通知。告警去重：同类型10分钟内合并。", "priority": 8},
    {"type": "training", "domain": "AI运维", "topic": "容器化部署标准", "content": "Docker容器部署标准：1)镜像体积<500MB(多阶段构建) 2)健康检查HEALTHCHECK 3)资源限制(cpu/mem) 4)非root用户运行 5)日志重定向到stdout 6)优雅停止(STOPSIGNAL SIGTERM+30s宽限期) 7)标签规范(name/version/commit)。", "priority": 7},
    {"type": "training", "domain": "AI运维", "topic": "备份与恢复策略", "content": "3-2-1备份原则：3份备份、2种介质、1份异地。MTSCOS备份：1)每2小时增量备份到本地SSD 2)每日全量备份到OneDrive云 3)每周完整备份到外置硬盘。恢复RTO<4小时、RPO<2小时。", "priority": 9},
    {"type": "training", "domain": "AI运维", "topic": "性能瓶颈排查顺序", "content": "性能排查优先级：1)数据库(慢查询/索引/锁)→2)应用层(缓存命中率/算法复杂度/连接泄漏)→3)网络(带宽/延迟/丢包)→4)系统(CPU/内存/磁盘IO)→5)架构(水平扩展/读写分离/CDN)。每步量化数据后再行动。", "priority": 8},

    # ===== 安全防护知识 =====
    {"type": "system", "domain": "安全防护", "topic": "SQL注入防御三层防线", "content": "SQL注入防御：L1代码层(参数化查询/ORM)→L2中间件层(WAF规则/输入过滤)→L3数据库层(最小权限账号/只读分离/审计日志)。检测规则：关键词union/select/drop/--/';/sleep()/benchmark()等。", "priority": 9},
    {"type": "system", "domain": "安全防护", "topic": "XSS防御四件套", "content": "XSS防御：1)输入验证(白名单过滤) 2)输出转义(HTML/JS/URL上下文转义) 3)CSP内容安全策略(限制script-src) 4)HttpOnly Cookie(防止JS窃取)。存储型XSS危害最大，需重点防护。", "priority": 8},
    {"type": "system", "domain": "安全防护", "topic": "超级管理员七要素认证", "content": "SA七要素强认证：1)用户名唯一性(wuchenghao15) 2)密码强度(PBKDF2-HMAC-SHA256+10万轮+32字节盐) 3)VIKEY硬件加密狗(USB序列号+芯片ID) 4)IP白名单(仅内网IP段) 5)设备指纹 6)登录时间窗(08:00-23:00) 7)行为基线(5s<4次请求)。", "priority": 10},
    {"type": "system", "domain": "安全防护", "topic": "用户容器六字段验证", "content": "用户容器强制验证六要素：1)user_group(用户组别) 2)permission_code(权限识别码) 3)login_status(登录状态) 4)is_abnormal(是否异常) 5)is_legal(是否合法) 6)login_timestamp(唯一登录时间戳)。任何一项不合法立即跳转登录页。", "priority": 10},
    {"type": "system", "domain": "安全防护", "topic": "CSRF防护实现", "content": "CSRF防护三管齐下：1)Synchronizer Token Pattern(表单植入CSRF Token) 2)SameSite Cookie属性(Lax/Strict) 3)Referer/Origin校验。敏感操作(修改/删除/转账)必须强制校验。", "priority": 8},

    # ===== 技术知识 =====
    {"type": "technical", "domain": "Python", "topic": "Flask Blueprint最佳实践", "content": "Flask Blueprint模块化：1)按领域拆分(auth/user/admin/edu/ai) 2)每个Blueprint独立templates/static 3)url_prefix统一前缀 4)before_request做权限校验 5)errorhandler独立错误页 6)register_blueprint时设置url_prefix和subdomain。", "priority": 8},
    {"type": "technical", "domain": "Python", "topic": "SQLAlchemy性能优化", "content": "SQLAlchemy ORM性能优化：1)eager loading解决N+1(selectinload/joinedload) 2)lazy=dynamic动态查询 3)with_entities只取需要字段 4)yield_per分批处理 5)编译原生SQL复杂查询 6)二级缓存(可配合Redis)。", "priority": 8},
    {"type": "technical", "domain": "Python", "topic": "装饰器实现权限控制", "content": "@system_container权限装饰器实现：1)functools.wraps保留原函数元信息 2)解析request获取用户容器 3)验证六字段合法性 4)检查require_auth级别(guest/login/admin/super_admin) 5)检查allowed_roles列表 6)通过则调用原函数，失败返回401/403。", "priority": 9},
    {"type": "technical", "domain": "Python", "topic": "异步任务队列架构", "content": "Celery异步架构：Broker(Redis/RabbitMQ)→Worker(多进程/gevent)→Result Backend。任务分类：CPU密集用prefork池、IO密集用gevent。关键配置：task_acks_late=True(防止worker崩溃丢任务)、task_reject_on_worker_lost=True。", "priority": 7},
    {"type": "technical", "domain": "前端", "topic": "Vue3组合式API性能优化", "content": "Vue3性能优化：1)ref用于基础类型/reactive用于对象 2)computed缓存计算结果 3)watch明确指定immediate/deep 4)shallowRef/shallowReactive跳过深层响应 5)defineProps/defineEmits编译器宏 6)onMounted异步数据预取 7)v-memo缓存长列表渲染。", "priority": 7},
    {"type": "technical", "domain": "前端", "topic": "Element Plus设计Token体系", "content": "Element Plus设计Token：1)颜色令牌(el-color-primary/el-color-success/el-color-warning) 2)字体令牌(el-font-size-common/el-font-weight-primary) 3)间距令牌(el-spacing-xs~xxl) 4)边框令牌(el-border-radius) 5)阴影令牌(el-box-shadow)。禁止硬编码颜色/尺寸。", "priority": 8},
    {"type": "technical", "domain": "前端", "topic": "响应式设计断点策略", "content": "响应式断点：xs<768px(手机)→sm≥768px(平板竖)→md≥992px(平板横/小笔电)→lg≥1200px(桌面)→xl≥1920px(大屏)。策略：mobile-first，先写xs样式，逐级增强。图片用srcset/sizes适配。", "priority": 7},

    # ===== 教育理论知识 =====
    {"type": "business", "domain": "教育理论", "topic": "布卢姆认知目标分类", "content": "布卢姆教育目标分类(修订版)：认知领域六级：1)记忆(Remember) 2)理解(Understand) 3)应用(Apply) 4)分析(Analyze) 5)评价(Evaluate) 6)创造(Create)。题库难度对应：难度0-0.3(记忆/理解)→0.3-0.6(应用/分析)→0.6-1(评价/创造)。", "priority": 9},
    {"type": "business", "domain": "教育理论", "topic": "最近发展区(ZPD)理论", "content": "维果茨基ZPD理论：学生独立解决问题的现有发展水平，与在成人指导下可达到的潜在发展水平之间的差距，即最近发展区。教学应走在发展前面，题目推荐应定位在ZPD内(学生答对率60%-75%)，既不太难也不太易。", "priority": 9},
    {"type": "business", "domain": "教育理论", "topic": "艾宾浩斯遗忘曲线", "content": "艾宾浩斯遗忘规律：学习后20分钟遗忘42%、1小时遗忘56%、1天遗忘74%、1周遗忘77%。复习间隔建议：1天后→3天后→7天后→15天后→30天后。复习系统应按此曲线自动触发复习任务。", "priority": 9},
    {"type": "business", "domain": "教育理论", "topic": "IRT三参数逻辑斯蒂模型", "content": "IRT(项目反应理论)3PL模型：P(θ) = c + (1-c)/(1+exp(-Da(θ-b)))。θ：学生能力；a：题目区分度；b：题目难度；c：猜测系数(选择题25%)。可用于：1)精准评估学生能力 2)题目质量筛选 3)自适应选题。", "priority": 8},
    {"type": "business", "domain": "教育系统", "topic": "K12年级分层管理", "content": "K12教育分层：小学(1-6年级,6-12岁)→初中(7-9年级,12-15岁,义务教育)→高中(10-12年级,15-18岁)。权限控制：义务教育阶段(1-9)数据修改需教务主任审批；毕业年级(9/12)成绩锁定不可修改；跨年级题目共享需教研员审核。", "priority": 8},
    {"type": "business", "domain": "教育系统", "topic": "多维度考试评价体系", "content": "考试评价五维度：1)知识维度(知识点覆盖/掌握程度) 2)能力维度(布卢姆六级) 3)难度维度(基础/中档/难题比例3:5:2) 4)速度维度(单位时间得分率) 5)稳定维度(多次考试波动系数)。维度权重按考试类型动态调整。", "priority": 8},

    # ===== 项目经验知识 =====
    {"type": "experience", "domain": "项目经验", "topic": "数据同步写穿机制", "content": "写穿(Write-Through)缓存策略：写操作必须同时更新缓存和数据库，成功后才返回。优点：数据一致性强；缺点：写延迟增加。适用场景：一致性要求高的用户权限、参数配置。对比：写回(Write-Back)先写缓存异步刷库，性能高但有丢失风险。", "priority": 8},
    {"type": "experience", "domain": "项目经验", "topic": "RBAC权限设计模式", "content": "RBAC模型设计：用户→角色→权限三级映射。扩展：1)角色继承(admin包含user权限) 2)互斥角色(不能同时拥有财务和审计) 3)权限缓存(用户登录时加载权限树到Redis，TTL=30min) 4)审计日志(权限变更全记录)。", "priority": 8},
    {"type": "experience", "domain": "项目经验", "topic": "统一异常处理架构", "content": "全局异常处理三层：1)Flask @app.errorhandler(顶层兜底) 2)自定义BusinessException(业务异常带错误码和提示) 3)service层try-catch(记录上下文后抛出)。错误上下文JSON包含：trace_id、user_id、request_params、timestamp、error_stack。", "priority": 9},
    {"type": "experience", "domain": "项目经验", "topic": "性能优化四层方法论", "content": "性能优化四层：L1数据库(索引/SQL优化/分库分表)→L2缓存(Redis本地缓存/CDN/浏览器缓存)→L3代码(算法优化/异步/批处理/连接池)→L4架构(负载均衡/读写分离/微服务/静态化)。每步优化前后压测对比，数据驱动。", "priority": 8},
    {"type": "experience", "domain": "项目经验", "topic": "Git分支管理策略", "content": "Git Flow工作流：master(生产)→develop(开发)→feature/*(功能分支,从develop切)→release/*(发布分支)→hotfix/*(紧急修复,从master切)。合并规则：feature→develop(PR+CR)、develop→release(冻结新功能)、release→master+develop(双合并打标签)。", "priority": 8},

    # ===== AI脑库与神经网络 =====
    {"type": "system", "domain": "AI架构", "topic": "神经元信号传递机制", "content": "神经网络信号传递：输入→Σ(weight_i × input_i) + bias→激活函数(ReLU/Sigmoid/Tanh)→输出。ReLU：f(x)=max(0,x)，解决梯度消失；Sigmoid：f(x)=1/(1+e^-x)，输出0-1用于二分类；Tanh：输出-1~1零中心化。", "priority": 7},
    {"type": "system", "domain": "AI架构", "topic": "脑库知识全生命周期", "content": "知识六阶段生命周期：1)采集(系统池/网络/人工)→2)验证(去重/质量/敏感检测)→3)索引(标签/优先级/向量)→4)存储(ai_brain_knowledge表+向量库)→5)增强(关联/聚类/版本)→6)退役(过期/低质量归档)。记录每阶段审计日志。", "priority": 8},
    {"type": "system", "domain": "AI架构", "topic": "神经网络修剪策略", "content": "神经网络剪枝：1)权重剪枝(weight<0.1的连接置为pruned状态) 2)结构化剪枝(删除准确率低的整个节点) 3)正则化辅助(L1/L2正则化使权重稀疏化)。剪枝后需重新训练1-2个epoch恢复精度。阈值可配置(BRAIN_NEURAL_PRUNE_THRESHOLD)。", "priority": 7},
    {"type": "system", "domain": "AI架构", "topic": "AI学习触发条件判断", "content": "AI学习触发条件：1)定时触发(每小时低优先级学习) 2)新知识投喂触发(立即学习) 3)任务失败触发(针对失败领域强化学习) 4)能力评估触发(熟练度低于阈值强制补课) 5)人工指令触发(管理员指定学习内容)。", "priority": 9},

    # ===== 数据规范 =====
    {"type": "system", "domain": "数据规范", "topic": "题库难度映射标准", "content": "难度0-1映射：0.0-0.25(送分题,知识点直接对应)→0.25-0.45(基础题,单步推理)→0.45-0.65(中档题,多步推理)→0.65-0.85(难题,综合应用)→0.85-1.0(压轴题,创新/竞赛)。组卷难度配比基础:中档:难题=3:5:2或4:4:2。", "priority": 8},
    {"type": "system", "domain": "数据规范", "topic": "ID生成规范", "content": "ID三段式：前缀-时间戳-随机数。例：K-20260815120000-1234(知识ID)、Q-MATH-20260815-5678(题目ID)、F-20260815120000-9012(投喂ID)。前缀类型：K(知识)、Q(题目)、L(学习)、U(升级)、C(集群)、NN(神经网络节点)。", "priority": 8},
]


# ========== 数据库初始化 ==========

def init_question_tables(conn):
    """初始化题库相关表"""
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS question_bank_items (
            question_id TEXT PRIMARY KEY,
            subject TEXT,
            question_type TEXT,
            stem TEXT,
            options TEXT,
            answer TEXT,
            analysis TEXT,
            knowledge_points TEXT,
            difficulty REAL DEFAULT 0.5,
            score REAL DEFAULT 5.0,
            source TEXT DEFAULT 'feeding_script',
            equivalent_group TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS question_bank (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT DEFAULT 'chinese',
            category TEXT,
            difficulty INTEGER DEFAULT 3,
            content TEXT,
            options TEXT,
            correct_answer TEXT,
            explanation TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS question_bank_evolution_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evolution_type TEXT NOT NULL,
            question_id TEXT,
            action TEXT,
            details TEXT,
            ai_agent TEXT,
            confidence REAL,
            created_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS question_bank_quality_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT UNIQUE NOT NULL,
            difficulty_score REAL DEFAULT 0.5,
            usage_count INTEGER DEFAULT 0,
            correct_rate REAL DEFAULT 0.0,
            positive_feedback INTEGER DEFAULT 0,
            negative_feedback INTEGER DEFAULT 0,
            quality_score REAL DEFAULT 0.0,
            discrimination REAL DEFAULT 0.0,
            avg_response_time REAL DEFAULT 0.0,
            last_calibrated TEXT,
            created_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS question_bank_lifecycle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            stage_changed_at TEXT,
            changed_by TEXT,
            notes TEXT
        )
    ''')

    conn.commit()
    logger.info("✓ 题库表初始化完成")


def init_brain_tables(conn):
    """初始化脑库相关表"""
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS ai_brain_knowledge (
            knowledge_id TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            knowledge_type TEXT,
            source TEXT,
            tags TEXT,
            priority INTEGER DEFAULT 5,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS brain_feeding_queue (
            feed_id TEXT PRIMARY KEY,
            feed_type TEXT,
            feed_source TEXT,
            feed_data TEXT,
            knowledge_type TEXT,
            priority INTEGER,
            status TEXT,
            scheduled_at TEXT,
            data_size INTEGER,
            tags TEXT,
            description TEXT,
            created_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS ai_brain_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            knowledge_id TEXT,
            activity_type TEXT,
            details TEXT,
            timestamp TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS neural_network_nodes (
            node_id TEXT PRIMARY KEY,
            node_type TEXT,
            node_name TEXT,
            node_layer INTEGER,
            node_layer_name TEXT,
            activation_function TEXT,
            weight REAL,
            bias REAL,
            threshold REAL,
            status TEXT,
            processing_capacity REAL,
            current_load REAL,
            accuracy REAL,
            training_count INTEGER DEFAULT 0,
            created_at TEXT,
            last_trained TEXT,
            updated_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS neural_network_connections (
            connection_id TEXT PRIMARY KEY,
            source_node_id TEXT,
            target_node_id TEXT,
            connection_type TEXT,
            weight REAL,
            signal_strength REAL,
            status TEXT,
            learning_rate REAL,
            activation_count INTEGER DEFAULT 0,
            last_activated TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS brain_learning_records (
            record_id TEXT PRIMARY KEY,
            employee_id TEXT,
            employee_name TEXT,
            learning_type TEXT,
            domain TEXT,
            topic TEXT,
            content_summary TEXT,
            proficiency_before REAL,
            proficiency_after REAL,
            proficiency_gain REAL,
            learning_duration REAL,
            knowledge_id TEXT,
            learning_method TEXT,
            mastery_level TEXT,
            practice_count INTEGER,
            created_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS ai_upgrade_records (
            upgrade_id TEXT PRIMARY KEY,
            employee_id TEXT,
            employee_name TEXT,
            upgrade_type TEXT,
            upgrade_category TEXT,
            before_level INTEGER,
            after_level INTEGER,
            before_capabilities TEXT,
            after_capabilities TEXT,
            upgrade_score REAL,
            upgrade_data TEXT,
            upgrade_reason TEXT,
            status TEXT,
            performed_by TEXT,
            created_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS cluster_coordination_records (
            coordination_id TEXT PRIMARY KEY,
            cluster_id TEXT,
            coordination_type TEXT,
            task_description TEXT,
            participating_employees TEXT,
            task_assignment TEXT,
            coordination_strategy TEXT,
            result TEXT,
            efficiency_score REAL,
            duration_seconds REAL,
            status TEXT,
            created_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS brain_feeding_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stat_date TEXT UNIQUE,
            total_feeds INTEGER DEFAULT 0,
            total_learnings INTEGER DEFAULT 0,
            total_upgrades INTEGER DEFAULT 0,
            total_coordinations INTEGER DEFAULT 0,
            knowledge_count INTEGER DEFAULT 0,
            active_nodes INTEGER DEFAULT 0,
            active_connections INTEGER DEFAULT 0,
            avg_proficiency REAL,
            avg_accuracy REAL,
            neural_network_density REAL,
            cluster_efficiency REAL,
            created_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS system_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_code TEXT UNIQUE,
            rule_name TEXT,
            rule_value TEXT,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS system_maintenance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT,
            target TEXT,
            result TEXT,
            details TEXT,
            timestamp TEXT
        )
    ''')

    conn.commit()
    logger.info("✓ 脑库表初始化完成")


# ========== 投喂函数 ==========

def feed_question_bank(conn):
    """投喂题库"""
    cur = conn.cursor()
    fed_count = 0
    skipped = 0
    now = datetime.now().isoformat()

    for i, q in enumerate(ALL_QUESTIONS):
        try:
            # 生成题目ID
            qid = f"Q-{q['subject'][:2].upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{1000+i:04d}"

            # 去重检查
            cur.execute("SELECT COUNT(*) FROM question_bank_items WHERE stem = ? AND subject = ?",
                       (q['stem'], q['subject']))
            if cur.fetchone()[0] > 0:
                skipped += 1
                continue

            # 写入question_bank_items（标准格式）
            cur.execute('''
                INSERT OR IGNORE INTO question_bank_items
                (question_id, subject, question_type, stem, options, answer, analysis,
                 knowledge_points, difficulty, score, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                qid, q['subject'], q['question_type'], q['stem'], q['options'],
                q['answer'], q['analysis'], q.get('knowledge_points', ''),
                q.get('difficulty', 0.5), q.get('score', 5),
                'feeding_script', now, now
            ))

            # 同步写入question_bank（兼容旧格式）
            difficulty_int = max(1, min(5, int(q.get('difficulty', 0.5) * 5) + 1))
            cur.execute('''
                INSERT INTO question_bank
                (category, difficulty, content, options, correct_answer, explanation, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                q['subject'], difficulty_int, q['stem'], q['options'],
                q['answer'], q['analysis'], now, now
            ))

            # 写入生命周期记录
            cur.execute('''
                INSERT INTO question_bank_lifecycle
                (question_id, stage, stage_changed_at, changed_by, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (qid, 'published', now, 'feeding_script', '脚本批量投喂初始化'))

            # 写入质量指标
            cur.execute('''
                INSERT OR IGNORE INTO question_bank_quality_metrics
                (question_id, difficulty_score, created_at)
                VALUES (?, ?, ?)
            ''', (qid, q.get('difficulty', 0.5), now))

            # 写入进化日志
            cur.execute('''
                INSERT INTO question_bank_evolution_log
                (evolution_type, question_id, action, details, ai_agent, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('generate', qid, 'insert',
                  f'脚本投喂{q["subject"]}题目，难度{q.get("difficulty", 0.5):.2f}',
                  'feeding_script', 0.95, now))

            fed_count += 1
        except Exception as e:
            logger.error(f"  ✗ 写入题目失败[{i}]: {e}")

    conn.commit()
    logger.info(f"✓ 题库投喂完成: 新增{fed_count}道, 跳过{skipped}道重复")
    return fed_count


def feed_brain_knowledge(conn):
    """投喂脑库知识"""
    cur = conn.cursor()
    fed_count = 0
    skipped = 0
    now = datetime.now().isoformat()

    for i, k in enumerate(BRAIN_KNOWLEDGE):
        try:
            # 生成知识ID
            kid = f"K-FEED-{datetime.now().strftime('%Y%m%d%H%M%S')}-{1000+i:04d}"

            # 去重检查
            cur.execute("SELECT COUNT(*) FROM ai_brain_knowledge WHERE title = ?", (k['topic'],))
            if cur.fetchone()[0] > 0:
                skipped += 1
                continue

            # 写入知识表
            tags = f"{k['domain']},{k['type']}"
            cur.execute('''
                INSERT INTO ai_brain_knowledge
                (knowledge_id, title, content, knowledge_type, source, tags,
                 priority, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                kid, k['topic'], k['content'], k['type'],
                'feeding_script', tags, k.get('priority', 5),
                'active', now, now
            ))

            # 写入投喂队列记录
            fid = f"F-{datetime.now().strftime('%Y%m%d%H%M%S')}-{1000+i:04d}"
            feed_data = json.dumps(k, ensure_ascii=False)
            cur.execute('''
                INSERT INTO brain_feeding_queue
                (feed_id, feed_type, feed_source, feed_data, knowledge_type, priority,
                 status, scheduled_at, data_size, tags, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fid, 'knowledge', 'feeding_script', feed_data, k['type'],
                k.get('priority', 5), 'completed', now,
                len(k['content'].encode('utf-8')), k['domain'],
                f"投喂知识: {k['domain']}-{k['topic']}", now
            ))

            # 写入脑库活动
            cur.execute('''
                INSERT INTO ai_brain_activity
                (knowledge_id, activity_type, details, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (kid, 'fed', f"批量脚本投喂到脑库: {k['topic']}", now))

            fed_count += 1
        except Exception as e:
            logger.error(f"  ✗ 写入知识失败[{i}]: {e}")

    conn.commit()
    logger.info(f"✓ 脑库投喂完成: 新增{fed_count}条, 跳过{skipped}条重复")
    return fed_count


def init_neural_network(conn):
    """初始化基础神经网络节点（如果为空）"""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM neural_network_nodes")
    if cur.fetchone()[0] > 0:
        logger.info("  神经网络已存在节点，跳过初始化")
        return 0

    logger.info("  初始化神经网络基础节点...")
    layers = [
        ('input', 0, '输入层', ['数据采集', '知识输入', '任务接收', '信号感知']),
        ('hidden1', 1, '隐藏层1-特征提取', ['特征分析', '模式识别', '知识匹配', '意图理解']),
        ('hidden2', 2, '隐藏层2-决策推理', ['策略选择', '风险评估', '资源规划', '任务分解']),
        ('hidden3', 3, '隐藏层3-执行控制', ['执行调度', '监控反馈', '异常处理', '结果验证']),
        ('output', 4, '输出层', ['任务输出', '知识输出', '决策输出', '状态上报']),
    ]
    now = datetime.now().isoformat()
    node_ids = {}

    for layer_type, layer_num, layer_name, nodes in layers:
        node_ids[layer_type] = []
        for node_name in nodes:
            nid = f"NN-{layer_type}-{node_name}-{random.randint(1000, 9999)}"
            cur.execute('''
                INSERT INTO neural_network_nodes
                (node_id, node_type, node_name, node_layer, node_layer_name,
                 activation_function, weight, bias, threshold, status,
                 processing_capacity, current_load, accuracy, training_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                nid, layer_type, node_name, layer_num, layer_name,
                'relu', round(random.uniform(0.3, 0.8), 4),
                round(random.uniform(-0.1, 0.1), 4),
                round(random.uniform(0.3, 0.7), 4),
                'active', round(random.uniform(80, 120), 2),
                0.0, round(random.uniform(0.5, 0.9), 4), 0, now
            ))
            node_ids[layer_type].append(nid)

    # 创建层间连接
    layer_order = ['input', 'hidden1', 'hidden2', 'hidden3', 'output']
    conn_counter = 0
    for i in range(len(layer_order) - 1):
        for src_id in node_ids[layer_order[i]]:
            for tgt_id in node_ids[layer_order[i + 1]]:
                conn_counter += 1
                cid = f"CONN-{conn_counter:04d}-{src_id[:10]}-{tgt_id[:10]}"
                cur.execute('''
                    INSERT INTO neural_network_connections
                    (connection_id, source_node_id, target_node_id, connection_type,
                     weight, signal_strength, status, learning_rate, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cid, src_id, tgt_id, 'synapse',
                    round(random.uniform(0.1, 0.9), 4), 0.0,
                    'active', 0.01, now
                ))

    conn.commit()
    total_nodes = sum(len(v) for v in node_ids.values())
    logger.info(f"  ✓ 神经网络初始化: {total_nodes}节点, {conn_counter}连接")
    return total_nodes


def init_system_rules(conn):
    """初始化系统规则（用于投喂引擎开关）"""
    cur = conn.cursor()
    rules = [
        ('BRAIN_FEEDING_ENABLED', '脑库投喂开关', '1', '是否启用知识投喂'),
        ('BRAIN_FEEDING_BATCH_SIZE', '投喂批量大小', '10', '每次投喂知识条数'),
        ('BRAIN_NETWORK_LEARNING_ENABLED', '网络学习开关', '1', '是否启用网络采集'),
        ('BRAIN_LEARNING_ENABLED', 'AI学习开关', '1', '是否触发AI员工学习'),
        ('BRAIN_UPGRADE_ENABLED', 'AI升级开关', '1', '是否触发AI员工升级'),
        ('BRAIN_UPGRADE_THRESHOLD', '升级熟练度阈值', '0.8', '升级所需最低熟练度'),
        ('BRAIN_UPGRADE_MAX_LEVEL', '最大等级', '10', 'AI员工最高等级'),
        ('BRAIN_NEURAL_NETWORK_ENABLED', '神经网络训练开关', '1', '是否训练神经网络'),
        ('BRAIN_NEURAL_LEARNING_RATE', '神经网络学习率', '0.01', '权重调整步长'),
        ('BRAIN_NEURAL_PRUNE_ENABLED', '连接剪枝开关', '1', '是否启用弱连接剪枝'),
        ('BRAIN_NEURAL_PRUNE_THRESHOLD', '剪枝阈值', '0.1', '低于此权重的连接被剪除'),
        ('BRAIN_NEURAL_AUTO_EXPAND', '节点自动扩展', '1', '是否自动扩展神经网络节点'),
        ('BRAIN_NEURAL_MAX_NODES', '最大节点数', '200', '神经网络最大节点数'),
        ('BRAIN_CLUSTER_COORDINATION_ENABLED', '集群统筹开关', '1', '是否启用集群协调'),
        ('BRAIN_AUTO_DISCOVER_ENABLED', '学习方向发现开关', '1', '是否自动发现学习方向'),
    ]
    now = datetime.now().isoformat()
    inserted = 0
    for code, name, value, desc in rules:
        cur.execute('''
            INSERT OR IGNORE INTO system_rules
            (rule_code, rule_name, rule_value, description, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?)
        ''', (code, name, value, desc, now, now))
        if cur.rowcount > 0:
            inserted += 1
    conn.commit()
    logger.info(f"✓ 系统规则初始化: 新增{inserted}条（已存在跳过）")
    return inserted


# ========== 验证 ==========

def verify_results(conn):
    """验证投喂结果"""
    cur = conn.cursor()
    print("\n" + "=" * 60)
    print("  投喂结果验证报告")
    print("=" * 60)

    # 题库统计
    try:
        cur.execute("SELECT COUNT(*) FROM question_bank_items")
        q_items = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM question_bank")
        q_bank = cur.fetchone()[0]
        print(f"\n📚 题库统计")
        print(f"  question_bank_items (新格式): {q_items} 道")
        print(f"  question_bank (旧格式):      {q_bank} 道")

        cur.execute("SELECT subject, COUNT(*) FROM question_bank_items GROUP BY subject ORDER BY 2 DESC")
        for sub, cnt in cur.fetchall():
            print(f"    - {sub}: {cnt}道")
    except Exception as e:
        print(f"  题库统计错误: {e}")

    # 脑库统计
    try:
        cur.execute("SELECT COUNT(*) FROM ai_brain_knowledge")
        k_cnt = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM brain_feeding_queue")
        f_cnt = cur.fetchone()[0]
        print(f"\n🧠 脑库统计")
        print(f"  ai_brain_knowledge (知识):   {k_cnt} 条")
        print(f"  brain_feeding_queue (投喂):  {f_cnt} 条")

        cur.execute("SELECT knowledge_type, COUNT(*) FROM ai_brain_knowledge GROUP BY knowledge_type ORDER BY 2 DESC")
        for kt, cnt in cur.fetchall():
            print(f"    - {kt}: {cnt}条")

        cur.execute("SELECT tags, COUNT(*) FROM ai_brain_knowledge GROUP BY tags LIMIT 10")
        for tag, cnt in cur.fetchall():
            print(f"    - 领域[{tag}]: {cnt}条")
    except Exception as e:
        print(f"  脑库统计错误: {e}")

    # 神经网络统计
    try:
        cur.execute("SELECT COUNT(*) FROM neural_network_nodes WHERE status='active'")
        nn_nodes = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM neural_network_connections WHERE status='active'")
        nn_conns = cur.fetchone()[0]
        print(f"\n🔗 神经网络统计")
        print(f"  活跃节点: {nn_nodes}")
        print(f"  活跃连接: {nn_conns}")
        if nn_nodes > 0:
            print(f"  网络密度: {nn_conns/max(nn_nodes,1):.2f} 连接/节点")
    except Exception as e:
        print(f"  神经网络统计错误: {e}")

    print("\n" + "=" * 60)
    return True


# ========== 主流程 ==========

def main():
    logger.info("=" * 60)
    logger.info("  MTSCOS AI 题库与脑库综合投喂脚本")
    logger.info("=" * 60)

    # 解析数据库路径
    db_path = resolve_db_path()
    logger.info(f"数据库路径: {db_path}")

    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")

    try:
        # 1. 初始化表
        logger.info("\n[1/5] 初始化数据表...")
        init_question_tables(conn)
        init_brain_tables(conn)

        # 2. 初始化系统规则
        logger.info("\n[2/5] 初始化系统规则...")
        init_system_rules(conn)

        # 3. 投喂题库
        logger.info(f"\n[3/5] 投喂题库 (共{len(ALL_QUESTIONS)}道候选)...")
        logger.info(f"  K12: {len(K12_QUESTIONS)}题 | 高等: {len(HIGHER_EDU_QUESTIONS)}题 | 职业: {len(VOCATIONAL_QUESTIONS)}题")
        logger.info(f"  IT技能: {len(IT_SKILLS_QUESTIONS)}题 | 日语: {len(JAPANESE_QUESTIONS)}题")
        feed_question_bank(conn)

        # 4. 投喂脑库
        logger.info(f"\n[4/5] 投喂脑库 (共{len(BRAIN_KNOWLEDGE)}条候选)...")
        domains = set(k['domain'] for k in BRAIN_KNOWLEDGE)
        logger.info(f"  覆盖领域: {', '.join(domains)}")
        feed_brain_knowledge(conn)

        # 5. 初始化神经网络
        logger.info("\n[5/5] 初始化神经网络...")
        init_neural_network(conn)

        # 写入维护日志
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO system_maintenance_logs
            (operation_type, target, result, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', ('batch_feeding', 'question_bank+ai_brain', 'success',
              f'批量投喂脚本执行完成，题库候选{len(ALL_QUESTIONS)}题，脑库候选{len(BRAIN_KNOWLEDGE)}条',
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()

        # 验证结果
        verify_results(conn)

    except Exception as e:
        logger.error(f"✗ 投喂过程失败: {e}", exc_info=True)
        conn.rollback()
        raise
    finally:
        conn.close()

    logger.info("\n✓✓✓ 全部投喂流程完成 ✓✓✓")


if __name__ == '__main__':
    main()
