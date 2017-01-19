# -*- coding: cp936 -*-
import csv

def second_label(datadir):
    '''
    ͳ�ƶ��α�ע������������Ӷ��������ӱ�ע��������ͬ��עΪ׼��������α�ע����һ������ĵ�
    '''
    reader = csv.reader(file(datadir,'rb'))
    reserved_record = {}
    labeling_record = {}
    for id,content,title,em_info,stock_name,lable1,lable2,lable3 in reader:
        if lable1 == lable3:
            reserved_record[id] = [id,content,title,em_info,stock_name,lable1]
        elif lable2 == lable3:
            reserved_record[id] = [id,content,title,em_info,stock_name,lable2]
        else:
            labeling_record[id] = [id,content,title,em_info,stock_name,lable1,lable2,lable3]

    return reserved_record,labeling_record

if __name__ == '__main__':
    datadir = './second_label0406.csv'
    reserved,labeling = second_label(datadir)
    with open('./second_label_reserved.csv','wb')as f:
        writer = csv.writer(f)
        for k,v in reserved.iteritems():
            writer.writerow((v))

    with open('./need_third_labeling.csv','wb')as f:
        writer = csv.writer(f)
        for k,v in labeling.iteritems():
            writer.writerow((v))
        
