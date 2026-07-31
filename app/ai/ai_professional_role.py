#!/usr/bin/env python3
import os
import json
import time
import sqlite3
import threading
import random
from datetime import datetime
from collections import defaultdict

class ProfessionalRoleProfile:
    ROLES = {
        'software_engineer': {
            'name': '软件工程师',
            'personality': ['analytical', 'logical', 'detail_oriented', 'problem_solver', 'curious'],
            'work_style': 'methodical',
            'domain_expertise': ['programming', 'system_design', 'debugging', 'code_review', 'architecture'],
            'learning_preferences': ['hands_on', 'technical_docs', 'code_examples', 'online_courses'],
            'communication_style': 'direct',
            'motivation_factor': 'challenge'
        },
        'data_scientist': {
            'name': '数据科学家',
            'personality': ['analytical', 'curious', 'creative', 'detail_oriented', 'patient'],
            'work_style': 'exploratory',
            'domain_expertise': ['statistics', 'machine_learning', 'data_analysis', 'visualization', 'modeling'],
            'learning_preferences': ['research_papers', 'data_experiments', 'tutorials', 'competitions'],
            'communication_style': 'data_driven',
            'motivation_factor': 'discovery'
        },
        'system_architect': {
            'name': '系统架构师',
            'personality': ['strategic', 'visionary', 'analytical', 'decisive', 'collaborative'],
            'work_style': 'holistic',
            'domain_expertise': ['system_design', 'scalability', 'security', 'performance', 'integration'],
            'learning_preferences': ['white_papers', 'case_studies', 'conferences', 'industry_blogs'],
            'communication_style': 'strategic',
            'motivation_factor': 'innovation'
        },
        'devops_engineer': {
            'name': 'DevOps工程师',
            'personality': ['pragmatic', 'automation_focused', 'reliability_driven', 'proactive', 'collaborative'],
            'work_style': 'automated',
            'domain_expertise': ['infrastructure', 'automation', 'monitoring', 'deployment', 'security'],
            'learning_preferences': ['tools_docs', 'automation_scripts', 'cloud_platforms', 'CI_CD'],
            'communication_style': 'action_oriented',
            'motivation_factor': 'efficiency'
        },
        'ai_researcher': {
            'name': 'AI研究员',
            'personality': ['curious', 'creative', 'persistent', 'analytical', 'visionary'],
            'work_style': 'experimental',
            'domain_expertise': ['deep_learning', 'nlp', 'computer_vision', 'reinforcement_learning',
            'model_optimization'],
            'learning_preferences': ['arxiv_papers', 'research_projects', 'open_source', 'academic_conferences'],
            'communication_style': 'technical',
            'motivation_factor': 'breakthrough'
        },
        'database_administrator': {
            'name': '数据库管理员',
            'personality': ['detail_oriented', 'patient', 'proactive', 'methodical', 'problem_solver'],
            'work_style': 'systematic',
            'domain_expertise': ['database_design', 'performance_tuning', 'backup_recovery', 'security', 'scaling'],
            'learning_preferences': ['database_docs', 'performance_guides', 'best_practices', 'case_studies'],
            'communication_style': 'precise',
            'motivation_factor': 'reliability'
        },
        'security_specialist': {
            'name': '安全专家',
            'personality': ['detail_oriented', 'skeptical', 'proactive', 'analytical', 'cautious'],
            'work_style': 'defensive',
            'domain_expertise': ['penetration_testing', 'security_audit', 'threat_intelligence', 'secure_coding',
            'incident_response'],
            'learning_preferences': ['security_bulletins', 'CTF_challenges', 'security_conferences',
            'research_reports'],
            'communication_style': 'urgent',
            'motivation_factor': 'protection'
        },
        'quality_assurance': {
            'name': '质量保证工程师',
            'personality': ['detail_oriented', 'patient', 'methodical', 'persistent', 'communicative'],
            'work_style': 'thorough',
            'domain_expertise': ['test_design', 'automation', 'performance_testing', 'usability', 'compliance'],
            'learning_preferences': ['testing_frameworks', 'test_patterns', 'quality_standards', 'tools_training'],
            'communication_style': 'constructive',
            'motivation_factor': 'quality'
        },
        'product_manager': {
            'name': '产品经理',
            'personality': ['creative', 'empathetic', 'strategic', 'communicative', 'organized'],
            'work_style': 'user_focused',
            'domain_expertise': ['product_design', 'roadmap_planning', 'user_research', 'data_analysis',
            'stakeholder_management'],
            'learning_preferences': ['product_books', 'user_interviews', 'case_studies', 'industry_trends'],
            'communication_style': 'persuasive',
            'motivation_factor': 'impact'
        },
        'technical_writer': {
            'name': '技术文档工程师',
            'personality': ['detail_oriented', 'communicative', 'patient', 'analytical', 'organized'],
            'work_style': 'structured',
            'domain_expertise': ['technical_writing', 'documentation_design', 'API_docs', 'tutorials',
            'knowledge_management'],
            'learning_preferences': ['writing_guides', 'style_guides', 'documentation_tools', 'examples'],
            'communication_style': 'clear',
            'motivation_factor': 'clarity'
        },
        'japanese_listener_kansai': {
            'name': '日语听力报读员-关西腔',
            'personality': ['expressive', 'warm', 'humorous', 'casual', 'friendly'],
            'work_style': 'conversational',
            'domain_expertise': ['kansai_dialect', 'osaka_slang', 'kyoto_speech', 'regional_accent', 'casual_japanese'],
            'learning_preferences': ['anime_kansai', 'drama_kansai', 'podcasts_kansai', 'native_speakers'],
            'communication_style': 'lively',
            'motivation_factor': 'cultural_immersion'
        },
        'japanese_listener_kanto': {
            'name': '日语听力报读员-关东腔',
            'personality': ['polite', 'formal', 'reserved', 'precise', 'businesslike'],
            'work_style': 'standard',
            'domain_expertise': ['standard_japanese', 'tokyo_dialect', 'business_japanese', 'formal_speech', 'keigo'],
            'learning_preferences': ['news_japanese', 'business_videos', 'academic_content', 'npr_japan'],
            'communication_style': 'polite',
            'motivation_factor': 'professional_excellence'
        },
        'english_listener_american': {
            'name': '英语听力报读员-美式英语',
            'personality': ['energetic', 'casual', 'friendly', 'direct', 'confident'],
            'work_style': 'dynamic',
            'domain_expertise': ['american_pronunciation', 'slang_us', 'idioms_us', 'culture_us', 'media_us'],
            'learning_preferences': ['hollywood_movies', 'tv_shows_us', 'podcasts_us', 'youtube_us'],
            'communication_style': 'engaging',
            'motivation_factor': 'cultural_connection'
        },
        'english_listener_british': {
            'name': '英语听力报读员-英式英语',
            'personality': ['elegant', 'formal', 'sophisticated', 'reserved', 'refined'],
            'work_style': 'traditional',
            'domain_expertise': ['british_pronunciation', 'slang_uk', 'idioms_uk', 'culture_uk', 'media_uk'],
            'learning_preferences': ['bbc_news', 'uk_tv_shows', 'audiobooks_uk', 'royal_content'],
            'communication_style': 'articulate',
            'motivation_factor': 'linguistic_refinement'
        }
    }

    PERSONALITY_TRAITS = {
        'analytical': {'description': '善于分析问题，逻辑清晰', 'strength': 'problem_analysis', 'weakness': 'over_analysis'},
        'creative': {'description': '富有创造力，善于创新', 'strength': 'innovation', 'weakness': 'practicality'},
        'detail_oriented': {'description': '注重细节，一丝不苟', 'strength': 'accuracy', 'weakness': 'speed'},
        'logical': {'description': '逻辑严密，推理能力强', 'strength': 'reasoning', 'weakness': 'flexibility'},
        'curious': {'description': '好奇心强，乐于探索', 'strength': 'learning', 'weakness': 'focus'},
        'patient': {'description': '耐心细致，不急于求成', 'strength': 'persistence', 'weakness': 'urgency'},
        'strategic': {'description': '战略眼光，大局观强', 'strength': 'vision', 'weakness': 'detail'},
        'decisive': {'description': '果断决策，不犹豫', 'strength': 'action', 'weakness': 'reflection'},
        'collaborative': {'description': '善于协作，团队精神', 'strength': 'teamwork', 'weakness': 'independence'},
        'proactive': {'description': '主动进取，积极主动', 'strength': 'initiative', 'weakness': 'overcommitting'},
        'persistent': {'description': '坚持不懈，不轻言放弃', 'strength': 'determination', 'weakness': 'adaptability'},
        'visionary': {'description': '富有远见，眼光长远', 'strength': 'foresight', 'weakness': 'immediate_action'},
        'pragmatic': {'description': '务实务实，注重实际', 'strength': 'practicality', 'weakness': 'idealism'},
        'communicative': {'description': '善于沟通，表达清晰', 'strength': 'influence', 'weakness': 'over_talking'},
        'organized': {'description': '有条理，善于规划', 'strength': 'efficiency', 'weakness': 'spontaneity'},
        'empathy': {'description': '富有同理心，善于理解他人', 'strength': 'user_insight', 'weakness': 'objectivity'},
        'skeptical': {'description': '批判性思维，不轻信', 'strength': 'security', 'weakness': 'trust'},
        'cautious': {'description': '谨慎小心，风险意识强', 'strength': 'risk_management', 'weakness': 'innovation'},
        'methodical': {'description': '有条不紊，按部就班', 'strength': 'consistency', 'weakness': 'flexibility'},
        'action_oriented': {'description': '行动导向，注重执行', 'strength': 'execution', 'weakness': 'planning'},
        'expressive': {'description': '表达丰富，情感充沛', 'strength': 'communication', 'weakness': 'over_expression'},
        'warm': {'description': '热情温暖，亲和力强', 'strength': 'rapport', 'weakness': 'boundaries'},
        'humorous': {'description': '幽默风趣，善于调侃', 'strength': 'engagement', 'weakness': 'inappropriateness'},
        'casual': {'description': '随性随和，不拘小节', 'strength': 'approachability', 'weakness': 'formality'},
        'friendly': {'description': '友好亲切，容易相处', 'strength': 'likability', 'weakness': 'professionalism'},
        'energetic': {'description': '精力充沛，活力四射', 'strength': 'enthusiasm', 'weakness': 'burnout'},
        'confident': {'description': '自信满满，从容不迫', 'strength': 'leadership', 'weakness': 'overconfidence'},
        'elegant': {'description': '优雅得体，举止大方', 'strength': 'presence', 'weakness': 'rigidity'},
        'formal': {'description': '正式规范，彬彬有礼', 'strength': 'professionalism', 'weakness': 'approachability'},
        'sophisticated': {'description': '老练成熟，品味高雅', 'strength': 'discernment', 'weakness': 'snobbery'},
        'reserved': {'description': '内敛含蓄，沉稳克制', 'strength': 'thoughtfulness', 'weakness': 'expression'},
        'refined': {'description': '精致优雅，精益求精', 'strength': 'quality', 'weakness': 'perfectionism'},
        'lively': {'description': '活泼开朗，充满活力', 'strength': 'energy', 'weakness': 'distraction'},
        'engaging': {'description': '引人入胜，魅力十足', 'strength': 'captivation', 'weakness': 'superficiality'},
        'articulate': {'description': '口齿伶俐，表达清晰', 'strength': 'clarity', 'weakness': 'overly verbose'},
        'businesslike': {'description': '公事公办，专业高效', 'strength': 'efficiency', 'weakness': 'warmth'}
    }

    WORK_STYLES = {
        'methodical': '有条不紊，按计划执行',
        'exploratory': '探索性强，善于发现',
        'holistic': '全局视角，统筹规划',
        'automated': '追求自动化，效率优先',
        'experimental': '勇于尝试，不怕失败',
        'systematic': '系统严谨，注重规范',
        'defensive': '防御为主，风险控制',
        'thorough': '全面细致，不留死角',
        'user_focused': '用户为中心，体验至上',
        'structured': '结构清晰，逻辑严谨',
        'conversational': '轻松对话，自然交流',
        'standard': '标准规范，正式严谨',
        'dynamic': '活力四射，灵活多变',
        'traditional': '传统经典，稳重典雅'
    }

    LEARNING_PREFERENCES = {
        'hands_on': '动手实践',
        'technical_docs': '技术文档',
        'code_examples': '代码示例',
        'online_courses': '在线课程',
        'research_papers': '研究论文',
        'data_experiments': '数据实验',
        'tutorials': '教程',
        'competitions': '竞赛',
        'white_papers': '白皮书',
        'case_studies': '案例研究',
        'conferences': '会议',
        'industry_blogs': '行业博客',
        'tools_docs': '工具文档',
        'automation_scripts': '自动化脚本',
        'cloud_platforms': '云平台',
        'CI_CD': '持续集成/持续部署',
        'arxiv_papers': 'arxiv论文',
        'research_projects': '研究项目',
        'open_source': '开源项目',
        'academic_conferences': '学术会议',
        'database_docs': '数据库文档',
        'performance_guides': '性能指南',
        'best_practices': '最佳实践',
        'security_bulletins': '安全公告',
        'CTF_challenges': 'CTF挑战',
        'security_conferences': '安全会议',
        'research_reports': '研究报告',
        'testing_frameworks': '测试框架',
        'test_patterns': '测试模式',
        'quality_standards': '质量标准',
        'tools_training': '工具培训',
        'product_books': '产品书籍',
        'user_interviews': '用户访谈',
        'industry_trends': '行业趋势',
        'writing_guides': '写作指南',
        'style_guides': '风格指南',
        'documentation_tools': '文档工具',
        'examples': '示例',
        'anime_kansai': '关西腔动漫',
        'drama_kansai': '关西腔电视剧',
        'podcasts_kansai': '关西腔播客',
        'native_speakers': '母语者交流',
        'news_japanese': '日语新闻',
        'business_videos': '商务日语视频',
        'academic_content': '学术内容',
        'npr_japan': '日本NPR',
        'hollywood_movies': '好莱坞电影',
        'tv_shows_us': '美国电视剧',
        'podcasts_us': '美国播客',
        'youtube_us': '美国YouTube',
        'bbc_news': 'BBC新闻',
        'uk_tv_shows': '英国电视剧',
        'audiobooks_uk': '英国有声书',
        'royal_content': '皇室内容'
    }

    COMMUNICATION_STYLES = {
        'direct': '直接坦率',
        'data_driven': '数据驱动',
        'strategic': '战略层面',
        'action_oriented': '行动导向',
        'technical': '技术细节',
        'precise': '精确严谨',
        'urgent': '紧急重视',
        'constructive': '建设性',
        'persuasive': '有说服力',
        'clear': '清晰易懂',
        'lively': '生动活泼',
        'polite': '礼貌得体',
        'engaging': '引人入胜',
        'articulate': '口齿伶俐'
    }

    MOTIVATION_FACTORS = {
        'challenge': '挑战',
        'discovery': '发现',
        'innovation': '创新',
        'efficiency': '效率',
        'breakthrough': '突破',
        'reliability': '可靠性',
        'protection': '保护',
        'quality': '质量',
        'impact': '影响',
        'clarity': '清晰',
        'cultural_immersion': '文化沉浸',
        'professional_excellence': '专业卓越',
        'cultural_connection': '文化连接',
        'linguistic_refinement': '语言精进'
    }

    def __init__(self, role_type):
        self.role_type = role_type
        self.profile = self.ROLES.get(role_type, {})
        self.personality_traits = self.profile.get('personality', [])
        self.work_style = self.profile.get('work_style', 'methodical')
        self.domain_expertise = self.profile.get('domain_expertise', [])
        self.learning_preferences = self.profile.get('learning_preferences', [])
        self.communication_style = self.profile.get('communication_style', 'direct')
        self.motivation_factor = self.profile.get('motivation_factor', 'challenge')

    def get_personality_description(self):
        descriptions = []
        for trait in self.personality_traits:
            info = self.PERSONALITY_TRAITS.get(trait, {})
            descriptions.append(info.get('description', trait))
        return descriptions

    def get_strengths(self):
        strengths = []
        for trait in self.personality_traits:
            info = self.PERSONALITY_TRAITS.get(trait, {})
            strengths.append(info.get('strength', trait))
        return list(set(strengths))

    def get_weaknesses(self):
        weaknesses = []
        for trait in self.personality_traits:
            info = self.PERSONALITY_TRAITS.get(trait, {})
            weaknesses.append(info.get('weakness', trait))
        return list(set(weaknesses))

    def to_dict(self):
        return {
            'role_type': self.role_type,
            'role_name': self.profile.get('name', self.role_type),
            'personality_traits': self.personality_traits,
            'personality_descriptions': self.get_personality_description(),
            'work_style': self.work_style,
            'work_style_description': self.WORK_STYLES.get(self.work_style, self.work_style),
            'domain_expertise': self.domain_expertise,
            'learning_preferences': self.learning_preferences,
            'communication_style': self.communication_style,
            'communication_style_description': self.COMMUNICATION_STYLES.get(self.communication_style,
            self.communication_style),
            'motivation_factor': self.motivation_factor,
            'motivation_factor_description': self.MOTIVATION_FACTORS.get(self.motivation_factor,
            self.motivation_factor),
            'strengths': self.get_strengths(),
            'weaknesses': self.get_weaknesses()
        }

