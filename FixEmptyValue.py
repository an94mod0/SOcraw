# not complete
import requests
from bs4 import BeautifulSoup as bs
import types
import re
import pymysql
import time
import sys

db = pymysql.connect("140.138.77.90","knkn","tp6bjo4u;6","knkn",use_unicode=True, charset="utf8mb4")
cursor = db.cursor()
motion="SELECT `aid` FROM  `answers` WHERE  `owner_id` =0 OR `time`='0000-00-00 00:00:00'"
cursor.execute(motion)
results = cursor.fetchall()
problems=[]
for x in range(len(results)):
    problems.append(results[x][0])
print(problems)
if len(problems)<100 and len(problems)>0:
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
    while True: #one answer object every time
        if text.split('"user_type":')[x].split(',')[0]=='"does_not_exist"':
            owner_id='-1'
        else:
            owner_id=text.split('"user_id":')[y].split(',')[0]
            y+=1
        time=text.split('"creation_date":')[x].split(',')[0]
        aid=text.split('"answer_id":')[x].split(',')[0]
        motion+="UPDATE `knkn`.`answers` SET `owner_id` = '"+owner_id+"', `time` = '"+time+"' WHERE `answers`.`aid` = "
        motion+=str(aid)+';\n'
        print(x,' ',str(owner_id),' ',str(time))
        if text.split('"question_id"')[x].split('}')[1][0]==']':
            break
        x+=1
    print(motion)
    cursor.execute(motion)
    db.commit()
    db.close()