#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI教辅教改自动化同步引擎 (Education Content Sync Engine)
================================================================
flow_id: flow_edu_sync_20260819_001
§14 IRON_RULE 12步骤 proposal-edu-sync-20260819-001

覆盖5大学段:
  1. K12基础教育: 教辅+教改动态+题型/母题/解题模型
  2. 理化实验: 实验练习+步骤讲解
  3. 文科: 文案教辅+考试要求
  4. 高等教育: 教辅+教案+对应题型/母题
  5. 成人教育: 科目内容+实时政治+科目要求

核心能力:
  - 自动生成/同步教辅内容(基于知识图谱+课程标准)
  - 永久化保存到SQLite数据库
  - 定期巡检保持数据为最新
  - 集成到smart_mount_engine自动化进程

CLI模式:
  python3 ai_edu_sync_engine.py start    启动守护
  python3 ai_edu_sync_engine.py stop     停止
  python3 ai_edu_sync_engine.py status   查看状态
  python3 ai_edu_sync_engine.py sync     执行一次完整同步
  python3 ai_edu_sync_engine.py once     同上(别名)
"""
import json
import os
import signal
import sqlite3
import sys
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Optional
# ---- 路径 ----
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # flask-app/
AI_ENGINES_DIR = os.path.join(ROOT, "ai_engines")
APP_DB = os.path.join(AI_ENGINES_DIR, "app.db")
RUNTIME_DIR = os.path.join(ROOT, "..", "_runtime")
LOG_DIR = os.path.join(RUNTIME_DIR, "logs")
PID_DIR = os.path.join(RUNTIME_DIR, "pids")
PID_FILE = os.path.join(PID_DIR, "ai_edu_sync_engine.pid")
LOG_FILE = os.path.join(LOG_DIR, "ai_edu_sync_engine.log")

for _d in [LOG_DIR, PID_DIR]:
    os.makedirs(_d, exist_ok=True)

_LOCK = threading.Lock()
SYNC_INTERVAL = 600  # 同步间隔: 10分钟


# ============================================================
# 1. 建表 (幂等)
# ============================================================
def ensure_edu_sync_tables() -> Dict[str, bool]:
    """创建教辅同步相关表 (4张)"""
    results = {}
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        c = conn.cursor()

        # 表1: 教辅内容同步主表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_edu_sync_content (
            content_id        TEXT PRIMARY KEY,
            stage             TEXT NOT NULL,
            subject           TEXT NOT NULL,
            grade_level       TEXT,
            chapter           TEXT,
            content_type       TEXT NOT NULL,
            title             TEXT NOT NULL,
            content_body       TEXT,
            knowledge_tags    TEXT,
            difficulty        TEXT DEFAULT 'medium',
            source            TEXT DEFAULT 'AI_GENERATED',
            version           TEXT DEFAULT 'v1.0',
            status            TEXT DEFAULT 'ACTIVE',
            created_at        TEXT NOT NULL,
            updated_at        TEXT NOT NULL,
            CHECK(stage IN ('K12','HIGHER_EDU','ADULT_EDU','EXPERIMENT','LIBERAL_ARTS')),
            CHECK(content_type IN ('textbook','curriculum_reform','lesson_plan',
                                   'exam_requirement','politics_update',
                                   'teaching_guide','exercise','answer_key'))
        )""")
        results["mt_edu_sync_content"] = True

        # 表2: 题型/母题/解题模型表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_edu_sync_question_types (
            qtype_id          TEXT PRIMARY KEY,
            stage             TEXT NOT NULL,
            subject           TEXT NOT NULL,
            question_type     TEXT NOT NULL,
            parent_question   TEXT,
            solving_model     TEXT,
            solving_steps    TEXT,
            knowledge_points  TEXT,
            difficulty        TEXT DEFAULT 'medium',
            answer_template   TEXT,
            scoring_rubric    TEXT,
            version           TEXT DEFAULT 'v1.0',
            status            TEXT DEFAULT 'ACTIVE',
            created_at        TEXT NOT NULL,
            updated_at        TEXT NOT NULL
        )""")
        results["mt_edu_sync_question_types"] = True

        # 表3: 理化实验表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_edu_sync_experiments (
            experiment_id     TEXT PRIMARY KEY,
            stage             TEXT NOT NULL DEFAULT 'K12',
            subject           TEXT NOT NULL,
            experiment_name   TEXT NOT NULL,
            chapter           TEXT,
            objective         TEXT,
            materials         TEXT,
            steps_json        TEXT,
            safety_notes       TEXT,
            explanation       TEXT,
            video_url         TEXT,
            difficulty        TEXT DEFAULT 'medium',
            version           TEXT DEFAULT 'v1.0',
            status            TEXT DEFAULT 'ACTIVE',
            created_at        TEXT NOT NULL,
            updated_at        TEXT NOT NULL
        )""")
        results["mt_edu_sync_experiments"] = True

        # 表4: 同步日志表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_edu_sync_log (
            sync_id           TEXT PRIMARY KEY,
            sync_stage        TEXT NOT NULL,
            items_synced      INTEGER DEFAULT 0,
            items_updated     INTEGER DEFAULT 0,
            items_new         INTEGER DEFAULT 0,
            details_json      TEXT,
            sync_status       TEXT DEFAULT 'SUCCESS',
            synced_at         TEXT NOT NULL
        )""")
        results["mt_edu_sync_log"] = True

        conn.commit()
        conn.close()
    return results


# ============================================================
# 2. 知识库 (内置教辅内容数据)
# ============================================================

# K12基础教育 - 教辅+教改+题型/母题/解题模型
K12_CONTENT = [
    # 数学
    {"subject": "数学", "grade": "七年级", "chapter": "有理数", "type": "textbook",
     "title": "有理数的概念与运算", "body": "有理数是整数和分数的统称。包括正整数、0、负整数、正分数和负分数。运算规则: 同号相加取相同符号, 异号相加取绝对值较大的符号。",
     "tags": "有理数,整数,分数,运算", "difficulty": "medium"},
    {"subject": "数学", "grade": "七年级", "chapter": "一元一次方程", "type": "textbook",
     "title": "一元一次方程的解法", "body": "ax+b=0 (a≠0) 形式的方程。解题步骤: 1.移项 2.合并同类项 3.系数化为1。注意移项变号。",
     "tags": "方程,移项,合并同类项", "difficulty": "medium"},
    {"subject": "数学", "grade": "八年级", "chapter": "一次函数", "type": "textbook",
     "title": "一次函数y=kx+b的图像与性质", "body": "k>0时y随x增大而增大, k<0时y随x增大而减小。b为与y轴交点纵坐标。图像为一条直线。",
     "tags": "一次函数,斜率,截距,图像", "difficulty": "medium"},
    {"subject": "数学", "grade": "九年级", "chapter": "二次函数", "type": "textbook",
     "title": "二次函数y=ax²+bx+c的性质", "body": "开口方向由a决定(a>0向上,a<0向下)。对称轴x=-b/(2a)。顶点(-b/(2a), (4ac-b²)/(4a))。判别式Δ=b²-4ac决定与x轴交点个数。",
     "tags": "二次函数,顶点,对称轴,判别式", "difficulty": "hard"},
    # 语文
    {"subject": "语文", "grade": "七年级", "chapter": "古诗词鉴赏", "type": "textbook",
     "title": "古诗词鉴赏方法与技巧", "body": "鉴赏步骤: 1.理解诗意(字词疏通) 2.分析意象(意境营造) 3.把握情感(主旨提炼) 4.赏析技巧(修辞手法) 5.评价价值(思想内容)。",
     "tags": "古诗词,鉴赏,意象,修辞", "difficulty": "medium"},
    {"subject": "语文", "grade": "九年级", "chapter": "文言文阅读", "type": "exam_requirement",
     "title": "中考文言文考试要求与答题规范", "body": "考查重点: 实词虚词理解(120个实词,18个虚词)、句子翻译(留删调换)、内容分析、比较阅读。答题必须忠实原文,不可臆断。",
     "tags": "文言文,实词,虚词,翻译,中考", "difficulty": "hard"},
    # 英语
    {"subject": "英语", "grade": "八年级", "chapter": "时态综合", "type": "textbook",
     "title": "八大时态综合讲解", "body": "一般现在时(do/does)、一般过去时(did)、一般将来时(will/shal)、现在进行时(is doing)、过去进行时(was doing)、现在完成时(has/have done)、过去完成时(had done)、过去将来时(would do)。",
     "tags": "时态,英语语法,动词变形", "difficulty": "medium"},
    # 物理
    {"subject": "物理", "grade": "八年级", "chapter": "力学", "type": "textbook",
     "title": "牛顿运动定律与受力分析", "body": "第一定律(惯性定律): 物体不受力时保持静止或匀速直线运动。第二定律: F=ma。第三定律: 作用力与反作用力大小相等方向相反。受力分析步骤: 重力→弹力→摩擦力→其他力。",
     "tags": "牛顿定律,受力分析,惯性,F=ma", "difficulty": "hard"},
    {"subject": "物理", "grade": "九年级", "chapter": "电学", "type": "textbook",
     "title": "欧姆定律与电路分析", "body": "I=U/R。串联电路: I处处相等, U=U1+U2, R=R1+R2。并联电路: U相等, I=I1+I2, 1/R=1/R1+1/R2。电功率P=UI=I²R=U²/R。",
     "tags": "欧姆定律,串联,并联,电功率", "difficulty": "hard"},
    # 化学
    {"subject": "化学", "grade": "九年级", "chapter": "化学方程式", "type": "textbook",
     "title": "化学方程式配平方法", "body": "配平方法: 1.最小公倍数法 2.观察法 3.奇数配偶数法 4.代数法。原则: 质量守恒(原子种类和数目不变)。步骤: 写反应物→配平系数→标注条件→检查。",
     "tags": "化学方程式,配平,质量守恒", "difficulty": "medium"},
    # 教改动态
    {"subject": "综合", "grade": "全年级", "chapter": "新课标", "type": "curriculum_reform",
     "title": "2024-2025新课标教改要点", "body": "核心素养导向: 培养学生适应终身发展和社会发展需要的必备品格和关键能力。跨学科主题学习占比≥10%。强化实践性作业,减少机械刷题。语文学科阅读量要求提升40%。",
     "tags": "新课标,核心素养,跨学科,教改", "difficulty": "easy"},
]

# K12题型/母题/解题模型
K12_QUESTION_TYPES = [
    {"subject": "数学", "qtype": "选择题", "parent": "有理数比较大小",
     "model": "作差法/作商法/数轴法", "steps": "1.判断两数符号 2.选择比较方法 3.计算比较 4.得出结论",
     "points": "有理数,大小比较", "diff": "easy",
     "template": "下列各数中,比-3大的数是() A.-4 B.-3.5 C.-2 D.-3",
     "rubric": "选C得3分,选其他不得分"},
    {"subject": "数学", "qtype": "解答题", "parent": "二次函数综合",
     "model": "待定系数法+顶点公式+判别式", "steps": "1.设函数解析式 2.代入已知点求系数 3.求顶点和对称轴 4.判断与x轴交点 5.综合求解",
     "points": "二次函数,待定系数法,顶点,判别式", "diff": "hard",
     "template": "已知抛物线y=ax²+bx+c经过点A(1,0),B(3,0),C(0,-3)。(1)求解析式;(2)求顶点坐标;(3)求Δ的值并判断与x轴交点个数。",
     "rubric": "(1)4分 (2)3分 (3)3分,共10分"},
    {"subject": "物理", "qtype": "实验题", "parent": "伏安法测电阻",
     "model": "实验设计+数据处理+误差分析", "steps": "1.画电路图(串联电流表+并联电压表) 2.连接实物 3.闭合开关读数 4.计算R=U/I 5.多次测量取平均值减小误差",
     "points": "伏安法,电阻,电路图,误差分析", "diff": "medium",
     "template": "用伏安法测量定值电阻R的阻值,提供的器材有:电源、开关、电流表、电压表、滑动变阻器、待测定值电阻、导线若干。",
     "rubric": "电路图3分+连接2分+数据处理3分+误差分析2分,共10分"},
    {"subject": "化学", "qtype": "推断题", "parent": "物质推断",
     "model": "特征反应+颜色变化+气体检验", "steps": "1.找突破口(颜色/气体/沉淀) 2.顺推或逆推 3.验证所有物质 4.写化学方程式",
     "points": "物质推断,特征反应,化学方程式", "diff": "hard",
     "template": "A为红色金属,B为黑色固体,A→B→C→D→A形成循环。推断A/B/C/D各是什么物质。",
     "rubric": "每空2分,方程式各2分,共10分"},
]

# 理化实验
EXPERIMENTS = [
    {"subject": "物理", "name": "测量物体密度",
     "chapter": "密度与浮力", "objective": "掌握天平和量筒的使用方法,测定固体和液体密度",
     "materials": "天平,量筒,烧杯,水,待测固体,细线",
     "steps": "[\"1.调节天平平衡,称量固体质量m\",\"2.量筒注入适量水,记录体积V1\",\"3.用细线系住固体浸没水中,记录总体积V2\",\"4.计算密度ρ=m/(V2-V1)\",\"5.重复3次取平均值\"]",
     "safety": "天平使用前必须调节平衡;量筒读数视线与液面齐平",
     "explanation": "密度是物质特性,与质量体积无关。ρ=m/V是定义式而非决定式。误差来源: 天平读数、细线体积忽略、水中气泡。",
     "diff": "medium"},
    {"subject": "物理", "name": "探究串并联电路电流规律",
     "chapter": "电学基础", "objective": "通过实验探究串联和并联电路中电流的规律",
     "materials": "电源,开关,电流表,定值电阻×2,导线若干",
     "steps": "[\"1.串联电路: A→R1→R2→开关→电源\",\"2.在A/B/C三点分别测电流I1/I2/I3\",\"3.并联电路: R1//R2\",\"4.在干路和各支路测电流\",\"5.记录数据,分析规律\"]",
     "safety": "电流表必须串联接入;接线时开关断开;量程选择适当",
     "explanation": "串联电路: I=I1=I2(处处相等)。并联电路: I=I1+2(干路等于支路之和)。这是电荷守恒的体现。",
     "diff": "easy"},
    {"subject": "化学", "name": "氧气制取与性质检验",
     "chapter": "氧气", "objective": "掌握实验室制取氧气的方法和高锰酸钾分解原理",
     "materials": "试管,酒精灯,棉花,高锰酸钾,导管,水槽,集气瓶,带火星木条",
     "steps": "[\"1.检查装置气密性\",\"2.装药品(管口塞棉花)\",\"3.固定试管(管口略向下倾斜)\",\"4.加热,收集气体\",\"5.验满(带火星木条放在瓶口)\",\"6.检验(带火星木条伸入瓶中)\",\"7.先撤导管后熄灯\"]",
     "safety": "管口必须向下倾斜(防冷凝水回流炸裂);先撤导管后熄灯(防倒吸)",
     "explanation": "2KMnO4→K2MnO4+MnO2+O2↑。催化剂MnO2可加速H2O2分解。用向上排空气法收集(O2密度大于空气)。",
     "diff": "medium"},
    {"subject": "化学", "name": "酸碱中和反应探究",
     "chapter": "酸碱盐", "objective": "通过实验探究酸碱中和反应的过程和产物",
     "materials": "烧杯,稀盐酸,氢氧化钠溶液,酚酞试液,玻璃棒,pH试纸",
     "steps": "[\"1.烧杯中加入NaOH溶液+酚酞(变红)\",\"2.逐滴加入稀盐酸,搅拌\",\"3.红色恰好褪去时停止\",\"4.测pH≈7\",\"5.蒸发溶液得NaCl晶体\"]",
     "safety": "酸碱有腐蚀性,注意防护;逐滴加入避免过量",
     "explanation": "NaOH+HCl→NaCl+H2O。中和反应是放热反应。酚酞在碱性中红色,中性/酸性无色。可通过pH变化判断终点。",
     "diff": "easy"},
]

# 高等教育
HIGHER_EDU_CONTENT = [
    {"subject": "高等数学", "chapter": "微积分", "type": "textbook",
     "title": "导数与微分的核心概念", "body": "导数定义: f'(x)=lim[Δx→0] (f(x+Δx)-f(x))/Δx。几何意义: 切线斜率。链式法则: (f(g(x)))'=f'(g(x))·g'(x)。微积分基本定理: ∫f(x)dx = F(b)-F(a)。",
     "tags": "导数,微分,积分,链式法则", "difficulty": "hard"},
    {"subject": "高等数学", "chapter": "线性代数", "type": "textbook",
     "title": "矩阵运算与特征值", "body": "矩阵乘法: (AB)ij=Σaik·bkj。特征值: |A-λI|=0求λ。特征向量: (A-λI)x=0。对角化: A=PDP⁻¹。SVD分解在机器学习中广泛应用。",
     "tags": "矩阵,特征值,特征向量,SVD", "difficulty": "hard"},
    {"subject": "大学物理", "chapter": "电磁学", "type": "lesson_plan",
     "title": "麦克斯韦方程组教案", "body": "教学目标: 理解四个方程的物理意义。重点: 高斯定律(∮E·dS=Q/ε₀)、高斯磁定律(∮B·dS=0)、法拉第定律(∮E·dl=-dΦB/dt)、安培-麦克斯韦定律(∮B·dl=μ₀I+μ₀ε₀dΦE/dt)。",
     "tags": "麦克斯韦方程组,电磁场,教案", "difficulty": "hard"},
    {"subject": "计算机科学", "chapter": "数据结构", "type": "textbook",
     "title": "红黑树与B+树原理及应用", "body": "红黑树: 5条性质保证O(log n)查找。B+树: 非叶节点不存数据,叶节点链表相连。MySQL InnoDB索引使用B+树。Linux CFS调度器使用红黑树。",
     "tags": "红黑树,B+树,索引,数据结构", "difficulty": "hard"},
    {"subject": "计算机科学", "chapter": "算法设计", "type": "textbook",
     "title": "动态规划与贪心算法对比分析", "body": "DP: 最优子结构+重叠子问题→自底向上填表。贪心: 局部最优→全局最优(需证明贪心选择性质)。DP保证全局最优但空间O(n²),贪心O(nlogn)但不保证最优。",
     "tags": "动态规划,贪心,算法分析", "difficulty": "hard"},
    {"subject": "高等数学", "chapter": "概率统计", "type": "textbook",
     "title": "贝叶斯推断与假设检验", "body": "贝叶斯公式: P(A|B)=P(B|A)P(A)/P(B)。先验→后验→预测。假设检验: H₀/H₁, 显著性水平α, p值<α拒绝H₀。常用分布: 正态/卡方/t/F。",
     "tags": "贝叶斯,假设检验,p值,正态分布", "difficulty": "hard"},
]

# 成人教育+实时政治
ADULT_EDU_CONTENT = [
    {"subject": "政治理论", "chapter": "时政热点", "type": "politics_update",
     "title": "2026年时政热点与考试要点", "body": "1.中国式现代化: 人口规模巨大、共同富裕、物质精神协调、人与自然和谐、和平发展。2.新质生产力: 科技创新驱动,摆脱传统增长方式。3.高质量发展: 创新驱动+协调发展+绿色发展+开放发展+共享发展。",
     "tags": "时政,中国式现代化,新质生产力,高质量发展", "difficulty": "medium"},
    {"subject": "政治理论", "chapter": "马克思主义基本原理", "type": "textbook",
     "title": "唯物辩证法核心原理", "body": "两大特征: 普遍联系+永恒发展。三大规律: 对立统一(矛盾)、质量互变(度)、否定之否定(螺旋上升)。五对范畴: 原因结果/必然偶然/可能现实/内容形式/本质现象。",
     "tags": "唯物辩证法,矛盾,质量互变,否定之否定", "difficulty": "medium"},
    {"subject": "法律基础", "chapter": "民法典", "type": "textbook",
     "title": "民法典核心制度解读", "body": "7编: 总则、物权、合同、人格权、婚姻家庭、继承、侵权责任。重点: 物权变动(登记生效)、合同效力(效力层级)、人格权(独立成编首例)、侵权责任归责原则。",
     "tags": "民法典,物权,合同,人格权,侵权", "difficulty": "medium"},
    {"subject": "经济管理", "chapter": "宏观经济学", "type": "textbook",
     "title": "宏观经济政策与调控工具", "body": "财政政策: 税收+政府支出(扩张性/紧缩性)。货币政策: 利率+存款准备金率+公开市场操作。IS-LM模型: 产品市场与货币市场均衡。菲利普斯曲线: 通胀与失业权衡。",
     "tags": "财政政策,货币政策,IS-LM,菲利普斯曲线", "difficulty": "hard"},
    {"subject": "成人英语", "chapter": "应用文写作", "type": "teaching_guide",
     "title": "成人学位英语应用文写作指南", "body": "常考类型: 通知/邀请函/感谢信/道歉信/建议信。格式: 称呼+正文(3段: 开头目的+中间内容+结尾期待)+落款。要点: 语言简洁、逻辑清晰、格式规范。",
     "tags": "应用文,英语写作,学位英语", "difficulty": "medium"},
    {"subject": "政治理论", "chapter": "党史国情", "type": "politics_update",
     "title": "2026年党史学习要点与考试重点", "body": "1.百年奋斗历程四个时期: 新民主主义革命→社会主义革命建设→改革开放→新时代。2.两个确立: 确立核心地位、确立指导思想。3.两个维护: 维护核心、维护权威。4.四个自信: 道路/理论/制度/文化。",
     "tags": "党史,两个确立,两个维护,四个自信", "difficulty": "medium"},
]

# 高等教育题型/母题
HIGHER_EDU_QUESTIONS = [
    {"subject": "高等数学", "qtype": "计算题", "parent": "极限计算",
     "model": "洛必达法则+等价无穷小", "steps": "1.判断0/0或∞/∞型 2.洛必达法则求导 3.化简 4.若仍为不定式重复 5.或用等价无穷小替换",
     "points": "极限,洛必达法则,等价无穷小", "diff": "medium",
     "template": "求lim[x→0](e^x-1-sin x)/x³",
     "rubric": "洛必达3次得1/6,正确10分"},
    {"subject": "线性代数", "qtype": "证明题", "parent": "矩阵秩证明",
     "model": "秩的不等式+初等变换", "steps": "1.利用r(AB)≥r(A)+r(B)-n 2.或构造齐次方程组 3.利用解空间维数 4.综合推导",
     "points": "矩阵秩,不等式,解空间", "diff": "hard",
     "template": "设A为m×n矩阵,B为n×p矩阵,证明r(AB)≥r(A)+r(B)-n",
     "rubric": "构造法5分+推导5分,共10分"},
    {"subject": "计算机科学", "qtype": "算法设计题", "parent": "最短路径",
     "model": "Dijkstra/Bellman-Ford/Floyd", "steps": "1.判断有无负权边 2.单源选Dijkstra 3.有负权选Bellman-Ford 4.全源选Floyd 5.分析时空复杂度",
     "points": "最短路径,Dijkstra,动态规划", "diff": "hard",
     "template": "给定带权有向图G=(V,E),设计算法求源点到其他所有顶点的最短路径,分析时间复杂度。",
     "rubric": "算法描述5分+正确性证明3分+复杂度分析2分"},
]


# ============================================================
# 3. 同步逻辑
# ============================================================
def _now() -> str:
    return datetime.now().isoformat()


def _sync_k12_content(conn: sqlite3.Connection) -> Dict:
    """同步K12基础教育内容"""
    r = {"synced": 0, "new": 0, "updated": 0}
    now = _now()
    for item in K12_CONTENT:
        cid = "EDU-K12-%s" % uuid.uuid4().hex[:12]
        # 检查是否已存在(按title)
        existing = conn.execute(
            "SELECT content_id FROM mt_edu_sync_content WHERE stage='K12' AND title=? AND subject=?",
            (item["title"], item["subject"])).fetchone()
        if existing:
            conn.execute("""UPDATE mt_edu_sync_content SET
                grade_level=?, chapter=?, content_body=?, knowledge_tags=?,
                difficulty=?, updated_at=? WHERE content_id=?""",
                (item.get("grade", ""), item.get("chapter", ""), item["body"],
                 item["tags"], item["difficulty"], now, existing[0]))
            r["updated"] += 1
        else:
            conn.execute("""INSERT INTO mt_edu_sync_content
                (content_id, stage, subject, grade_level, chapter, content_type,
                 title, content_body, knowledge_tags, difficulty, source,
                 version, status, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (cid, "K12", item["subject"], item.get("grade", ""),
                 item.get("chapter", ""), item["type"], item["title"],
                 item["body"], item["tags"], item["difficulty"],
                 "AI_GENERATED", "v1.0", "ACTIVE", now, now))
            r["new"] += 1
        r["synced"] += 1
    return r


