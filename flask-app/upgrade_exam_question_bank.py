#!/usr/bin/env python3
"""
升级考试题库脚本
利用AI的升级能力和学习能力，升级考试题库，添加适配中国现有教育版本的题型试题
"""

import os
import sys
import json
import random
import time
import uuid
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_brain_library import AIBrainLibrary
from expand_question_bank import QuestionGenerator

class ExamQuestionBankUpgrader:
    """考试题库升级器"""
    
    def __init__(self):
        self.brain_library = AIBrainLibrary()
        self.question_generator = QuestionGenerator()
        self.upgrade_history = []
        
        # 中国教育版本相关配置
        self.chinese_education_config = {
            "primary": {
                "subjects": ["chinese", "math", "english"],
                "grades": ["grade_1", "grade_2", "grade_3", "grade_4", "grade_5", "grade_6"],
                "question_types": ["single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer"],
                "difficulty_distribution": {"easy": 0.6, "medium": 0.3, "hard": 0.1}
            },
            "junior": {
                "subjects": ["chinese", "math", "english", "physics", "chemistry", "biology", "history", "geography", "politics"],
                "grades": ["grade_7", "grade_8", "grade_9"],
                "question_types": ["single_choice", "multiple_choice", "fill_blank", "short_answer", "essay"],
                "difficulty_distribution": {"easy": 0.4, "medium": 0.4, "hard": 0.2}
            },
            "senior": {
                "subjects": ["chinese", "math", "english", "physics", "chemistry", "biology", "history", "geography", "politics"],
                "grades": ["grade_10", "grade_11", "grade_12"],
                "question_types": ["single_choice", "multiple_choice", "fill_blank", "short_answer", "essay", "computational"],
                "difficulty_distribution": {"easy": 0.3, "medium": 0.5, "hard": 0.2}
            }
        }
    
    def generate_chinese_education_questions(self, education_level, subject, count=10):
        """生成适配中国教育版本的题目"""
        """生成适配中国教育版本的题目"""
        config = self.chinese_education_config.get(education_level, self.chinese_education_config["primary"])
        
        if subject not in config["subjects"]:
            subject = config["subjects"][0]  # 默认使用第一个科目
        
        generated_questions = []
        
        # 根据难度分布生成不同难度的题目
        for difficulty, proportion in config["difficulty_distribution"].items():
            difficulty_count = int(count * proportion)
            if difficulty_count == 0:
                difficulty_count = 1
            
            for i in range(difficulty_count):
                # 随机选择题型
                question_type = random.choice(config["question_types"])
                
                # 生成题目
                question = self._generate_chinese_education_question(education_level, subject, difficulty, question_type)
                generated_questions.append(question)
        
        # 如果生成的题目数量不足，补充生成
        while len(generated_questions) < count:
            difficulty = random.choice(list(config["difficulty_distribution"].keys()))
            question_type = random.choice(config["question_types"])
            question = self._generate_chinese_education_question(education_level, subject, difficulty, question_type)
            generated_questions.append(question)
        
        return generated_questions[:count]
    
    def _generate_chinese_education_question(self, education_level, subject, difficulty, question_type):
        """生成单个适配中国教育版本的题目"""
        """生成单个适配中国教育版本的题目"""
        # 根据不同科目生成不同类型的题目
        if subject == "chinese":
            return self._generate_chinese_language_question(education_level, difficulty, question_type)
        elif subject == "math":
            return self._generate_math_question(education_level, difficulty, question_type)
        elif subject == "english":
            return self._generate_english_question(education_level, difficulty, question_type)
        elif subject in ["physics", "chemistry", "biology"]:
            return self._generate_science_question(subject, education_level, difficulty, question_type)
        elif subject in ["history", "geography", "politics"]:
            return self._generate_social_science_question(subject, education_level, difficulty, question_type)
        else:
            return self._generate_generic_question(subject, education_level, difficulty, question_type)
    
    def _generate_chinese_language_question(self, education_level, difficulty, question_type):
        """生成语文题目"""
        """生成语文题目"""
        # 小学语文题目模板
        primary_templates = {
            "single_choice": {
                "easy": [
                    ("下列词语中，加点字的读音正确的一项是？", "A. 学校(xiào) B. 美丽(měi) C. 快乐(yuè) D. 中国(zhōng)", "A", "学校的正确读音是xiào，美丽的正确读音是měi，快乐的正确读音是lè，中国的正确读音是zhōng。")
                ],
                "medium": [
                    ("下列词语中，书写正确的一项是？", "A. 兴高彩烈 B. 专心致志 C. 自做自受 D. 名列前矛", "B", "兴高采烈的正确写法是兴高采烈，专心致志的正确写法是专心致志，自作自受的正确写法是自作自受，名列前茅的正确写法是名列前茅。")
                ],
                "hard": [
                    ("下列句子中，标点符号使用正确的一项是？", 'A. 他说，"今天天气真好！" B. 我喜欢吃苹果、香蕉、葡萄等水果。 C. 你知道他是谁吗。 D. 这本书的作者是：鲁迅。', "B", "A选项引号使用错误，C选项应该使用问号，D选项冒号使用错误。")
                ]
            },
            "fill_blank": {
                "easy": [
                    ("_______是中国的首都。", [], "北京", "北京是中国的首都。")
                ],
                "medium": [
                    ("床前明月光，疑是地上霜。举头望_______，低头思故乡。", [], "明月", "这是李白《静夜思》中的诗句。")
                ],
                "hard": [
                    ("《论语》是记录_______及其弟子言行的一部书。", [], "孔子", "《论语》是儒家经典之一，记录了孔子及其弟子的言行。")
                ]
            }
        }
        
        # 初中语文题目模板
        junior_templates = {
            "single_choice": {
                "easy": [
                    ("下列词语中，加点字的读音完全正确的一项是？", "A. 称职(chèn) B. 狭隘(yì) C. 粗犷(kuàng) D. 狡黠(xié)", "A", "称职的正确读音是chèn，狭隘的正确读音是ài，粗犷的正确读音是guǎng，狡黠的正确读音是xiá。")
                ],
                "medium": [
                    ("下列句子中，没有语病的一项是？", "A. 通过这次活动，使我明白了许多道理。 B. 我们要认真克服并随时发现自己的缺点。 C. 能否刻苦学习是取得好成绩的关键。 D. 他的写作水平有了很大的提高。", "D", "A选项缺少主语，B选项语序错误，C选项两面对一面。")
                ],
                "hard": [
                    ("下列句子中，修辞手法与其他三项不同的一项是？", "A. 树上的苹果像灯笼似的又大又红。 B. 小溪唱着欢快的歌流向远方。 C. 弯弯的月亮像一条小船挂在夜空中。 D. 大象的耳朵像两把大大的蒲扇。", "B", "B选项是拟人，其他三项是比喻。")
                ]
            },
            "essay": {
                "easy": [
                    ("请以《我的老师》为题，写一篇不少于500字的作文。", [], "", "请围绕老师的外貌、性格、教学方法等方面进行描写，表达对老师的感激之情。")
                ],
                "medium": [
                    ("请以《成长的烦恼》为题，写一篇不少于600字的作文。", [], "", "请结合自己的经历，谈谈成长过程中遇到的烦恼及解决方法。")
                ],
                "hard": [
                    ("请以《品味生活》为题，写一篇不少于700字的作文。", [], "", "请结合生活中的具体事例，谈谈对生活的理解和感悟。")
                ]
            }
        }
        
        # 高中语文题目模板
        senior_templates = {
            "single_choice": {
                "easy": [
                    ("下列词语中，加点字的读音正确的一项是？", "A. 拘泥(nì) B. 包扎(zhā) C. 下载(zǎi) D. 剽窃(piáo)", "A", "包扎的正确读音是zā，下载的正确读音是zài，剽窃的正确读音是piāo。")
                ],
                "medium": [
                    ("下列句子中，加点成语使用正确的一项是？", "A. 这部小说情节跌宕起伏，抑扬顿挫，具有很强的感染力。 B. 他在演讲中夸夸其谈，赢得了观众的阵阵掌声。 C. 王老师对学生总是吹毛求疵，严格要求。 D. 我们要因地制宜，发展适合本地特色的产业。", "D", "A选项抑扬顿挫形容声音，B选项夸夸其谈是贬义词，C选项吹毛求疵是贬义词。")
                ],
                "hard": [
                    ("下列文学常识表述有误的一项是？", "A. 《诗经》是我国第一部诗歌总集，分为风、雅、颂三部分。 B. 李白是唐代伟大的浪漫主义诗人，被称为'诗仙'。 C. 鲁迅的《朝花夕拾》是一部小说集。 D. 《红楼梦》的作者是曹雪芹。", "C", "《朝花夕拾》是散文集，不是小说集。")
                ]
            },
            "essay": {
                "easy": [
                    ("请以《梦想与现实》为题，写一篇不少于800字的议论文。", [], "", "请结合实际，谈谈梦想与现实的关系。")
                ],
                "medium": [
                    ("请以《责任》为题，写一篇不少于800字的议论文。", [], "", "请结合自己的理解，谈谈对责任的认识和体会。")
                ],
                "hard": [
                    ("请以《科技与人文》为题，写一篇不少于800字的议论文。", [], "", "请结合社会现实，谈谈科技发展与人文关怀的关系。")
                ]
            }
        }
        
        # 根据教育水平选择模板
        if education_level == "primary":
            templates = primary_templates
        elif education_level == "junior":
            templates = junior_templates
        else:  # senior
            templates = senior_templates
        
        # 选择题型模板
        question_type_templates = templates.get(question_type, templates.get("single_choice", {}))
        difficulty_templates = question_type_templates.get(difficulty, question_type_templates.get("easy", []))
        
        # 随机选择一个模板
        template = random.choice(difficulty_templates) if difficulty_templates else ("请填写题目内容", [], "", "")
        
        return {
            "question_id": f"chinese_edu_{uuid.uuid4().hex[:12]}",
            "question_content": template[0],
            "options": template[1].split(" ") if template[1] else [],
            "correct_answer": template[2],
            "explanation": template[3],
            "subject": "chinese",
            "education_level": education_level,
            "difficulty": difficulty,
            "question_type": question_type,
            "created_at": datetime.now().isoformat()
        }
    
    def _generate_math_question(self, education_level, difficulty, question_type):
        """生成数学题目"""
        """生成数学题目"""
        # 小学数学题目模板
        primary_templates = {
            "single_choice": {
                "easy": [
                    ("5 + 3 = ?", "A. 7 B. 8 C. 9 D. 10", "B", "5加3等于8。")
                ],
                "medium": [
                    ("一个长方形的长是5厘米，宽是3厘米，它的面积是多少平方厘米？", "A. 15 B. 16 C. 17 D. 18", "A", "长方形面积=长×宽=5×3=15平方厘米。")
                ],
                "hard": [
                    ("小明有12个苹果，吃了3个，又买了5个，现在小明有多少个苹果？", "A. 13 B. 14 C. 15 D. 16", "B", "12-3+5=14个。")
                ]
            },
            "computational": {
                "easy": [
                    ("计算：25 + 13 = ?", [], "38", "25加13等于38。")
                ],
                "medium": [
                    ("计算：56 ÷ 8 = ?", [], "7", "56除以8等于7。")
                ],
                "hard": [
                    ("计算：12 × 4 + 8 = ?", [], "56", "12×4=48，48+8=56。")
                ]
            }
        }
        
        # 初中数学题目模板
        junior_templates = {
            "single_choice": {
                "easy": [
                    ("下列数中，属于有理数的是？", "A. √2 B. π C. 0.5 D. e", "C", "0.5是有限小数，属于有理数。")
                ],
                "medium": [
                    ("解方程：2x + 3 = 9", [], "3", "2x=6，x=3。")
                ],
                "hard": [
                    ("一个三角形的两边长分别是3和4，第三边长为x，那么x的取值范围是？", "A. 1 < x < 7 B. 1 ≤ x ≤ 7 C. x > 1 D. x < 7", "A", "三角形两边之和大于第三边，两边之差小于第三边，所以4-3 < x < 4+3，即1 < x < 7。")
                ]
            },
            "computational": {
                "easy": [
                    ("计算：(-2)² × 3 = ?", [], "12", "(-2)²=4，4×3=12。")
                ],
                "medium": [
                    ("计算：(x + 2)(x - 3) = ?", [], "x² - x - 6", "使用多项式乘法法则展开：x×x + x×(-3) + 2×x + 2×(-3) = x² - 3x + 2x - 6 = x² - x - 6。")
                ],
                "hard": [
                    ("计算：√12 + √27 = ?", [], "5√3", "√12=2√3，√27=3√3，所以2√3+3√3=5√3。")
                ]
            }
        }
        
        # 高中数学题目模板
        senior_templates = {
            "single_choice": {
                "easy": [
                    ("函数f(x) = x² + 2x + 1的对称轴是？", "A. x = -1 B. x = 1 C. x = 0 D. x = 2", "A", "二次函数f(x) = ax² + bx + c的对称轴是x = -b/(2a)，所以这里x = -2/(2×1) = -1。")
                ],
                "medium": [
                    ("计算：sin(π/6) = ?", "A. 0 B. 1/2 C. √2/2 D. √3/2", "B", "sin(π/6)等于1/2。")
                ],
                "hard": [
                    ("数列1, 3, 5, 7, 9, ...的第10项是？", "A. 17 B. 18 C. 19 D. 20", "C", "这是一个等差数列，首项a1=1，公差d=2，所以第n项an=a1+(n-1)d=1+2(n-1)=2n-1，第10项a10=2×10-1=19。")
                ]
            },
            "computational": {
                "easy": [
                    ("计算：∫(x²)dx = ?", [], "(1/3)x³ + C", "x²的不定积分是(1/3)x³ + C。")
                ],
                "medium": [
                    ("求函数f(x) = x³ - 3x的极值。", [], "极大值为2，极小值为-2", "f'(x)=3x²-3，令f'(x)=0，得x=±1。f''(x)=6x，f''(1)=6>0，所以x=1时取得极小值f(1)=1-3=-2；f''(-1)=-6<0，所以x=-1时取得极大值f(-1)=-1+3=2。")
                ],
                "hard": [
                    ("计算：∫(0到π) sin(x)dx = ?", [], "2", "sin(x)在0到π的定积分等于-cos(x)从0到π，即-cos(π) - (-cos(0)) = -(-1) - (-1) = 1 + 1 = 2。")
                ]
            }
        }
        
        # 根据教育水平选择模板
        if education_level == "primary":
            templates = primary_templates
        elif education_level == "junior":
            templates = junior_templates
        else:  # senior
            templates = senior_templates
        
        # 选择题型模板
        question_type_templates = templates.get(question_type, templates.get("single_choice", {}))
        difficulty_templates = question_type_templates.get(difficulty, question_type_templates.get("easy", []))
        
        # 随机选择一个模板
        template = random.choice(difficulty_templates) if difficulty_templates else ("请填写题目内容", [], "", "")
        
        return {
            "question_id": f"math_edu_{uuid.uuid4().hex[:12]}",
            "question_content": template[0],
            "options": template[1].split(" ") if template[1] else [],
            "correct_answer": template[2],
            "explanation": template[3],
            "subject": "math",
            "education_level": education_level,
            "difficulty": difficulty,
            "question_type": question_type,
            "created_at": datetime.now().isoformat()
        }
    
    def _generate_english_question(self, education_level, difficulty, question_type):
        """生成英语题目"""
        """生成英语题目"""
        # 小学英语题目模板
        primary_templates = {
            "single_choice": {
                "easy": [
                    ("What's this?", "A. It's a book. B. I'm fine. C. Thank you. D. Goodbye.", "A", "What's this?的回答是It's a...")
                ],
                "medium": [
                    ("I _____ a student.", "A. am B. is C. are D. be", "A", "I后面用am。")
                ],
                "hard": [
                    ("Where is the cat?", "A. It's under the chair. B. It's red. C. It's a cat. D. It's mine.", "A", "Where询问地点，所以回答应该是位置。")
                ]
            },
            "fill_blank": {
                "easy": [
                    ("I like ______ (read) books.", [], "reading", "like后面接动词ing形式。")
                ],
                "medium": [
                    ("She ______ (go) to school every day.", [], "goes", "一般现在时，第三人称单数动词加s。")
                ],
                "hard": [
                    ("They ______ (play) football yesterday.", [], "played", "yesterday表示过去，动词用过去式。")
                ]
            }
        }
        
        # 初中英语题目模板
        junior_templates = {
            "single_choice": {
                "easy": [
                    ("Which is the capital of China?", "A. Beijing B. Shanghai C. Guangzhou D. Shenzhen", "A", "北京是中国的首都。")
                ],
                "medium": [
                    ("I have two brothers. One is a teacher, ______ is a doctor.", "A. other B. another C. the other D. others", "C", "two...one...the other...表示两个中的一个...另一个...")
                ],
                "hard": [
                    ("If it ______ tomorrow, we won't go to the park.", "A. rain B. rains C. rained D. will rain", "B", "if引导的条件状语从句，主句用将来时，从句用一般现在时。")
                ]
            },
            "fill_blank": {
                "easy": [
                    ("He is interested ______ music.", [], "in", "be interested in表示对...感兴趣。")
                ],
                "medium": [
                    ("The book was written ______ Lu Xun.", [], "by", "被动语态用by引出动作执行者。")
                ],
                "hard": [
                    ("I ______ (not see) him for three years.", [], "haven't seen", "for+一段时间，用现在完成时。")
                ]
            }
        }
        
        # 高中英语题目模板
        senior_templates = {
            "single_choice": {
                "easy": [
                    ("The news ______ very exciting.", "A. is B. are C. be D. am", "A", "news是不可数名词，动词用单数。")
                ],
                "medium": [
                    ("______ by the teacher, he made great progress.", "A. Teaching B. Taught C. Teach D. To teach", "B", "过去分词作状语，表示被动。")
                ],
                "hard": [
                    ("Only when he returned ______ the truth.", "A. he knew B. he knows C. did he know D. does he know", "C", "only+状语位于句首，句子要用部分倒装。")
                ]
            },
            "fill_blank": {
                "easy": [
                    ("I suggested ______ (go) to the park.", [], "going", "suggest后面接动词ing形式。")
                ],
                "medium": [
                    ("The meeting ______ (hold) next week.", [], "will be held", "next week表示将来，会议被举行，用将来被动语态。")
                ],
                "hard": [
                    ("It is high time that we ______ (take) action to protect the environment.", [], "took", "It is high time that...后面接虚拟语气，用过去式。")
                ]
            }
        }
        
        # 根据教育水平选择模板
        if education_level == "primary":
            templates = primary_templates
        elif education_level == "junior":
            templates = junior_templates
        else:  # senior
            templates = senior_templates
        
        # 选择题型模板
        question_type_templates = templates.get(question_type, templates.get("single_choice", {}))
        difficulty_templates = question_type_templates.get(difficulty, question_type_templates.get("easy", []))
        
        # 随机选择一个模板
        template = random.choice(difficulty_templates) if difficulty_templates else ("请填写题目内容", [], "", "")
        
        return {
            "question_id": f"english_edu_{uuid.uuid4().hex[:12]}",
            "question_content": template[0],
            "options": template[1].split(" ") if template[1] else [],
            "correct_answer": template[2],
            "explanation": template[3],
            "subject": "english",
            "education_level": education_level,
            "difficulty": difficulty,
            "question_type": question_type,
            "created_at": datetime.now().isoformat()
        }
    
    def _generate_science_question(self, subject, education_level, difficulty, question_type):
        """生成理科题目"""
        """生成理科题目"""
        science_templates = {
            "physics": {
                "single_choice": {
                    "easy": [
                        ("下列哪个是力的单位？", "A. 米 B. 千克 C. 牛顿 D. 秒", "C", "力的单位是牛顿。")
                    ],
                    "medium": [
                        ("物体在光滑水平面上运动，不受力的作用，它将？", "A. 静止 B. 匀速直线运动 C. 加速运动 D. 减速运动", "B", "根据牛顿第一定律，不受力的物体将保持静止或匀速直线运动。")
                    ],
                    "hard": [
                        ("一个物体的质量是5kg，重力加速度是9.8m/s²，它的重力是多少？", "A. 49N B. 5N C. 9.8N D. 0.5N", "A", "重力G=mg=5×9.8=49N。")
                    ]
                }
            },
            "chemistry": {
                "single_choice": {
                    "easy": [
                        ("下列哪种物质是单质？", "A. 水 B. 氧气 C. 二氧化碳 D. 氯化钠", "B", "氧气是由一种元素组成的纯净物，是单质。")
                    ],
                    "medium": [
                        ("水的化学式是？", "A. H₂O B. CO₂ C. O₂ D. H₂", "A", "水的化学式是H₂O。")
                    ],
                    "hard": [
                        ("化学反应前后，下列哪项一定不变？", "A. 物质的种类 B. 分子的种类 C. 原子的种类 D. 分子的数目", "C", "化学反应前后原子的种类、数目、质量不变。")
                    ]
                }
            },
            "biology": {
                "single_choice": {
                    "easy": [
                        ("植物进行光合作用的场所是？", "A. 线粒体 B. 叶绿体 C. 细胞核 D. 细胞膜", "B", "光合作用的场所是叶绿体。")
                    ],
                    "medium": [
                        ("下列哪个是人体的呼吸系统器官？", "A. 心脏 B. 肺 C. 胃 D. 肾脏", "B", "肺是呼吸系统的主要器官。")
                    ],
                    "hard": [
                        ("下列哪种细胞没有细胞核？", "A. 红细胞 B. 白细胞 C. 神经细胞 D. 肌肉细胞", "A", "成熟的红细胞没有细胞核。")
                    ]
                }
            }
        }
        
        # 选择科目模板
        subject_templates = science_templates.get(subject, science_templates.get("physics", {}))
        question_type_templates = subject_templates.get(question_type, subject_templates.get("single_choice", {}))
        difficulty_templates = question_type_templates.get(difficulty, question_type_templates.get("easy", []))
        
        # 随机选择一个模板
        template = random.choice(difficulty_templates) if difficulty_templates else ("请填写题目内容", [], "", "")
        
        return {
            "question_id": f"{subject}_edu_{uuid.uuid4().hex[:12]}",
            "question_content": template[0],
            "options": template[1].split(" ") if template[1] else [],
            "correct_answer": template[2],
            "explanation": template[3],
            "subject": subject,
            "education_level": education_level,
            "difficulty": difficulty,
            "question_type": question_type,
            "created_at": datetime.now().isoformat()
        }
    
    def _generate_social_science_question(self, subject, education_level, difficulty, question_type):
        """生成文科题目"""
        """生成文科题目"""
        social_science_templates = {
            "history": {
                "single_choice": {
                    "easy": [
                        ("中国的第一个皇帝是？", "A. 秦始皇 B. 汉武帝 C. 唐太宗 D. 宋太祖", "A", "秦始皇是中国第一个皇帝。")
                    ],
                    "medium": [
                        ("辛亥革命发生在哪一年？", "A. 1840 B. 1911 C. 1949 D. 1978", "B", "辛亥革命发生在1911年。")
                    ],
                    "hard": [
                        ("下列哪项是唐朝的盛世？", "A. 文景之治 B. 贞观之治 C. 康乾盛世 D. 开元盛世", "B", "贞观之治是唐太宗时期的盛世，开元盛世是唐玄宗时期的盛世。")
                    ]
                }
            },
            "geography": {
                "single_choice": {
                    "easy": [
                        ("中国的首都是？", "A. 上海 B. 北京 C. 广州 D. 深圳", "B", "北京是中国的首都。")
                    ],
                    "medium": [
                        ("世界上最高的山峰是？", "A. 珠穆朗玛峰 B. 乔戈里峰 C. 干城章嘉峰 D. 洛子峰", "A", "珠穆朗玛峰是世界上最高的山峰。")
                    ],
                    "hard": [
                        ("下列哪个是季风气候的特点？", "A. 全年高温多雨 B. 夏季高温多雨，冬季寒冷干燥 C. 全年温和湿润 D. 冬季温和多雨，夏季炎热干燥", "B", "季风气候的特点是夏季高温多雨，冬季寒冷干燥。")
                    ]
                }
            },
            "politics": {
                "single_choice": {
                    "easy": [
                        ("中华人民共和国的成立日期是？", "A. 1911年10月1日 B. 1945年8月15日 C. 1949年10月1日 D. 1978年12月1日", "C", "中华人民共和国成立于1949年10月1日。")
                    ],
                    "medium": [
                        ("我国的根本政治制度是？", "A. 人民代表大会制度 B. 多党合作和政治协商制度 C. 民族区域自治制度 D. 基层群众自治制度", "A", "人民代表大会制度是我国的根本政治制度。")
                    ],
                    "hard": [
                        ("科学发展观的核心是？", "A. 发展 B. 以人为本 C. 全面协调可持续 D. 统筹兼顾", "B", "科学发展观的核心是以人为本。")
                    ]
                }
            }
        }
        
        # 选择科目模板
        subject_templates = social_science_templates.get(subject, social_science_templates.get("history", {}))
        question_type_templates = subject_templates.get(question_type, subject_templates.get("single_choice", {}))
        difficulty_templates = question_type_templates.get(difficulty, question_type_templates.get("easy", []))
        
        # 随机选择一个模板
        template = random.choice(difficulty_templates) if difficulty_templates else ("请填写题目内容", [], "", "")
        
        return {
            "question_id": f"{subject}_edu_{uuid.uuid4().hex[:12]}",
            "question_content": template[0],
            "options": template[1].split(" ") if template[1] else [],
            "correct_answer": template[2],
            "explanation": template[3],
            "subject": subject,
            "education_level": education_level,
            "difficulty": difficulty,
            "question_type": question_type,
            "created_at": datetime.now().isoformat()
        }
    
    def _generate_generic_question(self, subject, education_level, difficulty, question_type):
        """生成通用题目"""
        """生成通用题目"""
        return {
            "question_id": f"generic_edu_{uuid.uuid4().hex[:12]}",
            "question_content": f"请为{subject}科目生成题目",
            "options": [],
            "correct_answer": "",
            "explanation": f"这是一个{education_level}水平，{difficulty}难度的{question_type}类型题目。",
            "subject": subject,
            "education_level": education_level,
            "difficulty": difficulty,
            "question_type": question_type,
            "created_at": datetime.now().isoformat()
        }
    
    def upgrade_question_bank(self, target_count=100, education_levels=None, subjects=None):
        """升级考试题库"""
        """升级考试题库"""
        print("=" * 60)
        print("升级考试题库")
        print("=" * 60)
        
        # 默认为所有教育水平和科目
        if not education_levels:
            education_levels = list(self.chinese_education_config.keys())
        if not subjects:
            subjects = ["chinese", "math", "english"]
        
        total_generated = 0
        
        # 升级AI脑库
        print("\n1. 升级AI脑库")
        print("-" * 40)
        upgrade_result = self.brain_library.upgrade_all_libraries()
        print(f"AI脑库升级结果: {'成功' if upgrade_result['brain_map']['success'] else '失败'}")
        
        # 为每个教育水平和科目生成题目
        for education_level in education_levels:
            for subject in subjects:
                print(f"\n2. 为{education_level} {subject}生成题目")
                print("-" * 40)
                
                # 生成指定数量的题目
                questions_count = target_count // (len(education_levels) * len(subjects))
                questions_count = max(questions_count, 10)  # 至少生成10道题
                
                print(f"生成{questions_count}道{education_level} {subject}题目...")
                questions = self.generate_chinese_education_questions(education_level, subject, questions_count)
                
                # 将生成的题目添加到知识库
                print(f"将题目添加到知识库...")
                for question in questions:
                    # 转换为知识库条目格式
                    knowledge_item = {
                        "title": f"{education_level} {subject} {question['question_type']}题目",
                        "category": f"{subject}_education",
                        "content": json.dumps(question, ensure_ascii=False),
                        "difficulty": question["difficulty"],
                        "version": "1.0.0"
                    }
                    
                    # 添加到知识库
                    self.brain_library.add_to_library("knowledge", knowledge_item)
                    
                    # 同时尝试添加到数据库题库
                    try:
                        self._add_question_to_database(question)
                    except Exception as e:
                        print(f"添加到数据库失败: {e}")
                
                total_generated += len(questions)
                print(f"成功生成{len(questions)}道题目")
                
                # 学习生成的题目，优化AI脑库
                print("从生成的题目中学习...")
                self.brain_library.learn_from_data({
                    "type": "question_generation",
                    "data": {
                        "education_level": education_level,
                        "subject": subject,
                        "questions_count": len(questions),
                        "questions": questions
                    }
                }, "knowledge")
        
        # 记录升级历史
        upgrade_history = {
            "upgrade_id": f"upgrade_{uuid.uuid4().hex[:8]}",
            "target_count": target_count,
            "actual_count": total_generated,
            "education_levels": education_levels,
            "subjects": subjects,
            "timestamp": datetime.now().isoformat()
        }
        self.upgrade_history.append(upgrade_history)
        
        print(f"\n=" * 60)
        print(f"考试题库升级完成")
        print(f"目标生成题目数量: {target_count}")
        print(f"实际生成题目数量: {total_generated}")
        print(f"升级时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"升级ID: {upgrade_history['upgrade_id']}")
        print("=" * 60)
        
        return upgrade_history
    
    def _add_question_to_database(self, question):
        """将题目添加到数据库"""
        """将题目添加到数据库"""
        try:
            # 获取语言ID
            self.question_generator.cursor.execute("SELECT id FROM question_languages WHERE language_code = ?", ("chinese" if question["subject"] == "chinese" else "english",))
            language_result = self.question_generator.cursor.fetchone()
            if not language_result:
                return False
            language_id = language_result[0]
            
            # 获取等级ID
            level_code = f"{question['education_level']}_level"
            self.question_generator.cursor.execute("SELECT id FROM question_levels WHERE language_id = ? AND level_code = ?", (language_id, level_code))
            level_result = self.question_generator.cursor.fetchone()
            if not level_result:
                # 如果等级不存在，创建一个
                self.question_generator.cursor.execute("INSERT INTO question_levels (language_id, level_code, level_name) VALUES (?, ?, ?)", 
                                                     (language_id, level_code, f"{question['education_level']} Level"))
                level_id = self.question_generator.cursor.lastrowid
            else:
                level_id = level_result[0]
            
            # 获取章节ID
            section_map = {
                "chinese": 1, "math": 2, "english": 3, "physics": 4, "chemistry": 5,
                "biology": 6, "history": 7, "geography": 8, "politics": 9
            }
            section_id = section_map.get(question["subject"], 1)
            
            # 获取难度ID
            difficulty_map = {
                "easy": 1, "medium": 2, "hard": 3
            }
            difficulty_id = difficulty_map.get(question["difficulty"], 1)
            
            # 获取素材来源ID
            source_type = f"chinese_education"
            self.question_generator.cursor.execute("SELECT id FROM question_sources WHERE source_type = ?", (source_type,))
            source_result = self.question_generator.cursor.fetchone()
            if not source_result:
                # 如果素材来源不存在，创建一个
                self.question_generator.cursor.execute("INSERT INTO question_sources (source_type) VALUES (?)", (source_type,))
                source_id = self.question_generator.cursor.lastrowid
            else:
                source_id = source_result[0]
            
            # 获取题库ID
            question_bank_id = self.question_generator.get_question_bank(language_id)
            if not question_bank_id:
                return False
            
            # 添加题目到数据库
            success, question_id = self.question_generator.add_question(
                question_bank_id, level_id, section_id, difficulty_id, source_id,
                question["question_content"], question["correct_answer"], 
                question["explanation"], question["options"], question["question_type"]
            )
            
            return success
        except Exception as e:
            print(f"添加题目到数据库失败: {e}")
            return False
    
    def get_upgrade_history(self):
        """获取升级历史"""
        """获取升级历史"""
        return self.upgrade_history

# 测试代码
if __name__ == "__main__":
    upgrader = ExamQuestionBankUpgrader()
    
    # 升级题库，生成50道题
    upgrade_result = upgrader.upgrade_question_bank(
        target_count=50,
        education_levels=["primary", "junior"],
        subjects=["chinese", "math", "english"]
    )
    
    print("\n升级完成！")
    print(f"升级ID: {upgrade_result['upgrade_id']}")
    print(f"生成题目数量: {upgrade_result['actual_count']}")
