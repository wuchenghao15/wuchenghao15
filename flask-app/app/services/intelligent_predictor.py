"""
智能预测分析系统 v4.0.0
包括学习预测、系统性能预测、趋势分析
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """预测类型"""
    LEARNING_PERFORMANCE = "learning_performance"  # 学习表现预测
    STUDENT_RISK = "student_risk"                  # 学生风险预测
    SYSTEM_LOAD = "system_load"                    # 系统负载预测
    RESOURCE_USAGE = "resource_usage"              # 资源使用预测
    USER_GROWTH = "user_growth"                    # 用户增长预测
    ENGAGEMENT = "engagement"                      # 参与度预测


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PredictionResult:
    """预测结果"""
    prediction_type: PredictionType
    target: str
    predicted_value: float
    confidence: float
    trend: str  # "increasing", "decreasing", "stable"
    time_range: Dict[str, datetime]
    factors: List[str]
    recommendations: List[str]
    created_at: datetime


@dataclass
class TimeSeriesData:
    """时间序列数据"""
    timestamps: List[datetime]
    values: List[float]
    metadata: Dict[str, Any]


class IntelligentPredictor:
    """智能预测器"""
    
    def __init__(self):
        self.history: Dict[str, TimeSeriesData] = {}
        self.predictions: Dict[str, List[PredictionResult]] = defaultdict(list)
        self.max_history = 1000
        logger.info("智能预测分析系统初始化完成")
    
    def add_time_series(self, series_id: str, values: List[float], 
                       timestamps: Optional[List[datetime]] = None,
                       metadata: Optional[Dict[str, Any]] = None):
        """添加时间序列数据"""
        if timestamps is None:
            now = datetime.now()
            timestamps = [now - timedelta(hours=i) for i in range(len(values), 0, -1)]
        
        self.history[series_id] = TimeSeriesData(
            timestamps=timestamps,
            values=values,
            metadata=metadata or {}
        )
        logger.info(f"添加时间序列数据: {series_id}, {len(values)}个数据点")
    
    def exponential_smoothing(self, series: List[float], alpha: float = 0.3) -> List[float]:
        """指数平滑"""
        if not series:
            return []
        
        smoothed = [series[0]]
        for i in range(1, len(series)):
            smoothed.append(alpha * series[i] + (1 - alpha) * smoothed[-1])
        return smoothed
    
    def moving_average(self, series: List[float], window: int = 5) -> List[float]:
        """移动平均"""
        if len(series) < window:
            return series
        
        result = []
        for i in range(window - 1, len(series)):
            avg = sum(series[i - window + 1:i + 1]) / window
            result.append(avg)
        return result
    
    def detect_trend(self, series: List[float]) -> Tuple[str, float]:
        """检测趋势"""
        if len(series) < 2:
            return "stable", 0.0
        
        # 使用线性回归计算趋势
        n = len(series)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(series) / n
        
        numerator = sum((x[i] - x_mean) * (series[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable", 0.0
        
        slope = numerator / denominator
        
        if slope > 0.1:
            trend = "increasing"
        elif slope < -0.1:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return trend, slope
    
    def calculate_confidence(self, series: List[float]) -> float:
        """计算预测置信度"""
        if len(series) < 5:
            return 0.5
        
        # 基于变异系数计算置信度
        mean = sum(series) / len(series)
        if mean == 0:
            return 0.6
        
        variance = sum((x - mean) ** 2 for x in series) / len(series)
        cv = math.sqrt(variance) / mean
        
        # 变异系数越小，置信度越高
        confidence = max(0.3, min(0.95, 1.0 - cv))
        return confidence
    
    def predict_next_n(self, series_id: str, n: int = 7, 
                     method: str = "exponential") -> Optional[List[float]]:
        """预测未来n个时间点的值"""
        if series_id not in self.history:
            return None
        
        data = self.history[series_id]
        values = data.values
        
        if len(values) < 3:
            return None
        
        if method == "exponential":
            smoothed = self.exponential_smoothing(values, alpha=0.4)
            last_value = smoothed[-1]
            
            # 简单趋势延续
            trend, slope = self.detect_trend(smoothed[-10:])
            predictions = []
            
            for i in range(n):
                if trend == "increasing":
                    pred = last_value + (slope * (i + 1))
                elif trend == "decreasing":
                    pred = last_value + (slope * (i + 1))
                else:
                    pred = last_value
                
                pred = max(0, pred)  # 确保非负
                predictions.append(pred)
            
            return predictions
        
        elif method == "moving_average":
            ma = self.moving_average(values, window=min(7, len(values)))
            if not ma:
                return None
            
            avg_change = sum(ma[i] - ma[i-1] for i in range(1, len(ma))) / (len(ma) - 1) if len(ma) > 1 else 0
            last_value = ma[-1]
            
            predictions = []
            for i in range(n):
                pred = last_value + avg_change * (i + 1)
                pred = max(0, pred)
                predictions.append(pred)
            
            return predictions
        
        return None
    
    def predict_learning_performance(self, student_id: str, 
                                   historical_scores: List[Dict[str, Any]],
                                   study_hours: List[float],
                                   engagement_data: List[float]) -> PredictionResult:
        """预测学习表现"""
        # 准备数据
        scores = [s.get('score', 0) for s in historical_scores]
        if not scores:
            scores = [70, 75, 72]  # 默认值
        
        series_id = f"student_{student_id}_scores"
        self.add_time_series(series_id, scores)
        
        # 预测
        predictions = self.predict_next_n(series_id, n=5)
        predicted_score = sum(predictions) / len(predictions) if predictions else scores[-1]
        
        # 分析趋势
        trend, slope = self.detect_trend(scores[-10:])
        
        # 计算置信度
        confidence = self.calculate_confidence(scores)
        
        # 分析影响因素
        factors = []
        if len(study_hours) >= 2:
            recent_study = sum(study_hours[-7:]) / 7 if len(study_hours) >= 7 else sum(study_hours) / len(study_hours)
            if recent_study < 2:
                factors.append("学习时间不足")
        
        if len(engagement_data) >= 2:
            avg_engagement = sum(engagement_data[-7:]) / 7 if len(engagement_data) >= 7 else sum(engagement_data) / len(engagement_data)
            if avg_engagement < 0.5:
                factors.append("参与度较低")
        
        # 生成建议
        recommendations = self._generate_learning_recommendations(trend, factors, predicted_score)
        
        now = datetime.now()
        result = PredictionResult(
            prediction_type=PredictionType.LEARNING_PERFORMANCE,
            target=student_id,
            predicted_value=predicted_score,
            confidence=confidence,
            trend=trend,
            time_range={
                'start': now,
                'end': now + timedelta(days=7)
            },
            factors=factors,
            recommendations=recommendations,
            created_at=now
        )
        
        self.predictions[student_id].append(result)
        logger.info(f"生成学生 {student_id} 学习表现预测: {predicted_score:.1f}分, 趋势: {trend}")
        return result
    
    def predict_student_risk(self, student_id: str,
                           performance_trend: str,
                           attendance_rate: float,
                           assignment_completion: float,
                           recent_scores: List[float]) -> Tuple[RiskLevel, Dict[str, Any]]:
        """预测学生风险等级"""
        risk_score = 0
        factors = []
        
        # 成绩趋势分析
        if performance_trend == "decreasing":
            risk_score += 25
            factors.append("成绩下降")
        elif performance_trend == "stable":
            risk_score += 10
        
        # 出勤率分析
        if attendance_rate < 0.7:
            risk_score += 30
            factors.append("出勤率低")
        elif attendance_rate < 0.85:
            risk_score += 15
        
        # 作业完成情况
        if assignment_completion < 0.6:
            risk_score += 30
            factors.append("作业完成率低")
        elif assignment_completion < 0.8:
            risk_score += 15
        
        # 近期成绩分析
        if recent_scores:
            avg_score = sum(recent_scores) / len(recent_scores)
            if avg_score < 60:
                risk_score += 25
                factors.append("近期成绩偏低")
            elif avg_score < 70:
                risk_score += 10
        
        # 确定风险等级
        if risk_score >= 70:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 45:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 25:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        risk_details = {
            'risk_score': risk_score,
            'risk_level': risk_level.value,
            'factors': factors,
            'attendance_rate': attendance_rate,
            'assignment_completion': assignment_completion
        }
        
        logger.info(f"学生 {student_id} 风险评估: {risk_level.value} ({risk_score}分)")
        return risk_level, risk_details
    
    def predict_system_load(self, historical_load: List[float],
                           time_of_day: int = None) -> PredictionResult:
        """预测系统负载"""
        series_id = "system_load"
        self.add_time_series(series_id, historical_load)
        
        predictions = self.predict_next_n(series_id, n=24)
        avg_prediction = sum(predictions) / len(predictions) if predictions else historical_load[-1]
        
        trend, slope = self.detect_trend(historical_load[-48:])
        confidence = self.calculate_confidence(historical_load[-48:])
        
        factors = []
        if trend == "increasing":
            factors.append("负载呈上升趋势")
        
        if avg_prediction > 80:
            factors.append("预计高负载")
        
        recommendations = self._generate_system_recommendations(trend, avg_prediction)
        
        now = datetime.now()
        result = PredictionResult(
            prediction_type=PredictionType.SYSTEM_LOAD,
            target="system",
            predicted_value=avg_prediction,
            confidence=confidence,
            trend=trend,
            time_range={
                'start': now,
                'end': now + timedelta(hours=24)
            },
            factors=factors,
            recommendations=recommendations,
            created_at=now
        )
        
        self.predictions["system"].append(result)
        logger.info(f"系统负载预测: {avg_prediction:.1f}%, 趋势: {trend}")
        return result
    
    def predict_resource_usage(self, resource_type: str,
                              historical_usage: List[float],
                              capacity: float) -> Dict[str, Any]:
        """预测资源使用情况"""
        series_id = f"resource_{resource_type}"
        self.add_time_series(series_id, historical_usage)
        
        predictions = self.predict_next_n(series_id, n=30)
        
        # 预测何时达到容量
        days_to_full = None
        if predictions:
            trend, slope = self.detect_trend(historical_usage[-14:])
            if trend == "increasing" and slope > 0:
                current_usage = historical_usage[-1]
                remaining = capacity - current_usage
                if remaining > 0 and slope > 0:
                    days_to_full = int(remaining / slope)
        
        avg_prediction = sum(predictions) / len(predictions) if predictions else historical_usage[-1]
        
        return {
            'resource_type': resource_type,
            'predicted_usage': avg_prediction,
            'capacity': capacity,
            'utilization_rate': avg_prediction / capacity,
            'days_to_full': days_to_full,
            'trend': self.detect_trend(historical_usage[-7:])[0]
        }
    
    def _generate_learning_recommendations(self, trend: str, 
                                          factors: List[str],
                                          predicted_score: float) -> List[str]:
        """生成学习建议"""
        recommendations = []
        
        if trend == "decreasing":
            recommendations.append("建议回顾近期学习内容，重点复习薄弱环节")
        
        if predicted_score < 70:
            recommendations.append("考虑寻求老师或同学的帮助")
            recommendations.append("增加练习量，巩固基础知识")
        
        if "学习时间不足" in factors:
            recommendations.append("制定学习计划，保证每天至少2小时的学习时间")
        
        if "参与度较低" in factors:
            recommendations.append("积极参与课堂互动和讨论")
        
        if not recommendations:
            recommendations.append("保持良好的学习习惯，继续努力")
        
        return recommendations
    
    def _generate_system_recommendations(self, trend: str, 
                                       predicted_load: float) -> List[str]:
        """生成系统建议"""
        recommendations = []
        
        if predicted_load > 80:
            recommendations.append("建议启动自动扩容机制")
            recommendations.append("优化数据库查询，减轻负载")
        
        if trend == "increasing":
            recommendations.append("密切关注负载变化，准备应急预案")
            recommendations.append("检查系统资源配置，确保充足")
        
        if predicted_load > 90:
            recommendations.append("临时限制非关键服务，保证核心功能可用")
        
        return recommendations
    
    def get_prediction_history(self, target: str, 
                              limit: int = 10) -> List[PredictionResult]:
        """获取预测历史"""
        return self.predictions.get(target, [])[-limit:]
    
    def get_prediction_statistics(self) -> Dict[str, Any]:
        """获取预测统计信息"""
        total_predictions = sum(len(preds) for preds in self.predictions.values())
        type_counts = defaultdict(int)
        
        for preds in self.predictions.values():
            for pred in preds:
                type_counts[pred.prediction_type.value] += 1
        
        return {
            'total_predictions': total_predictions,
            'predictions_by_type': dict(type_counts),
            'active_series': len(self.history),
            'tracking_targets': len(self.predictions)
        }


# 全局单例
_predictor: Optional[IntelligentPredictor] = None


def get_predictor() -> IntelligentPredictor:
    """获取预测器单例"""
    global _predictor
    if _predictor is None:
        _predictor = IntelligentPredictor()
    return _predictor
