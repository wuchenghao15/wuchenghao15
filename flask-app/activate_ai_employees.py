import sqlite3
import uuid
import time
from datetime import datetime

DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

def get_all_employees(cursor):
    """获取所有AI员工"""
    cursor.execute("SELECT id, name, employee_code, capabilities, specialties FROM ai_employees ORDER BY id")
    return cursor.fetchall()

def get_existing_skill_employees(cursor):
    """获取已有specialized_skills的员工ID"""
    cursor.execute("SELECT DISTINCT employee_id FROM ai_specialized_skills")
    return {row[0] for row in cursor.fetchall()}

def get_existing_module_employees(cursor):
    """获取已有ai_employee_module的员工ID"""
    cursor.execute("SELECT DISTINCT employee_id FROM ai_employee_module")
    return {row[0] for row in cursor.fetchall()}

def activate_employee(cursor, emp_id, name, code):
    """激活AI员工"""
    now = datetime.now().isoformat()
    cursor.execute("""
        UPDATE ai_employees
        SET status = 'active',
            is_enabled = 1,
            system_adapted = 1,
            last_adapted_at = ?,
            updated_at = ?,
            last_learning = ?
        WHERE id = ?
    """, (now, now, now, emp_id))
    print(f'  ✅ 激活员工: [{emp_id}] {name} ({code})')

def add_specialized_skills(cursor, emp_id, code, capabilities, specialties):
    """为员工添加专业技能"""
    now = datetime.now().isoformat()
    skills = []

    # 从capabilities中提取技能
    if capabilities:
        try:
            caps = eval(capabilities) if isinstance(capabilities, str) else capabilities
            for i, cap in enumerate(caps[:3]):  # 取前3个技能
                skill_id = f"{code}_技能{i+1}"
                skills.append((
                    skill_id, emp_id, cap, 2, 80.0 + (i * 2), now, now, now
                ))
        except:
            pass

    # 从specialties中提取技能
    if specialties:
        try:
            specs = eval(specialties) if isinstance(specialties, str) else specialties
            for i, spec in enumerate(specs[:3]):  # 取前3个技能
                skill_id = f"{code}_专长{i+1}"
                skills.append((
                    skill_id, emp_id, spec, 2, 75.0 + (i * 3), now, now, now
                ))
        except:
            pass

    # 插入技能
    for skill in skills:
        try:
            cursor.execute("""
                INSERT INTO ai_specialized_skills
                (skill_id, employee_id, skill_name, skill_level, proficiency, last_practice, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, skill)
            print(f'    📚 添加技能: {skill[2]} (熟练度: {skill[4]:.1f}%)')
        except sqlite3.IntegrityError:
            pass  # 技能已存在

def add_module_assignment(cursor, emp_id, name, code):
    """为员工添加模块分配"""
    # 根据员工名称确定模块
    module_mapping = {
        'CDN': ('CDN_ICON', '资源管理员'),
        '代码修复': ('CODE_FIX', '修复专家'),
        '代码优化': ('CODE_FIX', '优化专家'),
        '通知': ('NOTIFICATION', '通知专家'),
        '按钮': ('NOTIFICATION', '按钮功能专家'),
        '高考': ('EXAM', '考试专家'),
        '中考': ('EXAM', '考试专家'),
        '日语': ('JAPANESE', '日语专家'),
        '新概念': ('ENGLISH', '英语专家'),
        '新东方': ('ENGLISH', '英语专家'),
        '雅思': ('ENGLISH', '英语专家'),
        '自主招生': ('ADMISSION', '招生专家'),
        '专科': ('ADMISSION', '招生专家'),
        '系统管理': ('SYS_ADMIN', '系统管理员'),
        '硬件管理': ('HARDWARE', '硬件管理员'),
        '考试系统': ('EXAM_MGR', '考试管理员'),
        '报表': ('REPORT', '报表管理员'),
        '安全': ('SECURITY', '安全管理员'),
        '数据库': ('DB_MGR', '数据库管理员'),
        '备份': ('BACKUP', '备份管理员'),
        '监控': ('MONITOR', '监控管理员'),
        '出题': ('QUESTION', '出题专家'),
        '练习题': ('QUESTION', '练习题专家'),
        '选择题': ('CHOICE', '选项专家'),
        '语言': ('LANGUAGE', '语言专家'),
        '单选题': ('CHOICE', '单选题专家'),
        '日本试卷': ('JAPANESE', '日语专家'),
        '新加坡': ('SINGAPORE', '新加坡考试专家'),
        '前端': ('FRONTEND', '前端专家'),
        '数据安全': ('SECURITY', '安全管理员'),
        '摸底': ('EXAM', '考试专家'),
        '音频': ('AUDIO', '音频专家'),
        '讲解': ('EXPLAIN', '讲解专家'),
        '听力': ('AUDIO', '音频专家'),
    }

    module_id = 'GENERAL'
    role = name

    for keyword, (mod, rl) in module_mapping.items():
        if keyword in name:
            module_id = mod
            role = rl
            break

    now = datetime.now().isoformat()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO ai_employee_module
            (employee_id, module_id, role, status, created_at)
            VALUES (?, ?, ?, 'active', ?)
        """, (emp_id, module_id, role, now))
        print(f'    📦 分配模块: {module_id} ({role})')
    except Exception as e:
        print(f'    ⚠️ 模块分配失败: {e}')

