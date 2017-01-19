# -*- coding:utf-8 -*-

fi = open('20151214.txt')
fo = open('2015-12-14.txt', 'w')
data = [line[:6]+'\n' for line in fi.readlines()]
fo.writelines(data)
fi.close()
fo.close()
