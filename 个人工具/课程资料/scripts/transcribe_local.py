"""Transcribe a permitted local lesson audio into a work-cache JSON."""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audio',type=Path,required=True)
    p.add_argument('--output-json',type=Path,required=True)
    p.add_argument('--model-cache',type=Path,required=True)
    p.add_argument('--deps-dir',type=Path)
    p.add_argument('--model',default='base')
    p.add_argument('--language',default='zh')
    p.add_argument('--source-url',default='')
    p.add_argument('--max-seconds',type=float)
    a=p.parse_args()
    if a.max_seconds is not None and a.max_seconds<=0:raise ValueError('max-seconds必须大于0')
    if not a.audio.is_file():raise FileNotFoundError(a.audio)
    digest=hashlib.sha256(a.audio.read_bytes()).hexdigest()
    if a.output_json.exists():
        cached=json.loads(a.output_json.read_text(encoding='utf-8'))
        if (cached.get('audio_sha256')==digest and cached.get('limit_seconds')==a.max_seconds
            and cached.get('model')==a.model and cached.get('language')==a.language):
            print(json.dumps({'status':'cache_ready','segments':len(cached['segments'])}))
            return
        raise FileExistsError('同名转写文件已存在不同来源或参数，保留原文件，请指定新输出位置')
    a.model_cache.mkdir(parents=True,exist_ok=True)
    os.environ['HF_HOME']=str(a.model_cache/'hf-cache')
    os.environ['HF_HUB_DISABLE_XET']='1'
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING']='1'
    os.environ['HF_HUB_DOWNLOAD_TIMEOUT']='45'
    os.environ['HF_HUB_ETAG_TIMEOUT']='20'
    os.environ['OMP_NUM_THREADS']='4'
    if a.deps_dir:sys.path.insert(0,str(a.deps_dir.resolve()))
    import av
    import numpy as np
    from faster_whisper import WhisperModel

    chunks=[];samples=0
    limit=int(a.max_seconds*16000) if a.max_seconds else None
    with av.open(str(a.audio)) as container:
        resampler=av.AudioResampler(format='s16',layout='mono',rate=16000)
        for frame in container.decode(audio=0):
            for resampled in resampler.resample(frame):
                chunk=resampled.to_ndarray().reshape(-1)
                chunks.append(chunk);samples+=len(chunk)
            if limit and samples>=limit:break
        for resampled in resampler.resample(None):chunks.append(resampled.to_ndarray().reshape(-1))
    if not chunks:raise ValueError('音轨没有可解码的采样')
    waveform=np.concatenate(chunks).astype(np.float32)/32768.
    if limit:waveform=waveform[:limit]
    start=time.monotonic()
    model=WhisperModel(a.model,device='cpu',compute_type='int8',cpu_threads=4,download_root=str(a.model_cache))
    segments,info=model.transcribe(waveform,language=a.language,beam_size=5,temperature=0,
                                   vad_filter=True,vad_parameters={'min_silence_duration_ms':500})
    records=[]
    for s in segments:
        records.append({'start':s.start,'end':s.end,'text':s.text,'avg_logprob':s.avg_logprob})
        if len(records)%25==0:
            print(json.dumps({'segments':len(records),'audio_seconds':round(s.end),'elapsed_seconds':round(time.monotonic()-start)}),flush=True)
    payload={'source':'local_automatic_speech_recognition','audio_sha256':digest,'source_url':a.source_url,
             'model':a.model,'language':a.language,'limit_seconds':a.max_seconds,'duration':info.duration,
             'segments':records,'elapsed_seconds':round(time.monotonic()-start)}
    a.output_json.parent.mkdir(parents=True,exist_ok=True)
    a.output_json.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'complete','segments':len(records),'duration':info.duration,'output':str(a.output_json)},ensure_ascii=False))


if __name__=='__main__':main()
