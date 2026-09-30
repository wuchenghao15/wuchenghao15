#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数学解题模型自动收集引擎
================================================================
flow_id: flow_math_models_20260819_001

功能:
  1. 收纳K12+高等教育+竞赛数学所有解题模型
  2. 按学段/模块/难度分类存储
  3. 每个模型含: 题型/条件/公式/解题步骤/例题/变式
  4. 数据库永久化, 自动更新
  5. 加入smart_mount自动化进程

CLI:
  python3 ai_math_models_engine.py sync     同步所有模型
  python3 ai_math_models_engine.py status   查看统计
  python3 ai_math_models_engine.py start    守护模式
"""
import json
import os
import re
import signal
import sqlite3
import sys
import time
import threading
from datetime import datetime
from typing import Dict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_ENGINES_DIR = os.path.join(ROOT, "ai_engines")
APP_DB = os.path.join(ROOT, "..", "_runtime", "databases", "Database", "app.db")
RUNTIME_DIR = os.path.join(ROOT, "..", "_runtime")
LOG_DIR = os.path.join(RUNTIME_DIR, "logs")
PID_DIR = os.path.join(RUNTIME_DIR, "pids")
PID_FILE = os.path.join(PID_DIR, "ai_math_models_engine.pid")
LOG_FILE = os.path.join(LOG_DIR, "ai_math_models_engine.log")

for _d in [LOG_DIR, PID_DIR]:
    os.makedirs(_d, exist_ok=True)

_LOCK = threading.Lock()
SYNC_INTERVAL = 1800  # 30分钟

# ============================================================
# 数学解题模型数据库
# ============================================================
MATH_MODELS = [
    # ====== K12 小学 ======
    {
        "model_id": "MATH-ES-001",
        "model_name": "四则运算模型",
        "education_stage": "小学",
        "module": "数与代数",
        "difficulty": 1,
        "problem_types": "整数/小数/分数加减乘除",
        "conditions": "已知两个数的运算关系",
        "formulas": "a+b=c, a-b=c, a×b=c, a÷b=c",
        "steps": "1.判断运算类型 2.对齐数位 3.执行运算 4.验算结果",
        "example": "125+348=473; 验算: 473-125=348",
        "variant": "小数运算/分数运算/混合运算/简便运算",
        "tags": "基础,四则,运算",
    },
    {
        "model_id": "MATH-ES-002",
        "model_name": "应用题数量关系模型",
        "education_stage": "小学",
        "module": "数与代数",
        "difficulty": 2,
        "problem_types": "行程问题/工程问题/利润问题/浓度问题",
        "conditions": "已知速度时间路程/工作效率/进价售价",
        "formulas": "路程=速度×时间; 工作量=效率×时间; 利润=售价-进价; 浓度=溶质÷溶液×100%",
        "steps": "1.读题提取已知量 2.画线段图 3.列数量关系式 4.求解 5.检验作答",
        "example": "甲乙相距300km, 甲速60km/h, 乙速40km/h, 相向而行, 几小时后相遇? 300÷(60+40)=3小时",
        "variant": "追及问题/环形跑道/流水行船/电梯问题",
        "tags": "应用题,数量关系,行程",
    },
    {
        "model_id": "MATH-ES-003",
        "model_name": "图形周长面积体积模型",
        "education_stage": "小学",
        "module": "图形与几何",
        "difficulty": 2,
        "problem_types": "长方形/正方形/三角形/圆形/圆柱/圆锥",
        "conditions": "已知图形边长/半径/高",
        "formulas": "C长=2(a+b); S长=ab; C圆=2πr; S圆=πr²; V柱=πr²h; V锥=⅓πr²h",
        "steps": "1.判断图形类型 2.提取已知边长 3.选择公式 4.代入计算 5.写单位",
        "example": "圆半径r=5cm, 面积S=π×5²=78.5cm²",
        "variant": "组合图形/阴影面积/展开图/容积计算",
        "tags": "几何,面积,体积",
    },
    {
        "model_id": "MATH-ES-004",
        "model_name": "分数百分数模型",
        "education_stage": "小学",
        "module": "数与代数",
        "difficulty": 3,
        "problem_types": "分数化简/百分数应用/折扣/利息",
        "conditions": "已知部分量与整体的关系",
        "formulas": "百分数=部分÷整体×100%; 折扣=现价÷原价; 利息=本金×利率×时间",
        "steps": "1.找单位'1' 2.判断求部分还是求整体 3.列式 4.计算 5.检验",
        "example": "原价200元, 打八折, 现价=200×0.8=160元",
        "variant": "连续打折/税率/增长率/比较大小",
        "tags": "分数,百分数,折扣",
    },
    {
        "model_id": "MATH-ES-005",
        "model_name": "方程模型(一元一次)",
        "education_stage": "小学",
        "module": "数与代数",
        "difficulty": 3,
        "problem_types": "ax+b=c型方程/ax=b/c型方程",
        "conditions": "已知等量关系, 求未知数",
        "formulas": "ax+b=c → x=(c-b)/a",
        "steps": "1.设未知数x 2.根据题意列方程 3.移项 4.系数化为1 5.验算",
        "example": "3x+5=20 → 3x=15 → x=5",
        "variant": "含括号方程/含分母方程/不等式",
        "tags": "方程,一元一次,未知数",
    },
    {
        "model_id": "MATH-ES-006",
        "model_name": "统计与概率模型",
        "education_stage": "小学",
        "module": "统计与概率",
        "difficulty": 2,
        "problem_types": "条形图/折线图/扇形图/平均数/中位数/众数",
        "conditions": "已知一组数据",
        "formulas": "平均数=总和÷个数; 中位数=排序后中间值; 众数=出现最多",
        "steps": "1.整理数据 2.选择统计图 3.计算特征数 4.分析结论",
        "example": "数据: 3,5,5,7,8 → 平均数=5.6, 中位数=5, 众数=5",
        "variant": "加权平均/方差/标准差/概率",
        "tags": "统计,概率,数据分析",
    },
    {
        "model_id": "MATH-ES-007",
        "model_name": "简便运算模型",
        "education_stage": "小学",
        "module": "数与代数",
        "difficulty": 2,
        "problem_types": "交换律/结合律/分配律/平方差/裂项相消",
        "conditions": "已知可凑整或可裂项的算式",
        "formulas": "a+b=b+a; (a+b)+c=a+(b+c); a×(b+c)=ab+ac; a²-b²=(a+b)(a-b); 1/(n(n+1))=1/n-1/(n+1)",
        "steps": "1.观察数字特征 2.选定律或公式 3.凑整/裂项 4.化简计算 5.验算",
        "example": "25×7×4=25×4×7=700; 1/2+1/6+1/12=1-1/2+1/2-1/3+1/3-1/4=3/4",
        "variant": "裂项求和/换元法/拆项法/借数法",
        "tags": "简便运算,分配律,平方差,裂项",
    },
    {
        "model_id": "MATH-ES-008",
        "model_name": "鸡兔同笼模型(假设法)",
        "education_stage": "小学",
        "module": "数与代数",
        "difficulty": 3,
        "problem_types": "鸡兔同笼/两物件假设/置换问题",
        "conditions": "已知总头数和总脚数",
        "formulas": "假设全是鸡: 兔数=(总脚-2×总头)÷(4-2); 假设全是兔: 鸡数=(4×总头-总脚)÷(4-2)",
        "steps": "1.假设全是某物 2.计算假设下的脚数 3.求差 4.除以单位差 5.求另一物",
        "example": "头共30, 脚共88 → 兔数=(88-2×30)÷2=14; 鸡数=30-14=16",
        "variant": "抬腿法/方程法/列表法/双假设法",
        "tags": "鸡兔同笼,假设法,置换问题",
    },
    {
        "model_id": "MATH-ES-009",
        "model_name": "植树问题模型",
        "education_stage": "小学",
        "module": "数与代数",
        "difficulty": 2,
        "problem_types": "直线两端植树/直线一端植树/直线两端都不植/封闭曲线植树",
        "conditions": "已知路长和棵距",
        "formulas": "两端都植: 棵数=段数+1; 一端植: 棵数=段数; 两端不植: 棵数=段数-1; 封闭: 棵数=段数; 段数=总长÷棵距",
        "steps": "1.判断类型(直线/封闭/两端情况) 2.计算段数 3.套对应公式 4.求解",
        "example": "路长100m, 每5m植一棵, 两端都植 → 段数=100÷5=20, 棵数=20+1=21",
        "variant": "锯木头问题/楼梯问题/钟声问题",
        "tags": "植树问题,段数,封闭曲线",
    },
    {
        "model_id": "MATH-ES-010",
        "model_name": "盈亏问题模型",
        "education_stage": "小学",
        "module": "数与代数",
        "difficulty": 3,
        "problem_types": "一盈一亏/两盈/两亏/一盈一正好",
        "conditions": "已知两次分配方案及盈亏结果",
        "formulas": "总份数=(盈+亏)÷两次分配差; (两次都盈)份数=(大盈-小盈)÷差; (两次都亏)份数=(大亏-小亏)÷差",
        "steps": "1.对比两次方案 2.求盈亏差 3.求单位差 4.相除得份数 5.求总量",
        "example": "分苹果, 每人3个剩5个, 每人4个少3个 → 人数=(5+3)÷(4-3)=8; 苹果=3×8+5=29",
        "variant": "双盈/双亏/正好型/含参盈亏",
        "tags": "盈亏问题,份数,分配差",
    },
    {
        "model_id": "MATH-ES-011",
        "model_name": "牛吃草问题模型",
        "education_stage": "小学",
        "module": "数与代数",
        "difficulty": 4,
        "problem_types": "牛吃草/排队入场/抽水机排水(草在长/水在进)",
        "conditions": "已知两次不同数量与天数",
        "formulas": "草生长速度=(长时间×长牛数-短时间×短牛数)÷(长时间-短时间); 原草量=长时间×长牛数-长时间×生长速度; 求天数=(原草量+天数×生长速度)÷牛数",
        "steps": "1.求草生长速度 2.求原草量 3.根据问题套公式 4.求解",
        "example": "10牛吃20天, 15牛吃10天 → 草速=(10×20-15×10)÷(20-10)=5; 原草=10×20-20×5=100",
        "variant": "排队入场/水库排水/牛吃草变式",
        "tags": "牛吃草,生长速度,原草量",
    },
    {
        "model_id": "MATH-ES-012",
        "model_name": "抽屉原理模型",
        "education_stage": "小学",
        "module": "数与代数",
        "difficulty": 4,
        "problem_types": "存在性证明/至少问题/构造抽屉",
        "conditions": "已知物体数n和抽屉数m, n>m",
        "formulas": "原则一: n+1个物体放入n个抽屉, 必有一抽屉至少2个; 原则二: n物体入m抽屉, 必有至少⌈n/m⌉个",
        "steps": "1.识别物体与抽屉 2.构造抽屉(关键) 3.套原理 4.下结论",
        "example": "13人中至少2人生肖相同(12生肖) → 13物体12抽屉, 必有≥2人在同一抽屉",
        "variant": "涂色问题/数列抽屉/余数抽屉/平均分配",
        "tags": "抽屉原理,存在性,构造抽屉",
    },
    {
        "model_id": "MATH-ES-013",
        "model_name": "和差倍问题模型",
        "education_stage": "小学",
        "module": "数与代数",
        "difficulty": 2,
        "problem_types": "和差问题/和倍问题/差倍问题",
        "conditions": "已知两数和或差及倍数关系",
        "formulas": "和差: 大数=(和+差)÷2, 小数=(和-差)÷2; 和倍: 小数=和÷(倍+1), 大数=小×倍; 差倍: 小数=差÷(倍-1), 大数=小×倍",
        "steps": "1.画线段图 2.找和差倍关系 3.套公式 4.求两数 5.验算",
        "example": "甲乙共98人, 甲比乙多6 → 甲=(98+6)÷2=52, 乙=(98-6)÷2=46",
        "variant": "三数和倍/变倍问题/年龄倍数",
        "tags": "和差倍,线段图,倍数关系",
    },
    {
        "model_id": "MATH-ES-014",
        "model_name": "归一归总问题模型",
        "education_stage": "小学",
        "module": "数与代数",
        "difficulty": 2,
        "problem_types": "归一问题(求单一量)/归总问题(求总量)",
        "conditions": "已知几份对应总量, 求其他份量",
        "formulas": "归一: 单一量=总量÷份数, 所求=单一量×新份数; 归总: 总量=一份量×份数, 所求份数=总量÷新一份量",
        "steps": "1.识别单一量或总量 2.求出不变量 3.套公式 4.求解",
        "example": "5支铅笔0.6元, 16支多少? 单一量=0.6÷5=0.12元, 16支=0.12×16=1.92元",
        "variant": "双归一/反归一/条件归总",
        "tags": "归一问题,归总问题,单一量",
    },
    {
        "model_id": "MATH-ES-015",
        "model_name": "周期循环问题模型",
        "education_stage": "小学",
        "module": "数与代数",
        "difficulty": 3,
        "problem_types": "周期数列/星期问题/生肖问题/截尾循环",
        "conditions": "已知循环节和总位置",
        "formulas": "位置÷周期长=商...余数; 余数对应循环节中第几个; 余0则对应最后一个",
        "steps": "1.找循环节长度 2.用位置÷周期长 3.看余数 4.对应元素 5.下结论",
        "example": "数列A B C D A B C D..., 第100个? 100÷4=25余0 → 第100个是D",
        "variant": "闰年平年/钟表周期/小数循环节",
        "tags": "周期,循环,余数对应",
    },
    {
        "model_id": "MATH-ES-016",
        "model_name": "还原问题模型(倒推法)",
        "education_stage": "小学",
        "module": "数与代数",
        "difficulty": 3,
        "problem_types": "还原问题/逆推问题/算式还原",
        "conditions": "已知最终结果和运算过程",
        "formulas": "逆运算: 加←→减, 乘←→除; 顺序倒推, 每步用逆运算",
        "steps": "1.从结果出发 2.倒着读题 3.每步用逆运算 4.求出原数 5.正向验算",
        "example": "某数乘3加5得20 → (20-5)÷3=5, 原数=5",
        "variant": "流程图还原/多步还原/含分支还原",
        "tags": "还原问题,倒推法,逆运算",
    },

    # ====== K12 初中 ======
    {
        "model_id": "MATH-MS-001",
        "model_name": "一元二次方程模型",
        "education_stage": "初中",
        "module": "数与代数",
        "difficulty": 3,
        "problem_types": "ax²+bx+c=0型/因式分解/公式法/配方法",
        "conditions": "已知二次项/一次项/常数项系数",
        "formulas": "求根公式: x=(-b±√(b²-4ac))/2a; 判别式Δ=b²-4ac; 韦达定理: x₁+x₂=-b/a, x₁·x₂=c/a",
        "steps": "1.化标准形式 2.计算判别式Δ 3.Δ>0两根/Δ=0一根/Δ<0无根 4.选方法求解 5.验算",
        "example": "x²-5x+6=0 → Δ=25-24=1 → x=(5±1)/2 → x₁=3, x₂=2",
        "variant": "含参方程/公共根/根的分布/逆向构造",
        "tags": "二次方程,判别式,韦达定理",
    },
    {
        "model_id": "MATH-MS-002",
        "model_name": "函数与图像模型",
        "education_stage": "初中",
        "module": "函数",
        "difficulty": 4,
        "problem_types": "一次函数/反比例函数/二次函数",
        "conditions": "已知函数解析式或图像特征",
        "formulas": "一次: y=kx+b; 反比例: y=k/x; 二次: y=ax²+bx+c 顶点(-b/2a, (4ac-b²)/4a)",
        "steps": "1.确定函数类型 2.求系数 3.画图像 4.分析性质(单调/极值/交点) 5.应用解题",
        "example": "y=x²-4x+3 → 顶点(2,-1), 与x轴交点(1,0)(3,0)",
        "variant": "函数平移/对称/缩放/分段函数",
        "tags": "函数,图像,顶点,交点",
    },
    {
        "model_id": "MATH-MS-003",
        "model_name": "三角形全等相似模型",
        "education_stage": "初中",
        "module": "图形与几何",
        "difficulty": 4,
        "problem_types": "全等判定SSS/SAS/ASA/AAS/HL; 相似判定AA/SAS/SSS",
        "conditions": "已知两边和/或角的关系",
        "formulas": "全等: 对应边相等+对应角相等; 相似: 对应边成比例+对应角相等",
        "steps": "1.找对应边/角 2.选择判定方法 3.证明过程 4.得出结论",
        "example": "△ABC中, AB=AC, D为BC中点 → △ABD≅△ACD (SSS: AB=AC, BD=CD, AD=AD)",
        "variant": "等腰/等边/直角三角形/圆中三角形",
        "tags": "三角形,全等,相似,证明",
    },
    {
        "model_id": "MATH-MS-004",
        "model_name": "圆的性质与计算模型",
        "education_stage": "初中",
        "module": "图形与几何",
        "difficulty": 4,
        "problem_types": "圆心角/圆周角/切线/弦/弧/扇形面积",
        "conditions": "已知半径/圆心角/弦长",
        "formulas": "圆周角=½圆心角; 切线⊥半径; 扇形面积=½r²θ(弧度); 弦长=2r·sin(θ/2)",
        "steps": "1.画图标注 2.找圆心角/圆周角关系 3.应用定理 4.计算求解",
        "example": "圆O半径r=6, 弦AB=6√3, 圆心角∠AOB=120° → 圆周角=60°",
        "variant": "内切圆/外接圆/九点圆/圆幂定理",
        "tags": "圆,切线,圆心角,扇形",
    },
    {
        "model_id": "MATH-MS-005",
        "model_name": "概率与统计模型",
        "education_stage": "初中",
        "module": "统计与概率",
        "difficulty": 3,
        "problem_types": "树状图/列表法/频率估计概率",
        "conditions": "已知试验次数和可能结果",
        "formulas": "P(A)=m/n (等可能); 频率→概率(大数定律); P(A∪B)=P(A)+P(B)-P(A∩B)",
        "steps": "1.列举所有等可能结果 2.找符合条件的结果数 3.计算概率 4.检验合理性",
        "example": "掷两枚骰子, 点数和为7的概率: 6/36=1/6",
        "variant": "条件概率/独立事件/互斥事件/几何概率",
        "tags": "概率,树状图,频率",
    },
    {
        "model_id": "MATH-MS-006",
        "model_name": "不等式与不等式组模型",
        "education_stage": "初中",
        "module": "数与代数",
        "difficulty": 3,
        "problem_types": "一元一次不等式/不等式组/含参不等式",
        "conditions": "已知不等关系",
        "formulas": "ax+b>c → ax>c-b (a>0不变号, a<0变号); 解集取交集(同大取大,同小取小)",
        "steps": "1.移项 2.合并同类项 3.系数化为1(注意变号) 4.画数轴 5.取交集",
        "example": "2x-1<3 → 2x<4 → x<2; x+1≥0 → x≥-1 → 解集: -1≤x<2",
        "variant": "绝对值不等式/分式不等式/含参讨论",
        "tags": "不等式,解集,数轴",
    },
    {
        "model_id": "MATH-MS-007",
        "model_name": "勾股定理模型",
        "education_stage": "初中",
        "module": "图形与几何",
        "difficulty": 3,
        "problem_types": "直角三角形求边/折叠问题/最短路径/立体表面最短",
        "conditions": "已知直角三角形两边, 求第三边",
        "formulas": "a²+b²=c² (c为斜边); 勾股逆定理: 若a²+b²=c²则△为直角三角形; 常见勾股数: 3,4,5; 5,12,13; 8,15,17",
        "steps": "1.判断直角三角形 2.找斜边 3.套勾股定理 4.求解 5.验算",
        "example": "直角三角形两直角边a=3,b=4 → 斜边c=√(9+16)=5",
        "variant": "折叠问题/将军饮马/立体表面最短/风吹红莲",
        "tags": "勾股定理,直角三角形,最短路径",
    },
    {
        "model_id": "MATH-MS-008",
        "model_name": "四边形性质与判定模型",
        "education_stage": "初中",
        "module": "图形与几何",
        "difficulty": 3,
        "problem_types": "平行四边形/矩形/菱形/正方形/中点四边形",
        "conditions": "已知四边形边角对角线关系",
        "formulas": "□: 对边平行且相等, 对角线互相平分; 矩形: 对角线相等; 菱形: 对角线垂直平分; 正方形: 兼具两者; 中点四边形必为平行四边形",
        "steps": "1.识别图形 2.选择性质或判定 3.证明过程 4.下结论",
        "example": "任意四边形中点连线 → 必为平行四边形; 若原对角线相等→菱形, 垂直→矩形",
        "variant": "动点四边形/面积比/折叠问题",
        "tags": "四边形,平行四边形,中点四边形",
    },
    {
        "model_id": "MATH-MS-009",
        "model_name": "二次根式模型",
        "education_stage": "初中",
        "module": "数与代数",
        "difficulty": 3,
        "problem_types": "最简二次根式/分母有理化/双重根式化简/混合运算",
        "conditions": "已知含根号的表达式",
        "formulas": "√a·√b=√(ab) (a,b≥0); √a/√b=√(a/b); 分母有理化: 乘共轭根式; (√a+√b)(√a-√b)=a-b",
        "steps": "1.化最简二次根式 2.分母有理化 3.合并同类二次根式 4.化简 5.验算",
        "example": "1/(√3+√2)=(√3-√2)/((√3+√2)(√3-√2))=(√3-√2)/1=√3-√2",
        "variant": "双重根式/配凑完全平方/换元法",
        "tags": "二次根式,有理化,双重根式",
    },
    {
        "model_id": "MATH-MS-010",
        "model_name": "绝对值方程与不等式模型",
        "education_stage": "初中",
        "module": "数与代数",
        "difficulty": 4,
        "problem_types": "绝对值方程/绝对值不等式/几何意义",
        "conditions": "已知含绝对值的方程或不等式",
        "formulas": "|x|=a(a≥0) → x=±a; |x|<a → -a<x<a; |x|>a → x<-a或x>a; |a-b|几何意义为数轴距离",
        "steps": "1.判断类型 2.用公式或几何意义 3.分类讨论 4.求解 5.验算",
        "example": "|x-2|=3 → x-2=±3 → x=5或x=-1; |x-2|<3 → -3<x-2<3 → -1<x<5",
        "variant": "含参绝对值/多重绝对值/零点分段法",
        "tags": "绝对值,几何意义,分类讨论",
    },
    {
        "model_id": "MATH-MS-011",
        "model_name": "构造法模型",
        "education_stage": "初中",
        "module": "数学思想",
        "difficulty": 5,
        "problem_types": "构造全等三角形/构造直角三角形/构造辅助圆/构造方程",
        "conditions": "题目条件不足或图形残缺",
        "formulas": "核心: 缺什么构造什么; 几何构造辅助线; 代数构造方程(已知a+b=m,ab=n构造t²-mt+n=0)",
        "steps": "1.审题找缺口 2.主动构造 3.回归基础解题 4.验证",
        "example": "已知a+b=5,ab=6 → 构造方程t²-5t+6=0 → t=2或3 → a,b为{2,3}",
        "variant": "截长补短/倍长中线/构造平行四边形/构造圆",
        "tags": "构造法,辅助线,构造方程",
    },
    {
        "model_id": "MATH-MS-012",
        "model_name": "将军饮马最短路径模型",
        "education_stage": "初中",
        "module": "图形与几何",
        "difficulty": 4,
        "problem_types": "两定点一动点求距离和最小/差最大/周长最小",
        "conditions": "已知两定点和一条直线(或圆)",
        "formulas": "作对称点: 距离和最小→两点异侧; 距离差最大→两点同侧; 折线转直线利用两点之间线段最短",
        "steps": "1.识别定点动点 2.作定点关于直线的对称点 3.连对称点与另一定点 4.与直线交点即为动点 5.求最小值",
        "example": "直线l外两点A,B同侧, 求l上点P使PA+PB最小 → 作A关于l的对称点A', 连A'B交l于P, PA+PB=A'B最小",
        "variant": "立体表面最短/圆锥表面/定差定值",
        "tags": "将军饮马,对称点,最短路径",
    },
    {
        "model_id": "MATH-MS-013",
        "model_name": "锐角三角函数模型",
        "education_stage": "初中",
        "module": "图形与几何",
        "difficulty": 4,
        "problem_types": "解直角三角形/仰角俯角/坡度坡角/方向角",
        "conditions": "已知直角三角形一边一锐角或两边",
        "formulas": "sinA=对/斜, cosA=邻/斜, tanA=对/邻; 特殊值: sin30°=1/2, sin45°=√2/2, sin60°=√3/2; 坡度i=tanα=h/l",
        "steps": "1.画图标角 2.选直角三角形 3.选三角函数 4.列方程 5.求解",
        "example": "仰角30°测塔高, 距塔50m → tan30°=h/50 → h=50×√3/3≈28.87m",
        "variant": "双仰角/俯角/方位角/航海问题",
        "tags": "锐角三角函数,仰角,解直角三角形",
    },
    {
        "model_id": "MATH-MS-014",
        "model_name": "数据分析模型(方差标准差)",
        "education_stage": "初中",
        "module": "统计与概率",
        "difficulty": 3,
        "problem_types": "方差/标准差/频数分布/数据波动",
        "conditions": "已知一组或多组数据",
        "formulas": "方差s²=(1/n)Σ(xᵢ-x̄)²; 标准差s=√(方差); 方差越小数据越稳定; 加减常数方差不变, 乘除常数方差乘除平方",
        "steps": "1.求平均数 2.求各数与平均数差 3.平方求和 4.除以n得方差 5.开方得标准差",
        "example": "数据2,4,6,8 → x̄=5; 方差=[(2-5)²+(4-5)²+(6-5)²+(8-5)²]/4=20/4=5; 标准差=√5",
        "variant": "加权方差/分组数据/稳定性比较",
        "tags": "方差,标准差,数据波动",
    },

    # ====== K12 高中 ======
    {
        "model_id": "MATH-HS-001",
        "model_name": "集合与逻辑模型",
        "education_stage": "高中",
        "module": "集合与逻辑",
        "difficulty": 2,
        "problem_types": "集合运算/子集/补集/交集/并集/命题逻辑",
        "conditions": "已知集合元素或条件",
        "formulas": "A∩B={x|x∈A且x∈B}; A∪B={x|x∈A或x∈B}; ∁UA={x|x∉A}; |A∪B|=|A|+|B|-|A∩B|",
        "steps": "1.化简集合 2.画Venn图 3.执行运算 4.验证结果",
        "example": "A={1,2,3}, B={2,3,4} → A∩B={2,3}, A∪B={1,2,3,4}",
        "variant": "集合方程/含参集合/德摩根律/命题等价",
        "tags": "集合,交集,并集,补集",
    },
    {
        "model_id": "MATH-HS-002",
        "model_name": "函数性质与导数模型",
        "education_stage": "高中",
        "module": "函数与导数",
        "difficulty": 5,
        "problem_types": "单调性/奇偶性/周期性/极值/最值/切线",
        "conditions": "已知函数f(x)和区间",
        "formulas": "f'(x)>0单调增; f'(x₀)=0且f''(x₀)<0极大值; 切线: y-f(x₀)=f'(x₀)(x-x₀)",
        "steps": "1.求f'(x) 2.解f'(x)=0找驻点 3.列表判断单调性 4.求极值 5.求最值 6.切线方程",
        "example": "f(x)=x³-3x → f'(x)=3x²-3=0 → x=±1 → x=1处取极大值f(1)=-2",
        "variant": "含参讨论/隐函数求导/高阶导数/积分应用",
        "tags": "导数,单调性,极值,切线",
    },
    {
        "model_id": "MATH-HS-003",
        "model_name": "三角函数与恒等变换模型",
        "education_stage": "高中",
        "module": "三角函数",
        "difficulty": 4,
        "problem_types": "sin/cos/tan化简/求值/图像/解三角形",
        "conditions": "已知角或三角函数值",
        "formulas": "sin²α+cos²α=1; sin(A±B)=sinAcosB±cosAsinB; 正弦定理: a/sinA=2R; 余弦定理: a²=b²+c²-2bc·cosA",
        "steps": "1.判断象限确定符号 2.选择公式 3.化简 4.求值 5.检验",
        "example": "已知sinα=3/5, α∈(π/2,π) → cosα=-4/5 → tanα=-3/4",
        "variant": "辅助角公式/积化和差/解三角形/反三角函数",
        "tags": "三角函数,正弦定理,余弦定理",
    },
    {
        "model_id": "MATH-HS-004",
        "model_name": "数列模型",
        "education_stage": "高中",
        "module": "数列",
        "difficulty": 4,
        "problem_types": "等差数列/等比数列/通项公式/前n项和",
        "conditions": "已知首项/公差/公比或递推关系",
        "formulas": "等差: aₙ=a₁+(n-1)d, Sₙ=na₁+n(n-1)d/2; 等比: aₙ=a₁·r^(n-1), Sₙ=a₁(1-rⁿ)/(1-r)",
        "steps": "1.判断数列类型 2.求首项和公差/公比 3.套公式求通项 4.求前n项和 5.检验",
        "example": "等差数列a₁=2, d=3 → a₁₀=2+9×3=29, S₁₀=2×10+10×9×3/2=155",
        "variant": "递推数列/裂项求和/错位相减/放缩法",
        "tags": "数列,等差,等比,求和",
    },
    {
        "model_id": "MATH-HS-005",
        "model_name": "立体几何模型",
        "education_stage": "高中",
        "module": "立体几何",
        "difficulty": 5,
        "problem_types": "线面关系/面面关系/空间向量/二面角",
        "conditions": "已知空间点坐标或线面关系",
        "formulas": "线面角: sinθ=|a·n|/(|a||n|); 面面角: cosθ=|n₁·n₂|/(|n₁||n₂|); 距离: d=|AP·n|/|n|",
        "steps": "1.建系标坐标 2.求方向向量/法向量 3.套公式 4.判断锐/钝角 5.计算结果",
        "example": "平面法向量n=(1,2,-1), 点A(1,0,1) → 点到平面距离d=|1+0-1-2|/√6=2/√6=√6/3",
        "variant": "翻折问题/截面问题/球内接/体积比",
        "tags": "立体几何,法向量,二面角,距离",
    },
    {
        "model_id": "MATH-HS-006",
        "model_name": "解析几何模型",
        "education_stage": "高中",
        "module": "解析几何",
        "difficulty": 5,
        "problem_types": "直线与圆/椭圆/双曲线/抛物线",
        "conditions": "已知曲线方程或几何条件",
        "formulas": "椭圆: x²/a²+y²/b²=1; 双曲线: x²/a²-y²/b²=1; 抛物线: y²=4px; 弦长: √(1+k²)|x₁-x₂|",
        "steps": "1.设曲线方程 2.联立直线方程 3.韦达定理 4.判别式Δ>0 5.弦长/面积/最值",
        "example": "椭圆x²/4+y²=1, 过(1,0)的直线y=k(x-1) → 联立得(1+4k²)x²-8k²x+4k²-4=0",
        "variant": "焦点弦/中点弦/定点定值/轨迹方程",
        "tags": "解析几何,椭圆,双曲线,抛物线",
    },
    {
        "model_id": "MATH-HS-007",
        "model_name": "概率统计(排列组合二项式)",
        "education_stage": "高中",
        "module": "概率统计",
        "difficulty": 4,
        "problem_types": "排列/组合/二项式定理/条件概率/正态分布",
        "conditions": "已知n个元素取r个",
        "formulas": "A(n,r)=n!/(n-r)!; C(n,r)=n!/[r!(n-r)!]; (a+b)ⁿ=ΣC(n,k)a^(n-k)b^k; E(X)=Σxᵢpᵢ; D(X)=E(X²)-[E(X)]²",
        "steps": "1.判断排列/组合 2.分类或分步 3.套公式 4.计算 5.检验",
        "example": "从5人中选3人: C(5,3)=10; 排列: A(5,3)=60; (x+1)⁵=1+5x+10x²+10x³+5x⁴+x⁵",
        "variant": "隔板法/插空法/捆绑法/容斥原理",
        "tags": "排列组合,二项式,期望,方差",
    },
    {
        "model_id": "MATH-HS-008",
        "model_name": "不等式选讲模型",
        "education_stage": "高中",
        "module": "不等式",
        "difficulty": 4,
        "problem_types": "均值不等式/柯西不等式/绝对值不等式/放缩法",
        "conditions": "已知正实数或不等关系",
        "formulas": "a+b≥2√(ab); a²+b²≥2ab; 柯西: (Σaᵢbᵢ)²≤(Σaᵢ²)(Σbᵢ²); |a|-|b|≤|a±b|≤|a|+|b|",
        "steps": "1.判断不等式类型 2.配凑公式 3.取等条件 4.证明/求解 5.检验",
        "example": "a>0,b>0,a+b=4 → ab≤((a+b)/2)²=4 → ab最大值=4(当a=b=2时取等)",
        "variant": "排序不等式/琴生不等式/放缩/数学归纳法",
        "tags": "不等式,均值不等式,柯西,放缩",
    },
    {
        "model_id": "MATH-HS-009",
        "model_name": "平面向量模型",
        "education_stage": "高中",
        "module": "向量",
        "difficulty": 4,
        "problem_types": "向量运算/数量积/共线垂直/向量分解",
        "conditions": "已知向量坐标或几何关系",
        "formulas": "a=(x,y); a+b=(x₁+x₂,y₁+y₂); |a|=√(x²+y²); a·b=|a||b|cosθ=x₁x₂+y₁y₂; a∥b ⟺ x₁y₂=x₂y₁; a⊥b ⟺ a·b=0",
        "steps": "1.建系标坐标 2.选公式 3.代入计算 4.判断关系 5.求解",
        "example": "a=(1,2),b=(-3,4) → 2a-b=(5,0); a·b=1×(-3)+2×4=5; |a|=√5",
        "variant": "向量分解/三点共线/向量最值/坐标系建系",
        "tags": "向量,数量积,共线垂直",
    },
    {
        "model_id": "MATH-HS-010",
        "model_name": "复数模型",
        "education_stage": "高中",
        "module": "复数",
        "difficulty": 3,
        "problem_types": "复数运算/几何意义/模与辐角/共轭复数",
        "conditions": "已知复数z=a+bi",
        "formulas": "z=a+bi; |z|=√(a²+b²); z̄=a-bi; z·w=(ac-bd)+(ad+bc)i; 1/i=-i; i²=-1; 棣莫弗公式: (cosθ+isinθ)ⁿ=cos(nθ)+isin(nθ)",
        "steps": "1.化简复数 2.选公式 3.代数运算或几何意义 4.求解 5.验证",
        "example": "z=3+4i → |z|=5; z̄=3-4i; z²=(3+4i)²=9+24i-16=-7+24i",
        "variant": "复数方程/辐角主值/欧拉公式/复数几何应用",
        "tags": "复数,模,共轭,棣莫弗",
    },
    {
        "model_id": "MATH-HS-011",
        "model_name": "参数方程与极坐标模型",
        "education_stage": "高中",
        "module": "解析几何",
        "difficulty": 4,
        "problem_types": "极坐标方程/参数方程/直角坐标互化/极坐标应用",
        "conditions": "已知曲线的极坐标或参数方程",
        "formulas": "x=ρcosθ, y=ρsinθ; ρ²=x²+y²; tanθ=y/x; 圆参数: x=r+rcosθ, y=r+rsinθ; 椭圆参数: x=acosθ, y=bsinθ",
        "steps": "1.识别坐标系 2.互化公式 3.代入求解 4.判断几何意义 5.验证",
        "example": "极坐标(2,π/3) → 直角坐标: x=2cos(π/3)=1, y=2sin(π/3)=√3 → (1,√3)",
        "variant": "极坐标曲线/参数化最值/阿基米德螺线/玫瑰线",
        "tags": "极坐标,参数方程,互化",
    },
    {
        "model_id": "MATH-HS-012",
        "model_name": "立体几何向量法模型",
        "education_stage": "高中",
        "module": "立体几何",
        "difficulty": 5,
        "problem_types": "线面角/二面角/距离/空间向量应用",
        "conditions": "已知空间几何体, 可建系",
        "formulas": "线面角: sinθ=|a·n|/(|a||n|); 二面角: cosθ=|n₁·n₂|/(|n₁||n₂|); 点面距: d=|AP·n|/|n|; 法向量求法: 联立两方程",
        "steps": "1.建系标坐标 2.求方向向量 3.设法向量联立求 4.套公式 5.判断锐钝角",
        "example": "正方体ABCD-A₁B₁C₁D₁求A₁到面BDC₁的距离 → 建系求法向量n, 套d=|A₁B·n|/|n|",
        "variant": "动点轨迹/截面问题/外接球/体积比",
        "tags": "立体几何,法向量,二面角,建系",
    },
    {
        "model_id": "MATH-HS-013",
        "model_name": "圆锥曲线综合模型(设而不求)",
        "education_stage": "高中",
        "module": "解析几何",
        "difficulty": 5,
        "problem_types": "弦长/中点弦/定点定值/轨迹方程/面积",
        "conditions": "已知圆锥曲线方程和直线方程",
        "formulas": "联立得二次方程; 韦达定理: x₁+x₂=-b/a, x₁x₂=c/a; 弦长=√(1+k²)|x₁-x₂|; 中点((x₁+x₂)/2,(y₁+y₂)/2); Δ>0保证两交点",
        "steps": "1.设直线方程 2.联立曲线方程 3.韦达定理 4.判别式Δ>0 5.套目标公式 6.化简验证",
        "example": "椭圆x²/4+y²=1, 过右焦点(√3,0)的直线y=k(x-√3) → 联立得(1+4k²)x²-8k²√3x+12k²-4=0 → 韦达求弦长",
        "variant": "焦点弦/中点弦/定点定值/面积最值",
        "tags": "圆锥曲线,设而不求,韦达定理,弦长",
    },
    {
        "model_id": "MATH-HS-014",
        "model_name": "数学归纳法模型",
        "education_stage": "高中",
        "module": "推理与证明",
        "difficulty": 4,
        "problem_types": "等式证明/不等式证明/整除性/数列通项",
        "conditions": "已知含自然数n的命题",
        "formulas": "第一归纳(简单归纳): 验证n=1成立; 假设n=k成立; 推n=k+1也成立; 第二归纳(强归纳): 假设n≤k都成立推n=k+1",
        "steps": "1.验证n=1(初始值) 2.假设n=k成立 3.推n=k+1(关键) 4.结论对一切n∈N*成立",
        "example": "证明1+3+5+...+(2n-1)=n²: n=1: 1=1²✓; 假设1+3+...+(2k-1)=k²; 推n=k+1: k²+(2k+1)=(k+1)²✓",
        "variant": "第二归纳法/跳跃归纳/反向归纳/数学归纳法变式",
        "tags": "数学归纳法,自然数命题,递推",
    },
    {
        "model_id": "MATH-HS-015",
        "model_name": "二项式定理深化模型",
        "education_stage": "高中",
        "module": "概率统计",
        "difficulty": 4,
        "problem_types": "展开式/特定项系数/二项式系数性质/赋值法",
        "conditions": "已知(a+b)ⁿ展开式",
        "formulas": "(a+b)ⁿ=ΣC(n,k)aⁿ⁻ᵏbᵏ; 通项T(r+1)=C(n,r)aⁿ⁻ʳbʳ; 二项式系数和=2ⁿ; 奇偶项和=2ⁿ⁻¹; C(n,0)+C(n,2)+...=C(n,1)+C(n,3)+...=2ⁿ⁻¹",
        "steps": "1.写通项公式 2.根据条件定r 3.求系数或特定项 4.赋值法验证 5.化简",
        "example": "(x+1/x)⁵ → T(r+1)=C(5,r)x^(5-r)·(1/x)^r=C(5,r)x^(5-2r); 常数项令5-2r=0 → r=2.5(无), 故无常数项",
        "variant": "多项式展开/赋值法求系数和/最大系数/二项式反演",
        "tags": "二项式定理,通项公式,二项式系数",
    },
    {
        "model_id": "MATH-HS-016",
        "model_name": "排列组合深化模型(隔板插空捆绑)",
        "education_stage": "高中",
        "module": "概率统计",
        "difficulty": 5,
        "problem_types": "隔板法/插空法/捆绑法/容斥原理/分配问题",
        "conditions": "已知元素及约束(相同/不同/相邻/不相邻)",
        "formulas": "隔板法: x₁+x₂+...+xₖ=n的正整数解个数=C(n-1,k-1); 插空法(不相邻): 先排其他再插入; 捆绑法(相邻): 视整体再排; 容斥: |A∪B|=|A|+|B|-|A∩B|",
        "steps": "1.识别相同/不同元素 2.判断约束类型 3.选方法(隔板/插空/捆绑) 4.套公式 5.验证",
        "example": "10相同球分4人每人至少1 → C(10-1,4-1)=C(9,3)=84种; ABCDEF排列AB相邻 → 视AB一体5!×2=240",
        "variant": "多重容斥/错位排列/圆排列/斯特林数",
        "tags": "隔板法,插空法,捆绑法,容斥",
    },

    # ====== 高等教育 ======
    {
        "model_id": "MATH-HE-001",
        "model_name": "极限与连续模型",
        "education_stage": "高等教育",
        "module": "数学分析",
        "difficulty": 4,
        "problem_types": "数列极限/函数极限/无穷小/连续性/间断点",
        "conditions": "已知f(x)或数列{aₙ}",
        "formulas": "lim(x→a)f(x)=L: ∀ε>0∃δ>0; 重要极限: lim(1+1/x)^x=e; lim(sin x/x)=1; 洛必达法则: lim f/g=lim f'/g'",
        "steps": "1.判断极限类型 2.选方法(代入/洛必达/等价无穷小/夹逼) 3.化简 4.求极限 5.验证连续性",
        "example": "lim(x→0)(sin3x/x)=lim(x→0)(3·sin3x/3x)=3×1=3",
        "variant": "∞-∞型/0·∞型/幂指函数/斯托尔兹定理",
        "tags": "极限,洛必达,等价无穷小,连续",
    },
    {
        "model_id": "MATH-HE-002",
        "model_name": "微分与中值定理模型",
        "education_stage": "高等教育",
        "module": "数学分析",
        "difficulty": 5,
        "problem_types": "求导/高阶导数/泰勒展开/中值定理/极值",
        "conditions": "已知f(x)可导",
        "formulas": "f'(x)=lim[f(x+h)-f(x)]/h; 泰勒: f(x)=Σf⁽ⁿ⁾(a)/n!·(x-a)ⁿ; 中值: ∃ξ, f'(ξ)=(f(b)-f(a))/(b-a)",
        "steps": "1.求导数 2.判断导数符号 3.应用中值定理 4.泰勒展开 5.误差估计",
        "example": "f(x)=eˣ → f'(x)=eˣ → 泰勒: eˣ=1+x+x²/2!+x³/3!+...",
        "variant": "柯西中值/积分中值/凹凸性/拐点",
        "tags": "导数,泰勒,中值定理,极值",
    },
    {
        "model_id": "MATH-HE-003",
        "model_name": "积分模型(定积分与不定积分)",
        "education_stage": "高等教育",
        "module": "数学分析",
        "difficulty": 5,
        "problem_types": "换元积分/分部积分/广义积分/二重积分/三重积分",
        "conditions": "已知f(x)求∫f(x)dx",
        "formulas": "换元: ∫f(g(x))g'(x)dx=∫f(u)du; 分部: ∫u dv=uv-∫v du; 牛顿-莱布尼茨: ∫ₐᵇf(x)dx=F(b)-F(a)",
        "steps": "1.判断积分类型 2.选方法(换元/分部/有理分解) 3.求原函数 4.代上下限 5.验证",
        "example": "∫x·eˣdx = [x·eˣ - ∫eˣdx] = x·eˣ - eˣ + C = (x-1)eˣ + C (分部积分)",
        "variant": "三角换元/倒代换/部分分式/含参积分",
        "tags": "积分,换元,分部,广义积分",
    },
    {
        "model_id": "MATH-HE-004",
        "model_name": "线性代数模型",
        "education_stage": "高等教育",
        "module": "线性代数",
        "difficulty": 4,
        "problem_types": "矩阵运算/行列式/特征值/向量空间/线性方程组",
        "conditions": "已知矩阵A或方程组Ax=b",
        "formulas": "det(A)=Σ(-1)^τa₁ₚ₁a₂ₚ₂...aₙₚₙ; 特征值: |λI-A|=0; Ax=b有解⟺r(A)=r(A|b); 克莱姆法则",
        "steps": "1.化简矩阵 2.求行列式 3.求秩 4.判断解的结构 5.求通解",
        "example": "A=[[1,2],[3,4]] → det(A)=-2, 特征值λ=5±√18 → 迹=5, 行列式=-2",
        "variant": "对角化/正交化/二次型/SVD分解",
        "tags": "矩阵,行列式,特征值,线性方程组",
    },
    {
        "model_id": "MATH-HE-005",
        "model_name": "概率论与数理统计模型",
        "education_stage": "高等教育",
        "module": "概率统计",
        "difficulty": 5,
        "problem_types": "分布函数/期望方差/参数估计/假设检验/回归",
        "conditions": "已知分布类型或样本数据",
        "formulas": "正态N(μ,σ²): f(x)=1/(σ√2π)·e^(-(x-μ)²/2σ²); 矩估计; 极大似然估计; t检验/χ²检验/F检验",
        "steps": "1.确定分布 2.计算期望方差 3.参数估计 4.假设检验 5.结论",
        "example": "X~N(μ,4), 样本均值x̄=5, n=16 → μ的95%置信区间: 5±1.96×2/4 = (4.02, 5.98)",
        "variant": "贝叶斯估计/方差分析/非参数检验/ Bootstrap",
        "tags": "概率分布,期望,假设检验,置信区间",
    },
    {
        "model_id": "MATH-HE-006",
        "model_name": "常微分方程模型",
        "education_stage": "高等教育",
        "module": "微分方程",
        "difficulty": 5,
        "problem_types": "一阶ODE/二阶常系数/变量分离/常数变易/拉普拉斯",
        "conditions": "已知微分方程和初始条件",
        "formulas": "可分离: ∫f(y)dy=∫g(x)dx; 一阶线性: y=e^(-∫Pdx)·[∫Q·e^(∫Pdx)dx+C]; 二阶: r²+pr+q=0",
        "steps": "1.判断ODE类型 2.选解法 3.求通解 4.代入初始条件求特解 5.验证",
        "example": "y'+2y=0 → y=Ce^(-2x) → y(0)=1 → C=1 → y=e^(-2x)",
        "variant": "欧拉法/级数解/偏微分/稳定性分析",
        "tags": "微分方程,变量分离,常数变易,初值问题",
    },
    {
        "model_id": "MATH-HE-007",
        "model_name": "离散数学模型",
        "education_stage": "高等教育",
        "module": "离散数学",
        "difficulty": 4,
        "problem_types": "图论/逻辑/集合/组合数学/数论",
        "conditions": "已知图/逻辑命题/数论问题",
        "formulas": "欧拉路径: 度数为奇数的顶点数为0或2; 欧密顿路径: 依次经过所有顶点一次; 欧拉公式: V-E+F=2",
        "steps": "1.判断离散结构 2.选择定理 3.构造证明 4.验证",
        "example": "完全图K₅有10条边: C(5,2)=10; 平面图V-E+F=2 → K₅非平面图",
        "variant": "着色问题/最短路径/最小生成树/网络流",
        "tags": "图论,逻辑,组合,数论",
    },
    {
        "model_id": "MATH-HE-008",
        "model_name": "数值计算模型",
        "education_stage": "高等教育",
        "module": "数值分析",
        "difficulty": 5,
        "problem_types": "插值/拟合/数值积分/方程求根/ODE数值解",
        "conditions": "已知离散数据或需要近似求解",
        "formulas": "拉格朗日插值; 牛顿插值; 辛普森积分; 牛顿迭代: x_{n+1}=x_n-f(x_n)/f'(x_n); 龙格-库塔法",
        "steps": "1.选择数值方法 2.确定步长 3.迭代计算 4.误差估计 5.收敛性验证",
        "example": "求√2: 牛顿法 x_{n+1}=(x_n+2/x_n)/2 → x₁=1.5, x₂=1.4167, x₃=1.4142 → √2≈1.4142",
        "variant": "切比雪夫逼近/样条插值/有限元/蒙特卡洛",
        "tags": "数值分析,插值,迭代,数值积分",
    },
    {
        "model_id": "MATH-HE-009",
        "model_name": "偏微分方程模型",
        "education_stage": "高等教育",
        "module": "数学物理方程",
        "difficulty": 6,
        "problem_types": "波动方程/热传导方程/拉普拉斯方程/分离变量法/格林函数",
        "conditions": "已知PDE及边界初值条件",
        "formulas": "波动: u_tt=c²u_xx; 热传导: u_t=α²u_xx; 拉普拉斯: ∇²u=0; 分离变量: u(x,t)=X(x)T(t); 格林函数: u(r)=∫G(r,r')f(r')dr'",
        "steps": "1.判断PDE类型(双曲/抛物/椭圆) 2.选方法(分离变量/傅里叶变换/格林函数) 3.求通解 4.代入边界条件 5.验证",
        "example": "弦振动u_tt=c²u_xx, 边值u(0,t)=u(L,t)=0, 初值u(x,0)=f(x) → 分离变量得u=Σ(A_ncos(nπct/L)+B_nsin(nπct/L))sin(nπx/L)",
        "variant": "贝塞尔函数/勒让德多项式/特殊PDE/数值PDE",
        "tags": "PDE,分离变量,波动方程,格林函数",
    },
    {
        "model_id": "MATH-HE-010",
        "model_name": "复变函数模型",
        "education_stage": "高等教育",
        "module": "复变函数",
        "difficulty": 6,
        "problem_types": "解析函数/柯西积分/留数定理/保角映射/洛朗级数",
        "conditions": "已知复变函数f(z)",
        "formulas": "柯西-黎曼: ∂u/∂x=∂v/∂y, ∂u/∂y=-∂v/∂x; 柯西积分: f(z₀)=1/(2πi)∮f(z)/(z-z₀)dz; 留数: ∮f(z)dz=2πiΣRes(f,zₖ); 解析⟺CR条件成立",
        "steps": "1.判断解析性(CR条件) 2.选方法(柯西/留数/保角) 3.求奇点及留数 4.套公式 5.验证",
        "example": "∮e^z/z²dz (绕原点) → z=0为二阶极点, Res(e^z/z²,0)=1!的系数=1 → ∮=2πi×1=2πi",
        "variant": "辐角原理/最大模原理/调和函数/解析延拓",
        "tags": "复变函数,柯西积分,留数定理,解析",
    },
    {
        "model_id": "MATH-HE-011",
        "model_name": "泛函分析模型",
        "education_stage": "高等教育",
        "module": "泛函分析",
        "difficulty": 6,
        "problem_types": "巴拿赫空间/希尔伯特空间/线性算子/谱理论/弱收敛",
        "conditions": "已知赋范空间或线性算子",
        "formulas": "范数: ||x||=√(<x,x>); 完备性: Cauchy列必收敛; Riesz表示: 有界线性泛函f∈H* ⟺∃y∈H, f(x)=<x,y>; 紧算子谱仅有特征值+0",
        "steps": "1.识别空间类型 2.验证完备性 3.分析算子性质 4.套定理 5.求解",
        "example": "L²[0,1]希尔伯特空间, 内积<f,g>=∫₀¹f(x)g(x)dx; 投影Pf=(∫f)·1 → ||Pf||≤||f||",
        "variant": "弱拓扑/弱星收敛/谱分解/不动点",
        "tags": "泛函分析,希尔伯特空间,算子,谱",
    },
    {
        "model_id": "MATH-HE-012",
        "model_name": "抽象代数模型(群环域)",
        "education_stage": "高等教育",
        "module": "抽象代数",
        "difficulty": 6,
        "problem_types": "群论/环论/域论/伽罗瓦理论/同态",
        "conditions": "已知代数结构(群/环/域)及元素",
        "formulas": "群: 满足封闭/结合/单位元/逆元; 子群判定: a,b∈H ⟺ ab⁻¹∈H; 拉格朗日: |H|整除|G|; 同态基本定理: G/ker(φ)≅im(φ); 伽罗瓦群: Gal(E/F)",
        "steps": "1.识别代数结构 2.验证公理 3.套同态/同构定理 4.分析子群正规性 5.结论",
        "example": "S₃的阶6, 拉格朗日定理子群阶只能是1,2,3,6; A₃={e,(123),(132)}是S₃的3阶正规子群",
        "variant": "西罗定理/理想/扩张域/伽罗瓦对应",
        "tags": "抽象代数,群论,同态,拉格朗日",
    },
    {
        "model_id": "MATH-HE-013",
        "model_name": "拓扑学模型",
        "education_stage": "高等教育",
        "module": "拓扑学",
        "difficulty": 6,
        "problem_types": "开集闭集/连通性/紧致性/同伦/基本群/覆盖空间",
        "conditions": "已知拓扑空间(X,τ)",
        "formulas": "开集族τ满足: ∅,X∈τ, 任意并, 有限交; 闭包Ā=A∪A'; 连通: 不能分为两个非空不相交开集; 紧致: 任意开覆盖有有限子覆盖; 基本群π₁(X,x₀)",
        "steps": "1.验证拓扑公理 2.判断连通/紧致 3.求基本群或同伦 4.套定理 5.结论",
        "example": "π₁(S¹)=Z, π₁(Rⁿ)=0(平凡群); S¹与Rⁿ不同伦等价(基本群不同)",
        "variant": "同调群/欧拉示性数/紧致化/纤维丛",
        "tags": "拓扑学,基本群,连通,紧致",
    },
    {
        "model_id": "MATH-HE-014",
        "model_name": "微分几何模型",
        "education_stage": "高等教育",
        "module": "微分几何",
        "difficulty": 6,
        "problem_types": "曲线论/曲面论/曲率/测地线/联络",
        "conditions": "已知曲线r(t)或曲面参数方程",
        "formulas": "弧长: s=∫|r'(t)|dt; 曲率κ=|r'×r''|/|r'|³; 挠率τ=((r'×r'')·r''')/|r'×r''|²; 高斯曲率K=κ₁κ₂; 测地线: 局部最短",
        "steps": "1.求r'(t),r''(t) 2.计算曲率挠率 3.建标架(Frenet) 4.分析曲面性质 5.验证",
        "example": "圆r(t)=(Rcos t, Rsin t, 0) → 曲率κ=1/R, 挠率τ=0(平面曲线挠率为0)",
        "variant": "黎曼度量/张量分析/纤维丛/辛几何",
        "tags": "微分几何,曲率,挠率,测地线",
    },

    # ====== 竞赛数学 ======
    {
        "model_id": "MATH-CM-001",
        "model_name": "数论竞赛模型",
        "education_stage": "竞赛",
        "module": "数论",
        "difficulty": 6,
        "problem_types": "同余/费马小定理/中国剩余定理/原根/二次剩余",
        "conditions": "已知整数关系或同余式",
        "formulas": "费马小定理: a^(p-1)≡1(mod p); 中国剩余定理; 欧拉定理: a^φ(n)≡1(mod n); 威尔逊定理",
        "steps": "1.分析同余关系 2.选择定理 3.化简模运算 4.求解 5.验证",
        "example": "求7^100 mod 11: 费马小定理 → 7^10≡1(mod 11) → 7^100=(7^10)^10≡1(mod 11)",
        "variant": "卢卡斯定理/莫比乌斯反演/Pell方程/连分数",
        "tags": "数论,同余,费马小定理,欧拉定理",
    },
    {
        "model_id": "MATH-CM-002",
        "model_name": "组合数学竞赛模型",
        "education_stage": "竞赛",
        "module": "组合数学",
        "difficulty": 6,
        "problem_types": "计数/存在性/极值/构造/染色",
        "conditions": "已知组合约束条件",
        "formulas": "容斥原理; 抽屉原理; 生成函数; Burnside引理; Polya计数",
        "steps": "1.分析约束 2.选择计数方法 3.分类讨论 4.计算 5.验证",
        "example": "1-200中7的倍数: ⌊200/7⌋=28; 容斥: 7或11的倍数=28+18-2=44",
        "variant": "母函数/递推计数/极值组合/概率方法",
        "tags": "组合,容斥,抽屉,生成函数",
    },
    {
        "model_id": "MATH-CM-003",
        "model_name": "不等式竞赛模型",
        "education_stage": "竞赛",
        "module": "不等式",
        "difficulty": 6,
        "problem_types": "放缩法/柯西/均值/排序/琴生/舒尔",
        "conditions": "已知正实数不等关系",
        "formulas": "柯西不等式; 排序不等式; 琴生不等式; 舒尔不等式; 幂平均不等式",
        "steps": "1.分析不等式结构 2.配凑公式 3.放缩 4.取等条件 5.严格证明",
        "example": "a,b,c>0, a+b+c=3 → Σa²≥3 → a²+b²+c²≥3 (柯西: (a²+b²+c²)(1+1+1)≥(a+b+c)²=9)",
        "variant": "切线法/局部调整/数学归纳/拉格朗日乘数",
        "tags": "不等式,柯西,放缩,竞赛",
    },
    {
        "model_id": "MATH-CM-004",
        "model_name": "几何竞赛模型",
        "education_stage": "竞赛",
        "module": "几何",
        "difficulty": 6,
        "problem_types": "平面几何/解析几何/射影几何/组合几何",
        "conditions": "已知几何图形和条件",
        "formulas": "梅涅劳斯定理; 塞瓦定理; 托勒密定理; 蝴蝶定理; 西姆松线; 极点极线",
        "steps": "1.画精确图形 2.找关键点线 3.选择定理 4.证明 5.验证",
        "example": "圆内接四边形ABCD, 对角线交于P → PA·PC=PB·PD (圆幂定理); 特例: 托勒密 AC·BD=AB·CD+AD·BC",
        "variant": "反演变换/位似/旋转/复数法",
        "tags": "几何,梅涅劳斯,塞瓦,托勒密",
    },
    {
        "model_id": "MATH-CM-005",
        "model_name": "函数方程竞赛模型",
        "education_stage": "竞赛",
        "module": "函数方程",
        "difficulty": 6,
        "problem_types": "柯西方程/连续函数方程/递推函数方程/不动点法",
        "conditions": "已知含未知函数的方程",
        "formulas": "柯西方程f(x+y)=f(x)+f(y)→连续则f(x)=kx; 不动点: f(a)=a; 赋值法: 令x=y=0, x=y, x=-y等",
        "steps": "1.赋特殊值 2.观察结构 3.构造柯西或递推 4.证明唯一性 5.验证",
        "example": "f(x+y)=f(x)+f(y), f(1)=2 → f(n)=2n; 连续则f(x)=2x对所有实数成立",
        "variant": "多元函数方程/含参函数方程/单调函数方程",
        "tags": "函数方程,柯西方程,赋值法,不动点",
    },
    {
        "model_id": "MATH-CM-006",
        "model_name": "组合几何竞赛模型",
        "education_stage": "竞赛",
        "module": "组合几何",
        "difficulty": 6,
        "problem_types": "覆盖问题/极值几何/几何计数/凸包/镶嵌",
        "conditions": "已知几何对象和组合约束",
        "formulas": "凸包: 包含所有点的最小凸集; 覆盖: 面积比较法; 海伦公式面积: S=√(p(p-a)(p-b)(p-c)); 欧拉公式: V-E+F=2(连通平面图)",
        "steps": "1.分析几何性质 2.构造组合结构 3.套极值或计数原理 4.证明 5.验证",
        "example": "正三角形覆盖单位正方形, 最小边长需 ≥ √6/2; 平面镶嵌: 仅正三角形/正方形/正六边形可单独镶嵌",
        "variant": "凸多边形/几何不等式/几何 Ramsey/镶嵌",
        "tags": "组合几何,凸包,覆盖,欧拉公式",
    },
    {
        "model_id": "MATH-CM-007",
        "model_name": "数列竞赛模型",
        "education_stage": "竞赛",
        "module": "数列",
        "difficulty": 6,
        "problem_types": "递推数列/数列不等式/特征方程/母函数",
        "conditions": "已知递推关系或特殊结构数列",
        "formulas": "特征方程法: aₙ₊₂=paₙ₊₁+qaₙ → r²=pr+q; 通解aₙ=A·r₁ⁿ+B·r₂ⁿ; 母函数: A(x)=Σaₙxⁿ; Stolz定理: lim(aₙ/bₙ)=lim(Δa/Δb)",
        "steps": "1.识别递推类型 2.求特征方程 3.写通项 4.母函数或Stolz定理 5.证明不等式",
        "example": "斐波那契Fₙ₊₂=Fₙ₊₁+Fₙ → 特征r²=r+1 → r=(1±√5)/2 → Fₙ=(φⁿ-ψⁿ)/√5 (Binet公式)",
        "variant": "高阶递推/非线性递推/数列极限/放缩求和",
        "tags": "数列竞赛,特征方程,母函数,Stolz",
    },
    {
        "model_id": "MATH-CM-008",
        "model_name": "图论竞赛模型",
        "education_stage": "竞赛",
        "module": "图论",
        "difficulty": 6,
        "problem_types": "极值图论/着色/匹配/连通度/网络流",
        "conditions": "已知图G=(V,E)",
        "formulas": "握手定理: Σd(v)=2|E|; 树: |E|=|V|-1; 二分图判定: 无奇圈; 欧拉图: 所有顶点度数为偶; 棵完全图Kₙ边数n(n-1)/2; Turán定理",
        "steps": "1.分析图结构 2.判断图类(二分/欧拉/哈密顿) 3.套极值或计数定理 4.证明 5.验证",
        "example": "完全图K₆所有边染红蓝两色 → 至少存在一个单色三角形(Ramsey R(3,3)=6)",
        "variant": "Ramsey理论/极值图论/网络流/拓扑图论",
        "tags": "图论竞赛,Ramsey,极值,二分图",
    },
]


def _now() -> str:
    return datetime.now().isoformat()


def _log(msg: str):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{_now()}] {msg}\n")


# ============================================================
# 建表
# ============================================================
def ensure_math_tables():
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_math_solving_models (
            model_id         TEXT PRIMARY KEY,
            model_name       TEXT NOT NULL,
            education_stage  TEXT NOT NULL,
            module           TEXT NOT NULL,
            difficulty       INTEGER DEFAULT 3,
            problem_types    TEXT,
            conditions       TEXT,
            formulas         TEXT,
            steps            TEXT,
            example          TEXT,
            variant          TEXT,
            tags             TEXT,
            created_at       TEXT NOT NULL,
            updated_at       TEXT NOT NULL
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_math_sync_log (
            sync_id     TEXT PRIMARY KEY,
            total       INTEGER DEFAULT 0,
            new_count   INTEGER DEFAULT 0,
            updated     INTEGER DEFAULT 0,
            by_stage    TEXT,
            synced_at   TEXT NOT NULL
        )""")
        conn.commit()
        conn.close()


