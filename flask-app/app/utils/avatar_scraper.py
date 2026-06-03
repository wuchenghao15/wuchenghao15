# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
头像爬虫工具
用于爬取可爱的头像供用户选择
"""

import logging
logger = logging.getLogger(__name__)
import os
import requests
import shutil
from app.utils.logging import logger

class AvatarScraper:
    """头像爬虫类"""

    def __init__(self):
        self.base_url = "https://thispersondoesnotexist.com"
        self.save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'static', 'avatars', 'scraped')
        self.avatar_count = 10

    def ensure_save_dir(self):
        """确保保存目录存在"""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            logger.info(f"创建保存目录: {self.save_dir}")

    def scrape_avatars(self):
        """爬取头像"""
        logger.info("开始爬取可爱头像...")
        self.ensure_save_dir()

        for i in range(self.avatar_count):
            try:
                # 发送请求获取头像
                response = requests.get(self.base_url, stream=True, timeout=10)
                response.raise_for_status()

                # 保存头像
                avatar_path = os.path.join(self.save_dir, f"avatar_{i+1}.jpg")
                with open(avatar_path, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)

                logger.info(f"成功爬取头像 {i+1}/{self.avatar_count}: {avatar_path}")
            except Exception as e:
                logger.error(f"爬取头像 {i+1} 失败: {str(e)}")

        logger.info("头像爬取完成")

    def get_scraped_avatars(self):
        """获取已爬取的头像列表"""
        self.ensure_save_dir()
        avatars = []
        for filename in os.listdir(self.save_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                avatars.append({
                    'filename': filename,
                    'path': f"/static/avatars/scraped/{filename}"
                })

        return avatars
