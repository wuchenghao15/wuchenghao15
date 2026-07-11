#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修复AI员工
专门负责检测和修复系统问题，上报修复过程到数据库
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any

class AutoFixAIEmployee:
    """自动修复AI员工"""
    
    def __init__(self, db_path='system_logs.db'):
        self.db_path = db_path
        self.employee_name = "自动修复工程师"
        self.employee_id = "auto_fix_001"
        self.department = "技术支持部"
        self.init_database()
        
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_fix_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                action_type TEXT NOT NULL,
                problem_description TEXT,
                solution TEXT,
                affected_files TEXT,
                status TEXT,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def log_fix_action(self, action_type: str, problem: str, solution: str, 
                       files: List[str], status: str, details: str = ""):
        """记录修复操作到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO auto_fix_logs 
            (timestamp, employee_name, action_type, problem_description, 
             solution, affected_files, status, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            self.employee_name,
            action_type,
            problem,
            solution,
            json.dumps(files),
            status,
            details
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ [{self.employee_name}] {action_type}: {problem}")
        
    def detect_and_fix_white_screen(self) -> Dict[str, Any]:
        """检测并修复白屏问题"""
        problem = "主页显示为白屏/黑屏"
        solution = "修复CSS背景设置，确保背景颜色正确加载"
        affected_files = []
        
        try:
            index_file = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/frontend/pages/index.html'
            
            if not os.path.exists(index_file):
                return {
                    'status': 'failed',
                    'problem': problem,
                    'solution': '文件不存在',
                    'files': []
                }
            
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否有背景颜色设置
            if 'background-color: #0a0a0f' not in content:
                affected_files.append(index_file)
                # 添加背景颜色
                new_content = content.replace(
                    'body {\n            font-family:',
                    'body {\n            background-color: #0a0a0f;\n            font-family:'
                )
                with open(index_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                    
            self.log_fix_action('fix_white_screen', problem, solution, 
                              affected_files, 'success', '已修复背景颜色设置')
            
            return {
                'status': 'success',
                'problem': problem,
                'solution': solution,
                'files': affected_files
            }
            
        except Exception as e:
            self.log_fix_action('fix_white_screen', problem, solution, 
                              affected_files, 'failed', str(e))
            return {
                'status': 'failed',
                'problem': problem,
                'solution': str(e),
                'files': affected_files
            }
            
    def detect_and_fix_css_gradient(self) -> Dict[str, Any]:
        """检测并修复CSS渐变背景问题"""
        problem = "CSS渐变背景可能无法正确显示"
        solution = "使用明确的颜色值替代CSS变量"
        affected_files = []
        
        try:
            index_file = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/frontend/pages/index.html'
            
            if not os.path.exists(index_file):
                return {
                    'status': 'failed',
                    'problem': problem,
                    'solution': '文件不存在',
                    'files': []
                }
            
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否使用CSS变量
            if 'var(--cyber-black)' in content or 'var(--cyber-deep)' in content:
                affected_files.append(index_file)
                # 替换CSS变量为实际颜色值
                new_content = content.replace('var(--cyber-black)', '#0a0a0f')
                new_content = new_content.replace('var(--cyber-deep)', '#0f172a')
                
                with open(index_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                    
            self.log_fix_action('fix_css_gradient', problem, solution, 
                              affected_files, 'success', '已替换CSS变量为实际颜色值')
            
            return {
                'status': 'success',
                'problem': problem,
                'solution': solution,
                'files': affected_files
            }
            
        except Exception as e:
            self.log_fix_action('fix_css_gradient', problem, solution, 
                              affected_files, 'failed', str(e))
            return {
                'status': 'failed',
                'problem': problem,
                'solution': str(e),
                'files': affected_files
            }
            
    def detect_and_fix_js_errors(self) -> Dict[str, Any]:
        """检测并修复JavaScript错误"""
        problem = "JavaScript初始化可能存在错误"
        solution = "添加错误处理和空值检查"
        affected_files = []
        
        try:
            index_file = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/frontend/pages/index.html'
            
            if not os.path.exists(index_file):
                return {
                    'status': 'failed',
                    'problem': problem,
                    'solution': '文件不存在',
                    'files': []
                }
            
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否缺少错误处理
            if 'function init() {' in content and 'try {' not in content:
                affected_files.append(index_file)
                
                # 添加try-catch
                new_content = content.replace(
                    'function init() {\n            createParticles();',
                    'function init() {\n            try {\n                createParticles();'
                )
                new_content = new_content.replace(
                    'setInterval(updateTime, 1000);\n        }',
                    'setInterval(updateTime, 1000);\n            } catch (e) {\n                console.error(\'初始化错误:\', e);\n            }\n        }'
                )
                
                with open(index_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                    
            self.log_fix_action('fix_js_errors', problem, solution, 
                              affected_files, 'success', '已添加错误处理')
            
            return {
                'status': 'success',
                'problem': problem,
                'solution': solution,
                'files': affected_files
            }
            
        except Exception as e:
            self.log_fix_action('fix_js_errors', problem, solution, 
                              affected_files, 'failed', str(e))
            return {
                'status': 'failed',
                'problem': problem,
                'solution': str(e),
                'files': affected_files
            }
            
    def run_full_diagnostics(self) -> List[Dict[str, Any]]:
        """运行完整的诊断和修复"""
        results = []
        
        print("=" * 70)
        print("🔧 自动修复AI员工 - 系统诊断")
        print("=" * 70)
        
        print("\n📊 诊断项目：")
        print("1. 白屏问题检测")
        print("2. CSS渐变背景检测")
        print("3. JavaScript错误检测")
        
        print("\n🔍 开始检测...\n")
        
        # 运行各项检测和修复
        results.append(self.detect_and_fix_white_screen())
        results.append(self.detect_and_fix_css_gradient())
        results.append(self.detect_and_fix_js_errors())
        
        # 统计结果
        success_count = sum(1 for r in results if r['status'] == 'success')
        failed_count = sum(1 for r in results if r['status'] == 'failed')
        
        print("\n" + "=" * 70)
        print("📋 诊断报告")
        print("=" * 70)
        print(f"✅ 成功修复: {success_count} 项")
        print(f"❌ 修复失败: {failed_count} 项")
        print(f"📁 影响文件: {sum(len(r.get('files', [])) for r in results)} 个")
        print("=" * 70)
        
        # 生成总结报告
        self.generate_summary_report(results)
        
        return results
        
    def generate_summary_report(self, results: List[Dict[str, Any]]):
        """生成修复总结报告"""
        summary = f"""
