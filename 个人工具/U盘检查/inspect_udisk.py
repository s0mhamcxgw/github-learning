# -*- coding: utf-8 -*-
# 只读取样：查看 U 盘多个偏移处的数据内容，判断数据性质（文本/二进制/加密/垃圾）
import os, string

DEV = r'\\.\F:'
OFFSETS_MB = [0, 1, 10, 50, 100, 150, 200, 250]
READ = 2048

PRINTABLE = set(bytes(string.printable, 'ascii'))

def analyze(buf):
    total = len(buf)
    printable = sum(1 for b in buf if b in PRINTABLE or b in (9, 10, 13))
    # 尝试按 UTF-8 / GBK 解码统计中文/可读性
    txt = ''
    for enc in ('utf-8', 'gbk', 'utf-16-le', 'latin-1'):
        try:
            t = buf.decode(enc, errors='strict')
            txt = t
            enc_used = enc
            break
        except Exception:
            enc_used = None
    return printable / total if total else 0, enc_used, txt

fd = os.open(DEV, os.O_RDONLY | os.O_BINARY)
for mb in OFFSETS_MB:
    off = mb * 1024 * 1024
    try:
        os.lseek(fd, off, os.SEEK_SET)
        buf = os.read(fd, READ)
    except Exception as e:
        print('\n[偏移 %d MB] 读取失败: %s' % (mb, e))
        continue
    ratio, enc, txt = analyze(buf)
    print('\n========== 偏移 %d MB (0x%X) ==========' % (mb, off))
    print('  可打印字符占比: %.0f%%' % (ratio * 100))
    print('  首个256字节HEX: %s' % buf[:256].hex(' '))
    if enc:
        print('  可按 %s 解码，预览:' % enc)
        # 只显示可读片段
        preview = ''.join(ch if (ch.isprintable() or ch in '\n\t') else ' ' for ch in txt)
        print('  >>>', preview[:200].replace('\n', ' | '))
    else:
        print('  无法按常见编码解码（二进制/加密/压缩）')
os.close(fd)
