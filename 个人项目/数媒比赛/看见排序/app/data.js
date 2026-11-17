(function (root, factory) {
  'use strict';
  const data = factory();
  root.SortLabData = data;
  if (typeof module === 'object' && module.exports) module.exports = data;
})(typeof globalThis !== 'undefined' ? globalThis : window, function () {
  'use strict';
  const topics = [
    { id: 'sports', label: '运动', color: '#bd4d39', glyph: '↗' },
    { id: 'music', label: '音乐', color: '#7452a3', glyph: '♫' },
    { id: 'tech', label: '科技', color: '#286c9b', glyph: '⌘' },
    { id: 'art', label: '艺术', color: '#a24170', glyph: '◇' },
    { id: 'life', label: '生活', color: '#997225', glyph: '☀' },
    { id: 'nature', label: '自然', color: '#337c62', glyph: '✳' }
  ];
  // All stories and values are original simulated teaching material, not platform data.
  const cards = [
    { id: 'sports-01', title: '校园篮球集锦', summary: '一次传球、一次起跳。你是来看比赛，还是来找视频里的配乐？', topic: 'sports', p: 0.4, f: 0.6 },
    { id: 'sports-02', title: '跑道上的配速游戏', summary: '把一圈拆成四段，用呼吸和节奏找到自己的慢跑速度。', topic: 'sports', p: 0.72, f: 0.42 },
    { id: 'sports-03', title: '飞盘为什么会转弯', summary: '一只飞盘划出弧线，试着观察投掷角度与飞行轨迹。', topic: 'sports', p: 0.36, f: 0.88 },
    { id: 'sports-04', title: '课间五分钟伸展', summary: '从肩颈到脚踝，记录一组温和伸展动作的节奏。', topic: 'sports', p: 0.58, f: 0.38 },
    { id: 'music-01', title: '篮球声也能写成节拍', summary: '把运球、鞋底摩擦与掌声排进一小段校园节奏。', topic: 'music', p: 0.62, f: 0.68 },
    { id: 'music-02', title: '一首歌的四种开场', summary: '同一段旋律先后交给钢琴、吉他、人声和口哨。', topic: 'music', p: 0.78, f: 0.44 },
    { id: 'music-03', title: '给雨声配一条低音', summary: '听窗外雨滴的间隔，用几个低音接住它的起伏。', topic: 'music', p: 0.34, f: 0.82 },
    { id: 'music-04', title: '校园声音采集册', summary: '翻页、脚步、关门声：想象一张属于校园的声音地图。', topic: 'music', p: 0.46, f: 0.56 },
    { id: 'tech-01', title: '纸桥承重小实验', summary: '同一张纸，折成不同截面。什么结构能托住更多积木？', topic: 'tech', p: 0.8, f: 0.8 },
    { id: 'tech-02', title: '像素里的小秘密', summary: '放大一幅图，看看有限的小方格怎样拼成连续的色彩。', topic: 'tech', p: 0.66, f: 0.52 },
    { id: 'tech-03', title: '给闹钟设计一个按钮', summary: '画出三种按钮方案，比较误触、触达与反馈。', topic: 'tech', p: 0.28, f: 0.92 },
    { id: 'tech-04', title: '路口信号的等待时间', summary: '用简化时间线观察：改变一个时段，哪些等待会变化？', topic: 'tech', p: 0.54, f: 0.34 },
    { id: 'art-01', title: '用一条线画完校园', summary: '不抬笔走过食堂、图书馆与操场，把路线变成线稿。', topic: 'art', p: 0.56, f: 0.74 },
    { id: 'art-02', title: '海报留白的两种节奏', summary: '把同一组文字放在两种版式里，观察视线先落在哪里。', topic: 'art', p: 0.68, f: 0.46 },
    { id: 'art-03', title: '影子做的一分钟短剧', summary: '台灯、纸片和一双手，让几何形状成为舞台角色。', topic: 'art', p: 0.32, f: 0.86 },
    { id: 'art-04', title: '三种颜色的一张地图', summary: '限制调色盘，只用三种颜色标出校园里的安静角落。', topic: 'art', p: 0.44, f: 0.4 },
    { id: 'life-01', title: '旧玻璃瓶的新位置', summary: '从收纳到插花，同一个旧瓶子有几种继续使用的方法？', topic: 'life', p: 0.64, f: 0.7 },
    { id: 'life-02', title: '十分钟整理书桌', summary: '先决定常用物品的落点，再比较整理前后的取用路线。', topic: 'life', p: 0.74, f: 0.4 },
    { id: 'life-03', title: '给今天留一张便签', summary: '写下一个小发现，试着把抽象感受说成具体的一件事。', topic: 'life', p: 0.38, f: 0.9 },
    { id: 'life-04', title: '一份早餐的色彩表', summary: '给一份虚构早餐画色卡，练习用简洁图形记录日常。', topic: 'life', p: 0.52, f: 0.36 },
    { id: 'nature-01', title: '操场边的树叶档案', summary: '比较四片落叶的轮廓、叶脉和触感，画出观察记录。', topic: 'nature', p: 0.6, f: 0.76 },
    { id: 'nature-02', title: '云影移动的一小时', summary: '用一组虚构观察画面，想象云和影子如何走过建筑。', topic: 'nature', p: 0.7, f: 0.48 },
    { id: 'nature-03', title: '小水洼的倒影实验', summary: '改变观察位置，比较同一处水面的倒影与反光。', topic: 'nature', p: 0.3, f: 0.94 },
    { id: 'nature-04', title: '夜晚的声音清单', summary: '把风、虫鸣和远处脚步分层，试着描绘一个安静夜晚。', topic: 'nature', p: 0.42, f: 0.54 }
  ];
  topics.forEach(Object.freeze);
  cards.forEach(Object.freeze);
  return Object.freeze({ version: '1.0.0', simulated: true, topics: Object.freeze(topics), cards: Object.freeze(cards) });
});
