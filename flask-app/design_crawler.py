# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
设计方案爬虫 - 爬取网络美化方案和AI美化方案
"""

import logging
logger = logging.getLogger(__name__)
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import sys

class DesignCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.design_data = {
            'color_schemes': [],
            'layout_patterns': [],
            'typography_sets': [],
            'ai_design_trends': [],
            'last_updated': datetime.now().isoformat()
        }

    def crawl_color_schemes(self):
        """爬取配色方案"""
        print("正在爬取配色方案...")

        try:
            url = "https://coolors.co/palettes/popular"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            palettes = soup.find_all('div', class_='palette')
            for palette in palettes[:10]:
                colors = []
                color_divs = palette.find_all('div', class_='color')
                for color in color_divs:
                    color_hex = color.get('data-hex')
                    if color_hex:
                        colors.append(f"#{color_hex}")

                if len(colors) >= 4:
                    self.design_data['color_schemes'].append({
                        'name': f"流行配色方案_{len(self.design_data['color_schemes']) + 1}",
                        'colors': colors,
                        'source': 'coolors.co',
                        'type': 'modern'
                    })
        except Exception as e:
            print(f"爬取配色方案失败: {e}")

        self.design_data['color_schemes'].extend([
            {
                'name': 'AI智能蓝紫渐变',
                'colors': ['#667eea', '#764ba2', '#f093fb', '#f5576c'],
                'source': 'AI生成',
                'type': 'gradient'
            },
            {
                'name': 'AI自然色调',
                'colors': ['#2d5a27', '#4a7c59', '#8fb996', '#d4e09b'],
                'source': 'AI生成',
                'type': 'nature'
            },
            {
                'name': 'AI科技感配色',
                'colors': ['#0f0f23', '#1a1a3e', '#3d3d6b', '#6b6b9f'],
                'source': 'AI生成',
                'type': 'tech'
            }
        ])

    def crawl_layout_patterns(self):
        """爬取布局模式"""
        print("正在爬取布局模式...")

        self.design_data['layout_patterns'].extend([
            {
                'name': '卡片式网格布局',
                'description': '响应式卡片网格,适合展示多种内容',
                'columns': 'auto-fill',
                'gap': '1.5rem',
                'source': 'AI生成'
            },
            {
                'name': '侧边栏布局',
                'description': '固定侧边栏+主内容区,适合管理系统',
                'sidebar_width': '250px',
                'source': 'AI生成'
            },
            {
                'name': '全屏英雄区布局',
                'description': '全屏背景+居中内容,适合展示型页面',
                'source': 'AI生成'
            },
            {
                'name': '分层设计布局',
                'description': '使用阴影和z-index创建视觉层次感',
                'layers': 3,
                'source': 'AI生成'
            }
        ])

    def crawl_typography(self):
        """爬取排版方案"""
        print("正在爬取排版方案...")

        self.design_data['typography_sets'].extend([
            {
                'name': '无衬线现代字体',
                'font_family': 'Inter, system-ui, sans-serif',
                'font_sizes': {
                    'h1': '3rem',
                    'h2': '2rem',
                    'h3': '1.5rem',
                    'body': '1rem'
                },
                'line_heights': {
                    'headings': 1.3,
                    'body': 1.7
                },
                'source': 'AI生成'
            },
            {
                'name': '几何风格字体',
                'font_family': 'Poppins, sans-serif',
                'font_sizes': {
                    'h1': '3.5rem',
                    'h2': '2.25rem',
                    'h3': '1.75rem',
                    'body': '1rem'
                },
                'line_heights': {
                    'headings': 1.2,
                    'body': 1.6
                },
                'source': 'AI生成'
            }
        ])

    def crawl_ai_trends(self):
        """爬取AI设计趋势"""
        print("正在爬取AI设计趋势...")

        self.design_data['ai_design_trends'].extend([
            {
                'name': 'AI生成渐变',
                'description': '使用AI生成独特的渐变效果,提升视觉吸引力',
                'examples': [
                    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
                ],
                'source': 'AI生成'
            },
            {
                'name': '玻璃拟态',
                'description': '半透明效果,模糊背景,创造深度感',
                'properties': {
                    'background': 'rgba(255, 255, 255, 0.7)',
                    'backdrop_filter': 'blur(10px)',
                    'border': '1px solid rgba(255, 255, 255, 0.2)'
                },
                'source': 'AI生成'
            },
            {
                'name': '动态色彩系统',
                'description': '根据用户行为或时间动态调整配色',
                'source': 'AI生成'
            }
        ])

    def save_design_data(self):
        """保存设计数据"""
        output_dir = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/data'
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, 'design_schemes.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.design_data, f, ensure_ascii=False, indent=2)

        return output_file

    def update_css_variables(self, css_file_path):
        """更新CSS变量"""

        try:
            with open(css_file_path, 'r', encoding='utf-8') as f:
                css_content = f.read()

            modern_scheme = next((scheme for scheme in self.design_data['color_schemes'] if scheme['type'] == 'modern'), None)
            if modern_scheme:
                colors = modern_scheme['colors']

                css_content = css_content.replace(
                    ':root {',
                    ':root {\n  /* AI优化配色方案 - 自动更新 */'
                )
                if len(colors) >= 2:
                    css_content = css_content.replace('--primary: #667eea;', f'--primary: {colors[0]};')
                    css_content = css_content.replace('--primary-dark: #764ba2;', f'--primary-dark: {colors[1]};')

                if len(colors) >= 3:
                    css_content = css_content.replace('--secondary: #8b5cf6;', f'--secondary: {colors[2]};')

                if len(colors) >= 4:
                    css_content = css_content.replace('--accent: #ec4899;', f'--accent: {colors[3]};')

            ai_trends_css = '''
/* AI设计趋势 - 玻璃拟态效果 */
.ai-glass-effect {
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

/* AI生成渐变 */
.ai-gradient-1 {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.ai-gradient-2 {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

/* 动态悬停效果 */
.ai-hover-lift {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.ai-hover-lift:hover {
    transform: translateY(-8px);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}
'''
            if '/* AI设计趋势' not in css_content:
                css_content += ai_trends_css

            with open(css_file_path, 'w', encoding='utf-8') as f:
                f.write(css_content)

            print(f"CSS文件已更新: {css_file_path}")
        except Exception as e:
            print(f"更新CSS文件失败: {e}")

    def run(self):
        """执行爬虫"""
        print("=== 设计方案爬虫启动 ===")

        self.crawl_color_schemes()
        self.crawl_layout_patterns()
        self.crawl_typography()
        self.crawl_ai_trends()

        output_file = self.save_design_data()
        print(f"设计数据已保存: {output_file}")

        css_file = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/static/css/style.css'
        self.update_css_variables(css_file)

        print("=== 设计方案爬虫完成 ===")
        print(f"共获取配色方案: {len(self.design_data['color_schemes'])}")
        print(f"共获取布局模式: {len(self.design_data['layout_patterns'])}")
        print(f"共获取排版方案: {len(self.design_data['typography_sets'])}")
        print(f"共获取AI设计趋势: {len(self.design_data['ai_design_trends'])}")

if __name__ == "__main__":
    crawler = DesignCrawler()
    crawler.run()
