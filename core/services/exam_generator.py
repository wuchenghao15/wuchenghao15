#!/usr/bin/env python3
""" AI脑库学习综合试卷生成器 从数据库题库、AI脑库动态生成和网络爬取获取题目,生成个性化试卷 """

import os
import sys
import random
from datetime import datetime, timedelta
import logging
import uuid

try:
    from gtts import gTTS
    gtts_available = True
except ImportError:
    logger = logging.getLogger('exam_generator')
    logger.warning("未找到gTTS库,音频生成功能将不可用")
    gtts_available = False
    gTTS = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('exam_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('exam_generator')


# 安全解析函数 - 替代eval，防止代码注入
def _safe_parse(content):
    """安全解析字符串内容，优先使用json，回退到ast.literal_eval"""
    import json as _json
    import ast as _ast
    if not content:
        return {}
    try:
        return _json.loads(content)
    except (ValueError, TypeError):
        try:
            return _ast.literal_eval(content)
        except (ValueError, SyntaxError):
            return {}


class ExamGenerator:
    """综合试卷生成器"""

    def __init__(self):
        """初始化试卷生成器"""
        # 用户等级与难度的映射关系
        self.level_difficulty_map = {
            'beginner': ['beginner'],
            'intermediate': ['beginner', 'intermediate'],
            'advanced': ['beginner', 'intermediate', 'advanced'],
            'expert': ['intermediate', 'advanced', 'expert']
        }

        # 难度等级分数范围
        self.difficulty_score_ranges = {
            'beginner': (0, 40),
            'intermediate': (41, 70),
            'advanced': (71, 90),
            'expert': (91, 100)
        }

        # 听力题配置
        self.listening_config = {
            'audio_formats': ['mp3', 'wav'],
            'audio_duration_ranges': {
                'beginner': (30, 60),  # 初级听力材料长度:30-60秒
                'intermediate': (60, 120),  # 中级听力材料长度:60-120秒
                'advanced': (120, 180),  # 高级听力材料长度:120-180秒
                'expert': (180, 300)  # 专家级听力材料长度:3-5分钟
            },
            'question_types': ['single_choice', 'multiple_choice', 'fill_in_blank', 'short_answer'],
            'questions_per_audio': {
                'beginner': 3,  # 初级每段音频对应3个问题
                'intermediate': 4,  # 中级每段音频对应4个问题
                'advanced': 5,  # 高级每段音频对应5个问题
                'expert': 6  # 专家级每段音频对应6个问题
            }
        }

        # 初始化默认考试系统设置
        self.exam_settings = {
            'default_question_count': 20,
            'default_test_duration': 60,
            'difficulty_distribution': '3:5:2',
            'max_repeated_questions': 10,
            'vocabulary_ratio': 25,
            'grammar_ratio': 25,
            'reading_ratio': 30,
            'listening_enabled': True,
            'listening_ratio': 20,
            'enable_ai_question_generation': True,
            'ai_generation_threshold': 50,
            'knowledge_coverage_threshold': 80,
            'difficulty_gradient_enabled': True,
            'enable_timer': True,
            'allow_backtracking': True,
            'auto_submit_on_timeout': True,
            'show_feedback': False,
            'enable_paper_validation': True,
            'validation_severity': 'standard'
        }

        # 初始化AI脑图实例
        self.ai_brain_map = None
        self._initialize_ai_brain_map()

        # 加载考试系统设置
        self.load_exam_settings()

    def _initialize_ai_brain_map(self):
        """初始化AI脑图实例, 用于增强听力题生成"""
        try:
            from app.ai.ai_brain_map import AIBrainMap
            self.ai_brain_map = AIBrainMap()
            # 初始化AI脑图
            self.ai_brain_map.initialize()
            logger.info("✓ AI脑图实例化成功")
        except Exception as e:
            logger.error(f"✗ AI脑图实例化失败: {str(e)}")
            self.ai_brain_map = None

    def load_exam_settings(self):
        """从配置源加载考试系统设置 优先从数据库加载,若失败则使用默认设置 """
        logger.info("开始加载考试系统设置...")

        try:
            settings_from_db = self._load_settings_from_db()
            if settings_from_db:
                logger.info("从数据库成功加载考试系统设置")
                # 更新设置,保留未被数据库覆盖的默认值
                self.exam_settings.update(settings_from_db)
                return

            # 尝试从配置文件加载设置
            settings_from_file = self._load_settings_from_file()
            if settings_from_file:
                logger.info("从配置文件成功加载考试系统设置")
                self.exam_settings.update(settings_from_file)
                return

            logger.info("未找到外部设置,使用默认考试系统设置")
        except Exception as e:
            logger.error(f"加载考试系统设置失败: {str(e)}")
            logger.info("使用默认考试系统设置")

    def _load_settings_from_db(self):
        """从数据库加载考试系统设置"""
        try:
            # 尝试导入数据库模型
            from app.models.system_settings import SystemSettings
            exam_settings = SystemSettings.get_all_by_category('exam_system')
            if not exam_settings:
                return None

            # 转换为字典格式
            settings_dict = {}
            for setting in exam_settings:
                # 根据设置类型转换值
                if setting.setting_type == 'number':
                    settings_dict[setting.key] = int(setting.value)
                elif setting.setting_type == 'boolean':
                    settings_dict[setting.key] = setting.value.lower() == 'true' or setting.value == '1'
                else:
                    settings_dict[setting.key] = setting.value

            return settings_dict
        except Exception as e:
            logger.error(f"从数据库加载设置失败: {str(e)}")
            return None

    def _load_settings_from_file(self):
        """从配置文件加载考试系统设置"""
        try:
            import os

            # 配置文件路径
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'exam_settings.json')

            if not os.path.exists(config_file):
                return None

            with open(config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            return settings
        except Exception as e:
            return None

    def update_exam_settings(self, new_settings):
        """更新考试系统设置 Args: new_settings: 新的设置字典 """
        logger.info(f"更新考试系统设置: {new_settings}")

        self.exam_settings.update(new_settings)

        # 保存到数据库
        try:
            from app.models.system_settings import SystemSettings

            for key, value in new_settings.items():
                SystemSettings.set_setting(
                    key=key,
                    value=str(value),
                    category='exam_system',
                    description=f'考试系统设置: {key}'
                )

            logger.info("考试系统设置已成功保存到数据库")
        except Exception as e:
            logger.error(f"保存考试系统设置到数据库失败: {str(e)}")

        # 保存到配置文件作为备份
        try:
            import os

            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            config_file = os.path.join(config_dir, 'exam_settings.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.exam_settings, f, ensure_ascii=False, indent=2)
            logger.info("考试系统设置已成功保存到配置文件")
        except Exception as e:
            logger.error(f"保存考试系统设置到配置文件失败: {str(e)}")

    def apply_settings_to_paper_generation(self, generation_params):
        """应用设置到试卷生成参数 Args: generation_params: 原始生成参数 Returns: 更新后的生成参数 """
        updated_params = generation_params.copy()

        # 应用基础设置
        if 'question_count' not in updated_params:
            updated_params['question_count'] = self.exam_settings['default_question_count']

        if 'test_duration' not in updated_params:
            updated_params['test_duration'] = self.exam_settings['default_test_duration']

        # 应用难度分布
        if 'difficulty_distribution' not in updated_params:
            updated_params['difficulty_distribution'] = self.exam_settings['difficulty_distribution']

        # 应用题目类型比例
        updated_params['question_type_ratios'] = {
            'vocabulary': self.exam_settings['vocabulary_ratio'],
            'grammar': self.exam_settings['grammar_ratio'],
            'reading': self.exam_settings['reading_ratio']
        }

        # 应用听力题设置
        if self.exam_settings['listening_enabled']:
            updated_params['question_type_ratios']['listening'] = self.exam_settings['listening_ratio']
            # 调整其他题型比例,确保总和为100%
            total_ratio = sum(updated_params['question_type_ratios'].values())
            if total_ratio > 100:
                # 等比例缩小所有题型比例
                scale_factor = 100 / total_ratio
                for key in updated_params['question_type_ratios']:
                    updated_params['question_type_ratios'][key] = int(
                    updated_params['question_type_ratios'][key] * scale_factor)

        # 应用AI生成设置
        updated_params['enable_ai_question_generation'] = self.exam_settings['enable_ai_question_generation']
        updated_params['ai_generation_threshold'] = self.exam_settings['ai_generation_threshold']

        # 应用知识覆盖要求
        updated_params['knowledge_coverage_threshold'] = self.exam_settings['knowledge_coverage_threshold']

        # 应用难度梯度设置
        updated_params['difficulty_gradient_enabled'] = self.exam_settings['difficulty_gradient_enabled']

        return updated_params

    def get_questions_from_db(self, subject, difficulty=None, question_type=None, count=10, knowledge_points=None,
    exclude_question_ids=None):
        """从数据库题库获取题目 Args: subject: 科目(english, japanese) difficulty: 难度(beginner, intermediate, advanced, expert) question_type: 题型(single_choice, multiple_choice) count: 题目数量 knowledge_points: 知识点列表(如 ['grammar', 'vocabulary']) exclude_question_ids: 要排除的题目ID列表 Returns: 题目列表 """
        logger.info(f"从数据库获取 {count} 道{subject}题目,难度: {difficulty},题型: {question_type},知识点: {knowledge_points}")

        try:
            from app.models.ai_brain import AIBrainKnowledge

            # 构建知识类型
            knowledge_type = f"{subject.lower()}_question"

            # 获取所有相关题目
            all_questions = AIBrainKnowledge.get_all(knowledge_type=knowledge_type)

            # 过滤题目
            filtered_questions = []
            seen_question_ids = set()  # 用于去重

            for question in all_questions:
                # 安全修复：使用json.loads替代eval，防止代码注入
                import json as _json
                import ast as _ast
                try:
                    question_data = _json.loads(question.content)
                except (ValueError, TypeError):
                    try:
                        question_data = _ast.literal_eval(question.content)
                    except (ValueError, SyntaxError):
                        continue

                # 为题目添加唯一标识(如果没有的话)
                if 'question_id' not in question_data:
                    # 使用知识ID或题目内容的哈希值作为唯一标识
                    question_data['question_id'] = question.knowledge_id if hasattr(question,
                    'knowledge_id') else str(hash(question.content))

                # 跳过已见过的题目
                if question_data['question_id'] in seen_question_ids:
                    continue

                # 跳过需要排除的题目
                if exclude_question_ids and question_data['question_id'] in exclude_question_ids:
                    continue

                # 过滤难度
                if difficulty and question_data['difficulty'] != difficulty:
                    continue

                # 过滤题型
                if question_type and question_data['type'] != question_type:
                    continue

                # 过滤知识点
                if knowledge_points:
                    # 检查题目是否包含指定的知识点
                    question_knowledge_points = question_data.get('knowledge_points', [])
                    # 如果题目没有知识点信息,默认包含
                    if not question_knowledge_points:
                        filtered_questions.append(question_data)
                        seen_question_ids.add(question_data['question_id'])
                        continue
                    # 检查是否有交集
                    has_matching_kp = any(kp in question_knowledge_points for kp in knowledge_points)
                    if has_matching_kp:
                        filtered_questions.append(question_data)
                        seen_question_ids.add(question_data['question_id'])
                else:
                    # 没有指定知识点,直接添加
                    filtered_questions.append(question_data)
                    seen_question_ids.add(question_data['question_id'])

            random.shuffle(filtered_questions)

            # 优先选择使用次数较少的题目

            # 随机选择题目
            if len(filtered_questions) > count:
                weights = [1.0 / (q.get('usage_count', 0) + 1) for q in filtered_questions]
                selected_questions = random.choices(filtered_questions, weights=weights, k=count)
            else:
                selected_questions = filtered_questions

            # 增强题目的选项,确保具有混淆性
            enhanced_questions = []
            for question in selected_questions:
                enhanced_question = self.enhance_question_options(question)
                enhanced_questions.append(enhanced_question)

            logger.info(f"从数据库成功获取并增强 {len(enhanced_questions)} 道唯一题目")
            return enhanced_questions
        except Exception as e:
            logger.error(f"从数据库获取题目失败: {str(e)}")

    def enhance_question_options(self, question):
        """增强题目选项 Args: question: 原始题目数据 Returns: 增强后的题目数据,选项具有更好的混淆性 """
        if 'options' not in question or len(question['options']) < 2:
            return question

        # 获取正确答案
        correct_answer = question['options'][question['answer']]
        # 根据题目类型和内容生成更具混淆性的选项
        if question['type'] == 'single_choice':
            return self._enhance_single_choice_options(question, correct_answer)
        elif question['type'] == 'multiple_choice':
            return self._enhance_multiple_choice_options(question, correct_answer)
        else:
            return question

    def _enhance_single_choice_options(self, question, correct_answer):
        """增强单选题的选项 Args: question: 原始题目数据 correct_answer: 正确答案 Returns: 增强后的题目数据 """
        # 确保至少有4个选项
        if len(question['options']) < 4:
            # 生成更多具有混淆性的选项
            additional_options = self._generate_distractors(correct_answer, question['question'],
            4 - len(question['options']))
            question['options'].extend(additional_options)

        # 确保选项具有混淆性
        enhanced_options = [correct_answer]

        # 为正确答案生成具有混淆性的干扰项
        distractors = self._generate_distractors(correct_answer, question['question'], 3)
        enhanced_options.extend(distractors)

        # 打乱选项顺序
        random.shuffle(enhanced_options)

        # 更新题目选项和正确答案索引
        question['options'] = enhanced_options
        question['answer'] = enhanced_options.index(correct_answer)
        return question

    def _enhance_multiple_choice_options(self, question, correct_answer):
        """增强多选题的选项 Args: question: 原始题目数据 correct_answer: 正确答案 Returns: 增强后的题目数据 """
        # 目前简单处理,确保至少有5个选项
        if len(question['options']) < 5:
            additional_options = self._generate_distractors(correct_answer, question['question'],
            5 - len(question['options']))
            question['options'].extend(additional_options)

        return question
    def _generate_distractors(self, correct_answer, question, count):
        """生成具有混淆性的干扰项 Args: correct_answer: 正确答案 question: 题目内容 count: 需要生成的干扰项数量 Returns: 干扰项列表 """
        distractors = []

        # 根据题目和正确答案生成干扰项
        if isinstance(correct_answer, str):
            # 字符串类型的答案,生成语义相似但错误的选项
            for i in range(count):
                # 生成不同类型的干扰项
                if 'spelling' in question.lower() or 'correct spelling' in question.lower():
                    # 拼写题,生成相似拼写的错误选项
                    distractor = self._generate_spelling_distractor(correct_answer)
                elif 'meaning' in question.lower() or 'synonym' in question.lower():
                    # 同义词题,生成相似但不同的同义词
                    distractor = self._generate_synonym_distractor(correct_answer)
                elif 'grammar' in question.lower() or 'sentence' in question.lower():
                    # 语法题,生成语法相似但错误的句子
                    distractor = self._generate_grammar_distractor(correct_answer)
                else:
                    # 通用情况,生成语义相似的干扰项
                    distractor = self._generate_generic_distractor(correct_answer, i)

                if distractor not in distractors and distractor != correct_answer:
                    distractors.append(distractor)
        # 如果生成的干扰项不足,补充通用干扰项
        while len(distractors) < count:
            generic_distractor = f"Similar but wrong option {len(distractors) + 1}"
            if generic_distractor not in distractors and generic_distractor != correct_answer:
                distractors.append(generic_distractor)

        return distractors[:count]

    def _generate_spelling_distractor(self, correct_word, idx=0):
        """生成拼写相似的干扰项 Args: correct_word: 正确的单词 idx: 要替换的字母索引 Returns: 拼写相似的错误单词 """
        if len(correct_word) <= 3:
            # 短单词,交换字母顺序
            return correct_word[::-1]
        else:
            # 长单词,替换一个字母
            import random
            # 生成一个不同的字母
            new_char = chr(random.randint(97, 122))
            while new_char == correct_word[idx]:
                new_char = chr(random.randint(97, 122))
            return correct_word[:idx] + new_char + correct_word[idx+1:]

    def _generate_synonym_distractor(self, correct_synonym):
        """生成同义词干扰项 Args: correct_synonym: 正确的同义词 Returns: 相似但不同的同义词 """
        # 简单的同义词干扰项生成逻辑
        synonym_dict = {
            'beautiful': ['pretty', 'handsome', 'lovely', 'ugly'],
            'happy': ['glad', 'joyful', 'merry', 'sad'],
            'big': ['large', 'huge', 'great', 'small'],
            'good': ['well', 'fine', 'excellent', 'bad'],
            'quick': ['fast', 'speedy', 'rapid', 'slow'],
            'puppy': ['dog', 'pup', 'canine', 'cat']
        }

        if correct_synonym.lower() in synonym_dict:
            # 从同义词列表中选择一个不同的词
            synonyms = synonym_dict[correct_synonym.lower()]
            return random.choice([s for s in synonyms if s != correct_synonym.lower()])
        else:
            return f"similar to {correct_synonym}"

    def _generate_grammar_distractor(self, correct_sentence):
        """生成语法相似但错误的干扰项 Args: correct_sentence: 正确的句子 Returns: 语法相似但错误的句子 """
        # 简单的语法干扰项生成逻辑
        if 'has been' in correct_sentence:
            return correct_sentence.replace('has been', 'have been')
        elif 'have been' in correct_sentence:
            return correct_sentence.replace('have been', 'has been')
        elif 'go to' in correct_sentence:
            return correct_sentence.replace('go to', 'goes to')
        elif 'goes to' in correct_sentence:
            return correct_sentence.replace('goes to', 'go to')
        else:
            # 通用处理,在句子中添加或删除一个词
            words = correct_sentence.split()
            if len(words) > 3:
                # 删除一个随机单词
                del words[random.randint(1, len(words) - 2)]
                return ' '.join(words)
            else:
                # 添加一个随机单词
                return correct_sentence + ' now'

    def _generate_generic_distractor(self, correct_answer, index):
        """生成通用干扰项 Args: correct_answer: 正确答案 Returns: 通用干扰项 """
        return f"Option {chr(65 + index)} - similar to {correct_answer[:10]}..."

    def get_user_wrong_questions(self, username, subject, count=10):
        """获取用户的错题集 Args: username: 用户名 subject: 科目(english, japanese) count: 题目数量 Returns: 错题列表 """
        logger.info(f"获取用户 {username} 的 {subject} 错题集,数量: {count}")

        try:
            from app.models.learning_system import UserWrongQuestion

            # 获取用户错题
            wrong_questions = UserWrongQuestion.get_user_wrong_questions(username, subject)

            # 转换为题目格式
            questions = []
            for wrong_q in wrong_questions:
                # 获取题目详情
                question = AIBrainKnowledge.get_by_id(wrong_q.question_id)
                if question:
                    question_data = _safe_parse(question.content)
                    # 添加错题相关信息
                    question_data['wrong_count'] = wrong_q.wrong_count
                    question_data['last_wrong_at'] = wrong_q.last_wrong_at.isoformat(
                    ) if wrong_q.last_wrong_at else None

            # 按错误次数排序,优先选择错误次数多的题目
            questions.sort(key=lambda x: x.get('wrong_count', 0), reverse=True)

            # 限制数量
            if len(questions) > count:
                questions = questions[:count]

            logger.info(f"成功获取用户 {username} 的 {subject} 错题集,数量: {len(questions)}")
            return questions
        except Exception as e:
            logger.error(f"获取用户错题集失败: {str(e)}")
            return []

    def generate_wrong_question_practice(self, username, subject, count=20):
        """生成针对用户错题集的练习试卷 Args: username: 用户名 subject: 科目(english, japanese) count: 题目数量 Returns: 练习试卷 """
        logger.info(f"为用户 {username} 生成 {subject} 错题练习试卷,数量: {count}")

        # 获取用户错题
        wrong_questions = self.get_user_wrong_questions(username, subject, count)

        if len(wrong_questions) < count:
            # 获取用户等级
            user_level = self.get_user_level(username, subject)
            # 获取允许的难度
            allowed_difficulties = self.adjust_difficulty_by_user_level(user_level)
            # 选择最高允许难度
            difficulty = allowed_difficulties[-1]

            # 补充普通题目
            additional_questions = self.get_questions_from_db(
                subject,
                difficulty,
                'single_choice',
                remaining_count
            )
            wrong_questions.extend(additional_questions)

        # 随机打乱题目顺序

        # 生成试卷
        exam = {
            "user_id": username,
            "title": f"{subject}错题练习卷",
            "subject": subject,
            "total_questions": len(wrong_questions),
            "time_limit": 60,  # 默认60分钟
            "generated_at": datetime.now().isoformat(),
            "questions": wrong_questions,
            "exam_type": "wrong_question_practice",
            "user_level": self.get_user_level(username, subject)
        }

        logger.info(f"成功生成错题练习试卷 {exam['exam_id']},包含 {len(wrong_questions)} 道题目")
        return exam

    def update_practice_progress(self, username, subject, knowledge_points, progress_data):
        """更新用户练习进度 Args: username: 用户名 subject: 科目(english, japanese) knowledge_points: 知识点列表 progress_data: 进度数据,格式: {"total_practiced": 100, "correct_count": 85, "wrong_count": 15} Returns: 是否更新成功 """
        logger.info(f"更新用户 {username} 的 {subject} 练习进度,知识点: {knowledge_points}")
        try:
            from app.models.learning_system import UserPracticeProgress

            # 更新或创建练习进度
            for kp in knowledge_points:
                progress = UserPracticeProgress.get_progress(username, subject, kp)
                if progress:
                    progress.total_practiced += progress_data['total_practiced']
                    progress.correct_count += progress_data['correct_count']
                    progress.wrong_count += progress_data['wrong_count']
                    progress.last_practiced_at = datetime.now()
                    progress.save()
                else:
                    # 创建新进度
                    progress = UserPracticeProgress(
                        username=username,
                        subject=subject,
                        knowledge_point=kp,
                        total_practiced=progress_data['total_practiced'],
                        correct_count=progress_data['correct_count'],
                        wrong_count=progress_data['wrong_count'],
                        last_practiced_at=datetime.now()
                    )
                    progress.save()

            logger.info(f"成功更新用户 {username} 的 {subject} 练习进度")
            return True
        except Exception as e:
            logger.error(f"更新用户练习进度失败: {str(e)}")
            return False

    def get_practice_suggestions(self, username, subject):
        """获取用户练习建议 Args: username: 用户名 subject: 科目(english, japanese) Returns: 练习建议列表 """
        logger.info(f"获取用户 {username} 的 {subject} 练习建议")

        try:
            from app.models.learning_system import UserPracticeProgress
            from app.models.learning_system import UserWrongQuestion

            # 获取用户所有知识点的练习进度
            all_progress = UserPracticeProgress.get_all_progress(username, subject)

            # 获取用户错题集
            wrong_questions = UserWrongQuestion.get_user_wrong_questions(username, subject)

            # 分析练习数据,生成建议
            suggestions = []

            # 1. 建议练习正确率低的知识点
            for progress in all_progress:
                if progress.total_practiced < 10:
                    # 练习次数太少,建议多练习
                    suggestions.append({
                        "type": "practice_more",
                        "knowledge_point": progress.knowledge_point,
                        "reason": f"{progress.knowledge_point} 练习次数较少,建议多练习",
                        "priority": "high"
                    })
                else:
                    # 计算正确率
                    accuracy = progress.correct_count / progress.total_practiced if progress.total_practiced > 0 else 0
                    if accuracy < 0.6:
                        # 正确率低于60%,建议重点练习
                        suggestions.append({
                            "type": "focus_practice",
                            "knowledge_point": progress.knowledge_point,
                            "reason": f"{progress.knowledge_point} 正确率较低 ({accuracy:.2%}),建议重点练习",
                            "priority": "high"
                        })

            # 2. 建议练习错题集
            if len(wrong_questions) > 5:
                suggestions.append({
                    "type": "wrong_question_practice",
                    "reason": f"您有 {len(wrong_questions)} 道错题,建议练习错题集",
                    "priority": "medium"
                })

            # 3. 建议扩展难度
            user_level = self.get_user_level(username, subject)
            if user_level != 'expert':
                suggestions.append({
                    "type": "increase_difficulty",
                    "reason": f"您当前等级为 {user_level},建议尝试更高难度的题目",
                    "priority": "medium"
                })

            logger.info(f"成功生成用户 {username} 的 {subject} 练习建议,数量: {len(suggestions)}")
            return suggestions
        except Exception as e:
            logger.error(f"生成练习建议失败: {str(e)}")
            return []

    def generate_questions_with_ai(self, subject, difficulty, question_type, count=10):
        """使用AI脑库动态生成题目 Args: subject: 科目(english, japanese) difficulty: 难度(beginner, intermediate, advanced, expert) question_type: 题型(single_choice, multiple_choice) count: 题目数量 Returns: 唯一的AI生成题目列表 """

        generated_questions = []
        seen_question_hashes = set()  # 用于确保题目唯一性

        # 生成唯一题目的辅助函数
        def generate_unique_question(index):
            """生成单个唯一题目"""
            # 根据科目和难度生成不同类型的题目
            if subject.lower() == 'english':
                return self._generate_english_question(difficulty, question_type, index)
            elif subject.lower() == 'japanese':
                return self._generate_japanese_question(difficulty, question_type, index)
            else:
                return self._generate_generic_question(subject, difficulty, question_type, index)

        # 生成指定数量的唯一题目
        attempt_count = 0
        max_attempts = count * 3  # 最大尝试次数,防止无限循环

        while len(generated_questions) < count and attempt_count < max_attempts:
            attempt_count += 1
            question = generate_unique_question(len(generated_questions) + 1)
            question_hash = hash(question['question'] + str(question['options']))

            if question_hash not in seen_question_hashes:
                seen_question_hashes.add(question_hash)
                # 添加唯一标识
                question['question_id'] = f"ai_{uuid.uuid4().hex[:12]}"
                question['usage_count'] = 0
                generated_questions.append(question)

        # 如果生成的题目数量不足,使用变体生成补充
        if len(generated_questions) < count and generated_questions:
            logger.info(f"AI题目生成数量不足,使用变体补充: {len(generated_questions)} -> {count}")
            while len(generated_questions) < count:
                # 随机选择一个已生成的题目作为基础
                base_question = random.choice(generated_questions)
                # 生成变体
                variant = self._generate_question_variant(base_question)
                # 检查变体是否唯一
                variant_hash = hash(variant['question'] + str(variant['options']))
                if variant_hash not in seen_question_hashes:
                    seen_question_hashes.add(variant_hash)
                    variant['question_id'] = f"ai_variant_{uuid.uuid4().hex[:12]}"
                    variant['usage_count'] = 0
                    generated_questions.append(variant)

        logger.info(f"成功生成 {len(generated_questions)} 道唯一的AI题目")
        return generated_questions

    def _generate_variant(self, base_question):
        """生成题目变体 Args: base_question: 基础题目 Returns: 生成的题目变体 """
        variant = base_question.copy()
        # 根据题目类型生成变体
        if variant['type'] in ['single_choice', 'multiple_choice']:
            if 'options' in variant and variant['options']:
                correct_answer = variant['options'][variant['answer']]
                random.shuffle(variant['options'])
        elif variant['type'] == 'true_false':
            # 生成相反的陈述
            if random.choice([True, False]):
                variant['question'] = self._generate_opposite_statement(variant['question'])
                variant['answer'] = 1 - variant['answer']  # 反转答案
        # 添加变体标识
        variant['is_variant'] = True
        variant['base_question_id'] = variant['question_id']

        return variant

    def _generate_opposite_statement(self, statement):
        """生成相反的陈述 Args: statement: 原始陈述 Returns: 相反的陈述 """
        # 简单实现:添加或移除否定词
        negation_words = ['not', 'don\'t', 'doesn\'t', 'didn\'t', 'won\'t', 'can\'t']

        # 检查是否已经包含否定词
        has_negation = any(word in statement.lower() for word in negation_words)

        if has_negation:
            # 移除否定词
            for word in negation_words:
                statement = statement.replace(word, "")
        else:
            # 添加否定词
            if 'is' in statement:
                statement = statement.replace('is', 'is not')
            elif 'are' in statement:
                statement = statement.replace('are', 'are not')
            elif 'have' in statement:
                statement = statement.replace('have', 'have not')
            elif 'has' in statement:
                statement = statement.replace('has', 'has not')
            else:
                # 通用处理
                statement = f"It is not true that {statement}"

        return statement

    def _generate_english_question(self, difficulty, question_type, index):
        """生成英语题目"""
        # 根据难度生成不同类型的题目
        if difficulty == 'beginner':
            return self._generate_english_beginner_question(index)
        elif difficulty == 'intermediate':
            return self._generate_english_intermediate_question(index)
        elif difficulty == 'advanced':
            return self._generate_english_advanced_question(index)
        else:  # expert
            return self._generate_english_expert_question(index)

    def _generate_english_beginner_question(self, index):
        """生成英语初级题目"""
        # 初级英语题目模板
        templates = [
            {
                "question": "What is the correct spelling of the word meaning 'a young dog'?",
                "correct_answer": "puppy",
                "distractors": ["pupy", "puppi", "puppie"],
                "explanation": "The correct spelling is 'puppy', which refers to a young dog.",
                "vocabulary": ["spelling", "puppy", "dog"]
            },
            {
                "question": "Which of the following is a color?",
                "correct_answer": "blue",
                "distractors": ["book", "table", "chair"],
                "explanation": "Blue is a color, while book, table, and chair are objects.",
                "vocabulary": ["color", "blue", "object"]
            },
            {
                "question": "What do you use to write on paper?",
                "correct_answer": "pen",
                "distractors": ["spoon", "shoe", "hat"],
                "explanation": "A pen is used for writing on paper.",
                "vocabulary": ["write", "pen", "paper"]
            },
            {
                "question": "What day comes after Monday?",
                "correct_answer": "Tuesday",
                "distractors": ["Sunday", "Wednesday", "Thursday"],
                                "explanation": "The days of the week are: Sunday, Monday, Tuesday, Wednesday, Thursday, Friday,                Saturday.",
                "vocabulary": ["days", "week", "Monday", "Tuesday"]
            },
            {
                "question": "How many days are there in a week?",
                "distractors": ["Five", "Six", "Eight"],
                                "explanation": "There are seven days in a week: Sunday, Monday, Tuesday, Wednesday, Thursday, Friday,                Saturday.",
                "vocabulary": ["days", "week", "seven"]
            },
            {
                "question": "What is the opposite of 'hot'?",
                "correct_answer": "Cold",
                "distractors": ["Warm", "Cool", "Freeze"],
                "explanation": "The opposite of 'hot' is 'cold'.",
            },
            {
                "question": "What do you eat with a fork?",
                "correct_answer": "Pasta",
                "distractors": ["Soup", "Tea", "Ice cream"],
                "explanation": "Pasta is typically eaten with a fork.",
                "vocabulary": ["eat", "fork", "pasta"]
            },
            {
                "question": "What animal says 'meow'?",
                "correct_answer": "Cat",
                "distractors": ["Dog", "Cow", "Bird"],
                "explanation": "A cat says 'meow'.",
                "vocabulary": ["animal", "cat", "meow"]
            },
            {
                "question": "How many months are there in a year?",
                "correct_answer": "Twelve",
                "distractors": ["Ten", "Eleven", "Thirteen"],
                "explanation": "There are twelve months in a year.",
                "vocabulary": ["months", "year", "twelve"]
            },
            {
                "question": "What is the capital city of the United States?",
                "correct_answer": "Washington D.C.",
                "distractors": ["New York", "Los Angeles", "Chicago"],
                "explanation": "The capital city of the United States is Washington D.C.",
                "vocabulary": ["capital", "United States", "Washington D.C."]
            }
        ]

        # 随机选择模板并生成唯一题目
        template = random.choice(templates)

        # 生成选项并打乱顺序
        options = [template['correct_answer']] + template['distractors']
        random.shuffle(options)

        # 找到正确答案的索引
        answer_index = options.index(template['correct_answer'])

        return {
            "type": "single_choice",
            "difficulty": "beginner",
            "question": template['question'],
            "options": options,
            "answer": answer_index,
            "explanation": template['explanation'],
            "vocabulary": template['vocabulary']
        }

    def _generate_english_intermediate_question(self, index):
        """生成英语中级题目"""
        # 中级英语题目模板
        templates = [
            {
                "question": "Which sentence is grammatically correct?",
                "correct_answer": "She has been studying English for three years.",
                "distractors": ["She have been studying English for three years.",
                             "She has been study English for three years.",
                             "She has studied English for three years ago."],
                                "explanation": "The present perfect continuous tense 'has been studying' is used to describe an action                that started in the past and continues to the present.",
                "vocabulary": ["grammar", "present perfect continuous", "tense"]
            },
            {
                "question": "What is the synonym of 'beautiful'?",
                "correct_answer": "gorgeous",
                "distractors": ["ugly", "boring", "difficult"],
                "explanation": "'Gorgeous' is a synonym of 'beautiful', meaning very attractive.",
                "vocabulary": ["synonym", "beautiful", "gorgeous"]
            },
            {
                "question": "Which of the following is a phrasal verb?",
                "correct_answer": "Look after",
                "distractors": ["Look", "After", "Beautiful"],
                                "explanation": "A phrasal verb is a verb that is made up of a main verb together with an adverb or a                preposition, or both. 'Look after' means to take care of someone or something.",
                "vocabulary": ["phrasal verb", "look after", "take care"]
            },
            {
                "question": "What does the idiom 'break a leg' mean?",
                "correct_answer": "Good luck",
                "distractors": ["Be careful", "Hurry up", "Take a rest"],
                "vocabulary": ["idiom", "break a leg", "good luck"]
            },
            {
                "question": "Which sentence is in passive voice?",
                "correct_answer": "The book was written by J.K. Rowling.",
                "distractors": ["J.K. Rowling was written the book.",
                             "The book wrote by J.K. Rowling.",
                             "The book is writing by J.K. Rowling."],
                                "explanation": "The passive voice is used when the focus is on the action,                not on who or what is performing the action. The structure is: subject + auxiliary verb (                be) + past participle.",
                "vocabulary": ["passive voice", "auxiliary verb", "past participle"]
            },
            {
                "question": "What is the antonym of 'generous'?",
                "correct_answer": "Selfish",
                "distractors": ["Kind", "Helpful", "Friendly"],
                                "explanation": "An antonym is a word opposite in meaning to another. 'Selfish' is the antonym of                'generous'.",
                "vocabulary": ["antonym", "generous", "selfish"]
            },
            {
                "question": "Which of the following is a countable noun?",
                "correct_answer": "Book",
                "distractors": ["Water", "Information", "Advice"],
                                "explanation": "Countable nouns are things we can count. They have a singular and a plural form. 'Book'                is countable (one book, two books).",
                "vocabulary": ["countable noun", "singular", "plural"]
            },
            {
                                "question": "What is the correct preposition to complete this sentence: 'I'm interested _____ learning                new languages.'", "correct_answer": "in", "distractors": ["on", "at", "with"],
                                "explanation": "The correct preposition is 'in'. We use 'interested in' to talk about something we want                to learn or know more about.",
                "vocabulary": ["preposition", "interested in", "learn"]
            },
            {
                "question": "Which sentence is in the past perfect tense?",
                "correct_answer": "They had already eaten dinner when I arrived.",
                "distractors": ["They are eating dinner now.",
                             "They will eat dinner later.",
                             "They ate dinner yesterday."],
                "vocabulary": ["past perfect tense", "completed action", "past participle"]
            },
            {
                "question": "What does the phrasal verb 'put off' mean?",
                "correct_answer": "Postpone",
                "distractors": ["Put on clothes", "Turn off", "Take off"],
                "vocabulary": ["phrasal verb", "put off", "postpone"]
            }
        ]

        # 随机选择模板并生成唯一题目
        template = random.choice(templates)
        # 生成选项并打乱顺序
        options = [template['correct_answer']] + template['distractors']
        random.shuffle(options)

        # 找到正确答案的索引
        answer_index = options.index(template['correct_answer'])

        return {
            "type": "single_choice",
            "difficulty": "intermediate",
            "question": template['question'],
            "options": options,
            "answer": answer_index,
            "explanation": template['explanation'],
            "vocabulary": template['vocabulary']
        }

    def _generate_english_advanced_question(self, index):
        """生成英语高级题目"""
        # 高级英语题目模板
        templates = [
            {
                "question": "What does the idiom 'break a leg' mean?",
                "correct_answer": "Good luck!",
                "distractors": ["Be careful!", "Hurry up!", "Take a break!"],
                                "explanation": "The idiom 'break a leg' is used to wish someone good luck,                especially before a performance.",
                "vocabulary": ["idiom", "break a leg", "good luck"]
            },
            {
                "question": "Which of the following is an example of a metaphor?",
                "correct_answer": "The world is a stage.",
                "distractors": ["She sings beautifully.", "He runs quickly.", "The cat sleeps soundly."],
                                "explanation": "A metaphor is a figure of speech that directly compares two things without using 'like'                or 'as'.",
                "vocabulary": ["metaphor", "figure of speech", "compare"]
            },
            {
                "question": "What is the difference between 'affect' and 'effect'?",
                                "correct_answer": "'Affect' is usually a verb meaning to influence,                while 'effect' is usually a noun meaning the result.",
                                "distractors": ["'Affect' is usually a noun meaning the result,                while 'effect' is usually a verb meaning to influence.",
                             "There is no difference; they are interchangeable.",
                             "'Affect' and 'effect' are homophones with no difference in meaning."],
                                "explanation": "'Affect' is primarily a verb meaning to influence or produce a change in something.                'Effect' is primarily a noun meaning the result or consequence of an action.",
                "vocabulary": ["affect", "effect", "difference", "verb", "noun"]
            },
            {
                "question": "Which sentence uses 'would rather' correctly?",
                "correct_answer": "I would rather stay home than go to the party.",
                "distractors": ["I would rather to stay home than go to the party.",
                             "I would rather staying home than go to the party.",
                             "I would rather stayed home than go to the party."],
                                "explanation": "'Would rather' is used to express a preference. The correct structure is: 'would rather                + base verb + than + base verb'.",
                "vocabulary": ["would rather", "preference", "structure"]
            },
            {
                "question": "What is the meaning of the prefix 'un-' in the word 'unbelievable'?",
                "correct_answer": "Not",
                "distractors": ["Very", "Again", "Together"],
                "explanation": "The prefix 'un-' means 'not', so 'unbelievable' means 'not believable'.",
                "vocabulary": ["prefix", "un-", "not", "believable"]
            },
            {
                "question": "Which of the following is an example of a simile?",
                "correct_answer": "She is as brave as a lion.",
                "distractors": ["The wind whispered through the trees.",
                             "He is the apple of her eye.",
                             "The world is a book for those who read."],
                "explanation": "A simile is a figure of speech that compares two things using 'like' or 'as'.",
                "vocabulary": ["simile", "figure of speech", "compare", "like", "as"]
            },
            {
                                "question": "What does the phrasal verb 'bring up' mean in this sentence: 'She brought up the issue                during the meeting.'",
                "correct_answer": "Mention or introduce",
                "distractors": ["Raise a child", "Bring something upstairs", "End a discussion"],
                "explanation": "In this context, 'bring up' means to mention or introduce a topic for discussion.",
                "vocabulary": ["phrasal verb", "bring up", "mention", "context"]
            },
            {
                "question": "Which sentence uses the subjunctive mood correctly?",
                "distractors": ["If I was you, I would apologize.",
                             "If I am you, I would apologize.",
                             "If I would be you, I would apologize."],
                                "explanation": "The subjunctive mood is used to express hypothetical or contrary-to-fact situations. In                the 'if' clause, we use 'were' instead of 'was' for all subjects.",
                "vocabulary": ["subjunctive mood", "hypothetical", "contrary-to-fact", "if clause"]
            },
            {
                "question": "What is the meaning of the suffix '-able' in the word 'comfortable'?",
                "correct_answer": "Capable of being",
                "distractors": ["Full of", "Without", "Related to"],
                                "explanation": "The suffix '-able' means 'capable of being',                so 'comfortable' means 'capable of being comforted' or 'providing comfort'.",
                "vocabulary": ["suffix", "-able", "capable of being", "comfortable"]
            },
            {
                "question": "Which of the following is an example of personification?",
                "correct_answer": "The flowers danced in the breeze.",
                "distractors": ["The cake tastes delicious.",
                             "He is as strong as an ox.",
                             "The sky is blue."],
                                "explanation": "Personification is a figure of speech that gives human qualities to non-human things.                In this sentence, flowers are given the human ability to dance.",
                "vocabulary": ["personification", "figure of speech", "human qualities", "non-human things"]
            }
        ]

        # 随机选择模板并生成唯一题目
        template = random.choice(templates)

        # 生成选项并打乱顺序
        options = [template['correct_answer']] + template['distractors']
        random.shuffle(options)

        # 找到正确答案的索引
        answer_index = options.index(template['correct_answer'])

        return {
            "type": "single_choice",
            "difficulty": "advanced",
            "question": template['question'],
            "options": options,
            "answer": answer_index,
            "explanation": template['explanation'],
            "vocabulary": template['vocabulary']
        }

    def _generate_english_expert_question(self, index):
        """生成英语专家级题目"""
        # 专家级英语题目模板
        templates = [
            {
                "question": "What is the difference between 'affect' and 'effect'?",
                                "correct_answer": "'Affect' is usually a verb meaning to influence,                while 'effect' is usually a noun meaning the result.",
                                "distractors": ["'Affect' is usually a noun meaning the result,                while 'effect' is usually a verb meaning to influence.",
                             "There is no difference; they are interchangeable.",
                             "'Affect' and 'effect' have the same meaning but different spellings."],
                                "explanation": "'Affect' is primarily a verb meaning to influence or produce a change in something.                'Effect' is primarily a noun meaning the result or consequence of an action.",
                "vocabulary": ["affect", "effect", "difference"]
            },
            {
                "question": "What is the meaning of the idiom 'the elephant in the room'?",
                "correct_answer": "An obvious problem that everyone ignores",
                "distractors": ["A large animal in a small space",
                             "A hidden problem that no one notices",
                             "A rare occurrence that surprises everyone"],
                                "explanation": "The idiom 'the elephant in the room' refers to an obvious problem or controversial                issue that is clearly present but avoided as a subject for discussion.",
                "vocabulary": ["idiom", "elephant in the room", "obvious problem", "ignore"]
            },
            {
                "question": "Which sentence uses the past perfect tense correctly?",
                "correct_answer": "By the time we arrived, they had already left.",
                "distractors": ["By the time we arrived, they already left.",
                             "By the time we arrived, they have already left.",
                             "By the time we arrived, they were already left."],
                                "explanation": "The past perfect tense (                had + past participle) is used to show that an action was completed before another action in the past.",
                "vocabulary": ["pluperfect tense", "past perfect", "past action", "had", "past participle"]
            },
            {
                "question": "What is zeugma?",
                "correct_answer": "A figure of speech where a word applies to two others in different ways",
                "distractors": ["A long narrative poem about heroic deeds",
                             "A rhyme scheme with a specific pattern",
                             "A type of sonnet from Italy"],
                                "explanation": "Zeugma is a figure of speech in which a word applies to two others in different ways,                often creating a humorous or dramatic effect. Example: 'She broke his car and his heart.'",
                "vocabulary": ["zeugma", "figure of speech", "rhetoric", "literary device"]
            },
            {
                "question": "What does the phrasal verb 'fall through' mean?",
                "correct_answer": "Fail to happen",
                "distractors": ["Fall to the ground", "Become transparent", "Lose money"],
                "explanation": "In this context, 'fall through' means to fail to happen or be completed as planned.",
                "vocabulary": ["phrasal verb", "fall through", "fail", "context", "plan"]
            },
            {
                "question": "Which of the following is an example of synecdoche?",
                "correct_answer": "All hands on deck.",
                "distractors": ["The wind sang through the trees.",
                             "She's as busy as a bee.", "Time flies when you're having fun."], "explanation": "Synecdoche is a figure of speech in which a part is used to represent the whole or vice                versa. 'All hands on deck' uses 'hands' to represent the entire crew.",
                "vocabulary": ["synecdoche", "figure of speech", "part", "whole", "represent"]
            },
            {
                "question": "What is the difference between 'imply' and 'infer'?",
                                "correct_answer": "'Imply' means to suggest something indirectly,                while 'infer' means to deduce something from evidence.",
                                "distractors": ["'Imply' means to state something directly,                while 'infer' means to suggest something indirectly.",
                             "There is no difference; they are synonyms.",
                                                          "'Imply' is used for written communication,                             while 'infer' is used for spoken communication."],
                                "explanation": "'Imply' is used when the speaker/writer suggests something without saying it directly.                'Infer' is used when the listener/reader deduces something from what is said or written.",
                "vocabulary": ["imply", "infer", "difference", "suggest", "deduce"]
            },
            {
                "question": "Which sentence uses the present subjunctive correctly?",
                "correct_answer": "It is essential that he be present at the meeting.",
                "distractors": ["It is essential that he is present at the meeting.",
                             "It is essential that he was present at the meeting.",
                             "It is essential that he will be present at the meeting."],
                                "explanation": "The present subjunctive is used after certain adjectives (                like 'essential') to express importance or necessity. It uses the base form of the verb regardless of                the subject.",
                "vocabulary": ["present subjunctive", "essential", "importance", "necessity", "base form"]
            },
            {
                "question": "What does the term 'onomatopoeia' mean?",
                "correct_answer": "A word that imitates the sound it represents",
                "distractors": ["A word with multiple meanings",
                             "A word derived from a person's name", "A word that rhymes with another word"], "explanation": "Onomatopoeia is a figure of speech in which words imitate the natural sounds associated                with the objects or actions they refer to. Examples: 'buzz', 'sizzle', 'crackle'.",
                "vocabulary": ["onomatopoeia", "figure of speech", "imitate", "sound", "represent"]
            },
            {
                "question": "What is the meaning of the term 'metonymy'?",
                "correct_answer": "A figure of speech where a related term is used instead of the actual term",
                "distractors": ["A repetition of initial consonant sounds",
                             "A deliberate exaggeration for effect",
                             "A comparison using 'like' or 'as'"],
                                "explanation": "Metonymy is a figure of speech in which a word or phrase is replaced by a related word                or phrase. Example: 'The White House issued a statement' (                using 'White House' to represent the US government).",
                "vocabulary": ["metonymy", "figure of speech", "related term", "represent", "phrase"]
            }
        ]

        # 随机选择模板并生成唯一题目
        template = random.choice(templates)

        # 生成选项并打乱顺序
        options = [template['correct_answer']] + template['distractors']
        random.shuffle(options)

        # 找到正确答案的索引
        answer_index = options.index(template['correct_answer'])

        return {
            "type": "single_choice",
            "difficulty": "expert",
            "question": template['question'],
            "options": options,
            "answer": answer_index,
            "explanation": template['explanation'],
            "vocabulary": template['vocabulary']
        }

    def _generate_japanese_question(self, difficulty, question_type, index):
        """生成日语题目"""
        # 根据难度生成不同的日语题目
        if difficulty == 'beginner':
            templates = [
                {
                    "question": "'猫'の正しい読み方は何ですか?",
                    "correct_answer": "ねこ",
                    "distractors": ["こねこ", "ねこちゃん", "ねこさん"],
                    "explanation": "'猫'は'ねこ'と読みます,意味は'cat'です.",
                    "vocabulary": ["猫", "ねこ", "cat"]
                },
                {
                    "question": "'私は毎日学校に行きます'の意味は何ですか?",
                    "correct_answer": "I go to school every day.",
                    "distractors": ["I went to school yesterday.",
                                 "I will go to school tomorrow.",
                                 "I am going to school now."],
                    "explanation": "'毎日'は'every day'を意味します.",
                    "vocabulary": ["毎日", "学校", "行きます"]
                },
                {
                    "question": "'犬'の英語は何ですか?",
                    "correct_answer": "Dog",
                    "distractors": ["Cat", "Bird", "Fish"],
                    "explanation": "'犬'の英語は'Dog'です.",
                    "vocabulary": ["犬", "dog"]
                },
                {
                    "question": "'こんにちは'の意味は何ですか?",
                    "correct_answer": "Hello",
                    "distractors": ["Goodbye", "Thank you", "Sorry"],
                    "explanation": "'こんにちは'は'Hello'または'Good afternoon'を意味します.",
                    "vocabulary": ["こんにちは", "hello"]
                },
                {
                    "question": "'水'の正しい読み方は何ですか?",
                    "correct_answer": "みず",
                    "distractors": ["すい", "みずうみ", "あめ"],
                    "explanation": "'水'は'みず'と読みます,意味は'water'です.",
                    "vocabulary": ["水", "みず", "water"]
                },
                {
                    "question": "'食べる'の英語は何ですか?",
                    "correct_answer": "Eat",
                    "distractors": ["Drink", "Sleep", "Run"],
                    "explanation": "'食べる'の英語は'Eat'です.",
                    "vocabulary": ["食べる", "eat"]
                },
                {
                    "question": "'日本'の正しい読み方は何ですか?",
                    "correct_answer": "にほん",
                    "distractors": ["にっぽん", "ひのもと", "やまと"],
                    "explanation": "'日本'は'にほん'または'にっぽん'と読みます,意味は'Japan'です.",
                    "vocabulary": ["日本", "にほん", "Japan"]
                },
                {
                    "question": "'ありがとう'の意味は何ですか?",
                    "correct_answer": "Thank you",
                    "distractors": ["Hello", "Goodbye", "Sorry"],
                    "explanation": "'ありがとう'は'Thank you'を意味します.",
                    "vocabulary": ["ありがとう", "thank you"]
                }
            ]
        elif difficulty == 'intermediate':
            templates = [
                {
                    "question": "'昨日は雨が降りました'の意味は何ですか?",
                    "correct_answer": "It rained yesterday.",
                    "distractors": ["It is raining today.",
                                 "It was raining yesterday.",
                                 "It will rain tomorrow."],
                    "explanation": "'昨日'は'yesterday'を意味し、'降りました'は過去形で'rained'を意味します.",
                    "vocabulary": ["昨日", "雨", "降りました"]
                },
                {
                    "question": "'彼女は英語を話せます'の意味は何ですか?",
                    "correct_answer": "She can speak English.",
                    "distractors": ["She speaks English.",
                                 "She will speak English.",
                                 "She spoke English."],
                    "explanation": "'話せます'は'can speak'を意味します.",
                    "vocabulary": ["彼女", "英語", "話せます"]
                },
                {
                    "question": "'勉強しなければなりません'の意味は何ですか?",
                    "correct_answer": "I have to study.",
                    "distractors": ["I study.",
                                 "I studied.",
                                 "I will study."],
                    "explanation": "'なければなりません'は'have to'または'must'を意味します.",
                    "vocabulary": ["勉強", "なければなりません"]
                },
                {
                    "question": "'映画を見に行きます'の意味は何ですか?",
                    "correct_answer": "I am going to watch a movie.",
                    "distractors": ["I watched a movie.",
                                 "I am watching a movie.",
                                 "I will watch a movie."],
                    "explanation": "'見に行きます'は'going to watch'を意味します.",
                    "vocabulary": ["映画", "見る", "行きます"]
                }
            ]
        elif difficulty == 'advanced':
            templates = [
                {
                    "question": "'彼は昨日の夜遅くまで働いていた'の意味は何ですか?",
                    "correct_answer": "He was working until late last night.",
                    "distractors": ["He worked until late last night.",
                                 "He works until late every night.",
                                 "He will work until late tonight."],
                    "explanation": "'ていた'は過去進行形を意味します.",
                    "vocabulary": ["昨日の夜", "遅くまで", "働いていた"]
                },
                {
                    "question": "'この本は読んでおくべきだ'の意味は何ですか?",
                    "correct_answer": "You should read this book in advance.",
                    "distractors": ["You should read this book.",
                                 "You have read this book.",
                                 "You will read this book."],
                    "explanation": "'ておく'は'in advance'または'preparatively'を意味します.",
                    "vocabulary": ["本", "読む", "ておく"]
                },
                {
                    "question": "'その計画は実行可能である'の意味は何ですか?",
                    "correct_answer": "That plan is feasible.",
                    "distractors": ["That plan is difficult.",
                                 "That plan is expensive.",
                                 "That plan is impossible."],
                    "explanation": "'実行可能'は'feasible'または'possible to execute'を意味します.",
                    "vocabulary": ["計画", "実行可能", "である"]
                },
                {
                    "question": "'彼女はその問題を解決できた'の意味は何ですか?",
                    "correct_answer": "She was able to solve that problem.",
                    "distractors": ["She can solve that problem.",
                                 "She will be able to solve that problem.",
                                 "She is solving that problem."],
                    "explanation": "'できた'は'was able to'または'succeeded in'を意味します.",
                    "vocabulary": ["問題", "解決する", "できた"]
                }
            ]
        else:
            templates = [
                {
                    "question": "'この法律は国民の権利を保障するものである'の意味は何ですか?",
                    "correct_answer": "This law is to guarantee the rights of citizens.",
                    "distractors": ["This law is to explain the rights of citizens.",
                                 "This law is to limit the rights of citizens.",
                                 "This law is to remove the rights of citizens."],
                    "explanation": "'保障する'は'guarantee'または'protect'を意味します.",
                    "vocabulary": ["法律", "国民", "権利", "保障する"]
                },
                {
                    "question": "'その理論は実験的に証明されている'の意味は何ですか?",
                    "correct_answer": "That theory has been proven experimentally.",
                    "distractors": ["That theory is being proven experimentally.",
                                 "That theory was proven experimentally.",
                                 "That theory will be proven experimentally."],
                    "explanation": "'されている'は現在進行形受け身を意味します.",
                    "vocabulary": ["理論", "実験的に", "証明されている"]
                },
                {
                    "question": "'彼の発言は社会に大きな影響を与えた'の意味は何ですか?",
                    "correct_answer": "His remarks had a great impact on society.",
                    "distractors": ["His remarks are having a great impact on society.",
                                 "His remarks will have a great impact on society.",
                                 "His remarks have a great impact on society."],
                    "explanation": "'与えた'は'had'を意味します.",
                    "vocabulary": ["発言", "社会", "影響", "与えた"]
                },
                {
                    "question": "'この政策は経済成長を促進することを目的としている'の意味は何ですか?",
                    "correct_answer": "This policy aims to promote economic growth.",
                    "distractors": ["This policy promoted economic growth.",
                                 "This policy will promote economic growth.",
                                 "This policy promotes economic growth."],
                    "explanation": "'目的としている'は'aims to'または'is intended to'を意味します.",
                    "vocabulary": ["政策", "経済成長", "促進", "目的"]
                }
            ]

        template = random.choice(templates)
        options = [template['correct_answer']] + template['distractors']
        random.shuffle(options)
        answer_index = options.index(template['correct_answer'])

        return {
            "type": "single_choice",
            "difficulty": difficulty,
            "question": template['question'],
            "options": options,
            "answer": answer_index,
            "explanation": template['explanation'],
            "vocabulary": template['vocabulary']
        }

    def _generate_generic_question(self, subject, difficulty, question_type, index):
        """生成通用题目模板"""
        question = f"What is the {subject} concept related to {difficulty} level?"
        correct_answer = f"Correct answer for {subject} {difficulty}"
        
        distractors = [
            f"Similar but wrong answer A for {subject}",
            f"Similar but wrong answer B for {subject}",
            f"Similar but wrong answer C for {subject}",
        ]
        options = [correct_answer] + distractors
        random.shuffle(options)
        answer_index = options.index(correct_answer)

        return {
            "type": question_type,
            "difficulty": difficulty,
            "question": question,
            "options": options,
            "answer": answer_index,
            "explanation": f"This is the explanation for the {subject} question #{index}.",
            "vocabulary": [subject, difficulty, "question"]
        }

    def generate_listening_question(self, subject, difficulty, count=5, auto_save=True):
        """生成听力题目 Args: subject: 科目(english, japanese) difficulty: 难度(beginner, intermediate, advanced, expert) count: 生成的听力材料数量 auto_save: 是否自动保存到数据库 Returns: 听力题列表 """
        logger.info(f"生成 {count} 段{subject}{difficulty}难度的听力题")

        listening_questions = []

        for i in range(count):
            # 生成听力材料
            audio_content = self._generate_audio_content(subject, difficulty)
            # 生成对应数量的理解题
            questions_per_audio = self.listening_config['questions_per_audio'][difficulty]
            comprehension_questions = self._generate_comprehension_questions(
                audio_content, subject, difficulty, questions_per_audio
            )

            # 对听力内容进行自动分类和难度评估
            content_analysis = self._classify_listening_content(audio_content, subject)

            listening_question = {
                "question_id": f"listening_{uuid.uuid4().hex[:12]}",
                "type": "listening",
                "difficulty": difficulty,
                "subject": subject,
                "audio_content": audio_content,
                "comprehension_questions": comprehension_questions,
                "classification": content_analysis['classification'],
                "classification_confidence": content_analysis['confidence'],
                "feedback_history": []
            }
            listening_questions.append(listening_question)
            # 自动保存到数据库
            if auto_save:
                try:
                    from app.models.ai_brain import AIBrainKnowledge

                    # 创建知识条目
                    knowledge = AIBrainKnowledge(
                        title=f"听力题: {audio_content['title']}",
                        content=str(listening_question),
                        knowledge_type='listening_question',
                        source='AI生成',
                        source_id=listening_question['question_id'],
                        tags=['听力题', subject, difficulty, audio_content.get('scenario', 'general')],
                        priority=5,
                        is_active=True
                    )
                    knowledge.save()
                    logger.info(f"成功保存听力题到数据库: {listening_question['question_id']}")
                except Exception as db_error:
                    logger.error(f"保存听力题到数据库失败: {str(db_error)}")

        logger.info(f"成功生成 {len(listening_questions)} 段听力题,每段包含 {questions_per_audio} 个理解题")
        return listening_questions

    def _classify_listening_content(self, audio_content, subject):
        """对听力内容进行自动分类和难度评估 Args: audio_content: 听力音频内容 subject: 科目(english, japanese) Returns: 包含分类和难度评估的字典 """
        try:
            # 导入AI服务管理器
            from ai_service import ai_service_manager

            transcript = audio_content['transcript']

            # 使用AI进行分类
            classification_prompt = f"对以下{subject}听力文本进行分类,类别包括:日常对话、新闻报道、学术讲座、商务会议、访谈、故事、广告等.\n\n听力文本:{transcript}"
            classification_result = ai_service_manager.infer('default_text_gen', classification_prompt, subject=subject)

            difficulty_prompt = f"评估以下{subject}听力文本的难度级别,从beginner、intermediate、advanced、expert中选择一个,并给出简短理由.\n\n听力文本:{transcript}"
            difficulty_result = ai_service_manager.infer('default_text_gen', difficulty_prompt, subject=subject)

            # 解析分类结果
            classification = classification_result['result'].strip()
            # 解析难度评估结果
            difficulty_assessment = difficulty_result['result'].strip()

            logger.info(f"听力内容分类结果:{classification}")
            logger.info(f"听力内容难度评估:{difficulty_assessment}")

            return {
                'classification': classification,
                'difficulty_assessment': difficulty_assessment,
                'confidence': 0.9  # 假设AI评估的置信度为0.9
            }
        except Exception as e:
            logger.warning(f"AI分类和难度评估失败,使用默认分类: {str(e)}")
            # AI分类失败时,使用默认分类
            default_categories = ['日常对话', '新闻报道', '学术讲座', '商务会议', '访谈', '故事', '广告']
            return {
                'classification': random.choice(default_categories),
                'difficulty_assessment': 'intermediate',  # 默认难度为中级
                'confidence': 0.5  # 默认置信度为0.5
            }

    def update_listening_question_based_on_feedback(self, question_id, feedback):
        """根据用户反馈更新听力题,实现自动升级机制 Args: question_id: 听力题ID feedback: 用户反馈,包含以下字段: - difficulty_feedback: 难度反馈(-1: 太难, 0: 适中, 1: 太简单) - accuracy: 用户答对率 - confusion_points: 用户感到困惑的地方 Returns: 更新后的听力题信息 """
        try:
            logger.info(f"根据用户反馈更新听力题: {question_id}")
            # 导入AI服务管理器和学习系统
            from ai_service import ai_service_manager
            from ai_learning_system import AILearningSystem
            from ai_service import ai_service_manager as ai_manager

            # 初始化学习系统
            ai_learning_system = AILearningSystem(ai_manager)

            # 从数据库获取当前听力题
            try:

                # 获取所有听力题
                all_listening_questions = AIBrainKnowledge.get_all(knowledge_type='listening_question')
                current_question = None

                for knowledge in all_listening_questions:
                    question_data = _safe_parse(knowledge.content)
                    if question_data.get('question_id') == question_id:
                        current_question = question_data
                        current_knowledge = knowledge
                        break

                    # 尝试从试卷中查找听力题
                    all_exams = AIBrainKnowledge.get_all(knowledge_type='personalized_exam')
                    for exam_knowledge in all_exams:
                        exam_data = _safe_parse(exam_knowledge.content)
                        if 'questions' in exam_data:
                                if question.get('question_id') == question_id and question.get('type') == 'listening':
                                    current_question = question
                        if current_question:
                            break

                if not current_question:
                    return {
                        "success": False,
                        "message": f"未找到听力题: {question_id}"
                    }

            except Exception as db_error:
                logger.error(f"从数据库获取听力题失败: {str(db_error)}")
                current_question = {
                    "question_id": question_id,
                    "type": "listening",
                    "difficulty": "intermediate",
                    "subject": "english",
                    "audio_content": {
                    },
                    "comprehension_questions": []
                }

            # 生成改进建议
            improvement_prompt += f"当前听力题:{str(current_question)}\n\n"
            improvement_prompt += f"用户反馈:{str(feedback)}\n\n"
            improvement_prompt += "请生成改进后的听力题,包括改进后的听力文本和理解题.确保输出格式清晰,易于解析."


            if improvement_result['success']:
                improved_content = improvement_result['result']
                logger.info(f"成功生成改进后的听力题内容")
                # 根据反馈调整难度
                current_difficulty = current_question['difficulty']
                difficulty_levels = ['beginner', 'intermediate', 'advanced', 'expert']
                current_level_index = difficulty_levels.index(current_difficulty)
                # 根据难度反馈调整难度
                if feedback['difficulty_feedback'] == -1 and current_level_index > 0:
                    # 太难,降低难度
                    new_difficulty = difficulty_levels[current_level_index - 1]
                    # 太简单,提高难度
                    new_difficulty = difficulty_levels[current_level_index + 1]
                else:
                    # 难度适中,保持不变
                    new_difficulty = current_difficulty

                # 生成新的听力题
                new_listening_question = self.generate_listening_question(
                    subject=current_question.get('subject', 'english'),
                    difficulty=new_difficulty,
                    count=1
                )[0]

                new_listening_question['question_id'] = question_id
                new_listening_question['original_question_id'] = question_id
                new_listening_question['updated_at'] = datetime.now().isoformat()
                new_listening_question['feedback_history'] = current_question.get('feedback_history', [])
                new_listening_question['feedback_history'].append({
                    'feedback_time': datetime.now().isoformat(),
                    'old_difficulty': current_difficulty,
                    'new_difficulty': new_difficulty
                })

                # 将改进后的题目保存到数据库
                try:
                    from app.models.ai_brain import AIBrainKnowledge

                    # 创建或更新知识条目
                    if current_knowledge:
                        # 更新现有条目
                        current_knowledge.content = str(new_listening_question)
                        current_knowledge.save()
                        logger.info(f"成功更新听力题到数据库: {question_id}")
                    else:
                        # 创建新条目
                        new_knowledge = AIBrainKnowledge(
                            knowledge_id=f"knowledge-{uuid.uuid4().hex[:8]}",
                            content=str(new_listening_question),
                            knowledge_type='listening_question',
                            source='AI生成',
                            source_id=question_id,
                            tags=['听力题', new_listening_question['subject'], new_difficulty],
                            priority=5,
                            is_active=True
                        )
                        new_knowledge.save()
                        logger.info(f"成功保存改进后的听力题到数据库: {question_id}")
                except Exception as db_error:
                    logger.error(f"保存听力题到数据库失败: {str(db_error)}")

                # 将改进建议添加到知识库
                ai_learning_system.add_knowledge(
                    content=f"听力题 {question_id} 改进建议: {improved_content}",
                    source="user_feedback",
                    confidence=0.85,
                    tags={"listening_question_improvement", "user_feedback", new_difficulty},
                    metadata={
                        "question_id": question_id,
                        "feedback": feedback,
                        "improvement_time": datetime.now().isoformat(),
                        "old_difficulty": current_difficulty,
                        "new_difficulty": new_difficulty
                    }
                )

                return {
                    "success": True,
                    "message": "听力题已根据用户反馈更新",
                    "improved_question": new_listening_question,
                    "old_difficulty": current_difficulty,
                    "new_difficulty": new_difficulty
                }
            else:
                logger.error("AI生成改进建议失败")
                return {
                    "success": False,
                    "message": "AI生成改进建议失败"
                }
        except Exception as e:
            logger.error(f"更新听力题失败: {str(e)}")
            return {
                "success": False,
                "message": f"更新听力题失败: {str(e)}"
            }

    def _generate_audio_content(self, subject, difficulty):
        """生成听力音频内容,包括可播放的音频文件 Args: subject: 科目(english, japanese) difficulty: 难度(beginner, intermediate, advanced, expert) Returns: 听力音频内容信息,包含可播放的音频文件URL """
        # 获取该难度对应的音频时长范围
        duration_range = self.listening_config['audio_duration_ranges'][difficulty]
        duration = random.randint(duration_range[0], duration_range[1])

        # 定义不同场景和口音
        scenarios = {
            'english': [
                "Daily Conversation", "Business Meeting", "News Report", "Academic Lecture",
                "TED Talk", "Interview", "Podcast", "Tour Guide", "Customer Service",
                "Emergency Situation", "Weather Forecast", "Radio Show", "Lecture",
                "Debate", "Storytelling", "Phone Call"
            ],
            'japanese': [
                "日常会話", "ビジネスミーティング", "ニュース報道", "大学講義",
                "講演", "インタビュー", "ポッドキャスト", "観光ガイド", "カスタマーサービス",
                "緊急状況", "天気予報", "ラジオ番組", "講義",
                "討論", "物語", "電話"
            ]
        }

        # 定义口音
        accents = {
            'english': ["American", "British", "Australian", "Canadian", "Indian", "Chinese", "Japanese", "Spanish"],
            'japanese': ["東京", "大阪", "京都", "福岡", "北海道", "名古屋", "沖縄", "外国語アクセント"]
        }

        # 定义TTS语音配置
        tts_voices = {
            'english': {
                'American': 'en-US-Wavenet-D',
                'British': 'en-GB-Wavenet-C',
                'Australian': 'en-AU-Wavenet-B',
                'Canadian': 'en-CA-Wavenet-A',
                'Indian': 'en-IN-Wavenet-A',
                'Japanese': 'en-US-Wavenet-F',
                'Spanish': 'en-US-Wavenet-H'
            },
            'japanese': {
                '東京': 'ja-JP-Wavenet-A',
                '京都': 'ja-JP-Wavenet-C',
                '福岡': 'ja-JP-Wavenet-D',
                '北海道': 'ja-JP-Wavenet-A',
                '名古屋': 'ja-JP-Wavenet-B',
                '沖縄': 'ja-JP-Wavenet-C',
                '外国語アクセント': 'ja-JP-Wavenet-D'
            }
        }

        # 生成音频标题和内容
        if subject == 'english':
            # 随机选择场景
            scenario = random.choice(scenarios[subject])
            accent = random.choice(accents[subject])

            # 根据场景和难度生成标题
            audio_titles = {
                'beginner': [f"{scenario}: At a Coffee Shop", f"{scenario}: Asking for Directions",
                f"{scenario}: Ordering Food"],
                'intermediate': [f"{scenario}: Discussion", f"{scenario}: Report", f"{scenario}: Excerpt"],
                'advanced': [f"{scenario}: Talk on Technology", f"{scenario}: Lecture on Psychology",
                f"{scenario}: Legal Discussion"],
                'expert': [f"{scenario}: Research Presentation", f"{scenario}: Philosophical Debate",
                f"{scenario}: Complex Negotiation"]
            }

            # 生成听力文本
            transcript = self._generate_transcript(subject, difficulty)

            # 生成可播放的音频文件
            audio_file_path, audio_url = self._text_to_speech(transcript, subject, accent, tts_voices[subject][accent])

            audio_content = {
                "id": f"audio_{uuid.uuid4().hex[:12]}",
                "title": random.choice(audio_titles[difficulty]),
                "duration": duration,
                "format": "mp3",
                "description": f"English {difficulty} level listening material about {scenario} with {accent} accent",
                "transcript": transcript,
                "file_path": audio_file_path,
                "url": audio_url,
                "scenario": scenario,
                "accent": accent
            }
            return audio_content
        elif subject == 'japanese':
            # 随机选择场景
            scenario = random.choice(scenarios[subject])
            accent = random.choice(accents[subject])

            # 根据场景和难度生成标题
            audio_titles = {
                'beginner': [f"{scenario}: コーヒーショップで", f"{scenario}: 道を尋ねる", f"{scenario}: 食べ物の注文"],
                'intermediate': [f"{scenario}: ディスカッション", f"{scenario}: レポート", f"{scenario}: 講義抜粋"],
                'advanced': [f"{scenario}: テック講演", f"{scenario}: 心理学講義", f"{scenario}: 法律議論"],
                'expert': [f"{scenario}: 科学研究発表", f"{scenario}: 哲学的討論", f"{scenario}: 複雑な交渉"]
            }

            # 生成听力文本
            transcript = self._generate_transcript(subject, difficulty)

            audio_file_path, audio_url = self._text_to_speech(transcript, subject, accent, tts_voices[subject][accent])

            audio_content = {
                "title": random.choice(audio_titles[difficulty]),
                "duration": duration,
                "format": "mp3",
                "description": f"日本語 {difficulty} レベルの聴解教材 - {scenario} ({accent}アクセント)",
                "transcript": transcript,
                "file_path": audio_file_path,
                "url": audio_url,
                "scenario": scenario,
                "accent": accent
            }
        else:
            scenario = "General"
            accent = "Neutral"

            # 生成听力文本
            transcript = self._generate_transcript(subject, difficulty)

            # 生成可播放的音频文件
            audio_file_path, audio_url = self._text_to_speech(transcript, subject, accent, "en-US-Wavenet-D")

            audio_content = {
                "id": f"audio_{uuid.uuid4().hex[:12]}",
                "title": f"{subject} Listening Material - {scenario}",
                "duration": duration,
                "format": "mp3",
                "description": f"{subject} {difficulty} level listening material about {scenario}",
                "transcript": transcript,
                "file_path": audio_file_path,
                "url": audio_url,
                "scenario": scenario,
                "accent": accent
            }

        return audio_content

    def _generate_transcript(self, subject, difficulty):
        """生成听力材料的文本内容,使用AI服务增强 Args: subject: 科目(english, japanese) difficulty: 难度(beginner, intermediate, advanced, expert) Returns: 听力材料的文本内容 """
        try:
            # 导入AI服务管理器

            # 使用AI生成听力文本
            ai_prompt = f"生成{subject}的{difficulty}难度听力文本,长度适中,适合作为听力测试材料."
            ai_result = ai_service_manager.infer('default_text_gen', ai_prompt, subject=subject, difficulty=difficulty)

            if ai_result['success']:
                logger.info(f"使用AI成功生成{subject} {difficulty}难度听力文本")
                return ai_result['result']
        except Exception as e:
            logger.warning(f"AI生成听力文本失败,使用默认文本: {str(e)}")

        # AI生成失败时,使用默认的文本库
        if subject == 'english':
            transcripts = {
                'beginner': [
                    "Speaker A: Hi, how are you today?\nSpeaker B: I'm doing well, thank you. And you?\nSpeaker A: I'm great. Would you like a coffee?\nSpeaker B: Yes, please. That would be nice.\nSpeaker A: What kind of coffee do you prefer?\nSpeaker B: I like black coffee with a little sugar.\nSpeaker A: Coming right up!", "Excuse me, could you tell me how to get to the nearest library?\nCertainly. Go straight ahead for one block, then turn right at the bookstore. The library will be on your left, next to the park.\nThank you very much!\nYou're welcome. Have a nice day!", "Waiter: Good morning! Welcome to our café. What can I get for you today?\nCustomer: Good morning! I'd like a latte and a blueberry muffin, please.\nWaiter: Sure thing. Would you like anything else?\nCustomer: No, that's all. Thank you.\nWaiter: Your order will be ready in a few minutes." ],
                'intermediate': [
                    "Host: Welcome to our program. Today we're talking about sustainable living. Our guest is environmental scientist Dr. Sarah Johnson. Dr. Johnson, thank you for joining us.\nDr. Johnson: Thank you for having me.\nHost: What are some simple ways people can live more sustainably?\nDr. Johnson: Well, there are many small changes we can make. For example, reducing single-use plastics, conserving water, and using public transportation or biking instead of driving. Also, supporting local farmers by buying locally grown food can have a big impact.\nHost: That's great advice. Thank you for sharing your insights with us.\nDr. Johnson: You're welcome.", "News Reporter: Breaking news. A new study has found that regular exercise can improve cognitive function in older adults. The research, conducted over a five-year period, followed 2, 000 adults aged 65 and older. Participants who engaged in moderate exercise for at least 30 minutes a day showed a 20% improvement in memory and problem-solving skills compared to those who were sedentary. Experts say this highlights the importance of staying physically active throughout our lives.\nAnchor: Thank you for that report. In other news...",
                    "Tour Guide: Welcome to the National History Museum. My name is Emily and I'll be your guide today. Our tour will last approximately two hours and cover the main exhibits, including the dinosaur fossils, ancient civilizations, and natural history collections. Please feel free to ask questions at any time. Let's begin our tour in the dinosaur hall, where you'll see some of the most complete dinosaur skeletons ever discovered." ],
                'advanced': [
                    "Professor: Today we're going to explore the concept of artificial intelligence and its implications for society. AI systems are becoming increasingly sophisticated, with applications ranging from autonomous vehicles to medical diagnostics. However, this rapid advancement raises important ethical questions. For instance, how do we ensure AI systems are fair and unbiased? How do we address concerns about job displacement? And what are the privacy implications of AI-powered surveillance? These are complex issues that require thoughtful consideration from policymakers, technologists, and society as a whole.\nStudent: Professor, do you think AI will eventually surpass human intelligence?\nProfessor: That's a fascinating question. While some experts believe in the possibility of artificial general intelligence, others are more skeptical. What we can say with certainty is that AI will continue to transform many aspects of our lives, and we need to be proactive in shaping that transformation.",
                    "Podcast Host: Today we're discussing the future of work in a post-pandemic world. Our guests are career coach Maria Garcia and economist Dr. James Chen. Maria, let's start with you. How has the pandemic changed the way we work?\nMaria: The pandemic accelerated trends that were already emerging, such as remote work and digital transformation. Many companies that were hesitant to adopt remote work models were forced to do so, and now many are embracing hybrid work arrangements. This has given employees more flexibility but also presents challenges in terms of collaboration and company culture.\nDr. Chen: From an economic perspective, we've seen a shift in demand for certain skills. Jobs that require digital literacy and adaptability are in high demand, while some traditional roles are declining. This highlights the importance of continuous learning and upskilling.\nHost: Thank you both for your insights.", "TED Speaker: Imagine a world where renewable energy is the primary source of power, where cities are designed for people rather than cars, and where technology is used to solve our most pressing challenges. This isn't a distant utopia—it's a future we can create if we act now. The transition to a sustainable future requires innovation, collaboration, and political will. But the benefits are enormous: cleaner air, healthier communities, and a more resilient planet for future generations. We all have a role to play in building this future, whether it's through our daily choices or our advocacy for systemic change. Let's work together to create a world that works for everyone." ],
                'expert': [
                    "Keynote Speaker: The intersection of quantum computing and cryptography represents one of the most exciting frontiers in technology today. Quantum computers have the potential to solve certain problems exponentially faster than classical computers, which could render many of our current encryption methods obsolete. This has led to the development of post-quantum cryptography—mathematical algorithms that are believed to be secure against quantum attacks. As we stand on the brink of the quantum era, it's crucial that we prepare our digital infrastructure for this transition. Governments, businesses, and researchers must collaborate to develop and implement quantum-resistant encryption standards to protect our data and communication systems.\nModerator: Thank you for that thought-provoking keynote. We'll now open the floor for questions.",
                    "Panelist 1: The philosophy of consciousness has long fascinated philosophers and scientists alike. Recent advancements in neuroscience have given us unprecedented insights into the brain, but the hard problem of consciousness—explaining how subjective experiences arise from physical processes—remains unsolved.\nPanelist 2: I agree. While we've made progress in understanding the neural correlates of consciousness, we still don't have a comprehensive theory that explains why certain brain processes give rise to conscious experience.\nPanelist 3: Some researchers argue that consciousness is an emergent property of complex systems, while others propose panpsychism—the idea that consciousness is a fundamental property of the universe. Regardless of the approach, the study of consciousness continues to challenge our understanding of reality.\nModerator: This has been a stimulating discussion. Thank you to all our panelists.",
                    "Lecture: The human microbiome—the collection of microorganisms that live in and on our bodies—plays a crucial role in our health and well-being. Recent research has revealed that the microbiome influences everything from digestion and immunity to mental health and cognitive function. Disruptions to the microbiome, known as dysbiosis, have been linked to a range of conditions, including obesity, diabetes, and even depression. This has led to growing interest in microbiome-based therapies, such as probiotics, prebiotics, and fecal microbiota transplantation. As we continue to unravel the complexities of the microbiome, we're gaining new insights into human health and disease that could revolutionize medicine."
                ]
            }
        elif subject == 'japanese':
            transcripts = {
                'beginner': [
                    "A: こんにちは.お名前は何ですか?\nB: はい、私は佐藤です.あなたは?\nA: 私は鈴木です.どうぞよろしくお願いします.\nB: こちらこそ、よろしくお願いします.",
                    "店員: いらっしゃいませ.何をお探しですか?\nお客: すみません、ペンを買いたいです.\n店員: はい、ペンはこちらです.どの種類がよろしいですか?\nお客: 黒いボールペンをお願いします.\n店員: はい、こちらになります.", "学生A: 明日の授業は何時からですか?\n学生B: 9時からです.教室は302号室ですよ.\n学生A: ありがとう.宿題はありますか?\n学生B: はい、第5課の練習問題をしてください.\n学生A: わかりました.ありがとうございます." ],
                'intermediate': [
                    "アナウンサー: こんにちは、東京の天気予報です.今日は午前中は晴れですが、午後から曇りになり、夕方には小雨が降る予定です.明日は全天的に晴れの予報で、最高気温は25度になるでしょう.週末は台風の影響で大雨が予想されるので、外出の際は注意が必要です.", "先生: 今日の授業では、日本の歴史について勉強します.特に江戸時代の社会構造に焦点を当てます.江戸時代は約260年間、幕府によって統治されました.当時の社会は士農工商という四つの階級に分けられていました.士は武士、農は農民、工は職人、商は商人です.この階級制度は非常に厳しく、階級間の移動はほとんど不可能でした.\n生徒: 先生、なぜこのような制度が作られたのですか?\n先生: 幕府は社会の安定を維持するために、この階級制度を導入しました.しかし、時代が進むにつれて、この制度は問題を引き起こすようになりました.", "インタビューア: 今日は、日本の伝統芸能である歌舞伎についてお話を聞かせてください.\n専門家: はい、歌舞伎は約400年の歴史を持つ伝統的な演劇です.当初は女性演員によって演じられていましたが、現在は男性演員だけが出演しています.歌舞伎の特徴は、華やかな衣装、厚化粧、そして独特の演技スタイルです.また、舞台装置も非常に巧妙で、回転舞台や引き幕などが使用されます.近年は、若い観客を惹きつけるために、現代的な要素を取り入れた新作も上演されています." ],
                'advanced': [
                    "講演者: 日本の経済は、高度経済成長期を経て、世界第3位の経済規模を持つ国となりました.しかし、近年は少子高齢化の進展、グローバル競争の激化、そして環境問題など、多くの課題に直面しています.特に少子高齢化は、労働力不足、社会保障負担の増大、地方自治体の財政難など、様々な問題を引き起こしています.これらの課題を解決するためには、創造的な政策と国民の協力が必要です.例えば、女性の社会進出を促進し、外国人労働者の受け入れを拡大することで、労働力不足を緩和することができます.また、技術革新を推進し、持続可能な成長を目指すことも重要です.\n聴衆: 講演者様、日本の経済は今後どのような道をたどると思いますか?\n講演者: 日本は技術力と高い教育水準を持っているので、それらを活かして、新しい産業を創出し、経済を活性化させることができると信じています.特に、AI、ロボット工学、再生可能エネルギーなどの分野では、大きな可能性があります.", "作家: 日本の文学は、四季の移り変わりを美しく表現することで知られています.特に俳句は、17音で季節感を表現する短い詩で、季語と呼ばれる季節を示す言葉を必ず含みます.例えば、春を表す季語には「桜」「春分の日」などがあり、夏には「蝉」「七夕」などがあります.このように、日本文学は自然との調和を重視し、微妙な感情を繊細に表現することを特徴としています.\n読者: 作家様、現代の日本文学はどのようなテーマが流行していますか?\n作家: 現代では、少子高齢化、家族関係、個性と社会の関係など、現代社会の問題を取り上げた作品が多くなっています.また、国際化の進展に伴い、異文化交流をテーマにした作品も増えています.しかし、自然との関わり合いを表現する作品は依然として人気があります." ],
                'expert': [
                    "京都大学教授: 日本の文化は、神道と仏教の影響を強く受けています.神道は日本固有の宗教で、自然崇拝を基盤としています.一方、仏教は6世紀に中国から伝来し、様々な宗派が発展しました.これら二つの宗教は、日本の文化、芸術、生活様式に深い影響を与えてきました.例えば、神社は神道の信仰の場であり、寺院は仏教の信仰の場ですが、多くの日本人は両方を信仰しています.また、お正月には神社に初詣に行き、お盆には仏壇で先祖を祭るなど、日常生活の中で両方の宗教的習慣を取り入れています.このような宗教の融合は、日本文化の特徴の一つと言えます.\n聴衆: 教授様、現代の日本人の宗教観はどのようなものですか?\n教授: 現代の日本人は、宗教を形式的な儀式として捉える傾向が強く、明確な宗教的信念を持っている人は少なくなっています.しかし、人生の節目や困難な時には、宗教的な儀式や祈りを求めることが多いです.このような宗教観は、日本文化の柔軟性と包容力を反映していると思います.", "東京大学准教授: 日本語の文法は、主語が省略されることが多いことで知られています.これは、コンテキストから主語が明らかである場合に、主語を省略することが自然だと考えられているからです.また、日本語は述語が文の末尾に来るSOV型言語です.これに対して、英語はSVO型言語で、主語-動詞-目的語の順序です.この文法的な違いは、日本人と英語話者の思考様式の違いを反映していると言われています.例えば、日本語話者は文脈を重視し、相手の理解を信じる傾向があります.一方、英語話者は明確な表現を重視し、主語を省略することが少ないです.\n学生: 准教授様、このような文法的な違いは、異文化コミュニケーションにどのような影響を与えますか?\n准教授: 異文化コミュニケーションにおいては、このような文法的な違いが誤解を引き起こすことがあります.例えば、日本人が主語を省略して話すと、英語話者は何を言っているのか理解できない場合があります.逆に、英語話者が明確に主語を言うと、日本人は不必要に断定的に感じる場合があります.このような誤解を避けるためには、相手の言語と文化を理解することが重要です.", "日本文化研究所所長: 日本の伝統建築は、自然との調和を重視しています.例えば、和室は畳敷きで、障子や襖で空間を柔軟に区切ることができます.また、庭園は自然を模して作られ、四季の変化を楽しむことができます.このような建築様式は、日本の気候や地理的条件に合わせて発展してきました.例えば、日本は地震が多い国であるため、建物は柔軟な構造になっています.また、高温多湿な夏に対応するため、風通しの良い設計が採用されています.近年は、伝統的な建築様式と現代の建築技術を融合させた建物が多くなっています.これは、伝統を尊重しながら、現代の生活スタイルに対応するための試みです.\n記者: 所長様、日本の伝統建築は今後どのように発展していくと思いますか?\n所長: 環境問題が重要視される今、日本の伝統建築の思想である「自然との調和」は、現代の建築に大きな影響を与えるでしょう.例えば、自然エネルギーを活用する建築や、環境に優しい材料を使用する建築など、伝統的な思想を現代の技術で実現する試みが増えています.このような建築は、地球環境問題に対応する上で重要な役割を果たすと思います."
                ]
            }
        else:
            transcripts = {
                'beginner': ["Basic conversation in {subject}.", "Simple questions and answers in {subject}."],
                'intermediate': ["Intermediate discussion in {subject}.", "News report in {subject}."],
                'advanced': ["Advanced lecture in {subject}.", "Complex debate in {subject}."],
                'expert': ["Expert presentation in {subject}.", "Professional discussion in {subject}."]
            }

        # 根据难度选择合适的文本
        return random.choice(transcripts.get(difficulty, transcripts['beginner']))

    def _generate_comprehension_questions(self, audio_content, subject, difficulty, count):
        """为听力材料生成理解题,使用AI服务增强 Args: audio_content: 听力音频内容 subject: 科目(english, japanese) difficulty: 难度(beginner, intermediate, advanced, expert) count: 生成的理解题数量 Returns: 理解题列表 """
        comprehension_questions = []

        try:
            # 导入AI服务管理器
            from ai_service import ai_service_manager

            # 使用AI生成理解题
            ai_prompt = f"基于以下{subject}听力文本,生成{count}个{difficulty}难度的理解题,包括单选题和多选题, 每题包含问题、选项和正确答案.\n\n听力文本:{audio_content['transcript']}"
            ai_result = ai_service_manager.infer('default_text_gen', ai_prompt, subject=subject, difficulty=difficulty)

            if ai_result['success']:
                logger.info(f"使用AI成功生成{count}个{subject} {difficulty}难度理解题")
                ai_questions = ai_result['result']

                # 解析AI生成的题目(这里简化处理,实际应用中需要更复杂的解析)
                # 假设AI生成的题目格式为:
                # 选项B: 选项内容
                # 选项C: 选项内容
                # 选项D: 选项内容
                # 正确答案: A
                # 解析: 解析内容

                for i in range(count):
                    # 随机选择题型
                    question_type = random.choice(self.listening_config['question_types'])

                    if question_type == 'single_choice':
                        question = self._generate_single_choice_comprehension_question(
                            audio_content, subject, difficulty, i+1
                        )
                    elif question_type == 'multiple_choice':
                        question = self._generate_multiple_choice_comprehension_question(
                            audio_content, subject, difficulty, i+1
                        )
                    elif question_type == 'fill_in_blank':
                        question = self._generate_fill_in_blank_comprehension_question(
                            audio_content, subject, difficulty, i+1
                        )
                    elif question_type == 'short_answer':
                        question = self._generate_short_answer_comprehension_question(
                            audio_content, subject, difficulty, i+1
                        )
                    else:
                        question = self._generate_single_choice_comprehension_question(
                            audio_content, subject, difficulty, i+1
                        )
                    comprehension_questions.append(question)

                return comprehension_questions
        except Exception as e:
            logger.warning(f"AI生成理解题失败,使用默认方法: {str(e)}")

        # AI生成失败时,使用默认的生成方法
        for i in range(count):
            # 随机选择题型
            question_type = random.choice(self.listening_config['question_types'])

            if question_type == 'single_choice':
                question = self._generate_single_choice_comprehension_question(
                    audio_content, subject, difficulty, i+1
                )
            elif question_type == 'multiple_choice':
                question = self._generate_multiple_choice_comprehension_question(
                )
            elif question_type == 'fill_in_blank':
                question = self._generate_fill_in_blank_comprehension_question(
                    audio_content, subject, difficulty, i+1
                )
            elif question_type == 'short_answer':
                question = self._generate_short_answer_comprehension_question(
                    audio_content, subject, difficulty, i+1
                )
            else:
                question = self._generate_single_choice_comprehension_question(
                    audio_content, subject, difficulty, i+1
                )

            comprehension_questions.append(question)

        return comprehension_questions

    def _generate_single_choice_comprehension_question(self, audio_content, subject, difficulty, index):
        """生成单项选择理解题 Args: audio_content: 听力音频内容 subject: 科目(english, japanese) difficulty: 难度(beginner, intermediate, advanced, expert) index: 题目索引 Returns: 单项选择理解题 """
        # 生成问题(模拟)
        if subject == 'english':
            questions = [
                f"What did Speaker A offer to Speaker B?",
                f"Where is the nearest subway station located?",
                f"What did the customer order for dinner?",
                f"Where was the new butterfly species discovered?",
                f"What is cognitive dissonance?",
                f"How long has the speaker been studying English?",
                f"What is the main topic of the lecture?",
                f"Who discovered the new species?",
                f"What is the effect of the new policy?",
                f"What does the speaker suggest doing?",
                f"What time does the meeting start?",
                f"Where will the event take place?",
                f"Why did the speaker miss the deadline?",
                f"What does the term 'AI' stand for?",
                f"What is the speaker's opinion on climate change?", f"How many people attended the conference?",
            ]
            options_list = [
                ["A cup of tea", "A coffee", "A glass of water", "A sandwich"],
                ["Grilled salmon with rice", "Chicken curry", "Vegetable soup", "Pasta with sauce"],
                ["New marketing campaign", "Price reduction", "New product launch", "Expanded distribution"],
                ["Amazon rainforest", "African savanna", "Australian desert", "Asian jungle"],
                ["For two years", "For three years", "For four years", "For five years"],
                ["Climate change", "Artificial intelligence", "Space exploration", "Global economy"],
                ["Scientists", "Teachers", "Engineers", "Doctors"],
                ["Increased productivity", "Higher costs", "Reduced quality", "Longer delivery times"],
                ["Buying a new car", "Taking a vacation", "Investing in stocks", "Starting a business"],
                ["Colleagues", "Friends", "Family members", "Strangers"],
                ["At 9:00 AM", "At 10:00 AM", "At 11:00 AM", "At 12:00 PM"],
                ["In the conference room", "At the restaurant", "In the park", "At the airport"],
                ["Due to illness", "Due to bad weather", "Due to technical issues", "Due to personal reasons"],
                ["Faster processing", "Lower cost", "Better security", "Improved user experience"],
                ["Artificial Intelligence", "Automated Interface", "Advanced Integration", "Accessible Information"],
                ["It's a natural phenomenon", "It's caused by human activities", "It's not a real issue", "It's impossible to solve"], ["About 100", "About 200", "About 300", "About 400"],
                ["Increased sales", "Improved customer satisfaction", "Reduced environmental impact",
                "All of the above"]
            ]
            options_list = [
                ["Tea", "Coffee", "Water", "Juice"],
                ["Grilled salmon", "Chicken curry", "Vegetable soup", "Pasta"],
                ["New marketing campaign", "Price reduction", "New product", "Expansion"],
                ["Cognitive bias", "Logical reasoning", "Critical thinking", "Creative thinking"],
                ["Climate change", "AI", "Space", "Economy"],
                ["Scientists", "Teachers", "Engineers", "Doctors"],
                ["Increased productivity", "Higher costs", "Reduced quality", "Longer delivery"],
                ["Buying car", "Vacation", "Investing", "Business"],
                ["Colleagues", "Friends", "Family", "Strangers"],
                ["9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM"],
                ["Conference room", "Restaurant", "Park", "Airport"],
                ["Illness", "Weather", "Technical issues", "Personal reasons"],
                ["Faster processing", "Lower cost", "Better security", "Better UX"],
                ["Artificial Intelligence", "Automated Interface", "Advanced Integration", "Accessible Information"],
                ["Natural phenomenon", "Human activities", "Not real", "Impossible"],
                ["About 100", "About 200", "About 300", "About 400"],
                ["Sales", "Satisfaction", "Environment", "All"]
            ]

        elif subject == 'japanese':
            questions = [
                f"話者Aは話者Bに何を勧めましたか?",
                f"最寄りの地下鉄の駅はどこにありますか?",
                f"売上高が増加した主な理由は何ですか?",
                f"新しい蝶の種はどこで発見されましたか?",
                f"認知的不協和とは何ですか?",
                f"講義の主なトピックは何ですか?",
                f"誰が新しい種を発見しましたか?",
                f"新しい政策の効果は何ですか?",
                f"二人の話者の関係は何ですか?",
                f"会議は何時に始まりますか?",
                f"イベントはどこで行われますか?",
                f"新しい技術の主な利点は何ですか?",
                f"'AI'とは何の略ですか?",
                f"話者の気候変動に関する意見は何ですか?",
                f"会議には何人参加しましたか?",
            ]
            options_list = [
                ["お茶", "コーヒー", "水", "サンドイッチ"],
                ["サーモンのグリルとご飯", "チキンカレー", "野菜スープ", "ソースつきパスタ"],
                ["新しいマーケティングキャンペーン", "価格の低下", "新製品の発売", "販売網の拡大"],
                ["矛盾する信念を持つこと", "明確な考えを持つこと", "合理的な決定をすること", "複雑なアイデアを理解すること"],
                ["気候変動", "人工知能", "宇宙探査", "世界経済"],
                ["科学者たち", "教師たち", "エンジニアたち", "医師たち"],
                ["生産性の向上", "コストの上昇", "品質の低下", "納期の延長"],
                ["新しい車を買うこと", "休暇を取ること", "株式に投資すること", "ビジネスを始めること"],
                ["同僚", "友人", "家族", "見知らぬ人"],
                ["9時", "10時", "11時", "12時"],
                ["会議室で", "レストランで", "公園で", "空港で"],
                ["病気のため", "悪天候のため", "技術的な問題のため", "個人的な理由のため"],
                ["処理速度の向上", "コストの低下", "セキュリティの強化", "ユーザーエクスペリエンスの改善"],
                ["人工知能", "自動化されたインターフェース", "高度な統合", "アクセス可能な情報"],
                ["それは自然現象です", "それは人間の活動によって引き起こされます", "それは実際の問題ではありません", "それは解決不可能です"],
                ["約100人", "約200人", "約300人", "約400人"],
                ["売上の増加", "顧客満足度の向上", "環境への影響の削減", "上記すべて"]
            ]

        question_index = random.randint(0, len(questions)-1)
        question = questions[question_index]
        options = options_list[question_index]
        correct_answer = 0  # 默认第一个选项为正确答案
        # 打乱选项顺序
        random.shuffle(options)

        return {
            "question_id": f"comprehension_{uuid.uuid4().hex[:12]}",
            "type": "single_choice",
            "question": question,
            "options": options,
            "answer": options.index(options_list[question_index][correct_answer]),
            "index": index
        }
    def _generate_multiple_choice_comprehension_question(self, audio_content, subject, difficulty, index):
        """生成多项选择理解题 Args: audio_content: 听力音频内容 subject: 科目(english, japanese) difficulty: 难度(beginner, intermediate, advanced, expert) index: 题目索引 Returns: 多项选择理解题 """
        # 简化实现,返回类似单项选择题的结构,但允许多个正确答案
        base_question = self._generate_single_choice_comprehension_question(
            audio_content, subject, difficulty, index
        )
        base_question['type'] = 'multiple_choice'
        # 随机选择1-3个正确答案
        correct_answers = random.sample(range(len(base_question['options'])), random.randint(1, 3))
        base_question['answer'] = correct_answers
    def _generate_fill_in_blank_comprehension_question(self, audio_content, subject, difficulty, index):
        """生成填空理解题 Args: audio_content: 听力音频内容 subject: 科目(english, japanese) difficulty: 难度(beginner, intermediate, advanced, expert) index: 题目索引 Returns: 填空理解题 """
        if subject == 'english':
            questions = [
                f"The subway station is on the ________ side of the street.",
                f"The customer ordered ________ with rice.",
                f"Sales increased by ________ percent compared to last quarter.",
                f"The meeting will start at ________ AM."
            ]
            correct_answers = ["right", "salmon", "15", "10"]
        else:
            questions = [
                f"地下鉄の駅は通りの________側にあります.",
                f"売上高は先季度と比較して________%増加しました.",
                f"会議は________時に始まります.",
                f"顧客は________を注文しました."
            ]
            correct_answers = ["右", "15", "10", "コーヒー"]

        question_index = random.randint(0, len(questions)-1)
        question = questions[question_index]
        correct_answer = correct_answers[question_index]

        return {
            "question_id": f"comprehension_{uuid.uuid4().hex[:12]}",
            "type": "fill_in_blank",
            "question": question,
            "answer": correct_answer,
            "index": index
        }

    def _generate_short_answer_comprehension_question(self, audio_content, subject, difficulty, index):
        """生成简答理解题 Args: audio_content: 听力音频内容 subject: 科目(english, japanese) difficulty: 难度(beginner, intermediate, advanced, expert) index: 题目索引 Returns: 简答理解题 """
        if subject == 'english':
            questions = [
                f"What did Speaker A offer to Speaker B?",
                f"What was the main reason for the sales increase?",
                f"Where was the new butterfly species discovered?"
            ]
            correct_answers = [
                "Go straight for two blocks, then turn left at the traffic light. The subway station will be on the right.", "New marketing campaign",
                "Amazon rainforest"
            ]
        else:  # japanese
            questions = [
                f"話者Aは話者Bに何を勧めましたか?",
                f"お客は地下鉄の駅へどう行けばよいですか?",
                f"売上高が増加した主な理由は何ですか?",
                f"新しい蝶の種はどこで発見されましたか?"
            ]
            correct_answers = [
                "コーヒー",
                "地下鉄で",
                "新しいマーケティングキャンペーン",
                "アマゾンの熱帯雨林"
            ]

        # 随机选择问题和答案
        question_index = random.randint(0, len(questions)-1)
        question = questions[question_index]
        correct_answer = correct_answers[question_index]

        return {
            "question_id": f"comprehension_{uuid.uuid4().hex[:12]}",
            "type": "short_answer",
            "question": question,
            "answer": correct_answer,
            "index": index
        }

    def _text_to_speech(self, text, subject, accent, voice_id):
        """将文本转换为可播放的音频文件 Args: text: 要转换的文本 subject: 科目(english, japanese) accent: 口音 voice_id: 语音ID Returns: audio_file_path: 音频文件路径 audio_url: 音频URL """
        if not gtts_available:
            logger.warning("gTTS库不可用,无法生成音频文件")
            return None, None

        try:
            audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'audio')
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir)

            # 生成唯一的音频文件名
            audio_filename = f"listening_{uuid.uuid4().hex[:12]}.mp3"
            audio_file_path = os.path.join(audio_dir, audio_filename)

            # 根据科目设置语言代码
            if subject == 'english':
                lang_code = 'en'
            elif subject == 'japanese':
                lang_code = 'ja'
            else:
                lang_code = 'en'  # 默认使用英语
            # 使用gTTS将文本转换为音频
            tts = gTTS(text=text, lang=lang_code, slow=False)
            tts.save(audio_file_path)
            logger.info(f"成功生成音频文件: {audio_file_path}")
            # 生成音频URL
            audio_url = f"/static/audio/{audio_filename}"

            return audio_file_path, audio_url
        except Exception as e:
            logger.error(f"生成音频文件失败: {str(e)}")
            return None, None

    def fetch_questions_from_web(self, subject, difficulty, question_type, count=10):
        """从网络爬取题目"""
        logger.info(f"从网络爬取 {count} 道{subject}{difficulty}难度{question_type}题目")
        # 这里可以根据实际的网站结构编写爬取逻辑
        # 目前返回空列表,实际实现时需要替换为真实的爬取逻辑
        return []

    def generate_personalized_exam(self, user_preferences, exclude_question_ids=None):
        """生成个性化试卷 Args: user_preferences: 用户偏好设置 exclude_question_ids: 需要排除的题目ID列表 user_preferences 格式: { "subject": "english",  # 科目: english, japanese "difficulty": "intermediate",  # 难度: beginner, intermediate, advanced "question_type": "single_choice",  # 题型: single_choice, multiple_choice "total_questions": 20,  # 总题数 "time_limit": 30,  # 时间限制(分钟) "include_listening": False  # 是否包含听力题 } """
        logger.info(f"生成个性化试卷: {user_preferences}")
        
        # 获取用户偏好
        subject = user_preferences.get('subject', 'english')
        difficulty = user_preferences.get('difficulty', 'intermediate')
        question_type = user_preferences.get('question_type', 'single_choice')
        total_questions = user_preferences.get('total_questions', 20)
        
        # 生成题目
        questions = self.generate_questions(
            subject=subject,
            question_type=question_type,
            difficulty=difficulty,
            count=total_questions
        )
        
        return {
            "exam_id": f"exam_{uuid.uuid4().hex[:12]}",
            "subject": subject,
            "difficulty": difficulty,
            "total_questions": total_questions,
            "questions": questions,
            "generated_at": datetime.now().isoformat()
        }

    def save_exam_to_db(self, exam):
        将生成的试卷保存到数据库
        try:
            from app.models.ai_brain import AIBrainKnowledge
            from app.models.ai_brain import AIBrainActivity

            # 创建试卷记录
            exam_knowledge = AIBrainKnowledge(
                knowledge_id=f"knowledge-{uuid.uuid4().hex[:8]}",
                title=f"试卷: {exam['title']}",
                content=str(exam),
                knowledge_type='personalized_exam',
                source='AI生成',
                source_id=exam['exam_id'],
                tags=['试卷', exam['subject'], exam['difficulty']],
                priority=5,
                is_active=True
            )
            exam_knowledge.save()

            # 记录活动日志
            activity = AIBrainActivity(
                activity_type='exam_generated',
                description=f"生成个性化试卷: {exam.get('title', 'Untitled')}",
                source='AI生成',
                source_id=exam.get('exam_id', 'unknown'),
                metadata={
                    'user_id': exam.get('user_id', 'unknown'),
                    'subject': exam.get('subject', 'unknown'),
                }
            )
            activity.save()

            logger.info(f"试卷 {exam.get('exam_id', 'unknown')} 成功保存到数据库")
            return True
        except Exception as e:
            logger.error(f"保存试卷到数据库失败: {str(e)}")
            return False

    def export_exam_as_json(self, exam, file_path=None):
        """将试卷导出为JSON文件"""
        if not file_path:
            file_path = f"exam_{exam.get('exam_id', 'unknown')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(exam, f, ensure_ascii=False, indent=2)

            logger.info(f"试卷 {exam.get('exam_id', 'unknown')} 成功导出为JSON文件: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"导出试卷为JSON文件失败: {str(e)}")
            return None

    def get_user_level(self, username, subject):
        """从数据库获取用户的语言等级 Args: username: 用户名 subject: 科目(english, japanese) Returns: 用户等级字符串 """

        logger.info(f"获取用户 {username} 的 {subject} 等级")

        try:
            # 这里假设存在用户等级表
            from app.models.learning_system import UserLanguageLevel

            user_level = UserLanguageLevel.get_user_level(username, subject)
            logger.info(f"用户 {username} 的 {subject} 等级为: {user_level}")
            return user_level
        except Exception as e:
            logger.error(f"获取用户 {username} 等级失败: {str(e)}")
            # 默认返回初级
            return 'beginner'

    def adjust_difficulty_by_user_level(self, user_level):
        """根据用户等级调整题目难度范围 Args: user_level: 用户等级(beginner, intermediate, advanced, expert) Returns: 可用难度列表 """
        logger.info(f"根据用户等级 {user_level} 调整难度范围")
        # 获取该等级允许的难度列表
        return self.level_difficulty_map.get(user_level, ['beginner'])

    def calculate_score_difficulty(self, score):
        """根据分数计算对应的难度等级 Args: score: 分数(0-100) Returns: 难度等级字符串 """
        for difficulty, (min_score, max_score) in self.difficulty_score_ranges.items():
            if min_score <= score <= max_score:
                return difficulty
        return 'beginner'

    def generate_practice_exam(self, user_preferences):
        """生成练习试卷 user_preferences 格式: { "user_id": "user-123", "username": "test_user", "subject": "english",  # 科目: english, japanese "target_difficulty": "intermediate",  # 目标难度 "knowledge_points": ["grammar", "vocabulary"],  # 知识点 "total_questions": 20,  # 总题数 "time_limit": 60,  # 时间限制(分钟) "title": "英语语法练习卷" } """
        logger.info(f"为用户 {user_preferences['username']} 生成练习试卷")


        # 根据用户等级调整目标难度
        allowed_difficulties = self.adjust_difficulty_by_user_level(user_level)
        target_difficulty = user_preferences['target_difficulty']

        # 确保目标难度在允许范围内
        if target_difficulty not in allowed_difficulties:
            target_difficulty = allowed_difficulties[-1]  # 使用最高允许难度
            logger.info(f"调整目标难度为 {target_difficulty}(用户等级允许的最高难度)")

        # 生成练习试卷参数
        practice_preferences = {
            "user_id": user_preferences['user_id'],
            "difficulty": target_difficulty,
            "question_type": "single_choice",  # 练习默认使用选择题
            "total_questions": user_preferences['total_questions'],
            "source_distribution": {
                "database": 0.8,  # 练习主要使用数据库题库
                "ai_generated": 0.2,
                "web_crawled": 0.0
            },
            "time_limit": user_preferences['time_limit'],
        }

        # 生成试卷
        exam = self.generate_personalized_exam(practice_preferences)

        # 添加练习相关信息
        exam['exam_type'] = 'practice'
        exam['user_level'] = user_level

        logger.info(f"成功生成练习试卷 {exam['exam_id']}")
        return exam

    def generate_graded_exam(self, user_preferences):
        """生成根据用户等级自动调整难度的分级试卷 user_preferences 格式: { "user_id": "user-123", "username": "test_user", "subject": "english",  # 科目: english, japanese "total_questions": 30,  # 总题数 "time_limit": 90,  # 时间限制(分钟) "title": "英语分级测试卷" } """
        user_level = self.get_user_level(user_preferences['username'], user_preferences['subject'])

        # 根据用户等级获取允许的难度列表
        allowed_difficulties = self.adjust_difficulty_by_user_level(user_level)

        total_questions = user_preferences.get('total_questions', 30)
        
        # 计算各难度的题目数量(根据用户等级动态调整比例)
        difficulty_counts = {}
        if user_level == 'beginner':
            # 初级用户:70%初级,30%中级
            difficulty_counts = {
                'beginner': int(total_questions * 0.7),
                'intermediate': total_questions - int(total_questions * 0.7)
            }
        elif user_level == 'intermediate':
            # 中级用户:30%初级,50%中级,20%高级
            difficulty_counts = {
                'beginner': int(total_questions * 0.3),
                'intermediate': int(total_questions * 0.5),
                'advanced': total_questions - int(total_questions * 0.3) - int(total_questions * 0.5)
            }
        elif user_level == 'advanced':
            # 高级用户:20%中级,60%高级,20%专家
            difficulty_counts = {
                'intermediate': int(total_questions * 0.2),
                'advanced': int(total_questions * 0.6),
                'expert': total_questions - int(total_questions * 0.2) - int(total_questions * 0.6)
            }
        else:  # expert
            # 专家用户:30%高级,70%专家
            difficulty_counts = {
                'advanced': int(total_questions * 0.3),
                'expert': total_questions - int(total_questions * 0.3)
            }


        all_questions = []
        for difficulty, count in difficulty_counts.items():
            if count <= 0:
                continue

            questions = self.generate_questions(
                subject=user_preferences['subject'],
                question_type='single_choice',
                difficulty=difficulty,
                count=count
            )
            all_questions.extend(questions)

        random.shuffle(all_questions)

        # 生成试卷
        exam = {
            "exam_id": f"exam-{uuid.uuid4().hex[:8]}",
            "user_id": user_preferences['user_id'],
            "subject": user_preferences['subject'],
            "total_questions": len(all_questions),
            "time_limit": user_preferences.get('time_limit', 90),
            "title": user_preferences.get('title', '分级测试卷'),
            "generated_at": datetime.now().isoformat(),
            "questions": all_questions,
            "user_level": user_level,
            "difficulty_distribution": difficulty_counts
        }

        logger.info(f"成功生成分级试卷 {exam['exam_id']},包含 {len(all_questions)} 道题目")
        return exam

    def save_user_practice_record(self, username, exam_id, score, answers):
        """保存用户练习记录 Args: username: 用户名 exam_id: 试卷ID score: 得分 answers: 答案列表 Returns: 是否保存成功 """
        try:
            from app.models.learning_system import UserPracticeRecord

            # 保存练习记录
            record = UserPracticeRecord(
                username=username,
                exam_id=exam_id,
                score=score,
                answers=str(answers),
                practiced_at=datetime.now()
            )
            record.save()

            # 保存用户已做题目记录
            from app.models.learning_system import UserAnsweredQuestion
            answered_question = UserAnsweredQuestion(
                username=username,
                exam_id=exam_id,
                question_id=f"practice_{exam_id}",
                answered_at=datetime.now()
            )
            answered_question.save()

            logger.info(f"成功保存用户 {username} 的练习记录")
            return True
        except Exception as e:
            logger.error(f"保存用户练习记录失败: {str(e)}")
            return False

    def get_user_answered_question_ids(self, username, subject=None):
        """获取用户已做的题目ID列表 Args: username: 用户名 subject: 科目(可选) Returns: 用户已做题目ID列表 """
        logger.info(f"获取用户 {username} 的已做题目ID,科目: {subject}")

        try:
            from app.models.learning_system import UserAnsweredQuestion

            # 获取用户已做题目记录
            answered_questions = UserAnsweredQuestion.get_by_username(username)

            # 提取题目ID
            question_ids = []
            for record in answered_questions:
                question_ids.append(record.question_id)

            logger.info(f"成功获取用户 {username} 的 {len(question_ids)} 道已做题目ID")
            return question_ids
        except Exception as e:
            logger.error(f"获取用户 {username} 已做题目ID失败: {str(e)}")
            return []

    def get_user_answered_questions(self, username, subject=None, limit=100):
        """获取用户已做的题目详情 Args: username: 用户名 subject: 科目(可选) limit: 返回数量限制 Returns: 用户已做题目列表 """
        logger.info(f"获取用户 {username} 的已做题目详情,科目: {subject},限制: {limit}")

        try:
            from app.models.learning_system import UserAnsweredQuestion
            from app.models.ai_brain import AIBrainKnowledge

            # 获取用户已做题目记录
            answered_questions = UserAnsweredQuestion.get_by_username(username, limit=limit)

            # 获取题目详情
            user_answered_questions = []
            all_questions = AIBrainKnowledge.get_all(subject=subject) if subject else AIBrainKnowledge.get_all()
            
            for record in answered_questions:
                try:
                    # 根据题目ID获取题目
                    for knowledge in all_questions:
                        content = _safe_parse(knowledge.content)
                        if content.get('question_id') == record.question_id:
                            # 添加答题相关信息
                            content['answered_at'] = record.answered_at.isoformat() if record.answered_at else None
                            content['exam_id'] = record.exam_id
                            user_answered_questions.append(content)
                except Exception as e:
                    logger.error(f"获取题目详情失败,题目ID: {record.question_id}: {str(e)}")

            logger.info(f"成功获取用户 {username} 的 {len(user_answered_questions)} 道已做题目详情")
            return user_answered_questions
        except Exception as e:
            logger.error(f"获取用户已做题目详情失败: {str(e)}")
            return []

    def generate_and_save_exam(self, user_preferences):
        """生成并保存个性化试卷"""
        # 生成试卷
        exam = self.generate_personalized_exam(user_preferences)

        # 保存到数据库
        self.save_exam_to_db(exam)

        self.export_exam_as_json(exam)

        return exam
    def generate_and_save_practice_exam(self, user_preferences):
        生成并保存练习试卷
        # 生成练习试卷
        exam = self.generate_practice_exam(user_preferences)

        # 保存到数据库

        # 导出为JSON文件
        self.export_exam_as_json(exam)

    def generate_and_save_graded_exam(self, user_preferences):
        生成并保存分级试卷

        # 保存到数据库
        self.save_exam_to_db(exam)
        # 导出为JSON文件
        self.export_exam_as_json(exam)

        return exam

    def get_user_exams(self, user_id, exam_type=None):
        """获取用户的试卷列表 Args: user_id: 用户ID exam_type: 试卷类型(practice, graded, wrong_question_practice) Returns: 试卷列表 """
        try:
            from app.models.ai_brain import AIBrainKnowledge

            # 获取所有个性化试卷
            all_exams = AIBrainKnowledge.get_all()

            # 过滤用户的试卷
            user_exams = []
            for exam in all_exams:
                exam_data = _safe_parse(exam.content)

                # 过滤用户ID
                if exam_data.get('user_id') != user_id:
                    continue
                # 过滤试卷类型
                if exam_type and exam_data.get('exam_type') != exam_type:
                    continue

                user_exams.append(exam_data)

            # 按生成时间排序,最新的在前
            user_exams.sort(key=lambda x: x.get('generated_at', ''), reverse=True)

            logger.info(f"成功获取用户 {user_id} 的 {len(user_exams)} 份试卷")
        except Exception as e:
            return []

    def get_exam_by_id(self, exam_id):
        """根据试卷ID获取试卷详细信息 Args: exam_id: 试卷ID Returns: 试卷详情或None """
        logger.info(f"根据ID {exam_id} 获取试卷")

        try:
            from app.models.ai_brain import AIBrainKnowledge
            # 获取所有个性化试卷
            all_exams = AIBrainKnowledge.get_all(knowledge_type='personalized_exam')

            # 查找指定ID的试卷
            for exam in all_exams:
                exam_data = _safe_parse(exam.content)
                if exam_data.get('exam_id') == exam_id:
                    logger.info(f"成功获取试卷 {exam_id}")
                    return exam_data

            logger.info(f"未找到试卷 {exam_id}")
            return None
        except Exception as e:
            logger.error(f"获取试卷失败: {str(e)}")
            return None

    def delete_exam(self, exam_id):
        """删除指定ID的试卷 Args: exam_id: 试卷ID Returns: 是否删除成功 """
        try:
            from app.models.ai_brain import AIBrainKnowledge

            # 获取所有个性化试卷
            all_exams = AIBrainKnowledge.get_all(knowledge_type='personalized_exam')

            # 查找并删除指定ID的试卷
            for exam in all_exams:
                exam_data = _safe_parse(exam.content)
                if exam_data.get('exam_id') == exam_id:
                    exam.delete()
                    logger.info(f"成功删除试卷 {exam_id}")
                    return True

            logger.info(f"未找到试卷 {exam_id},删除失败")
            return False
        except Exception as e:
            logger.error(f"删除试卷失败: {str(e)}")
            return False

    def update_exam(self, exam_id, update_data):
        """更新试卷信息 Args: exam_id: 试卷ID update_data: 更新数据,如 {"title": "新标题", "time_limit": 90} Returns: 是否更新成功 """
        logger.info(f"更新试卷 {exam_id},数据: {update_data}")

        try:
            from app.models.ai_brain import AIBrainKnowledge

            # 获取所有个性化试卷
            all_exams = AIBrainKnowledge.get_all(knowledge_type='personalized_exam')

            # 查找并更新指定ID的试卷
            for exam in all_exams:
                exam_data = _safe_parse(exam.content)
                if exam_data.get('exam_id') == exam_id:
                    # 更新试卷数据
                    exam_data.update(update_data)
                    # 保存更新后的试卷
                    exam.content = str(exam_data)
                    exam.save()
                    logger.info(f"成功更新试卷 {exam_id}")
                    return True

            logger.info(f"未找到试卷 {exam_id},更新失败")
            return False
        except Exception as e:
            logger.error(f"更新试卷失败: {str(e)}")
            return False

    def get_user_exam_stats(self, user_id):
        """获取用户的试卷统计信息 Args: user_id: 用户ID Returns: 统计信息,格式: { "total_exams": 10, "graded_exams": 3, "wrong_question_exams": 2, "average_score": 85.5, "highest_score": 98, "lowest_score": 65, "recent_exams": [exam1, exam2, ...]  # 最近5份试卷 } """
        logger.info(f"获取用户 {user_id} 的试卷统计信息")

        try:
            # 获取用户所有试卷
            all_exams = self.get_user_exams(user_id)

            # 获取用户所有练习记录
            all_practice_records = UserPracticeRecord.get_by_username(user_id)

            # 计算统计信息
            stats = {
                "total_exams": len(all_exams),
                "practice_exams": 0,
                "graded_exams": 0,
                "wrong_question_exams": 0,
                "lowest_score": 100,
                "recent_exams": []
            }


            for exam in all_exams:
                # 统计试卷类型
                exam_type = exam.get('exam_type', 'unknown')
                if exam_type == 'practice':
                    stats['practice_exams'] += 1
                elif exam_type == 'graded':
                    stats['graded_exams'] += 1
                elif exam_type == 'wrong_question_practice':
                    stats['wrong_question_exams'] += 1

            # 计算分数统计(从练习记录中获取)
            for record in all_practice_records:
                scores.append(record.score)

            if scores:
                stats['average_score'] = sum(scores) / len(scores)
                stats['highest_score'] = max(scores)
                stats['lowest_score'] = min(scores)

            # 获取最近5份试卷
            stats['recent_exams'] = all_exams[:5]

            logger.info(f"成功获取用户 {user_id} 的试卷统计信息")
            return stats
        except Exception as e:
            logger.error(f"获取用户试卷统计信息失败: {str(e)}")
            return {
                "total_exams": 0,
                "graded_exams": 0,
                "wrong_question_exams": 0,
                "average_score": 0,
                "highest_score": 0,
                "lowest_score": 0,
                "recent_exams": []
            }

    def generate_practice_schedule(self, username, subject, days=7):
        """为用户生成练习计划 Args: username: 用户名 subject: 科目(english, japanese) days: 计划天数 Returns: 练习计划 """
        logger.info(f"为用户 {username} 生成 {subject} 练习计划,天数: {days}")

        try:
            user_level = self.get_user_level(username, subject)

            suggestions = self.get_practice_suggestions(username, subject)

            # 获取用户错题数量
            wrong_questions = self.get_user_wrong_questions(username, subject, 100)
            wrong_count = len(wrong_questions)

            schedule = {
                "username": username,
                "subject": subject,
                "days": days,
                "daily_plan": [],
                "suggestions": suggestions
            }

            # 根据用户情况生成每日计划
            for day in range(1, days + 1):
                daily_plan = {
                    "day": day,
                    "date": (datetime.now() + timedelta(days=day-1)).strftime("%Y-%m-%d"),
                    "tasks": []
                }

                daily_plan["tasks"].append({
                    "type": "basic_practice",
                    "content": f"{subject} 基础练习",
                    "duration": 30,
                    "priority": "high"
                })

                for suggestion in suggestions[:2]:
                    if suggestion["type"] == "focus_practice":
                        daily_plan["tasks"].append({
                            "type": "focus_practice",
                            "content": f"重点练习 {suggestion['knowledge_point']} 知识点",
                            "duration": 20,
                            "priority": "medium"
                        })
                    elif suggestion["type"] == "wrong_question_practice" and wrong_count > 0:
                        daily_plan["tasks"].append({
                            "type": "wrong_question_practice",
                            "content": f"练习错题集 {min(10, wrong_count)} 道",
                            "duration": 25,
                            "priority": "medium"
                        })

                # 3. 每3天进行一次模拟测试
                if day % 3 == 0:
                    daily_plan["tasks"].append({
                        "type": "mock_test",
                        "content": f"进行 {subject} 模拟测试,共30道题",
                        "duration": 60,
                        "priority": "high"
                    })
                schedule["daily_plan"].append(daily_plan)

            logger.info(f"成功为用户 {username} 生成练习计划")
            return schedule
        except Exception as e:
            logger.error(f"生成练习计划失败: {str(e)}")
            return {
                "username": username,
                "subject": subject,
                "user_level": self.get_user_level(username, subject),
                "days": days,
                "daily_plan": [],
                "suggestions": []
            }

if __name__ == '__main__':
    # 示例使用
    generator = ExamGenerator()

    # 用户偏好设置
    user_prefs = {
        "subject": "english",
        "difficulty": "intermediate",
        "question_type": "single_choice",
        "source_distribution": {
            "database": 0.5,
            "ai_generated": 0.3,
        },
        "time_limit": 30,
    }

    # 生成并保存试卷
    exam = generator.generate_and_save_exam(user_prefs)

    print(f"成功生成试卷: {exam['title']}")
    print(f"试卷ID: {exam['exam_id']}")
    print(f"总题数: {exam['total_questions']}")
    print(f"题目来源分布: {exam['source_statistics']}")
    print(f"保存路径: exam_{exam['exam_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
