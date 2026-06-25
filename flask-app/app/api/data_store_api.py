#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)
from flask import Blueprint, jsonify, request
import sqlite3
import os
import json

data_store_bp = Blueprint("data_store", __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mtscos.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@data_store_bp.route("/api/data/store/list", methods=["GET"])
def list_data():
    conn = get_db()
    cursor = conn.cursor()
    category = request.args.get("category")
    if category:
        cursor.execute("SELECT * FROM json_data_store WHERE data_category = ? ORDER BY created_at DESC", (category,))
    else:
        cursor.execute("SELECT * FROM json_data_store ORDER BY created_at DESC LIMIT 100")
    results = cursor.fetchall()
    conn.close()
    return jsonify({"status": "success", "data": [dict(row) for row in results]})

@data_store_bp.route("/api/data/store/get", methods=["GET"])
def get_data():
    file_name = request.args.get("file_name")
    if not file_name:
        return jsonify({"status": "error", "message": "file_name参数必填"}), 400
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM json_data_store WHERE file_name = ?", (file_name,))
    result = cursor.fetchone()
    if result:
        cursor.execute("INSERT INTO data_access_log (api_endpoint, data_category, file_name) VALUES (?, ?, ?)", 
                      ("/api/data/store/get", result["data_category"], file_name))
        conn.commit()
        try:
            content = json.loads(result["content"])
        except Exception:
            content = result["content"]
        conn.close()
        return jsonify({
            "status": "success", 
            "data": content, 
            "metadata": {
                "file_name": result["file_name"], 
                "data_category": result["data_category"], 
                "created_at": result["created_at"]
            }
        })
    else:
        conn.close()
        return jsonify({"status": "error", "message": "数据不存在"}), 404

@data_store_bp.route("/api/data/store/categories", methods=["GET"])
def get_categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT data_category, COUNT(*) as count FROM json_data_store GROUP BY data_category")
    results = cursor.fetchall()
    conn.close()
    return jsonify({"status": "success", "data": [dict(row) for row in results]})

@data_store_bp.route("/api/data/store/search", methods=["GET"])
def search_data():
    keyword = request.args.get("keyword")
    if not keyword:
        return jsonify({"status": "error", "message": "keyword参数必填"}), 400
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM json_data_store WHERE file_name LIKE ? OR content LIKE ? OR data_category LIKE ? ORDER BY created_at DESC LIMIT 50", 
                  (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    results = cursor.fetchall()
    conn.close()
    return jsonify({"status": "success", "data": [dict(row) for row in results]})

@data_store_bp.route("/api/data/store/count", methods=["GET"])
def get_count():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM json_data_store")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT data_category, COUNT(*) as count FROM json_data_store GROUP BY data_category")
    categories = cursor.fetchall()
    conn.close()
    return jsonify({"status": "success", "data": {"total": total, "categories": [dict(row) for row in categories]}})
