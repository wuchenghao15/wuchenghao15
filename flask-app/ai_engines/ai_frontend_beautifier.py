#!/usr/bin/env python3
"""
前端AI智能美化系统
用于自动分析和美化前端代码,增强用户体验
"""

import os
import re
import json
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_frontend_beautifier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FrontendAnalyzer:
    """前端代码分析器"""

    def __init__(self):
        self.html_issues = []
        self.css_issues = []
        self.js_issues = []

    def analyze_html(self, html_content: str) -> Dict:
        """分析HTML代码"""
        logger.info("开始分析HTML代码...")

        issues = []

        if '<!DOCTYPE html>' not in html_content:
            issues.append({"type": "warning", "message": "缺少DOCTYPE声明"})

        if '<html' not in html_content or '</html>' not in html_content:
            issues.append({"type": "error", "message": "HTML标签不完整"})

        if '<head' not in html_content or '</head>' not in html_content:
            issues.append({"type": "error", "message": "HEAD标签不完整"})

        if '<body' not in html_content or '</body>' not in html_content:
            issues.append({"type": "error", "message": "BODY标签不完整"})

        if '<meta charset=' not in html_content:
            issues.append({"type": "warning", "message": "缺少字符集声明"})

        if '<meta name="viewport"' not in html_content:
            issues.append({"type": "warning", "message": "缺少viewport元标签,影响移动端显示"})

        span_width_issues = re.findall(r'<span[^>]*style=["\'](?!.*width:)[^"\']*["\'][^>]*>.*?</span>', html_content, re.DOTALL)
        if span_width_issues:
            issues.append({"type": "suggestion", "message": f"发现{len(span_width_issues)}个可能需要设置宽度的span标签"})

        div_nesting = re.findall(r'<div[^>]*>\s*<div[^>]*>\s*<div[^>]*>', html_content)
        if len(div_nesting) > 10:
            issues.append({"type": "suggestion", "message": "发现过多嵌套的div标签,建议优化HTML结构"})

        self.html_issues = issues
        return {"issues": issues, "score": max(0, 100 - len(issues) * 5)}

    def analyze_css(self, css_content: str) -> Dict:
        """分析CSS代码"""
        logger.info("开始分析CSS代码...")

        issues = []
        if '--' not in css_content:
            issues.append({"type": "suggestion", "message": "建议使用CSS变量提高样式可维护性"})

        if '@media' not in css_content:
            issues.append({"type": "warning", "message": "缺少响应式设计,建议添加媒体查询"})

        complex_selectors = re.findall(r'[^\s]+>[^\s]+>[^\s]+>[^\s]+', css_content)
        if len(complex_selectors) > 5:
            issues.append({"type": "suggestion", "message": f"发现{len(complex_selectors)}个复杂选择器,建议简化"})

        style_declarations = re.findall(r'[^\s]+:\s*[^;]+;', css_content)
        style_counts = defaultdict(int)
        for style in style_declarations:
            style_counts[style.strip()] += 1

        duplicate_styles = [style for style, count in style_counts.items() if count > 3]
        if duplicate_styles:
            issues.append({"type": "suggestion", "message": f"发现{len(duplicate_styles)}个重复样式,建议优化"})

        if 'animation' not in css_content and '@keyframes' not in css_content:
            issues.append({"type": "suggestion", "message": "建议添加适当的动画效果提升用户体验"})

        self.css_issues = issues
        return {"issues": issues, "score": max(0, 100 - len(issues) * 5)}

    def analyze_js(self, js_content: str) -> Dict:
        """分析JavaScript代码"""
        logger.info("开始分析JavaScript代码...")

        issues = []
        if 'var ' in js_content:
            issues.append({"type": "suggestion", "message": "建议使用let/const代替var,提高代码安全性"})

        console_logs = re.findall(r'console\.log\(', js_content)
        if len(console_logs) > 5:
            issues.append({"type": "warning", "message": f"发现{len(console_logs)}个console.log语句,建议清理生产环境代码"})

        if 'try {' not in js_content:
            issues.append({"type": "suggestion", "message": "建议添加错误处理机制,提高代码健壮性"})

        self.js_issues = issues
        return {"issues": issues, "score": max(0, 100 - len(issues) * 5)}

    def analyze_file(self, file_path: str) -> Dict:
        """分析文件"""
        if not os.path.exists(file_path):
            return {"error": "文件不存在"}

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if file_path.endswith('.html'):
            return self.analyze_html(content)
        elif file_path.endswith('.css'):
            return self.analyze_css(content)
        elif file_path.endswith('.js'):
            return self.analyze_js(content)
        else:
            return {"error": "不支持的文件类型"}

