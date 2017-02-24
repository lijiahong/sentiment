# -*- coding: utf-8 -*-
import os
import re
import scws
import csv
import random
import math
import sys
import time
import datetime
import json
from collections import Counter

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
    num_neg = 0
    num_pos = 0
    num_neu = 0
    num_other = 0
    for fname in files:
        reader = csv.reader(file(datadir+fname,'rb'))
        for id,content,title,em_info,stock_name,label in reader:
            text = content + title
            if id not in different_data.keys():
                if label == '2':
                    num_neu += 1
                elif label == '1':
                    num_pos += 1
                elif label == '0':
                    num_neg += 1
                else:
                    num_other += 1
                if (len(text)<284) and (em_info!=None) and (em_info.decode("utf8") not in info_type):
                    if label == '-1' or label == '2':
                        data_neu.append([id,content,title,em_info,stock_name,'2','same'])
                    elif label == '1':
                        data_p.append([id,content,title,em_info,stock_name,label,'same'])
                    else:
                        data_neg.append([id,content,title,em_info,stock_name,label,'same'])
                else:
                    not_train_count += 1
            else:
                label = different_data[id][5]
                if label == '2':
                    num_neu += 1
                elif label == '1':
                    num_pos += 1
                elif label == '0':
                    num_neg += 1
                else:
                    num_other += 1
                if len(text)<284 and (em_info!=None) and (em_info.decode("utf8") not in info_type):
                    if label == '-1' or label == '2':
                        data_neu.append(different_data[id])
                    elif label == '1':
                        data_p.append(different_data[id])
                    else:
                        data_neg.append(different_data[id])
                else:
                    not_train_count += 1
    print num_other, num_neg, num_neu, num_pos 
    print not_train_count,len(data_neg),len(data_neu),len(data_p)
    return data_neg,data_neu,data_p

def train_freq():
    train_neg, train_neu, train_p = under_sampling()
    f_neg = freq_word(train_neg)
    f_neu = freq_word(train_neu)
    f_p = freq_word(train_p)

    #统计各类下单词总数（算重复）、估算重复单词数、文档单词个数
    negative_total,negative_word_count,neutral_total,neutral_word_count,positive_total,positive_word_count,total,dic_len=word_count(f_neg,f_neu,f_p)

    #参数列表
    para_list = [f_neg,f_neu,f_p,negative_total,negative_word_count,neutral_total,neutral_word_count,positive_total,positive_word_count,total,dic_len]
    print para_list
    return para_list

def under_sampling():
    '''
    训练分类模型
    '''
    data_neg,data_neu,data_p = read_train()
    train_neg = []
    train_neu = []
    train_p = []
    list_len = [len(data_neg),len(data_neu),len(data_p)]
    min_len = min(list_len)
    min_index = list_len.index(min_len)
    if min_index == 0:
        rand_neu = [random.randint(0,len(data_neu)-1)for i in range(min_len)]
        train_neu = [data_neu[i] for i in rand_neu]
        rand_p = [random.randint(0,len(data_p)-1)for i in range(min_len)]
        train_p = [data_p[i] for i in rand_p]
        train_neg = data_neg
    elif min_index == 1:
        rand_neg = [random.randint(0,len(data_neg)-1)for i in range(min_len)]
        train_neg = [data_neg[i] for i in rand_neg]
        rand_p = [random.randint(0,len(data_p)-1)for i in range(min_len)]
        train_p = [data_p[i] for i in rand_p]
        train_neu = data_neu
    else:
        rand_neg = [random.randint(0,len(data_neg)-1)for i in range(min_len)]
        train_neg = [data_neg[i] for i in rand_neg]
        rand_neu = [random.randint(0,len(data_neu)-1)for i in range(min_len)]
        train_neu = [data_neu[i] for i in rand_neu]
        train_p = data_p
    #print 'train_neg:%s;train_neu:%s;train_p:%s'%(len(train_neg),len(train_neu),len(train_p))
    
    return train_neg, train_neu, train_p
    

sw = load_scws()
def freq_doc(data):
    '''
    统计指定数据下词及出现的文档数
    '''
    black = load_black_words()
    addition = [u'!',u'如何',u'怎么',u'什么']
    word_list = []
    for i in range(len(data)):
        text = data[i][1] + '***' + data[i][2]
        words = sw.participle(text)
        all_words = [term for term,cx in words if cx in cx_dict and (3<len(term)<30 or term in single_word_whitelist) and (term not in black)]
        all_words_single = list(set(all_words))    #去重
        word_list.extend(all_words_single)
    word_list.extend(addition)
    
    counter = Counter(word_list)
    #freq_word = {k:v for k,v in counter.most_common() if v>=3}
    freq_word = {k:v for k,v in counter.most_common()}
    
    return freq_word

