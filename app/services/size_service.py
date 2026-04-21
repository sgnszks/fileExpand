"""
体积计算与策略选择服务

负责计算目标体积、评估可达性、选择最佳膨胀策略。
"""
import logging

from app.config import (
    MAX_MULTIPLIER, MIN_MULTIPLIER, MULTIPLIER_TOLERANCE,
    SAFE_EXPANDABLE_EXTENSIONS, UNSUPPORTED_BINARY_EXTENSIONS
)

logger = logging.getLogger(__name__)

STRATEGY_CUSTOM_XML = 'custom_xml_metadata'
STRATEGY_REPACK_LOW_COMPRESSION = 'repack_low_compression'
STRATEGY_COMBINED = 'combined_metadata_and_repack'
STRATEGY_PDF_METADATA = 'pdf_metadata_stream'
STRATEGY_UNSUPPORTED = 'unsupported'


class SizeService:
    """体积计算与策略选择服务。"""

    @staticmethod
    def validate_multiplier(multiplier):
        """
        验证用户输入的目标倍数是否合法。

        Args:
            multiplier: 用户输入的倍数值

        Returns:
            (bool, str | None) - (是否合法, 错误信息)
        """
        try:
            m = float(multiplier)
        except (TypeError, ValueError):
            return False, f'倍数必须是有效数字，收到: {multiplier}'

        if m < MIN_MULTIPLIER:
            return False, f'倍数不能小于 {MIN_MULTIPLIER}'
        if m > MAX_MULTIPLIER:
            return False, f'倍数不能大于 {MAX_MULTIPLIER}，当前输入: {m}'

        return True, None

    @staticmethod
    def calculate_target_size(original_size, multiplier):
        """
        计算目标文件体积。

        Args:
            original_size: 原始文件大小（字节）
            multiplier: 目标倍数

        Returns:
            int: 目标体积（字节）
        """
        return int(original_size * float(multiplier))

    @staticmethod
    def calculate_padding_needed(original_size, multiplier):
        """
        计算需要填充的额外字节数。

        Args:
            original_size: 原始文件大小（字节）
            multiplier: 目标倍数

        Returns:
            int: 需要填充的字节数
        """
        target = SizeService.calculate_target_size(original_size, multiplier)
        return max(0, target - original_size)

    @staticmethod
    def select_strategy(extension, original_size, multiplier):
        """
        根据文件类型和目标倍数选择最佳膨胀策略。

        策略优先级:
        1. 标准兼容的自定义元数据扩容
        2. 容器级安全扩容（低压缩率重新打包）
        3. 两者结合

        Args:
            extension: 文件扩展名
            original_size: 原始文件大小
            multiplier: 目标倍数

        Returns:
            dict: {
                'strategy': str,
                'feasible': bool,
                'reason': str | None,
                'estimated_steps': list[str]
            }
        """
        ext = extension.lower()
        m = float(multiplier)

        if ext in UNSUPPORTED_BINARY_EXTENSIONS:
            return {
                'strategy': STRATEGY_UNSUPPORTED,
                'feasible': False,
                'reason': f'{ext} 为旧版二进制 Office 格式，暂不支持安全的体积膨胀处理',
                'estimated_steps': []
            }

        if ext in {'.xlsx', '.docx', '.pptx'}:
            return SizeService._select_ooxml_strategy(ext, original_size, m)

        if ext == '.pdf':
            return SizeService._select_pdf_strategy(original_size, m)

        return {
            'strategy': STRATEGY_UNSUPPORTED,
            'feasible': False,
            'reason': f'未知的文件类型: {ext}',
            'estimated_steps': []
        }

    @staticmethod
    def _select_ooxml_strategy(ext, original_size, multiplier):
        """
        为 OOXML 格式选择膨胀策略。

        对于较小的倍数优先使用自定义 XML 元数据，
        较大倍数时结合低压缩率重新打包。

        Args:
            ext: 文件扩展名
            original_size: 原始文件大小
            multiplier: 目标倍数

        Returns:
            策略描述字典
        """
        if multiplier <= 3.0:
            return {
                'strategy': STRATEGY_CUSTOM_XML,
                'feasible': True,
                'reason': None,
                'estimated_steps': [
                    '解析 OOXML 容器结构',
                    '注入自定义 XML 部件作为填充元数据',
                    '更新 Content_Types 和关系文件',
                    '重新打包',
                    '验证输出文件'
                ]
            }

        if multiplier <= MAX_MULTIPLIER:
            return {
                'strategy': STRATEGY_COMBINED,
                'feasible': True,
                'reason': None,
                'estimated_steps': [
                    '解析 OOXML 容器结构',
                    '注入自定义 XML 部件作为填充元数据',
                    '以低压缩率重新打包所有内容',
                    '更新 Content_Types 和关系文件',
                    '验证输出文件'
                ]
            }

        return {
            'strategy': STRATEGY_UNSUPPORTED,
            'feasible': False,
            'reason': f'请求的倍数 {multiplier}x 超过最大安全限制 {MAX_MULTIPLIER}x',
            'estimated_steps': []
        }

    @staticmethod
    def _select_pdf_strategy(original_size, multiplier):
        """
        为 PDF 格式选择膨胀策略。

        Args:
            original_size: 原始文件大小
            multiplier: 目标倍数

        Returns:
            策略描述字典
        """
        if multiplier <= MAX_MULTIPLIER:
            return {
                'strategy': STRATEGY_PDF_METADATA,
                'feasible': True,
                'reason': None,
                'estimated_steps': [
                    '解析 PDF 结构',
                    '检查是否包含数字签名',
                    '通过元数据流注入填充数据',
                    '重建 xref 表',
                    '验证输出文件'
                ]
            }

        return {
            'strategy': STRATEGY_UNSUPPORTED,
            'feasible': False,
            'reason': f'请求的倍数 {multiplier}x 超过最大安全限制 {MAX_MULTIPLIER}x',
            'estimated_steps': []
        }

    @staticmethod
    def is_within_tolerance(actual_multiplier, target_multiplier):
        """
        判断实际达到的倍数是否在可接受的偏差范围内。

        Args:
            actual_multiplier: 实际达到的倍数
            target_multiplier: 目标倍数

        Returns:
            bool: 是否在可接受范围内
        """
        target = float(target_multiplier)
        actual = float(actual_multiplier)
        lower_bound = target * (1 - MULTIPLIER_TOLERANCE)
        return actual >= lower_bound
