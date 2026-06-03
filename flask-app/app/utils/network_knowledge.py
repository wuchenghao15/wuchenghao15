# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络知识获取模块
负责从网络获取专业知识并整合到知识库
"""

import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

logger = logging.getLogger('network_knowledge')


class NetworkKnowledge:
    """网络知识获取类"""

    def __init__(self):
        """初始化网络知识获取"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 10
        logger.info("网络知识获取模块初始化完成")

    def fetch_knowledge(self, url: str) -> Optional[Dict[str, Any]]:
        """从指定URL获取知识"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            if 'python.org' in url:
                return self._extract_python_knowledge(soup)
            else:
                return self._extract_general_knowledge(soup)

        except requests.RequestException as e:
            logger.error(f"获取知识失败: {str(e)}")
            return None

    def _extract_python_knowledge(self, soup) -> Dict[str, Any]:
        """从Python官网提取知识"""
        knowledge = {
            'source': 'python.org',
            'title': '',
            'content': '',
            'code_examples': []
        }

        title_elem = soup.find('h1')
        if title_elem:
            knowledge['title'] = title_elem.get_text(strip=True)

        content_elem = soup.find('div', class_='body')
        if content_elem:
            knowledge['content'] = content_elem.get_text(strip=True)

        code_blocks = soup.find_all('pre')
        for code in code_blocks:
            knowledge['code_examples'].append(code.get_text(strip=True))

        return knowledge

    def _extract_general_knowledge(self, soup) -> Dict[str, Any]:
        """从一般网页提取知识"""
        knowledge = {
            'source': 'general',
            'title': '',
            'content': '',
            'code_examples': []
        }

        title_elem = soup.find('title')
        if title_elem:
            knowledge['title'] = title_elem.get_text(strip=True)

        content_elem = soup.find('article') or soup.find('main') or soup.find('body')
        if content_elem:
            knowledge['content'] = content_elem.get_text(strip=True)

        return knowledge
