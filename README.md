# 文件体积膨胀工具

基于 Web 的文件体积放大工具，在**不改变用户可见内容**的前提下，将文件体积膨胀到指定倍数。

## 支持的文件格式

| 格式 | 状态 | 膨胀策略 |
|------|------|----------|
| .xlsx | 支持 | 自定义 XML 元数据注入 / 低压缩率重打包 |
| .docx | 支持 | 自定义 XML 元数据注入 / 低压缩率重打包 |
| .pptx | 支持 | 自定义 XML 元数据注入 / 低压缩率重打包 |
| .pdf  | 支持 | PDF 元数据流对象注入 |
| .doc  | 不支持 | 旧版二进制格式，安全风险高 |
| .ppt  | 不支持 | 旧版二进制格式，安全风险高 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python run.py
```

服务启动后访问 http://localhost:5000

### 3. 运行测试

```bash
pytest tests/ -v
```

## 项目结构

```
fileExpand/
├── app/
│   ├── __init__.py
│   ├── config.py              # 配置与常量
│   ├── main.py                # Flask 应用工厂
│   ├── models/
│   │   └── result.py          # 处理结果数据模型
│   ├── processors/
│   │   ├── base_processor.py  # 处理器抽象基类
│   │   ├── ooxml_base.py      # OOXML 通用处理逻辑
│   │   ├── xlsx_processor.py  # XLSX 处理器
│   │   ├── docx_processor.py  # DOCX 处理器
│   │   ├── pptx_processor.py  # PPTX 处理器
│   │   ├── pdf_processor.py   # PDF 处理器
│   │   └── binary_processor.py# DOC/PPT 处理器（返回不支持）
│   ├── routes/
│   │   └── api.py             # API 路由
│   ├── services/
│   │   ├── expand_service.py  # 核心协调服务
│   │   ├── file_type_service.py # 文件类型识别
│   │   ├── processor_registry.py# 处理器注册表
│   │   └── size_service.py    # 体积计算与策略选择
│   ├── utils/
│   │   └── file_utils.py      # 文件操作工具
│   └── validators/
│       └── file_validator.py  # 输出文件验证
├── static/
│   ├── css/style.css          # 前端样式
│   └── js/app.js              # 前端交互逻辑
├── templates/
│   └── index.html             # 主页面模板
├── tests/
│   ├── conftest.py            # 测试配置
│   ├── test_api.py            # API 路由测试
│   ├── test_file_type_service.py # 文件类型识别测试
│   ├── test_file_utils.py     # 工具函数测试
│   ├── test_integration.py    # 集成测试
│   └── test_size_service.py   # 体积计算测试
├── temp/                      # 临时文件目录（运行时自动创建）
├── requirements.txt
├── run.py                     # 启动入口
└── README.md
```

## 处理流程

1. **上传接收** — 接收文件并保存到临时目录
2. **类型识别** — 通过扩展名 + 文件签名双重验证
3. **策略选择** — 根据文件类型和目标倍数选择最安全的膨胀策略
4. **格式处理** — 由对应处理器执行体积膨胀
5. **输出验证** — 使用对应解析库重新验证输出文件
6. **下载响应** — 返回膨胀后的文件供下载

## 安全性

- 文件大小限制 100MB
- 文件名清洗防止路径穿越
- 扩展名与文件签名交叉验证
- 临时文件隔离处理
- 不执行上传文件中的任何内容
- 验证失败的文件不会被返回给用户

## 膨胀倍数

- 最小: 1.1 倍
- 最大: 10 倍
- 允许 5% 的倍数偏差
