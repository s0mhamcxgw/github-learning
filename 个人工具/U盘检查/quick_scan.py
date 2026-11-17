# -*- coding: utf-8 -*-
# 快速只读采样：扫前 256MB，确认 U 盘上是否还有数据（严格只读）
import os, collections

DEV = r'\\.\F:'
LIMIT = 256 * 1024 * 1024
CHUNK = 1024 * 1024

SIGS = [
    (b'\xFF\xD8\xFF', 'JPEG图片'), (b'\x89PNG', 'PNG图片'),
    (b'%PDF', 'PDF'), (b'PK\x03\x04', 'ZIP/Office(docx/xlsx/pptx)'),
    (b'\xD0\xCF\x11\xE0', '旧版Office(doc/xls/ppt)'), (b'GIF8', 'GIF'),
    (b'Rar!', 'RAR'), (b'7z\xBC\xAF', '7Z'), (b'\x1F\x8B', 'GZIP'),
    (b'RIFF', 'WAV/AVI'), (b'BM', 'BMP'),
]

try:
    fd = os.open(DEV, os.O_RDONLY | os.O_BINARY)
except Exception as e:
    print('打开失败: %s（可能需要管理员权限）' % e); raise SystemExit(1)

counts = collections.Counter()
nonzero = zero = 0
read = 0
while read < LIMIT:
    try:
        data = os.read(fd, CHUNK)
    except Exception as e:
        print('读取中断于 %.0f MB: %s' % (read / (1024**2), e)); break
    if not data:
        break
    read += len(data)
    sample = data[:4096]
    if any(sample):
        nonzero += 1
        for sig, name in SIGS:
            if sig in sample:
                counts[name] += 1
    else:
        zero += 1
os.close(fd)
print('设备: %s（容量约 7.5GB）' % DEV)
print('已扫描前 %.0f MB' % (read / (1024**2)))
print('含数据的块: %d | 全零块: %d' % (nonzero, zero))
if nonzero + zero:
    print('数据占比: %.1f%%' % (100.0 * nonzero / (nonzero + zero)))
print('--- 检测到的文件签名 ---')
if counts:
    for n, c in counts.most_common():
        print('  %s: %d 处' % (n, c))
else:
    print('  未检测到已知签名（纯文本笔记 txt/md 无固定签名，不代表不存在）')
