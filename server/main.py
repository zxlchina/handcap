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



def escape_str(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")
    

@app.route("/get_clist", methods=['GET', 'POST'])
def get_clist():
    sql = "select cid, cname from community_info"
    result = get_result(sql)

    if result is None:
        res["ret"] = -1
        res["error"] = "query db error!" 
        return json.dumps(res)
        

    res = {}
    res["ret"] = 0
    res["clist"] = []
    for item in result:
        one = {}
        one["cid"] = item[0]
        one["cname"] = item[1]
        res["clist"].append(one)

    return json.dumps(res) 



@app.route("/replay", methods=['GET', 'POST'])
def replay():
    content = escape_str(request.args.get('content', ''))
    openid = escape_str(request.args.get('openid', ''))
    sql = "insert into replay (content, author) values ('%s', '%s')" % (content, openid)

    print(sql)


    
    result = get_result(sql)
    
    if result is None:
        res = {}
        res["ret"] = -1
        res["error"] = "提交失败，请稍后再试"
        return json.dumps(res)


    res = {} 
    res["ret"] = 0
    return json.dumps(res) 
    
 


@app.route("/get_detail", methods=['GET', 'POST'])
def get_detail():
    car_number = request.args.get('car_number', '')
    cid = int(request.args.get('cid', '')) 

    sql = ""
    if cid == 0 :
        sql = "select create_time, img_url from cap_info where car_number = '%s' order by create_time desc" % (car_number)
    else:
        sql = "select create_time, img_url from cap_info where car_number = '%s' and cid = %d order by create_time desc" % (car_number, cid)
    result = get_result(sql)


    res = {}
    res["ret"] = 0
    res["detail"] = []
    for item in result:
        one = {}
        one["create_time"] = item[0].strftime("%Y-%m-%d %H:%M:%S")
        one["img_url"] = item[1]
        res["detail"].append(one)

    return json.dumps(res)
        

    

@app.route("/get_user_count", methods=['GET', 'POST'])
def get_user_count():
    openid = escape_str(request.args.get('openid', ''))

    if openid == "":
        res = {}
        res["ret"] = -1
        res["error"] = "invalid openid"
        return json.dumps(res)

    
    sql = "select count(distinct pub_id), count(distinct(if(create_time>=DATE_FORMAT( SUBDATE(CURDATE(),DATE_FORMAT(CURDATE(),'%%w')-1), '%%Y-%%m-%%d 00:00:00'), pub_id, null))) from cap_info where author = '%s'" % (openid)
    sql = "select count(distinct pub_id), count(distinct(if(create_time>=DATE_FORMAT(curdate()- WEEKDAY(curdate()), '%%Y-%%m-%%d 00:00:00'), pub_id, null))) from cap_info where author = '%s'" % (openid)
    #sql = "select count(distinct pub_id), count(distinct(if(create_time>=DATE_FORMAT( DATE_SUB(CURDATE(), INTERVAL 1 DAY), '%%Y-%%m-%%d 23:59:59'), pub_id, null))) from cap_info where author = '%s'" % (openid)

    print(sql)
    result = get_result(sql) 
    if result is None:
        res = {}
        res["ret"] = -1
        res["error"] = "query db error!"
        return json.dumps(res) 

    for item in result:
        res = {}
        print(item)
        res["ret"] = 0
        res["total_count"] = int(item[0])
        res["week_count"] = int(item[1])
        return json.dumps(res)

    res = {}
    res["ret"] = 0
    res["total_count"] = 0 
    res["week_count"] = 0 
    return json.dumps(res)



@app.route("/get_rank", methods=['GET', 'POST'])
def get_rank():
    cid = int(request.args.get('cid', '')) 

    sql = ""
    if cid == 0:
        sql = "select car_number, count(1) as cnt from cap_info where car_number != ''  group by car_number order by cnt desc"
    else:
        sql = "select car_number, count(1) as cnt from cap_info where car_number != '' and cid=%d group by car_number order by cnt desc" % (cid)

    result = get_result(sql)

    if result is None:
        res["ret"] = -1
        res["error"] = "query db error!" 
        return json.dumps(res)

    res = {}
    res["ret"] = 0
    res["rank_list"] = []
    
    for item in result:
        car = {}
        car["number"] = item[0]
        car["count"] = item[1]
        res["rank_list"].append(car)
    
    return json.dumps(res)

   


@app.route("/update_user_info", methods=['GET', 'POST'])
def update_user_info():
    openid = escape_str(request.args.get('openid', ''))
    nickname = escape_str(request.args.get('nickname', ''))
    gender = escape_str(request.args.get('gender', ''))
    avatar = escape_str(request.args.get('avatar', ''))
    city = escape_str(request.args.get('city', ''))
    country = escape_str(request.args.get('country', ''))
    province = escape_str(request.args.get('province', ''))
    lang = escape_str(request.args.get('lang', ''))

    sql = "replace into user_info (openid, nickname, gender, avatar, city, country, province, lang) values ('%s', '%s', %s, '%s', '%s', '%s', '%s', '%s')" \
     % (openid, nickname, gender, avatar, city, country, province, lang)
    print(sql)


    res = {}
    res["ret"] = 0

    result = get_result(sql)
    if result is None:
        res["ret"] = -1
        res["error"] = "insert db error!" 

    return json.dumps(res)


@app.route("/add_item", methods=['GET', 'POST'])
def add_item():
    img = escape_str(request.args.get('img', ''))
    openid = escape_str(request.args.get('openid', ''))
    car_numbers = escape_str(request.args.get('car_numbers', ''))
    cid = escape_str(request.args.get('cid', ''))

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

    #生成pub_id
    t = time.time()
    pub_id = str((int(round(t * 1000))))

    #检查是否需要写入空值
    need_empty = True
    for number in numbers:
        if number != "":
            #只要有一个非空的，则不需要写入空值
            need_empty = False
        

    img_url = urlparse(img)
    img_path = img_url.path
    
    sql = ""
    has_insert = False
    for number in numbers:
        if number == "" :
            if need_empty == False: #不需要保存空的
                continue
            if need_empty == True and has_insert == True: #需要保存空的，但是已经保存过了
                continue

        sql="insert into cap_info (author, car_number, img_url, pub_id, cid) values ('%s', '%s', '%s', '%s', %s)"  % (openid, number.upper(), img_path, pub_id, cid)
        print (sql)

        result = get_result(sql)
        if result is None:
            app.logger.error("insert error:" + sql)
            res = {}
            res["ret"] = -1 
            return json.dumps(res)

        has_insert = True
    
    res = {}
    res["ret"] = 0 
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
        
        #http转https,  否则图片预览时可能出现黑屏
        url = url.replace("http:", "https:") 

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



