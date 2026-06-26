# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, jsonify, request, session
import sqlite3
import os

exam_system_bp = Blueprint('exam_system', __name__)

@exam_system_bp.route('/exam_system')
def exam_system_index():
    return render_template('exam_system.html')

@exam_system_bp.route('/exam_center')
def exam_center():
    return render_template('exam_center.html')

@exam_system_bp.route('/exam_page/<int:exam_id>')
def exam_page(exam_id):
    return render_template('exam_page.html')
