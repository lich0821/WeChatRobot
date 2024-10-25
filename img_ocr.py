#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: panda

import base64
import json

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ocr.v20181119 import ocr_client, models

import re


def image_to_base64(path):
    with open(path, "rb") as image_file:
        # 读取图片文件并编码为base64
        encoded_string = base64.b64encode(image_file.read())
        # 将字节类型转换为字符串
        return encoded_string.decode('utf-8')


def perform_ocr(secretid, secretkey, img_base_64, region="ap-beijing"):
    try:
        # 实例化一个认证对象
        cred = credential.Credential(secretid, secretkey)

        # 实例化一个http选项
        httpProfile = HttpProfile()
        httpProfile.endpoint = "ocr.tencentcloudapi.com"

        # 实例化一个client选项
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile

        # 实例化要请求产品的client对象
        client = ocr_client.OcrClient(cred, region, clientProfile)

        # 实例化一个请求对象
        req = models.GeneralAccurateOCRRequest()
        params = {
            "ImageBase64": img_base_64
        }
        req.from_json_string(json.dumps(params))

        # 返回的resp是一个GeneralAccurateOCRResponse的实例
        resp = client.GeneralAccurateOCR(req)

        # 返回json格式的字符串回包
        return json.loads(resp.to_json_string())

    except TencentCloudSDKException as err:
        print(err)
        return None


def points(string, num):
    return int(string) * num


# 未执行的积分
def unclaimed(data):
    for i, item in enumerate(data):
        if "积分值" in item["DetectedText"]:
            match = re.search(r"积分值\s*(\d+)/", data[i]['DetectedText'])
            if match:
                return int(match.group(1))
            else:
                return None


# 计算宝箱积分并排序
def sort_and_filter_x_texts(data):
    def get_min_x(detect):
        return min(point['X'] for point in detect['Polygon'])

    def is_x_text(detect):
        return re.match(r'X\d+', detect['DetectedText']) is not None

    x_texts = list(filter(is_x_text, data))
    sorted_detections = sorted(x_texts, key=get_min_x)

    sorted_x_texts = [detection['DetectedText'] for detection in sorted_detections]

    # 返回第 0、1、2、4 个元素
    return [sorted_x_texts[i] for i in [0, 1, 2, 4] if i < len(sorted_x_texts)]


# 过滤非宝箱图片

def contains_all_keywords_combined(text_detections, keywords):
    combined_text = " ".join(detection['DetectedText'] for detection in text_detections)
    return all(keyword in combined_text for keyword in keywords)


def extract_values(response, keywords):
    values = {}
    for detection in response['TextDetections']:
        detected_text = detection['DetectedText']
        for keyword in keywords:
            if keyword in detected_text:
                try:
                    values[keyword] = int(detected_text.split('x')[1])
                except (IndexError, ValueError):
                    values[keyword] = 0
    return values


def calculate_points(wood, bronze, gold, platinum):
    return points(wood, 1), points(bronze, 10), points(gold, 20), points(platinum, 50)


def format_integral(points_all, divisor=3340):
    return float(f"{points_all / divisor:.2f}")


def calculate_difference(current, initial, name, is_float=False):
    difference = initial - current
    if is_float or isinstance(current, float) or isinstance(initial, float):
        difference = f"{difference:.2f}"
    if current < initial:
        return f"{name}不足，还差: {difference}"
    return f"{name}满足，超出: {difference}"


def process_response(response):
    box_keywords = ["宝箱", "积分领取", "抽到紫将概率", "打开", "个宝箱"]
    fish_keywords = ["黄金鱼竿", "招募令", "金砖x", "木质宝箱", "青铜宝箱", "黄金宝箱", "铂金宝箱"]

    if contains_all_keywords_combined(response['TextDetections'], box_keywords):
        sorted_unique_x_texts = sort_and_filter_x_texts(response['TextDetections'])
        wood_box, bronze_box, gold_box, platinum_box = [text.replace('X', '') for text in sorted_unique_x_texts[:4]]

        points_wood, points_bronze, points_gold, points_platinum = calculate_points(wood_box, bronze_box, gold_box, platinum_box)
        points_all = points_wood + points_bronze + points_gold + points_platinum
        points_no_wood = points_bronze + points_gold + points_platinum
        points_no_platinum = points_wood + points_bronze + points_gold

        msg = ("木质箱子: {}个 --- 积分: {}\n"
               "青铜箱子: {}个 --- 积分: {}\n"
               "黄金箱子: {}个 --- 积分: {}\n"
               "铂金箱子: {}个 --- 积分: {}\n"
               "原始积分: {}\n"
               "未领取累计积分: {}\n"
               "宝箱周: {:.2f}轮\n"
               "不开木箱: {:.2f}轮\n"
               "不开铂金: {:.2f}轮\n"
               "------------------".format(
                   wood_box, points_wood, bronze_box, points_bronze,
                   gold_box, points_gold, platinum_box, points_platinum,
                   points_all, unclaimed(response["TextDetections"]),
                   format_integral(points_all),
                   format_integral(points_no_wood),
                   format_integral(points_no_platinum)))
        return msg

    elif contains_all_keywords_combined(response['TextDetections'], fish_keywords):
        values = extract_values(response, fish_keywords)

        points_wood, points_bronze, points_gold, points_platinum = calculate_points(
            values.get('木质宝箱', 0), values.get('青铜宝箱', 0),
            values.get('黄金宝箱', 0), values.get('铂金宝箱', 0))
        points_all = points_wood + points_bronze + points_gold + points_platinum
        formatted_integral = format_integral(points_all)

        fish_msg = calculate_difference(values.get('黄金鱼竿', 0), 700, "金鱼竿数量")
        recruit_msg = calculate_difference(values.get('招募令', 0), 3300, "招募令数量")
        integral_msg = calculate_difference(formatted_integral, 8.50, "宝箱积分")
        gold_msg = calculate_difference(values.get('金砖x', 0), 250000, "金砖")

        msg = "{}\n{}\n{}\n{}\n推荐资源参考：25w金砖,3300招募,8.5轮积分,700金鱼竿,请根据实际情况分析".format(
            fish_msg, recruit_msg, integral_msg, gold_msg)
        return msg

    return None
