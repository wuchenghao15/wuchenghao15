#!/usr/bin/env python3
"""
考试测试专家AI模块
负责考试测试的设计、管理和评估
"""

import time
from app.ai.instances import ai_instance_manager
from app.utils.logging import logger

class ExamExpertAI:
    """考试测试专家AI类，负责考试测试的设计、管理和评估"""
    
    def __init__(self):
        self.instance_id = "exam-expert-ai-001"
        self.ai_type = "exam_expert"
        self.name = "考试测试专家AI"
        self.description = "负责考试测试的设计、管理和评估的AI专家"
        self.functions = [
            "试题生成",
            "考试设计",
            "考试管理",
            "成绩评估",
            "考试分析",
            "题库管理",
            "考试安全",
            "考试报告生成",
            "学习建议生成",
            "考试系统维护",
            "学科能力评级",
            "能力审核",
            "关西腔日语命题",
            "关东腔日语命题",
            "日语方言试题设计",
            "英国英语命题",
            "美国英语命题",
            "英语方言试题设计",
            "九年制义务教育教案",
            "九年制义务教育素材",
            "九年制义务教育命题"
        ]
        self.responsibilities = [
            "根据教学大纲生成试题",
            "设计合理的考试结构",
            "管理考试流程和规则",
            "评估学生考试成绩",
            "分析考试数据和趋势",
            "管理和扩充题库",
            "确保考试安全和公平",
            "生成详细的考试报告",
            "根据考试结果提供学习建议",
            "维护考试系统的正常运行",
            "对学生各学科能力进行评级",
            "审核学生能力评级结果",
            "设计关西腔日语试题",
            "设计关东腔日语试题",
            "设计日语方言相关试题",
            "设计英国英语试题",
            "设计美国英语试题",
            "设计英语方言相关试题",
            "生成九年制义务教育教案",
            "提供九年制义务教育素材",
            "设计九年制义务教育命题"
        ]
        self.config = {
            "version": 1.0,
            "question_generation": {
                "enabled": True,
                "auto_generation": True,
                "difficulty_levels": ["easy", "medium", "hard", "expert"],
                "question_types": ["multiple_choice", "short_answer", "essay", "practical"]
            },
            "exam_design": {
                "enabled": True,
                "auto_design": True,
                "time_management": True
            },
            "assessment": {
                "enabled": True,
                "auto_grading": True,
                "performance_analysis": True
            },
            "question_bank": {
                "enabled": True,
                "auto_expansion": True,
                "categorization": True
            },
            "security": {
                "enabled": True,
                "anti_cheating": True,
                "access_control": True
            },
            "ability_rating": {
                "enabled": True,
                "auto_rating": True,
                "rating_levels": ["beginner", "intermediate", "advanced", "expert"],
                "subjects": ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治", "日语"],
                "review_required": True
            },
            "japanese_dialects": {
                "enabled": True,
                "kansai_ben": {
                    "enabled": True,
                    "name": "关西腔",
                    "regions": ["大阪", "京都", "兵库", "奈良", "和歌山"],
                    "features": [
                        "词尾多用「や」「ねん」",
                        "尊敬语较简洁",
                        "语调起伏较大",
                        "元音发音独特",
                        "特有词汇丰富"
                    ]
                },
                "kanto_ben": {
                    "enabled": True,
                    "name": "关东腔",
                    "regions": ["东京", "神奈川", "千叶", "埼玉", "茨城"],
                    "features": [
                        "标准语基础",
                        "词尾多用「だ」「です」",
                        "尊敬语使用规范",
                        "语调相对平稳",
                        "商务用语发达"
                    ]
                },
                "question_types": [
                    "dialect_translation",
                    "dialect_identification",
                    "dialect_conversation",
                    "dialect_vocabulary",
                    "dialect_grammar"
                ]
            },
            "english_dialects": {
                "enabled": True,
                "british_english": {
                    "enabled": True,
                    "name": "British English",
                    "regions": ["UK", "England", "Scotland", "Wales", "Northern Ireland"],
                    "features": [
                        "使用colour而非color",
                        "使用centre而非center",
                        "使用travelled而非traveled",
                        "使用organisation而非organization",
                        "使用lift而非elevator",
                        "使用tap而非faucet",
                        "使用rubbish而非garbage",
                        "使用queue而非line",
                        "使用torch而非flashlight",
                        "使用petrol而非gasoline"
                    ]
                },
                "american_english": {
                    "enabled": True,
                    "name": "American English",
                    "regions": ["USA", "United States", "America"],
                    "features": [
                        "使用color而非colour",
                        "使用center而非centre",
                        "使用traveled而非travelled",
                        "使用organization而非organisation",
                        "使用elevator而非lift",
                        "使用faucet而非tap",
                        "使用garbage而非rubbish",
                        "使用line而非queue",
                        "使用flashlight而非torch",
                        "使用gasoline而非petrol"
                    ]
                },
                "question_types": [
                    "vocabulary_difference",
                    "spelling_identification",
                    "usage_comparison",
                    "translation_between",
                    "comprehension"
                ]
            },
            "nine_year_education": {
                "enabled": True,
                "grades": ["小学1-2年级", "小学3-4年级", "小学5-6年级", "初中1年级", "初中2年级", "初中3年级"],
                "subjects": ["语文", "数学", "英语", "科学", "道德与法治", "历史", "地理", "生物", "物理", "化学", "体育", "音乐", "美术", "信息技术"],
                "materials": {
                    "enabled": True,
                    "teaching_plans": True,
                    "courseware": True,
                    "worksheets": True,
                    "exams": True
                },
                "question_types": [
                    "multiple_choice",
                    "true_false",
                    "fill_in_blank",
                    "short_answer",
                    "essay",
                    "practical",
                    "calculation"
                ]
            }
        }
        self.japanese_dialect_knowledge = self._init_japanese_dialect_knowledge()
        self.english_dialect_knowledge = self._init_english_dialect_knowledge()
        self.nine_year_education_knowledge = self._init_nine_year_education_knowledge()
    
    def create_instance(self):
        """创建考试测试专家AI实例"""
        try:
            logger.info(f"开始创建考试测试专家AI实例: {self.instance_id}")
            
            # 创建AI实例
            ai_instance = ai_instance_manager.create_ai_instance(
                instance_id=self.instance_id,
                ai_type=self.ai_type,
                name=self.name,
                description=self.description,
                functions=self.functions,
                responsibilities=self.responsibilities,
                config=self.config
            )
            
            if ai_instance:
                logger.info(f"成功创建考试测试专家AI实例: {self.instance_id}")
                return ai_instance
            else:
                logger.error(f"创建考试测试专家AI实例失败: {self.instance_id}")
                return None
        except Exception as e:
            logger.error(f"创建考试测试专家AI实例时发生错误: {str(e)}")
            return None
    
    def get_instance(self):
        """获取考试测试专家AI实例"""
        try:
            return ai_instance_manager.get_ai_instance(self.instance_id)
        except Exception as e:
            logger.error(f"获取考试测试专家AI实例时发生错误: {str(e)}")
            return None
    
    def update_instance(self, updates):
        """更新考试测试专家AI实例"""
        try:
            return ai_instance_manager.update_ai_instance(self.instance_id, updates)
        except Exception as e:
            logger.error(f"更新考试测试专家AI实例时发生错误: {str(e)}")
            return False
    
    def delete_instance(self):
        """删除考试测试专家AI实例"""
        try:
            return ai_instance_manager.delete_ai_instance(self.instance_id)
        except Exception as e:
            logger.error(f"删除考试测试专家AI实例时发生错误: {str(e)}")
            return False
    
    def generate_questions(self, subject, difficulty, count):
        """生成试题"""
        try:
            logger.info(f"考试测试专家AI正在生成试题: {subject}, 难度: {difficulty}, 数量: {count}")
            # 这里可以添加具体的试题生成逻辑
            return {
                "status": "success",
                "message": f"试题生成完成: {subject}, 难度: {difficulty}, 数量: {count}",
                "questions": [f"{subject} 问题 {i+1} (难度: {difficulty})" for i in range(count)],
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"生成试题时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"生成试题时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def design_exam(self, exam_name, subject, duration, difficulty):
        """设计考试"""
        try:
            logger.info(f"考试测试专家AI正在设计考试: {exam_name}, 科目: {subject}, 时长: {duration}分钟, 难度: {difficulty}")
            # 这里可以添加具体的考试设计逻辑
            return {
                "status": "success",
                "message": f"考试 {exam_name} 设计完成",
                "exam_design": {
                    "name": exam_name,
                    "subject": subject,
                    "duration": f"{duration}分钟",
                    "difficulty": difficulty,
                    "sections": ["单选题", "多选题", "简答题", "论述题"]
                },
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"设计考试时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"设计考试时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def evaluate_exam(self, exam_id, student_id):
        """评估考试"""
        try:
            logger.info(f"考试测试专家AI正在评估考试: {exam_id}, 学生: {student_id}")
            # 这里可以添加具体的考试评估逻辑
            return {
                "status": "success",
                "message": f"考试 {exam_id} 评估完成",
                "evaluation": {
                    "exam_id": exam_id,
                    "student_id": student_id,
                    "score": 92,
                    "grade": "A",
                    "feedback": "表现优秀，继续保持",
                    "suggestions": ["加强知识点X的学习", "提高答题速度"]
                },
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"评估考试时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"评估考试时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def rate_subject_ability(self, student_id, subject, performance_data):
        """对学生特定学科能力进行评级"""
        try:
            logger.info(f"考试测试专家AI正在对学生 {student_id} 的 {subject} 学科能力进行评级")
            # 这里可以添加具体的能力评级逻辑
            # 根据performance_data计算能力等级
            rating_level = "intermediate"  # 示例评级
            
            return {
                "status": "success",
                "message": f"学生 {student_id} 的 {subject} 学科能力评级完成",
                "rating": {
                    "student_id": student_id,
                    "subject": subject,
                    "level": rating_level,
                    "score": 75,
                    "feedback": "表现良好，有提升空间",
                    "suggestions": ["加强基础知识学习", "多做练习"]
                },
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"对学生学科能力评级时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"对学生学科能力评级时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def rate_all_subjects(self, student_id, performance_data):
        """对学生所有学科能力进行评级"""
        try:
            logger.info(f"考试测试专家AI正在对学生 {student_id} 的所有学科能力进行评级")
            # 这里可以添加具体的全学科能力评级逻辑
            subjects = self.config["ability_rating"]["subjects"]
            ratings = {}
            
            for subject in subjects:
                # 为每个学科生成评级
                rating_level = "intermediate"  # 示例评级
                ratings[subject] = {
                    "level": rating_level,
                    "score": 75,
                    "feedback": "表现良好，有提升空间"
                }
            
            return {
                "status": "success",
                "message": f"学生 {student_id} 的所有学科能力评级完成",
                "ratings": ratings,
                "overall_level": "intermediate",
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"对学生全学科能力评级时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"对学生全学科能力评级时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def review_ability_rating(self, student_id, subject=None):
        """审核学生学科能力评级结果"""
        try:
            if subject:
                logger.info(f"考试测试专家AI正在审核学生 {student_id} 的 {subject} 学科能力评级")
            else:
                logger.info(f"考试测试专家AI正在审核学生 {student_id} 的所有学科能力评级")
            
            # 这里可以添加具体的审核逻辑
            review_result = "approved"  # 示例审核结果
            
            return {
                "status": "success",
                "message": f"学生 {student_id} 的{subject + ' ' if subject else ''}学科能力评级审核完成",
                "review": {
                    "student_id": student_id,
                    "subject": subject,
                    "result": review_result,
                    "comments": "评级结果合理，符合学生实际水平",
                    "reviewer": "考试测试专家AI"
                },
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"审核学生学科能力评级时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"审核学生学科能力评级时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def _init_japanese_dialect_knowledge(self):
        """初始化日语方言知识库"""
        return {
            "kansai_ben": {
                "vocabulary": [
                    {"kansai": "あかん", "standard": "だめ", "meaning": "不行"},
                    {"kansai": "おおきに", "standard": "ありがとう", "meaning": "谢谢"},
                    {"kansai": "ほんま", "standard": "ほんとう", "meaning": "真的"},
                    {"kansai": "なんでやねん", "standard": "なんでだよ", "meaning": "为什么啊"},
                    {"kansai": "ちゃう", "standard": "ちがう", "meaning": "不对"},
                    {"kansai": "めっちゃ", "standard": "すごく", "meaning": "非常"},
                    {"kansai": "わい", "standard": "わたし", "meaning": "我"},
                    {"kansai": "ご飯や", "standard": "ご飯だ", "meaning": "是饭"},
                    {"kansai": "知らんがな", "standard": "知らないよ", "meaning": "不知道啊"},
                    {"kansai": "ええじゃん", "standard": "いいじゃん", "meaning": "不是挺好的吗"}
                ],
                "grammar_examples": [
                    {"kansai": "明日、大阪へ行くやで", "standard": "明日、大阪へ行くんだよ", "meaning": "明天要去大阪哦"},
                    {"kansai": "この本、おもろいわ", "standard": "この本、おもしろいね", "meaning": "这本书很有趣啊"},
                    {"kansai": "早よせえや", "standard": "早くしてよ", "meaning": "快点啊"},
                    {"kansai": "雨降ってきたわ", "standard": "雨降ってきたね", "meaning": "下雨了啊"}
                ],
                "conversation_examples": [
                    {
                        "title": "购物对话",
                        "kansai": [
                            "客：これ、いくらでっか？",
                            "店員：これやったら500円やで。",
                            "客：ちょっと高いなあ。まけてくれへん？",
                            "店員：まけられへんわ。これでもうけてへんねん。"
                        ],
                        "standard": [
                            "客：これ、いくらですか？",
                            "店員：これでしたら500円ですよ。",
                            "客：ちょっと高いですね。安くしてくれませんか？",
                            "店員：安くできませんよ。これでもうけていないんです。"
                        ]
                    }
                ]
            },
            "kanto_ben": {
                "vocabulary": [
                    {"kanto": "ごめんください", "standard": "ごめんください", "meaning": "打扰了"},
                    {"kanto": "ですます調", "standard": "ですます調", "meaning": "礼貌体"},
                    {"kanto": "お願いします", "standard": "お願いします", "meaning": "拜托了"},
                    {"kanto": "承知いたしました", "standard": "承知いたしました", "meaning": "知道了"},
                    {"kanto": "恐縮です", "standard": "恐縮です", "meaning": "不好意思"},
                    {"kanto": "さようでございます", "standard": "そうです", "meaning": "是的"},
                    {"kanto": "よろしゅう", "standard": "よろしく", "meaning": "请多关照"},
                    {"kanto": "できたら", "standard": "できれば", "meaning": "如果可以的话"},
                    {"kanto": "おっしゃる", "standard": "言う", "meaning": "说（敬语）"},
                    {"kanto": "なさる", "standard": "する", "meaning": "做（敬语）"}
                ],
                "grammar_examples": [
                    {"kanto": "明日、東京へ参ります", "standard": "明日、東京へ行きます", "meaning": "明天要去东京"},
                    {"kanto": "このレポート、拝読しました", "standard": "このレポート、読みました", "meaning": "这份报告我读过了"},
                    {"kanto": "少々お待ちください", "standard": "少し待ってください", "meaning": "请稍等"},
                    {"kanto": "お手数ですが", "standard": "手数ですが", "meaning": "麻烦您了"}
                ],
                "conversation_examples": [
                    {
                        "title": "商务对话",
                        "kanto": [
                            "部長：今日の会議、資料は準備できましたか？",
                            "部下：はい、こちらにございます。ご確認ください。",
                            "部長：ありがとう。よくできていますね。",
                            "部下：恐縮です。まだ改善の余地がございます。"
                        ],
                        "standard": [
                            "部長：今日の会議、資料は準備できましたか？",
                            "部下：はい、こちらにあります。確認してください。",
                            "部長：ありがとう。よくできていますね。",
                            "部下：すみません。まだ改善の余地があります。"
                        ]
                    }
                ]
            },
            "comparison": [
                {
                    "category": "词尾",
                    "kansai": "「や」「ねん」",
                    "kanto": "「だ」「です」",
                    "example": "大阪や（关西）vs 東京だ（关东）"
                },
                {
                    "category": "否定形",
                    "kansai": "「へん」",
                    "kanto": "「ない」",
                    "example": "知らへん（关西）vs 知らない（关东）"
                },
                {
                    "category": "命令形",
                    "kansai": "「せえ」",
                    "kanto": "「しろ」「せよ」",
                    "example": "早よせえ（关西）vs 早くしろ（关东）"
                },
                {
                    "category": "语调",
                    "kansai": "起伏较大，末尾上升",
                    "kanto": "相对平稳，标准语调",
                    "example": "说话时关西腔更有节奏感"
                }
            ],
            "questions": {
                "vocabulary": [
                    {
                        "question": "「おおきに」は標準語で何ですか？",
                        "options": ["ありがとう", "さようなら", "すみません", "はい"],
                        "answer": "ありがとう",
                        "explanation": "「おおきに」是关西腔中表示感谢的说法，相当于标准语的「ありがとう」。"
                    },
                    {
                        "question": "「あかん」はどういう意味ですか？",
                        "options": ["いい", "だめ", "わかった", "知らない"],
                        "answer": "だめ",
                        "explanation": "「あかん」是关西腔中表示「不行、不可以」的意思，相当于标准语的「だめ」。"
                    }
                ],
                "grammar": [
                    {
                        "question": "「この本、おもろいわ」を標準語に訳してください。",
                        "options": [
                            "この本、おもしろいね",
                            "この本、つまらないね",
                            "この本、高いね",
                            "この本、安いね"
                        ],
                        "answer": "この本、おもしろいね",
                        "explanation": "「おもろい」是关西腔「おもしろい」的说法，「わ」是句尾语气词，相当于标准语的「ね」。"
                    }
                ],
                "translation": [
                    {
                        "question": "「ちょっとまけてくれへん？」を標準語に訳してください。",
                        "answer": "ちょっと安くしてくれませんか？",
                        "explanation": "「まけて」是关西腔「安くして」的意思，「へん」是否定助动词，相当于标准语的「ない」。"
                    }
                ],
                "identification": [
                    {
                        "question": "次のうち、関西弁の特徴はどれですか？",
                        "options": [
                            "語尾に「や」「ねん」を使う",
                            "語尾に「です」「ます」を使う",
                            "敬語をあまり使わない",
                            "語調が平坦である"
                        ],
                        "answer": "語尾に「や」「ねん」を使う",
                        "explanation": "关西腔的特征之一是词尾多用「や」「ねん」等，而关东腔（标准语）多用「だ」「です」。"
                    }
                ],
                "conversation": [
                    {
                        "question": "次の会話を読んで、質問に答えてください。\n\nA：これ、いくらでっか？\nB：これやったら800円やで。\nA：ちょっと高いなあ。\n\n質問：Aは何を言っていますか？",
                        "answer": "値段を聞いて、高いと思っています。",
                        "explanation": "A在询问价格（いくらでっか？），然后说有点贵（ちょっと高いなあ）。"
                    }
                ]
            }
        }
    
    def generate_kansai_ben_questions(self, question_type, count=5, difficulty="medium"):
        """生成关西腔日语试题"""
        try:
            logger.info(f"考试测试专家AI正在生成关西腔日语试题，类型: {question_type}, 数量: {count}")
            
            if not self.japanese_dialect_knowledge:
                return {
                    "status": "error",
                    "message": "日语方言知识库未初始化",
                    "timestamp": time.time()
                }
            
            kansai_data = self.japanese_dialect_knowledge.get("kansai_ben", {})
            questions_data = self.japanese_dialect_knowledge.get("questions", {})
            
            type_mapping = {
                "vocabulary": "vocabulary",
                "grammar": "grammar",
                "translation": "translation",
                "identification": "identification",
                "conversation": "conversation"
            }
            
            target_type = type_mapping.get(question_type, "vocabulary")
            target_questions = questions_data.get(target_type, [])
            
            # 生成试题
            generated_questions = []
            for i in range(min(count, len(target_questions))):
                question_data = target_questions[i].copy()
                question_data["difficulty"] = difficulty
                question_data["dialect_type"] = "kansai"
                generated_questions.append(question_data)
            
            return {
                "status": "success",
                "message": f"成功生成 {len(generated_questions)} 道关西腔日语试题",
                "questions": generated_questions,
                "dialect_type": "kansai",
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"生成关西腔日语试题时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"生成关西腔日语试题时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def generate_kanto_ben_questions(self, question_type, count=5, difficulty="medium"):
        """生成关东腔日语试题"""
        try:
            logger.info(f"考试测试专家AI正在生成关东腔日语试题，类型: {question_type}, 数量: {count}")
            
            if not self.japanese_dialect_knowledge:
                return {
                    "status": "error",
                    "message": "日语方言知识库未初始化",
                    "timestamp": time.time()
                }
            
            kanto_data = self.japanese_dialect_knowledge.get("kanto_ben", {})
            questions_data = self.japanese_dialect_knowledge.get("questions", {})
            
            # 为关东腔生成类似格式的试题
            # 这里基于标准语和敬语生成关东腔试题
            kanto_questions = [
                {
                    "question": "「承知いたしました」はどういう意味ですか？",
                    "options": ["わかりました", "知りません", "すみません", "ありがとう"],
                    "answer": "わかりました",
                    "explanation": "「承知いたしました」是关东腔/标准语中表示「知道了、了解了」的礼貌说法。",
                    "difficulty": difficulty,
                    "dialect_type": "kanto"
                },
                {
                    "question": "「お手数ですが」を標準語で説明してください。",
                    "answer": "ご迷惑をおかけしますが",
                    "explanation": "「お手数ですが」是关东腔/标准语中表示「麻烦您了、给您添麻烦了」的礼貌说法。",
                    "difficulty": difficulty,
                    "dialect_type": "kanto"
                }
            ]
            
            # 生成试题
            generated_questions = []
            for i in range(min(count, len(kanto_questions))):
                generated_questions.append(kanto_questions[i])
            
            return {
                "status": "success",
                "message": f"成功生成 {len(generated_questions)} 道关东腔日语试题",
                "questions": generated_questions,
                "dialect_type": "kanto",
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"生成关东腔日语试题时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"生成关东腔日语试题时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def generate_japanese_dialect_comparison_questions(self, count=5, difficulty="medium"):
        """生成日语方言对比试题"""
        try:
            logger.info(f"考试测试专家AI正在生成日语方言对比试题，数量: {count}")
            
            if not self.japanese_dialect_knowledge:
                return {
                    "status": "error",
                    "message": "日语方言知识库未初始化",
                    "timestamp": time.time()
                }
            
            comparison_data = self.japanese_dialect_knowledge.get("comparison", [])
            
            # 生成对比试题
            comparison_questions = []
            for i, item in enumerate(comparison_data[:count]):
                question = {
                    "question": f"関西弁と関東弁の「{item['category']}」の違いを説明してください。",
                    "kansai": item["kansai"],
                    "kanto": item["kanto"],
                    "example": item["example"],
                    "difficulty": difficulty,
                    "question_type": "comparison"
                }
                comparison_questions.append(question)
            
            return {
                "status": "success",
                "message": f"成功生成 {len(comparison_questions)} 道日语方言对比试题",
                "questions": comparison_questions,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"生成日语方言对比试题时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"生成日语方言对比试题时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def get_japanese_dialect_knowledge(self, dialect_type=None):
        """获取日语方言知识库"""
        try:
            logger.info(f"考试测试专家AI正在获取日语方言知识库，方言类型: {dialect_type}")
            
            if not self.japanese_dialect_knowledge:
                return {
                    "status": "error",
                    "message": "日语方言知识库未初始化",
                    "timestamp": time.time()
                }
            
            if dialect_type == "kansai":
                knowledge = self.japanese_dialect_knowledge.get("kansai_ben", {})
            elif dialect_type == "kanto":
                knowledge = self.japanese_dialect_knowledge.get("kanto_ben", {})
            else:
                knowledge = self.japanese_dialect_knowledge
            
            return {
                "status": "success",
                "message": f"成功获取{' ' + dialect_type if dialect_type else ''}日语方言知识库",
                "dialect_type": dialect_type,
                "knowledge": knowledge,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"获取日语方言知识库时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"获取日语方言知识库时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def design_japanese_dialect_exam(self, exam_name, dialect_types=None, sections=None, duration=60):
        """设计日语方言考试"""
        try:
            logger.info(f"考试测试专家AI正在设计日语方言考试: {exam_name}")
            
            if not dialect_types:
                dialect_types = ["kansai", "kanto"]
            
            if not sections:
                sections = ["词汇", "语法", "翻译", "识别", "会话", "对比"]
            
            # 生成考试结构
            exam_sections = []
            for section in sections:
                section_info = {
                    "name": section,
                    "question_count": 5,
                    "score_per_question": 20,
                    "total_score": 100
                }
                exam_sections.append(section_info)
            
            return {
                "status": "success",
                "message": f"日语方言考试 {exam_name} 设计完成",
                "exam_design": {
                    "name": exam_name,
                    "dialect_types": dialect_types,
                    "duration": f"{duration}分钟",
                    "sections": exam_sections,
                    "total_score": sum(sec["total_score"] for sec in exam_sections)
                },
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"设计日语方言考试时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"设计日语方言考试时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def _init_english_dialect_knowledge(self):
        """初始化英语方言知识库"""
        return {
            "british_english": {
                "vocabulary": [
                    {"british": "colour", "american": "color", "meaning": "颜色"},
                    {"british": "centre", "american": "center", "meaning": "中心"},
                    {"british": "travelled", "american": "traveled", "meaning": "旅行（过去式）"},
                    {"british": "organisation", "american": "organization", "meaning": "组织"},
                    {"british": "lift", "american": "elevator", "meaning": "电梯"},
                    {"british": "tap", "american": "faucet", "meaning": "水龙头"},
                    {"british": "rubbish", "american": "garbage", "meaning": "垃圾"},
                    {"british": "queue", "american": "line", "meaning": "排队"},
                    {"british": "torch", "american": "flashlight", "meaning": "手电筒"},
                    {"british": "petrol", "american": "gasoline", "meaning": "汽油"},
                    {"british": "boot", "american": "trunk", "meaning": "汽车后备箱"},
                    {"british": "bonnet", "american": "hood", "meaning": "汽车引擎盖"},
                    {"british": "biscuit", "american": "cookie", "meaning": "饼干"},
                    {"british": "chips", "american": "fries", "meaning": "薯条"},
                    {"british": "crisps", "american": "chips", "meaning": "薯片"},
                    {"british": "aubergine", "american": "eggplant", "meaning": "茄子"},
                    {"british": "courgette", "american": "zucchini", "meaning": "西葫芦"}
                ],
                "grammar_examples": [
                    {
                        "british": "I have just finished my homework.",
                        "american": "I just finished my homework.",
                        "meaning": "我刚做完作业。"
                    },
                    {
                        "british": "She has gone to the shop.",
                        "american": "She went to the store.",
                        "meaning": "她去商店了。"
                    },
                    {
                        "british": "We needn't worry about that.",
                        "american": "We don't need to worry about that.",
                        "meaning": "我们不必担心那个。"
                    }
                ],
                "conversation_examples": [
                    {
                        "title": "Shopping Dialogue",
                        "british": [
                            "Customer: Could you tell me where the lift is?",
                            "Shopkeeper: Certainly, it's just around the corner.",
                            "Customer: Thank you very much.",
                            "Shopkeeper: You're welcome. Enjoy your shopping!"
                        ],
                        "american": [
                            "Customer: Could you tell me where the elevator is?",
                            "Shopkeeper: Certainly, it's just around the corner.",
                            "Customer: Thank you very much.",
                            "Shopkeeper: You're welcome. Enjoy your shopping!"
                        ]
                    }
                ]
            },
            "american_english": {
                "vocabulary": [
                    {"american": "color", "british": "colour", "meaning": "颜色"},
                    {"american": "center", "british": "centre", "meaning": "中心"},
                    {"american": "traveled", "british": "travelled", "meaning": "旅行（过去式）"},
                    {"american": "organization", "british": "organisation", "meaning": "组织"},
                    {"american": "elevator", "british": "lift", "meaning": "电梯"},
                    {"american": "faucet", "british": "tap", "meaning": "水龙头"},
                    {"american": "garbage", "british": "rubbish", "meaning": "垃圾"},
                    {"american": "line", "british": "queue", "meaning": "排队"},
                    {"american": "flashlight", "british": "torch", "meaning": "手电筒"},
                    {"american": "gasoline", "british": "petrol", "meaning": "汽油"},
                    {"american": "trunk", "british": "boot", "meaning": "汽车后备箱"},
                    {"american": "hood", "british": "bonnet", "meaning": "汽车引擎盖"},
                    {"american": "cookie", "british": "biscuit", "meaning": "饼干"},
                    {"american": "fries", "british": "chips", "meaning": "薯条"},
                    {"american": "chips", "british": "crisps", "meaning": "薯片"},
                    {"american": "eggplant", "british": "aubergine", "meaning": "茄子"},
                    {"american": "zucchini", "british": "courgette", "meaning": "西葫芦"}
                ],
                "grammar_examples": [
                    {
                        "american": "I just finished my homework.",
                        "british": "I have just finished my homework.",
                        "meaning": "我刚做完作业。"
                    },
                    {
                        "american": "She went to the store.",
                        "british": "She has gone to the shop.",
                        "meaning": "她去商店了。"
                    },
                    {
                        "american": "We don't need to worry about that.",
                        "british": "We needn't worry about that.",
                        "meaning": "我们不必担心那个。"
                    }
                ],
                "conversation_examples": [
                    {
                        "title": "Business Meeting",
                        "american": [
                            "Manager: Can we start the meeting?",
                            "Employee: Sure, everyone is here.",
                            "Manager: Great, let's get started.",
                            "Employee: Should I take notes?",
                            "Manager: That would be helpful, thank you."
                        ],
                        "british": [
                            "Manager: Can we start the meeting?",
                            "Employee: Sure, everyone is here.",
                            "Manager: Great, let's get started.",
                            "Employee: Should I take notes?",
                            "Manager: That would be helpful, thank you."
                        ]
                    }
                ]
            },
            "comparison": [
                {
                    "category": "Spelling - our vs -or",
                    "british": "colour, honour, labour",
                    "american": "color, honor, labor",
                    "example": "British English uses 'our' endings"
                },
                {
                    "category": "Spelling - re vs -er",
                    "british": "centre, theatre, metre",
                    "american": "center, theater, meter",
                    "example": "British English uses 're' endings"
                },
                {
                    "category": "Spelling - double l",
                    "british": "travelled, cancelled, levelled",
                    "american": "traveled, canceled, leveled",
                    "example": "British English doubles the 'l'"
                },
                {
                    "category": "Vocabulary",
                    "british": "lift, petrol, rubbish",
                    "american": "elevator, gasoline, garbage",
                    "example": "Different words for the same thing"
                },
                {
                    "category": "Grammar - Present Perfect",
                    "british": "I've just eaten.",
                    "american": "I just ate.",
                    "example": "American English uses Simple Past more"
                }
            ],
            "questions": {
                "vocabulary": [
                    {
                        "question": "What is the British English word for 'color'?",
                        "options": ["colur", "colour", "coler", "colore"],
                        "answer": "colour",
                        "explanation": "British English uses 'our' endings for words like colour, honour, and labour."
                    },
                    {
                        "question": "What do Americans call a 'lift'?",
                        "options": ["escalator", "elevator", "stairs", "ramp"],
                        "answer": "elevator",
                        "explanation": "In American English, a 'lift' is called an 'elevator'."
                    },
                    {
                        "question": "What is 'petrol' called in American English?",
                        "options": ["gas", "diesel", "fuel", "oil"],
                        "answer": "gas",
                        "explanation": "Petrol in British English is called gas or gasoline in American English."
                    }
                ],
                "spelling": [
                    {
                        "question": "Which is the correct British spelling?",
                        "options": ["center", "centre", "centr", "centar"],
                        "answer": "centre",
                        "explanation": "British English uses 're' endings for words like centre, theatre, and metre."
                    },
                    {
                        "question": "Which is the correct American spelling?",
                        "options": ["travelled", "traveled", "travaled", "travelleed"],
                        "answer": "traveled",
                        "explanation": "American English doesn't double the 'l' in words like traveled, canceled, and leveled."
                    }
                ],
                "grammar": [
                    {
                        "question": "Which sentence is more common in American English?",
                        "options": [
                            "I have just finished.",
                            "I just finished.",
                            "I am just finishing.",
                            "I just finish."
                        ],
                        "answer": "I just finished.",
                        "explanation": "American English often uses the Simple Past tense where British English uses the Present Perfect."
                    }
                ],
                "comprehension": [
                    {
                        "question": "Read the sentence and answer the question:\n\nBritish: 'Could you wait in the queue, please?'\nAmerican: 'Could you wait in the line, please?'\n\nWhat does 'queue' mean in American English?",
                        "answer": "line",
                        "explanation": "In American English, people wait 'in line' while in British English they wait 'in queue'."
                    }
                ]
            }
        }
    
    def generate_british_english_questions(self, question_type, count=5, difficulty="medium"):
        """生成英国英语试题"""
        try:
            logger.info(f"考试测试专家AI正在生成英国英语试题，类型: {question_type}, 数量: {count}")
            
            if not self.english_dialect_knowledge:
                return {
                    "status": "error",
                    "message": "英语方言知识库未初始化",
                    "timestamp": time.time()
                }
            
            questions_data = self.english_dialect_knowledge.get("questions", {})
            
            type_mapping = {
                "vocabulary": "vocabulary",
                "spelling": "spelling",
                "grammar": "grammar",
                "comprehension": "comprehension"
            }
            
            target_type = type_mapping.get(question_type, "vocabulary")
            target_questions = questions_data.get(target_type, [])
            
            # 生成试题
            generated_questions = []
            for i in range(min(count, len(target_questions))):
                question_data = target_questions[i].copy()
                question_data["difficulty"] = difficulty
                question_data["dialect_type"] = "british"
                generated_questions.append(question_data)
            
            return {
                "status": "success",
                "message": f"成功生成 {len(generated_questions)} 道英国英语试题",
                "questions": generated_questions,
                "dialect_type": "british",
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"生成英国英语试题时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"生成英国英语试题时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def generate_american_english_questions(self, question_type, count=5, difficulty="medium"):
        """生成美国英语试题"""
        try:
            logger.info(f"考试测试专家AI正在生成美国英语试题，类型: {question_type}, 数量: {count}")
            
            if not self.english_dialect_knowledge:
                return {
                    "status": "error",
                    "message": "英语方言知识库未初始化",
                    "timestamp": time.time()
                }
            
            questions_data = self.english_dialect_knowledge.get("questions", {})
            
            type_mapping = {
                "vocabulary": "vocabulary",
                "spelling": "spelling",
                "grammar": "grammar",
                "comprehension": "comprehension"
            }
            
            target_type = type_mapping.get(question_type, "vocabulary")
            target_questions = questions_data.get(target_type, [])
            
            # 生成美国英语视角的试题
            generated_questions = []
            for i in range(min(count, len(target_questions))):
                question_data = target_questions[i].copy()
                question_data["difficulty"] = difficulty
                question_data["dialect_type"] = "american"
                generated_questions.append(question_data)
            
            return {
                "status": "success",
                "message": f"成功生成 {len(generated_questions)} 道美国英语试题",
                "questions": generated_questions,
                "dialect_type": "american",
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"生成美国英语试题时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"生成美国英语试题时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def generate_english_dialect_comparison_questions(self, count=5, difficulty="medium"):
        """生成英语方言对比试题"""
        try:
            logger.info(f"考试测试专家AI正在生成英语方言对比试题，数量: {count}")
            
            if not self.english_dialect_knowledge:
                return {
                    "status": "error",
                    "message": "英语方言知识库未初始化",
                    "timestamp": time.time()
                }
            
            comparison_data = self.english_dialect_knowledge.get("comparison", [])
            
            # 生成对比试题
            comparison_questions = []
            for i, item in enumerate(comparison_data[:count]):
                question = {
                    "question": f"Explain the difference between British English and American English in {item['category']}.",
                    "british": item["british"],
                    "american": item["american"],
                    "example": item["example"],
                    "difficulty": difficulty,
                    "question_type": "comparison"
                }
                comparison_questions.append(question)
            
            return {
                "status": "success",
                "message": f"成功生成 {len(comparison_questions)} 道英语方言对比试题",
                "questions": comparison_questions,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"生成英语方言对比试题时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"生成英语方言对比试题时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def get_english_dialect_knowledge(self, dialect_type=None):
        """获取英语方言知识库"""
        try:
            logger.info(f"考试测试专家AI正在获取英语方言知识库，方言类型: {dialect_type}")
            
            if not self.english_dialect_knowledge:
                return {
                    "status": "error",
                    "message": "英语方言知识库未初始化",
                    "timestamp": time.time()
                }
            
            if dialect_type == "british":
                knowledge = self.english_dialect_knowledge.get("british_english", {})
            elif dialect_type == "american":
                knowledge = self.english_dialect_knowledge.get("american_english", {})
            else:
                knowledge = self.english_dialect_knowledge
            
            return {
                "status": "success",
                "message": f"成功获取{' ' + dialect_type if dialect_type else ''}英语方言知识库",
                "dialect_type": dialect_type,
                "knowledge": knowledge,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"获取英语方言知识库时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"获取英语方言知识库时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def design_english_dialect_exam(self, exam_name, dialect_types=None, sections=None, duration=60):
        """设计英语方言考试"""
        try:
            logger.info(f"考试测试专家AI正在设计英语方言考试: {exam_name}")
            
            if not dialect_types:
                dialect_types = ["british", "american"]
            
            if not sections:
                sections = ["Vocabulary", "Spelling", "Grammar", "Comprehension", "Comparison"]
            
            # 生成考试结构
            exam_sections = []
            for section in sections:
                section_info = {
                    "name": section,
                    "question_count": 5,
                    "score_per_question": 20,
                    "total_score": 100
                }
                exam_sections.append(section_info)
            
            return {
                "status": "success",
                "message": f"英语方言考试 {exam_name} 设计完成",
                "exam_design": {
                    "name": exam_name,
                    "dialect_types": dialect_types,
                    "duration": f"{duration} minutes",
                    "sections": exam_sections,
                    "total_score": sum(sec["total_score"] for sec in exam_sections)
                },
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"设计英语方言考试时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"设计英语方言考试时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def _init_nine_year_education_knowledge(self):
        """初始化九年制义务教育知识库"""
        return {
            "primary_school": {
                "grade_1_2": {
                    "chinese": {
                        "topics": ["拼音", "识字", "简单句子", "古诗", "看图写话"],
                        "teaching_plans": [
                            {
                                "title": "拼音教学计划",
                                "objectives": ["认识声母韵母", "学会拼音拼写", "能够正确拼读"],
                                "duration": "2课时",
                                "materials": ["拼音卡片", "拼音挂图", "练习册"]
                            }
                        ],
                        "example_questions": [
                            {"type": "fill_in_blank", "question": "b-ā→(    )", "answer": "bā"},
                            {"type": "multiple_choice", "question": "下列哪个是声母？", "options": ["a", "b", "o", "e"], "answer": "b"}
                        ]
                    },
                    "math": {
                        "topics": ["10以内数的认识", "10以内加减法", "图形认识", "简单应用题"],
                        "teaching_plans": [
                            {
                                "title": "10以内加减法教学计划",
                                "objectives": ["掌握10以内加减法", "理解加减法含义", "解决简单应用题"],
                                "duration": "3课时",
                                "materials": ["小棒", "计数器", "练习题"]
                            }
                        ],
                        "example_questions": [
                            {"type": "calculation", "question": "3+5=(    )", "answer": "8"},
                            {"type": "word_problem", "question": "小明有3个苹果，妈妈又给了他2个，小明现在有几个苹果？", "answer": "5个"}
                        ]
                    }
                },
                "grade_3_4": {
                    "chinese": {
                        "topics": ["词语积累", "句子训练", "阅读理解", "作文入门", "古诗鉴赏"],
                        "teaching_plans": [
                            {
                                "title": "阅读理解教学计划",
                                "objectives": ["理解文章大意", "找出关键信息", "回答问题"],
                                "duration": "2课时",
                                "materials": ["阅读材料", "练习题"]
                            }
                        ],
                        "example_questions": [
                            {"type": "reading", "question": "阅读短文，回答问题：太阳从什么方向升起？", "answer": "东方"}
                        ]
                    },
                    "math": {
                        "topics": ["万以内数的认识", "乘除法", "周长面积", "小数初步认识"],
                        "teaching_plans": [
                            {
                                "title": "乘除法教学计划",
                                "objectives": ["掌握乘法口诀", "学会除法运算", "解决乘除应用题"],
                                "duration": "4课时",
                                "materials": ["乘法口诀表", "练习题"]
                            }
                        ],
                        "example_questions": [
                            {"type": "calculation", "question": "6×7=(    )", "answer": "42"}
                        ]
                    },
                    "english": {
                        "topics": ["字母", "简单单词", "日常用语", "简单对话"],
                        "teaching_plans": [
                            {
                                "title": "字母教学计划",
                                "objectives": ["认识26个字母", "学会字母发音", "正确书写字母"],
                                "duration": "3课时",
                                "materials": ["字母卡片", "字母挂图"]
                            }
                        ],
                        "example_questions": [
                            {"type": "multiple_choice", "question": "哪个是字母A？", "options": ["B", "A", "C", "D"], "answer": "A"}
                        ]
                    }
                },
                "grade_5_6": {
                    "chinese": {
                        "topics": ["修辞手法", "篇章理解", "作文训练", "文言文初步", "文学常识"],
                        "teaching_plans": [
                            {
                                "title": "修辞手法教学计划",
                                "objectives": ["认识比喻拟人", "学会运用修辞", "赏析文中修辞"],
                                "duration": "2课时",
                                "materials": ["例句", "练习题"]
                            }
                        ],
                        "example_questions": [
                            {"type": "short_answer", "question": "请写出一个比喻句。", "answer": "示例：月亮像个大圆盘。"}
                        ]
                    },
                    "math": {
                        "topics": ["分数", "小数", "百分数", "比例", "几何图形", "统计初步"],
                        "teaching_plans": [
                            {
                                "title": "分数教学计划",
                                "objectives": ["理解分数概念", "掌握分数运算", "解决分数应用题"],
                                "duration": "5课时",
                                "materials": ["教具", "练习题"]
                            }
                        ],
                        "example_questions": [
                            {"type": "calculation", "question": "1/2 + 1/3 = (    )", "answer": "5/6"}
                        ]
                    },
                    "science": {
                        "topics": ["生命世界", "物质世界", "地球与宇宙", "科学探究"],
                        "teaching_plans": [
                            {
                                "title": "生命世界教学计划",
                                "objectives": ["了解生物特征", "认识动植物", "理解生态系统"],
                                "duration": "3课时",
                                "materials": ["图片", "标本", "视频"]
                            }
                        ],
                        "example_questions": [
                            {"type": "multiple_choice", "question": "下列哪个是植物？", "options": ["猫", "狗", "树", "鸟"], "answer": "树"}
                        ]
                    }
                }
            },
            "middle_school": {
                "grade_1": {
                    "chinese": {
                        "topics": ["现代文阅读", "古诗文阅读", "写作训练", "语文基础"],
                        "teaching_plans": [
                            {
                                "title": "现代文阅读教学计划",
                                "objectives": ["理解文章主旨", "分析人物形象", "品味语言"],
                                "duration": "3课时",
                                "materials": ["阅读材料", "练习题"]
                            }
                        ],
                        "example_questions": [
                            {"type": "short_answer", "question": "请概括文章的主要内容。", "answer": "根据具体文章作答"}
                        ]
                    },
                    "math": {
                        "topics": ["有理数", "整式", "一元一次方程", "几何图形"],
                        "teaching_plans": [
                            {
                                "title": "有理数教学计划",
                                "objectives": ["理解有理数概念", "掌握有理数运算", "解决实际问题"],
                                "duration": "6课时",
                                "materials": ["教材", "练习题"]
                            }
                        ],
                        "example_questions": [
                            {"type": "calculation", "question": "-3 + 5 = (    )", "answer": "2"}
                        ]
                    },
                    "english": {
                        "topics": ["词汇积累", "语法基础", "阅读理解", "写作入门"],
                        "teaching_plans": [
                            {
                                "title": "语法基础教学计划",
                                "objectives": ["掌握基本时态", "理解句子结构", "正确运用语法"],
                                "duration": "4课时",
                                "materials": ["教材", "练习题"]
                            }
                        ],
                        "example_questions": [
                            {"type": "multiple_choice", "question": "I (    ) a student.", "options": ["is", "am", "are", "be"], "answer": "am"}
                        ]
                    },
                    "history": {
                        "topics": ["中国古代史", "世界古代史", "历史事件", "历史人物"],
                        "teaching_plans": [
                            {
                                "title": "中国古代史教学计划",
                                "objectives": ["了解朝代更替", "认识重要事件", "理解历史影响"],
                                "duration": "5课时",
                                "materials": ["教材", "地图", "图片"]
                            }
                        ],
                        "example_questions": [
                            {"type": "multiple_choice", "question": "中国第一个统一的封建王朝是？", "options": ["商", "周", "秦", "汉"], "answer": "秦"}
                        ]
                    },
                    "geography": {
                        "topics": ["地球与地图", "世界地理", "中国地理", "自然地理"],
                        "teaching_plans": [
                            {
                                "title": "地球与地图教学计划",
                                "objectives": ["认识地球形状", "学会使用地图", "理解经纬线"],
                                "duration": "3课时",
                                "materials": ["地球仪", "地图"]
                            }
                        ],
                        "example_questions": [
                            {"type": "multiple_choice", "question": "地球的形状是？", "options": ["圆形", "方形", "不规则球体", "三角形"], "answer": "不规则球体"}
                        ]
                    },
                    "biology": {
                        "topics": ["生物与细胞", "生物多样性", "生态系统", "生物圈"],
                        "teaching_plans": [
                            {
                                "title": "生物与细胞教学计划",
                                "objectives": ["认识生物特征", "了解细胞结构", "理解生命活动"],
                                "duration": "4课时",
                                "materials": ["显微镜", "玻片", "图片"]
                            }
                        ],
                        "example_questions": [
                            {"type": "multiple_choice", "question": "细胞的控制中心是？", "options": ["细胞膜", "细胞质", "细胞核", "细胞壁"], "answer": "细胞核"}
                        ]
                    }
                },
                "grade_2": {
                    "physics": {
                        "topics": ["机械运动", "声现象", "光现象", "物态变化", "力学"],
                        "teaching_plans": [
                            {
                                "title": "机械运动教学计划",
                                "objectives": ["理解运动相对性", "掌握速度计算", "解决运动问题"],
                                "duration": "4课时",
                                "materials": ["教材", "实验器材"]
                            }
                        ],
                        "example_questions": [
                            {"type": "calculation", "question": "一个物体以5m/s的速度运动10秒，经过的距离是多少？", "answer": "50m"}
                        ]
                    },
                    "chemistry": {
                        "topics": ["物质的变化", "空气", "水", "溶液", "化学方程式"],
                        "teaching_plans": [
                            {
                                "title": "物质的变化教学计划",
                                "objectives": ["区分物理化学变化", "理解物质性质", "观察实验现象"],
                                "duration": "3课时",
                                "materials": ["实验器材", "药品"]
                            }
                        ],
                        "example_questions": [
                            {"type": "multiple_choice", "question": "下列哪个是化学变化？", "options": ["水结冰", "纸撕碎", "蜡烛燃烧", "玻璃破碎"], "answer": "蜡烛燃烧"}
                        ]
                    }
                },
                "grade_3": {
                    "chinese": {
                        "topics": ["现代文阅读", "古诗文阅读", "作文训练", "语文综合运用"],
                        "teaching_plans": [
                            {
                                "title": "中考复习教学计划",
                                "objectives": ["系统复习知识", "提高解题能力", "备战中考"],
                                "duration": "20课时",
                                "materials": ["复习资料", "模拟试题"]
                            }
                        ],
                        "example_questions": [
                            {"type": "essay", "question": "请以\"梦想\"为话题，写一篇600字以上的作文。", "answer": "略"}
                        ]
                    },
                    "math": {
                        "topics": ["函数", "圆", "相似三角形", "统计与概率", "中考复习"],
                        "teaching_plans": [
                            {
                                "title": "函数教学计划",
                                "objectives": ["理解函数概念", "掌握函数图像", "解决函数问题"],
                                "duration": "8课时",
                                "materials": ["教材", "练习题"]
                            }
                        ],
                        "example_questions": [
                            {"type": "calculation", "question": "求y=2x+1在x=3时的值。", "answer": "7"}
                        ]
                    }
                }
            }
        }
    
    def generate_nine_year_teaching_plan(self, subject, grade, topic=None):
        """生成九年制义务教育教案"""
        try:
            logger.info(f"考试测试专家AI正在生成九年制义务教育教案，学科: {subject}, 年级: {grade}")
            
            if not self.nine_year_education_knowledge:
                return {
                    "status": "error",
                    "message": "九年制义务教育知识库未初始化",
                    "timestamp": time.time()
                }
            
            # 确定年级段
            grade_section = None
            if "小学" in grade:
                if "1-2" in grade:
                    grade_section = "grade_1_2"
                elif "3-4" in grade:
                    grade_section = "grade_3_4"
                elif "5-6" in grade:
                    grade_section = "grade_5_6"
                section_key = "primary_school"
            elif "初中" in grade:
                if "1" in grade:
                    grade_section = "grade_1"
                elif "2" in grade:
                    grade_section = "grade_2"
                elif "3" in grade:
                    grade_section = "grade_3"
                section_key = "middle_school"
            else:
                return {
                    "status": "error",
                    "message": f"未找到年级: {grade}",
                    "timestamp": time.time()
                }
            
            subject_mapping = {
                "语文": "chinese",
                "数学": "math",
                "英语": "english",
                "科学": "science",
                "历史": "history",
                "地理": "geography",
                "生物": "biology",
                "物理": "physics",
                "化学": "chemistry"
            }
            
            subject_key = subject_mapping.get(subject)
            if not subject_key:
                return {
                    "status": "error",
                    "message": f"未找到学科: {subject}",
                    "timestamp": time.time()
                }
            
            # 获取对应学科知识
            section_data = self.nine_year_education_knowledge.get(section_key, {})
            grade_data = section_data.get(grade_section, {})
            subject_data = grade_data.get(subject_key, {})
            
            if not subject_data:
                return {
                    "status": "error",
                    "message": f"未找到 {grade} 年级 {subject} 学科的教案",
                    "timestamp": time.time()
                }
            
            # 选择特定主题或第一个主题
            if topic:
                # 查找匹配的主题
                selected_topic = None
                for plan in subject_data.get("teaching_plans", []):
                    if topic in plan.get("title", ""):
                        selected_topic = plan
                        break
                if selected_topic:
                    teaching_plan = selected_topic
                else:
                    teaching_plan = subject_data.get("teaching_plans", [{}])[0]
            else:
                teaching_plan = subject_data.get("teaching_plans", [{}])[0]
            
            return {
                "status": "success",
                "message": f"成功生成 {grade} 年级 {subject} 学科教案",
                "teaching_plan": teaching_plan,
                "topics": subject_data.get("topics", []),
                "grade": grade,
                "subject": subject,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"生成九年制义务教育教案时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"生成九年制义务教育教案时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def generate_nine_year_materials(self, subject, grade, material_type="teaching_plans"):
        """生成九年制义务教育素材"""
        try:
            logger.info(f"考试测试专家AI正在生成九年制义务教育素材，学科: {subject}, 年级: {grade}, 类型: {material_type}")
            
            if not self.nine_year_education_knowledge:
                return {
                    "status": "error",
                    "message": "九年制义务教育知识库未初始化",
                    "timestamp": time.time()
                }
            
            # 获取教案数据
            plan_result = self.generate_nine_year_teaching_plan(subject, grade)
            if plan_result["status"] != "success":
                return plan_result
            
            subject_data = None
            # 重新获取完整的学科数据
            grade_section = None
            if "小学" in grade:
                if "1-2" in grade:
                    grade_section = "grade_1_2"
                elif "3-4" in grade:
                    grade_section = "grade_3_4"
                elif "5-6" in grade:
                    grade_section = "grade_5_6"
                section_key = "primary_school"
            elif "初中" in grade:
                if "1" in grade:
                    grade_section = "grade_1"
                elif "2" in grade:
                    grade_section = "grade_2"
                elif "3" in grade:
                    grade_section = "grade_3"
                section_key = "middle_school"
            
            subject_mapping = {
                "语文": "chinese",
                "数学": "math",
                "英语": "english",
                "科学": "science",
                "历史": "history",
                "地理": "geography",
                "生物": "biology",
                "物理": "physics",
                "化学": "chemistry"
            }
            
            subject_key = subject_mapping.get(subject)
            section_data = self.nine_year_education_knowledge.get(section_key, {})
            grade_data = section_data.get(grade_section, {})
            subject_data = grade_data.get(subject_key, {})
            
            materials = {
                "teaching_plans": subject_data.get("teaching_plans", []),
                "example_questions": subject_data.get("example_questions", []),
                "topics": subject_data.get("topics", []),
                "worksheets": self._generate_worksheets(subject, grade, subject_data),
                "courseware_outline": self._generate_courseware_outline(subject, grade, subject_data)
            }
            
            return {
                "status": "success",
                "message": f"成功生成 {grade} 年级 {subject} 学科素材",
                "materials": materials.get(material_type, materials),
                "grade": grade,
                "subject": subject,
                "material_type": material_type,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"生成九年制义务教育素材时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"生成九年制义务教育素材时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def _generate_worksheets(self, subject, grade, subject_data):
        """生成练习题"""
        example_questions = subject_data.get("example_questions", [])
        worksheets = {
            "title": f"{grade} {subject} 练习题",
            "questions": example_questions[:10],
            "duration": "45分钟",
            "total_score": 100
        }
        return worksheets
    
    def _generate_courseware_outline(self, subject, grade, subject_data):
        """生成课件大纲"""
        topics = subject_data.get("topics", [])
        courseware = {
            "title": f"{grade} {subject} 课件",
            "chapters": [],
            "duration": f"{len(topics)}课时"
        }
        for i, topic in enumerate(topics, 1):
            courseware["chapters"].append({
                "chapter": i,
                "title": topic,
                "duration": "1课时"
            })
        return courseware
    
    def generate_nine_year_exam_questions(self, subject, grade, question_type=None, count=10, difficulty="medium"):
        """生成九年制义务教育试题"""
        try:
            logger.info(f"考试测试专家AI正在生成九年制义务教育试题，学科: {subject}, 年级: {grade}")
            
            if not self.nine_year_education_knowledge:
                return {
                    "status": "error",
                    "message": "九年制义务教育知识库未初始化",
                    "timestamp": time.time()
                }
            
            # 获取素材
            materials_result = self.generate_nine_year_materials(subject, grade)
            if materials_result["status"] != "success":
                return materials_result
            
            materials = materials_result["materials"]
            all_questions = []
            
            if isinstance(materials, dict) and "example_questions" in materials:
                all_questions = materials["example_questions"]
            elif isinstance(materials, list):
                all_questions = materials
            
            # 根据题型筛选
            if question_type:
                filtered_questions = [q for q in all_questions if q.get("type") == question_type]
                if filtered_questions:
                    all_questions = filtered_questions
            
            # 选择指定数量的试题
            selected_questions = all_questions[:count]
            
            # 添加难度标记
            for q in selected_questions:
                q["difficulty"] = difficulty
            
            return {
                "status": "success",
                "message": f"成功生成 {count} 道 {grade} 年级 {subject} 学科试题",
                "questions": selected_questions,
                "grade": grade,
                "subject": subject,
                "difficulty": difficulty,
                "count": len(selected_questions),
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"生成九年制义务教育试题时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"生成九年制义务教育试题时发生错误: {str(e)}",
                "timestamp": time.time()
            }
    
    def get_nine_year_education_knowledge(self, subject=None, grade=None):
        """获取九年制义务教育知识库"""
        try:
            logger.info(f"考试测试专家AI正在获取九年制义务教育知识库，学科: {subject}, 年级: {grade}")
            
            if not self.nine_year_education_knowledge:
                return {
                    "status": "error",
                    "message": "九年制义务教育知识库未初始化",
                    "timestamp": time.time()
                }
            
            knowledge = self.nine_year_education_knowledge
            
            if grade:
                if "小学" in grade:
                    if "1-2" in grade:
                        grade_section = "grade_1_2"
                    elif "3-4" in grade:
                        grade_section = "grade_3_4"
                    elif "5-6" in grade:
                        grade_section = "grade_5_6"
                    else:
                        return {
                            "status": "error",
                            "message": f"未找到年级: {grade}",
                            "timestamp": time.time()
                        }
                    knowledge = knowledge.get("primary_school", {}).get(grade_section, {})
                elif "初中" in grade:
                    if "1" in grade:
                        grade_section = "grade_1"
                    elif "2" in grade:
                        grade_section = "grade_2"
                    elif "3" in grade:
                        grade_section = "grade_3"
                    else:
                        return {
                            "status": "error",
                            "message": f"未找到年级: {grade}",
                            "timestamp": time.time()
                        }
                    knowledge = knowledge.get("middle_school", {}).get(grade_section, {})
                else:
                    return {
                        "status": "error",
                        "message": f"未找到年级: {grade}",
                        "timestamp": time.time()
                    }
            
            if subject:
                subject_mapping = {
                    "语文": "chinese",
                    "数学": "math",
                    "英语": "english",
                    "科学": "science",
                    "历史": "history",
                    "地理": "geography",
                    "生物": "biology",
                    "物理": "physics",
                    "化学": "chemistry"
                }
                subject_key = subject_mapping.get(subject)
                if subject_key:
                    knowledge = knowledge.get(subject_key, {})
            
            return {
                "status": "success",
                "message": f"成功获取九年制义务教育知识库",
                "knowledge": knowledge,
                "subject": subject,
                "grade": grade,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"获取九年制义务教育知识库时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"获取九年制义务教育知识库时发生错误: {str(e)}",
                "timestamp": time.time()
            }

# 创建考试测试专家AI实例
exam_expert_ai = ExamExpertAI()

# 初始化时创建实例
def init_exam_expert_ai():
    """初始化考试测试专家AI"""
    try:
        logger.info("初始化考试测试专家AI...")
        instance = exam_expert_ai.create_instance()
        if instance:
            logger.info("考试测试专家AI初始化成功")
            return True
        else:
            logger.error("考试测试专家AI初始化失败")
            return False
    except Exception as e:
        logger.error(f"初始化考试测试专家AI时发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    # 测试创建考试测试专家AI实例
    init_exam_expert_ai()
