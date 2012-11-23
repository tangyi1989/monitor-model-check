#*_* coding=utf8 *_*

from pymongo import Connection
from datetime import datetime
from datetime import timedelta
import time
import mongodb
import random
import pprint

"""
不停的记录,不停的记录,交给stat_mapreduce.js进行归档.
然后悲剧了,见测试结果.
"""
INST_PREFIX = 'instance-%08x'
COLLECTE = ['cpu', 'mem', 'disk_write', 'disk_read', 'vnet_up', 'vnet_down']
    
report_value = 0;

def generate_data(report_time):
    global report_value
    records = []
    
    for i in range(1, 1001):
        host = INST_PREFIX % i
        timestamp = int(report_time.strftime('%s'))
        
        record = dict(name = host)
        record['timestamp'] = timestamp
        record['performance'] = dict()
        for type in COLLECTE:
            record['performance'][type] = report_value
            
        records.append(record)
    
    report_value = report_value + 1
        
    return records

def record_perf_records(perf_records):
    conn = get_mongo_conn()
    vm_perf = conn.vm_perf
    vm_hour = vm_perf.hour
    
    for record in perf_records:
        vm_hour.insert(record)
    
def record_data_loop():
    start_time = datetime(2012, 11, 11)
    end_time = start_time + timedelta(hours = 1)
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
        options = dict(capped = True, size=1000*2*24*60*60, max=1000*2*24*60*60)
        if col_name not in db.collection_names():
            db.create_collection(col_name, )
            coll = db[col_name]
            for index in indexes:
                coll.ensure_index(index)
    
    conn = Connection(host='localhost', port=27017)
    create_col_if_not_exist(conn.vm_perf, 'hour', ['name', "timestamp"])
    create_col_if_not_exist(conn.vm_perf, 'hour', ['name'])
    
if __name__ == "__main__":
    init_mongo_db()
    start = time.time()
    record_data_loop()
    end = time.time()
    print 'Total cost : %s' % (end - start)
    