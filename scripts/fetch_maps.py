#!/usr/bin/env python3
"""Standalone, resumable Definitiv Guide downloader. No startup integration.
Run: python3 scripts/fetch_maps.py [--delay 1.5]
Sources retain copyright; review permissions before redistributing assets.
"""
import argparse, hashlib, json, re, time
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit, quote, unquote
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

try:
    from .localize_maps import zone_name, image_filename, image_caption
except ImportError:
    from localize_maps import zone_name, image_filename, image_caption

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://www.definitivguide.com'
UA = 'PoEHelperMapArchive/1.0 (personal offline guide; polite sequential requests)'

class Article(HTMLParser):
    def __init__(self):
        super().__init__(); self.active=False; self.images=[]; self.blocks=[]; self.text=[]; self.capture=None; self.title=''
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='div' and 'theme-doc-markdown' in attrs.get('class',''): self.active=True
        if not self.active: return
        if tag=='img' and attrs.get('src'):
            self.images.append({'src':attrs['src'], 'caption':attrs.get('alt','Layout')})
        if tag in ('h1','p','li'):
            self.capture=tag; self.text=[]
    def handle_data(self, data):
        if self.active and self.capture: self.text.append(data)
    def handle_endtag(self,tag):
        if self.active and tag==self.capture:
            text=' '.join(''.join(self.text).replace('\u200b','').split())
            if tag=='h1': self.title=text
            elif text: self.blocks.append(text)
            self.capture=None
        if tag=='article': self.active=False

