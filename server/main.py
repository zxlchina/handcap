from flask import Flask, url_for
import time
import random
import json
from flask import request
import os
import requests
import hashlib
import urllib
import base64

import sys

sys.path.append("/home/lichzhang/code/JKTW/server/tools")
from commonlib import *




app = Flask(__name__)


upload_file_path = "/home/lichzhang/release/HandCap/images/"


@app.route('/')
def hello_world():
    return "Hello World!"


@app.route("/publish", methods=['GET', 'POST'])
def publish():
    res = {}
    res["ret"] = 0

    return json.dumps(res)




def get_file_name():
    #得到当前时间
    return  time.strftime("%Y%m%d%H%M%S", time.localtime(time.time())) + "_" + str(int(random.uniform(1000,9999)))


def get_sign(params):
    uri_str = ""
    for key in sorted(params.keys()):
        if key == "app_key":
            continue
        uri_str += "%s=%s&" % (key, urllib.parse.quote(str(params[key]), safe = ""))
    sign_str = uri_str + "app_key=" + params["app_key"]

    hash_md5 = hashlib.md5(sign_str.encode())
    return hash_md5.hexdigest().upper()
    


def get_car_numbers_bd(img_path):
    res = get_car_number(img_path)

    number_list = [] 
    for num in res["words_result"]:
       number_list.append(num["number"])

    return number_list



#根据图片得到车牌号
def get_car_numbers(img_url):
    params = {}
    url = "https://api.ai.qq.com/fcgi-bin/ocr/ocr_plateocr"
    with open(img_url, "rb") as img_file:
        image_data = img_file.read()

    bs64 = base64.b64encode(image_data)
    params["image"] = bs64.decode("utf-8")
    params["app_id"] = 2109009601
    params["app_key"] = "j3uUlfX3KWokWLe4"
    #params["image_url"] = img_url
    params["time_stamp"] = str(int(time.time()))
    params["nonce_str"] = str(int(time.time()))
    params["sign"] = get_sign(params)

    data = ""
    for key in params:
        data += "%s=%s&" % (key, params[key])

    response = requests.post(url, data=params) 
    res = response.text

    print(res)
    
    car_number_list = []
    try:
        data = json.loads(res)
        if data["ret"] != 0:
            print ("get car number error:" ,res)
            return []

        for item in data["data"]["item_list"]:
            car_number_list.append(item["itemstring"])
    except :
        print("json exception")
        return []

    return car_number_list




@app.route("/upload", methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        filename = get_file_name()
        f = request.files['img']

        ext = os.path.splitext(f.filename)[1] 
        filename = filename + ext
        f.save(upload_file_path + filename)

        url = request.host_url + "static/" + filename

        #下面调用ocr接口识别车牌号
        #car_numbers = get_car_numbers(upload_file_path + filename)
        car_numbers = get_car_numbers_bd(upload_file_path + filename)



        res = {}
        res["ret"] = 0
        res["file"] = url
        res["msg"] = "this is test"
        res["car_numbers"] = car_numbers
        #url_for('static', filename=filename) 
        return json.dumps(res)


if __name__ == '__main__':
    print(get_file_name())
    init_aip()
    app.run(host="0.0.0.0", port=5001, debug=True)



