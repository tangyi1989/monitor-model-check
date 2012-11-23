#*_* coding=utf8 *_*

import MySQLdb
import random
from datetime import datetime
from datetime import timedelta
import time

"""
状况:
1000 台虚拟机,
每10秒钟产生一次数据,
一次数据包含7-10个指标,
产生24小时的数据.
共 : 1000 * 7 * 24 * 60 * 6 = 60,480,000

测试:
现在做出如下测试,假设有1000台虚拟机,每10秒产生10项的监控数据,现在把它加入数据库,
测试数据库读写压力.现在使用mysql数据库,试着产生一天的数据,并观察数据库读写压力.

结果:
写性能基本上不会随着数据的增加下降太多,但是读性能会下降很多.(没有建立索引)
查找性能会随着数据增加,查找时间现行增加,预计达到目标数据之后,大概达到20秒左右.
查看测试报告.
"""

#第一次测试的时候,没有建立索引.
#第二轮测试会手动增加索引测试.
sql_create_table = """
CREATE TABLE IF NOT EXISTS data(
    id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    type CHAR(128),
    host CHAR(128),
    report_time DATETIME,
    value INT)
"""

HOST = '127.0.0.1'
USER = 'root'
PASSWD = 'tang'
DB = 'monitor'

def get_conn():
    conn=MySQLdb.connect(host=HOST, user=USER,
                         passwd=PASSWD, db=DB, port=3306)
    return conn

def create_database():
    conn=MySQLdb.connect(host=HOST, user=USER, passwd=PASSWD, port=3306)
    cur=conn.cursor()
    cur.execute('create database if not exists monitor')
    conn.commit()
    cur.close()
    conn.close()

def create_monitor_table():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql_create_table)
    conn.commit()
    cur.close()
    conn.close()

def init():
    create_database()
    create_monitor_table()

def generate_data(date):
    records = 0
    
    conn = get_conn()
    cur = conn.cursor()
    inst_prefix = 'instance-%08x'
    collect_type = ['cpu', 'mem', 'disk_read', 'disk_write', 'disk_read', 
                    'eth0_up', 'eth0_down']
    for i in range(1, 1001):
        host = inst_prefix % i
        for type in collect_type:
            sql = 'insert into data (type, host, report_time, value) values("%s", "%s", "%s", %d)' % \
                        (type, host, str(date), random.randint(1, 100))
            cur.execute(sql)
            records = records + 1
            
    conn.commit()
    cur.close()
    conn.close()
    return records

if __name__ == "__main__":
    init()
    date_now = datetime(2012, 11, 11)
    date_end = datetime(2012, 11, 12)
    start = time.time()
    
    total_records = 0
    
    while date_now < date_end:
        
        task_start = time.time()
        records = generate_data(date_now)
        total_records = total_records + records
        
        date_now = date_now + timedelta(seconds = 10)
        task_end = time.time()
        
        print '记录了 %d 条记录, 花费 %s 秒 Total: %d' % \
                (records, task_end - task_start, total_records)
                
    end = time.time()
        
    print 'TOTAL COST : %s' % (end - start)
        