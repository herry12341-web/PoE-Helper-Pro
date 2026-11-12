"""Taiwan zone names and Windows-safe image filenames. Run to migrate existing maps."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAMES=json.loads((ROOT/'data/zone_names.zh-TW.json').read_text(encoding='utf-8'))['zones']
def zone_name(zone_id):
    return NAMES[zone_id]  # Require explicit translations for new source regions.
def image_caption(name,index):
    return f'{name}｜參考圖 {index:02d}'
def image_filename(name,index,digest,extension):
    safe=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',name).strip(' .')
    return f'{safe}_參考圖{index:02d}_{digest}{extension}'
def localize(data, root=ROOT):
    for zone in data['zones']:
        zone.setdefault('source_zone_name',zone['zone_name'])
        zone['zone_name']=zone_name(zone['zone_id'])
        for index,im in enumerate(zone['map_images'],1):
            old=Path(im['src']); digest=re.search(r'([a-f0-9]{16})$',old.stem)[1]
            dest=old.with_name(image_filename(zone['zone_name'],index,digest,old.suffix))
            if dest!=old:(root/old).rename(root/dest)
            im.setdefault('source_caption',im['caption']);im['caption']=image_caption(zone['zone_name'],index);im['src']=dest.as_posix()
    return data
if __name__=='__main__':
    p=ROOT/'data/acts_data.json';d=localize(json.loads(p.read_text(encoding='utf-8')));p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    p=ROOT/'data/extra_zones.json';zones=json.loads(p.read_text(encoding='utf-8'))
    for z in zones:z['zone_name']=zone_name(z['zone_id'])
    p.write_text(json.dumps(zones,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Localized',len(d['zones']),'zones and',sum(len(z['map_images']) for z in d['zones']),'images')
