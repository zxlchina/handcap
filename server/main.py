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
import logging
from urllib.parse import urlparse

import sys

sys.path.append("/home/lichzhang/code/JKTW/server/tools")
from commonlib import *


g_appid="wxb13b07fdd29e86af"
g_secret="85b7d64f15ed6bab2a1bbe2c219592ca"




app = Flask(__name__)


upload_file_path = "/home/lichzhang/release/HandCap/images/"


@app.route('/')
def hello_world():
    app.logger.debug("debug, this is a log test")
    app.logger.warning("warning, this is a log test")
    app.logger.error("error, thir is a log test")
    return "Hello World! "


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

    if "words_result" not in res:
        number_list.append("")
        return number_list
    for num in res["words_result"]:
       number_list.append(num["number"])

    return number_list


@app.route("/add_item", methods=['GET', 'POST'])
def add_item():
    img = request.args.get('img', '')
    openid = request.args.get('openid', '')
    car_numbers = request.args.get('car_numbers', '')

    if img == "" :
        res = {}
        res["ret"] = -1 
        res["error"] = "请选择违停图片"
        return json.dumps(res)

    if car_numbers == "" :
        res = {}
        res["ret"] = -1 
        res["error"] = "请设置车牌号"
        return json.dumps(res)

    
    numbers = json.loads(car_numbers) 

    img_url = urlparse(img)
    img_path = img_url.path
    
    sql = ""
    for number in numbers:
        sql="insert into cap_info (author, car_number, img_url) values ('%s', '%s', '%s')"  % (openid, number.upper(), img_path)
        print (sql)
    
    res = {}
    res["ret"] = -1 
    res["sql"] = sql
    return json.dumps(res)




@app.route("/code2session", methods=['GET', 'POST'])
def code_2_session():
    jscode = request.args.get('jscode', '')
    if jscode == "":
        res = {}
        res["ret"] = -1 
        res["error"] = "jscode is empty!"
        return json.dumps(res)

    #下面开始换session信息
    url = "https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code" % (g_appid, g_secret, jscode)

    res = requests.get(url)
    
    print(res.text)
    time.sleep(1)

    return res.text



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
        
        
        if not "img" in request.files.to_dict():
            res = {}
            res["ret"] = -1
            res["error"] = "Invalid File, need file named img"
            return json.dumps(res)
            
        f = request.files['img']


        ext = os.path.splitext(f.filename)[1] 
        filename = filename + ext
        f.save(upload_file_path + filename)

        url = request.host_url + "static/" + filename

        app.logger.debug("this is a log test")

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
    handler = logging.FileHandler('flask2.log', encoding='UTF-8')
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)

    print(get_file_name())
    init_aip()
    init_db()
    app.run(host="0.0.0.0", port=5001, debug=True)



