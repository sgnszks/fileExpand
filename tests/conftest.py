"""
测试配置与公共 fixtures

提供 Flask 测试客户端和临时测试文件生成器。
"""
import os
import shutil
import tempfile

import pytest

from app.config import UPLOAD_DIR, OUTPUT_DIR


@pytest.fixture
def app():
    """创建测试用 Flask 应用。"""
    from app.main import create_app
    application = create_app()
    application.config['TESTING'] = True
    yield application


@pytest.fixture
def client(app):
    """创建测试客户端。"""
    return app.test_client()


@pytest.fixture(autouse=True)
def setup_dirs():
    """确保上传和输出目录存在，测试后清理。"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    yield
    for f in os.listdir(OUTPUT_DIR):
        try:
            os.remove(os.path.join(OUTPUT_DIR, f))
        except OSError:
            pass


@pytest.fixture
def temp_dir():
    """提供一个临时目录，测试后自动清理。"""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)
