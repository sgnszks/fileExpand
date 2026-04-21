"""
XLSX 文件处理器

支持的格式: .xlsx (Office Open XML Spreadsheet)
扩容策略: 自定义 XML 元数据注入 + 低压缩率重新打包
风险点: 过多自定义 XML 部件可能导致旧版 Excel 打开缓慢
验证方式: openpyxl 重新加载，检查工作表列表和基本结构
"""

from app.processors.ooxml_base import OoxmlBaseProcessor


class XlsxProcessor(OoxmlBaseProcessor):
    """XLSX 文件体积膨胀处理器。"""

    @property
    def supported_extensions(self):
        """返回支持的扩展名集合。"""
        return {'.xlsx'}

    @property
    def strategy_description(self):
        """返回策略描述。"""
        return (
            'XLSX (OOXML): 优先注入自定义 XML 元数据部件；'
            '高倍数时结合 ZIP_STORED 低压缩率重新打包'
        )
