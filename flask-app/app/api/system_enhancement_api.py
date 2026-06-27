# -*- coding: utf-8 -*-
"""
系统增强API
提供文件上传下载、搜索、数据导出等通用功能
"""

from flask import Blueprint, request, jsonify, session, send_file, Response
import logging
import os

logger = logging.getLogger(__name__)

system_enhancement_bp = Blueprint('system_enhancement', __name__)


def get_current_user():
    """获取当前用户"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    username = session.get('username', '')
    role = session.get('role', '')
    return user_id, {'username': username, 'role': role}


def get_file_service():
    """获取文件服务"""
    try:
        from app.services.system_enhancement_service import FileStorageService
        return FileStorageService()
    except Exception as e:
        logger.error(f"获取文件服务失败: {str(e)}")
        return None


def get_search_service():
    """获取搜索服务"""
    try:
        from app.services.system_enhancement_service import SearchService
        return SearchService()
    except Exception as e:
        logger.error(f"获取搜索服务失败: {str(e)}")
        return None


def get_export_service():
    """获取导出服务"""
    try:
        from app.services.system_enhancement_service import DataExportService
        return DataExportService()
    except Exception as e:
        logger.error(f"获取导出服务失败: {str(e)}")
        return None


# ==================== 文件上传下载 ====================

@system_enhancement_bp.route('/api/files/upload', methods=['POST'])
def upload_file():
    """上传文件"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有上传文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400

        category = request.form.get('category', 'general')
        description = request.form.get('description', '')
        is_public = int(request.form.get('is_public', 0))

        service = get_file_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        result = service.upload_file(
            file, file.filename,
            uploader_id=user_id,
            uploader_name=user_info.get('username'),
            category=category,
            description=description,
            is_public=is_public
        )

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_enhancement_bp.route('/api/files', methods=['GET'])
def get_user_files():
    """获取用户文件列表"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        category = request.args.get('category')
        limit = request.args.get('limit', 50, type=int)

        service = get_file_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        files = service.get_user_files(user_id, category, limit)
        return jsonify({
            'success': True,
            'files': files,
            'count': len(files)
        })
    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_enhancement_bp.route('/api/files/<int:file_id>', methods=['GET'])
def get_file_info(file_id):
    """获取文件信息"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_file_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        file_info = service.get_file(file_id)
        if not file_info:
            return jsonify({'success': False, 'error': '文件不存在'}), 404

        if not file_info.get('is_public') and file_info.get('uploader_id') != user_id:
            if user_info.get('role') not in ['admin', 'super_admin', 'hardware_admin']:
                return jsonify({'success': False, 'error': '无权访问'}), 403

        return jsonify({
            'success': True,
            'file': file_info
        })
    except Exception as e:
        logger.error(f"获取文件信息失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_enhancement_bp.route('/api/files/<int:file_id>/download', methods=['GET'])
def download_file(file_id):
    """下载文件"""
    try:
        service = get_file_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        file_info = service.get_file(file_id)
        if not file_info:
            return jsonify({'success': False, 'error': '文件不存在'}), 404

        file_path = file_info['file_path']
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件已删除'}), 404

        service.increment_download(file_id)

        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_info.get('original_name', file_info['filename']),
            mimetype=file_info.get('mime_type', 'application/octet-stream')
        )
    except Exception as e:
        logger.error(f"文件下载失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_enhancement_bp.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """删除文件"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_file_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        is_admin = user_info.get('role') in ['admin', 'super_admin', 'hardware_admin']
        uploader_id = None if is_admin else user_id

        success = service.delete_file(file_id, uploader_id)
        if not success:
            return jsonify({'success': False, 'error': '文件不存在或无权删除'}), 404

        return jsonify({
            'success': True,
            'message': '文件已删除'
        })
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_enhancement_bp.route('/api/files/stats', methods=['GET'])
def get_file_stats():
    """获取文件统计"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_file_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        is_admin = user_info.get('role') in ['admin', 'super_admin', 'hardware_admin']
        stats = service.get_stats(None if is_admin else user_id)

        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"获取文件统计失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 搜索功能 ====================

@system_enhancement_bp.route('/api/search', methods=['GET'])
def search():
    """全局搜索"""
    try:
        query = request.args.get('q', '')
        search_type = request.args.get('type', 'all')
        limit = request.args.get('limit', 20, type=int)

        service = get_search_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        results = service.search(query, search_type, limit)
        return jsonify({
            'success': True,
            'query': query,
            'total': results.get('total', 0),
            'results': results.get('results', [])
        })
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_enhancement_bp.route('/api/search/suggestions', methods=['GET'])
def search_suggestions():
    """搜索建议"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 10, type=int)

        service = get_search_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        suggestions = service.search_suggestions(query, limit)
        return jsonify({
            'success': True,
            'query': query,
            'suggestions': suggestions,
            'count': len(suggestions)
        })
    except Exception as e:
        logger.error(f"获取搜索建议失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 数据导出 ====================

@system_enhancement_bp.route('/api/export/user', methods=['GET'])
def export_user_data():
    """导出用户数据"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        export_format = request.args.get('format', 'json')

        service = get_export_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        result = service.export_user_data(user_id, export_format)
        if not result['success']:
            return jsonify(result), 400

        return Response(
            result['content'],
            mimetype=result['mime_type'],
            headers={
                'Content-Disposition': f'attachment; filename="{result["filename"]}"'
            }
        )
    except Exception as e:
        logger.error(f"导出用户数据失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@system_enhancement_bp.route('/api/export/exam/<int:exam_id>', methods=['GET'])
def export_exam_results(exam_id):
    """导出考试结果"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    if user_info.get('role') not in ['teacher', 'admin', 'super_admin', 'hardware_admin']:
        return jsonify({'success': False, 'error': '无权限'}), 403

    try:
        export_format = request.args.get('format', 'json')

        service = get_export_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        result = service.export_exam_results(exam_id, export_format)
        if not result['success']:
            return jsonify(result), 400

        return Response(
            result['content'],
            mimetype=result['mime_type'],
            headers={
                'Content-Disposition': f'attachment; filename="{result["filename"]}"'
            }
        )
    except Exception as e:
        logger.error(f"导出考试结果失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
