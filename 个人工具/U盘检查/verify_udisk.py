# -*- coding: utf-8 -*-
# 严格验证：读取 U 盘多个偏移的 512 字节，逐一比对是否完全相同
# 若全部相同 → 主控固件故障，返回的是固定"假"数据而非真实闪存内容
import os, hashlib

DEV = r'\\.\F:'
SIZE_GB = 7.5
N = 24  # 采样点数
SIZE = int(SIZE_GB * 1024**3)
SECTOR = 512

fd = os.open(DEV, os.O_RDONLY | os.O_BINARY)
hashes = []
results = []
for i in range(N):
    off = int(i * (SIZE - SECTOR) / (N - 1))
    off = (off // SECTOR) * SECTOR  # 对齐到 512
    try:
        os.lseek(fd, off, os.SEEK_SET)
        buf = os.read(fd, SECTOR)
        h = hashlib.md5(buf).hexdigest()[:10]
        hashes.append(h)
        results.append((off, h, buf[:8].hex()))
    except Exception as e:
        results.append((off, 'READ_ERROR', str(e)[:30]))
os.close(fd)

print('采样 %d 个位置（覆盖 %.1f GB）：' % (N, SIZE_GB))
for off, h, head in results:
    print('  偏移 %10.1f MB : hash=%s  head=%s' % (off / (1024**2), h, head))

uniq = len(set(h for _, h, _ in results))
print()
print('不同内容块数: %d / %d' % (uniq, N))
if uniq == 1:
    print('>>> 结论：所有扇区返回完全相同的内容 —— 主控固件故障')
    print('>>> 读到的不是真实数据，而是控制器返回的固定固件信息')
elif uniq < N * 0.2:
    print('>>> 结论：大面积重复 —— 疑似主控故障或严重损坏')
else:
    print('>>> 结论：内容各异，数据是真实的，可用恢复软件找回')
