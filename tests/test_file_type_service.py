"""
文件类型识别服务单元测试

覆盖:
- 合法文件识别
- 非法文件拒绝
- 扩展名与签名不匹配检测
"""
import os
import tempfile

import pytest

from app.services.file_type_service import FileTypeService


class TestFileTypeIdentify:
    """文件类型识别测试。"""

    def test_unsupported_extension(self, temp_dir):
        filepath = os.path.join(temp_dir, 'test.txt')
        with open(filepath, 'w') as f:
            f.write('test')
        result = FileTypeService.identify(filepath, '.txt')
        assert result['valid'] is False
        assert '不支持' in result['error']

    def test_pdf_correct_signature(self, temp_dir):
        filepath = os.path.join(temp_dir, 'test.pdf')
        with open(filepath, 'wb') as f:
            f.write(b'%PDF-1.4 dummy pdf content')
        result = FileTypeService.identify(filepath, '.pdf')
        assert result['valid'] is True
        assert result['format_family'] == 'pdf'
        assert result['expandable'] is True

    def test_pdf_wrong_signature(self, temp_dir):
        filepath = os.path.join(temp_dir, 'fake.pdf')
        with open(filepath, 'wb') as f:
            f.write(b'This is not a PDF')
        result = FileTypeService.identify(filepath, '.pdf')
        assert result['valid'] is False

    def test_doc_correct_signature(self, temp_dir):
        filepath = os.path.join(temp_dir, 'test.doc')
        with open(filepath, 'wb') as f:
            f.write(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1 ole content')
        result = FileTypeService.identify(filepath, '.doc')
        assert result['valid'] is True
        assert result['expandable'] is False

    def test_empty_file(self, temp_dir):
        filepath = os.path.join(temp_dir, 'empty.xlsx')
        with open(filepath, 'wb') as f:
            pass
        result = FileTypeService.identify(filepath, '.xlsx')
        assert result['valid'] is False
