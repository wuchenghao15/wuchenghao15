#!/usr/bin/env python3
"""
用户头像服务
===============
提供AI自动生成头像、头像管理功能。
"""
import os
import base64
import sqlite3
import logging
from datetime import datetime
from typing import Optional

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('AvatarService')


class AvatarService:
    """用户头像服务"""

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_avatars (
                    user_id TEXT PRIMARY KEY,
                    avatar_data TEXT,
                    generated_by TEXT DEFAULT 'ai',
                    generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def generate_ai_avatar(self, username: str) -> str:
        """使用AI生成头像（基于用户名的彩色几何图案）"""
        import random
        import io
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            return self._generate_simple_avatar(username)

        size = 128
        colors = [
            (99, 102, 241), (139, 92, 246), (168, 85, 247),
            (236, 72, 153), (249, 115, 22), (234, 179, 8),
            (34, 197, 94), (20, 184, 166), (6, 182, 212),
            (59, 130, 246), (14, 165, 233), (139, 92, 246)
        ]

        img = Image.new('RGB', (size, size), (30, 30, 60))
        draw = ImageDraw.Draw(img)

        seed = hash(username) % 1000
        random.seed(seed)

        base_color = colors[seed % len(colors)]
        accent_color = colors[(seed + 5) % len(colors)]

        for i in range(3):
            x = random.randint(0, size)
            y = random.randint(0, size)
            r = random.randint(20, 60)
            alpha = random.randint(30, 80)
            draw.ellipse([x-r, y-r, x+r, y+r], fill=(base_color[0], base_color[1], base_color[2], alpha))

        center_x, center_y = size // 2, size // 2
        draw.ellipse([center_x-45, center_y-45, center_x+45, center_y+45], fill=base_color)

        initial = username[0].upper()
        font_size = 48
        text_color = (255, 255, 255)
        draw.text((center_x, center_y), initial, fill=text_color, 
                  font=None, anchor='mm')

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        avatar_data = base64.b64encode(buffer.read()).decode('utf-8')
        
        return f"data:image/png;base64,{avatar_data}"

    def _generate_simple_avatar(self, username: str) -> str:
        """生成简单的SVG头像（备用方案）"""
        import random
        seed = hash(username) % 1000
        random.seed(seed)
        
        colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f97316', '#22c55e', '#06b6d4']
        bg_color = colors[seed % len(colors)]
        initial = username[0].upper()
        
        svg = f'''
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
            <circle cx="64" cy="64" r="64" fill="{bg_color}"/>
            <text x="64" y="76" font-family="Arial, sans-serif" font-size="48" 
                  font-weight="bold" fill="white" text-anchor="middle">{initial}</text>
        </svg>
        '''
        return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"

    def get_user_avatar(self, user_id: str) -> Optional[str]:
        """获取用户头像"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT avatar FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row and row['avatar']:
                return row['avatar']
            
            cursor.execute('SELECT avatar_data FROM user_avatars WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row and row['avatar_data']:
                return row['avatar_data']
            
            return None

    def set_user_avatar(self, user_id: str, avatar_data: str):
        """设置用户头像"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('UPDATE users SET avatar = ? WHERE id = ?', (avatar_data, user_id))
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_avatars (user_id, avatar_data, generated_by, updated_at)
                VALUES (?, ?, 'user', ?)
            ''', (user_id, avatar_data, datetime.now().isoformat()))
            
            conn.commit()
            logger.info(f"用户 {user_id} 设置头像成功")

    def generate_and_save_avatar(self, user_id: str, username: str) -> str:
        """生成并保存AI头像"""
        avatar_data = self.generate_ai_avatar(username)
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('UPDATE users SET avatar = ? WHERE id = ?', (avatar_data, user_id))
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_avatars (user_id, avatar_data, generated_by, generated_at, updated_at)
                VALUES (?, ?, 'ai', ?, ?)
            ''', (user_id, avatar_data, datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
        
        logger.info(f"为用户 {user_id} 生成AI头像")
        return avatar_data

    def ensure_avatar_exists(self, user_id: str, username: str) -> str:
        """确保用户有头像，没有则生成"""
        avatar = self.get_user_avatar(user_id)
        if avatar:
            return avatar
        return self.generate_and_save_avatar(user_id, username)


avatar_service = AvatarService()