def log_activation(cursor, emp_id, name, code):
    """记录激活日志"""
    now = int(time.time())
    cursor.execute("""
        INSERT INTO ai_employee_tasks
        (employee_code, task_type, task_description, status, result, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        code,
        'activation',
        f'激活AI员工: {name}',
        'completed',
        f'{{"status": "completed", "employee_id": {emp_id}, "timestamp": "{datetime.now().isoformat()}"}}',
        datetime.now().isoformat()
    ))

def main():
    print('=' * 70)
    print('[AI员工激活] 开始激活所有AI员工...')
    print('=' * 70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 获取所有员工
    employees = get_all_employees(cursor)
    existing_skills = get_existing_skill_employees(cursor)
    existing_modules = get_existing_module_employees(cursor)

    print(f'\n[统计] 总员工数: {len(employees)}')
    print(f'[统计] 已有技能的员工: {len(existing_skills)} 个')
    print(f'[统计] 已分配模块的员工: {len(existing_modules)} 个')
    print()

    activated_count = 0
    skills_added = 0
    modules_added = 0

    for emp_id, name, code, capabilities, specialties in employees:
        print(f'\n[{emp_id}] {name} ({code})')

        # 1. 激活员工
        cursor.execute("SELECT status, is_enabled FROM ai_employees WHERE id = ?", (emp_id,))
        status, is_enabled = cursor.fetchone()
        if status != 'active' or not is_enabled:
            activate_employee(cursor, emp_id, name, code)
            activated_count += 1
        else:
            print(f'  ℹ️  员工已激活')

        # 2. 添加专业技能（如果缺失）
        if emp_id not in existing_skills:
            print(f'  📚 添加专业技能...')
            add_specialized_skills(cursor, emp_id, code, capabilities, specialties)
            skills_added += 1

        # 3. 添加模块分配（如果缺失）
        if emp_id not in existing_modules:
            print(f'  📦 添加模块分配...')
            add_module_assignment(cursor, emp_id, name, code)
            modules_added += 1

        # 4. 记录激活日志
        log_activation(cursor, emp_id, name, code)

    # 提交事务
    conn.commit()

    # 输出汇总
    print('\n' + '=' * 70)
    print('[激活完成]')
    print(f'  - 新激活员工: {activated_count} 个')
    print(f'  - 新增技能组: {skills_added} 个员工')
    print(f'  - 新增模块分配: {modules_added} 个员工')
    print(f'  - 总员工数: {len(employees)} 个')
    print('=' * 70)

    # 验证结果
    print('\n[验证] 重新统计...')
    cursor.execute("SELECT COUNT(*) FROM ai_employees WHERE status = 'active' AND is_enabled = 1")
    active_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT employee_id) FROM ai_specialized_skills")
    skill_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT employee_id) FROM ai_employee_module")
    module_count = cursor.fetchone()[0]

    print(f'  - 活跃员工: {active_count} / {len(employees)}')
    print(f'  - 有技能的员工: {skill_count} / {len(employees)}')
    print(f'  - 有模块的员工: {module_count} / {len(employees)}')

    conn.close()
    print('\n✅ 所有AI员工已成功激活！')

if __name__ == '__main__':
    main()