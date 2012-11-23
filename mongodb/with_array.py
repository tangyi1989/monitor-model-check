#*_* coding=utf8 *_*

from pymongo import Connection
from datetime import datetime
from datetime import timedelta
import time
import mongodb
import random
import pprint

"""
使用数组的时候:
使用upsert的时候,更新后不阻塞,但有如下问题:
1.数组中的数据顺序和客户端更新的顺序无法保证相同,需要做特殊处理
2.upsert过快导致数据库崩溃. insert的效率倒是很高.
"""

record_value = 0
def generate_data(report_time):
    global record_value
    
    inst_prefix = 'instance-%08x'
    collect_type = ['cpu', 'mem', 'disk_read', 'disk_write', 'disk_read', 
                    'vnet_up', 'vnet_down']
    records = []
    
    record_value = record_value + 1
    
    for i in range(1, 1001):
        host = inst_prefix % i
        
        record = dict(name = host)
        record['report_time'] = report_time
        record['performance'] = dict()
        for type in collect_type:
            record['performance'][type] = record_value
            
        records.append(record)
        
    return records

def rescord_upsert_arg(record):
    upsert_arg = dict()
    
    upsert_arg['$set'] = {'last_report_time' : record['report_time']}
    upsert_arg['$inc'] = {'unarchive' : 1}
    upsert_arg['$push'] = dict()
    upsert_arg['$push']['report_time'] = record['report_time']
    for k, v in record['performance'].items():
        upsert_arg['$push']['performance.' + k] = v
    
    return upsert_arg
    
def record_perf_records(perf_records):
    conn = get_mongo_conn()
    perf_db = conn.perf_db
    
    vm_hour = perf_db.vm_hour
    vm_week = perf_db.vm_week
    
    for record in perf_records:
        update_key = {"name" : record['name']}
        upsert_arg = rescord_upsert_arg(record)
        
        ret = vm_hour.update(update_key, upsert_arg, True)
    
def record_data_loop():
    start_time = datetime(2012, 11, 11)
    end_time = datetime(2012, 11, 12)
    current_time = start_time
    
    while current_time < end_time:
        
        perf_records = generate_data(current_time)
        start = time.time()
        record_perf_records(perf_records)
        stop = time.time()
        print 'Insert %d record, cost %s' % (len(perf_records), stop - start)
        current_time = current_time + timedelta(seconds = 10)

def get_mongo_conn():
    conn = Connection(host='localhost', port=27017)
    return conn

def init_mongo_db():
    def create_col_if_not_exist(db, col_name, indexes=[]):
        options = dict(capped = True, size=3600, max=3600)
        if col_name not in db.collection_names():
            db.create_collection(col_name, )
            coll = db[col_name]
            for index in indexes:
                coll.ensure_index(index)
    
    conn = Connection(host='localhost', port=27017)
    create_col_if_not_exist(conn.perf_db, 'vm_hour', ['name'])
    create_col_if_not_exist(conn.perf_db, 'vm_week', ['name'])
    
if __name__ == "__main__":
    init_mongo_db()
    record_data_loop()
    