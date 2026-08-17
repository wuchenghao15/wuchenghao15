#!/usr/bin/env python3
"""
安全漏洞管理 API
=================
提供漏洞管理、攻击模拟、安全扫描、修复方案等API接口。
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps

security_vuln_api = Bluelogger.info('security_vuln_api', __name__)


def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        role = session.get('role', 'guest')
        if role not in ['admin', 'super_admin', 'security_admin']:
            return jsonify({'success': False, 'error': '权限不足'}), 403
        return f(*args, **kwargs)
    return decorated_function


@security_vuln_api.route('/api/security/vulnerabilities', methods=['GET'])
@require_admin
def list_vulnerabilities():
    from security_vulnerability_service import vulnerability_service
    severity = request.args.get('severity')
    category = request.args.get('category')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    vulns = vulnerability_service.list_vulnerabilities(severity, category, status, limit, offset)
    return jsonify({'success': True, 'data': vulns, 'total': len(vulns)})


@security_vuln_api.route('/api/security/vulnerabilities/<vuln_id>', methods=['GET'])
@require_admin
def get_vulnerability(vuln_id):
    from security_vulnerability_service import vulnerability_service
    vuln = vulnerability_service.get_vulnerability(vuln_id)
    if vuln:
        return jsonify({'success': True, 'data': vuln})
    return jsonify({'success': False, 'error': '漏洞不存在'}), 404


@security_vuln_api.route('/api/security/vulnerabilities', methods=['POST'])
@require_admin
def add_vulnerability():
    from security_vulnerability_service import vulnerability_service
    data = request.json
    result = vulnerability_service.add_vulnerability(
        name=data.get('name'),
        category=data.get('category'),
        severity=data.get('severity'),
        description=data.get('description', ''),
        **{k: v for k, v in data.items() if k not in ['name', 'category', 'severity', 'description']}
    )
    return jsonify(result)


@security_vuln_api.route('/api/security/vulnerabilities/<vuln_id>/signatures', methods=['POST'])
@require_admin
def add_signature(vuln_id):
    from security_vulnerability_service import vulnerability_service
    data = request.json
    result = vulnerability_service.add_signature(
        vuln_id=vuln_id,
        signature_type=data.get('signature_type'),
        pattern=data.get('pattern'),
        payload=data.get('payload'),
        detection_method=data.get('detection_method', ''),
        severity=data.get('severity', 'medium'),
        description=data.get('description', '')
    )
    return jsonify(result)


@security_vuln_api.route('/api/security/vulnerabilities/<vuln_id>/fixes', methods=['POST'])
@require_admin
def add_fix(vuln_id):
    from security_vulnerability_service import vulnerability_service
    data = request.json
    result = vulnerability_service.add_fix(
        vuln_id=vuln_id,
        fix_title=data.get('fix_title'),
        fix_description=data.get('fix_description', ''),
        fix_code=data.get('fix_code', ''),
        fix_steps=data.get('fix_steps', ''),
        fix_type=data.get('fix_type', 'code_fix'),
        estimated_effort_hours=data.get('estimated_effort_hours', 1)
    )
    return jsonify(result)


@security_vuln_api.route('/api/security/scans', methods=['POST'])
@require_admin
def create_scan():
    from security_vulnerability_service import vulnerability_service
    data = request.json
    result = vulnerability_service.create_scan(
        scan_name=data.get('scan_name'),
        scan_type=data.get('scan_type'),
        target=data.get('target'),
        initiated_by=str(session.get('user_id', 'system'))
    )
    return jsonify(result)


@security_vuln_api.route('/api/security/scans/<scan_id>/run', methods=['POST'])
@require_admin
def run_scan(scan_id):
    from security_vulnerability_service import vulnerability_service
    data = request.json or {}
    target_url = data.get('target_url', 'http://localhost:8888/auth/login')
    result = vulnerability_service.run_security_scan(scan_id, target_url)
    return jsonify(result)


@security_vuln_api.route('/api/security/simulate/sql-injection', methods=['POST'])
@require_admin
def simulate_sql_injection():
    from security_vulnerability_service import vulnerability_service
    data = request.json
    result = vulnerability_service.simulate_sql_injection(
        target_url=data.get('target_url', '/auth/login'),
        param_name=data.get('param_name', 'username')
    )
    return jsonify(result)


@security_vuln_api.route('/api/security/simulate/xss', methods=['POST'])
@require_admin
def simulate_xss():
    from security_vulnerability_service import vulnerability_service
    data = request.json
    result = vulnerability_service.simulate_xss(
        target_url=data.get('target_url', '/search'),
        param_name=data.get('param_name', 'q')
    )
    return jsonify(result)


@security_vuln_api.route('/api/security/simulations', methods=['GET'])
@require_admin
def list_simulations():
    from security_vulnerability_service import vulnerability_service
    attack_type = request.args.get('attack_type')
    limit = int(request.args.get('limit', 50))
    sims = vulnerability_service.list_simulations(attack_type, limit)
    return jsonify({'success': True, 'data': sims, 'total': len(sims)})


@security_vuln_api.route('/api/security/stats', methods=['GET'])
@require_admin
def get_security_stats():
    from security_vulnerability_service import vulnerability_service
    stats = vulnerability_service.get_security_stats()
    return jsonify({'success': True, 'data': stats})


@security_vuln_api.route('/api/security/learning/sync', methods=['POST'])
@require_admin
def sync_learning():
    from security_vulnerability_service import vulnerability_service
    data = request.json or {}
    category = data.get('category', 'security')
    result = vulnerability_service.sync_learning_to_brain(category)
    return jsonify(result)
