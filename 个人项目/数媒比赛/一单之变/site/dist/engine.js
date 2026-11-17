/* 一单之变 1.0 | 有界离散约束求解；无第三方运行时依赖。 */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.PromiseLab = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const VERSION = '1.0.0';
  const clone = value => JSON.parse(JSON.stringify(value));
  const idPattern = /^[a-zA-Z][a-zA-Z0-9_-]{0,31}$/;
  const forbidden = new Set(['__proto__', 'constructor', 'prototype']);
  const integer = Number.isInteger;
  const horizon = s => (s.days - 1) * 48 + 16;
  const label = value => typeof value === 'string' && value.length > 0 && value.length <= 90 && !/[\u0000-\u001f]/.test(value);
  function validate(s) {
    const errors = [];
    if (!s || typeof s !== 'object' || Array.isArray(s)) return ['项目必须是一个对象。'];
    if (!label(s.name)) errors.push('项目名称须为 1-90 个字符，且不含控制字符。');
    for (const key of ['summary', 'category', 'source', 'note']) if (s[key] !== undefined && (typeof s[key] !== 'string' || s[key].length > 2000)) errors.push(key + ' 须为不超过 2000 个字符的文字。');
    if (s.id !== undefined && (typeof s.id !== 'string' || !idPattern.test(s.id) || forbidden.has(s.id))) errors.push('项目 ID 无效。');
    if (!integer(s.days) || s.days < 1 || s.days > 4) errors.push('推演范围须为 1-4 天。');
    if (s.slotMinutes !== 30) errors.push('当前模型采用固定 30 分钟时间格。');
    if (s.openLunch !== undefined && typeof s.openLunch !== 'boolean') errors.push('午间开放标记须为布尔值。');
    for (const [key, max] of [['resources', 8], ['orders', 6], ['tasks', 16]]) {
      if (!Array.isArray(s[key]) || s[key].length < 1 || s[key].length > max) errors.push(key + ' 数量不在支持范围。');
    }
    if (errors.length) return errors;
    const H = horizon(s), maps = {};
    for (const key of ['resources', 'orders', 'tasks']) {
      maps[key] = new Map();
      for (const v of s[key]) {
        if (!v || !idPattern.test(v.id) || forbidden.has(v.id)) { errors.push(key + ' 中存在无效 ID。'); continue; }
        if (maps[key].has(v.id)) errors.push('重复 ID：' + v.id);
        maps[key].set(v.id, v);
        if (!label(v.label)) errors.push(v.id + ' 的名称无效。');
      }
    }
    if (errors.length) return errors;
    for (const r of s.resources) {
      if (!integer(r.capacity) || r.capacity < 1 || r.capacity > 3) errors.push(r.id + ' 容量须为 1-3。');
      if (!['work', 'always'].includes(r.calendar)) errors.push(r.id + ' 日历无效。');
      if (r.blocked !== undefined && (!Array.isArray(r.blocked) || r.blocked.length > 12 || r.blocked.some(x => !Array.isArray(x) || x.length !== 2 || !integer(x[0]) || !integer(x[1]) || x[0] < 0 || x[1] <= x[0] || x[1] > H))) errors.push(r.id + ' 不可用时段无效。');
    }
    for (const o of s.orders) {
      if (!integer(o.due) || o.due < 1 || o.due > H) errors.push(o.id + ' 交期超出范围。');
      if (!integer(o.release ?? 0) || (o.release ?? 0) < 0 || (o.release ?? 0) >= H) errors.push(o.id + ' 最早开始时间无效。');
      if (o.isNew !== undefined && typeof o.isNew !== 'boolean') errors.push(o.id + ' 新单标记须为布尔值。');
      if (!s.tasks.some(t => t.order === o.id)) errors.push(o.id + ' 没有工序。');
    }
    if (s.orders.filter(o => o.isNew).length !== 1) errors.push('项目须且只能标记一张待接新单。');
    for (const t of s.tasks) {
      if (!maps.orders.has(t.order)) errors.push(t.id + ' 所属订单不存在。');
      if (!integer(t.duration) || t.duration < 1 || t.duration > 48) errors.push(t.id + ' 时长须为 1-48 格。');
      if (!integer(t.release ?? 0) || (t.release ?? 0) < 0 || (t.release ?? 0) >= H) errors.push(t.id + ' 最早开始时间无效。');
      if (!t.needs || typeof t.needs !== 'object' || Array.isArray(t.needs) || !Object.keys(t.needs).length) errors.push(t.id + ' 资源要求为空。');
      else for (const [r, n] of Object.entries(t.needs)) if (!maps.resources.has(r) || !integer(n) || n < 1 || n > 3) errors.push(t.id + ' 资源要求无效。');
      if (!Array.isArray(t.after) || t.after.length > 8 || new Set(t.after).size !== t.after.length) errors.push(t.id + ' 依赖列表无效。');
      else for (const p of t.after) {
        const prior = maps.tasks.get(p);
        if (!prior || prior.id === t.id || prior.order !== t.order) errors.push(t.id + ' 的依赖须为同订单的其他工序。');
      }
    }
    if (!errors.length) {
      const pending = new Set(s.tasks.map(t => t.id)), done = new Set();
      while (pending.size) {
        const ready = s.tasks.filter(t => pending.has(t.id) && t.after.every(p => done.has(p)));
        if (!ready.length) { errors.push('工序依赖存在循环。'); break; }
        for (const t of ready) { pending.delete(t.id); done.add(t.id); }
      }
    }
    return errors;
  }
  function isOpen(s, resource, slot) {
    if (slot < 0 || slot >= horizon(s)) return false;
    if ((resource.blocked || []).some(([a, b]) => slot >= a && slot < b)) return false;
    if (resource.calendar === 'always') return true;
    const local = slot % 48;
    return local < 6 || (local >= 10 && local < 16) || (s.openLunch === true && local >= 6 && local < 10);
  }
  function formatTime(slot) {
    const day = Math.floor(slot / 48) + 1;
    const minutes = (540 + (slot % 48) * 30) % 1440;
    // 0 格为第 1 天 09:00；跨午夜须归入下一自然日。
    const naturalDay = day + Math.floor((540 + (slot % 48) * 30) / 1440);
    return '第' + naturalDay + '天 ' + String(Math.floor(minutes / 60)).padStart(2, '0') + ':' + String(minutes % 60).padStart(2, '0');
  }
  function timeLabel(slot) { return formatTime(slot).split(' ')[1]; }
  function selected(s, options) {
    const ids = options.orderIds ? new Set(options.orderIds) : new Set(s.orders.filter(o => options.includeNew !== false || !o.isNew).map(o => o.id));
    return {orders: s.orders.filter(o => ids.has(o.id)), tasks: s.tasks.filter(t => ids.has(t.order))};
  }
  function solve(s, options = {}) {
    const errors = validate(s);
    if (errors.length) return {status: 'invalid', errors, schedule: [], nodes: 0, proof: null};
    const {orders, tasks} = selected(s, options), H = horizon(s), limit = options.nodeLimit === undefined ? 60000 : options.nodeLimit;
    const om = new Map(orders.map(o => [o.id, o])), rm = new Map(s.resources.map(r => [r.id, r]));
    const domains = new Map(), earliest = new Map(), done = new Set();
    const failure = (kind, summary, items = []) => ({status: 'infeasible', schedule: [], nodes: 0, proof: {kind, summary, items}, complete: true});
    for (let k = 0; k < tasks.length; k++) {
      const t = tasks.find(t => !done.has(t.id) && t.after.every(p => done.has(p)));
      const o = om.get(t.order), release = Math.max(o.release || 0, t.release || 0, ...t.after.map(p => earliest.get(p)));
      const starts = [];
      for (let start = release; start + t.duration <= o.due; start++) {
        let fits = true;
        for (const [r, units] of Object.entries(t.needs)) {
          const resource = rm.get(r);
          if (units > resource.capacity) { fits = false; break; }
          for (let j = start; j < start + t.duration; j++) if (!isOpen(s, resource, j)) { fits = false; break; }
          if (!fits) break;
        }
        if (fits) starts.push(start);
      }
      if (!starts.length) return failure('window', t.label + ' 在依赖、连续工时、资源日历与交期约束下没有可用时段。', [{task: t.id, earliest: release, duration: t.duration, due: o.due}]);
      domains.set(t.id, starts); earliest.set(t.id, starts[0] + t.duration); done.add(t.id);
    }
    const deadlines = [...new Set(orders.map(o => o.due))].sort((a, b) => a - b);
    for (const r of s.resources) for (const due of deadlines) {
      const relevant = tasks.filter(t => om.get(t.order).due <= due && t.needs[r.id]);
      const load = relevant.reduce((sum, t) => sum + t.duration * t.needs[r.id], 0);
      let available = 0;
      for (let x = 0; x < due; x++) if (isOpen(s, r, x)) available += r.capacity;
      if (load > available) return failure('capacity', r.label + ' 在 ' + formatTime(due) + ' 前需要 ' + load / 2 + ' 资源小时，仅有 ' + available / 2 + ' 资源小时。', [{resource: r.id, load, available, due, tasks: relevant.map(t => t.id)}]);
    }
    // 对依赖边做安全的时域收缩；每次只删除不可能与相邻工序兼容的开始时间。
    let changed = true;
    while (changed) {
      changed = false;
      for (const t of tasks) for (const priorId of t.after) {
        const prior = tasks.find(p => p.id === priorId), before = domains.get(priorId), after = domains.get(t.id);
        const nextBefore = before.filter(start => start + prior.duration <= after[after.length - 1]);
        if (!nextBefore.length) return failure('dependency-window', prior.label + ' 与 ' + t.label + ' 的连续工时和先后关系无法在交期内成立。', [{tasks:[priorId,t.id]}]);
        const nextAfter = after.filter(start => start >= nextBefore[0] + prior.duration);
        if (!nextAfter.length) return failure('dependency-window', t.label + ' 在前置工序之后没有可用开始时间。', [{task:t.id}]);
        if (nextBefore.length !== before.length || nextAfter.length !== after.length) changed = true;
        domains.set(priorId,nextBefore); domains.set(t.id,nextAfter);
      }
    }
    // 不论如何排程都会占用的交叠区间，构成可直接检查的不可行证据。
    for (const r of s.resources) for (let slot = 0; slot < H; slot++) {
      const compulsory = tasks.filter(t => t.needs[r.id] && domains.get(t.id)[domains.get(t.id).length - 1] <= slot && domains.get(t.id)[0] + t.duration > slot);
      const demand = compulsory.reduce((n,t)=>n+t.needs[r.id],0);
      if (demand > r.capacity) {
        const end = Math.min(...compulsory.map(t=>domains.get(t.id)[0]+t.duration));
        return failure('compulsory-overlap', compulsory.map(t=>t.label).join('、') + ' 在 ' + formatTime(slot) + '—' + timeLabel(end) + ' 必然重叠；' + r.label + ' 所需容量 ' + demand + '，可用容量只有 ' + r.capacity + '。', [{resource:r.id,start:slot,end,demand,capacity:r.capacity,tasks:compulsory.map(t=>({task:t.id,earliest:domains.get(t.id)[0],latest:domains.get(t.id)[domains.get(t.id).length-1],duration:t.duration}))}]);
      }
    }
    const usage = new Map(s.resources.map(r => [r.id, new Uint8Array(H)])), assigned = new Map();
    let nodes = 0, aborted = false, found = null;
    function fit(t, start) {
      for (const [r, units] of Object.entries(t.needs)) {
        const u = usage.get(r), cap = rm.get(r).capacity;
        for (let x = start; x < start + t.duration; x++) if (u[x] + units > cap) return false;
      }
      return true;
    }
    function remainingCapacity() {
      for (const r of s.resources) for (const due of deadlines) {
        let load = 0;
        for (const t of tasks) if (!assigned.has(t.id) && om.get(t.order).due <= due) load += t.duration * (t.needs[r.id] || 0);
        if (!load) continue;
        let available = 0;
        for (let x = 0; x < due; x++) if (isOpen(s, r, x)) available += r.capacity - usage.get(r.id)[x];
        if (load > available) return false;
      }
      return true;
    }
    function search() {
      if (nodes >= limit) { aborted = true; return false; }
      nodes++;
      if (assigned.size === tasks.length) { found = tasks.map(t => ({task: t.id, start: assigned.get(t.id).start, end: assigned.get(t.id).end})); return true; }
      if (!remainingCapacity()) return false;
      let chosen = null, candidates = null;
      for (const t of tasks) {
        if (assigned.has(t.id) || !t.after.every(p => assigned.has(p))) continue;
        const minStart = Math.max(0, ...t.after.map(p => assigned.get(p).end));
        const possible = domains.get(t.id).filter(start => start >= minStart && fit(t, start));
        if (!possible.length) return false;
        if (candidates === null || possible.length < candidates.length || (possible.length === candidates.length && om.get(t.order).due < om.get(chosen.order).due)) { chosen = t; candidates = possible; }
      }
      for (const start of candidates) {
        const end = start + chosen.duration;
        assigned.set(chosen.id, {start, end});
        for (const [r, units] of Object.entries(chosen.needs)) for (let x = start; x < end; x++) usage.get(r)[x] += units;
        if (search()) return true;
        for (const [r, units] of Object.entries(chosen.needs)) for (let x = start; x < end; x++) usage.get(r)[x] -= units;
        assigned.delete(chosen.id);
        if (aborted) return false;
      }
      return false;
    }
    search();
    if (found) return {status: 'feasible', schedule: found.sort((a, b) => a.start - b.start || a.task.localeCompare(b.task)), nodes, complete: false, proof: {kind: 'witness', summary: '找到一份满足全部已建模约束的排程；不声称最优。', items: []}};
    if (aborted) return {status: 'unknown', schedule: [], nodes, complete: false, proof: {kind: 'limit', summary: '搜索达到 ' + limit + ' 个节点，尚不能判定。请减少范围或提高预算。', items: []}};
    return {status: 'infeasible', schedule: [], nodes, complete: true, proof: {kind: 'exhaustive', summary: '已遍历当前离散模型的可用安排，未找到能同时兑现全部承诺的排程。', items: []}};
  }
  function verify(s, result, options = {}) {
    const errors = validate(s);
    if (errors.length) return errors;
    const {tasks, orders} = selected(s, options), om = new Map(orders.map(o => [o.id, o])), tm = new Map(tasks.map(t => [t.id, t]));
    const entries = result.schedule || [], seen = new Map(), used = new Map(s.resources.map(r => [r.id, new Uint8Array(horizon(s))]));
    if (entries.length !== tasks.length) errors.push('工序数量不匹配。');
    for (const e of entries) {
      const t = tm.get(e.task);
      if (!t || seen.has(e.task)) { errors.push('未知或重复工序。'); continue; }
      seen.set(e.task, e);
      if (!integer(e.start) || !integer(e.end) || e.start < 0 || e.end > horizon(s) || e.end - e.start !== t.duration) { errors.push(t.id + ' 起止时间或时长不正确。'); continue; }
      if (e.start < Math.max(t.release || 0, om.get(t.order).release || 0) || e.end > om.get(t.order).due) errors.push(t.id + ' 违反可开始时间或交期。');
      for (const [id, units] of Object.entries(t.needs)) {
        const resource = s.resources.find(r => r.id === id);
        for (let x = e.start; x < e.end; x++) { if (!isOpen(s, resource, x)) errors.push(t.id + ' 占用了关闭时段。'); used.get(id)[x] += units; }
      }
    }
    for (const t of tasks) for (const p of t.after) if (!seen.has(t.id) || !seen.has(p) || seen.get(p).end > seen.get(t.id).start) errors.push(t.id + ' 依赖不满足。');
    for (const r of s.resources) if ([...used.get(r.id)].some(v => v > r.capacity)) errors.push(r.id + ' 资源容量冲突。');
    return [...new Set(errors)];
  }
  function conflictCore(s) {
    let ids = s.orders.map(o => o.id), checks = [];
    const initial = solve(s, {nodeLimit: 20000});
    if (initial.status !== 'infeasible') return {orders: [], minimal: false, checks, summary: '尚无已证明的不可行结果。'};
    for (const id of [...ids]) {
      const remaining = ids.filter(x => x !== id), r = solve(s, {orderIds: remaining, nodeLimit: 12000});
      checks.push({removed: id, status: r.status, nodes: r.nodes});
      if (r.status === 'infeasible') ids = remaining;
    }
    // 单调约束下逐项删除可得包含意义上的极小集合；超限时不得宣称极小。
    let minimal = true;
    for (const id of ids) if (solve(s, {orderIds: ids.filter(x => x !== id), nodeLimit: 12000}).status !== 'feasible') minimal = false;
    return {orders: ids, minimal, checks, summary: minimal ? '这组订单无法同时兑现；移除其中任一张后，均找到可行排程。它是包含意义上的极小冲突集，不保证订单数量最少或唯一。' : '已缩小到这组不可兼容订单；部分移除检查超限，不声称极小。'};
  }
  function transform(s, options) {
    const next = clone(s);
    next.openLunch = !!options.openLunch;
    const incoming = next.orders.find(o => o.isNew);
    incoming.due = Math.min(horizon(next), incoming.due + (options.delayDays || 0) * 48);
    if (options.collaborate && next.resources.some(r => r.id === 'helper')) {
      for (const t of next.tasks) if (t.order === incoming.id && t.delegate === true && t.needs.maker) {
        t.needs.helper = t.needs.maker; delete t.needs.maker;
      }
    }
    return next;
  }
  function effort(original, scenario, result) {
    let extra = 0, helper = 0;
    const resource = original.resources.find(r => r.id === 'maker');
    for (const e of result.schedule) {
      const t = scenario.tasks.find(t => t.id === e.task);
      helper += (t.needs.helper || 0) * t.duration;
      if (resource && t.needs.maker) for (let x = e.start; x < e.end; x++) if (!isOpen(original, resource, x)) extra += t.needs.maker;
    }
    return {delay: scenario.orders.find(o => o.isNew).due - original.orders.find(o => o.isNew).due, extra, helper};
  }
  function comparePlans(s) {
    const plans = [], known = new Set();
    const canDelegate = s.resources.some(r => r.id === 'helper') && s.tasks.some(t => t.order === s.orders.find(o => o.isNew).id && t.delegate === true && t.needs.maker);
    for (const delayDays of [0, 1, 2]) for (const openLunch of (s.openLunch ? [true] : [false, true])) for (const collaborate of (canDelegate ? [false, true] : [false])) {
      const opts = {delayDays, openLunch, collaborate}, scenario = transform(s, opts);
      const key = fingerprint(scenario);
      if (known.has(key)) continue; known.add(key);
      const result = solve(scenario, {nodeLimit: 16000});
      const metrics = result.status === 'feasible' ? effort(s, scenario, result) : null;
      plans.push({id: 'd' + delayDays + '-l' + Number(openLunch) + '-c' + Number(collaborate), options: opts, scenario, result, metrics, frontier: false});
    }
    for (const p of plans) {
      if (!p.metrics) continue;
      p.frontier = !plans.some(q => q !== p && q.metrics && ['delay', 'extra', 'helper'].every(k => q.metrics[k] <= p.metrics[k]) && ['delay', 'extra', 'helper'].some(k => q.metrics[k] < p.metrics[k]));
      if (p.frontier) {
        const equivalent = plans.slice(0, plans.indexOf(p)).find(q => q.metrics && ['delay', 'extra', 'helper'].every(k => q.metrics[k] === p.metrics[k]));
        if (equivalent) { p.frontier = false; p.equivalentTo = equivalent.id; }
      }
    }
    return plans;
  }
  function analyze(s) {
    const errors = validate(s);
    if (errors.length) return {errors};
    const baseline = solve(s, {includeNew: false}), incoming = solve(s);
    return {errors: [], baseline, incoming, conflict: incoming.status === 'infeasible' ? conflictCore(s) : null, plans: comparePlans(s), fingerprint: fingerprint(s)};
  }
  function stress(s) {
    const items = [];
    const add = (id, label, change, note) => { const next = clone(s); change(next); const errors = validate(next); const result = errors.length ? {status: 'unknown', nodes: 0, schedule: [], proof: {kind: 'outside-model', summary: '扰动超出当前支持范围，未作可行性判断：' + errors.join('；'), items: []}} : solve(next, {nodeLimit: 20000}); items.push({id, label, note, result, scenario: next}); };
    add('reference', '原始工时与日历', () => {}, '参照组；仍重新求解。');
    for (const [id, factor] of [['plus10', 1.1], ['plus25', 1.25]]) add(id, '人工工序工时 +' + Math.round((factor - 1) * 100) + '%', n => { for (const t of n.tasks) if (t.needs.maker || t.needs.helper) t.duration = Math.ceil(t.duration * factor); }, '按 30 分钟向上取整；短工序实际增幅可能超过标称比例。');
    add('new-extra', '新单每道人工作业 +30 分钟', n => { const o = n.orders.find(o => o.isNew); for (const t of n.tasks) if (t.order === o.id && (t.needs.maker || t.needs.helper)) t.duration += 1; }, '只改变待接新单，既有订单保持原工时。');
    add('arrival', '新单最早开始推迟 2 小时', n => { const o = n.orders.find(o => o.isNew); o.release = Math.min(horizon(n) - 1, (o.release || 0) + 4); }, '模拟资料或材料较晚准备好；不代表实际到货预测。');
    const device = s.resources.find(r => !['maker', 'helper'].includes(r.id));
    if (device) add('outage', device.label + ' 第一天上午不可用', n => { const r = n.resources.find(r => r.id === device.id); r.blocked = [...(r.blocked || []), [0, 6]]; }, '增加单个设备停用窗口，其余条件不变。');
    return {items, pass: items.filter(i => i.result.status === 'feasible').length, fail: items.filter(i => i.result.status === 'infeasible').length, unknown: items.filter(i => i.result.status === 'unknown').length, total: items.length};
  }
  function stable(value) { if (Array.isArray(value)) return '[' + value.map(stable).join(',') + ']'; if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + stable(value[k])).join(',') + '}'; return JSON.stringify(value); }
  function fingerprint(value) { let hash = 2166136261; const text = stable(value); for (let i = 0; i < text.length; i++) { hash ^= text.charCodeAt(i); hash = Math.imul(hash, 16777619); } return (hash >>> 0).toString(16).padStart(8, '0'); }
  return {VERSION, clone, validate, horizon, isOpen, formatTime, timeLabel, solve, verify, conflictCore, transform, effort, comparePlans, analyze, stress, fingerprint};
});
