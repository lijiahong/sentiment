# -*- coding: utf-8 -*-
import os
import csv
import re
import time
import datetime
import json
#from elasticsearch import Elasticsearch
from guba.xz_classifier.classifier import naivebayes as nb_classifier
import pymongo
import math
from pymongo import MongoClient

conn =  MongoClient('219.224.134.212',27017)
db = conn.gubalyl02


#读取沪深300股票+34只股票的stock_id
def get_stocks300():
    stocks300 = []
    with open(hs300) as f:
        for line in f:
            stockid = line.strip()
            stocks300.append(stockid)
    return stocks300

def get_stocks34():
    stocks34 = []
    with open('stocks34.txt') as f:
        for line in f:
            stockid = line.strip()
            stocks34.append(stockid)
    return stocks34

#统计相应“stocksid,sentiment,start_date,end_date”下的帖子数
def account_find(stocksid,sentiment,start_date,end_date):
    collation = "post_stock_"+stocksid
    account = db[collation]
    count_num = account.find({"sentiment":sentiment, "releaseTime": {"$gte": start_date, '$lt': end_date}}).count()
    return count_num

def sentiment_count(stockid, start_date, end_date):
    pos = neg = neu = 0
    try:
        fi = open('../data_json/'+stockid+'.jl')
    except:
        return pos, neg, neu
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
                sentiment = nb_classifier(post)
                #print line['post_id']
                if sentiment == 1:
                    pos += 1
                elif sentiment == 0:
                    neg += 1
                else:
                    neu += 1

        except:
            pass
    return pos, neg, neu

'''
def sentiment_count(stocksid,start_date,end_date):
    collation = "post_stock_"+stocksid
    account = db[collation]
    count_num = account.find({"releaseTime": {"$gte": start_date, '$lt': end_date}})
    pos = neg = neu = 0
    for item in count_num:
        try:
            em_info = item['em_info']
        except:
            em_info = None
        title = item['title']
        content = item['content']
        post = {'title':title, 'content': content, 'em_info':em_info} 
        sentiment = naivebayes(post, parameter)
        if sentiment == 1:
            pos += 1
        elif sentiment == 0:
            neg += 1
        else:
            neu += 1
        
    return pos, neg, neu
'''
#计算bt指数值
def calculate_bt(count_pos,count_neg):
    index_bt = (count_pos-count_neg)*1.0/(count_pos+count_neg+1.0)
    return index_bt

#计算b*指数值
def calculate_bs(index_bt,count_pos,count_neg):
    index_bs = math.log((1.0 + count_pos) / (1.0 + count_neg))
    #index_bs = index_bt*math.log(1.0+count_pos+count_neg)
    return index_bs

def calculate_bz(index_bt, count_pos, count_neg, count_neu):
    index_bz = index_bt*math.log(1.0+count_pos+count_neg+count_neu)
    return index_bz

#计算某一天具体时间段内的各股的情感指数值
def calculate_bm(start_date,end_date):
    '''
    start_date：计算日具体开始时间段
    end_date：计算日具体结束时间段

    return emotionlist：返回计算日沪深300所有成份股的情感指数值和各类型帖子数量
    '''
    all_pos = all_neg = all_neu = 0
    stock_dict = {}
    
    for stocksid in stocks300:
        #count_pos, count_neg, count_neu = sentiment_count(stocksid, start_date, end_date)
        
        count_pos = account_find(stocksid,1,start_date,end_date)
        count_neg = account_find(stocksid,0,start_date,end_date)
        count_neu = account_find(stocksid,2,start_date,end_date)
        
        #print stocksid, count_pos, count_neg, count_neu
        index_bt = calculate_bt(count_pos,count_neg)
        index_bs = calculate_bs(index_bt,count_pos,count_neg)
        stock_dict[stocksid] = [count_pos, count_neg, count_neu, index_bt, index_bs] #保存个股情感指数值
        
        #统计沪深300股票的所有positive和negative帖子数
        all_pos = all_pos + count_pos
        all_neg = all_neg + count_neg
        all_neu = all_neu + count_neu
    
    #计算和保存34支股票、沪深300股票的bt,bs值
    all_bt = calculate_bt(all_pos, all_neg)
    all_bs = calculate_bs(all_bt, all_pos, all_neg)
    all_bz = calculate_bz(all_bt, all_pos, all_neg, all_neu)
    emotionlist = [all_pos, all_neg, all_neu, all_bt, all_bs, all_bz]
    return emotionlist, stock_dict

#汇总日度交易段和非交易段的各股的情感指数值
def today_emotion(yesterday, today):
    open_time = " 09:00:00" #开盘时间
    close_time = " 15:00:00" #收盘时间

    off_start_datestr = yesterday + close_time
    off_end_datestr = today + open_time

    on_start_datestr = today + open_time
    on_end_datestr = today + close_time

    emotions_off = calculate_bm(off_start_datestr, off_end_datestr)
    emotions_on = calculate_bm(on_start_datestr, on_end_datestr)

    emotions_today = {"off":emotions_off, "on":emotions_on}

    return emotions_today

