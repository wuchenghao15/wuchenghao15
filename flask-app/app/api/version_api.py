# -*- coding: utf-8 -*-
"""
系统版本管理API
提供版本信息和更新日志接口
"""

from flask import Blueprint, jsonify, request
from app.version import (
    VERSION, VERSION_INFO, CHANGELOG, RELEASE_DATE,
    get_version, get_version_info, get_changelog,
    get_latest_version, get_changelog_by_version, check_for_updates,
    get_version_range, get_major_versions, get_version_stats
)
from app.models.database_version_manager import db_version_manager
from app.services.version_manager import version_manager
from app.utils.logging import logger
from app.services.auto_version_updater import get_auto_version_updater

version_api = Blueprint('version_api', __name__)


@version_api.route('/version')
def get_version_endpoint():
    """获取当前版本信息"""
    return jsonify({
        'success': True,
        'version': VERSION,
        'version_info': VERSION_INFO
    })


@version_api.route('/version/changelog')
def get_changelog_endpoint():
    """获取更新日志"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated = CHANGELOG[start:end]
    
    return jsonify({
        'success': True,
        'changelog': paginated,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': len(CHANGELOG),
            'total_pages': (len(CHANGELOG) + per_page - 1) // per_page
        }
    })


@version_api.route('/version/changelog/<version>')
def get_changelog_by_version_endpoint(version):
    """获取指定版本的更新日志"""
    changelog = get_changelog_by_version(version)
    
    if changelog:
        return jsonify({
            'success': True,
            'changelog': changelog
        })
    else:
        return jsonify({
            'success': False,
            'error': f'版本 {version} 不存在'
        }), 404


@version_api.route('/version/check-update')
def check_update_endpoint():
    """检查更新"""
    current_version = request.args.get('current_version', VERSION)
    result = check_for_updates(current_version)
    
    return jsonify({
        'success': True,
        'update_info': result
    })


@version_api.route('/version/latest')
def get_latest_version_endpoint():
    """获取最新版本信息"""
    latest = get_latest_version()
    
    return jsonify({
        'success': True,
        'latest_version': latest
    })


@version_api.route('/version/database')
def get_database_version():
    """获取数据库版本信息"""
    try:
        stats = db_version_manager.get_database_stats()
        versions = db_version_manager.get_all_versions()
        
        return jsonify({
            'success': True,
            'database_stats': stats,
            'versions': versions
        })
    except Exception as e:
        logger.error(f"获取数据库版本信息失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/summary')
def get_version_summary():
    """获取版本摘要"""
    summary = {
        'application': VERSION_INFO,
        'database': {
            'total_versions': 0,
            'latest_version': 'N/A'
        },
        'api_status': 'operational',
        'last_updated': RELEASE_DATE
    }
    
    try:
        stats = db_version_manager.get_database_stats()
        versions = db_version_manager.get_all_versions()
        
        summary['database']['total_versions'] = stats.get('version_count', 0)
        if versions:
            summary['database']['latest_version'] = versions[0].get('version', 'N/A')
    except Exception as e:
        logger.error(f"获取数据库摘要失败: {e}")
    
    return jsonify({
        'success': True,
        'summary': summary
    })


@version_api.route('/version/export', methods=['POST'])
def export_version_history():
    """导出版本历史"""
    try:
        data = request.get_json()
        format_type = data.get('format', 'json')
        filepath = data.get('filepath', 'version_report')
        
        if format_type not in ['json', 'markdown']:
            return jsonify({
                'success': False,
                'error': '不支持的格式类型'
            }), 400
        
        full_path = f"{filepath}.{format_type}"
        success = db_version_manager.export_version_history(full_path, format_type)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'版本历史已导出到: {full_path}'
            })
        else:
            return jsonify({
                'success': False,
                'error': '导出失败'
            }), 500
    
    except Exception as e:
        logger.error(f"导出版本历史失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/compare')
def compare_versions():
    """比较两个版本"""
    v1 = request.args.get('v1')
    v2 = request.args.get('v2')
    
    if not v1 or not v2:
        return jsonify({
            'success': False,
            'error': '请提供两个版本号 v1 和 v2'
        }), 400
    
    try:
        result = version_manager.compare_versions_detail(v1, v2)
        return jsonify({
            'success': True,
            'comparison': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/diff')
def get_version_diff():
    """获取两个版本之间的差异"""
    v1 = request.args.get('v1')
    v2 = request.args.get('v2')
    
    if not v1 or not v2:
        return jsonify({
            'success': False,
            'error': '请提供两个版本号 v1 和 v2'
        }), 400
    
    try:
        result = version_manager.get_version_diff(v1, v2)
        return jsonify({
            'success': True,
            'diff': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/tree')
def get_version_tree():
    """获取版本树结构"""
    try:
        tree = version_manager.get_version_tree()
        return jsonify({
            'success': True,
            'tree': tree
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/stats')
def get_version_statistics():
    """获取版本统计信息"""
    try:
        changelog_stats = get_version_stats()
        db_stats = version_manager.get_version_statistics()
        
        return jsonify({
            'success': True,
            'stats': {
                'changelog': changelog_stats,
                'database': db_stats
            }
        })
    except Exception as e:
        logger.error(f"获取版本统计失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/major')
def get_major_version_list():
    """获取主版本列表"""
    try:
        majors = get_major_versions()
        return jsonify({
            'success': True,
            'major_versions': majors
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/range')
def get_version_range_endpoint():
    """获取版本范围内的更新记录"""
    start = request.args.get('start')
    end = request.args.get('end')
    
    if not start:
        return jsonify({
            'success': False,
            'error': '请提供起始版本 start'
        }), 400
    
    try:
        versions = get_version_range(start, end)
        return jsonify({
            'success': True,
            'versions': versions,
            'count': len(versions)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/history')
def get_version_history():
    """获取版本历史记录"""
    limit = request.args.get('limit', 20, type=int)
    
    try:
        history = version_manager.get_version_history(limit=limit)
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/upgrade', methods=['POST'])
def upgrade_version():
    """升级版本号"""
    try:
        data = request.get_json() or {}
        level = data.get('level', 'patch')
        description = data.get('description')
        
        new_version = version_manager.upgrade_version(level=level, description=description)
        
        return jsonify({
            'success': True,
            'new_version': new_version,
            'message': f'版本升级成功: {new_version}'
        })
    except Exception as e:
        logger.error(f"版本升级失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/init-changelog', methods=['POST'])
def init_from_changelog():
    """从changelog初始化版本历史"""
    try:
        success = version_manager.initialize_from_changelog()
        
        if success:
            return jsonify({
                'success': True,
                'message': '从changelog初始化版本历史完成'
            })
        else:
            return jsonify({
                'success': False,
                'error': '初始化失败'
            }), 500
    except Exception as e:
        logger.error(f"初始化版本历史失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/<version>')
def get_version_detail(version):
    """获取版本详细信息"""
    try:
        info = version_manager.get_version_info(version)
        changelog = get_changelog_by_version(version)
        
        if info or changelog:
            return jsonify({
                'success': True,
                'version_info': info,
                'changelog': changelog
            })
        else:
            return jsonify({
                'success': False,
                'error': f'版本 {version} 不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/auto-update', methods=['POST'])
def auto_update_version():
    """自动更新版本"""
    try:
        updater = get_auto_version_updater()
        data = request.get_json() or {}
        trigger = data.get('trigger', 'manual')
        
        result = updater.auto_update(trigger=trigger)
        
        return jsonify({
            'success': result.get('success', False),
            'data': result
        })
    except Exception as e:
        logger.error(f"自动更新版本失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/update', methods=['POST'])
def manual_update_version():
    """手动更新版本"""
    try:
        updater = get_auto_version_updater()
        data = request.get_json() or {}
        
        level = data.get('level', 'patch')
        title = data.get('title', '')
        changes = data.get('changes', [])
        
        result = updater.update_version(level=level, changes=changes, title=title)
        
        return jsonify({
            'success': result.get('success', False),
            'data': result
        })
    except Exception as e:
        logger.error(f"手动更新版本失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/git-status')
def get_git_status():
    """获取Git状态"""
    try:
        updater = get_auto_version_updater()
        result = updater.check_git_status()
        
        return jsonify({
            'success': result.get('success', False),
            'data': result
        })
    except Exception as e:
        logger.error(f"获取Git状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@version_api.route('/version/git-pull', methods=['POST'])
def git_pull():
    """拉取最新代码"""
    try:
        updater = get_auto_version_updater()
        result = updater.pull_latest()
        
        return jsonify({
            'success': result.get('success', False),
            'data': result
        })
    except Exception as e:
        logger.error(f"拉取代码失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
