#!/usr/bin/env python3
"""
问题诊断修复AI员工
专门负责检测和修复系统问题的AI员工
"""

import logging
import json
import uuid
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class DiagnosticsRepairEmployee:
    """问题诊断修复AI员工"""
    
    def __init__(self, employee_id: str, name: str, level: int = 1):
        self.employee_id = employee_id
        self.name = name
        self.level = level
        self.type = "diagnostics_repair"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.performance_score = 80 + level * 2
        self.knowledge_base = []
        
        self.skills = [
            {"name": "system_diagnostics", "level": 5 + level, "experience": 0.0},
            {"name": "problem_detection", "level": 5 + level, "experience": 0.0},
            {"name": "auto_repair", "level": 5 + level, "experience": 0.0},
            {"name": "health_monitoring", "level": 5 + level, "experience": 0.0},
            {"name": "report_generation", "level": 4 + level, "experience": 0.0},
            {"name": "root_cause_analysis", "level": 4 + level, "experience": 0.0}
        ]
        
        logger.info(f"[诊断修复员工] 创建: {self.name} ({self.employee_id}) 级别: {self.level}")
    
    def start(self):
        """启动员工"""
        self.status = "active"
        logger.info(f"[诊断修复员工] {self.name} 已启动")
    
    def get_status(self) -> Dict[str, Any]:
        """获取员工状态"""
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "status": self.status,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / max(self.task_count, 1) * 100,
            "performance_score": self.performance_score,
            "skills": self.skills
        }
    
    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        self.task_count += 1
        start_time = time.time()
        
        try:
            task_type = task_data.get("task_type", "diagnostics")
            
            if task_type == "diagnostics":
                result = self._run_diagnostics(task_data)
            elif task_type == "repair":
                result = self._run_repair(task_data)
            elif task_type == "health_check":
                result = self._run_health_check(task_data)
            elif task_type == "full_scan":
                result = self._run_full_scan(task_data)
            else:
                result = {"success": False, "error": f"未知任务类型: {task_type}"}
            
            if result.get("success", False):
                self.success_count += 1
                self._update_performance(True, time.time() - start_time)
            else:
                self.failure_count += 1
                self._update_performance(False, time.time() - start_time)
            
            result["execution_time"] = time.time() - start_time
            result["employee_id"] = self.employee_id
            result["employee_name"] = self.name
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self._update_performance(False, time.time() - start_time)
            logger.error(f"[诊断修复员工] 任务执行失败: {self.name}, 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "employee_id": self.employee_id,
                "employee_name": self.name
            }
    
    def _run_diagnostics(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """运行诊断检测"""
        logger.info(f"[诊断修复员工] {self.name} 开始诊断检测...")
        
        from app.services.problems_and_diagnostics import get_problems_and_diagnostics_service
        
        try:
            diagnostics = get_problems_and_diagnostics_service()
            problems = diagnostics.detect_problems()
            
            problems_data = []
            for problem in problems:
                problems_data.append({
                    "problem_id": problem.problem_id,
                    "severity": problem.severity,
                    "category": problem.category,
                    "title": problem.title,
                    "description": problem.description,
                    "recommendation": problem.recommendation,
                    "status": problem.status
                })
            
            logger.info(f"[诊断修复员工] {self.name} 检测到 {len(problems_data)} 个问题")
            
            return {
                "success": True,
                "message": f"诊断完成，检测到 {len(problems_data)} 个问题",
                "problems": problems_data,
                "total_problems": len(problems_data),
                "critical_count": len([p for p in problems_data if p["severity"] == "critical"]),
                "high_count": len([p for p in problems_data if p["severity"] == "high"]),
                "medium_count": len([p for p in problems_data if p["severity"] == "medium"]),
                "low_count": len([p for p in problems_data if p["severity"] == "low"])
            }
            
        except Exception as e:
            logger.error(f"[诊断修复员工] 诊断检测失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_repair(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """运行修复任务"""
        logger.info(f"[诊断修复员工] {self.name} 开始修复任务...")
        
        problem_data = task_data.get("problem_data", {})
        
        try:
            from app.ai.ai_task_scheduler import get_ai_task_scheduler
            
            scheduler = get_ai_task_scheduler()
            
            problems_data = [problem_data]
            fix_result = scheduler.submit_problems_for_fix(problems_data)
            
            scheduler.start_scheduler()
            time.sleep(5)
            
            tasks = scheduler.get_all_tasks()
            task_id = fix_result.get("task_ids", [None])[0]
            
            if task_id and task_id in [t["task_id"] for t in tasks]:
                task = next(t for t in tasks if t["task_id"] == task_id)
                success = task.get("success", False)
                fix_result = task.get("fix_result", "修复完成")
                
                if success:
                    logger.info(f"[诊断修复员工] {self.name} 修复成功: {problem_data.get('title')}")
                    return {
                        "success": True,
                        "message": "修复成功",
                        "problem_id": problem_data.get("problem_id"),
                        "fix_result": fix_result,
                        "task_id": task_id
                    }
                else:
                    logger.warning(f"[诊断修复员工] {self.name} 修复失败: {problem_data.get('title')}")
                    return {
                        "success": False,
                        "message": "修复失败",
                        "problem_id": problem_data.get("problem_id"),
                        "fix_result": fix_result,
                        "task_id": task_id
                    }
            
            return {"success": False, "error": "任务未执行"}
            
        except Exception as e:
            logger.error(f"[诊断修复员工] 修复任务失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_health_check(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """运行健康检查"""
        logger.info(f"[诊断修复员工] {self.name} 开始健康检查...")
        
        try:
            from app.services.problems_and_diagnostics import get_problems_and_diagnostics_service
            
            diagnostics = get_problems_and_diagnostics_service()
            health_result = diagnostics.run_health_check()
            
            logger.info(f"[诊断修复员工] {self.name} 健康检查完成: {health_result['summary']}")
            
            return {
                "success": True,
                "message": "健康检查完成",
                "health_check": health_result,
                "status": "healthy" if health_result["summary"]["fail"] == 0 else "unhealthy"
            }
            
        except Exception as e:
            logger.error(f"[诊断修复员工] 健康检查失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_full_scan(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """运行全面扫描和修复"""
        logger.info(f"[诊断修复员工] {self.name} 开始全面扫描和修复...")
        
        start_time = time.time()
        
        try:
            from app.services.problems_and_diagnostics import run_powerful_diagnostic_fix
            
            result = run_powerful_diagnostic_fix()
            
            execution_time = time.time() - start_time
            
            logger.info(f"[诊断修复员工] {self.name} 全面扫描完成，耗时: {execution_time:.2f}s")
            
            return {
                "success": True,
                "message": result.get("message", "全面扫描完成"),
                "diagnostics_result": result,
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"[诊断修复员工] 全面扫描失败: {e}")
            return {"success": False, "error": str(e), "execution_time": time.time() - start_time}
    
    def _update_performance(self, success: bool, execution_time: float):
        """更新性能评分"""
        score_change = 2 if success else -3
        
        if execution_time < 3:
            score_change += 1
        elif execution_time > 10:
            score_change -= 1
        
        self.performance_score = max(0, min(100, self.performance_score + score_change))
        
        if success:
            for skill in self.skills:
                skill["experience"] += 0.5
    
    def learn_from_experience(self, problem_data: Dict[str, Any], fix_result: Dict[str, Any]):
        """从经验中学习"""
        experience = {
            "problem_id": problem_data.get("problem_id"),
            "category": problem_data.get("category"),
            "severity": problem_data.get("severity"),
            "fix_strategy": fix_result.get("strategy"),
            "success": fix_result.get("success", False),
            "timestamp": datetime.now().isoformat()
        }
        
        self.knowledge_base.append(experience)
        if len(self.knowledge_base) > 1000:
            self.knowledge_base = self.knowledge_base[-1000:]
        
        if fix_result.get("success", False):
            self.level = min(10, self.level + 1)
            logger.info(f"[诊断修复员工] {self.name} 学习升级，当前级别: {self.level}")
    
    def generate_report(self, problems: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成诊断报告"""
        report = {
            "report_id": f"report_{uuid.uuid4().hex[:8]}",
            "generated_by": self.employee_id,
            "employee_name": self.name,
            "generated_at": datetime.now().isoformat(),
            "total_problems": len(problems),
            "problems_by_category": {},
            "problems_by_severity": {},
            "summary": "",
            "recommendations": []
        }
        
        for problem in problems:
            category = problem.get("category", "unknown")
            severity = problem.get("severity", "unknown")
            
            report["problems_by_category"][category] = report["problems_by_category"].get(category, 0) + 1
            report["problems_by_severity"][severity] = report["problems_by_severity"].get(severity, 0) + 1
            
            if problem.get("recommendation"):
                report["recommendations"].append(problem["recommendation"])
        
        critical_count = report["problems_by_severity"].get("critical", 0)
        high_count = report["problems_by_severity"].get("high", 0)
        
        if critical_count > 0:
            report["summary"] = f"检测到 {critical_count} 个严重问题，需要立即处理"
        elif high_count > 0:
            report["summary"] = f"检测到 {high_count} 个高优先级问题，建议尽快处理"
        else:
            report["summary"] = "系统状态良好，无严重问题"
        
        return report
