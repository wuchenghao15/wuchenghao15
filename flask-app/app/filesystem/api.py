# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
import json
import sys

filesystem_bp = Blueprint('filesystem', __name__, url_prefix='/api/filesystem')

@filesystem_bp.route('/files')
def list_files():
    """列出文件"""
    return jsonify({'files': []})

@filesystem_bp.route('/directories')
def list_dirs():
    """列出目录"""
    return jsonify({'directories': []})