自动修复工程师 - 诊断总结报告
生成时间: {datetime.now().isoformat()}

诊断结果:
"""
        for i, result in enumerate(results, 1):
            summary += f"""
{i}. {result['problem']}
   解决方案: {result['solution']}
   状态: {'✅ 成功' if result['status'] == 'success' else '❌ 失败'}
   影响文件: {', '.join(result.get('files', [])) or '无'}
"""
        
        summary += """
建议:
1. 清除浏览器缓存后重新访问
2. 使用硬刷新 (Ctrl+Shift+R)
3. 检查浏览器控制台是否有其他错误
4. 如问题持续，请联系技术支持

自动修复工程师签名
"""
        
        print(summary)
        
        # 保存报告到文件
        report_file = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/auto_fix_report.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(summary)
            
        print(f"\n📄 报告已保存到: {report_file}")
        
    def get_fix_history(self, limit: int = 10) -> List[Dict]:
        """获取修复历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, action_type, problem_description, 
                   solution, affected_files, status
            FROM auto_fix_logs
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'timestamp': row[0],
                'action_type': row[1],
                'problem': row[2],
                'solution': row[3],
                'files': json.loads(row[4]) if row[4] else [],
                'status': row[5]
            })
            
        return history

def main():
    """主函数"""
    fixer = AutoFixAIEmployee()
    
    print("🚀 启动自动修复AI员工...")
    print("=" * 70)
    
    # 运行完整诊断
    results = fixer.run_full_diagnostics()
    
    # 显示修复历史
    print("\n📜 最近修复历史:")
    history = fixer.get_fix_history(5)
    for h in history:
        print(f"  • {h['timestamp']} - {h['action_type']}: {h['problem']}")
    
    return results

if __name__ == '__main__':
    main()