# -*- coding: utf-8 -*-
import os
import glob
from animation_fixer import AnimationFixerAI

class AIEnsemble:
    def __init__(self):
        self.ais = {}
        self.feature_to_ai_map = {}
        self.ai_mapping = {}
        self.init_methods = {}

        # 初始化AI集成系统
        self._init_ai_system()

    def _init_ai_system(self):
        """初始化AI系统"""
        # 注册AI组件
        self._register_ais()

        # 初始化AI实例
        self._init_ai_instances()

    def _register_ais(self):
        """注册AI组件"""
        # 注册AnimationFixerAI
        self.init_methods['animation_fixer'] = self._init_animation_fixer_ai
        self.feature_to_ai_map['animation_fix'] = 'animation_fixer'
        self.ai_mapping.update({
            "fix_animations": "animation_fixer",
            "analyze_animations": "animation_fixer",
            "generate_animation_report": "animation_fixer"
        })

    def _init_ai_instances(self):
        """初始化AI实例"""
        # 初始化动画修复AI
        self._init_animation_fixer_ai()

    def _init_animation_fixer_ai(self):
        """初始化动画修复AI"""
        self.ais['animation_fixer'] = AnimationFixerAI()

    def detect_project_features(self):
        """检测项目特性"""
        features = []

        # 检测动画修复特性
        if os.path.exists('templates'):
            features.append('animation_fix')

        return features

    def adapt_to_project_changes(self):
        """根据项目变化调整AI配置"""
        features = self.detect_project_features()

        # 根据检测到的特性初始化相应的AI
        for feature in features:
            if feature in self.feature_to_ai_map:
                ai_type = self.feature_to_ai_map[feature]
                if ai_type in self.init_methods and ai_type not in self.ais:
                    self.init_methods[ai_type]()

    def optimize_ai_config(self):
        """优化AI配置"""
        # 为动画修复AI优化配置
        if 'animation_fixer' in self.ais:
            animation_ai = self.ais['animation_fixer']
            # 可以在这里添加优化逻辑

    def execute_ai_task(self, task_type, **kwargs):
        """执行AI任务"""
        if task_type not in self.ai_mapping:
            return {"error": f"未知任务类型: {task_type}"}

        ai_type = self.ai_mapping[task_type]
        if ai_type not in self.ais:
            return {"error": f"AI {ai_type} 未初始化"}

        ai = self.ais[ai_type]

        try:
            if task_type == "fix_animations":
                template_files = kwargs.get('template_files')
                animation_type = kwargs.get('animation_type')
                return ai.analyze_and_fix_animations(template_files, animation_type)
            elif task_type == "analyze_animations":
                animation_type = kwargs.get('animation_type')
            elif task_type == "generate_animation_report":
                return {"message": "动画报告生成功能待实现"}
            else:
                return {"error": f"未实现的任务类型: {task_type}"}
        except Exception as e:
            return {"error": str(e)}

    def get_ai_status(self):
        """获取AI状态"""
        status = {}
        for ai_name, ai_instance in self.ais.items():
            status[ai_name] = {
                "name": ai_instance.name,
                "description": ai_instance.description
            }
        return status

# 全局AI集成实例
global_ai_ensemble = None

def get_ai_ensemble():
    """获取全局AI集成实例"""
    global global_ai_ensemble
    if global_ai_ensemble is None:
        global_ai_ensemble = AIEnsemble()
    return global_ai_ensemble