#汇总日度、周度、月度下的各股的情感指数值（收盘至收盘）
def emotion(yesterday, today):
    close_time = " 15:00:00"
    start_datestr = yesterday + close_time
    end_datestr = today + close_time

    emotions_today, stock_dict = calculate_bm(start_datestr, end_datestr)    #[all_pos, all_neg, all_neu, all_bt, all_bs, all_bz]

    return emotions_today, stock_dict

def hs300_main():
    hs300_list = ['2014-06-16', '2014-12-15', '2015-06-15', '2015-12-14', '2016-06-13'] 
    file_list = ['20141103', '20141215', '20150615', '20151214', '20160613']
    unit = 'month'
    
    for order in range(len(file_list)):
        hs300 = 'hs300/' + hs300_list[order] + '.txt'
        stocks300 = get_stocks300()

        results = 'results/' + unit + '/results_' + file_list[order] + '.csv'
        #results = 'results/test.csv'
        writer = csv.writer(open(results,'wb'))
        writer.writerow(['date','积极帖子数','消极帖子数','中性帖子数', '原始B','修正B', '中性B'])
        #writer.writerow(['date','交易时段积极帖子数','交易时段消极帖子数','交易时段中性帖子数','交易时段原始B','交易时段修正B','交易时段中性B', \
        #                 '非交易时段积极帖子数', '非交易时段消极帖子数','非交易时段中性帖子数', '非交易时段原始B', '非交易时段修正B', '非交易时段中性B'])
        
        name = 'cal_date/' + unit + '/date_' + file_list[order] + '.txt'
        fi = open(name)
        date_list = fi.readlines()
        print 'start calculating', order
        for i in range(1, len(date_list)):
            yesterday = date_list[i-1][:10]
            today = date_list[i][:10]
                   
            emotion_list = emotion(yesterday, today) #计算当日各股情感指数
            print today, emotion_list
            all_pos = emotion_list[0]
            all_neg = emotion_list[1]
            all_neu = emotion_list[2]
            all_bt = emotion_list[3]
            all_bs = emotion_list[4]
            all_bz = emotion_list[5]
            writer.writerow([today, all_pos, all_neg, all_neu, all_bt, all_bs, all_bz])
            '''
            emotion_dict = today_emotion(yesterday, today) #计算当日各股情感指数
            print today, emotion_dict
            on_emotion_list = emotion_dict['on']
            on_all_pos = on_emotion_list[0]
            on_all_neg = on_emotion_list[1]
            on_all_neu = on_emotion_list[2]
            on_all_bt = on_emotion_list[3]
            on_all_bs = on_emotion_list[4]
            on_all_bz = on_emotion_list[5]
            off_emotion_list = emotion_dict['off']
            off_all_pos = off_emotion_list[0]
            off_all_neg = off_emotion_list[1]
            off_all_neu = off_emotion_list[2]
            off_all_bt = off_emotion_list[3]
            off_all_bs = off_emotion_list[4]
            off_all_bz = off_emotion_list[5]
            writer.writerow([today, on_all_pos, on_all_neg, on_all_neu, on_all_bt, on_all_bs, on_all_bz, off_all_pos, off_all_neg, off_all_neu, off_all_bt, off_all_bs, off_all_bz])
            '''

if __name__ == "__main__":
    '''
    hs300 = 'hs300/2013-04-01.txt'
    stocks300 = get_stocks300()
    stocks300 = ['600809']
    yesterday = '2013-03-29'
    today = '2013-04-01'
    #yesterday = '2013-04-25'
    #today = '2013-04-26'
    emotion_list, stock_dict = emotion(yesterday, today) #计算当日各股情感指数
    print emotion_list
    '''
    '''
    stock_results = 'results/test_stocks.csv'
    stock_writer = csv.writer(open(stock_results, 'wb'))
    stock_writer.writerow(['date','股票代码','积极帖子数','消极帖子数','中性帖子数', '原始B','修正B'])
    for stockid in stock_dict:
        stock_index = stock_dict[stockid]
        count_pos = stock_index[0]
        count_neg = stock_index[1]
        count_neu = stock_index[2]
        index_bt = stock_index[3]
        index_bs = stock_index[4]
        stock_writer.writerow([today, stockid, count_pos, count_neg, count_neu, index_bt, index_bs])
    '''
    
    hs300 = 'new.txt'
    stocks300 = get_stocks300()
    stocks300 = ['600809']
    name = 'cal_date/month/month_test.txt'
    results = 'results/411_month_test.csv'
    writer = csv.writer(open(results,'wb'))
    writer.writerow(['date','股票代码','积极帖子数','消极帖子数','中性帖子数', '原始B','修正B'])

    fi = open(name)
    date_list = fi.readlines()
    print 'start calculating'
    for i in range(1, len(date_list)):
        yesterday = date_list[i-1][:10]
        today = date_list[i][:10]
           
        emotion_list, stock_dict = emotion(yesterday, today) #计算当日各股情感指数
        print today, emotion_list
        for stockid in stock_dict:
            stock_index = stock_dict[stockid]
            count_pos = stock_index[0]
            count_neg = stock_index[1]
            count_neu = stock_index[2]
            index_bt = stock_index[3]
            index_bs = stock_index[4]
            writer.writerow([today, stockid, count_pos, count_neg, count_neu, index_bt, index_bs])
