import os
import sys
import random
import sqlite3
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

MATH_MODELS = [
    '将军饮马', '胡不归问题', '拉窗帘模型', '费马点', '瓜豆原理', '阿氏圆', '隐圆模型',
    '中点模型', '相似三角形', '勾股定理', '极值点偏移', '隐零点问题', '放缩法',
    '和差倍问题', '鸡兔同笼', '盈亏问题', '植树问题', '年龄问题', '二次函数', '二次函数最值'
]

QUESTION_TYPES = ['single_choice', 'multiple_choice', 'fill_blank', 'short_answer']

DIFFICULTIES = ['easy', 'medium', 'hard']

def generate_math_model_question(model_name, difficulty):
    if difficulty == 'easy':
        template = random.randint(1, 6)
    elif difficulty == 'medium':
        template = random.randint(1, 10)
    else:
        template = random.randint(1, 15)
    
    if model_name == '将军饮马':
        if template <= 4:
            a, b = random.randint(2, 8), random.randint(2, 8)
            dist = random.randint(3, 15)
            return f"直线l同侧有A、B两点，A到l距离{a}，B到l距离{b}，A、B投影距离{dist}，将军饮马最短路径是", f"{(a+b)*2}"
        elif template <= 8:
            a, b = random.randint(3, 10), random.randint(3, 10)
            return f"河岸同侧两村庄A、B，A距河{a}km，B距河{b}km，水平距离{a+b}km，最短路径长", str((a+b)*2)
        else:
            return f"将军饮马问题的核心思想是什么？", "作对称点转化为两点间线段"
    
    elif model_name == '胡不归问题':
        if template <= 4:
            a, b, k = random.randint(3, 10), random.randint(2, 6), round(random.randint(1, 9)/10, 1)
            return f"A到直线l距离{a}，B在l上距投影{b}，速度比k={k}，最短时间路径", f"沿直线到l再到B"
        elif template <= 8:
            a, b, k = random.randint(5, 15), random.randint(3, 8), round(random.randint(3, 7)/10, 1)
            return f"沙漠边缘A距公路{a}km，B在公路上{b}km远，沙漠与公路速度比{k}，最短时间", "构造三角函数转化"
        else:
            return f"胡不归问题中，为什么可以用三角函数转化路径？", "利用sin值等于速度比"
    
    elif model_name == '拉窗帘模型':
        if template <= 4:
            a, b, c = random.randint(2, 6), random.randint(2, 6), random.randint(4, 12)
            return f"矩形ABCD中AB={c}, BC={a+b}，E在BC上BE={a}，求AE+DE最小值", str(c + a + b)
        elif template <= 8:
            a, b = random.randint(4, 12), random.randint(3, 8)
            return f"矩形ABCD中AB={a}, AD={b}，E在BC上，AE+DE最小值", str(a + b)
        else:
            return f"拉窗帘模型的本质是什么？", "利用对称转化为两点间距离"
    
    elif model_name == '费马点':
        if template <= 4:
            a = random.randint(3, 10)
            return f"等边三角形ABC边长{a}，费马点到三顶点距离之和", str(a)
        elif template <= 8:
            a, b, c = random.randint(4, 12), random.randint(4, 12), random.randint(4, 12)
            return f"△ABC中AB={a},BC={b},CA={c}，费马点到三顶点距离和最小值", f"{a+b+c}"
        else:
            return f"费马点的定义是什么？", "到三角形三顶点距离之和最小的点"
    
    elif model_name == '瓜豆原理':
        if template <= 4:
            r = random.randint(1, 5)
            return f"A绕O旋转，P满足OP={r}OA，P的轨迹是", f"半径{r}OA的圆"
        elif template <= 8:
            a, b = random.randint(1, 6), random.randint(1, 6)
            return f"定点O，A在圆上运动，OP={a}OA且∠AOP={b*30}°，P的轨迹", "缩放旋转后的圆"
        else:
            return f"瓜豆原理中，主动点和从动点的关系是什么？", "相似变换关系"
    
    elif model_name == '阿氏圆':
        if template <= 4:
            a, b, r = random.randint(2, 8), random.randint(1, 4), random.randint(3, 10)
            return f"阿氏圆半径{r}，内分点距{a}，外分点距{b}，比值k=", str(round(a/b, 2))
        elif template <= 8:
            a, b, k = random.randint(3, 10), random.randint(1, 5), round(random.randint(1, 9)/10, 1)
            return f"两点距离{a+b}，内分点距近点{a}，阿氏圆半径", f"{a*b*k/(1-k**2)}"
        else:
            return f"阿氏圆定理是什么？", "到两定点距离之比为常数的点的轨迹"
    
    elif model_name == '隐圆模型':
        if template <= 4:
            a = random.randint(2, 10)
            return f"点P满足PA={a},PB={a}，P的轨迹是", "以AB中点为圆心的圆"
        elif template <= 8:
            a, b = random.randint(3, 10), random.randint(3, 10)
            return f"点P满足∠APB=90°，AB={a+b}，P的轨迹是", "以AB为直径的圆"
        else:
            return f"隐圆模型常见的构造方法有哪些？", "定角对定边、到定点定距等"
    
    elif model_name == '中点模型':
        if template <= 4:
            a, b = random.randint(3, 10), random.randint(3, 10)
            return f"△ABC中D、E是AB、AC中点，DE与BC的关系", "DE平行且等于BC的一半"
        elif template <= 8:
            return f"四边形各边中点连线构成什么图形？", "平行四边形"
        else:
            return f"中点模型的核心辅助线是什么？", "连接中点构造中位线"
    
    elif model_name == '相似三角形':
        if template <= 4:
            a, b = random.randint(1, 10), random.randint(1, 10)
            return f"相似三角形对应边比{a}:{b}，面积比为", f"{a*a}:{b*b}"
        elif template <= 8:
            a, b, c = random.randint(2, 8), random.randint(2, 8), random.randint(2, 8)
            return f"△ABC∽△DEF，AB={a},DE={b},BC={c}，EF=", str(round(b*c/a, 1))
        else:
            return f"相似三角形的判定定理有哪些？", "AA、SAS、SSS"
    
    elif model_name == '勾股定理':
        if template <= 4:
            a, b = random.randint(3, 10), random.randint(4, 10)
            c = int((a*a + b*b)**0.5)
            ans = str(c) if c*c == a*a + b*b else f"√({a*a + b*b})"
            return f"直角三角形两直角边{a}和{b}，斜边为", ans
        elif template <= 8:
            a, b = random.randint(5, 15), random.randint(5, 15)
            return f"直角三角形直角边{a}cm和{b}cm，斜边", f"√({a*a + b*b})cm"
        else:
            return f"勾股定理的逆定理是什么？", "若三边满足a²+b²=c²则为直角三角形"
    
    elif model_name == '极值点偏移':
        if template <= 4:
            a = random.randint(1, 5)
            return f"函数f(x)={a}x - lnx的极值点为", f"x=1/{a}"
        elif template <= 8:
            a, b = random.randint(1, 5), random.randint(1, 5)
            return f"函数f(x)={a}x**2 - {b}lnx的极值点为", f"x=√({b}/{2*a})"
        else:
            return f"极值点偏移问题常用的解决方法是什么？", "构造对称函数、对数平均不等式"
    
    elif model_name == '隐零点问题':
        if template <= 4:
            return f"证明f(x)=x - e^(-x)存在零点", "零点存在定理"
        elif template <= 8:
            a = random.randint(1, 5)
            return f"函数f(x)={a}x - lnx存在隐零点，证明范围", "构造辅助函数"
        else:
            return f"隐零点问题的核心思想是什么？", "设而不求，整体代换"
    
    elif model_name == '放缩法':
        if template <= 4:
            return f"证明1/n**2 < 1/(n(n-1)) (n≥2)", "裂项放缩"
        elif template <= 8:
            return f"证明1+1/2+1/3+...+1/n > ln(n+1)", "积分放缩"
        else:
            return f"放缩法在不等式证明中有哪些常用技巧？", "裂项、积分、均值不等式"
    
    elif model_name == '和差倍问题':
        if template <= 4:
            a, b = random.randint(10, 50), random.randint(2, 5)
            return f"甲数比乙数多{a}，甲数是乙数{b}倍，乙数=", str(a/(b-1))
        elif template <= 8:
            a, b = random.randint(20, 100), random.randint(2, 5)
            return f"两数之和{a}，大数是小数{b}倍，两数分别为", f"小数{a/(b+1)},大数{a*b/(b+1)}"
        else:
            return f"和差倍问题的基本公式是什么？", "和=(大数+小数),差=(大数-小数)"
    
    elif model_name == '鸡兔同笼':
        if template <= 4:
            a, b = random.randint(10, 50), random.randint(20, 150)
            return f"鸡兔共{a}头{b}脚，鸡兔各几只", f"鸡{(4*a-b)/2},兔{(b-2*a)/2}"
        elif template <= 8:
            a, b = random.randint(20, 100), random.randint(50, 300)
            return f"鸡兔共{a}只{b}腿，各有几只", f"鸡{(4*a-b)/2},兔{(b-2*a)/2}"
        else:
            return f"鸡兔同笼问题常用的解法有哪些？", "假设法、方程法、抬腿法"
    
    elif model_name == '盈亏问题':
        if template <= 4:
            a, b, c = random.randint(3, 10), random.randint(5, 20), random.randint(2, 5)
            return f"每人分{a}多{b}，每人分{a+c}少{c}，人数=", str((b+c)/c)
        elif template <= 8:
            a, b, c, d = random.randint(5, 15), random.randint(10, 40), random.randint(2, 5), random.randint(5, 20)
            return f"每人分{a}盈{b}，每人分{a+c}亏{d}，物品总数", str(a*(b+d)/c + b)
        else:
            return f"盈亏问题的基本公式是什么？", "人数=(盈+亏)/两次分配差"
    
    elif model_name == '植树问题':
        if template <= 4:
            a = random.randint(10, 100)
            return f"马路长{a}米，每隔{a//10}米植树，两端都种，需几棵", str(a//(a//10) + 1)
        elif template <= 8:
            a, b = random.randint(20, 200), random.randint(5, 20)
            return f"圆形池塘周长{a}米，每隔{b}米栽树，需几棵", str(a//b)
        else:
            return f"植树问题中，两端都种和两端都不种的公式区别？", "都种=间隔数+1,都不种=间隔数-1"
    
    elif model_name == '年龄问题':
        if template <= 4:
            b = random.randint(5, 15)
            multiple = random.randint(2, 5)
            a = b * multiple + random.randint(10, 20)
            return f"爸爸{a}岁，儿子{b}岁，几年后爸爸是儿子{multiple}倍", str((a - b*multiple)/(multiple - 1))
        elif template <= 8:
            b = random.randint(5, 15)
            c = random.randint(2, 5)
            multiple = c * 4
            a = b * multiple + random.randint(10, 20)
            return f"妈妈{a}岁，女儿{b}岁，几年前妈妈是女儿{multiple}倍", str((a - b*multiple)/(multiple - 1))
        else:
            return f"年龄问题的核心特点是什么？", "年龄差始终不变"
    
    elif model_name == '二次函数':
        if template <= 4:
            a, b, c = random.randint(1, 5), random.randint(-10, 10), random.randint(-10, 10)
            return f"二次函数y={a}x**2+{b}x+{c}开口方向", "向上" if a > 0 else "向下"
        elif template <= 8:
            a, b, c = random.randint(1, 5), random.randint(-10, 10), random.randint(-10, 10)
            return f"二次函数y={a}x**2+{b}x+{c}与x轴交点个数", f"判别式Δ={b*b-4*a*c}"
        else:
            return f"二次函数的三种形式是什么？", "一般式、顶点式、交点式"
    
    elif model_name == '二次函数最值':
        if template <= 4:
            a, b = random.randint(1, 5), random.randint(-10, 10)
            return f"二次函数y={a}x**2+{b}最小值", str(b)
        elif template <= 8:
            a, b, c = random.randint(1, 5), random.randint(-10, 10), random.randint(-10, 10)
            return f"二次函数y={a}x**2+{b}x+{c}顶点纵坐标", f"{(4*a*c - b*b)/(4*a)}"
        else:
            return f"求二次函数最值的方法有哪些？", "配方法、公式法、导数法"
    
    else:
        a, b, c = random.randint(1, 10), random.randint(-10, 10), random.randint(1, 10)
        return f"解方程{a}x**2+{b}x+{c}=0（求根公式）", f"x=[-{b}±√({b}**2-4*{a}*{c})]/(2*{a})"

def generate_question(model_name, q_type, difficulty):
    question_text, correct_answer = generate_math_model_question(model_name, difficulty)
    
    options = []
    if q_type == 'single_choice':
        options = [correct_answer]
        while len(options) < 4:
            fake = str(random.randint(1, 100))
            if fake != correct_answer and fake not in options:
                options.append(fake)
        random.shuffle(options)
    elif q_type == 'multiple_choice':
        options = [correct_answer]
        while len(options) < 6:
            fake = str(random.randint(1, 100))
            if fake != correct_answer and fake not in options:
                options.append(fake)
        random.shuffle(options)
    elif q_type == 'fill_blank':
        options = []
    elif q_type == 'short_answer':
        options = []
    
    return {
        'question_id': str(uuid.uuid4())[:16],
        'question_text': question_text,
        'options': json.dumps(options) if options else '',
        'correct_answer': correct_answer,
        'subject': '数学',
        'topic': model_name,
        'question_type': q_type,
        'difficulty': difficulty,
        'explanation': f"{model_name}专项训练题"
    }

import json

def batch_generate_questions(model_name, count, thread_id):
    questions = []
    for i in range(count):
        q_type = random.choice(QUESTION_TYPES)
        difficulty = random.choice(DIFFICULTIES)
        question = generate_question(model_name, q_type, difficulty)
        questions.append(question)
        if (i + 1) % 500 == 0:
            print(f"  Thread {thread_id}: Generated {i+1}/{count} questions for {model_name}")
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

def generate_math_model_questions(target_per_model=5000):
    print("=" * 60)
    print("MTSCOS 数学解题模型专项训练题生成")
    print("=" * 60)
    print(f"目标: 每个解题模型生成 {target_per_model} 道题目")
    print(f"涉及模型: {', '.join(MATH_MODELS)}")
    
    total_added = 0
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        for model_name in MATH_MODELS:
            print(f"\n=== 开始生成 {model_name} 专项训练题 ===")
            
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM knowledge_base_questions WHERE subject = ? AND topic = ?', 
                          ('数学', model_name))
            current_count = cursor.fetchone()[0]
            print(f"当前 {model_name} 题目数量: {current_count}")
            
            needed_count = max(0, target_per_model - current_count)
            print(f"需要新增题目数量: {needed_count}")
            
            if needed_count <= 0:
                print(f"{model_name} 已达到目标数量！")
                continue
            
            batch_size = 1000
            batches = (needed_count + batch_size - 1) // batch_size
            total_saved = 0
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for batch_num in range(batches):
                    actual_size = min(batch_size, needed_count - batch_num * batch_size)
                    futures.append(executor.submit(batch_generate_questions, model_name, actual_size, batch_num))
                
                for future in as_completed(futures):
                    questions = future.result()
                    saved = save_questions_batch(questions, conn)
                    total_saved += saved
            
            print(f"成功生成 {model_name} 题目: {total_saved} 道")
            total_added += total_saved
    
    print(f"\n=== 全部完成 ===")
    print(f"总计新增数学解题模型专项训练题: {total_added} 道")

if __name__ == '__main__':
    generate_math_model_questions()