class AIFrontendBeautifier:
    """AI前端美化器"""

    def __init__(self):
        self.beautification_history = []
        self.analyzer = FrontendAnalyzer()

        self.beautification_styles = {
            "modern": {
                "color_scheme": {
                    "primary": "#3498db",
                    "secondary": "#2ecc71",
                    "accent": "#e74c3c",
                    "background": "#f8f9fa",
                    "text": "#333333"
                },
                "features": ["rounded_corners", "subtle_shadows", "smooth_transitions", "modern_fonts"]
            },
            "minimalist": {
                "color_scheme": {
                    "primary": "#6c757d",
                    "secondary": "#adb5bd",
                    "accent": "#495057",
                    "background": "#ffffff",
                    "text": "#212529"
                },
                "features": ["clean_layout", "ample_whitespace", "simple_typography", "minimal_animations"]
            },
            "ai_tech": {
                "color_scheme": {
                    "primary": "#667eea",
                    "secondary": "#764ba2",
                    "background": "#0f172a",
                    "text": "#ffffff"
                },
                "features": ["gradient_backgrounds", "neon_effects", "futuristic_typography", "dynamic_animations"]
            }
        }

    def generate_beautification_suggestions(self, file_path: str, style: str = "modern") -> Dict:
        """生成美化建议"""
        logger.info(f"生成{style}风格的美化建议...")
        analysis_result = self.analyzer.analyze_file(file_path)
        if "error" in analysis_result:
            return analysis_result

        suggestions = []
        file_type = os.path.splitext(file_path)[1]
        if file_type == ".html":
            suggestions.append({"type": "structure", "message": "优化HTML结构,减少不必要的嵌套"})
            suggestions.append({"type": "meta", "message": "添加必要的meta标签,优化SEO和移动端显示"})
            suggestions.append({"type": "accessibility", "message": "添加alt属性到图片标签,提高可访问性"})

        elif file_type == ".css":
            style_config = self.beautification_styles.get(style, self.beautification_styles["modern"])
            suggestions.append({"type": "variables", "message": f"使用CSS变量定义主题色: {style_config['color_scheme']}"})
            suggestions.append({"type": "responsive", "message": "添加媒体查询,实现响应式设计"})
            suggestions.append({"type": "animations", "message": "添加适当的过渡和动画效果"})
            suggestions.append({"type": "organization", "message": "按功能组织CSS代码,提高可维护性"})

        elif file_type == ".js":
            suggestions.append({"type": "modern_syntax", "message": "使用ES6+语法,提高代码可读性"})
            suggestions.append({"type": "error_handling", "message": "添加适当的错误处理机制"})
            suggestions.append({"type": "performance", "message": "优化JavaScript性能,减少不必要的计算"})

        return {
            "analysis": analysis_result,
            "suggestions": suggestions,
            "style": style,
            "estimated_improvement": analysis_result["score"] + len(suggestions) * 3
        }

    def apply_beautification(self, file_path: str, style: str = "modern", suggestions: List[Dict] = None) -> Dict:
        """应用美化"""
        logger.info(f"应用{style}风格的美化...")

        if not os.path.exists(file_path):
            return {"error": "文件不存在"}

        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        beautified_content = original_content
        changes = []
        file_type = os.path.splitext(file_path)[1]

        if file_type == ".html":
            if '<!DOCTYPE html>' not in beautified_content:
                beautified_content = '<!DOCTYPE html>\n' + beautified_content
                changes.append("添加DOCTYPE声明")

            if '<meta name="viewport"' not in beautified_content and '<head>' in beautified_content:
                beautified_content = beautified_content.replace('<head>', '<head>\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
                changes.append("添加viewport元标签")

            beautified_content = re.sub(r'(<span[^>]*style=["\'])([^"\']*)(["\'][^>]*>)',
                                      lambda m: f'{m.group(1)}{m.group(2)}{"; width: auto" if "width:" not in m.group(2) else ""}{m.group(3)}',
                                      beautified_content)
            changes.append("优化span标签宽度")
        elif file_type == ".css":
            style_config = self.beautification_styles.get(style, self.beautification_styles["modern"])

            css_variables = f":root {{\n"
            for var_name, color in style_config["color_scheme"].items():
                css_variables += f"    --color-{var_name}: {color};\n"
            css_variables += "}\n\n"

            if ':root' not in beautified_content:
                beautified_content = css_variables + beautified_content
                changes.append("添加CSS变量主题")

            if '@media' not in beautified_content:
                responsive_css = "\n/* 响应式设计 */\n@media (max-width: 768px) {\n    body {\n        padding: 0 10px;\n    }\n}\n"
                beautified_content += responsive_css
                changes.append("添加响应式设计")
            if 'transition:' not in beautified_content:
                transitions_css = "\n/* 过渡效果 */\n* {\n    transition: all 0.3s ease;\n}\n"
                beautified_content += transitions_css
                changes.append("添加过渡效果")

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(beautified_content)

        beautification_record = {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "style": style,
            "changes": changes,
            "original_score": self.analyzer.analyze_file(file_path)["score"],
            "new_score": self.analyzer.analyze_file(file_path)["score"]
        }

        self.beautification_history.append(beautification_record)

        self.update_ai_learning(beautification_record)

        return {
            "status": "success",
            "message": f"文件已成功美化,应用了{len(changes)}项更改",
            "changes": changes,
            "before_score": beautification_record["original_score"],
            "after_score": beautification_record["new_score"]
        }

    def batch_beautify(self, file_paths: List[str], style: str = "modern") -> Dict:
        """批量美化文件"""
        logger.info(f"批量美化{len(file_paths)}个文件...")
        results = []
        for file_path in file_paths:
            result = self.apply_beautification(file_path, style)
            results.append({"file_path": file_path, "result": result})

        success_count = len([r for r in results if r["result"].get("status") == "success"])

        return {
            "status": "completed",
            "success_count": success_count,
            "total_count": len(file_paths),
            "results": results
        }

    def update_ai_learning(self, beautification_record: Dict) -> None:
        """更新AI学习数据库"""

        history_file = "ai_frontend_beautification_history.json"

        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = []

        history.append(beautification_record)

        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def get_beautification_history(self) -> List[Dict]:
        """获取美化历史"""
        return self.beautification_history

class AIFrontendLearningSystem:
    """前端AI学习系统"""

    def __init__(self):
        self.knowledge_base = {
            "html_optimizations": [],
            "css_optimizations": [],
            "js_optimizations": []
        }
        self.performance_metrics = []

        self.load_knowledge_base()

    def load_knowledge_base(self) -> None:
        """加载知识库"""
        knowledge_file = "ai_frontend_knowledge_base.json"
        if os.path.exists(knowledge_file):
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)

    def save_knowledge_base(self) -> None:
        """保存知识库"""
        knowledge_file = "ai_frontend_knowledge_base.json"
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)

    def learn_from_beautification(self, beautification_result: Dict) -> None:
        """从美化结果中学习"""
        logger.info("从美化结果中学习...")

        if beautification_result.get("status") != "success":
            return

        improvement = beautification_result["after_score"] - beautification_result["before_score"]

        self.performance_metrics.append({
            "timestamp": datetime.now().isoformat(),
            "improvement": improvement,
            "changes": beautification_result["changes"],
            "file_type": os.path.splitext(beautification_result.get("file_path", ""))[1]
        })

        for change in beautification_result["changes"]:
            file_type = os.path.splitext(beautification_result.get("file_path", ""))[1][1:]
            optimization_key = f"{file_type}_optimizations"

            if optimization_key in self.knowledge_base:
                existing_optimization = next((opt for opt in self.knowledge_base[optimization_key] if opt["change"] == change), None)
                if existing_optimization:
                    existing_optimization["count"] += 1
                    existing_optimization["total_improvement"] += improvement
                    existing_optimization["average_improvement"] = existing_optimization["total_improvement"] / existing_optimization["count"]
                else:
                    self.knowledge_base[optimization_key].append({
                        "change": change,
                        "count": 1,
                        "total_improvement": improvement,
                        "average_improvement": improvement,
                        "first_used": datetime.now().isoformat(),
                        "last_used": datetime.now().isoformat()
                    })

        self.save_knowledge_base()

    def optimize_beautification_algorithm(self) -> None:
        """优化美化算法"""
        logger.info("优化美化算法...")

        for opt_type, optimizations in self.knowledge_base.items():
            if not optimizations:
                continue

            sorted_optimizations = sorted(optimizations, key=lambda x: x["average_improvement"], reverse=True)

            self.knowledge_base[opt_type] = sorted_optimizations[:10]

        self.save_knowledge_base()

        logger.info("美化算法优化完成")

    def generate_optimization_report(self) -> Dict:
        """生成优化报告"""
        logger.info("生成优化报告...")

        total_improvement = sum(m["improvement"] for m in self.performance_metrics)
        average_improvement = total_improvement / len(self.performance_metrics) if self.performance_metrics else 0

        optimization_effectiveness = {}
        for opt_type, optimizations in self.knowledge_base.items():
            for opt in optimizations:
                if opt["change"] not in optimization_effectiveness:
                    optimization_effectiveness[opt["change"]] = 0
                optimization_effectiveness[opt["change"]] += opt["average_improvement"]

        top_optimizations = sorted(optimization_effectiveness.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "report_date": datetime.now().isoformat(),
            "total_beautifications": len(self.performance_metrics),
            "total_improvement": total_improvement,
            "average_improvement": average_improvement,
            "top_optimizations": [{
                "change": opt[0],
                "effectiveness": opt[1]
            } for opt in top_optimizations],
            "knowledge_base_size": {
                "html_optimizations": len(self.knowledge_base["html_optimizations"]),
                "css_optimizations": len(self.knowledge_base["css_optimizations"]),
                "js_optimizations": len(self.knowledge_base["js_optimizations"])
            }
        }

