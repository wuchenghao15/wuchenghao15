#!/usr/bin/env python3
"""
SSL / VPN 管理 API
====================
SSL证书管理、HTTPS配置、VPN管理、代理管理的RESTful API。
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps

sslvpn_api = Bluelogger.info('sslvpn_api', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        if session.get('role') not in ['admin', 'super_admin']:
            return jsonify({'success': False, 'error': '权限不足'}), 403
        return f(*args, **kwargs)
    return decorated


# ==================== SSL证书管理 ====================

@sslvpn_api.route('/api/sslvpn/certificates', methods=['GET'])
@admin_required
def list_certificates():
    from sslvpn_service import sslvpn_service
    certs = sslvpn_service.list_certificates()
    return jsonify({'success': True, 'data': certs, 'total': len(certs)})


@sslvpn_api.route('/api/sslvpn/certificates', methods=['POST'])
@admin_required
def generate_certificate():
    from sslvpn_service import sslvpn_service
    data = request.json
    result = sslvpn_service.generate_self_signed_cert(
        domain=data.get('domain', 'localhost'),
        org=data.get('org', 'MTSCOS AI'),
        org_unit=data.get('org_unit', 'IT'),
        country=data.get('country', 'CN'),
        state=data.get('state', 'Beijing'),
        city=data.get('city', 'Beijing'),
        days_valid=int(data.get('days_valid', 3650)),
        key_size=int(data.get('key_size', 2048)),
        name=data.get('name')
    )
    return jsonify(result)


@sslvpn_api.route('/api/sslvpn/certificates/<cert_id>/default', methods=['PUT'])
@admin_required
def set_default_cert(cert_id):
    from sslvpn_service import sslvpn_service
    result = sslvpn_service.set_default_certificate(cert_id)
    return jsonify(result)


@sslvpn_api.route('/api/sslvpn/certificates/<cert_id>', methods=['DELETE'])
@admin_required
def delete_certificate(cert_id):
    from sslvpn_service import sslvpn_service
    result = sslvpn_service.delete_certificate(cert_id)
    return jsonify(result)


@sslvpn_api.route('/api/sslvpn/certificates/expiring', methods=['GET'])
@admin_required
def get_expiring_certs():
    from sslvpn_service import sslvpn_service
    expiring = sslvpn_service.check_cert_expiry()
    return jsonify({'success': True, 'data': expiring, 'total': len(expiring)})


# ==================== SSL配置 ====================

@sslvpn_api.route('/api/sslvpn/config', methods=['GET'])
@admin_required
def get_ssl_config():
    from sslvpn_service import sslvpn_service
    config = sslvpn_service.get_ssl_config()
    return jsonify({'success': True, 'data': config})


@sslvpn_api.route('/api/sslvpn/config', methods=['PUT'])
@admin_required
def update_ssl_config():
    from sslvpn_service import sslvpn_service
    data = request.json or {}
    result = sslvpn_service.update_ssl_config(**data)
    return jsonify(result)


@sslvpn_api.route('/api/sslvpn/config/headers', methods=['GET'])
@admin_required
def get_security_headers():
    from sslvpn_service import sslvpn_service
    headers = sslvpn_service.get_security_headers()
    return jsonify({'success': True, 'data': headers})


@sslvpn_api.route('/api/sslvpn/config/test', methods=['GET'])
@admin_required
def test_ssl_config():
    from sslvpn_service import sslvpn_service
    result = sslvpn_service.test_ssl_config()
    return jsonify(result)


# ==================== VPN管理 ====================

@sslvpn_api.route('/api/sslvpn/vpns', methods=['GET'])
@admin_required
def list_vpns():
    from sslvpn_service import sslvpn_service
    vpns = sslvpn_service.list_vpn_configs()
    return jsonify({'success': True, 'data': vpns, 'total': len(vpns)})


@sslvpn_api.route('/api/sslvpn/vpns/wireguard', methods=['POST'])
@admin_required
def create_wireguard_vpn():
    from sslvpn_service import sslvpn_service
    data = request.json
    result = sslvpn_service.create_wireguard_config(
        name=data.get('name', 'WireGuard VPN'),
        server_address=data.get('server_address', ''),
        port=int(data.get('port', 51820)),
        network=data.get('network', '10.0.0.0/24'),
        dns=data.get('dns', '8.8.8.8, 1.1.1.1'),
        mtu=int(data.get('mtu', 1420)),
        keepalive=int(data.get('keepalive', 25))
    )
    return jsonify(result)


@sslvpn_api.route('/api/sslvpn/vpns/<vpn_id>/users', methods=['GET'])
@admin_required
def list_vpn_users(vpn_id):
    from sslvpn_service import sslvpn_service
    users = sslvpn_service.list_vpn_users(vpn_id)
    return jsonify({'success': True, 'data': users, 'total': len(users)})


@sslvpn_api.route('/api/sslvpn/vpns/<vpn_id>/users', methods=['POST'])
@admin_required
def add_vpn_user(vpn_id):
    from sslvpn_service import sslvpn_service
    data = request.json
    result = sslvpn_service.add_vpn_user(
        vpn_id=vpn_id,
        username=data.get('username', ''),
        client_ip=data.get('client_ip')
    )
    return jsonify(result)


@sslvpn_api.route('/api/sslvpn/vpn-users/<user_id>/toggle', methods=['PUT'])
@admin_required
def toggle_vpn_user(user_id):
    from sslvpn_service import sslvpn_service
    data = request.json
    active = data.get('active', True)
    result = sslvpn_service.toggle_vpn_user(user_id, active)
    return jsonify(result)


# ==================== VPN服务器控制 ====================

@sslvpn_api.route('/api/sslvpn/vpn-server/status', methods=['GET'])
@admin_required
def get_vpn_server_status():
    from sslvpn_service import sslvpn_service
    result = sslvpn_service.get_vpn_server_status()
    return jsonify(result)


@sslvpn_api.route('/api/sslvpn/vpn-server/clients', methods=['GET'])
@admin_required
def get_vpn_server_clients():
    from sslvpn_service import sslvpn_service
    result = sslvpn_service.get_vpn_server_clients()
    return jsonify(result)


@sslvpn_api.route('/api/sslvpn/vpn-server/stats', methods=['GET'])
@admin_required
def get_vpn_server_stats():
    from sslvpn_service import sslvpn_service
    result = sslvpn_service.get_vpn_server_stats()
    return jsonify(result)


@sslvpn_api.route('/api/sslvpn/vpn-server/start', methods=['POST'])
@admin_required
def start_vpn_server():
    from sslvpn_service import sslvpn_service
    data = request.json or {}
    port = data.get('port', 51820)
    result = sslvpn_service.start_vpn_server(port)
    return jsonify(result)


@sslvpn_api.route('/api/sslvpn/vpn-server/stop', methods=['POST'])
@admin_required
def stop_vpn_server():
    from sslvpn_service import sslvpn_service
    result = sslvpn_service.stop_vpn_server()
    return jsonify(result)


@sslvpn_api.route('/api/sslvpn/vpn-server/client/<client_id>/disconnect', methods=['POST'])
@admin_required
def disconnect_vpn_client(client_id):
    from sslvpn_service import sslvpn_service
    result = sslvpn_service.disconnect_vpn_client(int(client_id))
    return jsonify(result)


@sslvpn_api.route('/api/sslvpn/vpn-types', methods=['GET'])
@admin_required
def get_vpn_types():
    from sslvpn_service import sslvpn_service
    return jsonify({'success': True, 'data': sslvpn_service.VPN_TYPES})


# ==================== 代理管理 ====================

@sslvpn_api.route('/api/sslvpn/proxies', methods=['GET'])
@admin_required
def list_proxies():
    from sslvpn_service import sslvpn_service
    proxy_type = request.args.get('type')
    active_only = request.args.get('active') == '1'
    proxies = sslvpn_service.list_proxies(proxy_type, active_only)
    return jsonify({'success': True, 'data': proxies, 'total': len(proxies)})


@sslvpn_api.route('/api/sslvpn/proxies', methods=['POST'])
@admin_required
def add_proxy():
    from sslvpn_service import sslvpn_service
    data = request.json
    result = sslvpn_service.add_proxy(
        name=data.get('name', ''),
        proxy_type=data.get('proxy_type', 'http'),
        host=data.get('host', ''),
        port=int(data.get('port', 8080)),
        username=data.get('username'),
        password=data.get('password'),
        country=data.get('country')
    )
    return jsonify(result)


@sslvpn_api.route('/api/sslvpn/proxies/<proxy_id>/test', methods=['POST'])
@admin_required
def test_proxy(proxy_id):
    from sslvpn_service import sslvpn_service
    data = request.json or {}
    result = sslvpn_service.test_proxy(proxy_id, data.get('test_url', 'https://www.google.com'))
    return jsonify(result)


@sslvpn_api.route('/api/sslvpn/proxies/<proxy_id>', methods=['DELETE'])
@admin_required
def delete_proxy(proxy_id):
    from sslvpn_service import sslvpn_service
    result = sslvpn_service.delete_proxy(proxy_id)
    return jsonify(result)


# ==================== 统计与日志 ====================

@sslvpn_api.route('/api/sslvpn/stats', methods=['GET'])
@admin_required
def get_stats():
    from sslvpn_service import sslvpn_service
    stats = sslvpn_service.get_stats()
    return jsonify({'success': True, 'data': stats})


@sslvpn_api.route('/api/sslvpn/logs', methods=['GET'])
@admin_required
def get_logs():
    from sslvpn_service import sslvpn_service
    log_type = request.args.get('type')
    limit = int(request.args.get('limit', 50))
    logs = sslvpn_service.get_logs(log_type, limit)
    return jsonify({'success': True, 'data': logs, 'total': len(logs)})
