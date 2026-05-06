#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修复工具 - 根据AI建议修复异常和错误
"""
import os
import sqlite3
import json
from datetime import datetime
import shutil

class AutoFixer:
    """自动修复器"""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
        self.fixed_count = 0
        self.skipped_count = 0
        self.failed_count = 0
        self.fix_log = []
    
    def get_recommendations(self):
        """获取待修复的建议"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, type, description, action, priority, file_path, details, status
            FROM file_organization_log
            WHERE status = 'pending' AND priority = 'high'
            ORDER BY id ASC
            LIMIT 100
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        recommendations = []
        for row in rows:
            try:
                details = json.loads(row['details']) if row['details'] else {}
            except:
                details = {'raw': row['details']}
            
            recommendations.append({
                'id': row['id'],
                'type': row['type'],
                'description': row['description'],
                'action': row['action'],
                'priority': row['priority'],
                'file_path': row['file_path'],
                'details': details,
                'status': row['status']
            })
        
        return recommendations
    
    def fix_duplicate_files(self, rec):
        """修复重复文件"""
        files = rec.get('details', {}).get('files', [])
        if not files:
            return False, '没有文件列表'
        
        project_root = os.path.dirname(os.path.abspath(__file__))
        files_full = [os.path.join(project_root, f) for f in files]
        
        existing_files = [f for f in files_full if os.path.exists(f)]
        if len(existing_files) < 2:
            return False, '文件不足'
        
        existing_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        keep_file = existing_files[0]
        delete_files = existing_files[1:]
        
        success_count = 0
        for file_path in delete_files:
            try:
                os.remove(file_path)
                success_count += 1
            except Exception as e:
                print(f"  删除失败: {file_path} - {e}")
        
        return True, f"保留: {os.path.basename(keep_file)}, 删除 {success_count} 个重复文件"
    
    def fix_path_reference(self, rec):
        """修复路径引用问题"""
        file_path = rec.get('file_path', '')
        missing_import = rec.get('details', {}).get('missing_import', '')
        
        if not file_path or not missing_import:
            return False, '缺少必要信息'
        
        project_root = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(project_root, file_path)
        
        if not os.path.exists(full_path):
            return False, '文件不存在'
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original_content = content
            content = self._fix_import_statement(content, file_path)
            content = self._fix_relative_paths(content)
            
            if content != original_content:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True, '路径引用已修复'
            else:
                return False, '无需修复'
        except Exception as e:
            return False, str(e)
    
    def _fix_import_statement(self, content, file_path):
        """修复导入语句"""
        import re
        content = re.sub(r'from\s+["\']\.\.([^"\']+)["\']', r'from ".\1"', content)
        content = re.sub(r'import\s+["\']\.\.([^"\']+)["\']', r'import "\1"', content)
        return content
    
    def _fix_relative_paths(self, content):
        """修复相对路径"""
        import re
        content = re.sub(r'\.\./static/', '/static/', content)
        content = re.sub(r'\.\./images/', '/static/images/', content)
        content = re.sub(r'\.\./css/', '/static/css/', content)
        content = re.sub(r'\.\./js/', '/static/js/', content)
        return content
    
    def update_status(self, rec_id, status, result):
        """更新修复状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE file_organization_log 
            SET status = ?, details = ?
            WHERE id = ?
        ''', (status, json.dumps({'fix_result': result}, ensure_ascii=False), rec_id))
        
        conn.commit()
        conn.close()
    
    def add_fix_log(self, rec, success, message):
        """添加修复日志"""
        self.fix_log.append({
            'recommendation_id': rec['id'],
            'type': rec['type'],
            'description': rec['description'],
            'success': success,
            'message': message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def save_fix_logs(self):
        """保存修复日志到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fix_execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_id INTEGER,
                type TEXT,
                description TEXT,
                success INTEGER,
                message TEXT,
                timestamp TEXT
            )
        ''')
        
        for log in self.fix_log:
            cursor.execute('''
                INSERT INTO fix_execution_log 
                (recommendation_id, type, description, success, message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                log['recommendation_id'],
                log['type'],
                log['description'],
                1 if log['success'] else 0,
                log['message'],
                log['timestamp']
            ))
        
        conn.commit()
        conn.close()
    
    def run(self):
        """运行自动修复"""
        print("=" * 60)
        print("自动修复工具 - 根据AI建议修复异常和错误")
        print("=" * 60)
        
        recommendations = self.get_recommendations()
        print(f"\n发现 {len(recommendations)} 条待修复建议")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n[{i}/{len(recommendations)}] {rec['type']} - {rec['priority']}")
            print(f"  描述: {rec['description'][:60]}...")
            
            try:
                if rec['type'] == 'duplicate_files':
                    success, message = self.fix_duplicate_files(rec)
                elif rec['type'] == 'path_reference':
                    success, message = self.fix_path_reference(rec)
                else:
                    success = False
                    message = '不支持的修复类型'
                
                if success:
                    self.fixed_count += 1
                    self.update_status(rec['id'], 'completed', message)
                    print(f"  ✅ 修复成功: {message}")
                else:
                    self.skipped_count += 1
                    self.update_status(rec['id'], 'skipped', message)
                    print(f"  ⚠️ 跳过: {message}")
                
                self.add_fix_log(rec, success, message)
                
            except Exception as e:
                self.failed_count += 1
                self.update_status(rec['id'], 'failed', str(e))
                self.add_fix_log(rec, False, str(e))
                print(f"  ❌ 失败: {e}")
        
        self.save_fix_logs()
        
        print("\n" + "=" * 60)
        print("修复完成！")
        print("=" * 60)
        print(f"✅ 修复成功: {self.fixed_count}")
        print(f"⚠️ 跳过: {self.skipped_count}")
        print(f"❌ 失败: {self.failed_count}")
        
        return {
            'total': len(recommendations),
            'fixed': self.fixed_count,
            'skipped': self.skipped_count,
            'failed': self.failed_count,
            'logs': self.fix_log[:10]
        }

if __name__ == '__main__':
    fixer = AutoFixer()
    result = fixer.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))