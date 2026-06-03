# -*- coding: utf-8 -*-
"""报关数据API - 供系统和AI自动调取"""
from flask import Blueprint, request, jsonify
import sqlite3
import json
import os
import sys

customs_api = Blueprint('customs_api', __name__)

def get_db_connection():
    """获取数据库连接"""
    db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@customs_api.route('/api/customs/declarations', methods=['GET'])
def get_declarations():
    """获取报关单列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 支持查询参数
        status = request.args.get('status')
        declaration_no = request.args.get('declaration_no')
        declarant_name = request.args.get('declarant_name')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        query = "SELECT * FROM customs_declarations WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if declaration_no:
            query += " AND declaration_no LIKE ?"
            params.append(f"%{declaration_no}%")
        
        if declarant_name:
            query += " AND declarant_name LIKE ?"
            params.append(f"%{declarant_name}%")
        
        query += " ORDER BY declared_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        declarations = [dict(row) for row in cursor.fetchall()]
        
        # 获取总数
        count_query = "SELECT COUNT(*) FROM customs_declarations WHERE 1=1"
        count_params = params[:-2]
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': declarations,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@customs_api.route('/api/customs/declarations/<declaration_no>', methods=['GET'])
def get_declaration(declaration_no):
    """获取单个报关单详情"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取报关主信息
        cursor.execute("SELECT * FROM customs_declarations WHERE declaration_no = ?", (declaration_no,))
        declaration = cursor.fetchone()
        
        if not declaration:
            return jsonify({'success': False, 'message': '报关单不存在'}), 404
        
        # 获取商品明细
        cursor.execute("SELECT * FROM customs_items WHERE declaration_id = ?", (declaration['id'],))
        items = [dict(row) for row in cursor.fetchall()]
        
        # 获取状态日志
        cursor.execute("SELECT * FROM customs_status_logs WHERE declaration_id = ? ORDER BY operated_at DESC", (declaration['id'],))
        logs = [dict(row) for row in cursor.fetchall()]
        
        # 获取AI分析
        cursor.execute("SELECT * FROM customs_ai_analysis WHERE declaration_id = ? ORDER BY analyzed_at DESC", (declaration['id'],))
        ai_analysis = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        result = dict(declaration)
        result['items'] = items
        result['logs'] = logs
        result['ai_analysis'] = ai_analysis
        
        return jsonify({'success': True, 'data': result})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@customs_api.route('/api/customs/declarations', methods=['POST'])
