from flask import Blueprint, request, jsonify

ai_diagnosis_bp = Bluelogger.info('ai_diagnosis', __name__)

from app.ai.ai_learning_diagnosis import ai_learning_diagnosis

@ai_diagnosis_bp.route('/diagnose', methods=['POST'])
def diagnose():
    """执行学习诊断"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        subject = data.get('subject')
        
        if not user_id or not subject:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        result = ai_learning_diagnosis.diagnose_learning(user_id, subject)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_diagnosis_bp.route('/diagnosis/<record_id>', methods=['GET'])
def get_diagnosis(record_id):
    """获取诊断记录详情"""
    try:
        result = ai_learning_diagnosis.get_diagnosis(record_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_diagnosis_bp.route('/diagnosis/<record_id>', methods=['DELETE'])
def delete_diagnosis(record_id):
    """删除诊断记录"""
    try:
        result = ai_learning_diagnosis.delete_diagnosis(record_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_diagnosis_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """获取学习分析数据"""
    try:
        user_id = request.args.get('user_id')
        subject = request.args.get('subject')
        
        if not user_id:
            return jsonify({'success': False, 'error': '缺少user_id参数'}), 400
        
        result = ai_learning_diagnosis.get_learning_analytics(user_id, subject)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_diagnosis_bp.route('/knowledge-points', methods=['GET'])
def get_knowledge_points():
    """获取知识点列表"""
    try:
        subject = request.args.get('subject')
        
        if not subject:
            return jsonify({'success': False, 'error': '缺少subject参数'}), 400
        
        result = ai_learning_diagnosis.get_knowledge_points(subject)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_diagnosis_bp.route('/knowledge-points', methods=['POST'])
def add_knowledge_point():
    """添加知识点"""
    try:
        data = request.get_json()
        subject = data.get('subject')
        domain = data.get('domain')
        point_name = data.get('point_name')
        description = data.get('description', '')
        
        if not subject or not domain or not point_name:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        result = ai_learning_diagnosis.add_knowledge_point(subject, domain, point_name, description)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_diagnosis_bp.route('/knowledge-points/<point_id>', methods=['DELETE'])
def delete_knowledge_point(point_id):
    """删除知识点"""
    try:
        result = ai_learning_diagnosis.delete_knowledge_point(point_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_diagnosis_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """获取提升任务列表"""
    try:
        user_id = request.args.get('user_id')
        subject = request.args.get('subject')
        status = request.args.get('status')
        
        if not user_id:
            return jsonify({'success': False, 'error': '缺少user_id参数'}), 400
        
        result = ai_learning_diagnosis.get_improvement_tasks(user_id, subject, status)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_diagnosis_bp.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务状态"""
    try:
        data = request.get_json()
        status = data.get('status')
        current_score = data.get('current_score')
        
        result = ai_learning_diagnosis.update_improvement_task(task_id, status, current_score)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_diagnosis_bp.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除提升任务"""
    try:
        result = ai_learning_diagnosis.delete_improvement_task(task_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_diagnosis_bp.route('/report', methods=['POST'])
def generate_report():
    """生成诊断报告"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        subject = data.get('subject')
        
        if not user_id or not subject:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        result = ai_learning_diagnosis.generate_report(user_id, subject)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_diagnosis_bp.route('/report/<report_id>', methods=['GET'])
def get_report(report_id):
    """获取诊断报告"""
    try:
        result = ai_learning_diagnosis.get_report(report_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_diagnosis_bp.route('/history', methods=['GET'])
def get_history():
    """获取诊断历史"""
    try:
        user_id = request.args.get('user_id')
        subject = request.args.get('subject')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        if not user_id:
            return jsonify({'success': False, 'error': '缺少user_id参数'}), 400
        
        result = ai_learning_diagnosis.get_diagnosis_history(user_id, subject, page, limit)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500