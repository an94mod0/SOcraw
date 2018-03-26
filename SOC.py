"""
2018/03/23最後修改

"""
import requests
from bs4 import BeautifulSoup as bs
import types
import re
import pymysql
import time
import sys
#上傳文字到SQL前做跳脫處理
def apostrophed(text):
    new_text=""
    for c in text:
        if c=='\'': new_text+="''"
        elif c=='\\': new_text+=""
        else : new_text+=c
    return new_text

#餵BS物件，完成question爬取與executeSQL，吐被採用答案(right_ans)
def handleQ(page): 
    if page.find('span',class_='vote-accepted-on load-accepted-answer-date') is not None:
        solved="1"
        right_ans=page.find('span',class_='vote-accepted-on load-accepted-answer-date').parent.find('input')['value']
    else:
        solved="0"
        right_ans="0"
    title=page.find('h1',itemprop='name').text
    question=page.find('div',class_='question')
    qID=question['data-questionid']
    if question.find('a',href=re.compile(r'^/users/') ) is not None:
        ownerID=question.find('a',href=re.compile(r'^/users/'))['href'].split('users/')[1].split('/')[0]
    else: return 
    if question.find('div',class_='user-action-time') is not None:
        time=question.find('div',class_='user-action-time').find('span')['title'].split('Z')[0]
    else: time='0000-00-00 00:00:00'
    posts=""
    for x in question.find('div',class_='post-text').children:
        posts+=str(x)
    score=question.find('span',itemprop='upvoteCount').text
    tags=""
    if question.find('div',class_='post-taglist') is not None:
        for x in question.find('div',class_='post-taglist').find_all('a'):
            if tags=="": tags=x.text
            else: tags=tags+","+x.text
    add_question="INSERT INTO `knkn`.`questions` VALUES (NULL, '"+str(qID)+"', '"+apostrophed(title)+"', '"+tags+"', '"+ownerID+"', '"+score+"', '"+solved+"', '"+time+"', '"+apostrophed(posts)+"');"
    add_comment="INSERT INTO  `knkn`.`comments` VALUES "
    for comm in question.find_all('li',id=re.compile(r'^comment-')):
        cID=comm["data-comment-id"]
        comment=comm.find('span',class_='comment-copy').text
        ownerID='0'
        if comm.find('a',class_=re.compile(r'^comment-user')) is not None:
            ownerID=comm.find('a',class_=re.compile(r'^comment-user'))['href'].split('users/')[1].split('/')[0]
        if comm.find('span',class_='relativetime-clean') is not None:
            time=comm.find('span',class_='relativetime-clean')['title'].split('Z')[0]
        else: time='0000-00-00 00:00:00'
        if add_comment[-2]!='S': add_comment+=","
        add_comment+="(NULL, '"+cID+"', '"+qID+"','0','"+ownerID+"', '"+time+"', '"+apostrophed(comment)+"')"
    cursor.execute(add_question)
    if add_comment[-2]!='S': cursor.execute(add_comment+";")
    return right_ans

#餵BS物件與被採用答案，完成Answer爬取與executeSQL
def handleA(page,right_ans):
    add_answer="INSERT INTO `knkn`.`answers`VALUES "
    for father in page.find_all('div',id=re.compile(r'^answer-') ):
        aID=father['data-answerid']
        if aID==right_ans: solved="1"
        else: solved="0"
        posts=""
        for x in father.find('div',class_='post-text').children:
            posts+=str(x)
        score=father.find('span',itemprop='upvoteCount').text
        if father.find('a',href=re.compile(r'^/users/')) is not None:
            ownerID=father.find('a',href=re.compile(r'^/users/'))['href'].split('users/')[1].split('/')[0]
        else: ownerID='0'
        #print(type(father.find('div',class_='user-action-time')))
        if father.find('div',class_='user-action-time') is not None:
            time=father.find('div',class_='user-action-time').find('span')['title'].split('Z')[0]
        else: time='0000-00-00 00:00:00'
        if add_answer[-2]!='S':add_answer+=","
        add_answer+="(NULL, '"+aID+"', '"+qID+"', '"+ownerID+"', '"+score+"', '"+solved+"', '"+time+"', '"+apostrophed(posts)+"')"
        add_comment="INSERT INTO  `knkn`.`comments` VALUES "
        for comm in father.find_all('li',id=re.compile(r'^comment-')):
            cID=comm["data-comment-id"]
            comment=comm.find('span',class_='comment-copy').text
            if comm.find('a',class_=re.compile(r'^comment-user')) is not None:
                ownerID=comm.find('a',class_=re.compile(r'^comment-user'))['href'].split('users/')[1].split('/')[0]
            else: ownerID='0'
            if comm.find('span',class_='relativetime-clean') is not None:
                time=comm.find('span',class_='relativetime-clean')['title'].split('Z')[0]
            else: time='0000-00-00 00:00:00'
            if add_comment[-2]!='S': add_comment+=","
            add_comment+="(NULL, '"+cID+"', '"+aID+"','1','"+ownerID+"', '"+time+"', '"+apostrophed(comment)+"')"
        if add_comment[-2]!='S': cursor.execute(add_comment+";")
    if add_answer[-2]!='S': 
        cursor.execute(add_answer+";")

#把DATETIME轉成UNIXtime
def dttounix(dt):
    return int(time.mktime(time.strptime(dt, '%Y-%m-%d %H:%M:%S')))

#餵起訖時間回傳有一堆questionID的陣列
def GetqIDs(s,e,m):
    Qlist=[]
    start=dttounix(s)
    end=dttounix(e)
    page=1
    psize=100 #一頁有100個question object
    minscore=m
    while True: #每次迴圈就是翻一頁
        url="https://api.stackexchange.com/2.2/questions?page="+str(page)+"&pagesize="+str(psize)+"&fromdate="+str(start)+"&todate="+str(end)+"&order=desc&min="+str(minscore)+"&sort=votes&site=stackoverflow"
        text=bs(requests.get(url).text,'html.parser').text
        if text.split('"items":')[1][0:2]=='[]': break
        x=1
        sys.stdout.write('\rloading page '+str(page))
        sys.stdout.flush()
        while True: #每次迴圈是一個question object
            qID=text.split('"question_id":')[x].split(',')[0]
            if qID[-1]=='}': #特殊情況
                Qlist.append(qID[0:-1])
            else:
                Qlist.append(qID)
                if text.split('"question_id":')[x].split('],')[1][1]=='h':
                    break
            x+=1
        if text.split('"has_more":')[1][0:4]=="true": #還有下一頁
            page+=1
        else: break
        if text.find('backoff') is not -1:
            time.sleep(10) # 避免過度頻繁呼叫API
    return Qlist


db = pymysql.connect("140.138.77.90","knkn","tp6bjo4u;6","knkn",use_unicode=True, charset="utf8mb4")
cursor = db.cursor()

qIDs=GetqIDs('2016-03-21 00:00:00','2016-03-25 23:59:59',20)
print('\rall ',len(qIDs),' qIDs are loaded')
print('crawling data now..')
counter=1
for qID in qIDs:
    url="https://stackoverflow.com/questions/"+qID
    page=bs(requests.get(url).text,'html.parser')
    right_ans=handleQ(page)
    handleA(page,right_ans)
    db.commit()
    sys.stdout.write('\r完成度: {:.2%}'.format(counter/len(qIDs)))
    sys.stdout.flush()
    counter+=1
db.close()
print("\nProgress Finish!!")
