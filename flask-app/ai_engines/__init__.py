import sys as _sys
import importlib as _importlib
import importlib.machinery as _machinery
import importlib.util as _util
import types as _types

# 集成Ollama相关AI引擎，依赖: ollama>=0.2.0
_BASENAME_TO_PATH = {
    'ai_activity_manager': 'ai_engines.management.ai_activity_manager',
    'ai_api_database_manager': 'ai_engines.management.ai_api_database_manager',
    'ai_archive_manager': 'ai_engines.management.ai_archive_manager',
    'ai_cluster_manager': 'ai_engines.management.ai_cluster_manager',
    'ai_collection_manager': 'ai_engines.management.ai_collection_manager',
    'ai_community_manager': 'ai_engines.management.ai_community_manager',
    'ai_config_manager': 'ai_engines.management.ai_config_manager',
    'ai_distributed_db_manager': 'ai_engines.management.ai_distributed_db_manager',
    'ai_education_manager': 'ai_engines.management.ai_education_manager',
    'ai_employee_api': 'ai_engines.management.ai_employee_api',
    'ai_employee_auto_generator': 'ai_engines.management.ai_employee_auto_generator',
    'ai_employee_distributed_upgrade': 'ai_engines.management.ai_employee_distributed_upgrade',
    'ai_employee_manager': 'ai_engines.management.ai_employee_manager',
    'ai_employee_sync': 'ai_engines.management.ai_employee_sync',
    'ai_employee_system': 'ai_engines.management.ai_employee_system',
    'ai_employees': 'ai_engines.management.ai_employees',
    'ai_instance_manager': 'ai_engines.management.ai_instance_manager',
    'ai_master_slave_manager': 'ai_engines.management.ai_master_slave_manager',
    'ai_routes_database_manager': 'ai_engines.management.ai_routes_database_manager',
    'ai_code_review_agent': 'ai_engines.security.ai_code_review_agent',
    'ai_security_auditor': 'ai_engines.security.ai_security_auditor',
    'ai_brain': 'ai_engines.brain.ai_brain',
    'ai_brain_api': 'ai_engines.brain.ai_brain_api',
    'ai_brain_enhancer': 'ai_engines.brain.ai_brain_enhancer',
    'ai_brain_library': 'ai_engines.brain.ai_brain_library',
    'ai_brain_map': 'ai_engines.brain.ai_brain_map',
    'ai_brain_middleware': 'ai_engines.brain.ai_brain_middleware',
    'ai_brain_search_enhancer': 'ai_engines.brain.ai_brain_search_enhancer',
    'ai_brain_service': 'ai_engines.brain.ai_brain_service',
    'brain_based_learning': 'ai_engines.brain.brain_based_learning',
    'brain_learning_api': 'ai_engines.brain.brain_learning_api',
    'brain_updater': 'ai_engines.brain.brain_updater',
    'ai_learning': 'ai_engines.learning.ai_learning',
    'ai_learning_api': 'ai_engines.learning.ai_learning_api',
    'ai_learning_recommender': 'ai_engines.learning.ai_learning_recommender',
    'ai_learning_system': 'ai_engines.learning.ai_learning_system',
    'learning': 'ai_engines.learning.learning',
    'learning_analytics_engine': 'ai_engines.learning.learning_analytics_engine',
    'learning_diagnosis_engine': 'ai_engines.learning.learning_diagnosis_engine',
    'learning_prediction_engine': 'ai_engines.learning.learning_prediction_engine',
    'learning_report_engine': 'ai_engines.learning.learning_report_engine',
    'learning_visualization_engine': 'ai_engines.learning.learning_visualization_engine',
    'ai_anomaly_detector': 'ai_engines.monitoring.ai_anomaly_detector',
    'ai_monitor_employee': 'ai_engines.monitoring.ai_monitor_employee',
    'ai_monitor_server': 'ai_engines.monitoring.ai_monitor_server',
    'ai_internal_instruction_processor': 'ai_engines.core.ai_internal_instruction_processor',
    'ai_internal_command_executor': 'ai_engines.core.ai_internal_command_executor',
    'ai_instruction_parser': 'ai_engines.core.ai_instruction_parser',
    'ai_instruction_queue_manager': 'ai_engines.core.ai_instruction_queue_manager',
    'ai_internal_instruction_scheduler': 'ai_engines.core.ai_internal_instruction_scheduler',
    'ollama_engine': 'ai_engines.ollama.ollama_engine',
    'ollama_client': 'ai_engines.ollama.ollama_client',
    'ollama_model_manager': 'ai_engines.ollama.ollama_model_manager',
    'ollama_bridge': 'ai_engines.ollama.ollama_bridge',
    'ollama_adapter': 'ai_engines.ollama.ollama_adapter',
    'ollama_stream_handler': 'ai_engines.ollama.ollama_stream_handler',
    'new_module': 'ai_engines.new_module.new_module',  # 新增模块路径
}

__all__ = list(_BASENAME_TO_PATH.keys())


class _AiEnginesAliasFinder:
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        if not fullname.startswith('ai_engines.'):
            return None
        parts = fullname.split('.', 2)
        if len(parts) < 2:
            return None
        basename = parts[1]
        target_path = _BASENAME_TO_PATH.get(basename)
        if target_path is None:
            return None
        if fullname == target_path or (len(target_path) > len(fullname)
                                       and target_path.startswith(fullname + '.')):
            return None
        if fullname != 'ai_engines.' + basename:
            return None
        try:
            real_mod = _importlib.import_module(target_path)
        except Exception:
            return None
        _sys.modules.setdefault(fullname, real_mod)
        loader = getattr(real_mod, '__loader__', None) or _machinery.SourceFileLoader(fullname, '')
        origin = getattr(real_mod, '__file__', None)
        spec = _util.spec_from_loader(fullname, loader, origin=origin,
                                      is_package=bool(getattr(real_mod, '__path__', None)))
        return spec


already = False
for finder in _sys.meta_path:
    if finder.__class__.__name__ == '_AiEnginesAliasFinder':
        already = True
        break
if not already:
    _sys.meta_path.insert(0, _AiEnginesAliasFinder())


def __getattr__(name):
    target_path = _BASENAME_TO_PATH.get(name)
    if target_path is None:
        raise AttributeError("module ai_engines has no attribute %r" % name)
    try:
        submod = _importlib.import_module(target_path)
    except Exception as orig_exc:
        raise AttributeError(
            "ai_engines.%s 解析到 %s 但导入失败: %r" % (name, target_path, orig_exc)
        ) from orig_exc
    globals()[name] = submod
    return submod


def __dir__():
    return sorted(set(list(globals().keys()) + __all__))