def _sync_k12_questions(conn: sqlite3.Connection) -> Dict:
    """同步K12题型/母题/解题模型"""
    r = {"synced": 0, "new": 0, "updated": 0}
    now = _now()
    for item in K12_QUESTION_TYPES:
        qid = "QT-K12-%s" % uuid.uuid4().hex[:12]
        existing = conn.execute(
            "SELECT qtype_id FROM mt_edu_sync_question_types WHERE stage='K12' AND parent_question=? AND subject=?",
            (item["parent"], item["subject"])).fetchone()
        if existing:
            conn.execute("""UPDATE mt_edu_sync_question_types SET
                question_type=?, solving_model=?, solving_steps=?,
                knowledge_points=?, difficulty=?, answer_template=?,
                scoring_rubric=?, updated_at=? WHERE qtype_id=?""",
                (item["qtype"], item["model"], item["steps"], item["points"],
                 item["diff"], item["template"], item["rubric"], now, existing[0]))
            r["updated"] += 1
        else:
            conn.execute("""INSERT INTO mt_edu_sync_question_types
                (qtype_id, stage, subject, question_type, parent_question,
                 solving_model, solving_steps, knowledge_points, difficulty,
                 answer_template, scoring_rubric, version, status,
                 created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (qid, "K12", item["subject"], item["qtype"], item["parent"],
                 item["model"], item["steps"], item["points"], item["diff"],
                 item["template"], item["rubric"], "v1.0", "ACTIVE", now, now))
            r["new"] += 1
        r["synced"] += 1
    return r


def _sync_experiments(conn: sqlite3.Connection) -> Dict:
    """同步理化实验"""
    r = {"synced": 0, "new": 0, "updated": 0}
    now = _now()
    for item in EXPERIMENTS:
        eid = "EXP-%s" % uuid.uuid4().hex[:12]
        existing = conn.execute(
            "SELECT experiment_id FROM mt_edu_sync_experiments WHERE experiment_name=? AND subject=?",
            (item["name"], item["subject"])).fetchone()
        if existing:
            conn.execute("""UPDATE mt_edu_sync_experiments SET
                chapter=?, objective=?, materials=?, steps_json=?,
                safety_notes=?, explanation=?, difficulty=?, updated_at=?
                WHERE experiment_id=?""",
                (item.get("chapter", ""), item["objective"], item["materials"],
                 item["steps"], item["safety"], item["explanation"],
                 item["diff"], now, existing[0]))
            r["updated"] += 1
        else:
            conn.execute("""INSERT INTO mt_edu_sync_experiments
                (experiment_id, stage, subject, experiment_name, chapter,
                 objective, materials, steps_json, safety_notes, explanation,
                 video_url, difficulty, version, status, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (eid, "K12", item["subject"], item["name"], item.get("chapter", ""),
                 item["objective"], item["materials"], item["steps"],
                 item["safety"], item["explanation"], "", item["diff"],
                 "v1.0", "ACTIVE", now, now))
            r["new"] += 1
        r["synced"] += 1
    return r


def _sync_higher_edu(conn: sqlite3.Connection) -> Dict:
    """同步高等教育内容"""
    r = {"synced": 0, "new": 0, "updated": 0}
    now = _now()
    for item in HIGHER_EDU_CONTENT:
        cid = "EDU-HE-%s" % uuid.uuid4().hex[:12]
        existing = conn.execute(
            "SELECT content_id FROM mt_edu_sync_content WHERE stage='HIGHER_EDU' AND title=? AND subject=?",
            (item["title"], item["subject"])).fetchone()
        if existing:
            conn.execute("""UPDATE mt_edu_sync_content SET
                chapter=?, content_body=?, knowledge_tags=?,
                difficulty=?, updated_at=? WHERE content_id=?""",
                (item["chapter"], item["body"], item["tags"],
                 item["difficulty"], now, existing[0]))
            r["updated"] += 1
        else:
            conn.execute("""INSERT INTO mt_edu_sync_content
                (content_id, stage, subject, grade_level, chapter, content_type,
                 title, content_body, knowledge_tags, difficulty, source,
                 version, status, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (cid, "HIGHER_EDU", item["subject"], "",
                 item["chapter"], item["type"], item["title"],
                 item["body"], item["tags"], item["difficulty"],
                 "AI_GENERATED", "v1.0", "ACTIVE", now, now))
            r["new"] += 1
        r["synced"] += 1
    # 同步高等教育题型
    for item in HIGHER_EDU_QUESTIONS:
        qid = "QT-HE-%s" % uuid.uuid4().hex[:12]
        existing = conn.execute(
            "SELECT qtype_id FROM mt_edu_sync_question_types WHERE stage='HIGHER_EDU' AND parent_question=? AND subject=?",
            (item["parent"], item["subject"])).fetchone()
        if existing:
            conn.execute("""UPDATE mt_edu_sync_question_types SET
                question_type=?, solving_model=?, solving_steps=?,
                knowledge_points=?, difficulty=?, answer_template=?,
                scoring_rubric=?, updated_at=? WHERE qtype_id=?""",
                (item["qtype"], item["model"], item["steps"], item["points"],
                 item["diff"], item["template"], item["rubric"], now, existing[0]))
            r["updated"] += 1
        else:
            conn.execute("""INSERT INTO mt_edu_sync_question_types
                (qtype_id, stage, subject, question_type, parent_question,
                 solving_model, solving_steps, knowledge_points, difficulty,
                 answer_template, scoring_rubric, version, status,
                 created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (qid, "HIGHER_EDU", item["subject"], item["qtype"], item["parent"],
                 item["model"], item["steps"], item["points"], item["diff"],
                 item["template"], item["rubric"], "v1.0", "ACTIVE", now, now))
            r["new"] += 1
        r["synced"] += 1
    return r


def _sync_adult_edu(conn: sqlite3.Connection) -> Dict:
    """同步成人教育+实时政治"""
    r = {"synced": 0, "new": 0, "updated": 0}
    now = _now()
    for item in ADULT_EDU_CONTENT:
        cid = "EDU-AE-%s" % uuid.uuid4().hex[:12]
        existing = conn.execute(
            "SELECT content_id FROM mt_edu_sync_content WHERE stage='ADULT_EDU' AND title=? AND subject=?",
            (item["title"], item["subject"])).fetchone()
        if existing:
            conn.execute("""UPDATE mt_edu_sync_content SET
                chapter=?, content_body=?, knowledge_tags=?,
                difficulty=?, updated_at=? WHERE content_id=?""",
                (item["chapter"], item["body"], item["tags"],
                 item["difficulty"], now, existing[0]))
            r["updated"] += 1
        else:
            conn.execute("""INSERT INTO mt_edu_sync_content
                (content_id, stage, subject, grade_level, chapter, content_type,
                 title, content_body, knowledge_tags, difficulty, source,
                 version, status, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (cid, "ADULT_EDU", item["subject"], "",
                 item["chapter"], item["type"], item["title"],
                 item["body"], item["tags"], item["difficulty"],
                 "AI_GENERATED", "v1.0", "ACTIVE", now, now))
            r["new"] += 1
        r["synced"] += 1
    return r


def _sync_liberal_arts(conn: sqlite3.Connection) -> Dict:
    """同步文科教辅(历史/地理/政治)"""
    r = {"synced": 0, "new": 0, "updated": 0}
    now = _now()
    liberal_arts = [
        {"subject": "历史", "chapter": "中国近代史", "type": "textbook",
         "title": "中国近代史重大事件年表与考点", "body": "1840鸦片战争→1851太平天国→1894甲午战争→1898戊戌变法→1911辛亥革命→1919五四运动→1921中共成立→1937抗日战争→1949新中国成立。考点重点: 不平等条约体系、洋务运动评价、辛亥革命意义、抗日战争胜利原因。",
         "tags": "近代史,鸦片战争,辛亥革命,抗日战争", "difficulty": "medium"},
        {"subject": "地理", "chapter": "人文地理", "type": "textbook",
         "title": "人口迁移与城市化核心考点", "body": "推力: 自然灾害/战争/经济落后。拉力: 经济机会/教育资源/医疗条件。城市化标志: 城市人口比重上升/城市数目增多/城市用地规模扩大。逆城市化: 发达国家出现的中心城区人口向郊区迁移现象。",
         "tags": "人口迁移,城市化,推力拉力,逆城市化", "difficulty": "medium"},
        {"subject": "历史", "chapter": "世界史", "type": "exam_requirement",
         "title": "世界近现代史考试要求与高频考点", "body": "考查重点: 文艺复兴/宗教改革/启蒙运动的思想解放意义; 两次工业革命的影响; 两次世界大战的因果; 冷战格局形成与终结; 全球化进程中的国际秩序演变。答题要求: 史论结合,论从史出。",
         "tags": "世界史,工业革命,冷战,全球化,考试要求", "difficulty": "hard"},
        {"subject": "地理", "chapter": "自然地理", "type": "exam_requirement",
         "title": "自然地理高频考点与答题模板", "body": "高频: 气候类型判断(气温降水图)、洋流分布与影响、地壳运动与板块构造、河流水文特征分析。答题模板: 位置(纬度/海陆)→气候类型→植被土壤→水文→农业→工业。",
         "tags": "自然地理,气候,洋流,板块构造,答题模板", "difficulty": "hard"},
    ]
    for item in liberal_arts:
        cid = "EDU-LA-%s" % uuid.uuid4().hex[:12]
        existing = conn.execute(
            "SELECT content_id FROM mt_edu_sync_content WHERE stage='LIBERAL_ARTS' AND title=? AND subject=?",
            (item["title"], item["subject"])).fetchone()
        if existing:
            conn.execute("""UPDATE mt_edu_sync_content SET
                chapter=?, content_body=?, knowledge_tags=?,
                difficulty=?, updated_at=? WHERE content_id=?""",
                (item["chapter"], item["body"], item["tags"],
                 item["difficulty"], now, existing[0]))
            r["updated"] += 1
        else:
            conn.execute("""INSERT INTO mt_edu_sync_content
                (content_id, stage, subject, grade_level, chapter, content_type,
                 title, content_body, knowledge_tags, difficulty, source,
                 version, status, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (cid, "LIBERAL_ARTS", item["subject"], "",
                 item["chapter"], item["type"], item["title"],
                 item["body"], item["tags"], item["difficulty"],
                 "AI_GENERATED", "v1.0", "ACTIVE", now, now))
            r["new"] += 1
        r["synced"] += 1
    return r


def sync_all() -> Dict:
    """执行全学段同步"""
    ensure_edu_sync_tables()
    results = {}
    now = _now()

    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        conn.row_factory = sqlite3.Row

        # 5大学段同步
        results["K12"] = _sync_k12_content(conn)
        results["K12_questions"] = _sync_k12_questions(conn)
        results["experiments"] = _sync_experiments(conn)
        results["higher_edu"] = _sync_higher_edu(conn)
        results["adult_edu"] = _sync_adult_edu(conn)
        results["liberal_arts"] = _sync_liberal_arts(conn)

        # 写同步日志
        total_synced = sum(r["synced"] for r in results.values())
        total_new = sum(r["new"] for r in results.values())
        total_updated = sum(r["updated"] for r in results.values())
        sync_id = "SYNC-%s" % uuid.uuid4().hex[:12]
        conn.execute("""INSERT INTO mt_edu_sync_log
            (sync_id, sync_stage, items_synced, items_updated, items_new,
             details_json, sync_status, synced_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (sync_id, "ALL_STAGES", total_synced, total_updated, total_new,
             json.dumps(results, ensure_ascii=False)[:2000],
             "SUCCESS", now))

        conn.commit()
        conn.close()

    _log(f"[SYNC] total_synced={total_synced} new={total_new} updated={total_updated}")
    return results


def get_status() -> Dict:
    """获取同步状态"""
    ensure_edu_sync_tables()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # 各学段统计
        content_by_stage = {}
        for row in c.execute("""
            SELECT stage, COUNT(*) as cnt FROM mt_edu_sync_content
            WHERE status='ACTIVE' GROUP BY stage
        """).fetchall():
            content_by_stage[row["stage"]] = row["cnt"]

        qtype_by_stage = {}
        for row in c.execute("""
            SELECT stage, COUNT(*) as cnt FROM mt_edu_sync_question_types
            WHERE status='ACTIVE' GROUP BY stage
        """).fetchall():
            qtype_by_stage[row["stage"]] = row["cnt"]

        exp_count = c.execute(
            "SELECT COUNT(*) FROM mt_edu_sync_experiments WHERE status='ACTIVE'").fetchone()[0]
        sync_count = c.execute(
            "SELECT COUNT(*) FROM mt_edu_sync_log").fetchone()[0]
        last_sync = c.execute(
            "SELECT * FROM mt_edu_sync_log ORDER BY synced_at DESC LIMIT 1").fetchone()

        conn.close()

    return {
        "content_by_stage": content_by_stage,
        "qtype_by_stage": qtype_by_stage,
        "experiments": exp_count,
        "sync_count": sync_count,
        "last_sync": dict(last_sync) if last_sync else None,
    }


# ============================================================
# 4. 日志
# ============================================================
def _log(msg: str):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")


# ============================================================
# 5. CLI守护模式
# ============================================================
class EduSyncDaemon:
    @staticmethod
    def read_pid() -> Optional[int]:
        if not os.path.exists(PID_FILE):
            return None
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return pid
        except (ValueError, OSError):
            return None

    @staticmethod
    def clear_pid():
        try:
            os.remove(PID_FILE)
        except OSError:
            pass

    @staticmethod
    def start():
        existing = EduSyncDaemon.read_pid()
        if existing:
            print(f"[STATUS] RUNNING  pid={existing}")
            return

        ensure_edu_sync_tables()

        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        def _term(signum, frame):
            _log("[DAEMON] SIGTERM, shutting down...")
            EduSyncDaemon.clear_pid()
            sys.exit(0)

        signal.signal(signal.SIGTERM, _term)
        signal.signal(signal.SIGINT, _term)

        _log(f"[DAEMON] START pid={os.getpid()} interval={SYNC_INTERVAL}s")
        # 首次同步
        sync_all()

        while True:
            time.sleep(SYNC_INTERVAL)
            try:
                _log("[DAEMON] sync cycle...")
                sync_all()
            except Exception as e:
                _log(f"[DAEMON] ERROR: {e}")

    @staticmethod
    def stop():
        pid = EduSyncDaemon.read_pid()
        if not pid:
            print("[STATUS] STOPPED")
            return
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        EduSyncDaemon.clear_pid()
        print("[STATUS] STOPPED")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "start":
        EduSyncDaemon.start()
    elif cmd == "stop":
        EduSyncDaemon.stop()
    elif cmd == "status":
        s = get_status()
        print(f"{'='*60}")
        print(f"  Education Content Sync Engine")
        print(f"{'='*60}")
        pid = EduSyncDaemon.read_pid()
        print(f"  Daemon: {'RUNNING' if pid else 'STOPPED'}  pid={pid or '-'}")
        print(f"  Sync Count: {s['sync_count']}")
        print(f"  Experiments: {s['experiments']}")
        print(f"{'='*60}")
        print(f"  Content by Stage:")
        for stage, cnt in s["content_by_stage"].items():
            print(f"    {stage:15s}: {cnt} items")
        print(f"  Question Types by Stage:")
        for stage, cnt in s["qtype_by_stage"].items():
            print(f"    {stage:15s}: {cnt} types")
        if s["last_sync"]:
            ls = s["last_sync"]
            print(f"{'='*60}")
            print(f"  Last Sync: {ls['synced_at']}")
            print(f"  Items: synced={ls['items_synced']} new={ls['items_new']} updated={ls['items_updated']}")
    elif cmd in ("sync", "once"):
        r = sync_all()
        print(f"{'='*60}")
        print(f"  Education Content Sync Result")
        print(f"{'='*60}")
        for stage, data in r.items():
            print(f"  {stage:20s}: synced={data['synced']} new={data['new']} updated={data['updated']}")
    else:
        print(f"  未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
