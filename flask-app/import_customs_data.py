# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""报关数据导入工具 - 支持JSON数据上传并适配系统"""
import os
import sys
import json
import sqlite3
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class CustomsDataImporter:
    def __init__(self, db_path='app.db'):
        self.db_path = db_path
        self.conn = None
        self.import_log = []
    
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def create_tables(self):
        """创建报关相关数据表"""
        cursor = self.conn.cursor()
        
        # 报关主表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customs_declarations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                declaration_no TEXT UNIQUE NOT NULL,
                declaration_type TEXT,
                trade_mode TEXT,
                customs_code TEXT,
                declarant_code TEXT,
                declarant_name TEXT,
                consignee_code TEXT,
                consignee_name TEXT,
                notify_party TEXT,
                port_of_entry TEXT,
                port_of_destination TEXT,
                country_of_origin TEXT,
                country_of_destination TEXT,
                transport_mode TEXT,
                vessel_name TEXT,
                voyage_no TEXT,
                bill_of_lading_no TEXT,
                packing_type TEXT,
                total_packages INTEGER,
                gross_weight REAL,
                net_weight REAL,
                measure TEXT,
                currency_code TEXT,
                total_amount REAL,
                exchange_rate REAL,
                customs_value REAL,
                tax_amount REAL,
                duty_amount REAL,
                status TEXT DEFAULT 'pending',
                declared_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 报关商品明细表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customs_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                declaration_id INTEGER,
                item_no INTEGER,
                hs_code TEXT,
                goods_name TEXT,
                goods_description TEXT,
                quantity REAL,
                unit TEXT,
                unit_price REAL,
                total_price REAL,
                currency_code TEXT,
                country_of_origin TEXT,
                brand TEXT,
                model TEXT,
                specification TEXT,
                customs_tariff REAL,
                tax_rate REAL,
                FOREIGN KEY (declaration_id) REFERENCES customs_declarations(id) ON DELETE CASCADE
            )
        """)
        
        # 报关附件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customs_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                declaration_id INTEGER,
                attachment_name TEXT,
                attachment_path TEXT,
                attachment_type TEXT,
                file_size INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (declaration_id) REFERENCES customs_declarations(id) ON DELETE CASCADE
            )
        """)
        
        # 报关状态日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customs_status_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                declaration_id INTEGER,
                previous_status TEXT,
                current_status TEXT,
                status_reason TEXT,
                operated_by TEXT,
                operated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (declaration_id) REFERENCES customs_declarations(id) ON DELETE CASCADE
            )
        """)
        
        # AI分析数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customs_ai_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                declaration_id INTEGER,
                analysis_type TEXT,
                analysis_data TEXT,
                confidence_score REAL,
                recommendations TEXT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (declaration_id) REFERENCES customs_declarations(id) ON DELETE CASCADE
            )
        """)
        
        self.conn.commit()
        print("✅ 创建报关数据表完成")
    
    def import_json_data(self, json_data):
        """导入JSON数据"""
        try:
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
            
            cursor = self.conn.cursor()
            imported_count = 0
            
            # 导入报关数据
            if 'declarations' in data:
                for declaration in data['declarations']:
                    # 检查是否已存在
                    cursor.execute("SELECT id FROM customs_declarations WHERE declaration_no = ?", 
                                (declaration.get('declaration_no'),))
                    if cursor.fetchone():
                        print(f"⚠️ 报关单 {declaration.get('declaration_no')} 已存在,跳过")
                        continue
                    
                    # 插入报关主表
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
                        declaration.get('declaration_no'),
                        declaration.get('declaration_type'),
                        declaration.get('trade_mode'),
                        declaration.get('customs_code'),
                        declaration.get('declarant_code'),
                        declaration.get('declarant_name'),
                        declaration.get('consignee_code'),
                        declaration.get('consignee_name'),
                        declaration.get('notify_party'),
                        declaration.get('port_of_entry'),
                        declaration.get('port_of_destination'),
                        declaration.get('country_of_origin'),
                        declaration.get('country_of_destination'),
                        declaration.get('transport_mode'),
                        declaration.get('vessel_name'),
                        declaration.get('voyage_no'),
                        declaration.get('bill_of_lading_no'),
                        declaration.get('packing_type'),
                        declaration.get('total_packages'),
                        declaration.get('gross_weight'),
                        declaration.get('net_weight'),
                        declaration.get('measure'),
                        declaration.get('currency_code'),
                        declaration.get('total_amount'),
                        declaration.get('exchange_rate'),
                        declaration.get('customs_value'),
                        declaration.get('tax_amount'),
                        declaration.get('duty_amount'),
                        declaration.get('status', 'pending'),
                        declaration.get('declared_at')
                    ))
                    
                    declaration_id = cursor.lastrowid
                    
                    # 导入商品明细
                    if 'items' in declaration:
                        for idx, item in enumerate(declaration['items'], 1):
                            cursor.execute("""
                                INSERT INTO customs_items (
                                    declaration_id, item_no, hs_code, goods_name,
                                    goods_description, quantity, unit, unit_price,
                                    total_price, currency_code, country_of_origin,
                                    brand, model, specification, customs_tariff, tax_rate
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                declaration_id,
                                idx,
                                item.get('hs_code'),
                                item.get('goods_name'),
                                item.get('goods_description'),
                                item.get('quantity'),
                                item.get('unit'),
                                item.get('unit_price'),
                                item.get('total_price'),
                                item.get('currency_code'),
                                item.get('country_of_origin'),
                                item.get('brand'),
                                item.get('model'),
                                item.get('specification'),
                                item.get('customs_tariff'),
                                item.get('tax_rate')
                            ))
                    
                    imported_count += 1
                    print(f"✅ 成功导入报关单: {declaration.get('declaration_no')}")
            
            self.conn.commit()
            print(f"\n🎉 导入完成!共导入 {imported_count} 条报关数据")
            return imported_count
            
        except Exception as e:
            print(f"❌ 导入失败: {str(e)}")
            return 0
    
    def get_statistics(self):
        """获取报关数据统计"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM customs_declarations")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT status, COUNT(*) FROM customs_declarations GROUP BY status")
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute("SELECT COUNT(*) FROM customs_items")
        items_count = cursor.fetchone()[0]
        
        return {
            'total_declarations': total,
            'status_distribution': status_counts,
            'total_items': items_count
        }
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()

