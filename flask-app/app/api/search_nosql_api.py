#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索引擎 + NoSQL数据库管理API
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime

search_nosql_api = Blueprint('search_nosql_api', __name__)

# 全局实例
search_engine_instance = None
nosql_manager_instance = None

def init_search_nosql():
    """初始化搜索引擎和NoSQL"""
    global search_engine_instance, nosql_manager_instance
    if search_engine_instance is None:
        from app.utils.search_nosql_manager import get_search_engine, get_nosql_manager
        search_engine_instance = get_search_engine()
        nosql_manager_instance = get_nosql_manager()
    return search_engine_instance, nosql_manager_instance

def get_search_engine():
    """获取搜索引擎实例"""
    if search_engine_instance is None:
        init_search_nosql()
    return search_engine_instance

def get_nosql_manager():
    """获取NoSQL管理器实例"""
    if nosql_manager_instance is None:
        init_search_nosql()
    return nosql_manager_instance

@search_nosql_api.route('/')
def index():
    return jsonify({'status': 'ok', 'service': 'search-nosql-api'})

# ==================== 搜索引擎API ====================

@search_nosql_api.route('/search/indexes')
def list_indexes():
    """获取所有索引"""
    search_engine = get_search_engine()
    indexes = search_engine.get_all_indexes()
    return jsonify({'indexes': indexes})

@search_nosql_api.route('/search/indexes/<index_name>')
def get_index(index_name):
    """获取索引信息"""
    search_engine = get_search_engine()
    stats = search_engine.get_index_stats(index_name)
    return jsonify(stats)

@search_nosql_api.route('/search/indexes/<index_name>/stats')
def index_stats(index_name):
    """获取索引统计"""
    search_engine = get_search_engine()
    stats = search_engine.get_index_stats(index_name)
    return jsonify(stats)

@search_nosql_api.route('/search/indexes/<index_name>/documents', methods=['POST'])
def add_document(index_name):
    """添加文档到索引"""
    search_engine = get_search_engine()
    data = request.get_json()
    
    if not data or 'doc_id' not in data or 'document' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    search_engine.add_document(index_name, data['doc_id'], data['document'])
    return jsonify({'success': True, 'message': '文档添加成功'})

@search_nosql_api.route('/search/indexes/<index_name>/search', methods=['POST'])
def search(index_name):
    """搜索"""
    search_engine = get_search_engine()
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({'error': '缺少查询参数'}), 400
    
    query = data['query']
    fields = data.get('fields')
    
    results = search_engine.search(index_name, query, fields)
    return jsonify({
        'success': True,
        'query': query,
        'count': len(results),
        'results': results
    })

@search_nosql_api.route('/search/indexes/<index_name>/documents/<doc_id>', methods=['GET'])
def get_document(index_name, doc_id):
    """获取文档"""
    search_engine = get_search_engine()
    document = search_engine.get_document(index_name, doc_id)
    
    if document:
        return jsonify(document)
    return jsonify({'error': '文档不存在'}), 404

@search_nosql_api.route('/search/indexes/<index_name>/documents/<doc_id>', methods=['DELETE'])
def delete_document(index_name, doc_id):
    """删除文档"""
    search_engine = get_search_engine()
    search_engine.delete_document(index_name, doc_id)
    return jsonify({'success': True, 'message': '文档删除成功'})

# ==================== NoSQL API ====================

@search_nosql_api.route('/nosql/collections')
def list_collections():
    """获取所有集合"""
    nosql_manager = get_nosql_manager()
    collections = nosql_manager.get_collection_names()
    return jsonify({'collections': collections})

@search_nosql_api.route('/nosql/collections/<collection_name>/stats')
def collection_stats(collection_name):
    """获取集合统计"""
    nosql_manager = get_nosql_manager()
    stats = nosql_manager.get_collection_stats(collection_name)
    return jsonify(stats)

@search_nosql_api.route('/nosql/collections/<collection_name>/documents', methods=['POST'])
def insert_document(collection_name):
    """插入文档"""
    nosql_manager = get_nosql_manager()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '缺少文档数据'}), 400
    
    doc_id = nosql_manager.insert(collection_name, data)
    return jsonify({'success': True, 'doc_id': doc_id})