def validate(data):
    assert {z['act'] for z in data['zones']}==set(range(1,11)), 'Missing act'
    assert len({z['zone_id'] for z in data['zones']})==len(data['zones'])
    zone_ids={z['zone_id'] for z in data['zones']}
    assert len({s['id'] for s in data['steps']})==len(data['steps'])
    for step in data['steps']:
        assert step['zone_id'] in zone_ids and step['act'] in range(1,11) and step['text']
    for z in data['zones']:
        assert z['zone_name'] and isinstance(z['speedrun_tips'],list) and isinstance(z['gem_purchases'],list)
        for im in z['map_images']:
            p=ROOT/im['src']; assert p.is_file() and p.stat().st_size>0, str(p)
    for act in range(1,11):
        assert any(z['map_images'] for z in data['zones'] if z['act']==act), f'No images in Act {act}'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--delay',type=float,default=1.0); args=ap.parse_args()
    if not 1<=args.delay<=2: ap.error('--delay must be between 1 and 2 seconds')
    cache=ROOT/'.map-cache'; cache.mkdir(exist_ok=True)
    existing_images={re.search(r'([a-f0-9]{16})$',p.stem)[1]:p for p in (ROOT/'assets/maps').rglob('*') if p.is_file() and not p.name.endswith('.tmp')}
    last=0; robot=None
    def get(url, dest=None):
        nonlocal last
        url=quote(unquote(url),safe=':/?=&%')
        if urlsplit(url).netloc!=urlsplit(BASE).netloc: raise ValueError('External host: '+url)
        if robot and not robot.can_fetch(UA,url): raise ValueError('robots.txt disallows '+url)
        p=dest or cache/hashlib.sha256(url.encode()).hexdigest()
        if p.exists() and p.stat().st_size: return p.read_bytes()
        if dest and re.search(r'([a-f0-9]{16})$',dest.stem)[1] in existing_images:
            content=existing_images[re.search(r'([a-f0-9]{16})$',dest.stem)[1]].read_bytes();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content);return content
        for attempt in range(3):
            time.sleep(max(0,args.delay-(time.monotonic()-last)))
            try:
                last=time.monotonic()
                with urlopen(Request(url,headers={'User-Agent':UA}),timeout=45) as response:
                    content=response.read(); kind=response.headers.get('Content-Type','')
                    if dest and not kind.startswith('image/'): raise ValueError('Not image: '+url)
                p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_bytes(content);tmp.replace(p)
                if dest: existing_images[re.search(r'([a-f0-9]{16})$',dest.stem)[1]]=dest
                return content
            except HTTPError as ex:
                if ex.code not in (429,500,502,503,504) or attempt==2: raise
                time.sleep(min(60,float(ex.headers.get('Retry-After','5')))*(attempt+1))
            except (TimeoutError, OSError):
                if attempt==2: raise
                time.sleep(3*(attempt+1))
    try:
        rules=get(BASE+'/robots.txt').decode(); robot=RobotFileParser(); robot.parse(rules.splitlines())
    except HTTPError as ex:
        if ex.code!=404: raise
        print('robots.txt: 404; no published rules',flush=True)
    sitemap=ET.fromstring(get(BASE+'/sitemap.xml'))
    urls=sorted({e.text for e in sitemap.iter() if e.tag.endswith('loc') and re.search(r'/PoE1/Act(?:%20| )(?:10|[1-9])/',e.text or '')},key=lambda u:(int(re.search(r'Act (\d+)',unquote(u))[1]),u))
    zones=[]; failures=[]
    for index,url in enumerate(urls):
        try:
            act=int(re.search(r'Act (\d+)',unquote(url))[1]); slug=re.sub('[^a-z0-9]+','-',unquote(url).rstrip('/').split('/')[-1].lower()).strip('-')
            parser=Article();parser.feed(get(url).decode())
            if not parser.title: raise ValueError('Missing article title')
            zid=f'a{act}-{slug}'; name=zone_name(zid); images=[]
            for j,im in enumerate(parser.images):
                remote=urljoin(url,im['src']); ext=Path(unquote(urlsplit(remote).path)).suffix.lower()
                if ext not in ('.png','.jpg','.jpeg','.webp','.gif','.svg'): continue
                filename=image_filename(name,j+1,hashlib.sha256(remote.encode()).hexdigest()[:16],ext)
                relative=f'assets/maps/act{act:02d}/{slug}/{filename}'
                get(remote,ROOT/relative)
                images.append({'id':f'{zid}-{j+1}','src':relative,'caption':image_caption(name,j+1),'source_caption':im['caption'],'source_url':remote,'credit':'CyclonDefinitiv / Definitiv Guide'})
            zones.append({'zone_id':zid,'act':act,'zone_name':name,'source_zone_name':parser.title,'map_images':images,'speedrun_tips':parser.blocks,'gem_purchases':[],'source_url':url})
            print(f'[{index+1}/{len(urls)}] A{act} {parser.title}: {len(images)} images',flush=True)
        except Exception as ex:
            failures.append({'url':url,'error':str(ex)}); print('FAILED',url,str(ex),flush=True)
    extra=ROOT/'data/extra_zones.json'
    if extra.exists(): zones.extend(json.loads(extra.read_text()))
    report={'pages':len(urls),'zones':len(zones),'images':sum(len(z['map_images']) for z in zones),'failures':failures,'acts':{str(a):sum(len(z['map_images']) for z in zones if z['act']==a) for a in range(1,11)}}
    (ROOT/'data').mkdir(exist_ok=True);(ROOT/'data/fetch-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    if failures: raise SystemExit('Incomplete download; previous acts_data.json preserved. Rerun to resume.')
    data={'schema_version':1,'game':'poe1','game_version':'source-current-unverified','route_id':'definitiv-layouts','sources':[{'name':'Definitiv Guide','url':BASE,'attribution':'CyclonDefinitiv','route_attribution':'Not independently verified as Tytykiller or Havoc616 route'}],'zones':zones,'steps':[]}
    route=ROOT/'data/route_steps.json'
    if route.exists(): data['steps']=json.loads(route.read_text())
    references=ROOT/'data/route_sources.json'
    if references.exists(): data['sources'].extend(json.loads(references.read_text()))
    validate(data); target=ROOT/'data/acts_data.json'; tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2));tmp.replace(target)
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__': main()