def main():
    """主函数"""
    importer = CustomsDataImporter()
    importer.connect()
    
    # 创建表
    importer.create_tables()
    
    # 示例报关数据
    sample_data = {
        "declarations": [
            {
                "declaration_no": "C20240512001",
                "declaration_type": "一般贸易",
                "trade_mode": "一般贸易",
                "customs_code": "3100",
                "declarant_code": "SH123456789",
                "declarant_name": "上海进出口贸易有限公司",
                "consignee_code": "BJ987654321",
                "consignee_name": "北京国际贸易有限公司",
                "notify_party": "北京国际贸易有限公司",
                "port_of_entry": "上海浦东海关",
                "port_of_destination": "北京朝阳海关",
                "country_of_origin": "JP",
                "country_of_destination": "CN",
                "transport_mode": "海运",
                "vessel_name": "MAERSK HUB",
                "voyage_no": "V.2024-0512",
                "bill_of_lading_no": "MAEU20240512001",
                "packing_type": "纸箱",
                "total_packages": 100,
                "gross_weight": 2500.0,
                "net_weight": 2200.0,
                "measure": "60x40x50",
                "currency_code": "USD",
                "total_amount": 50000.0,
                "exchange_rate": 7.24,
                "customs_value": 50000.0,
                "tax_amount": 6500.0,
                "duty_amount": 2500.0,
                "status": "pending",
                "declared_at": "2024-05-12 10:30:00",
                "items": [
                    {
                        "hs_code": "85235110",
                        "goods_name": "固态硬盘",
                        "goods_description": "SSD 1TB SATA3",
                        "quantity": 100,
                        "unit": "个",
                        "unit_price": 500.0,
                        "total_price": 50000.0,
                        "currency_code": "USD",
                        "country_of_origin": "JP",
                        "brand": "Samsung",
                        "model": "870 EVO",
                        "specification": "1TB, 2.5英寸",
                        "customs_tariff": 0.13,
                        "tax_rate": 0.13
                    }
                ]
            },
            {
                "declaration_no": "C20240512002",
                "declaration_type": "加工贸易",
                "trade_mode": "进料加工",
                "customs_code": "3100",
                "declarant_code": "SZ112233445",
                "declarant_name": "深圳电子科技有限公司",
                "consignee_code": "SZ112233445",
                "consignee_name": "深圳电子科技有限公司",
                "notify_party": "深圳电子科技有限公司",
                "port_of_entry": "深圳蛇口海关",
                "port_of_destination": "深圳蛇口海关",
                "country_of_origin": "KR",
                "country_of_destination": "CN",
                "transport_mode": "海运",
                "vessel_name": "HYUNDAI ACE",
                "voyage_no": "V.2024-0510",
                "bill_of_lading_no": "HDMU20240510002",
                "packing_type": "木箱",
                "total_packages": 50,
                "gross_weight": 5000.0,
                "net_weight": 4800.0,
                "measure": "120x80x60",
                "currency_code": "USD",
                "total_amount": 120000.0,
                "exchange_rate": 7.24,
                "customs_value": 120000.0,
                "tax_amount": 15600.0,
                "duty_amount": 6000.0,
                "status": "approved",
                "declared_at": "2024-05-10 14:20:00",
                "items": [
                    {
                        "hs_code": "85258013",
                        "goods_name": "手机主板",
                        "goods_description": "智能手机主板组件",
                        "quantity": 500,
                        "unit": "块",
                        "unit_price": 240.0,
                        "total_price": 120000.0,
                        "currency_code": "USD",
                        "country_of_origin": "KR",
                        "brand": "Samsung",
                        "model": "SM-A546B",
                        "specification": "5G, 8GB+256GB",
                        "customs_tariff": 0.05,
                        "tax_rate": 0.13
                    }
                ]
            }
        ]
    }
    
    # 导入示例数据
    print("📥 开始导入报关数据...")
    count = importer.import_json_data(sample_data)
    
    # 显示统计信息
    stats = importer.get_statistics()
    print("\n📊 报关数据统计:")
    print(f"  报关单总数: {stats['total_declarations']}")
    print(f"  商品明细总数: {stats['total_items']}")
    print(f"  状态分布: {stats['status_distribution']}")
    
    importer.close()

if __name__ == '__main__':
    main()