def freq_word(data):
    '''
    统计指定数据下词及词频
    '''
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
    all_dict = list(set(dic))
    dic_len = len(all_dict)

    return negative_total,negative_word_count,neutral_total,neutral_word_count,positive_total,positive_word_count,total,dic_len,all_dict

def naivebayes_v2(post, para_list):
    '''
    朴素贝叶斯三类分类器(bernoulli)
    '''
    #print post['em_info']
    #计算三类先验概率
    p_negative = float(para_list[3])/float(para_list[6])
    p_neutral = float(para_list[4])/float(para_list[6])
    p_positive = float(para_list[5])/float(para_list[6])
    #label = []#分类后类别标签列表
    info_type = [u'数据',u'新闻',u'研报',u'公告']
    addition_w = [u'如何',u'怎么',u'什么']
    #如果记录的em_info字段为数据、新闻、研报、公告，则直接将该条记录归为中性类
    if (post['em_info']!=None) and (post['em_info'].decode("utf8") in info_type):
        #label.append('2')
        label = 2
    else:
        flag = {}
        all_dict = para_list[7]
        for term in all_dict:
            flag[term] = False
        text = post['content']+'***'+post['title']
        try:
            words = sw.participle(text)
            for word in words:
                if word[0] in flag:
                    flag[word[0]] = True
            p_neg = 0
            p_neu = 0
            p_p = 0
            prob = []
            for word in flag:
                if word in para_list[0]:
                    p_w_neg = (float(para_list[0][word])+1)/(float(para_list[3])+float(para_list[6]))
                else:
                    p_w_neg = 1.0/(float(para_list[3])+float(para_list[6]))
                
                if word in para_list[1]:
                    p_w_neu = (float(para_list[1][word])+1)/(float(para_list[4])+float(para_list[6]))
                else:
                    p_w_neu = 1.0/(float(para_list[4])+float(para_list[6]))
                
                if word in para_list[2]:
                    p_w_pos = (float(para_list[2][word])+1)/(float(para_list[5])+float(para_list[6]))
                else:
                    p_w_pos = 1.0/(float(para_list[5])+float(para_list[6]))
                
                if flag[word]:
                    p_neg = p_neg + math.log(p_w_neg)
                    p_neu = p_neu + math.log(p_w_neu)
                    p_p = p_p + math.log(p_w_pos)
                else:
                    p_neg = p_neg + math.log(1.0-p_w_neg)
                    p_neu = p_neu + math.log(1.0-p_w_neu)
                    p_p = p_p + math.log(1.0-p_w_pos)

            prob_neg = math.log(p_negative) + p_neg
            prob_neu = math.log(p_neutral) + p_neu
            prob_p = math.log(p_positive) + p_p
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

def naivebayes(post, para_list):
    '''
    朴素贝叶斯三类分类器
    '''
    #print post['em_info']
    #计算三类先验概率
    p_negative = float(para_list[3])/float(para_list[9])
    p_neutral = float(para_list[5])/float(para_list[9])
    p_positive = float(para_list[7])/float(para_list[9])
    #label = []#分类后类别标签列表
    info_type = [u'数据',u'新闻',u'研报',u'公告']
    addition_w = [u'如何',u'怎么',u'什么']
    #如果记录的em_info字段为数据、新闻、研报、公告，则直接将该条记录归为中性类
    if (post['em_info']!=None) and (post['em_info'].decode("utf8") in info_type):
        #label.append('2')
        label = 2
    else:
        text = post['content']+'***'+post['title']
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

def multi_naivebayes(para_list, test_data):
    label_list = []
    for item in test_data:
        post = {'content':item[1], 'title':item[2], 'em_info':item[3]}
        label = naivebayes_v2(post, para_list)
        label_list.append(label)
    return label_list

