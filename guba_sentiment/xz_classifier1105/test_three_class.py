# -*- coding: utf-8 -*- 

import os
import scws
import time
import csv
import re
import random
import math
import sys
reload(sys)
sys.setdefaultencoding('utf8')
##from svmutil import *

SCWS_ENCODING = 'utf-8'
SCWS_RULES = '/usr/local/scws/etc/rules.utf8.ini'
CHS_DICT_PATH = '/usr/local/scws/etc/dict.utf8.xdb'
CHT_DICT_PATH = '/usr/local/scws/etc/dict_cht.utf8.xdb'
IGNORE_PUNCTUATION = 1

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
    reader = csv.reader(file('./second_label/second_label_reserved_1.csv','rb'))
    for id, content,title,em_info,stock_name,label in reader:
        different_data[id] = [id,content,title,em_info,stock_name,label,'different']
    #问题标注，部标
    reader = csv.reader(file('./second_label/second_label_reserved_2.csv','rb'))
    for id,content,title,em_info,stock_name,label in reader:
        different_data[id] = [id,content,title,em_info,stock_name,label,'different']
##    print len(different_data.keys())
            
    data_neg = []
    data_neu = []
    data_p = []
    not_train_count = 0
    info_type = [u'数据',u'新闻',u'研报',u'公告']
    datadir = './label0403/lab_labeled/label_csv/'
    files = os.listdir(datadir)
    pos = neg = neu = other = 0
    for fname in files:
        reader = csv.reader(file(datadir+fname,'rb'))
        for id,content,title,em_info,stock_name,label in reader:
            if id not in different_data.keys():
                text = content+title
                if label == '1':
                    pos += 1
                elif label == '2':
                    neu += 1
                elif label == '0':
                    neg += 1
                else:
                    other += 1
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
                lable = different_data[id][5]
                if lable == '1':
                    pos += 1
                elif lable == '2':
                    neu += 1
                elif lable == '0':
                    neg += 1
                else:
                    other += 1
                if len(text)<284 and (different_data[id][2]!=None) and (different_data[id][2].decode("utf8") not in info_type):
                    # lable != label
                    if label == '-1' or label == '2':
                        data_neu.append(different_data[id])
                    elif label == '1':
                        data_p.append(different_data[id])
                    else:
                        data_neg.append(different_data[id])
                else:
                    not_train_count += 1
                
    print not_train_count,len(data_neg),len(data_neu),len(data_p)
    print neg, neu, pos, other
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
    #f_neg = freq_word(train_neg)
    #f_neu = freq_word(train_neu)
    #f_p = freq_word(train_p)
    #统计每类下词频（非等比例抽样）
    f_neg = freq_word(data_neg)
    f_neu = freq_word(data_neu)
    f_p = freq_word(data_p)

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
    from collections import Counter
    
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
    
def naivebayes(para_list,test_data):
    '''
    朴素贝叶斯三类分类器
    '''
    sw = load_scws()
    
    #计算三类先验概率
    p_negative = float(para_list[3])/float(para_list[9])
    p_neutral = float(para_list[5])/float(para_list[9])
    p_positive = float(para_list[7])/float(para_list[9])

    lable = []#分类后类别标签列表
    for i in range(len(test_data)):
        info_type = [u'数据',u'新闻',u'研报',u'公告']
        addition_w = [u'如何',u'怎么',u'什么']
        #如果记录的em_info字段为数据、新闻、研报、公告，则直接将该条记录归为中性类
        if (test_data[i][3]!=None) and (test_data[i][3].decode("utf8") in info_type):
            lable.append('2')
            #lable.append([2])#实验
        else:
            text = test_data[i][1]+'***'+test_data[i][2]
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
                    lable.append(2)
                    #lable.append([2])#实验
                else:
                    prob.append(prob_neg)
                    prob.append(prob_p)
                    prob.append(prob_neu)
                    lable.append(str(prob.index(max(prob))))
                    #实验
                    #lable.append([str(prob.index(max(prob))),prob_neg,prob_neu,prob_p])
            except:
                lable.append(2)
                #lable.append([2])#实验
            

    return lable

