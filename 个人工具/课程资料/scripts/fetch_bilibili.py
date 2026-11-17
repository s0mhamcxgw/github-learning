"""Read public Bilibili course metadata and a selected lesson's materials.

Only writes work-cache files. It never writes or overwrites vault notes.
"""
import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36'


def request(url, referer='https://www.bilibili.com/'):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':UA,'Referer':referer}), timeout=30)


def api(route, params):
    url='https://api.bilibili.com/'+route+'?'+urllib.parse.urlencode(params)
    with request(url) as response:
        result=json.load(response)
    if result.get('code') != 0:
        raise RuntimeError(f'平台接口未成功：{result.get("code")} {result.get("message","")}')
    return result.get('data') or {}


def parse_link(value):
    if re.fullmatch(r'BV[A-Za-z0-9]{10}',value):
        return value,1
    parsed=urllib.parse.urlparse(value)
    if parsed.hostname=='b23.tv':
        with request(value) as response:
            parsed=urllib.parse.urlparse(response.url)
    if not (parsed.hostname or '').endswith('.bilibili.com') and parsed.hostname!='bilibili.com':
        raise ValueError('需要B站视频链接或BV号')
    match=re.search(r'/video/(BV[A-Za-z0-9]{10})(?:/|$)',parsed.path)
    if not match:
        raise ValueError('未找到视频BV号；请使用具体视频页面链接')
    part=int(urllib.parse.parse_qs(parsed.query).get('p',['1'])[0])
    return match[1],part


def save_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',required=True)
    parser.add_argument('--work-dir',type=Path,required=True)
    parser.add_argument('--download-audio',action='store_true',help='Only the selected part, and only when no public subtitle is returned')
    args=parser.parse_args()
    bvid,part=parse_link(args.url)
    root=args.work_dir.resolve()
    root.mkdir(parents=True,exist_ok=True)
    old=root/'course.json'
    if old.exists() and json.loads(old.read_text(encoding='utf-8')).get('bvid')!=bvid:
        raise ValueError('工作目录已属于另一门课程；请换一个工作目录')
    data=api('x/web-interface/view',{'bvid':bvid})
    pages=[{'page':p['page'],'cid':p['cid'],'title':p['part'],'duration':p['duration'],
            'url':f'https://www.bilibili.com/video/{bvid}/?p={p["page"]}'} for p in data.get('pages',[])]
    selected=next((p for p in pages if p['page']==part),None)
    if not selected:
        raise ValueError(f'分P {part} 不在已核实课程目录中')
    course={'bvid':bvid,'aid':data['aid'],'title':data['title'],'publisher':data['owner']['name'],
            'publisher_mid':data['owner']['mid'],'description':data.get('desc',''),
            'url':f'https://www.bilibili.com/video/{bvid}/','pages':pages,'selected_part':part}
    save_json(root/'course.json',course)
    manifest={'bvid':bvid,'part':part,'cid':selected['cid'],'source_url':selected['url'],
              'subtitle_status':'not_returned','subtitle_file':None,'audio_file':None}
    previous_path=root/f'part-{part:03d}-manifest.json'
    previous=json.loads(previous_path.read_text(encoding='utf-8')) if previous_path.exists() else None
    cached_audio=root/f'part-{part:03d}-audio.m4a'
    if cached_audio.exists() and (not previous or previous.get('cid')!=selected['cid']):
        raise ValueError('已有音轨的来源与当前分P/CID未能匹配，停止复用；请指定新的工作目录')
    try:
        player=api('x/player/v2',{'aid':course['aid'],'cid':selected['cid']})
        subtitles=(player.get('subtitle') or {}).get('subtitles') or []
        usable=[s for s in subtitles if s.get('subtitle_url')]
        usable.sort(key=lambda s:(not str(s.get('lan','')).startswith('zh'),bool(s.get('ai_type'))))
        if usable:
            subtitle=usable[0]
            url=subtitle['subtitle_url']
            if url.startswith('//'):url='https:'+url
            parsed=urllib.parse.urlparse(url)
            if parsed.scheme!='https' or not (parsed.hostname or '').endswith('.hdslb.com'):
                raise ValueError('字幕地址不是预期的平台HTTPS资源域名，停止自动读取')
            with request(url,selected['url']) as response:
                payload=json.load(response)
            segments=[{'start':float(s['from']),'end':float(s['to']),'text':s['content']} for s in payload.get('body',[])]
            if any(s['start']<0 or s['end']<s['start'] for s in segments):
                raise ValueError('字幕时间范围异常')
            target=root/f'part-{part:03d}-subtitles.json'
            save_json(target,{'source':'platform_subtitle','language':subtitle.get('lan_doc'),'segments':segments})
            manifest.update(subtitle_status='available',subtitle_file=str(target),subtitle_segments=len(segments))
    except Exception as error:
        manifest.update(subtitle_status='unavailable',subtitle_error=str(error))
    if args.download_audio and manifest['subtitle_status']!='available':
        play=api('x/player/playurl',{'bvid':bvid,'cid':selected['cid'],'fnval':16,'qn':16,'fourk':0})
        audios=(play.get('dash') or {}).get('audio') or []
        if not audios:
            manifest['audio_status']='not_returned; no restricted-content workaround attempted'
        else:
            audio=max(audios,key=lambda item:item.get('bandwidth',0))
            url=audio.get('baseUrl') or audio.get('base_url')
            parsed=urllib.parse.urlparse(url)
            if parsed.scheme!='https' or not any((parsed.hostname or '').endswith('.'+suffix) for suffix in ['bilivideo.com','bilivideo.cn','biliapi.net']):
                raise ValueError('音轨地址不是预期的平台HTTPS资源域名，停止自动读取')
            target=root/f'part-{part:03d}-audio.m4a'
            if not target.exists():
                temp=target.with_suffix('.partial')
                try:
                    with request(url,selected['url']) as response,temp.open('wb') as out:
                        while block:=response.read(1048576):out.write(block)
                    temp.replace(target)
                finally:
                    if temp.exists():temp.unlink()
            digest=hashlib.sha256(target.read_bytes()).hexdigest()
            manifest.update(audio_file=str(target),audio_status='downloaded',audio_bytes=target.stat().st_size,audio_sha256=digest)
    save_json(root/f'part-{part:03d}-manifest.json',manifest)
    print(json.dumps({'course':course['title'],'publisher':course['publisher'],'lessons':len(pages),
                      'current':selected,'materials':manifest},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
