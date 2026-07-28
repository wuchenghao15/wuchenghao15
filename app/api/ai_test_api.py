# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
测试系统API
提供安全工程师测试功能的REST API接口
"""

import json
import time
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from ai_engines.security_engineer_employee import SecurityEngineerEmployee

ai_test_api = Bluelogger.info('ai_test_api', __name__)

_engineer = None

def _get_engineer():
    global _engineer
    if _engineer is None:
        _engineer = SecurityEngineerEmployee()
    return _engineer

@ai_test_api.route('/api/ai/test/engineer/status', methods=['GET'])
@require_login
def get_engineer_status():
    engineer = _get_engineer()
    return jsonify({'success': True, 'data': engineer.get_status(), 'timestamp': datetime.now().isoformat()})

@ai_test_api.route('/api/ai/test/engineer/start', methods=['POST'])
@require_admin
def start_engineer():
    engineer = _get_engineer()
    result = engineer.start()
    return jsonify(result)

@ai_test_api.route('/api/ai/test/engineer/stop', methods=['POST'])
@require_admin
def stop_engineer():
    engineer = _get_engineer()
    result = engineer.stop()
    return jsonify(result)

@ai_test_api.route('/api/ai/test/security/scan', methods=['POST'])
@require_admin
def run_security_scan():
    engineer = _get_engineer()
    scan_type = request.json.get('scan_type', 'full')
    
    try:
        result = engineer.run_security_scan(scan_type)
        return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_test_api.route('/api/ai/test/functional', methods=['POST'])
@require_admin
def run_functional_tests():
    engineer = _get_engineer()
    categories = request.json.get('categories', None)
    
    try:
        result = engineer.run_functional_tests(categories)
        return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_test_api.route('/api/ai/test/performance', methods=['POST'])
@require_admin
def run_performance_tests():
    engineer = _get_engineer()
    duration = request.json.get('duration', 30)
    
    try:
        result = engineer.run_performance_tests(duration)
        return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_test_api.route('/api/ai/test/full', methods=['POST'])
@require_admin
def run_full_test_suite():
    engineer = _get_engineer()
    
    try:
        result = engineer.run_full_test_suite()
        return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_test_api.route('/api/ai/test/report', methods=['GET'])
@require_login
def get_test_report():
    engineer = _get_engineer()
    report_type = request.args.get('type', 'full')
    
    try:
        result = engineer.generate_test_report(report_type)
        return jsonify({'success': True, 'data': result, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_test_api.route('/api/ai/test/rules', methods=['GET'])
@require_login
def get_test_rules():
    engineer = _get_engineer()
    return jsonify({'success': True, 'data': engineer.test_rules, 'timestamp': datetime.now().isoformat()})

@ai_test_api.route('/api/ai/test/rules/write', methods=['POST'])
@require_admin
def write_test_rules():
    engineer = _get_engineer()
    
    try:
        result = engineer.write_test_rules_to_system()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_test_api.route('/api/ai/test/findings', methods=['GET'])
@require_login
def get_security_findings():
    engineer = _get_engineer()
    severity = request.args.get('severity', None)
    
    findings = engineer.security_findings
    if severity:
        findings = [f for f in findings if f['severity'] == severity]
    
    return jsonify({
        'success': True,
        'data': findings,
        'count': len(findings),
        'timestamp': datetime.now().isoformat()
    })

@ai_test_api.route('/api/ai/test/results', methods=['GET'])
@require_login
def get_test_results():
    engineer = _get_engineer()
    test_type = request.args.get('type', None)
    
    results = engineer.test_results
    if test_type:
        results = [r for r in results if r['test_type'] == test_type]
    
    return jsonify({
        'success': True,
        'data': results,
        'count': len(results),
        'timestamp': datetime.now().isoformat()
    })

@ai_test_api.route('/api/ai/test/findings/<finding_id>/resolve', methods=['POST'])
@require_admin
def resolve_finding(finding_id):
    engineer = _get_engineer()
    
    try:
        db_path = engineer._save_security_finding.__code__.co_consts[1]
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE security_findings SET status = ? WHERE finding_id = ?', ('resolved', finding_id))
            conn.commit()
        
        for finding in engineer.security_findings:
            if finding['finding_id'] == finding_id:
                finding['status'] = 'resolved'
                break
        
        return jsonify({'success': True, 'message': '安全发现已处理'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500