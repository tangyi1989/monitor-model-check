/*
 对一个小时内的记录数据进行归档,把每600秒数据取平均数合成一条数据.
 注意:mapreduce数据过多将导致mongodb崩溃.
*/

function mapf(){
	var timestamp = this.timestamp - (this.timestamp % 600);
	var key = this.name + '@' + timestamp.toString();
	
	emit(key, {performance : this.performance});
}

function reducef(key, values){
	var count = 0;
	var properties = ['cpu', 'mem', 'disk_write', 'disk_read', 'vnet_up', 'vnet_down'];
	var keys = key.split('@');
	
	var sum = {};
	for(var i=0; i < properties.length; i++){
		sum[properties[i]] = 0
	}
	
    values.forEach(function(value) {
    	var performance = value.performance;
    	for(var i in performance){
    		sum[i] += performance[i];
    	}
    	count ++;
    });
    
    var average = {};
    for(var i in sum){
    	average[i] = sum[i] / count;
    }

    return {name : keys[0], timestamp : keys[1], performance : average};
}

var job_start = new Date();

//进行归档统计
var stat_start_at = 1352563200 - 1;
var stat_end_at = stat_start_at + 10 * 60;
var vm_perf_db = db.getSiblingDB("vm_perf");
var cmd_result = vm_perf_db.runCommand({mapreduce:"hour",
			map:mapf,
			reduce:reducef,
			query: {timestamp: 
				{$gt : stat_start_at, $lt : stat_end_at}},
			out: {merge : "week"}
			});

var job_end = new Date();
var cost = (job_end - job_start) / 1000;
print(tojson(cmd_result));
print("Archive cost " + cost + " seconds.");
