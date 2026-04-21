"""
体积计算服务单元测试

覆盖:
- 目标体积计算
- 倍数验证
- 策略选择
"""
import pytest

from app.services.size_service import (
    SizeService, STRATEGY_CUSTOM_XML, STRATEGY_COMBINED,
    STRATEGY_PDF_METADATA, STRATEGY_UNSUPPORTED
)


class TestValidateMultiplier:
    """倍数验证测试。"""

    def test_valid_multiplier(self):
        valid, err = SizeService.validate_multiplier(2.0)
        assert valid is True
        assert err is None

    def test_min_boundary(self):
        valid, err = SizeService.validate_multiplier(1.1)
        assert valid is True

    def test_max_boundary(self):
        valid, err = SizeService.validate_multiplier(10.0)
        assert valid is True

    def test_below_min(self):
        valid, err = SizeService.validate_multiplier(0.5)
        assert valid is False
        assert '不能小于' in err

    def test_above_max(self):
        valid, err = SizeService.validate_multiplier(15)
        assert valid is False
        assert '不能大于' in err

    def test_invalid_string(self):
        valid, err = SizeService.validate_multiplier('abc')
        assert valid is False

    def test_none_input(self):
        valid, err = SizeService.validate_multiplier(None)
        assert valid is False


class TestCalculateTargetSize:
    """目标体积计算测试。"""

    def test_double_size(self):
        result = SizeService.calculate_target_size(1000, 2.0)
        assert result == 2000

    def test_fractional_multiplier(self):
        result = SizeService.calculate_target_size(1000, 1.5)
        assert result == 1500

    def test_zero_original(self):
        result = SizeService.calculate_target_size(0, 2.0)
        assert result == 0


class TestCalculatePaddingNeeded:
    """填充字节计算测试。"""

    def test_normal_padding(self):
        result = SizeService.calculate_padding_needed(1000, 2.0)
        assert result == 1000

    def test_no_negative_padding(self):
        result = SizeService.calculate_padding_needed(1000, 1.0)
        assert result == 0


class TestSelectStrategy:
    """策略选择测试。"""

    def test_xlsx_low_multiplier(self):
        result = SizeService.select_strategy('.xlsx', 10000, 2.0)
        assert result['strategy'] == STRATEGY_CUSTOM_XML
        assert result['feasible'] is True

    def test_xlsx_high_multiplier(self):
        result = SizeService.select_strategy('.xlsx', 10000, 5.0)
        assert result['strategy'] == STRATEGY_COMBINED
        assert result['feasible'] is True

    def test_docx_strategy(self):
        result = SizeService.select_strategy('.docx', 10000, 2.0)
        assert result['feasible'] is True

    def test_pptx_strategy(self):
        result = SizeService.select_strategy('.pptx', 10000, 2.0)
        assert result['feasible'] is True

    def test_pdf_strategy(self):
        result = SizeService.select_strategy('.pdf', 10000, 2.0)
        assert result['strategy'] == STRATEGY_PDF_METADATA
        assert result['feasible'] is True

    def test_doc_unsupported(self):
        result = SizeService.select_strategy('.doc', 10000, 2.0)
        assert result['strategy'] == STRATEGY_UNSUPPORTED
        assert result['feasible'] is False

    def test_ppt_unsupported(self):
        result = SizeService.select_strategy('.ppt', 10000, 2.0)
        assert result['strategy'] == STRATEGY_UNSUPPORTED
        assert result['feasible'] is False


class TestIsWithinTolerance:
    """倍数偏差容忍度测试。"""

    def test_exact_match(self):
        assert SizeService.is_within_tolerance(2.0, 2.0) is True

    def test_within_tolerance(self):
        assert SizeService.is_within_tolerance(1.96, 2.0) is True

    def test_outside_tolerance(self):
        assert SizeService.is_within_tolerance(1.5, 2.0) is False
