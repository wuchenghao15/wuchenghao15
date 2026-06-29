# -*- coding: utf-8 -*-
"""
K12智慧教育视图模块
负责K12教育相关的页面路由和API接口
包含权限控制和访问约束规则
"""
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from functools import wraps
import logging

logger = logging.getLogger(__name__)

k12_bp = Blueprint('k12', __name__)

ALLOWED_ROLES = ['student', 'student_vip', 'teacher']
STUDENT_ONLY_ROUTES = ['k12_exam', 'k12_report']
GRADE_REQUIRED_ROUTES = ['k12_subject', 'k12_exam', 'k12_report']


def require_login(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning("[K12] 未登录用户尝试访问")
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'error': '请先登录', 'code': 'NOT_LOGGED_IN'}), 401
            return redirect('/login?next=' + request.full_path)
        return f(*args, **kwargs)
    return decorated_function


def require_k12_role(f):
    """K12角色验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('role', '')
        if role not in ALLOWED_ROLES:
            logger.warning(f"[K12] 用户 {session.get('username')} ({role}) 权限不足，无法访问K12功能")
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'error': 'K12功能仅对学生和教师开放', 'code': 'ROLE_NOT_ALLOWED'}), 403
            return render_template('k12/403.html', message='K12功能仅对学生和教师开放'), 403
        return f(*args, **kwargs)
    return decorated_function


def require_grade(f):
    """年级设置验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_grade = session.get('grade', '')
        if not user_grade:
            logger.warning(f"[K12] 用户 {session.get('username')} 未设置年级")
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'error': '请先设置年级', 'code': 'GRADE_NOT_SET'}), 403
            return redirect('/set_grade?next=' + request.full_path)
        return f(*args, **kwargs)
    return decorated_function


