# -*- coding: utf-8 -*- 

import os
import scws
import time
import csv
import re
import random
import math
import sys
from collections import Counter
reload(sys)
sys.setdefaultencoding('utf8')
##from svmutil import *

SCWS_ENCODING = 'utf-8'
SCWS_RULES = '/usr/local/scws/etc/rules.utf8.ini'
CHS_DICT_PATH = '/usr/local/scws/etc/dict.utf8.xdb'
CHT_DICT_PATH = '/usr/local/scws/etc/dict_cht.utf8.xdb'
IGNORE_PUNCTUATION = 1

P_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), './'))

ABSOLUTE_DICT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), './dict'))
CUSTOM_DICT_PATH = os.path.join(ABSOLUTE_DICT_PATH, 'userdic.txt')
EXTRA_STOPWORD_PATH = os.path.join(ABSOLUTE_DICT_PATH, 'stopword.txt')
EXTRA_EMOTIONWORD_PATH = os.path.join(ABSOLUTE_DICT_PATH, 'emotionlist.txt')
EXTRA_ONE_WORD_WHITE_LIST_PATH = os.path.join(ABSOLUTE_DICT_PATH, 'one_word_white_list.txt')
EXTRA_BLACK_LIST_PATH = os.path.join(ABSOLUTE_DICT_PATH, 'black.txt')

cx_dict = ['a','n','nr','ns','nt','nz','v','@','d']#关键词词性词典,考虑加入副词d

def load_scws():
    s = scws.Scws()
    s.set_charset(SCWS_ENCODING)

    s.set_dict(CHS_DICT_PATH, scws.XDICT_MEM)
    s.add_dict(CHT_DICT_PATH, scws.XDICT_MEM)
    s.add_dict(CUSTOM_DICT_PATH, scws.XDICT_TXT)

    # 把停用词全部拆成单字，再过滤掉单字，以达到去除停用词的目的
    s.add_dict(EXTRA_STOPWORD_PATH, scws.XDICT_TXT)
    # 即基于表情表对表情进行分词，必要的时候在返回结果处或后剔除
    s.add_dict(EXTRA_EMOTIONWORD_PATH, scws.XDICT_TXT)

    s.set_rules(SCWS_RULES)
    s.set_ignore(IGNORE_PUNCTUATION)
    return s

def load_one_words():
    one_words = [line.strip('\r\n') for line in file(EXTRA_ONE_WORD_WHITE_LIST_PATH)]
    return one_words

def load_black_words():
    one_words = [line.strip('\r\n') for line in file(EXTRA_BLACK_LIST_PATH)]
    return one_words

single_word_whitelist = set(load_one_words())
single_word_whitelist |= set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')

def read_train():
    '''
    读入训练数据
    '''
    different_data = {}
    #问题标注
    reader = csv.reader(file(os.path.join(P_PATH, './second_label/second_label_reserved_1.csv'),'rb'))
    for id, content,title,em_info,stock_name,label in reader:
        different_data[id] = [id,content,title,em_info,stock_name,label,'different']
    #问题标注，部标
    reader = csv.reader(file(os.path.join(P_PATH, './second_label/second_label_reserved_2.csv'),'rb'))
    for id,content,title,em_info,stock_name,label in reader:
        different_data[id] = [id,content,title,em_info,stock_name,label,'different']
    ##    print len(different_data.keys())
            
    data_neg = []
    data_neu = []
    data_p = []
    not_train_count = 0
    info_type = [u'数据',u'新闻',u'研报',u'公告']
    datadir = os.path.join(P_PATH, './label0403/lab_labeled/label_csv/')
    files = os.listdir(datadir)
    for fname in files:
        reader = csv.reader(file(datadir+fname,'rb'))
        for id,content,title,em_info,stock_name,label in reader:
            if id not in different_data.keys():
                text = content+title
                if len(text)<284 and (em_info!=None) and (em_info.decode("utf8") not in info_type):
                    if label == '-1' or label == '2':
                        data_neu.append([id,content,title,em_info,stock_name,'2','same'])
                    elif label == '1':
                        data_p.append([id,content,title,em_info,stock_name,label,'same'])
                    else:
                        data_neg.append([id,content,title,em_info,stock_name,label,'same'])
                else:
                    not_train_count += 1
            else:
                text = different_data[id][1]+different_data[id][2]
                label = different_data[id][5]
                if len(text)<284 and (different_data[id][2]!=None) and (different_data[id][2].decode("utf8") not in info_type):
                    if label == '-1' or label == '2':
                        data_neu.append(different_data[id])
                    elif label == '1':
                        data_p.append(different_data[id])
                    else:
                        data_neg.append(different_data[id])
                else:
                    not_train_count += 1
                
    #print not_train_count,len(data_neg),len(data_neu),len(data_p)
    return data_neg,data_neu,data_p

