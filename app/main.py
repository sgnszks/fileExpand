"""
Flask 应用工厂

创建并配置 Flask 应用实例，注册蓝图，设置日志。
"""
import os
import logging

from flask import Flask, render_template

from app.config import LOG_FORMAT, LOG_LEVEL, MAX_UPLOAD_SIZE_BYTES


def create_app():
    """
    创建并配置 Flask 应用。

    Returns:
        Flask: 配置完成的应用实例
    """
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
    )

    app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE_BYTES

    _setup_logging()

    from app.routes.api import api_bp
    app.register_blueprint(api_bp)

    @app.route('/')
    def index():
        """渲染主页面。"""
        return render_template('index.html')

    @app.errorhandler(413)
    def too_large(e):
        """处理文件过大错误。"""
        from flask import jsonify
        size_mb = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        return jsonify({
            'success': False,
            'error': f'文件大小超过限制（最大 {size_mb:.0f}MB）'
        }), 413

    return app


def _setup_logging():
    """配置应用日志。"""
    logging.basicConfig(
        format=LOG_FORMAT,
        level=getattr(logging, LOG_LEVEL, logging.INFO),
    )
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
