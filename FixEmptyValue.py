# cant handle more than 100 wrong data
import requests
from bs4 import BeautifulSoup as bs
import types
import re
import pymysql
import time
import sys
from datetime import datetime
def unixtodt(unix):
    if type(unix) is not type(999):
        return str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(unix))))
    else:
        return str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(unix)))


db = pymysql.connect("140.138.77.90","knkn","tp6bjo4u;6","knkn",use_unicode=True, charset="utf8mb4")
cursor = db.cursor()
motion="SELECT `aid` FROM  `answers` WHERE `time`='0000-00-00 00:00:00' AND `owner_id`=0"
cursor.execute(motion)
results = cursor.fetchall()
problems=[]
for x in range(len(results)):
    problems.append(results[x][0])
print('wrong data list: ',problems)
if len(problems)<=100 and len(problems)>0:
    url="https://api.stackexchange.com/2.2/answers/"
    for x in range(len(problems)):
        if x is not 0: url+=';'
        url+=str(problems[x])
    url+="?pagesize=100&order=desc&sort=activity&site=stackoverflow"
    print(url)
    text=bs(requests.get(url).text,'html.parser').text
    x=1
    y=1
    motion=""
    while True: #one answer object every time\
        if text.split('"user_type":')[x].split(',')[0]=='"does_not_exist"':
            owner_id='-1'
        else:
            owner_id=text.split('"user_id":')[y].split(',')[0]
            y+=1
        timestamp=int(text.split('"creation_date":')[x].split(',')[0])
        dt=unixtodt(timestamp)
        aid=text.split('"answer_id":')[x].split(',')[0]
        motion+="UPDATE `knkn`.`answers` SET `owner_id` = '"+owner_id+"', `time` = '"+dt+"' WHERE `answers`.`aid` = "
        motion+=str(aid)+';\n'
        print(x,' ',str(owner_id),' ',str(dt))
        if text.split('"question_id"')[x].split('}')[1][0]==']':
            break
        x+=1
    print(motion)
    cursor.execute(motion)
    db.commit()
    db.close()
    print('update data success')
elif len(problems) is 0:
    print('all data are clear')
else:
    print('too many problem')