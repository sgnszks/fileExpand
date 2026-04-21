"""
OOXML 处理器基类

XLSX、DOCX、PPTX 共享的 OOXML ZIP 容器操作逻辑。
包含自定义 XML 部件注入、低压缩率重新打包等核心膨胀能力。

扩容策略说明:
- 优先级 1: 向 OOXML 包中注入自定义 XML 部件（customXml），作为标准兼容的元数据填充。
  这些部件会在 [Content_Types].xml 中注册，但不会被任何可见内容引用，
  因此不影响文档的显示。
- 优先级 2: 以低压缩率（ZIP_STORED）重新打包，使存储体积增大。
- 优先级 3: 两种策略结合使用。

风险点:
- 过多的自定义 XML 部件可能导致旧版 Office 打开缓慢
- ZIP_STORED 模式下原始内容不被压缩，文件会更大
"""
import zipfile
import logging

from app.config import CUSTOM_XML_NAMESPACE, CUSTOM_PROPERTY_PREFIX, METADATA_CHUNK_SIZE
from app.processors.base_processor import BaseProcessor
from app.services.size_service import (
    STRATEGY_CUSTOM_XML, STRATEGY_COMBINED, STRATEGY_REPACK_LOW_COMPRESSION
)
from app.utils.file_utils import get_file_size

logger = logging.getLogger(__name__)

CONTENT_TYPES_FILE = '[Content_Types].xml'

PADDING_PART_PATH_TEMPLATE = 'customXml/expanderPadding{index}.xml'

PADDING_XML_OVERHEAD = 220

PADDING_MAX_CHUNK = METADATA_CHUNK_SIZE


