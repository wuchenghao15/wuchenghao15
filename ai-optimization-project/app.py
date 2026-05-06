#!/usr/bin/env python3
"""
Web服务器模块 - 提供Web界面和API

from flask import Flask, jsonify, render_template, request, g
from flask_cors import CORS
from functools import wraps
import time
import traceback
import os
# JSON import removed - using database
from utils.logging import logger
from services.ai_optimizer import ai_optimizer
from services.system_optimizer import system_optimizer
from services.maintenance import maintenance_service
from services.terminal_monitor import terminal_monitor
from services.server_optimizer_ai import server_optimizer_ai
from config.config import config

app = Flask(__name__)
CORS(app)  # 启用CORS

# 确保templates目录存在
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

# 确保static目录存在
static_dir = os.path.join(os.path.dirname(__file__), 'static')
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

@app.before_request
def before_request():
    """请求前处理"""
    g.start_time = time.time()
    g.request = request

    # 记录请求基本信息
    g.terminal_id = terminal_monitor.generate_terminal_id(request)
    g.client_ip = terminal_monitor.get_client_ip(request)

    # 检查访问控制
    access_status = terminal_monitor.db.check_access_control(g.client_ip)
    if access_status == 'blocked':
        return jsonify({
            'success': False,
            'error': 'IP已被阻止',
            'ip': g.client_ip
        }), 403

@app.after_request
def after_request(response):
    """请求后处理"""
    # 记录请求
    try:
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            terminal_monitor.record_request(request, response, response_time)
    except Exception as e:
        logger.error(f"记录请求失败: {str(e)}")

    return response

@app.errorhandler(404)
def handle_404(e):
    """404错误处理"""
    # 记录错误
    terminal_monitor.record_error(
        error_type='404',
        error_message=str(e),
        severity='low',
        source='server',
        request=request
    )

    logger.warning(f"404错误: {str(e)}")

    return jsonify({
        'error': '页面不存在',
    }), 404

@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理"""
    error_trace = traceback.format_exc()

    # 记录错误
    terminal_monitor.record_error(
        error_type='exception',
        severity='high',
        request=request,
        stack_trace=error_trace

    logger.error(f"全局异常: {str(e)}")

    return jsonify({
        'error': '服务器内部错误',

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    report = maintenance_service.perform_health_check()
    return jsonify(report)

@app.route('/api/metrics')
def get_metrics():
    """获取系统指标"""
    ai_metrics = ai_optimizer.get_system_metrics()
    server_metrics = system_optimizer.get_server_metrics()

    return jsonify({
        'server_metrics': server_metrics
    })

@app.route('/api/optimization')
def get_optimization_status():
    """获取优化状态"""
    report = system_optimizer.get_optimization_report()
    return jsonify(report)

@app.route('/api/maintenance')
def get_maintenance_status():
    """获取维护状态"""
    report = maintenance_service.get_maintenance_report()
    return jsonify(report)

@app.route('/api/models')
def get_models():
    """获取AI模型列表"""
    models = ai_optimizer.get_models()

@app.route('/api/backup', methods=['POST'])
def perform_backup():
    """执行备份"""
    result = maintenance_service.perform_backup()

@app.route('/api/health-check', methods=['POST'])
def run_health_check():
    """执行健康检查"""
    report = maintenance_service.perform_health_check()
    return jsonify(report)

@app.route('/api/optimize', methods=['POST'])
def run_optimization():
    """执行优化"""
    data = request.json or {}
    project_name = data.get('project_name')

    if project_name:
        result = system_optimizer.optimize_project(project_name)
    else:
        results = []
            result = system_optimizer.optimize_project(project_name)
            results.append(result)
        result = {
            'status': 'success',
            'results': results
        }

    return jsonify(result)

@app.route('/api/version')
def get_version():
    """获取系统版本"""
    return jsonify({
        'version': config.VERSION,
        'build_date': config.BUILD_DATE
    })
# 终端监控API路由
@app.route('/api/terminals')
def get_terminals():
    """获取所有终端信息"""
    try:
        terminals = terminal_monitor.get_terminals()
            'data': terminals,
            'count': len(terminals)
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/terminals/<terminal_id>')
def get_terminal(terminal_id):
    """获取指定终端信息"""
        terminal = next((t for t in terminals if t['terminal_id'] == terminal_id), None)

        if not terminal:
            return jsonify({
                'error': '终端不存在'
            }), 404

        return jsonify({
        })
    except Exception as e:
        return jsonify({
        }), 500

@app.route('/api/errors')
def get_errors():
    """获取所有错误信息"""
    try:
        limit = request.args.get('limit', 100, type=int)
        errors = terminal_monitor.get_errors(limit)
            'data': errors,
            'count': len(errors)
        })
        logger.error(f"获取错误列表失败: {str(e)}")
        }), 500

