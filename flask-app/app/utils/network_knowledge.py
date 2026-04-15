#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络知识获取模块
负责从网络获取专业知识，整合到知识库
"""

import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

# 配置日志
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
            # 发送请求
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # 解析内容
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 根据URL类型提取知识
            if 'python.org' in url:
                return self._extract_python_knowledge(soup)
            elif 'flask.palletsprojects.com' in url:
                return self._extract_flask_knowledge(soup)
            elif 'sqlite.org' in url:
                return self._extract_sqlite_knowledge(soup)
            elif 'owasp.org' in url:
                return self._extract_owasp_knowledge(soup)
            else:
                return self._extract_generic_knowledge(soup)
        except Exception as e:
            logger.error(f"从 {url} 获取知识失败: {str(e)}")
            return None
    
    def _extract_python_knowledge(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取Python相关知识"""
        knowledge = {
            'python': {}
        }
        
        try:
            # 提取标题
            title = soup.find('h1').text if soup.find('h1') else 'Python Documentation'
            knowledge['python']['title'] = title
            
            # 提取内容
            content = soup.find('div', class_='document')
            if content:
                # 提取章节
                sections = content.find_all('section')
                for section in sections:
                    section_title = section.find('h2').text if section.find('h2') else 'Unknown Section'
                    section_content = section.get_text(separator='\n', strip=True)
                    knowledge['python'][section_title] = section_content[:500]  # 限制内容长度
        except Exception as e:
            logger.error(f"提取Python知识失败: {str(e)}")
        
        return knowledge
    
    def _extract_flask_knowledge(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取Flask相关知识"""
        knowledge = {
            'flask': {}
        }
        
        try:
            # 提取标题
            title = soup.find('h1').text if soup.find('h1') else 'Flask Documentation'
            knowledge['flask']['title'] = title
            
            # 提取内容
            content = soup.find('div', class_='document')
            if content:
                # 提取章节
                sections = content.find_all('section')
                for section in sections:
                    section_title = section.find('h2').text if section.find('h2') else 'Unknown Section'
                    section_content = section.get_text(separator='\n', strip=True)
                    knowledge['flask'][section_title] = section_content[:500]  # 限制内容长度
        except Exception as e:
            logger.error(f"提取Flask知识失败: {str(e)}")
        
        return knowledge
    
    def _extract_sqlite_knowledge(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取SQLite相关知识"""
        knowledge = {
            'database': {}
        }
        
        try:
            # 提取标题
            title = soup.find('h1').text if soup.find('h1') else 'SQLite Documentation'
            knowledge['database']['title'] = title
            
            # 提取内容
            content = soup.find('body')
            if content:
                # 提取章节
                sections = content.find_all('div', class_='section')
                for section in sections:
                    section_title = section.find('h2').text if section.find('h2') else 'Unknown Section'
                    section_content = section.get_text(separator='\n', strip=True)
                    knowledge['database'][section_title] = section_content[:500]  # 限制内容长度
        except Exception as e:
            logger.error(f"提取SQLite知识失败: {str(e)}")
        
        return knowledge
    
    def _extract_owasp_knowledge(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取OWASP相关知识"""
        knowledge = {
            'security': {}
        }
        
        try:
            # 提取标题
            title = soup.find('h1').text if soup.find('h1') else 'OWASP Documentation'
            knowledge['security']['title'] = title
            
            # 提取内容
            content = soup.find('div', class_='wiki-content')
            if content:
                # 提取章节
                sections = content.find_all('div', class_='section')
                for section in sections:
                    section_title = section.find('h2').text if section.find('h2') else 'Unknown Section'
                    section_content = section.get_text(separator='\n', strip=True)
                    knowledge['security'][section_title] = section_content[:500]  # 限制内容长度
        except Exception as e:
            logger.error(f"提取OWASP知识失败: {str(e)}")
        
        return knowledge
    
    def _extract_generic_knowledge(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取通用知识"""
        knowledge = {
            'general': {}
        }
        
        try:
            # 提取标题
            title = soup.find('h1').text if soup.find('h1') else 'Unknown Page'
            knowledge['general']['title'] = title
            
            # 提取内容
            content = soup.find('body')
            if content:
                page_content = content.get_text(separator='\n', strip=True)
                knowledge['general']['content'] = page_content[:1000]  # 限制内容长度
        except Exception as e:
            logger.error(f"提取通用知识失败: {str(e)}")
        
        return knowledge
    
    def search_knowledge(self, query: str) -> Optional[Dict[str, Any]]:
        """搜索知识"""
        try:
            # 使用Google搜索API（需要API密钥）
            # 这里使用一个简单的模拟实现
            search_url = f"https://www.google.com/search?q={query}"
            response = requests.get(search_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # 解析搜索结果
            soup = BeautifulSoup(response.content, 'html.parser')
            search_results = []
            
            # 提取搜索结果
            result_divs = soup.find_all('div', class_='g')
            for i, result in enumerate(result_divs[:5]):  # 只取前5个结果
                title = result.find('h3').text if result.find('h3') else 'No Title'
                link = result.find('a')['href'] if result.find('a') else '#'
                snippet = result.find('div', class_='s').text if result.find('div', class_='s') else ''
                
                search_results.append({
                    'title': title,
                    'link': link,
                    'snippet': snippet
                })
            
            return {
                'query': query,
                'results': search_results
            }
        except Exception as e:
            logger.error(f"搜索知识失败: {str(e)}")
            return None
    
    def fetch_stack_overflow_answers(self, query: str) -> Optional[Dict[str, Any]]:
        """从Stack Overflow获取答案"""
        try:
            # 构建Stack Overflow搜索URL
            stack_url = f"https://stackoverflow.com/search?q={query}"
            response = requests.get(stack_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # 解析搜索结果
            soup = BeautifulSoup(response.content, 'html.parser')
            answers = []
            
            # 提取问题和答案
            question_divs = soup.find_all('div', class_='question-summary')
            for i, question in enumerate(question_divs[:3]):  # 只取前3个问题
                title = question.find('a', class_='question-hyperlink').text if question.find('a', class_='question-hyperlink') else 'No Title'
                link = question.find('a', class_='question-hyperlink')['href'] if question.find('a', class_='question-hyperlink') else '#'
                votes = question.find('span', class_='vote-count-post').text if question.find('span', class_='vote-count-post') else '0'
                answers_count = question.find('div', class_='status').find('strong').text if question.find('div', class_='status') else '0'
                
                answers.append({
                    'title': title,
                    'link': f"https://stackoverflow.com{link}",
                    'votes': votes,
                    'answers_count': answers_count
                })
            
            return {
                'query': query,
                'answers': answers
            }
        except Exception as e:
            logger.error(f"获取Stack Overflow答案失败: {str(e)}")
            return None
    
    def update_knowledge_base(self, knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """更新知识库"""
        try:
            # 从多个来源获取知识
            sources = [
                'https://docs.python.org/3/tutorial/',
                'https://flask.palletsprojects.com/en/2.0.x/',
                'https://www.sqlite.org/docs.html',
                'https://owasp.org/www-project-top-ten/'
            ]
            
            for source in sources:
                knowledge = self.fetch_knowledge(source)
                if knowledge:
                    # 整合知识
                    for category, items in knowledge.items():
                        if category not in knowledge_base:
                            knowledge_base[category] = {}
                        knowledge_base[category].update(items)
            
            logger.info("知识库更新成功")
            return knowledge_base
        except Exception as e:
            logger.error(f"更新知识库失败: {str(e)}")
            return knowledge_base

if __name__ == '__main__':
    # 测试网络知识获取
    knowledge_fetcher = NetworkKnowledge()
    
    # 测试从Python官网获取知识
    print("从Python官网获取知识:")
    python_knowledge = knowledge_fetcher.fetch_knowledge('https://docs.python.org/3/tutorial/')
    if python_knowledge:
        print(f"获取到 {len(python_knowledge.get('python', {}))} 条Python知识")
    
    # 测试从Flask官网获取知识
    print("\n从Flask官网获取知识:")
    flask_knowledge = knowledge_fetcher.fetch_knowledge('https://flask.palletsprojects.com/en/2.0.x/')
    if flask_knowledge:
        print(f"获取到 {len(flask_knowledge.get('flask', {}))} 条Flask知识")
    
    # 测试搜索知识
    print("\n搜索Python异常处理知识:")
    search_result = knowledge_fetcher.search_knowledge('python exception handling best practices')
    if search_result:
        print(f"找到 {len(search_result.get('results', []))} 个搜索结果")
        for result in search_result.get('results', [])[:2]:
            print(f"- {result['title']}")
            print(f"  {result['link']}")
    
    # 测试从Stack Overflow获取答案
    print("\n从Stack Overflow获取Python问题答案:")
    stack_result = knowledge_fetcher.fetch_stack_overflow_answers('python sqlite3 tutorial')
    if stack_result:
        print(f"找到 {len(stack_result.get('answers', []))} 个答案")
        for answer in stack_result.get('answers', [])[:2]:
            print(f"- {answer['title']}")
            print(f"  投票: {answer['votes']}, 答案数: {answer['answers_count']}")
            print(f"  {answer['link']}")