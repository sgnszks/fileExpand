"""
文件类型识别服务

结合文件扩展名和文件签名（魔数）进行双重验证，
确保文件的声称类型与实际类型一致。
"""
import os
import zipfile
import logging

from app.config import (
    SUPPORTED_EXTENSIONS, SAFE_EXPANDABLE_EXTENSIONS,
    UNSUPPORTED_BINARY_EXTENSIONS, OOXML_CONTENT_TYPES
)
from app.utils.file_utils import detect_file_type_by_signature

logger = logging.getLogger(__name__)


class FileTypeService:
    """文件类型识别与验证服务。"""

    @staticmethod
    def identify(filepath, claimed_extension):
        """
        识别并验证文件的真实类型。

        同时检查文件扩展名和文件签名，拒绝扩展名与签名不匹配的文件。

        Args:
            filepath: 文件的完整路径
            claimed_extension: 用户声称的文件扩展名（含点号，如 '.xlsx'）

        Returns:
            dict: {
                'valid': bool,
                'extension': str,        # 最终确认的扩展名
                'format_family': str,     # 'ooxml' | 'ole' | 'pdf'
                'expandable': bool,       # 是否支持安全膨胀
                'error': str | None       # 错误信息
            }
        """
        claimed_ext = claimed_extension.lower()

        if claimed_ext not in SUPPORTED_EXTENSIONS:
            return {
                'valid': False,
                'extension': claimed_ext,
                'format_family': None,
                'expandable': False,
                'error': f'不支持的文件类型: {claimed_ext}'
            }

        detected_sig = detect_file_type_by_signature(filepath)

        if detected_sig is None:
            return {
                'valid': False,
                'extension': claimed_ext,
                'format_family': None,
                'expandable': False,
                'error': '无法识别文件签名，文件可能已损坏或为空'
            }

        valid, format_family, error = FileTypeService._cross_validate(
            claimed_ext, detected_sig, filepath
        )

        if not valid:
            return {
                'valid': False,
                'extension': claimed_ext,
                'format_family': format_family,
                'expandable': False,
                'error': error
            }

        expandable = claimed_ext in SAFE_EXPANDABLE_EXTENSIONS

        logger.info(
            "文件类型识别完成: extension=%s, family=%s, expandable=%s",
            claimed_ext, format_family, expandable
        )

        return {
            'valid': True,
            'extension': claimed_ext,
            'format_family': format_family,
            'expandable': expandable,
            'error': None
        }

    @staticmethod
    def _cross_validate(claimed_ext, detected_sig, filepath):
        """
        交叉验证扩展名与文件签名。

        Args:
            claimed_ext: 声称的扩展名
            detected_sig: 检测到的签名类型
            filepath: 文件路径

        Returns:
            (bool, str, str | None) - (是否有效, 格式族, 错误信息)
        """
        if claimed_ext in {'.xlsx', '.docx', '.pptx'}:
            if detected_sig != '.zip':
                return (
                    False, None,
                    f'文件扩展名为 {claimed_ext}，但文件签名不是 OOXML/ZIP 格式'
                )
            ooxml_type = FileTypeService._detect_ooxml_subtype(filepath)
            expected = claimed_ext[1:]  # 去掉点号
            if ooxml_type and ooxml_type != expected:
                return (
                    False, 'ooxml',
                    f'文件扩展名为 {claimed_ext}，但内部内容类型为 {ooxml_type}'
                )
            return (True, 'ooxml', None)

        if claimed_ext in {'.doc', '.ppt'}:
            if detected_sig != '.ole':
                return (
                    False, None,
                    f'文件扩展名为 {claimed_ext}，但文件签名不是 OLE 复合文档格式'
                )
            return (True, 'ole', None)

        if claimed_ext == '.pdf':
            if detected_sig != '.pdf':
                return (
                    False, None,
                    f'文件扩展名为 .pdf，但文件签名不匹配 PDF 格式'
                )
            return (True, 'pdf', None)

        return (False, None, f'未知的文件类型: {claimed_ext}')

    @staticmethod
    def _detect_ooxml_subtype(filepath):
        """
        通过检查 OOXML ZIP 包内的 [Content_Types].xml 来确定具体子类型。

        Args:
            filepath: OOXML 文件路径

        Returns:
            str | None: 'xlsx', 'docx', 'pptx', 或 None
        """
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                if '[Content_Types].xml' not in zf.namelist():
                    return None
                content_types = zf.read('[Content_Types].xml').decode('utf-8')
                for ext, content_type in OOXML_CONTENT_TYPES.items():
                    if content_type in content_types:
                        return ext
        except (zipfile.BadZipFile, KeyError, UnicodeDecodeError) as e:
            logger.warning("OOXML 子类型检测失败: %s", e)
        return None
