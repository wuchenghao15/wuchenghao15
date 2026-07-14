#!/usr/bin/env python3
"""
MTSCOS AI 系统全面测试脚本
测试所有AI页面、API、数据库连接和功能模块
"""

import os
import sys
import json
import subprocess
import sqlite3
import time
from datetime import datetime

BASE_URL = "http://localhost:8888"
TEST_RESULTS = []

def run_curl(url, method='GET', data=None):
    """使用curl测试URL"""
    cmd = ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', f"{BASE_URL}{url}"]
    if method == 'POST' and data:
        cmd = ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(data), f"{BASE_URL}{url}"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()

def log_result(test_name, status, details=""):
    """记录测试结果"""
    result = {
        'test_name': test_name,
        'status': status,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }
    TEST_RESULTS.append(result)
    print(f"{'✅' if status else '❌'} {test_name}: {details}")
    return result

def test_page(url):
    """测试页面访问"""
    try:
        time.sleep(0.2)
        status_code = run_curl(url)
        
        if status_code == '200':
            return log_result(f"页面: {url}", True, f"HTTP {status_code}")
        elif status_code == '302':
            return log_result(f"页面: {url}", True, f"HTTP {status_code} (重定向到登录页，正常)")
        else:
            return log_result(f"页面: {url}", False, f"HTTP {status_code}")
    except Exception as e:
        return log_result(f"页面: {url}", False, f"测试失败: {str(e)}")

def test_api(url, method='GET', data=None):
    """测试API接口"""
    try:
        time.sleep(0.2)
        status_code = run_curl(url, method, data)
        
        if status_code == '200':
            cmd = ['curl', '-s', f"{BASE_URL}{url}"]
            if method == 'POST' and data:
                cmd = ['curl', '-s', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(data), f"{BASE_URL}{url}"]
            
            response = subprocess.run(cmd, capture_output=True, text=True)
            try:
                json_data = json.loads(response.stdout)
                details = f"HTTP {status_code}"
                if 'success' in json_data:
                    if json_data['success']:
                        if 'data' in json_data:
                            data_len = len(json_data['data']) if isinstance(json_data['data'], list) else '返回数据'
                            details += f", 数据量: {data_len}"
                    else:
                        details += f", 错误: {json_data.get('message', '')}"
                return log_result(f"API: {url}", json_data.get('success', True), details)
            except:
                return log_result(f"API: {url}", True, f"HTTP {status_code}")
        else:
            return log_result(f"API: {url}", False, f"HTTP {status_code}")
    except Exception as e:
        return log_result(f"API: {url}", False, f"测试失败: {str(e)}")

def test_database(db_path, table_name):
    """测试数据库表"""
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        conn.close()
        return log_result(f"数据库: {os.path.basename(db_path)} - {table_name}", True, f"记录数: {count}")
    except Exception as e:
        return log_result(f"数据库: {os.path.basename(db_path)} - {table_name}", False, f"查询失败: {str(e)}")

def test_all_ai_pages():
    """测试所有AI相关页面"""
    print("\n" + "="*70)
    print("AI页面测试")
    print("="*70)
    
    ai_pages = [
        '/ai-chat',
        '/ai_cluster_matrix',
        '/enhancement',
        '/super_admin_dashboard',
        '/dashboard',
        '/settings',
    ]
    
    for page in ai_pages:
        test_page(page)

def test_all_ai_apis():
    """测试所有AI相关API"""
    print("\n" + "="*70)
    print("AI API测试")
    print("="*70)
    
    ai_apis = [
        ('/api/ai/models', 'GET'),
        ('/api/ai/nodes', 'GET'),
        ('/api/mobile/detect', 'GET'),
        ('/api/mobile/config', 'GET'),
        ('/api/questions/categories', 'GET'),
        ('/api/questions/tags', 'GET'),
        ('/api/system/status/extended', 'GET'),
        ('/api/system/notices/marquee/toggle', 'POST', {'enabled': False}),
        ('/api/notification/send', 'POST', {'title': '测试通知', 'content': '测试内容'}),
        ('/api/notification/queue', 'GET'),
    ]
    
    for api in ai_apis:
        if len(api) == 3:
            test_api(api[0], api[1], api[2])
        else:
            test_api(api[0], api[1])

