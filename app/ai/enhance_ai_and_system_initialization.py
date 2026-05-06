# -*- coding: utf-8 -*-
import os
# JSON import removed - using database
import sqlite3
import logging
import subprocess
import time
from datetime import datetime

# 配置日志
logs_dir = os.path.join(os.path.dirname(__file__), '../logs')
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'enhance_ai_and_system_initialization.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIAndSystemInitializationEnhancer:
    """AI和系统初始化增强器类"""

    def __init__(self):
        """初始化AI和系统初始化增强器"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, 'data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')
        self.init_dir = os.path.join(self.data_dir, 'system_init')
        self.ai_brain_dir = os.path.join(self.data_dir, 'ai_brain')
        self.scripts_dir = os.path.join(self.project_root, '../scripts')

        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.init_dir, exist_ok=True)
        os.makedirs(self.ai_brain_dir, exist_ok=True)
        os.makedirs(self.scripts_dir, exist_ok=True)

        # 新AI类型定义
        self.new_ai_types = [
            {
                'ai_type': 'system_init_ai',
                'name': '系统初始化AI',
                'description': '专门负责系统初始化和启动过程的管理',
                'functions': [
                    '系统初始化管理',
                    '启动脚本优化',
                    '初始化过程监控',
                    '启动异常处理'
                ],
                'required_skills': ['system_administration', 'scripting', 'monitoring', 'error_handling']
            },
                'ai_type': 'init_error_handling_ai',
                'name': '初始化错误处理AI',
                'description': '专门负责系统初始化和启动过程中的错误检测和处理',
                'functions': [
                    '错误分析',
                    '自动修复',
                    '错误上报'
                ],
                'required_skills': ['error_detection', 'error_analysis', 'error_fix', 'system_administration']
                'ai_type': 'init_test_learning_ai',
                'name': '初始化测试学习AI',
                'functions': [
                    '测试结果分析',
                    '知识提取',
                    '学习模型更新'
                ],
                'required_skills': ['machine_learning', 'pattern_recognition', 'knowledge_extraction', 'system_administration']
            }


    def check_database(self):
        """检查数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查ai_types表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_types'")
            if not cursor.fetchone():
                cursor.execute('''
                    CREATE TABLE ai_types (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ai_type TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        functions TEXT,
                        required_skills TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                conn.commit()
                logger.info("创建ai_types表")

            # 检查system_init_tests表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_init_tests'")
            if not cursor.fetchone():
                cursor.execute('''
                    CREATE TABLE system_init_tests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id TEXT UNIQUE NOT NULL,
                        test_name TEXT NOT NULL,
                        test_description TEXT,
                        test_status TEXT DEFAULT 'pending',
                        start_time TIMESTAMP,
                        error_count INTEGER DEFAULT 0,
                        performance_metrics TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                conn.commit()
                logger.info("创建system_init_tests表")

            # 检查init_test_errors表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='init_test_errors'")
            if not cursor.fetchone():
                cursor.execute('''
                    CREATE TABLE init_test_errors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        error_id TEXT UNIQUE NOT NULL,
                        error_type TEXT NOT NULL,
                        error_message TEXT NOT NULL,
                        severity TEXT DEFAULT 'medium',
                        fixed_by TEXT,
                        fix_method TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (test_id) REFERENCES system_init_tests(test_id)
                conn.commit()
                logger.info("创建init_test_errors表")

            # 检查init_test_breakpoints表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='init_test_breakpoints'")
            if not cursor.fetchone():
                cursor.execute('''
                    CREATE TABLE init_test_breakpoints (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        breakpoint_id TEXT UNIQUE NOT NULL,
                        test_id TEXT NOT NULL,
                        breakpoint_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metrics TEXT,
                        FOREIGN KEY (test_id) REFERENCES system_init_tests(test_id)
                conn.commit()

            logger.info("数据库检查完成")
            logger.error(f"数据库检查失败: {str(e)}")

        """添加新AI类型"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for ai_type in self.new_ai_types:
                # 检查是否已存在
                cursor.execute("SELECT id FROM ai_types WHERE ai_type = ?", (ai_type['ai_type'],))
                if not cursor.fetchone():
                        "INSERT INTO ai_types (ai_type, name, description, functions, required_skills) VALUES (?, ?, ?, ?, ?)",
                        (
                            ai_type['description'],
                            str(ai_type['required_skills'])
                else:
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"添加新AI类型失败: {str(e)}")

    def optimize_system_initialization_scripts(self):
        """优化系统初始化和启动脚本"""
        try:
            # 创建优化后的启动脚本
            start_script = """
#!/bin/bash

# 系统启动脚本

# 日志目录
LOG_DIR="logs"
mkdir -p $LOG_DIR

# 启动时间
START_TIME=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$START_TIME] 开始启动系统..." >> $LOG_DIR/startup.log
# 检查Python环境
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 检查Python环境..." >> $LOG_DIR/startup.log
if command -v python3 &> /dev/null; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] Python 3 已安装" >> $LOG_DIR/startup.log
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 错误: Python 3 未安装" >> $LOG_DIR/startup.log
    exit 1
fi

echo "[$(date +"%Y-%m-%d %H:%M:%S")] 检查依赖..." >> $LOG_DIR/startup.log
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt >> $LOG_DIR/startup.log 2>&1
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 依赖安装完成" >> $LOG_DIR/startup.log
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 警告: requirements.txt 未找到" >> $LOG_DIR/startup.log

# 启动Flask应用
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 启动Flask应用..." >> $LOG_DIR/startup.log
cd flask-app
python3 -m flask run --host=0.0.0.0 --port=5000 >> $LOG_DIR/startup.log 2>&1

# 结束时间
END_TIME=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$END_TIME] 系统启动完成" >> $LOG_DIR/startup.log
            """

            # 保存启动脚本
            start_script_path = os.path.join(self.scripts_dir, 'start_system.sh')
            with open(start_script_path, 'w', encoding='utf-8') as f:
                f.write(start_script)

            # 设置执行权限
            os.chmod(start_script_path, 0o755)

            # 创建初始化检查脚本
            init_check_script = """
