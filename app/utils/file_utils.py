"""
文件工具模块

提供安全的文件名清洗、路径验证、文件签名检测等通用文件操作。
"""
import os
import re
import uuid
import logging

from app.config import (
    FILE_SIGNATURES, UPLOAD_DIR, OUTPUT_DIR,
    SUPPORTED_EXTENSIONS
)

logger = logging.getLogger(__name__)

_UNSAFE_FILENAME_PATTERN = re.compile(r'[^\w\u4e00-\u9fff\-_. ()（）]')


def sanitize_filename(filename):
    """
    清洗文件名，移除路径分隔符和不安全字符。

    Args:
        filename: 原始文件名

    Returns:
        清洗后的安全文件名
    """
    filename = os.path.basename(filename)
    name, ext = os.path.splitext(filename)
    name = _UNSAFE_FILENAME_PATTERN.sub('_', name)
    if not name:
        name = 'unnamed'
    return f"{name}{ext}"


def generate_unique_filename(original_filename, multiplier):
    """
    生成带有处理标记的唯一输出文件名。

    Args:
        original_filename: 原始文件名
        multiplier: 目标倍数

    Returns:
        唯一的输出文件名，格式为 原名_expanded_Nx_uuid.ext
    """
    name, ext = os.path.splitext(sanitize_filename(original_filename))
    short_id = uuid.uuid4().hex[:8]
    multiplier_str = f"{multiplier}x" if multiplier == int(multiplier) else f"{multiplier}x"
    return f"{name}_expanded_{multiplier_str}_{short_id}{ext}"


def get_safe_upload_path(filename):
    """
    获取安全的上传文件保存路径，防止路径穿越。

    Args:
        filename: 清洗后的文件名

    Returns:
        安全的绝对上传路径
    """
    safe_name = sanitize_filename(filename)
    path = os.path.join(UPLOAD_DIR, safe_name)
    real_path = os.path.realpath(path)
    real_upload_dir = os.path.realpath(UPLOAD_DIR)
    if not real_path.startswith(real_upload_dir):
        raise ValueError("检测到路径穿越尝试")
    return real_path


def get_safe_output_path(filename):
    """
    获取安全的输出文件保存路径，防止路径穿越。

    Args:
        filename: 清洗后的文件名

    Returns:
        安全的绝对输出路径
    """
    safe_name = sanitize_filename(filename)
    path = os.path.join(OUTPUT_DIR, safe_name)
    real_path = os.path.realpath(path)
    real_output_dir = os.path.realpath(OUTPUT_DIR)
    if not real_path.startswith(real_output_dir):
        raise ValueError("检测到路径穿越尝试")
    return real_path


def detect_file_type_by_signature(filepath):
    """
    通过文件签名（魔数）检测文件的真实类型。

    Args:
        filepath: 文件路径

    Returns:
        检测到的文件扩展名（如 '.pdf'），或 None
    """
    try:
        with open(filepath, 'rb') as f:
            header = f.read(16)
    except IOError:
        logger.error("无法读取文件签名: %s", filepath)
        return None

    if header.startswith(b'%PDF'):
        return '.pdf'
    if header.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        return '.ole'  # OLE 复合文档 (doc/ppt/xls)
    if header.startswith(b'PK\x03\x04'):
        return '.zip'  # OOXML 容器 (xlsx/docx/pptx)
    return None


def validate_extension(filename):
    """
    检查文件扩展名是否在支持列表中。

    Args:
        filename: 文件名

    Returns:
        (bool, str) - (是否有效, 小写扩展名)
    """
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    return ext in SUPPORTED_EXTENSIONS, ext


def ensure_directories():
    """确保上传和输出目录存在。"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def cleanup_file(filepath):
    """
    安全删除临时文件。

    Args:
        filepath: 要删除的文件路径
    """
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            logger.debug("已清理临时文件: %s", filepath)
    except OSError as e:
        logger.warning("清理文件失败 %s: %s", filepath, e)


def get_file_size(filepath):
    """
    获取文件大小（字节）。

    Args:
        filepath: 文件路径

    Returns:
        文件大小（字节），文件不存在时返回 0
    """
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0
