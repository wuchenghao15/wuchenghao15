#!/usr/bin/env python3
"""
AI驱动的自动功能拓展系统
功能：
1. 自动识别项目中的可改进功能
2. 生成功能改进方案
3. 自动实施改进
4. 测试改进效果
5. 学习和优化改进过程
"""

import os
import sys
import json
import logging
import time
import random
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_auto_expander.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AI_Auto_Expander')

class AIAutoExpander:
    def __init__(self, project_root=None):
        self.project_root = project_root or os.getcwd()
        self.knowledge_base_path = os.path.join(self.project_root, 'knowledge_base.json')
        self.improvement_history = os.path.join(self.project_root, 'ai_improvement_history.json')
        
        # 初始化改进历史
        if not os.path.exists(self.improvement_history):
            with open(self.improvement_history, 'w', encoding='utf-8') as f:
                json.dump({'improvements': []}, f, ensure_ascii=False, indent=2)
        
        # 可改进功能列表
        self.improvement_categories = {
            'security': self.improve_security,
            'performance': self.improve_performance,
            'usability': self.improve_usability,
            'scalability': self.improve_scalability,
            'maintainability': self.improve_maintainability
        }
        
        logger.info("AI自动功能拓展系统初始化完成")
    
    def load_improvement_history(self) -> Dict:
        """加载改进历史"""
        try:
            with open(self.improvement_history, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载改进历史失败: {e}")
            return {'improvements': []}
    
    def save_improvement(self, improvement: Dict):
        """保存改进记录"""
        history = self.load_improvement_history()
        history['improvements'].append(improvement)
        
        try:
            with open(self.improvement_history, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            logger.info(f"保存改进记录成功: {improvement['improvement_id']}")
        except Exception as e:
            logger.error(f"保存改进记录失败: {e}")
    
    def identify_improvements(self) -> List[Dict]:
        """识别可改进的功能"""
        logger.info("开始识别可改进功能")
        improvements = []
        
        # 1. 检查现有代码中的TODO和FIXME注释
        todo_comments = self._find_todo_comments()
        if todo_comments:
            improvements.append({
                'type': 'code_quality',
                'priority': 'medium',
                'description': f"修复代码中的TODO/FIXME注释 ({len(todo_comments)} 处)",
                'details': todo_comments
            })
        
        # 2. 检查重复代码
        duplicate_code = self._find_duplicate_code()
        if duplicate_code:
            improvements.append({
                'type': 'maintainability',
                'priority': 'high',
                'description': f"重构重复代码 ({len(duplicate_code)} 处)",
                'details': duplicate_code
            })
        
        # 3. 检查安全漏洞
        security_issues = self._find_security_issues()
        if security_issues:
            improvements.append({
                'type': 'security',
                'priority': 'critical',
                'description': f"修复安全漏洞 ({len(security_issues)} 处)",
                'details': security_issues
            })
        
        # 4. 检查性能瓶颈
        performance_issues = self._find_performance_issues()
        if performance_issues:
            improvements.append({
                'type': 'performance',
                'priority': 'medium',
                'description': f"优化性能瓶颈 ({len(performance_issues)} 处)",
                'details': performance_issues
            })
        
        logger.info(f"识别到 {len(improvements)} 项可改进功能")
        return improvements
    
    def _find_todo_comments(self) -> List[Dict]:
        """查找代码中的TODO和FIXME注释"""
        todo_files = []
        try:
            result = subprocess.run(
                ['grep', '-r', '-n', '-i', 'TODO\|FIXME', '--include="*.py"', '--include="*.html"', '--include="*.js"', '--include="*.css"', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line:
                        parts = line.split(':', 2)
                        if len(parts) == 3:
                            todo_files.append({
                                'file': parts[0],
                                'line': int(parts[1]),
                                'comment': parts[2].strip()
                            })
        except Exception as e:
            logger.error(f"查找TODO注释失败: {e}")
        
        return todo_files
    
    def _find_duplicate_code(self) -> List[Dict]:
        """查找重复代码"""
        # 简单实现，实际项目中可使用更复杂的算法
        duplicate_candidates = []
        try:
            # 检查常见的重复代码模式
            result = subprocess.run(
                ['grep', '-r', '-n', '--include="*.py"', 'def ', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                # 统计函数名出现次数
                function_count = {}
                for line in result.stdout.split('\n'):
                    if line and 'def ' in line:
                        func_name = line.split('def ')[1].split('(')[0]
                        function_count[func_name] = function_count.get(func_name, 0) + 1
                
                # 查找出现多次的函数
                for func_name, count in function_count.items():
                    if count > 1:
                        duplicate_candidates.append({
                            'function': func_name,
                            'count': count
                        })
        except Exception as e:
            logger.error(f"查找重复代码失败: {e}")
        
        return duplicate_candidates
    
    def _find_security_issues(self) -> List[Dict]:
        """查找安全漏洞"""
        security_issues = []
        
        # 检查硬编码的密码和密钥
        try:
            result = subprocess.run(
                ['grep', '-r', '-n', '-i', '--include="*.py"', '--include="*.env"', 'password\|secret\|key\|token', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line and any(kw in line.lower() for kw in ['password', 'secret', 'key', 'token']):
                        if not any(ignore in line.lower() for ignore in ['__secret_key__', 'generate', 'random', 'token_', 'secrets.']):
                            parts = line.split(':', 2)
                            if len(parts) == 3:
                                security_issues.append({
                                    'file': parts[0],
                                    'line': int(parts[1]),
                                    'issue': 'potential_hardcoded_secret',
                                    'description': parts[2].strip()
                                })
        except Exception as e:
            logger.error(f"查找安全漏洞失败: {e}")
        
        return security_issues
    
    def _find_performance_issues(self) -> List[Dict]:
        """查找性能瓶颈"""
        performance_issues = []
        
        # 检查可能的性能瓶颈
        try:
            result = subprocess.run(
                ['grep', '-r', '-n', '--include="*.py"', 'time.sleep\|while True\|for.*range', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line:
                        parts = line.split(':', 2)
                        if len(parts) == 3:
                            performance_issues.append({
                                'file': parts[0],
                                'line': int(parts[1]),
                                'issue': 'potential_performance_bottleneck',
                                'description': parts[2].strip()
                            })
        except Exception as e:
            logger.error(f"查找性能瓶颈失败: {e}")
        
        return performance_issues
    
    def improve_security(self) -> bool:
        """改进系统安全性"""
        logger.info("开始改进系统安全性")
        success = True
        
        # 1. 增强密码哈希
        password_files = self._find_password_handling_files()
        for file_path in password_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否使用了安全的密码哈希算法
                if 'bcrypt' not in content and 'scrypt' not in content and 'argon2' not in content:
                    logger.info(f"增强 {file_path} 中的密码哈希")
                    # 添加更安全的密码哈希算法
                    if 'from werkzeug.security import generate_password_hash, check_password_hash' in content:
                        # 已经使用了werkzeug的安全哈希，无需修改
                        continue
                    
                    # 添加密码哈希改进
                    if 'import hashlib' in content:
                        content = content.replace(
                            'import hashlib',
                            'import hashlib\nfrom werkzeug.security import generate_password_hash, check_password_hash'
                        )
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
            except Exception as e:
                logger.error(f"改进 {file_path} 安全性失败: {e}")
                success = False
        
        return success
    
    def improve_performance(self) -> bool:
        """改进系统性能"""
        logger.info("开始改进系统性能")
        success = True
        
        # 1. 添加缓存机制
        api_files = self._find_api_files()
        for file_path in api_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否已添加缓存
                if 'cache' not in content.lower():
                    logger.info(f"为 {file_path} 添加缓存机制")
                    # 添加缓存装饰器
                    if '@app.route' in content and 'from functools import lru_cache' not in content:
                        content = content.replace(
                            'from flask import',
                            'from flask import\nfrom functools import lru_cache'
                        )
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
            except Exception as e:
                logger.error(f"改进 {file_path} 性能失败: {e}")
                success = False
        
        return success
    
    def improve_usability(self) -> bool:
        """改进用户体验"""
        logger.info("开始改进用户体验")
        success = True
        
        # 1. 增强表单验证
        form_files = self._find_form_files()
        for file_path in form_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查表单验证
                if 'validate' in content.lower() and 'wtforms' not in content.lower():
                    logger.info(f"增强 {file_path} 中的表单验证")
                    # 添加更强大的表单验证
                    if 'from flask_wtf import FlaskForm' not in content:
                        content = content.replace(
                            'from flask import',
                            'from flask import\nfrom flask_wtf import FlaskForm, CSRFProtect'
                        )
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
            except Exception as e:
                logger.error(f"改进 {file_path} 用户体验失败: {e}")
                success = False
        
        return success
    
    def improve_scalability(self) -> bool:
        """改进系统可扩展性"""
        logger.info("开始改进系统可扩展性")
        success = True
        
        # 1. 添加异步处理支持
        async_files = self._find_async_candidates()
        for file_path in async_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否已支持异步
                if 'async def' not in content and 'await' not in content:
                    logger.info(f"为 {file_path} 添加异步处理支持")
                    # 添加异步支持
                    if '@app.route' in content and 'from flask import Flask' in content:
                        content = content.replace(
                            'from flask import Flask',
                            'from flask import Flask\nimport asyncio'
                        )
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
            except Exception as e:
                logger.error(f"改进 {file_path} 可扩展性失败: {e}")
                success = False
        
        return success
    
    def improve_maintainability(self) -> bool:
        """改进系统可维护性"""
        logger.info("开始改进系统可维护性")
        success = True
        
        # 1. 重构长函数
        long_functions = self._find_long_functions()
        for func in long_functions:
            try:
                file_path, line_num, func_name, line_count = func
                logger.info(f"重构 {file_path} 中的长函数 {func_name} ({line_count} 行)")
                # 简单的长函数警告，实际重构需要更复杂的逻辑
            except Exception as e:
                logger.error(f"重构长函数失败: {e}")
                success = False
        
        return success
    
    def _find_password_handling_files(self) -> List[str]:
        """查找处理密码的文件"""
        try:
            result = subprocess.run(
                ['grep', '-r', '-l', '--include="*.py"', 'password\|login\|register', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except Exception as e:
            logger.error(f"查找密码处理文件失败: {e}")
        
        return []
    
    def _find_api_files(self) -> List[str]:
        """查找API相关文件"""
        try:
            result = subprocess.run(
                ['grep', '-r', '-l', '--include="*.py"', '@app.route\|@api.route', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except Exception as e:
            logger.error(f"查找API文件失败: {e}")
        
        return []
    
    def _find_form_files(self) -> List[str]:
        """查找表单相关文件"""
        try:
            result = subprocess.run(
                ['grep', '-r', '-l', '--include="*.py"', 'request.form\|form\.get', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except Exception as e:
            logger.error(f"查找表单文件失败: {e}")
        
        return []
    
    def _find_async_candidates(self) -> List[str]:
        """查找适合异步处理的文件"""
        try:
            result = subprocess.run(
                ['grep', '-r', '-l', '--include="*.py"', 'requests\.get\|time\.sleep\|subprocess\.run', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except Exception as e:
            logger.error(f"查找异步处理候选文件失败: {e}")
        
        return []
    
    def _find_long_functions(self) -> List[tuple]:
        """查找长函数"""
        long_functions = []
        
        try:
            result = subprocess.run(
                ['grep', '-r', '-n', '--include="*.py"', 'def ', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line:
                        parts = line.split(':', 2)
                        if len(parts) == 3:
                            file_path = parts[0]
                            line_num = int(parts[1])
                            func_name = parts[2].strip().split('(')[0].replace('def ', '')
                            
                            # 计算函数长度
                            line_count = self._count_function_lines(file_path, line_num)
                            if line_count > 50:  # 超过50行的函数视为长函数
                                long_functions.append((file_path, line_num, func_name, line_count))
        except Exception as e:
            logger.error(f"查找长函数失败: {e}")
        
        return long_functions
    
    def _count_function_lines(self, file_path: str, start_line: int) -> int:
        """计算函数的行数"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if start_line > len(lines):
                return 0
            
            line_count = 0
            indent_level = None
            
            for i in range(start_line - 1, len(lines)):
                line = lines[i]
                stripped = line.strip()
                
                if i == start_line - 1:
                    # 函数定义行
                    line_count += 1
                    # 计算缩进级别
                    indent_level = len(line) - len(stripped)
                    continue
                
                # 跳过空行和注释
                if not stripped or stripped.startswith('#'):
                    continue
                
                # 计算当前行缩进
                current_indent = len(line) - len(stripped)
                
                # 如果缩进级别小于等于函数定义的缩进，说明函数结束
                if current_indent <= indent_level and stripped:
                    break
                
                line_count += 1
            
            return line_count
        except Exception as e:
            logger.error(f"计算函数行数失败: {e}")
            return 0
    
    def run_auto_expansion(self):
        """执行自动功能拓展"""
        logger.info("开始执行自动功能拓展")
        
        # 1. 识别可改进功能
        improvements = self.identify_improvements()
        
        # 2. 生成改进计划
        improvement_plan = self._generate_improvement_plan(improvements)
        
        # 3. 执行改进
        for improvement in improvement_plan:
            improvement_id = f"impr_{int(time.time())}_{random.randint(1000, 9999)}"
            improvement['improvement_id'] = improvement_id
            improvement['start_time'] = time.time()
            
            logger.info(f"开始实施改进: {improvement['description']} (ID: {improvement_id})")
            
            # 执行改进
            try:
                success = False
                if improvement['type'] in self.improvement_categories:
                    success = self.improvement_categories[improvement['type']]()
                
                improvement['end_time'] = time.time()
                improvement['success'] = success
                improvement['duration'] = improvement['end_time'] - improvement['start_time']
                
                # 保存改进记录
                self.save_improvement(improvement)
                
                if success:
                    logger.info(f"改进成功: {improvement['description']} (ID: {improvement_id})")
                else:
                    logger.error(f"改进失败: {improvement['description']} (ID: {improvement_id})")
            except Exception as e:
                logger.error(f"实施改进时发生错误: {e}")
                improvement['end_time'] = time.time()
                improvement['success'] = False
                improvement['error'] = str(e)
                improvement['duration'] = improvement['end_time'] - improvement['start_time']
                self.save_improvement(improvement)
        
        logger.info("自动功能拓展执行完成")
    
    def _generate_improvement_plan(self, improvements: List[Dict]) -> List[Dict]:
        """生成改进计划"""
        # 按优先级排序
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        improvements.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        # 限制一次改进的数量
        return improvements[:5]  # 每次最多改进5项功能

if __name__ == "__main__":
    expander = AIAutoExpander()
    expander.run_auto_expansion()