@app.route('/api/terminal-stats')
def get_terminal_stats():
    try:
        stats = terminal_monitor.get_access_stats()
        return jsonify({
            'data': stats
        })
        logger.error(f"获取统计信息失败: {str(e)}")
        }), 500

def add_to_blacklist():
    """添加IP到黑名单"""
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        if not ip_address:
            return jsonify({
            }), 400

        success = terminal_monitor.block_ip(ip_address, reason)

        return jsonify({
            'message': f'IP {ip_address} 已添加到黑名单' if success else '添加失败'
        return jsonify({
            'error': str(e)
        }), 500

    """从黑名单移除IP"""
    try:
        success = terminal_monitor.unblock_ip(ip_address)

        return jsonify({
        })
    except Exception as e:
        logger.error(f"移除黑名单失败: {str(e)}")
        return jsonify({

@app.route('/api/whitelist', methods=['POST'])
    """添加IP到白名单"""
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        reason = data.get('reason', '手动白名单')

        if not ip_address:
                'error': 'IP地址不能为空'
            }), 400
        success = terminal_monitor.whitelist_ip(ip_address, reason)
            'message': f'IP {ip_address} 已添加到白名单' if success else '添加失败'
        })
    except Exception as e:
        logger.error(f"添加白名单失败: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/record-client-error', methods=['POST'])
def record_client_error():
    """记录客户端错误"""
    try:
            error_type='client_exception',
            error_message=data.get('exception_message', ''),
            source='client',
            request=request,
            exception_type=data.get('exception_type'),
            stack_trace=data.get('stack_trace'),
            console_logs=data.get('console_logs'),
            browser_info=data.get('browser_info'),
            page_url=data.get('page_url')
        )
        return jsonify({
            'message': '客户端错误记录成功'
        })
        logger.error(f"记录客户端错误失败: {str(e)}")
        return jsonify({
        }), 500

