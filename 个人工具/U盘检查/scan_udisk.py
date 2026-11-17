# -*- coding: utf-8 -*-
"""
U盘只读扫描：确认数据是否仍在盘上，并统计常见文件类型的残留签名。
严格只读：只 Open 为 Read，绝不写入任何字节。
"""
import sys, os, collections

DEV = r'\\.\F:'
TOTAL = None
CHUNK = 1024 * 1024  # 1MB
SAMPLE = 4096        # 每个 1MB 采样 4KB

SIGS = [
    (b'\xFF\xD8\xFF',            'JPEG图片'),
    (b'\x89PNG\r\n\x1a\n',       'PNG图片'),
    (b'%PDF',                    'PDF文档'),
    (b'PK\x03\x04',              'ZIP/Office(docx,xlsx,pptx)'),
    (b'PK\x05\x06',              'ZIP尾(目录结束)'),
    (b'\xD0\xCF\x11\xE0',        '旧版Office(doc,xls,ppt)'),
    (b'GIF8',                    'GIF图片'),
    (b'RIFF',                    'WAV/AVI'),
    (b'\x00\x00\x01\x00',        'ICO图标'),
    (b'BM',                      'BMP图片'),
    (b'<?xml',                   'XML'),
    (b'{\\rtf',                  'RTF文档'),
    (b'\x1F\x8B',                'GZIP压缩包'),
    (b'Rar!',                    'RAR压缩包'),
    (b'7z\xBC\xAF',              '7Z压缩包'),
    (b'fts',                     'SQLite/其他'),
]

def main():
    try:
        f = open(DEV, 'rb')
    except Exception as e:
        print('无法打开设备 %s: %s' % (DEV, e))
        print('提示：可能需要以管理员身份运行')
        return 1

    # 获取总大小
    try:
        f.seek(0, os.SEEK_END)
        total = f.tell()
        f.seek(0)
    except Exception:
        total = 0
    print('设备: %s' % DEV)
    print('总大小: %.2f GB (%d 字节)' % (total / (1024**3), total) if total else '总大小: 未知')

    counts = collections.Counter()
    nonzero_blocks = 0
    zero_blocks = 0
    scanned = 0
    pos = 0

    try:
        while True:
            data = f.read(CHUNK)
            if not data:
                break
            scanned += len(data)
            # 采样判断非零
            sample = data[:SAMPLE]
            if any(sample):
                nonzero_blocks += 1
                for sig, name in SIGS:
                    if sig in sample:
                        counts[name] += 1
            else:
                zero_blocks += 1
            pos += len(data)
            # 每 512MB 报一次进度
            if pos % (512 * 1024 * 1024) < CHUNK:
                print('  已扫描 %.2f GB ...' % (pos / (1024**3)))
    except Exception as e:
        print('读取中断: %s' % e)

    f.close()
    print()
    print('扫描完成: %.2f GB' % (scanned / (1024**3)))
    print('有数据的 1MB 块: %d' % nonzero_blocks)
    print('全零的 1MB 块:   %d' % zero_blocks)
    if nonzero_blocks + zero_blocks > 0:
        ratio = 100.0 * nonzero_blocks / (nonzero_blocks + zero_blocks)
        print('数据占比: %.1f%%' % ratio)
    print()
    print('=== 检测到的文件签名（每 1MB 采样一次，仅作存在性参考）===')
    if counts:
        for name, c in counts.most_common():
            print('  %-28s %d 处' % (name, c))
    else:
        print('  未检测到已知文件签名')
    return 0

if __name__ == '__main__':
    sys.exit(main())