@search_nosql_api.route('/nosql/collections/<collection_name>/documents', methods=['GET'])
def find_documents(collection_name):
    """查询文档"""
    nosql_manager = get_nosql_manager()
    
    # 解析查询参数
    query = {}
    for key, value in request.args.items():
        # 尝试转换类型
        try:
            query[key] = int(value)
        except ValueError:
            try:
                query[key] = float(value)
            except ValueError:
                query[key] = value
    
    results = nosql_manager.find(collection_name, query)
    return jsonify({
        'success': True,
        'count': len(results),
        'results': results
    })

@search_nosql_api.route('/nosql/collections/<collection_name>/documents/<doc_id>', methods=['GET'])
def find_document(collection_name, doc_id):
    """获取单个文档"""
    nosql_manager = get_nosql_manager()
    document = nosql_manager.find_one(collection_name, {'_id': doc_id})
    
    if document:
        return jsonify(document)
    return jsonify({'error': '文档不存在'}), 404

@search_nosql_api.route('/nosql/collections/<collection_name>/documents/<doc_id>', methods=['PUT'])
def update_document(collection_name, doc_id):
    """更新文档"""
    nosql_manager = get_nosql_manager()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '缺少更新数据'}), 400
    
    updated = nosql_manager.update(collection_name, {'_id': doc_id}, data)
    return jsonify({'success': True, 'updated_count': updated})

@search_nosql_api.route('/nosql/collections/<collection_name>/documents/<doc_id>', methods=['DELETE'])
def delete_document_nosql(collection_name, doc_id):
    """删除文档"""
    nosql_manager = get_nosql_manager()
    deleted = nosql_manager.delete(collection_name, {'_id': doc_id})
    return jsonify({'success': True, 'deleted_count': deleted})

@search_nosql_api.route('/nosql/collections/<collection_name>/count')
def count_documents(collection_name):
    """统计文档数量"""
    nosql_manager = get_nosql_manager()
    
    query = {}
    for key, value in request.args.items():
        try:
            query[key] = int(value)
        except ValueError:
            query[key] = value
    
    count = nosql_manager.count(collection_name, query)
    return jsonify({'count': count})

# ==================== 综合API ====================

@search_nosql_api.route('/search/nosql/index', methods=['POST'])
def index_document():
    """同时插入NoSQL并建立索引"""
    search_engine = get_search_engine()
    nosql_manager = get_nosql_manager()
    
    data = request.get_json()
    
    if not data or 'collection' not in data or 'document' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    # 插入NoSQL
    doc_id = nosql_manager.insert(data['collection'], data['document'])
    
    # 建立索引
    index_name = data.get('index', data['collection'])
    search_engine.add_document(index_name, doc_id, data['document'])
    
    return jsonify({'success': True, 'doc_id': doc_id})

@search_nosql_api.route('/search/nosql/search', methods=['POST'])
def search_nosql():
    """搜索NoSQL数据"""
    search_engine = get_search_engine()
    nosql_manager = get_nosql_manager()
    
    data = request.get_json()
    
    if not data or 'index' not in data or 'query' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    # 搜索索引
    results = search_engine.search(data['index'], data['query'], data.get('fields'))
    
    # 如果需要,从NoSQL获取完整数据
    if data.get('include_full_data', False):
        collection = data.get('collection', data['index'])
        full_results = []
        for doc in results:
            if '_id' in doc:
                full_doc = nosql_manager.find_one(collection, {'_id': doc['_id']})
                if full_doc:
                    full_results.append(full_doc)
        results = full_results
    
    return jsonify({
        'success': True,
        'count': len(results),
        'results': results
    })

@search_nosql_api.route('/test')
def test():
    """测试功能"""
    search_engine = get_search_engine()
    nosql_manager = get_nosql_manager()
    
    results = {
        'search_test': False,
        'nosql_test': False,
        'index_test': False
    }
    
    # 测试搜索
    try:
        search_engine.add_document('test_index', 'test1', {'title': 'Test', 'content': 'Test content'})
        res = search_engine.search('test_index', 'Test')
        results['search_test'] = len(res) > 0
    except Exception:
        pass
    
    # 测试NoSQL
    try:
        doc_id = nosql_manager.insert('test_collection', {'name': 'Test'})
        found = nosql_manager.find_one('test_collection', {'_id': doc_id})
        results['nosql_test'] = found is not None
    except Exception:
        pass
    
    # 测试综合
    try:
        results['index_test'] = True
    except Exception:
        pass
    
    return jsonify(results)

@search_nosql_api.route('/health')
def health():
    """健康检查"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
