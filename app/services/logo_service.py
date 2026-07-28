#!/usr/bin/env python3
"""
系统LOGO服务
===============
提供系统LOGO的生成和管理功能。
根据系统功能设计初衷（智能学习评估系统）AI生成LOGO。
"""
import os
import base64
import sqlite3
import logging
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('LogoService')


class LogoService:
    """系统LOGO服务"""

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logo (
                    id TEXT PRIMARY KEY,
                    logo_data TEXT NOT NULL,
                    logo_type TEXT DEFAULT 'svg',
                    theme TEXT DEFAULT 'default',
                    generated_by TEXT DEFAULT 'ai',
                    generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def generate_system_logo(self, theme: str = 'default') -> str:
        """根据系统功能设计初衷AI生成LOGO
        
        系统定位：智能学习评估系统（MTSCOS AI）
        设计元素：
        1. AI大脑/神经网络 - 代表智能、人工智能
        2. 书本/学习 - 代表教育、学习
        3. 评分/评估 - 代表评估、考试
        4. 知识/智慧 - 代表知识获取
        """
        logos = {
            'default': self._generate_default_logo(),
            'brain': self._generate_brain_logo(),
            'education': self._generate_education_logo(),
            'neural': self._generate_neural_logo(),
            'modern': self._generate_modern_logo()
        }
        
        return logos.get(theme, logos['default'])

    def _generate_default_logo(self) -> str:
        """生成默认LOGO - 结合大脑和书本的设计"""
        svg = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
    <defs>
        <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#6366f1"/>
            <stop offset="100%" style="stop-color:#8b5cf6"/>
        </linearGradient>
        <linearGradient id="bookGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#f59e0b"/>
            <stop offset="100%" style="stop-color:#ef4444"/>
        </linearGradient>
        <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
    </defs>
    
    <circle cx="64" cy="64" r="60" fill="url(#bgGradient)" filter="url(#glow)"/>
    
    <ellipse cx="64" cy="50" rx="28" ry="22" fill="rgba(255,255,255,0.15)"/>
    <ellipse cx="64" cy="68" rx="20" ry="16" fill="rgba(255,255,255,0.1)"/>
    
    <path d="M42 50 Q42 35 52 35 Q64 35 64 50 Q64 65 76 65 Q86 65 86 50 Q86 35 64 35" 
          fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="2"/>
    <path d="M48 45 Q48 38 56 38 Q64 38 64 45 Q64 52 72 52 Q80 52 80 45 Q80 38 64 38" 
          fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
    <circle cx="48" cy="55" r="4" fill="rgba(255,255,255,0.5)"/>
    <circle cx="80" cy="55" r="4" fill="rgba(255,255,255,0.5)"/>
    <circle cx="64" cy="62" r="6" fill="rgba(255,255,255,0.6)"/>
    
    <rect x="36" y="80" width="56" height="28" rx="4" fill="url(#bookGradient)"/>
    <rect x="38" y="82" width="24" height="24" rx="2" fill="rgba(255,255,255,0.1)"/>
    <rect x="66" y="82" width="24" height="24" rx="2" fill="rgba(0,0,0,0.1)"/>
    <line x1="62" y1="82" x2="62" y2="106" stroke="rgba(255,255,255,0.3)" stroke-width="2"/>
    <line x1="42" y1="92" x2="58" y2="92" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
    <line x1="42" y1="98" x2="56" y2="98" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
    <line x1="66" y1="92" x2="82" y2="92" stroke="rgba(0,0,0,0.2)" stroke-width="1.5"/>
    <line x1="66" y1="98" x2="80" y2="98" stroke="rgba(0,0,0,0.2)" stroke-width="1.5"/>
    
    <polygon points="64,115 60,108 68,108" fill="#ffffff"/>
</svg>
        '''
        return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"

    def _generate_brain_logo(self) -> str:
        """生成大脑主题LOGO"""
        svg = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
    <defs>
        <radialGradient id="brainGradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" style="stop-color:#a855f7"/>
            <stop offset="100%" style="stop-color:#6366f1"/>
        </radialGradient>
    </defs>
    <circle cx="64" cy="64" r="60" fill="url(#brainGradient)"/>
    <ellipse cx="45" cy="55" rx="20" ry="25" fill="rgba(255,255,255,0.2)"/>
    <ellipse cx="83" cy="55" rx="20" ry="25" fill="rgba(255,255,255,0.2)"/>
    <ellipse cx="64" cy="75" rx="18" ry="15" fill="rgba(255,255,255,0.15)"/>
    <circle cx="38" cy="50" r="3" fill="rgba(255,255,255,0.6)"/>
    <circle cx="90" cy="50" r="3" fill="rgba(255,255,255,0.6)"/>
    <circle cx="64" cy="70" r="4" fill="rgba(255,255,255,0.7)"/>
    <path d="M40 60 Q45 55 50 60 Q55 65 60 60 Q65 55 70 60 Q75 65 80 60" 
          fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="2"/>
    <path d="M35 55 Q45 45 55 55 Q65 65 75 55 Q85 45 95 55" 
          fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1.5"/>
</svg>
        '''
        return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"

    def _generate_education_logo(self) -> str:
        """生成教育主题LOGO"""
        svg = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
    <defs>
        <linearGradient id="eduGradient" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#22c55e"/>
            <stop offset="100%" style="stop-color:#06b6d4"/>
        </linearGradient>
    </defs>
    <circle cx="64" cy="64" r="60" fill="url(#eduGradient)"/>
    <path d="M30 90 L64 35 L98 90 Z" fill="rgba(255,255,255,0.2)"/>
    <path d="M38 80 L64 45 L90 80 Z" fill="rgba(255,255,255,0.3)"/>
    <path d="M46 70 L64 50 L82 70 Z" fill="rgba(255,255,255,0.4)"/>
    <circle cx="64" cy="65" r="8" fill="rgba(255,255,255,0.8)"/>
    <path d="M60 65 L68 65 M64 61 L64 69" stroke="#6366f1" stroke-width="2" stroke-linecap="round"/>
    <rect x="50" y="100" width="28" height="8" rx="2" fill="rgba(255,255,255,0.3)"/>
</svg>
        '''
        return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"

    def _generate_neural_logo(self) -> str:
        """生成神经网络主题LOGO"""
        svg = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
    <defs>
        <linearGradient id="neuralGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#ec4899"/>
            <stop offset="100%" style="stop-color:#f97316"/>
        </linearGradient>
    </defs>
    <circle cx="64" cy="64" r="60" fill="url(#neuralGradient)"/>
    <circle cx="35" cy="40" r="8" fill="rgba(255,255,255,0.7)"/>
    <circle cx="93" cy="40" r="8" fill="rgba(255,255,255,0.7)"/>
    <circle cx="64" cy="64" r="12" fill="rgba(255,255,255,0.9)"/>
    <circle cx="35" cy="88" r="8" fill="rgba(255,255,255,0.7)"/>
    <circle cx="93" cy="88" r="8" fill="rgba(255,255,255,0.7)"/>
    <line x1="35" y1="40" x2="64" y2="64" stroke="rgba(255,255,255,0.4)" stroke-width="2"/>
    <line x1="93" y1="40" x2="64" y2="64" stroke="rgba(255,255,255,0.4)" stroke-width="2"/>
    <line x1="35" y1="88" x2="64" y2="64" stroke="rgba(255,255,255,0.4)" stroke-width="2"/>
    <line x1="93" y1="88" x2="64" y2="64" stroke="rgba(255,255,255,0.4)" stroke-width="2"/>
    <circle cx="18" cy="64" r="5" fill="rgba(255,255,255,0.5)"/>
    <circle cx="110" cy="64" r="5" fill="rgba(255,255,255,0.5)"/>
    <line x1="18" y1="64" x2="35" y2="40" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
    <line x1="18" y1="64" x2="35" y2="88" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
    <line x1="93" y1="40" x2="110" y2="64" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
    <line x1="93" y1="88" x2="110" y2="64" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
</svg>
        '''
        return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"

    def _generate_modern_logo(self) -> str:
        """生成现代简约主题LOGO"""
        svg = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
    <defs>
        <linearGradient id="modernGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#0ea5e9"/>
            <stop offset="100%" style="stop-color:#8b5cf6"/>
        </linearGradient>
    </defs>
    <rect x="4" y="4" width="120" height="120" rx="30" fill="url(#modernGradient)"/>
    <rect x="20" y="20" width="24" height="88" rx="4" fill="rgba(255,255,255,0.2)"/>
    <rect x="48" y="20" width="24" height="50" rx="4" fill="rgba(255,255,255,0.3)"/>
    <rect x="76" y="20" width="24" height="70" rx="4" fill="rgba(255,255,255,0.25)"/>
    <circle cx="64" cy="95" r="12" fill="rgba(255,255,255,0.9)"/>
    <path d="M58 95 L62 99 L70 91" stroke="#6366f1" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" 
    fill="none"/>
</svg>
        '''
        return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"

    def get_system_logo(self, theme: str = 'default') -> str:
        """获取系统LOGO，不存在则生成"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT logo_data FROM system_logo WHERE theme = ?', (theme,))
            row = cursor.fetchone()
            
            if row and row['logo_data']:
                return row['logo_data']
            
            logo_data = self.generate_system_logo(theme)
            
            cursor.execute('''
                INSERT OR REPLACE INTO system_logo (id, logo_data, logo_type, theme, generated_at, updated_at)
                VALUES (?, ?, 'svg', ?, ?, ?)
            ''', (theme, logo_data, theme, datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
            
            logger.info(f"生成系统LOGO: {theme}")
            return logo_data

    def set_custom_logo(self, logo_data: str, theme: str = 'custom'):
        """设置自定义LOGO"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO system_logo (id, logo_data, logo_type, theme, generated_by, generated_at,
                updated_at)
                VALUES (?, ?, 'custom', ?, 'user', ?, ?)
            ''', (theme, logo_data, theme, datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
            logger.info(f"设置自定义LOGO: {theme}")


logo_service = LogoService()