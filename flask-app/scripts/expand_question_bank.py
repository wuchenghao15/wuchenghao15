import os
import sys
import json
import time
import random
import sqlite3
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

SUBJECTS = [
    '语文', '数学', '英语', '物理', '化学', '生物',
    '历史', '地理', '政治', '科学', '日语',
    '成人高考语文', '成人高考数学', '成人高考英语',
    '成人高考政治', '成人高考物理', '成人高考化学',
    '成人高考历史', '成人高考地理', '成人高考医学综合',
    '自考汉语言文学', '自考法律', '自考会计',
    '自考计算机', '自考心理学', '自考教育学',
    '小学语文', '小学数学', '小学英语', '小学科学',
    '初中语文', '初中数学', '初中英语', '初中物理', '初中化学',
    '初中生物', '初中历史', '初中地理', '初中道德与法治',
    '高中语文', '高中数学', '高中英语', '高中物理', '高中化学',
    '高中生物', '高中历史', '高中地理', '高中政治'
]

QUESTION_TYPES = ['single_choice', 'multiple_choice', 'true_false', 'fill_blank', 'short_answer']

DIFFICULTIES = ['easy', 'medium', 'hard']

MATH_TOPICS = ['代数', '几何', '函数', '概率统计', '三角函数', '数列', '导数', '积分', '方程', '不等式',
                '将军饮马', '胡不归问题', '拉窗帘模型', '费马点', '瓜豆原理', '阿氏圆', '隐圆模型',
                '中点模型', '相似三角形', '勾股定理', '极值点偏移', '隐零点问题', '放缩法', '和差倍问题',
                '鸡兔同笼', '盈亏问题', '植树问题', '年龄问题', '二次函数', '二次函数最值']
CHINESE_TOPICS = ['阅读理解', '文言文', '古诗词', '写作', '基础知识', '现代文', '文学常识', '修辞手法']
ENGLISH_TOPICS = ['词汇', '语法', '阅读理解', '完形填空', '写作', '听力', '翻译', '口语']
PHYSICS_TOPICS = ['力学', '电学', '光学', '热学', '声学', '电磁学', '量子力学', '相对论']
CHEMISTRY_TOPICS = ['有机化学', '无机化学', '化学反应', '元素周期', '溶液', '酸碱盐', '化学平衡']
BIOLOGY_TOPICS = ['细胞', '遗传', '生态', '进化', '人体生理', '微生物', '生物技术']
HISTORY_TOPICS = ['中国古代史', '中国近代史', '世界史', '古代文明', '现代史']
GEOGRAPHY_TOPICS = ['自然地理', '人文地理', '区域地理', '气候', '地形', '资源']
POLITICS_TOPICS = ['经济生活', '政治生活', '文化生活', '哲学', '时事政治']
SCIENCE_TOPICS = ['自然现象', '科学实验', '生命科学', '物质科学', '地球科学']
JAPANESE_TOPICS = ['N5', 'N4', 'N3', 'N2', 'N1', '词汇', '语法', '阅读', '听力']

SUBJECT_TOPICS = {
    '语文': CHINESE_TOPICS,
    '数学': MATH_TOPICS,
    '英语': ENGLISH_TOPICS,
    '物理': PHYSICS_TOPICS,
    '化学': CHEMISTRY_TOPICS,
    '生物': BIOLOGY_TOPICS,
    '历史': HISTORY_TOPICS,
    '地理': GEOGRAPHY_TOPICS,
    '政治': POLITICS_TOPICS,
    '科学': SCIENCE_TOPICS,
    '日语': JAPANESE_TOPICS
}

