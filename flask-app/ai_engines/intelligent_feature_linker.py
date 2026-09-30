#!/usr/bin/env python3
"""
智能功能联想引擎 (Intelligent Feature Linker)

基于AST代码分析 + TF-IDF语义相似度，自动发现孤立服务并生成路由绑定。
核心能力：
1. 扫描所有服务文件，提取类/方法/文档字符串
2. 构建功能知识图谱（服务间相似度矩阵）
3. 识别孤立服务（无路由调用的服务）
4. 自动生成Flask Blueprint路由绑定代码
5. 智能推荐功能组合（A+B → C 新能力）
"""

import os
import ast
import re
import json
import math
import sqlite3
import hashlib
import logging
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional, Any

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICES_DIR = os.path.join(BASE_DIR, 'services')
ROUTES_DIR = os.path.join(BASE_DIR, 'routes')


class ServiceAnalyzer:
    """AST分析器 - 从Python文件中提取功能特征"""

    def __init__(self):
        self.services: Dict[str, Dict] = {}
        self.method_index: Dict[str, List[str]] = defaultdict(list)
        self.keyword_index: Dict[str, List[str]] = defaultdict(list)

    def analyze_file(self, filepath: str) -> Optional[Dict]:
        """分析单个Python文件，提取类、方法、关键词"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            tree = ast.parse(source)
        except Exception as e:
            logger.debug(f"AST parse failed for {filepath}: {e}")
            return None

        filename = os.path.basename(filepath)
        module_name = filename.replace('.py', '')

        classes = []
        all_methods = []
        all_keywords = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                docstring = ast.get_docstring(node) or ''

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_name = item.name
                        method_doc = ast.get_docstring(item) or ''
                        params = [arg.arg for arg in item.args.args if arg.arg != 'self']

                        methods.append({
                            'name': method_name,
                            'params': params,
                            'doc': method_doc[:200],
                            'is_public': not method_name.startswith('_'),
                        })
                        all_methods.append(method_name)

                        # 从方法名提取关键词
                        words = re.findall(r'[a-z]+|[A-Z][a-z]*', method_name)
                        all_keywords.extend([w.lower() for w in words if len(w) > 2])

                        # 从文档字符串提取关键词
                        if method_doc:
                            words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]{3,}', method_doc)
                            all_keywords.extend([w.lower() for w in words])

                classes.append({
                    'name': node.name,
                    'methods': methods,
                    'method_count': len(methods),
                    'public_method_count': sum(1 for m in methods if m['is_public']),
                    'doc': docstring[:300],
                })

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.col_offset == 0:
                # 模块级函数
                func_name = node.name
                func_doc = ast.get_docstring(node) or ''
                params = [arg.arg for arg in node.args.args]
                all_methods.append(func_name)
                all_keywords.extend(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]{3,}', func_doc))

        # 从文件名提取关键词
        name_words = re.findall(r'[a-z]+|[A-Z][a-z]*', module_name)
        all_keywords.extend([w.lower() for w in name_words if len(w) > 2])

        # 从文档字符串提取
        module_doc = ast.get_docstring(tree) or ''
        if module_doc:
            all_keywords.extend(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]{3,}', module_doc))

        info = {
            'filepath': filepath,
            'filename': filename,
            'module': module_name,
            'classes': classes,
            'class_count': len(classes),
            'methods': all_methods,
            'method_count': len(all_methods),
            'keywords': all_keywords,
            'keyword_freq': dict(Counter(all_keywords)),
            'doc': module_doc[:500],
            'has_init_db': '_init_db' in all_methods,
            'has_crud': self._check_crud(all_methods),
        }

        self.services[module_name] = info
        for m in all_methods:
            self.method_index[m].append(module_name)
        for kw in set(all_keywords):
            self.keyword_index[kw].append(module_name)

        return info

    def _check_crud(self, methods: List[str]) -> Dict[str, bool]:
        """检查CRUD完整性"""
        method_str = ' '.join(methods).lower()
        return {
            'create': any(k in method_str for k in ['create', 'add', 'insert', 'save', 'new']),
            'read': any(k in method_str for k in ['get', 'list', 'search', 'find', 'query', 'fetch']),
            'update': any(k in method_str for k in ['update', 'edit', 'modify', 'set', 'change']),
            'delete': any(k in method_str for k in ['delete', 'remove', 'drop', 'clear']),
        }

    def scan_directory(self, directory: str) -> int:
        """扫描目录下所有Python文件"""
        count = 0
        for root, dirs, files in os.walk(directory):
            # 跳过__pycache__
            dirs[:] = [d for d in dirs if d != '__pycache__' and not d.startswith('.')]
            for f in files:
                if f.endswith('.py') and not f.startswith('_') and not f.startswith('test_'):
                    filepath = os.path.join(root, f)
                    if self.analyze_file(filepath):
                        count += 1
        return count


class TfidfSimilarity:
    """TF-IDF语义相似度计算 - 发现服务间的功能关联"""

    def __init__(self, services: Dict[str, Dict]):
        self.services = services
        self.vocabulary: Set[str] = set()
        self.idf: Dict[str, float] = {}
        self.tfidf_vectors: Dict[str, Dict[str, float]] = {}
        self._build()

    def _build(self):
        """构建TF-IDF模型"""
        # 构建词汇表
        doc_count = len(self.services)
        if doc_count == 0:
            return

        df = defaultdict(int)
        for module, info in self.services.items():
            keywords = set(info.get('keywords', []))
            self.vocabulary.update(keywords)
            for kw in keywords:
                df[kw] += 1

        # 计算IDF
        for kw in self.vocabulary:
            self.idf[kw] = math.log((doc_count + 1) / (df[kw] + 1)) + 1

        # 计算每个服务的TF-IDF向量
        for module, info in self.services.items():
            freq = info.get('keyword_freq', {})
            total = sum(freq.values()) or 1
            vector = {}
            for kw, count in freq.items():
                tf = count / total
                vector[kw] = tf * self.idf.get(kw, 1)
            self.tfidf_vectors[module] = vector

    def cosine_similarity(self, vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """计算余弦相似度"""
        if not vec_a or not vec_b:
            return 0.0
        common_keys = set(vec_a.keys()) & set(vec_b.keys())
        if not common_keys:
            return 0.0
        dot = sum(vec_a[k] * vec_b[k] for k in common_keys)
        norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
        norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def find_similar(self, module_name: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """找到与指定服务最相似的服务"""
        target_vec = self.tfidf_vectors.get(module_name, {})
        if not target_vec:
            return []

        similarities = []
        for other_module, other_vec in self.tfidf_vectors.items():
            if other_module == module_name:
                continue
            sim = self.cosine_similarity(target_vec, other_vec)
            if sim > 0.01:
                similarities.append((other_module, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]

    def find_complementary(self, module_a: str, module_b: str) -> float:
        """计算两个服务的互补度（A有Create无Read, B有Read无Create → 高互补）"""
        info_a = self.services.get(module_a, {})
        info_b = self.services.get(module_b, {})
        crud_a = info_a.get('has_crud', {})
        crud_b = info_b.get('has_crud', {})

        complement_score = 0
        for op in ['create', 'read', 'update', 'delete']:
            if crud_a.get(op, False) and not crud_b.get(op, False):
                complement_score += 0.25
            elif not crud_a.get(op, False) and crud_b.get(op, False):
                complement_score += 0.25

        return complement_score


class RouteDetector:
    """路由检测器 - 识别哪些服务已被路由绑定"""

    def __init__(self):
        self.routed_modules: Set[str] = set()
        self.route_patterns = [
            r'from\s+services\.(\w+)\s+import',
            r'from\s+services\.\w+\.(\w+)\s+import',
            r'import\s+services\.(\w+)',
            r'from\s+core\.services\.(\w+)\s+import',
        ]

    def scan_routes_file(self, filepath: str):
        """扫描路由文件，找出被引用的服务模块"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            for pattern in self.route_patterns:
                for match in re.finditer(pattern, content):
                    self.routed_modules.add(match.group(1))
        except Exception as e:
            logger.debug(f"Route scan failed for {filepath}: {e}")

    def scan_all_routes(self, routes_dir: str = ROUTES_DIR, main_app: str = None):
        """扫描所有路由文件"""
        if os.path.isdir(routes_dir):
            for f in os.listdir(routes_dir):
                if f.endswith('.py'):
                    self.scan_routes_file(os.path.join(routes_dir, f))

        if main_app and os.path.isfile(main_app):
            self.scan_routes_file(main_app)

    def is_orphaned(self, module_name: str) -> bool:
        """判断服务是否孤立（无路由引用）"""
        return module_name not in self.routed_modules