def train_freq():
    '''
    训练分类模型
    '''
    data_neg,data_neu,data_p = read_train()
    train_neg = []
    train_neu = []
    train_p = []
    list_len = [len(data_neg),len(data_neu),len(data_p)]
    min_index = list_len.index(min(list_len))
    if min_index == 0:
        rand_neu = [random.randint(0,len(data_neu)-1)for i in range(min(list_len))]
        rand_p = [random.randint(0,len(data_p)-1)for i in range(min(list_len))]
        train_neg = data_neg
        for item in rand_neu:
            train_neu.append(data_neu[item])
        for item in rand_p:
            train_p.append(data_p[item])
    elif min_index == 1:
        rand_neg = [random.randint(0,len(data_neg)-1)for i in range(min(list_len))]
        rand_p = [random.randint(0,len(data_p)-1)for i in range(min(list_len))]
        train_neu = data_neu
        for item in rand_neg:
            train_neg.append(data_neg[item])
        for item in rand_p:
            train_p.append(data_p[item])
    else:
        rand_neg = [random.randint(0,len(data_neg)-1)for i in range(min(list_len))]
        rand_neu = [random.randint(0,len(data_neu)-1)for i in range(min(list_len))]
        train_p = data_p
        for item in rand_neg:
            train_neg.append(data_neg[item])
        for item in rand_neu:
            train_neu.append(data_neu[item])            
    #print 'train_neg:%s;train_neu:%s;train_p:%s'%(len(train_neg),len(train_neu),len(train_p))

    #统计每类下词频(等比例抽样)
    f_neg = freq_word(train_neg)
    f_neu = freq_word(train_neu)
    f_p = freq_word(train_p)
    #统计每类下词频（非等比例抽样）
    #f_neg = freq_word(data_neg)
    #f_neu = freq_word(data_neu)
    #f_p = freq_word(data_p)

    #统计各类下单词总数（算重复）、估算重复单词数、文档单词个数
    negative_total,negative_word_count,neutral_total,neutral_word_count,positive_total,positive_word_count,total,dic_len=word_count(f_neg,f_neu,f_p)

    #参数列表
    para_list = [f_neg,f_neu,f_p,negative_total,negative_word_count,neutral_total,neutral_word_count,positive_total,positive_word_count,total,dic_len]
    
    return para_list

def naivebayes_main(para_list,data):
    
    result_lable = naivebayes(para_list,data)

    return result_lable
    

def freq_word(data):
    '''
    统计指定数据下词及词频
    '''
    
    sw = load_scws()
    black = load_black_words()
    addition = [u'!',u'如何',u'怎么',u'什么']
    word_list = []
    for i in range(len(data)):
        text = data[i][1] + '***' + data[i][2]
        words = sw.participle(text)
        word_list.extend([term for term,cx in words if cx in cx_dict and (3<len(term)<30 or term in single_word_whitelist) and (term not in black)])
    word_list.extend(addition)
    
    counter = Counter(word_list)
    #freq_word = {k:v for k,v in counter.most_common() if v>=3}
    freq_word = {k:v for k,v in counter.most_common()}
    
    return freq_word

