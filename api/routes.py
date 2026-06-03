# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API routes module - v2.1.0 Enhanced
"""

from flask import Blueprint, jsonify, request
from typing import Dict, Any
from core import logger, db, system, ai_service, config, get_version
import json
import sys

api_bp = Blueprint('api', __name__)
API_VERSION = "2.1.0"

# --- API Version and Root ---
@api_bp.route('/', methods=['GET'])
def api_root():
    """API root endpoint"""
    return jsonify({
        "version": API_VERSION,
        "core_version": get_version(),
        "endpoints": {
            "health": "/api/health",
            "system": "/api/system/info",
            "performance": "/api/system/performance",
            "processes": "/api/system/processes",
            "config": "/api/config",
            "ai": "/api/ai",
            "database": "/api/database"
        }
    })

@api_bp.route('/version', methods=['GET'])
def api_version():
    """Get API version"""
    return jsonify({
        "api_version": API_VERSION,
        "core_version": get_version(),
        "features": {
            "multi_provider_ai": True,
            "ai_caching": True,
            "streaming": True,
            "performance_monitoring": True,
            "enhanced_config": True,
            "code_analysis": True
        }
    })

# --- Health and System Monitoring ---
@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    health = system.get_health_report()
    return jsonify(health)

@api_bp.route('/system/info', methods=['GET'])
def get_system_info():
    """Get system information"""
    info = system.get_system_info()
    return jsonify(info)

@api_bp.route('/system/health', methods=['GET'])
def get_health():
    """Get health report"""
    report = system.get_health_report()
    return jsonify(report)

@api_bp.route('/system/performance', methods=['GET'])
def get_performance():
    """Get performance report"""
    report = system.get_performance_report()
    return jsonify(report)

@api_bp.route('/system/network', methods=['GET'])
def get_network_info():
    """Get network interfaces information"""
    try:
        network = system.get_network_interfaces()
        return jsonify({"interfaces": network})
    except Exception as e:
        logger.error(f"Network info error: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/system/disks', methods=['GET'])
def get_disk_info():
    """Get disk partitions information"""
    try:
        disks = system.get_disk_partitions()
        return jsonify({"partitions": disks})
    except Exception as e:
        logger.error(f"Disk info error: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/system/processes', methods=['GET'])
def get_processes():
    """Get top processes by CPU"""
    try:
        limit = int(request.args.get('limit', 10))
        processes = system.get_all_processes(limit=limit)
        return jsonify({"processes": processes, "count": len(processes)})
    except Exception as e:
        logger.error(f"Processes error: {e}")
        return jsonify({"error": str(e)}), 500

# --- Configuration ---
@api_bp.route('/config', methods=['GET'])
def get_config():
    """Get configuration"""
    return jsonify(config.get_all())

@api_bp.route('/config/<key>', methods=['GET'])
def get_config_key(key: str):
    """Get specific config value"""
    value = config.get(key)
    if value is None:
        return jsonify({"error": "Config key not found"}), 404
    return jsonify({key: value})

@api_bp.route('/config/<key>', methods=['PUT'])
def set_config_key(key: str):
    """Set specific config value"""
    data = request.get_json()
    if 'value' not in data:
        return jsonify({"error": "Missing 'value' in request"}), 400
    
    config.set(key, data['value'])
    config.save()
    return jsonify({"message": "Config updated successfully", key: data['value']})

@api_bp.route('/config/reload', methods=['POST'])
def reload_config():
    """Reload configuration from file"""
    try:
        config.reload()
        return jsonify({"message": "Config reloaded", "config": config.get_all()})
    except Exception as e:
        logger.error(f"Config reload error: {e}")
        return jsonify({"error": str(e)}), 500

# --- AI Service ---
@api_bp.route('/ai', methods=['GET'])
def ai_status():
    """Get AI service status"""
    return jsonify(ai_service.get_status())

@api_bp.route('/ai/generate', methods=['POST'])
def ai_generate():
    """Generate text using AI"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        model = data.get('model')
        provider = data.get('provider')
        use_cache = data.get('use_cache', True)
        
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        
        result = ai_service.generate(prompt, model=model, provider=provider, use_cache=use_cache)
        return jsonify({"result": result})
    
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/ai/chat', methods=['POST'])
def ai_chat():
    """Chat with AI using conversation history"""
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        model = data.get('model')
        provider = data.get('provider')
        
        if not messages:
            return jsonify({"error": "Messages are required"}), 400
        
        result = ai_service.chat(messages, model=model, provider=provider)
        return jsonify({"result": result})
    
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/ai/analyze', methods=['POST'])
def ai_analyze():
    """Analyze code using AI"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        analysis_type = data.get('type', 'general')
        
        if not code:
            return jsonify({"error": "Code is required"}), 400
        
        result = ai_service.analyze_code(code, analysis_type=analysis_type)
        return jsonify({"analysis": result})
    
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/ai/summarize', methods=['POST'])
def ai_summarize():
    """Summarize text using AI"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        max_length = data.get('max_length', 200)
        style = data.get('style', 'concise')
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        result = ai_service.summarize_text(text, max_length=max_length, style=style)
        return jsonify({"summary": result})
    
    except Exception as e:
        logger.error(f"AI summarization error: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/ai/translate', methods=['POST'])
def ai_translate():
    """Translate text using AI"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        target_lang = data.get('target', 'English')
        source_lang = data.get('source')
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        result = ai_service.translate_text(text, target_lang, source_lang)
        return jsonify({"translation": result})
    
    except Exception as e:
        logger.error(f"AI translation error: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/ai/cache/clear', methods=['POST'])
def clear_ai_cache():
    """Clear AI response cache"""
    try:
        ai_service.clear_cache()
        return jsonify({"message": "AI cache cleared"})
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/ai/providers', methods=['GET'])
def get_ai_providers():
    """Get available AI providers"""
    providers = ai_service.get_available_providers()
    return jsonify({"providers": providers})

@api_bp.route('/ai/models', methods=['GET'])
def get_ai_models():
    """Get available AI models"""
    provider = request.args.get('provider')
    models = ai_service.get_available_models(provider=provider)
    return jsonify({"models": models})

# --- Database ---
@api_bp.route('/database/backup', methods=['POST'])
def backup_database():
    """Create database backup"""
    try:
        backup_file = db.backup()
        if backup_file:
            return jsonify({"message": "Backup created", "file": backup_file})
        return jsonify({"error": "Backup failed"}), 500
    except Exception as e:
        logger.error(f"Backup error: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/database/restore', methods=['POST'])
def restore_database():
    """Restore database from backup"""
    try:
        data = request.get_json()
        backup_file = data.get('file', '')
        
        if not backup_file:
            return jsonify({"error": "Backup file path is required"}), 400
        
        success = db.restore(backup_file)
        if success:
            return jsonify({"message": "Restore successful"})
        return jsonify({"error": "Restore failed"}), 500
    except Exception as e:
        logger.error(f"Restore error: {e}")
        return jsonify({"error": str(e)}), 500

# --- System Commands ---
@api_bp.route('/command', methods=['POST'])
def run_command():
    """Run shell command"""
    try:
        data = request.get_json()
        command = data.get('command', '')
        timeout = data.get('timeout', 30)
        
        if not command:
            return jsonify({"error": "Command is required"}), 400
        
        result = system.run_command(command, timeout=timeout)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Command error: {e}")
        return jsonify({"error": str(e)}), 500

# --- Error Handlers ---
@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Not found", "api_version": API_VERSION}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error", "api_version": API_VERSION}), 500
