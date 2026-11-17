(function () {
  'use strict';
  const E = window.PromiseLab, examples = window.PromiseScenarios;
  const $ = selector => document.querySelector(selector);
  const e = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const palette = ['#347465', '#738da2', '#c86e43', '#9a8961', '#8d79a3', '#67979a'];
  const state = {scenario: E.clone(examples[0]), analysis: null, view: 'overview', includeNew: false, day: 0, selectedPlan: '', filter: 'frontier', focusedTask: '', stress: null, stressDetail: '', tourIndex: 0, tourRunning: false, tourPaused: false};
  const sections = [['overview', '承诺总览', '▦'], ['lab', '接单推演', '⇄'], ['compare', '方案比较', '◈'], ['stress', '压力测试', '⌁'], ['edit', '约束编辑', '☷'], ['report', '推演报告', '▤']];
  const statuses = {feasible: '找到可行排程', infeasible: '已证明不可行', unknown: '尚不能判定', invalid: '输入待修正'};
  let toastTimer, tourTimer;
  const hours = slots => Number((slots / 2).toFixed(1));
  const badge = result => '<span class="status ' + e(result?.status || 'neutral') + '">' + e(statuses[result?.status] || '待推演') + '</span>';
  const color = (s, order) => s.orders.find(o => o.id === order)?.isNew ? '#c86e43' : palette[Math.max(0, s.orders.filter(o => !o.isNew).findIndex(o => o.id === order)) % palette.length];
  const plan = () => state.analysis.plans.find(p => p.id === state.selectedPlan);
  const incomingOrder = () => state.scenario.orders.find(o => o.isNew);
  function notify(text) { const node = $('#toast'); node.textContent = text; node.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { node.hidden = true; }, 3500); }
  function calculate() {
    state.analysis = E.analyze(state.scenario); state.stress = null; state.stressDetail = ''; state.focusedTask = '';
    state.day = Math.min(state.day, state.scenario.days - 1);
    const preferred = state.analysis.plans.find(p => p.id === 'd1-l0-c0' && p.result.status === 'feasible');
    state.selectedPlan = (preferred || state.analysis.plans.find(p => p.frontier) || state.analysis.plans[0])?.id || '';
  }
  function setScenario(id) { const item = examples.find(s => s.id === id); if (!item) return; state.scenario = E.clone(item); state.includeNew = false; state.day = 0; calculate(); render(); }
  function navigate(view) { if (!sections.some(v => v[0] === view)) return; state.view = view; state.focusedTask = ''; if (view === 'stress') ensureStress(); render(); window.scrollTo({top: 0, behavior: state.tourRunning ? 'instant' : 'auto'}); }
  function heading(eyebrow, title, copy, action = '') { return '<div class="page-heading"><div><div class="eyebrow">' + e(eyebrow) + '</div><h1>' + title + '</h1><p class="subcopy">' + e(copy) + '</p></div>' + action + '</div>'; }
  function scenarioStrip() {
    return '<div class="scenario-strip"><div><span class="scenario-label">当前工作室</span><select id="scenario-select" aria-label="选择合成场景" data-action="scenario">' + examples.map(s => '<option value="' + s.id + '"' + (s.id === state.scenario.id ? ' selected' : '') + '>' + e(s.name) + '</option>').join('') + (!examples.some(s => s.id === state.scenario.id) ? '<option value="custom" selected>' + e(state.scenario.name) + '</option>' : '') + '</select></div><span class="scenario-note">' + e(state.scenario.category || '自定义约束') + ' · ' + state.scenario.days + ' 天推演窗口</span><button class="link-button" data-action="set-view" data-view="edit">查看约束 ↗</button></div>';
  }
  function statistics() {
    const s = state.scenario, a = state.analysis, maker = s.tasks.filter(t => t.needs.maker).reduce((v, t) => v + t.duration * t.needs.maker, 0);
    const cards = [
      ['既有承诺', s.orders.filter(o => !o.isNew).length, '张', a.baseline.status === 'feasible' ? '已核对基线排程' : '基线本身需重新核实'],
      ['待接新单', s.orders.filter(o => o.isNew).length, '张', '交期：' + E.formatTime(incomingOrder().due)],
      ['人工总需求', hours(maker), '小时', '含新单；不含无人值守时段'],
      ['取舍候选', a.plans.filter(p => p.frontier).length, '项', '已检查候选中的非支配方案']
    ];
    return '<div class="stats">' + cards.map((c, i) => '<div class="stat"><div class="stat-label">' + e(c[0]) + '<span class="light">0' + (i + 1) + '</span></div><div class="stat-value">' + c[1] + '<small>' + c[2] + '</small></div><div class="stat-note">' + e(c[3]) + '</div></div>').join('') + '</div>';
  }
  function orderBriefs() { return '<div class="order-briefs">' + state.scenario.orders.map(o => '<div class="order-brief"><div class="order-left"><i class="order-swatch" style="background:' + color(state.scenario, o.id) + '"></i><div>' + e(o.label) + '<small>' + state.scenario.tasks.filter(t => t.order === o.id).length + ' 道工序 · ' + (o.isNew ? '尚未接受' : '既有承诺') + '</small></div></div><div>' + e(E.formatTime(o.due)) + '<small>承诺完成时间</small></div></div>').join('') + '</div>'; }
  function proofPanel(result, compact = false) {
    const a = state.analysis, s = state.scenario;
    let text, headline;
    if (result.status === 'feasible') { headline = '当前条件下，<em style="color:var(--green)">可以兑现。</em>'; text = '找到满足已建模约束的排程。工时与资源假设仍可能变化，建议继续检查扰动后的可行性。'; }
    else if (result.status === 'infeasible') { headline = '这一单，<em>先别急着答应。</em>'; text = '当前承诺在模型中不能全部同时满足。先看冲突来自哪里，再决定修改哪一个条件。'; }
    else { headline = '先补足证据，<em>再作承诺。</em>'; text = '尚无足够结果支持接单或拒单。搜索超限不代表不可行，输入错误也不属于排程结论。'; }
    const conflict = result === a.incoming ? a.conflict : null;
    return '<div class="eyebrow">' + (state.includeNew ? '接入新单后的判断' : '承诺边界') + '</div>' + badge(result) + '<h2 class="conflict-title">' + headline + '</h2><p class="body-copy">' + text + '</p><div class="proof-box ' + (result.status === 'feasible' ? 'green' : '') + '">' + e(result.proof?.summary || result.errors?.join('；')) + '</div>' + (conflict ? '<div class="eyebrow">' + (conflict.minimal ? '极小冲突集 / 非唯一' : '已确认冲突集') + '</div><div class="core-orders">' + conflict.orders.map(id => '<span class="core-chip">' + e(s.orders.find(o => o.id === id).label) + '</span>').join('') + '</div><p class="timeline-note">' + e(conflict.summary) + '</p>' : '') + (!compact ? '<hr class="divider"><button class="link-button" data-action="set-view" data-view="compare">看看可以改变哪些条件 <span>→</span></button>' : '');
  }
  function timeline(scenario, result, proposal = false, title = '订单时间纸带') {
    const day = state.day, start = day * 48, end = start + 18, s = scenario;
    let schedule = result.schedule || [];
    if (proposal) {
      const incoming = s.orders.find(o => o.isNew), alone = E.solve(s, {orderIds: [incoming.id]});
      schedule = [...schedule, ...alone.schedule.map(t => ({...t, proposal: true}))];
    }
    const orderIds = new Set(schedule.map(x => s.tasks.find(t => t.id === x.task)?.order));
    const rows = s.orders.filter(o => orderIds.has(o.id)).map(o => {
      const tasks = schedule.filter(x => s.tasks.find(t => t.id === x.task).order === o.id);
      const blocks = tasks.filter(x => x.start < end && x.end > start).map(x => {
        const t = s.tasks.find(t => t.id === x.task), left = Math.max(0, x.start - start) / 18 * 100, width = (Math.min(x.end, end) - Math.max(x.start, start)) / 18 * 100;
        return '<button class="task-block ' + (x.proposal ? 'proposal' : '') + '" data-action="task" data-task="' + e(t.id) + '" style="left:' + left + '%;width:' + width + '%;background:' + color(s, o.id) + '" title="' + e(t.label + ' · ' + E.formatTime(x.start) + ' 至 ' + E.formatTime(x.end) + (x.proposal ? '，新单单独排程，未合并' : '')) + '">' + e(t.label) + '</button>';
      }).join('');
      const duePosition = (o.due - start) / 18 * 100;
      return '<div class="timeline-row"><div class="row-label">' + e(o.label.split(' · ')[0]) + '<small>' + (o.isNew && proposal ? '单独排程 · 未接受' : e(E.formatTime(o.due))) + '</small></div><div class="track">' + (!s.openLunch ? '<div class="lunch-band" title="12:00-14:00 人工休息时段"></div>' : '') + blocks + (duePosition >= 0 && duePosition <= 100 ? '<i class="due-marker" style="left:' + duePosition + '%" title="承诺交期"></i>' : '') + '</div></div>';
    }).join('');
    const scale = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18].map((h, i) => '<span class="tick" style="left:' + i / 9 * 100 + '%">' + String(h).padStart(2, '0') + '</span>').join('');
    let detail = '';
    if (state.focusedTask) {
      const task = s.tasks.find(t => t.id === state.focusedTask), run = schedule.find(t => t.task === state.focusedTask);
      if (task) detail = '<div class="task-detail"><h3>' + e(task.label) + '</h3><div class="kv"><span>连续占用</span><span>' + hours(task.duration) + ' 小时 · 不可中断</span></div><div class="kv"><span>所需资源</span><span>' + e(Object.entries(task.needs).map(([id, units]) => s.resources.find(r => r.id === id).label + ' ×' + units).join('，')) + '</span></div><div class="kv"><span>前置工序</span><span>' + e(task.after.map(id => s.tasks.find(t => t.id === id).label).join('、') || '无') + '</span></div>' + (run ? '<div class="kv"><span>本次安排</span><span>' + e(E.formatTime(run.start) + ' → ' + E.formatTime(run.end)) + '</span></div>' : '') + '</div>';
    }
    return '<div class="panel"><div class="panel-heading"><div><h2>' + e(title) + '</h2><p>点选工序，查看占用、依赖与起止。</p></div><div class="day-tabs" role="group" aria-label="查看日期">' + Array.from({length: s.days}, (_, i) => '<button class="day-tab ' + (i === day ? 'active' : '') + '" data-action="day" data-day="' + i + '">第' + (i + 1) + '天</button>').join('') + '</div></div><div class="timeline-wrap"><div class="timeline"><div class="time-scale">' + scale + '</div>' + (rows || '<div class="empty">此日没有排程工序。</div>') + '</div></div><div class="legend"><span><i style="background:#347465"></i>既有订单</span><span><i style="background:#c86e43"></i>待接新单</span><span><i style="background:#edf0e8"></i>人工休息</span><span>┆ 承诺交期</span></div><p class="timeline-note">当前展示当天 09:00—18:00；跨夜工序的完整起止可点选查看。无人值守设备可在人工休息时运行。' + (proposal ? '<strong> 橙色虚线是新单单独安排，与基线并列展示，不能当作已合并的可行排程。</strong>' : '') + '</p>' + detail + '</div>';
  }
  function caseCards() { return '<div class="section-label"><h2>三个场景，三种承诺难题</h2><span class="eyebrow">原创合成案例</span></div><div class="case-grid">' + examples.map((s, i) => '<button class="case-card ' + (state.scenario.id === s.id ? 'active' : '') + '" data-action="case" data-id="' + s.id + '"><span class="case-index">CASE 0' + (i + 1) + '</span><h3>' + e(s.category) + '</h3><p>' + e(s.summary) + '</p><div class="case-foot"><span>' + e(s.name) + '</span><span>进入推演 ↗</span></div></button>').join('') + '</div>'; }
  function overview() {
    const a = state.analysis, totalFeasible = a.plans.filter(p => p.result.status === 'feasible').length;
    return '<div class="hero"><div class="hero-copy"><div class="eyebrow">THE PROMISE BEFORE THE ORDER</div><h1>接下一单之前，<br>先看见<span>承诺的边界。</span></h1><p>一张加急单，改变的不只是自己的安排。<br>把工序、资源与交期放在同一张时间纸带上，找到可以解释、也可以兑现的选择。</p><div class="hero-buttons"><button class="button dark" data-action="start-lab">开始接单推演 <span>↗</span></button><button class="button quiet" data-action="tour">▷ 看一次完整演示</button></div></div><div class="promise-card"><div class="promise-top"><span>本次条件检查</span><span>↗</span></div><div class="promise-number">' + a.plans.filter(p => p.frontier).length + '<small>种取舍方向</small></div><p>推迟新单、开放午间，或引入协作。先看每种选择实际改变了什么，再决定要承诺什么。</p><div class="promise-bottom"><span>' + a.plans.length + ' 组条件已推演</span><span>' + totalFeasible + ' 组找到可行安排</span></div></div></div>' + scenarioStrip() + statistics() + '<div class="grid-main">' + timeline(state.scenario, a.baseline, false, '先看已经答应的订单') + '<div class="panel">' + proofPanel(a.incoming, true) + '<hr class="divider"><button class="link-button" data-action="start-lab">加入新单，看清连锁变化 <span>→</span></button></div></div>' + caseCards();
  }
  function lab() {
    const s = state.scenario, a = state.analysis, result = state.includeNew ? a.incoming : a.baseline;
    return heading('01 / ORDER IMPACT', '这一单，会改变什么？', '既有承诺先保持不变。只加入一张新单，核对它是否能与原有安排同时成立。') + scenarioStrip() + '<div class="toggle-row"><div><strong>' + e(incomingOrder().label) + '</strong><small>要求 ' + e(E.formatTime(incomingOrder().due)) + ' 前完成；切换后实际重新展示对应结果。</small></div><button class="switch ' + (state.includeNew ? 'on' : '') + '" data-action="toggle-incoming" role="switch" aria-checked="' + state.includeNew + '" aria-label="把待接新单加入推演"></button></div><div class="grid-main">' + timeline(s, result.status === 'feasible' ? result : a.baseline, state.includeNew && result.status !== 'feasible') + '<div class="panel">' + proofPanel(result) + '</div></div><div class="section-spacer panel"><div class="panel-heading"><div><h2>本次推演的订单与承诺</h2><p>时间均为模型中的相对日期，与现实今天无关。</p></div><span class="tag">工序不可拆分</span></div>' + orderBriefs() + '<p class="timeline-note">' + e(s.note || '自定义模型：请核实输入与实际工序是否一致。') + '</p></div>';
  }
  function planName(p) { const bits = []; if (p.options.delayDays) bits.push('新单交期 +' + p.options.delayDays + ' 天'); if (p.options.openLunch) bits.push('开放午间'); if (p.options.collaborate) bits.push('引入协作'); return bits.join(' ＋ ') || '保持当前承诺'; }
  function planNote(p) { return '新单交期 ' + E.formatTime(p.scenario.orders.find(o => o.isNew).due) + '。' + (p.options.collaborate ? '只转移允许委派的人工，原设备不增加。' : '由主制作人完成。') + (p.options.openLunch ? '假设午间工作时段可用。' : '保留午间休息。'); }
  function plot() {
    const items = state.analysis.plans.filter(p => p.frontier), maxX = Math.max(1, ...items.map(p => p.metrics.delay / 48)), maxY = Math.max(1, ...items.map(p => hours(p.metrics.extra)));
    return '<svg class="plot" viewBox="0 0 450 220" role="img" aria-label="候选非支配方案：横轴新单推迟天数，纵轴午间人工占用，圆点大小提示协作工时"><path d="M55 20V175H425" fill="none" stroke="#cbd4c2"/><path d="M55 98H425M240 20V175" stroke="#e7ecdf" stroke-dasharray="4 4"/>' + [0, 1, 2].map(i => '<text x="' + (55 + i * 185) + '" y="196" text-anchor="middle">' + (maxX * i / 2).toFixed(1) + '天</text>').join('') + '<text x="12" y="24">' + maxY + 'h</text><text x="22" y="178">0</text><text x="55" y="12">午间人工占用</text><text x="329" y="216">新单交期推迟 →</text>' + items.map((p, i) => {
      const x = 55 + p.metrics.delay / 48 / maxX * 370, y = 175 - hours(p.metrics.extra) / maxY * 150, radius = 7 + Math.min(9, hours(p.metrics.helper) * 2);
      return '<g class="point" data-action="plan" data-id="' + p.id + '" tabindex="0" role="button" aria-label="查看' + e(planName(p)) + '"><circle cx="' + x + '" cy="' + y + '" r="' + radius + '" fill="' + (p.id === state.selectedPlan ? '#c86e43' : '#50816b') + '" stroke="#fff" stroke-width="2"/><text x="' + (x + 13) + '" y="' + (y - 11) + '">P' + String(state.analysis.plans.indexOf(p) + 1).padStart(2, '0') + '</text><title>' + e(planName(p) + '，协作 ' + hours(p.metrics.helper) + ' 小时') + '</title></g>';
    }).join('') + '</svg>';
  }
  function compare() {
    const a = state.analysis, chosen = plan(), visible = state.filter === 'all' ? a.plans : a.plans.filter(p => p.frontier);
    return heading('02 / CHOICES WITH CONSEQUENCES', '把选择，和它的代价放在一起。', '在已生成的条件组合中比较交期推迟、午间人工和协作占用。非支配不等于唯一最佳，也不代表穷尽所有方案。') + scenarioStrip() + '<div class="compare-summary"><div class="panel"><div class="panel-heading"><div><h2>可见的取舍</h2><p>点越大，协作占用越多；所有数值来自可行排程。</p></div><span class="tag">候选非支配</span></div>' + plot() + '</div><div class="panel"><div class="eyebrow">本次比较范围</div><h2>' + a.plans.length + ' 组条件，逐一核对。</h2><p class="body-copy" style="margin-top:14px">仅改变新单交期、午间时段和允许委派的人工，保留既有订单交期与设备容量。资源是否真的可用，需要在现实接单前确认。</p><div class="callout">工时来自找到的可行排程，不是最小工时保证。“非支配”仅针对这些候选排程的三项指标；不宣称全局帕累托最优。</div></div></div><div class="filters"><button class="filter ' + (state.filter === 'frontier' ? 'active' : '') + '" data-action="filter" data-filter="frontier">取舍候选 ' + a.plans.filter(p => p.frontier).length + '</button><button class="filter ' + (state.filter === 'all' ? 'active' : '') + '" data-action="filter" data-filter="all">全部条件 ' + a.plans.length + '</button></div><div class="plan-list">' + (visible.length ? visible.map(p => '<button class="plan-card ' + (p.id === state.selectedPlan ? 'selected' : '') + '" data-action="plan" data-id="' + p.id + '"><div class="plan-top"><span class="plan-index">P' + String(a.plans.indexOf(p) + 1).padStart(2, '0') + '</span>' + badge(p.result) + '</div><h3>' + e(planName(p)) + '</h3>' + (p.metrics ? '<div class="plan-metrics"><div><span>' + p.metrics.delay / 48 + '<small>新单推迟 / 天</small></span></div><div><span>' + hours(p.metrics.extra) + '<small>午间人工 / 小时</small></span></div><div><span>' + hours(p.metrics.helper) + '<small>协作占用 / 小时</small></span></div></div>' : '<p style="margin:16px 0">' + e(p.result.proof?.summary) + '</p>') + '<p>' + e(planNote(p)) + '</p></button>').join('') : '<div class="empty">这些条件中尚无可比较的可行方案。请查看全部结果或修改约束。</div>') + '</div>' + (chosen ? '<div class="section-label"><h2>正在查看：' + e(planName(chosen)) + '</h2><button class="link-button" data-action="set-view" data-view="stress">对这个方案做压力测试 →</button></div>' + (chosen.result.status === 'feasible' ? timeline(chosen.scenario, chosen.result, false, '调整后的真实排程') : '<div class="panel">' + badge(chosen.result) + '<p class="body-copy" style="margin-top:12px">' + e(chosen.result.proof?.summary) + '</p></div>') : '');
  }
  function ensureStress() { if (!state.stress) state.stress = E.stress(plan()?.scenario || state.scenario); }
  function stressView() {
    ensureStress(); const r = state.stress, chosen = plan(), detail = r.items.find(i => i.id === state.stressDetail);
    return heading('03 / STRESS THE PROMISE', '能排进去，还能承受变化吗？', '对指定方案施加明确扰动并重新排程。通过数量只描述这些合成检查，不是现实准时率或风险概率。') + scenarioStrip() + '<div class="panel"><div class="panel-heading"><div><h2>当前检查条件</h2><p>每次检查均保留交期，重新寻找可行安排。</p></div><select class="form-select" id="stress-plan" aria-label="选择压力测试方案" data-action="stress-plan"><option value="original"' + (!chosen ? ' selected' : '') + '>原始承诺 · 不调整</option>' + state.analysis.plans.filter(p => p.result.status === 'feasible').map(p => '<option value="' + p.id + '"' + (chosen?.id === p.id ? ' selected' : '') + '>' + e(planName(p)) + '</option>').join('') + '</select></div><div class="stress-summary"><div><div class="stress-ratio">' + r.pass + '<small> / ' + r.total + '</small></div><div class="stress-bars">' + r.items.map(i => '<i class="' + (i.result.status === 'infeasible' ? 'fail' : i.result.status === 'unknown' ? 'unknown' : '') + '"></i>').join('') + '</div></div><div><h3>组条件找到可行排程</h3><p class="body-copy">' + r.fail + ' 组已证明不可行，' + r.unknown + ' 组尚不能判定。<br>工时按 30 分钟向上取整；这是有限场景检查。</p></div></div><div class="table-wrap"><table class="data-table"><thead><tr><th>扰动条件</th><th>重新推演</th><th>结果依据</th><th>查看</th></tr></thead><tbody>' + r.items.map(i => '<tr class="' + (i.id === state.stressDetail ? 'selected' : '') + '"><td>' + e(i.label) + '<span class="small-note">' + e(i.note) + '</span></td><td>' + badge(i.result) + '</td><td>' + e(i.result.proof?.summary || i.result.errors?.join('；')) + '<span class="small-note">搜索节点：' + i.result.nodes + '</span></td><td><button class="button quiet small" data-action="stress-detail" data-id="' + i.id + '">依据 ↗</button></td></tr>').join('') + '</tbody></table></div></div>' + (detail ? '<div class="section-label"><h2>' + e(detail.label) + '</h2></div>' + (detail.result.status === 'feasible' ? timeline(detail.scenario, detail.result) : '<div class="panel"><div class="proof-box">' + e(detail.result.proof?.summary || detail.result.errors?.join('；')) + '</div><p class="body-copy">该结论仅适用于这次扰动后的输入，不能推广成实际经营结果。</p></div>') : '') + '<div class="callout">一次通过，不代表所有变化都通过；一次失败，也不等于现实一定延期。真实数据校准、真实用户研究与实际工艺审查尚未开展。</div>';
  }
  function dueOptions(due) { let text = ''; for (let d = 0; d < state.scenario.days; d++) for (let t = 1; t <= 16; t++) { const value = d * 48 + t; text += '<option value="' + value + '"' + (value === due ? ' selected' : '') + '>' + E.formatTime(value) + '</option>'; } if (!Array.from({length:state.scenario.days},(_,d)=>d).some(d=>due>=d*48+1&&due<=d*48+16)) text += '<option value="' + due + '" selected>' + E.formatTime(due) + '</option>'; return text; }
  function edit() {
    const s = state.scenario;
    return heading('04 / MAKE ASSUMPTIONS EXPLICIT', '每一个结论，都从这些条件出发。', '直接修改交期和工时，或导入完整项目。输入验证通过后重新计算，旧报告结果不会被当作新的事实。') + '<div class="edit-actions screen-only"><button class="button dark" data-action="apply-edit">验证并重新推演 ↗</button><button class="button quiet" data-action="import">导入 JSON</button><button class="button quiet" data-action="export-config">导出当前项目</button><button class="button quiet" data-action="reset">恢复此场景</button></div><div id="validation-errors" class="validation-errors" role="alert"></div><div class="panel section-spacer"><div class="panel-heading"><div><h2>订单与完成承诺</h2><p>日期为相对日期；原始数据均为合成示例。</p></div><span class="tag">硬交期约束</span></div><div class="table-wrap"><table class="data-table edit-table"><thead><tr><th>订单</th><th>类型</th><th>完成承诺</th></tr></thead><tbody>' + s.orders.map(o => '<tr><td><input aria-label="' + e(o.id) + '订单名称" data-order-label="' + o.id + '" value="' + e(o.label) + '" maxlength="90"></td><td>' + (o.isNew ? '待接新单' : '既有承诺') + '</td><td><select data-due="' + o.id + '" aria-label="' + e(o.label) + '完成承诺">' + dueOptions(o.due) + '</select></td></tr>').join('') + '</tbody></table></div></div><div class="panel section-spacer"><div class="panel-heading"><div><h2>工序、连续时长与资源</h2><p>30 分钟为一格；每道工序不可中断，依赖完成后才能开始。</p></div><span class="tag">最多 16 道工序</span></div><div class="table-wrap"><table class="data-table edit-table"><thead><tr><th>工序</th><th>时长 / 分钟</th><th>同时占用</th><th>前置工序</th></tr></thead><tbody>' + s.tasks.map(t => '<tr><td>' + e(t.label) + '</td><td><input type="number" min="30" max="1440" step="30" data-duration="' + t.id + '" value="' + t.duration * 30 + '" aria-label="' + e(t.label) + '时长分钟"></td><td>' + e(Object.entries(t.needs).map(([id,n]) => s.resources.find(r=>r.id===id).label + ' ×' + n).join('、')) + '</td><td>' + e(t.after.map(id=>s.tasks.find(t=>t.id===id).label).join('、') || '无') + '</td></tr>').join('') + '</tbody></table></div></div><div class="panel section-spacer"><div class="panel-heading"><div><h2>高级约束 JSON</h2><p>支持 1—4 天、1—6 张订单、1—16 道工序、1—8 种资源。最早开始、设备停用、容量与依赖可在此编辑。</p></div><button class="button quiet small" data-action="apply-json">验证并应用 JSON</button></div><textarea id="json-editor" class="json-editor" spellcheck="false" aria-label="完整项目约束 JSON">' + e(JSON.stringify(s, null, 2)) + '</textarea><p class="timeline-note">时间编码：第 1 天 09:00 = 0，每格 30 分钟；第 2 天 09:00 = 48。work 日历为每天 09:00—12:00、14:00—17:00；always 设备可跨夜运行。blocked 使用 [开始格, 结束格) 表示不可用区间。资源同时占用上限为 capacity。</p></div>';
  }
  function reportData() {
    const a = state.analysis, p = plan();
    return {kind: 'promise-lab-evidence', version: E.VERSION, createdAt: new Date().toISOString(), fingerprint: a.fingerprint, dataStatus: '合成案例或用户自填；未做真实商户验证', scenario: E.clone(state.scenario), baseline: a.baseline, incoming: a.incoming, conflict: a.conflict, plans: a.plans.map(p => ({id:p.id, options:p.options, result:p.result, metrics:p.metrics, frontier:p.frontier})), selectedPlan: p?.id || 'original', stress: state.stress ? {pass:state.stress.pass, fail:state.stress.fail, unknown:state.stress.unknown, total:state.stress.total, items:state.stress.items.map(i=>({id:i.id,label:i.label,note:i.note,result:i.result}))} : null, limits: ['30分钟离散模型；1-4天；最多16道不可中断工序', '可行解不保证最优；非支配仅针对已生成候选', '压力检查是指定条件下重新排程，不是现实概率', 'FNV-1a校验码用于比较输入，不是安全签名或第三方认证']};
  }
  function reportMarkdown() {
    const d = reportData(), s = state.scenario;
    const lines = ['# 一单之变：推演依据', '', '生成时间：' + d.createdAt, '版本：' + d.version + '；输入校验码：' + d.fingerprint + '（FNV-1a，非安全签名）', '', '## 输入与状态', s.name, s.source || '用户自填输入，未经独立核实。', '既有承诺：' + statuses[d.baseline.status], '加入新单：' + statuses[d.incoming.status], d.incoming.proof?.summary || '', '', '## 订单', ...s.orders.map(o => '- ' + o.label + '：' + E.formatTime(o.due)), '', '## 候选条件与结果', ...d.plans.map(p => '- ' + planName(p) + '：' + statuses[p.result.status] + (p.metrics ? '；新单推迟' + p.metrics.delay/48 + '天，午间人工' + hours(p.metrics.extra) + '小时，协作' + hours(p.metrics.helper) + '小时' : '')), '', '## 冲突集', d.conflict?.summary || '当前没有已确认的不可行冲突集。', ...(d.conflict?.orders || []).map(id => '- ' + s.orders.find(o=>o.id===id).label), '', '## 指定扰动检查', d.stress ? '找到可行：' + d.stress.pass + '/' + d.stress.total + '；不可行：' + d.stress.fail + '；尚不能判定：' + d.stress.unknown : '未执行。', ...(d.stress?.items || []).map(i=>'- '+i.label+'：'+statuses[i.result.status]), '', '## 解释边界', ...d.limits.map(x=>'- '+x), '', '合成推演、浏览器自动化与演示均不是用户研究。作品未声称真实落地效果。完整输入和排程请同时导出 JSON，重新导入后会重新求解，而不是信任旧结果。'];
    return lines.join('\n');
  }
  function report() {
    const a = state.analysis, p = plan();
    return heading('05 / EVIDENCE TO TAKE AWAY', '带走的，不只是一句“可以”。', '把输入、结果和假设放在一起。JSON 包含当前约束与排程；重新导入会再次计算，不直接相信保存的结论。', '<div class="edit-actions screen-only"><button class="button dark" data-action="export-json">导出 JSON 依据 ↗</button><button class="button quiet" data-action="export-md">导出文字报告</button><button class="button quiet" data-action="print">打印 / 存为 PDF</button></div>') + '<div class="report-hero"><div><div class="eyebrow">PROMISE EVIDENCE / ' + E.VERSION + '</div><h2>' + e(state.scenario.name) + '</h2><p>合成案例或自填约束 · 浏览器本地计算 · ' + state.scenario.tasks.length + ' 道工序</p></div><div class="report-code">' + a.fingerprint + '</div></div><div class="report-grid"><div class="panel"><div class="panel-heading"><h2>从条件到结论的五步</h2></div><ol class="numbered-list"><li><div><strong>先核实已有承诺</strong><span>' + e(statuses[a.baseline.status]) + '。基线若不成立，应先修正已有安排。</span></div></li><li><div><strong>只加入待接新单</strong><span>' + e(statuses[a.incoming.status] + '；' + a.incoming.proof?.summary) + '</span></div></li><li><div><strong>定位相互冲突的承诺</strong><span>' + e(a.conflict ? a.conflict.summary : '当前没有已确认的不可行冲突集。') + '</span></div></li><li><div><strong>比较有明确代价的修改</strong><span>' + a.plans.length + ' 组候选条件，' + a.plans.filter(p=>p.frontier).length + ' 组候选非支配安排。当前查看：' + e(p ? planName(p) : '原始承诺') + '。</span></div></li><li><div><strong>再问一次：条件变化后呢</strong><span>' + (state.stress ? '已执行 ' + state.stress.total + ' 组指定扰动，' + state.stress.pass + ' 组找到可行排程。' : '当前还未执行压力检查。可先进入压力测试。') + '</span></div></li></ol></div><div class="panel"><div class="panel-heading"><h2>报告里的每个“尚未”也要保留</h2></div><p class="body-copy">尚未开展真实商户试用、真实工时校准与实际收益评估。当前结果只能证明给定离散模型中的关系。</p><div class="callout">输入校验码是 FNV-1a 内容校验值，便于核对输入是否变化；不是密码学签名、可信时间戳或第三方认证。</div><div class="report-evidence">引擎版本  ' + E.VERSION + '\n时间粒度  30 min\n当前范围  ' + state.scenario.days + ' days\n搜索结果  ' + e(a.incoming.status) + '\n搜索节点  ' + a.incoming.nodes + '\n输入校验  ' + a.fingerprint + '</div><hr class="divider"><button class="link-button screen-only" data-action="about">查看来源与完整边界 ↗</button></div></div>';
  }
  function render() {
    $('#nav').innerHTML = sections.map(([id, label, symbol], i) => '<button class="nav-item ' + (state.view === id ? 'active' : '') + '" data-action="set-view" data-view="' + id + '" aria-label="' + label + '"' + (state.view === id ? ' aria-current="page"' : '') + '><span class="nav-symbol" aria-hidden="true">' + symbol + '</span><span>' + label + '</span><span class="nav-no">0' + (i + 1) + '</span></button>').join('');
    $('#view-label').textContent = sections.find(v => v[0] === state.view)[1];
    const views = {overview, lab, compare, stress: stressView, edit, report};
    $('#main').innerHTML = views[state.view](); $('#main').setAttribute('aria-busy', 'false');
    renderTour();
  }
  function download(name, text, type) { const url = URL.createObjectURL(new Blob([text], {type})), link = document.createElement('a'); link.href = url; link.download = name; document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); notify('已生成下载文件。'); }
  function showErrors(errors) { const target = $('#validation-errors'); if (target) { target.innerHTML = '<strong>条件尚未应用</strong><br>' + errors.map(e).join('<br>'); target.scrollIntoView({block: 'center'}); } else notify(errors[0]); }
  function acceptScenario(candidate) { const errors = E.validate(candidate); if (errors.length) { showErrors(errors); return false; } state.scenario = E.clone(candidate); calculate(); render(); notify('约束已验证，全部结果已重新计算。'); return true; }
  async function importFile(file) {
    if (!file) return;
    if (file.size > 1024 * 1024) { showErrors(['JSON 文件须不超过 1MB。']); return; }
    try { const payload = JSON.parse(await file.text()); acceptScenario(payload.kind === 'promise-lab-evidence' ? payload.scenario : payload); } catch (error) { showErrors(['无法读取项目：' + error.message]); }
  }
  function applyEdit() {
    const next = E.clone(state.scenario);
    for (const node of document.querySelectorAll('[data-order-label]')) next.orders.find(o=>o.id===node.dataset.orderLabel).label = node.value.trim();
    for (const node of document.querySelectorAll('[data-due]')) next.orders.find(o=>o.id===node.dataset.due).due = Number(node.value);
    for (const node of document.querySelectorAll('[data-duration]')) next.tasks.find(t=>t.id===node.dataset.duration).duration = Number(node.value) / 30;
    acceptScenario(next);
  }
  const tourSteps = [
    {view:'overview', title:'一单之变：在承诺之前看清影响', text:'从三张合成订单出发。所有结果都由当前约束计算，作品无需账号、外部 API 或观众先填数据。', run:()=>setScenario('ceramic')},
    {view:'lab', title:'第一步：先看已经答应的订单', text:'主制作人每天工作六小时；连续工序不能跨过午间休息。绿色与蓝色是原有承诺。', run:()=>{state.includeNew=false;}},
    {view:'lab', title:'第二步：加入加急单，定位承诺冲突', text:'新单单独能做，但无法与青釉杯的承诺同时兑现。虚线新单排程仅供冲突对照，不能视为已接受。', run:()=>{state.includeNew=true;}},
    {view:'compare', title:'第三步：把不同取舍放在一起', text:'推迟新单、开放午间或引入协作，改变的是不同条件。这里比较的是已生成候选，不宣称穷尽全部最优解。', run:()=>{state.filter='frontier';state.selectedPlan='d1-l0-c0';}},
    {view:'compare', title:'点开方案，看实际排程而不是口号', text:'放宽新单交期后，查看引擎实际找到的工序位置。交期放宽不等于必须推迟开工，设备也可以在人工休息时自行运行。', run:()=>{state.day=0;state.selectedPlan='d1-l0-c0';}},
    {view:'stress', title:'第四步：承诺还要经得住条件变化', text:'对工时、准备时间和设备停用分别扰动，再次求解。这是明确的场景检查，不是现实准时概率。', run:()=>{state.day=0;state.stress=null;}},
    {view:'lab', title:'换一个场景，瓶颈也会改变', text:'丝印场景只有一台印台。即使引入协作者，设备仍然互斥，系统不会凭空多出一台机器。', run:()=>{setScenario('print');state.includeNew=true;}},
    {view:'stress', title:'能接进去，也可能缺少工时余量', text:'皮具场景在原估计下可行，人工工时增加后可能不可行。用同一引擎检查，而不是给一个装饰性的风险分。', run:()=>{setScenario('leather');state.selectedPlan='d0-l0-c0';state.stress=null;}},
    {view:'edit', title:'第五步：条件可以改，结论必须跟着改', text:'工序时长、交期、资源和依赖均可检查。导入旧报告只取其输入重新计算，不直接沿用保存的结论。', run:()=>{}},
    {view:'report', title:'留下输入、结果与边界', text:'可导出 JSON 与文字报告。内置数据为合成案例，尚未开展真实商户试用；这些事实会与计算结果一并保留。', run:()=>{}}
  ];
  function tourStep(index) {
    clearTimeout(tourTimer); state.tourIndex = Math.max(0, Math.min(tourSteps.length-1,index));
    const step = tourSteps[state.tourIndex]; step.run(); state.view = step.view; if(step.view==='stress') ensureStress(); render(); window.scrollTo(0,0);
    if (state.tourRunning && !state.tourPaused) tourTimer = setTimeout(() => { if (state.tourIndex < tourSteps.length-1) tourStep(state.tourIndex+1); else {state.tourPaused=true;renderTour();} }, 11500);
  }
  function startTour() { state.tourRunning=true;state.tourPaused=false;document.body.classList.add('touring');tourStep(0); }
  function stopTour() { clearTimeout(tourTimer);state.tourRunning=false;state.tourPaused=false;document.body.classList.remove('touring');renderTour(); }
  function renderTour() { const node=$('#tour'); node.hidden=!state.tourRunning;if(!state.tourRunning){node.innerHTML='';return;}const t=tourSteps[state.tourIndex];node.innerHTML='<div class="tour-bar"><div class="tour-counter">'+String(state.tourIndex+1).padStart(2,'0')+' / '+tourSteps.length+'</div><div class="tour-narration"><strong>'+e(t.title)+'</strong><p>'+e(t.text)+'</p></div><div class="tour-controls"><button data-action="tour-prev" aria-label="上一步">←</button><button data-action="tour-pause">'+(state.tourPaused?'继续':'暂停')+'</button><button data-action="tour-next" aria-label="下一步">→</button><button data-action="tour-stop">结束</button></div></div>'; }
  const actions = {
    'set-view':node=>navigate(node.dataset.view), 'start-lab':()=>{state.includeNew=false;navigate('lab');},
    'case':node=>setScenario(node.dataset.id), 'toggle-incoming':()=>{state.includeNew=!state.includeNew;state.focusedTask='';render();},
    'day':node=>{state.day=Number(node.dataset.day);render();}, 'task':node=>{state.focusedTask=node.dataset.task;render();},
    'plan':node=>{state.selectedPlan=node.dataset.id;state.stress=null;state.focusedTask='';render();},
    'filter':node=>{state.filter=node.dataset.filter;render();}, 'stress-detail':node=>{state.stressDetail=node.dataset.id;state.focusedTask='';render();},
    'apply-edit':applyEdit, 'apply-json':()=>{try{acceptScenario(JSON.parse($('#json-editor').value));}catch(error){showErrors(['JSON 语法不正确：'+error.message]);}},
    'import':()=>$('#import-file').click(), 'reset':()=>{const original=examples.find(s=>s.id===state.scenario.id)||examples[0];setScenario(original.id);notify('已恢复内置合成案例。');},
    'export-json':()=>download('一单之变-推演依据.json',JSON.stringify(reportData(),null,2),'application/json;charset=utf-8'),
    'export-config':()=>download('一单之变-项目约束.json',JSON.stringify(state.scenario,null,2),'application/json;charset=utf-8'),
    'export-md':()=>download('一单之变-推演报告.md',reportMarkdown(),'text/markdown;charset=utf-8'),
    'about':()=>$('#about').showModal(),'close-about':()=>$('#about').close(),'print':()=>window.print(),
    'tour':startTour,'tour-stop':stopTour,'tour-prev':()=>tourStep(state.tourIndex-1),'tour-next':()=>tourStep(state.tourIndex+1),
    'tour-pause':()=>{state.tourPaused=!state.tourPaused;clearTimeout(tourTimer);if(!state.tourPaused)tourTimer=setTimeout(()=>tourStep(Math.min(tourSteps.length-1,state.tourIndex+1)),11500);renderTour();}
  };
  document.addEventListener('click',event=>{const node=event.target.closest('[data-action]');if(node&&actions[node.dataset.action])actions[node.dataset.action](node);});
  document.addEventListener('keydown',event=>{if((event.key==='Enter'||event.key===' ')&&event.target.matches('g[data-action]')){event.preventDefault();actions[event.target.dataset.action]?.(event.target);}});
  document.addEventListener('change',event=>{const node=event.target;if(node.dataset.action==='scenario')setScenario(node.value);if(node.dataset.action==='stress-plan'){state.selectedPlan=node.value==='original'?'':node.value;state.stress=null;state.stressDetail='';ensureStress();render();}});
  $('#import-file').addEventListener('change',async event=>{await importFile(event.target.files[0]);event.target.value='';});
  calculate(); render();
  // 只暴露可复核快照与导览入口，便于离线验收及实际录屏。
  window.PromiseLabApp={getSnapshot:()=>E.clone(reportData()),startTour,stopTour,goTourStep:index=>tourStep(index)};
  if(new URLSearchParams(location.search).get('autoplay')==='1')setTimeout(startTour,600);
})();