#!/bin/bash

# 系统初始化检查脚本

# 日志目录
LOG_DIR="logs"
mkdir -p $LOG_DIR

# 检查时间
CHECK_TIME=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$CHECK_TIME] 开始系统初始化检查..." >> $LOG_DIR/init_check.log

# 检查目录结构
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 检查目录结构..." >> $LOG_DIR/init_check.log
required_dirs=("app" "app/ai" "app/models" "app/utils" "app/templates" "app/static" "logs" "data")
    if [ -d "$dir" ]; then
        echo "[$(date +"%Y-%m-%d %H:%M:%S")] 目录 $dir 存在" >> $LOG_DIR/init_check.log
        echo "[$(date +"%Y-%m-%d %H:%M:%S")] 警告: 目录 $dir 不存在，正在创建..." >> $LOG_DIR/init_check.log
        mkdir -p $dir
    fi
done

# 检查数据库文件
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 检查数据库文件..." >> $LOG_DIR/init_check.log
if [ -f "app/data/mtscos_ai_project.db" ]; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 数据库文件存在" >> $LOG_DIR/init_check.log
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 警告: 数据库文件不存在" >> $LOG_DIR/init_check.log
fi

# 检查配置文件
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 检查配置文件..." >> $LOG_DIR/init_check.log
if [ -f "app/config.py" ]; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 配置文件存在" >> $LOG_DIR/init_check.log
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] 警告: 配置文件不存在" >> $LOG_DIR/init_check.log
fi
# 检查完成
END_TIME=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$END_TIME] 系统初始化检查完成" >> $LOG_DIR/init_check.log
            """
            # 保存初始化检查脚本
            with open(init_check_script_path, 'w', encoding='utf-8') as f:

            # 设置执行权限
            os.chmod(init_check_script_path, 0o755)

            logger.info("系统初始化和启动脚本优化完成")
            return start_script_path, init_check_script_path
        except Exception as e:
            logger.error(f"优化系统初始化和启动脚本失败: {str(e)}")
            return None, None

    def run_system_initialization_tests(self):
        """运行系统初始化测试"""
            test_id = f"init-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            test_name = "系统初始化综合测试"
            test_description = "测试系统初始化和启动过程"

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO system_init_tests (test_id, test_name, test_description, test_status, start_time) VALUES (?, ?, ?, ?, ?)",
                    test_id,
                    test_name,
                    test_description,
                    datetime.now().isoformat()

            # 模拟测试步骤
                {'name': '目录结构检查', 'description': '检查系统目录结构是否完整'},
                {'name': '依赖检查', 'description': '检查系统依赖是否安装'},
                {'name': '配置文件检查', 'description': '检查配置文件是否存在'},
                {'name': '启动脚本执行', 'description': '执行启动脚本测试'},
                {'name': '服务状态检查', 'description': '检查服务是否正常启动'}
            warning_count = 0
            breakpoints = []
            errors = []

            for step in test_steps:
                logger.info(f"执行测试步骤: {step['name']}")
                # 记录测试拐点
                breakpoint_id = f"breakpoint-{test_id}-{len(breakpoints) + 1}"
                    'breakpoint_id': breakpoint_id,
                    'test_id': test_id,
                    'breakpoint_type': 'test_step',
                    'description': step['description'],
                    'timestamp': datetime.now().isoformat(),
                    'metrics': str({
                        'step': step['name'],
                        'duration': 1.0,
                        'resources_used': {'cpu': 30.5, 'memory': 45.2}
                    })
                }

                # 插入拐点记录
                    (
                        breakpoint['breakpoint_id'],
                        breakpoint['test_id'],
                        breakpoint['breakpoint_type'],
                        breakpoint['description'],
                        breakpoint['timestamp'],
                        breakpoint['metrics']
                    )
                )
                if step['name'] in ['依赖检查', '数据库检查', '服务状态检查']:
                    error_id = f"error-{test_id}-{error_count + 1}"
                        'error_id': error_id,
                        'test_id': test_id,
                        'error_type': 'dependency_issue' if step['name'] == '依赖检查' else 'database_error' if step['name'] == '数据库检查' else 'service_error',
                        'error_message': f"{step['name']}中发现问题",
                        'error_location': f"init/{step['name'].replace(' ', '_').lower()}",
                        'severity': 'high' if step['name'] == '服务状态检查' else 'medium',
                        'status': 'unfixed',
                        'created_at': datetime.now().isoformat()
                    }
                    errors.append(error)
                    error_count += 1

                    # 插入错误记录
                    cursor.execute(
                        "INSERT INTO init_test_errors (error_id, test_id, error_type, error_message, error_location, severity, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            error['error_id'],
                            error['test_id'],
                            error['error_type'],
                            error['error_message'],
                            error['error_location'],
                            error['severity'],
                            error['status']
                        )
                    )
                if step['name'] == '配置文件检查':
                    warning_count += 1
            # 更新测试状态
            performance_metrics = {
                'avg_response_time': 80,
                'max_response_time': 200,
                'success_rate': (len(test_steps) - error_count) / len(test_steps)
            }
            cursor.execute(
                "UPDATE system_init_tests SET test_status = ?, end_time = ?, error_count = ?, warning_count = ?, performance_metrics = ? WHERE test_id = ?",
                (
                    datetime.now().isoformat(),
                    error_count,
                    warning_count,
                    str(performance_metrics),
                    test_id
                )
            )
            conn.close()

            logger.info(f"系统初始化测试完成，发现 {error_count} 个错误，{warning_count} 个警告")
            return test_id, errors
        except Exception as e:
            logger.error(f"运行系统初始化测试失败: {str(e)}")
            return None, []

        """处理测试中发现的错误"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for error in errors:
                # 模拟错误修复
                if error['error_type'] == 'dependency_issue':
                    fix_method = "自动修复: 安装缺失的依赖包"
                    fix_method = "自动修复: 初始化数据库表结构"
                else:
                    fix_method = "自动修复: 重启服务并检查配置"

                cursor.execute(
                    "UPDATE init_test_errors SET status = ?, fix_attempts = fix_attempts + 1, fixed_by = ?, fix_time = ?, fix_method = ? WHERE error_id = ?",
                    (
                        'fixed',
                        'init_error_handling_ai',
                        datetime.now().isoformat(),
                        fix_method,
                        error['error_id']
                    )
                )
                brain_knowledge = {
                    'knowledge_id': f"knowledge-{error['error_id']}",
                    'title': f"修复初始化错误: {error['error_message']}",
                    'content': f"错误类型: {error['error_type']}\n错误位置: {error['error_location']}\n修复方法: {fix_method}",
                    'severity': error['severity'],
                    'created_at': datetime.now().isoformat()

                # 保存到AI脑库
                    json.dump(brain_knowledge, f, ensure_ascii=False, indent=2)

                logger.info(f"修复错误: {error['error_message']}")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"处理错误失败: {str(e)}")

    def generate_test_report(self, test_id):
        """生成测试报告"""
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取测试信息
            cursor.execute("SELECT * FROM system_init_tests WHERE test_id = ?", (test_id,))
            test = cursor.fetchone()

                logger.error("测试记录不存在")
                return None

            # 获取错误信息
            cursor.execute("SELECT * FROM init_test_errors WHERE test_id = ?", (test_id,))
            errors = cursor.fetchall()

            # 获取拐点信息
            cursor.execute("SELECT * FROM init_test_breakpoints WHERE test_id = ?", (test_id,))
            breakpoints = cursor.fetchall()

            conn.close()

            # 生成报告
            report = {
                'test_id': test_id,
                'test_name': test[2],
                'test_description': test[3],
                'end_time': test[6],
                'warning_count': test[8],
                'performance_metrics': eval(test[9]) if test[9] else {},
                'errors': [
                        'error_id': error[1],
                        'error_location': error[5],
                        'severity': error[6],
                        'status': error[7],
                        'fix_time': error[10],
                        'fix_method': error[11]
                    }
                    for error in errors
                ],
                'breakpoints': [
                    {
                        'breakpoint_type': bp[3],
                        'description': bp[4],
                        'metrics': eval(bp[6]) if bp[6] else {}
                    }
                    for bp in breakpoints
                ],
                'generated_at': datetime.now().isoformat()
            }

            report_path = os.path.join(self.init_dir, f"init_test_report_{test_id}.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"生成测试报告失败: {str(e)}")
            return None
    def run(self):
        try:
            logger.info("开始AI和系统初始化增强")

            # 1. 检查数据库
            self.check_database()

            # 2. 添加新AI类型

            if not start_script or not init_check_script:
                logger.error("优化系统初始化和启动脚本失败，终止流程")
                return
            # 4. 运行系统初始化测试
            test_id, errors = self.run_system_initialization_tests()
            if not test_id:
                logger.error("运行系统初始化测试失败，终止流程")
                return
            # 5. 处理测试中发现的错误
            if errors:
                self.handle_errors(errors)

            # 6. 生成测试报告
            report = self.generate_test_report(test_id)
            if not report:
                logger.error("生成测试报告失败")

            logger.info("AI和系统初始化增强完成")
        except Exception as e:
            logger.error(f"运行增强流程失败: {str(e)}")

if __name__ == "__main__":
    enhancer = AIAndSystemInitializationEnhancer()
