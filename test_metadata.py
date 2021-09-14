import json
import math
fname = 'C:\\Users\\kubus\\Documents\\test\\metadata.txt'
with open(fname) as f:
    out =  [json.loads(l) for l in f]

tm = [x['acquire_time'] for x in out]
times = [math.floor((x-tm[0])/1000) for x in tm]
print(times)
        