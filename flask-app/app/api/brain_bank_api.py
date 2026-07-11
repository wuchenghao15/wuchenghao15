# -*- coding: utf-8 -*-
"""
AI脑库系统API
"""

from flask import Blueprint, request, jsonify, session
import logging
from app.ai.knowledge_brain_bank import (
    knowledge_brain_bank,
    KnowledgeEntry,
    KnowledgeType,
    KnowledgeDomain,
    KnowledgeValue,
    TriggerCondition,
    TriggerConditionType,
    BrainBankStatus
)
from app.utils.logging import logger

brain_bank_api = Blueprint('brain_bank_api', __name__)


@brain_bank_api.route('/brain-bank/status', methods=['GET'])
def get_brain_status():
    """获取脑库状态"""
    try:
        stats = knowledge_brain_bank.get_brain_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"获取脑库状态失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/knowledge', methods=['GET'])
def get_knowledge_list():
    """获取知识列表"""
    try:
        query = request.args.get('q', '')
        domain = request.args.get('domain')
        knowledge_type = request.args.get('type')
        min_value = int(request.args.get('min_value', 0))
        limit = int(request.args.get('limit', 20))
        
        if query:
            entries = knowledge_brain_bank.storage.search_knowledge(
                query=query,
                knowledge_type=knowledge_type,
                domain=domain,
                min_value=min_value,
                limit=limit
            )
        elif domain:
            entries = knowledge_brain_bank.storage.get_by_domain(domain, limit)
        elif knowledge_type:
            entries = knowledge_brain_bank.storage.get_by_type(knowledge_type, limit)
        else:
            entries = knowledge_brain_bank.storage.get_top_knowledge(limit)
        
        return jsonify({
            'success': True,
            'data': {
                'knowledge': [e.to_dict() for e in entries],
                'total': len(entries)
            }
        })
    except Exception as e:
        logger.error(f"获取知识列表失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/knowledge/<knowledge_id>', methods=['GET'])
def get_knowledge_detail(knowledge_id):
    """获取知识详情"""
    try:
        entry = knowledge_brain_bank.storage.get_knowledge(knowledge_id)
        
        if not entry:
            return jsonify({
                'success': False,
                'message': '知识不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'knowledge_id': entry.knowledge_id,
                'title': entry.title,
                'content': entry.content,
                'knowledge_type': entry.knowledge_type.value,
                'domain': entry.domain.value,
                'source': entry.source,
                'value_level': entry.value.value,
                'tags': entry.tags,
                'created_at': entry.created_at.isoformat(),
                'updated_at': entry.updated_at.isoformat(),
                'access_count': entry.access_count,
                'useful_count': entry.useful_count,
                'version': entry.version,
                'trigger_count': entry.trigger_count,
                'success_rate': entry.success_rate,
                'related_knowledge': entry.related_knowledge,
                'is_validated': entry.is_validated,
                'metadata': entry.metadata
            }
        })
    except Exception as e:
        logger.error(f"获取知识详情失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/knowledge', methods=['POST'])
def add_knowledge():
    """添加知识"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        title = data.get('title')
        content = data.get('content', '')
        type_str = data.get('type', 'experience')
        domain_str = data.get('domain', 'general')
        value_str = data.get('value', 'medium')
        tags = data.get('tags', [])
        source = data.get('source', 'manual')
        
        if not title:
            return jsonify({
                'success': False,
                'message': '标题不能为空'
            }), 400
        
        type_map = {e.value: e for e in KnowledgeType}
        domain_map = {e.value: e for e in KnowledgeDomain}
        value_map = {e.name.lower(): e for e in KnowledgeValue}
        
        knowledge_type = type_map.get(type_str, KnowledgeType.EXPERIENCE)
        knowledge_domain = domain_map.get(domain_str, KnowledgeDomain.GENERAL)
        knowledge_value = value_map.get(value_str.lower(), KnowledgeValue.MEDIUM)
        
        entry = KnowledgeEntry(
            title=title,
            content=content,
            knowledge_type=knowledge_type,
            domain=knowledge_domain,
            source=source,
            value=knowledge_value,
            tags=tags
        )
        
        knowledge_id = knowledge_brain_bank.storage.add_knowledge(entry)
        
        return jsonify({
            'success': True,
            'message': '知识已添加',
            'data': {
                'knowledge_id': knowledge_id
            }
        })
    except Exception as e:
        logger.error(f"添加知识失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/knowledge/search', methods=['POST'])
def search_knowledge():
    """搜索知识"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        query = data.get('query', '')
        domain = data.get('domain')
        knowledge_type = data.get('type')
        min_value = data.get('min_value', 0)
        limit = data.get('limit', 20)
        
        entries = knowledge_brain_bank.storage.search_knowledge(
            query=query,
            knowledge_type=knowledge_type,
            domain=domain,
            min_value=min_value,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': {
                'results': [e.to_dict() for e in entries],
                'total': len(entries),
                'query': query
            }
        })
    except Exception as e:
        logger.error(f"搜索知识失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/knowledge/top', methods=['GET'])
def get_top_knowledge():
    """获取最有价值的知识"""
    try:
        limit = int(request.args.get('limit', 10))
        entries = knowledge_brain_bank.storage.get_top_knowledge(limit)
        
        return jsonify({
            'success': True,
            'data': {
                'knowledge': [e.to_dict() for e in entries],
                'total': len(entries)
            }
        })
    except Exception as e:
        logger.error(f"获取顶级知识失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/triggers', methods=['GET'])
def get_triggers():
    """获取触发条件列表"""
    try:
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 50))
        
        triggers = knowledge_brain_bank.trigger_learner.get_all_triggers(active_only, limit)
        
        return jsonify({
            'success': True,
            'data': {
                'triggers': [t.to_dict() for t in triggers],
                'total': len(triggers)
            }
        })
    except Exception as e:
        logger.error(f"获取触发条件失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/triggers', methods=['POST'])
def add_trigger():
    """添加触发条件"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        name = data.get('name')
        type_str = data.get('type', 'threshold')
        rule = data.get('rule', {})
        action = data.get('action', '')
        priority = data.get('priority', 50)
        cooldown = data.get('cooldown', 60)
        
        if not name:
            return jsonify({
                'success': False,
                'message': '名称不能为空'
            }), 400
        
        type_map = {e.value: e for e in TriggerConditionType}
        condition_type = type_map.get(type_str, TriggerConditionType.THRESHOLD)
        
        trigger = TriggerCondition(
            name=name,
            condition_type=condition_type,
            rule=rule,
            action=action
        )
        trigger.priority = priority
        trigger.cooldown = cooldown
        trigger.is_active = True
        
        trigger_id = knowledge_brain_bank.trigger_learner.add_trigger(trigger)
        
        return jsonify({
            'success': True,
            'message': '触发条件已添加',
            'data': {
                'trigger_id': trigger_id
            }
        })
    except Exception as e:
        logger.error(f"添加触发条件失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/triggers/evaluate', methods=['POST'])
def evaluate_triggers():
    """评估触发条件"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        context = data.get('context', {})
        results = knowledge_brain_bank.evaluate_and_trigger(context)
        
        return jsonify({
            'success': True,
            'data': {
                'triggered': len(results) > 0,
                'triggers': results,
                'total_triggered': len(results)
            }
        })
    except Exception as e:
        logger.error(f"评估触发条件失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/empower/decision', methods=['POST'])
def empower_decision():
    """用脑库增强决策"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        decision_context = data.get('context', {})
        result = knowledge_brain_bank.empowerment.empower_decision(decision_context)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"决策赋能失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/empower/cross-pollinate', methods=['POST'])
def cross_pollinate():
    """跨领域知识迁移"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        source_domain = data.get('source_domain')
        target_domain = data.get('target_domain')
        
        if not source_domain or not target_domain:
            return jsonify({
                'success': False,
                'message': '源领域和目标领域不能为空'
            }), 400
        
        insights = knowledge_brain_bank.empowerment.cross_pollinate(
            source_domain, target_domain
        )
        
        return jsonify({
            'success': True,
            'data': {
                'insights': insights,
                'total': len(insights)
            }
        })
    except Exception as e:
        logger.error(f"跨领域知识迁移失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/learn/from-experience', methods=['POST'])
def learn_from_experience():
    """从经验中学习"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        experience = data.get('experience', {})
        
        if not experience.get('title'):
            return jsonify({
                'success': False,
                'message': '经验标题不能为空'
            }), 400
        
        knowledge_id = knowledge_brain_bank.add_knowledge_from_experience(experience)
        
        return jsonify({
            'success': True,
            'message': '学习完成，知识已入库',
            'data': {
                'knowledge_id': knowledge_id
            }
        })
    except Exception as e:
        logger.error(f"从经验学习失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/learn/from-event', methods=['POST'])
def learn_from_event():
    """从事件中学习触发条件"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        event = data.get('event', {})
        outcome = data.get('outcome', True)
        
        knowledge_brain_bank.trigger_learner.learn_from_event(event, outcome)
        
        return jsonify({
            'success': True,
            'message': '事件学习完成'
        })
    except Exception as e:
        logger.error(f"从事件学习失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/knowledge/domains', methods=['GET'])
def get_domains():
    """获取知识领域列表"""
    try:
        domains = [
            {'value': e.value, 'name': e.name, 'description': _get_domain_description(e)}
            for e in KnowledgeDomain
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'domains': domains,
                'total': len(domains)
            }
        })
    except Exception as e:
        logger.error(f"获取领域列表失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


def _get_domain_description(domain: KnowledgeDomain) -> str:
    descriptions = {
        KnowledgeDomain.ERROR_FIX: '错误修复领域',
        KnowledgeDomain.PERFORMANCE: '性能优化领域',
        KnowledgeDomain.SECURITY: '安全领域',
        KnowledgeDomain.DATABASE: '数据库领域',
        KnowledgeDomain.FRONTEND: '前端领域',
        KnowledgeDomain.BACKEND: '后端领域',
        KnowledgeDomain.DEVOPS: '运维领域',
        KnowledgeDomain.AI_ML: 'AI/机器学习领域',
        KnowledgeDomain.UX: '用户体验领域',
        KnowledgeDomain.BUSINESS: '业务领域',
        KnowledgeDomain.GENERAL: '通用领域',
    }
    return descriptions.get(domain, domain.value)


@brain_bank_api.route('/brain-bank/knowledge/types', methods=['GET'])
def get_knowledge_types():
    """获取知识类型列表"""
    try:
        types = [
            {'value': e.value, 'name': e.name, 'description': _get_type_description(e)}
            for e in KnowledgeType
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'types': types,
                'total': len(types)
            }
        })
    except Exception as e:
        logger.error(f"获取知识类型失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


def _get_type_description(ktype: KnowledgeType) -> str:
    descriptions = {
        KnowledgeType.EXPERIENCE: '经验知识',
        KnowledgeType.PATTERN: '模式知识',
        KnowledgeType.RULE: '规则知识',
        KnowledgeType.SOLUTION: '解决方案',
        KnowledgeType.INSIGHT: '洞见知识',
        KnowledgeType.BEST_PRACTICE: '最佳实践',
        KnowledgeType.LESSON_LEARNED: '教训知识',
        KnowledgeType.HEURISTIC: '启发式知识',
        KnowledgeType.PREDICTIVE: '预测性知识',
        KnowledgeType.CAUSAL: '因果知识',
    }
    return descriptions.get(ktype, ktype.value)


@brain_bank_api.route('/brain-bank/consolidate', methods=['POST'])
def consolidate_knowledge():
    """知识整合"""
    try:
        count = knowledge_brain_bank.storage.consolidate_knowledge()
        
        return jsonify({
            'success': True,
            'message': f'知识整合完成，处理 {count} 条知识',
            'data': {
                'processed_count': count
            }
        })
    except Exception as e:
        logger.error(f"知识整合失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/stats', methods=['GET'])
def get_detailed_stats():
    """获取详细统计"""
    try:
        stats = knowledge_brain_bank.get_brain_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"获取统计失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@brain_bank_api.route('/brain-bank/test', methods=['GET'])
def test_brain_bank():
    """测试脑库系统"""
    try:
        stats = knowledge_brain_bank.get_brain_stats()
        
        # 测试搜索
        test_results = knowledge_brain_bank.storage.search_knowledge('优化', limit=3)
        
        # 测试触发评估
        test_context = {'cpu_percent': 95, 'memory_percent': 80}
        triggered = knowledge_brain_bank.evaluate_and_trigger(test_context)
        
        return jsonify({
            'success': True,
            'data': {
                'brain_status': stats['status'],
                'total_knowledge': stats['knowledge']['total_knowledge'],
                'total_triggers': stats['triggers']['total_triggers'],
                'search_test_results': len(test_results),
                'trigger_test_count': len(triggered),
                'empowerment_rate': stats['empowerment_rate']
            }
        })
    except Exception as e:
        logger.error(f"测试脑库失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
