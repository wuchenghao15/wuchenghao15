import json
import random
import time
from app.models.question import Question
from app.utils.logging import logger
from app.ai.learning import ai_learning

class AIQuestionGenerator:
    """AI题目生成器，用于自动扩充题库"""
    
    def __init__(self, config=None):
        # 默认配置
        default_config = {
            'generation_enabled': True,
            'languages': ['japanese', 'english'],
            'levels': ['beginner', 'intermediate', 'advanced', 'expert'],
            'min_questions_per_category': 15,
            'min_vocab_questions': 30,
            'max_attempts': 10,  # 增加默认尝试次数
            'question_type_expansion_threshold': 0.15,
            'duplicate_detection_enabled': True,
            'similarity_threshold': 0.5,  # 使用优化后的相似度阈值
            'variant_generation_enabled': True  # 启用变体生成
        }
        
        # 合并用户配置
        self.config = {**default_config, **(config or {})}
        
        # 初始化属性
        self.generation_enabled = self.config['generation_enabled']
        self.languages = self.config['languages']
        self.levels = self.config['levels']
        self.categories = {
            'japanese': ['日常对话', '商务日语', '学术日语', '日本文化', '往年真题', '词汇题', '日语精读'],
            'english': ['日常对话', '商务英语', '学术写作', '英语听力', '雅思托福', '词汇题']
        }
        # 支持的题型
        self.question_types = {
            'multiple_choice': '选择题',
            'fill_in_blank': '填空题',
            'true_false': '判断题',
            'short_answer': '简答题',
            'essay': '作文题',
            'matching': '匹配题',
            'ordering': '排序题',
            'image_based': '图片题',
            'drag_drop': '拖拽题',
            'gap_filling': '完形填空题',
            'listening': '听力题',
            'speaking': '口语题',
            'reading': '阅读题',
            'case_analysis': '案例分析题',
            'comprehensive': '综合应用题',
            'debate_topic': '辩论题',
            'presentation_topic': '演讲题',
            'translation': '翻译题'
        }
        # 每个类别保持的最少题目数量
        self.min_questions_per_category = self.config['min_questions_per_category']
        # 词汇题保持的最少题目数量，提高优先级
        self.min_vocab_questions = self.config['min_vocab_questions']
        # AI生成题目的最大尝试次数
        self.max_attempts = self.config['max_attempts']
        # 题型扩充阈值：当某题型占比低于此值时，自动扩充
        self.question_type_expansion_threshold = self.config['question_type_expansion_threshold']
        # 重复检测相关配置
        self.duplicate_detection_enabled = self.config['duplicate_detection_enabled']
        self.similarity_threshold = self.config['similarity_threshold']
        self.variant_generation_enabled = self.config['variant_generation_enabled']
    
    def generate_question(self, language='japanese', level='beginner', category=None, question_type=None):
        """生成单个题目"""
        if not self.generation_enabled:
            logger.warning("AI题目生成功能已禁用")
            return None
        
        # 如果没有指定类别，随机选择一个
        if not category:
            # 确保language在categories中
            if language not in self.categories:
                language = 'japanese'
            # 确保categories[language]不为空
            if not self.categories[language]:
                self.categories[language] = ['日常对话']
            category = random.choice(self.categories[language])
        
        # 如果没有指定题型，根据题型分布自动选择需要扩充的题型
        if not question_type:
            needed_types = self._get_needed_question_types(language, level, category)
            if needed_types:
                # 从需要扩充的题型中随机选择一个
                question_type = random.choice(needed_types)
            else:
                # 如果所有题型都足够，随机选择一个
                question_type = random.choice(list(self.question_types.keys()))
        
        try:
            logger.info(f"开始生成题目: {language}, {level}, {category}, {question_type}")
            
            # 首先参考现有题库，了解题目结构和类型
            existing_questions = self._get_existing_questions(language, level, category, question_type)
            
            # 根据语言和题型生成题目内容
            question_content, options, correct_answer, explanation = self._generate_question_content(
                language, level, category, existing_questions, question_type
            )
            
            # 优化选择题的选项，确保相似性和排他性
            if question_type == 'multiple_choice' and options:
                options = self._optimize_multiple_choice_options(options, correct_answer)
            
            # 转换参数映射
            language_id_map = {'japanese': 1, 'english': 2}
            language_id = language_id_map.get(language, 1)
            
            level_id_map = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4}
            level_id = level_id_map.get(level, 1)
            
            # 简化处理，使用默认分类ID
            category_id = 1
            
            # 使用QuestionManager创建题目
            from app.models.question import question_manager
            
            question = question_manager.create_question(
                content=question_content,
                answer=correct_answer,
                explanation=explanation,
                category_id=category_id,
                language_id=language_id,
                level_id=level_id,
                question_type=question_type,
                options=options
            )
            
            # 获取题目ID
            question_id = question.id
            
            if question_id:
                logger.info(f"成功生成题目: {question_id} - {question_content} (题型: {self.question_types[question_type]})")
                return question
            else:
                logger.error("保存题目失败: 未返回有效的question_id")
                return None
        except Exception as e:
            logger.error(f"生成题目失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return None
    
    def _optimize_multiple_choice_options(self, options, correct_answer):
        """优化选择题的选项，确保相似性和排他性
        
        Args:
            options: 原始选项列表
            correct_answer: 正确答案
            
        Returns:
            优化后的选项列表
        """
        try:
            # 确保有至少4个选项
            if len(options) < 4:
                # 生成更多具有混淆性的选项
                while len(options) < 4:
                    distractor = self._generate_distractor(correct_answer)
                    if distractor not in options:
                        options.append(distractor)
            
            # 确保正确答案在选项中
            if correct_answer not in options:
                # 替换一个随机选项为正确答案
                if options:
                    options[random.randint(0, len(options) - 1)] = correct_answer
                else:
                    options.append(correct_answer)
            
            # 打乱选项顺序
            random.shuffle(options)
            
            return options
        except Exception as e:
            logger.error(f"优化选择题选项失败: {str(e)}")
            return options
    
    def _generate_distractor(self, correct_answer):
        """生成具有混淆性的干扰选项
        
        Args:
            correct_answer: 正确答案
            
        Returns:
            干扰选项
        """
        try:
            # 根据正确答案的类型生成干扰选项
            if isinstance(correct_answer, str):
                # 字符串类型的答案
                if len(correct_answer) <= 3:
                    # 短答案，生成相似的字符串
                    return correct_answer[::-1]  # 反转字符串
                else:
                    # 长答案，生成部分相似的字符串
                    # 替换一个字符
                    idx = random.randint(1, len(correct_answer) - 2)
                    new_char = chr(random.randint(97, 122))
                    while new_char == correct_answer[idx]:
                        new_char = chr(random.randint(97, 122))
                    return correct_answer[:idx] + new_char + correct_answer[idx+1:]
            elif isinstance(correct_answer, int):
                # 数字类型的答案
                # 生成相近的数字
                return correct_answer + random.randint(-5, 5)
            else:
                # 其他类型，返回通用干扰选项
                return f"Similar to {correct_answer}"
        except Exception as e:
            logger.error(f"生成干扰选项失败: {str(e)}")
            return f"Distractor for {correct_answer}"
    
    def _generate_question_content(self, language, level, category, existing_questions, question_type='multiple_choice'):
        """生成题目内容（示例实现，实际项目中应调用AI模型）"""
        # 这里是示例实现，实际项目中应集成AI模型生成真实题目
        if language == 'japanese':
            if category == 'case_analysis':
                return self._generate_japanese_case_analysis(level, category)
            elif category == 'comprehensive':
                return self._generate_japanese_comprehensive(level, category)
            elif category == 'translation':
                return self._generate_japanese_translation(level, category)
            elif category == '日语精读':
                return self._generate_japanese_intensive_reading(level, category)
            else:
                return self._generate_japanese_question(level, category, existing_questions, question_type)
        else:
            if question_type == 'case_analysis':
                return self._generate_english_case_analysis(level, category)
            elif question_type == 'comprehensive':
                return self._generate_english_comprehensive(level, category)
            elif question_type == 'translation':
                return self._generate_english_translation(level, category)
            else:
                return self._generate_english_question(level, category, existing_questions, question_type)
    
    def generate_question_variants(self, base_question, variant_count=3):
        """生成题目变体，增加题目多样性
        
        Args:
            base_question: 基础题目对象
            variant_count: 要生成的变体数量
            
        Returns:
            题目变体列表
        """
        variants = []
        
        try:
            for i in range(variant_count):
                # 复制基础题目
                variant = {
                    'language': base_question.language,
                    'level': base_question.level,
                    'category': base_question.category,
                    'question_type': base_question.question_type,
                    'content': base_question.content,
                    'options': base_question.options.copy() if base_question.options else [],
                    'correct_answer': base_question.correct_answer,
                    'explanation': base_question.explanation
                }
                
                # 根据题目类型生成变体
                if base_question.question_type == 'multiple_choice':
                    # 重新排列选项
                    if variant['options']:
                        original_options = variant['options'].copy()
                        correct_answer = variant['correct_answer']
                        random.shuffle(variant['options'])
                        variant['correct_answer'] = variant['options'].index(correct_answer)
                elif base_question.question_type == 'fill_in_blank':
                    # 生成不同的填空位置
                    variant['content'] = self._generate_blank_variant(variant['content'])
                elif base_question.question_type == 'true_false':
                    # 生成相反的陈述
                    if random.choice([True, False]):
                        variant['content'] = self._generate_opposite_statement(variant['content'])
                        variant['correct_answer'] = '对' if variant['correct_answer'] == '错' else '错'
                
                # 转换参数映射
                language_id_map = {'japanese': 1, 'english': 2}
                language_id = language_id_map.get(variant['language'], 1)
                
                level_id_map = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4}
                level_id = level_id_map.get(variant['level'], 1)
                
                # 简化处理，使用默认分类ID
                category_id = 1
                
                # 使用QuestionManager创建题目变体
                from app.models.question import question_manager
                
                variant_question = question_manager.create_question(
                    content=variant['content'],
                    answer=variant['correct_answer'],
                    explanation=variant['explanation'],
                    category_id=category_id,
                    language_id=language_id,
                    level_id=level_id,
                    question_type=variant['question_type'],
                    options=variant['options']
                )
                
                variants.append(variant_question)
            
            return variants
        except Exception as e:
            logger.error(f"生成题目变体失败: {str(e)}")
            return []
    
    def _generate_blank_variant(self, content):
        """生成填空题的变体"""
        # 简单实现：替换不同的单词为空白
        words = content.split()
        if len(words) > 3:
            # 选择一个不同的位置
            blank_pos = random.randint(1, len(words) - 2)
            words[blank_pos] = "____"
            return " ".join(words)
        return content
    
    def _generate_opposite_statement(self, content):
        """生成相反的陈述"""
        # 简单实现：添加否定词
        negation_words = ['不', '没有', '未', '非']
        if any(word in content for word in negation_words):
            # 移除否定词
            for word in negation_words:
                content = content.replace(word, "")
        else:
            # 添加否定词
            negation = random.choice(negation_words)
            # 在适当位置插入否定词
            words = content.split()
            if len(words) > 1:
                insert_pos = random.randint(1, len(words) - 1)
                words.insert(insert_pos, negation)
                content = " ".join(words)
        return content
    
    def _generate_japanese_question(self, level, category, existing_questions, question_type='multiple_choice'):
        """生成日语题目（示例实现）"""
        try:
            # 增加随机变体，避免重复
            variant = random.randint(1, 3)
            
            if category == '词汇题':
                # 词汇题生成逻辑，重点关注单词意义、读音和用法
                # 扩充词汇库，增加更多单词和不同级别，包括高级词汇
                vocab_words = {
                    'beginner': [
                        {'word': 'こんにちは', 'meaning': '你好', 'reading': 'こんにちは', 'usage': '日常问候'},
                        {'word': '本', 'meaning': '书', 'reading': 'ほん', 'usage': '物品名称'},
                        {'word': '食べる', 'meaning': '吃', 'reading': 'たべる', 'usage': '动词'},
                        {'word': '水', 'meaning': '水', 'reading': 'みず', 'usage': '物品名称'},
                        {'word': '行く', 'meaning': '去', 'reading': 'いく', 'usage': '动词'},
                        {'word': '来る', 'meaning': '来', 'reading': 'くる', 'usage': '动词'},
                        {'word': '見る', 'meaning': '看', 'reading': 'みる', 'usage': '动词'},
                        {'word': '聞く', 'meaning': '听', 'reading': 'きく', 'usage': '动词'},
                        {'word': '話す', 'meaning': '说', 'reading': 'はなす', 'usage': '动词'},
                        {'word': '読む', 'meaning': '读', 'reading': 'よむ', 'usage': '动词'}
                    ],
                    'intermediate': [
                        {'word': '迅速', 'meaning': '迅速', 'reading': 'じんそく', 'usage': '形容词'},
                        {'word': '効率', 'meaning': '效率', 'reading': 'こうりつ', 'usage': '名词'},
                        {'word': '協力', 'meaning': '合作', 'reading': 'きょうりょく', 'usage': '名词'},
                        {'word': '分析', 'meaning': '分析', 'reading': 'ぶんせき', 'usage': '名词/动词'},
                        {'word': '戦略', 'meaning': '战略', 'reading': 'せんりゃく', 'usage': '名词'},
                        {'word': '革新', 'meaning': '革新', 'reading': 'かくしん', 'usage': '名词'},
                        {'word': '持続', 'meaning': '持续', 'reading': 'じぞく', 'usage': '名词/动词'},
                        {'word': '信頼', 'meaning': '信赖', 'reading': 'しんらい', 'usage': '名词/动词'},
                        {'word': '責任', 'meaning': '责任', 'reading': 'せきにん', 'usage': '名词'},
                        {'word': '発展', 'meaning': '发展', 'reading': 'はってん', 'usage': '名词/动词'}
                    ],
                    'advanced': [
                        {'word': '専門的', 'meaning': '专业的', 'reading': 'せんもんてき', 'usage': '形容词'},
                        {'word': '複雑', 'meaning': '复杂', 'reading': 'ふくざつ', 'usage': '形容词'},
                        {'word': '柔軟', 'meaning': '灵活', 'reading': 'じゅうなん', 'usage': '形容词'},
                        {'word': '戦術', 'meaning': '战术', 'reading': 'せんじゅつ', 'usage': '名词'},
                        {'word': '戦略的', 'meaning': '战略性的', 'reading': 'せんりゃくてき', 'usage': '形容词'},
                        {'word': '革新的', 'meaning': '革新性的', 'reading': 'かくしんてき', 'usage': '形容词'},
                        {'word': '持続可能', 'meaning': '可持续的', 'reading': 'じぞくかのう', 'usage': '形容词'},
                        {'word': '信頼性', 'meaning': '可靠性', 'reading': 'しんらいせい', 'usage': '名词'},
                        {'word': '責任感', 'meaning': '责任感', 'reading': 'せきにんかん', 'usage': '名词'},
                        {'word': '発展途上', 'meaning': '发展中', 'reading': 'はってんとじょう', 'usage': '形容词'}
                    ],
                    'expert': [
                        {'word': '専門知識', 'meaning': '专业知识', 'reading': 'せんもんちしき', 'usage': '名词'},
                        {'word': '複雑性', 'meaning': '复杂性', 'reading': 'ふくざつせい', 'usage': '名词'},
                        {'word': '柔軟性', 'meaning': '灵活性', 'reading': 'じゅうなんせい', 'usage': '名词'},
                        {'word': '戦術的', 'meaning': '战术性的', 'reading': 'せんじゅつてき', 'usage': '形容词'},
                        {'word': '戦略計画', 'meaning': '战略计划', 'reading': 'せんりゃくけいかく', 'usage': '名词'},
                        {'word': '革新的技術', 'meaning': '革新性技术', 'reading': 'かくしんてきぎじゅつ', 'usage': '名词'},
                        {'word': '持続可能性', 'meaning': '可持续性', 'reading': 'じぞくかのうせい', 'usage': '名词'},
                        {'word': '信頼関係', 'meaning': '信赖关系', 'reading': 'しんらいかんけい', 'usage': '名词'},
                        {'word': '責任能力', 'meaning': '责任能力', 'reading': 'せきにんのうりょく', 'usage': '名词'},
                        {'word': '発展戦略', 'meaning': '发展战略', 'reading': 'はってんせんりゃく', 'usage': '名词'}
                    ]
                }
                
                # 随机选择一个词汇，确保级别存在
                if level not in vocab_words:
                    level = 'beginner'  # 默认使用beginner级别，更安全
                selected_word = random.choice(vocab_words[level])
                
                # 根据不同题型生成不同类型的词汇题
                if question_type == 'true_false':
                    # 判断题：词汇相关的真假判断，增加更多变体
                    if random.choice([True, False]):
                        if variant == 1:
                            content = f'「{selected_word["word"]}」の意味は「{selected_word["meaning"]}」です。'
                        elif variant == 2:
                            content = f'「{selected_word["word"]}」は「{selected_word["meaning"]}」という意味です。'
                        else:
                            content = f'「{selected_word["word"]}」の正しい意味は「{selected_word["meaning"]}」です。'
                        correct_answer = '对'
                        explanation = f'「{selected_word["word"]}」的意思确实是「{selected_word["meaning"]}」。'
                    else:
                        # 从其他单词中选择干扰选项，更相关
                        wrong_words = vocab_words[level]
                        wrong_word = random.choice(wrong_words)
                        while wrong_word['word'] == selected_word['word']:
                            wrong_word = random.choice(wrong_words)
                        if variant == 1:
                            content = f'「{selected_word["word"]}」の意味は「{wrong_word["meaning"]}」です。'
                        elif variant == 2:
                            content = f'「{selected_word["word"]}」は「{wrong_word["meaning"]}」という意味です。'
                        else:
                            content = f'「{selected_word["word"]}」の正しい意味は「{wrong_word["meaning"]}」です。'
                        correct_answer = '错'
                        explanation = f'「{selected_word["word"]}」的意思是「{selected_word["meaning"]}」，而不是「{wrong_word["meaning"]}」。'
                    options = ['对', '错']
                elif question_type == 'fill_in_blank':
                    # 填空题：根据描述填写正确的词汇，移除多余选项
                    if variant == 1:
                        content = f'「{selected_word["meaning"]}」の日本語は「____」です。'
                    elif variant == 2:
                        content = f'「{selected_word["reading"]}」と読む日本語で「{selected_word["meaning"]}」という意味の言葉は「____」です。'
                    else:
                        content = f'「{selected_word["usage"]}」として使われる「{selected_word["meaning"]}」の日本語は「____」です。'
                    correct_answer = selected_word["word"]
                    # 填空题只需要正确答案作为选项，移除"（填空题）"
                    options = [correct_answer]
                    explanation = f'「{selected_word["meaning"]}」的日语是「{selected_word["word"]}」，读音是「{selected_word["reading"]}」。'
                elif question_type == 'short_answer':
                    # 简答题：解释词汇，移除多余选项
                    if variant == 1:
                        content = f'「{selected_word["word"]}」の意味を説明してください。'
                    elif variant == 2:
                        content = f'「{selected_word["word"]}」の読み方と意味を答えてください。'
                    else:
                        content = f'「{selected_word["word"]}」の使い方を説明してください。'
                    correct_answer = selected_word["meaning"] if variant == 1 else f'{selected_word["reading"]}，{selected_word["meaning"]}' if variant == 2 else f'{selected_word["usage"]}，例：{selected_word["word"]}を使った文'
                    # 简答题不需要多余选项，移除"（简答题）"
                    options = []
                    explanation = f'「{selected_word["word"]}」的意思是「{selected_word["meaning"]}」，读音是「{selected_word["reading"]}」，用法：{selected_word["usage"]}。'
                elif question_type == 'essay':
                    # 作文题：生成相关主题
                    if variant == 1:
                        content = f'「{selected_word["word"]}」について、200字程度で作文を書いてください。'
                    elif variant == 2:
                        content = f'「{selected_word["word"]}」をテーマにした作文を書いてください。（約200字）'
                    else:
                        content = f'「{selected_word["meaning"]}」について考え、「{selected_word["word"]}」を使って作文を書いてください。（200字程度）'
                    correct_answer = f'「{selected_word["word"]}」についての作文を評価基準に従って採点してください。'
                    options = []
                    explanation = f'「{selected_word["word"]}」的意思是「{selected_word["meaning"]}」，读音是「{selected_word["reading"]}」，用法：{selected_word["usage"]}。作文题主要考察学生的日语表达能力和对主题的理解。'
                else:  # multiple_choice
                    # 传统选择题，优化选项生成
                    vocab_question_types = ['meaning', 'reading', 'usage']
                    vocab_question_type = random.choice(vocab_question_types)
                    
                    if vocab_question_type == 'meaning':
                        # 词义题，增加更多变体和更相关的选项
                        if variant == 1:
                            content = f'「{selected_word["word"]}」の意味は？'
                        elif variant == 2:
                            content = f'「{selected_word["word"]}」という言葉の意味は次のどれですか？'
                        else:
                            content = f'「{selected_word["word"]}」の正しい意味を選んでください。'
                        correct_answer = selected_word["meaning"]
                        # 生成更相关的干扰选项
                        options = [correct_answer]
                        while len(options) < 4:
                            # 从其他单词中选择干扰选项，更相关
                            other_words = vocab_words[level]
                            distractor_word = random.choice(other_words)
                            while distractor_word['word'] == selected_word['word'] or distractor_word['meaning'] in options:
                                distractor_word = random.choice(other_words)
                            distractor = distractor_word['meaning']
                            options.append(distractor)
                        random.shuffle(options)
                        explanation = f'「{selected_word["word"]}」的意思是{selected_word["meaning"]}，读音是{selected_word["reading"]}，用法：{selected_word["usage"]}。'
                    elif vocab_question_type == 'reading':
                        # 读音题，增加更多变体
                        if variant == 1:
                            content = f'「{selected_word["word"]}」の正しい読み方は？'
                        elif variant == 2:
                            content = f'「{selected_word["word"]}」という言葉の読み方は？'
                        else:
                            content = f'「{selected_word["word"]}」の発音は次のどれですか？'
                        correct_answer = selected_word["reading"]
                        # 生成更相关的干扰选项
                        options = [correct_answer]
                        while len(options) < 4:
                            # 生成更合理的假读音，基于日语发音规则
                            syllables = ['あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ', 'さ', 'し', 'す', 'せ', 'そ', 'た', 'ち', 'つ', 'て', 'と', 'な', 'に', 'ぬ', 'ね', 'の', 'は', 'ひ', 'ふ', 'へ', 'ほ', 'ま', 'み', 'む', 'め', 'も', 'や', 'ゆ', 'よ', 'ら', 'り', 'る', 'れ', 'ろ', 'わ', 'を', 'ん']
                            # 根据原单词长度生成相似长度的假读音
                            length = len(selected_word["reading"])
                            distractor = ''.join(random.choice(syllables) for _ in range(max(2, min(length, 5))))
                            if distractor not in options:
                                options.append(distractor)
                        random.shuffle(options)
                        explanation = f'「{selected_word["word"]}」的正确读音是{selected_word["reading"]}，意思是{selected_word["meaning"]}，用法：{selected_word["usage"]}。'
                    else:  # usage
                        # 用法题，增加更多变体
                        if variant == 1:
                            content = f'「{selected_word["word"]}」の正しい使い方は次のどれですか？'
                        elif variant == 2:
                            content = f'「{selected_word["word"]}」を使った正しい文を選んでください。'
                        else:
                            content = f'「{selected_word["word"]}」の用法として正しいのはどれですか？'
                        # 生成用法示例
                        correct_usage = f'私は毎日{selected_word["word"]}を食べます。'
                        correct_answer = correct_usage
                        # 生成干扰选项
                        options = [correct_usage]
                        while len(options) < 4:
                            # 生成错误的用法示例
                            wrong_words = vocab_words[level]
                            wrong_word = random.choice(wrong_words)
                            while wrong_word['word'] == selected_word['word']:
                                wrong_word = random.choice(wrong_words)
                            wrong_usage = f'私は毎日{wrong_word["word"]}を{selected_word["word"]}ます。'
                            if wrong_usage not in options:
                                options.append(wrong_usage)
                        random.shuffle(options)
                        explanation = f'「{selected_word["word"]}」的意思是{selected_word["meaning"]}，读音是{selected_word["reading"]}，正确用法是：{correct_usage}。'
            
            return (content, options, correct_answer, explanation)
        except Exception as e:
            logger.error(f"生成日语题目失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            # 返回默认值
            return ("题目生成失败", [], "无", "无")
    
    def _generate_japanese_case_analysis(self, level, category):
        """生成日语案例分析题"""
        # 示例案例分析题生成
        cases = [
            {
                'scenario': 'あなたは日本の企業で働く新入社員です。上司から、客先との会議の準備を任されました。会議の前日に、客先から会議の時間変更の連絡が来ました。この場合、どのように対応しますか？',
                'correct_answer': '1. まず客先の時間変更の要請を確認し、了解を伝える。2. 上司に会議時間の変更を報告し、承認を得る。3. 会議室の予約変更を行う。4. 関係者全員に会議時間の変更を通知する。5. 変更後の準備を再度確認する。',
                'explanation': 'この場合、客先の要請に迅速に対応し、上司と関係者に適切に情報共有することが重要です。'
            },
            {
                'scenario': 'あなたは日本語学校の教師です。学生から「敬語の使い方が分からない」と相談されました。どのように指導しますか？',
                'correct_answer': '1. 敬語の基本的な分類（尊敬語、謙譲語、丁寧語）を説明する。2. それぞれの使用場面と例を挙げる。3. 学生が実際に使ってみる練習をする。4. 誤った使用例を分析し、正しい使い方を教える。5. 日常生活での敬語の使用例を観察するように指導する。',
                'explanation': '敬語の指導では、理論と実践を組み合わせ、学生の理解度に合わせた指導が効果的です。'
            }
        ]
        
        selected_case = random.choice(cases)
        return (
            selected_case['scenario'],
            [],  # 案例分析题不需要选项
            selected_case['correct_answer'],
            selected_case['explanation']
        )
    
    def _generate_japanese_comprehensive(self, level, category):
        """生成日语综合应用题"""
        # 示例综合应用题生成
        comprehensive_questions = [
            {
                'content': '以下の文章を読み、質問に答えてください。\n\n日本は島国であり、四季の変化がはっきりしています。春には桜が咲き、夏は暑くて雨が多く、秋は紅葉が美しく、冬は寒くて雪が降ります。日本の文化は四季と密接に関係しています。例えば、春にはお花見が行われ、秋には紅葉狩りが人気です。\n\n質問：日本の四季の特徴を説明し、文化との関係を例を挙げて説明してください。',
                'correct_answer': '日本の四季の特徴は、春に桜が咲き、夏は暑くて雨が多く、秋は紅葉が美しく、冬は寒くて雪が降ることです。文化との関係として、春にはお花見が行われ、秋には紅葉狩りが人気です。これらの行事は四季の変化を楽しみ、自然との調和を大切にする日本の文化を反映しています。',
                'explanation': 'この問題では、文章の内容を理解し、日本の四季の特徴と文化との関係を正確に説明することが求められます。'
            },
            {
                'content': '以下の会話を読み、質問に答えてください。\n\nA: こんにちは。すみません、新宿へ行くにはどの電車に乗ればいいですか？\nB: 新宿ですか。JR山手線が便利ですよ。ここから徒歩5分の駅で乗れます。\nA: そうですか。どのホームに行けばいいですか？\nB: 3番ホームです。次の電車は15分後に来ますよ。\nA: ありがとうございます。\n\n質問：Aさんはどこへ行きたいですか？どの電車に乗ればいいですか？どのホームで乗れますか？次の電車はいつ来ますか？',
                'correct_answer': 'Aさんは新宿へ行きたいです。JR山手線に乗ればいいです。3番ホームで乗れます。次の電車は15分後に来ます。',
                'explanation': 'この問題では、会話の内容を正確に理解し、複数の質問に答えることが求められます。'
            }
        ]
        
        selected_question = random.choice(comprehensive_questions)
        return (
            selected_question['content'],
            [],  # 综合应用题不需要选项
            selected_question['correct_answer'],
            selected_question['explanation']
        )
    
    def _generate_japanese_translation(self, level, category):
        """生成日语翻译题"""
        # 示例翻译题生成
        translation_pairs = [
            {
                'content': '将以下日语句子翻译成中文：「私は毎日日本語を勉強しています。」',
                'correct_answer': '我每天都在学习日语。',
                'explanation': '日语句子「私は毎日日本語を勉強しています。」中，「私は」表示「我」，「毎日」表示「每天」，「日本語を勉強しています」表示「正在学习日语」。'
            },
            {
                'content': '将以下中文句子翻译成日语：「今天天气很好。」',
                'correct_answer': '今日は天気が良いです。',
                'explanation': '中文句子「今天天气很好」中，「今天」表示「今日は」，「天气很好」表示「天気が良いです」。'
            }
        ]
        
        selected_pair = random.choice(translation_pairs)
        return (
            selected_pair['content'],
            [],  # 翻译题不需要选项
            selected_pair['correct_answer'],
            selected_pair['explanation']
        )
        
    def _generate_japanese_intensive_reading(self, level, category):
        """生成日语精读题"""
        # 示例精读题生成
        intensive_reading_content = [
            {
                'passage': '昨日は日曜日でした。私は友達と一緒に公園へ行きました。公園にはたくさんの人がいました。私たちはピクニックをしました。午後は映画を見ました。とても楽しかったです。',
                'question': '昨日は何曜日でしたか？',
                'options': ['月曜日', '火曜日', '水曜日', '日曜日'],
                'correct_answer': '日曜日',
                'explanation': '文章の最初に「昨日は日曜日でした」と書かれています。'
            },
            {
                'passage': '現代社会において、テクノロジーの発展は私たちの生活を大きく変えています。特にインターネットとスマートフォンの普及により、情報の取得やコミュニケーションの方法は以前と比べて大幅に改善されました。しかし、その一方で、テクノロジー依存症やプライバシーの問題も生じています。私たちはテクノロジーの利点を活かしながら、その弊害にも注意する必要があります。',
                'question': 'テクノロジーの普及により改善されたものはどれですか？',
                'options': ['交通手段', '食生活', '情報の取得とコミュニケーション', '住宅環境'],
                'correct_answer': '情報の取得とコミュニケーション',
                'explanation': '文章の中に「特にインターネットとスマートフォンの普及により、情報の取得やコミュニケーションの方法は以前と比べて大幅に改善されました」と書かれています。'
            },
            {
                'passage': '日本の経済は第二次世界大戦後、奇跡的な発展を遂げました。これは主に、高度な教育水準を持つ労働力、政府の産業政策、企業の革新的な管理手法、そして海外市場への積極的な進出によるものです。しかし、近年は少子高齢化、人口減少、グローバル競争の激化などの課題に直面しています。日本経済の将来を考える上で、これらの課題にどう対応するかが重要な問題となっています。',
                'question': '近年、日本経済が直面している課題はどれですか？',
                'options': ['労働力不足とインフレ', '少子高齢化と人口減少', '貿易赤字と通貨安', '環境問題とエネルギー不足'],
                'correct_answer': '少子高齢化と人口減少',
                'explanation': '文章の中に「しかし、近年は少子高齢化、人口減少、グローバル競争の激化などの課題に直面しています」と書かれています。'
            }
        ]
        
        selected_content = random.choice(intensive_reading_content)
        content = f"以下の文章を読んで、質問に答えてください。\n\n{selected_content['passage']}\n\n質問：{selected_content['question']}"
        
        return (
            content,
            selected_content['options'],
            selected_content['correct_answer'],
            selected_content['explanation']
        )
    
    def _generate_english_question(self, level, category, existing_questions, question_type='multiple_choice'):
        """生成英语题目"""
        try:
            # 增加随机变体，避免重复
            variant = random.randint(1, 3)
            
            if category == '词汇题':
                # 英语词汇题生成逻辑
                vocab_words = {
                    'beginner': [
                        {'word': 'cat', 'meaning': '猫', 'usage': '动物名称'},
                        {'word': 'dog', 'meaning': '狗', 'usage': '动物名称'},
                        {'word': 'book', 'meaning': '书', 'usage': '物品名称'},
                        {'word': 'pen', 'meaning': '钢笔', 'usage': '物品名称'},
                        {'word': 'run', 'meaning': '跑', 'usage': '动词'},
                        {'word': 'eat', 'meaning': '吃', 'usage': '动词'},
                        {'word': 'red', 'meaning': '红色', 'usage': '颜色'},
                        {'word': 'blue', 'meaning': '蓝色', 'usage': '颜色'},
                        {'word': 'happy', 'meaning': '开心', 'usage': '形容词'},
                        {'word': 'sad', 'meaning': '悲伤', 'usage': '形容词'}
                    ],
                    'intermediate': [
                        {'word': 'beautiful', 'meaning': '美丽的', 'usage': '形容词'},
                        {'word': 'difficult', 'meaning': '困难的', 'usage': '形容词'},
                        {'word': 'important', 'meaning': '重要的', 'usage': '形容词'},
                        {'word': 'develop', 'meaning': '发展', 'usage': '动词'},
                        {'word': 'improve', 'meaning': '改进', 'usage': '动词'},
                        {'word': 'technology', 'meaning': '技术', 'usage': '名词'},
                        {'word': 'education', 'meaning': '教育', 'usage': '名词'},
                        {'word': 'environment', 'meaning': '环境', 'usage': '名词'},
                        {'word': 'communication', 'meaning': '交流', 'usage': '名词'},
                        {'word': 'innovation', 'meaning': '创新', 'usage': '名词'}
                    ],
                    'advanced': [
                        {'word': 'sophisticated', 'meaning': '复杂的', 'usage': '形容词'},
                        {'word': 'comprehensive', 'meaning': '全面的', 'usage': '形容词'},
                        {'word': 'analytical', 'meaning': '分析的', 'usage': '形容词'},
                        {'word': 'implement', 'meaning': '实施', 'usage': '动词'},
                        {'word': 'facilitate', 'meaning': '促进', 'usage': '动词'},
                        {'word': 'infrastructure', 'meaning': '基础设施', 'usage': '名词'},
                        {'word': 'sustainability', 'meaning': '可持续性', 'usage': '名词'},
                        {'word': 'competitive', 'meaning': '竞争的', 'usage': '形容词'},
                        {'word': 'collaborative', 'meaning': '协作的', 'usage': '形容词'},
                        {'word': 'strategic', 'meaning': '战略的', 'usage': '形容词'}
                    ],
                    'expert': [
                        {'word': 'ephemeral', 'meaning': '短暂的', 'usage': '形容词'},
                        {'word': 'ubiquitous', 'meaning': '普遍存在的', 'usage': '形容词'},
                        {'word': 'pervasive', 'meaning': '普遍的', 'usage': '形容词'},
                        {'word': 'ameliorate', 'meaning': '改善', 'usage': '动词'},
                        {'word': 'exacerbate', 'meaning': '加剧', 'usage': '动词'},
                        {'word': 'paradigm', 'meaning': '范式', 'usage': '名词'},
                        {'word': 'conundrum', 'meaning': '难题', 'usage': '名词'},
                        {'word': 'ambiguity', 'meaning': '歧义', 'usage': '名词'},
                        {'word': 'nuance', 'meaning': '细微差别', 'usage': '名词'},
                        {'word': 'idiosyncratic', 'meaning': '特有的', 'usage': '形容词'}
                    ]
                }
                
                # 随机选择一个词汇
                if level not in vocab_words:
                    level = 'beginner'
                selected_word = random.choice(vocab_words[level])
                
                if question_type == 'true_false':
                    # 判断题
                    if random.choice([True, False]):
                        content = f'The word "{selected_word["word"]}" means "{selected_word["meaning"]}".'
                        correct_answer = '对'
                        explanation = f'The word "{selected_word["word"]}" indeed means "{selected_word["meaning"]}".'
                    else:
                        # 从其他单词中选择干扰选项
                        wrong_words = vocab_words[level]
                        wrong_word = random.choice(wrong_words)
                        while wrong_word['word'] == selected_word['word']:
                            wrong_word = random.choice(wrong_words)
                        content = f'The word "{selected_word["word"]}" means "{wrong_word["meaning"]}".'
                        correct_answer = '错'
                        explanation = f'The word "{selected_word["word"]}" means "{selected_word["meaning"]}", not "{wrong_word["meaning"]}".'
                    options = ['对', '错']
                elif question_type == 'fill_in_blank':
                    # 填空题
                    content = f'The English word for "{selected_word["meaning"]}" is ____.'
                    correct_answer = selected_word["word"]
                    options = [correct_answer]
                    explanation = f'The English word for "{selected_word["meaning"]}" is "{selected_word["word"]}".'
                elif question_type == 'short_answer':
                    # 简答题
                    content = f'What does the word "{selected_word["word"]}" mean?'
                    correct_answer = selected_word["meaning"]
                    options = []
                    explanation = f'The word "{selected_word["word"]}" means "{selected_word["meaning"]}".'
                else:  # multiple_choice
                    # 选择题
                    vocab_question_types = ['meaning', 'usage']
                    vocab_question_type = random.choice(vocab_question_types)
                    
                    if vocab_question_type == 'meaning':
                        # 词义题
                        content = f'What does the word "{selected_word["word"]}" mean?'
                        correct_answer = selected_word["meaning"]
                        # 生成更相关的干扰选项
                        options = [correct_answer]
                        while len(options) < 4:
                            other_words = vocab_words[level]
                            distractor_word = random.choice(other_words)
                            while distractor_word['word'] == selected_word['word'] or distractor_word['meaning'] in options:
                                distractor_word = random.choice(other_words)
                            distractor = distractor_word['meaning']
                            options.append(distractor)
                        random.shuffle(options)
                        explanation = f'The word "{selected_word["word"]}" means "{selected_word["meaning"]}".'
                    else:  # usage
                        # 用法题
                        content = f'Which of the following is the correct usage of "{selected_word["word"]}"?'
                        correct_usage = f'The {selected_word["usage"]} "{selected_word["word"]}" is important.'
                        correct_answer = correct_usage
                        # 生成干扰选项
                        options = [correct_usage]
                        while len(options) < 4:
                            wrong_words = vocab_words[level]
                            wrong_word = random.choice(wrong_words)
                            while wrong_word['word'] == selected_word['word']:
                                wrong_word = random.choice(wrong_words)
                            wrong_usage = f'The {wrong_word["usage"]} "{wrong_word["word"]}" is important.'
                            if wrong_usage not in options:
                                options.append(wrong_usage)
                        random.shuffle(options)
                        explanation = f'The correct usage of "{selected_word["word"]}" is: {correct_usage}.'
            else:
                # 其他类型的英语题目
                if question_type == 'multiple_choice':
                    # 语法题
                    grammar_topics = {
                        'beginner': [
                            'present tense',
                            'past tense',
                            'articles',
                            'prepositions'
                        ],
                        'intermediate': [
                            'present perfect',
                            'past perfect',
                            'modal verbs',
                            'conditional sentences'
                        ],
                        'advanced': [
                            'passive voice',
                            'reported speech',
                            'gerunds and infinitives',
                            'complex sentences'
                        ],
                        'expert': [
                            'subjunctive mood',
                            'advanced conditional sentences',
                            'advanced phrasal verbs',
                            'idiomatic expressions'
                        ]
                    }
                    
                    topic = random.choice(grammar_topics.get(level, grammar_topics['beginner']))
                    
                    if topic == 'present tense':
                        content = 'Which sentence is in the present tense?'
                        options = [
                            'I eat breakfast every day.',
                            'I ate breakfast yesterday.',
                            'I will eat breakfast tomorrow.',
                            'I have eaten breakfast.'
                        ]
                        correct_answer = 'I eat breakfast every day.'
                        explanation = 'The sentence "I eat breakfast every day." is in the present simple tense.'
                    elif topic == 'past tense':
                        content = 'Which sentence is in the past tense?'
                        options = [
                            'I eat breakfast every day.',
                            'I ate breakfast yesterday.',
                            'I will eat breakfast tomorrow.',
                            'I have eaten breakfast.'
                        ]
                        correct_answer = 'I ate breakfast yesterday.'
                        explanation = 'The sentence "I ate breakfast yesterday." is in the past simple tense.'
                    elif topic == 'articles':
                        content = 'Which sentence uses articles correctly?'
                        options = [
                            'I am student.',
                            'I am a student.',
                            'I am the student.',
                            'I am an student.'
                        ]
                        correct_answer = 'I am a student.'
                        explanation = 'The sentence "I am a student." uses the indefinite article "a" correctly.'
                    else:
                        content = 'Which sentence is grammatically correct?'
                        options = [
                            'He goes to school every day.',
                            'He go to school every day.',
                            'He going to school every day.',
                            'He gone to school every day.'
                        ]
                        correct_answer = 'He goes to school every day.'
                        explanation = 'The sentence "He goes to school every day." is grammatically correct.'
                else:
                    # 其他题型
                    content = "This is an English question."
                    options = ["Option A", "Option B", "Option C", "Option D"]
                    correct_answer = "Option A"
                    explanation = "This is the explanation for the question."
            
            return (content, options, correct_answer, explanation)
        except Exception as e:
            logger.error(f"生成英语题目失败: {str(e)}")
            # 返回默认值
            return ("题目生成失败", [], "无", "无")
    
    def _generate_english_case_analysis(self, level, category):
        """生成英语案例分析题"""
        # 示例案例分析题生成
        cases = [
            {
                'scenario': 'You are an intern at a multinational company. Your manager asks you to prepare a presentation for an important client meeting. The meeting is scheduled for tomorrow, but you realize you don\'t have all the necessary information. What should you do?',
                'correct_answer': '1. First, identify exactly what information is missing. 2. Contact your manager immediately to explain the situation. 3. Ask for help from colleagues who might have the information. 4. If the information can\'t be obtained in time, propose a revised plan to your manager, such as rescheduling part of the presentation. 5. Prepare thoroughly with the information you do have.',
                'explanation': 'In this case, it\'s important to communicate proactively with your manager and team, while also taking initiative to solve the problem.'
            }
        ]
        
        selected_case = random.choice(cases)
        return (
            selected_case['scenario'],
            [],  # 案例分析题不需要选项
            selected_case['correct_answer'],
            selected_case['explanation']
        )
    
    def _generate_english_comprehensive(self, level, category):
        """生成英语综合应用题"""
        # 示例综合应用题生成
        comprehensive_questions = [
            {
                'content': 'Read the following passage and answer the question.\n\nEnglish is a global language used in business, education, and communication worldwide. It has evolved over centuries, absorbing words from many other languages such as French, Latin, and German. Today, English is the most widely spoken language in the world, with over 1.5 billion people speaking it either as a first or second language.\n\nQuestion: Why is English considered a global language? Explain its importance in various fields.',
                'correct_answer': 'English is considered a global language because it is used extensively in business, education, and communication worldwide. It has evolved over centuries, absorbing words from many other languages. Its importance lies in facilitating international communication, enabling global business transactions, providing access to a vast amount of information and resources, and serving as a common language in fields like science, technology, and diplomacy.',
                'explanation': 'This question tests the ability to understand the passage and explain the global significance of English.'
            }
        ]
        
        selected_question = random.choice(comprehensive_questions)
        return (
            selected_question['content'],
            [],  # 综合应用题不需要选项
            selected_question['correct_answer'],
            selected_question['explanation']
        )
    
    def _generate_english_translation(self, level, category):
        """生成英语翻译题"""
        # 示例翻译题生成
        translation_pairs = [
            {
                'content': 'Translate the following English sentence into Chinese: "The quick brown fox jumps over the lazy dog."',
                'correct_answer': '敏捷的棕色狐狸跳过了懒惰的狗。',
                'explanation': 'This is a classic pangram that contains all letters of the English alphabet.'
            },
            {
                'content': 'Translate the following Chinese sentence into English: "学习一门新语言需要时间和练习。"',
                'correct_answer': 'Learning a new language requires time and practice.',
                'explanation': 'The Chinese sentence "学习一门新语言需要时间和练习" translates to "Learning a new language requires time and practice" in English.'
            }
        ]
        
        selected_pair = random.choice(translation_pairs)
        return (
            selected_pair['content'],
            [],  # 翻译题不需要选项
            selected_pair['correct_answer'],
            selected_pair['explanation']
        )
    
    def _get_needed_question_types(self, language, level, category):
        """获取需要扩充的题型列表"""
        # 这里是示例实现，实际项目中应根据现有题库的题型分布来确定
        return []
    
    def _get_existing_questions(self, language, level, category, question_type):
        """获取现有题库中的相关题目"""
        # 这里是示例实现，实际项目中应从数据库中查询
        return []

# 创建全局实例
ai_question_generator = AIQuestionGenerator()