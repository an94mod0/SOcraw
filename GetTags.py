import requests
import pymysql
import json
import time
psize=100
page=1
endpage=100
def apostrophed(text):
    new_text=""
    for c in text:
        if c=='\'': new_text+="''"
        elif c=='\\': new_text+=""
        else : new_text+=c
    return new_text
me=json.loads(open('account.json',encoding = 'utf8').read().encode('utf8'))
db = pymysql.connect(me['host'],me['username'],me['password'],me['db'],use_unicode=True, charset="utf8mb4")
cursor = db.cursor()
while True:
    #print(page)
    APIurl="https://api.stackexchange.com/2.2/tags?page="+str(page)+"&pagesize="+str(psize)
    APIurl+="&order=desc&sort=popular&site=stackoverflow"
    text=requests.get(APIurl).json()
    for x in text['items']:
        count=1
        command="INSERT INTO `knkn`.`tags` VALUES (NULL, '"+apostrophed(x['name'])+"', '"+str(x['count'])+ "');"
        cursor.execute(command)
    if page==endpage:
        break
    if text['has_more']:
        page+=1
        if 'backoff' in text:
            time.sleep(text['backoff'])
    else:
        break
db.commit()
db.close()