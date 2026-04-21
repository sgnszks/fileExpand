"""
文件工具函数单元测试

覆盖:
- 文件名清洗
- 扩展名验证
- 文件签名检测
"""
import os
import tempfile

import pytest

from app.utils.file_utils import (
    sanitize_filename, validate_extension,
    detect_file_type_by_signature, generate_unique_filename
)


class TestSanitizeFilename:
    """文件名清洗测试。"""

    def test_normal_filename(self):
        assert sanitize_filename('test.xlsx') == 'test.xlsx'

    def test_chinese_filename(self):
        result = sanitize_filename('测试文件.docx')
        assert result.endswith('.docx')
        assert '测试文件' in result

    def test_path_traversal(self):
        result = sanitize_filename('../../etc/passwd')
        assert '..' not in result
        assert '/' not in result

    def test_special_chars(self):
        result = sanitize_filename('file<>:"|?*.xlsx')
        assert '<' not in result
        assert '>' not in result
        assert result.endswith('.xlsx')

    def test_empty_name(self):
        result = sanitize_filename('.xlsx')
        assert result.endswith('.xlsx')


class TestValidateExtension:
    """扩展名验证测试。"""

    def test_supported_xlsx(self):
        valid, ext = validate_extension('test.xlsx')
        assert valid is True
        assert ext == '.xlsx'

    def test_supported_pdf(self):
        valid, ext = validate_extension('doc.pdf')
        assert valid is True
        assert ext == '.pdf'

    def test_unsupported_txt(self):
        valid, ext = validate_extension('test.txt')
        assert valid is False

    def test_case_insensitive(self):
        valid, ext = validate_extension('test.XLSX')
        assert valid is True
        assert ext == '.xlsx'


class TestDetectFileTypeBySignature:
    """文件签名检测测试。"""

    def test_pdf_signature(self):
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4 test content')
            f.flush()
            result = detect_file_type_by_signature(f.name)
        os.unlink(f.name)
        assert result == '.pdf'

    def test_zip_signature(self):
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            f.write(b'PK\x03\x04 test content')
            f.flush()
            result = detect_file_type_by_signature(f.name)
        os.unlink(f.name)
        assert result == '.zip'

    def test_ole_signature(self):
        with tempfile.NamedTemporaryFile(suffix='.doc', delete=False) as f:
            f.write(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1 test')
            f.flush()
            result = detect_file_type_by_signature(f.name)
        os.unlink(f.name)
        assert result == '.ole'

    def test_unknown_signature(self):
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            f.write(b'unknown content here')
            f.flush()
            result = detect_file_type_by_signature(f.name)
        os.unlink(f.name)
        assert result is None

    def test_nonexistent_file(self):
        result = detect_file_type_by_signature('/nonexistent/path/file.xyz')
        assert result is None


class TestGenerateUniqueFilename:
    """唯一文件名生成测试。"""

    def test_includes_expanded(self):
        result = generate_unique_filename('test.xlsx', 2.0)
        assert 'expanded' in result
        assert result.endswith('.xlsx')

    def test_includes_multiplier(self):
        result = generate_unique_filename('test.pdf', 3.0)
        assert '3.0x' in result

    def test_unique_names(self):
        name1 = generate_unique_filename('test.xlsx', 2.0)
        name2 = generate_unique_filename('test.xlsx', 2.0)
        assert name1 != name2
