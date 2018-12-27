# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = "xoxb-507364314564-507974089297-8pt6An998nAZPRUb8VdaExaC"
slack_client_id = "507364314564.508407968388"
slack_client_secret = "bba2a26cc2069c6ed2463d876688083e"
slack_verification = "boPVIRYCriya3f0u76T2mvBR"
sc = SlackClient(slack_token)

# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):
    inp=""
    for i in text[13:]:
        inp+=i
    print(inp)
    #url = re.search(r'(https?://\S+)',text.split("|")[0]).group(0)
    url = 'https://movie.naver.com/movie/sdb/rank/rreserve.nhn'
    req = urllib.request.Request(url)
    
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")
    links=[]
    s1=soup.find_all("div",class_='tit4')[:10]
    for i in s1:
        links.append(url+str(i.find('a')["href"]))
    #print(links)
    context=[]
    for newurl in links:
        req=urllib.request.Request(newurl)
        newsource=urllib.request.urlopen(newurl).read()
        newsoup=BeautifulSoup(newsource,"html.parser")
        context.append((newsoup.find("p",class_="con_tx").get_text().strip()))
    context1=[]
    for url2 in links:
        req=urllib.request.Request(url2)
        newsource1=urllib.request.urlopen(url2).read()
        newsoup1=BeautifulSoup(newsource1,"html.parser")
        context1.append((newsoup1.find("span",class_="st_off").get_text().strip()))
        
        
    s2=soup.find_all("td",class_="reserve_per ar")[:10]
    key_titles=[each.get_text().strip() for each in s1][:10]
    key_percent=[each.get_text().strip() for each in s2][:10]
    keywords=[str(i+1)+"위 : "+key_titles[i]+" / " +context1[i]+" / " " 예매율 :" +key_percent[i] +'\n'+" 줄거리 :"+context[i]+'\n'+'\n' + " 영화정보 :" +links[i] +'\n' for i in range(len(key_titles))]
    
    
    
    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    return u'영화 예매 순위 및 예매율 \n\n'+'\n'.join(keywords)


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        keywords = _crawl_naver_keywords(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )

        return make_response("App mention message has been sent", 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})

@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                            })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})
    
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    if slack_event['event_time'] < (datetime.now() - timedelta(seconds=1)).timestamp():
        return make_response("this message is before sent.", 200, {"X-Slack-No-Retry": 1})

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    app.run('127.0.0.1', port=8080)
