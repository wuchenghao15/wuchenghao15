import os
import re
from bs4 import BeautifulSoup

class AnimationFixerAI:
    def __init__(self):
        self.name = "AnimationFixerAI"
        self.description = "专门修复过渡动画和极窄路动画的AI"
        self.animation_types = ["transition", "narrow_road"]
    
    def analyze_and_fix_animations(self, template_files, animation_type=None):
        """分析并修复模板文件中的动画问题"""
        fixed_files = []
        issues_found = 0
        
        for file_path in template_files:
            if not os.path.exists(file_path):
                continue
            
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            content = original_content
            
            # 检测并修复过渡动画问题
            if animation_type is None or animation_type == "transition":
                issues, fixed_content = self._detect_and_fix_transition_issues(content)
                content = fixed_content
                issues_found += issues
            
            # 检测并修复极窄路动画问题
            if animation_type is None or animation_type == "narrow_road":
                issues, fixed_content = self._detect_and_fix_narrow_road_issues(content)
                content = fixed_content
                issues_found += issues
            
            # 如果有修改，保存文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_files.append(file_path)
        
        return {
            "fixed_files": fixed_files,
            "issues_found": issues_found,
            "message": f"成功修复了{len(fixed_files)}个文件中的{issues_found}个动画问题"
        }
    
    def _detect_and_fix_transition_issues(self, content):
        """检测并修复过渡动画问题"""
        issues = 0
        soup = BeautifulSoup(content, 'html.parser')
        
        # 检查过渡动画容器
        transition_container = soup.find('div', class_='transition-content')
        if not transition_container:
            # 添加过渡动画容器
            body = soup.find('body')
            if body:
                transition_div = soup.new_tag('div', **{'class': 'transition-content'})
                transition_div['style'] = 'display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); z-index: 9999; transition: opacity 0.5s ease;'
                
                # 添加加载动画
                spinner_ring = soup.new_tag('div', **{'class': 'spinner-ring'})
                spinner_ring['style'] = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 60px; height: 60px; border: 4px solid rgba(255, 255, 255, 0.3); border-radius: 50%; border-top-color: #ffffff; animation: spin 1s ease-in-out infinite;'
                
                # 添加spinner-inner元素
                spinner_inner = soup.new_tag('div', **{'class': 'spinner-inner'})
                spinner_inner['style'] = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 40px; height: 40px; border: 4px solid rgba(255, 255, 255, 0.5); border-radius: 50%; border-bottom-color: #ffffff; animation: spin 0.75s ease-in-out infinite reverse;'
                
                spinner_ring.append(spinner_inner)
                transition_div.append(spinner_ring)
                body.append(transition_div)
                issues += 1
        else:
            # 检查spinner-inner元素是否存在
            spinner_ring = transition_container.find('div', class_='spinner-ring')
            if spinner_ring and not spinner_ring.find('div', class_='spinner-inner'):
                # 添加spinner-inner元素
                spinner_inner = soup.new_tag('div', **{'class': 'spinner-inner'})
                spinner_inner['style'] = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 40px; height: 40px; border: 4px solid rgba(255, 255, 255, 0.5); border-radius: 50%; border-bottom-color: #ffffff; animation: spin 0.75s ease-in-out infinite reverse;'
                spinner_ring.append(spinner_inner)
                issues += 1
        
        # 检查CSS动画定义
        if 'keyframes spin' not in content:
            # 添加CSS动画
            head = soup.find('head')
            if head:
                style_tag = soup.new_tag('style')
                style_tag.string = '''
                    @keyframes spin {
                        0% { transform: translate(-50%, -50%) rotate(0deg); }
                        100% { transform: translate(-50%, -50%) rotate(360deg); }
                    }
                    .transition-content {
                        display: none;
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        z-index: 9999;
                        transition: opacity 0.5s ease;
                        box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
                    }
                    .spinner-ring {
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        width: 60px;
                        height: 60px;
                        border: 4px solid rgba(255, 255, 255, 0.3);
                        border-radius: 50%;
                        border-top-color: #ffffff;
                        animation: spin 1s ease-in-out infinite;
                    }
                    .spinner-inner {
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        width: 40px;
                        height: 40px;
                        border: 4px solid rgba(255, 255, 255, 0.5);
                        border-radius: 50%;
                        border-bottom-color: #ffffff;
                        animation: spin 0.75s ease-in-out infinite reverse;
                    }
                '''
                head.append(style_tag)
                issues += 1
        
        return issues, str(soup)
    
    def _detect_and_fix_narrow_road_issues(self, content):
        """检测并修复极窄路动画问题"""
        issues = 0
        soup = BeautifulSoup(content, 'html.parser')
        
        # 检查极窄路动画容器
        narrow_road_animations = soup.find_all('div', class_='narrow-road-animation')
        for animation in narrow_road_animations:
            # 检查必要的CSS类
            if not animation.find(class_='road-line'):
                # 添加道路线元素
                road_line = soup.new_tag('div', **{'class': 'road-line'})
                road_line['style'] = 'position: absolute; top: 50%; left: 0; width: 100%; height: 2px; background: repeating-linear-gradient(90deg, #ffffff 0px, #ffffff 20px, transparent 20px, transparent 40px); animation: road-move 1s linear infinite;'
                animation.append(road_line)
                issues += 1
            
            # 检查道路动画CSS
            if 'keyframes road-move' not in content:
                head = soup.find('head')
                if head:
                    style_tag = soup.find('style')
                    if style_tag:
                        style_tag.string += '''
                            @keyframes road-move {
                                0% { transform: translateX(0); }
                                100% { transform: translateX(-40px); }
                            }
                            .narrow-road-animation {
                                position: relative;
                                overflow: hidden;
                                background: #2c3e50;
                                border-radius: 10px;
                            }
                            .road-line {
                                position: absolute;
                                top: 50%;
                                left: 0;
                                width: 100%;
                                height: 2px;
                                background: repeating-linear-gradient(90deg, #ffffff 0px, #ffffff 20px, transparent 20px, transparent 40px);
                                animation: road-move 1s linear infinite;
                            }
                        '''
                    else:
                        new_style_tag = soup.new_tag('style')
                        new_style_tag.string = '''
                            @keyframes road-move {
                                0% { transform: translateX(0); }
                                100% { transform: translateX(-40px); }
                            }
                            .narrow-road-animation {
                                position: relative;
                                overflow: hidden;
                                background: #2c3e50;
                                border-radius: 10px;
                            }
                            .road-line {
                                position: absolute;
                                top: 50%;
                                left: 0;
                                width: 100%;
                                height: 2px;
                                background: repeating-linear-gradient(90deg, #ffffff 0px, #ffffff 20px, transparent 20px, transparent 40px);
                                animation: road-move 1s linear infinite;
                            }
                        '''
                        head.append(new_style_tag)
                    issues += 1
        
        return issues, str(soup)
