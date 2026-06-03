# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
import json

exam_test_api = Blueprint('exam_test_api', __name__)

@exam_test_api.route('/')
def index():
    return jsonify({'status': 'ok', 'exam': 'ready'})

@exam_test_api.route('/test')
def test():
    return jsonify({'result': 'passed'})
