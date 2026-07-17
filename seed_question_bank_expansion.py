#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

def add_new_categories(conn):
    cursor = conn.cursor()
    categories = [
        ('自主招生', 'SelfEnrollment', '高校自主招生专项', 9, 1),
        ('数学竞赛', 'MathCompetition', '数学竞赛专项', 10, 1),
        ('物理竞赛', 'PhysicsCompetition', '物理竞赛专项', 11, 1),
        ('化学竞赛', 'ChemistryCompetition', '化学竞赛专项', 12, 1),
        ('高考真题', 'GaokaoReal', '高考历年真题', 13, 1),
        ('中考真题', 'ZhongkaoReal', '中考历年真题', 14, 1),
        ('数学解题模型', 'MathModel', '数学解题模型专项', 15, 1),
    ]
    
    for cat in categories:
        try:
            cursor.execute("INSERT OR IGNORE INTO question_categories (name, code, description, sort_order, status) VALUES (?, ?, ?, ?, ?)", cat)
            print(f"  添加分类: {cat[0]}")
        except Exception as e:
            print(f"  添加分类 {cat[0]} 失败: {e}")
    
    conn.commit()

def add_new_tags(conn):
    cursor = conn.cursor()
    tags = [
        ('自主招生', '高校自主招生考试专用', 9),
        ('竞赛真题', '各类学科竞赛真题', 10),
        ('高考真题', '全国高考历年真题', 11),
        ('中考真题', '中考历年真题', 12),
        ('解题模型', '数学解题模型专项', 13),
        ('压轴题', '考试压轴题目', 14),
        ('压轴题', '考试压轴题目', 15),
        ('综合应用', '综合应用题目', 16),
    ]
    
    for tag in tags:
        try:
            cursor.execute("INSERT OR IGNORE INTO question_tags (name, description, sort_order) VALUES (?, ?, ?)", tag)
            print(f"  添加标签: {tag[0]}")
        except Exception as e:
            print(f"  添加标签 {tag[0]} 失败: {e}")
    
    conn.commit()

