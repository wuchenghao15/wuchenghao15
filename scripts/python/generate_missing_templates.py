import re
from pathlib import Path

app_file = 'app.py'
templates_dir = Path('templates')

with open(app_file, 'r', encoding='utf-8') as f:
    content = f.read()

matches = re.findall(r"render_template\('([^']+)',?", content)
templates = set()
for m in matches:
    templates.add(m)

missing = []
for t in sorted(templates):
    if not (templates_dir / t).exists():
        missing.append(t)

logger.info(f'总模板数: {len(templates)}')
logger.info(f'缺失模板数: {len(missing)}')

template_base = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 16px;
            padding: 40px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 500px;
            width: 100%;
        }}
        .icon {{
            font-size: 64px;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #333;
            font-size: 24px;
            margin-bottom: 10px;
        }}
        p {{
            color: #666;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        .path {{
            background: #f5f5f5;
            padding: 10px 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 12px;
            color: #888;
            margin-bottom: 20px;
        }}
        .btn {{
            display: inline-block;
            padding: 12px 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
            margin: 5px;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }}
        .btn-secondary {{
            background: #f0f0f0;
            color: #666;
        }}
        .btn-secondary:hover {{
            background: #e0e0e0;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">{icon}</div>
        <h1>{title}</h1>
        <p>{description}</p>
        <div class="path">{path}</div>
        <a href="/" class="btn">返回首页</a>
        {extra_buttons}
    </div>
</body>
</html>"""

templates_info = {
    '403.html': {'title': '访问被拒绝', 'icon': '🚫', 'description': '您没有访问此页面的权限，请联系管理员。',
    'extra': '<a href="/auth/login" class="btn btn-secondary">重新登录</a>'},
    'admin_app/ai_exam_composer.html': {'title': 'AI试卷合成', 'icon': '📝', 'description': 'AI智能试卷合成功能页面。', 'extra': ''},
    'admin_app/ai_intelligent_center.html': {'title': 'AI智能中心', 'icon': '🧠', 'description': 'AI智能功能管理中心。', 'extra': ''},
    'admin_app/ai_question_generator.html': {'title': 'AI题目生成', 'icon': '🤖', 'description': 'AI题目生成器页面。', 'extra': ''},
    'admin_app/ai_study_path.html': {'title': 'AI学习路径', 'icon': '🗺️', 'description': 'AI智能学习路径规划。', 'extra': ''},
    'admin_app/ai_tutor.html': {'title': 'AI辅导', 'icon': '👨‍🏫', 'description': 'AI智能辅导功能页面。', 'extra': ''},
    'admin_app/arduino_ide.html': {'title': 'Arduino IDE', 'icon': '🔧', 'description': 'Arduino编程开发环境。', 'extra': ''},
    'admin_app/enhanced_settings.html': {'title': '增强设置', 'icon': '⚙️', 'description': '系统增强设置页面。', 'extra': ''},
    'admin_app/health_details.html': {'title': '健康详情', 'icon': '❤️', 'description': '系统健康检查详情。', 'extra': ''},
    'admin_app/health_monitor.html': {'title': '健康监控', 'icon': '📊', 'description': '系统健康监控页面。', 'extra': ''},
    'admin_app/security_dashboard.html': {'title': '安全仪表板', 'icon': '🔒', 'description': '系统安全监控仪表板。', 'extra': ''},
    'admin_app/settings.html': {'title': '系统设置', 'icon': '⚙️', 'description': '系统设置页面。', 'extra': ''},
    'admin_app/visualization.html': {'title': '数据可视化', 'icon': '📈', 'description': '数据可视化展示页面。', 'extra': ''},
    'admin_app/wrong_book.html': {'title': '错题本管理', 'icon': '📕', 'description': '错题本管理页面。', 'extra': ''},
    'admin_center.html': {'title': '管理中心', 'icon': '🏢', 'description': '系统管理中心。', 'extra': ''},
    'adult_placement_test.html': {'title': '成人分级测试', 'icon': '📋', 'description': '成人英语分级测试。', 'extra': ''},
    'ai_auto_expand.html': {'title': 'AI自动扩展', 'icon': '🌱', 'description': 'AI自动扩展功能页面。', 'extra': ''},
    'backup_manager.html': {'title': '备份管理', 'icon': '💾', 'description': '系统备份管理页面。', 'extra': ''},
    'custom_practice.html': {'title': '自定义练习', 'icon': '🎯', 'description': '自定义练习页面。', 'extra': ''},
    'daily_practice.html': {'title': '每日练习', 'icon': '📅', 'description': '每日练习页面。', 'extra': ''},
    'error.html': {'title': '系统错误', 'icon': '❌', 'description': '系统发生错误，请稍后重试。', 'extra': ''},
    'exam_center.html': {'title': '考试中心', 'icon': '📝', 'description': '考试中心页面。', 'extra': ''},
    'exam_page.html': {'title': '考试页面', 'icon': '📋', 'description': '在线考试页面。', 'extra': ''},
    'exam_start.html': {'title': '开始考试', 'icon': '🚀', 'description': '考试开始页面。', 'extra': ''},
    'exam_system_exams.html': {'title': '考试列表', 'icon': '📚', 'description': '考试系统考试列表。', 'extra': ''},
    'exam_system_tests.html': {'title': '测试列表', 'icon': '📝', 'description': '考试系统测试列表。', 'extra': ''},
    'github_sync.html': {'title': 'GitHub同步', 'icon': '🌐', 'description': 'GitHub同步管理页面。', 'extra': ''},
    'layout_manager.html': {'title': '布局管理', 'icon': '🎨', 'description': '系统布局管理页面。', 'extra': ''},
    'login.html': {'title': '用户登录', 'icon': '🔐', 'description': '用户登录页面。', 'extra': ''},
    'logout.html': {'title': '退出登录', 'icon': '👋', 'description': '您已成功退出登录。', 'extra': ''},
    'major_placement_test.html': {'title': '专业分级测试', 'icon': '📋', 'description': '专业分级测试页面。', 'extra': ''},
    'mobile/ai_learning_h5.html': {'title': 'AI学习', 'icon': '🤖', 'description': '移动端AI学习页面。', 'extra': ''},
    'mobile/device_management.html': {'title': '设备管理', 'icon': '📱', 'description': '移动端设备管理页面。', 'extra': ''},
    'mobile/exam.html': {'title': '考试', 'icon': '📝', 'description': '移动端考试页面。', 'extra': ''},
    'mobile/home.html': {'title': '首页', 'icon': '🏠', 'description': '移动端首页。', 'extra': ''},
    'mobile/profile.html': {'title': '个人中心', 'icon': '👤', 'description': '移动端个人中心。', 'extra': ''},
    'mobile/training.html': {'title': '训练', 'icon': '💪', 'description': '移动端训练页面。', 'extra': ''},
    'placement_test.html': {'title': '分级测试', 'icon': '📋', 'description': '英语分级测试页面。', 'extra': ''},
    'placement_test_take.html': {'title': '开始测试', 'icon': '🚀', 'description': '开始分级测试。', 'extra': ''},
    'privacy.html': {'title': '隐私政策', 'icon': '🔒', 'description': '隐私政策页面。', 'extra': ''},
    'random_challenge.html': {'title': '随机挑战', 'icon': '🎲', 'description': '随机挑战页面。', 'extra': ''},
    'redeem_store.html': {'title': '积分兑换', 'icon': '🎁', 'description': '积分兑换商店。', 'extra': ''},
    'reset_password.html': {'title': '重置密码', 'icon': '🔑', 'description': '密码重置页面。', 'extra': ''},
    'set_grade.html': {'title': '设置年级', 'icon': '📚', 'description': '设置学生年级。', 'extra': ''},
    'student_portal.html': {'title': '学生门户', 'icon': '🎓', 'description': '学生门户页面。', 'extra': ''},
    'super_admin_dashboard.html': {'title': '超级管理员', 'icon': '👑', 'description': '超级管理员控制台。', 'extra': ''},
    'system_upgrade_center.html': {'title': '系统升级', 'icon': '⬆️', 'description': '系统升级中心。', 'extra': ''},
    'terms.html': {'title': '用户协议', 'icon': '📄', 'description': '用户协议页面。', 'extra': ''},
    'wrong_book.html': {'title': '错题本', 'icon': '📕', 'description': '个人错题本页面。', 'extra': ''},
}

for t in missing:
    info = templates_info.get(t, {'title': t.replace('/', ' > '), 'icon': '📄', 'description': f'页面开发中: {t}',
    'extra': ''})
    template_path = templates_dir / t
    template_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = template_base.format(
        title=info['title'],
        icon=info['icon'],
        description=info['description'],
        path=f'/templates/{t}',
        extra_buttons=info['extra']
    )
    
    template_path.write_text(content, encoding='utf-8')
    logger.info(f'创建: {t}')

logger.info(f'已创建 {len(missing)} 个模板文件')


