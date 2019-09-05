import paramiko
import time
import os

from keras0 import VGGNet
import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import argparse
import time
import cv2
import sys
from itertools import cycle
 
import threading

location = '2'

class Reading (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        global location
        print ("开始线程：" + self.name)
        transport = paramiko.Transport(('192.168.137.142', 22))
        transport.connect(username='pi', password='raspberry')
        ssh = paramiko.SSHClient()
        ssh._transport = transport
        # 执行命令，和传统方法一样
        sftp = paramiko.SFTPClient.from_transport(transport)
        print('初始化已完成\r\n')
        namespace = 'mycar'
        stdin, stdout, stderr = ssh.exec_command('cd '+namespace+'/data;ls -t|grep tub|head -1')
        re0 = str(stdout.read().decode()).strip();
        dir = '/home/pi/'+namespace+'/data/'+re0
        re = 'cd '+namespace+'/data/'+ re0 +';ls -t *.jpg|head -1'

        print('文件夹定位',dir,'完成\r\n')

        index = 'compare.h5'
        result = './data'
        h5f = h5py.File(index,'r')
        feats = h5f['dataset_1'][:]
        imgNames = h5f['dataset_2'][:]
        h5f.close()
        print("进程开始\r\n")
        model = VGGNet()
        print("\r\n")   # 

        num = 1
        lastre = re

        iniflag = 0

        preloc = 0
        imbuf = 0

        while num:
            stdin, stdout, stderr = ssh.exec_command(re)
            reply = stdout.read().decode().strip()

            if reply != lastre and  reply != None:
                path = dir+'/'+reply
                try:
                    sftp.get(path,'./template/'+str(num)+'.jpg')
                except:
                    print('未找到文件')
                else:
                    print('已下载文件',reply)
                    lastre = reply;
                    print(num)
                    query = './template/'+str(num)+'.jpg'
                    queryVec = model.vgg_extract_feat(query)    #修改此处改变提取特征的网络
                    scores = np.dot(queryVec, feats.T)
                    rank_ID = np.argsort(scores)[::-1]
                    rank_score = scores[rank_ID]
                    maxres = 7          #检索出三张相似度最高的图片
                    imlist = []
                    imlists = []

                    for i,index in enumerate(rank_ID[0:maxres]):
                        imlist.append(imgNames[index])
                        print("image names: "+str(imgNames[index]) + " scores: %f"%rank_score[i])

                    print("\r\n最相似的 %d 张图片是: " %maxres, imlist)

                    mayloc = []
                    imlist_str = ''

                    
                    for de in range(0,7):
                        imlists.append(str(imlist[de]))
                        imlist_str = imlist_str + imlists[de].split('(')[0].split("'")[-1].strip()

                    if iniflag == 0 and rank_score[0] > 0.68 and imlist_str.count(imlist_str[0]) > 3:
                        location = imlist_str[0]
                        iniflag = 1
                        preloc = location
                        print('开始定位')

                    if iniflag == 1 and rank_score[0] > 0.68 and imlist_str.count(imlist_str[0]) > 3:
                        imbuf = imbuf + 1
                        if imbuf == 3:
                            location = imlist_str[0]
                            preloc = location
                            imbuf = 0
                        else:
                            location = location
                            preloc = preloc

                    elif iniflag == 1 and rank_score[0] < 0.63 :
                        location = '2'

                    print("本次定位 ",imlist_str[0],'\r\n')
                    print("参考位置 %s"%location+'\r\n')
                    num = num + 1
            else:
                print('等待...',end='\r')
                time.sleep(0.5)

        transport.close()
        print ("退出线程：" + self.name)

class Playing (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        global location
        print ("开始线程：" + self.name)
        key = 0
        while key & 0xFF != 27:

            cv2.namedWindow('location',0)
            cv2.resizeWindow("location",900,600)
            img = cv2.imread('./map/'+str(location).strip()+'.jpg')
            cv2.imshow('location',img)
            key = cv2.waitKey(1000)  #1000为间隔1000毫秒 cv2.waitKey()参数不为零的时候则可以和循环结合产生动态画面
        print ("退出线程：" + self.name)

thread1 = Reading(1, "Thread-1", 1)
thread2 = Playing(2, "Thread-2", 2)

# 开启新线程
thread1.start()
time.sleep(5)
thread2.start()