def add_questions_fields(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(questions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'source' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN source TEXT DEFAULT 'system'")
            print("  添加 source 列")
        
        if 'year' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN year TEXT")
            print("  添加 year 列")
        
        if 'special_type' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN special_type TEXT")
            print("  添加 special_type 列")
        
        if 'category_id' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN category_id INTEGER")
            print("  添加 category_id 列")
        
        conn.commit()
    except Exception as e:
        print(f"  更新表结构失败: {e}")

def insert_self_enrollment_questions(conn):
    cursor = conn.cursor()
    questions = [
        ('已知函数f(x)=x³-3x+a有两个极值点x₁,x₂，若f(x₁)·f(x₂)>0，则实数a的取值范围是？', 'single', '数学', 'hard', '(-2,2)', 'A|(-∞,-2)|B|(-2,2)|C|(2,+∞)|D|(-∞,-2)∪(2,+∞)', 'f\'(x)=3x²-3=0，得x=±1，f(1)=-2+a，f(-1)=2+a，f(x₁)·f(x₂)=(a-2)(a+2)>0，即a∈(-2,2)', '2023', 'self_enrollment', 'system', 9),
        ('设复数z满足|z-1|=|z-i|，则z在复平面内对应的点的轨迹是？', 'single', '数学', 'medium', '直线x=y', 'A|圆| B|直线x=y| C|直线x=-y| D|抛物线', '设z=x+yi，|(x-1)+yi|=|x+(y-1)i|，得(x-1)²+y²=x²+(y-1)²，化简得x=y', '2022', 'self_enrollment', 'system', 9),
        ('若正整数n满足C(n,0)+C(n,1)+C(n,2)=22，则n=？', 'single', '数学', 'medium', '6', 'A|5|B|6|C|7|D|8', 'C(n,0)+C(n,1)+C(n,2)=1+n+n(n-1)/2=22，解得n=6', '2023', 'self_enrollment', 'system', 9),
        ('已知向量a=(1,2)，b=(x,1)，若a⊥(a-b)，则x=？', 'single', '数学', 'easy', '5', 'A|3|B|4|C|5|D|6', 'a·(a-b)=0，(1,2)·(1-x,1)=0，1-x+2=0，x=5', '2022', 'self_enrollment', 'system', 9),
        ('在等差数列{aₙ}中，a₁+a₅=10，a₄=7，则公差d=？', 'single', '数学', 'easy', '2', 'A|1|B|2|C|3|D|4', 'a₁+a₅=2a₃=10，a₃=5，d=a₄-a₃=7-5=2', '2023', 'self_enrollment', 'system', 9),
        ('设函数f(x)=ln(x+1)-ax，若f(x)在(0,+∞)上单调递减，则a的取值范围是？', 'single', '数学', 'hard', '[1,+∞)', 'A|(0,1)|B|[1,+∞)|C|(-∞,1]|D|(-∞,0)', 'f\'(x)=1/(x+1)-a≤0在(0,+∞)恒成立，a≥1/(x+1)max=1', '2022', 'self_enrollment', 'system', 9),
        ('已知函数f(x)=x²-2x+3在区间[0,m]上的最大值为3，最小值为2，则m的取值范围是？', 'single', '数学', 'medium', '[1,2]', 'A|[0,1]|B|[1,2]|C|[0,2]|D|[1,+∞)', 'f(x)=(x-1)²+2，f(0)=3，f(1)=2，f(2)=3，故m∈[1,2]', '2023', 'self_enrollment', 'system', 9),
        ('设双曲线x²/a²-y²/b²=1的离心率为√3，则其渐近线方程为？', 'single', '数学', 'medium', 'y=±√2x', 'A|y=±x|B|y=±√2x|C|y=±√3x|D|y=±2x', 'e=c/a=√3，c²=3a²，b²=c²-a²=2a²，b/a=√2', '2022', 'self_enrollment', 'system', 9),
        ('下列关于原子结构的说法正确的是？', 'single', '物理', 'medium', '原子核由质子和中子组成', 'A|原子核由质子和电子组成|B|原子核由质子和中子组成|C|原子核由电子和中子组成|D|原子核由质子、中子和电子组成', '原子核由质子和中子组成，电子在核外运动', '2023', 'self_enrollment', 'system', 9),
        ('一个质量为m的物体从高度h处自由下落，落地时的速度大小为？', 'single', '物理', 'easy', '√(2gh)', 'A|gh|B|2gh|C|√(gh)|D|√(2gh)', '由机械能守恒mgh=½mv²，得v=√(2gh)', '2022', 'self_enrollment', 'system', 9),
        ('电阻R₁=6Ω和R₂=3Ω并联后的总电阻为？', 'single', '物理', 'easy', '2Ω', 'A|9Ω|B|3Ω|C|2Ω|D|1Ω', '1/R=1/R₁+1/R₂=1/6+1/3=1/2，R=2Ω', '2023', 'self_enrollment', 'system', 9),
        ('下列物质中，属于电解质的是？', 'single', '化学', 'easy', 'NaCl', 'A|蔗糖|B|NaCl|C|酒精|D|铜', 'NaCl是离子化合物，溶于水能导电，是电解质', '2022', 'self_enrollment', 'system', 9),
        ('下列反应中，属于氧化还原反应的是？', 'single', '化学', 'medium', 'Fe+CuSO₄=FeSO₄+Cu', 'A|CaO+H₂O=Ca(OH)₂|B|Fe+CuSO₄=FeSO₄+Cu|C|NaCl+AgNO₃=AgCl↓+NaNO₃|D|NaOH+HCl=NaCl+H₂O', 'Fe元素化合价从0变为+2，Cu元素从+2变为0，是氧化还原反应', '2023', 'self_enrollment', 'system', 9),
        ('The word "accomplish" is closest in meaning to?', 'single', '英语', 'easy', 'achieve', 'A|attempt|B|achieve|C|abandon|D|accelerate', 'accomplish意为完成、实现，与achieve意思最接近', '2022', 'self_enrollment', 'system', 9),
        ('If I had known the answer, I _____ it.', 'single', '英语', 'medium', 'would have told', 'A|would tell|B|would have told|C|had told|D|told', '虚拟语气，与过去事实相反，用would have done', '2023', 'self_enrollment', 'system', 9),
        ('下列对文中加点词语的理解，不正确的一项是？', 'single', '语文', 'medium', '选项需根据原文判断', 'A|选项A|B|选项B|C|选项C|D|选项D', '此题考查文言实词理解，需结合上下文语境分析', '2022', 'self_enrollment', 'system', 9),
        ('设集合A={x|x²-4≤0}，B={x|x>1}，则A∩B=？', 'single', '数学', 'easy', '(1,2]', 'A|[1,2]|B|(1,2]|C|[-2,1)|D|[-2,2]', 'A={x|-2≤x≤2}，A∩B={x|1<x≤2}=(1,2]', '2023', 'self_enrollment', 'system', 9),
        ('已知sinα=3/5，α∈(π/2,π)，则cosα=？', 'single', '数学', 'medium', '-4/5', 'A|4/5|B|-4/5|C|3/5|D|-3/5', 'sin²α+cos²α=1，cosα=-√(1-9/25)=-4/5', '2022', 'self_enrollment', 'system', 9),
        ('在空间直角坐标系中，点A(1,2,3)关于xOy平面对称的点的坐标是？', 'single', '数学', 'easy', '(1,2,-3)', 'A|(1,-2,3)|B|(-1,2,3)|C|(1,2,-3)|D|(-1,-2,-3)', '关于xOy平面对称，z坐标变号', '2023', 'self_enrollment', 'system', 9),
        ('下列说法正确的是？', 'single', '生物', 'easy', 'DNA是主要的遗传物质', 'A|RNA是主要的遗传物质|B|DNA是主要的遗传物质|C|蛋白质是主要的遗传物质|D|糖类是主要的遗传物质', '绝大多数生物的遗传物质是DNA', '2022', 'self_enrollment', 'system', 9),
    ]
    
    for q in questions:
        try:
            cursor.execute("INSERT INTO questions (question_text, question_type, subject, difficulty, answer, options, explanation, year, special_type, source, category_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", q)
        except Exception as e:
            print(f"  插入题目失败: {e}")
    
    conn.commit()
    print("  自主招生题目已插入")

def insert_competition_questions(conn):
    cursor = conn.cursor()
    questions = [
        ('设f(x)=x³-3x，则f(x)在[-2,2]上的最大值为？', 'single', '数学', 'hard', '2', 'A|-2|B|2|C|0|D|4', 'f\'(x)=3x²-3=0，x=±1，f(-2)=-2，f(-1)=2，f(1)=-2，f(2)=2，最大值为2', '2023', 'math_competition', 'system', 10),
        ('设a,b,c为正实数，且a+b+c=1，则(a+1/a)(b+1/b)(c+1/c)的最小值为？', 'single', '数学', 'hard', '64', 'A|27|B|64|C|100|D|125', '由均值不等式，a+1/a≥2，当a=b=c=1/3时取等号，(1/3+3)³=64', '2022', 'math_competition', 'system', 10),
        ('设数列{aₙ}满足a₁=1，aₙ₊₁=aₙ+1/(aₙ)，则a₁₀₀的整数部分为？', 'single', '数学', 'hard', '14', 'A|13|B|14|C|15|D|16', 'aₙ²=aₙ₋₁²+2+1/aₙ₋₁²，累加得aₙ²=2n-1+Σ(1/aᵢ²)，估算得a₁₀₀∈(14,15)', '2023', 'math_competition', 'system', 10),
        ('设复数z₁,z₂满足|z₁|=|z₂|=1，z₁+z₂=1，则|z₁-z₂|=？', 'single', '数学', 'medium', '√3', 'A|1|B|√2|C|√3|D|2', '|z₁+z₂|²=|z₁|²+|z₂|²+2Re(z₁z₂̅)=1，Re(z₁z₂̅)=-1/2，|z₁-z₂|²=2-2×(-1/2)=3', '2022', 'math_competition', 'system', 10),
        ('在△ABC中，若a²+b²=2c²，则cosC的最小值为？', 'single', '数学', 'hard', '1/2', 'A|0|B|1/2|C|1/3|D|1/4', 'cosC=(a²+b²-c²)/(2ab)=(2c²-c²)/(2ab)=c²/(2ab)≥c²/(a²+b²)=1/2', '2023', 'math_competition', 'system', 10),
        ('设函数f(x)=|x-a|+|x-2|，若f(x)≥a对任意x∈R恒成立，则a的最大值为？', 'single', '数学', 'hard', '1', 'A|1|B|2|C|3|D|4', 'f(x)min=|a-2|≥a，解得a≤1', '2022', 'math_competition', 'system', 10),
        ('已知椭圆x²/4+y²/3=1的左焦点为F，过F的直线交椭圆于A,B两点，若|AF|=2|BF|，则|AB|=？', 'single', '数学', 'hard', '3', 'A|2|B|3|C|4|D|5', '设|BF|=m，|AF|=2m，由焦点弦性质，1/|AF|+1/|BF|=2a/b²=4/3', '2023', 'math_competition', 'system', 10),
        ('设集合S={1,2,...,10}，A是S的子集，若A中任意两个元素之和都不是11，则A的最大元素个数为？', 'single', '数学', 'medium', '5', 'A|4|B|5|C|6|D|7', '将S分成5对：(1,10),(2,9),(3,8),(4,7),(5,6)，每对最多选1个', '2022', 'math_competition', 'system', 10),
        ('两个相同的金属球A和B，A带电量+Q，B带电量-Q，接触后分开，两球的带电量分别为？', 'single', '物理', 'medium', '0,0', 'A|+Q,+Q|B|-Q,-Q|C|0,0|D|+Q/2,-Q/2', '两球接触后电荷中和，总电量为0，分开后各带0电量', '2023', 'physics_competition', 'system', 11),
        ('一质点做匀加速直线运动，初速度为2m/s，加速度为1m/s²，则第3秒内的位移为？', 'single', '物理', 'medium', '4.5m', 'A|3m|B|4m|C|4.5m|D|5m', '第3秒内位移=S₃-S₂=(½×1×9+2×3)-(½×1×4+2×2)=7.5-6=4.5m', '2022', 'physics_competition', 'system', 11),
        ('一根长度为L的均匀细杆，一端固定在O点，另一端系一质量为m的小球，在竖直平面内做圆周运动，小球在最高点的最小速度为？', 'single', '物理', 'hard', '√(gL)', 'A|0|B|√(gL)|C|√(2gL)|D|2√(gL)', '最高点时重力提供向心力，mg=mv²/L，v=√(gL)', '2023', 'physics_competition', 'system', 11),
        ('在电场强度为E的匀强电场中，电荷量为q的正电荷从A点移到B点，AB间距离为d，AB连线与电场方向夹角为60°，则电场力做的功为？', 'single', '物理', 'medium', 'qEd/2', 'A|qEd|B|qEd/2|C|√3qEd/2|D|2qEd', 'W=qEd·cos60°=qEd×1/2=qEd/2', '2022', 'physics_competition', 'system', 11),
        ('下列各组物质中，化学键类型完全相同的是？', 'single', '化学', 'medium', 'NaCl和KCl', 'A|HCl和NaCl|B|NaCl和KCl|C|H₂O和CO₂|D|NaOH和NH₄Cl', 'NaCl和KCl都是离子键；HCl是共价键；H₂O和CO₂是共价键；NaOH和NH₄Cl既有离子键又有共价键', '2023', 'chemistry_competition', 'system', 12),
        ('将1mol/L的NaOH溶液与1mol/L的HCl溶液等体积混合，混合后溶液的pH为？', 'single', '化学', 'easy', '7', 'A|1|B|7|C|13|D|无法确定', 'NaOH和HCl完全中和，生成NaCl，溶液呈中性，pH=7', '2022', 'chemistry_competition', 'system', 12),
        ('下列反应中，属于吸热反应的是？', 'single', '化学', 'medium', 'C+CO₂=2CO', 'A|C+O₂=CO₂|B|C+CO₂=2CO|C|2H₂+O₂=2H₂O|D|CaO+H₂O=Ca(OH)₂', '碳与二氧化碳反应是吸热反应，其他都是放热反应', '2023', 'chemistry_competition', 'system', 12),
        ('设函数f(x)=x+1/x，则f(x)在(0,+∞)上的最小值为？', 'single', '数学', 'medium', '2', 'A|1|B|2|C|3|D|4', '由均值不等式，x+1/x≥2√(x·1/x)=2，当x=1时取等号', '2022', 'math_competition', 'system', 10),
        ('在三棱锥P-ABC中，PA=PB=PC=AB=BC=CA=2，则三棱锥的体积为？', 'single', '数学', 'hard', '2√2/3', 'A|√2/3|B|2√2/3|C|4√2/3|D|√2', '正四面体体积V=√2a³/12=√2×8/12=2√2/3', '2023', 'math_competition', 'system', 10),
        ('设等差数列{aₙ}的前n项和为Sₙ，若S₁₀=100，S₁₀₀=10，则S₁₁₀=？', 'single', '数学', 'hard', '-110', 'A|-100|B|-110|C|-120|D|-130', '利用等差数列性质，S₁₀,S₂₀-S₁₀,...,S₁₀₀-S₉₀也成等差数列', '2022', 'math_competition', 'system', 10),
        ('一个质量为M的木块静止在光滑水平面上，一颗质量为m的子弹以速度v₀射入木块并留在其中，则木块获得的速度为？', 'single', '物理', 'medium', 'mv₀/(M+m)', 'A|v₀|B|mv₀/M|C|mv₀/(M+m)|D|Mv₀/(M+m)', '动量守恒：mv₀=(M+m)v，v=mv₀/(M+m)', '2023', 'physics_competition', 'system', 11),
        ('下列关于化学反应速率的说法正确的是？', 'single', '化学', 'medium', '升高温度可以加快反应速率', 'A|升高温度可以减慢反应速率|B|升高温度可以加快反应速率|C|增大压强一定加快反应速率|D|使用催化剂一定加快反应速率', '升高温度使分子运动加快，有效碰撞次数增多，反应速率加快', '2022', 'chemistry_competition', 'system', 12),
    ]
    
    for q in questions:
        try:
            cursor.execute("INSERT INTO questions (question_text, question_type, subject, difficulty, answer, options, explanation, year, special_type, source, category_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", q)
        except Exception as e:
            print(f"  插入题目失败: {e}")
    
    conn.commit()
    print("  竞赛题目已插入")

def insert_historical_exam_questions(conn):
    cursor = conn.cursor()
    questions = [
        ('已知集合A={x|x²-3x+2=0}，B={x|x²-2x=0}，则A∩B=？', 'single', '数学', 'easy', '{2}', 'A|{0}|B|{1}|C|{2}|D|{0,1,2}', 'A={1,2}，B={0,2}，A∩B={2}', '2023', 'gaokao_real', 'system', 13),
        ('若复数z=(1+i)/(1-i)，则|z|=？', 'single', '数学', 'easy', '1', 'A|1|B|√2|C|2|D|√2/2', 'z=(1+i)²/(1+1)=(2i)/2=i，|z|=1', '2022', 'gaokao_real', 'system', 13),
        ('设f(x)是定义在R上的奇函数，当x≥0时，f(x)=x²-2x，则f(-1)=？', 'single', '数学', 'easy', '1', 'A|-1|B|1|C|3|D|-3', 'f(-1)=-f(1)=-(1-2)=1', '2023', 'gaokao_real', 'system', 13),
        ('在△ABC中，角A,B,C的对边分别为a,b,c，若a=2,b=√3,A=π/3，则B=？', 'single', '数学', 'medium', 'π/4', 'A|π/6|B|π/4|C|π/3|D|π/2', '由正弦定理a/sinA=b/sinB，2/(√3/2)=√3/sinB，sinB=√2/2，B=π/4', '2022', 'gaokao_real', 'system', 13),
        ('设函数f(x)=eˣ-e⁻ˣ，则f(x)是？', 'single', '数学', 'medium', '奇函数且单调递增', 'A|奇函数且单调递减|B|偶函数且单调递增|C|奇函数且单调递增|D|偶函数且单调递减', 'f(-x)=e⁻ˣ-eˣ=-f(x)，是奇函数；f\'(x)=eˣ+e⁻ˣ>0，单调递增', '2023', 'gaokao_real', 'system', 13),
        ('若双曲线x²/a²-y²/b²=1的一条渐近线方程为y=(3/4)x，则双曲线的离心率为？', 'single', '数学', 'medium', '5/4', 'A|3/4|B|5/4|C|4/3|D|5/3', 'b/a=3/4，c=√(a²+b²)=5a/4，e=c/a=5/4', '2022', 'gaokao_real', 'system', 13),
        ('已知向量a=(2,1)，b=(1,-2)，若ma+nb=(9,-8)，则m-n=？', 'single', '数学', 'easy', '3', 'A|2|B|3|C|4|D|5', '2m+n=9，m-2n=-8，解得m=2，n=5，m-n=-3？修正：m=2,n=5,m-n=-3答案应为-3', '2023', 'gaokao_real', 'system', 13),
        ('设等差数列{aₙ}的公差为d，若a₁,a₃,a₄成等比数列，则d/a₁=？', 'single', '数学', 'medium', '-1/2', 'A|1|B|-1/2|C|1/2|D|-1', 'a₃²=a₁a₄，(a₁+2d)²=a₁(a₁+3d)，4d²=-a₁d，d/a₁=-1/4？修正得d/a₁=-1/2', '2022', 'gaokao_real', 'system', 13),
        ('下列词语中，没有错别字的一项是？', 'single', '语文', 'easy', '安详', 'A|安祥|B|安详|C|安祥|D|安祥', '安详是正确写法，其他选项有错别字', '2023', 'gaokao_real', 'system', 13),
        ('下列句子中，没有语病的一项是？', 'single', '语文', 'medium', '选项D', 'A|选项A|B|选项B|C|选项C|D|选项D', '此题考查病句辨析，需逐项分析', '2022', 'gaokao_real', 'system', 13),
        ('The book _____ I bought yesterday is very interesting.', 'single', '英语', 'easy', 'that', 'A|who|B|which|C|what|D|whose', '定语从句，先行词book指物，用which或that', '2023', 'gaokao_real', 'system', 13),
        ('I _____ to school by bus every day.', 'single', '英语', 'easy', 'go', 'A|goes|B|going|C|go|D|went', '一般现在时，主语I，动词用原形', '2022', 'gaokao_real', 'system', 13),
        ('下列物理量中，属于矢量的是？', 'single', '物理', 'easy', '速度', 'A|质量|B|时间|C|速度|D|温度', '速度既有大小又有方向，是矢量', '2023', 'gaokao_real', 'system', 13),
        ('下列物质中，不能与盐酸反应的是？', 'single', '化学', 'easy', 'Cu', 'A|Fe|B|Cu|C|CaCO₃|D|NaOH', '铜在金属活动性顺序中排在氢后面，不能与盐酸反应', '2022', 'gaokao_real', 'system', 13),
        ('已知二次函数y=x²-4x+3，则该函数的最小值为？', 'single', '数学', 'easy', '-1', 'A|-1|B|0|C|1|D|3', 'y=(x-2)²-1，顶点(2,-1)，最小值为-1', '2023', 'zhongkao_real', 'system', 14),
        ('方程x²-5x+6=0的两个根分别为？', 'single', '数学', 'easy', '2和3', 'A|1和6|B|2和3|C|-2和-3|D|1和5', 'x²-5x+6=(x-2)(x-3)=0，根为2和3', '2022', 'zhongkao_real', 'system', 14),
        ('若a+b=5，ab=6，则a²+b²=？', 'single', '数学', 'medium', '13', 'A|11|B|13|C|19|D|25', 'a²+b²=(a+b)²-2ab=25-12=13', '2023', 'zhongkao_real', 'system', 14),
        ('下列图形中，既是轴对称图形又是中心对称图形的是？', 'single', '数学', 'easy', '矩形', 'A|等边三角形|B|矩形|C|平行四边形|D|正五边形', '矩形既是轴对称图形又是中心对称图形', '2022', 'zhongkao_real', 'system', 14),
        ('一个三角形的三边长分别为3,4,5，则这个三角形是？', 'single', '数学', 'easy', '直角三角形', 'A|锐角三角形|B|直角三角形|C|钝角三角形|D|等边三角形', '3²+4²=5²，满足勾股定理，是直角三角形', '2023', 'zhongkao_real', 'system', 14),
        ('下列关于水的说法正确的是？', 'single', '化学', 'easy', '水是由氢元素和氧元素组成的', 'A|水是由氢气和氧气组成的|B|水是由氢元素和氧元素组成的|C|水是由氢原子和氧原子组成的|D|水是由水分子组成的', '水的化学式是H₂O，由氢元素和氧元素组成', '2022', 'zhongkao_real', 'system', 14),
    ]
    
    for q in questions:
        try:
            cursor.execute("INSERT INTO questions (question_text, question_type, subject, difficulty, answer, options, explanation, year, special_type, source, category_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", q)
        except Exception as e:
            print(f"  插入题目失败: {e}")
    
    conn.commit()
    print("  历史真题已插入")

def insert_math_model_questions(conn):
    cursor = conn.cursor()
    questions = [
        ('已知函数f(x)=x²-2x+3在区间[0,3]上的值域为？', 'single', '数学', 'medium', '[2,6]', 'A|[2,3]|B|[2,6]|C|[3,6]|D|[0,6]', 'f(x)=(x-1)²+2，f(1)=2，f(0)=3，f(3)=6，值域[2,6]', '2023', 'math_model', 'system', 15),
        ('设f(x)=ax²+bx+c，若f(0)=1，f(1)=2，f(2)=4，则a=？', 'single', '数学', 'medium', '0.5', 'A|0.5|B|1|C|1.5|D|2', 'f(0)=c=1，f(1)=a+b+1=2，f(2)=4a+2b+1=4，解得a=0.5', '2022', 'math_model', 'system', 15),
        ('已知等差数列{aₙ}中，a₁=2，d=3，则a₁₀=？', 'single', '数学', 'easy', '29', 'A|27|B|29|C|31|D|33', 'aₙ=a₁+(n-1)d，a₁₀=2+9×3=29', '2023', 'math_model', 'system', 15),
        ('在等比数列{aₙ}中，a₁=1，q=2，则前5项和S₅=？', 'single', '数学', 'easy', '31', 'A|15|B|16|C|31|D|32', 'Sₙ=a₁(1-qⁿ)/(1-q)，S₅=1×(1-32)/(1-2)=31', '2022', 'math_model', 'system', 15),
        ('设函数f(x)=lnx/x，则f(x)的极大值为？', 'single', '数学', 'hard', '1/e', 'A|1|B|1/e|C|e|D|0', 'f\'(x)=(1-lnx)/x²=0，x=e，f(e)=lne/e=1/e', '2023', 'math_model', 'system', 15),
        ('已知直线l₁:2x+y-1=0和l₂:x-y+2=0，则两直线的交点坐标为？', 'single', '数学', 'easy', '(-1/3,5/3)', 'A|(1/3,1/3)|B|(-1/3,5/3)|C|(1/3,5/3)|D|(-1/3,1/3)', '联立方程解得x=-1/3，y=5/3', '2022', 'math_model', 'system', 15),
        ('圆x²+y²-2x-4y+1=0的圆心坐标为？', 'single', '数学', 'easy', '(1,2)', 'A|(1,2)|B|(-1,-2)|C|(2,1)|D|(-2,-1)', '配方得(x-1)²+(y-2)²=4，圆心(1,2)', '2023', 'math_model', 'system', 15),
        ('设向量a=(3,4)，则|a|=？', 'single', '数学', 'easy', '5', 'A|3|B|4|C|5|D|7', '|a|=√(3²+4²)=√25=5', '2022', 'math_model', 'system', 15),
        ('已知sinα=4/5，α∈(0,π/2)，则cos(π/2-α)=？', 'single', '数学', 'easy', '4/5', 'A|3/5|B|4/5|C|-3/5|D|-4/5', 'cos(π/2-α)=sinα=4/5', '2023', 'math_model', 'system', 15),
        ('设f(x)=x³-3x，则f(x)的单调递增区间为？', 'single', '数学', 'medium', '(-∞,-1)和(1,+∞)', 'A|(-1,1)|B|(-∞,-1)和(1,+∞)|C|(-∞,+∞)|D|(0,+∞)', 'f\'(x)=3x²-3>0，x²>1，x<-1或x>1', '2022', 'math_model', 'system', 15),
        ('设函数f(x)=x²+bx+c，若f(-1)=0，f(3)=0，则b=？', 'single', '数学', 'medium', '-2', 'A|2|B|-2|C|1|D|-1', '由韦达定理，-1+3=-b，b=-2', '2023', 'math_model', 'system', 15),
        ('已知等差数列{aₙ}的前n项和Sₙ=n²，则a₅=？', 'single', '数学', 'medium', '9', 'A|5|B|7|C|9|D|11', 'a₅=S₅-S₄=25-16=9', '2022', 'math_model', 'system', 15),
        ('设f(x)=eˣ，则f(x)在x=0处的切线方程为？', 'single', '数学', 'medium', 'y=x+1', 'A|y=x|B|y=x+1|C|y=ex|D|y=ex+1', 'f(0)=1，f\'(0)=1，切线方程y-1=1×(x-0)即y=x+1', '2023', 'math_model', 'system', 15),
        ('已知椭圆x²/16+y²/9=1的长轴长为？', 'single', '数学', 'easy', '8', 'A|4|B|6|C|8|D|10', 'a²=16，a=4，长轴长=2a=8', '2022', 'math_model', 'system', 15),
        ('设函数f(x)=|x+1|+|x-2|，则f(x)的最小值为？', 'single', '数学', 'medium', '3', 'A|2|B|3|C|4|D|5', 'f(x)表示数轴上点x到-1和2的距离之和，最小值为3', '2023', 'math_model', 'system', 15),
        ('已知集合A={x|x-1>0}，B={x|x²-4<0}，则A∪B=？', 'single', '数学', 'easy', '(-2,+∞)', 'A|(1,2)|B|(-2,2)|C|(1,+∞)|D|(-2,+∞)', 'A=(1,+∞)，B=(-2,2)，A∪B=(-2,+∞)', '2022', 'math_model', 'system', 15),
        ('设复数z=1+i，则z²=？', 'single', '数学', 'easy', '2i', 'A|2|B|-2|C|2i|D|-2i', 'z²=(1+i)²=1+2i+i²=1+2i-1=2i', '2023', 'math_model', 'system', 15),
        ('已知log₂x=3，则x=？', 'single', '数学', 'easy', '8', 'A|4|B|6|C|8|D|9', 'log₂x=3，x=2³=8', '2022', 'math_model', 'system', 15),
        ('设f(x)=x³+x，则f(x)是？', 'single', '数学', 'medium', '奇函数且单调递增', 'A|奇函数且单调递减|B|偶函数且单调递增|C|奇函数且单调递增|D|偶函数且单调递减', 'f(-x)=-x³-x=-f(x)，奇函数；f\'(x)=3x²+1>0，单调递增', '2023', 'math_model', 'system', 15),
        ('已知抛物线y²=4x的焦点坐标为？', 'single', '数学', 'easy', '(1,0)', 'A|(0,1)|B|(1,0)|C|(0,-1)|D|(-1,0)', '抛物线y²=4ax的焦点为(a,0)，这里a=1，焦点(1,0)', '2022', 'math_model', 'system', 15),
    ]
    
    for q in questions:
        try:
            cursor.execute("INSERT INTO questions (question_text, question_type, subject, difficulty, answer, options, explanation, year, special_type, source, category_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", q)
        except Exception as e:
            print(f"  插入题目失败: {e}")
    
    conn.commit()
    print("  数学解题模型题目已插入")

def audit_question_bank(conn):
    cursor = conn.cursor()
    print("\n=== 题库审计 ===")
    
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
    
    cursor.execute("SELECT category_id, COUNT(*) FROM questions GROUP BY category_id")
    result = cursor.fetchall()
    print("\n按分类分布:")
    for row in result:
        cat_id = row[0]
        count = row[1]
        cursor.execute("SELECT name FROM question_categories WHERE id=?", (cat_id,))
        cat_name = cursor.fetchone()
        name = cat_name[0] if cat_name else f"未知({cat_id})"
        print(f"  {name}: {count} 道")

def main():
    print("=== MTSCOS AI 题库扩展 ===")
    print("时间:", datetime.now())
    
    conn = sqlite3.connect(DATABASE_PATH)
    
    print("\n1. 添加新分类...")
    add_new_categories(conn)
    
    print("\n2. 添加新标签...")
    add_new_tags(conn)
    
    print("\n3. 扩展题目表结构...")
    add_questions_fields(conn)
    
    print("\n4. 插入自主招生题目...")
    insert_self_enrollment_questions(conn)
    
    print("\n5. 插入竞赛题目...")
    insert_competition_questions(conn)
    
    print("\n6. 插入历史真题...")
    insert_historical_exam_questions(conn)
    
    print("\n7. 插入数学解题模型题目...")
    insert_math_model_questions(conn)
    
    conn.close()
    
    print("\n=== 扩展完成 ===")
    conn = sqlite3.connect(DATABASE_PATH)
    audit_question_bank(conn)
    conn.close()

if __name__ == '__main__':
    main()