class RouteGenerator:
    """路由代码生成器 - 为孤立服务自动生成Flask Blueprint"""

    @staticmethod
    def generate_blueprint(service_info: Dict, blueprint_name: str = None) -> str:
        """为服务生成Flask Blueprint代码"""
        module = service_info['module']
        bp_name = blueprint_name or f"{module}_bp"
        url_prefix = f"/api/{module.replace('_', '/')}"

        classes = service_info.get('classes', [])
        primary_class = classes[0]['name'] if classes else None

        lines = [
            f'"""自动生成的路由蓝图 - {module}"""',
            f'from flask import Blueprint, jsonify, request',
            f'from services.{module} import {primary_class}' if primary_class else f'import services.{module}',
            '',
            f'{bp_name} = Blueprint(\'{bp_name}\', __name__, url_prefix=\'{url_prefix}\')',
            '',
        ]

        if primary_class and classes:
            methods = [m for m in classes[0]['methods'] if m['is_public']]

            for method in methods[:15]:  # 限制最多15个方法
                method_name = method['name']
                params = method['params']
                doc = method['doc']

                # 推断HTTP方法和路径
                if any(k in method_name.lower() for k in ['create', 'add', 'insert', 'save', 'new']):
                    http_method = 'POST'
                    path = f'/{method_name}'
                elif any(k in method_name.lower() for k in ['delete', 'remove', 'drop']):
                    http_method = 'DELETE'
                    path = f'/{method_name}/<int:item_id>'
                elif any(k in method_name.lower() for k in ['update', 'edit', 'modify', 'set']):
                    http_method = 'PUT'
                    path = f'/{method_name}/<int:item_id>'
                elif any(k in method_name.lower() for k in ['get', 'list', 'search', 'find', 'query']):
                    http_method = 'GET'
                    path = f'/{method_name}'
                else:
                    http_method = 'POST'
                    path = f'/{method_name}'

                # 构建参数提取
                param_extract = []
                for p in params:
                    if http_method == 'GET':
                        param_extract.append(f"'{p}': request.args.get('{p}')")
                    else:
                        param_extract.append(f"'{p}': data.get('{p}')")

                param_str = ', '.join(param_extract)

                lines.extend([
                    f'@{bp_name}.route(\'{path}\', methods=[\'{http_method}\'])',
                    f'def {method_name}({"item_id" if "<int:item_id>" in path else ""}):',
                    f'    """{doc}"""',
                ])

                if http_method != 'GET':
                    lines.append(f'    data = request.get_json() or {{}}')

                if param_str:
                    lines.append(f'    kwargs = {{{param_str}}}')
                    lines.append(f'    kwargs = {{k: v for k, v in kwargs.items() if v is not None}}')
                    lines.append(f'    try:')
                    lines.append(f'        service = {primary_class}()')
                    lines.append(f'        result = service.{method_name}(**kwargs)')
                    lines.append(f'        return jsonify(result) if isinstance(result, dict) else jsonify({{"data": result}})')
                    lines.append(f'    except Exception as e:')
                    lines.append(f'        return jsonify({{"error": str(e)}}), 500')
                else:
                    lines.append(f'    try:')
                    lines.append(f'        service = {primary_class}()')
                    lines.append(f'        result = service.{method_name}()')
                    lines.append(f'        return jsonify(result) if isinstance(result, dict) else jsonify({{"data": result}})')
                    lines.append(f'    except Exception as e:')
                    lines.append(f'        return jsonify({{"error": str(e)}}), 500')

                lines.append('')

        return '\n'.join(lines)

    @staticmethod
    def generate_registration(blueprints: List[str]) -> str:
        """生成Blueprint注册代码"""
        lines = [
            '# 自动生成的Blueprint注册代码',
            '# 请将此代码添加到 server_real_db.py 的 Blueprint 注册区域',
            '',
        ]
        for bp in blueprints:
            module = bp.replace('_bp', '')
            lines.extend([
                f'try:',
                f'    from routes.auto_{module} import {bp}',
                f'    app.register_blueprint({bp})',
                f'except Exception as _e:',
                f'    print(f"[WARN] Failed to register {bp}: {{_e}}")',
                '',
            ])
        return '\n'.join(lines)


