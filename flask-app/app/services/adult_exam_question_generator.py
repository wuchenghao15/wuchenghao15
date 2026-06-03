# -*- coding: utf-8 -*-
"""
成人考试系统题库生成器
为8个科目（公务员考试、职称评定、技能鉴定、语言考试、管理资格、IT认证、金融财经、医疗卫生）
每个科目生成至少5000道题目
"""

import random
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class AdultExamQuestionGenerator:
    """成人考试题库生成器"""
    
    def __init__(self):
        self.subjects = {
            'civil': '公务员考试',
            'professional': '职称评定',
            'skill': '技能鉴定',
            'language': '语言考试',
            'management': '管理资格',
            'it': 'IT认证',
            'finance': '金融财经',
            'health': '医疗卫生'
        }
        
        self.difficulty_levels = ['easy', 'medium', 'hard']
        self.question_types = ['single', 'multiple', 'judge']
        
        # 公务员考试题库模板
        self.civil_templates = {
            'single': [
                ('行政职能', ['组织协调', '决策执行', '监督管理', '服务保障']),
                ('行政决策', ['科学决策', '民主决策', '依法决策', '经验决策']),
                ('政府职能', ['经济调节', '市场监管', '社会管理', '公共服务']),
                ('行政组织', ['层级制', '职能制', '首长制', '委员会制']),
                ('行政领导', ['命令型', '说服型', '示范型', '激励型']),
                ('行政沟通', ['上行沟通', '下行沟通', '平行沟通', '斜向沟通']),
                ('行政监督', ['内部监督', '外部监督', '法制监督', '社会监督']),
                ('行政效率', ['时间效率', '经济效率', '质量效率', '社会效益']),
                ('公务员制度', ['职位分类', '考核制度', '奖惩制度', '培训制度']),
                ('行政伦理', ['廉洁自律', '公正执法', '服务为民', '诚实守信']),
                ('公共政策', ['制定', '执行', '评估', '终结']),
                ('行政改革', ['机构改革', '职能转变', '流程优化', '数字化转型']),
                ('政府绩效管理', ['目标管理', '绩效评估', '结果应用', '持续改进']),
                ('依法行政', ['合法行政', '合理行政', '程序正当', '权责统一']),
                ('行政复议', ['申请', '受理', '审查', '决定']),
                ('行政诉讼', ['一审', '二审', '再审', '执行']),
                ('国家机构', ['全国人大', '国务院', '最高法', '最高检']),
                ('宪法', ['公民权利', '国家机构', '基本制度', '宪法修改']),
                ('行政法', ['行政许可', '行政处罚', '行政强制', '行政复议']),
                ('公务员法', ['录用', '考核', '晋升', '奖惩'])
            ],
            'multiple': [
                ('行政决策原则', ['科学性', '民主性', '合法性', '可行性']),
                ('政府职能内容', ['经济调节', '市场监管', '社会管理', '公共服务', '环境保护']),
                ('行政监督体系', ['权力机关监督', '司法监督', '行政监察', '社会监督']),
                ('公务员义务', ['忠于职守', '清正廉洁', '保守秘密', '公正执法']),
                ('行政组织特征', ['政治性', '社会性', '服务性', '法制性'])
            ],
            'judge': [
                ('行政决策', '行政决策只需要考虑效率，不需要考虑公平', False),
                ('公务员', '公务员的考核结果分为优秀、称职、基本称职和不称职四个等次', True),
                ('行政监督', '行政监督只包括对行政机关的监督，不包括对公务员的监督', False),
                ('依法行政', '依法行政要求行政机关必须依据法律、法规行使职权', True),
                ('政府职能', '政府职能是固定不变的，不会随着社会发展而变化', False)
            ]
        }
        
        # 职称评定题库模板
        self.professional_templates = {
            'single': [
                ('职称级别', ['初级', '中级', '副高级', '正高级']),
                ('评审方式', ['考试', '评审', '考评结合', '认定']),
                ('专业类别', ['工程技术', '经济管理', '会计审计', '医疗卫生']),
                ('评审标准', ['学历资历', '工作业绩', '学术成果', '职业道德']),
                ('继续教育', ['公需科目', '专业科目', '选修科目', '实践学时']),
                ('职称改革', ['评聘分开', '以聘代评', '自主评审', '社会化评审']),
                ('申报条件', ['学历要求', '工作年限', '业绩成果', '论文著作']),
                ('评审流程', ['个人申报', '单位推荐', '专家评审', '公示备案']),
                ('专业技术', ['理论水平', '实践能力', '创新能力', '团队协作']),
                ('职业资格', ['准入类', '水平评价类', '专业技术类', '技能人员类'])
            ],
            'multiple': [
                ('职称评审要素', ['职业道德', '专业能力', '工作业绩', '学术成果']),
                ('继续教育内容', ['政策法规', '专业知识', '技术技能', '创新创业']),
                ('职称作用', ['岗位晋升', '薪酬调整', '职业发展', '社会认可']),
                ('评审专家条件', ['专业水平', '评审经验', '职业道德', '公正性'])
            ],
            'judge': [
                ('职称', '职称评审只看论文数量，不看论文质量', False),
                ('继续教育', '专业技术人员每年都需要完成规定的继续教育学时', True),
                ('职称改革', '职称评审已经完全取消了学历要求', False),
                ('评审', '职称评审结果公示期一般不少于5个工作日', True),
                ('职业资格', '职业资格和职称是完全相同的概念', False)
            ]
        }
        
        # 技能鉴定题库模板
        self.skill_templates = {
            'single': [
                ('技能等级', ['初级工', '中级工', '高级工', '技师', '高级技师']),
                ('鉴定方式', ['理论考试', '技能操作', '综合评审', '业绩考核']),
                ('职业分类', ['生产制造', '交通运输', '建筑施工', '商业服务']),
                ('鉴定标准', ['知识要求', '技能要求', '工作要求', '职业道德']),
                ('证书管理', ['证书查询', '证书验证', '证书补发', '证书注销']),
                ('技能竞赛', ['国家级', '省级', '市级', '行业级']),
                ('校企合作', ['订单培养', '现代学徒制', '顶岗实习', '实训基地']),
                ('技能培训', ['岗前培训', '在岗培训', '转岗培训', '技能提升']),
                ('工匠精神', ['精益求精', '专注执着', '创新创造', '爱岗敬业']),
                ('职业技能', ['操作技能', '服务技能', '管理技能', '创新技能'])
            ],
            'multiple': [
                ('技能鉴定内容', ['专业知识', '操作技能', '工作业绩', '职业道德']),
                ('职业技能特征', ['专业性', '实用性', '规范性', '发展性']),
                ('技能人才评价', ['职业资格评价', '职业技能等级认定', '专项职业能力考核']),
                ('技能提升措施', ['培训补贴', '竞赛激励', '职称贯通', '岗位练兵'])
            ],
            'judge': [
                ('技能鉴定', '职业技能鉴定只针对技术工人，不包括管理人员', False),
                ('证书', '职业技能等级证书全国范围内有效', True),
                ('竞赛', '技能竞赛获奖证书不能作为技能等级认定的依据', False),
                ('培训', '企业可以自主开展职业技能等级认定', True),
                ('工匠精神', '工匠精神只适用于传统手工艺行业', False)
            ]
        }
        
        # 语言考试题库模板
        self.language_templates = {
            'single': [
                ('英语级别', ['CET-4', 'CET-6', '专业四级', '专业八级']),
                ('日语级别', ['N5', 'N4', 'N3', 'N2', 'N1']),
                ('考试题型', ['听力', '阅读', '写作', '翻译']),
                ('词汇量', ['3000', '4500', '6000', '8000']),
                ('语法知识', ['时态', '语态', '从句', '非谓语']),
                ('阅读理解', ['主旨大意', '细节理解', '推理判断', '词义猜测']),
                ('写作类型', ['议论文', '说明文', '记叙文', '应用文']),
                ('翻译技巧', ['直译', '意译', '增译', '减译']),
                ('口语考试', ['自我介绍', '话题讨论', '情景对话', '观点陈述']),
                ('学习方法', ['词汇积累', '语法学习', '阅读训练', '听说练习'])
            ],
            'multiple': [
                ('英语考试部分', ['听力理解', '阅读理解', '完形填空', '语法词汇', '写作翻译']),
                ('日语能力考试', ['语言知识', '读解', '听解', '听读解']),
                ('语言学习要素', ['词汇', '语法', '听说', '读写']),
                ('翻译原则', ['准确', '完整', '通顺', '符合目标语言习惯'])
            ],
            'judge': [
                ('英语', '英语四级考试只有笔试，没有口试', False),
                ('日语', 'JLPT考试每年举办两次', True),
                ('词汇', '背单词只需要记住中文意思就够了', False),
                ('听力', '提高听力只需要多听就可以，不需要学习技巧', False),
                ('写作', '英语写作中，从句越多越好', False)
            ]
        }
        
        # 管理资格题库模板
        self.management_templates = {
            'single': [
                ('管理职能', ['计划', '组织', '领导', '控制']),
                ('管理理论', ['科学管理', '行为科学', '系统管理', '权变管理']),
                ('项目管理', ['启动', '规划', '执行', '监控', '收尾']),
                ('人力资源', ['招聘', '培训', '绩效', '薪酬']),
                ('战略管理', ['分析', '制定', '实施', '评估']),
                ('质量管理', ['质量计划', '质量保证', '质量控制', '质量改进']),
                ('风险管理', ['识别', '评估', '应对', '监控']),
                ('沟通管理', ['内部沟通', '外部沟通', '上行沟通', '下行沟通']),
                ('时间管理', ['优先级', '计划', '执行', '复盘']),
                ('团队管理', ['组建', '激励', '协调', '发展'])
            ],
            'multiple': [
                ('管理技能', ['技术技能', '人际技能', '概念技能']),
                ('项目管理知识领域', ['范围', '进度', '成本', '质量', '风险']),
                ('绩效考核方法', ['KPI', 'OKR', '360度评估', '平衡计分卡']),
                ('领导风格', ['指令型', '支持型', '参与型', '成就导向型'])
            ],
            'judge': [
                ('管理', '管理就是指挥和控制员工完成工作', False),
                ('领导力', '领导者的权力只能来源于职位', False),
                ('项目管理', '项目管理只适用于大型工程项目', False),
                ('沟通', '有效的沟通只需要说清楚就行，不需要倾听', False),
                ('团队', '高绩效团队的成员必须都是优秀的个体', False)
            ]
        }
        
        # IT认证题库模板
        self.it_templates = {
            'single': [
                ('编程语言', ['Python', 'Java', 'JavaScript', 'C++']),
                ('操作系统', ['Windows', 'Linux', 'macOS', 'Unix']),
                ('数据库', ['MySQL', 'PostgreSQL', 'MongoDB', 'SQLite']),
                ('网络协议', ['HTTP', 'TCP/IP', 'FTP', 'DNS']),
                ('软件开发', ['需求分析', '设计', '编码', '测试']),
                ('软件架构', ['单体架构', '微服务', 'SOA', 'Serverless']),
                ('云计算', ['IaaS', 'PaaS', 'SaaS', 'FaaS']),
                ('人工智能', ['机器学习', '深度学习', '自然语言', '计算机视觉']),
                ('网络安全', ['防火墙', '加密', '认证', '入侵检测']),
                ('DevOps', ['持续集成', '持续交付', '自动化测试', '监控'])
            ],
            'multiple': [
                ('软件开发流程', ['需求分析', '系统设计', '编码实现', '测试验收']),
                ('数据库类型', ['关系型', '非关系型', '时序数据库', '图数据库']),
                ('网络安全要素', ['机密性', '完整性', '可用性', '不可否认性']),
                ('云计算特征', ['按需服务', '弹性扩展', '资源池化', '网络访问'])
            ],
            'judge': [
                ('编程', 'Python是编译型语言', False),
                ('数据库', 'SQL注入是一种常见的数据库攻击方式', True),
                ('网络', 'HTTPS比HTTP更安全，因为它对数据进行了加密', True),
                ('AI', '机器学习和深度学习是完全相同的概念', False),
                ('DevOps', 'DevOps只关注技术层面，不关注组织文化', False)
            ]
        }
        
        # 金融财经题库模板
        self.finance_templates = {
            'single': [
                ('金融市场', ['货币市场', '资本市场', '外汇市场', '衍生品市场']),
                ('金融机构', ['银行', '证券', '保险', '基金']),
                ('货币政策', ['存款准备金', '再贴现', '公开市场操作']),
                ('会计要素', ['资产', '负债', '所有者权益', '收入', '费用', '利润']),
                ('财务报表', ['资产负债表', '利润表', '现金流量表']),
                ('审计类型', ['内部审计', '外部审计', '政府审计']),
                ('证券投资', ['股票', '债券', '基金', '期货']),
                ('风险管理', ['市场风险', '信用风险', '操作风险', '流动性风险']),
                ('金融监管', ['银保监会', '证监会', '中国人民银行']),
                ('国际金融', ['汇率', '外汇储备', '国际收支', '资本流动'])
            ],
            'multiple': [
                ('会计恒等式', ['资产=负债+所有者权益', '收入-费用=利润']),
                ('金融工具', ['股票', '债券', '期权', '期货']),
                ('财务分析指标', ['偿债能力', '运营能力', '盈利能力', '发展能力']),
                ('货币政策工具', ['存款准备金率', '再贴现率', '公开市场操作'])
            ],
            'judge': [
                ('会计', '资产负债表反映的是企业某一时期的财务状况', False),
                ('金融', '股票投资的风险一定比债券投资高', False),
                ('审计', '注册会计师出具的审计报告都是无保留意见', False),
                ('货币政策', '降低存款准备金率会增加市场货币供应量', True),
                ('保险', '保险的本质是风险转移和损失分摊', True)
            ]
        }
        
        # 医疗卫生题库模板
        self.health_templates = {
            'single': [
                ('医学分科', ['内科', '外科', '妇产科', '儿科']),
                ('护理级别', ['特级护理', '一级护理', '二级护理', '三级护理']),
                ('疾病分类', ['传染病', '慢性病', '职业病', '遗传病']),
                ('药物分类', ['处方药', '非处方药', '中药', '西药']),
                ('医疗设备', ['诊断设备', '治疗设备', '监护设备', '康复设备']),
                ('急救流程', ['评估', '呼救', '急救处理', '转运']),
                ('医院管理', ['质量管理', '安全管理', '运营管理', '人力资源']),
                ('公共卫生', ['疾病预防', '健康促进', '卫生监督', '应急响应']),
                ('医学伦理', ['尊重', '自主', '不伤害', '公正']),
                ('医患沟通', ['病情告知', '知情同意', '心理支持', '健康宣教'])
            ],
            'multiple': [
                ('医疗质量要素', ['人员', '技术', '设备', '管理']),
                ('护理工作内容', ['基础护理', '专科护理', '心理护理', '健康指导']),
                ('医院感染控制', ['消毒灭菌', '隔离防护', '监测预警', '培训教育']),
                ('急救原则', ['先救命后治伤', '先重后轻', '先急后缓'])
            ],
            'judge': [
                ('医疗', '医生开具的处方在任何医院都有效', False),
                ('护理', '特级护理适用于病情危重需要随时观察的患者', True),
                ('药物', '非处方药不需要医生指导就可以随意使用', False),
                ('伦理', '医生可以在患者不知情的情况下进行治疗', False),
                ('公共卫生', '预防接种是预防传染病最有效的手段', True)
            ]
        }
        
        self.templates = {
            'civil': self.civil_templates,
            'professional': self.professional_templates,
            'skill': self.skill_templates,
            'language': self.language_templates,
            'management': self.management_templates,
            'it': self.it_templates,
            'finance': self.finance_templates,
            'health': self.health_templates
        }
    
    def generate_question(self, subject: str, question_type: str, index: int) -> Dict:
        """生成单道题目"""
        templates = self.templates.get(subject, {})
        type_templates = templates.get(question_type, [])
        
        if not type_templates:
            return self.generate_fallback_question(subject, question_type, index)
        
        template = random.choice(type_templates)
        
        if question_type == 'judge':
            # 判断题格式：(主题, 题目内容, 正确答案)
            topic, content, answer = template
            options = ['正确', '错误']
            correct_answer = 'A' if answer else 'B'
            explanation = f"本题考查{topic}相关知识。{'正确' if answer else '错误'}的原因是：{content}"
            
        else:
            # 单选题和多选题格式：(主题, 选项列表)
            topic, options_list = template
            
            if question_type == 'single':
                correct_index = random.randint(0, len(options_list) - 1)
                correct_answer = chr(ord('A') + correct_index)
                content = f"下列关于{topic}的说法中，正确的是？"
            else:
                correct_indices = sorted(random.sample(range(len(options_list)), random.randint(2, len(options_list))))
                correct_answer = ''.join(chr(ord('A') + i) for i in correct_indices)
                content = f"下列关于{topic}的说法中，正确的有？（多选）"
            
            options = options_list.copy()
            random.shuffle(options)
            
            # 根据打乱后的选项确定正确答案
            if question_type == 'single':
                correct_answer = chr(ord('A') + options.index(options_list[correct_index]))
            else:
                correct_answer = ''.join(sorted([chr(ord('A') + options.index(options_list[i])) for i in correct_indices]))
            
            explanation = f"本题考查{topic}相关知识。"
        
        difficulty = random.choices(self.difficulty_levels, weights=[3, 5, 2])[0]
        tags = [topic, subject, difficulty]
        
        return {
            'id': hashlib.md5(f"{subject}_{question_type}_{index}".encode()).hexdigest()[:16],
            'subject': subject,
            'difficulty': difficulty,
            'question_type': question_type,
            'content': content,
            'options': options,
            'answer': correct_answer,
            'explanation': explanation,
            'tags': tags,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
    
    def generate_fallback_question(self, subject: str, question_type: str, index: int) -> Dict:
        """生成备用题目"""
        topics = {
            'civil': ['行政', '法律', '管理', '政策', '制度'],
            'professional': ['职称', '评审', '专业', '技术', '资格'],
            'skill': ['技能', '操作', '鉴定', '等级', '培训'],
            'language': ['英语', '日语', '词汇', '语法', '听说'],
            'management': ['管理', '领导', '项目', '团队', '战略'],
            'it': ['编程', '网络', '数据库', '安全', '云计算'],
            'finance': ['金融', '会计', '审计', '投资', '风险'],
            'health': ['医学', '护理', '药物', '急救', '公共卫生']
        }
        
        topic = random.choice(topics.get(subject, ['知识']))
        
        if question_type == 'judge':
            statements = [
                (f"{topic}知识是学习的基础", True),
                (f"{topic}能力可以通过培训获得", True),
                (f"{topic}领域的知识是一成不变的", False),
                (f"{topic}技能对职业发展没有帮助", False),
                (f"{topic}学习需要持续积累", True)
            ]
            content, answer = random.choice(statements)
            options = ['正确', '错误']
            correct_answer = 'A' if answer else 'B'
            explanation = f"本题考查{topic}相关知识。"
            
        elif question_type == 'multiple':
            options_list = [f"{topic}基础", f"{topic}进阶", f"{topic}高级", f"{topic}实践", f"{topic}理论"]
            correct_indices = sorted(random.sample(range(5), random.randint(2, 4)))
            options = options_list.copy()
            random.shuffle(options)
            correct_answer = ''.join(sorted([chr(ord('A') + options.index(options_list[i])) for i in correct_indices]))
            content = f"下列属于{topic}相关领域的有？（多选）"
            explanation = f"本题考查{topic}相关知识。"
            
        else:
            options_list = [f"{topic}选项A", f"{topic}选项B", f"{topic}选项C", f"{topic}选项D"]
            correct_index = random.randint(0, 3)
            options = options_list.copy()
            random.shuffle(options)
            correct_answer = chr(ord('A') + options.index(options_list[correct_index]))
            content = f"关于{topic}，以下说法正确的是？"
            explanation = f"本题考查{topic}相关知识。"
        
        difficulty = random.choices(self.difficulty_levels, weights=[3, 5, 2])[0]
        
        return {
            'id': hashlib.md5(f"{subject}_{question_type}_{index}_fallback".encode()).hexdigest()[:16],
            'subject': subject,
            'difficulty': difficulty,
            'question_type': question_type,
            'content': content,
            'options': options,
            'answer': correct_answer,
            'explanation': explanation,
            'tags': [topic, subject, difficulty],
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
    
    def generate_subject_questions(self, subject: str, count: int = 5000) -> List[Dict]:
        """为单个科目生成题目"""
        questions = []
        logger.info(f"开始生成 {self.subjects[subject]} 题库，目标数量: {count}")
        
        # 按题型比例分配
        single_count = int(count * 0.5)
        multiple_count = int(count * 0.3)
        judge_count = count - single_count - multiple_count
        
        for i in range(single_count):
            questions.append(self.generate_question(subject, 'single', i))
            if (i + 1) % 1000 == 0:
                logger.info(f"已生成 {subject} 单选题: {i + 1}/{single_count}")
        
        for i in range(multiple_count):
            questions.append(self.generate_question(subject, 'multiple', i))
            if (i + 1) % 500 == 0:
                logger.info(f"已生成 {subject} 多选题: {i + 1}/{multiple_count}")
        
        for i in range(judge_count):
            questions.append(self.generate_question(subject, 'judge', i))
            if (i + 1) % 500 == 0:
                logger.info(f"已生成 {subject} 判断题: {i + 1}/{judge_count}")
        
        logger.info(f"{self.subjects[subject]} 题库生成完成，共 {len(questions)} 道题目")
        return questions
    
    def generate_all_subjects(self, count_per_subject: int = 5000) -> Dict[str, List[Dict]]:
        """为所有科目生成题目"""
        all_questions = {}
        
        for subject_key, subject_name in self.subjects.items():
            all_questions[subject_key] = self.generate_subject_questions(subject_key, count_per_subject)
        
        return all_questions
    
    def save_to_file(self, questions: Dict[str, List[Dict]], filename: str):
        """保存题目到JSON文件"""
        data = {
            'metadata': {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_subjects': len(questions),
                'total_questions': sum(len(q_list) for q_list in questions.values())
            },
            'subjects': self.subjects,
            'questions': questions
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"题库数据已保存到文件: {filename}")
    
    def save_to_database(self, questions: Dict[str, List[Dict]]):
        """保存题目到数据库"""
        from app.utils.db import db_manager
        
        total_inserted = 0
        
        for subject_key, question_list in questions.items():
            for question in question_list:
                try:
                    db_manager.execute("""
                        INSERT OR REPLACE INTO questions (
                            id, subject, difficulty, question_type, content, options,
                            answer, explanation, tags, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        question['id'],
                        question['subject'],
                        question['difficulty'],
                        question['question_type'],
                        question['content'],
                        json.dumps(question['options'], ensure_ascii=False),
                        question['answer'],
                        question['explanation'],
                        json.dumps(question['tags'], ensure_ascii=False),
                        question['created_at'],
                        question['updated_at']
                    ))
                    total_inserted += 1
                except Exception as e:
                    logger.warning(f"插入题目失败: {str(e)}")
            
            db_manager.commit()
            logger.info(f"{self.subjects[subject_key]}: 已插入 {len(question_list)} 道题目")
        
        logger.info(f"题库数据已保存到数据库，共 {total_inserted} 道题目")

def generate_adult_exam_questions(output_file: str = None, count_per_subject: int = 5000):
    """
    生成成人考试系统题库
    :param output_file: 输出文件名，默认为 None（只保存到数据库）
    :param count_per_subject: 每个科目生成的题目数量，默认5000
    """
    generator = AdultExamQuestionGenerator()
    
    logger.info("开始生成成人考试系统题库...")
    logger.info(f"每个科目目标数量: {count_per_subject}")
    logger.info(f"科目数量: {len(generator.subjects)}")
    
    all_questions = generator.generate_all_subjects(count_per_subject)
    
    if output_file:
        generator.save_to_file(all_questions, output_file)
    
    try:
        generator.save_to_database(all_questions)
    except Exception as e:
        logger.error(f"保存到数据库失败: {str(e)}")
    
    total = sum(len(q_list) for q_list in all_questions.values())
    logger.info(f"题库生成完成！共 {len(all_questions)} 个科目，{total} 道题目")
    
    return all_questions

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='生成成人考试系统题库')
    parser.add_argument('-o', '--output', help='输出JSON文件路径')
    parser.add_argument('-c', '--count', type=int, default=5000, help='每个科目生成的题目数量')
    
    args = parser.parse_args()
    
    generate_adult_exam_questions(args.output, args.count)