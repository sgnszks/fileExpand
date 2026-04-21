"""
文件膨胀核心服务

协调整个文件膨胀流程：类型识别 -> 策略选择 -> 处理 -> 验证。
作为上层路由和底层处理器之间的中间协调层。
"""
import os
import logging

from app.config import MAX_UPLOAD_SIZE_BYTES
from app.services.file_type_service import FileTypeService
from app.services.size_service import SizeService
from app.services.processor_registry import get_processor
from app.validators.file_validator import FileValidator
from app.utils.file_utils import (
    generate_unique_filename, get_safe_output_path,
    get_file_size, cleanup_file
)

logger = logging.getLogger(__name__)


class ExpandService:
    """文件膨胀核心协调服务。"""

    def __init__(self):
        self.file_type_service = FileTypeService()
        self.size_service = SizeService()
        self.validator = FileValidator()

    def process(self, upload_path, original_filename, multiplier):
        """
        执行完整的文件膨胀处理流程。

        流程步骤:
        1. 验证倍数输入
        2. 文件大小检查
        3. 文件类型识别与验证
        4. 策略评估
        5. 获取处理器
        6. 执行膨胀
        7. 验证输出
        8. 返回结果

        Args:
            upload_path: 已上传文件的路径
            original_filename: 用户上传的原始文件名
            multiplier: 目标倍数

        Returns:
            dict: 包含处理结果的完整响应
        """
        output_path = None

        try:
            # 1. 验证倍数
            valid, error = self.size_service.validate_multiplier(multiplier)
            if not valid:
                logger.warning("倍数验证失败: %s", error)
                return self._error_response(error)

            multiplier = float(multiplier)

            # 2. 文件大小检查
            file_size = get_file_size(upload_path)
            if file_size == 0:
                return self._error_response('上传的文件为空')
            if file_size > MAX_UPLOAD_SIZE_BYTES:
                size_mb = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
                return self._error_response(
                    f'文件大小超过限制（最大 {size_mb:.0f}MB）'
                )

            # 3. 文件类型识别
            _, ext = os.path.splitext(original_filename)
            type_info = self.file_type_service.identify(upload_path, ext)

            logger.info(
                "文件类型识别: filename=%s, ext=%s, valid=%s, family=%s",
                original_filename, ext, type_info['valid'], type_info['format_family']
            )

            if not type_info['valid']:
                return self._error_response(type_info['error'])

            if not type_info['expandable']:
                return self._error_response(
                    f'{type_info["extension"]} 格式暂不支持安全的体积膨胀处理'
                )

            # 4. 策略评估
            strategy_info = self.size_service.select_strategy(
                type_info['extension'], file_size, multiplier
            )

            logger.info(
                "策略选择: strategy=%s, feasible=%s",
                strategy_info['strategy'], strategy_info['feasible']
            )

            if not strategy_info['feasible']:
                return self._error_response(strategy_info['reason'])

            # 5. 获取处理器
            processor = get_processor(type_info['extension'])
            if not processor:
                return self._error_response(
                    f'找不到 {type_info["extension"]} 格式的处理器'
                )

            # 6. 执行膨胀
            output_filename = generate_unique_filename(original_filename, multiplier)
            output_path = get_safe_output_path(output_filename)

            logger.info(
                "开始处理: file=%s, original_size=%d, multiplier=%s, strategy=%s",
                original_filename, file_size, multiplier, strategy_info['strategy']
            )

            result = processor.expand(upload_path, output_path, multiplier)

            if not result.success:
                cleanup_file(output_path)
                return self._error_response(result.error_message)

            # 7. 验证输出
            validation = self.validator.validate(output_path, type_info['extension'])

            logger.info(
                "验证结果: valid=%s, passed=%s, failed=%s",
                validation['valid'],
                validation['checks_passed'],
                validation['checks_failed']
            )

            if not validation['valid']:
                cleanup_file(output_path)
                return self._error_response(
                    f'输出文件验证失败: {validation["error"]}'
                )

            # 8. 检查倍数偏差
            actual_multiplier = result.actual_multiplier
            within_tolerance = self.size_service.is_within_tolerance(
                actual_multiplier, multiplier
            )

            warnings = list(result.warnings)
            if not within_tolerance:
                warnings.append(
                    f'实际倍数 {actual_multiplier:.2f}x 与目标 {multiplier}x 存在偏差'
                )

            logger.info(
                "处理完成: output_size=%d, actual_multiplier=%.2f, strategy=%s",
                result.output_size, actual_multiplier, result.strategy_used
            )

            return {
                'success': True,
                'data': {
                    'original_filename': original_filename,
                    'output_filename': output_filename,
                    'output_path': output_path,
                    'original_size': result.original_size,
                    'output_size': result.output_size,
                    'target_multiplier': multiplier,
                    'actual_multiplier': round(actual_multiplier, 2),
                    'strategy_used': result.strategy_used,
                    'validation': validation,
                    'warnings': warnings,
                },
                'error': None,
            }

        except Exception as e:
            logger.error("处理过程异常: %s", e, exc_info=True)
            if output_path:
                cleanup_file(output_path)
            return self._error_response(f'服务器内部错误: {str(e)}')

    @staticmethod
    def _error_response(message):
        """
        构建标准化错误响应。

        Args:
            message: 错误描述

        Returns:
            dict: 标准错误响应
        """
        return {
            'success': False,
            'data': None,
            'error': message,
        }