class AIFrontendBeautificationSystem:
    """前端AI美化系统主类"""

    def __init__(self):
        self.beautifier = AIFrontendBeautifier()
        self.learning_system = AIFrontendLearningSystem()

    def beautify_file(self, file_path: str, style: str = "modern") -> Dict:
        """美化单个文件"""
        result = self.beautifier.apply_beautification(file_path, style)

        if result.get("status") == "success":
            self.learning_system.learn_from_beautification(result)
            self.learning_system.optimize_beautification_algorithm()

        return result

    def beautify_project(self, project_dir: str, style: str = "modern") -> Dict:
        """美化整个项目"""
        logger.info(f"美化项目: {project_dir},风格: {style}")

        frontend_files = []

        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'venv', 'logs', 'backups']]

            for file in files:
                if file.endswith((".html", ".css", ".js")):
                    frontend_files.append(os.path.join(root, file))

        if not frontend_files:
            return {"status": "error", "message": "未找到前端文件"}

        batch_result = self.beautifier.batch_beautify(frontend_files, style)

        for result in batch_result["results"]:
            if result["result"].get("status") == "success":
                self.learning_system.learn_from_beautification(result["result"])

        self.learning_system.optimize_beautification_algorithm()

        optimization_report = self.learning_system.generate_optimization_report()

        return {
            "status": "completed",
            "batch_result": batch_result,
            "optimization_report": optimization_report
        }

    def get_system_status(self) -> Dict:
        """获取系统状态"""
        return {
            "beautification_history_count": len(self.beautifier.beautification_history),
            "knowledge_base_size": {
                "html_optimizations": len(self.learning_system.knowledge_base["html_optimizations"]),
                "css_optimizations": len(self.learning_system.knowledge_base["css_optimizations"]),
                "js_optimizations": len(self.learning_system.knowledge_base["js_optimizations"])
            },
            "performance_metrics_count": len(self.learning_system.performance_metrics)
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="前端AI智能美化系统")
    parser.add_argument("--file", type=str, help="要美化的单个文件路径")
    parser.add_argument("--project", type=str, help="要美化的项目目录")
    parser.add_argument("--style", type=str, default="modern", choices=["modern", "minimalist", "ai_tech"], help="美化风格")
    parser.add_argument("--report", action="store_true", help="生成优化报告")
    args = parser.parse_args()

    ai_beautification_system = AIFrontendBeautificationSystem()
    if args.file:
        result = ai_beautification_system.beautify_file(args.file, args.style)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.project:
        result = ai_beautification_system.beautify_project(args.project, args.style)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.report:
        report = ai_beautification_system.learning_system.generate_optimization_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        parser.print_help()
