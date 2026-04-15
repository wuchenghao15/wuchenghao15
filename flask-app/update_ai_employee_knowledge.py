#!/usr/bin/env python3
"""
Update AI Employee Knowledge Base with Login Page Fix Information
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from standalone_ai_brain_map import StandaloneAIBrainService

def main():
    # 创建AI脑库服务实例
    ai_brain_service = StandaloneAIBrainService()
    
    # 添加登录页面修复知识
    title = "登录页面渲染错误修复"
    content = "修复了登录页面渲染错误：login.html模板中存在被注释掉的{{ url_for('auto_guest_login') }}引用，该端点不存在导致Jinja2渲染失败。修复方法：移除包含该引用的注释行。"
    knowledge_type = "fix"
    tags = ["login", "fix", "jinja2", "template", "rendering", "security"]
    
    # 添加知识到AI脑库
    knowledge = ai_brain_service.add_knowledge(title, content, knowledge_type, tags)
    
    print("AI员工知识库已成功更新")
    print(f"添加的知识ID: {knowledge['knowledge_id']}")
    print(f"知识标题: {knowledge['title']}")
    print(f"知识类型: {knowledge['knowledge_type']}")
    print(f"知识标签: {knowledge['tags']}")
    print(f"当前知识库条目数: {len(ai_brain_service.knowledge_base)}")

if __name__ == "__main__":
    main()
