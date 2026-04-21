"""
应用配置模块

集中管理所有配置项，包括文件大小限制、路径、支持的格式等。
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UPLOAD_DIR = os.path.join(BASE_DIR, 'temp', 'uploads')
OUTPUT_DIR = os.path.join(BASE_DIR, 'temp', 'output')

MAX_UPLOAD_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
MAX_MULTIPLIER = 10.0
MIN_MULTIPLIER = 1.1

SUPPORTED_EXTENSIONS = {'.xlsx', '.docx', '.pptx', '.pdf', '.doc', '.ppt'}

SAFE_EXPANDABLE_EXTENSIONS = {'.xlsx', '.docx', '.pptx', '.pdf'}

UNSUPPORTED_BINARY_EXTENSIONS = {'.doc', '.ppt'}

FILE_SIGNATURES = {
    'xlsx': b'PK\x03\x04',
    'docx': b'PK\x03\x04',
    'pptx': b'PK\x03\x04',
    'pdf': b'%PDF',
    'doc': b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',
    'ppt': b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',
}

OOXML_CONTENT_TYPES = {
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}

MULTIPLIER_TOLERANCE = 0.05  # 允许 5% 的倍数偏差

CUSTOM_XML_NAMESPACE = 'http://fileexpander.tool/custom-metadata'
CUSTOM_PROPERTY_PREFIX = '_expand_padding_'

METADATA_CHUNK_SIZE = 1024 * 64  # 64KB 每个元数据块

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'
