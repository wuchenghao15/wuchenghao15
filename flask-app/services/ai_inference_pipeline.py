#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI推理流水线
提供预处理→推理→后处理的完整AI推理管道
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable

logger = print


class PipelineStage:
    """流水线阶段"""

    def __init__(self, stage_id: str, name: str, stage_type: str,
                 handler: Callable = None, order: int = 0,
                 is_enabled: bool = True, config: Dict[str, Any] = None):
        self.stage_id = stage_id
        self.name = name
        self.stage_type = stage_type  # preprocess, inference, postprocess
        self.handler = handler
        self.order = order
        self.is_enabled = is_enabled
        self.config = config or {}

        self.total_executions = 0
        self.total_errors = 0
        self.avg_duration = 0.0

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段"""
        if not self.is_enabled:
            return data

        start_time = time.time()

        try:
            if self.handler:
                result = self.handler(data, self.config)
            else:
                result = self._default_handler(data)

            duration = time.time() - start_time
            self.total_executions += 1
            self.avg_duration = (
                (self.avg_duration * (self.total_executions - 1) + duration) /
                self.total_executions
            )

            return result if result is not None else data

        except Exception as e:
            self.total_errors += 1
            logger(f"[推理流水线] 阶段 {self.name} 执行失败: {e}")
            data['_errors'] = data.get('_errors', [])
            data['_errors'].append({'stage': self.stage_id, 'error': str(e)})
            return data

    def _default_handler(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """默认处理器"""
        return data

    def to_dict(self) -> Dict[str, Any]:
        return {
            'stage_id': self.stage_id,
            'name': self.name,
            'stage_type': self.stage_type,
            'order': self.order,
            'is_enabled': self.is_enabled,
            'config': self.config,
            'total_executions': self.total_executions,
            'total_errors': self.total_errors,
            'avg_duration': round(self.avg_duration, 4)
        }


class PipelineExecution:
    """流水线执行记录"""

    def __init__(self, execution_id: str, pipeline_id: str,
                 input_data: Dict[str, Any]):
        self.execution_id = execution_id
        self.pipeline_id = pipeline_id
        self.input_data = input_data
        self.output_data: Dict[str, Any] = {}
        self.stage_results: List[Dict[str, Any]] = []
        self.total_duration = 0.0
        self.success = True
        self.error = None
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'execution_id': self.execution_id,
            'pipeline_id': self.pipeline_id,
            'total_duration': round(self.total_duration, 4),
            'success': self.success,
            'error': self.error,
            'stage_count': len(self.stage_results),
            'stage_results': self.stage_results,
            'created_at': self.created_at
        }


class InferencePipeline:
    """推理流水线"""

    def __init__(self, pipeline_id: str, name: str,
                 description: str = '', model_id: str = ''):
        self.pipeline_id = pipeline_id
        self.name = name
        self.description = description
        self.model_id = model_id
        self.stages: Dict[str, PipelineStage] = {}
        self.is_active = True
        self.created_at = datetime.now().isoformat()
        self.total_executions = 0
        self.total_errors = 0

    def add_stage(self, stage: PipelineStage):
        """添加阶段"""
        self.stages[stage.stage_id] = stage

    def remove_stage(self, stage_id: str) -> bool:
        return self.stages.pop(stage_id, None) is not None

    def get_ordered_stages(self) -> List[PipelineStage]:
        """获取按顺序排列的阶段"""
        return sorted(self.stages.values(), key=lambda s: (s.stage_type, s.order))

    def execute(self, input_data: Dict[str, Any]) -> PipelineExecution:
        """执行流水线"""
        import uuid
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"

        execution = PipelineExecution(execution_id, self.pipeline_id, input_data)
        start_time = time.time()

        data = dict(input_data)
        data['_pipeline_id'] = self.pipeline_id
        data['_execution_id'] = execution_id

        try:
            ordered_stages = self.get_ordered_stages()

            for stage in ordered_stages:
                stage_start = time.time()
                data = stage.execute(data)
                stage_duration = time.time() - stage_start

                execution.stage_results.append({
                    'stage_id': stage.stage_id,
                    'stage_name': stage.name,
                    'stage_type': stage.stage_type,
                    'duration': round(stage_duration, 4),
                    'success': '_errors' not in data or len(data.get('_errors', [])) == 0
                })

            execution.output_data = data
            self.total_executions += 1

        except Exception as e:
            execution.success = False
            execution.error = str(e)
            self.total_errors += 1
            logger(f"[推理流水线] 执行失败 {self.name}: {e}")

        execution.total_duration = time.time() - start_time

        return execution

    def to_dict(self) -> Dict[str, Any]:
        return {
            'pipeline_id': self.pipeline_id,
            'name': self.name,
            'description': self.description,
            'model_id': self.model_id,
            'is_active': self.is_active,
            'stage_count': len(self.stages),
            'stages': [s.to_dict() for s in self.get_ordered_stages()],
            'total_executions': self.total_executions,
            'total_errors': self.total_errors,
            'created_at': self.created_at
        }


# 默认预处理函数
def default_preprocess(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """默认预处理"""
    text = data.get('input', '')

    # 清理文本
    text = text.strip()

    # 截断
    max_length = config.get('max_length', 4096)
    if len(text) > max_length:
        text = text[:max_length]

    data['processed_input'] = text
    data['input_length'] = len(text)
    return data


# 默认推理函数
def default_inference(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """默认推理"""
    prompt = data.get('processed_input', data.get('input', ''))

    # 模拟推理
    response = f"推理结果: {prompt[:100]}"

    data['raw_output'] = response
    data['output_tokens'] = len(response) // 4
    return data


# 默认后处理函数
def default_postprocess(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """默认后处理"""
    output = data.get('raw_output', '')

    # 格式化输出
    data['result'] = {
        'response': output,
        'input_tokens': data.get('input_length', 0) // 4,
        'output_tokens': data.get('output_tokens', 0),
        'metadata': {
            'pipeline_id': data.get('_pipeline_id', ''),
            'execution_id': data.get('_execution_id', '')
        }
    }

    return data


class AIInferencePipelineService:
    """AI推理流水线服务"""

    def __init__(self):
        self.pipelines: Dict[str, InferencePipeline] = {}
        self.is_running = False
        self.lock = threading.Lock()
        self.recent_executions: List[PipelineExecution] = []
        self.max_recent = 100

        self._init_database()
        self._register_default_pipelines()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_pipelines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pipeline_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    model_id TEXT,
                    is_active INTEGER DEFAULT 1,
                    stage_count INTEGER DEFAULT 0,
                    total_executions INTEGER DEFAULT 0,
                    total_errors INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_pipeline_stages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stage_id TEXT NOT NULL UNIQUE,
                    pipeline_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    stage_type TEXT NOT NULL,
                    stage_order INTEGER DEFAULT 0,
                    is_enabled INTEGER DEFAULT 1,
                    config TEXT,
                    total_executions INTEGER DEFAULT 0,
                    total_errors INTEGER DEFAULT 0,
                    avg_duration REAL DEFAULT 0
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_pipeline_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL UNIQUE,
                    pipeline_id TEXT NOT NULL,
                    total_duration REAL DEFAULT 0,
                    success INTEGER DEFAULT 1,
                    error TEXT,
                    stage_count INTEGER DEFAULT 0,
                    stage_results TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ai_pipelines_id ON ai_pipelines(pipeline_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ai_executions_pipeline ON ai_pipeline_executions(pipeline_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[推理流水线] 初始化数据库失败: {e}")

    def _register_default_pipelines(self):
        """注册默认流水线"""
        # 标准文本推理流水线
        pipeline1 = InferencePipeline('pipe_text', '文本推理流水线',
                                       '标准文本推理管道', 'model_gpt35')

        pipeline1.add_stage(PipelineStage(
            'stage_preprocess_1', '文本预处理', 'preprocess',
            handler=default_preprocess, order=1,
            config={'max_length': 4096}
        ))
        pipeline1.add_stage(PipelineStage(
            'stage_inference_1', '模型推理', 'inference',
            handler=default_inference, order=1,
            config={'temperature': 0.7}
        ))
        pipeline1.add_stage(PipelineStage(
            'stage_postprocess_1', '结果后处理', 'postprocess',
            handler=default_postprocess, order=1
        ))

        self.pipelines['pipe_text'] = pipeline1
        self._save_pipeline_to_db(pipeline1)

        # 快速推理流水线
        pipeline2 = InferencePipeline('pipe_fast', '快速推理流水线',
                                       '低延迟推理管道', 'model_local')

        pipeline2.add_stage(PipelineStage(
            'stage_preprocess_2', '快速预处理', 'preprocess',
            handler=default_preprocess, order=1,
            config={'max_length': 1024}
        ))
        pipeline2.add_stage(PipelineStage(
            'stage_inference_2', '快速推理', 'inference',
            handler=default_inference, order=1,
            config={'temperature': 0.5}
        ))
        pipeline2.add_stage(PipelineStage(
            'stage_postprocess_2', '快速后处理', 'postprocess',
            handler=default_postprocess, order=1
        ))

        self.pipelines['pipe_fast'] = pipeline2
        self._save_pipeline_to_db(pipeline2)

        # 知识增强推理流水线
        pipeline3 = InferencePipeline('pipe_rag', '知识增强推理',
                                       'RAG知识增强推理管道', 'model_gpt4')

        pipeline3.add_stage(PipelineStage(
            'stage_rag_preprocess', 'RAG预处理', 'preprocess',
            order=1, config={'max_length': 4096, 'enable_rag': True}
        ))
        pipeline3.add_stage(PipelineStage(
            'stage_rag_retrieve', '知识检索', 'preprocess',
            order=2, config={'top_k': 3}
        ))
        pipeline3.add_stage(PipelineStage(
            'stage_rag_inference', '增强推理', 'inference',
            handler=default_inference, order=1,
            config={'temperature': 0.3}
        ))
        pipeline3.add_stage(PipelineStage(
            'stage_rag_postprocess', '结果整合', 'postprocess',
            handler=default_postprocess, order=1
        ))

        self.pipelines['pipe_rag'] = pipeline3
        self._save_pipeline_to_db(pipeline3)

    def _save_pipeline_to_db(self, pipeline: InferencePipeline):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_pipelines
                (pipeline_id, name, description, model_id, is_active,
                 stage_count, total_executions, total_errors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pipeline.pipeline_id, pipeline.name, pipeline.description,
                pipeline.model_id, 1 if pipeline.is_active else 0,
                len(pipeline.stages), pipeline.total_executions,
                pipeline.total_errors
            ))

            for stage in pipeline.stages.values():
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_pipeline_stages
                    (stage_id, pipeline_id, name, stage_type, stage_order,
                     is_enabled, config, total_executions, total_errors, avg_duration)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stage.stage_id, pipeline.pipeline_id, stage.name,
                    stage.stage_type, stage.order,
                    1 if stage.is_enabled else 0,
                    json.dumps(stage.config),
                    stage.total_executions, stage.total_errors,
                    stage.avg_duration
                ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[推理流水线] 保存流水线失败: {e}")

    def create_pipeline(self, name: str, description: str = '',
                        model_id: str = '') -> str:
        """创建流水线"""
        import uuid
        pipeline_id = f"pipe_{uuid.uuid4().hex[:8]}"

        pipeline = InferencePipeline(pipeline_id, name, description, model_id)

        with self.lock:
            self.pipelines[pipeline_id] = pipeline

        self._save_pipeline_to_db(pipeline)
        logger(f"[推理流水线] 创建流水线: {name}")

        return pipeline_id

    def add_stage(self, pipeline_id: str, name: str, stage_type: str,
                  handler: Callable = None, order: int = 0,
                  config: Dict[str, Any] = None) -> Optional[str]:
        """添加阶段"""
        import uuid

        with self.lock:
            pipeline = self.pipelines.get(pipeline_id)
            if not pipeline:
                return None

            stage_id = f"stage_{uuid.uuid4().hex[:8]}"

            stage = PipelineStage(
                stage_id=stage_id, name=name, stage_type=stage_type,
                handler=handler, order=order, config=config
            )

            pipeline.add_stage(stage)

        self._save_pipeline_to_db(pipeline)
        return stage_id

    def execute(self, pipeline_id: str,
                input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """执行流水线"""
        with self.lock:
            pipeline = self.pipelines.get(pipeline_id)
            if not pipeline:
                return None

        execution = pipeline.execute(input_data)

        # 保存执行记录
        with self.lock:
            self.recent_executions.append(execution)
            if len(self.recent_executions) > self.max_recent:
                self.recent_executions.pop(0)

        self._save_execution_to_db(execution)
        self._save_pipeline_to_db(pipeline)

        return execution.to_dict()

    def _save_execution_to_db(self, execution: PipelineExecution):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_pipeline_executions
                (execution_id, pipeline_id, total_duration, success,
                 error, stage_count, stage_results)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                execution.execution_id, execution.pipeline_id,
                execution.total_duration, 1 if execution.success else 0,
                execution.error, len(execution.stage_results),
                json.dumps(execution.stage_results)
            ))

            conn.commit()
            conn.close()
        except:
            pass

    def get_pipeline(self, pipeline_id: str) -> Optional[InferencePipeline]:
        return self.pipelines.get(pipeline_id)

    def get_pipelines(self, active_only: bool = False) -> List[Dict[str, Any]]:
        with self.lock:
            pipes = list(self.pipelines.values())

            if active_only:
                pipes = [p for p in pipes if p.is_active]

            return [p.to_dict() for p in pipes]

    def get_recent_executions(self, pipeline_id: str = None,
                              limit: int = 20) -> List[Dict[str, Any]]:
        with self.lock:
            executions = list(self.recent_executions)

            if pipeline_id:
                executions = [e for e in executions if e.pipeline_id == pipeline_id]

            return [e.to_dict() for e in executions[-limit:]]

    def get_execution_history(self, pipeline_id: str = None,
                              limit: int = 50) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            if pipeline_id:
                cursor.execute('''
                    SELECT * FROM ai_pipeline_executions
                    WHERE pipeline_id = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (pipeline_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM ai_pipeline_executions
                    ORDER BY created_at DESC LIMIT ?
                ''', (limit,))

            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return logs
        except:
            return []

    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        with self.lock:
            total_exec = sum(p.total_executions for p in self.pipelines.values())
            total_errors = sum(p.total_errors for p in self.pipelines.values())

            stage_stats = []
            for pipeline in self.pipelines.values():
                for stage in pipeline.stages.values():
                    stage_stats.append({
                        'pipeline': pipeline.name,
                        'stage': stage.name,
                        'type': stage.stage_type,
                        'executions': stage.total_executions,
                        'errors': stage.total_errors,
                        'avg_duration': round(stage.avg_duration, 4)
                    })

            return {
                'total_pipelines': len(self.pipelines),
                'active_pipelines': sum(1 for p in self.pipelines.values() if p.is_active),
                'total_executions': total_exec,
                'total_errors': total_errors,
                'success_rate': round((total_exec - total_errors) / max(1, total_exec) * 100, 2),
                'stage_stats': stage_stats
            }

    def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_pipelines': len(self.pipelines),
            'recent_executions': len(self.recent_executions)
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[推理流水线] 服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[推理流水线] 服务已停止")


ai_inference_pipeline = AIInferencePipelineService()