class IndependentThinkingEngine:
    THINKING_STAGES = ['analysis', 'planning', 'execution', 'reflection']

    def __init__(self):
        self.learning_plans = {}
        self.thinking_history = defaultdict(list)
        self.skill_analysis_cache = {}
        self._lock = threading.Lock()
        self._create_tables()

    def _create_tables(self):
        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()

            cursor.execute(''' CREATE TABLE IF NOT EXISTS learning_plans ( id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT NOT NULL, plan_name TEXT, status TEXT DEFAULT 'active', objectives TEXT, skills_to_learn TEXT, resources TEXT, timeline TEXT, progress REAL DEFAULT 0.0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, completed_at TEXT ) ''')

            cursor.execute(''' CREATE TABLE IF NOT EXISTS thinking_history ( id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT NOT NULL, stage TEXT, analysis_content TEXT, plan_content TEXT, execution_content TEXT, reflection_content TEXT, insights TEXT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP ) ''')

            cursor.execute(''' CREATE TABLE IF NOT EXISTS skill_gaps ( id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT NOT NULL, skill_name TEXT, current_level TEXT, target_level TEXT, gap_score REAL, priority TEXT DEFAULT 'medium', action_plan TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, resolved INTEGER DEFAULT 0 ) ''')

            cursor.execute(''' CREATE TABLE IF NOT EXISTS self_reflection ( id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT NOT NULL, reflection_type TEXT, content TEXT, insights TEXT, action_items TEXT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP ) ''')

            conn.commit()
            conn.close()
            logger.info("[IndependentThinkingEngine] 数据库表创建完成")
        except Exception as e:
            logger.info(f"[IndependentThinkingEngine] 创建表失败: {e}")

    def analyze_skills(self, employee_id, employee_name, current_skills):
        with self._lock:
            analysis = {
                'employee_id': employee_id,
                'employee_name': employee_name,
                'timestamp': datetime.now().isoformat(),
                'current_skills': {},
                'skill_gaps': [],
                'strengths': [],
                'weaknesses': [],
                'recommendations': []
            }

            for skill_name, skill_data in current_skills.items():
                analysis['current_skills'][skill_name] = {
                    'level': skill_data.get('level', 'beginner'),
                    'score': skill_data.get('score', 0),
                    'improvement_rate': skill_data.get('improvement_rate', 0)
                }

                score = skill_data.get('score', 0)
                if score >= 80:
                    analysis['strengths'].append(skill_name)
                elif score < 50:
                    analysis['weaknesses'].append(skill_name)
                    analysis['skill_gaps'].append({
                        'skill_name': skill_name,
                        'current_level': skill_data.get('level', 'beginner'),
                        'target_level': 'advanced',
                        'gap_score': 100 - score,
                        'priority': 'high' if score < 30 else 'medium',
                        'action_plan': f"加强{skill_name}的学习，建议进行专项训练"
                    })

            avg_score = sum(s.get('score', 0) for s in current_skills.values()) / max(1, len(current_skills))
            analysis['average_score'] = avg_score

            if avg_score < 60:
                analysis['recommendations'].append({
                    'type': 'foundation',
                    'content': '建议先巩固基础知识，打好基础后再进行进阶学习',
                    'priority': 'high'
                })
            elif avg_score >= 80:
                analysis['recommendations'].append({
                    'type': 'advanced',
                    'content': '当前技能水平优秀，建议挑战更高难度的任务，探索新技术',
                    'priority': 'medium'
                })
            else:
                analysis['recommendations'].append({
                    'type': 'improvement',
                    'content': '技能水平中等，建议针对薄弱环节进行专项提升',
                    'priority': 'medium'
                })

            try:
                conn = sqlite3.connect('professional_role.db')
                cursor = conn.cursor()

                for gap in analysis['skill_gaps']:
                    cursor.execute(''' INSERT OR IGNORE INTO skill_gaps (employee_id, skill_name, current_level, target_level, gap_score, priority, action_plan) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (employee_id, gap['skill_name'], gap['current_level'], gap['target_level'],
                          gap['gap_score'], gap['priority'], gap['action_plan']))

                conn.commit()
                conn.close()
            except Exception as e:
                logger.info(f"[IndependentThinkingEngine] 保存技能分析失败: {e}")

            self.skill_analysis_cache[employee_id] = analysis
            return analysis

    def generate_learning_plan(self, employee_id, employee_name, role_profile, skill_analysis):
        with self._lock:
            plan = {
                'employee_id': employee_id,
                'employee_name': employee_name,
                'plan_name': f"{employee_name}的{role_profile.profile.get('name', '')}职业发展计划",
                'status': 'active',
                'objectives': [],
                'skills_to_learn': [],
                'resources': [],
                'timeline': {},
                'progress': 0.0,
                'created_at': datetime.now().isoformat()
            }

            objectives = []
            objectives.append(f"成为{role_profile.profile.get('name', '')}领域的高级专家")
            objectives.append(f"掌握{role_profile.domain_expertise[:3]}等核心技能")
            objectives.append(f"提升整体技能评分至80分以上")
            plan['objectives'] = objectives

            skill_gaps = skill_analysis.get('skill_gaps', [])
            for gap in skill_gaps[:5]:
                plan['skills_to_learn'].append({
                    'skill_name': gap['skill_name'],
                    'current_level': gap['current_level'],
                    'target_level': gap['target_level'],
                    'priority': gap['priority'],
                    'estimated_time_weeks': 2 if gap['priority'] == 'high' else 4
                })

            for pref in role_profile.learning_preferences[:5]:
                plan['resources'].append({
                    'type': pref,
                    'description': role_profile.LEARNING_PREFERENCES.get(pref, pref),
                    'priority': 'high' if pref in ['online_courses', 'tutorials', 'hands_on'] else 'medium'
                })

            timeline = {}
            week_count = 1
            for skill in plan['skills_to_learn']:
                weeks = skill['estimated_time_weeks']
                start_week = week_count
                end_week = week_count + weeks - 1
                timeline[f'第{start_week}-{end_week}周'] = {
                    'focus_skill': skill['skill_name'],
                    'goal': f"将{skill['skill_name']}从{skill['current_level']}提升到{skill['target_level']}",
                    'activities': [
                        f"学习{skill['skill_name']}基础知识",
                        f"完成{skill['skill_name']}实践项目",
                        f"进行{skill['skill_name']}技能评估"
                    ]
                }
                week_count = end_week + 1
            plan['timeline'] = timeline

            try:
                conn = sqlite3.connect('professional_role.db')
                cursor = conn.cursor()

                cursor.execute(''' INSERT INTO learning_plans (employee_id, plan_name, status, objectives, skills_to_learn, resources, timeline) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (employee_id, plan['plan_name'], plan['status'],
                      json.dumps(plan['objectives']), json.dumps(plan['skills_to_learn']),
                      json.dumps(plan['resources']), json.dumps(plan['timeline'])))

                conn.commit()
                conn.close()
            except Exception as e:
                logger.info(f"[IndependentThinkingEngine] 保存学习计划失败: {e}")

            self.learning_plans[employee_id] = plan
            return plan

    def execute_independent_thinking(self, employee_id, employee_name, role_profile, current_skills):
        thinking_record = {
            'employee_id': employee_id,
            'employee_name': employee_name,
            'stage': 'completed',
            'analysis_content': '',
            'plan_content': '',
            'execution_content': '',
            'reflection_content': '',
            'insights': [],
            'timestamp': datetime.now().isoformat()
        }

        analysis = self.analyze_skills(employee_id, employee_name, current_skills)
        thinking_record['analysis_content'] = json.dumps(analysis)

        learning_plan = self.generate_learning_plan(employee_id, employee_name, role_profile, analysis)
        thinking_record['plan_content'] = json.dumps(learning_plan)

        thinking_record['execution_content'] = json.dumps({
            'message': f"{employee_name}已开始执行学习计划",
            'plan_id': learning_plan.get('plan_name', ''),
            'skills_to_learn': [s['skill_name'] for s in learning_plan.get('skills_to_learn', [])],
            'estimated_duration': f"{len(learning_plan.get('timeline', {}))}周"
        })

        reflections = []
        if analysis.get('average_score', 0) < 60:
            reflections.append("当前技能水平偏低，需要加大学习投入")
        if len(analysis.get('skill_gaps', [])) > 3:
            reflections.append("存在多个技能缺口，建议优先解决高优先级的")
        if analysis.get('strengths'):
            reflections.append(f"优势技能: {', '.join(analysis.get('strengths')[:3])}")
        thinking_record['reflection_content'] = '\n'.join(reflections)

        thinking_record['insights'] = [
            f"{employee_name}作为{role_profile.profile.get('name', '')}，当前平均技能评分为{analysis.get('average_score', 0):.1f}",
            f"已识别{len(analysis.get('skill_gaps', []))}个技能缺口",
            f"制定了{len(learning_plan.get('timeline', {}))}周的学习计划",
            f"性格特点: {', '.join(role_profile.personality_traits[:3])}",
            f"学习偏好: {', '.join(role_profile.learning_preferences[:3])}"
        ]

        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()

            cursor.execute(''' INSERT INTO thinking_history (employee_id, stage, analysis_content, plan_content, execution_content, reflection_content, insights) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (employee_id, thinking_record['stage'], thinking_record['analysis_content'],
                  thinking_record['plan_content'], thinking_record['execution_content'],
                  thinking_record['reflection_content'], json.dumps(thinking_record['insights'])))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[IndependentThinkingEngine] 保存思考记录失败: {e}")

        self.thinking_history[employee_id].append(thinking_record)
        return thinking_record

    def get_thinking_history(self, employee_id):
        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM thinking_history WHERE employee_id = ? ORDER BY timestamp DESC', (employee_id,
            ))
            rows = cursor.fetchall()

            history = []
            for row in rows:
                history.append({
                    'id': row[0],
                    'stage': row[2],
                    'timestamp': row[7],
                    'insights': json.loads(row[6]) if row[6] else []
                })

            conn.close()
            return history
        except Exception as e:
            logger.info(f"[IndependentThinkingEngine] 获取思考历史失败: {e}")
            return self.thinking_history.get(employee_id, [])

    def get_learning_plan(self, employee_id):
        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()
            cursor.execute(
            'SELECT * FROM learning_plans WHERE employee_id = ? AND status = "active" ORDER BY created_at DESC LIMIT 1',
            (employee_id,))
            row = cursor.fetchone()

            if row:
                plan = {
                    'id': row[0],
                    'employee_id': row[1],
                    'plan_name': row[2],
                    'status': row[3],
                    'objectives': json.loads(row[4]) if row[4] else [],
                    'skills_to_learn': json.loads(row[5]) if row[5] else [],
                    'resources': json.loads(row[6]) if row[6] else [],
                    'timeline': json.loads(row[7]) if row[7] else {},
                    'progress': row[8],
                    'created_at': row[9],
                    'updated_at': row[10],
                    'completed_at': row[11]
                }
                conn.close()
                return plan

            conn.close()
        except Exception as e:
            logger.info(f"[IndependentThinkingEngine] 获取学习计划失败: {e}")

        return self.learning_plans.get(employee_id, {})

    def update_plan_progress(self, employee_id, progress, skill_name=None):
        with self._lock:
            try:
                conn = sqlite3.connect('professional_role.db')
                cursor = conn.cursor()

                cursor.execute('UPDATE learning_plans SET progress = ?, updated_at = ? WHERE employee_id = ? AND status = "active"',
                              (progress, datetime.now().isoformat(), employee_id))

                if skill_name:
                    cursor.execute(''' INSERT INTO self_reflection (employee_id, reflection_type, content, insights) VALUES (?, ?, ?, ?) ''', (employee_id, 'progress_update',
                          f"技能'{skill_name}'学习进度更新",
                          json.dumps([f"当前整体进度: {progress}%"])))

                conn.commit()
                conn.close()
                return True
            except Exception as e:
                logger.info(f"[IndependentThinkingEngine] 更新学习计划进度失败: {e}")
                return False

class InternetSelfLearning:
    LEARNING_SOURCES = {
        'documentation': {'name': '官方文档', 'url_patterns': ['docs.', '.io', '/docs/']},
        'github': {'name': 'GitHub', 'url_patterns': ['github.com']},
        'stackoverflow': {'name': 'Stack Overflow', 'url_patterns': ['stackoverflow.com']},
        'medium': {'name': 'Medium', 'url_patterns': ['medium.com']},
        'devto': {'name': 'Dev.to', 'url_patterns': ['dev.to']},
        'arxiv': {'name': 'arXiv', 'url_patterns': ['arxiv.org']},
        'youtube': {'name': 'YouTube', 'url_patterns': ['youtube.com', 'youtu.be']},
        'courses': {'name': '在线课程', 'url_patterns': ['coursera.org', 'udemy.com', 'edx.org']}
    }

    def __init__(self):
        self.learning_history = defaultdict(list)
        self.knowledge_base = defaultdict(dict)
        self._lock = threading.Lock()
        self._create_tables()

    def _create_tables(self):
        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()

            cursor.execute(''' CREATE TABLE IF NOT EXISTS web_learning_history ( id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT NOT NULL, topic TEXT, source_type TEXT, source_url TEXT, content_summary TEXT, knowledge_acquired TEXT, skill_impact TEXT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP ) ''')

            cursor.execute(''' CREATE TABLE IF NOT EXISTS knowledge_base ( id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT NOT NULL, knowledge_domain TEXT, knowledge_topic TEXT, content TEXT, source TEXT, confidence REAL DEFAULT 0.8, added_at TEXT DEFAULT CURRENT_TIMESTAMP, accessed_count INTEGER DEFAULT 0 ) ''')

            cursor.execute(''' CREATE TABLE IF NOT EXISTS learning_resources ( id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT NOT NULL, resource_type TEXT, title TEXT, url TEXT, topic TEXT, difficulty TEXT DEFAULT 'medium', recommended INTEGER DEFAULT 1, completed INTEGER DEFAULT 0, rating REAL DEFAULT 0.0, added_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')

            conn.commit()
            conn.close()
            logger.info("[InternetSelfLearning] 数据库表创建完成")
        except Exception as e:
            logger.info(f"[InternetSelfLearning] 创建表失败: {e}")

    def _simulate_web_search(self, topic, employee_id):
        search_results = []

        mock_results = {
            'programming': [
                {'title': 'Python高级编程技巧', 'source': 'medium', 'url': 'https://medium.com/python-advanced',
                 'summary': '掌握Python高级特性如装饰器、生成器、上下文管理器等',
                 'skills': ['python', 'advanced', 'code_quality']},
                {'title': '系统设计入门', 'source': 'github', 'url': 'https://github.com/donnemartin/system-design-primer',
                 'summary': '学习大规模系统设计的核心概念和模式',
                 'skills': ['system_design', 'architecture', 'scalability']},
                {'title': '算法与数据结构', 'source': 'stackoverflow', 'url': 'https://stackoverflow.com/tags/algorithm/info',
                 'summary': '深入理解常用算法和数据结构',
                 'skills': ['algorithms', 'data_structures', 'problem_solving']}
            ],
            'machine_learning': [
                {'title': '深度学习入门', 'source': 'arxiv', 'url': 'https://arxiv.org/abs/1806.01261',
                 'summary': '深度学习基础概念和神经网络架构',
                 'skills': ['deep_learning', 'neural_networks', 'ML_fundamentals']},
                {'title': '机器学习实战', 'source': 'github', 'url': 'https://github.com/ageron/handson-ml2',
                 'summary': '通过实战项目学习机器学习算法',
                 'skills': ['ML_practice', 'scikit-learn', 'tensorflow']},
                {'title': 'NLP入门指南', 'source': 'medium', 'url': 'https://medium.com/nlp-guide',
                 'summary': '自然语言处理基础和Transformer架构',
                 'skills': ['NLP', 'transformers', 'text_processing']}
            ],
            'security': [
                {'title': 'Web安全入门', 'source': 'devto', 'url': 'https://dev.to/web-security-guide',
                 'summary': '常见Web安全漏洞和防护措施',
                 'skills': ['web_security', 'OWASP', 'vulnerabilities']},
                {'title': '渗透测试实战', 'source': 'github', 'url': 'https://github.com/cyberdefenders/Penetration-Testing',
                 'summary': '渗透测试方法论和工具使用',
                 'skills': ['penetration_testing', 'security_tools', 'ethical_hacking']}
            ],
            'database': [
                {'title': 'SQL性能优化', 'source': 'stackoverflow',
                'url': 'https://stackoverflow.com/tags/sql-performance/info',
                 'summary': '数据库查询优化技巧和最佳实践',
                 'skills': ['SQL', 'performance', 'database_tuning']},
                {'title': '分布式数据库原理', 'source': 'medium', 'url': 'https://medium.com/distributed-db',
                 'summary': '分布式数据库设计和一致性保证',
                 'skills': ['distributed_systems', 'database', 'consistency']}
            ],
            'devops': [
                {'title': 'Docker实战', 'source': 'github', 'url': 'https://github.com/docker/labs',
                 'summary': '容器化部署和Docker最佳实践',
                 'skills': ['docker', 'containers', 'deployment']},
                {'title': 'Kubernetes入门', 'source': 'devto', 'url': 'https://dev.to/k8s-guide',
                 'summary': 'Kubernetes核心概念和集群管理',
                 'skills': ['kubernetes', 'orchestration', 'cloud']}
            ],
            'ai': [
                {'title': '大语言模型原理', 'source': 'arxiv', 'url': 'https://arxiv.org/abs/2301.03728',
                 'summary': 'LLM架构和训练方法',
                 'skills': ['LLM', 'transformers', 'AI_research']},
                {'title': 'LangChain实战', 'source': 'github', 'url': 'https://github.com/langchain-ai/langchain',
                 'summary': '使用LangChain构建AI应用',
                 'skills': ['langchain', 'AI_development', 'prompt_engineering']}
            ],
            'kansai_dialect': [
                {'title': '关西腔入门指南', 'source': 'japanese-learning', 'url': 'https://kansai-ben.example.com',
                 'summary': '关西腔特点：句尾使用「な」「ねん」「やん」，语调较高，表达更直接',
                 'skills': ['kansai_dialect', 'osaka_slang', 'regional_accent']},
                {'title': '大阪方言常用表达', 'source': 'osaka-guide', 'url': 'https://osaka-ben.example.com',
                 'summary': '大阪方言特色词汇：「めっちゃ」(非常)、「ちゃう」(不是)、「ほんま」(真的)、「なんでやねん」(为什么)',
                 'skills': ['osaka_slang', 'casual_japanese', 'kansai_pronunciation']},
                {'title': '关西腔与标准语对比', 'source': 'language-study', 'url': 'https://dialect-compare.example.com',
                 'summary': '关西腔和标准语的差异：关西腔省略助词、使用独特终助词、发音有差异',
                 'skills': ['dialect_comparison', 'kansai_speech', 'japanese_variation']},
                {'title': '京都方言特点', 'source': 'kyoto-guide', 'url': 'https://kyoto-ben.example.com',
                 'summary': '京都方言比大阪方言更优雅，保留更多古语，敬语使用更细腻',
                 'skills': ['kyoto_speech', 'classical_japanese', 'polite_kansai']}
            ],
            'kanto_dialect': [
                {'title': '标准日语发音指南', 'source': 'japanese-learning', 'url': 'https://standard-japanese.example.com',
                 'summary': '东京方言即标准语，发音清晰，语调平稳，是日本广播的标准发音',
                 'skills': ['standard_japanese', 'tokyo_dialect', 'broadcast_japanese']},
                {'title': '日本敬语体系详解', 'source': 'keigo-guide', 'url': 'https://keigo.example.com',
                 'summary': '尊敬语、自谦语、郑重语的区别与用法，商务日语必备',
                 'skills': ['keigo', 'business_japanese', 'formal_speech']},
                {'title': '东京方言特色表达', 'source': 'tokyo-guide', 'url': 'https://tokyo-ben.example.com',
                 'summary': '东京方言常用表达：「ちょっと」(稍微)、「やっぱり」(果然)、「まさか」(没想到)',
                 'skills': ['tokyo_slang', 'standard_japanese', 'everyday_japanese']},
                {'title': '商务日语会话技巧', 'source': 'business-japanese', 'url': 'https://business-jp.example.com',
                 'summary': '职场日语表达、会议用语、邮件书写规范',
                 'skills': ['business_japanese', 'formal_japanese', 'professional_speech']}
            ],
            'american_english': [
                {'title': '美式英语发音指南', 'source': 'english-learning', 'url': 'https://american-pronunciation.example.com',
                 'summary': '美式英语特点：卷舌音(r)、短元音发音、语调起伏较大',
                 'skills': ['american_pronunciation', 'rhotic_accent', 'us_phonetics']},
                {'title': '美式英语常用俚语', 'source': 'us-slang', 'url': 'https://us-slang.example.com',
                 'summary': '美国常用俚语：「cool」(酷)、「awesome」(太棒了)、「like」(嗯)、「gonna/wanna」(将要/想要)',
                 'skills': ['slang_us', 'idioms_us', 'casual_english']},
                {'title': '好莱坞电影英语', 'source': 'movie-english', 'url': 'https://hollywood-english.example.com',
                 'summary': '通过电影学习美式英语：发音、语速、文化背景',
                 'skills': ['media_us', 'listening_comprehension', 'cultural_context']},
                {'title': '美式英语词汇差异', 'source': 'vocab-guide', 'url': 'https://us-uk-vocab.example.com',
                 'summary': '美式vs英式词汇：color/colour, vacation/holiday, subway/underground',
                 'skills': ['vocabulary_us', 'american_english', 'us_terminology']}
            ],
            'british_english': [
                {'title': '英式英语发音指南', 'source': 'english-learning', 'url': 'https://british-pronunciation.example.com',
                 'summary': '英式英语特点：非卷舌音、长元音发音更饱满、语调平稳优雅',
                 'skills': ['british_pronunciation', 'non_rhotic', 'received_pronunciation']},
                {'title': '英式英语常用俚语', 'source': 'uk-slang', 'url': 'https://uk-slang.example.com',
                 'summary': '英国常用俚语：「cheers」(谢谢/干杯)、「bloke」(家伙)、「chuffed」(高兴)、「mate」(朋友)',
                 'skills': ['slang_uk', 'idioms_uk', 'british_expressions']},
                {'title': 'BBC新闻英语', 'source': 'bbc-learning', 'url': 'https://bbc-news-english.example.com',
                 'summary': 'BBC标准发音、正式表达、国际新闻用语',
                 'skills': ['media_uk', 'formal_english', 'news_english']},
                {'title': '英式英语文化背景', 'source': 'uk-culture', 'url': 'https://uk-culture.example.com',
                 'summary': '英国文化习俗、皇室用语、礼仪规范、下午茶文化',
                 'skills': ['culture_uk', 'british_customs', 'etiquette']}
            ],
            'japanese_listening': [
                {'title': '日语听力训练方法', 'source': 'japanese-learning', 'url': 'https://jp-listening.example.com',
                 'summary': '精听和泛听技巧、影子跟读法、听写训练',
                 'skills': ['listening_comprehension', 'dictation', 'audio_training']},
                {'title': '日语语音语调分析', 'source': 'jp-phonetics', 'url': 'https://jp-phonetics.example.com',
                 'summary': '日语声调(アクセント)规则、音变现象、连浊和连声',
                 'skills': ['japanese_phonetics', 'intonation', 'sound_change']},
                {'title': '日语广播新闻听力', 'source': 'jp-news', 'url': 'https://jp-news-listening.example.com',
                 'summary': 'NHK新闻听力技巧、速记方法、关键词提取',
                 'skills': ['news_listening', 'broadcast_japanese', 'information_extraction']}
            ],
            'english_listening': [
                {'title': '英语听力训练方法', 'source': 'english-learning', 'url': 'https://en-listening.example.com',
                 'summary': '精听训练、泛听训练、听写技巧、跟读模仿',
                 'skills': ['english_listening', 'dictation', 'shadowing']},
                {'title': '英语连读技巧', 'source': 'en-phonetics', 'url': 'https://en-phonetics.example.com',
                 'summary': '连读、弱读、省音规则，听懂快速英语口语的关键',
                 'skills': ['connected_speech', 'phonetics', 'pronunciation']},
                {'title': '英语广播和播客', 'source': 'en-media', 'url': 'https://en-podcasts.example.com',
                 'summary': 'BBC、NPR、TED等优质听力资源推荐和学习方法',
                 'skills': ['media_listening', 'podcast_learning', 'news_english']}
            ]
        }

        for category, results in mock_results.items():
            if category.lower() in topic.lower() or topic.lower() in category.lower():
                search_results.extend(results)

        if not search_results:
            search_results = [
                {'title': f'{topic}学习指南', 'source': 'documentation',
                 'url': f'https://docs.example.com/{topic}',
                 'summary': f'{topic}的全面学习资源和教程',
                 'skills': [topic.lower().replace(' ', '_')]}
            ]

        return search_results[:5]

    def search_knowledge(self, topic, employee_id):
        with self._lock:
            results = self._simulate_web_search(topic, employee_id)
            self.learning_history[employee_id].append({
                'action': 'search',
                'topic': topic,
                'results_count': len(results),
                'timestamp': datetime.now().isoformat()
            })

            try:
                conn = sqlite3.connect('professional_role.db')
                cursor = conn.cursor()

                for result in results:
                    cursor.execute(''' INSERT INTO learning_resources (employee_id, resource_type, title, url, topic, difficulty, recommended) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (employee_id, result.get('source', 'unknown'), result.get('title', ''),
                          result.get('url', ''), topic, 'medium', 1))

                conn.commit()
                conn.close()
            except Exception as e:
                logger.info(f"[InternetSelfLearning] 保存搜索结果失败: {e}")

            return results

    def learn_from_web(self, employee_id, topic, resource_url=None):
        search_results = self.search_knowledge(topic, employee_id)

        learning_record = {
            'employee_id': employee_id,
            'topic': topic,
            'sources': [],
            'knowledge_acquired': [],
            'skill_impact': [],
            'timestamp': datetime.now().isoformat()
        }

        for result in search_results:
            acquired_knowledge = self._extract_knowledge(result, employee_id)
            learning_record['sources'].append({
                'title': result.get('title'),
                'url': result.get('url'),
                'source': result.get('source')
            })
            learning_record['knowledge_acquired'].extend(acquired_knowledge.get('knowledge', []))
            learning_record['skill_impact'].extend(acquired_knowledge.get('skills', []))

        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()

            cursor.execute(''' INSERT INTO web_learning_history (employee_id, topic, source_type, source_url, content_summary, knowledge_acquired, skill_impact) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (employee_id, topic, 'web_search',
                  ','.join([r.get('url', '') for r in search_results]),
                  json.dumps(learning_record['sources']),
                  json.dumps(learning_record['knowledge_acquired']),
                  json.dumps(learning_record['skill_impact'])))

            conn.commit()
            conn.close()
        except Exception as e:
                logger.info(f"[InternetSelfLearning] 保存学习记录失败: {e}")

        self.learning_history[employee_id].append(learning_record)
        return learning_record

    def _extract_knowledge(self, result, employee_id):
        knowledge_items = []
        skills_impacted = []

        summary = result.get('summary', '')
        skills = result.get('skills', [])

        knowledge_items.append({
            'type': 'concept',
            'content': summary[:100],
            'source': result.get('title', '')
        })

        for skill in skills:
            skills_impacted.append(skill)
            knowledge_items.append({
                'type': 'skill',
                'content': f"提升{skill}技能",
                'source': result.get('title', '')
            })

        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()

            for knowledge in knowledge_items:
                cursor.execute(''' INSERT INTO knowledge_base (employee_id, knowledge_domain, knowledge_topic, content, source, confidence) VALUES (?, ?, ?, ?, ?, ?) ''', (employee_id, result.get('source', 'general'),
                      result.get('title', ''), knowledge['content'],
                      result.get('url', ''), 0.8))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[InternetSelfLearning] 保存知识失败: {e}")

        return {
            'knowledge': knowledge_items,
            'skills': skills_impacted
        }

    def get_knowledge_base(self, employee_id, domain=None):
        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()

            if domain:
                cursor.execute('SELECT * FROM knowledge_base WHERE employee_id = ? AND knowledge_domain = ?',
                (employee_id, domain))
            else:
                cursor.execute('SELECT * FROM knowledge_base WHERE employee_id = ?', (employee_id,))

            rows = cursor.fetchall()
            knowledge = []
            for row in rows:
                knowledge.append({
                    'id': row[0],
                    'domain': row[2],
                    'topic': row[3],
                    'content': row[4],
                    'source': row[5],
                    'confidence': row[6],
                    'added_at': row[7],
                    'accessed_count': row[8]
                })

            conn.close()
            return knowledge
        except Exception as e:
            logger.info(f"[InternetSelfLearning] 获取知识库失败: {e}")
            return []

    def get_learning_history(self, employee_id):
        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM web_learning_history WHERE employee_id = ? ORDER BY timestamp DESC',
            (employee_id,))
            rows = cursor.fetchall()

            history = []
            for row in rows:
                history.append({
                    'id': row[0],
                    'topic': row[2],
                    'source_type': row[3],
                    'timestamp': row[7],
                    'knowledge_acquired': json.loads(row[5]) if row[5] else []
                })

            conn.close()
            return history
        except Exception as e:
            logger.info(f"[InternetSelfLearning] 获取学习历史失败: {e}")
            return []

class AIProfessionalRoleSystem:
    def __init__(self):
        self.role_assignments = {}
        self.professional_profiles = {}
        self.thinking_engine = IndependentThinkingEngine()
        self.internet_learning = InternetSelfLearning()
        self._lock = threading.Lock()
        self._create_tables()

    def _create_tables(self):
        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()

            cursor.execute(''' CREATE TABLE IF NOT EXISTS role_assignments ( id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT NOT NULL UNIQUE, employee_name TEXT, role_type TEXT, assigned_at TEXT DEFAULT CURRENT_TIMESTAMP, last_updated TEXT DEFAULT CURRENT_TIMESTAMP ) ''')

            cursor.execute(''' CREATE TABLE IF NOT EXISTS professional_summary ( id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT NOT NULL, employee_name TEXT, role_type TEXT, role_name TEXT, total_thinking_sessions INTEGER DEFAULT 0, total_learning_hours REAL DEFAULT 0.0, knowledge_base_size INTEGER DEFAULT 0, avg_skill_score REAL DEFAULT 0.0, current_plan_progress REAL DEFAULT 0.0, last_activity TEXT DEFAULT CURRENT_TIMESTAMP ) ''')

            conn.commit()
            conn.close()
            logger.info("[AIProfessionalRoleSystem] 数据库表创建完成")
        except Exception as e:
            logger.info(f"[AIProfessionalRoleSystem] 创建表失败: {e}")

    def assign_role(self, employee_id, employee_name, role_type):
        with self._lock:
            if role_type not in ProfessionalRoleProfile.ROLES:
                return {
                    'success': False,
                    'message': f"未知的职业角色类型: {role_type}",
                    'available_roles': list(ProfessionalRoleProfile.ROLES.keys())
                }

            profile = ProfessionalRoleProfile(role_type)
            self.role_assignments[employee_id] = {
                'role_type': role_type,
                'employee_name': employee_name,
                'profile': profile.to_dict(),
                'assigned_at': datetime.now().isoformat()
            }

            self.professional_profiles[employee_id] = profile

            try:
                conn = sqlite3.connect('professional_role.db')
                cursor = conn.cursor()

                cursor.execute(''' INSERT OR REPLACE INTO role_assignments (employee_id, employee_name, role_type, assigned_at, last_updated) VALUES (?, ?, ?, ?, ?) ''', (employee_id, employee_name, role_type,
                      self.role_assignments[employee_id]['assigned_at'],
                      datetime.now().isoformat()))

                cursor.execute(''' INSERT OR REPLACE INTO professional_summary (employee_id, employee_name, role_type, role_name) VALUES (?, ?, ?, ?) ''', (employee_id, employee_name, role_type, profile.profile.get('name', role_type)))

                conn.commit()
                conn.close()
            except Exception as e:
                logger.info(f"[AIProfessionalRoleSystem] 保存角色分配失败: {e}")

            return {
                'success': True,
                'message': f"成功为{employee_name}分配职业角色: {profile.profile.get('name', role_type)}",
                'role_type': role_type,
                'role_name': profile.profile.get('name', role_type),
                'profile': profile.to_dict()
            }

    def get_role(self, employee_id):
        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM role_assignments WHERE employee_id = ?', (employee_id,))
            row = cursor.fetchone()

            if row:
                profile = ProfessionalRoleProfile(row[2])
                conn.close()
                return {
                    'success': True,
                    'employee_id': row[1],
                    'employee_name': row[2],
                    'role_type': row[3],
                    'role_name': profile.profile.get('name', row[3]),
                    'profile': profile.to_dict(),
                    'assigned_at': row[4]
                }

            conn.close()
        except Exception as e:
            logger.info(f"[AIProfessionalRoleSystem] 获取角色失败: {e}")

        if employee_id in self.role_assignments:
            return {
                'success': True,
                **self.role_assignments[employee_id]
            }

        return {
            'success': False,
            'message': f"未找到员工 {employee_id} 的职业角色分配"
        }

    def list_all_roles(self):
        roles_info = {}
        for role_type, role_data in ProfessionalRoleProfile.ROLES.items():
            profile = ProfessionalRoleProfile(role_type)
            roles_info[role_type] = profile.to_dict()
        return roles_info

    def trigger_independent_thinking(self, employee_id, employee_name, current_skills=None):
        role_data = self.get_role(employee_id)
        if not role_data['success']:
            return {
                'success': False,
                'message': f"员工 {employee_id} 未分配职业角色，请先分配角色"
            }

        role_profile = self.professional_profiles.get(employee_id)
        if not role_profile:
            role_profile = ProfessionalRoleProfile(role_data['role_type'])
            self.professional_profiles[employee_id] = role_profile

        if current_skills is None:
            current_skills = {}

        thinking_result = self.thinking_engine.execute_independent_thinking(
            employee_id, employee_name, role_profile, current_skills
        )

        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()

            cursor.execute(''' UPDATE professional_summary SET total_thinking_sessions = total_thinking_sessions + 1, last_activity = ? WHERE employee_id = ? ''', (datetime.now().isoformat(), employee_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AIProfessionalRoleSystem] 更新思考次数失败: {e}")

        return {
            'success': True,
            'message': f"{employee_name}完成独立思考分析",
            'thinking_result': thinking_result,
            'role_profile': role_profile.to_dict()
        }

    def trigger_web_learning(self, employee_id, employee_name, topic):
        role_data = self.get_role(employee_id)
        if not role_data['success']:
            return {
                'success': False,
                'message': f"员工 {employee_id} 未分配职业角色，请先分配角色"
            }

        learning_result = self.internet_learning.learn_from_web(employee_id, topic)

        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()

            cursor.execute(''' UPDATE professional_summary SET total_learning_hours = total_learning_hours + 1, knowledge_base_size = knowledge_base_size + ?, last_activity = ? WHERE employee_id = ? ''', (len(learning_result.get('knowledge_acquired', [])),
                  datetime.now().isoformat(), employee_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AIProfessionalRoleSystem] 更新学习统计失败: {e}")

        return {
                'success': True,
                'message': f"{employee_name}完成网络学习: {topic}",
                'learning_result': learning_result
            }

    def get_learning_plan(self, employee_id):
        plan = self.thinking_engine.get_learning_plan(employee_id)
        if plan:
            return {
                'success': True,
                'plan': plan
            }
        return {
            'success': False,
            'message': f"员工 {employee_id} 暂无学习计划，请先触发独立思考"
        }

    def get_knowledge_base(self, employee_id):
        knowledge = self.internet_learning.get_knowledge_base(employee_id)
        return {
            'success': True,
            'knowledge_base': knowledge,
            'count': len(knowledge)
        }

    def get_professional_summary(self):
        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM professional_summary ORDER BY last_activity DESC')
            rows = cursor.fetchall()

            summaries = []
            for row in rows:
                summaries.append({
                    'employee_id': row[1],
                    'employee_name': row[2],
                    'role_type': row[3],
                    'role_name': row[4],
                    'total_thinking_sessions': row[5],
                    'total_learning_hours': row[6],
                    'knowledge_base_size': row[7],
                    'avg_skill_score': row[8],
                    'current_plan_progress': row[9],
                    'last_activity': row[10]
                })

            conn.close()
            return summaries
        except Exception as e:
            logger.info(f"[AIProfessionalRoleSystem] 获取职业发展摘要失败: {e}")
            return []

    def get_all_employees_overview(self):
        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()

            cursor.execute(''' SELECT ra.employee_id, ra.employee_name, ra.role_type, pr.name as role_name, ps.total_thinking_sessions, ps.total_learning_hours, ps.knowledge_base_size, ps.avg_skill_score, ps.current_plan_progress, ps.last_activity FROM role_assignments ra LEFT JOIN professional_summary ps ON ra.employee_id = ps.employee_id LEFT JOIN (SELECT role_type, name FROM (VALUES ('software_engineer', '软件工程师'), ('data_scientist', '数据科学家'), ('system_architect', '系统架构师'), ('devops_engineer', 'DevOps工程师'), ('ai_researcher', 'AI研究员'), ('database_administrator', '数据库管理员'), ('security_specialist', '安全专家'), ('quality_assurance', '质量保证工程师'), ('product_manager', '产品经理'), ('technical_writer', '技术文档工程师') )) pr ON ra.role_type = pr.role_type ORDER BY ps.last_activity DESC ''')

            rows = cursor.fetchall()
            overview = []
            for row in rows:
                overview.append({
                    'employee_id': row[0],
                    'employee_name': row[1],
                    'role_type': row[2],
                    'role_name': row[3] or row[2],
                    'total_thinking_sessions': row[4] or 0,
                    'total_learning_hours': row[5] or 0.0,
                    'knowledge_base_size': row[6] or 0,
                    'avg_skill_score': row[7] or 0.0,
                    'current_plan_progress': row[8] or 0.0,
                    'last_activity': row[9]
                })

            conn.close()
            return overview
        except Exception as e:
            logger.info(f"[AIProfessionalRoleSystem] 获取员工概览失败: {e}")
            return []

ai_professional_role_system = AIProfessionalRoleSystem()