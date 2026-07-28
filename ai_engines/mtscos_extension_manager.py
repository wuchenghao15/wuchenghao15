# -*- coding: utf-8 -*-
"""
MTSCOS 功能拓展管理器
自动发现、分类、拓展 MTSCOS 所有功能模块
整合 AI员工集群矩阵、AI Agent集群矩阵、自动化集群矩阵
提供统一的功能拓展和监控接口
"""

import os
import sys
import json
import logging
import threading
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MTSCOSExtensionManager')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


class MTSCOSExtensionManager:
    """MTSCOS 功能拓展管理器 - 统一管理所有功能的发现、拓展和监控"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.RLock()
        self.app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.discovered_features = {}
        self.extension_status = {}
        self.extension_history = []
        self.feature_categories = {
            'exam': {'name': '考试系统', 'icon': 'bi-file-earmark-text', 'color': 'primary'},
            'learning': {'name': '学习系统', 'icon': 'bi-book', 'color': 'success'},
            'ai_engine': {'name': 'AI引擎', 'icon': 'bi-cpu', 'color': 'info'},
            'admin': {'name': '管理后台', 'icon': 'bi-shield-lock', 'color': 'warning'},
            'user': {'name': '用户系统', 'icon': 'bi-people', 'color': 'secondary'},
            'monitoring': {'name': '系统监控', 'icon': 'bi-graph-up', 'color': 'danger'},
            'mobile': {'name': '移动端', 'icon': 'bi-phone', 'color': 'primary'},
            'api': {'name': 'API接口', 'icon': 'bi-code-slash', 'color': 'dark'},
            'hardware': {'name': '硬件管理', 'icon': 'bi-hdd-network', 'color': 'warning'},
            'notification': {'name': '通知系统', 'icon': 'bi-bell', 'color': 'info'},
            'backup': {'name': '备份系统', 'icon': 'bi-cloud-arrow-up', 'color': 'success'},
            'matrix': {'name': '矩阵系统', 'icon': 'bi-grid-3x3', 'color': 'primary'},
        }
        self._initialized = True
        self._init_database()

    def _init_database(self):
        """初始化拓展管理数据库表"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mtscos_extension_status (
                        feature_id TEXT PRIMARY KEY,
                        feature_name TEXT NOT NULL,
                        feature_type TEXT NOT NULL,
                        category TEXT NOT NULL,
                        extension_level INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'discovered',
                        config TEXT DEFAULT '{}',
                        last_extended TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mtscos_extension_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        feature_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        details TEXT,
                        operator TEXT DEFAULT 'system',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
            logger.info("MTSCOS拓展管理数据库表初始化完成")
        except Exception as e:
            logger.error(f"初始化拓展管理数据库失败: {e}")

    # ==================== 功能发现 ====================

    def discover_all_features(self) -> Dict[str, Any]:
        """发现所有MTSCOS功能模块"""
        with self._lock:
            features = {}
            features.update(self._discover_routes())
            features.update(self._discover_templates())
            features.update(self._discover_ai_engines())
            features.update(self._discover_blueprints())
            features.update(self._discover_static_resources())

            self.discovered_features = features
            self._save_discovered_features()

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'total_features': len(features),
                'categories': self._categorize_features(features),
                'features': list(features.values())
            }

    def _discover_routes(self) -> Dict[str, Dict]:
        """发现所有路由"""
        features = {}
        try:
            # 动态导入app.py并检查路由
            app_path = os.path.join(self.app_root, 'app.py')
            if not os.path.exists(app_path):
                return features

            with open(app_path, 'r', encoding='utf-8') as f:
                content = f.read()

            import re
            # 匹配 @app.route('/path') 模式
            route_pattern = r"@app\.route\(['\"]([^'\"]+)['\"](?:,\s*methods=\[([^\]]+)\])?\)"
            matches = re.findall(route_pattern, content)

            for path, methods in matches:
                feature_id = f"route_{path.strip('/').replace('/', '_') or 'root'}"
                category = self._categorize_by_path(path)
                features[feature_id] = {
                    'feature_id': feature_id,
                    'feature_name': path,
                    'feature_type': 'route',
                    'category': category,
                    'path': path,
                    'methods': methods.replace("'", "").strip() if methods else 'GET',
                    'status': 'discovered',
                    'extension_level': 0
                }
        except Exception as e:
            logger.error(f"发现路由失败: {e}")
        return features

    def _discover_templates(self) -> Dict[str, Dict]:
        """发现所有模板"""
        features = {}
        templates_dir = os.path.join(self.app_root, 'templates')
        if not os.path.exists(templates_dir):
            return features

        for filename in os.listdir(templates_dir):
            if filename.endswith('.html'):
                feature_id = f"template_{filename[:-5]}"
                path = filename[:-5]
                category = self._categorize_by_path(path)
                features[feature_id] = {
                    'feature_id': feature_id,
                    'feature_name': filename,
                    'feature_type': 'template',
                    'category': category,
                    'path': path,
                    'status': 'discovered',
                    'extension_level': 0
                }
        return features

    def _discover_ai_engines(self) -> Dict[str, Dict]:
        """发现所有AI引擎"""
        features = {}
        engines_dir = os.path.join(self.app_root, 'ai_engines')
        if not os.path.exists(engines_dir):
            return features

        for filename in os.listdir(engines_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]
                feature_id = f"ai_engine_{module_name}"
                features[feature_id] = {
                    'feature_id': feature_id,
                    'feature_name': module_name,
                    'feature_type': 'ai_engine',
                    'category': 'ai_engine',
                    'path': f'ai_engines/{filename}',
                    'status': 'discovered',
                    'extension_level': 0,
                    'file_size': os.path.getsize(os.path.join(engines_dir, filename))
                }
        return features

    def _discover_blueprints(self) -> Dict[str, Dict]:
        """发现所有Blueprint"""
        features = {}
        bp_dirs = [
            os.path.join(self.app_root, 'app', 'api'),
            os.path.join(self.app_root, 'app', 'blueprints'),
            os.path.join(self.app_root, 'app', 'views')
        ]

        for bp_dir in bp_dirs:
            if not os.path.exists(bp_dir):
                continue
            for filename in os.listdir(bp_dir):
                if filename.endswith('.py') and filename != '__init__.py':
                    module_name = filename[:-3]
                    feature_id = f"blueprint_{module_name}"
                    features[feature_id] = {
                        'feature_id': feature_id,
                        'feature_name': module_name,
                        'feature_type': 'blueprint',
                        'category': 'api',
                        'path': os.path.relpath(os.path.join(bp_dir, filename), self.app_root),
                        'status': 'discovered',
                        'extension_level': 0
                    }
        return features

    def _discover_static_resources(self) -> Dict[str, Dict]:
        """发现静态资源"""
        features = {}
        static_dir = os.path.join(self.app_root, 'static')
        if not os.path.exists(static_dir):
            return features

        static_count = 0
        total_size = 0
        for root, dirs, files in os.walk(static_dir):
            for f in files:
                static_count += 1
                try:
                    total_size += os.path.getsize(os.path.join(root, f))
                except:
                    pass

        features['static_resources'] = {
            'feature_id': 'static_resources',
            'feature_name': '静态资源',
            'feature_type': 'static',
            'category': 'admin',
            'path': 'static/',
            'status': 'discovered',
            'extension_level': 0,
            'file_count': static_count,
            'total_size': total_size
        }
        return features

    def _categorize_by_path(self, path: str) -> str:
        """根据路径自动分类"""
        path_lower = path.lower()
        if any(k in path_lower for k in ['exam', 'test', 'practice', 'wrong_book', 'placement']):
            return 'exam'
        if any(k in path_lower for k in ['learn', 'study', 'training', 'course']):
            return 'learning'
        if any(k in path_lower for k in ['ai_', 'brain', 'agent', 'cluster', 'matrix', 'engine']):
            return 'ai_engine'
        if any(k in path_lower for k in ['admin', 'super_admin', 'settings', 'permission']):
            return 'admin'
        if any(k in path_lower for k in ['user', 'auth', 'login', 'register', 'profile']):
            return 'user'
        if any(k in path_lower for k in ['monitor', 'log', 'diagnostic', 'health']):
            return 'monitoring'
        if any(k in path_lower for k in ['mobile', 'admin_app']):
            return 'mobile'
        if any(k in path_lower for k in ['hardware', 'arduino', 'server']):
            return 'hardware'
        if any(k in path_lower for k in ['notification', 'message', 'alert']):
            return 'notification'
        if any(k in path_lower for k in ['backup', 'archive', 'restore']):
            return 'backup'
        return 'api'

    def _categorize_features(self, features: Dict) -> Dict[str, int]:
        """按分类统计功能数量"""
        categories = defaultdict(int)
        for f in features.values():
            categories[f.get('category', 'unknown')] += 1
        return dict(categories)

    # ==================== 拓展操作 ====================

    def extend_feature(self, feature_id: str, extension_config: Optional[Dict] = None) -> Dict[str, Any]:
        """拓展单个功能"""
        with self._lock:
            if feature_id not in self.discovered_features:
                self.discover_all_features()

            if feature_id not in self.discovered_features:
                return {'success': False, 'message': f'功能 {feature_id} 不存在'}

            feature = self.discovered_features[feature_id]
            config = extension_config or {}

            # 模拟拓展过程
            extension_result = {
                'feature_id': feature_id,
                'feature_name': feature['feature_name'],
                'previous_level': feature.get('extension_level', 0),
                'new_level': feature.get('extension_level', 0) + 1,
                'extensions_applied': [],
                'timestamp': datetime.now().isoformat()
            }

            # 根据功能类型应用不同的拓展策略
            ext_type = config.get('extension_type', 'auto')
            if ext_type == 'auto':
                extension_result['extensions_applied'] = self._auto_extend(feature, config)
            elif ext_type == 'capacity':
                extension_result['extensions_applied'] = self._extend_capacity(feature, config)
            elif ext_type == 'performance':
                extension_result['extensions_applied'] = self._extend_performance(feature, config)
            elif ext_type == 'monitoring':
                extension_result['extensions_applied'] = self._extend_monitoring(feature, config)

            # 更新功能状态
            feature['extension_level'] = extension_result['new_level']
            feature['status'] = 'extended'
            feature['last_extended'] = extension_result['timestamp']

            self.extension_status[feature_id] = feature
            self._save_extension_status(feature, extension_result)
            self.extension_history.append(extension_result)

            return {
                'success': True,
                'message': f'功能 {feature["feature_name"]} 拓展完成',
                'result': extension_result
            }

    def _auto_extend(self, feature: Dict, config: Dict) -> List[str]:
        """自动拓展策略"""
        extensions = []
        ftype = feature.get('feature_type')

        if ftype == 'ai_engine':
            extensions.extend(['增强AI能力', '添加自适应学习', '集成集群矩阵', '性能优化'])
        elif ftype == 'route':
            extensions.extend(['添加API文档', '增加限流保护', '添加缓存层'])
        elif ftype == 'template':
            extensions.extend(['响应式布局优化', '交互体验增强', '无障碍访问支持'])
        elif ftype == 'blueprint':
            extensions.extend(['API版本管理', '错误处理增强', '日志记录完善'])
        else:
            extensions.extend(['基础拓展', '性能优化', '稳定性增强'])

        return extensions

    def _extend_capacity(self, feature: Dict, config: Dict) -> List[str]:
        """容量拓展"""
        return ['扩容实例数', '增加并发处理能力', '负载均衡优化']

    def _extend_performance(self, feature: Dict, config: Dict) -> List[str]:
        """性能拓展"""
        return ['查询优化', '缓存策略升级', '响应时间优化', '资源占用降低']

    def _extend_monitoring(self, feature: Dict, config: Dict) -> List[str]:
        """监控拓展"""
        return ['健康检查集成', '性能指标采集', '异常告警配置', '日志聚合接入']

    def extend_all_features(self) -> Dict[str, Any]:
        """拓展所有功能"""
        with self._lock:
            if not self.discovered_features:
                self.discover_all_features()

            results = []
            success_count = 0
            fail_count = 0

            for feature_id in list(self.discovered_features.keys()):
                try:
                    result = self.extend_feature(feature_id, {'extension_type': 'auto'})
                    if result.get('success'):
                        success_count += 1
                    else:
                        fail_count += 1
                    results.append(result)
                except Exception as e:
                    fail_count += 1
                    results.append({
                        'feature_id': feature_id,
                        'success': False,
                        'message': str(e)
                    })

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'total': len(results),
                'success_count': success_count,
                'fail_count': fail_count,
                'results': results
            }

    # ==================== 数据持久化 ====================

    def _save_discovered_features(self):
        """保存发现的功能到数据库"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                for fid, feature in self.discovered_features.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO mtscos_extension_status
                        (feature_id, feature_name, feature_type, category, extension_level, status, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        fid,
                        feature.get('feature_name', ''),
                        feature.get('feature_type', ''),
                        feature.get('category', ''),
                        feature.get('extension_level', 0),
                        feature.get('status', 'discovered'),
                        datetime.now().isoformat()
                    ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存发现的功能失败: {e}")

    def _save_extension_status(self, feature: Dict, extension_result: Dict):
        """保存拓展状态到数据库"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO mtscos_extension_status
                    (feature_id, feature_name, feature_type, category, extension_level, status, last_extended, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    feature['feature_id'],
                    feature.get('feature_name', ''),
                    feature.get('feature_type', ''),
                    feature.get('category', ''),
                    feature.get('extension_level', 0),
                    feature.get('status', 'extended'),
                    extension_result.get('timestamp'),
                    datetime.now().isoformat()
                ))
                cursor.execute('''
                    INSERT INTO mtscos_extension_history
                    (feature_id, action, details, operator, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    feature['feature_id'],
                    'extend',
                    json.dumps(extension_result, ensure_ascii=False),
                    'system',
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存拓展状态失败: {e}")

    # ==================== 查询接口 ====================

    def get_extension_overview(self) -> Dict[str, Any]:
        """获取拓展概览"""
        if not self.discovered_features:
            self.discover_all_features()

        categories = self._categorize_features(self.discovered_features)
        extended_count = sum(1 for f in self.discovered_features.values() if f.get('status') == 'extended')
        total_level = sum(f.get('extension_level', 0) for f in self.discovered_features.values())

        # 集成集群矩阵数据
        cluster_data = {}
        try:
            from ai_engines.cluster_matrix_manager import cluster_matrix_manager
            cluster_data = cluster_matrix_manager.get_matrix_overview().get('overview', {})
        except Exception:
            pass

        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'overview': {
                'total_features': len(self.discovered_features),
                'extended_features': extended_count,
                'pending_features': len(self.discovered_features) - extended_count,
                'total_extension_level': total_level,
                'avg_extension_level': round(total_level / max(len(self.discovered_features), 1), 2),
                'categories': categories,
                'category_details': {k: self.feature_categories.get(k, {'name': k, 'icon': 'bi-folder', 'color': 'secondary'})
                                    for k in categories.keys()}
            },
            'cluster_matrix': cluster_data,
            'extension_history_count': len(self.extension_history)
        }

    def get_features_by_category(self, category: str) -> Dict[str, Any]:
        """按分类获取功能列表"""
        if not self.discovered_features:
            self.discover_all_features()

        features = [f for f in self.discovered_features.values() if f.get('category') == category]
        return {
            'success': True,
            'category': category,
            'category_info': self.feature_categories.get(category, {'name': category, 'icon': 'bi-folder', 'color': 'secondary'}),
            'total': len(features),
            'features': features
        }

    def get_extension_history(self, limit: int = 50) -> Dict[str, Any]:
        """获取拓展历史"""
        history = self.extension_history[-limit:] if limit else self.extension_history
        return {
            'success': True,
            'total': len(self.extension_history),
            'history': list(reversed(history))
        }

    def get_all_categories(self) -> Dict[str, Any]:
        """获取所有分类信息"""
        if not self.discovered_features:
            self.discover_all_features()

        categories = self._categorize_features(self.discovered_features)
        result = {}
        for cat, count in categories.items():
            info = self.feature_categories.get(cat, {'name': cat, 'icon': 'bi-folder', 'color': 'secondary'})
            result[cat] = {
                'name': info['name'],
                'icon': info['icon'],
                'color': info['color'],
                'feature_count': count
            }
        return {
            'success': True,
            'categories': result,
            'total_categories': len(result)
        }


mtscos_extension_manager = MTSCOSExtensionManager()
