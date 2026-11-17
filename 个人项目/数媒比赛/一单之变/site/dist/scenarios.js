(function (root, factory) {
  const scenarios = factory();
  if (typeof module === 'object' && module.exports) module.exports = scenarios;
  else root.PromiseScenarios = scenarios;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const resources = device => [
    {id: 'maker', label: '主制作人', capacity: 1, calendar: 'work'},
    {id: 'helper', label: '假设可用的协作者', capacity: 1, calendar: 'work'},
    device
  ];
  return [
    {
      id: 'ceramic', name: '青禾陶艺工作室', category: '连续工时冲突', days: 3, slotMinutes: 30,
      summary: '三小时拉坯无法拆开做。即使总工时看似够用，也可能没有一段能兑现承诺的连续时间。',
      source: '本作品原创合成案例；不是实际商家、访谈或生产数据。',
      resources: resources({id: 'kiln', label: '恒温定型设备', capacity: 1, calendar: 'always'}),
      orders: [
        {id: 'cup', label: '青釉杯 · 已承诺', due: 6, release: 0, isNew: false, color: '#347465'},
        {id: 'plate', label: '小食碟 · 已承诺', due: 16, release: 0, isNew: false, color: '#738da2'},
        {id: 'incense', label: '定制香插 · 待接新单', due: 14, release: 0, isNew: true, color: '#c86e43'}
      ],
      tasks: [
        {id: 'cup-form', order: 'cup', label: '青釉杯成型', duration: 4, needs: {maker: 1}, after: []},
        {id: 'cup-set', order: 'cup', label: '青釉杯定型', duration: 2, needs: {kiln: 1}, after: ['cup-form']},
        {id: 'plate-form', order: 'plate', label: '小食碟成型', duration: 2, needs: {maker: 1}, after: []},
        {id: 'plate-set', order: 'plate', label: '小食碟定型', duration: 2, needs: {kiln: 1}, after: ['plate-form']},
        {id: 'incense-form', order: 'incense', label: '香插连续成型', duration: 6, needs: {maker: 1}, after: [], delegate: true},
        {id: 'incense-set', order: 'incense', label: '香插定型', duration: 2, needs: {kiln: 1}, after: ['incense-form']}
      ],
      note: '这是工序约束的教学性抽象；“定型设备”时长不是陶瓷烧制工艺参数，不可作为生产工艺指导。'
    },
    {
      id: 'print', name: '两色丝印小队', category: '共享设备瓶颈', days: 3, slotMinutes: 30,
      summary: '多一名协作者也不一定能多接一单：只有一台印台时，设备占用仍然互斥。',
      source: '本作品原创合成案例；不是实际商家、访谈或生产数据。',
      resources: resources({id: 'press', label: '共享印台', capacity: 1, calendar: 'work'}),
      orders: [
        {id: 'poster', label: '活动海报 · 已承诺', due: 6, release: 0, isNew: false, color: '#347465'},
        {id: 'bag', label: '帆布袋 · 已承诺', due: 16, release: 0, isNew: false, color: '#738da2'},
        {id: 'card', label: '纪念卡 · 待接新单', due: 6, release: 0, isNew: true, color: '#c86e43'}
      ],
      tasks: [
        {id: 'poster-prep', order: 'poster', label: '海报制版', duration: 1, needs: {maker: 1}, after: []},
        {id: 'poster-print', order: 'poster', label: '海报印制', duration: 4, needs: {maker: 1, press: 1}, after: ['poster-prep']},
        {id: 'bag-print', order: 'bag', label: '帆布袋印制', duration: 3, needs: {maker: 1, press: 1}, after: []},
        {id: 'card-prep', order: 'card', label: '纪念卡制版', duration: 1, needs: {maker: 1}, after: [], delegate: true},
        {id: 'card-print', order: 'card', label: '纪念卡印制', duration: 4, needs: {maker: 1, press: 1}, after: ['card-prep'], delegate: true}
      ],
      note: '协作方案仅替换允许委派的人工占用，仍使用原有印台；不会假设协作者自带另一台设备。'
    },
    {
      id: 'leather', name: '拾光皮具工坊', category: '工时扰动与承诺余量', days: 3, slotMinutes: 30,
      summary: '按估计工时可以完成，不代表遇到返工或材料晚到后仍能完成。用明确的扰动检查承诺余量。',
      source: '本作品原创合成案例；不是实际商家、访谈或生产数据。',
      resources: resources({id: 'rack', label: '独立固化架位', capacity: 1, calendar: 'always'}),
      orders: [
        {id: 'wallet', label: '短夹 · 已承诺', due: 16, release: 0, isNew: false, color: '#347465'},
        {id: 'belt', label: '腰带 · 已承诺', due: 54, release: 0, isNew: false, color: '#738da2'},
        {id: 'tag', label: '礼物铭牌 · 待接新单', due: 16, release: 0, isNew: true, color: '#c86e43'}
      ],
      tasks: [
        {id: 'wallet-cut', order: 'wallet', label: '短夹裁片', duration: 2, needs: {maker: 1}, after: []},
        {id: 'wallet-stitch', order: 'wallet', label: '短夹缝制', duration: 2, needs: {maker: 1}, after: ['wallet-cut']},
        {id: 'belt-prep', order: 'belt', label: '腰带涂饰', duration: 2, needs: {maker: 1}, after: []},
        {id: 'belt-dry', order: 'belt', label: '腰带静置固化', duration: 8, needs: {rack: 1}, after: ['belt-prep']},
        {id: 'belt-pack', order: 'belt', label: '腰带整理', duration: 1, needs: {maker: 1}, after: ['belt-dry']},
        {id: 'tag-cut', order: 'tag', label: '铭牌裁片', duration: 2, needs: {maker: 1}, after: [], delegate: true},
        {id: 'tag-finish', order: 'tag', label: '铭牌装饰', duration: 2, needs: {maker: 1}, after: ['tag-cut'], delegate: true}
      ],
      note: '固化工序只占架位，人工可以并行处理其他订单。工时为合成模型值，不是工艺标准。'
    }
  ];
});