def check_test(index):

    #五折交叉检验
    data = {'1':[],'2':[],'3':[],'4':[],'5':[]}
    data_neg,data_neu,data_p = read_train()
    inputs = []
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
    inputs.extend(train_neg)
    inputs.extend(train_neu)
    inputs.extend(train_p)

    for i in range(len(inputs)):
        flag = random.randint(1,5)
        if flag == 1:
            item = data['1']
            item.append(inputs[i])
            data['1'] = item
        elif flag == 2:
            item = data['2']
            item.append(inputs[i])
            data['2'] = item
        elif flag == 3:
            item = data['3']
            item.append(inputs[i])
            data['3'] = item
        elif flag == 4:
            item = data['4']
            item.append(inputs[i])
            data['4'] = item
        elif flag == 5:
            item = data['5']
            item.append(inputs[i])
            data['5'] = item

    check_result = []
    for i in range(1,6):
        test_data = []
        test_flag = []
        train_data = []
        train_flag = []
        new_neg = []
        new_neu = []
        new_pos = []
        for k,v in data.iteritems():
            if k == str(i):
                for item in v:
                    test_data.append(item)
                    test_flag.append(item[5])
            else:
                for item in v:
                    train_data.append(item)
                    train_flag.append(item[5])
                    if item[5] == '0':
                        new_neg.append(item)
                    elif item[5] == '1':
                        new_pos.append(item)
                    else:
                        new_neu.append(item)

        #训练模型
        #三类等比例抽取训练样本
        print len(train_neg), len(train_neu), len(train_p)
        f_neg = freq_word(train_neg)
        f_neu = freq_word(train_neu)
        f_p = freq_word(train_p)
        #全部标记数据做样本
##        f_neg = freq_word(data_neg)
##        f_neu = freq_word(data_neu)
##        f_p = freq_word(data_p)
        negative_total,negative_word_count,neutral_total,neutral_word_count,positive_total,positive_word_count,total,dic_len=word_count(f_neg,f_neu,f_p)
        para_list = [f_neg,f_neu,f_p,negative_total,negative_word_count,neutral_total,neutral_word_count,positive_total,positive_word_count,total,dic_len]
        result_lable = naivebayes(para_list,test_data)

        #交叉检验
        p_neg,r_neg,f_neg,p_neu,r_neu,f_neu,p_p,r_p,f_p = check(test_flag,result_lable)
        check_result.append([i,p_neg,r_neg,f_neg,p_neu,r_neu,f_neu,p_p,r_p,f_p])
        with open('./3class_result/20161105/train_%s_%s.csv'%(index,i),'wb')as f:
            writer = csv.writer(f)
            for j in range(len(train_data)):
                writer.writerow((train_data[j]))
                
        with open('./3class_result/20161105/test_%s_%s.csv'%(index,i),'wb')as f:
            writer = csv.writer(f)
            for j in range(len(test_data)):
                row = test_data[j]
                writer.writerow((row))

    with open('./3class_result/20161105/accuracy_result_%s.csv'%index,'wb')as f:
        writer = csv.writer(f)
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

    p_neu = float(index[4])/(float(index[1])+float(index[4])+float(index[7]))
    r_neu = float(index[4])/(float(index[3])+float(index[4])+float(index[5]))
    f_neu = float(2*p_neu*r_neu)/float(p_neu+r_neu)

    p_p = float(index[8])/(float(index[2])+float(index[5])+float(index[8]))
    r_p = float(index[8])/(float(index[6])+float(index[7])+float(index[8]))
    f_p = float(2*p_p*r_p)/float(p_p+r_p)

    return p_neg,r_neg,f_neg,p_neu,r_neu,f_neu,p_p,r_p,f_p

