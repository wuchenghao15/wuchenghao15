#!/usr/bin/env python3
"""
更新题库数据库，添加考试等级体系
日语N1-N5、英语九年制/四六级/专四专八、其他学科九年制

import os
import sys
import sqlite3
# JSON import removed - using database
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def update_question_bank():
    """更新题库数据库"""
    db_path = "app.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查并添加新的列
        print("检查数据库结构...")

        # 获取现有列
        cursor.execute("PRAGMA table_info(questions)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        # 添加新列
        new_columns = {
            "exam_type": "TEXT",
            "exam_level": "TEXT",
            "difficulty_description": "TEXT"
        }

        for column, data_type in new_columns.items():
            if column not in existing_columns:
                try:
                    print(f"添加列: {column}")
                except Exception as e:
                    print(f"添加列 {column} 失败: {e}")

        # 更新题库内容
        print("\n更新题库内容...")

        # 日语题目 - N5-N1
        japanese_questions = [
            # N5级别
            ("日语", "词汇", "N5", "JLPT", "请选择'あ'的平假名", "multiple_choice", 1, "あ", "い,う,え,お", "あ是日语五十音图的第一个假名"),
            ("日语", "语法", "N5", "JLPT", "'です'的意思是", "multiple_choice", 1, "是", "不是,有,做", "です是日语的断定助动词，表示'是'"),
            # N4级别
            ("日语", "语法", "N4", "JLPT", "动词'食べる'的て形是", "multiple_choice", 2, "食べて", "食べり,食べるて,食べった", "食べる是二类动词，て形为食べて"),
            # N3级别
            ("日语", "阅读", "N3", "JLPT", "请阅读短文并回答问题", "reading", 3, "根据文章内容", "", "需要理解文章主旨和细节"),
            # N2级别
            ("日语", "语法", "N2", "JLPT", "〜わけにはいかない的意思是", "multiple_choice", 5, "不能...", "必须...,应该...,可以...", "表示由于某种原因不能做某事"),
            # N1级别
            ("日语", "语法", "N1", "JLPT", "〜ともすれば的用法是", "multiple_choice", 8, "动不动就...", "总是...,偶尔...,一定...", "表示某种倾向或状态容易出现"),
        ]

        # 英语题目 - 九年制/四六级/专四专八
        english_questions = [
            # 九年制基础
            ("英语", "词汇", "九年制基础", "九年义务教育", "'Apple'的中文意思是", "multiple_choice", 1, "苹果", "香蕉,橙子,葡萄", "apple是苹果的意思"),
            ("英语", "语法", "九年制基础", "九年义务教育", "'I ___ a student.' 空格处应填", "multiple_choice", 1, "am", "is,are,be", "I后面用am"),
            # 九年制进阶
            ("英语", "语法", "九年制进阶", "九年义务教育", "现在完成时的结构是", "multiple_choice", 3, "have/has + 过去分词", "will + 动词原形,be + 动词ing,动词过去式", "现在完成时表示过去发生的动作对现在的影响"),
            # 四级
            ("英语", "阅读", "四级", "CET", "阅读理解：根据文章内容选择正确答案", "reading", 4, "根据文章内容", "", "四级阅读要求理解文章主旨和细节"),
            ("英语", "词汇", "四级", "CET", "'Abundant'的意思是", "multiple_choice", 4, "丰富的", "缺乏的,普通的,稀少的", "abundant表示大量的、丰富的"),
            # 六级
            ("英语", "词汇", "六级", "CET", "'Meticulous'的意思是", "multiple_choice", 5, "一丝不苟的", "粗心的,快速的,简单的", "meticulous表示非常仔细、注重细节"),
            ("英语", "写作", "六级", "CET", "请就'人工智能对未来工作的影响'写一篇议论文", "essay", 6, "", "", "六级写作要求逻辑清晰、论证充分"),
            # 专四
            ("英语", "语法", "专四", "TEM", "虚拟语气中，与现在事实相反的条件句结构是", "multiple_choice", 6, "If + 过去式, would + 动词原形", "If + 现在式, will + 动词原形,If + had + 过去分词, would have + 过去分词,If + should + 动词原形, would + 动词原形", "与现在事实相反的虚拟语气用过去式"),
            # 专八
            ("英语", "翻译", "专八", "TEM", "请将以下段落翻译成英文：'在全球化的今天，文化交流日益频繁...'", "translation", 8, "", "", "专八翻译要求准确、流畅、符合英语表达习惯"),
            ("英语", "文学", "专八", "TEM", "分析莎士比亚《哈姆雷特》中'To be or not to be'的深层含义", "essay", 9, "", "", "需要结合时代背景和人物心理进行分析"),
        ]

        math_questions = [
            # 九年制基础
            ("数学", "算术", "九年制基础", "九年义务教育", "2 + 3 × 4 = ?", "multiple_choice", 1, "14", "20,24,10", "先乘除后加减：3×4=12，2+12=14"),
            ("数学", "几何", "九年制基础", "九年义务教育", "三角形的内角和是", "multiple_choice", 2, "180度", "90度,360度,270度", "三角形内角和为180度"),
            ("数学", "代数", "九年制进阶", "九年义务教育", "解方程：2x + 5 = 13", "fill_blank", 3, "x = 4", "", "移项得2x=8，x=4"),
            # 高中
            ("数学", "函数", "高中数学", "高考", "函数f(x) = x²的导数是", "multiple_choice", 5, "2x", "x,2,x²", "根据求导公式，x^n的导数为nx^(n-1)"),
            # 大学
            ("数学", "微积分", "高等数学", "大学", "求极限：lim(x→0) sin(x)/x", "fill_blank", 7, "1", "", "重要极限之一"),
            ("数学", "线性代数", "高等数学", "大学", "矩阵A可逆的充要条件是", "multiple_choice", 8, "det(A) ≠ 0", "A ≠ 0,A^T = A,A² = I", "矩阵可逆当且仅当其行列式不为零"),
        ]

        physics_questions = [
            # 九年制
            ("物理", "力学", "九年制基础", "九年义务教育", "力的单位是", "multiple_choice", 2, "牛顿(N)", "千克(kg),米(m),秒(s)", "力的国际单位是牛顿"),
            ("物理", "电学", "九年制进阶", "九年义务教育", "欧姆定律的公式是", "multiple_choice", 3, "I = U/R", "U = IR,R = UI,P = UI", "电流等于电压除以电阻"),
            # 高中
            ("物理", "力学", "高中物理", "高考", "牛顿第二定律的表达式是", "multiple_choice", 4, "F = ma", "F = mv,F = m/v,F = ma²", "力等于质量乘以加速度"),
            # 大学
            ("物理", "电磁学", "大学物理", "大学", "麦克斯韦方程组包含几个方程", "multiple_choice", 8, "4个", "2个,3个,5个", "麦克斯韦方程组包含4个基本方程"),
        ]

            # 九年制
            ("化学", "基础", "九年制基础", "九年义务教育", "水的化学式是", "multiple_choice", 1, "H₂O", "CO₂,O₂,H₂", "水由氢和氧组成"),
            # 高中
            ("化学", "有机", "高中化学", "高考", "甲烷的分子式是", "multiple_choice", 4, "CH₄", "C₂H₆,C₃H₈,C₄H₁₀", "甲烷是最简单的烃"),
        ]

        biology_questions = [
            # 九年制
            ("生物", "遗传", "高中生物", "高考", "DNA的双螺旋结构是由谁发现的", "multiple_choice", 5, "沃森和克里克", "达尔文,孟德尔,摩尔根", "1953年沃森和克里克发现DNA双螺旋结构"),
        ]

        history_questions = [
            # 九年制
            ("历史", "中国史", "九年制基础", "九年义务教育", "中国历史上第一个统一的多民族封建国家是", "multiple_choice", 2, "秦朝", "汉朝,唐朝,明朝", "秦始皇统一六国建立秦朝"),
            # 高中
        ]
        geography_questions = [
            # 九年制
            ("地理", "自然", "九年制基础", "九年义务教育", "地球的自转周期是", "multiple_choice", 2, "24小时", "365天,30天,12小时", "地球自转一周约24小时"),
            # 高中
            ("地理", "人文", "高中地理", "高考", "影响人口迁移的主要因素是", "multiple_choice", 5, "经济因素", "自然因素,政治因素,文化因素", "经济因素是影响人口迁移的最主要因素"),

        computer_questions = [
            ("计算机", "基础", "九年制基础", "九年义务教育", "计算机的存储器中，断电后数据会丢失的是", "multiple_choice", 3, "RAM", "硬盘,ROM,光盘", "RAM是随机存取存储器，断电数据丢失"),
            # 高中
            ("计算机", "编程", "高中信息技术", "高考", "Python中，print()函数的作用是", "multiple_choice", 4, "输出内容到屏幕", "从键盘输入,计算数学公式,绘制图形", "print()用于输出"),
            # 大学
        ]

        all_questions = (japanese_questions + english_questions + math_questions +
                        history_questions + geography_questions + computer_questions)

        # 插入题目到数据库
        for q in all_questions:
            subject, topic, level, exam_type, question, q_type, difficulty, answer, options, explanation = q

            # 获取或创建分类ID
            category_row = cursor.fetchone()
            if category_row:
            else:
                cursor.execute("INSERT INTO question_categories (name, description) VALUES (?, ?)",
                             (topic, f"{subject}-{topic}"))
                category_id = cursor.lastrowid

            # 获取或创建难度级别ID
            cursor.execute("SELECT id FROM question_difficulties WHERE difficulty_level = ?", (f"Level {difficulty}",))
            diff_row = cursor.fetchone()
            if diff_row:
                difficulty_id = diff_row[0]
            else:
                cursor.execute("INSERT INTO question_difficulties (difficulty_level, description) VALUES (?, ?)",
                             (f"Level {difficulty}", f"难度等级 {difficulty}"))
                difficulty_id = cursor.lastrowid

            # 获取或创建语言ID
            cursor.execute("SELECT id FROM question_languages WHERE name = ?", (subject,))
            lang_row = cursor.fetchone()
            if lang_row:
                language_id = lang_row[0]
            else:
                cursor.execute("INSERT INTO question_languages (name, code) VALUES (?, ?)",
                             (subject, subject.lower()))
                language_id = cursor.lastrowid

            # 获取或创建题库ID
            cursor.execute("SELECT id FROM question_banks WHERE name = ?", (f"{subject}题库",))
            bank_row = cursor.fetchone()
            if bank_row:
                bank_id = bank_row[0]
            else:
                cursor.execute("INSERT INTO question_banks (name, description, language_id) VALUES (?, ?, ?)",
                             (f"{subject}题库", f"{subject}考试题库", language_id))
                bank_id = cursor.lastrowid

            try:
                    INSERT OR IGNORE INTO questions
                    (content, answer, explanation, category_id, language_id, level_id,
                     question_type, options, exam_type, exam_level, difficulty_description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (question, answer, explanation, category_id, language_id, difficulty_id,
                      q_type, f'["{options}"]' if options else '[]', exam_type, level, f"难度{difficulty}"))

                if cursor.rowcount > 0:
            except Exception as e:
                print(f"插入题目失败: {e}")

        print(f"\n成功插入 {inserted_count} 道新题目")

        # 统计各等级题目数量
        print("\n各考试等级题目统计：")
        cursor.execute("""
            SELECT exam_type, exam_level, COUNT(*) as count
            WHERE exam_type IS NOT NULL
            GROUP BY exam_type, exam_level
            ORDER BY exam_type, exam_level
        """)

        for row in cursor.fetchall():
            print(f"  {row[0]} - {row[1]}: {row[2]} 题")

        conn.close()
        print("\n题库更新完成！")
        return True

    except Exception as e:
        print(f"更新题库失败: {str(e)}")
        import traceback
        return False

if __name__ == "__main__":
    update_question_bank()
停止预谋
