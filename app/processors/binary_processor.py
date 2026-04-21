"""
旧版二进制 Office 格式处理器 (DOC/PPT)

支持的格式: .doc, .ppt（仅返回不支持信息）
扩容策略: 无 —— 当前不支持安全的体积膨胀
风险点: OLE 复合文档格式的二进制结构复杂，无依据修改可能导致文件损坏
验证方式: 不适用

根据规范要求，对旧版二进制格式不做无依据的修改，
明确返回"该格式暂不支持安全的体积膨胀处理"。
"""

from app.processors.base_processor import BaseProcessor
from app.models.result import ProcessingResult
from app.utils.file_utils import get_file_size


class BinaryOfficeProcessor(BaseProcessor):
    """旧版二进制 Office 格式处理器（DOC/PPT），仅返回不支持。"""

    @property
    def supported_extensions(self):
        """返回声称关联的扩展名集合。"""
        return {'.doc', '.ppt'}

    @property
    def strategy_description(self):
        """返回策略描述。"""
        return 'DOC/PPT: 旧版二进制 Office 格式，暂不支持安全的体积膨胀处理'

    def expand(self, input_path, output_path, multiplier):
        """
        始终返回不支持的错误结果。

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            multiplier: 目标倍数

        Returns:
            ProcessingResult: 包含不支持信息的失败结果
        """
        return ProcessingResult(
            success=False,
            original_size=get_file_size(input_path),
            target_multiplier=float(multiplier),
            error_message='该格式暂不支持安全的体积膨胀处理。'
                          'DOC/PPT 为旧版二进制 Office 格式，'
                          '无法在不破坏文件结构的前提下安全膨胀。'
        )
