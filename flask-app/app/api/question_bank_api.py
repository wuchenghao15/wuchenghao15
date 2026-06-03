# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
import json

question_bank_api = Blueprint('question_bank_api', __name__)

@question_bank_api.route('/')
def index():
    return jsonify({'status': 'ok', 'question_bank': 'ready'})

@question_bank_api.route('/questions')
def questions():
    return jsonify({'questions': []})
