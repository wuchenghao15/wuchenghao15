#!/usr/bin/env python3
"""
独立的AI员工集群服务器
负责处理任务发布和批处理
"""

import os
import sys
import time
import threading
import uuid
import logging
from flask import Flask, request, jsonify

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 配置模板目录
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# 任务管理器类
class SimpleTaskManager:
    """
    简单的任务管理器，负责任务的发布和执行
    """
    def __init__(self):
        self.tasks = {}
        self.task_queue = []
        self.processing_tasks = {}
        self.completed_tasks = []
        self.running = False
        self.max_concurrent_tasks = 5
        
        # 锁
        self.tasks_lock = threading.Lock()
        self.queue_lock = threading.Lock()
        self.processing_lock = threading.Lock()
        
        logger.info("[任务管理] 初始化任务管理器")
    
    def start(self):
        """
        启动任务管理器
        """
        if self.running:
            return
        
        self.running = True
        threading.Thread(target=self._process_tasks_loop, daemon=True).start()
        logger.info("[任务管理] 任务管理器已启动")
    
    def _process_tasks_loop(self):
        """
        任务处理循环
        """
        while self.running:
            try:
                self._process_next_task()
            except Exception as e:
                logger.error(f"[任务管理] 任务处理失败: {str(e)}")
            time.sleep(1)
    
    def _process_next_task(self):
        """
        处理下一个任务
        """
        # 检查并发任务数
        with self.processing_lock:
            if len(self.processing_tasks) >= self.max_concurrent_tasks:
                return
        
        # 获取下一个任务
        task = None
        with self.queue_lock:
            if self.task_queue:
                task = self.task_queue.pop(0)
        
        if not task:
            return
        
        task_id = task['task_id']
        
        # 更新任务状态
        with self.tasks_lock:
            self.tasks[task_id]['status'] = 'processing'
            self.tasks[task_id]['started_at'] = time.time()
        
        with self.processing_lock:
            self.processing_tasks[task_id] = task
        
        # 异步执行任务
        threading.Thread(target=self._execute_task, args=(task,), daemon=True).start()
    
    def _execute_task(self, task):
        """
        执行任务
        """
        task_id = task['task_id']
        task_type = task['task_type']
        task_data = task['task_data']
        
        try:
            # 模拟任务执行
            time.sleep(3)  # 模拟处理时间
            
            result = {
                'success': True,
                'result': f"任务执行完成，类型: {task_type}, 数据: {task_data}",
                'processed_by': 'ai-cluster-server'
            }
            
            # 更新任务状态
            with self.tasks_lock:
                self.tasks[task_id]['status'] = 'completed'
                self.tasks[task_id]['completed_at'] = time.time()
                self.tasks[task_id]['result'] = result
            
            with self.processing_lock:
                if task_id in self.processing_tasks:
                    del self.processing_tasks[task_id]
            
            logger.info(f"[任务管理] 任务处理完成，任务ID: {task_id}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[任务管理] 任务处理失败，任务ID: {task_id}, 错误: {error_msg}")
            
            with self.tasks_lock:
                self.tasks[task_id]['status'] = 'failed'
                self.tasks[task_id]['completed_at'] = time.time()
                self.tasks[task_id]['error'] = error_msg
            
            with self.processing_lock:
                if task_id in self.processing_tasks:
                    del self.processing_tasks[task_id]
    
    def publish_task(self, task_type, task_data, priority=0):
        """
        发布任务
        """
        task_id = str(uuid.uuid4())
        
        task = {
            'task_id': task_id,
            'task_type': task_type,
            'task_data': task_data,
            'priority': priority,
            'status': 'pending',
            'created_at': time.time(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None
        }
        
        with self.tasks_lock:
            self.tasks[task_id] = task
        
        with self.queue_lock:
            self.task_queue.append(task)
        
        return task_id
    
    def publish_batch_tasks(self, tasks):
        """
        发布批量任务
        """
        task_ids = []
        for task_info in tasks:
            task_type = task_info.get('task_type', 'default')
            task_data = task_info.get('task_data', {})
            priority = task_info.get('priority', 0)
            task_id = self.publish_task(task_type, task_data, priority)
            task_ids.append(task_id)
        
        return task_ids
    
    def get_task(self, task_id):
        """
        获取任务
        """
        with self.tasks_lock:
            return self.tasks.get(task_id)
    
    def get_all_tasks(self):
        """
        获取所有任务
        """
        with self.tasks_lock:
            return self.tasks.copy()

# 创建全局任务管理器实例
task_manager = SimpleTaskManager()

# 健康检查路由
@app.route('/health')
def health():
    return "OK", 200

# 根路由
@app.route('/')
def root():
    from flask import render_template
    return render_template('index.html', versions={'system_version': '1.0.0'})

# AI集群API路由
@app.route('/api/ai-cluster/health', methods=['GET'])
def ai_cluster_health():
    return jsonify({'success': True, 'message': 'AI Cluster API is healthy'}), 200

@app.route('/api/ai-cluster/status', methods=['GET'])
def ai_cluster_status():
    return jsonify({
        'success': True,
        'task_status': {
            'total_tasks': len(task_manager.get_all_tasks()),
            'processing_tasks': len(task_manager.processing_tasks)
        }
    }), 200

@app.route('/api/ai-cluster/tasks', methods=['POST'])
def publish_task():
    try:
        data = request.get_json()
        task_type = data.get('task_type', 'default')
        task_data = data.get('task_data', {})
        priority = data.get('priority', 0)
        
        task_id = task_manager.publish_task(task_type, task_data, priority)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '任务发布成功'
        }), 200
    except Exception as e:
        logger.error(f"[AI集群API] 发布任务失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai-cluster/tasks/batch', methods=['POST'])
def publish_batch_tasks():
    try:
        data = request.get_json()
        tasks = data.get('tasks', [])
        
        task_ids = task_manager.publish_batch_tasks(tasks)
        
        return jsonify({
            'success': True,
            'task_ids': task_ids,
            'total_tasks': len(task_ids),
            'message': '批量任务发布成功'
        }), 200
    except Exception as e:
        logger.error(f"[AI集群API] 发布批量任务失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai-cluster/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    return jsonify({'success': True, 'task': task}), 200

@app.route('/api/ai-cluster/tasks', methods=['GET'])
def get_all_tasks():
    tasks = task_manager.get_all_tasks()
    return jsonify({'success': True, 'tasks': tasks}), 200

if __name__ == '__main__':
    # 启动任务管理器
    task_manager.start()
    
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='AI Cluster Server')
    parser.add_argument('--port', type=int, default=8888, help='Server port')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Server host')
    args = parser.parse_args()
    
    logger.info(f"Starting AI Cluster Server on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False, use_reloader=False)
