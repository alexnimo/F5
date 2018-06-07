# how to extract table data from admdb in one shot, using python code injection
s = b"""
import os,json

def chch2a(chch):
    # convert 2 chars encode, to ascii char
    if chch[0]=='_':
        return chch[1]
    else:
        return chr(int(chch,16))

def fixedDecodeURIComponent(vs):
    # demangles encoded vs name
    return "".join([chch2a(vs[i:i+2]) for i in range(0, len(vs), 2)])
    
    
def vs_table_query(base_path='/ts/dms/dos/bados/admdb',db='default'):
    # return list of virtual servers (not demangled) in db (except for 'all' component)
    return [x for x in os.listdir(os.path.join(base_path,db)) if x!='_a_l_l']

def cell_table_query(base_path,db,vs_raw,metric,sRate,columns,tsfiles,ts):
    #ts=(from,to)
    # returns {columns:[cola,colb],rows[[a,b]]}
    for tsfile in reversed(tsfiles): # from last file
        try:
            with open(os.path.join(base_path,db,vs_raw,metric,str(sRate),tsfile+'.txt'),'r') as f:
                try:
                    j=json.loads(f.read()+']}')
                    cols = j['properties']['columns']
                    d=dict(zip(cols,range(len(cols))))
                    tcol=d['time']
                    if columns!="*":
                        d=dict([(k,d[k]) for k in columns if k in d]) #col:idx
                    for v in reversed(j['values']):
                        if v[tcol]<=ts[1] and v[tcol]>=ts[0]:
                            return {'columns':d.keys(),'rows':[[v[i] for i in d.values()]]}
                except:
                    pass
        except:pass
    return {'columns':[], 'rows':[]}
    
def table_query(base_path,db,sRate,tsfiles,ts,metric_columns):
    vs_raw_list = vs_table_query(base_path,db)
    ret = { "columns": [{"text":"vs"}], "rows":[], "type":"table" } # 
    for ixrow,vs_raw in enumerate(vs_raw_list):
        row = [fixedDecodeURIComponent(vs_raw)]
        for mc in metric_columns:
            r=cell_table_query(base_path,db,vs_raw,mc[0],sRate,mc[1],tsfiles,ts)
            if ixrow==0:
                ret['columns']+=[{"text":mc[0]+'.'+c} for c in r['columns']]
            if len(r['rows']) and len(r['rows'][0])==len(r['columns']):
                row+=r['rows'][0]
            else:
                row+=[0]*len(r['columns'])   
        ret['rows'].append(row)
             
        
    return json.dumps(ret)

#print vs_table_query()
#print cell_table_query('/ts/dms/dos/bados/admdb','default','2f_C_o_m_m_o_n2f_d_a_t_a','sig.tps',1000,["v0"],['1471346688000'],(1471347709000,1471347710000))
print table_query('/ts/dms/dos/bados/admdb','default',1000,['1471354880000'],(1471355030000,1471355030000),[['sig.tps','*']])
"""

import base64;
s = base64.b64encode(s)
#s=b'cHJpbnQgW3ggZm9yIHggaW4gcmFuZ2UoMTApXQ=='
#print(s.decode('ascii'))
print (requests.post('https://10.241.108.22/mgmt/tm/util/bash', verify=False, headers = {'content-type': 'application/json'}, 
                     auth=HTTPBasicAuth('admin', 'admin'), 
                     data=json.dumps({"command":"run","utilCmdArgs": 
                                      "-c \"echo '"+s.decode('ascii')+"' |python -c 'import base64; exec(base64.b64decode(raw_input()))' \""
                                     })).json())