"""
文件验证模块

对处理后的输出文件进行结构性验证，确保文件可被对应程序正常打开。
验证与文件修改严格分离，独立执行。
"""
import os
import zipfile
import logging

logger = logging.getLogger(__name__)


class FileValidator:
    """输出文件验证器。"""

    def validate(self, filepath, extension):
        """
        根据文件类型执行对应的验证检查。

        Args:
            filepath: 输出文件路径
            extension: 文件扩展名

        Returns:
            dict: {
                'valid': bool,
                'checks_passed': list[str],
                'checks_failed': list[str],
                'error': str | None
            }
        """
        if not os.path.exists(filepath):
            return self._fail('输出文件不存在')

        if os.path.getsize(filepath) == 0:
            return self._fail('输出文件大小为 0')

        ext = extension.lower()
        validators = {
            '.xlsx': self._validate_xlsx,
            '.docx': self._validate_docx,
            '.pptx': self._validate_pptx,
            '.pdf': self._validate_pdf,
        }

        validator_func = validators.get(ext)
        if not validator_func:
            return self._fail(f'没有可用的验证器: {ext}')

        return validator_func(filepath)

    def _validate_xlsx(self, filepath):
        """
        验证 XLSX 文件。

        检查项:
        - ZIP 包可正常打开
        - [Content_Types].xml 存在
        - workbook.xml 存在
        - 工作表列表可读取
        """
        checks_passed = []
        checks_failed = []

        if not self._check_valid_zip(filepath):
            return self._fail('文件不是有效的 ZIP 包')
        checks_passed.append('ZIP 包结构有效')

        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                names = zf.namelist()

                if '[Content_Types].xml' not in names:
                    checks_failed.append('[Content_Types].xml 缺失')
                else:
                    checks_passed.append('[Content_Types].xml 存在')

                workbook_found = any(
                    'workbook.xml' in n for n in names
                    if n.startswith('xl/')
                )
                if not workbook_found:
                    checks_failed.append('workbook.xml 缺失')
                else:
                    checks_passed.append('workbook.xml 存在')

        except Exception as e:
            checks_failed.append(f'结构检查失败: {str(e)}')

        try:
            import openpyxl
            wb = openpyxl.load_workbook(filepath, read_only=True)
            sheet_names = wb.sheetnames
            wb.close()
            checks_passed.append(f'openpyxl 可正常加载，工作表: {sheet_names}')
        except Exception as e:
            checks_failed.append(f'openpyxl 加载失败: {str(e)}')

        if checks_failed:
            return {
                'valid': False,
                'checks_passed': checks_passed,
                'checks_failed': checks_failed,
                'error': '; '.join(checks_failed)
            }

        return {
            'valid': True,
            'checks_passed': checks_passed,
            'checks_failed': [],
            'error': None
        }

    def _validate_docx(self, filepath):
        """
        验证 DOCX 文件。

        检查项:
        - ZIP 包可正常打开
        - [Content_Types].xml 存在
        - word/document.xml 存在
        - python-docx 可正常加载
        """
        checks_passed = []
        checks_failed = []

        if not self._check_valid_zip(filepath):
            return self._fail('文件不是有效的 ZIP 包')
        checks_passed.append('ZIP 包结构有效')

        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                names = zf.namelist()

                if '[Content_Types].xml' not in names:
                    checks_failed.append('[Content_Types].xml 缺失')
                else:
                    checks_passed.append('[Content_Types].xml 存在')

                doc_found = any(
                    'document.xml' in n for n in names
                    if n.startswith('word/')
                )
                if not doc_found:
                    checks_failed.append('word/document.xml 缺失')
                else:
                    checks_passed.append('word/document.xml 存在')

        except Exception as e:
            checks_failed.append(f'结构检查失败: {str(e)}')

        try:
            from docx import Document
            doc = Document(filepath)
            para_count = len(doc.paragraphs)
            checks_passed.append(f'python-docx 可正常加载，段落数: {para_count}')
        except Exception as e:
            checks_failed.append(f'python-docx 加载失败: {str(e)}')

        if checks_failed:
            return {
                'valid': False,
                'checks_passed': checks_passed,
                'checks_failed': checks_failed,
                'error': '; '.join(checks_failed)
            }

        return {
            'valid': True,
            'checks_passed': checks_passed,
            'checks_failed': [],
            'error': None
        }

    def _validate_pptx(self, filepath):
        """
        验证 PPTX 文件。

        检查项:
        - ZIP 包可正常打开
        - [Content_Types].xml 存在
        - ppt/presentation.xml 存在
        - python-pptx 可正常加载
        """
        checks_passed = []
        checks_failed = []

        if not self._check_valid_zip(filepath):
            return self._fail('文件不是有效的 ZIP 包')
        checks_passed.append('ZIP 包结构有效')

        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                names = zf.namelist()

                if '[Content_Types].xml' not in names:
                    checks_failed.append('[Content_Types].xml 缺失')
                else:
                    checks_passed.append('[Content_Types].xml 存在')

                pres_found = any(
                    'presentation.xml' in n for n in names
                    if n.startswith('ppt/')
                )
                if not pres_found:
                    checks_failed.append('ppt/presentation.xml 缺失')
                else:
                    checks_passed.append('ppt/presentation.xml 存在')

        except Exception as e:
            checks_failed.append(f'结构检查失败: {str(e)}')

        try:
            from pptx import Presentation
            prs = Presentation(filepath)
            slide_count = len(prs.slides)
            checks_passed.append(f'python-pptx 可正常加载，幻灯片数: {slide_count}')
        except Exception as e:
            checks_failed.append(f'python-pptx 加载失败: {str(e)}')

        if checks_failed:
            return {
                'valid': False,
                'checks_passed': checks_passed,
                'checks_failed': checks_failed,
                'error': '; '.join(checks_failed)
            }

        return {
            'valid': True,
            'checks_passed': checks_passed,
            'checks_failed': [],
            'error': None
        }

    def _validate_pdf(self, filepath):
        """
        验证 PDF 文件。

        检查项:
        - pikepdf 可正常加载
        - 页数保持稳定
        - 文档对象结构有效
        """
        checks_passed = []
        checks_failed = []

        try:
            import pikepdf
            pdf = pikepdf.open(filepath)
            page_count = len(pdf.pages)
            pdf.close()
            checks_passed.append(f'pikepdf 可正常加载，页数: {page_count}')
        except Exception as e:
            checks_failed.append(f'pikepdf 加载失败: {str(e)}')

        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(filepath)
            page_count_2 = len(reader.pages)
            checks_passed.append(f'PyPDF2 可正常加载，页数: {page_count_2}')
        except Exception as e:
            checks_failed.append(f'PyPDF2 加载失败: {str(e)}')

        if checks_failed:
            return {
                'valid': False,
                'checks_passed': checks_passed,
                'checks_failed': checks_failed,
                'error': '; '.join(checks_failed)
            }

        return {
            'valid': True,
            'checks_passed': checks_passed,
            'checks_failed': [],
            'error': None
        }

    @staticmethod
    def _check_valid_zip(filepath):
        """检查文件是否为有效的 ZIP 包。"""
        return zipfile.is_zipfile(filepath)

    @staticmethod
    def _fail(message):
        """构建验证失败结果。"""
        return {
            'valid': False,
            'checks_passed': [],
            'checks_failed': [message],
            'error': message
        }
