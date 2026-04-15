#!/usr/bin/env python3
"""
Update Knowledge Base with Login Page Fix Information
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_learning_system import KnowledgeBase

def update_knowledge_base():
    """更新AI知识库，添加新的知识条目"""
    try:
        # 创建知识库实例
        kb = KnowledgeBase()
        
        # 定义知识内容
        contents = [
            {
                "content": "修复了登录页面渲染错误：login.html模板中存在被注释掉的{{ url_for('auto_guest_login') }}引用，该端点不存在导致Jinja2渲染失败。修复方法：移除包含该引用的注释行。",
                "source": "login_page_fix_20260317",
                "confidence": 0.95,
                "tags": ["login", "fix", "jinja2", "template", "rendering"],
                "metadata": {
                    "fix_time": 1773630170.716798,
                    "affected_file": "templates/login.html",
                    "error_type": "BuildError",
                    "solution": "Remove non-existent endpoint reference"
                }
            },
            {
                "content": "AI员工系统修复：TestSystemAIEmployee类缺少_get_questions_from_db方法，导致从数据库获取题目失败。修复方法：添加该方法并实现数据库查询逻辑。",
                "source": "ai_employee_fix_20260321",
                "confidence": 0.98,
                "tags": ["ai_employee", "fix", "database", "questions"],
                "metadata": {
                    "fix_time": 1774097150.0,
                    "affected_file": "ai_employee_system.py",
                    "error_type": "AttributeError",
                    "solution": "Add _get_questions_from_db method to TestSystemAIEmployee class"
                }
            },
            {
                "content": "AI员工系统修复：缺少get_ai_route_system函数，导致无法导入该函数。修复方法：添加该函数并实现单例管理。",
                "source": "ai_route_system_fix_20260321",
                "confidence": 0.98,
                "tags": ["ai_employee", "fix", "singleton", "import"],
                "metadata": {
                    "fix_time": 1774097200.0,
                    "affected_file": "ai_employee_system.py",
                    "error_type": "ImportError",
                    "solution": "Add get_ai_route_system function"
                }
            }
        ]
        
        # 添加所有知识到知识库
        for item in contents:
            kb.add_knowledge(
                item["content"],
                item["source"],
                item["confidence"],
                item["tags"],
                item["metadata"]
            )
        
        print("知识已成功添加到知识库")
        print(f"当前知识库条目数: {len(kb.knowledge['entries'])}")
        return True
    except Exception as e:
        print(f"更新知识库失败: {e}")
        return False

def main():
    update_knowledge_base()

if __name__ == "__main__":
    main()
