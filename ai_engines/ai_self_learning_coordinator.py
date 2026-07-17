# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI自我学习统一协调器
功能: 整合所有子系统,协调网络学习、自我觉醒、脑库投喂、学习方向发现和规则执行
实现AI自我学习的完整闭环
"""

import os
import sys
import json
import logging
import threading
import time
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_self_learning_coordinator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AISelfLearningCoordinator:
    """AI自我学习统一协调器"""
    
    def __init__(self, rules_file: str = 'rules.json'):
        self.rules_file = rules_file
        self.rules = self._load_rules()
        
        self.is_running = False
        self.coordination_thread = None
        self.coordination_interval = 3600
        
        self.subsystems = {}
        self.system_status = {
            'network_learning': {'running': False, 'last_run': None, 'knowledge_count': 0},
            'self_awakening': {'running': False, 'last_run': None, 'insights_count': 0},
            'brain_feeding': {'running': False, 'last_run': None, 'stored_count': 0},
            'direction_discovery': {'running': False, 'last_run': None, 'directions_count': 0},
            'rule_execution': {'running': False, 'last_run': None, 'compliant': True}
        }
        
        self._init_subsystems()
    
    def _load_rules(self) -> Dict:
        """加载规则"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载规则文件失败: {str(e)}")
            return {}
    
    def _init_subsystems(self):
        """初始化子系统"""
        logger.info("初始化AI自我学习子系统...")
        
        try:
            from ai_network_learning_engine import AINetworkLearningEngine
            self.subsystems['network_learning'] = AINetworkLearningEngine(self.rules_file)
            logger.info("网络知识学习引擎初始化完成")
        except Exception as e:
            logger.error(f"初始化网络知识学习引擎失败: {str(e)}")
        
        try:
            from ai_self_awakening_learning import AISelfAwakeningSystem
            self.subsystems['self_awakening'] = AISelfAwakeningSystem(self.rules_file)
            logger.info("自我觉醒学习系统初始化完成")
        except Exception as e:
            logger.error(f"初始化自我觉醒学习系统失败: {str(e)}")
        
        try:
            from ai_brain_auto_feeding import AIBrainAutoFeedingSystem
            self.subsystems['brain_feeding'] = AIBrainAutoFeedingSystem(self.rules_file)
            logger.info("脑库自动投喂系统初始化完成")
        except Exception as e:
            logger.error(f"初始化脑库自动投喂系统失败: {str(e)}")
        
        try:
            from ai_learning_direction_discoverer import AILearningDirectionDiscoverer
            self.subsystems['direction_discovery'] = AILearningDirectionDiscoverer(self.rules_file)
            logger.info("学习方向发现系统初始化完成")
        except Exception as e:
            logger.error(f"初始化学习方向发现系统失败: {str(e)}")
        
        try:
            from ai_rule_executor import AIRuleExecutor
            self.subsystems['rule_execution'] = AIRuleExecutor(self.rules_file)
            logger.info("规则执行监督系统初始化完成")
        except Exception as e:
            logger.error(f"初始化规则执行监督系统失败: {str(e)}")
        
        logger.info(f"共初始化 {len(self.subsystems)} 个子系统")
    
    def start(self):
        """启动统一协调器"""
        if not self.is_running:
            self.is_running = True
            
            for name, subsystem in self.subsystems.items():
                try:
                    subsystem.start()
                    self.system_status[name]['running'] = True
                    logger.info(f"子系统 {name} 已启动")
                except Exception as e:
                    logger.error(f"启动子系统 {name} 失败: {str(e)}")
            
            self.coordination_thread = threading.Thread(target=self._coordination_loop, daemon=True)
            self.coordination_thread.start()
            
            logger.info("AI自我学习统一协调器已启动")
    
    def stop(self):
        """停止统一协调器"""
        self.is_running = False
        
        if self.coordination_thread and self.coordination_thread.is_alive():
            self.coordination_thread.join(timeout=5)
        
        for name, subsystem in self.subsystems.items():
            try:
                subsystem.stop()
                self.system_status[name]['running'] = False
                logger.info(f"子系统 {name} 已停止")
            except Exception as e:
                logger.error(f"停止子系统 {name} 失败: {str(e)}")
        
        logger.info("AI自我学习统一协调器已停止")
    
    def _coordination_loop(self):
        """协调循环"""
        while self.is_running:
            try:
                self.perform_coordination()
                time.sleep(self.coordination_interval)
            except Exception as e:
                logger.error(f"协调循环出错: {str(e)}")
                time.sleep(600)
    
    def perform_coordination(self) -> Dict:
        """执行协调任务"""
        logger.info("开始执行协调任务...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'subsystems': {}
        }
        
        self._execute_network_learning(results)
        self._execute_self_awakening(results)
        self._execute_brain_feeding(results)
        self._execute_direction_discovery(results)
        self._execute_rule_execution(results)
        
        self._update_system_status(results)
        
        logger.info(f"协调任务执行完成: {results}")
        return results
    
    def _execute_network_learning(self, results: Dict):
        """执行网络学习"""
        if 'network_learning' not in self.subsystems:
            return
        
        try:
            network_engine = self.subsystems['network_learning']
            
            knowledge = network_engine.manual_fetch()
            self.system_status['network_learning']['last_run'] = datetime.now().isoformat()
            self.system_status['network_learning']['knowledge_count'] += len(knowledge)
            
            results['subsystems']['network_learning'] = {
                'status': 'success',
                'knowledge_fetched': len(knowledge)
            }
            
            logger.info(f"网络学习完成,获取 {len(knowledge)} 条知识")
        except Exception as e:
            results['subsystems']['network_learning'] = {
                'status': 'error',
                'error': str(e)
            }
            logger.error(f"网络学习失败: {str(e)}")
    
    def _execute_self_awakening(self, results: Dict):
        """执行自我觉醒"""
        if 'self_awakening' not in self.subsystems:
            return
        
        try:
            awakening_system = self.subsystems['self_awakening']
            
            awakening_result = awakening_system.perform_self_awakening()
            self.system_status['self_awakening']['last_run'] = datetime.now().isoformat()
            self.system_status['self_awakening']['insights_count'] += awakening_result.get('insights_extracted', 0)
            
            results['subsystems']['self_awakening'] = {
                'status': 'success',
                'events': awakening_result.get('awakening_events', 0),
                'insights': awakening_result.get('insights_extracted', 0)
            }
            
            logger.info(f"自我觉醒完成,提取 {awakening_result.get('insights_extracted', 0)} 条洞察")
        except Exception as e:
            results['subsystems']['self_awakening'] = {
                'status': 'error',
                'error': str(e)
            }
            logger.error(f"自我觉醒失败: {str(e)}")
    
    def _execute_brain_feeding(self, results: Dict):
        """执行脑库投喂"""
        if 'brain_feeding' not in self.subsystems or 'network_learning' not in self.subsystems:
            return
        
        try:
            feeding_system = self.subsystems['brain_feeding']
            network_engine = self.subsystems['network_learning']
            
            knowledge_buffer = network_engine.flush_buffer()
            
            feeding_result = feeding_system.batch_add_knowledge(knowledge_buffer)
            self.system_status['brain_feeding']['last_run'] = datetime.now().isoformat()
            self.system_status['brain_feeding']['stored_count'] += feeding_result.get('accepted', 0)
            
            results['subsystems']['brain_feeding'] = {
                'status': 'success',
                'accepted': feeding_result.get('accepted', 0),
                'rejected': feeding_result.get('rejected', 0),
                'duplicate': feeding_result.get('duplicate', 0)
            }
            
            logger.info(f"脑库投喂完成,接受 {feeding_result.get('accepted', 0)} 条知识")
        except Exception as e:
            results['subsystems']['brain_feeding'] = {
                'status': 'error',
                'error': str(e)
            }
            logger.error(f"脑库投喂失败: {str(e)}")
    
    def _execute_direction_discovery(self, results: Dict):
        """执行学习方向发现"""
        if 'direction_discovery' not in self.subsystems:
            return
        
        try:
            discoverer = self.subsystems['direction_discovery']
            
            discovery_result = discoverer.discover_learning_directions()
            self.system_status['direction_discovery']['last_run'] = datetime.now().isoformat()
            self.system_status['direction_discovery']['directions_count'] += discovery_result.get('total_directions', 0)
            
            results['subsystems']['direction_discovery'] = {
                'status': 'success',
                'gap_directions': discovery_result.get('gap_directions', 0),
                'trend_directions': discovery_result.get('trend_directions', 0),
                'problem_directions': discovery_result.get('problem_directions', 0),
                'success_directions': discovery_result.get('success_directions', 0)
            }
            
            logger.info(f"学习方向发现完成,发现 {discovery_result.get('total_directions', 0)} 个方向")
        except Exception as e:
            results['subsystems']['direction_discovery'] = {
                'status': 'error',
                'error': str(e)
            }
            logger.error(f"学习方向发现失败: {str(e)}")
    
    def _execute_rule_execution(self, results: Dict):
        """执行规则监督"""
        if 'rule_execution' not in self.subsystems:
            return
        
        try:
            rule_executor = self.subsystems['rule_execution']
            
            supervision_result = rule_executor.perform_supervision()
            self.system_status['rule_execution']['last_run'] = datetime.now().isoformat()
            self.system_status['rule_execution']['compliant'] = supervision_result['compliance_check']['overall_compliance']
            
            results['subsystems']['rule_execution'] = {
                'status': 'success',
                'compliant': supervision_result['compliance_check']['overall_compliance'],
                'violations': len(supervision_result['compliance_check']['violations']),
                'alerts': len(supervision_result['alerts'])
            }
            
            logger.info(f"规则监督完成,合规性: {'合规' if supervision_result['compliance_check']['overall_compliance'] else '不合规'}")
        except Exception as e:
            results['subsystems']['rule_execution'] = {
                'status': 'error',
                'error': str(e)
            }
            logger.error(f"规则监督失败: {str(e)}")
    
    def _update_system_status(self, results: Dict):
        """更新系统状态"""
        if 'rule_execution' in self.subsystems:
            stats = self._get_brain_stats()
            self.subsystems['rule_execution'].update_system_status({
                'learning_efficiency': self._calculate_learning_efficiency(),
                'knowledge_quality': stats.get('avg_confidence', 0.8),
                'brain_growth_rate': stats.get('growth_rate', 0),
                'rule_compliance': 1 if self.system_status['rule_execution']['compliant'] else 0,
                'system_health': self._calculate_system_health()
            })
    
    def _get_brain_stats(self) -> Dict:
        """获取脑库统计"""
        if 'brain_feeding' in self.subsystems:
            try:
                return self.subsystems['brain_feeding'].get_brain_stats()
            except Exception as e:
                logger.error(f"获取脑库统计失败: {str(e)}")
        
        return {'avg_confidence': 0.8, 'growth_rate': 0}
    
    def _calculate_learning_efficiency(self) -> float:
        """计算学习效率"""
        total_knowledge = self.system_status['network_learning']['knowledge_count']
        total_stored = self.system_status['brain_feeding']['stored_count']
        
        if total_knowledge > 0:
            return round(total_stored / total_knowledge, 2)
        return 0.8
    
    def _calculate_system_health(self) -> float:
        """计算系统健康度"""
        running_count = sum(1 for status in self.system_status.values() if status.get('running', False))
        total_count = len(self.system_status)
        
        if total_count > 0:
            health = running_count / total_count
            if not self.system_status['rule_execution']['compliant']:
                health *= 0.8
            return round(health, 2)
        return 1.0
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        return {
            'is_running': self.is_running,
            'subsystems': self.system_status,
            'brain_stats': self._get_brain_stats(),
            'learning_priorities': self._get_learning_priorities()
        }
    
    def _get_learning_priorities(self) -> List[Dict]:
        """获取学习优先级"""
        return self.rules.get('learning_policy', {}).get('learning_priorities', [])
    
    def trigger_learning_cycle(self) -> Dict:
        """手动触发学习周期"""
        logger.info("手动触发学习周期...")
        return self.perform_coordination()
    
    def get_learning_summary(self) -> Dict:
        """获取学习总结"""
        brain_stats = self._get_brain_stats()
        
        return {
            'total_knowledge_fetched': self.system_status['network_learning']['knowledge_count'],
            'total_knowledge_stored': self.system_status['brain_feeding']['stored_count'],
            'total_insights_extracted': self.system_status['self_awakening']['insights_count'],
            'total_directions_discovered': self.system_status['direction_discovery']['directions_count'],
            'brain_knowledge_count': brain_stats.get('knowledge_count', 0),
            'brain_size_mb': brain_stats.get('total_size_mb', 0),
            'avg_confidence': brain_stats.get('avg_confidence', 0),
            'system_health': self._calculate_system_health()
        }


