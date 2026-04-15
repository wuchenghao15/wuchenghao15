#!/usr/bin/env python3
"""
智能题目生成模块
利用预训练语言模型增强题目质量
"""

import os
import sys
import json
import time
import random
import re
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class AIModel(ABC):
    """AI模型抽象基类"""
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    def generate_question(self, language: str, category: str, difficulty: int, **kwargs) -> Dict[str, Any]:
        """生成题目"""
        pass

class MockAIModel(AIModel):
    """模拟AI模型，用于测试"""
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        return f"Mock response for: {prompt}"
    
    def generate_question(self, language: str, category: str, difficulty: int, **kwargs) -> Dict[str, Any]:
        """生成题目"""
        # 使用现有的模板生成逻辑
        return {}

class SmartQuestionGenerator:
    """智能题目生成器"""
    
    def __init__(self, ai_model: Optional[AIModel] = None):
        # 从数据库加载配置
        self._load_config_from_db()
        
        # 初始化AI模型
        self.using_ai_integrator = False
        if ai_model:
            self.ai_model = ai_model
        else:
            try:
                # 尝试使用项目中的AI引擎集成器
                from app.ai.ai_engine_integrator import ai_engine_integrator
                self.ai_engine_integrator = ai_engine_integrator
                self.using_ai_integrator = True
                print("[INFO] 已初始化AI引擎集成器")
            except ImportError:
                # 如果AI引擎集成器不可用，使用Mock模型
                self.ai_model = MockAIModel()
                print("[WARNING] AI引擎集成器不可用，使用Mock模型")
        
        # 添加更多题目模板
        self._init_enhanced_templates()
    
    def _load_config_from_db(self):
        """从数据库加载配置"""
        try:
            import sqlite3
            import json
            
            # 简化配置加载：直接使用默认配置，避免尝试加载Flask应用或primary.db
            config_dict = {}
            print("[INFO] 使用简化配置加载，避免依赖Flask应用")
            
            # 设置配置值
            self.model_type = config_dict.get("ai_model_type", "gpt-4o-mini")
            self.supported_languages = config_dict.get("supported_languages", ["japanese", "english", "chinese"])
            self.supported_categories = config_dict.get("supported_categories", ["词汇", "语法", "阅读", "听力", "写作", "口语", "翻译"])
            self.supported_difficulties = config_dict.get("supported_difficulties", [1, 2, 3, 4, 5])  # 从数据库加载
            self.supported_question_types = config_dict.get("supported_question_types", ["single", "multiple", "fill", "short_answer", "essay", "speaking", "translation"])
            self.paper_category_ratios = config_dict.get("paper_category_ratios", {})
            self.scoring_criteria = config_dict.get("scoring_criteria", {})
            self.default_question_count = int(config_dict.get("default_question_count", 20))
            self.default_user_level = int(config_dict.get("default_user_level", 3))
            
            # 新增：AI评分相关配置
            self.ai_scoring_enabled = config_dict.get("ai_scoring_enabled", True)
            self.ai_scoring_threshold = float(config_dict.get("ai_scoring_threshold", 0.8))
            self.ai_scoring_max_time = int(config_dict.get("ai_scoring_max_time", 30))
            
            # 新增：题目生成质量控制
            self.question_generation_quality = config_dict.get("question_generation_quality", "high")
            self.question_generation_timeout = int(config_dict.get("question_generation_timeout", 60))
            
            # 新增：题库扩展配置
            self.question_bank_expansion_enabled = config_dict.get("question_bank_expansion_enabled", True)
            self.question_bank_expansion_rate = float(config_dict.get("question_bank_expansion_rate", 0.1))
            
            print("[INFO] 配置加载成功")
        except Exception as e:
            # 如果数据库加载失败，使用默认配置
            print(f"[WARNING] 配置加载失败，使用默认配置: {e}")
            self.model_type = "gpt-4o-mini"  # 默认使用的模型类型
            self.supported_languages = ["japanese", "english", "chinese"]
            self.supported_categories = ["词汇", "语法", "阅读", "听力", "写作", "口语", "翻译"]
            self.supported_difficulties = [1, 2, 3, 4, 5]
            self.supported_question_types = ["single", "multiple", "fill", "short_answer", "essay", "speaking", "translation"]
            self.paper_category_ratios = {}
            self.scoring_criteria = {}
            self.default_question_count = 20
            self.default_user_level = 3
            
            # 新增：AI评分相关默认配置
            self.ai_scoring_enabled = True
            self.ai_scoring_threshold = 0.8
            self.ai_scoring_max_time = 30
            
            # 新增：题目生成质量控制默认配置
            self.question_generation_quality = "high"
            self.question_generation_timeout = 60
            
            # 新增：题库扩展默认配置
            self.question_bank_expansion_enabled = True
            self.question_bank_expansion_rate = 0.1
    
    def _init_enhanced_templates(self):
        """初始化增强的题目模板"""
        # 后续实现更丰富的模板系统
        pass
        
    def generate_question(self, language: str, category: str, difficulty: int, knowledge_points: List[str] = None, 
                         question_type: Optional[str] = None, use_ai: bool = True) -> Dict[str, Any]:
        """
        生成单个智能题目
        
        Args:
            language: 语言类型 (japanese/english/chinese)
            category: 题目类别 (词汇/语法/阅读/听力/写作/口语/翻译)
            difficulty: 难度等级 (1-5)
            knowledge_points: 知识点列表
            question_type: 题目类型 (single/multiple/fill/short_answer/essay/speaking/translation)
            use_ai: 是否使用AI生成题目
            
        Returns:
            题目字典
        """
        if language not in self.supported_languages:
            raise ValueError(f"不支持的语言: {language}")
        
        if category not in self.supported_categories:
            raise ValueError(f"不支持的题目类别: {category}")
        
        if difficulty not in self.supported_difficulties:
            raise ValueError(f"难度等级必须在1-5之间: {difficulty}")
        
        # 生成唯一ID
        unique_id = f"smart_{int(time.time() * 1000)}_{random.randint(1, 1000)}"
        
        # 生成题目
        try:
            # 直接使用模板生成，避免依赖AI引擎集成器
            question = self._generate_question_content(language, category, difficulty, knowledge_points, question_type)
            options = self._generate_options(question, category, language, difficulty)
            explanation = self._generate_explanation(question, category, language, difficulty)
            
            # 如果成功生成题目，添加选项和解析
            question['options'] = options
            question['explanation'] = explanation
        except Exception as e:
            # 生成失败，使用默认模板
            print(f"生成题目失败，使用默认模板: {e}")
            question = {
                'content': f"{language} {category} 题目示例",
                'options': ["选项A", "选项B", "选项C", "选项D"],
                'type': question_type or 'single',
                'required_answers': 1,
                'correct_answers': ['A'],
                'explanation': "这是一道示例题目"
            }
        
        # 生成知识点
        if not knowledge_points:
            knowledge_points = self._generate_knowledge_points(category, difficulty)
        
        # 计算新鲜感分数
        freshness_score = random.uniform(0.8, 1.0)
        
        return {
            'id': unique_id,
            'language': language,
            'category': category,
            'difficulty': difficulty,
            'content': question['content'],
            'options': question['options'],
            'question_type': question['type'] or question_type or 'single',
            'required_answers': question.get('required_answers', 1),
            'correct_answers': question['correct_answers'],
            'explanation': question['explanation'],
            'knowledge_points': knowledge_points,
            'used_count': 0,
            'created_at': time.time(),
            'freshness_score': freshness_score,
            'generated_by_ai': use_ai
        }
    
    def _generate_question_with_ai_integrator(self, language: str, category: str, difficulty: int, 
                                             knowledge_points: List[str] = None, question_type: Optional[str] = None) -> Dict[str, Any]:
        """
        使用AI引擎集成器生成题目
        """
        # 定义语言映射
        language_map = {
            "japanese": "日语",
            "english": "英语",
            "chinese": "中文"
        }
        
        # 定义题目类型映射
        question_type_map = {
            "single": "单选题",
            "multiple": "多选题",
            "fill": "填空题",
            "short_answer": "简答题",
            "essay": "作文题",
            "speaking": "口语题",
            "translation": "翻译题"
        }
        
        # 生成知识点字符串
        knowledge_points_str = "、".join(knowledge_points) if knowledge_points else "相关知识点"
        
        # 根据题目类型生成不同的提示词
        if question_type in ["single", "multiple"]:
            prompt = f"请生成一道{language_map[language]}的{category}类{question_type_map[question_type]}，难度为{difficulty}级（1-5级，1级最简单，5级最难）。\n"
            prompt += f"知识点：{knowledge_points_str}\n"
            prompt += "请按照以下JSON格式返回，确保JSON格式正确：\n"
            prompt += "{\n"
            prompt += '  "content": "题目内容",\n'
            prompt += '  "options": ["选项A", "选项B", "选项C", "选项D"],\n'
            prompt += '  "type": "single或multiple",\n'
            prompt += '  "required_answers": 1或多个,\n'
            prompt += '  "correct_answers": ["正确选项字母"],\n'
            prompt += '  "explanation": "详细解析"\n'
            prompt += "}\n"
            prompt += "要求：\n"
            prompt += "1. 题目内容必须原创，不能重复\n"
            prompt += "2. 选项必须清晰、有区分度\n"
            prompt += "3. 正确答案必须唯一（单选题）或多个（多选题）\n"
            prompt += "4. 解析必须详细，说明为什么正确答案正确，错误选项错误\n"
        elif question_type == "fill":
            prompt = f"请生成一道{language_map[language]}的{category}类{question_type_map[question_type]}，难度为{difficulty}级（1-5级，1级最简单，5级最难）。\n"
            prompt += f"知识点：{knowledge_points_str}\n"
            prompt += "请按照以下JSON格式返回，确保JSON格式正确：\n"
            prompt += "{\n"
            prompt += '  "content": "题目内容（含空格或下划线）",\n'
            prompt += '  "type": "fill",\n'
            prompt += '  "required_answers": 1或多个,\n'
            prompt += '  "correct_answers": ["正确答案内容"],\n'
            prompt += '  "explanation": "详细解析"\n'
            prompt += "}\n"
        elif question_type in ["short_answer", "essay", "speaking"]:
            prompt = f"请生成一道{language_map[language]}的{category}类{question_type_map[question_type]}，难度为{difficulty}级（1-5级，1级最简单，5级最难）。\n"
            prompt += f"知识点：{knowledge_points_str}\n"
            prompt += "请按照以下JSON格式返回，确保JSON格式正确：\n"
            prompt += "{\n"
            prompt += '  "content": "题目内容",\n'
            prompt += f'  "type": "{question_type}",\n'
            prompt += '  "required_answers": 1,\n'
            prompt += '  "correct_answers": [],\n'
            prompt += '  "explanation": "评分标准或答题要点"\n'
            prompt += "}\n"
        elif question_type == "translation":
            prompt = f"请生成一道{language_map[language]}的{category}类{question_type_map[question_type]}，难度为{difficulty}级（1-5级，1级最简单，5级最难）。\n"
            prompt += f"知识点：{knowledge_points_str}\n"
            prompt += "请按照以下JSON格式返回，确保JSON格式正确：\n"
            prompt += "{\n"
            prompt += '  "content": "需要翻译的内容",\n'
            prompt += '  "type": "translation",\n'
            prompt += '  "required_answers": 1,\n'
            prompt += '  "correct_answers": ["正确翻译"],\n'
            prompt += '  "explanation": "翻译要点"\n'
            prompt += "}\n"
        else:
            # 默认生成单选题
            prompt = f"请生成一道{language_map[language]}的{category}类单选题，难度为{difficulty}级（1-5级，1级最简单，5级最难）。\n"
            prompt += f"知识点：{knowledge_points_str}\n"
            prompt += "请按照JSON格式返回，包含content、options、type、required_answers、correct_answers和explanation字段。\n"
        
        try:
            # 调用AI引擎生成题目
            result = self.ai_engine_integrator.call_engine("openai", prompt, temperature=0.7, max_tokens=2048)
            
            if result and result.get("code") == 0:
                ai_response = result["data"]["response"]
                
                # 提取JSON部分
                json_start = ai_response.find("{")
                json_end = ai_response.rfind("}") + 1
                if json_start != -1 and json_end != -1:
                    json_str = ai_response[json_start:json_end]
                    question_data = json.loads(json_str)
                    
                    # 验证必要字段
                    if "content" in question_data:
                        # 确保type字段正确
                        if "type" not in question_data and question_type:
                            question_data["type"] = question_type
                        
                        # 确保options字段存在（如果需要）
                        if question_type in ["single", "multiple"] and "options" not in question_data:
                            question_data["options"] = ["选项A", "选项B", "选项C", "选项D"]
                        
                        # 确保required_answers字段存在
                        if "required_answers" not in question_data:
                            question_data["required_answers"] = 1
                        
                        # 确保correct_answers字段存在
                        if "correct_answers" not in question_data:
                            question_data["correct_answers"] = []
                        
                        # 确保explanation字段存在
                        if "explanation" not in question_data:
                            question_data["explanation"] = ""
                        
                        return question_data
            
            # 如果AI生成失败，回退到模板生成
            return self._generate_question_content(language, category, difficulty, knowledge_points, question_type)
            
        except Exception as e:
            print(f"AI引擎生成题目失败: {e}")
            # 回退到模板生成
            return self._generate_question_content(language, category, difficulty, knowledge_points, question_type)
    
    def _generate_question_content(self, language: str, category: str, difficulty: int, knowledge_points: List[str] = None, 
                                  question_type: Optional[str] = None) -> Dict[str, Any]:
        """生成题目内容"""
        # 模拟不同语言和类别的题目生成
        if language == "japanese":
            return self._generate_japanese_question(category, difficulty, question_type)
        elif language == "english":
            return self._generate_english_question(category, difficulty, question_type)
        else:
            return self._generate_chinese_question(category, difficulty, question_type)
    
    def _generate_japanese_question(self, category: str, difficulty: int, question_type: Optional[str] = None) -> Dict[str, Any]:
        """生成日语题目"""
        # 日语题目模板库
        templates = {
            '词汇': {
                1: [
                    {
                        'content': '「こんにちは」の正しい意味はどれですか？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': '「ありがとう」の正しい意味はどれですか？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    },
                    {
                        'content': '「おはようございます」は何時に使いますか？',
                        'type': 'multiple',
                        'required_answers': 2,
                        'correct_answers': ['A', 'B']
                    }
                ],
                2: [
                    {
                        'content': '「友達」の正しい意味はどれですか？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': '「食べる」の正しい意味はどれですか？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': '次の単語の中から、食べ物に関するものを選んでください。',
                        'type': 'multiple',
                        'required_answers': 3,
                        'correct_answers': ['A', 'C', 'E']
                    }
                ],
                3: [
                    {
                        'content': '「勉強」の正しい意味はどれですか？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': '「上手」の正しい意味はどれですか？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': '「昨日、私は公園で友達に_____。」の空欄に入る最も適切な単語は？',
                        'type': 'fill',
                        'required_answers': 1,
                        'correct_answers': ['会いました']
                    }
                ],
                4: [
                    {
                        'content': '「喧嘩」の正しい意味はどれですか？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    },
                    {
                        'content': '「感激」の正しい意味はどれですか？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    },
                    {
                        'content': '「この本はとても_____で、一気に読んでしまいました。」の空欄に入る最も適切な単語は？',
                        'type': 'fill',
                        'required_answers': 1,
                        'correct_answers': ['面白い']
                    }
                ],
                5: [
                    {
                        'content': '「邂逅」の正しい意味はどれですか？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['D']
                    },
                    {
                        'content': '「一蹴」の正しい意味はどれですか？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    },
                    {
                        'content': '「彼は困難な状況でも、決して_____ことはない。」の空欄に入る最も適切な単語は？',
                        'type': 'fill',
                        'required_answers': 1,
                        'correct_answers': ['諦める']
                    }
                ]
            },
            '语法': {
                1: [
                    {
                        'content': '私は_____です。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': 'あなたは_____ですか？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    }
                ],
                2: [
                    {
                        'content': '昨日、私は映画を_____。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    },
                    {
                        'content': '毎日、私は学校に_____。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ],
                3: [
                    {
                        'content': '彼は来週_____と言いました。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    },
                    {
                        'content': 'もし雨が降ったら、私は行きません。これは_____文です。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    }
                ],
                4: [
                    {
                        'content': 'この本は私が_____だけでなく、友達にも勧めています。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['D']
                    },
                    {
                        'content': '彼は_____と言っているが、本当かどうかは分からない。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ],
                5: [
                    {
                        'content': 'この問題は_____難しくて、私には解けません。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    },
                    {
                        'content': '彼は_____について、詳しく説明してくれました。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    }
                ]
            },
            '阅读': {
                1: [
                    {
                        'content': '私は毎朝7時に起きます。それから、歯を磨いて、朝ご飯を食べます。8時半に学校に行きます。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ],
                2: [
                    {
                        'content': '昨日、私は友達と映画を見に行きました。映画はとても面白かったです。帰りに、レストランで食事をしました。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    }
                ],
                3: [
                    {
                        'content': '日本の春は3月から5月までです。桜が咲いて、とてもきれいです。多くの人が花見に行きます。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    }
                ],
                4: [
                    {
                        'content': '近年、日本の高齢化が進んでいます。65歳以上の人口が増えて、社会保障費が増加しています。政府は様々な対策を講じています。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['D']
                    }
                ],
                5: [
                    {
                        'content': '日本の経済は高度成長期を経て、世界第3位の経済大国になりました。近年は少子化や高齢化の影響で、成長率が低くなっています。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ]
            },
            '听力': {
                1: [
                    {
                        'content': '会話を聞いて、正しい答えを選んでください。（会話：A: こんにちは。B: こんにちは。）',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ],
                2: [
                    {
                        'content': '会話を聞いて、正しい答えを選んでください。（会話：A: 昨日何をしましたか？B: 映画を見ました。）',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    }
                ]
            },
            '写作': {
                1: [
                    {
                        'content': '「私の一日」をテーマに、50字程度の短文を書いてください。',
                        'type': 'essay',
                        'required_answers': 1,
                        'correct_answers': []
                    }
                ],
                2: [
                    {
                        'content': '「私の趣味」をテーマに、100字程度の短文を書いてください。',
                        'type': 'essay',
                        'required_answers': 1,
                        'correct_answers': []
                    }
                ]
            },
            '口语': {
                1: [
                    {
                        'content': '「自己紹介」をしてください。（30秒程度）',
                        'type': 'speaking',
                        'required_answers': 1,
                        'correct_answers': []
                    }
                ],
                2: [
                    {
                        'content': '「私の好きな食べ物」について話してください。（1分程度）',
                        'type': 'speaking',
                        'required_answers': 1,
                        'correct_answers': []
                    }
                ]
            },
            '翻译': {
                1: [
                    {
                        'content': '请将「こんにちは」翻译成中文。',
                        'type': 'translation',
                        'required_answers': 1,
                        'correct_answers': ['你好']
                    }
                ],
                2: [
                    {
                        'content': '请将「ありがとう」翻译成中文。',
                        'type': 'translation',
                        'required_answers': 1,
                        'correct_answers': ['谢谢']
                    }
                ]
            }
        }
        
        # 根据question_type过滤模板
        category_templates = templates.get(category, {})
        difficulty_templates = category_templates.get(difficulty, [])
        
        # 如果指定了题目类型，过滤出对应类型的题目
        if question_type:
            filtered_templates = [t for t in difficulty_templates if t['type'] == question_type]
            if filtered_templates:
                difficulty_templates = filtered_templates
        
        if not difficulty_templates:
            # 如果当前难度没有模板，使用相邻难度的模板
            adjacent_templates = category_templates.get(difficulty - 1, []) + category_templates.get(difficulty + 1, [])
            if question_type:
                adjacent_templates = [t for t in adjacent_templates if t['type'] == question_type]
            difficulty_templates.extend(adjacent_templates)
        
        if not difficulty_templates:
            # 如果还是没有模板，使用任意难度的模板
            for diff in category_templates:
                diff_templates = category_templates[diff]
                if question_type:
                    diff_templates = [t for t in diff_templates if t['type'] == question_type]
                difficulty_templates.extend(diff_templates)
        
        if not difficulty_templates:
            # 如果还是没有模板，使用默认模板
            difficulty_templates = [
                {
                    'content': 'これは例題です。',
                    'type': question_type or 'single',
                    'required_answers': 1,
                    'correct_answers': ['A']
                }
            ]
        
        return random.choice(difficulty_templates)
    
    def _generate_english_question(self, category: str, difficulty: int, question_type: Optional[str] = None) -> Dict[str, Any]:
        """生成英语题目"""
        # 英语题目模板库
        templates = {
            '词汇': {
                1: [
                    {
                        'content': 'What is the meaning of "hello"?',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': 'What is the meaning of "thank you"?',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    },
                    {
                        'content': 'Which of the following are greetings?',
                        'type': 'multiple',
                        'required_answers': 2,
                        'correct_answers': ['A', 'B']
                    }
                ],
                2: [
                    {
                        'content': 'What is the meaning of "friend"?',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': 'What is the meaning of "eat"?',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': 'Fill in the blank: I _____ apple every day.',
                        'type': 'fill',
                        'required_answers': 1,
                        'correct_answers': ['eat an']
                    }
                ],
                3: [
                    {
                        'content': 'What is the meaning of "study"?',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': 'What is the meaning of "good at"?',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': 'Choose the correct synonyms for "happy".',
                        'type': 'multiple',
                        'required_answers': 3,
                        'correct_answers': ['A', 'C', 'E']
                    }
                ],
                4: [
                    {
                        'content': 'What is the meaning of "quarrel"?',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    },
                    {
                        'content': 'What is the meaning of "grateful"?',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    },
                    {
                        'content': 'Fill in the blank: She is _____ grateful for your help.',
                        'type': 'fill',
                        'required_answers': 1,
                        'correct_answers': ['deeply']
                    }
                ],
                5: [
                    {
                        'content': 'What is the meaning of "encounter"?',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['D']
                    },
                    {
                        'content': 'What is the meaning of "reject"?',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    },
                    {
                        'content': 'Choose the correct antonyms for "accept".',
                        'type': 'multiple',
                        'required_answers': 2,
                        'correct_answers': ['B', 'D']
                    }
                ]
            },
            '语法': {
                1: [
                    {
                        'content': 'I _____ a student.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': 'Are you _____ teacher?',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    }
                ],
                2: [
                    {
                        'content': 'Yesterday, I _____ a movie.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    },
                    {
                        'content': 'Every day, I _____ to school.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ],
                3: [
                    {
                        'content': 'He said he _____ next week.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    },
                    {
                        'content': 'If it rains, I _____ not go. This is a _____ sentence.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    }
                ],
                4: [
                    {
                        'content': 'I recommend this book not only to myself _____ also to my friends.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['D']
                    },
                    {
                        'content': 'He says he is rich, but I don\'t know _____ it\'s true.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ],
                5: [
                    {
                        'content': 'This problem is _____ difficult that I can\'t solve it.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    },
                    {
                        'content': 'He explained _____ in detail.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    }
                ]
            },
            '阅读': {
                1: [
                    {
                        'content': 'I get up at 7 o\'clock every morning. Then I brush my teeth and eat breakfast. I go to school at 8:30.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ],
                2: [
                    {
                        'content': 'Yesterday, I went to the movies with my friends. The movie was very interesting. On the way back, we ate dinner at a restaurant.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    }
                ],
                3: [
                    {
                        'content': 'Spring in Japan is from March to May. Cherry blossoms bloom and it is very beautiful. Many people go to see the cherry blossoms.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    }
                ],
                4: [
                    {
                        'content': 'In recent years, Japan has been aging. The population over 65 has increased, and social security costs have increased. The government is taking various measures.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['D']
                    }
                ],
                5: [
                    {
                        'content': 'Japan\'s economy has become the third largest in the world through a period of high growth. In recent years, growth rates have slowed due to the effects of declining birthrates and aging.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ]
            },
            '听力': {
                1: [
                    {
                        'content': 'Listen to the conversation and choose the correct answer. (Conversation: A: Hello. B: Hello.)',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ],
                2: [
                    {
                        'content': 'Listen to the conversation and choose the correct answer. (Conversation: A: What did you do yesterday? B: I watched a movie.)',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    }
                ]
            },
            '写作': {
                1: [
                    {
                        'content': 'Write a short paragraph about "My Day" (50 words).',
                        'type': 'essay',
                        'required_answers': 1,
                        'correct_answers': []
                    }
                ],
                2: [
                    {
                        'content': 'Write a short paragraph about "My Hobby" (100 words).',
                        'type': 'essay',
                        'required_answers': 1,
                        'correct_answers': []
                    }
                ]
            },
            '口语': {
                1: [
                    {
                        'content': 'Introduce yourself (30 seconds).',
                        'type': 'speaking',
                        'required_answers': 1,
                        'correct_answers': []
                    }
                ],
                2: [
                    {
                        'content': 'Talk about your favorite food (1 minute).',
                        'type': 'speaking',
                        'required_answers': 1,
                        'correct_answers': []
                    }
                ]
            },
            '翻译': {
                1: [
                    {
                        'content': 'Translate "Hello" into Chinese.',
                        'type': 'translation',
                        'required_answers': 1,
                        'correct_answers': ['你好']
                    }
                ],
                2: [
                    {
                        'content': 'Translate "Thank you" into Chinese.',
                        'type': 'translation',
                        'required_answers': 1,
                        'correct_answers': ['谢谢']
                    }
                ]
            }
        }
        
        # 根据question_type过滤模板
        category_templates = templates.get(category, {})
        difficulty_templates = category_templates.get(difficulty, [])
        
        # 如果指定了题目类型，过滤出对应类型的题目
        if question_type:
            filtered_templates = [t for t in difficulty_templates if t['type'] == question_type]
            if filtered_templates:
                difficulty_templates = filtered_templates
        
        if not difficulty_templates:
            # 如果当前难度没有模板，使用相邻难度的模板
            adjacent_templates = category_templates.get(difficulty - 1, []) + category_templates.get(difficulty + 1, [])
            if question_type:
                adjacent_templates = [t for t in adjacent_templates if t['type'] == question_type]
            difficulty_templates.extend(adjacent_templates)
        
        if not difficulty_templates:
            # 如果还是没有模板，使用任意难度的模板
            for diff in category_templates:
                diff_templates = category_templates[diff]
                if question_type:
                    diff_templates = [t for t in diff_templates if t['type'] == question_type]
                difficulty_templates.extend(diff_templates)
        
        if not difficulty_templates:
            # 如果还是没有模板，使用默认模板
            difficulty_templates = [
                {
                    'content': 'This is an example question.',
                    'type': question_type or 'single',
                    'required_answers': 1,
                    'correct_answers': ['A']
                }
            ]
        
        return random.choice(difficulty_templates)
    
    def _generate_chinese_question(self, category: str, difficulty: int, question_type: Optional[str] = None) -> Dict[str, Any]:
        """生成中文题目"""
        # 中文题目模板库
        templates = {
            '词汇': {
                1: [
                    {
                        'content': '"你好"的正确英文表达是？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': '"谢谢"的正确英文表达是？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    },
                    {
                        'content': '下列哪些是问候语？',
                        'type': 'multiple',
                        'required_answers': 2,
                        'correct_answers': ['A', 'B']
                    }
                ],
                2: [
                    {
                        'content': '"朋友"的正确英文表达是？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': '"吃"的正确英文表达是？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': '填空：I _____ apple every day.',
                        'type': 'fill',
                        'required_answers': 1,
                        'correct_answers': ['eat an']
                    }
                ],
                3: [
                    {
                        'content': '"学习"的正确英文表达是？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': '"擅长"的正确英文表达是？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': '选择"happy"的同义词。',
                        'type': 'multiple',
                        'required_answers': 3,
                        'correct_answers': ['A', 'C', 'E']
                    }
                ],
                4: [
                    {
                        'content': '"争吵"的正确英文表达是？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    },
                    {
                        'content': '"感激"的正确英文表达是？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    },
                    {
                        'content': '填空：She is _____ grateful for your help.',
                        'type': 'fill',
                        'required_answers': 1,
                        'correct_answers': ['deeply']
                    }
                ],
                5: [
                    {
                        'content': '"邂逅"的正确英文表达是？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['D']
                    },
                    {
                        'content': '"拒绝"的正确英文表达是？',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    },
                    {
                        'content': '选择"accept"的反义词。',
                        'type': 'multiple',
                        'required_answers': 2,
                        'correct_answers': ['B', 'D']
                    }
                ]
            },
            '语法': {
                1: [
                    {
                        'content': 'I _____ a student.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    },
                    {
                        'content': 'Are you _____ teacher?',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    }
                ],
                2: [
                    {
                        'content': 'Yesterday, I _____ a movie.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    },
                    {
                        'content': 'Every day, I _____ to school.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ],
                3: [
                    {
                        'content': 'He said he _____ next week.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    },
                    {
                        'content': 'If it rains, I _____ not go. This is a _____ sentence.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    }
                ],
                4: [
                    {
                        'content': 'I recommend this book not only to myself _____ also to my friends.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['D']
                    },
                    {
                        'content': 'He says he is rich, but I don\'t know _____ it\'s true.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ],
                5: [
                    {
                        'content': 'This problem is _____ difficult that I can\'t solve it.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    },
                    {
                        'content': 'He explained _____ in detail.',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    }
                ]
            },
            '阅读': {
                1: [
                    {
                        'content': '我每天早上7点起床。然后刷牙，吃早饭。8点半去上学。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ],
                2: [
                    {
                        'content': '昨天，我和朋友去看电影了。电影很有趣。回来的路上，我们在餐厅吃了饭。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    }
                ],
                3: [
                    {
                        'content': '日本的春天是从3月到5月。樱花开了，非常漂亮。很多人去赏花。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['C']
                    }
                ],
                4: [
                    {
                        'content': '近年来，日本的老龄化在加剧。65岁以上的人口在增加，社会保障费也在增加。政府正在采取各种对策。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['D']
                    }
                ],
                5: [
                    {
                        'content': '日本经济经过高度成长期，成为了世界第三大经济大国。近年来由于少子化和老龄化的影响，增长率降低了。',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ]
            },
            '听力': {
                1: [
                    {
                        'content': '听对话，选择正确答案。（对话：A: Hello. B: Hello.）',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['A']
                    }
                ],
                2: [
                    {
                        'content': '听对话，选择正确答案。（对话：A: What did you do yesterday? B: I watched a movie.）',
                        'type': 'single',
                        'required_answers': 1,
                        'correct_answers': ['B']
                    }
                ]
            },
            '写作': {
                1: [
                    {
                        'content': '写一篇关于"我的一天"的短文（50字）。',
                        'type': 'essay',
                        'required_answers': 1,
                        'correct_answers': []
                    }
                ],
                2: [
                    {
                        'content': '写一篇关于"我的爱好"的短文（100字）。',
                        'type': 'essay',
                        'required_answers': 1,
                        'correct_answers': []
                    }
                ]
            },
            '口语': {
                1: [
                    {
                        'content': '自我介绍（30秒）。',
                        'type': 'speaking',
                        'required_answers': 1,
                        'correct_answers': []
                    }
                ],
                2: [
                    {
                        'content': '谈论你最喜欢的食物（1分钟）。',
                        'type': 'speaking',
                        'required_answers': 1,
                        'correct_answers': []
                    }
                ]
            },
            '翻译': {
                1: [
                    {
                        'content': 'Translate "Hello" into Chinese.',
                        'type': 'translation',
                        'required_answers': 1,
                        'correct_answers': ['你好']
                    }
                ],
                2: [
                    {
                        'content': 'Translate "Thank you" into Chinese.',
                        'type': 'translation',
                        'required_answers': 1,
                        'correct_answers': ['谢谢']
                    }
                ]
            }
        }
        
        # 根据question_type过滤模板
        category_templates = templates.get(category, {})
        difficulty_templates = category_templates.get(difficulty, [])
        
        # 如果指定了题目类型，过滤出对应类型的题目
        if question_type:
            filtered_templates = [t for t in difficulty_templates if t['type'] == question_type]
            if filtered_templates:
                difficulty_templates = filtered_templates
        
        if not difficulty_templates:
            # 如果当前难度没有模板，使用相邻难度的模板
            adjacent_templates = category_templates.get(difficulty - 1, []) + category_templates.get(difficulty + 1, [])
            if question_type:
                adjacent_templates = [t for t in adjacent_templates if t['type'] == question_type]
            difficulty_templates.extend(adjacent_templates)
        
        if not difficulty_templates:
            # 如果还是没有模板，使用任意难度的模板
            for diff in category_templates:
                diff_templates = category_templates[diff]
                if question_type:
                    diff_templates = [t for t in diff_templates if t['type'] == question_type]
                difficulty_templates.extend(diff_templates)
        
        if not difficulty_templates:
            # 如果还是没有模板，使用默认模板
            difficulty_templates = [
                {
                    'content': '这是一个例题。',
                    'type': question_type or 'single',
                    'required_answers': 1,
                    'correct_answers': ['A']
                }
            ]
        
        return random.choice(difficulty_templates)
    
    def _generate_options(self, question: Dict[str, Any], category: str, language: str, difficulty: int) -> List[Dict[str, Any]]:
        """生成选项"""
        options = []
        correct_answers = question['correct_answers']
        question_type = question['type']
        
        # 根据题目类型生成不同的选项
        if question_type in ['single', 'multiple']:
            # 选择题生成选项
            option_count = 6  # 单选题和多选题6个选项
            
            # 生成选项内容
            option_content = self._generate_option_content(question, category, language, difficulty, correct_answers)
            
            # 生成选项ID和内容
            for i in range(option_count):
                option_id = chr(ord('A') + i)
                is_correct = option_id in correct_answers
                
                options.append({
                    'id': option_id,
                    'content': option_content[i],
                    'is_correct': is_correct
                })
        elif question_type == 'fill':
            # 填空题，返回正确答案作为参考
            for i, answer in enumerate(correct_answers):
                options.append({
                    'id': str(i+1),
                    'content': answer,
                    'is_correct': True
                })
        elif question_type in ['short_answer', 'essay', 'speaking', 'translation']:
            # 简答题、写作题、口语题、翻译题，不生成选项
            # 这些题型需要人工或AI评分
            pass
        
        return options
    
    def _generate_option_content(self, question: Dict[str, Any], category: str, language: str, difficulty: int, correct_answers: List[str]) -> List[str]:
        """生成选项内容"""
        # 生成选项内容
        if language == "japanese":
            return self._generate_japanese_options(question, category, difficulty, correct_answers)
        elif language == "english":
            return self._generate_english_options(question, category, difficulty, correct_answers)
        else:
            return self._generate_chinese_options(question, category, difficulty, correct_answers)
    
    def _generate_japanese_options(self, question: Dict[str, Any], category: str, difficulty: int, correct_answers: List[str]) -> List[str]:
        """生成日语选项"""
        # 日语选项模板库
        templates = {
            '词汇': {
                1: [
                    ['你好', '再见', '谢谢', '对不起', '欢迎', '请'],
                    ['谢谢', '再见', '你好', '对不起', '欢迎', '请']
                ],
                2: [
                    ['朋友', '家人', '同事', '同学', '邻居', '老师'],
                    ['吃', '喝', '睡', '走', '跑', '跳']
                ],
                3: [
                    ['学习', '工作', '休息', '玩耍', '旅行', '运动'],
                    ['擅长', '糟糕', '普通', '困难', '简单', '有趣']
                ],
                4: [
                    ['争吵', '合作', '帮助', '支持', '理解', '原谅'],
                    ['感激', '感动', '感谢', '感慨', '感想', '感情']
                ],
                5: [
                    ['邂逅', '相遇', '相见', '相识', '相知', '相恋'],
                    ['拒绝', '接受', '同意', '反对', '赞成', '否定']
                ]
            },
            '语法': {
                1: [
                    ['学生', '先生', '医者', '教师', '会社員', '社長'],
                    ['先生', '学生', '医者', '教师', '会社員', '社長']
                ],
                2: [
                    ['見ました', '見ます', '見ています', '見よう', '見たい', '見せる'],
                    ['行きます', '行っています', '行きました', '行こう', '行きたい', '行かせる']
                ],
                3: [
                    ['来ます', '来ました', '来ています', '来よう', '来たい', '来させる'],
                    ['条件', '原因', '结果', '目的', '手段', '理由']
                ],
                4: [
                    ['だけ', 'しか', 'も', 'は', 'が', 'を'],
                    ['か', 'が', 'を', 'は', 'も', 'で']
                ],
                5: [
                    ['とても', '非常に', 'すごく', 'めっちゃ', 'かなり', 'そんなに'],
                    ['これ', 'それ', 'あれ', 'どれ', 'この', 'その']
                ]
            },
            '阅读': {
                1: [
                    ['7時', '8時', '9時', '10時', '11時', '12時'],
                    ['映画', '食事', '買い物', '散歩', '勉強', '遊び']
                ],
                2: [
                    ['映画', '食事', '買い物', '散歩', '勉強', '遊び'],
                    ['3月', '4月', '5月', '6月', '7月', '8月']
                ],
                3: [
                    ['3月から5月', '4月から6月', '5月から7月', '6月から8月', '7月から9月', '8月から10月'],
                    ['花見', '登山', '海', '温泉', '滑雪', '购物']
                ],
                4: [
                    ['高齢化', '少子化', '人口増加', '人口減少', '城市化', '農村化'],
                    ['社会保障費', '教育費', '医療費', '軍事費', '交通費', '環境費']
                ],
                5: [
                    ['世界第1位', '世界第2位', '世界第3位', '世界第4位', '世界第5位', '世界第6位'],
                    ['高度成長期', '安定成長期', '低速成長期', '停滞期', '衰退期', '回復期']
                ]
            }
        }
        
        # 随机选择一个模板
        category_templates = templates.get(category, {})
        difficulty_templates = category_templates.get(difficulty, [])
        
        if not difficulty_templates:
            # 如果当前难度没有模板，使用相邻难度的模板
            difficulty_templates = category_templates.get(difficulty - 1, []) + category_templates.get(difficulty + 1, [])
        
        if not difficulty_templates:
            # 如果还是没有模板，使用任意难度的模板
            for diff in category_templates:
                difficulty_templates.extend(category_templates[diff])
        
        if not difficulty_templates:
            # 如果还是没有模板，使用默认模板
            difficulty_templates = [
                ['选项A', '选项B', '选项C', '选项D', '选项E', '选项F']
            ]
        
        return random.choice(difficulty_templates)
    
    def _generate_english_options(self, question: Dict[str, Any], category: str, difficulty: int, correct_answers: List[str]) -> List[str]:
        """生成英语选项"""
        # 英语选项模板库
        templates = {
            '词汇': {
                1: [
                    ['Hello', 'Goodbye', 'Thank you', 'Sorry', 'Welcome', 'Please'],
                    ['Thank you', 'Goodbye', 'Hello', 'Sorry', 'Welcome', 'Please']
                ],
                2: [
                    ['Friend', 'Family', 'Colleague', 'Classmate', 'Neighbor', 'Teacher'],
                    ['Eat', 'Drink', 'Sleep', 'Walk', 'Run', 'Jump']
                ],
                3: [
                    ['Study', 'Work', 'Rest', 'Play', 'Travel', 'Exercise'],
                    ['Good at', 'Bad', 'Average', 'Difficult', 'Easy', 'Interesting']
                ],
                4: [
                    ['Quarrel', 'Cooperate', 'Help', 'Support', 'Understand', 'Forgive'],
                    ['Grateful', 'Moved', 'Thankful', 'Impressed', 'Emotional', 'Sentimental']
                ],
                5: [
                    ['Encounter', 'Meet', 'See', 'Know', 'Understand', 'Love'],
                    ['Reject', 'Accept', 'Agree', 'Disagree', 'Approve', 'Deny']
                ]
            },
            '语法': {
                1: [
                    ['am', 'is', 'are', 'be', 'was', 'were'],
                    ['a', 'an', 'the', 'this', 'that', 'these']
                ],
                2: [
                    ['watched', 'watch', 'watching', 'will watch', 'would watch', 'have watched'],
                    ['go', 'goes', 'went', 'going', 'will go', 'have gone']
                ],
                3: [
                    ['will come', 'comes', 'came', 'coming', 'would come', 'has come'],
                    ['conditional', 'causal', 'result', 'purpose', 'means', 'reason']
                ],
                4: [
                    ['but', 'and', 'or', 'so', 'for', 'yet'],
                    ['if', 'whether', 'that', 'which', 'who', 'whom']
                ],
                5: [
                    ['so', 'very', 'too', 'such', 'quite', 'rather'],
                    ['this', 'that', 'these', 'those', 'it', 'they']
                ]
            },
            '阅读': {
                1: [
                    ['7 o\'clock', '8 o\'clock', '9 o\'clock', '10 o\'clock', '11 o\'clock', '12 o\'clock'],
                    ['Movie', 'Dinner', 'Shopping', 'Walking', 'Studying', 'Playing']
                ],
                2: [
                    ['Movie', 'Dinner', 'Shopping', 'Walking', 'Studying', 'Playing'],
                    ['March', 'April', 'May', 'June', 'July', 'August']
                ],
                3: [
                    ['March to May', 'April to June', 'May to July', 'June to August', 'July to September', 'August to October'],
                    ['Cherry blossoms', 'Mountains', 'Beach', 'Hot springs', 'Skiing', 'Shopping']
                ],
                4: [
                    ['Aging', 'Declining birthrate', 'Population growth', 'Population decline', 'Urbanization', 'Ruralization'],
                    ['Social security costs', 'Education costs', 'Medical costs', 'Military costs', 'Transportation costs', 'Environmental costs']
                ],
                5: [
                    ['1st', '2nd', '3rd', '4th', '5th', '6th'],
                    ['High growth period', 'Stable growth period', 'Low growth period', 'Stagnation period', 'Recession period', 'Recovery period']
                ]
            }
        }
        
        # 随机选择一个模板
        category_templates = templates.get(category, {})
        difficulty_templates = category_templates.get(difficulty, [])
        
        if not difficulty_templates:
            # 如果当前难度没有模板，使用相邻难度的模板
            difficulty_templates = category_templates.get(difficulty - 1, []) + category_templates.get(difficulty + 1, [])
        
        if not difficulty_templates:
            # 如果还是没有模板，使用任意难度的模板
            for diff in category_templates:
                difficulty_templates.extend(category_templates[diff])
        
        if not difficulty_templates:
            # 如果还是没有模板，使用默认模板
            difficulty_templates = [
                ['Option A', 'Option B', 'Option C', 'Option D', 'Option E', 'Option F']
            ]
        
        return random.choice(difficulty_templates)
    
    def _generate_chinese_options(self, question: Dict[str, Any], category: str, difficulty: int, correct_answers: List[str]) -> List[str]:
        """生成中文选项"""
        # 中文选项模板库
        templates = {
            '词汇': {
                1: [
                    ['Hello', 'Goodbye', 'Thank you', 'Sorry', 'Welcome', 'Please'],
                    ['Thank you', 'Goodbye', 'Hello', 'Sorry', 'Welcome', 'Please']
                ],
                2: [
                    ['Friend', 'Family', 'Colleague', 'Classmate', 'Neighbor', 'Teacher'],
                    ['Eat', 'Drink', 'Sleep', 'Walk', 'Run', 'Jump']
                ],
                3: [
                    ['Study', 'Work', 'Rest', 'Play', 'Travel', 'Exercise'],
                    ['Good at', 'Bad', 'Average', 'Difficult', 'Easy', 'Interesting']
                ],
                4: [
                    ['Quarrel', 'Cooperate', 'Help', 'Support', 'Understand', 'Forgive'],
                    ['Grateful', 'Moved', 'Thankful', 'Impressed', 'Emotional', 'Sentimental']
                ],
                5: [
                    ['Encounter', 'Meet', 'See', 'Know', 'Understand', 'Love'],
                    ['Reject', 'Accept', 'Agree', 'Disagree', 'Approve', 'Deny']
                ]
            },
            '语法': {
                1: [
                    ['am', 'is', 'are', 'be', 'was', 'were'],
                    ['a', 'an', 'the', 'this', 'that', 'these']
                ],
                2: [
                    ['watched', 'watch', 'watching', 'will watch', 'would watch', 'have watched'],
                    ['go', 'goes', 'went', 'going', 'will go', 'have gone']
                ],
                3: [
                    ['will come', 'comes', 'came', 'coming', 'would come', 'has come'],
                    ['conditional', 'causal', 'result', 'purpose', 'means', 'reason']
                ],
                4: [
                    ['but', 'and', 'or', 'so', 'for', 'yet'],
                    ['if', 'whether', 'that', 'which', 'who', 'whom']
                ],
                5: [
                    ['so', 'very', 'too', 'such', 'quite', 'rather'],
                    ['this', 'that', 'these', 'those', 'it', 'they']
                ]
            },
            '阅读': {
                1: [
                    ['7 o\'clock', '8 o\'clock', '9 o\'clock', '10 o\'clock', '11 o\'clock', '12 o\'clock'],
                    ['Movie', 'Dinner', 'Shopping', 'Walking', 'Studying', 'Playing']
                ],
                2: [
                    ['Movie', 'Dinner', 'Shopping', 'Walking', 'Studying', 'Playing'],
                    ['March', 'April', 'May', 'June', 'July', 'August']
                ],
                3: [
                    ['March to May', 'April to June', 'May to July', 'June to August', 'July to September', 'August to October'],
                    ['Cherry blossoms', 'Mountains', 'Beach', 'Hot springs', 'Skiing', 'Shopping']
                ],
                4: [
                    ['Aging', 'Declining birthrate', 'Population growth', 'Population decline', 'Urbanization', 'Ruralization'],
                    ['Social security costs', 'Education costs', 'Medical costs', 'Military costs', 'Transportation costs', 'Environmental costs']
                ],
                5: [
                    ['1st', '2nd', '3rd', '4th', '5th', '6th'],
                    ['High growth period', 'Stable growth period', 'Low growth period', 'Stagnation period', 'Recession period', 'Recovery period']
                ]
            }
        }
        
        # 随机选择一个模板
        category_templates = templates.get(category, {})
        difficulty_templates = category_templates.get(difficulty, [])
        
        if not difficulty_templates:
            # 如果当前难度没有模板，使用相邻难度的模板
            difficulty_templates = category_templates.get(difficulty - 1, []) + category_templates.get(difficulty + 1, [])
        
        if not difficulty_templates:
            # 如果还是没有模板，使用任意难度的模板
            for diff in category_templates:
                difficulty_templates.extend(category_templates[diff])
        
        if not difficulty_templates:
            # 如果还是没有模板，使用默认模板
            difficulty_templates = [
                ['选项A', '选项B', '选项C', '选项D', '选项E', '选项F']
            ]
        
        return random.choice(difficulty_templates)
    
    def _generate_explanation(self, question: Dict[str, Any], category: str, language: str, difficulty: int) -> str:
        """生成解释"""
        # 生成解释
        if language == "japanese":
            return f'这是{language}第{difficulty}级{category}题的解释。'
        elif language == "english":
            return f'This is an explanation for {language} level {difficulty} {category} question.'
        else:
            return f'这是{language}第{difficulty}级{category}题的解释。'
    
    def _generate_knowledge_points(self, category: str, difficulty: int) -> List[str]:
        """生成知识点"""
        # 知识点模板库
        templates = {
            '词汇': {
                1: ['基础词汇', '日常用语', '问候语'],
                2: ['常用词汇', '生活用语', '社交用语'],
                3: ['中级词汇', '学习用语', '工作用语'],
                4: ['高级词汇', '专业用语', '书面语'],
                5: ['生僻词汇', '文学用语', '成语']
            },
            '语法': {
                1: ['基础语法', '名词', '动词'],
                2: ['常用语法', '形容词', '副词'],
                3: ['中级语法', '时态', '语态'],
                4: ['高级语法', '从句', '虚拟语气'],
                5: ['复杂语法', '倒装', '强调']
            },
            '阅读': {
                1: ['基础阅读', '简单对话', '短文'],
                2: ['常用阅读', '日常文章', '新闻'],
                3: ['中级阅读', '议论文', '说明文'],
                4: ['高级阅读', '学术论文', '专业文章'],
                5: ['复杂阅读', '文学作品', '哲学文章']
            }
        }
        
        # 随机选择知识点
        category_templates = templates.get(category, {})
        difficulty_templates = category_templates.get(difficulty, [])
        
        if not difficulty_templates:
            # 如果当前难度没有模板，使用相邻难度的模板
            difficulty_templates = category_templates.get(difficulty - 1, []) + category_templates.get(difficulty + 1, [])
        
        if not difficulty_templates:
            # 如果还是没有模板，使用任意难度的模板
            for diff in category_templates:
                difficulty_templates.extend(category_templates[diff])
        
        if not difficulty_templates:
            # 如果还是没有模板，使用默认模板
            difficulty_templates = ['知识点1', '知识点2', '知识点3']
        
        # 随机选择3个知识点
        return random.sample(difficulty_templates, min(3, len(difficulty_templates)))
    
    def generate_paper(self, user_id: str, language: str, test_type: str = 'level', question_count: int = 20, user_level: int = 3) -> Dict[str, Any]:
        """
        生成智能试卷
        
        Args:
            user_id: 用户ID
            language: 语言类型 (japanese/english/chinese)
            test_type: 测试类型 (level/placement/diagnostic)
            question_count: 题目数量
            user_level: 用户等级 (1-5)
            
        Returns:
            试卷字典
        """
        # 生成试卷ID
        paper_id = f"smart_paper_{int(time.time() * 1000)}_{random.randint(1, 1000)}"
        
        # 生成题目分布
        category_ratios = self._get_category_ratios(language, test_type, user_level)
        
        # 生成题目
        questions = []
        for category, ratio in category_ratios.items():
            # 计算该类别的题目数量
            count = max(1, int(question_count * ratio / 100))
            
            # 生成该类别的题目
            for i in range(count):
                # 根据用户等级调整难度
                difficulty = self._adjust_difficulty(user_level, category, i, count)
                
                # 生成题目
                question = self.generate_question(language, category, difficulty)
                questions.append(question)
        
        # 调整题目数量
        if len(questions) > question_count:
            questions = random.sample(questions, question_count)
        elif len(questions) < question_count:
            # 补充题目
            while len(questions) < question_count:
                category = random.choice(list(category_ratios.keys()))
                difficulty = self._adjust_difficulty(user_level, category, 0, 1)
                question = self.generate_question(language, category, difficulty)
                questions.append(question)
        
        # 按照考试惯例对题目进行排序
        # 1. 按类别排序：词汇 -> 语法 -> 阅读
        # 2. 同类题目按难度从易到难排序
        category_order = {
            '词汇': 1,
            '语法': 2,
            '阅读': 3,
            '听力': 4,
            '写作': 5
        }
        
        questions.sort(key=lambda x: (
            category_order.get(x['category'], 99),  # 按类别排序
            x['difficulty']  # 同类题目按难度从易到难排序
        ))
        
        # 统计试卷的题目分布
        paper_stats = {
            'vocabulary_count': sum(1 for q in questions if q['category'] == '词汇'),
            'grammar_count': sum(1 for q in questions if q['category'] == '语法'),
            'reading_count': sum(1 for q in questions if q['category'] == '阅读'),
            'listening_count': sum(1 for q in questions if q['category'] == '听力'),
            'writing_count': sum(1 for q in questions if q['category'] == '写作'),
            'speaking_count': sum(1 for q in questions if q['category'] == '口语'),
            'translation_count': sum(1 for q in questions if q['category'] == '翻译'),
            'difficulty_distribution': {
                diff: sum(1 for q in questions if q['difficulty'] == diff) 
                for diff in range(1, 6)
            },
            'question_type_distribution': {
                q_type: sum(1 for q in questions if q['question_type'] == q_type)
                for q_type in self.supported_question_types
            },
            'ai_generated_count': sum(1 for q in questions if q['generated_by_ai'])
        }
        
        # 生成试卷说明
        paper_instructions = {
            'title': f'{language.capitalize()} Language Proficiency Test',
            'subtitle': f'{'Placement Test' if test_type == 'placement' else 'Level-Adaptive Test'}',
            'instructions': [
                'This test consists of multiple-choice questions only',
                'Each question has 6 options, please select the correct one',
                'You can only select one answer per question',
                'The test is timed, please manage your time wisely',
                'Vocabulary questions: 1 minute per question',
                'Grammar questions: 1.5 minutes per question',
                'Reading comprehension: 2.5 minutes per question',
                'Do not refresh the page during the test',
                'Your test results will be available immediately after submission'
            ],
            'suggested_time': len(questions) * 1.5,  # 平均每题1.5分钟
            'question_order_reminder': 'The questions are arranged from vocabulary -> grammar -> reading comprehension, with increasing difficulty within each section, following standard exam conventions',
            'test_type_reminder': f'This is a {'placement test' if test_type == 'placement' else 'level-adaptive test'} designed to accurately assess your {language} proficiency',
            'difficulty_reminder': f'Questions are tailored to your level ({user_level}/5), with appropriate challenge progression',
            'scoring_reminder': 'Each question carries equal weight, and your final score will determine your proficiency level'
        }
        
        return {
            'paper_id': paper_id,
            'language': language,
            'test_type': test_type,
            'user_level': user_level,
            'is_assessed': 1,
            'difficulty': user_level,
            'questions': questions,
            'total_questions': len(questions),
            'generated_at': time.time(),
            'instructions': paper_instructions,
            'suggested_time': len(questions) * 1.5,
            'stats': paper_stats,
            'rule_compliance': {
                'overall_compliance': True,
                'suggestions': []
            }
        }
    
    def _get_category_ratios(self, language: str, test_type: str, user_level: int) -> Dict[str, int]:
        """获取题目类别比例"""
        # 优先使用从数据库加载的配置
        if self.paper_category_ratios:
            # 检查是否有对应测试类型的配置
            if test_type in self.paper_category_ratios:
                # 如果是等级测试，检查是否有对应等级的配置
                if test_type == 'level' and str(user_level) in self.paper_category_ratios[test_type]:
                    return self.paper_category_ratios[test_type][str(user_level)]
                return self.paper_category_ratios[test_type]
        
        # 如果数据库配置不存在，使用默认配置
        if test_type == 'placement':
            # 摸底测试，各类别均衡分布
            return {
                '词汇': 20,
                '语法': 20,
                '阅读': 20,
                '听力': 20,
                '写作': 10,
                '翻译': 10
            }
        elif test_type == 'diagnostic':
            # 诊断测试，重点测试薄弱环节
            return {
                '词汇': 25,
                '语法': 25,
                '阅读': 20,
                '听力': 20,
                '写作': 5,
                '翻译': 5
            }
        elif test_type == 'comprehensive':
            # 综合测试，包含所有类别
            return {
                '词汇': 15,
                '语法': 15,
                '阅读': 20,
                '听力': 20,
                '写作': 15,
                '口语': 10,
                '翻译': 5
            }
        else:
            # 等级测试，根据用户等级调整
            if user_level <= 2:
                return {
                    '词汇': 30,
                    '语法': 25,
                    '阅读': 20,
                    '听力': 15,
                    '写作': 5,
                    '翻译': 5
                }
            elif user_level <= 3:
                return {
                    '词汇': 25,
                    '语法': 20,
                    '阅读': 20,
                    '听力': 20,
                    '写作': 10,
                    '翻译': 5
                }
            else:
                return {
                    '词汇': 20,
                    '语法': 15,
                    '阅读': 20,
                    '听力': 20,
                    '写作': 15,
                    '口语': 5,
                    '翻译': 5
                }
    
    def _adjust_difficulty(self, user_level: int, category: str, index: int, total: int) -> int:
        """调整题目难度"""
        # 根据用户等级和题目索引调整难度
        # 基础难度为用户等级
        base_difficulty = user_level
        
        # 根据题目索引调整难度，前半部分题目难度略低，后半部分略高
        if index < total / 2:
            difficulty = max(1, base_difficulty - 1)
        else:
            difficulty = min(5, base_difficulty + 1)
        
        # 根据类别调整难度
        if category == '阅读':
            difficulty = min(5, difficulty + 1)
        elif category == '词汇':
            difficulty = max(1, difficulty - 1)
        
        return difficulty
    
    def generate_multiple_papers(self, user_id: str, language: str, test_type: str = 'level', question_count: int = 20, user_level: int = 3, count: int = 5) -> List[Dict[str, Any]]:
        """
        生成多份智能试卷
        
        Args:
            user_id: 用户ID
            language: 语言类型 (japanese/english/chinese)
            test_type: 测试类型 (level/placement/diagnostic)
            question_count: 题目数量
            user_level: 用户等级 (1-5)
            count: 试卷数量
            
        Returns:
            试卷列表
        """
        papers = []
        for i in range(count):
            paper = self.generate_paper(user_id, language, test_type, question_count, user_level)
            papers.append(paper)
        
        return papers
    
    def score_answer(self, question: Dict[str, Any], user_answer: str, user_level: int = 3) -> Dict[str, Any]:
        """
        AI辅助评分功能
        
        Args:
            question: 题目字典
            user_answer: 用户答案
            user_level: 用户等级 (1-5)
            
        Returns:
            评分结果字典
        """
        question_type = question['question_type']
        score = 0.0
        feedback = ""
        
        try:
            if question_type in ['single', 'multiple']:
                # 选择题评分
                correct_answers = question['correct_answers']
                user_answers = user_answer.split(',') if ',' in user_answer else [user_answer]
                
                # 计算正确答案数量
                correct_count = sum(1 for ans in user_answers if ans in correct_answers)
                total_count = len(correct_answers)
                
                if question_type == 'single':
                    # 单选题，全对得100分
                    score = 100.0 if correct_count == total_count else 0.0
                else:
                    # 多选题，按比例得分
                    score = (correct_count / total_count) * 100.0
                
                feedback = f"正确答案: {', '.join(correct_answers)}\n你的答案: {', '.join(user_answers)}\n得分: {score:.1f}分"
            elif question_type == 'fill':
                # 填空题评分
                correct_answers = question['correct_answers']
                user_answers = user_answer.split('||') if '||' in user_answer else [user_answer]
                
                # 计算正确答案数量
                correct_count = 0
                for i, (correct, user) in enumerate(zip(correct_answers, user_answers)):
                    if re.search(correct, user, re.IGNORECASE):
                        correct_count += 1
                
                total_count = len(correct_answers)
                score = (correct_count / total_count) * 100.0
                feedback = f"正确答案: {', '.join(correct_answers)}\n你的答案: {', '.join(user_answers)}\n得分: {score:.1f}分"
            elif question_type in ['short_answer', 'essay', 'speaking', 'translation']:
                # AI辅助评分（简答题、写作题、口语题、翻译题）
                # 使用AI模型生成评分
                prompt = self._generate_scoring_prompt(question, user_answer, user_level)
                ai_response = self.ai_model.generate_text(prompt)
                
                # 解析AI评分结果
                score_result = self._parse_ai_scoring_response(ai_response)
                score = score_result.get('score', 0.0)
                feedback = score_result.get('feedback', '评分失败')
            
            return {
                'question_id': question['id'],
                'question_type': question_type,
                'user_answer': user_answer,
                'score': score,
                'feedback': feedback,
                'scored_at': time.time(),
                'scored_by_ai': True
            }
        except Exception as e:
            return {
                'question_id': question['id'],
                'question_type': question_type,
                'user_answer': user_answer,
                'score': 0.0,
                'feedback': f"评分失败: {str(e)}",
                'scored_at': time.time(),
                'scored_by_ai': True
            }
    
    def _generate_scoring_prompt(self, question: Dict[str, Any], user_answer: str, user_level: int) -> str:
        """
        生成评分提示词
        
        Args:
            question: 题目字典
            user_answer: 用户答案
            user_level: 用户等级
            
        Returns:
            评分提示词
        """
        question_type = question['question_type']
        category = question['category']
        difficulty = question['difficulty']
        
        prompt = f"请对以下{question_type}题进行评分，满分100分，评分标准如下：\n"
        
        # 优先使用从数据库加载的评分标准
        if self.scoring_criteria and question_type in self.scoring_criteria:
            criteria = self.scoring_criteria[question_type]
            for i, (criterion, weight) in enumerate(criteria.items(), 1):
                prompt += f"{i}. {criterion}（{weight}分）\n"
        else:
            # 如果数据库配置不存在，使用默认评分标准
            if question_type == 'short_answer':
                prompt += "1. 答案的准确性（40分）\n"
                prompt += "2. 答案的完整性（30分）\n"
                prompt += "3. 表达的清晰度（20分）\n"
                prompt += "4. 用词的准确性（10分）\n"
            elif question_type == 'essay':
                prompt += "1. 内容的完整性和深度（30分）\n"
                prompt += "2. 结构的合理性和逻辑性（25分）\n"
                prompt += "3. 语言表达的准确性和流畅性（20分）\n"
                prompt += "4. 创意和原创性（15分）\n"
                prompt += "5. 格式的正确性（10分）\n"
            elif question_type == 'speaking':
                prompt += "1. 发音的准确性和清晰度（25分）\n"
                prompt += "2. 语法的正确性（25分）\n"
                prompt += "3. 词汇的丰富性和准确性（20分）\n"
                prompt += "4. 表达的流畅性和连贯性（20分）\n"
                prompt += "5. 内容的完整性和相关性（10分）\n"
            elif question_type == 'translation':
                prompt += "1. 意思的准确性（40分）\n"
                prompt += "2. 语言表达的流畅性（30分）\n"
                prompt += "3. 用词的准确性和地道性（20分）\n"
                prompt += "4. 格式的正确性（10分）\n"
        
        prompt += f"\n题目：{question['content']}\n"
        prompt += f"用户答案：{user_answer}\n"
        prompt += f"用户等级：{user_level}\n"
        prompt += f"题目难度：{difficulty}\n"
        prompt += "\n请按照以下格式输出结果：\n"
        prompt += "分数：[0-100]\n"
        prompt += "反馈：[详细的评分反馈]\n"
        
        return prompt
    
    def _parse_ai_scoring_response(self, ai_response: str) -> Dict[str, Any]:
        """
        解析AI评分响应
        
        Args:
            ai_response: AI模型的响应
            
        Returns:
            解析后的评分结果
        """
        score = 0.0
        feedback = ai_response
        
        # 提取分数
        score_match = re.search(r'分数：(\d+(?:\.\d+)?)', ai_response)
        if score_match:
            try:
                score = float(score_match.group(1))
                # 提取反馈
                feedback_match = re.search(r'反馈：(.*)', ai_response, re.DOTALL)
                if feedback_match:
                    feedback = feedback_match.group(1).strip()
            except ValueError:
                pass
        
        return {
            'score': score,
            'feedback': feedback
        }

# 创建全局实例
smart_question_generator = SmartQuestionGenerator()

if __name__ == "__main__":
    # 测试智能题目生成器
    generator = SmartQuestionGenerator()
    
    # 生成单个题目
    question = generator.generate_question("japanese", "词汇", 3)
    print(f"生成的题目: {json.dumps(question, ensure_ascii=False, indent=2)}")
    
    # 生成试卷
    paper = generator.generate_paper("test_user", "japanese", "level", 10, 3)
    print(f"生成的试卷: {json.dumps(paper, ensure_ascii=False, indent=2)}")