class FeatureLinker:
    """功能联想引擎 - 主控制器"""

    def __init__(self):
        self.analyzer = ServiceAnalyzer()
        self.tfidf: Optional[TfidfSimilarity] = None
        self.route_detector = RouteDetector()
        self.feature_graph: Dict[str, List[Tuple[str, float]]] = {}

    def scan(self, services_dir: str = SERVICES_DIR, routes_dir: str = ROUTES_DIR,
             main_app: str = None) -> Dict:
        """完整扫描流程"""
        logger.info("开始智能功能联想扫描...")

        # 1. 扫描所有服务文件
        service_count = self.analyzer.scan_directory(services_dir)
        logger.info(f"扫描到 {service_count} 个服务文件")

        # 2. 构建TF-IDF模型
        self.tfidf = TfidfSimilarity(self.analyzer.services)
        logger.info(f"构建TF-IDF模型: {len(self.tfidf.vocabulary)} 个关键词")

        # 3. 扫描路由引用
        self.route_detector.scan_all_routes(routes_dir, main_app)
        logger.info(f"已路由绑定: {len(self.route_detector.routed_modules)} 个模块")

        # 4. 构建功能关联图
        for module in self.analyzer.services:
            similar = self.tfidf.find_similar(module, top_n=5)
            self.feature_graph[module] = similar

        # 5. 识别孤立服务
        orphaned = [m for m in self.analyzer.services if self.route_detector.is_orphaned(m)]
        logger.info(f"孤立服务: {len(orphaned)} 个")

        return {
            'total_services': service_count,
            'routed_services': len(self.route_detector.routed_modules),
            'orphaned_services': len(orphaned),
            'vocabulary_size': len(self.tfidf.vocabulary),
            'feature_graph_edges': sum(len(v) for v in self.feature_graph.values()),
        }

    def get_orphaned_services(self) -> List[Dict]:
        """获取孤立服务详情"""
        orphans = []
        for module, info in self.analyzer.services.items():
            if self.route_detector.is_orphaned(module):
                similar = self.feature_graph.get(module, [])
                crud = info.get('has_crud', {})
                orphans.append({
                    'module': module,
                    'filename': info['filename'],
                    'class_count': info['class_count'],
                    'method_count': info['method_count'],
                    'has_crud': crud,
                    'crud_complete': all(crud.values()) if crud else False,
                    'similar_services': [{'module': s[0], 'similarity': round(s[1], 3)} for s in similar[:3]],
                    'primary_class': info['classes'][0]['name'] if info['classes'] else None,
                    'public_methods': [m['name'] for c in info['classes'] for m in c['methods'] if m['is_public']][:10],
                })
        orphans.sort(key=lambda x: x['method_count'], reverse=True)
        return orphans

    def get_feature_recommendations(self) -> List[Dict]:
        """获取功能组合推荐（A+B → 新能力）"""
        recommendations = []
        modules = list(self.analyzer.services.keys())

        for i, mod_a in enumerate(modules):
            for mod_b in modules[i+1:i+6]:  # 每个模块只看前5个
                sim = self.tfidf.cosine_similarity(
                    self.tfidf.tfidf_vectors.get(mod_a, {}),
                    self.tfidf.tfidf_vectors.get(mod_b, {})
                )
                complement = self.tfidf.find_complementary(mod_a, mod_b)

                if sim > 0.15 and complement > 0.3:
                    info_a = self.analyzer.services[mod_a]
                    info_b = self.analyzer.services[mod_b]
                    recommendations.append({
                        'service_a': mod_a,
                        'service_b': mod_b,
                        'similarity': round(sim, 3),
                        'complementarity': round(complement, 3),
                        'combined_score': round(sim * 0.4 + complement * 0.6, 3),
                        'description': f"{info_a['filename']} + {info_b['filename']}",
                        'crud_a': info_a.get('has_crud', {}),
                        'crud_b': info_b.get('has_crud', {}),
                    })

        recommendations.sort(key=lambda x: x['combined_score'], reverse=True)
        return recommendations[:20]

    def generate_route_files(self, output_dir: str = ROUTES_DIR, max_files: int = 20) -> int:
        """为孤立服务生成路由文件"""
        orphans = self.get_orphaned_services()
        generated = 0

        os.makedirs(output_dir, exist_ok=True)

        for orphan in orphans[:max_files]:
            module = orphan['module']
            if not orphan.get('primary_class'):
                continue

            info = self.analyzer.services.get(module, {})
            code = RouteGenerator.generate_blueprint(info)

            filepath = os.path.join(output_dir, f'auto_{module}.py')
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(code)
                generated += 1
                logger.info(f"生成路由: {filepath}")
            except Exception as e:
                logger.error(f"生成路由失败 {module}: {e}")

        # 生成注册代码
        if generated > 0:
            reg_code = RouteGenerator.generate_registration(
                [f"{o['module']}_bp" for o in orphans[:max_files] if o.get('primary_class')]
            )
            reg_path = os.path.join(output_dir, '_auto_register.py')
            with open(reg_path, 'w', encoding='utf-8') as f:
                f.write(reg_code)

        return generated

    def persist_to_db(self, db_path: str = None):
        """将分析结果持久化到数据库"""
        if db_path is None:
            db_path = os.path.join(BASE_DIR, 'app.db')

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # 建表
        cur.execute('''
            CREATE TABLE IF NOT EXISTS ai_feature_linkage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT NOT NULL,
                filename TEXT,
                class_count INTEGER DEFAULT 0,
                method_count INTEGER DEFAULT 0,
                is_orphaned INTEGER DEFAULT 0,
                has_create INTEGER DEFAULT 0,
                has_read INTEGER DEFAULT 0,
                has_update INTEGER DEFAULT 0,
                has_delete INTEGER DEFAULT 0,
                similar_modules TEXT,
                public_methods TEXT,
                scanned_at TEXT,
                UNIQUE(module_name)
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS ai_feature_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_a TEXT NOT NULL,
                service_b TEXT NOT NULL,
                similarity REAL DEFAULT 0,
                complementarity REAL DEFAULT 0,
                combined_score REAL DEFAULT 0,
                description TEXT,
                created_at TEXT,
                UNIQUE(service_a, service_b)
            )
        ''')

        now = datetime.now().isoformat()

        # 写入服务信息
        for module, info in self.analyzer.services.items():
            similar = self.feature_graph.get(module, [])
            similar_json = json.dumps([{'module': s[0], 'sim': round(s[1], 3)} for s in similar[:5]])
            methods_json = json.dumps([m['name'] for c in info['classes'] for m in c['methods'] if m['is_public']][:20])
            crud = info.get('has_crud', {})

            cur.execute('''
                INSERT OR REPLACE INTO ai_feature_linkage
                (module_name, filename, class_count, method_count, is_orphaned,
                 has_create, has_read, has_update, has_delete,
                 similar_modules, public_methods, scanned_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                module, info['filename'], info['class_count'], info['method_count'],
                1 if self.route_detector.is_orphaned(module) else 0,
                1 if crud.get('create') else 0,
                1 if crud.get('read') else 0,
                1 if crud.get('update') else 0,
                1 if crud.get('delete') else 0,
                similar_json, methods_json, now
            ))

        # 写入推荐
        for rec in self.get_feature_recommendations():
            cur.execute('''
                INSERT OR REPLACE INTO ai_feature_recommendations
                (service_a, service_b, similarity, complementarity, combined_score, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                rec['service_a'], rec['service_b'], rec['similarity'],
                rec['complementarity'], rec['combined_score'], rec['description'], now
            ))

        conn.commit()
        conn.close()
        logger.info(f"分析结果已持久化到数据库: {db_path}")