def main():
    """主函数"""
    coordinator = AISelfLearningCoordinator()
    coordinator.start()
    
    print("\n" + "="*60)
    print("AI自我学习系统已启动")
    print("="*60)
    print("\n可用命令:")
    print("  status - 查看系统状态")
    print("  learn - 触发一次学习周期")
    print("  summary - 查看学习总结")
    print("  stop - 停止系统")
    print("  help - 显示帮助")
    print()
    
    try:
        while True:
            command = input("> ").strip().lower()
            
            if command == 'status':
                status = coordinator.get_system_status()
                print("\n系统状态:")
                print(f"  运行状态: {'运行中' if status['is_running'] else '已停止'}")
                print("\n子系统状态:")
                for name, stat in status['subsystems'].items():
                    print(f"  {name}: {'运行中' if stat['running'] else '已停止'}")
                    if stat['last_run']:
                        print(f"    最后运行: {stat['last_run'][:19]}")
                print("\n脑库统计:")
                brain = status['brain_stats']
                print(f"  知识总量: {brain.get('knowledge_count', 0)} 条")
                print(f"  总大小: {brain.get('total_size_mb', 0)} MB")
                print(f"  平均置信度: {brain.get('avg_confidence', 0)}")
            
            elif command == 'learn':
                print("\n正在执行学习周期...")
                result = coordinator.trigger_learning_cycle()
                print("学习周期完成:")
                for name, stat in result.get('subsystems', {}).items():
                    if stat['status'] == 'success':
                        print(f"  ✓ {name}: {stat}")
                    else:
                        print(f"  ✗ {name}: {stat['error']}")
            
            elif command == 'summary':
                summary = coordinator.get_learning_summary()
                print("\n学习总结:")
                print(f"  总获取知识: {summary['total_knowledge_fetched']} 条")
                print(f"  总存储知识: {summary['total_knowledge_stored']} 条")
                print(f"  总提取洞察: {summary['total_insights_extracted']} 条")
                print(f"  总发现方向: {summary['total_directions_discovered']} 个")
                print(f"  脑库知识量: {summary['brain_knowledge_count']} 条")
                print(f"  脑库大小: {summary['brain_size_mb']} MB")
                print(f"  平均置信度: {summary['avg_confidence']}")
                print(f"  系统健康度: {summary['system_health']}")
            
            elif command == 'stop':
                print("\n正在停止系统...")
                coordinator.stop()
                print("系统已停止")
                break
            
            elif command == 'help':
                print("\n可用命令:")
                print("  status - 查看系统状态")
                print("  learn - 触发一次学习周期")
                print("  summary - 查看学习总结")
                print("  stop - 停止系统")
                print("  help - 显示帮助")
            
            else:
                print(f"未知命令: {command}, 输入 help 查看可用命令")
            
            print()
    
    except KeyboardInterrupt:
        print("\n正在停止系统...")
        coordinator.stop()
        print("系统已停止")


if __name__ == "__main__":
    main()