def random_test(rand_num):
    '''
    随机抽取500条帖子做测试
    '''
    test = {}
    datadir = './label0403/lab_labeled/label_csv/'
    files = os.listdir(datadir)
    for fname in files:
        reader = csv.reader(file(datadir+fname,'rb'))
        for id,content,title,em_info,stock_name,label in reader:
            test[id] = [id,content,title,em_info,stock_name,label,'same']
    #问题标注
    reader = csv.reader(file('./second_label/second_label_reserved_1.csv','rb'))
    for id, content,title,em_info,stock_name,label in reader:
        test[id] = [id,content,title,em_info,stock_name,label,'different']
    #问题标注，部标
    reader = csv.reader(file('./second_label/second_label_reserved_2.csv','rb'))
    for id,content,title,em_info,stock_name,label in reader:
        test[id] = [id,content,title,em_info,stock_name,label,'different']
    test_data = test.values()
##    with open('./guba_label_final0407.csv','wb')as f:
##        writer = csv.writer(f)
##        for item in test:
##            writer.writerow((item))

    test_inputs = []
    test_id = [random.randint(0,len(test)-1)for i in range(rand_num)]
    test_lable = []
    for item in test_id:
        test_inputs.append(test_data[item])
        test_lable.append(test_data[item][5])

    parameter = train_freq()
    lable = naivebayes_main(parameter,test_inputs)
    p_neg,r_neg,f_neg,p_neu,r_neu,f_neu,p_p,r_p,f_p = check(test_lable,lable)
    print p_neg,r_neg,f_neg,p_neu,r_neu,f_neu,p_p,r_p,f_p

    with open('./500test_result.csv','wb')as f:
        writer = csv.writer(f)
        for i in range(len(test_inputs)):
            row = test_inputs[i]
            row.append(lable[i])
            writer.writerow((row))

def test_coding():
    test = []
    test_id = []
    test_label = []
    reader = csv.reader(file('./3class_result/20161105/test_0_1.csv','rb'))
    for line in reader:
        if line[5] == '-1' or line[5] == '2':
            test.append([line[0],line[1],line[2],line[3],line[4],'2',line[6]])
            test_id.append(line[0])
            test_label.append('2')
        else:
            test.append([line[0],line[1],line[2],line[3],line[4],line[5],line[6]])
            test_id.append(line[0])
            test_label.append(line[5])
    parameter = train_freq()
    lable = naivebayes_main(parameter,test)
    p_neg,r_neg,f_neg,p_neu,r_neu,f_neu,p_p,r_p,f_p = check(test_label,lable)
    print p_neg,r_neg,f_neg,p_neu,r_neu,f_neu,p_p,r_p,f_p
        

if __name__ == '__main__':
    #test_coding()
    #random_test(500)
    for i in range(0,1):
        print i
        check_test(i)

##    reader = csv.reader(file('different_label.csv','rb'))
##    inputs = []
##    for id,title,content,em_info,stock_name,label1,label2 in reader:
##        inputs.append([id,title,content,em_info,stock_name,label1,label2])
##
##    start = time.time()
##    parameter = train_freq()
##    result_label = naivebayes_main(parameter,inputs)
##    end = time.time()
##    print '500 classification takes:%s s'%(end-start)
##
##    different_data = {}
##    #问题标注
##    reader = csv.reader(file('./second_label/second_label_reserved_1.csv','rb'))
##    for id, content,title,em_info,stock_name,l in reader:
##        different_data[id] = [id,content,title,em_info,stock_name,l]
##    #问题标注，部标
##    reader = csv.reader(file('./second_label/second_label_reserved_2.csv','rb'))
##    for id,content,title,em_info,stock_name,l in reader:
##        different_data[id] = [id,content,title,em_info,stock_name,l]
##
##    with open('./different_label_result_3class.csv','wb')as f:
##        writer = csv.writer(f)
##        for i in range(len(inputs)):
##            row = inputs[i]
##            #row.append(label[i])
##            #实验
##            row.extend(result_label[i])
##            if different_data.has_key(inputs[i][0]):
##                row.append(different_data[inputs[i][0]][5])
##            else:
##                row.append(-1)
##            writer.writerow((row))
    
    
            
