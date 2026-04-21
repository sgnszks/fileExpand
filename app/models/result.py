"""
处理结果数据模型

定义文件处理过程中使用的结构化结果对象。
"""


class ProcessingResult:
    """文件处理结果，包含输出路径、体积信息和状态。"""

    def __init__(self, success, original_size=0, output_size=0,
                 target_multiplier=1.0, actual_multiplier=0.0,
                 output_path=None, strategy_used=None,
                 error_message=None, warnings=None):
        self.success = success
        self.original_size = original_size
        self.output_size = output_size
        self.target_multiplier = target_multiplier
        self.actual_multiplier = actual_multiplier
        self.output_path = output_path
        self.strategy_used = strategy_used
        self.error_message = error_message
        self.warnings = warnings or []

    def to_dict(self):
        """转换为可序列化的字典。"""
        return {
            'success': self.success,
            'original_size': self.original_size,
            'output_size': self.output_size,
            'target_multiplier': self.target_multiplier,
            'actual_multiplier': round(self.actual_multiplier, 2),
            'strategy_used': self.strategy_used,
            'error_message': self.error_message,
            'warnings': self.warnings,
        }
