# -*- coding:utf-8 -*-

import pymongo
import math
from pymongo import MongoClient
from xz_classifier1105.three_class import naivebayes

conn =  MongoClient('219.224.134.212',27017)
db = conn.gubalyl02

#统计相应“stocksid,sentiment,start_date,end_date”下的帖子数
def account_find(stocksid,sentiment,start_date,end_date):
    collation = "post_stock_"+stocksid
    account = db[collation]
    count_num = account.find({"sentiment":sentiment, "releaseTime": {"$gte": start_date, '$lt': end_date}}).count()
    return count_num

def reclassify(stocksid):
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
        sentiment = naivebayes(post)
        #print post, last_senti, sentiment
        account.update({'_id': idstr}, {'$set':{'sentiment': sentiment}}) 
        count += 1
        if count % 10000 == 0:
            print count, 'done'
    return

#读取沪深300股票+34只股票的stock_id
def get_stocks300():
    stocks300 = []
    with open("new.txt") as f:
        for line in f:
            stockid = line.strip()
            stocks300.append(stockid)
    return stocks300

if __name__ == '__main__':
    stocks300 = get_stocks300()
    unit = len(stocks300) # 411
    for i in range(300,411):
        stocksid = stocks300[i]
        reclassify(stocksid)
        print i, stocksid, 'done'
