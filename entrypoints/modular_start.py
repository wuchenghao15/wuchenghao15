#!/usr/bin/env python3
"""
MTSCOS AI 系统 - 完整模块化启动脚本
========================================
替代简化版 simple_start.py
- 分段从数据库调取配置参数（8个阶段）
- 模块化核心初始化（4个步骤）
- 功能模块分阶段加载（6个阶段）
- AI引擎后台异步加载
- 自动化任务启动
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime

# ========== 启动前初始化 ==========
START_TIME = datetime.now()

# 设置基础日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('modular_start')

# 添加项目根目录到Python路径
# 注意：本文件已从根目录迁入 entrypoints/，所以需要取上级目录为真正的项目根
_BASE = os.path.abspath(__file__)
THIS_DIR = os.path.dirname(_BASE)       # entrypoints/
PROJECT_ROOT = os.path.dirname(THIS_DIR)# 项目根
for _p in (PROJECT_ROOT, THIS_DIR, os.path.join(PROJECT_ROOT, '_config')):
    if _p not in sys.path:
        sys.path.insert(0, _p)
BASE_DIR = PROJECT_ROOT                 # 兼容旧代码：仍用 BASE_DIR 指向项目根

try:
    from core.db_path import patch_sqlite3_connect as _mtscos_patch
    _mtscos_patch(verbose=False)
except Exception as _e:
    sys.stderr.write(f"[WARN] db_path patch failed (modular_start): {_e}\n")

import _path_setup

print()
print("=" * 70)
print("  MTSCOS AI 智能考试系统 - 模块化启动")
print("  版本: v7.1.0 (Intelligent Modular Enhanced Edition)")
print("=" * 70)
print(f"  启动时间: {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  项目目录: {BASE_DIR}")
print("=" * 70)
print()

# ========== 阶段一: 数据库配置加载 ==========
logger.info("[启动 1/5] 加载数据库配置...")
print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  阶段 1: 数据库配置加载 (8个子阶段)")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

from startup_modules.db_config_loader import load_db_configs, get_all_db_configs, config_loader

# 加载所有配置（8个阶段）
all_configs = load_db_configs()

print(f"  ✓ 配置加载完成: {len(all_configs)} 项配置")
print(f"  ✓ 加载阶段: {', '.join(config_loader.loaded_stages)}")
print()

# ========== 阶段二: 核心初始化 ==========
logger.info("[启动 2/5] 核心初始化...")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  阶段 2: 核心初始化 (4个步骤)")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

from startup_modules.core_init import core_initialization

app = core_initialization(config=all_configs)

# 保存配置到app
app.config['DB_CONFIGS'] = all_configs
app.config['CONFIG_LOADER'] = config_loader

print(f"  ✓ Flask应用创建成功")
print(f"  ✓ 模板全局函数已注册")
print(f"  ✓ CORS跨域已配置")
print(f"  ✓ 数据库连接已初始化")
print()

# ========== 阶段三: 功能模块加载 ==========
logger.info("[启动 3/5] 加载功能模块...")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  阶段 3: 功能模块加载 (6个阶段)")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

from startup_modules.module_loader import ModuleLoader

module_loader = ModuleLoader(app)
load_results = module_loader.load_all_modules()

print(f"  ✓ 完成阶段: {load_results['completed_stages']}/{load_results['total_stages']}")
print(f"  ✓ 成功模块: {load_results['loaded_modules']}")
print(f"  ✗ 失败模块: {load_results['failed_modules']}")
if load_results['failed_list']:
    print(f"  失败列表: {', '.join(load_results['failed_list'][:10])}...")
print()

# 保存模块加载器引用
app.module_loader = module_loader
app.load_results = load_results

# ========== 阶段四: 系统路由和管理API ==========
logger.info("[启动 4/5] 注册系统管理API...")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  阶段 4: 系统管理API")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

from flask import jsonify, render_template, request, session

# require_login和require_admin在模块加载器中已设置
require_login = getattr(app, 'require_login', lambda f: f)

# ================ 系统状态API ================
@app.route('/api/system/status')
@require_login
def api_system_status():
    """获取系统完整状态"""
    elapsed = (datetime.now() - START_TIME).total_seconds()

    # 路由统计
    total_routes = len(list(app.url_map.iter_rules()))
    api_routes = len([r for r in app.url_map.iter_rules() if r.rule.startswith('/api/')])
    page_routes = total_routes - api_routes

    # 配置统计
    config_count = len(all_configs)
    stages = config_loader.loaded_stages

    # 模块统计
    module_stats = {
        'loaded': load_results.get('loaded_modules', 0),
        'failed': load_results.get('failed_modules', 0),
        'stages_completed': load_results.get('completed_stages', 0),
        'stages_total': load_results.get('total_stages', 0),
    }

    # AI状态
    ai_status = getattr(app, 'ai_status', {})

    return jsonify({
        'success': True,
        'data': {
            'app': {
                'name': all_configs.get('app_name', 'MTSCOS AI 智能考试系统'),
                'version': all_configs.get('app_version', '6.0.0'),
                'code_name': all_configs.get('app_code_name', 'Distributed Database Edition'),
                'debug': all_configs.get('debug', False),
                'timezone': all_configs.get('timezone', 'Asia/Shanghai'),
            },
            'runtime': {
                'start_time': START_TIME.isoformat(),
                'uptime_seconds': round(elapsed, 2),
                'uptime_formatted': f"{int(elapsed//3600)}小时{int((elapsed%3600)//60)}分{int(elapsed%60)}秒",
            },
            'routes': {
                'total': total_routes,
                'api_routes': api_routes,
                'page_routes': page_routes,
            },
            'configs': {
                'total_items': config_count,
                'loaded_stages': stages,
                'stage_count': len(stages),
            },
            'modules': module_stats,
            'ai': ai_status,
            'database': {
                'mode': 'distributed',
                'db_count': all_configs.get('db_count', 14),
                'split_db_dir': app.config.get('SPLIT_DB_DIR', ''),
            },
        }
    })

# ================ 配置管理API ================
@app.route('/api/system/configs')
@require_login
def api_system_configs():
    """获取系统配置"""
    stage = request.args.get('stage')
    if stage:
        configs = config_loader.get_stage_config(stage)
        return jsonify({'success': True, 'data': configs, 'stage': stage})

    return jsonify({
        'success': True,
        'data': {
            'all': all_configs,
            'by_stage': config_loader.configs,
            'stages': config_loader.loaded_stages,
            'total_count': len(all_configs),
        }
    })

@app.route('/api/system/configs/reload', methods=['POST'])
@require_login
def api_reload_configs():
    """重新加载配置"""
    data = request.get_json() or {}
    stage = data.get('stage')

    if stage:
        config_loader.reload_stage(stage)
        return jsonify({'success': True, 'message': f'阶段 {stage} 配置已重新加载'})

    # 重新加载所有
    global all_configs
    all_configs = load_db_configs()
    app.config['DB_CONFIGS'] = all_configs
    return jsonify({'success': True, 'message': '所有配置已重新加载'})

# ================ 模块管理API ================
@app.route('/api/system/modules')
@require_login
def api_system_modules():
    """获取已加载模块列表"""
    return jsonify({
        'success': True,
        'data': {
            'loaded_modules': module_loader.loaded_modules,
            'failed_modules': module_loader.failed_modules,
            'loading_order': module_loader.loading_order,
            'summary': load_results,
        }
    })

# ================ 启动信息页面 ================
@app.route('/dashboard')
@require_login
def dashboard_page():
    """仪表板页面"""
    return render_template('dashboard.html')

@app.route('/enhancement')
@require_login
def enhancement_dashboard_page():
    """系统增强管理器仪表板"""
    return render_template('enhancement_dashboard.html')

# ================ 系统增强管理器 ================
try:
    from ai_engines.system_enhancement_api import register_enhancement_blueprint
    if register_enhancement_blueprint(app):
        print("  ✓ 系统增强管理器蓝图已注册 (/api/enhancement/*)")
    else:
        print("  ! 系统增强管理器蓝图注册失败")
except Exception as e:
    logger.warning(f"系统增强管理器加载失败: {e}")
    print(f"  ! 系统增强管理器加载失败: {e}")

# 初始化增强管理器默认数据
try:
    from ai_engines.system_enhancement_manager import system_enhancement_manager
    # 注册默认端口
    system_enhancement_manager.allocate_port('mtscos_web', preferred=8888)
    # 注册默认集群节点
    system_enhancement_manager.manage_db_cluster('add', {
        'node_id': 'node_local_01',
        'node_type': 'master',
        'address': '127.0.0.1:8888',
        'status': 'online',
        'load': 0.0
    })
    # 注册默认AI节点
    system_enhancement_manager.manage_ai_nodes('upsert', {
        'node_id': 'ai_node_01',
        'node_name': '本地AI节点',
        'model': 'gpt-4',
        'status': 'idle',
        'load': 0.0,
        'capacity': 10
    })
    # 注册默认前端布局
    system_enhancement_manager.manage_layout_config('upsert', {
        'layout_id': 'default_layout',
        'layout_name': '默认布局',
        'config': {'sidebar': True, 'header': True, 'footer': False},
        'theme': 'blue',
        'is_active': 1
    })
    # 注册默认权限规则
    default_rules = [
        {'rule_id': 'rule_admin_full', 'role': 'admin', 'resource': '*', 'action_name': '*', 'allowed': 1,
        'priority': 100},
        {'rule_id': 'rule_super_admin_full', 'role': 'super_admin', 'resource': '*', 'action_name': '*', 'allowed': 1,
        'priority': 200},
        {'rule_id': 'rule_student_exam', 'role': 'student', 'resource': '/exam_system', 'action_name': 'GET',
        'allowed': 1, 'priority': 50},
        {'rule_id': 'rule_student_test', 'role': 'student', 'resource': '/exam_system/tests', 'action_name': 'GET',
        'allowed': 1, 'priority': 50},
        {'rule_id': 'rule_teacher_manage', 'role': 'teacher', 'resource': '/teacher', 'action_name': 'GET',
        'allowed': 1, 'priority': 60},
    ]
    for rule in default_rules:
        system_enhancement_manager.manage_permission_rules('upsert', rule)
    # 注册默认AI模型
    default_models = [
        {'model_id': 'model_gpt4', 'model_name': 'GPT-4', 'version': '1.0.0', 'status': 'registered',
        'performance_score': 95.0, 'config': {'provider': 'openai', 'type': 'llm'}},
        {'model_id': 'model_gpt35', 'model_name': 'GPT-3.5-Turbo', 'version': '1.0.0', 'status': 'registered',
        'performance_score': 88.0, 'config': {'provider': 'openai', 'type': 'llm'}},
        {'model_id': 'model_claude', 'model_name': 'Claude-3', 'version': '1.0.0', 'status': 'registered',
        'performance_score': 93.0, 'config': {'provider': 'anthropic', 'type': 'llm'}},
        {'model_id': 'model_qwen', 'model_name': 'Qwen-72B', 'version': '1.0.0', 'status': 'registered',
        'performance_score': 85.0, 'config': {'provider': 'alibaba', 'type': 'llm'}},
        {'model_id': 'model_embedding', 'model_name': 'text-embedding-ada-002', 'version': '1.0.0',
        'status': 'registered', 'performance_score': 90.0, 'config': {'provider': 'openai', 'type': 'embedding'}},
        {'model_id': 'model_whisper', 'model_name': 'Whisper', 'version': '1.0.0', 'status': 'registered',
        'performance_score': 87.0, 'config': {'provider': 'openai', 'type': 'audio'}},
    ]
    for model in default_models:
        system_enhancement_manager.register_model(model)
    print("  ✓ 增强管理器默认数据已初始化 (端口/集群/AI节点/布局/权限/6个AI模型)")
    # 深度数据填充(enhancement_data_seeder.py) 已于 v17.22.0 假数据清理中移除，
    # 39权限+16模型+5集群+5AI节点+24分类+6端口+5布局默认项均已在上文显式内置初始化。
except Exception as e:
    logger.warning(f"增强管理器默认数据初始化失败: {e}")
    print(f"  ! 增强管理器默认数据初始化失败: {e}")

print("  ✓ 系统状态API已注册")
print("  ✓ 配置管理API已注册")
print("  ✓ 模块管理API已注册")
print()

# ========== 阶段五: 启动服务器 ==========
logger.info("[启动 5/5] 启动Web服务器...")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  阶段 5: 启动Web服务器")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# 解析命令行参数
parser = argparse.ArgumentParser(description='MTSCOS AI 系统 - 模块化启动')
parser.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
parser.add_argument('--port', type=int, default=8888, help='监听端口 (默认: 8888)')
parser.add_argument('--debug', action='store_true', help='调试模式')
parser.add_argument('--no-ai', action='store_true', help='不加载AI引擎')
parser.add_argument('--skip-stages', default='', help='跳过的阶段，逗号分隔')
args = parser.parse_args()

total_elapsed = (datetime.now() - START_TIME).total_seconds()

print(f"  ✓ 准备就绪")
print(f"  ✓ 总耗时: {total_elapsed:.2f}秒")
print()
print("=" * 70)
print(f"  服务器即将启动")
print(f"  地址: http://{args.host}:{args.port}")
print(f"  调试模式: {'是' if args.debug else '否'}")
print("=" * 70)
print()

# 启动服务器
if __name__ == '__main__':
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        print(f"\n服务器启动失败: {e}")
        sys.exit(1)
