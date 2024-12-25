# 眼科数据提取工具

这是一个用于从眼科检查报告中提取关键信息的Python工具。该工具可以处理PDF格式的眼科检查报告，并提取双眼的测量数据以及患者病历信息。

## 功能特点

- PDF文档处理和图像分割
- OCR文字识别（使用PaddleOCR）
- 自动提取眼科测量数据（AL, ACD, LT, WTW, SE, K1, ΔK, K2等）
- 智能分析病历文本（使用Qwen大语言模型）
- 数据导出（Excel和JSON格式）

## 环境要求

- Python 3.6+
- PyPDF2
- pdf2image
- Pillow
- PaddleOCR
- pandas
- dashscope

## 安装说明

1. 克隆项目到本地
2. 安装依赖包：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 将眼科检查报告PDF文件放入`data`文件夹
2. 运行主程序：
```bash
python extract_info.py --pdf_path ./data/sample.pdf --page_number 2 --text_path ./data/sample_text.txt
```

参数说明：
- `--pdf_path`: PDF文件路径（默认：./data/sample.pdf）
- `--page_number`: 要提取的PDF页码，从1开始（默认：2）
- `--text_path`: 病历文本文件路径（默认：./data/sample_text.txt）

3. 程序将生成以下输出文件：
   - `eye_measurements.xlsx`：包含双眼测量数据
   - `eye_text_extracted.json`：包含病历文本提取结果
   - `left_eye.png`和`right_eye.png`：分割后的左右眼测量数据图像

## 数据格式

### 测量数据
包含以下指标的双眼数据：
- AL (眼轴长度)
- ACD (前房深度)
- LT (晶状体厚度)
- WTW (角膜直径)
- SE (等效球镜度)
- K1 (角膜曲率1)
- ΔK (角膜散光度)
- K2 (角膜曲率2)

### 病历文本提取
从病历中提取：
- 父母近视情况
- 散瞳验光数值

## 注意事项

- 使用前请确保已配置正确的API密钥
- PDF文件需要具有良好的图像质量以确保OCR准确性
- 建议定期备份重要数据

## License

MIT License



