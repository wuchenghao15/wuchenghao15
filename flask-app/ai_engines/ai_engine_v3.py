# 依赖说明：所有依赖均为Python标准库，无需额外安装
import os
import shutil
import time
import threading
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, Any


class AIEngineV3:
    """AI引擎 v3.0"""

    def __init__(self):
        self._router = Router()
        self._template_manager = TemplateManager()
        self._cache = Cache()
        self._monitor = EngineMonitor()
        self._conversation_history = defaultdict(deque)
        self._max_history = 10

    def organize_wav_files(self, source_dir: str, target_dir: str) -> Dict[str, Any]:
        """整理项目下所有wav文件到指定文件夹
        Args:
            source_dir: 待扫描的根目录路径
            target_dir: wav文件目标存放目录路径
        Returns:
            整理结果统计信息
        """
        source_path = Path(source_dir).resolve()
        target_path = Path(target_dir).resolve()
        # 自动创建目标目录
        target_path.mkdir(parents=True, exist_ok=True)
        
        total_count = 0
        success_count = 0
        skip_count = 0
        error_count = 0
        duplicate_files = []

        # 递归扫描所有wav文件
        for wav_file in source_path.rglob("*.wav"):
            if not wav_file.is_file():
                continue
            total_count += 1
            try:
                target_file = target_path / wav_file.name
                # 处理重名文件
                if target_file.exists():
                    stem = wav_file.stem
                    suffix = wav_file.suffix
                    counter = 1
                    while target_file.exists():
                        new_name = f"{stem}_{counter}{suffix}"
                        target_file = target_path / new_name
                        counter += 1
                    duplicate_files.append(str(wav_file))
                # 移动文件
                shutil.move(str(wav_file), str(target_file))
                success_count += 1
            except Exception as e:
                error_count += 1
                continue
        
        return {
            "success": True,
            "total_wav_found": total_count,
            "moved_success": success_count,
            "duplicate_processed": len(duplicate_files),
            "skip_count": skip_count,
            "error_count": error_count,
            "target_dir": str(target_path),
            "duplicate_file_list": duplicate_files
        }

    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成AI响应"""
        start_time = time.time()
        model = self._router.select_model(kwargs.get('task_type'), kwargs.get('model_type'))
        if not model:
            latency = time.time() - start_time
            self._monitor.record_request('error', latency)
            return {'success': False, 'error': '没有可用的AI模型', 'latency': latency}

        system_prompt = kwargs.get('system_prompt', '')
        template_name = kwargs.get('template')

        # 模拟模型响应
        if template_name:
            response = self._template_manager.render_prompt(template_name, prompt=prompt, system_prompt=system_prompt)
        else:
            response = f"{model.name} 正在处理您的请求...\n\n详细解答正在生成..."

        latency = time.time() - start_time
        result = {'content': response}

        # 检查缓存
        if self._cache.is_cached(prompt, model.type.value):
            result['cached'] = True
        else:
            self._cache.set_cache(prompt, model.type.value, result['content'])

        # 更新对话历史
        self._update_history(kwargs.get('conversation_id'), prompt, result['content'])

        # 记录监控指标
        self._monitor.record_request('success', latency, model.type.value)

        return {'success': True, **result}

    def _update_history(self, conversation_id: str, prompt: str, response: str):
        """更新对话历史"""
        self._conversation_history[conversation_id].append({
            'prompt': prompt,
            'response': response,
            'timestamp': time.time()
        })
        if len(self._conversation_history[conversation_id]) > self._max_history:
            self._conversation_history[conversation_id].popleft()

    def stream_generate(self, prompt: str, **kwargs) -> str:
        """流式生成AI响应"""
        model = self._router.select_model(kwargs.get('task_type'), kwargs.get('model_type'))
        if not model:
            yield {'success': False, 'error': '没有可用的AI模型'}
            return

        system_prompt = kwargs.get('system_prompt', '')

        # 模拟流式响应
        full_response = f"{model.name} 正在处理您的请求...\n\n"

        keywords = ['问题', '分析', '生成', '创建', '翻译', '帮助', '搜索']
        matched_keyword = next((k for k in keywords if k in prompt), None)

        responses = {
            '问题': "这是一个很好的问题!让我为您分析一下...\n\n首先，需要考虑问题的核心要点。\n其次，分析相关的背景信息。\n最后，提供可行的解决方案。",
            '分析': "正在进行数据分析...\n\n📊 数据收集完成\n🔍 正在识别关键趋势\n💡 生成洞察报告\n\n分析完成!",
            '生成': "正在生成内容...\n\n内容框架已创建\n核心内容正在生成\n格式优化中\n\n生成完成!",
            '创建': "正在创建新内容...\n\n基础框架已搭建\n核心功能已添加\n细节正在完善\n\n创建完成!",
            '翻译': "正在翻译...\n\n原文分析完成\n目标语言转换中\n译文优化\n\n翻译完成!",
            '帮助': "您好!我可以帮助您:\n\n🎯 问题解答\n📝 内容生成\n🔍 数据分析\n🤝 智能对话\n\n请问有什么可以帮您的?"
        }

        content = responses.get(matched_keyword, f"正在处理您的请求: '{prompt}'...\n\n详细解答正在生成...")

        # 模拟流式输出
        chunks = content.split('\n')
        for i, chunk in enumerate(chunks):
            time.sleep(0.1)
            yield {
                'success': True,
                'content': chunk + '\n',
                'model': model.name,
                'done': i == len(chunks) - 1,
                'chunk_index': i
            }

    def get_models(self) -> Dict[str, Dict]:
        """获取所有模型状态"""
        return self._router.get_model_status()

    def set_preferred_model(self, task_type: str, model_type: str):
        """设置任务类型的首选模型"""
        self._router.set_preferred_model(task_type, model_type)

    def add_prompt_template(self, name: str, template: Dict):
        """添加提示词模板"""
        self._template_manager.add_template(name, template)

    def get_prompt_templates(self) -> Dict[str, Dict]:
        """获取所有提示词模板"""
        return self._template_manager.list_templates()

    def render_prompt(self, template_name: str, **kwargs) -> str:
        """渲染提示词模板"""
        return self._template_manager.render_prompt(template_name, **kwargs)

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        return self._cache.get_stats()

    def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计"""
        return {
            'models': self.get_models(),
            'cache': self.get_cache_stats(),
            'monitor': self._monitor.get_stats(),
            'templates': list(self._template_manager.list_templates().keys())
        }

class Router:
    """模型路由器"""

    def __init__(self):
        self._models = {}
        self._preferred_models = {}

    def select_model(self, task_type: str, model_type: str) -> Any:
        """选择合适的模型"""
        preferred_model = self._preferred_models.get(task_type, None)
        if preferred_model and preferred_model in self._models:
            return self._models[preferred_model]

        models = [m for m in self._models.values() if m.type.value == model_type]
        if models:
            return models[0]

        return None

    def get_model_status(self) -> Dict[str, Dict]:
        """获取所有模型状态"""
        return {name: model.status for name, model in self._models.items()}

    def set_preferred_model(self, task_type: str, model_type: str):
        """设置任务类型的首选模型"""
       
