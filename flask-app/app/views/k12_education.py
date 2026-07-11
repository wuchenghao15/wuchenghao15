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
    'science': {'name': '科学', 'emoji': '🔬', 'description': '自然探索·科学实验·科技创新'},
    'information_tech': {'name': '信息技术', 'emoji': '💻', 'description': '编程·网络·数据·人工智能'},
    'general_tech': {'name': '通用技术', 'emoji': '🛠️', 'description': '技术设计·工程实践·创新制作'},
    'pe': {'name': '体育', 'emoji': '⚽', 'description': '体能训练·竞技运动·健康知识'},
    'music': {'name': '音乐', 'emoji': '🎵', 'description': '乐理知识·音乐欣赏·声乐器乐'},
    'art': {'name': '美术', 'emoji': '🎨', 'description': '绘画·雕塑·设计·艺术鉴赏'},
}

K12_GRADES = [
    '小学1年级', '小学2年级', '小学3年级', '小学4年级', '小学5年级', '小学6年级',
    '初中1年级', '初中2年级', '初中3年级',
    '高中1年级', '高中2年级', '高中3年级',
]

# ==================== 年级课程规划配置 ====================
GRADE_COURSE_PLANNING = {
    '小学1年级': {
        'subjects': ['chinese', 'math', 'science', 'pe', 'music', 'art'],
        'focus': ['基础识字', '拼音学习', '数字认知', '加减法入门', '自然探索', '体能启蒙'],
        'daily_hours': 5,
        'weekly_goals': ['掌握20个生字', '完成基础加减法练习', '认识5种动植物'],
        'difficulty_level': '基础入门'
    },
    '小学2年级': {
        'subjects': ['chinese', 'math', 'science', 'pe', 'music', 'art'],
        'focus': ['阅读理解入门', '乘除法基础', '词语积累', '科学观察', '运动技能'],
        'daily_hours': 5,
        'weekly_goals': ['阅读短文10篇', '掌握乘法口诀', '完成1个科学小实验'],
        'difficulty_level': '基础巩固'
    },
    '小学3年级': {
        'subjects': ['chinese', 'math', 'english', 'science', 'pe', 'music', 'art'],
        'focus': ['写作入门', '分数基础', '英语字母', '科学实验', '信息技术入门'],
        'daily_hours': 6,
        'weekly_goals': ['完成日记写作', '掌握基础英语词汇50个', '学习简单的电脑操作'],
        'difficulty_level': '基础拓展'
    },
    '小学4年级': {
        'subjects': ['chinese', 'math', 'english', 'science', 'information_tech', 'pe', 'music', 'art'],
        'focus': ['作文技巧', '几何入门', '英语对话', '科学探究', '计算机基础'],
        'daily_hours': 6,
        'weekly_goals': ['写作完整作文', '英语口语练习', '完成10个基础编程练习'],
        'difficulty_level': '进阶启蒙'
    },
    '小学5年级': {
        'subjects': ['chinese', 'math', 'english', 'science', 'information_tech', 'pe', 'music', 'art'],
        'focus': ['文言文入门', '代数基础', '英语阅读', '科学原理', '编程入门'],
        'daily_hours': 7,
        'weekly_goals': ['文言文翻译练习', '英语短文阅读', '完成Scratch编程项目'],
        'difficulty_level': '进阶提升'
    },
    '小学6年级': {
        'subjects': ['chinese', 'math', 'english', 'science', 'information_tech', 'pe', 'music', 'art'],
        'focus': ['小升初预备', '综合复习', '升学考点', '科学综合', '技术实践'],
        'daily_hours': 7,
        'weekly_goals': ['完成升学模拟测试', '系统复习核心知识', '完成1个科技小制作'],
        'difficulty_level': '升学冲刺'
    },
    '初中1年级': {
        'subjects': ['chinese', 'math', 'english', 'history', 'geography', 'biology', 'information_tech', 'pe', 'music', 'art'],
        'focus': ['文言文深入', '代数方程', '英语语法', '历史入门', '地理基础', '生物基础', '信息技术基础'],
        'daily_hours': 8,
        'weekly_goals': ['文言文背诵', '代数解题', '英语作文', '学习Python基础'],
        'difficulty_level': '初中基础'
    },
    '初中2年级': {
        'subjects': ['chinese', 'math', 'english', 'physics', 'history', 'geography', 'biology', 'information_tech', 'general_tech', 'pe'],
        'focus': ['现代文分析', '几何证明', '英语听力', '物理力学', '近代史', '技术设计'],
        'daily_hours': 8,
        'weekly_goals': ['物理实验', '几何证明题', '英语听力训练', '完成技术设计项目'],
        'difficulty_level': '初中进阶'
    },
    '初中3年级': {
        'subjects': ['chinese', 'math', 'english', 'physics', 'chemistry', 'history', 'politics', 'information_tech', 'general_tech'],
        'focus': ['中考冲刺', '综合复习', '化学入门', '中考模拟', '技术实践'],
        'daily_hours': 9,
        'weekly_goals': ['完成中考模拟试卷', '化学方程式记忆', '信息科技中考复习'],
        'difficulty_level': '中考冲刺'
    },
    '高中1年级': {
        'subjects': ['chinese', 'math', 'english', 'physics', 'chemistry', 'biology', 'history', 'geography', 'politics', 'information_tech', 'general_tech', 'pe'],
        'focus': ['高中适应', '函数深入', '英语写作', '必修课程', '信息技术必修'],
        'daily_hours': 9,
        'weekly_goals': ['函数综合练习', '英语写作提高', '完成信息技术必修项目'],
        'difficulty_level': '高中基础'
    },
    '高中2年级': {
        'subjects': ['chinese', 'math', 'english', 'physics', 'chemistry', 'biology', 'history', 'geography', 'politics', 'information_tech', 'general_tech'],
        'focus': ['选修课程', '高考预备', '学科深化', '技术选修'],
        'daily_hours': 10,
        'weekly_goals': ['选修科目强化', '高考知识点梳理', '完成通用技术设计'],
        'difficulty_level': '高考预备'
    },
    '高中3年级': {
        'subjects': ['chinese', 'math', 'english', 'physics', 'chemistry', 'biology', 'history', 'geography', 'politics', 'information_tech'],
        'focus': ['高考冲刺', '真题训练', '志愿准备', '信息科技备考'],
        'daily_hours': 11,
        'weekly_goals': ['完成高考真题', '知识点查漏补缺', '信息科技高考冲刺'],
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
        },
        'science': {
            '自然探索': ['动植物识别', '天气变化', '季节特征', '自然现象'],
            '科学实验': ['观察方法', '实验设计', '数据记录', '结论分析'],
            '科学原理': ['力与运动', '光与声', '电与磁', '物质变化']
        },
        'information_tech': {
            '计算机基础': ['电脑组成', '操作系统', '鼠标键盘', '开关机操作'],
            '办公软件': ['文字处理', '表格制作', '演示文稿', '文件管理'],
            '编程入门': ['Scratch编程', '算法思维', '逻辑控制', '创意编程']
        },
        'pe': {
            '体能训练': ['跑步', '跳绳', '游泳', '力量训练'],
            '球类运动': ['篮球', '足球', '羽毛球', '乒乓球'],
            '健康知识': ['营养常识', '运动安全', '卫生习惯', '心理健康']
        },
        'music': {
            '乐理知识': ['音符识读', '节奏节拍', '音高旋律', '调式调性'],
            '音乐欣赏': ['中外名曲', '乐器识别', '音乐风格', '情感表达'],
            '演唱演奏': ['声乐技巧', '简单乐器', '合唱合奏', '音乐表演']
        },
        'art': {
            '绘画基础': ['线条运用', '色彩搭配', '构图原理', '写生技法'],
            '手工制作': ['剪纸', '折纸', '泥塑', '创意手工'],
            '艺术鉴赏': ['中外名画', '艺术流派', '艺术风格', '审美培养']
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
        },
        'information_tech': {
            '信息技术基础': ['信息概念', '信息技术发展', '信息安全', '信息素养'],
            '编程基础': ['Python编程', '程序设计', '算法基础', '数据结构'],
            '网络基础': ['网络组成', 'IP地址', '网络协议', '互联网应用']
        },
        'general_tech': {
            '技术设计': ['设计原则', '设计流程', '创新思维', '方案优化'],
            '工程实践': ['材料选择', '工具使用', '工艺技术', '质量控制'],
            '技术与社会': ['技术影响', '技术伦理', '技术创新', '技术未来']
        },
        'pe': {
            '体能训练': ['耐力训练', '速度训练', '力量训练', '柔韧性训练'],
            '球类运动': ['篮球技巧', '足球战术', '排球技术', '田径运动'],
            '健康知识': ['运动生理学', '营养与健康', '运动心理学', '安全防护']
        },
        'music': {
            '乐理知识': ['五线谱识读', '调式调性', '和弦理论', '曲式分析'],
            '音乐欣赏': ['古典音乐', '民族音乐', '流行音乐', '音乐文化'],
            '演唱演奏': ['声乐训练', '器乐演奏', '音乐创作', '音乐表演']
        },
        'art': {
            '绘画基础': ['素描技法', '色彩理论', '构图原理', '透视画法'],
            '设计基础': ['平面设计', '立体构成', '色彩设计', '视觉传达'],
            '艺术鉴赏': ['西方美术史', '中国美术史', '现代艺术', '艺术批评']
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
        },
        'information_tech': {
            '数据与算法': ['数据采集', '数据分析', '算法设计', '人工智能'],
            '程序设计': ['Python高级', '面向对象', 'Web开发', '数据库'],
            '信息系统': ['系统设计', '网络安全', '软件工程', '信息化管理']
        },
        'general_tech': {
            '技术设计': ['创新设计', '系统设计', '优化设计', '设计评价'],
            '工程实践': ['工程材料', '制造工艺', '质量检测', '项目管理'],
            '技术创新': ['技术发明', '技术改造', '专利申请', '技术创业']
        },
        'pe': {
            '体能训练': ['专项体能', '体能测试', '体能训练计划', '运动恢复'],
            '球类运动': ['篮球战术', '足球技术', '羽毛球技巧', '游泳训练'],
            '健康知识': ['运动医学', '营养配餐', '心理训练', '运动生涯规划']
        },
        'music': {
            '乐理知识': ['和声学', '对位法', '配器法', '音乐分析'],
            '音乐欣赏': ['音乐史', '音乐美学', '音乐评论', '音乐文化'],
            '演唱演奏': ['专业声乐', '器乐独奏', '音乐创作', '指挥艺术']
        },
        'art': {
            '绘画基础': ['专业素描', '油画技法', '中国画', '版画'],
            '设计基础': ['视觉设计', '产品设计', '环境设计', '数字艺术'],
            '艺术鉴赏': ['艺术理论', '美学原理', '艺术批评', '艺术市场']
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
    },
    'science': {
        'name': '科学',
        'question_types': ['选择题', '填空题', '简答题', '实验题', '探究题'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'sc_ch1', 'name': '自然探索', 'question_count': 180, 'types': ['选择题', '填空题', '简答题']},
            {'id': 'sc_ch2', 'name': '科学实验', 'question_count': 150, 'types': ['实验题', '探究题', '分析题']},
            {'id': 'sc_ch3', 'name': '科学原理', 'question_count': 120, 'types': ['选择题', '计算题', '简答题']},
            {'id': 'sc_ch4', 'name': '科学探究', 'question_count': 100, 'types': ['探究题', '实验设计', '分析题']},
            {'id': 'sc_ch5', 'name': '科技发展', 'question_count': 80, 'types': ['选择题', '简答题', '论述题']}
        ],
        'sample_questions': [
            {'type': '选择题', 'difficulty': '基础', 'content': '植物进行光合作用的场所是?', 'answer': '叶绿体'},
            {'type': '实验题', 'difficulty': '中等', 'content': '设计实验验证光合作用需要光', 'answer': '对照实验'},
            {'type': '探究题', 'difficulty': '困难', 'content': '探究影响种子萌发的因素', 'answer': '多变量控制实验'}
        ]
    },
    'information_tech': {
        'name': '信息技术',
        'question_types': ['选择题', '填空题', '简答题', '编程题', '操作题'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'it_ch1', 'name': '信息技术基础', 'question_count': 150, 'types': ['选择题', '填空题', '简答题']},
            {'id': 'it_ch2', 'name': '编程基础', 'question_count': 200, 'types': ['编程题', '填空题', '分析题']},
            {'id': 'it_ch3', 'name': '网络基础', 'question_count': 120, 'types': ['选择题', '简答题', '分析题']},
            {'id': 'it_ch4', 'name': '数据与算法', 'question_count': 150, 'types': ['编程题', '计算题', '分析题']},
            {'id': 'it_ch5', 'name': '信息系统', 'question_count': 100, 'types': ['操作题', '简答题', '分析题']}
        ],
        'sample_questions': [
            {'type': '选择题', 'difficulty': '基础', 'content': '计算机中存储容量的基本单位是?', 'answer': '字节(Byte)'},
            {'type': '编程题', 'difficulty': '中等', 'content': '编写Python程序计算1到100的和', 'answer': 'sum(range(1,101))'},
            {'type': '简答题', 'difficulty': '困难', 'content': '简述TCP/IP协议的分层结构', 'answer': '应用层、传输层、网络层、网络接口层'}
        ]
    },
    'general_tech': {
        'name': '通用技术',
        'question_types': ['选择题', '填空题', '简答题', '设计题', '分析题'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'gt_ch1', 'name': '技术设计', 'question_count': 150, 'types': ['设计题', '简答题', '分析题']},
            {'id': 'gt_ch2', 'name': '工程实践', 'question_count': 120, 'types': ['操作题', '简答题', '分析题']},
            {'id': 'gt_ch3', 'name': '技术与社会', 'question_count': 100, 'types': ['选择题', '简答题', '论述题']},
            {'id': 'gt_ch4', 'name': '技术创新', 'question_count': 80, 'types': ['设计题', '分析题', '论述题']},
            {'id': 'gt_ch5', 'name': '材料与工艺', 'question_count': 100, 'types': ['选择题', '简答题', '分析题']}
        ],
        'sample_questions': [
            {'type': '选择题', 'difficulty': '基础', 'content': '技术设计的一般流程是?', 'answer': '发现问题→明确问题→方案设计→模型制作→测试优化'},
            {'type': '设计题', 'difficulty': '中等', 'content': '设计一款多功能笔筒', 'answer': '设计草图+功能说明'},
            {'type': '分析题', 'difficulty': '困难', 'content': '分析某产品的技术优缺点并提出改进方案', 'answer': '多维度分析+改进建议'}
        ]
    },
    'pe': {
        'name': '体育',
        'question_types': ['选择题', '填空题', '简答题', '技能题', '分析题'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'pe_ch1', 'name': '体能训练', 'question_count': 120, 'types': ['选择题', '简答题', '技能题']},
            {'id': 'pe_ch2', 'name': '球类运动', 'question_count': 150, 'types': ['技能题', '分析题', '简答题']},
            {'id': 'pe_ch3', 'name': '健康知识', 'question_count': 180, 'types': ['选择题', '简答题', '分析题']},
            {'id': 'pe_ch4', 'name': '田径运动', 'question_count': 100, 'types': ['技能题', '简答题', '分析题']},
            {'id': 'pe_ch5', 'name': '运动安全', 'question_count': 80, 'types': ['选择题', '简答题', '案例分析']}
        ],
        'sample_questions': [
            {'type': '选择题', 'difficulty': '基础', 'content': '人体运动的三大能源系统是?', 'answer': 'ATP-CP系统、乳酸能系统、有氧氧化系统'},
            {'type': '技能题', 'difficulty': '中等', 'content': '简述篮球三步上篮的动作要领', 'answer': '一大二小三高跳'},
            {'type': '分析题', 'difficulty': '困难', 'content': '分析某运动员受伤原因并提出预防措施', 'answer': '技术分析+预防方案'}
        ]
    },
    'music': {
        'name': '音乐',
        'question_types': ['选择题', '填空题', '简答题', '听音题', '分析题'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'mu_ch1', 'name': '乐理知识', 'question_count': 150, 'types': ['选择题', '填空题', '听音题']},
            {'id': 'mu_ch2', 'name': '音乐欣赏', 'question_count': 120, 'types': ['分析题', '简答题', '选择题']},
            {'id': 'mu_ch3', 'name': '演唱演奏', 'question_count': 100, 'types': ['技能题', '简答题', '分析题']},
            {'id': 'mu_ch4', 'name': '音乐史', 'question_count': 80, 'types': ['选择题', '简答题', '论述题']},
            {'id': 'mu_ch5', 'name': '音乐创作', 'question_count': 60, 'types': ['创作题', '分析题', '简答题']}
        ],
        'sample_questions': [
            {'type': '选择题', 'difficulty': '基础', 'content': '五线谱中高音谱号也称为?', 'answer': 'G谱号'},
            {'type': '听音题', 'difficulty': '中等', 'content': '听辨旋律的调式调性', 'answer': '根据听音结果判断'},
            {'type': '分析题', 'difficulty': '困难', 'content': '分析贝多芬《命运交响曲》第一乐章的音乐特点', 'answer': '主题分析+曲式分析'}
        ]
    },
    'art': {
        'name': '美术',
        'question_types': ['选择题', '填空题', '简答题', '创作题', '分析题'],
        'difficulty_levels': ['基础', '中等', '困难', '挑战'],
        'chapters': [
            {'id': 'ar_ch1', 'name': '绘画基础', 'question_count': 150, 'types': ['选择题', '创作题', '分析题']},
            {'id': 'ar_ch2', 'name': '设计基础', 'question_count': 120, 'types': ['设计题', '分析题', '简答题']},
            {'id': 'ar_ch3', 'name': '艺术鉴赏', 'question_count': 100, 'types': ['分析题', '简答题', '选择题']},
            {'id': 'ar_ch4', 'name': '中外美术史', 'question_count': 80, 'types': ['选择题', '简答题', '论述题']},
            {'id': 'ar_ch5', 'name': '艺术创作', 'question_count': 60, 'types': ['创作题', '分析题', '简答题']}
        ],
        'sample_questions': [
            {'type': '选择题', 'difficulty': '基础', 'content': '三原色指的是?', 'answer': '红、黄、蓝'},
            {'type': '创作题', 'difficulty': '中等', 'content': '以"春天"为主题创作一幅水彩画', 'answer': '作品+创作说明'},
            {'type': '分析题', 'difficulty': '困难', 'content': '分析达芬奇《蒙娜丽莎》的艺术特色', 'answer': '构图+技法+意境分析'}
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


import random

def generate_k12_questions(subject, grade, difficulty, count, question_type):
    """根据学科和年级生成K12题目"""
    grade_level = '小学' if grade.startswith('小学') else ('初中' if grade.startswith('初中') else '高中')
    
    question_generators = {
        'chinese': generate_k12_chinese_questions,
        'math': generate_k12_math_questions,
        'english': generate_k12_english_questions,
        'physics': generate_k12_physics_questions,
        'chemistry': generate_k12_chemistry_questions,
        'biology': generate_k12_biology_questions,
        'history': generate_k12_history_questions,
        'geography': generate_k12_geography_questions,
        'politics': generate_k12_politics_questions,
        'science': generate_k12_science_questions,
        'information_tech': generate_k12_it_questions,
        'general_tech': generate_k12_general_tech_questions,
        'pe': generate_k12_pe_questions,
        'music': generate_k12_music_questions,
        'art': generate_k12_art_questions,
    }
    
    generator = question_generators.get(subject)
    if generator:
        return generator(grade_level, difficulty, count, question_type)
    else:
        return generate_k12_fallback_questions(subject, grade_level, difficulty, count, question_type)


def generate_k12_chinese_questions(grade_level, difficulty, count, question_type):
    """生成语文题目"""
    bank_info = SUBJECT_QUESTION_BANK['chinese']
    
    question_templates = {
        '小学': {
            '基础': [
                ('"春眠不觉晓，处处闻啼鸟"的作者是？', '孟浩然', ['李白', '杜甫', '白居易']),
                ('下列哪个字是形声字？', '晴', ['日', '月', '山']),
                ('"画龙点睛"这个成语比喻什么？', '关键之处一笔传神', ['画技高超', '龙飞凤舞', '颜色鲜艳']),
            ],
            '中等': [
                ('"千里之行，始于足下"出自哪部经典？', '《老子》', ['《论语》', '《孟子》', '《庄子》']),
                ('下列句子使用了什么修辞手法？"月亮像一个大银盘挂在天上。"', '比喻', ['拟人', '夸张', '排比']),
                ('《西游记》中孙悟空的法名是谁取的？', '唐僧', ['观音菩萨', '菩提祖师', '如来佛祖']),
            ],
            '困难': [
                ('"先天下之忧而忧，后天下之乐而乐"出自哪篇文章？', '《岳阳楼记》', ['《醉翁亭记》', ['《滕王阁序》'], '《陋室铭》']),
                ('下列哪个不是李白的作品？', '《石壕吏》', ['《将进酒》', '《望庐山瀑布》', '《蜀道难》']),
                ('"不以物喜，不以己悲"表达了作者怎样的情怀？', '旷达胸襟', ['悲天悯人', ['怀才不遇'], '愤世嫉俗']),
            ]
        },
        '初中': {
            '基础': [
                ('《论语》是记录谁及其弟子言行的书？', '孔子', ['孟子', '老子', '庄子']),
                ('"海内存知己，天涯若比邻"的作者是？', '王勃', ['李白', '杜甫', '白居易']),
                ('小说的三要素是？', '人物、情节、环境', ['时间、地点、人物', ['起因、经过、结果'], '开头、中间、结尾']),
            ],
            '中等': [
                ('"出淤泥而不染，濯清涟而不妖"出自哪篇文章？', '《爱莲说》', ['《陋室铭》', '《桃花源记》', '《岳阳楼记》']),
                ('《水浒传》中"及时雨"指的是？', '宋江', ['林冲', '武松', '鲁智深']),
                ('记叙文的六要素是？', '时间、地点、人物、起因、经过、结果', ['人物、情节、环境', ['论点、论据、论证'], '首联、颔联、颈联、尾联']),
            ],
            '困难': [
                ('"先天下之忧而忧，后天下之乐而乐"的作者是？', '范仲淹', ['欧阳修', '王安石', '苏轼']),
                ('《红楼梦》中"潇湘馆"是谁的居所？', '林黛玉', ['薛宝钗', ['贾宝玉'], '王熙凤']),
                ('"沉舟侧畔千帆过，病树前头万木春"蕴含了什么哲理？', '新事物必将取代旧事物', ['时间流逝', ['人生无常'], '世事难料']),
            ]
        },
        '高中': {
            '基础': [
                ('"亦余心之所善兮，虽九死其犹未悔"出自？', '《离骚》', ['《诗经》', '《九歌》', '《天问》']),
                ('《史记》的作者是？', '司马迁', ['班固', '司马光', '陈寿']),
                ('"采菊东篱下，悠然见南山"的作者是？', '陶渊明', ['谢灵运', '王羲之', '嵇康']),
            ],
            '中等': [
                ('"师者，所以传道受业解惑也"出自哪篇文章？', '《师说》', ['《劝学》', '《六国论》', '《过秦论》']),
                ('《赤壁赋》的作者是？', '苏轼', ['欧阳修', '王安石', '苏洵']),
                ('"落霞与孤鹜齐飞，秋水共长天一色"出自？', '《滕王阁序》', ['《岳阳楼记》', '《醉翁亭记》', '《兰亭集序》']),
            ],
            '困难': [
                ('"人间四月芳菲尽，山寺桃花始盛开"体现了什么哲理？', '矛盾的特殊性', ['联系的普遍性', ['发展的永恒性'], '质量互变规律']),
                ('《红楼梦》中"机关算尽太聪明，反算了卿卿性命"说的是？', '王熙凤', ['林黛玉', ['薛宝钗'], '贾探春']),
                ('"苟利国家生死以，岂因祸福避趋之"的作者是？', '林则徐', ['魏源', '左宗棠', '张之洞']),
            ]
        }
    }
    
    level_templates = question_templates.get(grade_level, question_templates['小学'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'chinese_q{i+1}',
            'subject': 'chinese',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_math_questions(grade_level, difficulty, count, question_type):
    """生成数学题目"""
    bank_info = SUBJECT_QUESTION_BANK['math']
    
    question_templates = {
        '小学': {
            '基础': [
                ('计算：25 + 37 = ?', '62', ['61', '63', '72']),
                ('一个正方形的边长是5厘米，它的周长是多少厘米？', '20厘米', ['10厘米', '25厘米', '15厘米']),
                ('小明有15个苹果，吃了8个，还剩几个？', '7个', ['6个', '8个', '9个']),
            ],
            '中等': [
                ('计算：125 × 8 = ?', '1000', ['900', '1100', '1200']),
                ('一个长方形的长是8米，宽是5米，面积是多少平方米？', '40平方米', ['26平方米', '13平方米', '30平方米']),
                ('一件衣服原价100元，打8折后的价格是多少元？', '80元', ['90元', '70元', '60元']),
            ],
            '困难': [
                ('甲、乙两车同时从两地相向而行，甲车每小时行60千米，乙车每小时行40千米，3小时后两车相遇。两地相距多少千米？', '300千米', ['200千米', '250千米', '350千米']),
                ('一个圆柱的底面半径是3厘米，高是10厘米，它的体积是多少立方厘米？（π取3.14）', '282.6立方厘米', ['188.4立方厘米', '94.2立方厘米', '314立方厘米']),
                ('某班有50人，今天出勤48人，出勤率是多少？', '96%', ['98%', '94%', '92%']),
            ]
        },
        '初中': {
            '基础': [
                ('解方程：2x + 5 = 13，x = ?', '4', ['3', '5', '6']),
                ('直角三角形的两条直角边分别是3和4，斜边是多少？', '5', ['6', '7', '8']),
                ('计算：(-2)³ = ?', '-8', ['8', '-6', '6']),
            ],
            '中等': [
                ('一元二次方程x² - 5x + 6 = 0的两个根是？', '2和3', ['1和6', '-2和-3', '1和5']),
                ('圆的面积公式是？', 'S=πr²', ['S=2πr', 'S=πd', 'S=4πr²']),
                ('一次函数y=2x+1的图像经过哪个象限？', '一、二、三象限', ['一、二、四象限', '一、三、四象限', '二、三、四象限']),
            ],
            '困难': [
                ('已知等差数列{an}中，a1=2，d=3，求a10', '29', ['27', '30', '32']),
                ('求函数f(x)=x²-4x+3的最小值', '-1', ['0', '1', '3']),
                ('在△ABC中，a=3，b=4，C=90°，求c', '5', ['6', '7', '8']),
            ]
        },
        '高中': {
            '基础': [
                ('函数f(x)=sinx的最小正周期是？', '2π', ['π', 'π/2', '4π']),
                ('向量a=(1,2)，b=(3,4)，则a·b=?', '11', ['10', '12', '14']),
                ('复数z=1+i的模是？', '√2', ['2', '1', '√3']),
            ],
            '中等': [
                ('求函数f(x)=x³-3x的单调递增区间', '(-∞,-1)和(1,+∞)', ['(-1,1)', ['(-∞,1)'], '(0,+∞)']),
                ('在△ABC中，已知a=5，b=7，C=60°，求c', '√39', ['√35', '√40', '√42']),
                ('等差数列{an}中，a3=7，a7=15，求公差d', '2', ['3', '1', '4']),
            ],
            '困难': [
                ('求函数f(x)=lnx/x的最大值', '1/e', ['1', 'e', '2/e']),
                ('已知椭圆x²/25+y²/16=1的离心率是？', '3/5', ['4/5', '3/4', '1/5']),
                ('若sinα+cosα=1/2，则sin2α=?', '-3/4', ['3/4', '-1/2', '1/2']),
            ]
        }
    }
    
    level_templates = question_templates.get(grade_level, question_templates['小学'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'math_q{i+1}',
            'subject': 'math',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_english_questions(grade_level, difficulty, count, question_type):
    """生成英语题目"""
    bank_info = SUBJECT_QUESTION_BANK['english']
    
    question_templates = {
        '小学': {
            '基础': [
                ('What color is the sky?', 'Blue', ['Red', 'Green', 'Yellow']),
                ('How do you say "苹果" in English?', 'Apple', ['Banana', 'Orange', 'Grape']),
                ('She ___ to school every day.', 'goes', ['go', 'going', 'went']),
            ],
            '中等': [
                ('Which word is the past tense of "go"?', 'Went', ['Goes', 'Going', 'Gone']),
                ('What is the plural of "child"?', 'Children', ['Childs', 'Childes', 'Childrens']),
                ('I have ___ apple and ___ banana.', 'an, a', ['a, a', 'an, an', 'a, an']),
            ],
            '困难': [
                ('Which sentence is correct?', 'She is reading a book.', ['She reading a book.', ['She reads a book yesterday.'], 'She is read a book.']),
                ('What does "beautiful" mean?', '美丽的', ['丑陋的', '高的', '矮的']),
                ('Choose the correct answer: ___ you like some tea?', 'Would', ['Do', 'Are', 'Is']),
            ]
        },
        '初中': {
            '基础': [
                ('He ___ to Beijing last summer.', 'went', ['goes', 'has gone', 'is going']),
                ('The book ___ I bought yesterday is very interesting.', 'which', ['who', 'whom', 'whose']),
                ('How many ___ are there in the room?', 'people', ['person', 'peoples', 'persones']),
            ],
            '中等': [
                ('If it ___ tomorrow, we will stay at home.', 'rains', ['will rain', 'rained', 'is raining']),
                ('This is the most beautiful place ___ I have ever visited.', 'that', ['which', 'where', 'what']),
                ('By the time I got to the station, the train ___.', 'had left', ['left', 'has left', 'leaves']),
            ],
            '困难': [
                ('It is suggested that he ___ the meeting.', 'attend', ['attends', 'attended', 'will attend']),
                ('The harder you work, ___ progress you will make.', 'the greater', ['the great', ['greater'], 'great']),
                ('Not until he came back ___ the truth.', 'did I know', ['I knew', ['I did know'], 'knew I']),
            ]
        },
        '高中': {
            '基础': [
                ('The manager demanded that the work ___ before Friday.', 'be finished', ['was finished', 'would be finished', 'finished']),
                ('___ he said at the meeting surprised everyone.', 'What', ['That', 'Which', 'How']),
                ('The reason ___ he was absent is ___ he was ill.', 'why; that', ['that; why', ['why; because'], 'which; that']),
            ],
            '中等': [
                ('Had I known the truth, I ___ differently.', 'would have acted', ['would act', ['acted'], 'had acted']),
                ('The news ___ our team has won the game is exciting.', 'that', ['which', 'what', 'whether']),
                ('It is no use ___ over spilt milk.', 'crying', ['to cry', 'cry', 'cried']),
            ],
            '困难': [
                ('___ is known to all, China is a developing country.', 'As', ['It', 'What', 'Which']),
                ('The old man, ___ abroad for twenty years, is on the way back to his motherland.', 'having worked', ['to work', ['working'], 'worked']),
                ('Not only ___ polluted but ___ crowded.', 'was the city; the streets were', ['the city was; the streets were', ['was the city; were the streets'], 'the city was; were the streets']),
            ]
        }
    }
    
    level_templates = question_templates.get(grade_level, question_templates['小学'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'english_q{i+1}',
            'subject': 'english',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_physics_questions(grade_level, difficulty, count, question_type):
    """生成物理题目"""
    bank_info = SUBJECT_QUESTION_BANK['physics']
    
    question_templates = {
        '初中': {
            '基础': [
                ('声音在空气中的传播速度约为？', '340m/s', ['300m/s', '380m/s', '400m/s']),
                ('光在真空中的传播速度约为？', '3×10⁸m/s', ['3×10⁶m/s', '3×10¹⁰m/s', '3×10⁴m/s']),
                ('水的密度是多少？', '1.0×10³kg/m³', ['1.0×10²kg/m³', '1.0×10⁴kg/m³', '0.9×10³kg/m³']),
            ],
            '中等': [
                ('一个物体从10m高处自由落下，落地速度约为？（g取10m/s²）', '14.1m/s', ['10m/s', '20m/s', '100m/s']),
                ('欧姆定律的公式是？', 'I=U/R', ['U=I/R', 'R=UI', 'P=UI']),
                ('凸透镜对光线有什么作用？', '会聚作用', ['发散作用', '反射作用', '折射作用']),
            ],
            '困难': [
                ('将标有"220V 100W"的灯泡接在110V的电路中，其实际功率是？', '25W', ['50W', '75W', '100W']),
                ('质量为2kg的物体从高5m处自由落下，重力做功是多少？（g取10m/s²）', '100J', ['50J', '200J', '10J']),
                ('一个滑轮组的机械效率为80%，利用它将重为400N的物体提升2m，需要做的总功是？', '1000J', ['800J', '640J', '1250J']),
            ]
        },
        '高中': {
            '基础': [
                ('牛顿第一定律又称为？', '惯性定律', ['加速度定律', '作用力与反作用力定律', '万有引力定律']),
                ('匀速圆周运动的向心加速度公式是？', 'a=v²/r', ['a=v/r', 'a=vr', 'a=r/v']),
                ('电场强度的单位是？', 'N/C', ['J/C', 'V·s', 'Wb/m²']),
            ],
            '中等': [
                ('质量为m的物体在水平力F作用下沿水平面运动，位移为s，力F做的功是？', 'Fs', ['mgs', 'Fs/m', 'F/s']),
                ('单摆的周期公式是？', 'T=2π√(l/g)', ['T=2π√(g/l)', 'T=π√(l/g)', 'T=2π(l/g)']),
                ('法拉第电磁感应定律的公式是？', 'E=nΔΦ/Δt', ['E=BLv', 'E=IR', 'E=F/q']),
            ],
            '困难': [
                ('一质量为m的小球以初速度v₀水平抛出，经过时间t后速度的大小是？', '√(v₀²+(gt)²)', ['v₀+gt', ['gt-v₀'], 'v₀-gt']),
                ('理想变压器原线圈匝数为n₁，副线圈匝数为n₂，则电压比U₁/U₂等于？', 'n₁/n₂', ['n₂/n₁', ['(n₁/n₂)²'], '√(n₁/n₂)']),
                ('光电效应中，光电子的最大初动能与入射光的什么有关？', '频率', ['强度', '照射时间', '速度']),
            ]
        }
    }
    
    if grade_level == '小学':
        grade_level = '初中'
    
    level_templates = question_templates.get(grade_level, question_templates['初中'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'physics_q{i+1}',
            'subject': 'physics',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_chemistry_questions(grade_level, difficulty, count, question_type):
    """生成化学题目"""
    bank_info = SUBJECT_QUESTION_BANK['chemistry']
    
    question_templates = {
        '初中': {
            '基础': [
                ('下列物质属于纯净物的是？', '蒸馏水', ['空气', '海水', '牛奶']),
                ('空气中含量最多的气体是？', '氮气', ['氧气', '二氧化碳', '稀有气体']),
                ('水的化学式是？', 'H₂O', ['H₂O₂', 'HO', 'H₃O']),
            ],
            '中等': [
                ('下列物质在氧气中燃烧，产生大量白烟的是？', '红磷', ['木炭', '硫粉', '铁丝']),
                ('实验室制取二氧化碳的药品是？', '大理石和稀盐酸', ['大理石和稀硫酸', '碳酸钠和稀盐酸', '石灰石和浓硫酸']),
                ('下列物质中，属于氧化物的是？', 'CO₂', ['O₂', 'KMnO₄', 'NaOH']),
            ],
            '困难': [
                ('将50g质量分数为10%的氯化钠溶液稀释成质量分数为5%的溶液，需要加水多少克？', '50g', ['25g', '100g', '75g']),
                ('下列化学方程式书写正确的是？', '2H₂O₂=2H₂O+O₂↑', ['Fe+O₂=FeO₂', ['Mg+O₂=MgO₂'], 'S+O₂=SO₃']),
                ('某物质在空气中完全燃烧生成8.8g二氧化碳和5.4g水，则该物质的化学式可能是？', 'C₂H₆', ['CH₄', ['C₂H₄'], 'C₂H₅OH']),
            ]
        },
        '高中': {
            '基础': [
                ('下列物质中，属于电解质的是？', 'NaCl', ['蔗糖', '酒精', 'CO₂']),
                ('化学反应达到平衡状态的标志是？', '正逆反应速率相等', ['反应停止', ['反应物消耗完'], '各物质浓度相等']),
                ('下列元素中，原子半径最大的是？', 'Na', ['Mg', 'Al', 'Si']),
            ],
            '中等': [
                ('下列反应中，属于氧化还原反应的是？', '2Na+2H₂O=2NaOH+H₂↑', ['CaCO₃=CaO+CO₂↑', ['NaOH+HCl=NaCl+H₂O'], 'CO₂+H₂O=H₂CO₃']),
                ('pH=3的盐酸与pH=11的氢氧化钠溶液等体积混合后，溶液的pH是？', '7', ['大于7', ['小于7'], '无法判断']),
                ('下列物质中，既能与盐酸反应又能与氢氧化钠溶液反应的是？', 'Al(OH)₃', ['Mg(OH)₂', ['Fe(OH)₃'], 'Cu(OH)₂']),
            ],
            '困难': [
                ('在一定条件下，可逆反应N₂+3H₂⇌2NH₃达到平衡。若保持温度和体积不变，向容器中充入少量He，则平衡如何移动？', '不移动', ['向正反应方向移动', '向逆反应方向移动', '无法判断']),
                ('25℃时，将pH=4的盐酸稀释1000倍，溶液的pH约为？', '7', ['7以下接近7', '10', '1']),
                ('已知反应A+B=C+D的焓变ΔH<0，则该反应是？', '放热反应', ['吸热反应', '既不吸热也不放热', '无法判断']),
            ]
        }
    }
    
    if grade_level == '小学':
        grade_level = '初中'
    
    level_templates = question_templates.get(grade_level, question_templates['初中'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'chemistry_q{i+1}',
            'subject': 'chemistry',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_biology_questions(grade_level, difficulty, count, question_type):
    """生成生物题目"""
    bank_info = SUBJECT_QUESTION_BANK['biology']
    
    question_templates = {
        '初中': {
            '基础': [
                ('细胞膜的主要成分是？', '磷脂和蛋白质', ['糖类和脂肪', ['核酸和蛋白质'], '纤维素和果胶']),
                ('植物进行光合作用的场所是？', '叶绿体', ['线粒体', '细胞核', '液泡']),
                ('人体最大的消化腺是？', '肝脏', ['胃', '胰腺', '唾液腺']),
            ],
            '中等': [
                ('DNA的基本组成单位是？', '脱氧核苷酸', ['氨基酸', '核糖核苷酸', '葡萄糖']),
                ('下列哪种是有性生殖？', '种子繁殖', ['扦插', '嫁接', '分根']),
                ('人体血液循环中，流动脉血的血管是？', '主动脉', ['肺动脉', ['上腔静脉'], '下腔静脉']),
            ],
            '困难': [
                ('一对正常的夫妇生了一个白化病的孩子，这对夫妇的基因型是？（用A、a表示）', 'Aa和Aa', ['AA和Aa', 'AA和aa', 'aa和aa']),
                ('下列关于生态系统的说法，正确的是？', '生产者是生态系统的基石', ['消费者是生态系统的核心', ['分解者可有可无'], '非生物的物质和能量不重要']),
                ('显微镜的目镜为10×，物镜为40×，则放大倍数是？', '400倍', ['50倍', '40倍', '100倍']),
            ]
        },
        '高中': {
            '基础': [
                ('细胞呼吸的主要场所是？', '线粒体', ['叶绿体', '核糖体', '内质网']),
                ('基因的本质是？', '有遗传效应的DNA片段', ['蛋白质', ['RNA'], '染色体']),
                ('下列属于原核生物的是？', '细菌', ['病毒', '真菌', '动物']),
            ],
            '中等': [
                ('DNA复制的方式是？', '半保留复制', ['全保留复制', '分散复制', '随机复制']),
                ('下列关于酶的说法，正确的是？', '酶具有高效性和专一性', ['酶的化学本质都是蛋白质', ['酶在高温下都会失活'], '酶只能在细胞内起作用']),
                ('生长素的作用特点是？', '两重性', ['只促进生长', ['只抑制生长'], '无明显特点']),
            ],
            '困难': [
                ('某DNA分子中有1000个碱基对，其中腺嘌呤占20%，则胞嘧啶有多少个？', '600个', ['400个', '200个', '800个']),
                ('下列关于减数分裂的说法，错误的是？', '染色体复制两次，细胞分裂两次', ['染色体复制一次，细胞分裂两次', ['同源染色体联会'], '产生的配子染色体数目减半']),
                ('生态系统的能量流动特点是？', '单向流动、逐级递减', ['循环流动', ['逐级递增'], '双向流动']),
            ]
        }
    }
    
    if grade_level == '小学':
        grade_level = '初中'
    
    level_templates = question_templates.get(grade_level, question_templates['初中'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'biology_q{i+1}',
            'subject': 'biology',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_history_questions(grade_level, difficulty, count, question_type):
    """生成历史题目"""
    bank_info = SUBJECT_QUESTION_BANK['history']
    
    question_templates = {
        '小学': {
            '基础': [
                ('秦始皇统一六国是在哪一年？', '公元前221年', ['公元前202年', '公元前206年', '公元前256年']),
                ('中国的四大发明不包括？', '地动仪', ['造纸术', '印刷术', '火药']),
                ('万里长城始建于哪个朝代？', '秦朝', ['汉朝', '唐朝', '明朝']),
            ],
            '中等': [
                ('唐太宗的名字是？', '李世民', ['李渊', '李隆基', '李治']),
                ('丝绸之路是哪位人物开辟的？', '张骞', ['班超', '卫青', '霍去病']),
                ('《史记》的作者是？', '司马迁', ['班固', '司马光', '陈寿']),
            ],
            '困难': [
                ('"贞观之治"出现在哪个朝代？', '唐朝', ['汉朝', '隋朝', '宋朝']),
                ('中国历史上唯一的女皇帝是？', '武则天', ['慈禧', '吕后', '孝庄']),
                ('郑和下西洋最远到达哪里？', '非洲东海岸', ['地中海', ['红海沿岸'], '好望角']),
            ]
        },
        '初中': {
            '基础': [
                ('鸦片战争爆发于哪一年？', '1840年', ['1842年', '1856年', '1860年']),
                ('辛亥革命的领导者是？', '孙中山', ['毛泽东', '袁世凯', '蒋介石']),
                ('中国共产党成立于哪一年？', '1921年', ['1919年', '1927年', '1949年']),
            ],
            '中等': [
                ('"五四"运动爆发的直接原因是？', '巴黎和会上中国外交失败', ['新文化运动的推动', ['北洋军阀的黑暗统治'], '十月革命的影响']),
                ('新中国成立于哪一年？', '1949年', ['1945年', '1946年', '1950年']),
                ('中国第一部社会主义类型的宪法颁布于哪一年？', '1954年', ['1949年', '1950年', '1956年']),
            ],
            '困难': [
                ('十一届三中全会作出的伟大决策是？', '改革开放', ['以阶级斗争为纲', ['大跃进'], '人民公社化']),
                ('美国独立战争开始的标志是？', '来克星顿枪声', ['波士顿倾茶事件', ['萨拉托加大捷'], '约克镇战役']),
                ('工业革命最早开始于哪个国家？', '英国', ['法国', '德国', '美国']),
            ]
        },
        '高中': {
            '基础': [
                ('西周实行的政治制度是？', '分封制和宗法制', ['郡县制', ['三公九卿制'], '行省制']),
                ('中国古代专制主义中央集权制度达到顶峰的标志是？', '军机处的设立', ['丞相制度的废除', ['内阁的设立'], '科举制的实行']),
                ('第一次世界大战的导火索是？', '萨拉热窝事件', ['凡尔登战役', ['索姆河战役'], '马恩河战役']),
            ],
            '中等': [
                ('中国新民主主义革命开端的标志是？', '五四运动', ['辛亥革命', ['新文化运动'], '中国共产党成立']),
                ('第二次世界大战全面爆发的标志是？', '德国突袭波兰', ['九一八事变', ['珍珠港事件'], '诺曼底登陆']),
                ('罗斯福新政的中心措施是？', '对工业的调整', ['整顿金融', ['调整农业'], '以工代赈']),
            ],
            '困难': [
                ('"一国两制"构想首先成功运用于解决哪个问题？', '香港问题', ['台湾问题', ['澳门问题'], '西藏问题']),
                ('两极格局结束的标志是？', '苏联解体', ['东欧剧变', ['冷战开始'], '华约成立']),
                ('经济全球化趋势加强的根本原因是？', '生产力的发展和科技的进步', ['跨国公司的推动', ['市场经济体制的普遍建立'], '国际金融的发展']),
            ]
        }
    }
    
    level_templates = question_templates.get(grade_level, question_templates['小学'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'history_q{i+1}',
            'subject': 'history',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_geography_questions(grade_level, difficulty, count, question_type):
    """生成地理题目"""
    bank_info = SUBJECT_QUESTION_BANK['geography']
    
    question_templates = {
        '小学': {
            '基础': [
                ('地球自转一周的时间约为？', '24小时', ['12小时', '365天', '12个月']),
                ('世界上最大的海洋是？', '太平洋', ['大西洋', '印度洋', '北冰洋']),
                ('中国的首都是？', '北京', ['上海', '广州', '深圳']),
            ],
            '中等': [
                ('地球的形状是？', '两极稍扁赤道略鼓的不规则球体', ['正球体', '椭球体', '圆形']),
                ('世界上最高的山峰是？', '珠穆朗玛峰', ['乔戈里峰', '干城章嘉峰', '洛子峰']),
                ('我国面积最大的省级行政区是？', '新疆维吾尔自治区', ['西藏自治区', ['内蒙古自治区'], '青海省']),
            ],
            '困难': [
                ('地球公转产生的地理现象是？', '四季变化', ['昼夜更替', ['时间差异'], '日月星辰东升西落']),
                ('世界上最长的河流是？', '尼罗河', ['亚马孙河', '长江', '密西西比河']),
                ('我国人口分布的特点是？', '东多西少', ['西多东少', ['南多北少'], '北多南少']),
            ]
        },
        '初中': {
            '基础': [
                ('世界上面积最大的国家是？', '俄罗斯', ['中国', '美国', '加拿大']),
                ('我国地势的特点是？', '西高东低，呈三级阶梯分布', ['东高西低', ['南高北低'], '中间高四周低']),
                ('台湾岛东岸濒临的海洋是？', '太平洋', ['东海', '南海', '台湾海峡']),
            ],
            '中等': [
                ('长江发源于哪座山脉？', '唐古拉山脉', ['巴颜喀拉山脉', '喜马拉雅山脉', '昆仑山脉']),
                ('下列气候类型中，我国没有的是？', '温带海洋性气候', ['温带季风气候', ['亚热带季风气候'], '温带大陆性气候']),
                ('我国最大的淡水湖是？', '鄱阳湖', ['洞庭湖', '太湖', '青海湖']),
            ],
            '困难': [
                ('夏至日，下列城市白昼最长的是？', '哈尔滨', ['北京', '上海', '广州']),
                ('下列关于我国水资源分布的说法，正确的是？', '南多北少，东多西少', ['北多南少，西多东少', ['夏秋少，冬春多'], '总量丰富，人均充足']),
                ('非洲和南美洲的轮廓吻合可以作为什么学说的证据？', '大陆漂移学说', ['板块构造学说', ['海底扩张学说'], '日心说']),
            ]
        },
        '高中': {
            '基础': [
                ('地球自转的线速度最大的地方是？', '赤道', ['两极', ['回归线'], '极圈']),
                ('下列地质作用中，属于内力作用的是？', '火山喷发', ['风化作用', ['侵蚀作用'], '沉积作用']),
                ('冷锋过境时，通常会出现什么天气？', '大风、降温、雨雪', ['连续性降水', ['晴朗无云'], '台风']),
            ],
            '中等': [
                ('下列关于洋流的说法，正确的是？', '暖流对沿岸气候有增温增湿作用', ['寒流对沿岸气候有增温减湿作用', ['洋流都是从高纬流向低纬'], '洋流不会影响海洋生物']),
                ('城市化的主要标志是？', '城市人口比重上升', ['城市用地规模扩大', ['城市人口增加'], '城市数量增加']),
                ('下列属于可再生资源的是？', '水资源', ['煤炭', '石油', '天然气']),
            ],
            '困难': [
                ('某地位于东经120°，北纬40°，该地位于哪个时区？', '东八区', ['东七区', '东九区', '东六区']),
                ('下列关于自然带分布规律的说法，正确的是？', '从赤道到两极的地域分异以热量为基础', ['从沿海到内陆的地域分异以水分为基础', ['山地的垂直地域分异与海拔无关'], '非地带性没有规律可循']),
                ('环境人口容量的特点是？', '不确定性和相对确定性', ['确定性', ['不变性'], '不可估计性']),
            ]
        }
    }
    
    level_templates = question_templates.get(grade_level, question_templates['小学'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'geography_q{i+1}',
            'subject': 'geography',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_politics_questions(grade_level, difficulty, count, question_type):
    """生成道德与法治/政治题目"""
    bank_info = SUBJECT_QUESTION_BANK['politics']
    
    question_templates = {
        '小学': {
            '基础': [
                ('社会主义核心价值观个人层面的要求是？', '爱国、敬业、诚信、友善', ['富强、民主、文明、和谐', ['自由、平等、公正、法治'], '爱党、爱国、爱人民']),
                ('我国的国旗是？', '五星红旗', ['青天白日旗', '八一军旗', '镰刀锤头旗']),
                ('作为小学生，我们应该怎样对待长辈？', '尊敬孝顺', ['不理不睬', ['顶撞长辈'], '依赖长辈']),
            ],
            '中等': [
                ('我国的根本大法是？', '宪法', ['刑法', '民法', '行政法']),
                ('下列行为中，属于孝敬父母的是？', '帮父母做力所能及的家务', ['什么都听父母的', ['和父母顶嘴'], '只给钱不回家']),
                ('公民的基本权利和义务是由哪部法律规定的？', '宪法', ['民法', ['刑法'], '行政法']),
            ],
            '困难': [
                ('下列关于集体利益和个人利益关系的说法，正确的是？', '集体利益和个人利益在根本上是一致的', ['集体利益和个人利益是完全对立的', ['个人利益高于集体利益'], '集体利益可以代替个人利益']),
                ('当个人利益与集体利益发生冲突时，我们应该？', '以集体利益为重，必要时牺牲个人利益', ['只顾个人利益', ['两败俱伤'], '两边都不管']),
                ('下列行为中，属于正确行使公民权利的是？', '依法举报违法犯罪行为', ['造谣诽谤他人', ['聚众闹事'], '传播谣言']),
            ]
        },
        '初中': {
            '基础': [
                ('我国的国家性质是？', '人民民主专政的社会主义国家', ['资本主义国家', ['封建国家'], '联邦制国家']),
                ('我国最高国家权力机关是？', '全国人民代表大会', ['国务院', ['最高人民法院'], '最高人民检察院']),
                ('依法治国的核心是？', '依宪治国', ['执法必严', ['违法必究'], '有法可依']),
            ],
            '中等': [
                ('我国的基本经济制度是？', '公有制为主体、多种所有制经济共同发展', ['单一公有制', ['完全市场经济'], '计划经济']),
                ('下列关于公民权利和义务的关系，正确的是？', '权利和义务具有一致性', ['可以只享受权利不履行义务', ['可以只履行义务不享受权利'], '权利和义务是对立的']),
                ('我国处理民族关系的基本原则是？', '民族平等、团结、共同繁荣', ['大汉族主义', ['地方民族主义'], '民族同化']),
            ],
            '困难': [
                ('下列关于中国共产党的说法，正确的是？', '中国共产党是中国特色社会主义事业的领导核心', ['中国共产党是执政党，可以不受宪法约束', ['党员可以有特权'], '中国共产党与民主党派是执政党和在野党的关系']),
                ('"三个代表"重要思想的本质是？', '立党为公、执政为民', ['解放思想、实事求是', ['与时俱进'], '科学发展']),
                ('社会主义的根本任务是？', '解放和发展生产力', ['阶级斗争', ['平均分配'], '消灭剥削']),
            ]
        },
        '高中': {
            '基础': [
                ('哲学的基本问题是？', '思维和存在的关系问题', ['物质和运动的关系问题', ['认识和实践的关系问题'], '联系和发展的关系问题']),
                ('下列属于唯物主义观点的是？', '物质决定意识', ['心外无物', ['存在即被感知'], '我思故我在']),
                ('唯物辩证法的实质和核心是？', '对立统一规律', ['质量互变规律', ['否定之否定规律'], '联系和发展']),
            ],
            '中等': [
                ('实践是检验认识真理性的唯一标准，这是因为？', '实践是主观见之于客观的活动', ['实践具有社会历史性', ['实践是认识的来源'], '实践是认识发展的动力']),
                ('我国的政体是？', '人民代表大会制度', ['人民民主专政', ['民族区域自治制度'], '基层群众自治制度']),
                ('矛盾的两个基本属性是？', '同一性和斗争性', ['普遍性和特殊性', ['客观性和主观性'], '绝对性和相对性']),
            ],
            '困难': [
                ('下列关于价值规律的说法，正确的是？', '价值规律是商品经济的基本规律', ['价值规律可以自发调节生产，没有任何弊端', ['价格围绕价值上下波动是对价值规律的否定'], '价值规律只存在于资本主义社会']),
                ('社会存在和社会意识的关系是？', '社会存在决定社会意识，社会意识反作用于社会存在', ['社会意识决定社会存在', ['两者互不影响'], '社会存在和社会意识相互决定']),
                ('我国社会主义初级阶段的基本经济制度的决定因素是？', '社会主义性质和初级阶段国情', ['党的方针政策', ['领导人的意志'], '国际形势']),
            ]
        }
    }
    
    level_templates = question_templates.get(grade_level, question_templates['小学'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'politics_q{i+1}',
            'subject': 'politics',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_science_questions(grade_level, difficulty, count, question_type):
    """生成科学题目"""
    bank_info = SUBJECT_QUESTION_BANK['science']
    
    question_templates = {
        '小学': {
            '基础': [
                ('植物进行光合作用需要什么气体？', '二氧化碳', ['氧气', '氮气', '氢气']),
                ('下列哪种动物是胎生的？', '猫', ['鸡', '鸭', '鱼']),
                ('磁铁有几个磁极？', '2个', ['1个', '3个', '4个']),
            ],
            '中等': [
                ('下列哪种现象是化学变化？', '铁生锈', ['冰融化', '水蒸发', '打碎玻璃']),
                ('声音不能在什么中传播？', '真空', ['空气', '水', '钢铁']),
                ('彩虹是怎么形成的？', '光的色散', ['光的反射', '光的直线传播', '光的干涉']),
            ],
            '困难': [
                ('把一根筷子插入水中，看起来像折断了，这是什么现象？', '光的折射', ['光的反射', '光的色散', '光的散射']),
                ('下列哪种情况摩擦力最大？', '两个粗糙的物体挤压并相对运动', ['两个光滑的物体挤压', ['两个物体不接触'], '两个静止的物体']),
                ('种子萌发需要的条件不包括？', '阳光', ['适宜的温度', '一定的水分', '充足的空气']),
            ]
        }
    }
    
    level_templates = question_templates.get(grade_level, question_templates['小学'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'science_q{i+1}',
            'subject': 'science',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_it_questions(grade_level, difficulty, count, question_type):
    """生成信息技术题目"""
    bank_info = SUBJECT_QUESTION_BANK['information_tech']
    
    question_templates = {
        '小学': {
            '基础': [
                ('计算机中存储容量的基本单位是？', '字节(Byte)', ['位(bit)', '字(Word)', '千字节(KB)']),
                ('下列哪一项是计算机的输入设备？', '键盘', ['显示器', '打印机', '音箱']),
                ('Windows系统中，复制的快捷键是？', 'Ctrl+C', ['Ctrl+V', 'Ctrl+X', 'Ctrl+Z']),
            ],
            '中等': [
                ('计算机网络按照覆盖范围分类，不包括？', '电话网', ['局域网', '城域网', '广域网']),
                ('下列关于计算机病毒的说法，正确的是？', '计算机病毒是一种人为编写的程序', ['计算机病毒是一种细菌', ['计算机病毒不会传染'], '杀毒软件可以杀所有病毒']),
                ('IP地址的作用是？', '标识网络中的计算机', ['标识计算机的品牌', ['标识计算机的速度'], '标识计算机的大小']),
            ],
            '困难': [
                ('下列哪一项不是计算机的硬件？', '操作系统', ['CPU', '内存', '硬盘']),
                ('计算机能直接识别和执行的语言是？', '机器语言', ['汇编语言', ['高级语言'], 'Python语言']),
                ('在Word中，"剪切"的快捷键是？', 'Ctrl+X', ['Ctrl+C', 'Ctrl+V', 'Ctrl+A']),
            ]
        },
        '初中': {
            '基础': [
                ('下列编程语言中，哪个是高级语言？', 'Python', ['机器语言', '汇编语言', '二进制']),
                ('Internet使用的基本协议是？', 'TCP/IP', ['HTTP', 'FTP', 'SMTP']),
                ('计算机的CPU由什么组成？', '运算器和控制器', ['内存和硬盘', ['输入设备和输出设备'], '显示器和键盘']),
            ],
            '中等': [
                ('下列关于算法的说法，错误的是？', '算法必须有输入', ['算法必须有输出', ['算法必须是有限的'], '算法的每一步都必须是确定的']),
                ('HTML是什么？', '超文本标记语言', ['高级编程语言', ['数据库管理系统'], '操作系统']),
                ('下列哪种数据结构是先进先出？', '队列', ['栈', '链表', '树']),
            ],
            '困难': [
                ('冒泡排序的时间复杂度是？', 'O(n²)', ['O(n)', 'O(logn)', 'O(1)']),
                ('下列关于面向对象编程的说法，正确的是？', '面向对象的三大特性是封装、继承、多态', ['面向对象就是函数式编程', ['面向对象只有类没有对象'], '面向对象不支持代码复用']),
                ('数据库中，用来存储和管理数据的基本单位是？', '表', ['字段', '记录', '索引']),
            ]
        },
        '高中': {
            '基础': [
                ('下列关于人工智能的说法，正确的是？', '人工智能是研究、开发用于模拟人类智能的理论和技术', ['人工智能就是机器人', ['人工智能会完全取代人类'], '人工智能就是机器学习']),
                ('数据的三个基本特征是？', '名称、类型、值', ['大小、颜色、形状', ['速度、容量、价格'], '输入、处理、输出']),
                ('下列哪项不是信息技术的发展趋势？', '单一化', ['智能化', '网络化', '多媒体化']),
            ],
            '中等': [
                ('Python中，以下哪个是列表？', '[1,2,3]', ['(1,2,3)', '{"a":1}', '123']),
                ('下列关于网络安全的说法，错误的是？', '只要装了杀毒软件就绝对安全', ['要定期更新系统补丁', ['不要随意打开陌生邮件'], '要设置强密码']),
                ('信息系统的三个基本要素是？', '人、数据、技术', ['硬件、软件、网络', ['输入、处理、输出'], '服务器、客户端、数据库']),
            ],
            '困难': [
                ('深度学习属于人工智能的哪个分支？', '机器学习', ['专家系统', ['自然语言处理'], '计算机视觉']),
                ('下列哪种排序算法的平均时间复杂度最优？', '快速排序 O(nlogn)', ['冒泡排序 O(n²)', ['选择排序 O(n²)'], '插入排序 O(n²)']),
                ('大数据的5V特征不包括？', 'Value（价值）', ['Volume（规模）', 'Velocity（速度）', 'Variety（多样）']),
            ]
        }
    }
    
    level_templates = question_templates.get(grade_level, question_templates['小学'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'it_q{i+1}',
            'subject': 'information_tech',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_general_tech_questions(grade_level, difficulty, count, question_type):
    """生成通用技术题目"""
    bank_info = SUBJECT_QUESTION_BANK['general_tech']
    
    question_templates = {
        '初中': {
            '基础': [
                ('技术设计的一般流程是？', '发现问题→明确问题→方案设计→模型制作→测试优化', ['方案设计→发现问题→模型制作→测试优化', ['明确问题→发现问题→方案设计→测试优化'], '模型制作→方案设计→发现问题→测试优化']),
                ('下列哪种材料属于天然材料？', '木材', ['塑料', '钢铁', '玻璃']),
                ('设计的基本原则不包括？', '最贵原则', ['实用原则', '经济原则', '美观原则']),
            ],
            '中等': [
                ('三视图是指？', '主视图、俯视图、左视图', ['正视图、侧视图、底视图', ['前视图、后视图、上视图'], '主视图、仰视图、右视图']),
                ('下列关于结构的说法，正确的是？', '结构是指事物的各个组成部分之间的有序搭配和排列', ['结构只有建筑才有', ['结构是固定不变的'], '结构只考虑美观']),
                ('工艺是指？', '利用工具和设备对原材料、半成品进行技术处理，使之成为产品的方法', ['一种材料', ['一种工具'], '一种设计']),
            ],
            '困难': [
                ('下列哪一项是控制系统的组成部分？', '控制器、执行器、被控对象、传感器', ['只有控制器', ['只有执行器'], '只有被控对象']),
                ('流程优化的目的是？', '提高效率、降低成本、提高质量', ['只增加成本', ['只浪费时间'], '什么都不改变']),
                ('系统分析的基本原则不包括？', '主观性原则', ['整体性原则', '科学性原则', '综合性原则']),
            ]
        },
        '高中': {
            '基础': [
                ('技术的价值主要体现在哪些方面？', '技术与人、技术与社会、技术与自然', ['只有经济价值', ['只有军事价值'], '只有文化价值']),
                ('下列关于技术创新的说法，正确的是？', '技术创新是技术发展的核心', ['技术创新就是发明新东西', ['技术创新不需要试验'], '技术创新只有科学家才能做']),
                ('设计中的人机关系要实现的目标不包括？', '最昂贵', ['高效', '健康', '舒适']),
            ],
            '中等': [
                ('下列关于结构稳定性的说法，正确的是？', '重心越低，结构越稳定', ['支撑面越小，结构越稳定', ['结构越重越不稳定'], '结构的形状与稳定性无关']),
                ('流程设计的基本因素不包括？', '设计师的心情', ['材料', '工艺', '设备']),
                ('系统的基本特性不包括？', '随意性', ['整体性', '相关性', '目的性']),
            ],
            '困难': [
                ('下列关于闭环控制系统的说法，正确的是？', '闭环控制系统有反馈环节，控制精度高', ['闭环控制系统没有反馈', ['开环控制比闭环控制精度高'], '闭环控制就是手动控制']),
                ('下列不属于专利类型的是？', '技术专利', ['发明专利', '实用新型专利', '外观设计专利']),
                ('技术试验的方法不包括？', '想象试验法', ['优选试验法', '模拟试验法', '虚拟试验法']),
            ]
        }
    }
    
    if grade_level == '小学':
        grade_level = '初中'
    
    level_templates = question_templates.get(grade_level, question_templates['初中'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'gt_q{i+1}',
            'subject': 'general_tech',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_pe_questions(grade_level, difficulty, count, question_type):
    """生成体育题目"""
    bank_info = SUBJECT_QUESTION_BANK['pe']
    
    question_templates = {
        '小学': {
            '基础': [
                ('下列哪种运动属于有氧运动？', '长跑', ['举重', '短跑', '跳高']),
                ('运动前要做什么准备？', '热身运动', ['马上开始剧烈运动', ['先吃饭'], '先睡觉']),
                ('人体运动的三大能源系统不包括？', '消化系统', ['ATP-CP系统', '乳酸能系统', '有氧氧化系统']),
            ],
            '中等': [
                ('篮球比赛中，每队上场几人？', '5人', ['4人', '6人', '7人']),
                ('标准田径场一圈是多少米？', '400米', ['200米', '300米', '500米']),
                ('下列关于运动与健康的说法，正确的是？', '适量运动有益健康', ['运动越多越好', ['运动就不会生病'], '只有运动员才需要运动']),
            ],
            '困难': [
                ('立定跳远主要测试什么素质？', '下肢爆发力', ['耐力', '柔韧性', '灵敏性']),
                ('运动后下列哪种做法是正确的？', '做放松整理运动', ['马上喝冰水', ['立刻坐下休息'], '马上洗澡']),
                ('短跑的起跑姿势采用？', '蹲踞式起跑', ['站立式起跑', ['随便怎么跑'], '坐着起跑']),
            ]
        }
    }
    
    if grade_level != '小学':
        question_templates['初中'] = question_templates['小学']
        question_templates['高中'] = question_templates['小学']
    
    level_templates = question_templates.get(grade_level, question_templates['小学'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'pe_q{i+1}',
            'subject': 'pe',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_music_questions(grade_level, difficulty, count, question_type):
    """生成音乐题目"""
    bank_info = SUBJECT_QUESTION_BANK['music']
    
    question_templates = {
        '小学': {
            '基础': [
                ('五线谱中高音谱号也称为？', 'G谱号', ['F谱号', 'C谱号', 'D谱号']),
                ('下列哪种乐器是弦乐器？', '小提琴', ['钢琴', '笛子', '鼓']),
                ('简谱中"1"对应的音名是？', 'do', ['re', 'mi', 'fa']),
            ],
            '中等': [
                ('《义勇军进行曲》的曲作者是？', '聂耳', ['冼星海', '田汉', '贺绿汀']),
                ('下列什么是4/4拍的含义？', '以四分音符为一拍，每小节四拍', ['以四分音符为一拍，每小节两拍', ['以八分音符为一拍，每小节四拍'], '以二分音符为一拍，每小节四拍']),
                ('《黄河大合唱》的作曲者是？', '冼星海', ['聂耳', '田汉', '黄自']),
            ],
            '困难': [
                ('下列关于民歌的说法，正确的是？', '民歌是劳动人民在生活和劳动中自己创作、自己演唱的歌曲', ['民歌只有一种体裁', ['民歌都是作曲家写的'], '民歌没有地方特色']),
                ('贝多芬是哪国作曲家？', '德国', ['奥地利', '意大利', '法国']),
                ('下列哪种是中国传统乐器？', '古筝', ['钢琴', '小提琴', '吉他']),
            ]
        }
    }
    
    if grade_level != '小学':
        question_templates['初中'] = question_templates['小学']
        question_templates['高中'] = question_templates['小学']
    
    level_templates = question_templates.get(grade_level, question_templates['小学'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'music_q{i+1}',
            'subject': 'music',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_art_questions(grade_level, difficulty, count, question_type):
    """生成美术题目"""
    bank_info = SUBJECT_QUESTION_BANK['art']
    
    question_templates = {
        '小学': {
            '基础': [
                ('三原色指的是？', '红、黄、蓝', ['红、绿、蓝', ['红、橙、黄'], '红、白、黑']),
                ('下列哪种颜色是冷色？', '蓝色', ['红色', '橙色', '黄色']),
                ('中国画的主要工具不包括？', '油画棒', ['毛笔', '墨', '宣纸']),
            ],
            '中等': [
                ('《蒙娜丽莎》的作者是？', '达芬奇', ['梵高', '毕加索', '莫奈']),
                ('透视的基本规律是？', '近大远小', ['近小远大', ['远近一样大'], '没有规律']),
                ('下列哪种是中国画的题材？', '花鸟画', ['肖像画', ['风景画'], '静物画']),
            ],
            '困难': [
                ('梵高是哪国画家？', '荷兰', ['法国', '意大利', '西班牙']),
                ('下列关于素描的说法，正确的是？', '素描是一切绘画的基础', ['素描只能用铅笔画', ['素描不能表现光影'], '素描就是简单画几笔']),
                ('色彩的三要素是？', '色相、明度、纯度', ['红、黄、蓝', ['暖色、冷色、中性色'], '对比、调和、统一']),
            ]
        }
    }
    
    if grade_level != '小学':
        question_templates['初中'] = question_templates['小学']
        question_templates['高中'] = question_templates['小学']
    
    level_templates = question_templates.get(grade_level, question_templates['小学'])
    diff_templates = level_templates.get(difficulty, level_templates['中等'])
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        template = random.choice(diff_templates)
        question = {
            'id': f'art_q{i+1}',
            'subject': 'art',
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': template[0],
            'answer': template[1],
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题' and len(template) > 2:
            options = [template[1]] + template[2]
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


def generate_k12_fallback_questions(subject, grade_level, difficulty, count, question_type):
    """生成K12备用题目（当学科没有专门的生成函数时）"""
    bank_info = SUBJECT_QUESTION_BANK.get(subject, {'name': '未知学科', 'chapters': [{'name': '通用'}]})
    
    question_bases = [
        f'下列关于{bank_info["name"]}的说法，正确的是？',
        f'{bank_info["name"]}的基本概念是什么？',
        f'{bank_info["name"]}的主要特点包括？',
        f'学习{bank_info["name"]}的重要意义是？',
        f'下列哪项属于{bank_info["name"]}的研究内容？',
    ]
    
    questions = []
    chapters = [ch['name'] for ch in bank_info['chapters']]
    
    for i in range(count):
        content = random.choice(question_bases)
        question = {
            'id': f'{subject}_q{i+1}',
            'subject': subject,
            'grade': grade_level,
            'type': question_type,
            'difficulty': difficulty,
            'content': f'【{grade_level}{difficulty}难度】{content}',
            'answer': '正确答案（AI生成）',
            'chapter': chapters[i % len(chapters)]
        }
        if question_type == '选择题':
            options = ['正确选项', '干扰选项A', '干扰选项B', '干扰选项C']
            random.shuffle(options)
            question['options'] = [f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)]
        questions.append(question)
    
    return questions


@k12_bp.route('/api/k12/questions/generate', methods=['POST'])
@require_login
@require_k12_role
def api_generate_questions():
    """根据年级和学科生成题目（AI智能出题）"""
    data = request.get_json() or {}
    
    subject = data.get('subject', '')
    grade = data.get('grade', session.get('grade', ''))
    difficulty = data.get('difficulty', '中等')
    count = data.get('count', 10)
    question_type = data.get('question_type', '选择题')
    
    if subject not in SUBJECT_QUESTION_BANK:
        return jsonify({'success': False, 'error': '无效的学科', 'code': 'INVALID_SUBJECT'})
    
    if grade not in K12_GRADES:
        return jsonify({'success': False, 'error': '无效的年级', 'code': 'INVALID_GRADE'})
    
    count = min(count, 50)
    
    try:
        questions = generate_k12_questions(subject, grade, difficulty, count, question_type)
        
        return jsonify({
            'success': True,
            'data': {
                'questions': questions,
                'generated_count': len(questions),
                'subject': subject,
                'subject_name': SUBJECT_QUESTION_BANK[subject]['name'],
                'grade': grade,
                'difficulty': difficulty,
                'is_ai_generated': True
            }
        })
    except Exception as e:
        logger.error(f"生成K12题目失败: {e}")
        return jsonify({
            'success': False,
            'error': f'题目生成失败: {str(e)}',
            'code': 'GENERATION_FAILED'
        }), 500


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
