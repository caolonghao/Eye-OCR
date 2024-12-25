# -*- coding: utf-8 -*-
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from PIL import Image
import os
from paddleocr import PaddleOCR
import re
import pandas as pd
import dashscope
from dashscope import Generation
from http import HTTPStatus
import logging
import json

def call_qwen(prompts, content):
    # 设置 API key
    dashscope.api_key = "sk-d9663052329b443bbe79bb6022efa6d0"

    # 调用 API
    response = Generation.call(
        model=Generation.Models.qwen_turbo,
        prompt=prompts + '\n' + content
    )

    if response.status_code == HTTPStatus.OK:
        logging.info("Dashscope response received.")
        return response['output']['text']
    else:
        logging.error(f"Dashscope error code: {response.status_code}")
        logging.error(f"Dashscope error message: {response.message}")



def extract_both_eyes_data(left_eye_text, right_eye_text):
    
    # 使用之前的map_extract函数分别提取数据
    left_data = map_extract(left_eye_text)
    right_data = map_extract(right_eye_text)
    
    # 创建DataFrame
    df = pd.DataFrame({
        '指标': ['AL', 'ACD', 'LT', 'WTW', 'SE', 'K1', 'ΔK', 'K2'],
        '左眼': [left_data[key] if left_data else '-' for key in ['AL', 'ACD', 'LT', 'WTW', 'SE', 'K1', 'ΔK', 'K2']],
        '右眼': [right_data[key] if right_data else '-' for key in ['AL', 'ACD', 'LT', 'WTW', 'SE', 'K1', 'ΔK', 'K2']]
    })
    
    return df

def map_extract(text_list):
    text = ' '.join(text_list)
    
    # 1. 匹配 AL, ACD, LT, WTW, SE 的值（包含单位）
    al_pattern = r'AL: ([\d.]+\s*mm)'
    acd_pattern = r'ACD: ([\d.]+\s*mm)'
    lt_pattern = r'LT: ([\d.]+\s*mm)'
    wtw_pattern = r'WTW: ([\d.]+\s*mm)'
    se_pattern = r'SE: ([\d.]+\s*D)'

    # 2-4. 匹配 K1, K, K2 的值
    k1_pattern = r'K1: ([\d.]+\s*D\s*@\s*\d+)'
    delta_k_pattern = r'K: (-?[\d.]+\s*D\s*@\s*\d+)'
    k2_pattern = r'K2: ([\d.]+\s*D\s*@\s*\d+)'

    al = re.search(al_pattern, text).group(1)  # '23.85 mm'
    acd = re.search(acd_pattern, text).group(1)  # '3.57 mm'
    lt = re.search(lt_pattern, text).group(1)  # '3.24 mm'
    wtw = re.search(wtw_pattern, text).group(1)  # '12.0 mm'
    se = re.search(se_pattern, text).group(1)  # '41.80 D'
    k1 = re.search(k1_pattern, text).group(1)  # '41.46 D @ 170'
    delta_k = re.search(delta_k_pattern, text).group(1)  # '-0.68 D @ 170'
    k2 = re.search(k2_pattern, text).group(1)  # '42.15 D @ 80'
    
    # 将数据组织成字典格式
    data = {
        "AL": al,
        "ACD": acd, 
        "LT": lt,
        "WTW": wtw,
        "SE": se,
        "K1": k1 + '°',
        "ΔK": delta_k + '°',
        "K2": k2 + '°'
    }
    
    return data


def extract_text_from_image(image_path):
    os.environ['KMP_DUPLICATE_LIB_OK']='TRUE'
    # 初始化 PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    
    # 执行OCR识别
    result = ocr.ocr(image_path, cls=True)
    
    # 提取识别的文本
    extracted_text = []
    if result:
        for line in result[0]:
            text = line[1][0]  # 获取识别的文本内容
            extracted_text.append(text)
    
    return extracted_text

