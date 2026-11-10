import json, os, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HOST='0.0.0.0'; PORT=5000
DATA_DIRECTORY=os.getenv('DATA_DIRECTORY','/var/lib/backend_data')
DATA_FILE=os.path.join(DATA_DIRECTORY,'tasks.json')

def now(): return datetime.now(timezone.utc).isoformat()
def init():
    os.makedirs(DATA_DIRECTORY,exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE,'w',encoding='utf-8') as f: json.dump([],f)
def read():
    init()
    try:
        with open(DATA_FILE,encoding='utf-8') as f:
            data=json.load(f); return data if isinstance(data,list) else []
    except (OSError,json.JSONDecodeError): return []
def write(data):
    init(); tmp=DATA_FILE+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
    os.replace(tmp,DATA_FILE)
def normalize(body,old=None):
    old=old or {}; title=str(body.get('title',body.get('task',old.get('title',old.get('task',''))))).strip()
    member=str(body.get('member',old.get('member',''))).strip(); deadline=str(body.get('deadline',old.get('deadline',''))).strip()
    desc=str(body.get('description',old.get('description',''))).strip(); category=str(body.get('category',old.get('category','Lainnya'))).strip()
    priority=str(body.get('priority',old.get('priority','medium'))).lower(); status=str(body.get('status',old.get('status','todo'))).lower()
    if not title or not member or not deadline: raise ValueError('Judul, penanggung jawab, dan deadline wajib diisi')
    datetime.strptime(deadline,'%Y-%m-%d')
    if priority not in {'low','medium','high'}: raise ValueError('Prioritas tidak valid')
    if status not in {'todo','in_progress','completed'}: raise ValueError('Status tidak valid')
    return {'id':old.get('id') or 'task-'+uuid.uuid4().hex[:10], 'title':title[:120], 'task':title[:120], 'description':desc[:500], 'member':member[:60], 'category':category[:40], 'priority':priority, 'status':status, 'deadline':deadline, 'created_at':old.get('created_at') or now(), 'updated_at':now()}

class H(BaseHTTPRequestHandler):
    def sendj(self,code,payload):
        raw=json.dumps(payload,ensure_ascii=False).encode(); self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(raw)
    def body(self):
        n=int(self.headers.get('Content-Length','0'))
        if n<1 or n>200000: raise ValueError('Body tidak valid')
        return json.loads(self.rfile.read(n).decode())
    def index(self,items,q):
        ident=q.get('id',[''])[0]
        if ident:
            return next((i for i,x in enumerate(items) if x.get('id')==ident),-1)
        try: return int(q.get('index',['-1'])[0])
        except ValueError: return -1
    def do_GET(self):
        p=urlparse(self.path)
        if p.path=='/health':
            writable=os.access(DATA_DIRECTORY,os.W_OK); self.sendj(200,{'status':'healthy','service':'orbitask-api','storage':'writable' if writable else 'readonly','checked_at':now()}); return
        if p.path=='/tasks':
            items=read()
            for x in items:
                if 'title' not in x: x['title']=x.get('task','Tanpa judul')
                x.setdefault('status','todo'); x.setdefault('category','Lainnya'); x.setdefault('description',''); x.setdefault('updated_at',x.get('created_at',now()))
            self.sendj(200,{'status':'success','count':len(items),'data':items}); return
        if p.path=='/stats':
            items=read(); counts={s:sum(1 for x in items if x.get('status','todo')==s) for s in ['todo','in_progress','completed']}
            members={}
            for x in items:
                m=x.get('member','Tidak ditentukan'); members.setdefault(m,{'total':0,'completed':0}); members[m]['total']+=1; members[m]['completed']+=x.get('status')=='completed'
            self.sendj(200,{'status':'success','data':{'total':len(items),**counts,'members':members}}); return
        self.sendj(404,{'status':'error','message':'Endpoint tidak ditemukan'})
    def do_POST(self):
        if urlparse(self.path).path!='/tasks': self.sendj(404,{'status':'error','message':'Endpoint tidak ditemukan'}); return
        try:
            item=normalize(self.body()); items=read(); items.append(item); write(items); self.sendj(201,{'status':'success','message':'Tugas berhasil dibuat','data':item})
        except (ValueError,json.JSONDecodeError) as e: self.sendj(400,{'status':'error','message':str(e)})
    def do_PUT(self):
        p=urlparse(self.path); items=read(); i=self.index(items,parse_qs(p.query))
        if p.path!='/tasks' or i<0 or i>=len(items): self.sendj(404,{'status':'error','message':'Tugas tidak ditemukan'}); return
        try:
            items[i]=normalize(self.body(),items[i]); write(items); self.sendj(200,{'status':'success','message':'Tugas berhasil diperbarui','data':items[i]})
        except (ValueError,json.JSONDecodeError) as e: self.sendj(400,{'status':'error','message':str(e)})
    def do_PATCH(self):
        p=urlparse(self.path); items=read(); i=self.index(items,parse_qs(p.query))
        if p.path!='/tasks/status' or i<0 or i>=len(items): self.sendj(404,{'status':'error','message':'Tugas tidak ditemukan'}); return
        try:
            body=self.body(); status=str(body.get('status',''))
            if status not in {'todo','in_progress','completed'}: raise ValueError('Status tidak valid')
            items[i]['status']=status; items[i]['updated_at']=now(); write(items); self.sendj(200,{'status':'success','message':'Status tugas diperbarui','data':items[i]})
        except (ValueError,json.JSONDecodeError) as e: self.sendj(400,{'status':'error','message':str(e)})
    def do_DELETE(self):
        p=urlparse(self.path); items=read(); i=self.index(items,parse_qs(p.query))
        if p.path!='/tasks' or i<0 or i>=len(items): self.sendj(404,{'status':'error','message':'Tugas tidak ditemukan'}); return
        deleted=items.pop(i); write(items); self.sendj(200,{'status':'success','message':'Tugas dihapus permanen','data':deleted})
    def log_message(self,fmt,*args): print('[Orbitask API]',fmt%args)
if __name__=='__main__': init(); print('Orbitask API port',PORT); ThreadingHTTPServer((HOST,PORT),H).serve_forever()
