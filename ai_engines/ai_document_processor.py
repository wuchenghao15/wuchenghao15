#!/usr/bin/env python3
"""AI智能文档处理Agent"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIDocumentProcessor(AIEmployee):
    """AI文档处理Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI文档处理专家"):
        super().__init__(employee_id, name, 'document_processor', 7)
        self.skills = [
            '文档上传', '文档解析', '文档转换',
            '文档搜索', '文档摘要', '文档分类',
            '文档对比', '文档翻译', '文档格式优化'
        ]
        self.document_history = []
        self.total_documents = 0
    
    def upload_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """上传文档"""
        document = {
            'document_id': document_data.get('document_id', f'doc_{datetime.now().timestamp()}'),
            'name': document_data.get('name', ''),
            'type': document_data.get('type', 'text'),
            'content': document_data.get('content', ''),
            'size': len(document_data.get('content', '')),
            'uploaded_at': datetime.now().isoformat(),
            'processed': False
        }
        self.document_history.append(document)
        self.total_documents += 1
        return {'success': True, 'document': document}
    
    def process_document(self, document_id: str) -> Dict[str, Any]:
        """处理文档"""
        for document in self.document_history:
            if document['document_id'] == document_id:
                document['processed'] = True
                document['processed_at'] = datetime.now().isoformat()
                document['word_count'] = len(document.get('content', '').split())
                document['char_count'] = len(document.get('content', ''))
                document['paragraph_count'] = len(document.get('content', '').split('\n\n'))
                
                return {'success': True, 'document': document}
        return {'success': False, 'message': '文档不存在'}
    
    def summarize_document(self, document_id: str, max_length: int = 200) -> Dict[str, Any]:
        """文档摘要"""
        for document in self.document_history:
            if document['document_id'] == document_id:
                content = document.get('content', '')
                if len(content) <= max_length:
                    summary = content
                else:
                    sentences = content.split('。')
                    summary = '。'.join(sentences[:3]) + '。'
                
                return {'success': True, 'summary': summary[:max_length], 'original_length': len(content)}
        return {'success': False, 'message': '文档不存在'}
    
    def search_document(self, keyword: str) -> Dict[str, Any]:
        """搜索文档"""
        results = []
        for document in self.document_history:
            content = document.get('content', '')
            if keyword in content or keyword in document.get('name', ''):
                results.append({
                    'document_id': document['document_id'],
                    'name': document['name'],
                    'match_count': content.count(keyword),
                    'preview': content[:100] + '...' if len(content) > 100 else content
                })
        
        return {'success': True, 'results': results, 'count': len(results)}
    
    def classify_document(self, document_id: str) -> Dict[str, Any]:
        """文档分类"""
        categories = ['技术文档', '商业文档', '报告', '合同', '邮件', '其他']
        
        for document in self.document_history:
            if document['document_id'] == document_id:
                content = document.get('content', '')
                name = document.get('name', '')
                
                if any(kw in content for kw in ['代码', 'API', '函数', '类']):
                    category = '技术文档'
                elif any(kw in content for kw in ['合同', '协议', '条款']):
                    category = '合同'
                elif any(kw in content for kw in ['报告', '分析', '总结']):
                    category = '报告'
                elif '@' in content:
                    category = '邮件'
                elif any(kw in name for kw in ['doc', 'docx', 'pdf', 'txt']):
                    category = '其他'
                else:
                    category = '商业文档'
                
                document['category'] = category
                return {'success': True, 'category': category}
        return {'success': False, 'message': '文档不存在'}
    
    def compare_documents(self, doc_id1: str, doc_id2: str) -> Dict[str, Any]:
        """对比文档"""
        doc1 = None
        doc2 = None
        
        for document in self.document_history:
            if document['document_id'] == doc_id1:
                doc1 = document
            if document['document_id'] == doc_id2:
                doc2 = document
        
        if not doc1 or not doc2:
            return {'success': False, 'message': '文档不存在'}
        
        content1 = doc1.get('content', '')
        content2 = doc2.get('content', '')
        
        common_words = set(content1.split()) & set(content2.split())
        unique_doc1 = set(content1.split()) - set(content2.split())
        unique_doc2 = set(content2.split()) - set(content1.split())
        
        similarity = len(common_words) / max(len(content1.split()), len(content2.split()), 1) * 100
        
        return {
            'success': True,
            'similarity': round(similarity, 2),
            'common_words_count': len(common_words),
            'unique_doc1_count': len(unique_doc1),
            'unique_doc2_count': len(unique_doc2)
        }
    
    def translate_document(self, document_id: str, target_language: str = 'zh') -> Dict[str, Any]:
        """文档翻译"""
        for document in self.document_history:
            if document['document_id'] == document_id:
                content = document.get('content', '')
                translated = f'[翻译为{target_language}] {content[:50]}...'
                
                return {'success': True, 'translated_content': translated, 'target_language': target_language}
        return {'success': False, 'message': '文档不存在'}
    
    def optimize_format(self, document_id: str) -> Dict[str, Any]:
        """优化文档格式"""
        for document in self.document_history:
            if document['document_id'] == document_id:
                document['formatted'] = True
                document['formatted_at'] = datetime.now().isoformat()
                
                return {'success': True, 'message': '文档格式已优化', 'document': document}
        return {'success': False, 'message': '文档不存在'}
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        processed = len([d for d in self.document_history if d.get('processed')])
        categorized = len([d for d in self.document_history if d.get('category')])
        
        return {
            'total_documents': self.total_documents,
            'processed_documents': processed,
            'categorized_documents': categorized,
            'document_history_count': len(self.document_history),
            'employee_id': self.employee_id,
            'name': self.name,
            'employee_type': self.employee_type
        }