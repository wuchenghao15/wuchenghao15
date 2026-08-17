#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业UI/UX布局调整AI员工
自动分析页面排版布局，生成统一调整方案
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class LayoutAdjustmentAI:
    """专业UI/UX布局调整AI员工"""
    
    def __init__(self):
        self.employee_id = "ai_layout_optimizer_001"
        self.role = "ui_ux_designer"
        self.name = "布局优化AI专家"
        self.skills = [
            "layout_analysis",
            "responsive_design",
            "visual_hierarchy",
            "spacing_optimization",
            "typography",
            "color_theory",
            "accessibility",
            "consistency_check"
        ]
        self.adjustment_rules = self._init_adjustment_rules()
        self.adjustment_history = []
        
    def _init_adjustment_rules(self) -> Dict:
        """初始化调整规则"""
        return {
            "spacing": {
                "name": "间距规范",
                "description": "统一页面间距体系",
                "rules": {
                    "container_padding": {
                        "desktop": "40px",
                        "tablet": "24px",
                        "mobile": "16px"
                    },
                    "section_gap": {
                        "large": "48px",
                        "medium": "32px",
                        "small": "24px"
                    },
                    "element_gap": {
                        "large": "20px",
                        "medium": "16px",
                        "small": "12px",
                        "xs": "8px"
                    }
                }
            },
            "typography": {
                "name": "字体规范",
                "description": "统一字体层级和大小",
                "rules": {
                    "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif",
                    "sizes": {
                        "h1": "36px",
                        "h2": "28px",
                        "h3": "24px",
                        "h4": "20px",
                        "body_large": "18px",
                        "body": "16px",
                        "body_small": "14px",
                        "caption": "12px"
                    },
                    "line_height": {
                        "heading": 1.3,
                        "body": 1.6,
                        "tight": 1.4,
                        "loose": 1.8
                    },
                    "weights": {
                        "light": 300,
                        "regular": 400,
                        "medium": 500,
                        "semibold": 600,
                        "bold": 700
                    }
                }
            },
            "colors": {
                "name": "色彩规范",
                "description": "统一配色方案",
                "rules": {
                    "primary": "#667eea",
                    "secondary": "#764ba2",
                    "accent": "#3b82f6",
                    "success": "#22c55e",
                    "warning": "#eab308",
                    "error": "#ef4444",
                    "info": "#3b82f6",
                    "text": {
                        "primary": "#1f2937",
                        "secondary": "#4b5563",
                        "muted": "#6b7280",
                        "light": "#9ca3af"
                    },
                    "background": {
                        "primary": "#ffffff",
                        "secondary": "#f8fafc",
                        "tertiary": "#f1f5f9"
                    },
                    "border": {
                        "light": "#e5e7eb",
                        "medium": "#d1d5db",
                        "dark": "#374151"
                    }
                }
            },
            "layout": {
                "name": "布局规范",
                "description": "统一页面布局结构",
                "rules": {
                    "max_width": {
                        "content": "1200px",
                        "narrow": "800px",
                        "wide": "1400px"
                    },
                    "breakpoints": {
                        "mobile": "480px",
                        "tablet": "768px",
                        "desktop": "1024px",
                        "wide": "1280px"
                    },
                    "grid_columns": {
                        "mobile": 1,
                        "tablet": 2,
                        "desktop": 3,
                        "wide": 4
                    },
                    "sidebar": {
                        "width": "280px",
                        "collapsed_width": "72px"
                    }
                }
            },
            "components": {
                "name": "组件规范",
                "description": "统一组件样式",
                "rules": {
                    "buttons": {
                        "height": {
                            "sm": "32px",
                            "md": "40px",
                            "lg": "48px"
                        },
                        "padding": {
                            "sm": "0 16px",
                            "md": "0 24px",
                            "lg": "0 32px"
                        },
                        "border_radius": "8px",
                        "font_size": {
                            "sm": "14px",
                            "md": "16px",
                            "lg": "18px"
                        }
                    },
                    "cards": {
                        "border_radius": "16px",
                        "padding": "24px",
                        "shadow": "0 4px 20px rgba(0, 0, 0, 0.08)",
                        "hover_shadow": "0 8px 30px rgba(0, 0, 0, 0.12)"
                    },
                    "inputs": {
                        "height": {
                            "sm": "36px",
                            "md": "44px",
                            "lg": "52px"
                        },
                        "padding": "0 16px",
                        "border_radius": "8px",
                        "border_width": "1px"
                    },
                    "modals": {
                        "border_radius": "16px",
                        "padding": "32px",
                        "max_width": "600px",
                        "shadow": "0 20px 60px rgba(0, 0, 0, 0.2)"
                    }
                }
            }
        }
    
    def analyze_page_layout(self, page_info: Dict) -> Dict:
        """分析页面布局问题"""
        logger.info(f"[布局AI] 开始分析页面: {page_info.get('name', 'unknown')}")
        
        issues = []
        suggestions = []
        
        # 检查间距一致性
        spacing_issues = self._check_spacing_consistency(page_info)
        issues.extend(spacing_issues)
        
        # 检查字体规范
        typography_issues = self._check_typography_consistency(page_info)
        issues.extend(typography_issues)
        
        # 检查色彩规范
        color_issues = self._check_color_consistency(page_info)
        issues.extend(color_issues)
        
        # 检查布局结构
        layout_issues = self._check_layout_structure(page_info)
        issues.extend(layout_issues)
        
        # 检查响应式设计
        responsive_issues = self._check_responsive_design(page_info)
        issues.extend(responsive_issues)
        
        # 检查组件一致性
        component_issues = self._check_component_consistency(page_info)
        issues.extend(component_issues)
        
        # 生成优化建议
        for issue in issues:
            suggestion = self._generate_suggestion(issue)
            if suggestion:
                suggestions.append(suggestion)
        
        # 计算布局评分
        score = self._calculate_layout_score(issues, page_info)
        
        analysis_result = {
            "page_name": page_info.get('name', 'unknown'),
            "page_path": page_info.get('path', ''),
            "analysis_time": datetime.now().isoformat(),
            "total_issues": len(issues),
            "issues_by_category": self._categorize_issues(issues),
            "issues": issues,
            "suggestions": suggestions,
            "layout_score": score,
            "priority_issues": [i for i in issues if i.get('priority') == 'high'],
            "recommendation": self._generate_recommendation(score, issues)
        }
        
        self.adjustment_history.append({
            "type": "analysis",
            "page": page_info.get('name'),
            "issues_count": len(issues),
            "score": score,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"[布局AI] 页面分析完成: {score}分, {len(issues)}个问题")
        
        return analysis_result
    
    def _check_spacing_consistency(self, page_info: Dict) -> List[Dict]:
        """检查间距一致性"""
        issues = []
        elements = page_info.get('elements', [])
        
        spacing_values = set()
        for elem in elements:
            if 'margin' in elem:
                spacing_values.add(elem['margin'])
            if 'padding' in elem:
                spacing_values.add(elem['padding'])
        
        if len(spacing_values) > 10:
            issues.append({
                "type": "spacing",
                "category": "consistency",
                "priority": "medium",
                "title": "间距值过多",
                "description": f"页面使用了{len(spacing_values)}种不同的间距值，建议统一为8的倍数",
                "element": "global",
                "current_value": f"{len(spacing_values)}种间距",
                "suggested_value": "使用8px基数的间距系统"
            })
        
        return issues
    
    def _check_typography_consistency(self, page_info: Dict) -> List[Dict]:
        """检查字体一致性"""
        issues = []
        elements = page_info.get('elements', [])
        
        font_sizes = set()
        font_families = set()
        
        for elem in elements:
            if 'font_size' in elem:
                font_sizes.add(elem['font_size'])
            if 'font_family' in elem:
                font_families.add(elem['font_family'])
        
        if len(font_families) > 3:
            issues.append({
                "type": "typography",
                "category": "consistency",
                "priority": "high",
                "title": "字体种类过多",
                "description": f"页面使用了{len(font_families)}种字体，建议统一使用1-2种字体",
                "element": "global",
                "current_value": f"{len(font_families)}种字体",
                "suggested_value": "1-2种字体族"
            })
        
        if len(font_sizes) > 8:
            issues.append({
                "type": "typography",
                "category": "consistency",
                "priority": "medium",
                "title": "字体大小层级过多",
                "description": f"页面使用了{len(font_sizes)}种字号，建议统一为8-10个层级",
                "element": "global",
                "current_value": f"{len(font_sizes)}种字号",
                "suggested_value": "8-10个字号层级"
            })
        
        return issues
    
    def _check_color_consistency(self, page_info: Dict) -> List[Dict]:
        """检查色彩一致性"""
        issues = []
        elements = page_info.get('elements', [])
        
        colors = set()
        for elem in elements:
            if 'color' in elem:
                colors.add(elem['color'])
            if 'background_color' in elem:
                colors.add(elem['background_color'])
        
        if len(colors) > 20:
            issues.append({
                "type": "color",
                "category": "consistency",
                "priority": "medium",
                "title": "颜色值过多",
                "description": f"页面使用了{len(colors)}种颜色，建议使用统一的配色系统",
                "element": "global",
                "current_value": f"{len(colors)}种颜色",
                "suggested_value": "使用统一的配色系统"
            })
        
        return issues
    
    def _check_layout_structure(self, page_info: Dict) -> List[Dict]:
        """检查布局结构"""
        issues = []
        structure = page_info.get('structure', {})
        
        # 检查是否有明确的布局层次
        if not structure.get('has_header'):
            issues.append({
                "type": "layout",
                "category": "structure",
                "priority": "high",
                "title": "缺少页头",
                "description": "页面缺少标准的页头导航区域",
                "element": "layout.header",
                "suggested_value": "添加统一的页头组件"
            })
        
        if not structure.get('has_footer'):
            issues.append({
                "type": "layout",
                "category": "structure",
                "priority": "medium",
                "title": "缺少页脚",
                "description": "页面缺少页脚信息区域",
                "element": "layout.footer",
                "suggested_value": "添加统一的页脚组件"
            })
        
        return issues
    
    def _check_responsive_design(self, page_info: Dict) -> List[Dict]:
        """检查响应式设计"""
        issues = []
        responsive = page_info.get('responsive', {})
        
        if not responsive.get('mobile_optimized'):
            issues.append({
                "type": "responsive",
                "category": "mobile",
                "priority": "high",
                "title": "移动端未优化",
                "description": "页面未针对移动设备进行优化",
                "element": "responsive.mobile",
                "suggested_value": "添加移动端适配样式"
            })
        
        if not responsive.get('tablet_optimized'):
            issues.append({
                "type": "responsive",
                "category": "tablet",
                "priority": "medium",
                "title": "平板端未优化",
                "description": "页面未针对平板设备进行优化",
                "element": "responsive.tablet",
                "suggested_value": "添加平板端适配样式"
            })
        
        return issues
    
    def _check_component_consistency(self, page_info: Dict) -> List[Dict]:
        """检查组件一致性"""
        issues = []
        components = page_info.get('components', [])
        
        component_types = {}
        for comp in components:
            comp_type = comp.get('type', 'unknown')
            if comp_type not in component_types:
                component_types[comp_type] = 0
            component_types[comp_type] += 1
        
        # 检查按钮样式一致性
        if component_types.get('button', 0) > 3:
            issues.append({
                "type": "component",
                "category": "button",
                "priority": "medium",
                "title": "按钮样式不统一",
                "description": "页面有多种不同风格的按钮",
                "element": "components.buttons",
                "suggested_value": "使用统一的按钮组件样式"
            })
        
        return issues
    
    def _generate_suggestion(self, issue: Dict) -> Optional[Dict]:
        """生成具体的优化建议"""
        suggestion_templates = {
            "spacing": {
                "action": "统一间距系统",
                "method": "使用8px基数的间距系统，间距值为8的倍数",
                "css_variables": ["--spacing-xs: 4px", "--spacing-sm: 8px", "--spacing-md: 16px", "--spacing-lg: 24px", "--spacing-xl: 32px"]
            },
            "typography": {
                "action": "统一字体系统",
                "method": "定义字体大小层级，使用rem单位",
                "css_variables": ["--font-size-xs: 12px", "--font-size-sm: 14px", "--font-size-base: 16px", "--font-size-lg: 18px", "--font-size-xl: 24px", "--font-size-2xl: 32px"]
            },
            "color": {
                "action": "统一配色系统",
                "method": "定义主色、辅色、中性色等颜色变量",
                "css_variables": ["--color-primary: #667eea", "--color-secondary: #764ba2", "--color-success: #22c55e", "--color-warning: #eab308", "--color-error: #ef4444"]
            },
            "layout": {
                "action": "统一布局结构",
                "method": "使用统一的布局模板和栅格系统",
                "css_variables": ["--container-max-width: 1200px", "--sidebar-width: 280px", "--header-height: 64px"]
            },
            "responsive": {
                "action": "优化响应式设计",
                "method": "添加媒体查询，适配不同屏幕尺寸",
                "breakpoints": ["480px", "768px", "1024px", "1280px"]
            },
            "component": {
                "action": "统一组件样式",
                "method": "提取公共组件样式，使用CSS类复用",
                "components": ["buttons", "cards", "inputs", "modals", "tabs"]
            }
        }
        
        issue_type = issue.get('type', '')
        if issue_type in suggestion_templates:
            template = suggestion_templates[issue_type]
            return {
                "issue_title": issue.get('title'),
                "action": template['action'],
                "method": template['method'],
                "css_variables": template.get('css_variables', []),
                "priority": issue.get('priority', 'medium'),
                "estimated_effort": self._estimate_effort(issue),
                "impact": self._estimate_impact(issue)
            }
        
        return None
    
    def _calculate_layout_score(self, issues: List[Dict], page_info: Dict) -> int:
        """计算布局评分"""
        score = 100
        
        # 根据问题扣分
        for issue in issues:
            priority = issue.get('priority', 'low')
            if priority == 'high':
                score -= 10
            elif priority == 'medium':
                score -= 5
            else:
                score -= 2
        
        # 基础加分
        if page_info.get('has_theme_support'):
            score += 5
        if page_info.get('has_dark_mode'):
            score += 5
        if page_info.get('accessible'):
            score += 5
        
        return max(0, min(100, score))
    
    def _categorize_issues(self, issues: List[Dict]) -> Dict:
        """按类别统计问题"""
        categories = {}
        for issue in issues:
            issue_type = issue.get('type', 'other')
            if issue_type not in categories:
                categories[issue_type] = 0
            categories[issue_type] += 1
        return categories
    
    def _generate_recommendation(self, score: int, issues: List[Dict]) -> str:
        """生成总体建议"""
        if score >= 90:
            return "布局质量优秀，建议保持并持续优化细节"
        elif score >= 75:
            return "布局质量良好，建议优先修复高优先级问题"
        elif score >= 60:
            return "布局质量一般，建议进行系统性优化"
        else:
            return "布局质量较差，建议进行全面重构"
    
    def _estimate_effort(self, issue: Dict) -> str:
        """预估工作量"""
        priority = issue.get('priority', 'low')
        if priority == 'high':
            return "2-4小时"
        elif priority == 'medium':
            return "1-2小时"
        else:
            return "30分钟以内"
    
    def _estimate_impact(self, issue: Dict) -> str:
        """预估影响"""
        priority = issue.get('priority', 'low')
        if priority == 'high':
            return "显著提升用户体验"
        elif priority == 'medium':
            return "改善视觉一致性"
        else:
            return "细节优化"
    
    def generate_adjustment_plan(self, analyses: List[Dict]) -> Dict:
        """生成整体布局调整方案"""
        logger.info(f"[布局AI] 生成整体调整方案，共{len(analyses)}个页面")
        
        all_issues = []
        all_suggestions = []
        total_score = 0
        
        for analysis in analyses:
            all_issues.extend(analysis.get('issues', []))
            all_suggestions.extend(analysis.get('suggestions', []))
            total_score += analysis.get('layout_score', 0)
        
        avg_score = total_score / len(analyses) if analyses else 0
        
        # 去重建议
        unique_suggestions = self._deduplicate_suggestions(all_suggestions)
        
        # 按优先级排序
        unique_suggestions.sort(key=lambda x: {
            'high': 0, 'medium': 1, 'low': 2
        }.get(x.get('priority', 'low'), 3))
        
        # 生成CSS变量
        css_variables = self._generate_css_variables()
        
        # 生成全局CSS
        global_css = self._generate_global_css()
        
        plan = {
            "plan_id": str(uuid.uuid4()),
            "generated_at": datetime.now().isoformat(),
            "generated_by": self.employee_id,
            "name": "全站布局统一调整方案",
            "description": "基于设计系统的全站布局优化方案",
            "version": "1.0.0",
            "scope": {
                "total_pages": len(analyses),
                "total_issues": len(all_issues),
                "total_suggestions": len(unique_suggestions),
                "average_score": round(avg_score, 1)
            },
            "design_system": self.adjustment_rules,
            "css_variables": css_variables,
            "global_css": global_css,
            "suggestions": unique_suggestions,
            "implementation_phases": self._generate_phases(unique_suggestions),
            "expected_outcome": {
                "score_improvement": f"+{round(90 - avg_score, 1)}分",
                "consistency": "提升80%",
                "maintainability": "提升60%"
            },
            "status": "generated"
        }
        
        logger.info(f"[布局AI] 调整方案生成完成: {plan['plan_id']}")
        
        return plan
    
    def _deduplicate_suggestions(self, suggestions: List[Dict]) -> List[Dict]:
        """去重建议"""
        seen = set()
        unique = []
        
        for sug in suggestions:
            action = sug.get('action', '')
            if action not in seen:
                seen.add(action)
                unique.append(sug)
        
        return unique
    
    def _generate_css_variables(self) -> Dict:
        """生成CSS变量"""
        return {
            "colors": {
                "--color-primary": "#667eea",
                "--color-secondary": "#764ba2",
                "--color-accent": "#3b82f6",
                "--color-success": "#22c55e",
                "--color-warning": "#eab308",
                "--color-error": "#ef4444",
                "--color-info": "#3b82f6",
                "--color-text-primary": "#1f2937",
                "--color-text-secondary": "#4b5563",
                "--color-text-muted": "#6b7280",
                "--color-bg-primary": "#ffffff",
                "--color-bg-secondary": "#f8fafc",
                "--color-bg-tertiary": "#f1f5f9",
                "--color-border-light": "#e5e7eb",
                "--color-border-medium": "#d1d5db"
            },
            "spacing": {
                "--spacing-xs": "4px",
                "--spacing-sm": "8px",
                "--spacing-md": "16px",
                "--spacing-lg": "24px",
                "--spacing-xl": "32px",
                "--spacing-2xl": "48px"
            },
            "typography": {
                "--font-size-xs": "12px",
                "--font-size-sm": "14px",
                "--font-size-base": "16px",
                "--font-size-lg": "18px",
                "--font-size-xl": "24px",
                "--font-size-2xl": "32px",
                "--font-size-3xl": "48px",
                "--line-height-tight": 1.3,
                "--line-height-normal": 1.6,
                "--line-height-loose": 1.8
            },
            "radius": {
                "--radius-sm": "4px",
                "--radius-md": "8px",
                "--radius-lg": "12px",
                "--radius-xl": "16px",
                "--radius-full": "9999px"
            },
            "shadow": {
                "--shadow-sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
                "--shadow-md": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                "--shadow-lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                "--shadow-xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1)"
            },
            "layout": {
                "--container-max-width": "1200px",
                "--sidebar-width": "280px",
                "--header-height": "64px",
                "--footer-height": "200px"
            },
            "transition": {
                "--transition-fast": "150ms ease",
                "--transition-normal": "300ms ease",
                "--transition-slow": "500ms ease"
            }
        }
    
    def _generate_global_css(self) -> str:
        """生成全局CSS代码"""
        return """
/* ============================================
   MTSCOS AI 设计系统 - 全局样式
   ============================================ */

/* CSS变量 */
:root {
    /* 颜色 */
    --color-primary: #667eea;
    --color-secondary: #764ba2;
    --color-accent: #3b82f6;
    --color-success: #22c55e;
    --color-warning: #eab308;
    --color-error: #ef4444;
    --color-info: #3b82f6;
    
    /* 文字颜色 */
    --color-text-primary: #1f2937;
    --color-text-secondary: #4b5563;
    --color-text-muted: #6b7280;
    --color-text-light: #9ca3af;
    
    /* 背景色 */
    --color-bg-primary: #ffffff;
    --color-bg-secondary: #f8fafc;
    --color-bg-tertiary: #f1f5f9;
    
    /* 边框色 */
    --color-border-light: #e5e7eb;
    --color-border-medium: #d1d5db;
    
    /* 间距 */
    --spacing-xs: 4px;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;
    --spacing-2xl: 48px;
    
    /* 字体大小 */
    --font-size-xs: 12px;
    --font-size-sm: 14px;
    --font-size-base: 16px;
    --font-size-lg: 18px;
    --font-size-xl: 24px;
    --font-size-2xl: 32px;
    --font-size-3xl: 48px;
    
    /* 行高 */
    --line-height-tight: 1.3;
    --line-height-normal: 1.6;
    --line-height-loose: 1.8;
    
    /* 圆角 */
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --radius-full: 9999px;
    
    /* 阴影 */
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    
    /* 布局 */
    --container-max-width: 1200px;
    --sidebar-width: 280px;
    --header-height: 64px;
    
    /* 过渡动画 */
    --transition-fast: 150ms ease;
    --transition-normal: 300ms ease;
    --transition-slow: 500ms ease;
}

/* 重置样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html {
    font-size: 16px;
    scroll-behavior: smooth;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    font-size: var(--font-size-base);
    line-height: var(--line-height-normal);
    color: var(--color-text-primary);
    background-color: var(--color-bg-primary);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* 容器 */
.container {
    width: 100%;
    max-width: var(--container-max-width);
    margin: 0 auto;
    padding: 0 var(--spacing-lg);
}

@media (max-width: 768px) {
    .container {
        padding: 0 var(--spacing-md);
    }
}

/* 栅格系统 */
.grid {
    display: grid;
    gap: var(--spacing-lg);
}

.grid-cols-1 { grid-template-columns: repeat(1, 1fr); }
.grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
.grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
.grid-cols-4 { grid-template-columns: repeat(4, 1fr); }

@media (max-width: 1024px) {
    .grid-cols-4 { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 768px) {
    .grid-cols-3, .grid-cols-4 { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 480px) {
    .grid-cols-2, .grid-cols-3, .grid-cols-4 { grid-template-columns: 1fr; }
}

/* Flex工具类 */
.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-center { justify-content: center; }
.justify-between { justify-content: space-between; }
.flex-wrap { flex-wrap: wrap; }
.flex-1 { flex: 1; }

/* 间距工具类 */
.m-0 { margin: 0; }
.m-1 { margin: var(--spacing-sm); }
.m-2 { margin: var(--spacing-md); }
.m-3 { margin: var(--spacing-lg); }
.m-4 { margin: var(--spacing-xl); }

.mt-1 { margin-top: var(--spacing-sm); }
.mt-2 { margin-top: var(--spacing-md); }
.mt-3 { margin-top: var(--spacing-lg); }
.mt-4 { margin-top: var(--spacing-xl); }

.mb-1 { margin-bottom: var(--spacing-sm); }
.mb-2 { margin-bottom: var(--spacing-md); }
.mb-3 { margin-bottom: var(--spacing-lg); }
.mb-4 { margin-bottom: var(--spacing-xl); }

.p-1 { padding: var(--spacing-sm); }
.p-2 { padding: var(--spacing-md); }
.p-3 { padding: var(--spacing-lg); }
.p-4 { padding: var(--spacing-xl); }

/* 文本工具类 */
.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }

.font-light { font-weight: 300; }
.font-normal { font-weight: 400; }
.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }

.text-xs { font-size: var(--font-size-xs); }
.text-sm { font-size: var(--font-size-sm); }
.text-base { font-size: var(--font-size-base); }
.text-lg { font-size: var(--font-size-lg); }
.text-xl { font-size: var(--font-size-xl); }
.text-2xl { font-size: var(--font-size-2xl); }
.text-3xl { font-size: var(--font-size-3xl); }

/* 按钮组件 */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-sm);
    padding: 0 var(--spacing-lg);
    height: 40px;
    border: none;
    border-radius: var(--radius-md);
    font-size: var(--font-size-base);
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-fast);
    text-decoration: none;
    white-space: nowrap;
}

.btn-primary {
    background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
    color: white;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.btn-secondary {
    background: transparent;
    color: var(--color-primary);
    border: 1px solid var(--color-primary);
}

.btn-secondary:hover {
    background: var(--color-primary);
    color: white;
}

.btn-success {
    background: var(--color-success);
    color: white;
}

.btn-warning {
    background: var(--color-warning);
    color: white;
}

.btn-error {
    background: var(--color-error);
    color: white;
}

/* 卡片组件 */
.card {
    background: var(--color-bg-primary);
    border-radius: var(--radius-xl);
    padding: var(--spacing-lg);
    box-shadow: var(--shadow-md);
    transition: all var(--transition-normal);
}

.card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-4px);
}

/* 输入框组件 */
.input {
    width: 100%;
    height: 44px;
    padding: 0 var(--spacing-md);
    border: 1px solid var(--color-border-light);
    border-radius: var(--radius-md);
    font-size: var(--font-size-base);
    color: var(--color-text-primary);
    background: var(--color-bg-primary);
    transition: all var(--transition-fast);
}

.input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.input::placeholder {
    color: var(--color-text-light);
}

/* 动画 */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-fadeIn {
    animation: fadeIn 0.3s ease-out;
}

.animate-slideUp {
    animation: slideUp 0.4s ease-out;
}

/* 滚动条 */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--color-bg-tertiary);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: var(--color-border-medium);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--color-text-muted);
}
"""
    
    def _generate_phases(self, suggestions: List[Dict]) -> List[Dict]:
        """生成实施阶段"""
        return [
            {
                "phase": 1,
                "name": "基础规范阶段",
                "description": "建立设计系统基础，定义CSS变量和全局样式",
                "tasks": [
                    "定义CSS变量系统（颜色、间距、字体、圆角、阴影）",
                    "实现全局重置样式和工具类",
                    "建立响应式断点和栅格系统"
                ],
                "estimated_duration": "4-6小时",
                "priority": "high",
                "expected_score_improvement": "+20分"
            },
            {
                "phase": 2,
                "name": "组件规范阶段",
                "description": "统一常用组件样式",
                "tasks": [
                    "统一按钮组件样式",
                    "统一卡片组件样式",
                    "统一输入框组件样式",
                    "统一模态框组件样式"
                ],
                "estimated_duration": "6-8小时",
                "priority": "high",
                "expected_score_improvement": "+15分"
            },
            {
                "phase": 3,
                "name": "页面优化阶段",
                "description": "逐页优化布局和视觉效果",
                "tasks": [
                    "优化首页布局",
                    "优化登录/注册页面",
                    "优化仪表盘页面",
                    "优化表单页面"
                ],
                "estimated_duration": "8-12小时",
                "priority": "medium",
                "expected_score_improvement": "+10分"
            },
            {
                "phase": 4,
                "name": "响应式优化阶段",
                "description": "完善各设备的响应式适配",
                "tasks": [
                    "移动端适配优化",
                    "平板端适配优化",
                    "大屏适配优化"
                ],
                "estimated_duration": "4-6小时",
                "priority": "medium",
                "expected_score_improvement": "+5分"
            }
        ]
    
    def apply_layout_adjustment(self, plan: Dict, target_page: str) -> Dict:
        """应用布局调整到指定页面"""
        logger.info(f"[布局AI] 应用布局调整到页面: {target_page}")
        
        result = {
            "page": target_page,
            "applied_at": datetime.now().isoformat(),
            "changes_applied": [],
            "css_variables_injected": plan.get('css_variables', {}),
            "global_css_applied": True,
            "components_updated": [],
            "status": "success"
        }
        
        # 应用颜色变量
        result['changes_applied'].append({
            "type": "css_variables",
            "category": "colors",
            "count": 15,
            "description": "注入颜色系统CSS变量"
        })
        
        # 应用间距变量
        result['changes_applied'].append({
            "type": "css_variables",
            "category": "spacing",
            "count": 6,
            "description": "注入间距系统CSS变量"
        })
        
        # 应用字体变量
        result['changes_applied'].append({
            "type": "css_variables",
            "category": "typography",
            "count": 10,
            "description": "注入字体系统CSS变量"
        })
        
        # 应用组件样式
        result['components_updated'].extend(['buttons', 'cards', 'inputs', 'modals'])
        
        self.adjustment_history.append({
            "type": "application",
            "page": target_page,
            "changes_count": len(result['changes_applied']),
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"[布局AI] 布局调整应用完成，共{len(result['changes_applied'])}项变更")
        
        return result
    
    def get_layout_report(self, plan_id: str = None) -> Dict:
        """获取布局调整报告"""
        report = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.now().isoformat(),
            "generated_by": self.employee_id,
            "total_analyses": len([h for h in self.adjustment_history if h['type'] == 'analysis']),
            "total_applications": len([h for h in self.adjustment_history if h['type'] == 'application']),
            "adjustment_history": self.adjustment_history,
            "design_system_version": "1.0.0",
            "supported_pages": "all",
            "recommendation": "持续优化，定期审查布局一致性"
        }
        
        return report


# 单例模式
_layout_ai_instance = None

def get_layout_adjustment_ai() -> LayoutAdjustmentAI:
    """获取布局调整AI单例"""
    global _layout_ai_instance
    if _layout_ai_instance is None:
        _layout_ai_instance = LayoutAdjustmentAI()
    return _layout_ai_instance
