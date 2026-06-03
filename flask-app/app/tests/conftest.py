# -*- coding: utf-8 -*-
import pytest
from app import app
from app.models.user import User

@pytest.fixture(scope='session')
def app_fixture():
    """创建测试应用实例"""
    app.config.update({
        'TESTING': True,
        'DATABASE_PATH': 'test.db'
    })
    yield app

@pytest.fixture
def client(app_fixture):
    """创建测试客户端"""
    with app_fixture.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def setup_database():
    """设置测试数据库"""
    # 创建表
    User.create_table()
    yield
    # 清理数据库(如果需要)
