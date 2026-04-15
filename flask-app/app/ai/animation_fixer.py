import os
import time
from app.utils.logging import logger

class AnimationFixerAI:
    """专门修复过渡动画和极窄路动画的AI模块"""
    
    def __init__(self):
        self.name = "AnimationFixerAI"
        self.description = "专门用于修复过渡动画和极窄路动画的AI模块"
        self.animation_types = ["transition", "narrow_road"]
        self.fixed_files = []
        self.issues_found = 0
        self.issues_fixed = 0
        self.website_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..")
    
    def analyze_and_fix_animations(self, animation_type=None):
        """分析并修复动画问题
        
        Args:
            animation_type: 动画类型，可选值：transition, narrow_road, None(修复所有类型)
        """
        logger.info(f"开始分析和修复{'所有' if not animation_type else animation_type}动画问题")
        
        # 确定要修复的动画类型
        target_types = self.animation_types if not animation_type else [animation_type]
        
        # 分析模板文件
        template_files = self._get_template_files()
        
        for file_path in template_files:
            logger.debug(f"分析文件: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否包含过渡动画
            if "transition" in target_types:
                transition_issues = self._detect_transition_issues(content, file_path)
                if transition_issues:
                    content = self._fix_transition_issues(content, transition_issues)
                    self.issues_found += len(transition_issues)
                    self.issues_fixed += len(transition_issues)
            
            # 检查是否包含极窄路动画
            if "narrow_road" in target_types:
                narrow_road_issues = self._detect_narrow_road_issues(content, file_path)
                if narrow_road_issues:
                    content = self._fix_narrow_road_issues(content, narrow_road_issues)
                    self.issues_found += len(narrow_road_issues)
                    self.issues_fixed += len(narrow_road_issues)
            
            # 保存修复后的内容
            if self.issues_fixed > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                if file_path not in self.fixed_files:
                    self.fixed_files.append(file_path)
        
        logger.info(f"动画修复完成，共发现 {self.issues_found} 个问题，修复了 {self.issues_fixed} 个问题，修复了 {len(self.fixed_files)} 个文件")
        
        return {
            "status": "completed",
            "animation_type": animation_type,
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "fixed_files": self.fixed_files,
            "timestamp": time.time()
        }
    
    def _get_template_files(self):
        """获取所有模板文件"""
        template_dir = os.path.join(self.website_root, "templates")
        template_files = []
        
        for root, _, files in os.walk(template_dir):
            for file in files:
                if file.endswith(".html"):
                    template_files.append(os.path.join(root, file))
        
        return template_files
    
    def _detect_transition_issues(self, content, file_path):
        """检测过渡动画问题"""
        issues = []
        
        # 检查是否缺少spinner-inner元素
        if "transition-overlay" in content and "spinner-ring" in content:
            if "spinner-inner" not in content:
                issues.append({
                    "type": "missing_spinner_inner",
                    "description": "缺少spinner-inner元素，导致过渡动画不完整",
                    "file_path": file_path
                })
        
        # 检查transition-overlay元素是否存在
        if "transition-overlay" not in content:
            issues.append({
                "type": "missing_transition_overlay",
                "description": "缺少transition-overlay元素，无法显示过渡动画",
                "file_path": file_path
            })
        
        # 检查transition-content元素的样式是否正确
        if "transition-content" in content:
            if "background: white" in content or "background:white" in content:
                issues.append({
                    "type": "transition_content_background",
                    "description": "transition-content使用了纯白色背景，可能导致动画不可见",
                    "file_path": file_path
                })
        
        # 检查JavaScript过渡动画函数是否完整
        if "MTSCOS_AI" in content and "transition" in content:
            if "show" not in content or "hide" not in content or "navigate" not in content:
                issues.append({
                    "type": "incomplete_transition_functions",
                    "description": "过渡动画函数不完整，缺少show、hide或navigate方法",
                    "file_path": file_path
                })
        
        return issues
    
    def _fix_transition_issues(self, content, issues):
        """修复过渡动画问题"""
        for issue in issues:
            if issue["type"] == "missing_spinner_inner":
                # 修复缺少spinner-inner元素的问题
                content = content.replace('<div class="spinner-ring">', '<div class="spinner-ring">\n                    <div class="spinner-inner"></div>')
            
            elif issue["type"] == "missing_transition_overlay":
                # 添加完整的过渡动画组件
                transition_overlay = '''    <!-- 载入过渡动画组件 -->
    <div class="transition-overlay" id="transition-overlay">
        <div class="transition-content">
            <div class="transition-spinner">
                <div class="spinner-ring">
                    <div class="spinner-inner"></div>
                    <div class="spinner-dot"></div>
                </div>
            </div>
            <div class="transition-text" id="transition-text">正在加载...</div>
        </div>
    </div>'''
                # 使用普通字符串拼接避免f-string语法冲突
                content = content.replace('{% block content %}', transition_overlay + '\n\n    {% block content %}')
            
            elif issue["type"] == "transition_content_background":
                # 修复transition-content的背景色
                content = content.replace('background: white', 'background: rgba(255, 255, 255, 0.95)')
                content = content.replace('background:white', 'background: rgba(255, 255, 255, 0.95)')
            
            elif issue["type"] == "incomplete_transition_functions":
                # 检查是否需要添加完整的过渡动画函数
                if "MTSCOS_AI" in content and "transition" not in content:
                    transition_functions = '''            // 过渡动画功能
            transition: {
                show: function(text = '正在加载...') {
                    const overlay = document.getElementById('transition-overlay');
                    const textElement = document.getElementById('transition-text');
                    if (overlay && textElement) {
                        textElement.textContent = text;
                        overlay.classList.add('active');
                    }
                },
                
                hide: function() {
                    const overlay = document.getElementById('transition-overlay');
                    if (overlay) {
                        overlay.classList.remove('active');
                    }
                },
                
                // 页面跳转时显示过渡动画
                navigate: function(url, text = '正在跳转...') {
                    this.show(text);
                    setTimeout(() => {
                        window.location.href = url;
                    }, 500);
                }
            },'''
                    content = content.replace('const MTSCOS_AI = {', f'const MTSCOS_AI = {{{transition_functions}\n')
        
        return content
    
    def _detect_narrow_road_issues(self, content, file_path):
        """检测极窄路动画问题"""
        issues = []
        
        # 检查是否包含极窄路动画类
        narrow_road_classes = ["narrow-road", "narrow_road", "narrowroad"]
        for cls in narrow_road_classes:
            if cls in content:
                # 检查是否缺少必要的CSS样式
                if f".{cls}" not in content or "animation" not in content:
                    issues.append({
                        "type": "missing_narrow_road_css",
                        "description": f"缺少{cls}类的动画CSS样式",
                        "file_path": file_path,
                        "class_name": cls
                    })
        
        return issues
    
    def _fix_narrow_road_issues(self, content, issues):
        """修复极窄路动画问题"""
        for issue in issues:
            if issue["type"] == "missing_narrow_road_css":
                # 添加极窄路动画CSS样式
                narrow_road_css = f'''        /* 极窄路动画样式 */
        .{issue["class_name"]} {{
            position: relative;
            overflow: hidden;
            animation: narrowRoadMove 3s ease-in-out infinite;
        }}
        
        @keyframes narrowRoadMove {{
            0% {{
                transform: translateX(0);
            }}
            50% {{
                transform: translateX(-10px);
            }}
            100% {{
                transform: translateX(0);
            }}
        }}'''  
                
                # 检查是否有样式标签
                if "</style>" in content:
                    content = content.replace("</style>", f"{narrow_road_css}\n</style>")
                else:
                    # 如果没有样式标签，添加到head中
                    content = content.replace('</head>', f'<style>{narrow_road_css}</style>\n</head>')
        
        return content
    
    def generate_animation_report(self):
        """生成动画修复报告"""
        report = {
            "ai_name": self.name,
            "description": self.description,
            "timestamp": time.time(),
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "fixed_files": self.fixed_files,
            "status": "completed" if self.issues_fixed > 0 else "no_issues_found"
        }
        
        return report

# 初始化动画修复AI实例
animation_fixer_ai = AnimationFixerAI()