def test_all_databases():
    """测试数据库连接"""
    print("\n" + "="*70)
    print("数据库测试")
    print("="*70)
    
    split_db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'split_databases')
    databases = [
        ('system.db', ['system_notices', 'mobile_config', 'notification_queue', 'user_devices']),
        ('ai.db', ['ai_model_performance', 'ai_node_status']),
        ('question.db', ['question_categories_ext', 'question_tags']),
        ('auth.db', ['login_logs', 'mfa_settings']),
        ('exam.db', ['exam_statistics_ext', 'exam_error_analysis']),
        ('user.db', ['user_learning_progress', 'user_preferences']),
        ('log.db', ['operation_logs_ext', 'performance_logs']),
        ('admin.db', ['admin_operations', 'config_changes']),
    ]
    
    for db_name, tables in databases:
        db_path = os.path.join(split_db_dir, db_name)
        if os.path.exists(db_path):
            for table in tables:
                test_database(db_path, table)
        else:
            log_result(f"数据库: {db_name}", False, "文件不存在")

def test_enhancement_manager():
    """测试增强管理器"""
    print("\n" + "="*70)
    print("增强管理器测试")
    print("="*70)
    
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from ai_engines.system_enhancement_manager import system_enhancement_manager
        
        result = system_enhancement_manager.get_enhancement_status()
        log_result("增强管理器状态", True, f"状态: {result.get('status')}")
        
        port_stats = system_enhancement_manager.get_port_usage_stats()
        log_result("端口使用统计", True, f"端口数: {len(port_stats.get('ports', []))}")
        
        perm_matrix = system_enhancement_manager.get_role_permission_matrix()
        log_result("权限矩阵", True, f"角色数: {len(perm_matrix.get('roles', []))}")
        
        question_stats = system_enhancement_manager.get_question_bank_stats()
        log_result("题库统计", True, f"分类数: {question_stats.get('category_count', 0)}")
        
    except Exception as e:
        log_result("增强管理器", False, f"加载失败: {str(e)}")

def submit_test_results():
    """提交测试结果到数据库"""
    print("\n" + "="*70)
    print("提交测试结果到数据库")
    print("="*70)
    
    split_db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'split_databases')
    db_path = os.path.join(split_db_dir, 'system.db')
    
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                status INTEGER NOT NULL,
                details TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                test_batch TEXT
            )
        ''')
        
        batch_id = f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for result in TEST_RESULTS:
            cursor.execute('''
                INSERT INTO test_results (test_name, status, details, timestamp, test_batch)
                VALUES (?, ?, ?, ?, ?)
            ''', (result['test_name'], 1 if result['status'] else 0, result['details'], result['timestamp'], batch_id))
        
        conn.commit()
        conn.close()
        log_result("测试结果提交", True, f"批次: {batch_id}, 记录数: {len(TEST_RESULTS)}")
    except Exception as e:
        log_result("测试结果提交", False, f"提交失败: {str(e)}")

def generate_report():
    """生成测试报告"""
    print("\n" + "="*70)
    print("测试报告")
    print("="*70)
    
    passed = sum(1 for r in TEST_RESULTS if r['status'])
    failed = sum(1 for r in TEST_RESULTS if not r['status'])
    total = len(TEST_RESULTS)
    
    print(f"\n测试总数: {total}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    if failed > 0:
        print("\n失败项:")
        for r in TEST_RESULTS:
            if not r['status']:
                print(f"  - {r['test_name']}: {r['details']}")
    
    report = {
        'total': total,
        'passed': passed,
        'failed': failed,
        'pass_rate': passed/total*100 if total > 0 else 0,
        'timestamp': datetime.now().isoformat(),
        'results': TEST_RESULTS
    }
    
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存到: {report_path}")
    return report

def main():
    print("="*70)
    print("MTSCOS AI 系统全面测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    test_all_ai_pages()
    test_all_ai_apis()
    test_all_databases()
    test_enhancement_manager()
    submit_test_results()
    generate_report()

if __name__ == '__main__':
    main()