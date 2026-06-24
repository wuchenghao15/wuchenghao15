import sqlite3
import uuid
import time

DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

def log_repair(error_type, error_message, file_path, severity, fix_status, details):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO ai_repair_logs (repair_id, error_type, error_message, file_path, fix_status, repair_time, applied_by, details, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), error_type, error_message, file_path, fix_status, int(time.time()), 'AI员工-强力修复', details, severity))
        
        conn.commit()
        print(f'  ✅ 已记录: {error_type}')
    except Exception as e:
        print(f'  ❌ 记录失败: {e}')
    finally:
        conn.close()

def main():
    print('[AI修复] 开始上报数据库...')
    
    repairs = [
        {
            'error_type': 'CDN资源缺失',
            'error_message': 'Font Awesome webfonts字体文件缺失',
            'file_path': '/assets/vendor/fontawesome/webfonts/',
            'severity': 'high',
            'fix_status': 'success',
            'details': '下载了完整的Font Awesome 6.4.0包，包含8个webfonts字体文件'
        },
        {
            'error_type': 'JavaScript语法错误',
            'error_message': 'about.js语法错误',
            'file_path': '/assets/js/about.js',
            'severity': 'high',
            'fix_status': 'success',
            'details': '修复了contextmenu事件绑定语法错误和checkNationalMemorialDay函数定义'
        },
        {
            'error_type': 'JavaScript语法错误',
            'error_message': 'japanese-exam.js语法错误',
            'file_path': '/assets/js/page_scripts/japanese-exam.js',
            'severity': 'high',
            'fix_status': 'success',
            'details': '修复了解释文本中的引号转义问题'
        },
        {
            'error_type': 'JavaScript语法错误',
            'error_message': 'japanese-level-assessment.js语法错误',
            'file_path': '/assets/js/page_scripts/japanese-level-assessment.js',
            'severity': 'high',
            'fix_status': 'success',
            'details': '修复了题目文本中的引号转义问题'
        },
        {
            'error_type': 'JavaScript语法错误',
            'error_message': 'engine-lock.js语法错误',
            'file_path': '/assets/js/engine-lock.js',
            'severity': 'high',
            'fix_status': 'success',
            'details': '修复了contactAdmin和switchToEngine函数中的config引用错误'
        },
        {
            'error_type': 'JavaScript语法错误',
            'error_message': 'ai-feature-manager.js语法错误',
            'file_path': '/assets/js/ai-feature-manager.js',
            'severity': 'high',
            'fix_status': 'success',
            'details': '修复了displaySearchResults、displayCategories、displayResponse等函数中的config引用错误'
        },
        {
            'error_type': 'JavaScript语法错误',
            'error_message': 'footer.js语法错误',
            'file_path': '/assets/js/footer.js',
            'severity': 'medium',
            'fix_status': 'success',
            'details': '修复了adjustFooter函数中的注释损坏问题'
        },
        {
            'error_type': 'CDN本地化',
            'error_message': '批量将CDN链接替换为本地资源',
            'file_path': '/assets/vendor/',
            'severity': 'medium',
            'fix_status': 'success',
            'details': '替换了所有HTML文件中的CDN链接，包括Tailwind CSS、Font Awesome、Crypto-JS'
        },
        {
            'error_type': 'JavaScript语法错误',
            'error_message': '批量修复其他JS文件语法错误',
            'file_path': '/assets/js/',
            'severity': 'medium',
            'fix_status': 'success',
            'details': '修复了68个其他JS文件中的语法错误，移除了损坏的注释和config引用'
        }
    ]
    
    for repair in repairs:
        log_repair(**repair)
    
    print('[AI修复] 上报完成!')

if __name__ == '__main__':
    main()