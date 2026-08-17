#!/usr/bin/env python3
""" AI听力题优化服务 =============== 提供智能化的听力题生成、练习和评估功能。 支持多语言、多口音、自适应难度、语音识别答题等高级特性。 """
import os
import json
import random
import hashlib
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

logger = logging.getLogger('AIListeningService')


class AIListeningService:
    """AI听力题服务"""

    def __init__(self):
        self._listening_employee = None
        self._audio_manager = None
        self._init_cache()
        logger.info("[AIListeningService] AI听力题服务初始化成功")

    def _init_cache(self):
        """初始化缓存"""
        self._question_cache = {}
        self._audio_cache = {}
        self._user_level_cache = {}
        self._cache_ttl = 3600

    def _get_listening_employee(self):
        """获取听力题库AI员工"""
        if self._listening_employee is None:
            try:
                from ai_engines.listening_question_employee import create_listening_question_employee
                self._listening_employee = create_listening_question_employee(level=7)
                self._listening_employee.start()
            except Exception as e:
                logger.error(f"创建听力题库员工失败: {e}")
        return self._listening_employee

    def _get_audio_manager(self):
        """获取音频管理器"""
        if self._audio_manager is None:
            try:
                from ai_engines.audio_manager import audio_manager
                self._audio_manager = audio_manager
            except Exception as e:
                logger.error(f"获取音频管理器失败: {e}")
        return self._audio_manager

    def generate_ai_listening_questions(self, language: str = 'english', 
                                         count: int = 5, difficulty: int = None,
                                         topic: str = None, accent: str = None,
                                         voice: str = None, user_level: str = None) -> List[Dict]:
        """AI生成听力题目  参数: language: 语言 (english/japanese/chinese/korean/french/german/spanish) count: 题目数量 difficulty: 难度级别 (1-4) topic: 主题 accent: 口音 voice: 音色 user_level: 用户级别，用于自适应难度 """
        questions = []
        
        employee = self._get_listening_employee()
        if employee:
            task_data = {
                'task_type': 'generate_listening',
                'language': language,
                'count': count,
                'difficulty': difficulty,
                'topic': topic,
                'accent': accent,
                'voice': voice
            }
            
            result = employee.execute_task(task_data)
            
            if result.get('success') and result.get('questions'):
                questions = result['questions']
        
        if not questions:
            questions = self._generate_fallback_questions(language, count, difficulty, topic)
        
        for question in questions:
            question['audio_url'] = self._generate_audio_for_question(question)
            question['transcript'] = question.get('transcript', question.get('content', ''))
        
        logger.info(f"AI生成听力题: {len(questions)}道, 语言: {language}")
        return questions

    def _generate_fallback_questions(self, language: str, count: int, 
                                      difficulty: int = None, topic: str = None) -> List[Dict]:
        """降级生成听力题目"""
        fallback_templates = {
            'english': self._get_english_templates(),
            'japanese': self._get_japanese_templates(),
            'chinese': self._get_chinese_templates(),
            'korean': self._get_korean_templates(),
            'french': self._get_french_templates(),
            'german': self._get_german_templates(),
            'spanish': self._get_spanish_templates()
        }
        
        templates = fallback_templates.get(language, fallback_templates['english'])
        
        if difficulty:
            diff_map = {1: 'easy', 2: 'medium', 3: 'hard', 4: 'expert'}
            diff_key = diff_map.get(difficulty, 'medium')
            available = [t for t in templates if t['difficulty'] == diff_key]
        else:
            available = templates
        
        if topic:
            available = [t for t in available if topic.lower() in t['topic'].lower()]
        
        if not available:
            available = templates
        
        questions = []
        for i in range(count):
            template = random.choice(available)
            question = self._convert_template_to_question(template, i)
            questions.append(question)
        
        return questions

    def _get_english_templates(self) -> List[Dict]:
        """英语听力模板"""
        return [
            {'difficulty': 'easy', 'topic': 'Daily Life',
             'dialogue': 'A: Good morning! How are you today?\nB: I\'m fine, thank you. And you?\nA: I\'m great, thanks.',
             'question': 'How is person B feeling?',
             'options': ['Fine', 'Tired', 'Sick', 'Sad'], 'answer': 'A'},
            {'difficulty': 'easy', 'topic': 'Shopping',
             'dialogue': 'A: How much is this shirt?\nB: It\'s $25.\nA: OK, I\'ll take it.',
             'question': 'What does the person want to buy?',
             'options': ['A shirt', 'A dress', 'Shoes', 'A hat'], 'answer': 'A'},
            {'difficulty': 'medium', 'topic': 'Work',
             'dialogue': 'A: Did you finish the report?\nB: Almost. I need to add last quarter\'s data.\nA: When will  you be done?\nB: Probably by 3 PM.',
             'question': 'When will the report be finished?',
             'options': ['By 3 PM', 'By 4 PM', 'By 5 PM', 'Tomorrow'], 'answer': 'A'},
            {'difficulty': 'medium', 'topic': 'Travel',
             'dialogue': 'A: When does the train leave?\nB: At 9:30 AM. You need to arrive 30 minutes early.\nA: What  platform?\nB: Platform 5.',
             'question': 'Which platform is the train on?',
             'options': ['Platform 5', 'Platform 3', 'Platform 7', 'Platform 9'], 'answer': 'A'},
            {'difficulty': 'hard', 'topic': 'Technology',
             'dialogue': 'Artificial intelligence is transforming industries worldwide. From healthcare to finance, AI improves efficiency. However, ethical concerns about privacy and employment remain.',
             'question': 'What is the main topic?',
             'options': ['AI impact on society', 'Healthcare technology', 'Financial services',
             'Employment statistics'], 'answer': 'A'},
            {'difficulty': 'hard', 'topic': 'Environment',
             'dialogue': 'Climate change poses significant challenges. Rising temperatures affect ecosystems globally.  Governments are implementing policies to reduce carbon emissions and promote renewable energy.',
             'question': 'What are governments doing about climate change?',
             'options': ['Reducing emissions', 'Ignoring the problem', 'Building more factories',
             'Increasing pollution'], 'answer': 'A'},
            {'difficulty': 'expert', 'topic': 'Business',
             'dialogue': 'The quarterly earnings report shows a 15% increase in revenue compared to last year. Market  analysts attribute this growth to successful product launches and expanded market reach in emerging economies.',
             'question': 'What caused the revenue increase?',
             'options': ['Product launches', 'Economic recession', 'Cost cutting', 'Market decline'], 'answer': 'A'},
            {'difficulty': 'expert', 'topic': 'Science',
             'dialogue': 'Recent research on quantum computing has demonstrated significant breakthroughs in  computational speed. These developments could revolutionize cryptography, drug discovery, and complex system simulation.',
             'question': 'What could quantum computing revolutionize?',
             'options': ['Cryptography', 'Traditional computing', 'Mechanical engineering', 'Agriculture'],
             'answer': 'A'}
        ]

    def _get_japanese_templates(self) -> List[Dict]:
        """日语听力模板"""
        return [
            {'difficulty': 'easy', 'topic': '日常生活',
             'dialogue': 'A: こんにちは。元気ですか。\nB: はい、元気です。あなたは？\nA: 私も元気です。',
             'question': 'Bは元気ですか？',
             'options': ['はい', 'いいえ', '分かりません', 'まあまあ'], 'answer': 'A'},
            {'difficulty': 'easy', 'topic': '購入',
             'dialogue': 'A: このりんごはいくらですか。\nB: 一つ200円です。\nA: 三つください。',
             'question': 'りんごはいくらですか？',
             'options': ['200円', '300円', '500円', '600円'], 'answer': 'A'},
            {'difficulty': 'medium', 'topic': '学校',
             'dialogue': 'A: 明日の試験、準備はできましたか。\nB: まだです。数学が難しいです。\nA: 一緒に勉強しませんか。\nB: いいですね。図書館で午後2時からです。',
             'question': '二人はどこで勉強しますか？',
             'options': ['図書館', '教室', 'カフェ', '家'], 'answer': 'A'},
            {'difficulty': 'medium', 'topic': '交通',
             'dialogue': 'A: バスは何時に来ますか。\nB: 8時半に来ます。\nA: 遅れていませんか。\nB: いいえ、時間通りです。',
             'question': 'バスは何時に来ますか？',
             'options': ['8時半', '9時', '8時', '9時半'], 'answer': 'A'},
            {'difficulty': 'hard', 'topic': '社会',
             'dialogue': '高齢化社会の進行に伴い、医療や介護の問題が深刻化しています。政府は様々な施策を講じていますが、解決には時間がかかりそうです。',
             'question': 'この話の内容と合っているものはどれですか？',
             'options': ['高齢化問題は深刻', '医療問題は解決した', '政府は何もしていない', '問題は存在しない'], 'answer': 'A'},
            {'difficulty': 'hard', 'topic': '経済',
             'dialogue': '最近の経済状況は厳しいです。物価の上昇や雇用の不安が続いています。多くの企業が節約を迫られています。',
             'question': '企業は何を迫られていますか？',
             'options': ['節約', '拡大', '投資', '撤退'], 'answer': 'A'}
        ]

    def _get_chinese_templates(self) -> List[Dict]:
        """中文听力模板"""
        return [
            {'difficulty': 'easy', 'topic': '日常',
             'dialogue': 'A: 你好！最近怎么样？\nB: 我很好，谢谢。你呢？\nA: 我也很好。',
             'question': 'B最近怎么样？',
             'options': ['很好', '不好', '一般', '不知道'], 'answer': 'A'},
            {'difficulty': 'easy', 'topic': '购物',
             'dialogue': 'A: 这件衣服多少钱？\nB: 150元。\nA: 便宜一点可以吗？\nB: 最低130元。',
             'question': '这件衣服最低多少钱？',
             'options': ['130元', '150元', '100元', '200元'], 'answer': 'A'},
            {'difficulty': 'medium', 'topic': '工作',
             'dialogue': 'A: 会议准备得怎么样了？\nB: 差不多了，就差PPT了。\nA: 什么时候能完成？\nB: 今天下午应该可以。',
             'question': 'PPT什么时候能完成？',
             'options': ['今天下午', '明天', '后天', '下周'], 'answer': 'A'},
            {'difficulty': 'hard', 'topic': '科技',
             'dialogue': '人工智能正在改变我们的生活方式。从智能家居到自动驾驶，AI技术应用越来越广泛。但同时也带来了隐私和就业等问题。',
             'question': '人工智能带来了什么问题？',
             'options': ['隐私和就业', '环境污染', '能源消耗', '交通拥堵'], 'answer': 'A'}
        ]

    def _get_korean_templates(self) -> List[Dict]:
        """韩语听力模板"""
        return [
            {'difficulty': 'easy', 'topic': '일상',
             'dialogue': 'A: 안녕하세요! 잘 지냈어요?\nB: 네, 잘 지냈어요. 당신은요?\nA: 저도 잘 지냈어요.',
             'question': 'B는 어떻게 지냈어요?',
             'options': ['잘 지냈어요', '안 좋아요', '모르겠어요', '보통이에요'], 'answer': 'A'},
            {'difficulty': 'medium', 'topic': '쇼핑',
             'dialogue': 'A: 이 옷은 얼마예요?\nB: 5만 원입니다.\nA: 좀 깎아주세요.\nB: 최소 4만5천 원입니다.',
             'question': '옷은 최소 얼마예요?',
             'options': ['4만5천 원', '5만 원', '4만 원', '6만 원'], 'answer': 'A'}
        ]

    def _get_french_templates(self) -> List[Dict]:
        """法语听力模板"""
        return [
            {'difficulty': 'easy', 'topic': 'Quotidien',
             'dialogue': 'A: Bonjour! Comment ça va?\nB: Ça va bien, merci. Et toi?\nA: Ça va bien aussi.',
             'question': 'Comment ça va pour B?',
             'options': ['Bien', 'Mal', 'Moyen', 'Inconnu'], 'answer': 'A'},
            {'difficulty': 'medium', 'topic': 'Magasin',
             'dialogue': 'A: Combien coûte ce chemisier?\nB: Il coûte 45 euros.\nA: Pouvez-vous me faire un prix?\nB:  Le minimum est 38 euros.',
             'question': 'Quel est le prix minimum?',
             'options': ['38 euros', '45 euros', '40 euros', '50 euros'], 'answer': 'A'}
        ]

    def _get_german_templates(self) -> List[Dict]:
        """德语听力模板"""
        return [
            {'difficulty': 'easy', 'topic': 'Alltag',
             'dialogue': 'A: Hallo! Wie geht es dir?\nB: Es geht mir gut, danke. Und dir?\nA: Auch mir gut.',
             'question': 'Wie geht es B?',
             'options': ['Gut', 'Schlecht', 'Mittel', 'Unbekannt'], 'answer': 'A'},
            {'difficulty': 'medium', 'topic': 'Einkaufen',
             'dialogue': 'A: Wie viel kostet dieses Hemd?\nB: Es kostet 35 Euro.\nA: Kannst du einen Rabatt geben?\nB:  Der Mindestpreis ist 30 Euro.',
             'question': 'Was ist der Mindestpreis?',
             'options': ['30 Euro', '35 Euro', '25 Euro', '40 Euro'], 'answer': 'A'}
        ]

    def _get_spanish_templates(self) -> List[Dict]:
        """西班牙语听力模板"""
        return [
            {'difficulty': 'easy', 'topic': 'Diario',
             'dialogue': 'A: ¡Hola! ¿Cómo estás?\nB: Estoy bien, gracias. ¿Y tú?\nA: También estoy bien.',
             'question': '¿Cómo está B?',
             'options': ['Bien', 'Mal', 'Regular', 'Desconocido'], 'answer': 'A'},
            {'difficulty': 'medium', 'topic': 'Compras',
             'dialogue': 'A: ¿Cuánto cuesta esta camisa?\nB: Cuesta 40 euros.\nA: ¿Me puede hacer un descuento?\nB: El  precio mínimo es 35 euros.',
             'question': '¿Cuál es el precio mínimo?',
             'options': ['35 euros', '40 euros', '30 euros', '45 euros'], 'answer': 'A'}
        ]

    def _convert_template_to_question(self, template: Dict, index: int) -> Dict:
        """将模板转换为题目格式"""
        return {
            'id': f'ai_listen_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{index}',
            'type': 'listening',
            'subject': self._get_subject_from_language(template.get('topic', '')),
            'content': template['question'],
            'options': [{'key': chr(65 + i), 'value': opt} for i, opt in enumerate(template['options'])],
            'correct_answer': template['answer'],
            'explanation': f"听力原文：{template['dialogue']}",
            'difficulty': template['difficulty'],
            'topic': template['topic'],
            'transcript': template['dialogue'],
            'score': self._get_score_by_difficulty(template['difficulty']),
            'audio_url': None
        }

    def _get_subject_from_language(self, topic: str) -> str:
        """根据主题获取科目"""
        if any(t in topic.lower() for t in ['japanese', '日本', 'にほん']):
            return 'japanese'
        elif any(t in topic.lower() for t in ['korean', '韩国', '한국']):
            return 'korean'
        elif any(t in topic.lower() for t in ['french', '法国', 'français']):
            return 'french'
        elif any(t in topic.lower() for t in ['german', '德国', 'deutsch']):
            return 'german'
        elif any(t in topic.lower() for t in ['spanish', '西班牙', 'español']):
            return 'spanish'
        elif any(t in topic.lower() for t in ['chinese', '中文', '中国']):
            return 'chinese'
        return 'english'

    def _get_score_by_difficulty(self, difficulty: str) -> float:
        """根据难度获取分值"""
        scores = {'easy': 2.0, 'medium': 5.0, 'hard': 10.0, 'expert': 15.0}
        return scores.get(difficulty, 5.0)

    def _generate_audio_for_question(self, question: Dict) -> Optional[str]:
        """为题目生成音频"""
        try:
            dialogue = question.get('transcript', question.get('content', ''))
            if not dialogue:
                return None

            audio_manager = self._get_audio_manager()
            if audio_manager:
                language = question.get('language', 'english')
                accent = question.get('accent', 'standard')
                voice = question.get('voice', 'standard')
                
                result = audio_manager.text_to_speech(
                    text=dialogue,
                    language=language,
                    voice_type=accent,
                    speed=1.0
                )
                
                if result.get('success'):
                    return result['audio_url']
        except Exception as e:
            logger.error(f"生成音频失败: {e}")
        
        return None

    def generate_adaptive_practice(self, user_id: str, language: str = 'english',
                                   question_count: int = 5) -> List[Dict]:
        """生成自适应听力练习  根据用户历史表现动态调整难度 """
        user_stats = self._get_user_adaptive_stats(user_id, language)
        
        base_difficulty = user_stats.get('recommended_difficulty', 2)
        questions = []
        
        for i in range(question_count):
            difficulty = self._adjust_difficulty(base_difficulty, i, question_count)
            
            batch = self.generate_ai_listening_questions(
                language=language,
                count=1,
                difficulty=difficulty,
                user_level=str(base_difficulty)
            )
            
            if batch:
                questions.extend(batch)
        
        return questions

    def _get_user_adaptive_stats(self, user_id: str, language: str) -> Dict:
        """获取用户自适应统计数据"""
        try:
            from app.services.listening_service import listening_service
            stats = listening_service.get_user_stats(user_id, subject=language)
            
            if stats:
                accuracy = stats.get('accuracy', 0)
                total = stats.get('total_questions', 0)
                
                if total >= 10:
                    if accuracy >= 80:
                        return {'recommended_difficulty': 3, 'accuracy': accuracy}
                    elif accuracy >= 60:
                        return {'recommended_difficulty': 2, 'accuracy': accuracy}
                    else:
                        return {'recommended_difficulty': 1, 'accuracy': accuracy}
            
            return {'recommended_difficulty': 2, 'accuracy': 0}
        except Exception as e:
            logger.error(f"获取用户统计失败: {e}")
            return {'recommended_difficulty': 2, 'accuracy': 0}

    def _adjust_difficulty(self, base: int, index: int, total: int) -> int:
        """调整题目难度"""
        if total <= 3:
            return base
        
        if index == 0:
            return max(1, base - 1)
        elif index == total - 1:
            return min(4, base + 1)
        else:
            return base

    def generate_practice_session(self, user_id: str, language: str = 'english',
                                   question_count: int = 5, mode: str = 'adaptive',
                                   difficulty: int = None, topic: str = None) -> Dict:
        """生成练习会话"""
        start_time = time.time()
        
        if mode == 'adaptive':
            questions = self.generate_adaptive_practice(user_id, language, question_count)
        elif mode == 'review':
            questions = self._generate_review_session(user_id, language, question_count)
        elif mode == 'custom':
            questions = self.generate_ai_listening_questions(
                language=language,
                count=question_count,
                difficulty=difficulty,
                topic=topic
            )
        else:
            questions = self.generate_ai_listening_questions(
                language=language,
                count=question_count
            )
        
        session_id = f"session_{user_id}_{int(time.time())}"
        
        return {
            'success': True,
            'session_id': session_id,
            'questions': questions,
            'language': language,
            'question_count': len(questions),
            'mode': mode,
            'generated_at': datetime.now().isoformat(),
            'generation_time': round(time.time() - start_time, 2)
        }

    def _generate_review_session(self, user_id: str, language: str, count: int) -> List[Dict]:
        """生成复习会话（错题优先）"""
        try:
            from app.services.listening_service import listening_service
            wrong_questions = listening_service.get_user_wrong_questions(user_id, subject=language, limit=count)
            
            if wrong_questions:
                for q in wrong_questions:
                    q['audio_url'] = self._generate_audio_for_question(q)
                return wrong_questions
            
            return self.generate_ai_listening_questions(language=language, count=count)
        except Exception as e:
            logger.error(f"生成复习会话失败: {e}")
            return self.generate_ai_listening_questions(language=language, count=count)

    def get_supported_languages(self) -> List[Dict]:
        """获取支持的语言列表"""
        return [
            {'code': 'english', 'name': '英语', 'accents': ['us', 'uk', 'australia', 'canada', 'india']},
            {'code': 'japanese', 'name': '日语', 'accents': ['kanto', 'kansai']},
            {'code': 'chinese', 'name': '中文', 'accents': ['mandarin', 'cantonese', 'taiwan']},
            {'code': 'korean', 'name': '韩语', 'accents': ['standard']},
            {'code': 'french', 'name': '法语', 'accents': ['standard']},
            {'code': 'german', 'name': '德语', 'accents': ['standard']},
            {'code': 'spanish', 'name': '西班牙语', 'accents': ['standard', 'mexican']}
        ]

    def get_difficulty_levels(self) -> List[Dict]:
        """获取难度级别列表"""
        return [
            {'level': 1, 'name': '初级', 'description': '适合初学者，简单对话'},
            {'level': 2, 'name': '中级', 'description': '适合有一定基础，日常对话'},
            {'level': 3, 'name': '高级', 'description': '适合进阶学习者，复杂对话'},
            {'level': 4, 'name': '专家', 'description': '适合高级学习者，专业内容'}
        ]


ai_listening_service = AIListeningService()