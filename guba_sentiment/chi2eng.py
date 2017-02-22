#-*- coding:utf-8 -*-
import os

fidir = 'results/intraday/'
count = 0
for fname in os.listdir(fidir):

    fi = open(fidir+fname)
    all = fi.readlines()
    fi.close()
    print count, fname
    all[0] = 'date,stockid,on_pos,on_neg,on_neu,on_bt,on_bs,on_bz,off_pos,off_neg,off_neu,off_bt,off_bs,off_bz\n'
    fi = open(fidir+fname,'w')
    fi.writelines(all)
    fi.close()
    count += 1
