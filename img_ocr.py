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


# 宝箱积分计算
def count_box(response):
    # 过滤response内容关键字
    keywords = ["宝箱", "积分领取", "抽到紫将概率", "打开", "个宝箱"]
    if contains_all_keywords_combined(response['TextDetections'], keywords):
        # 宝箱积分
        sorted_unique_x_texts = sort_and_filter_x_texts(response['TextDetections'])

        wood, bronze, gold, platinum = [text.replace('X', '') for text in sorted_unique_x_texts[:4]]

        # 未使用积分
        points_unclaimed = unclaimed(response["TextDetections"])

        points_wood = points(wood, 1)
        points_bronze = points(bronze, 10)
        points_gold = points(gold, 20)
        points_platinum = points(platinum, 50)

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
               "------------------".format(wood,
                                           points_wood,
                                           bronze,
                                           points_bronze,
                                           gold,
                                           points_gold,
                                           platinum,
                                           points_platinum,
                                           points_all,
                                           points_unclaimed,
                                           points_all / 3340,
                                           points_no_wood / 3340,
                                           points_no_platinum / 3340))
        return msg
    else:
        return None