def check_test(index):

    #五折交叉检验
    train_neg, train_neu, train_p = under_sampling()

    inputs = []
    inputs.extend(train_neg)
    inputs.extend(train_neu)
    inputs.extend(train_p)
    
    data = []
    FOLDS_NUM = 5
    for i in range(FOLDS_NUM):
    	data.append([])
    for i in range(len(inputs)):
        flag = random.randint(0,FOLDS_NUM-1)
        data[flag].append(inputs[i]) 

    check_result = []
    for i in range(FOLDS_NUM):
    	test_data = []
        test_flag = []
        train_data = []
        train_flag = []
        new_neg = []
        new_neu = []
        new_pos = []
    	for j in range(FOLDS_NUM):
            if (i == j):
                test_data = data[j]
            else:
		train_data.extend(data[j])
		for item in data[j]:
		    if item[5] == '0':
		    	new_neg.append(item)
		    elif item[5] == '1':
		    	new_pos.append(item)
		    else:
		    	new_neu.append(item)
            test_flag = [item[5] for item in test_data]
            train_flag = [item[5] for item in train_data]
        
        #训练模型
        #三类等比例抽取训练样本
        
        print len(new_neg), len(new_neu), len(new_pos)
        n_neg = len(new_neg)
        n_neu = len(new_neu)
        n_pos = len(new_pos)
        n_total = n_neg + n_neu + n_pos
        f_neg = freq_doc(new_neg)
        f_neu = freq_doc(new_neu)
        f_p = freq_doc(new_pos)
        
        '''
        f_neg = freq_word(new_neg)
        f_neu = freq_word(new_neu)
        f_p = freq_word(new_pos)
        '''
        negative_total,negative_word_count,neutral_total,neutral_word_count,positive_total,positive_word_count,total,dic_len,all_dict=word_count(f_neg,f_neu,f_p)
        #para_list = [f_neg,f_neu,f_p,negative_total,negative_word_count,neutral_total,neutral_word_count,positive_total,positive_word_count,total,dic_len]
        para_list = [f_neg, f_neu, f_p, n_neg, n_neu, n_pos, n_total, all_dict]
        result_lable = multi_naivebayes(para_list,test_data)
        print para_list
        #交叉检验
        p_neg,r_neg,f_neg,p_pos,r_pos,f_pos,p_neu,r_neu,f_neu = check(test_flag,result_lable)
        check_result.append([i,p_neg,r_neg,f_neg,p_pos,r_pos,f_pos,p_neu,r_neu,f_neu])
        with open('./3class_result/train_%s_%s.csv'%(index,i),'wb')as f:
            writer = csv.writer(f)
            for j in range(len(train_data)):
                writer.writerow((train_data[j]))
                
        with open('./3class_result/test_%s_%s.csv'%(index,i),'wb')as f:
            writer = csv.writer(f)
            for j in range(len(test_data)):
                row = test_data[j]
                res = list(row)
                res.append(result_lable[j])
                writer.writerow(res)

    with open('./3class_result/accuracy_result_%s.csv'%index,'wb')as f:
        writer = csv.writer(f)
        writer.writerow(['id','p_neg','r_neg','f_neg','p_pos','r_pos','f_pos','p_neu','r_neu','f_neu'])
        for item in check_result:
            writer.writerow((item))

def check(test_flag,result_flag):

    index = [0]*9
    for i in range(len(test_flag)):
        if (str(test_flag[i])== '0') and (str(result_flag[i]) == '0'):
            index[0] += 1
        if (str(test_flag[i])== '0') and (str(result_flag[i]) == '1'):
            index[1] += 1
        if (str(test_flag[i])== '0') and (str(result_flag[i]) == '2'):
            index[2] += 1
        if (str(test_flag[i])== '1') and (str(result_flag[i]) == '0'):
            index[3] += 1
        if (str(test_flag[i])== '1') and (str(result_flag[i]) == '1'):
            index[4] += 1
        if (str(test_flag[i])== '1') and (str(result_flag[i]) == '2'):
            index[5] += 1
        if (str(test_flag[i])== '2') and (str(result_flag[i]) == '0'):
            index[6] += 1
        if (str(test_flag[i])== '2') and (str(result_flag[i]) == '1'):
            index[7] += 1
        if (str(test_flag[i])== '2') and (str(result_flag[i]) == '2'):
            index[8] += 1

    p_neg = float(index[0])/(float(index[0])+float(index[3])+float(index[6]))
    r_neg = float(index[0])/(float(index[0])+float(index[1])+float(index[2]))
    f_neg = float(2*p_neg*r_neg)/float(p_neg+r_neg)

    p_pos = float(index[4])/(float(index[1])+float(index[4])+float(index[7]))
    r_pos = float(index[4])/(float(index[3])+float(index[4])+float(index[5]))
    f_pos = float(2*p_pos*r_pos)/float(p_pos+r_pos)

    p_neu = float(index[8])/(float(index[2])+float(index[5])+float(index[8]))
    r_neu = float(index[8])/(float(index[6])+float(index[7])+float(index[8]))
    f_neu = float(2*p_neu*r_neu)/float(p_neu+r_neu)

    return p_neg,r_neg,f_neg,p_pos,r_pos,f_pos,p_neu,r_neu,f_neu
