import requests
from bs4 import BeautifulSoup as bs
import types
import re
import pymysql
import time
import sys
import json
#rewrite string to fit SQL syntax
def apostrophed(text):
    new_text=""
    for c in text:
        if c=='\'': new_text+="''"
        elif c=='\\': new_text+=""
        else : new_text+=c
    return new_text

def dttounix(dt):
    return int(time.mktime(time.strptime(dt, '%Y-%m-%d %H:%M:%S')))
def unixtodt(unix):
    if type(unix) is not type(999):
        return str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(unix))))
    else:
        return str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(unix)))
    

#crawl question,comment and upload to database, inquire API if necessary
#parameter: beautyfulsoup object of one question page
#return: right answer of this question, 0 if not found
def handleQ(page):
    callAPI=False
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
    else: ownerID='0'
    if question.find('div',class_='user-action-time') is not None:
        create_time=question.find('div',class_='user-action-time').find('span')['title'].split('Z')[0]
    else: cacllAPI=True 
    if ownerID=='0' or ownerID=='-1' :
        callAPI=True
    posts=""
    for x in question.find('div',class_='post-text').children:
        posts+=str(x)
    score=question.find('span',itemprop='upvoteCount').text
    tags=""
    if question.find('div',class_='post-taglist') is not None:
        for x in question.find('div',class_='post-taglist').find_all('a'):
            if tags=="": tags=x.text
            else: tags=tags+","+x.text
    last_active_time='0000-00-00 00:00:00'
    if callAPI:
        global callCount
        callCount+=1
        APIurl="https://api.stackexchange.com/2.2/questions/"+qID+"?order=desc&sort=activity&site=stackoverflow"
        #print(' callAPI-Question')
        #print(APIurl)
        info=(requests.get(APIurl).json())['items'][0]
        if 'user_id' in info['owner']:
            ownerID=str(info['owner']['user_id'])
        else: ownerID='0'
        create_time=unixtodt(info['creation_date'])
        last_active_time=unixtodt(info['last_activity_date'])
    add_question="INSERT INTO `knkn`.`questions` VALUES (NULL, '"+str(qID)+"', '"+apostrophed(title)+"', '"+tags+"', '"+ownerID+"', '"+score+"', '"+solved+"', '"+create_time+"', '"+last_active_time+"', '"+apostrophed(posts)+"');"
    add_comment="INSERT INTO  `knkn`.`comments` VALUES "
    #comment part
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

#crawl answer,comment and upload to database, inquire API if necessary
#parameter: beautyfulsoup object of one question page
#return: none
def handleA(page,right_ans):
    add_answer="INSERT INTO `knkn`.`answers`VALUES "
    for answer in page.find_all('div',id=re.compile(r'^answer-') ):
        callAPI=False
        aID=answer['data-answerid']
        if aID==right_ans: solved="1"
        else: solved="0"
        posts=""
        for x in answer.find('div',class_='post-text').children:
            posts+=str(x)
        score=answer.find('span',itemprop='upvoteCount').text
        if answer.find('a',href=re.compile(r'^/users/')) is not None:
            ownerID=answer.find('a',href=re.compile(r'^/users/'))['href'].split('users/')[1].split('/')[0]
        else: ownerID='0'
        if answer.find('div',class_='user-action-time') is not None:
            create_time=answer.find('div',class_='user-action-time').find('span')['title'].split('Z')[0]
        else:callAPI=True
        if ownerID=='0' or ownerID=='-1' :
            callAPI=True
        if callAPI:
            global callCount
            callCount+=1
            APIurl="https://api.stackexchange.com/2.2/answers/"+aID+"?order=desc&sort=activity&site=stackoverflow"
            #print(' callAPI-Answer')
            #print(APIurl)
            info=(requests.get(APIurl).json())['items'][0]
            if 'user_id' in info['owner']:
                ownerID=str(info['owner']['user_id'])
            else: ownerID='0'
            create_time=unixtodt(info['creation_date'])
        if add_answer[-2]!='S':add_answer+=","
        add_answer+="(NULL, '"+aID+"', '"+qID+"', '"+ownerID+"', '"+score+"', '"+solved+"', '"+create_time+"', '"+apostrophed(posts)+"')"
        #comment part
        add_comment="INSERT INTO  `knkn`.`comments` VALUES "
        for comm in answer.find_all('li',id=re.compile(r'^comment-')):
            cID=comm["data-comment-id"]
            comment=comm.find('span',class_='comment-copy').text
            if comm.find('a',class_=re.compile(r'^comment-user')) is not None:
                ownerID=comm.find('a',class_=re.compile(r'^comment-user'))['href'].split('users/')[1].split('/')[0]
            else: ownerID='0'
            if comm.find('span',class_='relativetime-clean') is not None:
                create_time=comm.find('span',class_='relativetime-clean')['title'].split('Z')[0]
            else: create_time='0000-00-00 00:00:00'
            if add_comment[-2]!='S': add_comment+=","
            add_comment+="(NULL, '"+cID+"', '"+aID+"','1','"+ownerID+"', '"+create_time+"', '"+apostrophed(comment)+"')"
        if add_comment[-2]!='S': cursor.execute(add_comment+";")
    if add_answer[-2]!='S': 
        cursor.execute(add_answer+";")

#use API to get list of qID
#parameter: start time,end time,min score,max score (all str type)
#return: list contain all qID (str type)
def GetqIDs(s,e,mi='0',ma=""):
    Qlist=[]
    start=dttounix(s)
    end=dttounix(e)
    page=1
    psize=100 #100 question object / page
    minscore=mi
    maxscore=ma
    while True: #one page every loop
        global callCount
        callCount+=1
        sys.stdout.write('\rloading page '+str(page))
        sys.stdout.flush()
        url="https://api.stackexchange.com/2.2/questions?page="+str(page)+"&pagesize="+str(psize)+"&fromdate="+str(start)+"&todate="+str(end)+"&order=desc&min="+str(minscore)+"&max="+str(maxscore)+"&sort=votes&site=stackoverflow"
        text=requests.get(url=url).json()
        for question in text['items']:
            qid=str(question['question_id'])
            Qlist.append(qid)
        if text["has_more"]: page+=1
        else: break
        if 'backoff' in text:
            time.sleep(text['backoff'])
    return Qlist

me=json.loads(open('account.json',encoding = 'utf8').read().encode('utf8'))
db = pymysql.connect(me['host'],me['username'],me['password'],me['db'],use_unicode=True, charset="utf8mb4")
cursor = db.cursor()
callCount=0
# # set factor
# start_time=input('start time(YYYY-MM-DD HH:MM:SS): ')
# end_time=input('end time(YYYY-MM-DD HH:MM:SS): ')
# try:
   # t=dttounix(start_time)
   # t=dttounix(end_time)
# except:
   # print('time format error')
# min_score=str(input('min score: '))
# max_score=str(input('max score: '))
# qIDs=GetqIDs(start_time,end_time,min_score,max_score)
qIDs=GetqIDs('2018-03-23 00:00:00','2018-03-25 23:59:59',5)
print('\rall ',len(qIDs),' qIDs are loaded')
print('crawling data now..')
counter=1
for qID in qIDs:
    url="https://stackoverflow.com/questions/"+qID
    page=bs(requests.get(url).text,'html.parser')
    right_ans=handleQ(page)
    handleA(page,right_ans)
    db.commit()
    sys.stdout.write('\rProgress Rate: {:.2%}'.format(counter/len(qIDs)))
    sys.stdout.flush()
    counter+=1
db.close()
print('\nCall API ',callCount,' times')
print("Progress Finish!!")