def run_full_scan():
    """执行完整扫描"""
    linker = FeatureLinker()
    main_app = os.path.join(BASE_DIR, 'server_real_db.py')

    stats = linker.scan(SERVICES_DIR, ROUTES_DIR, main_app)

    print("\n" + "=" * 60)
    print("智能功能联想引擎 - 扫描报告")
    print("=" * 60)
    print(f"  服务总数:       {stats['total_services']}")
    print(f"  已路由绑定:     {stats['routed_services']}")
    print(f"  孤立服务:       {stats['orphaned_services']}")
    print(f"  词汇表大小:     {stats['vocabulary_size']}")
    print(f"  关联图边数:     {stats['feature_graph_edges']}")

    orphans = linker.get_orphaned_services()
    print(f"\n孤立服务 Top 10:")
    for o in orphans[:10]:
        crud_str = ''.join([
            'C' if o['has_crud']['create'] else '-',
            'R' if o['has_crud']['read'] else '-',
            'U' if o['has_crud']['update'] else '-',
            'D' if o['has_crud']['delete'] else '-',
        ])
        print(f"  {o['module']:40s} [{crud_str}] {o['method_count']:3d}方法  相似: {o['similar_services'][:2]}")

    recs = linker.get_feature_recommendations()
    print(f"\n功能组合推荐 Top 5:")
    for r in recs[:5]:
        print(f"  {r['service_a']:30s} + {r['service_b']:30s}  相似={r['similarity']:.3f}  互补={r['complementarity']:.3f}")

    # 生成路由文件
    auto_dir = os.path.join(ROUTES_DIR, 'auto')
    generated = linker.generate_route_files(auto_dir, max_files=20)
    print(f"\n自动生成路由文件: {generated} 个 → {auto_dir}/")

    # 持久化到数据库
    try:
        linker.persist_to_db()
        print(f"分析结果已写入数据库 ai_feature_linkage + ai_feature_recommendations")
    except Exception as e:
        print(f"[WARN] 数据库写入失败: {e}")

    return linker


if __name__ == '__main__':
    run_full_scan()