def word_count(f_neg,f_neu,f_p):
    
    negative_total = sum([v for k,v in f_neg.iteritems()])#negative类下所有单词总数（含一个单词多次出现）
    negative_word_count = len(f_neg)#negative类下单词表总数（不算重复）

    positive_total = sum([v for k,v in f_p.iteritems()])
    positive_word_count = len(f_p)

    neutral_total = sum([v for k,v in f_neu.iteritems()])
    neutral_word_count = len(f_neu)

    total = negative_total+positive_total+neutral_total
    dic = f_neg.keys()
    dic.extend(f_neu.keys())
    dic.extend(f_p.keys())
    dic_len = len(set(dic))

    return negative_total,negative_word_count,neutral_total,neutral_word_count,positive_total,positive_word_count,total,dic_len

sw = load_scws()

def test_coding():
    data_neg, data_neu, data_p = read_train()
    f_neg =  freq_word(data_neg)
    f_neu = freq_word(data_neu)
    f_p = freq_word(data_p)

    negative_total,negative_word_count,neutral_total,neutral_word_count,positive_total,positive_word_count,total,dic_len=word_count(f_neg,f_neu,f_p)
    para_list = [f_neg,f_neu,f_p,negative_total,negative_word_count,neutral_total,neutral_word_count,positive_total,positive_word_count,total,dic_len]

    return para_list

para_list = train_freq()
def naivebayes(test_data):
    '''
    朴素贝叶斯三类分类器
    '''
    #print test_data['em_info']
    #计算三类先验概率
    p_negative = float(para_list[3])/float(para_list[9])
    p_neutral = float(para_list[5])/float(para_list[9])
    p_positive = float(para_list[7])/float(para_list[9])

    #label = []#分类后类别标签列表
    info_type = [u'数据',u'新闻',u'研报',u'公告']
    addition_w = [u'如何',u'怎么',u'什么']
    #如果记录的em_info字段为数据、新闻、研报、公告，则直接将该条记录归为中性类
    if (test_data['em_info']!=None) and (test_data['em_info'].decode("utf8") in info_type):
        #label.append('2')
        label = 2
    else:
        text = test_data['content']+'***'+test_data['title']
        try:
            words = sw.participle(text)
            p_neg = 1
            p_neu = 1
            p_p = 1
            prob = []
            for word in words:
                if word[0] in para_list[0]:
                    p_w_neg = (float(para_list[0][word[0]])+1)/(float(para_list[3])+float(para_list[10]))
                else:
                    p_w_neg = 1.0/(float(para_list[3])+float(para_list[10]))
                p_neg = p_neg * p_w_neg

                if word[0] in para_list[1]:
                    p_w_neu = (float(para_list[1][word[0]])+1)/(float(para_list[5])+float(para_list[10]))
                else:
                    p_w_neu = 1.0/(float(para_list[5])+float(para_list[10]))
                p_neu = p_neu*p_w_neu

                if word[0] in para_list[2]:
                    p_w_p = (float(para_list[2][word[0]])+1)/(float(para_list[7])+float(para_list[10]))
                else:
                    p_w_p = 1.0/(float(para_list[7])+float(para_list[10]))
                p_p = p_p * p_w_p

            prob_neg = p_negative * p_neg
            prob_neu = p_neutral * p_neu
            prob_p = p_positive * p_p
            if prob_neg == prob_neu and prob_neg == prob_p:
                #label.append(2)
                label = 2
            else:
                prob.append(prob_neg)
                prob.append(prob_p)
                prob.append(prob_neu)
                #print prob
                #label.append(str(prob.index(max(prob))))
                label = prob.index(max(prob))
        except:
            #label.append(2)      
            label = 2      
    #print label,prob_neg,prob_neu,prob_p
    return label

def read_test():
    test = []
    true_label = []
    reader = csv.reader(file('./test0915.csv','rb'))
    for id, title, content, em_info, flag in reader:
    #for line in reader:
        test.append({"content":content,"title":title})
        true_label.append(flag)

    return test,true_label
        
if __name__ == '__main__':
    test_data, true_label = read_test()
    for item in test_data:
        label = naivebayes(item)
        print label
