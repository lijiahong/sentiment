# -*- coding:utf-8 -*-

import pymongo
import math
from pymongo import MongoClient
from new_classifier.nb_classifier import naivebayes, train_freq, check_test

conn =  MongoClient('219.224.134.212',27017)
db = conn.gubalyl02

#统计相应“stocksid,sentiment,start_date,end_date”下的帖子数
def account_find(stocksid,sentiment,start_date,end_date):
    collation = "post_stock_"+stocksid
    account = db[collation]
    count_num = account.find({"sentiment":sentiment, "releaseTime": {"$gte": start_date, '$lt': end_date}}).count()
    return count_num

#读取沪深300股票+34只股票的stock_id
def get_stocks300(stocks_file):
    stocks300 = []
    with open(stocks_file) as f:
        for line in f:
            stockid = line.strip()
            stocks300.append(stockid)
    return stocks300

def reclassify():
    stocks_file = 'new.txt'
    stocks300 = get_stocks300(stocks_file)
    REP_TIMES = 5
    all_para = []
    for i in REP_TIMES:
        para_list = train_freq()
        all_para.append(para_list)

    unit = len(stocks300) # 411
    for i in range(300,411):
        stocksid = stocks300[i]
        collation = "post_stock_"+stocksid
        account = db[collation]
        all_item = account.find()
        count = 0
        for item in all_item:
            #print item
            idstr = item['_id']
            try:
                title = item['title']
            except:
                title = u''
            try:
                em_info = item['em_info']
            except:
                em_info = None
            try:
                content = item['content']
            except:
                content = u''
            #last_senti = item['sentiment']
            post = {'title': title, 'content': content, 'em_info':em_info}
            senti_list = [0, 0, 0]
            for i in range(len(all_para)):
                para_list = all_para[i]
                senti = naivebayes(post, para_list)
                senti_list[senti] += 1
            sentiment = senti_list.index(max(senti_list))
            #print post,sentiment
            account.update({'_id': idstr}, {'$set':{'sentiment': sentiment}}) 
            count += 1
            if count % 10000 == 0:
                print count, 'done'

        print i, stocksid, 'done'

def cross_validate():
    VALIDATE_TIMES = 5
    for i in range(0,VALIDATE_TIMES):
        print i
        check_test(i)


if __name__ == '__main__':
    #reclassify()
    cross_validate()
    
