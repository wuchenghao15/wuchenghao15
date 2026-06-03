# -*- coding: utf-8 -*-
"""路由优化API - 自动优化路由链路并上报数据库"""
from flask import Blueprint, request, jsonify
from app.utils.route_optimizer import route_optimizer
import json

route_optimization_api = Blueprint('route_optimization_api', __name__)


@route_optimization_api.route('/api/route-optimization/analyze', methods=['GET'])
def analyze_routes():
    """分析路由"""
    result = route_optimizer.analyze_routes()
    return jsonify(result)


@route_optimization_api.route('/api/route-optimization/optimize', methods=['POST'])
def optimize_routes():
    """优化路由"""
    result = route_optimizer.optimize_routes()
    return jsonify(result)


@route_optimization_api.route('/api/route-optimization/full', methods=['POST'])
def full_optimization():
    """完整优化流程"""
    result = route_optimizer.optimize_and_report()
    return jsonify(result)


@route_optimization_api.route('/api/route-optimization/report', methods=['GET'])
def get_report():
    """获取优化报告"""
    report = route_optimizer.get_optimization_report()
    return jsonify({"success": True, "report": report})


@route_optimization_api.route('/api/route-optimization/init-db', methods=['POST'])
def init_database():
    """初始化数据库"""
    result = route_optimizer.init_database()
    return jsonify(result)

