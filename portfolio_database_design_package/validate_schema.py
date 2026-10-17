import re
from pathlib import Path
BASE=Path(__file__).resolve().parent
core=(BASE/'portfolio_creation_schema.sql').read_text()
optional=(BASE/'portfolio_optional_extensions.sql').read_text()
demo=(BASE/'portfolio_schema_demo.sql').read_text()
def split_top(text):
 out=[];cur='';d=0;q=False;i=0
 while i<len(text):
  c=text[i]
  if c=="'":
   if q and i+1<len(text) and text[i+1]=="'": cur+=c+text[i+1];i+=2;continue
   q=not q
  elif not q:
   if c=='(':d+=1
   elif c==')':d-=1
   elif c==',' and d==0:out.append(cur.strip());cur='';i+=1;continue
  cur+=c;i+=1
 if cur.strip():out.append(cur.strip())
 return out
def parse(s):
 ts={}
 for m in re.finditer(r'CREATE TABLE\s+(\w+)\s*\((.*?)\n\);',s,re.S|re.I):
  n,b=m.group(1),m.group(2); items=split_top(b); cols=set(); pk=[]; uniques=[]; fks=[]
  for item in items:
   if re.match(r'^(CONSTRAINT|PRIMARY\s+KEY|FOREIGN\s+KEY|UNIQUE|CHECK|EXCLUDE)\b',item,re.I):
    z=re.search(r'PRIMARY KEY\s*\(([^)]+)\)',item,re.I)
    if z: pk=[x.strip() for x in z.group(1).split(',')];uniques.append(pk)
    z=re.search(r'UNIQUE\s*\(([^)]+)\)',item,re.I)
    if z: uniques.append([x.strip() for x in z.group(1).split(',')])
    z=re.search(r'FOREIGN KEY\s*\(([^)]+)\)\s*REFERENCES\s+(\w+)\s*\(([^)]+)\)',item,re.I)
    if z: fks.append(([x.strip() for x in z.group(1).split(',')],z.group(2),[x.strip() for x in z.group(3).split(',')]))
   else:
    c=re.match(r'^(\w+)\s+([A-Z]+(?:\s*\([^)]*\))?)(?=\s|$)(.*)$',re.sub(r'\s+',' ',item),re.I)
    if not c: print('column parse warning',n,item);continue
    cn,rest=c.group(1),c.group(3);cols.add(cn)
    if re.search(r'\bPRIMARY KEY\b',rest,re.I): pk.append(cn);uniques.append([cn])
    if re.search(r'\bUNIQUE\b',rest,re.I): uniques.append([cn])
    z=re.search(r'REFERENCES\s+(\w+)\s*\((\w+)\)',rest,re.I)
    if z:fks.append(([cn],z.group(1),[z.group(2)]))
  if pk and pk not in uniques: uniques.append(pk)
  ts[n]={'cols':cols,'unique':uniques,'fks':fks,'items':items}
 return ts
core_t=parse(core);opt_t=parse(optional)
# Combine for optional references to core
all_t={**core_t,**opt_t}
issues=[]
# Duplicate table names
for n in set(core_t)&set(opt_t):issues.append(('duplicate_table',n))
for n,t in all_t.items():
 for src,parent,dst in t['fks']:
  if parent not in all_t: issues.append(('missing_parent_table',n,parent,src,dst));continue
  for c in src:
   if c not in t['cols']:issues.append(('missing_child_column',n,c))
  for c in dst:
   if c not in all_t[parent]['cols']:issues.append(('missing_parent_column',parent,c))
  if not any(key==dst for key in all_t[parent]['unique']):
   issues.append(('referenced_columns_not_unique_key',n,src,parent,dst,all_t[parent]['unique']))
# all indexes point to known table
for s in (core,optional):
 for m in re.finditer(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(\w+)\s+ON\s+(\w+)\s*\((.*?)\)(?:\s+WHERE\s+(.*?))?;',s,re.S|re.I):
  idx,tab,cols,where=m.groups()
  if tab not in all_t: issues.append(('index_missing_table',idx,tab));continue
  # check raw simple column/index expression names. Ignore expressions such as lower(email).
  for col in re.split(r',\s*(?![^()]*\))',cols):
   col=col.strip()
   if re.fullmatch(r'\w+(?:\s+(?:ASC|DESC))?',col,re.I):
    cname=re.match(r'(\w+)',col).group(1)
    if cname not in all_t[tab]['cols']:issues.append(('index_missing_column',idx,tab,cname))
print(f'Core tables: {len(core_t)}, core columns: {sum(len(t["cols"]) for t in core_t.values())}')
print(f'Optional tables: {len(opt_t)}, optional columns: {sum(len(t["cols"]) for t in opt_t.values())}')
print(f'FK declarations checked: {sum(len(t["fks"]) for t in all_t.values())}')
print(f'Issues: {len(issues)}')
for x in issues: print('ISSUE',x)
# simple paren/string balance scanner (ignores comments, handles SQL single-quote escaping and dollar body)
def balance(txt,path):
 i=0;depth=0;quote=False;line_comment=False;block=False;dollar=None
 while i<len(txt):
  c=txt[i]; nxt=txt[i+1] if i+1<len(txt) else ''
  if line_comment:
   if c=='\n':line_comment=False
   i+=1;continue
  if block:
   if c=='*' and nxt=='/':block=False;i+=2;continue
   i+=1;continue
  if dollar:
   if txt.startswith(dollar,i):i+=len(dollar);dollar=None;continue
   i+=1;continue
  if not quote and c=='-' and nxt=='-':line_comment=True;i+=2;continue
  if not quote and c=='/' and nxt=='*':block=True;i+=2;continue
  if not quote and c=='$':
   mt=re.match(r'\$[A-Za-z_0-9]*\$',txt[i:])
   if mt:dollar=mt.group();i+=len(dollar);continue
  if c=="'":
   if quote and nxt=="'":i+=2;continue
   quote=not quote;i+=1;continue
  if not quote:
   if c=='(':depth+=1
   elif c==')':depth-=1
   if depth<0:print('Paren early close',path,i);return
  i+=1
 print(path,'balance',depth,'quote',quote,'dollar',dollar,'block',block)
for f,s in [(BASE/'portfolio_creation_schema.sql',core),(BASE/'portfolio_optional_extensions.sql',optional),(BASE/'portfolio_schema_demo.sql',demo)]:balance(s,str(f))
if issues: raise SystemExit(1)

# Verify that every named INSERT target and column in the demo seed exists.
for m in re.finditer(r'INSERT\s+INTO\s+(\w+)\s*\(([^)]*)\)', demo, re.I | re.S):
    table=m.group(1)
    columns=[x.strip() for x in m.group(2).split(',')]
    if table not in all_t:
        issues.append(('demo_insert_missing_table',table)); continue
    for column in columns:
        if column not in all_t[table]['cols']:
            issues.append(('demo_insert_missing_column',table,column))
if issues:
    print('Validation failed after demo INSERT checks:', issues)
    raise SystemExit(1)
print('Demo INSERT column references: PASS')
