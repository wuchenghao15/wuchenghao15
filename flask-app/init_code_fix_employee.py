#!/usr/bin/env python3
"""
代码错误修复专家AI员工初始化脚本
创建一个专门负责修复代码错误的AI员工
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

def init_code_fix_employee():
    """初始化代码错误修复专家AI员工"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("正在创建代码错误修复专家AI员工...")
    
    # 检查是否已有该员工
    cursor.execute("SELECT id FROM ai_employees WHERE employee_code = 'AI_CODE_FIXER_001'")
    existing = cursor.fetchone()
    
    if existing:
        print("✓ 代码错误修复专家AI员工已存在，跳过创建")
        conn.close()
        return
    
    # 插入AI员工记录（匹配实际表结构）
    cursor.execute('''
        INSERT INTO ai_employees 
        (name, employee_code, description, capabilities, specialties, status, accuracy, 
         total_tasks, successful_fixes, failed_fixes, learning_rate, knowledge_base_size,
         last_training, model_version, is_enabled, priority, max_concurrent_tasks, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        '代码错误修复专家',  # name
        'AI_CODE_FIXER_001',  # employee_code
        '专门负责检测和修复各类代码错误的AI员工，精通Python、JavaScript、Flask等语言',  # description
        '''1. 自动检测和修复代码错误
2. 分析错误堆栈跟踪并定位问题根源
3. 修复语法错误和运行时异常
4. 解决数据库连接和查询问题
5. 修复模板渲染错误
6. 解决路由和蓝图注册问题
7. 修复API响应和JSON格式问题
8. 解决前端交互和事件绑定问题
9. 优化代码性能和内存泄漏
10. 提供错误预防建议''',  # capabilities
        'Python, JavaScript, HTML, CSS, Flask, SQLAlchemy, Jinja2, API设计, 数据库, 调试, 错误处理',  # specialties
        'active',  # status
        99.8,  # accuracy
        0,  # total_tasks
        0,  # successful_fixes
        0,  # failed_fixes
        0.001,  # learning_rate
        0,  # knowledge_base_size
        datetime.now().isoformat(),  # last_training
        '1.0.0',  # model_version
        1,  # is_enabled
        10,  # priority (high = 10)
        10,  # max_concurrent_tasks
        datetime.now().isoformat()  # created_at
    ))
    
    # 获取新插入的员工ID
    employee_id = cursor.lastrowid
    
    # 检查并创建 ai_error_types 表（如果不存在）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_error_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_code TEXT NOT NULL UNIQUE,
            error_name TEXT NOT NULL,
            description TEXT,
            severity TEXT,
            avg_fix_time REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 插入错误类型记录
    error_types = [
        ('SYNTAX_ERROR', '语法错误', 'Python、JavaScript、HTML、CSS语法错误', 'high', 0.5),
        ('RUNTIME_ERROR', '运行时错误', '代码执行过程中的错误', 'high', 1.0),
        ('DATABASE_ERROR', '数据库错误', 'SQL查询、连接、ORM错误', 'high', 1.5),
        ('TEMPLATE_ERROR', '模板渲染错误', 'Jinja2模板错误、变量未定义', 'high', 1.0),
        ('ROUTE_ERROR', '路由错误', '路由未注册、蓝图冲突', 'high', 1.0),
        ('API_ERROR', 'API错误', 'REST API响应格式、认证问题', 'medium', 1.0),
        ('FRONTEND_ERROR', '前端错误', 'JavaScript异常、DOM操作错误', 'medium', 1.0),
        ('PERFORMANCE_ERROR', '性能问题', '内存泄漏、查询慢、阻塞', 'medium', 2.0),
    ]
    
    for error_type in error_types:
        try:
            cursor.execute('''
                INSERT INTO ai_error_types 
                (error_code, error_name, description, severity, avg_fix_time)
                VALUES (?, ?, ?, ?, ?)
            ''', error_type)
        except sqlite3.IntegrityError:
            # 如果已存在，跳过
            pass
    
    conn.commit()
    print(f"✓ 代码错误修复专家AI员工创建成功 (ID: {employee_id})")
    print(f"✓ 已添加 {len(error_types)} 种错误类型")
    
    # 创建专属工具表（如果不存在）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS code_fix_tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_code TEXT NOT NULL UNIQUE,
            tool_name TEXT NOT NULL,
            description TEXT,
            languages TEXT,
            capabilities TEXT,
            usage_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 100.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 插入工具记录
    tools = [
        ('PYLINT', 'Python代码检查', '使用pylint进行Python代码静态分析', 
         'Python', '语法检查、代码风格、潜在错误'),
        ('ESLINT', 'JavaScript代码检查', '使用ESLint进行JavaScript代码检查',
         'JavaScript', '语法检查、最佳实践、安全问题'),
        ('SQLCHECK', 'SQL语句检查', '检查SQL查询的正确性和性能',
         'SQL', '查询优化、注入防护、索引建议'),
        ('JINJA_ANALYZER', 'Jinja2模板分析', '分析Jinja2模板语法和变量',
         'HTML/Jinja2', '模板语法、变量引用、继承结构'),
        ('STACKTRACE', '堆栈跟踪分析', '分析Python/JS错误堆栈',
         'Python/JavaScript', '错误定位、原因分析、修复建议'),
        ('DB_PROFILER', '数据库分析', '分析数据库查询问题',
         'SQL', '查询分析、连接池、性能优化'),
    ]
    
    for tool in tools:
        try:
            cursor.execute('''
                INSERT INTO code_fix_tools 
                (tool_code, tool_name, description, languages, capabilities, usage_count, success_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (*tool, 0, 100.0))
        except sqlite3.IntegrityError:
            # 如果已存在，跳过
            pass
    
    conn.commit()
    print(f"✓ 已添加 {len(tools)} 个专属工具")
    
    # 创建修复历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS code_fix_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            error_type TEXT,
            error_message TEXT,
            fix_description TEXT,
            status TEXT DEFAULT 'fixed',
            fixed_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fixed_by) REFERENCES ai_employees(id)
        )
    ''')
    
    conn.commit()
    print("✓ 代码修复历史表创建完成")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ 代码错误修复专家AI员工初始化完成！")
    print("=" * 60)
    print("\n员工信息：")
    print("  - 员工代码: AI_CODE_FIXER_001")
    print("  - 员工名称: 代码错误修复专家")
    print("  - 角色: code_fixer")
    print("  - 准确率: 99.8%")
    print("  - 状态: active")
    print("  - 优先级: high")
    print("  - 最大并发任务: 10")
    print("\n专长领域：")
    print("  - Python, JavaScript, HTML, CSS")
    print("  - Flask, SQLAlchemy, Jinja2")
    print("  - API设计, 数据库, 调试")
    print("  - 错误处理, 性能优化")
    print("\n错误处理类型：")
    for error_type in error_types:
        print(f"  - {error_type[0]}: {error_type[1]}")
    print("\n专属工具：")
    for tool in tools:
        print(f"  - {tool[0]}: {tool[1]}")
    print("\n下一步：")
    print("  1. AI员工已添加到数据库")
    print("  2. 可以通过API调用该AI员工进行代码修复")
    print("  3. 所有代码错误将自动记录到修复历史")

if __name__ == "__main__":
    print("=" * 60)
    print("代码错误修复专家AI员工初始化")
    print("=" * 60)
    print()
    init_code_fix_employee()
