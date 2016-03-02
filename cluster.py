#-*- coding: UTF-8 -*-

'''
auther:Aljun
project:k-means聚类


'''

from random import randint
import math
import matplotlib.pylab as mlp
import seaborn as sns
import numpy


class point():
    def __init__(self,x,y):
        self.x=x
        self.y=y

'''
计算欧式距离
'''

def get_distance(vec1,vec2):
    return math.sqrt((vec1.x-vec2.x)**2+(vec1.y-vec2.y)**2)

'''
聚类开始程序，data_set为输入数据，k为要几个类，depth为做几次欧式距离聚类
'''

def cluster_start(data_set,k=5,depth=5):


    rand_num=[]
    for i in range(k):
        rand_num.append(point(x=randint(1,100),y=randint(1,100)))

    parse_list=cluster(rand_num,data_set)

    for i in range(depth-1):
        new_center=find_center(parse_list)

        parse_list=cluster(new_center,data_set)


    draw_pic(parse_list)

'''
画散点图

'''

def draw_pic(data_list_set):
    for i in range(len(data_list_set)):
        parse_x=[]
        parse_y=[]
        for j in range(len(data_list_set[i])):
            parse_x.append(data_list_set[i][j].x)
            parse_y.append(data_list_set[i][j].y)

        mlp.scatter(parse_x,parse_y,c=numpy.random.rand(3,1),alpha=0.65,label="Team:"+str(i),s=40)

    mlp.legend()
    mlp.title("The Result From The Cluster")

    mlp.show()

'''
得到一堆测试用的随机数
'''


def get_random_num(num=100):
    data_set=[]
    for i in range(num):
        data_set.append(point(x=randint(1,100),y=randint(1,100)))

    return data_set

'''
在第一次聚类后，寻找几个类的中心点，即是这个点到这个类的各个点的距离最短
'''

def find_center(data_set):
    res=[]
    for i in range(len(data_set)):
        minn=100000000000000
        min_p=None
        for j in range(len(data_set[i])):
            sumn=0
            for h in range(len(data_set[i])):
                sumn=sumn+get_distance(data_set[i][j],data_set[i][h])
            if sumn<minn:
                min_p=j
                minn=sumn
#        print i,min_p
        if min_p!=None:
            res.append(data_set[i][min_p])
#        print data_set[i][min_p]
    return res

'''
遍历所有的点，得到输入的k个类
'''

def cluster(center_num,data_set):
    the_clusted_list={}
    for i in range(len(center_num)):
        the_clusted_list[i]=[]
    for i in range(len(data_set)):
        maxn=0
        p_to_center=None
        for j in range(len(center_num)):
            if get_distance(data_set[i],center_num[j])>maxn:
                maxn=get_distance(data_set[i],center_num[j])
                p_to_center=j

        the_clusted_list[p_to_center].append(data_set[i])

    return the_clusted_list

'''
这里的data_set为输入数据
'''

if __name__=="__main__":
    data_set=get_random_num(num=300)
    cluster_start(data_set=data_set)
