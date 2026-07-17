# -*- coding: utf-8 -*-
"""
管理员页面路由健康检查脚本
"""

import subprocess
import time
import sys

ROUTES = [
    '/admin_app/login',
    '/admin_app/dashboard',
    '/admin_app/security_dashboard',
    '/admin_app/health_details',
    '/admin_app/users',
    '/admin_app/exams',
    '/admin_app/monitor',
    '/admin_app/github_sync',
    '/admin_app/settings',
    '/admin_app/courses',
    '/admin_app/assignments',
    '/admin_app/notifications',
    '/admin_app/resource_manager',
    '/admin_app/data_analysis',
    '/admin_app/user_auth',
    '/admin_app/learning_paths',
    '/admin_app/student_analytics',
    '/admin_app/exam_analysis',
    '/admin_app/wrong_book',
    '/admin_app/health_monitor',
    '/admin_app/visualization',
    '/admin_app/enhanced_settings',
    '/admin_app/ai_tutor',
    '/admin_app/ai_study_path',
    '/admin_app/ai_question_generator',
    '/admin_app/ai_intelligent_center',
    '/admin_app/ai_exam_composer',
    '/admin_app/arduino_ide',
]

BASE_URL = 'http://localhost:8888'

def test_routes():
    print("=" * 70)
    print("管理员页面路由健康检查")
    print("=" * 70)
    
    results = []
    
    for route in ROUTES:
        url = f"{BASE_URL}{route}"
        try:
            result = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-L', url],
                capture_output=True,
                text=True,
                timeout=10
            )
            status_code = result.stdout.strip()
            
            if status_code == '200':
                status = '✓'
                color = '\033[92m'
            elif status_code == '302':
                status = '~'
                color = '\033[93m'
            elif status_code == '404':
                status = '?'
                color = '\033[94m'
            elif status_code == '500':
                status = '✗'
                color = '\033[91m'
            else:
                status = '?'
                color = '\033[90m'
            
            print(f"{status} {color}{status_code}\033[0m - {route}")
            results.append({
                'route': route,
                'status': status_code,
                'ok': status_code in ['200', '302']
            })
            
        except subprocess.TimeoutExpired:
            print(f"✗ \033[91mTIMEOUT\033[0m - {route}")
            results.append({'route': route, 'status': 'TIMEOUT', 'ok': False})
        except Exception as e:
            print(f"✗ \033[91mERROR\033[0m - {route}: {e}")
            results.append({'route': route, 'status': 'ERROR', 'ok': False})
    
    print("=" * 70)
    
    success = sum(1 for r in results if r['ok'])
    total = len(results)
    failed = total - success
    
    print(f"结果: {success}/{total} 通过")
    if failed > 0:
        print("\n失败的路由:")
        for r in results:
            if not r['ok']:
                print(f"  - {r['route']} ({r['status']})")
        return False
    else:
        print("\n所有路由检查通过!")
        return True

if __name__ == '__main__':
    print("等待服务器启动...")
    time.sleep(2)
    success = test_routes()
    sys.exit(0 if success else 1)
