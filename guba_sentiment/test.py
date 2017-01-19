# -*- coding:utf-8 -*-
import csv
import math
import json
from xz_classifier1105.three_class import naivebayes as nb_classifier
#from xz_classifier1105.three_class import train_freq
#from guba.xz_classifier.classifier import naivebayes as nb_classifier
#from guba.naivebayes_classifier.naivebayes_classifier import naivebayes as nb_classifier
import pymongo
import math
from pymongo import MongoClient

conn =  MongoClient('219.224.134.212',27017)
db = conn.gubalyl02

'''
fi = open('checkdate_1023.txt')
fo = open('checkdate_1102.txt', 'w')
all = fi.readlines()
all.reverse()
fo.writelines([line for line in all])
fi.close()
fo.close()
'''
def sentiment_count(stockid, start_date, end_date):
    fi = open('../data_json/'+stockid+'.jl')
    pos = 0
    neg = 0
    neu = 0
    for line in fi.readlines():
        try:
            line = json.loads(line)
            em_info = line['em_info']
            releaseTime = line['releaseTime']
            if start_date <= releaseTime < end_date:
                title = line['title']
                content = line['content']
                #print releaseTime, title, content
                post  = {'title': title, 'content':content, 'em_info': em_info}
                #sentiment = nb_classifier(post, parameter)
                sentiment = nb_classifier(post)
                #print sentiment
                if sentiment == 1:
                    pos += 1
                elif sentiment == 0:
                    neg += 1
                else:
                    neu += 1

        except:
            pass
   
    return pos, neg, neu

#统计相应“stocksid,sentiment,start_date,end_date”下的帖子数
def account_find(stocksid,sentiment,start_date,end_date):
    collation = "post_stock_"+stocksid
    account = db[collation]
    count_num = account.find({"sentiment":sentiment, "releaseTime": {"$gte": start_date, '$lt': end_date}}).count()
    return count_num

def all_account_find(stocksid):
    collation = "post_stock_"+stocksid
    account = db[collation]
    count_num = account.find().count()
    neg = account.find({"sentiment":0}).count()
    pos = account.find({"sentiment":1}).count()
    neu = account.find({"sentiment":2}).count()
    print count_num, neg, pos, neu, (neg+pos+neu)
    return count_num

#计算bt指数值
def calculate_bt(count_pos,count_neg):
    index_bt = (count_pos-count_neg)*1.0/(count_pos+count_neg)
    return index_bt

#计算b*指数值
def calculate_bs(index_bt,count_pos,count_neg):
    index_bs = math.log((1.0 + count_pos) / (1.0 + count_neg))
    #index_bs = index_bt*math.log(1.0+count_pos+count_neg)
    return index_bs


#计算某一天具体时间段内的各股的情感指数值
def calculate_bm(start_date,end_date):
    '''
    start_date：计算日具体开始时间段
    end_date：计算日具体结束时间段

    return emotionlist：返回计算日沪深300所有成份股的情感指数值和各类型帖子数量
    '''
    all_pos = all_neg = all_neu = 0
    count = 0
    
    for stocksid in stocks300:
        count_pos, count_neg, count_neu = sentiment_count(stocksid, start_date, end_date)
        #count_pos = account_find(stocksid,1,start_date,end_date)
        #count_neg = account_find(stocksid,0,start_date,end_date)
        
        #统计沪深300股票的所有positive和negative帖子数
        all_pos = all_pos + count_pos
        all_neg = all_neg + count_neg
        all_neu = all_neu + count_neu
        count += 1
        print count, all_pos, all_neg, all_neu
    #计算和保存34支股票、沪深300股票的bt,bs值
    all_bt = calculate_bt(all_pos, all_neg)
    all_bs = calculate_bs(all_bt, all_pos, all_neg)
    emotionlist = [all_pos, all_neg, all_bt, all_bs]

    return emotionlist

def get_stocks300():
    stocks300 = []
    with open(hs300) as f:
        for line in f:
            stockid = line.strip()
            stocks300.append(stockid)
    return stocks300

def emotion(yesterday, today):
    close_time = " 15:00:00"
    start_datestr = yesterday + close_time
    end_datestr = today + close_time

    emotions_today = calculate_bm(start_datestr, end_datestr)    #[all_pos, all_neg, all_bt, all_bs]
    return emotions_today

if __name__ == '__main__':
    count = all_account_find('600809')
    print count
    '''
    hs300 = 'hs300/2014-06-16.txt'
    stocks300 = get_stocks300()
    results = 'results/results_20140616.csv'
    writer = csv.writer(open(results,'wb'))
    writer.writerow(['date','积极帖子数','消极帖子数','原始B','修正B'])

    #训练分类器
    #parameter = train_freq()
    
    yesterday = '2014-10-30'
    today = '2014-10-31'
    emotion_list = emotion(yesterday, today)
    print today, emotion_list
    all_pos = emotion_list[0]
    all_neg = emotion_list[1]
    all_bt = emotion_list[2]
    all_bs = emotion_list[3]
    writer.writerow([today, all_pos, all_neg, all_bt, all_bs])
    '''