def generate_math_question(difficulty, topic):
    if difficulty == 'easy':
        template = random.randint(1, 10)
        if topic == '代数':
            if template <= 3:
                a, b, c = random.randint(1, 10), random.randint(1, 10), random.randint(1, 10)
                return f"计算：{a} + {b} × {c} = ?", str(a + b * c)
            elif template <= 6:
                a, b = random.randint(1, 50), random.randint(1, 50)
                return f"计算：{a} - {b} = ?", str(a - b)
            else:
                a, b = random.randint(1, 20), random.randint(1, 20)
                return f"计算：{a} × {b} = ?", str(a * b)
        elif topic == '几何':
            if template <= 4:
                a, b = random.randint(2, 10), random.randint(2, 10)
                return f"一个长方形的长为{a}cm，宽为{b}cm，它的面积是多少平方厘米？", str(a * b)
            elif template <= 7:
                a, b = random.randint(2, 10), random.randint(2, 10)
                return f"一个长方形的长为{a}cm，宽为{b}cm，它的周长是多少厘米？", str(2 * (a + b))
            else:
                r = random.randint(1, 10)
                return f"一个正方形的边长为{r}cm，它的面积是多少平方厘米？", str(r * r)
        elif topic == '方程':
            if template <= 5:
                x = random.randint(1, 10)
                a = random.randint(2, 5)
                b = a * x
                return f"解方程：{a}x = {b}", str(x)
            else:
                x = random.randint(1, 20)
                b = random.randint(1, 20)
                c = x + b
                return f"解方程：x + {b} = {c}", str(x)
        elif topic == '概率统计':
            if template <= 5:
                a, b = random.randint(1, 10), random.randint(1, 10)
                return f"从{a}个红球和{b}个白球中随机取一个球，取到红球的概率是？", f"{a}/{a+b}"
            else:
                nums = [random.randint(1, 20) for _ in range(5)]
                avg = sum(nums) / len(nums)
                return f"求 {', '.join(map(str, nums))} 的平均数", str(avg)
        else:
            a, b = random.randint(1, 50), random.randint(1, 50)
            return f"计算：{a} + {b} = ?", str(a + b)
    
    elif difficulty == 'medium':
        template = random.randint(1, 15)
        if topic == '代数':
            if template <= 5:
                a, b, c = random.randint(1, 20), random.randint(1, 20), random.randint(1, 10)
                return f"化简：{a}x + {b}x - {c}x = ?", f"{a + b - c}x"
            elif template <= 10:
                a, b = random.randint(1, 10), random.randint(1, 10)
                return f"展开：({a}x + {b})({a}x - {b}) = ?", f"{a*a}x**2-{b*b}"
            else:
                a, b, c = random.randint(1, 10), random.randint(1, 10), random.randint(1, 10)
                return f"计算：{a}(x + {b}) + {c}(x - {b}) = ?", f"{a+c}x+{a*b-c*b}"
        elif topic == '函数':
            if template <= 5:
                a, b = random.randint(1, 5), random.randint(-10, 10)
                return f"函数 y = {a}x + {b} 的斜率是多少？", str(a)
            elif template <= 10:
                a, b, c = random.randint(1, 5), random.randint(-10, 10), random.randint(-10, 10)
                return f"函数 y = {a}x**2 + {b}x + {c} 的对称轴是？", f"x=-{b}/({2*a})"
            else:
                a, b = random.randint(1, 10), random.randint(-10, 10)
                return f"函数 y = {a}x + {b} 与y轴的交点坐标是？", f"(0,{b})"
        elif topic == '几何':
            if template <= 5:
                r = random.randint(1, 10)
                return f"一个圆的半径为{r}cm，它的周长是多少厘米？（π取3.14）", str(round(2 * 3.14 * r, 2))
            elif template <= 10:
                r = random.randint(1, 10)
                return f"一个圆的半径为{r}cm，它的面积是多少平方厘米？（π取3.14）", str(round(3.14 * r * r, 2))
            else:
                a, b, c = random.randint(3, 10), random.randint(4, 10), random.randint(5, 10)
                return f"一个三角形的底为{a}cm，高为{b}cm，面积是多少平方厘米？", str(a * b / 2)
        elif topic == '方程':
            if template <= 5:
                a, b = random.randint(1, 10), random.randint(1, 50)
                return f"解方程：{a}x + {b} = {2*b}", str(b // a)
            elif template <= 10:
                a, b, c = random.randint(1, 5), random.randint(1, 20), random.randint(1, 20)
                return f"解方程：{a}x + {b} = {c}x + {a}", str((a - b) // (a - c))
            else:
                x = random.randint(1, 10)
                a, b = random.randint(1, 5), random.randint(1, 10)
                c = a * x + b
                return f"解方程：{a}x + {b} = {c}", str(x)
        else:
            x = random.randint(1, 10)
            return f"计算：{x}**2 + {x} = ?", str(x * x + x)
    
    else:
        template = random.randint(1, 20)
        if topic == '函数':
            if template <= 5:
                a, b = random.randint(1, 5), random.randint(1, 10)
                return f"求函数 f(x) = {a}x**2 + {b}x 的导数", f"{2*a}x + {b}"
            elif template <= 10:
                a, b, c = random.randint(1, 5), random.randint(1, 10), random.randint(1, 10)
                return f"求函数 f(x) = {a}x³ + {b}x**2 + {c}x 的导数", f"{3*a}x**2+{2*b}x+{c}"
            else:
                a, b = random.randint(1, 10), random.randint(-10, 10)
                return f"求函数 y = {a}x**2 + {b} 的最小值", str(b)
        elif topic == '三角函数':
            if template <= 5:
                return "sin**2x + cos**2x = ?", "1"
            elif template <= 10:
                return "tanx = ?", "sinx/cosx"
            else:
                return "sin2x = ?", "2sinxcosx"
        elif topic == '数列':
            if template <= 5:
                a1, d = random.randint(1, 10), random.randint(1, 5)
                return f"等差数列中，a₁={a1}，公差d={d}，求a₁₀", str(a1 + 9 * d)
            elif template <= 10:
                a1, q = random.randint(1, 5), random.randint(2, 4)
                return f"等比数列中，a₁={a1}，公比q={q}，求a₅", str(a1 * (q ** 4))
            else:
                a1, d = random.randint(1, 10), random.randint(1, 5)
                return f"等差数列中，a₁={a1}，公差d={d}，求前10项和", str(10 * a1 + 45 * d)
        elif topic == '导数':
            if template <= 5:
                n = random.randint(2, 5)
                return f"求 y = x^{n} 的导数", f"{n}x^{n-1}"
            elif template <= 10:
                a, n = random.randint(1, 10), random.randint(2, 5)
                return f"求 y = {a}x^{n} 的导数", f"{a*n}x^{n-1}"
            else:
                return "求 y = e^x 的导数", "e^x"
        elif topic == '将军饮马':
            if template <= 6:
                a, b = random.randint(1, 10), random.randint(1, 10)
                return f"在直线l同侧有A、B两点，A到l的距离为{a}，B到l的距离为{b}，A、B在l上的投影距离为{a+b}，求将军饮马最短路径长", str((a+b)*2)
            else:
                a, b, c = random.randint(2, 8), random.randint(2, 8), random.randint(3, 12)
                return f"在河岸l同侧有村庄A和B，A距河岸{a}km，B距河岸{b}km，A、B水平距离{c}km，求从A到河边再到B的最短距离", str((a+b)*2)
        elif topic == '胡不归问题':
            if template <= 6:
                a, b, k = random.randint(3, 10), random.randint(2, 6), random.randint(1, 9)/10
                return f"点A到直线l距离为{a}，点B在l上距A投影点{b}，速度比k={k}，求最短时间路径", f"沿直线到l上某点再到B"
            else:
                a, b, k = random.randint(5, 15), random.randint(3, 8), random.randint(3, 7)/10
                return f"A在沙漠边缘，距公路l距离{a}km，B在公路上距A投影{b}km，沙漠速度与公路速度比为{k}，求A到B最短时间", f"构造三角函数转化"
        elif topic == '拉窗帘模型':
            if template <= 6:
                a, b, c = random.randint(1, 6), random.randint(1, 6), random.randint(2, 10)
                return f"矩形ABCD中，AB={c}, BC={a+b}，E在BC上且BE={a}，求AE+DE最小值", str(c + a + b)
            else:
                a, b, c, d = random.randint(2, 8), random.randint(2, 8), random.randint(3, 12), random.randint(2, 6)
                return f"矩形ABCD中，AB={c}, AD={d}，E在BC上，求AE+DE的最小值", str(c + d)
        elif topic == '费马点':
            if template <= 6:
                a, b, c = random.randint(3, 10), random.randint(3, 10), random.randint(3, 10)
                return f"等边三角形ABC边长为{a}，求费马点到三顶点距离之和", str(a)
            else:
                a, b, c = random.randint(4, 12), random.randint(4, 12), random.randint(4, 12)
                return f"三角形ABC中，AB={a}, BC={b}, CA={c}，求费马点到三顶点距离之和最小值", f"{a+b+c}"
        elif topic == '瓜豆原理':
            if template <= 6:
                r = random.randint(1, 5)
                return f"点A绕点O旋转，P是A的关联点，OP={r}OA，求P的轨迹", f"半径为{r}OA的圆"
            else:
                a, b = random.randint(1, 6), random.randint(1, 6)
                return f"定点O，点A在圆上运动，P满足OP={a}OA且∠AOP={b*30}°，求P的轨迹", f"缩放旋转后的圆"
        elif topic == '阿氏圆':
            if template <= 6:
                a, b, r = random.randint(2, 8), random.randint(1, 4), random.randint(3, 10)
                return f"阿氏圆半径{r}，内分点距圆心{a}，外分点距{b}，求比值k", str(a/b)
            else:
                a, b, k = random.randint(3, 10), random.randint(1, 5), random.randint(1, 9)/10
                return f"已知两点距离{a+b}，内分点距近点{a}，求阿氏圆半径", f"{a*b*k/(1-k**2)}"
        elif topic == '隐圆模型':
            if template <= 6:
                a = random.randint(2, 10)
                return f"点P满足PA={a}, PB={a}，则P的轨迹是", "以AB中点为圆心的圆"
            else:
                a, b = random.randint(3, 10), random.randint(3, 10)
                return f"点P满足∠APB=90°，AB={a+b}，则P的轨迹是", f"以AB为直径的圆"
        elif topic == '中点模型':
            if template <= 6:
                a, b = random.randint(3, 10), random.randint(3, 10)
                return f"三角形ABC中，D、E分别是AB、AC中点，则DE与BC的关系是", "DE平行且等于BC的一半"
            else:
                a, b, c = random.randint(4, 12), random.randint(4, 12), random.randint(4, 12)
                return f"四边形ABCD中，E、F、G、H是各边中点，则EFGH是", "平行四边形"
        elif topic == '相似三角形':
            if template <= 6:
                a, b = random.randint(1, 10), random.randint(1, 10)
                return f"相似三角形对应边比为{a}:{b}，则面积比为", f"{a*a}:{b*b}"
            else:
                a, b, c = random.randint(2, 8), random.randint(2, 8), random.randint(2, 8)
                return f"△ABC∽△DEF，AB={a}, DE={b}, BC={c}，求EF", str(b*c/a)
        elif topic == '勾股定理':
            if template <= 6:
                a, b = random.randint(3, 10), random.randint(4, 10)
                c = int((a*a + b*b)**0.5)
                return f"直角三角形两直角边为{a}和{b}，求斜边", str(c) if c*c == a*a + b*b else f"√({a*a + b*b})"
            else:
                a, b = random.randint(5, 15), random.randint(5, 15)
                return f"直角三角形两直角边分别为{a}cm和{b}cm，斜边长为多少？", f"√({a*a + b*b})cm"
        elif topic == '极值点偏移':
            if template <= 6:
                a = random.randint(1, 5)
                return f"函数f(x)={a}x - lnx的极值点为", f"x=1/{a}"
            else:
                a, b = random.randint(1, 5), random.randint(1, 5)
                return f"函数f(x)={a}x**2 - {b}lnx的极值点为", f"x=√({b}/{2*a})"
        elif topic == '隐零点问题':
            if template <= 6:
                return f"证明函数f(x)=x - e^(-x)存在零点", "利用零点存在定理"
            else:
                a = random.randint(1, 5)
                return f"函数f(x)={a}x - lnx存在隐零点，证明其范围", "构造辅助函数"
        elif topic == '放缩法':
            if template <= 6:
                return f"证明：1/n**2 < 1/(n(n-1)) (n≥2)", "裂项放缩"
            else:
                return f"证明：1+1/2+1/3+...+1/n > ln(n+1)", "积分放缩"
        elif topic == '和差倍问题':
            if template <= 6:
                a, b = random.randint(10, 50), random.randint(5, 20)
                return f"甲数比乙数多{a}，甲数是乙数的{b}倍，求乙数", str(a/(b-1))
            else:
                a, b = random.randint(20, 100), random.randint(2, 5)
                return f"两数之和为{a}，大数是小数的{b}倍，求两数", f"小数={a/(b+1)}, 大数={a*b/(b+1)}"
        elif topic == '鸡兔同笼':
            if template <= 6:
                a, b = random.randint(10, 50), random.randint(20, 150)
                return f"鸡兔同笼共{a}头，{b}脚，求鸡兔各多少只", f"鸡={(4*a-b)/2}, 兔={(b-2*a)/2}"
            else:
                a, b = random.randint(20, 100), random.randint(50, 300)
                return f"鸡兔同笼共{a}只，{b}条腿，鸡和兔各有几只？", f"鸡={(4*a-b)/2}, 兔={(b-2*a)/2}"
        elif topic == '盈亏问题':
            if template <= 6:
                a, b, c = random.randint(3, 10), random.randint(5, 20), random.randint(2, 10)
                return f"每人分{a}个多{b}个，每人分{a+c}个少{c}个，求人数", str((b+c)/c)
            else:
                a, b, c, d = random.randint(5, 15), random.randint(10, 40), random.randint(2, 5), random.randint(5, 20)
                return f"每人分{a}个盈{b}个，每人分{a+c}个亏{d}个，求物品总数", str(a*(b+d)/c + b)
        elif topic == '植树问题':
            if template <= 6:
                a = random.randint(10, 100)
                return f"马路长{a}米，每隔{a//10}米植树一棵，两端都种，共需几棵", str(a//(a//10) + 1)
            else:
                a, b = random.randint(20, 200), random.randint(5, 20)
                return f"圆形池塘周长{a}米，每隔{b}米栽一棵树，共需几棵", str(a//b)
        elif topic == '年龄问题':
            if template <= 6:
                a, b = random.randint(20, 40), random.randint(5, 15)
                return f"爸爸今年{a}岁，儿子今年{b}岁，几年后爸爸年龄是儿子的{a//b}倍", str((a - b*(a//b))/(a//b - 1))
            else:
                a, b, c = random.randint(25, 50), random.randint(5, 15), random.randint(2, 5)
                return f"妈妈今年{a}岁，女儿今年{b}岁，{c}年前妈妈年龄是女儿的{c*4}倍，求{c}年前女儿年龄", str((a-c)/(c*4))
        elif topic == '二次函数':
            if template <= 6:
                a, b, c = random.randint(1, 5), random.randint(-10, 10), random.randint(-10, 10)
                return f"二次函数y={a}x**2+{b}x+{c}的开口方向是", "向上" if a > 0 else "向下"
            else:
                a, b, c = random.randint(1, 5), random.randint(-10, 10), random.randint(-10, 10)
                return f"二次函数y={a}x**2+{b}x+{c}与x轴交点个数", f"判别式Δ={b*b-4*a*c}"
        elif topic == '二次函数最值':
            if template <= 6:
                a, b = random.randint(1, 5), random.randint(-10, 10)
                return f"二次函数y={a}x**2+{b}的最小值是", str(b)
            else:
                a, b, c = random.randint(1, 5), random.randint(-10, 10), random.randint(-10, 10)
                return f"二次函数y={a}x**2+{b}x+{c}的顶点纵坐标是", f"{(4*a*c - b*b)/(4*a)}"
        else:
            a, b, c = random.randint(1, 10), random.randint(-10, 10), random.randint(1, 10)
            return f"解方程：{a}x**2 + {b}x + {c} = 0（用求根公式）", f"x = [-{b} ± √({b}**2 - 4×{a}×{c})]/(2×{a})"

CHINESE_LITERARY_TERMS = [
    ('比喻', '用与本体有相似点的喻体来描绘本体'),
    ('拟人', '把事物当作人来写'),
    ('夸张', '为了表达效果故意扩大或缩小'),
    ('排比', '把三个或以上结构相似的句子排列'),
    ('对偶', '用字数相等、结构相同的短语表达'),
    ('反问', '用疑问的形式表达确定的意思'),
    ('设问', '先提出问题再自己回答'),
    ('借代', '用相关事物代替本体'),
]

CHINESE_IDIOMS = [
    ('画蛇添足', '比喻做了多余的事'),
    ('掩耳盗铃', '比喻自欺欺人'),
    ('亡羊补牢', '比喻出了问题及时补救'),
    ('守株待兔', '比喻死守狭隘经验'),
    ('狐假虎威', '比喻依仗别人的势力欺压人'),
    ('对牛弹琴', '比喻对不懂道理的人讲道理'),
    ('刻舟求剑', '比喻拘泥固执，不知变通'),
    ('拔苗助长', '比喻急于求成，反而坏事'),
]

CHINESE_WRITERS = [
    ('鲁迅', '《呐喊》《彷徨》'),
    ('郭沫若', '《女神》'),
    ('茅盾', '《子夜》'),
    ('巴金', '《家》《春》《秋》'),
    ('老舍', '《骆驼祥子》《茶馆》'),
    ('曹禺', '《雷雨》'),
    ('沈从文', '《边城》'),
    ('钱钟书', '《围城》'),
]

def generate_chinese_question(difficulty, topic):
    if difficulty == 'easy':
        template = random.randint(1, 8)
        if template <= 3:
            poem = random.choice(CHINESE_POEMS)
            return f'"{poem[0]}"的作者是？', poem[1]
        elif template <= 5:
            poem = random.choice(CHINESE_POEMS)
            return f'"{poem[0]}"出自哪首诗？', poem[2]
        elif template <= 7:
            idiom = random.choice(CHINESE_IDIOMS)
            return f'"{idiom[0]}"的意思是？', idiom[1]
        else:
            return '汉字的基本笔画有几种？', '8'
    
    elif difficulty == 'medium':
        template = random.randint(1, 12)
        if template <= 3:
            return '四书包括《大学》《中庸》《论语》和？', '《孟子》'
        elif template <= 5:
            return '五经包括《诗》《书》《礼》《易》和？', '《春秋》'
        elif template <= 7:
            term = random.choice(CHINESE_LITERARY_TERMS)
            return f'"{term[0]}"是什么修辞手法？', term[1]
        elif template <= 9:
            writer = random.choice(CHINESE_WRITERS)
            return f'{writer[0]}的代表作是？', writer[1]
        elif template <= 11:
            return '《水浒传》的作者是？', '施耐庵'
        else:
            return '《三国演义》的作者是？', '罗贯中'
    
    else:
        template = random.randint(1, 10)
        if template <= 2:
            return '《红楼梦》的作者是？', '曹雪芹'
        elif template <= 4:
            return '《西游记》的作者是？', '吴承恩'
        elif template <= 6:
            return '"采菊东篱下，悠然见南山"出自哪位诗人？', '陶渊明'
        elif template <= 8:
            return '唐宋八大家包括韩愈、柳宗元、欧阳修、苏轼、苏洵、苏辙、王安石和？', '曾巩'
        else:
            return '中国古代四大名著是《红楼梦》《三国演义》《水浒传》和？', '《西游记》'

ENGLISH_WORDS_EXTENDED = {
    'blue': '蓝色', 'happy': '快乐', 'beautiful': '美丽', 'important': '重要',
    'different': '不同', 'necessary': '必要', 'difficult': '困难', 'interesting': '有趣',
    'beautiful': '美丽', 'careful': '小心', 'dangerous': '危险', 'excellent': '优秀',
    'famous': '著名', 'generous': '慷慨', 'honest': '诚实', 'important': '重要',
    'jealous': '嫉妒', 'kind': '善良', 'lucky': '幸运', 'mysterious': '神秘',
}

ENGLISH_GRAMMAR_RULES = [
    ('一般现在时第三人称单数动词加s/es', 'She goes to school.'),
    ('一般过去时动词用过去式', 'He went to the park.'),
    ('现在进行时用be+动词ing', 'They are playing football.'),
    ('被动语态用be+过去分词', 'The book is read by students.'),
    ('情态动词后接动词原形', 'She can swim.'),
    ('不定式to后接动词原形', 'I want to go home.'),
]

ENGLISH_PREPOSITIONS = [
    ('in', '在...里面'), ('on', '在...上面'), ('at', '在...'),
    ('under', '在...下面'), ('above', '在...上面'), ('beside', '在...旁边'),
    ('between', '在...之间'), ('among', '在...之中'), ('behind', '在...后面'),
]

def generate_english_question(difficulty, topic):
    if difficulty == 'easy':
        template = random.randint(1, 6)
        if template <= 3:
            word, meaning = random.choice(list(ENGLISH_WORDS_EXTENDED.items()))
            return f'"{word}"的中文意思是？', meaning
        elif template <= 5:
            prep, meaning = random.choice(ENGLISH_PREPOSITIONS)
            return f'"{prep}"的中文意思是？', meaning
        else:
            return '英语字母表有多少个字母？', '26'
    
    elif difficulty == 'medium':
        template = random.randint(1, 8)
        if template <= 3:
            verbs = ['go', 'goes', 'going', 'went']
            return 'She ____ to school every day.', 'goes'
        elif template <= 5:
            return 'He ____ to the park yesterday.', 'went'
        elif template <= 7:
            rule = random.choice(ENGLISH_GRAMMAR_RULES)
            return f'{rule[0]}，这句话的正确形式是？', rule[1]
        else:
            return 'They ____ football now.', 'are playing'
    
    else:
        template = random.randint(1, 6)
        if template <= 2:
            return 'The book ____ by many students.', 'is read'
        elif template <= 4:
            return 'She ____ swim when she was five.', 'could'
        elif template <= 5:
            return 'I want ____ home.', 'to go'
        else:
            return '"beautiful"的比较级是？', 'more beautiful'

def generate_physics_question(difficulty, topic):
    if difficulty == 'easy':
        return '光在真空中的传播速度约为？', '3×10^8 m/s'
    elif difficulty == 'medium':
        return '牛顿第一定律又称为？', '惯性定律'
    else:
        return '功的计算公式是？', 'W=Fs'

def generate_chemistry_question(difficulty, topic):
    if difficulty == 'easy':
        return '水的化学式是？', 'H2O'
    elif difficulty == 'medium':
        return '空气中含量最多的气体是？', '氮气'
    else:
        return '元素周期表中第一个元素是？', '氢'

def generate_biology_question(difficulty, topic):
    if difficulty == 'easy':
        return '人体最大的器官是？', '皮肤'
    elif difficulty == 'medium':
        return '植物进行光合作用的场所是？', '叶绿体'
    else:
        return 'DNA的全称是？', '脱氧核糖核酸'

def generate_history_question(difficulty, topic):
    if difficulty == 'easy':
        return '中国的首都是？', '北京'
    elif difficulty == 'medium':
        return '秦始皇统一六国是在哪一年？', '公元前221年'
    else:
        return '鸦片战争发生在哪一年？', '1840年'

def generate_geography_question(difficulty, topic):
    if difficulty == 'easy':
        return '世界上最大的海洋是？', '太平洋'
    elif difficulty == 'medium':
        return '地球自转一周需要多长时间？', '24小时'
    else:
        return '长江发源于哪里？', '青藏高原'

def generate_politics_question(difficulty, topic):
    if difficulty == 'easy':
        return '我国的根本政治制度是？', '人民代表大会制度'
    elif difficulty == 'medium':
        return '社会主义核心价值观包括多少个词？', '12'
    else:
        return '我国的国家性质是？', '人民民主专政'

def generate_science_question(difficulty, topic):
    if difficulty == 'easy':
        return '一年有多少天？', '365'
    elif difficulty == 'medium':
        return '人体有多少块骨头？', '206'
    else:
        return '地球围绕太阳公转一周需要多长时间？', '一年'

def generate_japanese_question(difficulty, topic):
    if difficulty == 'easy':
        return '"こんにちは"的意思是？', '你好'
    elif difficulty == 'medium':
        return '"ありがとう"的意思是？', '谢谢'
    else:
        return '"すみません"的意思是？', '对不起/打扰了'

def generate_adult_exam_chinese_question(difficulty, topic):
    if difficulty == 'easy':
        return '《诗经》是我国最早的一部什么类型的书籍？', '诗歌总集'
    elif difficulty == 'medium':
        return '鲁迅的原名是？', '周树人'
    else:
        return '"沉舟侧畔千帆过，病树前头万木春"出自哪位诗人的作品？', '刘禹锡'

def generate_adult_exam_math_question(difficulty, topic):
    if difficulty == 'easy':
        a, b = random.randint(1, 20), random.randint(1, 20)
        return f"计算：{a} + {b} = ?", str(a + b)
    elif difficulty == 'medium':
        a, b = random.randint(1, 10), random.randint(1, 10)
        return f"计算：({a} + {b})^2 = ?", str((a + b) ** 2)
    else:
        a, b, c = random.randint(1, 5), random.randint(1, 10), random.randint(1, 10)
        return f"求二次函数 y = {a}x^2 + {b}x + {c} 的顶点坐标", f"(-{b}/{2*a}, {4*a*c-b*b}/{4*a})"

def generate_adult_exam_english_question(difficulty, topic):
    if difficulty == 'easy':
        return 'The sky is ____.', 'blue'
    elif difficulty == 'medium':
        return 'She ____ to school every day.', 'goes'
    else:
        return 'The book ____ by many students.', 'is read'

def generate_adult_exam_politics_question(difficulty, topic):
    if difficulty == 'easy':
        return '我国的根本大法是？', '宪法'
    elif difficulty == 'medium':
        return '社会主义初级阶段的基本路线的核心是？', '一个中心，两个基本点'
    else:
        return '科学发展观的第一要义是？', '发展'

def generate_adult_exam_physics_question(difficulty, topic):
    if difficulty == 'easy':
        return '物体做匀速直线运动时，其加速度为？', '0'
    elif difficulty == 'medium':
        return '动能的计算公式是？', 'Ek = 1/2 mv^2'
    else:
        return '牛顿第二定律的表达式是？', 'F = ma'

def generate_adult_exam_chemistry_question(difficulty, topic):
    if difficulty == 'easy':
        return '原子的中心是什么？', '原子核'
    elif difficulty == 'medium':
        return '物质的量的单位是？', '摩尔'
    else:
        return '化学反应速率的计算公式是？', 'v = Δc/Δt'

def generate_adult_exam_history_question(difficulty, topic):
    if difficulty == 'easy':
        return '新中国成立于哪一年？', '1949年'
    elif difficulty == 'medium':
        return '改革开放是在哪一年开始的？', '1978年'
    else:
        return '辛亥革命发生在哪一年？', '1911年'

def generate_adult_exam_geography_question(difficulty, topic):
    if difficulty == 'easy':
        return '我国面积最大的省级行政区是？', '新疆维吾尔自治区'
    elif difficulty == 'medium':
        return '我国人口最多的省份是？', '广东省'
    else:
        return '世界上最长的河流是？', '尼罗河'

def generate_adult_exam_medical_question(difficulty, topic):
    if difficulty == 'easy':
        return '人体最大的器官是？', '皮肤'
    elif difficulty == 'medium':
        return '心脏有几个腔？', '4个'
    else:
        return '血液循环包括体循环和什么循环？', '肺循环'

def generate_self_exam_chinese_question(difficulty, topic):
    if difficulty == 'easy':
        return '《红楼梦》的作者是？', '曹雪芹'
    elif difficulty == 'medium':
        return '《论语》是记录谁的言行的著作？', '孔子及其弟子'
    else:
        return '《诗经》分为风、雅、颂三部分，其中哪部分是民间歌谣？', '风'

def generate_self_exam_law_question(difficulty, topic):
    if difficulty == 'easy':
        return '法律的本质是什么？', '统治阶级意志的体现'
    elif difficulty == 'medium':
        return '我国的法律体系以什么为核心？', '宪法'
    else:
        return '民法的基本原则包括平等原则、自愿原则和什么原则？', '公平原则'

def generate_self_exam_accounting_question(difficulty, topic):
    if difficulty == 'easy':
        return '会计的基本职能是核算和什么？', '监督'
    elif difficulty == 'medium':
        return '资产=负债+什么？', '所有者权益'
    else:
        return '会计凭证按其填制程序和用途分为原始凭证和什么？', '记账凭证'

def generate_self_exam_computer_question(difficulty, topic):
    if difficulty == 'easy':
        return '计算机的核心部件是？', 'CPU'
    elif difficulty == 'medium':
        return '二进制数1010转换为十进制是？', '10'
    else:
        return '操作系统的主要功能包括进程管理、内存管理和什么管理？', '文件管理'

def generate_self_exam_psychology_question(difficulty, topic):
    if difficulty == 'easy':
        return '心理学的研究对象是？', '心理现象'
    elif difficulty == 'medium':
        return '马斯洛需要层次理论中最高层次的需要是？', '自我实现的需要'
    else:
        return '精神分析学派的创始人是？', '弗洛伊德'

def generate_self_exam_education_question(difficulty, topic):
    if difficulty == 'easy':
        return '教育的本质属性是？', '培养人的社会活动'
    elif difficulty == 'medium':
        return '我国现行学制的结构是？', '学前教育、初等教育、中等教育、高等教育'
    else:
        return '教学过程的基本规律包括间接经验与直接经验相结合和什么？', '掌握知识与发展智力相统一'

def generate_primary_chinese_question(difficulty, topic):
    if difficulty == 'easy':
        poem = random.choice(CHINESE_POEMS)
        return f'"{poem[0]}"的作者是？', poem[1]
    elif difficulty == 'medium':
        return '汉字的拼音有几种声调？', '4种'
    else:
        return '《静夜思》的作者是？', '李白'

def generate_primary_math_question(difficulty, topic):
    if difficulty == 'easy':
        a, b = random.randint(1, 100), random.randint(1, 100)
        return f"计算：{a} + {b} = ?", str(a + b)
    elif difficulty == 'medium':
        a, b = random.randint(1, 20), random.randint(1, 20)
        return f"计算：{a} × {b} = ?", str(a * b)
    else:
        a, b, c = random.randint(1, 10), random.randint(1, 10), random.randint(1, 10)
        return f"计算：{a} + {b} × {c} = ?", str(a + b * c)

def generate_primary_english_question(difficulty, topic):
    if difficulty == 'easy':
        word, meaning = random.choice(list(ENGLISH_WORDS_EXTENDED.items()))
        return f'"{word}"的意思是？', meaning
    elif difficulty == 'medium':
        return 'How many letters are in the English alphabet?', '26'
    else:
        return 'What is the plural of "book"?', 'books'

def generate_primary_science_question(difficulty, topic):
    if difficulty == 'easy':
        return '太阳从哪个方向升起？', '东方'
    elif difficulty == 'medium':
        return '水的三种状态是固态、液态和什么？', '气态'
    else:
        return '植物的光合作用需要什么气体？', '二氧化碳'

def generate_middle_chinese_question(difficulty, topic):
    if difficulty == 'easy':
        return '《西游记》的作者是？', '吴承恩'
    elif difficulty == 'medium':
        return '唐宋八大家中属于唐代的有韩愈和谁？', '柳宗元'
    else:
        return '"海内存知己，天涯若比邻"出自哪位诗人？', '王勃'

def generate_middle_math_question(difficulty, topic):
    if difficulty == 'easy':
        x = random.randint(1, 20)
        return f"解方程：x + {x} = {2*x}", str(x)
    elif difficulty == 'medium':
        a, b = random.randint(1, 10), random.randint(1, 20)
        return f"解方程：{a}x = {a*b}", str(b)
    else:
        a, b, c = random.randint(1, 5), random.randint(-10, 10), random.randint(-10, 10)
        return f"求二次函数 y = {a}x^2 + {b}x + {c} 的判别式", f"Δ = {b}^2 - 4×{a}×{c}"

def generate_middle_english_question(difficulty, topic):
    if difficulty == 'easy':
        return 'She ___ to school.', 'goes'
    elif difficulty == 'medium':
        return 'They ___ playing football now.', 'are'
    else:
        return 'The letter ___ by Tom yesterday.', 'was written'

def generate_middle_physics_question(difficulty, topic):
    if difficulty == 'easy':
        return '力的单位是？', '牛顿'
    elif difficulty == 'medium':
        return '速度的计算公式是？', 'v = s/t'
    else:
        return '重力加速度g约等于多少？', '9.8 m/s^2'

def generate_middle_chemistry_question(difficulty, topic):
    if difficulty == 'easy':
        return '氧气的化学式是？', 'O2'
    elif difficulty == 'medium':
        return '二氧化碳的化学式是？', 'CO2'
    else:
        return '酸碱中和反应生成盐和什么？', '水'

def generate_middle_biology_question(difficulty, topic):
    if difficulty == 'easy':
        return '细胞的基本结构包括细胞膜、细胞质和什么？', '细胞核'
    elif difficulty == 'medium':
        return '光合作用的产物是氧气和什么？', '有机物'
    else:
        return 'DNA位于细胞的哪个结构中？', '细胞核'

def generate_middle_history_question(difficulty, topic):
    if difficulty == 'easy':
        return '中国古代四大发明包括造纸术、印刷术、火药和什么？', '指南针'
    elif difficulty == 'medium':
        return '唐朝的开国皇帝是？', '李渊'
    else:
        return '明朝的开国皇帝是？', '朱元璋'

def generate_middle_geography_question(difficulty, topic):
    if difficulty == 'easy':
        return '地球的形状是什么？', '球体'
    elif difficulty == 'medium':
        return '我国的四大高原是青藏高原、黄土高原、内蒙古高原和什么？', '云贵高原'
    else:
        return '世界上面积最大的国家是？', '俄罗斯'

def generate_middle_politics_question(difficulty, topic):
    if difficulty == 'easy':
        return '我国的国旗是？', '五星红旗'
    elif difficulty == 'medium':
        return '我国的国歌是？', '义勇军进行曲'
    else:
        return '我国的国体是？', '人民民主专政'

def generate_high_chinese_question(difficulty, topic):
    if difficulty == 'easy':
        return '《离骚》的作者是？', '屈原'
    elif difficulty == 'medium':
        return '《史记》的作者是？', '司马迁'
    else:
        return '"落霞与孤鹜齐飞，秋水共长天一色"出自哪篇文章？', '《滕王阁序》'

def generate_high_math_question(difficulty, topic):
    if difficulty == 'easy':
        a = random.randint(1, 10)
        return f"求函数 y = {a}x 的导数", str(a)
    elif difficulty == 'medium':
        a, b = random.randint(1, 5), random.randint(1, 10)
        return f"求函数 y = {a}x^2 + {b}x 的导数", f"{2*a}x + {b}"
    else:
        a, b, c = random.randint(1, 5), random.randint(1, 10), random.randint(1, 10)
        return f"求函数 y = {a}x^3 + {b}x^2 + {c}x 的导数", f"{3*a}x^2 + {2*b}x + {c}"

def generate_high_english_question(difficulty, topic):
    if difficulty == 'easy':
        return 'The weather is getting ___ and ___.', 'colder, colder'
    elif difficulty == 'medium':
        return 'It is the first time that I ___ to Beijing.', 'have been'
    else:
        return '___ the project was completed ahead of schedule.', 'To our surprise'

def generate_high_physics_question(difficulty, topic):
    if difficulty == 'easy':
        return '功的单位是？', '焦耳'
    elif difficulty == 'medium':
        return '功率的计算公式是？', 'P = W/t'
    else:
        return '安培力的计算公式是？', 'F = BIL'

def generate_high_chemistry_question(difficulty, topic):
    if difficulty == 'easy':
        return '原子序数等于质子数还是中子数？', '质子数'
    elif difficulty == 'medium':
        return '元素周期表有多少个周期？', '7个'
    else:
        return '化学键包括离子键、共价键和什么？', '金属键'

def generate_high_biology_question(difficulty, topic):
    if difficulty == 'easy':
        return 'DNA的基本组成单位是？', '脱氧核苷酸'
    elif difficulty == 'medium':
        return '遗传信息的传递过程是DNA→RNA→什么？', '蛋白质'
    else:
        return '孟德尔遗传定律包括分离定律和什么定律？', '自由组合定律'

def generate_high_history_question(difficulty, topic):
    if difficulty == 'easy':
        return '第一次世界大战爆发于哪一年？', '1914年'
    elif difficulty == 'medium':
        return '第二次世界大战爆发于哪一年？', '1939年'
    else:
        return '巴黎和会召开于哪一年？', '1919年'

def generate_high_geography_question(difficulty, topic):
    if difficulty == 'easy':
        return '地球自转的方向是？', '自西向东'
    elif difficulty == 'medium':
        return '地球公转的周期是？', '一年'
    else:
        return '大气圈分为对流层、平流层和什么层？', '高层大气'

def generate_high_politics_question(difficulty, topic):
    if difficulty == 'easy':
        return '唯物辩证法的实质和核心是什么？', '对立统一规律'
    elif difficulty == 'medium':
        return '实践是检验真理的唯一标准，这是谁提出的观点？', '马克思'
    else:
        return '社会存在决定社会意识，社会意识对社会存在具有什么作用？', '反作用'

SUBJECT_GENERATORS = {
    '语文': generate_chinese_question,
    '数学': generate_math_question,
    '英语': generate_english_question,
    '物理': generate_physics_question,
    '化学': generate_chemistry_question,
    '生物': generate_biology_question,
    '历史': generate_history_question,
    '地理': generate_geography_question,
    '政治': generate_politics_question,
    '科学': generate_science_question,
    '日语': generate_japanese_question,
    '成人高考语文': generate_adult_exam_chinese_question,
    '成人高考数学': generate_adult_exam_math_question,
    '成人高考英语': generate_adult_exam_english_question,
    '成人高考政治': generate_adult_exam_politics_question,
    '成人高考物理': generate_adult_exam_physics_question,
    '成人高考化学': generate_adult_exam_chemistry_question,
    '成人高考历史': generate_adult_exam_history_question,
    '成人高考地理': generate_adult_exam_geography_question,
    '成人高考医学综合': generate_adult_exam_medical_question,
    '自考汉语言文学': generate_self_exam_chinese_question,
    '自考法律': generate_self_exam_law_question,
    '自考会计': generate_self_exam_accounting_question,
    '自考计算机': generate_self_exam_computer_question,
    '自考心理学': generate_self_exam_psychology_question,
    '自考教育学': generate_self_exam_education_question,
    '小学语文': generate_primary_chinese_question,
    '小学数学': generate_primary_math_question,
    '小学英语': generate_primary_english_question,
    '小学科学': generate_primary_science_question,
    '初中语文': generate_middle_chinese_question,
    '初中数学': generate_middle_math_question,
    '初中英语': generate_middle_english_question,
    '初中物理': generate_middle_physics_question,
    '初中化学': generate_middle_chemistry_question,
    '初中生物': generate_middle_biology_question,
    '初中历史': generate_middle_history_question,
    '初中地理': generate_middle_geography_question,
    '初中道德与法治': generate_middle_politics_question,
    '高中语文': generate_high_chinese_question,
    '高中数学': generate_high_math_question,
    '高中英语': generate_high_english_question,
    '高中物理': generate_high_physics_question,
    '高中化学': generate_high_chemistry_question,
    '高中生物': generate_high_biology_question,
    '高中历史': generate_high_history_question,
    '高中地理': generate_high_geography_question,
    '高中政治': generate_high_politics_question
}

def generate_question(subject, q_type, difficulty):
    topic = random.choice(SUBJECT_TOPICS.get(subject, ['通用']))
    generator = SUBJECT_GENERATORS.get(subject, generate_science_question)
    
    try:
        content, answer = generator(difficulty, topic)
    except:
        content, answer = f"{subject}-{topic}问题", "答案"
    
    options = {}
    if q_type in ['single_choice', 'multiple_choice']:
        distractors = generate_distractors(answer, subject)
        all_options = [answer] + distractors
        random.shuffle(all_options)
        options = {chr(65+i): opt for i, opt in enumerate(all_options)}
    elif q_type == 'true_false':
        options = {'A': '正确', 'B': '错误'}
        is_true = random.random() > 0.5
        answer = 'A' if is_true else 'B'
        if not is_true:
            content = "（判断正误）" + content
    else:
        options = {}
    
    return {
        'question_text': content,
        'options': json.dumps(options),
        'correct_answer': answer,
        'subject': subject,
        'topic': topic,
        'question_type': q_type,
        'difficulty': difficulty,
        'explanation': f"{subject}{topic}知识点解析"
    }

CHINESE_POEMS = [
    ('床前明月光', '李白', '静夜思'), ('春眠不觉晓', '孟浩然', '春晓'),
    ('白日依山尽', '王之涣', '登鹳雀楼'), ('锄禾日当午', '李绅', '悯农'),
    ('举头望明月', '李白', '静夜思'), ('红豆生南国', '王维', '相思'),
    ('独在异乡为异客', '王维', '九月九日忆山东兄弟'), ('飞流直下三千尺', '李白', '望庐山瀑布'),
    ('日照香炉生紫烟', '李白', '望庐山瀑布'), ('两个黄鹂鸣翠柳', '杜甫', '绝句'),
    ('一行白鹭上青天', '杜甫', '绝句'), ('窗含西岭千秋雪', '杜甫', '绝句'),
    ('门泊东吴万里船', '杜甫', '绝句'), ('千山鸟飞绝', '柳宗元', '江雪'),
    ('万径人踪灭', '柳宗元', '江雪'), ('孤舟蓑笠翁', '柳宗元', '江雪'),
    ('独钓寒江雪', '柳宗元', '江雪'), ('野火烧不尽', '白居易', '赋得古原草送别'),
    ('春风吹又生', '白居易', '赋得古原草送别'), ('离离原上草', '白居易', '赋得古原草送别'),
]

CHINESE_AUTHORS = ['李白', '杜甫', '白居易', '王维', '孟浩然', '王之涣', '李绅', '柳宗元']
CHINESE_WORKS = ['静夜思', '春晓', '登鹳雀楼', '悯农', '相思', '九月九日忆山东兄弟', '望庐山瀑布', '绝句', '江雪', '赋得古原草送别']

ENGLISH_WORDS = {
    'blue': ['red', 'green', 'yellow'], 'happy': ['sad', 'angry', 'tired'],
    'beautiful': ['ugly', 'ordinary', 'plain'], 'important': ['unimportant', 'trivial', 'minor'],
    'different': ['same', 'similar', 'identical'], 'necessary': ['unnecessary', 'optional', 'extra'],
    'difficult': ['easy', 'simple', 'straightforward'], 'interesting': ['boring', 'dull', 'uninteresting'],
    'goes': ['go', 'going', 'went'], 'am': ['is', 'are', 'be'],
    'was': ['is', 'were', 'be'], 'were': ['was', 'are', 'be'],
    'read': ['reads', 'reading', 'readed'], 'written': ['wrote', 'writing', 'write']
}

PHYSICS_FACTS = {
    '3×10^8 m/s': ['3×10^7 m/s', '3×10^9 m/s', '3×10^6 m/s'],
    '惯性定律': ['牛顿第二定律', '牛顿第三定律', '万有引力定律'],
    'W=Fs': ['W=Pt', 'P=W/t', 'F=ma'],
    '竖直向下': ['水平向右', '竖直向上', '水平向左'],
    '固体': ['液体', '气体', '真空'],
}

CHEMISTRY_FACTS = {
    'H2O': ['H2O2', 'CO2', 'NaCl'],
    '氮气': ['氧气', '二氧化碳', '氢气'],
    'HCl': ['H2SO4', 'NaOH', 'NaCl'],
    '氢': ['氦', '锂', '碳'],
    '不变': ['增加', '减少', '不确定'],
}

BIOLOGY_FACTS = {
    '皮肤': ['心脏', '肝脏', '大脑'],
    '叶绿体': ['线粒体', '细胞核', '细胞膜'],
    '脱氧核糖核酸': ['核糖核酸', '氨基酸', '蛋白质'],
    '23对': ['22对', '24对', '46对'],
    '细胞膜、细胞质、细胞核': ['细胞膜、细胞质、叶绿体', '细胞膜、细胞核、线粒体', '细胞质、细胞核、叶绿体'],
}

HISTORY_FACTS = {
    '北京': ['上海', '南京', '西安'],
    '公元前221年': ['公元前220年', '公元前222年', '公元前210年'],
    '1840年': ['1839年', '1841年', '1850年'],
    '秦始皇': ['汉武帝', '唐太宗', '宋太祖'],
}

GEOGRAPHY_FACTS = {
    '太平洋': ['大西洋', '印度洋', '北冰洋'],
    '24小时': ['12小时', '36小时', '48小时'],
    '青藏高原': ['黄土高原', '内蒙古高原', '云贵高原'],
    '赤道': ['回归线', '极圈', '经线'],
}

POLITICS_FACTS = {
    '人民代表大会制度': ['多党合作制度', '民族区域自治制度', '基层群众自治制度'],
    '12': ['8', '16', '24'],
    '人民民主专政': ['无产阶级专政', '资产阶级专政', '社会主义民主'],
}

JAPANESE_FACTS = {
    '你好': ['谢谢', '对不起', '再见'],
    '谢谢': ['你好', '对不起', '再见'],
    '对不起/打扰了': ['你好', '谢谢', '再见'],
}

SUBJECT_DISTRACTORS = {
    '语文': {'authors': CHINESE_AUTHORS, 'works': CHINESE_WORKS, 'poems': CHINESE_POEMS},
    '英语': {'words': ENGLISH_WORDS},
    '物理': {'facts': PHYSICS_FACTS},
    '化学': {'facts': CHEMISTRY_FACTS},
    '生物': {'facts': BIOLOGY_FACTS},
    '历史': {'facts': HISTORY_FACTS},
    '地理': {'facts': GEOGRAPHY_FACTS},
    '政治': {'facts': POLITICS_FACTS},
    '日语': {'facts': JAPANESE_FACTS},
}

def generate_distractors(correct_answer, subject):
    distractors = []
    
    if subject == '数学':
        num_answer = None
        try:
            num_answer = float(correct_answer)
        except:
            pass
        if num_answer is not None:
            for _ in range(3):
                offset = random.uniform(-0.3, 0.3)
                distractors.append(str(round(num_answer * (1 + offset), 2)))
        elif 'x' in correct_answer or 'X' in correct_answer:
            distractors = ['2x', '3x', '4x']
        else:
            distractors = ['1', '2', '3']
    
    elif subject == '语文':
        if any(poem[0] in correct_answer for poem in CHINESE_POEMS):
            authors = [a for a in CHINESE_AUTHORS if a != correct_answer]
            distractors = random.sample(authors, min(3, len(authors)))
        elif correct_answer in CHINESE_WORKS:
            works = [w for w in CHINESE_WORKS if w != correct_answer]
            distractors = random.sample(works, min(3, len(works)))
        else:
            distractors = ['选项A', '选项B', '选项C']
    
    elif subject == '英语':
        for word, alternatives in ENGLISH_WORDS.items():
            if correct_answer == word or correct_answer.lower() == word:
                distractors = alternatives[:3]
                break
        if not distractors:
            distractors = ['wrong', 'incorrect', 'mistake']
    
    elif subject in ['物理', '化学', '生物', '历史', '地理', '政治', '日语']:
        facts = SUBJECT_DISTRACTORS.get(subject, {}).get('facts', {})
        for key, alternatives in facts.items():
            if correct_answer in key or key in correct_answer:
                distractors = alternatives[:3]
                break
        if not distractors:
            distractors = ['选项A', '选项B', '选项C']
    
    else:
        distractors = ['选项A', '选项B', '选项C']
    
    return distractors[:3]

def batch_generate_questions(subject, count, thread_id=0):
    questions = []
    for i in range(count):
        q_type = random.choice(QUESTION_TYPES)
        difficulty = random.choice(DIFFICULTIES)
        question = generate_question(subject, q_type, difficulty)
        questions.append(question)
        if (i + 1) % 1000 == 0:
            print(f"  Thread {thread_id}: Generated {i+1}/{count} questions for {subject}")
    return questions

def save_questions_batch(questions, conn):
    cursor = conn.cursor()
    try:
        cursor.executemany('''
            INSERT INTO knowledge_base_questions 
            (question_id, question_text, options, correct_answer, 
             subject, topic, question_type, difficulty, explanation, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', [
            (str(uuid.uuid4())[:16], q['question_text'], q['options'], 
             q['correct_answer'], q['subject'], q['topic'], 
             q['question_type'], q['difficulty'], q['explanation'])
            for q in questions
        ])
        conn.commit()
        return len(questions)
    except Exception as e:
        print(f"Save error: {e}")
        conn.rollback()
        return 0

def expand_subject_questions(subject, target_count=1000):
    print(f"\n=== 开始扩充 {subject} 题库 ===")
    start_time = time.time()
    
    batch_size = 1000
    total_generated = 0
    total_saved = 0
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM knowledge_base_questions WHERE subject = ?', (subject,))
        current_count = cursor.fetchone()[0]
        print(f"当前 {subject} 题目数量: {current_count}")
        
        needed_count = max(0, target_count - current_count)
        print(f"需要新增题目数量: {needed_count}")
        
        if needed_count <= 0:
            print(f"{subject} 题库已达到目标数量！")
            return 0
        
        batches = (needed_count + batch_size - 1) // batch_size
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for batch_num in range(batches):
                actual_size = min(batch_size, needed_count - batch_num * batch_size)
                futures.append(executor.submit(batch_generate_questions, subject, actual_size, batch_num))
            
            for future in as_completed(futures):
                questions = future.result()
                saved = save_questions_batch(questions, conn)
                total_saved += saved
                total_generated += len(questions)
                
                progress = min(100, (total_saved / needed_count) * 100)
                elapsed = time.time() - start_time
                eta = (elapsed / total_saved) * (needed_count - total_saved) if total_saved > 0 else 0
                print(f"  进度: {total_saved}/{needed_count} ({progress:.1f}%) | "
                      f"已用: {elapsed:.1f}s | 预计剩余: {eta:.1f}s")
    
    elapsed_total = time.time() - start_time
    print(f"\n=== {subject} 题库扩充完成 ===")
    print(f"生成题目: {total_generated}")
    print(f"成功保存: {total_saved}")
    print(f"耗时: {elapsed_total:.1f}秒")
    
    return total_saved

def init_database():
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT UNIQUE NOT NULL,
                question_text TEXT NOT NULL,
                options TEXT,
                correct_answer TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT,
                question_type TEXT DEFAULT 'single_choice',
                difficulty TEXT DEFAULT 'medium',
                explanation TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_kbq_subject ON knowledge_base_questions(subject)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_kbq_type ON knowledge_base_questions(question_type)
        ''')
        conn.commit()
        print("数据库表初始化完成")

def main():
    print("=" * 60)
    print("MTSCOS 题库扩充工具")
    print("=" * 60)
    
    init_database()
    
    print(f"\n目标: 每个科目扩充到 1000 道题目")
    print(f"涉及科目: {', '.join(SUBJECTS)}")
    
    total_added = 0
    for subject in SUBJECTS:
        added = expand_subject_questions(subject, 1000)
        total_added += added
    
    print("\n" + "=" * 60)
    print("题库扩充全部完成！")
    print(f"总计新增题目: {total_added}")
    print("=" * 60)

if __name__ == '__main__':
    main()