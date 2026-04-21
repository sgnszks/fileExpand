"""
处理器注册表

维护文件扩展名到对应处理器的映射，
提供统一的处理器获取接口。
"""
import logging

from app.processors.xlsx_processor import XlsxProcessor
from app.processors.docx_processor import DocxProcessor
from app.processors.pptx_processor import PptxProcessor
from app.processors.pdf_processor import PdfProcessor
from app.processors.binary_processor import BinaryOfficeProcessor

logger = logging.getLogger(__name__)

_PROCESSOR_MAP = {}


def _register_defaults():
    """注册默认的文件处理器。"""
    processors = [
        XlsxProcessor(),
        DocxProcessor(),
        PptxProcessor(),
        PdfProcessor(),
        BinaryOfficeProcessor(),
    ]
    for processor in processors:
        for ext in processor.supported_extensions:
            _PROCESSOR_MAP[ext] = processor
            logger.debug("注册处理器: %s -> %s", ext, processor.__class__.__name__)


def get_processor(extension):
    """
    根据文件扩展名获取对应的处理器。

    Args:
        extension: 文件扩展名（含点号，如 '.xlsx'）

    Returns:
        BaseProcessor | None: 对应的处理器实例，或 None
    """
    if not _PROCESSOR_MAP:
        _register_defaults()
    return _PROCESSOR_MAP.get(extension.lower())


def get_all_processors():
    """
    获取所有已注册的处理器。

    Returns:
        dict: 扩展名到处理器的映射
    """
    if not _PROCESSOR_MAP:
        _register_defaults()
    return dict(_PROCESSOR_MAP)
