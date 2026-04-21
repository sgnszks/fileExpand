"""
PDF 文件处理器

支持的格式: .pdf
扩容策略: 通过 pikepdf 向 PDF 中添加大型元数据流对象
风险点:
  - 数字签名会因修改而失效
  - 线性化 PDF 修改后可能失去线性化特性
  - xref 表和对象偏移必须由 pikepdf 正确重建
验证方式: pikepdf/PyPDF2 重新加载，检查页数和对象结构
"""
import os
import logging

import pikepdf

from app.processors.base_processor import BaseProcessor
from app.services.size_service import STRATEGY_PDF_METADATA
from app.utils.file_utils import get_file_size

logger = logging.getLogger(__name__)


class PdfProcessor(BaseProcessor):
    """PDF 文件体积膨胀处理器。"""

    @property
    def supported_extensions(self):
        """返回支持的扩展名集合。"""
        return {'.pdf'}

    @property
    def strategy_description(self):
        """返回策略描述。"""
        return (
            'PDF: 通过添加不可见的元数据流对象来增大文件体积；'
            '保持页面可视内容不变，正确重建 xref 表'
        )

    def expand(self, input_path, output_path, multiplier):
        """
        对 PDF 文件执行体积膨胀。

        通过向 PDF 中添加大型的不可见流对象（Stream）来增大体积。
        这些对象不会被任何页面引用，因此不影响可视内容。

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            multiplier: 目标倍数

        Returns:
            ProcessingResult
        """
        try:
            original_size = get_file_size(input_path)
            target_size = int(original_size * float(multiplier))
            padding_needed = target_size - original_size

            self.logger.info(
                "开始 PDF 膨胀: 原始=%d, 目标=%d, 需填充=%d",
                original_size, target_size, padding_needed
            )

            warnings = []
            warnings.extend(self._check_pdf_features(input_path))

            self._perform_expansion(input_path, output_path, padding_needed)

            result = self._build_success_result(
                input_path, output_path, multiplier, STRATEGY_PDF_METADATA
            )
            result.warnings = warnings
            return result

        except pikepdf.PasswordError:
            return self._build_error_result(
                input_path, multiplier,
                '文件已加密或受密码保护，无法处理'
            )
        except Exception as e:
            self.logger.error("PDF 膨胀失败: %s", e, exc_info=True)
            return self._build_error_result(
                input_path, multiplier, f'PDF 处理失败: {str(e)}'
            )

    def _check_pdf_features(self, filepath):
        """
        检查 PDF 的特殊特性并生成警告。

        Args:
            filepath: PDF 文件路径

        Returns:
            list[str]: 警告信息列表
        """
        warnings = []
        try:
            with pikepdf.open(filepath) as pdf:
                if self._has_digital_signature(pdf):
                    warnings.append(
                        'PDF 包含数字签名，任何修改都可能导致签名失效'
                    )

                trailer = pdf.trailer
                if '/Linearized' in str(trailer):
                    warnings.append(
                        'PDF 已线性化，修改后将失去线性化特性'
                    )
        except Exception as e:
            self.logger.warning("PDF 特性检查失败: %s", e)

        return warnings

    def _has_digital_signature(self, pdf):
        """
        检查 PDF 是否包含数字签名。

        Args:
            pdf: pikepdf.Pdf 对象

        Returns:
            bool
        """
        try:
            if hasattr(pdf, 'Root') and '/AcroForm' in pdf.Root:
                acroform = pdf.Root['/AcroForm']
                if '/SigFlags' in acroform:
                    return True
                if '/Fields' in acroform:
                    for field in acroform['/Fields']:
                        resolved = field
                        if hasattr(resolved, 'keys') and '/FT' in resolved:
                            if str(resolved['/FT']) == '/Sig':
                                return True
        except Exception:
            pass
        return False

    def _perform_expansion(self, input_path, output_path, padding_needed):
        """
        执行 PDF 体积膨胀。

        向 PDF 中添加不可见的流对象（不被任何页面引用），
        pikepdf 会自动正确重建 xref 表和对象偏移。

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            padding_needed: 需要填充的字节数
        """
        with pikepdf.open(input_path) as pdf:
            chunk_size = 64 * 1024  # 64KB
            remaining = padding_needed
            stream_index = 0

            while remaining > 0:
                current_chunk = min(chunk_size, remaining)
                padding_bytes = b'\x00' * current_chunk

                stream = pikepdf.Stream(pdf, padding_bytes)
                stream['/Type'] = pikepdf.Name('/ExpanderPadding')
                stream['/Index'] = stream_index

                pdf.Root[f'/ExpanderPadding_{stream_index}'] = pdf.make_indirect(stream)

                remaining -= current_chunk
                stream_index += 1

            pdf.save(output_path, compress_streams=False, object_stream_mode=pikepdf.ObjectStreamMode.disable)

        self.logger.info("注入了 %d 个 PDF 填充流对象", stream_index)