# 登录路由（为了避免404错误）
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    """登录路由"""
    if request.method == 'POST':
        # 简单的登录处理
            # 安全处理JSON数据
            if request.is_json:
            else:

            username = data.get('username')

            # 记录登录尝试
            terminal_monitor.record_login_attempt(
                username=username,
                success=False,  # 始终返回失败，因为这是一个模拟登录
                user_agent=request.user_agent.string,
                details={'message': '登录功能未实现'}
            )

            return jsonify({
                'error': '登录功能未实现',
            # 记录错误
                error_type='login_error',
                error_message=str(e),
                severity='medium',
                request=request
            )
            return jsonify({
                'message': '此系统不需要登录'
        return jsonify({
            'message': '此系统不需要登录'

@app.route('/api/server-optimizer/status')
def get_server_status():
    try:
        status = server_optimizer_ai.get_current_status()
        return jsonify({
            'data': status
        })
    except Exception as e:
        logger.error(f"获取服务器状态失败: {str(e)}")
        return jsonify({

def get_performance_data():
    """获取性能数据"""
    try:
        hours = request.args.get('hours', 24, type=int)
        performance_data = server_optimizer_ai.get_performance_data(hours)
            'count': len(performance_data)
        })
    except Exception as e:
        logger.error(f"获取性能数据失败: {str(e)}")
        return jsonify({
            'error': str(e)

@app.route('/api/server-optimizer/optimizations')
def get_optimization_history():
    """获取优化历史"""
        days = request.args.get('days', 7, type=int)
        return jsonify({
            'data': optimizations,
    except Exception as e:
        logger.error(f"获取优化历史失败: {str(e)}")
            'error': str(e)
        }), 500
@app.route('/api/server-optimizer/events')
    try:
        days = request.args.get('days', 7, type=int)
        events = server_optimizer_ai.get_server_events(days)
            'data': events,
            'count': len(events)
    except Exception as e:
            'error': str(e)
        }), 500

@app.route('/api/server-optimizer/optimize', methods=['POST'])
        # 触发优化
        server_optimizer_ai._perform_optimization()

        return jsonify({
            'message': '优化执行成功'
        })
    except Exception as e:
        logger.error(f"执行优化失败: {str(e)}")
        return jsonify({
        }), 500

@app.route('/api/server-optimizer/metrics')
def get_server_metrics():
    """获取服务器指标"""
    try:
        # 获取当前状态

        performance_data = server_optimizer_ai.get_performance_data(1)  # 最近1小时

        # 计算平均值
        if performance_data:
            avg_cpu = sum([item['cpu_usage'] for item in performance_data]) / len(performance_data)
            avg_disk = sum([item['disk_usage'] for item in performance_data]) / len(performance_data)
            avg_cpu = 0
            avg_memory = 0
            avg_disk = 0

        metrics = {
            'current': status.get('performance', {}),
            'average': {
                'disk_usage': avg_disk
            },
            'recent_optimizations': status.get('recent_optimizations', [])
        }

        return jsonify({
            'data': metrics
    except Exception as e:
        logger.error(f"获取服务器指标失败: {str(e)}")
            'error': str(e)
        }), 500

def create_templates():
    index_html = '''
<html lang="zh-CN">
    <meta charset="UTF-8">
    <title>AI优化系统</title>
            margin: 0;
            padding: 0;

        body {
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
        }

        .container {
            padding: 20px;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

            font-size: 1.2em;
            opacity: 0.9;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;

        .card:hover {
            transform: translateY(-5px);
        }

            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5em;
        }

            margin-top: 20px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 10px;
            background: #f9f9f9;
            border-radius: 5px;
        }

        .metric label {
            font-weight: bold;

        .metric value {
            color: #667eea;

        .status {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.9em;
        }

        .status.healthy {
            background: #d4edda;
            color: #155724;

        .status.unhealthy {
            background: #f8d7da;
            color: #721c24;
        }

        .actions {
            margin-top: 20px;
        }

        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            font-size: 1em;
            margin-right: 10px;
            transition: background 0.3s ease;
        }

        button:hover {
            background: #5a6fd8;

        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
        }

        .message {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
            display: none;
        }

        .message.success {
            background: #d4edda;
            color: #155724;
            display: block;
        }

        .message.error {
            background: #f8d7da;
            color: #721c24;
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AI优化系统</h1>
            <div class="version" id="version">版本: 加载中...</div>
        </header>

        <div class="cards">
            <div class="card">
                <h2>系统健康</h2>
                <div id="health-status" class="status">加载中...</div>
                <div class="metrics" id="health-metrics">
                    <!-- 健康指标将通过JavaScript加载 -->
                </div>
            </div>

            <div class="card">
                <h2>系统指标</h2>
                <div class="metrics" id="system-metrics">
                    <!-- 系统指标将通过JavaScript加载 -->
                </div>
            </div>

            <div class="card">
                <h2>优化状态</h2>
                <div class="metrics" id="optimization-status">
                    <!-- 优化状态将通过JavaScript加载 -->
                </div>
            </div>

            <div class="card">
                <h2>维护状态</h2>
                <div class="metrics" id="maintenance-status">
                    <!-- 维护状态将通过JavaScript加载 -->
                </div>
            </div>
        </div>

        <div class="card">
            <h2>操作</h2>
            <div class="actions">
                <button onclick="performBackup()">执行备份</button>
                <button onclick="runHealthCheck()">健康检查</button>
                <button onclick="runOptimization()">执行优化</button>
            </div>
            <div class="loading" id="loading">处理中...</div>
            <div class="message" id="message"></div>
        </div>
    </div>

    <script>
        // 加载版本信息
        fetch('/api/version')
            .then(response => response.json())
            .then(data => {
                document.getElementById('version').textContent = `版本: ${data.version} (${data.build_date})`;
            });

        // 加载健康状态
        function loadHealthStatus() {
            fetch('/api/health')
                .then(response => response.json())
                .then(data => {
                    healthStatus.className = `status ${data.status}`;
                    healthStatus.textContent = data.status === 'healthy' ? '健康' : '不健康';

                    const healthMetrics = document.getElementById('health-metrics');

                    for (const [key, value] of Object.entries(data.checks)) {
                        metric.className = 'metric';
                        metric.innerHTML = `
                            <label>${key}:</label>
                            <value>${value.status}</value>
                        `;
                        healthMetrics.appendChild(metric);
                    }
                });
        }

        // 加载系统指标
        function loadSystemMetrics() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    const systemMetrics = document.getElementById('system-metrics');
                    systemMetrics.innerHTML = '';

                    if (data.ai_metrics) {
                        const aiMetrics = document.createElement('div');
                        aiMetrics.innerHTML = `
                            <label>CPU使用率:</label>
                        `;
                        systemMetrics.appendChild(aiMetrics);

                        const memoryMetrics = document.createElement('div');
                        memoryMetrics.innerHTML = `
                            <label>内存使用率:</label>
                            <value>${data.ai_metrics.memory_usage?.toFixed(2) || 'N/A'}%</value>
                        `;
                        systemMetrics.appendChild(memoryMetrics);
                    }

                        const cpuMetrics = document.createElement('div');
                        cpuMetrics.innerHTML = `
                            <label>服务器CPU:</label>
                            <value>${data.server_metrics.cpu.usage?.toFixed(2) || 'N/A'}%</value>
                        `;
                        systemMetrics.appendChild(cpuMetrics);
                    }
        }

        // 加载优化状态
        function loadOptimizationStatus() {
            fetch('/api/optimization')
                .then(response => response.json())
                .then(data => {
                    const optimizationStatus = document.getElementById('optimization-status');
                    optimizationStatus.innerHTML = '';

                    const totalProjects = document.createElement('div');
                    totalProjects.innerHTML = `
                        <label>总项目数:</label>
                    optimizationStatus.appendChild(totalProjects);

                    const optimizedProjects = document.createElement('div');
                    optimizedProjects.innerHTML = `
                        <label>已优化项目:</label>
                        <value>${data.optimized_projects || 0}</value>
                    `;
                    optimizationStatus.appendChild(optimizedProjects);
                    const pendingProjects = document.createElement('div');
                    pendingProjects.innerHTML = `
                        <label>待优化项目:</label>
                        <value>${data.pending_projects || 0}</value>
                    `;
                    optimizationStatus.appendChild(pendingProjects);
        }
        // 加载维护状态
        function loadMaintenanceStatus() {
            fetch('/api/maintenance')
                .then(response => response.json())
                .then(data => {
                    const maintenanceStatus = document.getElementById('maintenance-status');
                    maintenanceStatus.innerHTML = '';

                        <label>最后备份:</label>
                        <value>${data.maintenance_history?.[0]?.timestamp || '从未'}</value>
                    maintenanceStatus.appendChild(lastBackup);

                    const nextBackup = document.createElement('div');
                    nextBackup.innerHTML = `
                        <value>${data.next_backup || '未知'}</value>
                    `;
                    maintenanceStatus.appendChild(nextBackup);
                });

        // 执行备份
        function performBackup() {
            fetch('/api/backup', {
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                showMessage(data.status === 'success' ? '备份成功' : '备份失败', data.status);
            .catch(error => {
                showMessage('备份失败: ' + error.message, 'error');
            });

        // 执行健康检查
        function runHealthCheck() {
            showLoading();
            fetch('/api/health-check', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                showMessage('健康检查完成', 'success');
                loadHealthStatus();
            })
            .catch(error => {
                hideLoading();
                showMessage('健康检查失败: ' + error.message, 'error');
            });
        }
        // 执行优化
            showLoading();
            fetch('/api/optimize', {
                method: 'POST'
            })
                showMessage('优化完成', 'success');
                loadOptimizationStatus();
            })
            .catch(error => {
                hideLoading();

        // 显示加载状态
        function showLoading() {
            document.getElementById('loading').style.display = 'block';
        }
        }

        // 显示消息
        function showMessage(message, type) {
            const messageDiv = document.getElementById('message');
            messageDiv.className = `message ${type}`;
            messageDiv.textContent = message;
            // 3秒后自动隐藏
            setTimeout(() => {
        }

        // 初始加载
        loadHealthStatus();
        loadSystemMetrics();
        loadOptimizationStatus();
        loadMaintenanceStatus();

        // 定时刷新
        setInterval(() => {
            loadHealthStatus();
            loadSystemMetrics();
            loadOptimizationStatus();
            loadMaintenanceStatus();
        }, 30000); // 每30秒刷新一次
    </script>
</body>
</html>
    '''

    # 写入首页模板
    with open(os.path.join(templates_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)

    logger.info("HTML模板创建成功")

if __name__ == '__main__':
    # 创建HTML模板
    create_templates()

    # 启动Web服务器
    port = 8888
    host = '0.0.0.0'

    logger.info(f"Web服务器启动在 http://{host}:{port}")
    logger.info(f"访问地址: http://localhost:{port}")

    app.run(host=host, port=port, debug=config.DEBUG)
