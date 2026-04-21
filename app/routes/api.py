"""
API 路由模块

处理文件上传、膨胀请求和下载响应。
"""
import os
import logging

from flask import Blueprint, request, jsonify, send_file, current_app

from app.services.expand_service import ExpandService
from app.utils.file_utils import (
    sanitize_filename, get_safe_upload_path, validate_extension,
    ensure_directories, cleanup_file
)
from app.config import MAX_UPLOAD_SIZE_BYTES, SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

expand_service = ExpandService()


@api_bp.route('/upload', methods=['POST'])
def upload_and_expand():
    """
    处理文件上传和膨胀请求。

    请求参数:
    - file: 上传的文件 (multipart/form-data)
    - multiplier: 目标倍数 (form field)

    返回:
    - JSON 响应，包含处理结果或错误信息
    """
    upload_path = None

    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '未找到上传文件'}), 400

        file = request.files['file']
        if file.filename == '' or file.filename is None:
            return jsonify({'success': False, 'error': '未选择文件'}), 400

        multiplier = request.form.get('multiplier')
        if not multiplier:
            return jsonify({'success': False, 'error': '未指定目标倍数'}), 400

        original_filename = sanitize_filename(file.filename)

        valid_ext, ext = validate_extension(original_filename)
        if not valid_ext:
            supported = ', '.join(sorted(SUPPORTED_EXTENSIONS))
            return jsonify({
                'success': False,
                'error': f'不支持的文件类型: {ext}。支持的格式: {supported}'
            }), 400

        ensure_directories()
        upload_path = get_safe_upload_path(original_filename)
        file.save(upload_path)

        logger.info(
            "接收上传: filename=%s, size=%d, multiplier=%s",
            original_filename, os.path.getsize(upload_path), multiplier
        )

        result = expand_service.process(upload_path, original_filename, multiplier)

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error("上传处理异常: %s", e, exc_info=True)
        return jsonify({
            'success': False,
            'error': '服务器处理请求时发生错误'
        }), 500

    finally:
        if upload_path:
            cleanup_file(upload_path)


@api_bp.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    下载处理后的文件。

    Args:
        filename: 输出文件名

    返回:
    - 文件下载响应
    """
    try:
        safe_filename = sanitize_filename(filename)
        from app.config import OUTPUT_DIR
        filepath = os.path.join(OUTPUT_DIR, safe_filename)

        real_path = os.path.realpath(filepath)
        real_output_dir = os.path.realpath(OUTPUT_DIR)

        if not real_path.startswith(real_output_dir):
            return jsonify({'success': False, 'error': '非法的文件路径'}), 403

        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': '文件不存在或已过期'}), 404

        return send_file(
            filepath,
            as_attachment=True,
            download_name=safe_filename
        )

    except Exception as e:
        logger.error("下载异常: %s", e, exc_info=True)
        return jsonify({'success': False, 'error': '下载失败'}), 500


@api_bp.route('/supported-formats', methods=['GET'])
def get_supported_formats():
    """返回支持的文件格式列表。"""
    from app.services.processor_registry import get_all_processors
    processors = get_all_processors()
    formats = []
    for ext, processor in processors.items():
        formats.append({
            'extension': ext,
            'description': processor.strategy_description,
            'expandable': ext not in {'.doc', '.ppt'},
        })
    return jsonify({'formats': formats})
