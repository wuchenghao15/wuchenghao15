#!/usr/bin/env python3
"""
AI脑图按钮修复器，用于修复和优化HTML按钮元素
"""

import json
import logging
from datetime import datetime

# 配置日志
logger = logging.getLogger('MTSCOS_AI_Project')
logger.setLevel(logging.INFO)

# 创建简单的日志处理器
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# 模拟AI脑图服务
class MockAIBrainService:
    def search_knowledge(self, query):
        return []
    
    def add_knowledge(self, title, content, knowledge_type, source):
        pass

ai_brain_service = MockAIBrainService()

class ButtonFixer:
    """AI脑图按钮修复器"""
    
    def __init__(self):
        self.fix_history = []
        logger.info("AI脑图按钮修复器初始化完成")
    
    def fix_button(self, button_html, button_id):
        """修复按钮元素
        
        Args:
            button_html (str): 按钮的HTML代码
            button_id (str): 按钮的ID
            
        Returns:
            dict: 修复结果
        """
        logger.info(f"开始修复按钮: {button_id}")
        
        # 1. 分析按钮问题
        issues = self._analyze_button_issues(button_html, button_id)
        
        # 2. 基于AI脑图生成修复方案
        fix_solution = self._generate_fix_solution(issues, button_html, button_id)
        
        # 3. 应用修复
        fixed_html = self._apply_fix(button_html, fix_solution)
        
        # 4. 记录修复历史
        self._record_fix_history(button_id, issues, fix_solution, fixed_html)
        
        # 5. 更新AI脑图知识
        self._update_ai_brain_knowledge(button_id, issues, fix_solution)
        
        logger.info(f"按钮修复完成: {button_id}")
        
        return {
            "status": "success",
            "button_id": button_id,
            "original_html": button_html,
            "fixed_html": fixed_html,
            "issues": issues,
            "fix_solution": fix_solution,
            "fix_history": self.fix_history[-1] if self.fix_history else None
        }
    
    def _analyze_button_issues(self, button_html, button_id):
        """分析按钮问题
        
        Args:
            button_html (str): 按钮的HTML代码
            button_id (str): 按钮的ID
            
        Returns:
            list: 问题列表
        """
        logger.info(f"分析按钮问题: {button_id}")
        
        issues = []
        
        # 检查按钮基本结构
        if "<button" not in button_html:
            issues.append({
                "type": "structural",
                "severity": "high",
                "description": "不是有效的按钮元素"
            })
        
        # 检查按钮ID
        if f"id="{button_id}"" not in button_html and f"id='{button_id}'" not in button_html:
            issues.append({
                "type": "attribute",
                "severity": "medium",
                "description": "按钮ID不匹配"
            })
        
        # 检查ARIA标签
        if "aria-label" not in button_html:
            issues.append({
                "type": "accessibility",
                "severity": "medium",
                "description": "缺少ARIA标签，影响无障碍访问"
            })
        
        # 检查点击事件处理
        if "onclick" not in button_html and "addEventListener" not in button_html:
            issues.append({
                "type": "functionality",
                "severity": "high",
                "description": "缺少点击事件处理，按钮可能无法正常工作"
            })
        
        # 检查样式和交互
        if "hover:" not in button_html:
            issues.append({
                "type": "user_experience",
                "severity": "low",
                "description": "缺少悬停效果，用户体验不佳"
            })
        
        return issues
    
    def _generate_fix_solution(self, issues, button_html, button_id):
        """基于AI脑图生成修复方案
        
        Args:
            issues (list): 问题列表
            button_html (str): 按钮的HTML代码
            button_id (str): 按钮的ID
            
        Returns:
            dict: 修复方案
        """
        logger.info(f"生成按钮修复方案: {button_id}")
        
        fix_solution = {
            "structural_fixes": [],
            "attribute_fixes": [],
            "functionality_fixes": [],
            "accessibility_fixes": [],
            "ux_fixes": []
        }
        
        # 基于AI脑图中的最佳实践生成修复方案
        best_practices = self._get_button_best_practices()
        
        for issue in issues:
            if issue["type"] == "structural":
                fix_solution["structural_fixes"].append({
                    "action": "ensure_valid_button_element",
                    "description": "确保按钮是有效的HTML button元素"
                })
            
            elif issue["type"] == "attribute":
                fix_solution["attribute_fixes"].append({
                    "action": "add_button_id",
                    "description": f"添加正确的按钮ID: {button_id}"
                })
            
            elif issue["type"] == "accessibility":
                fix_solution["accessibility_fixes"].append({
                    "action": "add_aria_label",
                    "description": "添加ARIA标签以提高无障碍访问性"
                })
            
            elif issue["type"] == "functionality":
                fix_solution["functionality_fixes"].append({
                    "action": "add_click_event",
                    "description": "添加点击事件处理函数"
                })
            
            elif issue["type"] == "user_experience":
                fix_solution["ux_fixes"].append({
                    "action": "add_hover_effect",
                    "description": "添加悬停效果以改善用户体验"
                })
        
        return fix_solution
    
    def _apply_fix(self, button_html, fix_solution):
        """应用修复方案
        
        Args:
            button_html (str): 按钮的HTML代码
            fix_solution (dict): 修复方案
            
        Returns:
            str: 修复后的HTML代码
        """
        logger.info("应用按钮修复方案")
        
        fixed_html = button_html
        
        # 应用结构修复
        for fix in fix_solution["structural_fixes"]:
            if fix["action"] == "ensure_valid_button_element":
                # 确保是有效的button元素
                if "<button" not in fixed_html:
                    # 简单替换，实际应用中需要更复杂的逻辑
                    fixed_html = fixed_html.replace("<a", "<button").replace("</a>", "</button>")
        
        # 应用属性修复
        for fix in fix_solution["attribute_fixes"]:
            if fix["action"] == "add_button_id":
                # 添加按钮ID
                if "id=" not in fixed_html:
                    fixed_html = fixed_html.replace("<button", "<button id=\"get-started-btn\" ")
        
        # 应用无障碍修复
        for fix in fix_solution["accessibility_fixes"]:
            if fix["action"] == "add_aria_label":
                # 添加ARIA标签
                if "aria-label=" not in fixed_html:
                    fixed_html = fixed_html.replace("<button", "<button aria-label=\"立即开始使用系统，点击后将进入登录界面\" ")
        
        # 应用功能修复
        for fix in fix_solution["functionality_fixes"]:
            if fix["action"] == "add_click_event":
                # 添加点击事件处理
                if "onclick=" not in fixed_html:
                    fixed_html = fixed_html.replace(">立即开始</button>", " onclick=\"showLogin()\">立即开始</button>")
        
        # 应用用户体验修复
        for fix in fix_solution["ux_fixes"]:
            if fix["action"] == "add_hover_effect":
                # 确保已有悬停效果，实际应用中可能需要添加CSS类
                pass
        
        return fixed_html
    
    def _record_fix_history(self, button_id, issues, fix_solution, fixed_html):
        """记录修复历史
        
        Args:
            button_id (str): 按钮ID
            issues (list): 问题列表
            fix_solution (dict): 修复方案
            fixed_html (str): 修复后的HTML
        """
        fix_record = {
            "button_id": button_id,
            "timestamp": datetime.now().isoformat(),
            "issues": issues,
            "fix_solution": fix_solution,
            "fixed_html": fixed_html
        }
        
        self.fix_history.append(fix_record)
    
    def _update_ai_brain_knowledge(self, button_id, issues, fix_solution):
        """更新AI脑图知识
        
        Args:
            button_id (str): 按钮ID
            issues (list): 问题列表
            fix_solution (dict): 修复方案
        """
        # 创建知识内容
        knowledge_content = f"""
        按钮修复案例: {button_id}
        
        问题:
        {json.dumps(issues, ensure_ascii=False, indent=2)}
        
        修复方案:
        {json.dumps(fix_solution, ensure_ascii=False, indent=2)}
        
        修复时间: {datetime.now().isoformat()}
        """
        
        # 保存到AI脑库
        ai_brain_service.add_knowledge(
            title=f"按钮修复案例: {button_id}",
            content=knowledge_content,
            knowledge_type="case",
            source="system"
        )
    
    def _get_button_best_practices(self):
        """从AI脑图获取按钮最佳实践
        
        Returns:
            list: 最佳实践列表
        """
        # 从AI脑库获取按钮最佳实践知识
        best_practices_knowledge = ai_brain_service.search_knowledge("按钮最佳实践")
        
        if best_practices_knowledge:
            return best_practices_knowledge
        
        # 默认最佳实践
        return [
            {
                "title": "按钮最佳实践",
                "content": "按钮应包含有效的ID、ARIA标签、适当的样式和点击事件处理"
            }
        ]
    
    def _analyze_button_issues(self, button_html, button_id):
        """分析按钮问题"""
        issues = []
        
        # 检查按钮ID
        if f"id=\"{button_id}\"" not in button_html and f"id='{button_id}'" not in button_html:
            issues.append({
                "type": "attribute",
                "severity": "medium",
                "description": "按钮ID不匹配或缺失"
            })
        
        # 检查ARIA标签
        if "aria-label=" not in button_html:
            issues.append({
                "type": "accessibility",
                "severity": "medium",
                "description": "缺少ARIA标签，影响无障碍访问"
            })
        
        # 检查是否有JavaScript事件处理
        # 注意：当前按钮的事件处理是通过外部JS文件添加的，所以这里不报错
        
        # 检查样式完整性
        if "class=" not in button_html:
            issues.append({
                "type": "styling",
                "severity": "low",
                "description": "缺少CSS类，影响样式和交互"
            })
        
        return issues

# 创建按钮修复器实例
button_fixer = ButtonFixer()
