#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI配色方案爬取器
从网络上爬取成功的配色布局方案，并适配到系统中
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import sqlite3
import time
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('color_scheme.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ColorSchemeScraper:
    """配色方案爬取器"""
    
    def __init__(self):
        self.db_path = 'color_schemes.db'
        self.init_database()
        self.schemes = []
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建配色方案表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS color_schemes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            colors TEXT,
            source TEXT,
            scraped_at TEXT,
            popularity INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 0
        )
        ''')
        
        # 创建布局方案表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS layout_schemes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            layout_json TEXT,
            source TEXT,
            scraped_at TEXT,
            popularity INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 0
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def scrape_color_hunt(self):
        """从Color Hunt网站爬取配色方案"""
        import re
        logger.info("开始从Color Hunt爬取配色方案...")
        
        url = "https://colorhunt.co/popular"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Referer": "https://www.google.com/"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试不同的选择器
            color_palettes = soup.find_all('div', class_='palette')
            if not color_palettes:
                color_palettes = soup.find_all('div', attrs={'data-palette': True})
            
            if not color_palettes:
                # 尝试直接从脚本标签中提取数据
                script_tags = soup.find_all('script')
                for script in script_tags:
                    if 'palettes' in script.text or 'colors' in script.text:
                        # 尝试匹配配色方案数据
                        palette_matches = re.findall(r'\[\s*["#\w]+\s*(?:,\s*["#\w]+\s*){3,}\]', script.text)
                        for match in palette_matches[:5]:
                            try:
                                colors = json.loads(match)
                                # 确保是有效的颜色格式
                                valid_colors = []
                                for color in colors:
                                    if isinstance(color, str) and (color.startswith('#') or color.startswith('rgb')):
                                        valid_colors.append(color)
                                if len(valid_colors) >= 4:
                                    scheme = {
                                        'name': f'ColorHunt_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{len(self.schemes)}',
                                        'colors': valid_colors,
                                        'source': 'colorhunt.co',
                                        'scraped_at': datetime.now().isoformat()
                                    }
                                    self.schemes.append(scheme)
                                    self.save_scheme_to_db(scheme)
                            except json.JSONDecodeError:
                                pass
                        break
            else:
                for palette in color_palettes[:10]:  # 只爬取前10个
                    colors = []
                    color_elements = palette.find_all('div', class_='color')
                    if not color_elements:
                        color_elements = palette.find_all('div', style=re.compile('background-color'))
                    
                    for color in color_elements:
                        if color.get('style'):
                            style = color.get('style')
                            if 'background-color' in style:
                                color_hex = style.split('background-color:')[-1].split(';')[0].strip()
                            else:
                                color_hex = style.split(':')[-1].strip(';')
                            colors.append(color_hex)
                    
                    if len(colors) >= 4:  # 确保有足够的颜色
                        scheme = {
                            'name': f'ColorHunt_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{len(self.schemes)}',
                            'colors': colors,
                            'source': 'colorhunt.co',
                            'scraped_at': datetime.now().isoformat()
                        }
                        self.schemes.append(scheme)
                        self.save_scheme_to_db(scheme)
            
            logger.info(f"从Color Hunt成功爬取 {len(self.schemes)} 个配色方案")
            
        except Exception as e:
            logger.error(f"从Color Hunt爬取失败: {str(e)}")
            # 添加备用配色方案
            self.add_fallback_schemes()
    
    def add_fallback_schemes(self):
        """添加备用配色方案"""
        logger.info("添加备用配色方案...")
        
        fallback_schemes = [
            {
                'name': f'Fallback_{datetime.now().strftime("%Y%m%d_%H%M%S")}_1',
                'colors': ['#f8fafc', '#3b82f6', '#60a5fa', '#1e3a8a'],
                'source': 'fallback',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'name': f'Fallback_{datetime.now().strftime("%Y%m%d_%H%M%S")}_2',
                'colors': ['#fef3c7', '#f59e0b', '#d97706', '#92400e'],
                'source': 'fallback',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'name': f'Fallback_{datetime.now().strftime("%Y%m%d_%H%M%S")}_3',
                'colors': ['#ecfdf5', '#10b981', '#34d399', '#065f46'],
                'source': 'fallback',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'name': f'Fallback_{datetime.now().strftime("%Y%m%d_%H%M%S")}_4',
                'colors': ['#fdf2f8', '#ec4899', '#f472b6', '#be185d'],
                'source': 'fallback',
                'scraped_at': datetime.now().isoformat()
            }
        ]
        
        for scheme in fallback_schemes:
            self.schemes.append(scheme)
            self.save_scheme_to_db(scheme)
    
    def scrape_coolors(self):
        """从Coolors网站爬取配色方案"""
        logger.info("开始从Coolors爬取配色方案...")
        
        url = "https://coolors.co/palettes/popular"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Coolors使用动态加载，我们尝试从静态内容中提取
            script_tags = soup.find_all('script')
            for script in script_tags:
                if 'palettes' in script.text:
                    # 尝试提取配色方案数据
                    import re
                    palette_data = re.search(r'palettes\s*=\s*(\[.*?\])', script.text, re.DOTALL)
                    if palette_data:
                        try:
                            palettes = json.loads(palette_data.group(1))
                            for i, palette in enumerate(palettes[:5]):  # 只处理前5个
                                if isinstance(palette, list) and len(palette) >= 4:
                                    scheme = {
                                        'name': f'Coolors_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{len(self.schemes)}',
                                        'colors': palette,
                                        'source': 'coolors.co',
                                        'scraped_at': datetime.now().isoformat()
                                    }
                                    self.schemes.append(scheme)
                                    self.save_scheme_to_db(scheme)
                        except json.JSONDecodeError:
                            pass
                    break
            
            logger.info(f"从Coolors成功爬取 {len(self.schemes)} 个配色方案")
            
        except Exception as e:
            logger.error(f"从Coolors爬取失败: {str(e)}")
    
    def save_scheme_to_db(self, scheme):
        """保存配色方案到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO color_schemes (name, colors, source, scraped_at)
        VALUES (?, ?, ?, ?)
        ''', (scheme['name'], json.dumps(scheme['colors']), scheme['source'], scheme['scraped_at']))
        
        conn.commit()
        conn.close()
    
    def get_latest_schemes(self, limit=5):
        """获取最新的配色方案"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, name, colors, source, scraped_at FROM color_schemes
        ORDER BY scraped_at DESC
        LIMIT ?
        ''', (limit,))
        
        schemes = []
        for row in cursor.fetchall():
            schemes.append({
                'id': row[0],
                'name': row[1],
                'colors': json.loads(row[2]),
                'source': row[3],
                'scraped_at': row[4]
            })
        
        conn.close()
        return schemes
    
    def apply_scheme_to_frontend(self, scheme):
        """将配色方案应用到前端"""
        logger.info(f"应用配色方案: {scheme['name']}")
        
        # 读取当前的index.html文件
        index_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/templates/index.html'
        
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换body的背景色
            if len(scheme['colors']) >= 1:
                content = content.replace('bg-gray-50', f'bg-[{scheme["colors"][0]}]')
            
            # 替换主色调（蓝色）
            if len(scheme['colors']) >= 2:
                # 替换渐变背景
                content = content.replace('from-blue-500 to-blue-600', f'from-[{scheme["colors"][1]}] to-[{scheme["colors"][2]}]')
                # 替换边框颜色
                content = content.replace('border-blue-500', f'border-[{scheme["colors"][1]}]')
                content = content.replace('ring-blue-100', f'ring-[{scheme["colors"][1]}20]')
                content = content.replace('text-blue-500', f'text-[{scheme["colors"][1]}]')
            
            # 替换文本颜色
            if len(scheme['colors']) >= 4:
                content = content.replace('text-gray-800', f'text-[{scheme["colors"][3]}]')
            
            # 保存修改后的文件
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"配色方案 {scheme['name']} 已成功应用到前端")
            
        except Exception as e:
            logger.error(f"应用配色方案失败: {str(e)}")
    
    def run(self):
        """运行爬取器"""
        logger.info("启动配色方案爬取器...")
        
        # 爬取配色方案
        self.scrape_color_hunt()
        self.scrape_coolors()
        
        # 获取最新的配色方案并应用
        if self.schemes:
            latest_scheme = self.schemes[0]
            self.apply_scheme_to_frontend(latest_scheme)
        else:
            # 如果没有新爬取的，使用数据库中最新的
            latest_schemes = self.get_latest_schemes(1)
            if latest_schemes:
                self.apply_scheme_to_frontend(latest_schemes[0])
        
        logger.info("配色方案爬取器运行完成")


if __name__ == "__main__":
    scraper = ColorSchemeScraper()
    scraper.run()