def create_declaration():
    """创建报关单"""
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO customs_declarations (
                declaration_no, declaration_type, trade_mode, customs_code,
                declarant_code, declarant_name, consignee_code, consignee_name,
                notify_party, port_of_entry, port_of_destination,
                country_of_origin, country_of_destination, transport_mode,
                vessel_name, voyage_no, bill_of_lading_no, packing_type,
                total_packages, gross_weight, net_weight, measure,
                currency_code, total_amount, exchange_rate, customs_value,
                tax_amount, duty_amount, status, declared_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('declaration_no'),
            data.get('declaration_type'),
            data.get('trade_mode'),
            data.get('customs_code'),
            data.get('declarant_code'),
            data.get('declarant_name'),
            data.get('consignee_code'),
            data.get('consignee_name'),
            data.get('notify_party'),
            data.get('port_of_entry'),
            data.get('port_of_destination'),
            data.get('country_of_origin'),
            data.get('country_of_destination'),
            data.get('transport_mode'),
            data.get('vessel_name'),
            data.get('voyage_no'),
            data.get('bill_of_lading_no'),
            data.get('packing_type'),
            data.get('total_packages'),
            data.get('gross_weight'),
            data.get('net_weight'),
            data.get('measure'),
            data.get('currency_code'),
            data.get('total_amount'),
            data.get('exchange_rate'),
            data.get('customs_value'),
            data.get('tax_amount'),
            data.get('duty_amount'),
            data.get('status', 'pending'),
            data.get('declared_at')
        ))
        
        declaration_id = cursor.lastrowid
        
        # 插入商品明细
        if 'items' in data:
            for idx, item in enumerate(data['items'], 1):
                cursor.execute("""
                    INSERT INTO customs_items (
                        declaration_id, item_no, hs_code, goods_name,
                        goods_description, quantity, unit, unit_price,
                        total_price, currency_code, country_of_origin,
                        brand, model, specification, customs_tariff, tax_rate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    declaration_id, idx, item.get('hs_code'), item.get('goods_name'),
                    item.get('goods_description'), item.get('quantity'), item.get('unit'),
                    item.get('unit_price'), item.get('total_price'), item.get('currency_code'),
                    item.get('country_of_origin'), item.get('brand'), item.get('model'),
                    item.get('specification'), item.get('customs_tariff'), item.get('tax_rate')
                ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '报关单创建成功', 'id': declaration_id}), 201
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@customs_api.route('/api/customs/declarations/<declaration_no>/status', methods=['PUT'])
def update_status(declaration_no):
    """更新报关单状态"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        reason = data.get('reason', '')
        operated_by = data.get('operated_by', 'system')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取当前状态
        cursor.execute("SELECT id, status FROM customs_declarations WHERE declaration_no = ?", (declaration_no,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'success': False, 'message': '报关单不存在'}), 404
        
        declaration_id = row['id']
        previous_status = row['status']
        
        # 更新状态
        cursor.execute("UPDATE customs_declarations SET status = ? WHERE declaration_no = ?", (new_status, declaration_no))
        
        # 记录状态变更日志
        cursor.execute("""
            INSERT INTO customs_status_logs (declaration_id, previous_status, current_status, status_reason, operated_by)
            VALUES (?, ?, ?, ?, ?)
        """, (declaration_id, previous_status, new_status, reason, operated_by))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'状态已更新为 {new_status}'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@customs_api.route('/api/customs/statistics', methods=['GET'])
def get_statistics():
    """获取报关统计数据(供AI分析使用)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 总数统计
        cursor.execute("SELECT COUNT(*) FROM customs_declarations")
        total = cursor.fetchone()[0]
        
        # 状态分布
        cursor.execute("SELECT status, COUNT(*) FROM customs_declarations GROUP BY status")
        status_dist = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 贸易方式分布
        cursor.execute("SELECT trade_mode, COUNT(*) FROM customs_declarations GROUP BY trade_mode")
        trade_mode_dist = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 来源国分布
        cursor.execute("SELECT country_of_origin, COUNT(*) FROM customs_declarations GROUP BY country_of_origin")
        country_dist = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 商品统计
        cursor.execute("SELECT COUNT(*) FROM customs_items")
        total_items = cursor.fetchone()[0]
        
        # 金额统计
        cursor.execute("SELECT SUM(total_amount) FROM customs_declarations")
        total_amount = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'total_declarations': total,
                'total_items': total_items,
                'total_amount': total_amount,
                'status_distribution': status_dist,
                'trade_mode_distribution': trade_mode_dist,
                'country_distribution': country_dist
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@customs_api.route('/api/customs/ai/analyze/<declaration_no>', methods=['POST'])
def ai_analyze(declaration_no):
    """AI分析报关单"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取报关单信息
        cursor.execute("SELECT * FROM customs_declarations WHERE declaration_no = ?", (declaration_no,))
        declaration = cursor.fetchone()
        
        if not declaration:
            return jsonify({'success': False, 'message': '报关单不存在'}), 404
        
        # 模拟AI分析
        analysis_data = {
            'risk_score': round(30 + (declaration['total_amount'] / 10000), 2),
            'suggestions': [
                '检查商品归类是否正确',
                '确认原产地证明文件',
                '核实申报价值是否合理'
            ],
            'compliance_check': {
                'hs_code_valid': True,
                'document_complete': True,
                'tax_calculation': 'pending'
            }
        }
        
        # 保存分析结果
        cursor.execute("""
            INSERT INTO customs_ai_analysis (declaration_id, analysis_type, analysis_data, confidence_score, recommendations)
            VALUES (?, ?, ?, ?, ?)
        """, (
            declaration['id'],
            'risk_assessment',
            json.dumps(analysis_data),
            0.85,
            json.dumps(analysis_data['suggestions'])
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'AI分析完成',
            'data': analysis_data,
            'confidence': 0.85
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
