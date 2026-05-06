#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控系统集成脚本
将监控系统与现有的AI员工系统、分布式系统和影子系统集成

import time
import logging
import sys
import os
from monitoring_system import MonitoringSystem, MetricType, AlertLevel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integrate_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('IntegrateMonitoring')

class MonitoringIntegrator:
    """监控系统集成器"""

    def __init__(self):
        self.monitoring_system = None
        self.integrated_systems = []

    def start_monitoring_system(self):
        """启动监控系统"""
        logger.info("启动监控系统...")
        self.monitoring_system = MonitoringSystem("main_monitor")
        self.monitoring_system.start()
        logger.info("监控系统已启动")
        return self.monitoring_system

    def register_ai_employee_system(self):
        """注册AI员工系统"""
        logger.info("注册AI员工系统...")
        # 这里假设AI员工系统有一个实例可以注册
        # 实际情况下，可能需要通过API或其他方式连接
        self.monitoring_system.register_system(
            "ai_employee_system",
            "ai_employee",
            None  # 暂时没有实例，使用心跳机制监控
        )
        logger.info("AI员工系统已注册")

    def register_distributed_system(self):
        """注册分布式系统"""
        logger.info("注册分布式系统...")
        self.monitoring_system.register_system(
            "distributed_system",
            None  # 暂时没有实例，使用心跳机制监控
        )
        logger.info("分布式系统已注册")
    def register_shadow_system(self):
        """注册影子系统"""
        logger.info("注册影子系统...")
        self.monitoring_system.register_system(
            "shadow_system",
            "shadow",
        )
        logger.info("影子系统已注册")

    def register_ai_brain_system(self):
        logger.info("注册AI脑图系统...")
        self.monitoring_system.register_system(
            "ai_brain_system",
            "ai_brain",
            None  # 暂时没有实例，使用心跳机制监控
        logger.info("AI脑图系统已注册")

    def add_alert_rules(self):
        """添加告警规则"""
        logger.info("添加告警规则...")
        # CPU使用率告警
        self.monitoring_system.add_alert_rule(
            "rule_cpu_high",
            "cpu_usage",
            ">",
            80.0,
            AlertLevel.WARNING,
            "CPU使用率过高"
        )
        # 内存使用率告警
        self.monitoring_system.add_alert_rule(
            "rule_memory_high",
            "memory_usage",
            ">",
            85.0,
            AlertLevel.WARNING,
            "内存使用率过高"
        )
        # 系统心跳超时告警
        self.monitoring_system.add_alert_rule(
            "rule_heartbeat_timeout",
            "system_heartbeat",
            1,
            AlertLevel.CRITICAL,
            "系统心跳超时"
        # 请求错误率告警
        self.monitoring_system.add_alert_rule(
            "error_rate",
            ">",
            AlertLevel.ERROR,
            "请求错误率过高"
        )
        logger.info("告警规则已添加")

    def simulate_metrics(self, duration=60):
        """模拟指标数据（用于测试）"""
        logger.info(f"模拟指标数据，持续 {duration} 秒...")

        while time.time() - start_time < duration:
            for system_id in self.integrated_systems:
                # 模拟CPU使用率（40-70%）
                cpu_usage = 40 + (time.time() % 30)
                self.monitoring_system.add_metric(
                    "cpu_usage",
                    cpu_usage,
                    MetricType.GAUGE
                )
                # 模拟内存使用率（50-75%）
                memory_usage = 50 + (time.time() % 25)
                self.monitoring_system.add_metric(
                    system_id,
                    "memory_usage",
                    memory_usage,
                    MetricType.GAUGE
                )
                # 模拟请求计数
                request_count = int(time.time() % 1000)
                self.monitoring_system.add_metric(
                    system_id,
                    "request_count",
                    request_count,
                )
                # 模拟系统心跳
                self.monitoring_system.add_metric(
                    system_id,
                    "system_heartbeat",
                    1,
                    MetricType.GAUGE
                )
            time.sleep(2)


        logger.info("显示仪表盘数据...")

        dashboard = self.monitoring_system.get_dashboard_data()
        print("\n" + "=" * 60)
        print("监控系统仪表盘")

        # 系统状态
        for system_id, status in dashboard["system_status"].items():
            print(f"  {system_id} ({status['type']}): {status['status']}")

        # 最新指标
        for metric_key, metric in dashboard["latest_metrics"].items():
                system_id = metric_key.split("_")[0]
                print(f"  {system_id} - {metric_name}: {metric['value']:.2f}%")
        # 活跃告警
        print("\n活跃告警:")
        if dashboard["active_alerts"]:
            for alert in dashboard["active_alerts"]:
                print(f"  [{alert['level']}] {alert['system_id']} - {alert['description']}")
            print("  无活跃告警")

        # 系统状态摘要
        print("\n系统状态摘要:")
        system_status = self.monitoring_system.get_system_status()
        for key, value in system_status.items():
            if key != "timestamp":
                print(f"  {key}: {value}")

        print("\n" + "=" * 60)

    def generate_report(self):
        """生成监控报告"""
        logger.info("生成监控报告...")
        report = self.monitoring_system.generate_report(3600)  # 1小时报告

        print("\n监控报告摘要:")
        print(f"  报告ID: {report['report_id']}")
        print(f"  生成时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report['generated_at']))}")
        print(f"  监控时长: {report['duration']}秒")
        print(f"  指标总数: {report['metrics_summary']['total_metrics']}")
        print(f"  告警总数: {report['alerts_summary']['total_alerts']}")

        # 系统指标统计
        print("\n系统指标统计:")
        for system_id, count in report['metrics_summary']['metrics_by_system'].items():
            print(f"  {system_id}: {count}个指标")

        # 告警级别统计
        print("\n告警级别统计:")
        for level, count in report['alerts_summary']['alerts_by_level'].items():
            print(f"  {level}: {count}个告警")

    def run(self):
        """运行集成流程"""
        logger.info("开始监控系统集成...")

        try:
            # 1. 启动监控系统
            self.start_monitoring_system()

            # 2. 注册各个系统
            self.register_ai_employee_system()
            self.register_distributed_system()
            self.register_shadow_system()
            self.register_ai_brain_system()
            # 3. 添加告警规则
            self.add_alert_rules()

            # 4. 模拟指标数据
            self.simulate_metrics(30)

            # 5. 显示仪表盘
            self.display_dashboard()

            # 6. 生成报告
            self.generate_report()

            logger.info("监控系统集成完成")

            # 保持运行，持续监控
            print("\n监控系统已启动并集成，按 Ctrl+C 停止...")
            while True:
                time.sleep(10)
                self.display_dashboard()

        except KeyboardInterrupt:
            logger.info("监控系统集成已中断")
            if self.monitoring_system:
                self.monitoring_system.stop()
        except Exception as e:
            logger.error(f"监控系统集成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            if self.monitoring_system:
                self.monitoring_system.stop()

def main():
    """主函数"""
    integrator = MonitoringIntegrator()
    integrator.run()

if __name__ == "__main__":
    main()
