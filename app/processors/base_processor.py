"""
处理器基类

定义所有文件处理器的公共接口和通用行为。
每个具体的处理器必须继承此基类并实现 expand 方法。
"""
import logging
from abc import ABC, abstractmethod

from app.models.result import ProcessingResult
from app.utils.file_utils import get_file_size


class BaseProcessor(ABC):
    """
    文件处理器抽象基类。

    支持的格式: 由子类定义
    扩容策略: 由子类实现
    风险点: 由子类文档说明
    验证方式: 由子类实现
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def supported_extensions(self):
        """返回此处理器支持的文件扩展名集合。"""
        pass

    @property
    @abstractmethod
    def strategy_description(self):
        """返回此处理器使用的扩容策略描述。"""
        pass

    @abstractmethod
    def expand(self, input_path, output_path, multiplier):
        """
        执行文件体积膨胀。

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            multiplier: 目标倍数

        Returns:
            ProcessingResult: 处理结果
        """
        pass

    def _build_success_result(self, input_path, output_path, multiplier, strategy):
        """
        构建成功的处理结果。

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            multiplier: 目标倍数
            strategy: 使用的策略名称

        Returns:
            ProcessingResult
        """
        original_size = get_file_size(input_path)
        output_size = get_file_size(output_path)
        actual_multiplier = output_size / original_size if original_size > 0 else 0

        return ProcessingResult(
            success=True,
            original_size=original_size,
            output_size=output_size,
            target_multiplier=float(multiplier),
            actual_multiplier=actual_multiplier,
            output_path=output_path,
            strategy_used=strategy,
        )

    def _build_error_result(self, input_path, multiplier, error_message):
        """
        构建失败的处理结果。

        Args:
            input_path: 输入文件路径
            multiplier: 目标倍数
            error_message: 错误描述

        Returns:
            ProcessingResult
        """
        return ProcessingResult(
            success=False,
            original_size=get_file_size(input_path),
            target_multiplier=float(multiplier),
            error_message=error_message,
        )