# ============================================================
# 同步所有数学模型
# ============================================================
def sync_all_models() -> Dict:
    ensure_math_tables()
    now = _now()
    new_count = 0
    updated_count = 0
    by_stage = {}

    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        for model in MATH_MODELS:
            mid = model["model_id"]
            stage = model["education_stage"]
            by_stage[stage] = by_stage.get(stage, 0) + 1

            existing = conn.execute(
                "SELECT model_id FROM mt_math_solving_models WHERE model_id=?", (mid,)
            ).fetchone()

            if existing:
                conn.execute("""
                    UPDATE mt_math_solving_models SET
                    model_name=?, education_stage=?, module=?, difficulty=?,
                    problem_types=?, conditions=?, formulas=?, steps=?,
                    example=?, variant=?, tags=?, updated_at=?
                    WHERE model_id=?
                """, (
                    model["model_name"], stage, model["module"], model["difficulty"],
                    model["problem_types"], model["conditions"], model["formulas"],
                    model["steps"], model["example"], model["variant"],
                    model["tags"], now, mid
                ))
                updated_count += 1
            else:
                conn.execute("""
                    INSERT INTO mt_math_solving_models
                    (model_id, model_name, education_stage, module, difficulty,
                     problem_types, conditions, formulas, steps, example, variant, tags,
                     created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mid, model["model_name"], stage, model["module"], model["difficulty"],
                    model["problem_types"], model["conditions"], model["formulas"],
                    model["steps"], model["example"], model["variant"], model["tags"],
                    now, now
                ))
                new_count += 1

        # 记录同步日志
        import uuid
        sync_id = "SYNC-%s" % uuid.uuid4().hex[:10]
        conn.execute("""
            INSERT INTO mt_math_sync_log
            (sync_id, total, new_count, updated, by_stage, synced_at)
            VALUES (?,?,?,?,?,?)
        """, (
            sync_id, len(MATH_MODELS), new_count, updated_count,
            json.dumps(by_stage, ensure_ascii=False), now
        ))

        conn.commit()
        conn.close()

    _log(f"[SYNC] total={len(MATH_MODELS)} new={new_count} updated={updated_count} by_stage={by_stage}")
    return {
        "total": len(MATH_MODELS),
        "new": new_count,
        "updated": updated_count,
        "by_stage": by_stage,
    }


# ============================================================
# 查看统计
# ============================================================
def get_status() -> Dict:
    ensure_math_tables()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        total = conn.execute("SELECT COUNT(*) FROM mt_math_solving_models").fetchone()[0]

        by_stage = {}
        rows = conn.execute(
            "SELECT education_stage, COUNT(*) FROM mt_math_solving_models GROUP BY education_stage"
        ).fetchall()
        for row in rows:
            by_stage[row[0]] = row[1]

        by_module = {}
        rows = conn.execute(
            "SELECT module, COUNT(*) FROM mt_math_solving_models GROUP BY module"
        ).fetchall()
        for row in rows:
            by_module[row[0]] = row[1]

        by_difficulty = {}
        rows = conn.execute(
            "SELECT difficulty, COUNT(*) FROM mt_math_solving_models GROUP BY difficulty"
        ).fetchall()
        for row in rows:
            by_difficulty[str(row[0])] = row[1]

        last_sync = conn.execute(
            "SELECT synced_at, total, new_count, updated FROM mt_math_sync_log ORDER BY synced_at DESC LIMIT 1"
        ).fetchone()

        conn.close()

    return {
        "total_models": total,
        "by_stage": by_stage,
        "by_module": by_module,
        "by_difficulty": by_difficulty,
        "last_sync": {
            "at": last_sync[0] if last_sync else "N/A",
            "total": last_sync[1] if last_sync else 0,
            "new": last_sync[2] if last_sync else 0,
            "updated": last_sync[3] if last_sync else 0,
        } if last_sync else None,
    }


# ============================================================
# CLI守护
# ============================================================
class MathModelsDaemon:
    @staticmethod
    def read_pid():
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
        existing = MathModelsDaemon.read_pid()
        if existing:
            print(f"[STATUS] RUNNING pid={existing}")
            return
        ensure_math_tables()
        sync_all_models()
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        def _term(signum, frame):
            _log("[DAEMON] SIGTERM")
            MathModelsDaemon.clear_pid()
            sys.exit(0)

        signal.signal(signal.SIGTERM, _term)
        signal.signal(signal.SIGINT, _term)
        _log(f"[DAEMON] START pid={os.getpid()} interval={SYNC_INTERVAL}s")
        while True:
            time.sleep(SYNC_INTERVAL)
            try:
                r = sync_all_models()
                _log(f"[DAEMON] sync: {r}")
            except Exception as e:
                _log(f"[DAEMON] ERROR: {e}")

    @staticmethod
    def stop():
        pid = MathModelsDaemon.read_pid()
        if not pid:
            print("[STATUS] STOPPED")
            return
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        MathModelsDaemon.clear_pid()
        print("[STATUS] STOPPED")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1].lower()
    if cmd == "start":
        MathModelsDaemon.start()
    elif cmd == "stop":
        MathModelsDaemon.stop()
    elif cmd == "sync":
        r = sync_all_models()
        print(f"{'='*60}")
        print(f"  Math Models Sync Result")
        print(f"{'='*60}")
        print(f"  Total models:  {r['total']}")
        print(f"  New:           {r['new']}")
        print(f"  Updated:       {r['updated']}")
        print(f"  By stage:      {r['by_stage']}")
    elif cmd == "status":
        s = get_status()
        print(f"{'='*60}")
        print(f"  Math Models Database Status")
        print(f"{'='*60}")
        print(f"  Total models: {s['total_models']}")
        print(f"{'='*60}")
        print(f"  By education stage:")
        for stage, count in s["by_stage"].items():
            print(f"    {stage:10s}: {count}")
        print(f"{'='*60}")
        print(f"  By module:")
        for mod, count in s["by_module"].items():
            print(f"    {mod:20s}: {count}")
        print(f"{'='*60}")
        print(f"  By difficulty (1=easy ~ 6=competition):")
        for diff, count in s["by_difficulty"].items():
            print(f"    Level {diff}: {count}")
        if s["last_sync"]:
            ls = s["last_sync"]
            print(f"{'='*60}")
            print(f"  Last sync: {ls['at']}")
            print(f"    total={ls['total']} new={ls['new']} updated={ls['updated']}")
    else:
        print(f"  未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