class OoxmlBaseProcessor(BaseProcessor):
    """
    OOXML 格式通用处理器基类。

    子类需覆盖 supported_extensions 和 strategy_description 属性。
    """

    def expand(self, input_path, output_path, multiplier):
        """
        对 OOXML 文件执行体积膨胀。

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
            padding_needed = max(0, target_size - original_size)

            self.logger.info(
                "开始 OOXML 膨胀: 原始=%d, 目标=%d, 需填充=%d",
                original_size, target_size, padding_needed
            )

            strategy = self._determine_strategy(multiplier)

            entries, content_types_data = self._read_original_entries(input_path)

            if content_types_data is None:
                return self._build_error_result(
                    input_path, multiplier,
                    f'OOXML 包缺少 {CONTENT_TYPES_FILE}，不是有效的 Office 文档'
                )

            effective_padding = self._estimate_padding_after_repack(
                entries, padding_needed, strategy
            )

            num_parts, chunk_size = self._plan_padding_parts(effective_padding)

            self._write_output(
                output_path, entries, content_types_data,
                num_parts, chunk_size, strategy
            )

            return self._build_success_result(
                input_path, output_path, multiplier, strategy
            )

        except zipfile.BadZipFile as e:
            self.logger.error("ZIP 解析失败: %s", e)
            return self._build_error_result(
                input_path, multiplier,
                f'文件不是有效的 ZIP/OOXML 容器: {e}'
            )
        except Exception as e:
            self.logger.error("OOXML 膨胀失败: %s", e, exc_info=True)
            return self._build_error_result(
                input_path, multiplier, f'处理失败: {e}'
            )

    def _determine_strategy(self, multiplier):
        """
        根据倍数决定使用哪种策略。

        Args:
            multiplier: 目标倍数

        Returns:
            str: 策略常量
        """
        m = float(multiplier)
        if m <= 3.0:
            return STRATEGY_CUSTOM_XML
        return STRATEGY_COMBINED

    def _read_original_entries(self, input_path):
        """
        将输入 OOXML 文件的所有条目读取到内存。

        Args:
            input_path: 输入文件路径

        Returns:
            (list[(name, data)], bytes | None):
                除 Content_Types 外的条目列表，以及 Content_Types.xml 的内容
        """
        entries = []
        content_types_data = None

        with zipfile.ZipFile(input_path, 'r') as zin:
            for item in zin.infolist():
                if item.is_dir():
                    continue
                data = zin.read(item.filename)
                if item.filename == CONTENT_TYPES_FILE:
                    content_types_data = data
                else:
                    entries.append((item.filename, data))

        self.logger.debug(
            "读取完成: 共 %d 个条目（不含 Content_Types）",
            len(entries)
        )
        return entries, content_types_data

    def _estimate_padding_after_repack(self, entries, padding_needed, strategy):
        """
        估算在重新打包后仍需要补足的字节数。

        对于 STORED 策略（combined），重打包本身就会增大文件体积，
        因此需要的自定义 XML 填充可以相应减少。

        Args:
            entries: 原始条目列表
            padding_needed: 原始需要的填充字节数
            strategy: 使用的策略

        Returns:
            int: 估算的有效填充字节数
        """
        if strategy == STRATEGY_COMBINED:
            uncompressed_total = sum(len(data) for _, data in entries)
            estimated_repack_gain = int(uncompressed_total * 0.3)
            return max(0, padding_needed - estimated_repack_gain)

        return padding_needed

    def _plan_padding_parts(self, padding_needed):
        """
        计算需要多少个填充部件，以及每个部件的填充大小。

        Args:
            padding_needed: 需要填充的字节数

        Returns:
            (int, int): (部件数量, 每个部件的填充字节数)
        """
        if padding_needed <= 0:
            return (0, 0)

        chunk_size = min(PADDING_MAX_CHUNK, max(1024, padding_needed))
        num_parts = (padding_needed + chunk_size - 1) // chunk_size
        return (num_parts, chunk_size)

    def _write_output(self, output_path, entries, content_types_data,
                      num_parts, chunk_size, strategy):
        """
        将所有条目、填充部件和更新后的 Content_Types 写入输出 ZIP。

        Args:
            output_path: 输出文件路径
            entries: 原始条目列表（不含 Content_Types）
            content_types_data: 原始 Content_Types.xml 的字节内容
            num_parts: 需要写入的填充部件数量
            chunk_size: 每个填充部件的字节数
            strategy: 膨胀策略
        """
        use_stored = strategy in (STRATEGY_COMBINED, STRATEGY_REPACK_LOW_COMPRESSION)
        main_compression = zipfile.ZIP_STORED if use_stored else zipfile.ZIP_DEFLATED

        with zipfile.ZipFile(output_path, 'w', compression=main_compression,
                             allowZip64=True) as zout:
            for name, data in entries:
                zout.writestr(name, data, compress_type=main_compression)

            for i in range(num_parts):
                part_path = PADDING_PART_PATH_TEMPLATE.format(index=i)
                part_content = self._build_padding_xml(i, chunk_size)
                zout.writestr(
                    part_path,
                    part_content,
                    compress_type=zipfile.ZIP_STORED
                )

            updated_content_types = self._build_updated_content_types(
                content_types_data, num_parts
            )
            zout.writestr(
                CONTENT_TYPES_FILE,
                updated_content_types,
                compress_type=main_compression
            )

        self.logger.info(
            "写入完成: 条目=%d, 填充部件=%d, 策略=%s",
            len(entries), num_parts, strategy
        )

    def _build_padding_xml(self, index, payload_size):
        """
        构建单个填充 XML 部件的内容。

        Args:
            index: 部件序号
            payload_size: 期望的填充数据大小（字节）

        Returns:
            bytes: XML 部件内容
        """
        effective_size = max(0, payload_size - PADDING_XML_OVERHEAD)
        padding_data = 'A' * effective_size

        xml_content = (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<ExpanderMetadata xmlns="{CUSTOM_XML_NAMESPACE}">\n'
            f'  <PaddingData id="{CUSTOM_PROPERTY_PREFIX}{index}">'
            f'{padding_data}'
            f'</PaddingData>\n'
            f'</ExpanderMetadata>'
        )
        return xml_content.encode('utf-8')

    def _build_updated_content_types(self, original_xml_bytes, num_parts):
        """
        在原始 [Content_Types].xml 末尾前注入填充部件的 Override 声明。

        使用字符串拼接方式避免 XML 命名空间的序列化问题，
        保持原文件结构不变，只在 </Types> 前插入新节点。

        Args:
            original_xml_bytes: 原始 Content_Types.xml 的字节内容
            num_parts: 需要注册的填充部件数量

        Returns:
            bytes: 更新后的 Content_Types.xml 字节内容
        """
        if num_parts == 0:
            return original_xml_bytes

        try:
            xml_str = original_xml_bytes.decode('utf-8')
        except UnicodeDecodeError:
            self.logger.warning("Content_Types.xml 非 UTF-8 编码，跳过更新")
            return original_xml_bytes

        overrides = []
        for i in range(num_parts):
            part_name = f'/{PADDING_PART_PATH_TEMPLATE.format(index=i)}'
            overrides.append(
                f'<Override PartName="{part_name}" ContentType="application/xml"/>'
            )
        injection = ''.join(overrides)

        if '</Types>' in xml_str:
            xml_str = xml_str.replace('</Types>', injection + '</Types>', 1)
        else:
            self.logger.warning("Content_Types.xml 中未找到 </Types>，跳过注入")
            return original_xml_bytes

        return xml_str.encode('utf-8')