def require_student_only(f):
    """仅学生访问装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('role', '')
        if role not in ['student', 'student_vip']:
            logger.warning(f"[K12] 用户 {session.get('username')} ({role}) 非学生角色，无法访问学生专属功能")
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'error': '此功能仅限学生使用', 'code': 'STUDENT_ONLY'}), 403
            return render_template('k12/403.html', message='此功能仅限学生使用'), 403
        return f(*args, **kwargs)
    return decorated_function


def check_k12_permission(route_name):
    """检查K12路由访问权限"""
    errors = []
    
    if 'user_id' not in session:
        errors.append({'code': 'NOT_LOGGED_IN', 'message': '请先登录'})
        return False, errors
    
    role = session.get('role', '')
    if role not in ALLOWED_ROLES:
        errors.append({'code': 'ROLE_NOT_ALLOWED', 'message': f'您的角色({role})无法访问K12功能'})
        return False, errors
    
    if route_name in GRADE_REQUIRED_ROUTES:
        if not session.get('grade'):
            errors.append({'code': 'GRADE_NOT_SET', 'message': '请先设置您的年级'})
            return False, errors
    
    if route_name in STUDENT_ONLY_ROUTES and role not in ['student', 'student_vip']:
        errors.append({'code': 'STUDENT_ONLY', 'message': '此功能仅限学生使用'})
        return False, errors
    
    return True, errors


def get_user_k12_info():
    """获取用户在K12系统中的基本信息"""
    user_id = session.get('user_id')
    role = session.get('role', '')
    
    try:
        from app.middlewares.system_constraints import get_user_education_system
        education = get_user_education_system(user_id)
    except ImportError:
        education = None
    
    return {
        'user_id': user_id,
        'username': session.get('username', ''),
        'role': role,
        'grade': session.get('grade', ''),
        'education_system': education,
        'is_logged_in': 'user_id' in session,
        'has_grade': bool(session.get('grade')),
        'can_access_k12': role in ALLOWED_ROLES,
        'is_student': role in ['student', 'student_vip'],
        'is_teacher': role == 'teacher',
        'is_k12_education': education == 'k12'
    }

SUBJECT_INFO = {
    'chinese': {'name': '语文', 'emoji': '📖', 'description': '阅读·写作·文言文·古诗词'},
    'math': {'name': '数学', 'emoji': '🔢', 'description': '代数·几何·函数·概率统计'},
    'english': {'name': '英语', 'emoji': '🔤', 'description': '听说读写·语法·词汇'},
    'physics': {'name': '物理', 'emoji': '⚡', 'description': '力学·电学·光学·热学'},
    'chemistry': {'name': '化学', 'emoji': '🧪', 'description': '元素·反应·有机·无机'},
    'biology': {'name': '生物', 'emoji': '🧬', 'description': '细胞·遗传·生态·生理'},
    'history': {'name': '历史', 'emoji': '🏛️', 'description': '中国史·世界史·年代记'},
    'geography': {'name': '地理', 'emoji': '🌍', 'description': '自然地理·人文地理·区域'},
    'politics': {'name': '道德与法治', 'emoji': '⚖️', 'description': '道法·国情·法律·道德'},
}

K12_GRADES = [
    '小学1年级', '小学2年级', '小学3年级', '小学4年级', '小学5年级', '小学6年级',
    '初中1年级', '初中2年级', '初中3年级',
    '高中1年级', '高中2年级', '高中3年级',
]

# ==================== 年级课程规划配置 ====================
GRADE_COURSE_PLANNING = {
    '小学1年级': {
        'subjects': ['chinese', 'math'],
        'focus': ['基础识字', '拼音学习', '数字认知', '加减法入门'],
        'daily_hours': 4,
        'weekly_goals': ['掌握20个生字', '完成基础加减法练习'],
        'difficulty_level': '基础入门'
    },
    '小学2年级': {
        'subjects': ['chinese', 'math'],
        'focus': ['阅读理解入门', '乘除法基础', '词语积累'],
        'daily_hours': 4,
        'weekly_goals': ['阅读短文10篇', '掌握乘法口诀'],
        'difficulty_level': '基础巩固'
    },
    '小学3年级': {
        'subjects': ['chinese', 'math', 'english'],
        'focus': ['写作入门', '分数基础', '英语字母'],
        'daily_hours': 5,
        'weekly_goals': ['完成日记写作', '掌握基础英语词汇50个'],
        'difficulty_level': '基础拓展'
    },
    '小学4年级': {
        'subjects': ['chinese', 'math', 'english'],
        'focus': ['作文技巧', '几何入门', '英语对话'],
        'daily_hours': 5,
        'weekly_goals': ['写作完整作文', '英语口语练习'],
        'difficulty_level': '进阶启蒙'
    },
    '小学5年级': {
        'subjects': ['chinese', 'math', 'english'],
        'focus': ['文言文入门', '代数基础', '英语阅读'],
        'daily_hours': 6,
        'weekly_goals': ['文言文翻译练习', '英语短文阅读'],
        'difficulty_level': '进阶提升'
    },
    '小学6年级': {
        'subjects': ['chinese', 'math', 'english'],
        'focus': ['小升初预备', '综合复习', '升学考点'],
        'daily_hours': 6,
        'weekly_goals': ['完成升学模拟测试', '系统复习核心知识'],
        'difficulty_level': '升学冲刺'
    },
    '初中1年级': {
        'subjects': ['chinese', 'math', 'english', 'history', 'geography', 'biology'],
        'focus': ['文言文深入', '代数方程', '英语语法', '历史入门', '地理基础', '生物基础'],
        'daily_hours': 7,
        'weekly_goals': ['文言文背诵', '代数解题', '英语作文'],
        'difficulty_level': '初中基础'
    },
    '初中2年级': {
        'subjects': ['chinese', 'math', 'english', 'physics', 'history', 'geography', 'biology'],
        'focus': ['现代文分析', '几何证明', '英语听力', '物理力学', '近代史'],
        'daily_hours': 7,
        'weekly_goals': ['物理实验', '几何证明题', '英语听力训练'],
        'difficulty_level': '初中进阶'
    },
    '初中3年级': {
        'subjects': ['chinese', 'math', 'english', 'physics', 'chemistry', 'history', 'politics'],
        'focus': ['中考冲刺', '综合复习', '化学入门', '中考模拟'],
        'daily_hours': 8,
        'weekly_goals': ['完成中考模拟试卷', '化学方程式记忆'],
        'difficulty_level': '中考冲刺'
    },
    '高中1年级': {
        'subjects': ['chinese', 'math', 'english', 'physics', 'chemistry', 'biology', 'history', 'geography', 'politics'],
        'focus': ['高中适应', '函数深入', '英语写作', '必修课程'],
        'daily_hours': 8,
        'weekly_goals': ['函数综合练习', '英语写作提高'],
        'difficulty_level': '高中基础'
    },
    '高中2年级': {
        'subjects': ['chinese', 'math', 'english', 'physics', 'chemistry', 'biology', 'history', 'geography', 'politics'],
        'focus': ['选修课程', '高考预备', '学科深化'],
        'daily_hours': 9,
        'weekly_goals': ['选修科目强化', '高考知识点梳理'],
        'difficulty_level': '高考预备'
    },
    '高中3年级': {
        'subjects': ['chinese', 'math', 'english', 'physics', 'chemistry', 'biology', 'history', 'geography', 'politics'],
        'focus': ['高考冲刺', '真题训练', '志愿准备'],
        'daily_hours': 10,
        'weekly_goals': ['完成高考真题', '知识点查漏补缺'],
        'difficulty_level': '高考冲刺'
    }
}

# ==================== 年级知识点配置 ====================
GRADE_KNOWLEDGE_POINTS = {
    '小学': {
        'chinese': {
            '识字写字': ['拼音', '汉字结构', '笔画笔顺', '字形辨析'],
            '阅读理解': ['短文阅读', '信息提取', '情感理解', '主旨概括'],
            '写作表达': ['日记写作', '看图写话', '简单记叙文', '段落组织']
        },
        'math': {
            '数与运算': ['整数加减', '乘除运算', '分数初步', '小数入门'],
            '图形几何': ['图形识别', '面积计算', '周长概念', '立体图形'],
            '应用题': ['一步计算', '两步计算', '生活应用', '逻辑推理']
        },
        'english': {
            '词汇': ['日常词汇', '动物词汇', '颜色词汇', '数字词汇'],
            '句型': ['问候语', '介绍句', '疑问句', '简单陈述'],
            '听说': ['字母发音', '简单对话', '听力训练', '口语表达']
        }
    },
    '初中': {
        'chinese': {
            '文言文': ['实词虚词', '文言翻译', '文意理解', '诗词鉴赏'],
            '现代文': ['记叙文分析', '说明文阅读', '议论文理解', '散文鉴赏'],
            '写作': ['记叙文写作', '议论文入门', '说明文写作', '应用文写作']
        },
        'math': {
            '代数': ['方程求解', '不等式', '函数概念', '二次函数'],
            '几何': ['三角形', '四边形', '圆的性质', '几何证明'],
            '统计': ['数据收集', '图表分析', '概率初步', '统计应用']
        },
        'english': {
            '语法': ['时态语态', '从句结构', '非谓语动词', '句型转换'],
            '阅读': ['文章理解', '信息提取', '推理判断', '词汇推断'],
            '写作': ['短文写作', '应用文', '议论文', '书信写作']
        },
        'physics': {
            '力学': ['力的概念', '运动规律', '牛顿定律', '能量守恒'],
            '电学': ['电路基础', '欧姆定律', '电功率', '电磁现象'],
            '光学': ['光的反射', '光的折射', '透镜成像', '光的色散']
        },
        'chemistry': {
            '基础概念': ['物质分类', '化学用语', '原子结构', '化学式'],
            '化学反应': ['反应类型', '化学方程式', '反应条件', '能量变化'],
            '实验': ['实验操作', '物质鉴别', '定量实验', '安全规范']
        },
        'biology': {
            '细胞': ['细胞结构', '细胞功能', '细胞分裂', '细胞代谢'],
            '遗传': ['遗传规律', '基因概念', '变异类型', '进化理论'],
            '生态': ['生态系统', '生物多样性', '环境保护', '人与自然']
        },
        'history': {
            '中国古代史': ['朝代演变', '政治制度', '经济发展', '文化成就'],
            '中国近代史': ['近代变革', '革命运动', '民族觉醒', '改革开放'],
            '世界史': ['古代文明', '近代革命', '世界大战', '当代发展']
        },
        'geography': {
            '自然地理': ['地形地貌', '气候类型', '水文特征', '自然资源'],
            '人文地理': ['人口分布', '城市规划', '经济发展', '区域差异'],
            '区域地理': ['中国地理', '世界地理', '区域特色', '区域发展']
        },
        'politics': {
            '道德修养': ['个人品德', '家庭美德', '社会公德', '法律意识'],
            '国情国策': ['国家制度', '法律法规', '政策理解', '公民权利'],
            '时事热点': ['时事分析', '热点解读', '政策解读', '价值判断']
        }
    },
    '高中': {
        'chinese': {
            '文学鉴赏': ['诗歌鉴赏', '小说分析', '戏剧理解', '散文鉴赏'],
            '语言运用': ['修辞手法', '语言表达', '逻辑思维', '语言创新'],
            '写作': ['复杂记叙文', '议论文深化', '文学创作', '应用文写作']
        },
        'math': {
            '函数': ['函数性质', '导数应用', '函数综合', '函数建模'],
            '几何': ['空间几何', '解析几何', '向量应用', '几何证明'],
            '概率统计': ['概率计算', '统计推断', '随机变量', '分布模型']
        },
        'english': {
            '语法': ['复杂语法', '句法分析', '语篇衔接', '语法综合'],
            '阅读': ['深度阅读', '批判思维', '文化理解', '跨文化交际'],
            '写作': ['议论文', '说明文', '应用文', '创意写作']
        },
        'physics': {
            '力学': ['运动分析', '动力学', '能量守恒', '动量定理'],
            '电磁学': ['电磁场', '电磁感应', '电路分析', '电磁波'],
            '热学光学': ['热力学', '光学原理', '近代物理', '物理实验']
        },
        'chemistry': {
            '物质结构': ['原子结构', '分子结构', '晶体结构', '化学键'],
            '化学反应': ['反应原理', '平衡移动', '速率控制', '能量转化'],
            '有机化学': ['有机结构', '有机反应', '有机合成', '有机实验']
        },
        'biology': {
            '分子遗传': ['DNA结构', '基因表达', '遗传工程', '分子进化'],
            '生命活动': ['生命调节', '免疫机制', '生态系统', '生物技术'],
            '实验探究': ['实验设计', '数据分析', '科学探究', '生物伦理']
        },
        'history': {
            '政治史': ['政治制度', '政治变革', '民主发展', '国际关系'],
            '经济史': ['经济发展', '经济制度', '经济全球化', '经济危机'],
            '文化史': ['思想演变', '科技发展', '文化交流', '文化遗产']
        },
        'geography': {
            '自然地理': ['地球系统', '环境演变', '自然灾害', '资源环境'],
            '人文地理': ['人口迁移', '城市发展', '产业布局', '区域协调'],
            '地理技术': ['GIS应用', '遥感技术', '地图分析', '地理建模']
        },
        'politics': {
            '经济学': ['市场经济', '宏观调控', '国际贸易', '经济制度'],
            '政治学': ['国家理论', '民主制度', '国际政治', '公民参与'],
            '哲学': ['唯物论', '辩证法', '认识论', '价值观']
        }
    }
}

# ==================== 9学科完整题库配置 ====================
SUBJECT_QUESTION_BANK = {
    'chinese': {
        'name': '语文',
        'question_types': ['选择题', '填空题', '简答题', '阅读理解', '作文'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'ch_ch1', 'name': '文言文阅读', 'question_count': 200, 'types': ['选择题', '翻译题', '理解题']},
            {'id': 'ch_ch2', 'name': '现代文阅读', 'question_count': 180, 'types': ['选择题', '简答题', '分析题']},
            {'id': 'ch_ch3', 'name': '诗歌鉴赏', 'question_count': 150, 'types': ['鉴赏题', '选择题', '分析题']},
            {'id': 'ch_ch4', 'name': '语言运用', 'question_count': 120, 'types': ['选择题', '改错题', '表达题']},
            {'id': 'ch_ch5', 'name': '写作训练', 'question_count': 50, 'types': ['命题作文', '材料作文', '应用文']}
        ],
        'sample_questions': [
            {'type': '选择题', 'difficulty': '基础', 'content': '"不愤不启,不悱不发"出自哪本典籍?', 'answer': '论语'},
            {'type': '翻译题', 'difficulty': '中等', 'content': '翻译"学而时习之,不亦说乎"', 'answer': '学习了知识后按时温习,不是很愉快吗?'},
            {'type': '阅读理解', 'difficulty': '中等', 'content': '分析《背影》中父亲的形象特点', 'answer': '朴实、慈爱、艰辛、坚韧'}
        ]
    },
    'math': {
        'name': '数学',
        'question_types': ['选择题', '填空题', '计算题', '证明题', '应用题'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'ma_ch1', 'name': '函数与导数', 'question_count': 300, 'types': ['计算题', '证明题', '应用题']},
            {'id': 'ma_ch2', 'name': '几何与向量', 'question_count': 280, 'types': ['计算题', '证明题', '画图题']},
            {'id': 'ma_ch3', 'name': '数列与不等式', 'question_count': 200, 'types': ['计算题', '证明题', '应用题']},
            {'id': 'ma_ch4', 'name': '概率与统计', 'question_count': 150, 'types': ['计算题', '应用题', '分析题']},
            {'id': 'ma_ch5', 'name': '综合应用', 'question_count': 120, 'types': ['综合题', '探究题', '建模题']}
        ],
        'sample_questions': [
            {'type': '计算题', 'difficulty': '基础', 'content': '求函数f(x)=x²-2x+1的最小值', 'answer': '0'},
            {'type': '证明题', 'difficulty': '中等', 'content': '证明:三角形内角和为180°', 'answer': '略'},
            {'type': '应用题', 'difficulty': '困难', 'content': '某商品降价20%后售价为80元,原价是多少?', 'answer': '100元'}
        ]
    },
    'english': {
        'name': '英语',
        'question_types': ['选择题', '填空题', '完形填空', '阅读理解', '写作'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'en_ch1', 'name': '语法专项', 'question_count': 250, 'types': ['选择题', '填空题', '改错题']},
            {'id': 'en_ch2', 'name': '词汇运用', 'question_count': 200, 'types': ['选择题', '填空题', '辨析题']},
            {'id': 'en_ch3', 'name': '阅读理解', 'question_count': 180, 'types': ['选择题', '简答题', '分析题']},
            {'id': 'en_ch4', 'name': '完形填空', 'question_count': 100, 'types': ['完形填空', '语境理解']},
            {'id': 'en_ch5', 'name': '写作训练', 'question_count': 80, 'types': ['应用文', '议论文', '记叙文']}
        ],
        'sample_questions': [
            {'type': '选择题', 'difficulty': '基础', 'content': '选择正确形式: He ___ to school every day.', 'answer': 'goes'},
            {'type': '阅读理解', 'difficulty': '中等', 'content': '阅读短文并回答主旨问题', 'answer': '根据文章内容回答'},
            {'type': '写作', 'difficulty': '中等', 'content': '写一篇100词左右的英语短文介绍你的学校', 'answer': '开放性答案'}
        ]
    },
    'physics': {
        'name': '物理',
        'question_types': ['选择题', '填空题', '计算题', '实验题', '证明题'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'ph_ch1', 'name': '力学基础', 'question_count': 200, 'types': ['计算题', '选择题', '证明题']},
            {'id': 'ph_ch2', 'name': '电磁学', 'question_count': 180, 'types': ['计算题', '实验题', '选择题']},
            {'id': 'ph_ch3', 'name': '光学热学', 'question_count': 150, 'types': ['计算题', '实验题', '选择题']},
            {'id': 'ph_ch4', 'name': '近代物理', 'question_count': 100, 'types': ['选择题', '简答题', '计算题']},
            {'id': 'ph_ch5', 'name': '物理实验', 'question_count': 80, 'types': ['实验设计', '数据分析', '误差分析']}
        ],
        'sample_questions': [
            {'type': '计算题', 'difficulty': '基础', 'content': '一个物体从10m高处自由落下,求落地速度', 'answer': '约14m/s'},
            {'type': '选择题', 'difficulty': '中等', 'content': '下列哪种现象属于光的折射?', 'answer': '水中筷子变弯'},
            {'type': '实验题', 'difficulty': '中等', 'content': '设计实验测量重力加速度', 'answer': '自由落体实验'}
        ]
    },
    'chemistry': {
        'name': '化学',
        'question_types': ['选择题', '填空题', '计算题', '实验题', '推断题'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'ch_h1', 'name': '基本概念', 'question_count': 180, 'types': ['选择题', '填空题', '判断题']},
            {'id': 'ch_h2', 'name': '化学反应', 'question_count': 200, 'types': ['计算题', '选择题', '推断题']},
            {'id': 'ch_h3', 'name': '有机化学', 'question_count': 150, 'types': ['选择题', '推断题', '计算题']},
            {'id': 'ch_h4', 'name': '化学实验', 'question_count': 100, 'types': ['实验设计', '操作判断', '数据分析']},
            {'id': 'ch_h5', 'name': '化学计算', 'question_count': 80, 'types': ['计算题', '应用题', '综合题']}
        ],
        'sample_questions': [
            {'type': '选择题', 'difficulty': '基础', 'content': '下列物质属于纯净物的是?', 'answer': '蒸馏水'},
            {'type': '计算题', 'difficulty': '中等', 'content': '计算2Na+2H₂O→2NaOH+H₂↑中氢气质量', 'answer': '根据钠的质量计算'},
            {'type': '实验题', 'difficulty': '中等', 'content': '如何鉴别碳酸钠和碳酸氢钠?', 'answer': '加热法或加酸法'}
        ]
    },
    'biology': {
        'name': '生物',
        'question_types': ['选择题', '填空题', '简答题', '实验题', '分析题'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'bi_ch1', 'name': '细胞生物学', 'question_count': 200, 'types': ['选择题', '填空题', '简答题']},
            {'id': 'bi_ch2', 'name': '遗传与进化', 'question_count': 180, 'types': ['计算题', '选择题', '分析题']},
            {'id': 'bi_ch3', 'name': '生命活动调节', 'question_count': 150, 'types': ['选择题', '简答题', '分析题']},
            {'id': 'bi_ch4', 'name': '生态系统', 'question_count': 120, 'types': ['选择题', '简答题', '分析题']},
            {'id': 'bi_ch5', 'name': '生物实验', 'question_count': 100, 'types': ['实验设计', '操作题', '分析题']}
        ],
        'sample_questions': [
            {'type': '选择题', 'difficulty': '基础', 'content': '细胞膜的主要成分是?', 'answer': '磷脂和蛋白质'},
            {'type': '计算题', 'difficulty': '中等', 'content': '计算DNA复制后的比例', 'answer': '根据碱基配对原则计算'},
            {'type': '实验题', 'difficulty': '中等', 'content': '设计实验观察植物细胞有丝分裂', 'answer': '洋葱根尖实验'}
        ]
    },
    'history': {
        'name': '历史',
        'question_types': ['选择题', '填空题', '简答题', '材料分析', '论述题'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'hi_ch1', 'name': '中国古代史', 'question_count': 200, 'types': ['选择题', '简答题', '材料分析']},
            {'id': 'hi_ch2', 'name': '中国近代史', 'question_count': 180, 'types': ['选择题', '简答题', '论述题']},
            {'id': 'hi_ch3', 'name': '中国现代史', 'question_count': 150, 'types': ['选择题', '简答题', '材料分析']},
            {'id': 'hi_ch4', 'name': '世界古代近代史', 'question_count': 130, 'types': ['选择题', '简答题', '材料分析']},
            {'id': 'hi_ch5', 'name': '世界现代史', 'question_count': 100, 'types': ['选择题', '论述题', '材料分析']}
        ],
        'sample_questions': [
            {'type': '选择题', 'difficulty': '基础', 'content': '秦朝统一六国的时间是?', 'answer': '公元前221年'},
            {'type': '简答题', 'difficulty': '中等', 'content': '简述辛亥革命的历史意义', 'answer': '推翻封建帝制,建立民主共和'},
            {'type': '论述题', 'difficulty': '困难', 'content': '论述改革开放对中国的影响', 'answer': '开放性论述'}
        ]
    },
    'geography': {
        'name': '地理',
        'question_types': ['选择题', '填空题', '简答题', '读图分析', '综合题'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'ge_ch1', 'name': '自然地理', 'question_count': 200, 'types': ['选择题', '简答题', '读图分析']},
            {'id': 'ge_ch2', 'name': '人文地理', 'question_count': 180, 'types': ['选择题', '简答题', '综合题']},
            {'id': 'ge_ch3', 'name': '区域地理', 'question_count': 150, 'types': ['选择题', '读图分析', '综合题']},
            {'id': 'ge_ch4', 'name': '中国地理', 'question_count': 130, 'types': ['选择题', '简答题', '读图分析']},
            {'id': 'ge_ch5', 'name': '世界地理', 'question_count': 100, 'types': ['选择题', '简答题', '综合题']}
        ],
        'sample_questions': [
            {'type': '选择题', 'difficulty': '基础', 'content': '地球自转一周的时间约为?', 'answer': '24小时'},
            {'type': '读图分析', 'difficulty': '中等', 'content': '分析某区域地形图特征', 'answer': '根据图示分析'},
            {'type': '综合题', 'difficulty': '困难', 'content': '分析某城市的区位因素', 'answer': '自然+人文因素综合分析'}
        ]
    },
    'politics': {
        'name': '道德与法治',
        'question_types': ['选择题', '填空题', '简答题', '材料分析', '论述题'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'po_ch1', 'name': '道德修养', 'question_count': 150, 'types': ['选择题', '简答题', '材料分析']},
            {'id': 'po_ch2', 'name': '法律常识', 'question_count': 180, 'types': ['选择题', '案例分析', '简答题']},
            {'id': 'po_ch3', 'name': '国情国策', 'question_count': 130, 'types': ['选择题', '简答题', '材料分析']},
            {'id': 'po_ch4', 'name': '经济常识', 'question_count': 120, 'types': ['选择题', '简答题', '计算题']},
            {'id': 'po_ch5', 'name': '哲学常识', 'question_count': 100, 'types': ['选择题', '简答题', '论述题']}
        ],
        'sample_questions': [
            {'type': '选择题', 'difficulty': '基础', 'content': '社会主义核心价值观个人层面的要求是?', 'answer': '爱国、敬业、诚信、友善'},
            {'type': '案例分析', 'difficulty': '中等', 'content': '分析某消费者维权案例', 'answer': '根据法律条款分析'},
            {'type': '论述题', 'difficulty': '困难', 'content': '论述公民的权利与义务关系', 'answer': '开放性论述'}
        ]
    }
}

CHAPTERS_DATA = [
    {'id': 'ch1', 'name': '第一章 绪论', 'knowledge_count': 8, 'progress': 100},
    {'id': 'ch2', 'name': '第二章 基础知识', 'knowledge_count': 12, 'progress': 75},
    {'id': 'ch3', 'name': '第三章 进阶内容', 'knowledge_count': 10, 'progress': 40},
    {'id': 'ch4', 'name': '第四章 综合应用', 'knowledge_count': 15, 'progress': 15},
    {'id': 'ch5', 'name': '第五章 拓展提升', 'knowledge_count': 10, 'progress': 0},
]

KNOWLEDGE_POINTS = [
    {
        'name': '核心概念与定义',
        'type': 'concept',
        'type_name': '概念',
        'difficulty': '基础',
        'description': '本章的核心概念是后续学习的基础，需要深入理解并熟练掌握。概念的理解程度直接影响后续知识的学习效果。',
        'formula': None,
        'example': None
    },
    {
        'name': '基本定理与公式',
        'type': 'formula',
        'type_name': '公式',
        'difficulty': '中等',
        'description': '掌握本章的核心定理和公式，理解其推导过程和适用条件。公式是解决问题的工具，要做到灵活运用。',
        'formula': 'a² + b² = c²',
        'example': {
            'question': '已知直角三角形的两条直角边分别为3和4，求斜边长度。',
            'answer': '斜边长度为5',
            'analysis': '根据勾股定理 a² + b² = c²，代入a=3, b=4，得 c² = 9 + 16 = 25，所以 c = 5。'
        }
    },
    {
        'name': '解题方法与技巧',
        'type': 'method',
        'type_name': '方法',
        'difficulty': '进阶',
        'description': '学习常见的解题思路和方法技巧，培养逻辑思维能力。多做练习，总结规律，形成自己的解题方法体系。',
        'formula': None,
        'example': {
            'question': '求证：对于任意正整数n，n³ - n必能被6整除。',
            'answer': '证明见解析',
            'analysis': 'n³ - n = n(n²-1) = n(n-1)(n+1)，即三个连续整数的乘积。三个连续整数中必有一个是2的倍数，一个是3的倍数，故能被6整除。'
        }
    },
]

VIDEOS_DATA = [
    {'id': 'v1', 'title': '第一章知识点精讲', 'description': '系统讲解本章核心知识点，配合例题加深理解', 'duration': '45:30', 'views': 12580, 'rating': 4.8},
    {'id': 'v2', 'title': '典型例题解析', 'description': '精选典型例题，详细讲解解题思路和方法', 'duration': '32:15', 'views': 9860, 'rating': 4.9},
    {'id': 'v3', 'title': '难点突破专题', 'description': '针对本章难点内容进行专项讲解和训练', 'duration': '28:45', 'views': 7620, 'rating': 4.7},
    {'id': 'v4', 'title': '单元复习总结', 'description': '全章知识点梳理，构建知识体系框架', 'duration': '38:20', 'views': 15230, 'rating': 4.9},
]

RECOMMEND_EXAMS = [
    {'id': 'exam1', 'name': '数学第一单元测试', 'description': '第一章基础知识检测，检验学习成果', 'type': 'unit', 'type_name': '单元测试',
     'subject': 'math', 'subject_emoji': '🔢', 'difficulty': 'medium', 'difficulty_name': '中等',
     'question_count': 20, 'duration': 45, 'total_score': 100, 'participants': 1256},
    {'id': 'exam2', 'name': '语文阅读理解专项', 'description': '现代文阅读+文言文阅读专项训练', 'type': 'special', 'type_name': '专项训练',
     'subject': 'chinese', 'subject_emoji': '📖', 'difficulty': 'hard', 'difficulty_name': '困难',
     'question_count': 15, 'duration': 60, 'total_score': 100, 'participants': 892},
    {'id': 'exam3', 'name': '英语期中考试模拟', 'description': '期中考试全真模拟，提前适应考试节奏', 'type': 'mock', 'type_name': '模拟考试',
     'subject': 'english', 'subject_emoji': '🔤', 'difficulty': 'medium', 'difficulty_name': '中等',
     'question_count': 50, 'duration': 90, 'total_score': 120, 'participants': 2341},
    {'id': 'exam4', 'name': '物理力学综合测试', 'description': '力学知识点综合应用能力测试', 'type': 'unit', 'type_name': '单元测试',
     'subject': 'physics', 'subject_emoji': '⚡', 'difficulty': 'hard', 'difficulty_name': '困难',
     'question_count': 25, 'duration': 60, 'total_score': 100, 'participants': 678},
    {'id': 'exam5', 'name': '化学方程式默写', 'description': '常见化学方程式书写检测', 'type': 'special', 'type_name': '专项训练',
     'subject': 'chemistry', 'subject_emoji': '🧪', 'difficulty': 'easy', 'difficulty_name': '简单',
     'question_count': 30, 'duration': 30, 'total_score': 100, 'participants': 1567},
    {'id': 'exam6', 'name': '历史时间线检测', 'description': '重大历史事件时间顺序记忆检测', 'type': 'special', 'type_name': '专项训练',
     'subject': 'history', 'subject_emoji': '🏛️', 'difficulty': 'easy', 'difficulty_name': '简单',
     'question_count': 40, 'duration': 25, 'total_score': 100, 'participants': 945},
]

SUBJECT_STATS = [
    {'name': '语文', 'emoji': '📖', 'progress': 78, 'score': 85, 'color': '#ff6b6b'},
    {'name': '数学', 'emoji': '🔢', 'progress': 65, 'score': 78, 'color': '#4facfe'},
    {'name': '英语', 'emoji': '🔤', 'progress': 82, 'score': 90, 'color': '#43e97b'},
    {'name': '物理', 'emoji': '⚡', 'progress': 55, 'score': 72, 'color': '#fa709a'},
    {'name': '化学', 'emoji': '🧪', 'progress': 70, 'score': 82, 'color': '#a18cd1'},
    {'name': '生物', 'emoji': '🧬', 'progress': 68, 'score': 80, 'color': '#84fab0'},
]

WEAK_POINTS = [
    {'id': 'wp1', 'name': '二次函数综合应用', 'subject': '数学', 'subject_emoji': '🔢', 'mastery': 35, 'color': '#4facfe'},
    {'id': 'wp2', 'name': '文言文翻译', 'subject': '语文', 'subject_emoji': '📖', 'mastery': 42, 'color': '#ff6b6b'},
    {'id': 'wp3', 'name': '力学受力分析', 'subject': '物理', 'subject_emoji': '⚡', 'mastery': 48, 'color': '#fa709a'},
    {'id': 'wp4', 'name': '化学方程式配平', 'subject': '化学', 'subject_emoji': '🧪', 'mastery': 55, 'color': '#a18cd1'},
]

EXAM_STATS = {
    'total': 24,
    'completed': 16,
    'avg_score': 82.5,
    'rank': 15,
}

PRACTICE_STATS = {
    'total': 1256,
    'done': 892,
    'accuracy': 87.3,
    'avg_time': '3分20秒',
}


@k12_bp.route('/k12')
def k12_index():
    """K12教育首页 - 公开访问，展示功能介绍"""
    logger.info(f"[K12] 访客访问K12首页")
    user_grade = session.get('grade', '')
    user_info = get_user_k12_info()
    
    # 检查是否需要显示登录提示
    show_login_prompt = not user_info['is_logged_in']
    show_grade_prompt = user_info['is_logged_in'] and user_info['can_access_k12'] and not user_info['has_grade']
    
    return render_template('k12/k12_index.html',
                         title='K12智慧教育',
                         current_page='k12',
                         user_grade=user_grade,
                         user_info=user_info,
                         show_login_prompt=show_login_prompt,
                         show_grade_prompt=show_grade_prompt)


@k12_bp.route('/k12/subject/<subject>')
@require_login
@require_k12_role
@require_grade
def k12_subject(subject):
    """K12学科学习页面 - 需要登录、角色验证、年级设置"""
    logger.info(f"[K12] 用户 {session.get('username')} 访问{subject}学科页面")
    
    # 检查学科是否有效
    if subject not in SUBJECT_INFO:
        logger.warning(f"[K12] 无效的学科: {subject}")
        return render_template('404.html', message=f'学科 {subject} 不存在'), 404
    
    info = SUBJECT_INFO.get(subject, {'name': subject, 'emoji': '📚', 'description': ''})
    user_info = get_user_k12_info()
    
    return render_template('k12/k12_subject.html',
                         title=f'{info["name"]} - K12学科学习',
                         current_page='k12',
                         subject=subject,
                         subject_name=info['name'],
                         subject_emoji=info['emoji'],
                         subject_description=info['description'],
                         chapters_count=len(CHAPTERS_DATA),
                         knowledge_points=65,
                         questions_count=1280,
                         chapters=CHAPTERS_DATA,
                         knowledge_points_list=KNOWLEDGE_POINTS,
                         videos=VIDEOS_DATA,
                         exams=RECOMMEND_EXAMS[:3],
                         practice_stats=PRACTICE_STATS,
                         user_info=user_info)


@k12_bp.route('/k12/exam')
@require_login
@require_k12_role
@require_student_only
@require_grade
def k12_exam():
    """K12考试中心 - 需要登录、角色验证、仅学生、年级设置"""
    logger.info(f"[K12] 用户 {session.get('username')} 访问考试中心")
    user_info = get_user_k12_info()
    return render_template('k12/k12_exam.html',
                         title='K12考试中心',
                         current_page='k12',
                         recommend_exams=RECOMMEND_EXAMS,
                         ongoing_exams=[],
                         upcoming_exams=[],
                         history_exams=[],
                         exam_stats=EXAM_STATS,
                         user_info=user_info)


@k12_bp.route('/k12/report')
@require_login
@require_k12_role
@require_student_only
@require_grade
def k12_report():
    """K12学习报告 - 需要登录、角色验证、仅学生、年级设置"""
    logger.info(f"[K12] 用户 {session.get('username')} 访问学习报告")
    user_info = get_user_k12_info()
    return render_template('k12/k12_report.html',
                         title='K12学习报告',
                         current_page='k12',
                         subject_stats=SUBJECT_STATS,
                         weak_points=WEAK_POINTS,
                         user_info=user_info)


@k12_bp.route('/k12/practice')
@require_login
@require_k12_role
def k12_practice():
    """K12智能练习 - 需要登录和角色验证，但不需要年级设置"""
    logger.info(f"[K12] 用户 {session.get('username')} 访问智能练习")
    return redirect(url_for('learning_system.learning_system_index'))


@k12_bp.route('/api/k12/set_grade', methods=['POST'])
@require_login
@require_k12_role
def api_set_grade():
    """设置用户年级 - 需要登录和角色验证"""
    try:
        data = request.get_json()
        grade = data.get('grade', '')
        
        if grade not in K12_GRADES:
            return jsonify({'success': False, 'error': '无效的年级', 'code': 'INVALID_GRADE'})
        
        user_id = session.get('user_id')
        username = session.get('username')
        if user_id:
            try:
                import sqlite3
                db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE users SET grade = ? WHERE id = ?', (grade, user_id))
                    conn.commit()
                    logger.info(f"[K12] 用户 {username} (ID:{user_id}) 设置年级为: {grade}")
            except Exception as e:
                logger.warning(f"更新数据库年级失败: {e}")
        
        session['grade'] = grade
        return jsonify({
            'success': True,
            'grade': grade,
            'message': f'年级设置成功：{grade}'
        })
    except Exception as e:
        logger.error(f"设置年级失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@k12_bp.route('/api/k12/subjects')
@require_login
@require_k12_role
def api_get_subjects():
    """获取学科列表 - 需要登录和角色验证"""
    subjects = []
    for key, info in SUBJECT_INFO.items():
        subjects.append({
            'key': key,
            'name': info['name'],
            'emoji': info['emoji'],
            'description': info['description']
        })
    return jsonify({'success': True, 'data': subjects})


@k12_bp.route('/api/k12/grades')
@require_login
@require_k12_role
def api_get_grades():
    """获取K12年级列表 - 需要登录和角色验证"""
    return jsonify({'success': True, 'data': K12_GRADES})


@k12_bp.route('/api/k12/status')
def api_k12_status():
    """获取K12访问状态 - 公开接口，无需登录"""
    return jsonify({
        'success': True,
        'is_logged_in': 'user_id' in session,
        'user_role': session.get('role', ''),
        'user_grade': session.get('grade', ''),
        'can_access': session.get('role', '') in ALLOWED_ROLES,
        'allowed_roles': ALLOWED_ROLES
    })


@k12_bp.route('/api/k12/user_info')
@require_login
def api_user_k12_info():
    """获取用户在K12系统中的详细信息 - 需要登录"""
    user_info = get_user_k12_info()
    return jsonify({'success': True, 'data': user_info})


@k12_bp.route('/api/k12/permission_check')
@require_login
def api_permission_check():
    """权限检查接口 - 检查当前用户对指定路由的访问权限"""
    route_name = request.args.get('route', '')
    
    if not route_name:
        return jsonify({'success': False, 'error': '未指定路由名称'})
    
    allowed, errors = check_k12_permission(route_name)
    
    return jsonify({
        'success': True,
        'allowed': allowed,
        'route': route_name,
        'errors': errors,
        'user_info': get_user_k12_info()
    })


# ==================== 年级管理增强API ====================

@k12_bp.route('/api/k12/grade/planning')
@require_login
@require_k12_role
@require_grade
def api_get_grade_planning():
    """获取年级课程规划 - 根据用户年级返回对应的课程规划"""
    user_grade = session.get('grade', '')
    
    if user_grade not in GRADE_COURSE_PLANNING:
        return jsonify({'success': False, 'error': '未找到该年级的课程规划', 'code': 'PLANNING_NOT_FOUND'})
    
    planning = GRADE_COURSE_PLANNING[user_grade]
    
    # 获取该年级各学科的知识点
    grade_level = '小学' if user_grade.startswith('小学') else ('初中' if user_grade.startswith('初中') else '高中')
    grade_knowledge = GRADE_KNOWLEDGE_POINTS.get(grade_level, {})
    
    # 筛选该年级涉及的学科知识点
    relevant_knowledge = {}
    for subject_key in planning['subjects']:
        if subject_key in grade_knowledge:
            relevant_knowledge[subject_key] = grade_knowledge[subject_key]
    
    return jsonify({
        'success': True,
        'data': {
            'grade': user_grade,
            'planning': planning,
            'knowledge_points': relevant_knowledge,
            'available_subjects': [SUBJECT_INFO.get(s, {'name': s}) for s in planning['subjects']]
        }
    })


@k12_bp.route('/api/k12/grade/<grade>/planning')
@require_login
@require_k12_role
def api_get_specific_grade_planning(grade):
    """获取指定年级的课程规划 - 教师可查看任意年级"""
    role = session.get('role', '')
    
    # 只有教师可以查看任意年级规划
    if role != 'teacher' and grade != session.get('grade', ''):
        return jsonify({'success': False, 'error': '只能查看自己年级的课程规划', 'code': 'GRADE_NOT_ALLOWED'}), 403
    
    if grade not in GRADE_COURSE_PLANNING:
        return jsonify({'success': False, 'error': '无效的年级', 'code': 'INVALID_GRADE'})
    
    planning = GRADE_COURSE_PLANNING[grade]
    grade_level = '小学' if grade.startswith('小学') else ('初中' if grade.startswith('初中') else '高中')
    grade_knowledge = GRADE_KNOWLEDGE_POINTS.get(grade_level, {})
    
    relevant_knowledge = {}
    for subject_key in planning['subjects']:
        if subject_key in grade_knowledge:
            relevant_knowledge[subject_key] = grade_knowledge[subject_key]
    
    return jsonify({
        'success': True,
        'data': {
            'grade': grade,
            'planning': planning,
            'knowledge_points': relevant_knowledge
        }
    })


@k12_bp.route('/api/k12/grade/all_planning')
@require_login
@require_k12_role
def api_get_all_grade_planning():
    """获取所有年级的课程规划概览 - 仅教师可访问"""
    role = session.get('role', '')
    if role != 'teacher':
        return jsonify({'success': False, 'error': '此接口仅限教师访问', 'code': 'TEACHER_ONLY'})
    
    return jsonify({
        'success': True,
        'data': GRADE_COURSE_PLANNING
    })


@k12_bp.route('/api/k12/grade/knowledge_points')
@require_login
@require_k12_role
@require_grade
def api_get_grade_knowledge_points():
    """获取年级知识点配置"""
    user_grade = session.get('grade', '')
    grade_level = '小学' if user_grade.startswith('小学') else ('初中' if user_grade.startswith('初中') else '高中')
    
    knowledge_points = GRADE_KNOWLEDGE_POINTS.get(grade_level, {})
    
    return jsonify({
        'success': True,
        'data': {
            'grade': user_grade,
            'grade_level': grade_level,
            'knowledge_points': knowledge_points
        }
    })


# ==================== 学科题库API ====================

@k12_bp.route('/api/k12/question_bank/<subject>')
@require_login
@require_k12_role
def api_get_subject_question_bank(subject):
    """获取学科题库信息"""
    if subject not in SUBJECT_QUESTION_BANK:
        return jsonify({'success': False, 'error': '无效的学科', 'code': 'INVALID_SUBJECT'})
    
    bank_info = SUBJECT_QUESTION_BANK[subject]
    
    # 计算总题数
    total_questions = sum(ch['question_count'] for ch in bank_info['chapters'])
    
    return jsonify({
        'success': True,
        'data': {
            'subject': subject,
            'subject_name': bank_info['name'],
            'question_types': bank_info['question_types'],
            'difficulty_levels': bank_info['difficulty_levels'],
            'chapters': bank_info['chapters'],
            'total_questions': total_questions,
            'sample_questions': bank_info['sample_questions']
        }
    })


@k12_bp.route('/api/k12/question_bank/all')
@require_login
@require_k12_role
def api_get_all_question_bank():
    """获取所有学科题库概览"""
    banks = []
    total_questions = 0
    
    for subject_key, bank_info in SUBJECT_QUESTION_BANK.items():
        subject_total = sum(ch['question_count'] for ch in bank_info['chapters'])
        total_questions += subject_total
        
        banks.append({
            'subject': subject_key,
            'subject_name': bank_info['name'],
            'subject_emoji': SUBJECT_INFO.get(subject_key, {}).get('emoji', '📚'),
            'total_questions': subject_total,
            'chapters_count': len(bank_info['chapters']),
            'question_types': bank_info['question_types']
        })
    
    return jsonify({
        'success': True,
        'data': {
            'banks': banks,
            'total_questions': total_questions,
            'subjects_count': len(banks)
        }
    })


@k12_bp.route('/api/k12/questions/generate', methods=['POST'])
@require_login
@require_k12_role
def api_generate_questions():
    """根据年级和学科生成题目"""
    data = request.get_json() or {}
    
    subject = data.get('subject', '')
    grade = data.get('grade', session.get('grade', ''))
    difficulty = data.get('difficulty', '中等')
    count = data.get('count', 10)
    question_type = data.get('question_type', '选择题')
    
    # 验证参数
    if subject not in SUBJECT_QUESTION_BANK:
        return jsonify({'success': False, 'error': '无效的学科', 'code': 'INVALID_SUBJECT'})
    
    if grade not in K12_GRADES:
        return jsonify({'success': False, 'error': '无效的年级', 'code': 'INVALID_GRADE'})
    
    bank_info = SUBJECT_QUESTION_BANK[subject]
    
    # 模拟生成题目 (实际项目中应从数据库或AI生成)
    questions = []
    for i in range(min(count, 20)):
        questions.append({
            'id': f'{subject}_q{i+1}',
            'subject': subject,
            'grade': grade,
            'type': question_type,
            'difficulty': difficulty,
            'content': f'【示例题目{i+1}】根据{grade} {bank_info["name"]} {difficulty}难度要求生成的题目',
            'options': ['选项A', '选项B', '选项C', '选项D'] if question_type == '选择题' else None,
            'chapter': bank_info['chapters'][i % len(bank_info['chapters'])]['name']
        })
    
    return jsonify({
        'success': True,
        'data': {
            'questions': questions,
            'generated_count': len(questions),
            'subject': subject,
            'grade': grade,
            'difficulty': difficulty
        }
    })


# ==================== 学生学习进度追踪API ====================

@k12_bp.route('/api/k12/progress/update', methods=['POST'])
@require_login
@require_k12_role
@require_student_only
def api_update_learning_progress():
    """更新学生学习进度"""
    data = request.get_json() or {}
    
    user_id = session.get('user_id')
    subject = data.get('subject', '')
    chapter = data.get('chapter', '')
    progress = data.get('progress', 0)
    score = data.get('score', 0)
    
    if subject not in SUBJECT_INFO:
        return jsonify({'success': False, 'error': '无效的学科', 'code': 'INVALID_SUBJECT'})
    
    try:
        import sqlite3
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 创建进度表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS k12_learning_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    chapter TEXT,
                    progress REAL DEFAULT 0,
                    score REAL DEFAULT 0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, subject, chapter)
                )
            ''')
            
            # 更新或插入进度
            cursor.execute('''
                INSERT OR REPLACE INTO k12_learning_progress 
                (user_id, subject, chapter, progress, score, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            ''', (user_id, subject, chapter, progress, score))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': '学习进度更新成功',
            'data': {
                'subject': subject,
                'chapter': chapter,
                'progress': progress,
                'score': score
            }
        })
    except Exception as e:
        logger.error(f"更新学习进度失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@k12_bp.route('/api/k12/progress/get')
@require_login
@require_k12_role
def api_get_learning_progress():
    """获取学生学习进度"""
    user_id = session.get('user_id')
    subject = request.args.get('subject', '')
    
    try:
        import sqlite3
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            if subject:
                cursor.execute('''
                    SELECT subject, chapter, progress, score, updated_at 
                    FROM k12_learning_progress WHERE user_id = ? AND subject = ?
                ''', (user_id, subject))
            else:
                cursor.execute('''
                    SELECT subject, chapter, progress, score, updated_at 
                    FROM k12_learning_progress WHERE user_id = ?
                ''', (user_id,))
            
            progress_list = []
            for row in cursor.fetchall():
                progress_list.append({
                    'subject': row[0],
                    'subject_name': SUBJECT_INFO.get(row[0], {}).get('name', row[0]),
                    'chapter': row[1],
                    'progress': row[2],
                    'score': row[3],
                    'updated_at': row[4]
                })
        
        return jsonify({
            'success': True,
            'data': progress_list
        })
    except Exception as e:
        logger.error(f"获取学习进度失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 薄弱点分析API ====================

@k12_bp.route('/api/k12/weak_points/analyze')
@require_login
@require_k12_role
@require_student_only
def api_analyze_weak_points():
    """分析学生薄弱知识点"""
    user_id = session.get('user_id')
    
    try:
        import sqlite3
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT subject, chapter, progress, score 
                FROM k12_learning_progress WHERE user_id = ? AND score < 80
                ORDER BY score ASC
            ''', (user_id,))
            
            weak_points = []
            for row in cursor.fetchall():
                weak_points.append({
                    'subject': row[0],
                    'subject_name': SUBJECT_INFO.get(row[0], {}).get('name', row[0]),
                    'chapter': row[1],
                    'score': row[3],
                    'progress': row[2],
                    'mastery_level': '薄弱' if row[3] < 60 else '待提升'
                })
        
        return jsonify({
            'success': True,
            'data': {
                'weak_points': weak_points,
                'recommendations': [
                    {'subject': wp['subject'], 'action': '建议加强练习', 'chapter': wp['chapter']}
                    for wp in weak_points[:5]
                ]
            }
        })
    except Exception as e:
        logger.error(f"分析薄弱点失败: {e}")
        # 返回默认数据
        return jsonify({
            'success': True,
            'data': {
                'weak_points': WEAK_POINTS,
                'recommendations': []
            }
        })