def split_pdf_page_to_eyes(pdf_path, page_number):
    # 将指定页面的PDF转换为图像
    images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number)
    
    # 获取转换后的图像（应该只有一页）
    if images:
        img = images[0]
        
        # 获取图像尺寸
        width, height = img.size
        
        # 将图像分为左右两半
        left_half = img.crop((0, 0.4 * height, width//2 + 15, 0.5*height))
        right_half = img.crop((width//2+ 15, 0.4 * height, width, 0.5*height))
        
        # 保存图像
        # 注意：右眼对应左半部分，左眼对应右半部分
        left_half.save('right_eye.png')  # 左半部分保存为右眼
        right_half.save('left_eye.png')  # 右半部分保存为左眼
        
        print("图像已成功分割并保存为 left_eye.png 和 right_eye.png")
    else:
        print("无法处理PDF页面")
        
extract_prompts = """
    请你作为我的眼科信息提取专家，从一段文字中提取以下内容：
    1、父母近视情况。
    2、散瞳验光的数值。注意其符号也要抽取，斜杠前面的是右眼，后面的是左眼，每一眼中第一个是近视度，第二个是散光，第三个是散光的位置
    结果以json格式返回，未提及的内容或是不符合规则无法识别的内容标记为未知。

    这是一个例子：
    ---
    待提取文本: "主诉及现病史：双眼远视力下降复查。新冠流调未见异常，无发热、呼吸道及消化道症状。 既往史：既往体健。药敏史-，父亲近视-6.0D。 查体和专科情况：视力0.6/0.25，眼位-，双眼角膜清，前房周边1ct，中央5ct，晶体透明，眼底前置镜观察-，双眼均为中心注视。 辅助检查： 散瞳验光-2.00-0.50*180/-2.00 1.0/1.0，眼轴长 25.34-25.38 诊断或印象诊断：近视 处理意见：完善检查。复验配镜，规律戴镜，3-6个月复查，注意用眼卫生。 处方：复方托吡卡胺滴眼液, 滴眼, 1ml/, 1ml/支; 诊��：中央前房深度测量-裂隙灯法;周边前房深度测量-裂隙灯法;前置镜眼底检查;注视性质检查;普通远视力检查;非接触眼压计(NCT)测量; 检查：眼科检查散瞳验光组合;眼科检查眼轴IOL度数测量-光学法(Master);眼科检查激光扫描检眼镜眼底检查(欧堡); 检验：   嘱托：不适随诊 提示：病情发生变化时建议门诊复诊，必要时急诊就诊。 医师：     就诊日期：2022-08-31 眼压日曲线 眼外伤玻璃体手术随访登记表 眼科健康教育处方 8028 8058"
    提取结果：
    "
    {
    "父母近视情况": {
        "父亲": "-6.0D",
        "母亲": "未知"
    },
    "散瞳验光": {
        "右眼": {
        "近视度数": "-2.00",
        "散光": "-0.50",
        "轴位": "180"
        },
        "左眼": {
        "近视度数": "-2.00",
        "散光": "1.0",
        "轴位": "未知"
        }
    }
    }
    "
    ---

    以下是需要提取的内容：
"""

if __name__=='__main__':
    pdf_path = "./data/sample.pdf"  # 替换为你的PDF文件路径
    page_number = 2  # 想要提取的页码（从1开始）

    split_pdf_page_to_eyes(pdf_path, page_number)
    
    left_eye_text = extract_text_from_image('left_eye.png')
    right_eye_text = extract_text_from_image('right_eye.png')
    
    measurement_data = extract_both_eyes_data(left_eye_text, right_eye_text)
    measurement_data.to_excel('eye_measurements.xlsx', index=False)
    
    # 从文件中读取测试文本
    with open('./data/sample_text.txt', 'r', encoding='utf-8') as f:
        test_text = f.read()
    
    response_text = call_qwen(extract_prompts, test_text)
    
    # 使用正则表达式提取 JSON 部分
    json_pattern = r'\{[\s\S]*\}'
    json_match = re.search(json_pattern, response_text)
    
    if json_match:
        json_str = json_match.group()
        try:
            # 解析 JSON 字符串
            json_data = json.loads(json_str)
            # print("提取的JSON数据:")
            # print(json.dumps(json_data, ensure_ascii=False, indent=4))
            # 将JSON数据保存到文件
            with open('eye_text_extracted.json', 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            
            logging.info("JSON数据已保存到 extracted_data.json")
        except json.JSONDecodeError as e:
            logging.error(f"JSON解析错误: {e}")
    else:
        logging.warning("未找到JSON格式的内容")