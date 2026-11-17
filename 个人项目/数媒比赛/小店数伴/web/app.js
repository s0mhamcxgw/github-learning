'use strict';
const $ = (s, root = document) => root.querySelector(s);
const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const fmt = (n, digits = 0) => n === null || n === undefined ? '—' : Number(n).toLocaleString('zh-CN', {minimumFractionDigits: digits, maximumFractionDigits: digits});
const percent = (n, digits = 1) => n === null || n === undefined ? '—' : `${(Number(n) * 100).toFixed(digits)}%`;
const paths = {
  overview:'M3 11 12 3l9 8M5 10v11h5v-7h4v7h5V10',
  quality:'M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6l-8-3Zm-4 9 3 3 5-6',
  products:'m3 7 9-4 9 4-9 4-9-4Zm0 0v10l9 4 9-4V7M12 11v10',
  actions:'M8 5H5v16h14V5h-3M8 3h8v4H8V3Zm0 9 2 2 5-4M8 18h7',
  methods:'M12 10v7M12 7h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0',
  sales:'M3 17 9 11l4 3 8-10M15 4h6v6',
  orders:'M5 3h14v18H5V3Zm4 5h6M9 12h6M9 16h3',
  average:'M3 7h18v13H3V7Zm0 5h18M6 3h12M16 16h2',
  export:'M12 3v12m-5-5 5 5 5-5M4 15v6h16v-6',
};
const icon = name => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.overview}"/></svg>`;
const views = {overview:'经营概览',quality:'数据体检',products:'商品洞察',actions:'行动清单',methods:'来源与方法'};
const state = {view:'overview', dataset:'', defaultDataset:'', days:30, deduplicate:true, data:null, loading:false, importToken:null};
const LOCAL_ACTION_KEY = 'shopcompanion.action-notes.v1';
let notes = {};
try { notes = JSON.parse(localStorage.getItem(LOCAL_ACTION_KEY) || '{}'); } catch { notes = {}; }
if (!notes || typeof notes !== 'object' || Array.isArray(notes)) notes = {};
for (const button of document.querySelectorAll('#nav button')) button.innerHTML = `${icon(button.dataset.view)}<span>${views[button.dataset.view]}</span>`;

function toast(message, link = null) {
  const el = $('#toast');
  el.innerHTML = esc(message) + (link ? `<a class="export-link" href="${esc(link)}" target="_blank" rel="noopener">打开导出的报告 ↗</a>` : '');
  el.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { el.hidden = true; }, link ? 18000 : 6000);
}

async function api(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || '请求未完成，请重试。');
  return data;
}

function money(n) { return `${esc(state.data.meta.currencySymbol)}${fmt(n, 2)}`; }
function stored(action) { return notes[`${state.dataset}:${action.id}`] || {status:'todo',note:''}; }
function noteKey(actionId) { return `${state.dataset}:${actionId}`; }
function saveNotes() {
  try { localStorage.setItem(LOCAL_ACTION_KEY, JSON.stringify(notes)); }
  catch { toast('当前浏览器无法持久保存核查记录；可导出行动清单保留记录。'); }
}

async function refresh() {
  state.loading = true;
  $('#content').innerHTML = '<div class="loading-card"><span class="spinner"></span><p>正在核对订单与分析口径…</p></div>';
  try {
    state.data = await api(`/api/analyze?dataset=${encodeURIComponent(state.dataset)}&days=${state.days}&deduplicate=${state.deduplicate}`);
    state.loading = false;
    render();
  } catch (error) {
    state.loading = false;
    $('#content').innerHTML = `<div class="error-card"><h2>暂时未能完成分析</h2><p>${esc(error.message)}</p><button class="secondary-button" data-action="reload">重新载入公开样例</button></div>`;
  }
}

function periodControl() {
  const d = state.data;
  return `<div><div class="heading-controls"><select id="period-select" class="select-control" aria-label="分析区间">${[[7,'最近7个样本日'],[14,'最近14个样本日'],[30,'最近30个样本日'],[60,'最近60个样本日'],[0,'全部样本日期']].map(([value,label])=>`<option value="${value}" ${state.days===value?'selected':''}>${label}</option>`).join('')}</select><button class="secondary-button" data-action="export-report">${icon('export')} 导出报告</button></div><div class="period-meta">${d.period.start} — ${d.period.end} · ${d.meta.currency}</div></div>`;
}

function heading(eyebrow, title, text, controls = true) {
  return `<div class="page-heading"><div><span class="eyebrow">${eyebrow}</span><h1>${title}</h1><p>${text}</p></div>${controls?periodControl():''}</div>`;
}

function change(key) {
  const value = state.data.deltas[key];
  if (value === null) return '<span>上期未完整覆盖或分母为零</span>';
  return `<b class="${value<0?'down':''}">${value<0?'↘':'↗'} ${percent(Math.abs(value))}</b><span>较前一个同长区间</span>`;
}

function kpis() {
  const s = state.data.summary;
  const cards = [['sales','正向销售额',`<span class="currency">${esc(state.data.meta.currencySymbol)}</span>${fmt(s.sales,2)}`,'sales'],['orders','正向订单数',fmt(s.orders),'orders'],['averageOrder','平均订单金额',`<span class="currency">${esc(state.data.meta.currencySymbol)}</span>${fmt(s.averageOrder,2)}`,'average'],['products','有销售的商品',fmt(s.products),'products']];
  return `<div class="kpi-grid">${cards.map(([key,label,value,ico],index)=>`<article class="kpi-card ${index===0?'featured':''}"><div class="kpi-label">${label}<span class="kpi-icon">${icon(ico)}</span></div><div class="kpi-value">${value}</div><div class="kpi-change">${change(key)}</div></article>`).join('')}</div>`;
}

function chart() {
  const d = state.data, rows = d.trend;
  const width=700,height=226,left=57,right=12,top=15,bottom=29;
  const iw=width-left-right,ih=height-top-bottom;
  const rawMax=Math.max(1,...rows.flatMap(r=>[r.sales||0,r.previous||0]));
  const magnitude=10**Math.floor(Math.log10(rawMax));
  const max=Math.ceil(rawMax/magnitude*2)/2*magnitude;
  const x = i => left+(rows.length===1?iw/2:i/(rows.length-1)*iw);
  const y = value => top+ih-(value/max*ih);
  const line = key => rows.map((r,i)=>`${i?'L':'M'}${x(i).toFixed(2)},${y(r[key]||0).toFixed(2)}`).join(' ');
  const current = line('sales');
  const labelNumber = n => n>=1000000?`${(n/1000000).toFixed(1)}m`:n>=1000?`${(n/1000).toFixed(0)}k`:fmt(n);
  const grid = Array.from({length:5},(_,i)=>{const n=max*i/4,py=y(n);return `<line x1="${left}" x2="${width-right}" y1="${py}" y2="${py}" stroke="#eef1e8" stroke-dasharray="3 5"/><text x="${left-12}" y="${py+4}" text-anchor="end">${esc(d.meta.currencySymbol)}${labelNumber(n)}</text>`;}).join('');
  const ticks = Array.from(new Set([0,Math.floor((rows.length-1)/4),Math.floor((rows.length-1)/2),Math.floor((rows.length-1)*3/4),rows.length-1]));
  return `<svg class="trend-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${d.period.start}至${d.period.end}每日正向销售额趋势；详细数值见下方数据表"><defs><linearGradient id="area-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#84b59d" stop-opacity=".22"/><stop offset="100%" stop-color="#84b59d" stop-opacity=".015"/></linearGradient></defs>${grid}<path d="${current} L${x(rows.length-1)},${top+ih} L${x(0)},${top+ih} Z" fill="url(#area-fill)"/>${d.period.comparisonComplete?`<path d="${line('previous')}" fill="none" stroke="#c8d0bc" stroke-width="1.6" stroke-dasharray="5 5"/>`:''}<path d="${current}" fill="none" stroke="#4d8c7e" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>${rows.map((r,i)=>`<circle cx="${x(i)}" cy="${y(r.sales)}" r="3" fill="#fff" stroke="#4d8c7e" stroke-width="1.7"><title>${r.date}：${esc(d.meta.currencySymbol)}${fmt(r.sales,2)}</title></circle>`).join('')}${ticks.map(i=>`<text x="${x(i)}" y="${height-7}" text-anchor="middle">${rows[i].date.slice(5).replace('-','/')}</text>`).join('')}</svg>`;
}

function overview() {
  const d=state.data,q=d.quality,s=d.summary;
  const ratio=q.totalRows?q.positiveRows/q.totalRows:0;
  const topShare=d.products.slice(0,3).reduce((sum,p)=>sum+p.share,0);
  return heading('A CLEARER VIEW, A BETTER NEXT STEP','经营情况，一眼有数。','先把数字看清，再决定今天做什么。') + kpis() +
  `<div class="analysis-grid"><section class="card card-body"><div class="card-header"><div><h2>销售走势</h2><p>按订单发生日期汇总 · 不含负向与取消记录</p></div><div class="chart-legend"><span>本期</span>${d.period.comparisonComplete?'<span class="previous">上一同长区间</span>':''}</div></div>${chart()}<div class="chart-caption"><span>日期为样本日期，不是当前日期</span><b>${d.period.comparisonComplete?'上期完整覆盖，可比较':'上期覆盖不足，不显示增幅'}</b></div><details class="chart-table"><summary>查看每日数值及上期口径</summary><div class="table-scroll"><table><thead><tr><th>本期日期</th><th class="numeric">正向销售额 ${d.meta.currency}</th><th class="numeric">上期对应日金额</th></tr></thead><tbody>${d.trend.map(r=>`<tr><td>${r.date}</td><td class="numeric">${fmt(r.sales,2)}</td><td class="numeric">${fmt(r.previous,2)}</td></tr>`).join('')}</tbody></table></div><p class="table-caption">${esc(d.methods.comparison)}</p></details></section>
  <section class="card readout-card"><div class="card-body"><div class="readout-head"><h2>先确认数据，再做判断</h2><span class="pill">全文件体检</span></div><div class="donut-row"><div class="donut"><svg viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="40" fill="none" stroke="#eef2e7" stroke-width="8"/><circle cx="50" cy="50" r="40" fill="none" stroke="#8eaa8a" stroke-width="8" stroke-linecap="round" stroke-dasharray="${ratio*251.327} 251.327"/></svg><div class="donut-label">${percent(ratio,1)}<small>可计入正向行</small></div></div><div class="donut-copy"><strong>${fmt(q.totalRows)} 条原始记录</strong><p>保留数据处理依据，<br>让每个数字都可追溯。</p></div></div><div class="readout-row"><span>当前排除行数</span><b>${fmt(q.excludedRows)} 行</b></div><div class="readout-row"><span>本期负向 / 取消订单</span><b>${fmt(s.reversalOrders)} 单</b></div><div class="readout-row"><span>前三商品销售占比</span><b>${percent(topShare)}</b></div><div class="readout-row"><button class="text-link" data-go="quality">查看数据体检详情 →</button></div></div></section></div>
  <div class="lower-grid"><section class="card card-body"><div class="card-header"><div><h2>今天，可以先看这些</h2><p>从统计线索中形成待核查事项</p></div><button class="text-link" data-go="actions">全部 ${d.actions.length} 项 →</button></div>${d.actions.slice(0,3).map((a,i)=>`<div class="action-preview"><span class="action-preview-index">${String(i+1).padStart(2,'0')}</span><div><strong>${esc(a.title)}</strong><p>${esc(a.evidence)}</p></div><button class="text-link" data-go="actions" aria-label="查看${esc(a.title)}">↗</button></div>`).join('') || '<div class="empty">当前规则下暂无待核查建议。</div>'}</section>
  <section class="card card-body"><div class="card-header"><div><h2>本期主要商品</h2><p>按有效正向行金额排序</p></div><button class="text-link" data-go="products">查看洞察 →</button></div>${d.products.slice(0,5).map((p,i)=>`<div class="product-mini"><div class="product-avatar">${String(i+1).padStart(2,'0')}</div><div class="product-mini-name"><strong title="${esc(p.name)}">${esc(p.name)}</strong><small>SKU ${esc(p.sku)} · ${fmt(p.orders)}单</small></div><div class="product-mini-amount">${money(p.sales)}<small>销售占比 ${percent(p.share)}</small></div></div>`).join('')||'<div class="empty">本区间没有可计入的正向商品记录。</div>'}</section></div>`;
}

function quality() {
  const d=state.data,q=d.quality;
  return heading('TRUST STARTS WITH THE DETAILS','每个数字，都能回到原表。','看清哪些记录被计入、排除或单独列示。',false)+
  `<div class="data-note">${esc(q.note)} 取消与负向记录不是数据错误，单独列示用于核对。</div><div class="quality-summary"><div class="card card-body"><small>原始记录</small><div class="quality-number">${fmt(q.totalRows)}</div><small>整份文件，未改写原始内容</small></div><div class="card card-body"><small>可计入正向记录</small><div class="quality-number">${fmt(q.positiveRows)}</div><small>已排除负向、不可用及所选重复行</small></div><div class="card card-body"><small>按当前规则排除</small><div class="quality-number">${fmt(q.excludedRows)}</div><label class="check-label"><input id="dedup-checkbox" type="checkbox" ${state.deduplicate?'checked':''}> 剔除精确重复候选行</label></div></div>
  <div class="issues-grid">${q.issues.map(item=>`<article class="issue-card"><h3>${esc(item.title)}</h3><strong>${fmt(item.count)}</strong><p>${esc(item.description)}</p></article>`).join('')}</div>
  <section class="card table-card"><div class="card-header"><div><h2>需要核对的原始记录</h2><p>保留原行号，不用猜问题出在哪里</p></div><input class="table-search" id="quality-search" placeholder="搜索当前预览中的订单或商品" aria-label="搜索当前问题预览"></div><div class="table-scroll"><table><thead><tr><th>原表行号</th><th>订单号</th><th>商品</th><th>原始日期</th><th class="numeric">数量</th><th class="numeric">行金额</th><th>核对原因</th></tr></thead><tbody id="quality-table">${qualityRows(q.examples)}</tbody></table></div><p class="table-caption">仅预览文件顺序中的前30条问题记录。负向记录可能不在当前分析区间；上述体检统计均覆盖全文件。</p></section>
  <div class="data-note"><strong>当前去重依据：</strong>${esc(d.methods.duplicates)}<br><strong>日期口径：</strong>${esc({iso:'年-月-日',dmy:'日/月/年',mdy:'月/日/年'}[d.options.dateOrder])}；${d.options.cancelledPrefix?'将C开头订单号视为取消记录':'不根据C开头订单号推断取消'}。核实原表后，可修正并重新导入。</div>`;
}

function qualityRows(rows) {
  return rows.map(r=>`<tr><td>${fmt(r.sourceRow)}</td><td>${esc(r.order||'（缺失）')}</td><td class="table-product" title="${esc(r.product)}">${esc(r.product||'（缺失）')}</td><td>${esc(r.date)}</td><td class="numeric">${fmt(r.quantity,2)}</td><td class="numeric">${fmt(r.amount,2)}</td><td>${r.issues.map(label=>`<span class="tag">${esc(label)}</span>`).join('')}</td></tr>`).join('') || '<tr><td colspan="7"><div class="empty">当前预览中没有匹配记录。</div></td></tr>';
}

function productRows(rows) {
  return rows.map((p,i)=>`<tr><td><span class="product-rank">${String(i+1).padStart(2,'0')}</span>${esc(p.sku)}</td><td class="table-product" title="${esc(p.name)}">${esc(p.name)}</td><td class="numeric">${money(p.sales)}</td><td class="numeric">${fmt(p.quantity,2)}</td><td class="numeric">${fmt(p.orders)}</td><td class="numeric"><span class="share-bar"><i style="width:${Math.min(100,p.share*300)}%"></i></span>${percent(p.share)}</td></tr>`).join('') || '<tr><td colspan="6"><div class="empty">当前结果中没有匹配商品。</div></td></tr>';
}

function products() {
  const d=state.data;
  return heading('FIND THE SIGNAL IN EVERY ORDER','商品之间，藏着经营线索。','看清商品表现，把同购关联变成可检验的想法。')+
  `<section class="card table-card"><div class="card-header"><div><h2>商品表现</h2><p>显示销售额最高的至多100种商品 · 金额币种 ${d.meta.currency}</p></div><input id="product-search" class="table-search" placeholder="搜索当前结果中的商品 / SKU" aria-label="搜索当前商品结果"></div><div class="table-scroll"><table><thead><tr><th>SKU</th><th>商品</th><th class="numeric">正向销售额</th><th class="numeric">数量</th><th class="numeric">订单数</th><th class="numeric">销售占比</th></tr></thead><tbody id="product-table">${productRows(d.products)}</tbody></table></div><p class="table-caption">同一商品的金额按商品编码汇总；订单数按订单号去重。商品原名来自导入表，不做自动翻译或改写。</p></section>
  <div class="card-header"><div><h2>哪些商品，经常出现在同一笔订单？</h2><p>同购探索 · 统计关联不能证明因果</p></div><span class="pill">${fmt(d.pairMethod.basketOrders)} 个计算订单</span></div>
  <div class="pairs-grid">${d.pairs.map((p,index)=>`<article class="pair-card"><div class="pair-names"><span class="pair-name">${esc(p.aName)}<br><small class="muted">A · ${esc(p.a)}</small></span><span class="pair-plus">＋</span><span class="pair-name">${esc(p.bName)}<br><small class="muted">B · ${esc(p.b)}</small></span></div><div class="pair-stats"><div><span>同购订单</span><strong>${fmt(p.count)}</strong></div><div><span>支持度</span><strong>${percent(p.support)}</strong></div><div><span>置信度 A→B</span><strong>${percent(p.confidence)}</strong></div><div><span>提升度</span><strong>${fmt(p.lift,2)}</strong></div></div><button class="text-link evidence-button" data-pair-evidence="${index}">查看同购订单与原表行号 ↗</button></article>`).join('')||'<div class="empty full-width">当前样本不足以形成满足条件的同购关联，暂不生成组合建议。</div>'}</div>
  <p class="method-note">${esc(d.pairMethod.description)} 本期排除${fmt(d.pairMethod.largeOrdersSkipped)}个超大商品篮。${d.meta.kind==='public'?`公开示例中邮费、折扣、手工记账等已知非商品编码不参与商品榜单及同购计算。本期有效非商品金额${money(d.summary.nonProductAmount)}仍计入正向总额；商品占比的分母为全部正向行金额。`:''}<br>支持度 = 同购订单 / 有效商品订单；置信度 A→B = 同购订单 / 含A订单；提升度 = 观察同购概率 / 独立情况下的同购概率。</p>`;
}

function actions() {
  const d=state.data, done=d.actions.filter(a=>stored(a).status==='done').length;
  return heading('SMALL ACTIONS, CLEAR EVIDENCE','下一步，先做有依据的事。','每条建议都能查看依据；核查结果由你记录。',false)+
  `<div class="action-toolbar"><span class="pill">${done} / ${d.actions.length} 项已核查 · 本期 ${d.period.start} — ${d.period.end}</span><button class="secondary-button" data-action="export-actions">${icon('export')} 导出核查记录</button></div><div class="data-note">这些事项由明确统计规则生成，不代表已发现经营原因。选择“已核查”仅表示你记录了核查状态，不等于建议有效或经营成效已验证。</div>
  <div class="actions-list">${d.actions.map((a,i)=>{const saved=stored(a);return `<article class="action-card ${saved.status==='done'?'done':''}"><div class="action-number">${saved.status==='done'?'✓':String(i+1).padStart(2,'0')}</div><div><div class="action-header"><h2>${esc(a.title)}</h2><span class="pill"><span class="priority-dot"></span>${esc(a.priority)}</span></div><p>${esc(a.detail)}</p><div class="evidence"><small>这条建议的依据</small>${esc(a.evidence)}</div><textarea class="action-notes" data-note="${a.id}" placeholder="记录你的实际核查结果；尚未测试时可留空" aria-label="${esc(a.title)}的核查记录">${esc(saved.note)}</textarea><div class="action-bottom"><select data-status="${a.id}" aria-label="${esc(a.title)}的核查状态"><option value="todo" ${saved.status==='todo'?'selected':''}>待核查</option><option value="done" ${saved.status==='done'?'selected':''}>已核查</option><option value="later" ${saved.status==='later'?'selected':''}>暂不采纳</option></select><button class="text-link" data-go="${a.target}">查看对应数据 →</button><span class="action-meta">${saved.updated?'最近记录：'+esc(saved.updated):'尚未记录实际反馈'}</span></div></div></article>`;}).join('')||'<div class="empty">当前没有满足规则的待核查事项。</div>'}</div>`;
}

function methods() {
  const d=state.data,m=d.meta;
  const mappingNames={order:'订单',date:'日期',product:'商品',sku:'编码',quantity:'数量',unitprice:'单价',amount:'行金额'};
  return heading('KNOW WHERE EVERY NUMBER COMES FROM','数据有来处，结论有边界。','把来源、处理方式和分析局限，一起说清楚。',false)+
  `<div class="data-note evidence-toolbar"><span>保留来源摘要、分析参数、指标及订单依据，方便复核当前结果。</span><button class="secondary-button" data-action="export-evidence">${icon('export')} 导出分析凭据 JSON</button></div>`+
  `<div class="methods-grid"><section class="card method-card"><h2>当前数据来源</h2><div class="source-detail"><span>数据集</span><strong>${esc(m.name)}</strong><span>来源</span><strong>${esc(m.source)}</strong><span>日期覆盖</span><strong>${m.start} — ${m.end}</strong><span>原始行数</span><strong>${fmt(m.rows)}</strong><span>金额币种</span><strong>${esc(m.currency)}（不做汇率换算）</strong><span>许可 / 权限</span><strong>${esc(m.license)}</strong>${m.creator?`<span>作者</span><strong>${esc(m.creator)}</strong>`:''}</div>${m.sourceUrl?`<p style="margin-top:17px"><a href="${esc(m.sourceUrl)}" target="_blank" rel="noopener">打开数据集原始来源 ↗</a></p>`:''}<p>${esc(m.selection)}</p><p>${esc(m.limitations)}</p>${m.citation?`<p>${esc(m.citation)}</p>`:''}<div class="source-detail"><span>文件 SHA256</span><strong class="hash">${esc(m.derivedSha256)}</strong></div></section>
  <section class="card method-card"><h2>指标是怎样算出来的</h2><dl><dt>正向销售额</dt><dd>${esc(d.methods.sales)}</dd><dt>平均订单金额</dt><dd>${esc(d.methods.averageOrder)}</dd><dt>时间对比</dt><dd>${esc(d.methods.comparison)}</dd><dt>精确重复候选</dt><dd>${esc(d.methods.duplicates)}</dd></dl></section>
  <section class="card method-card"><h2>同购关联的口径</h2><p>${esc(d.pairMethod.description)}</p><dl><dt>支持度</dt><dd>${esc(d.pairMethod.support)}</dd><dt>置信度 A→B</dt><dd>${esc(d.pairMethod.confidence)}</dd><dt>提升度</dt><dd>${esc(d.pairMethod.lift)}</dd></dl><p>提升度大于1仅表示样本内观察同现频率高于独立假设；小样本、批发订单、活动和商品季节性均可能影响结果。</p></section>
  <section class="card method-card"><h2>文件处理与使用边界</h2><p>内置样例由公开数据截取，导入文件只在本机服务进程中分析，不调用外部模型或上传到云端。关闭服务后，导入数据和字段映射清除；核查笔记保存在当前浏览器，导出文件保存在作品目录的exports中。</p><p>日期不覆盖完整上期时不展示增幅。缺少库存、成本、支付流水时，不推断库存量、利润或已确认退款。当前未开展真实商户应用成效验证。</p><h3>当前字段映射</h3><div class="mapping-list">${Object.entries(d.mapping).filter(([,v])=>v).map(([key,value])=>`<span class="tag">${esc(mappingNames[key]||key)} ← ${esc(value)}</span>`).join('')}</div><p style="margin-top:15px">默认示例货币为英镑。自行导入时，请明确行金额含义、币种和日期顺序。支持CSV及XLSX，文件不超过35MB。</p><a href="/api/template" download="导入格式示例_非经营数据.csv">下载导入格式示例 ↗</a></section></div>`;
}

function render() {
  if (!state.data) return;
  const d=state.data;
  $('#breadcrumb-view').textContent=views[state.view];
  document.title=`${views[state.view]} · 小店数伴`;
  for(const button of document.querySelectorAll('#nav button')) {
    button.classList.toggle('active',button.dataset.view===state.view);
    if(button.dataset.view===state.view)button.setAttribute('aria-current','page');else button.removeAttribute('aria-current');
  }
  $('#source-strip').innerHTML=`<span class="source-badge">${d.meta.kind==='public'?'公开样例':'本机导入'}</span><p>${esc(d.meta.name)} · ${esc(d.meta.currency)}${d.meta.kind==='public'?' · 英国历史零售数据，仅用于功能验证':''}</p><button data-go="methods">查看来源 ↗</button>`;
  $('#content').innerHTML=({overview,quality,products,actions,methods})[state.view]();
}

function navigate(view) {
  if(!views[view])return;
  state.view=view;
  history.replaceState(null,'',`#${view}`);
  if(!state.loading)render();
  window.scrollTo({top:0,behavior:'instant'});
}

document.addEventListener('click',async event=>{
  const nav=event.target.closest('[data-view],[data-go]');
  if(nav)navigate(nav.dataset.view||nav.dataset.go);
  const action=event.target.closest('[data-action]')?.dataset.action;
  if(action==='reload')loadSample();
  if(action==='export-report')await exportReport();
  if(action==='export-actions')await exportActions();
  if(action==='export-evidence')await exportEvidence();
  const pairButton=event.target.closest('[data-pair-evidence]');
  if(pairButton)openPairEvidence(Number(pairButton.dataset.pairEvidence));
});
document.addEventListener('change',event=>{
  if(event.target.id==='period-select'){state.days=Number(event.target.value);refresh();}
  if(event.target.id==='dedup-checkbox'){state.deduplicate=event.target.checked;refresh();}
  if(event.target.matches('[data-status]')){
    const key=noteKey(event.target.dataset.status);
    notes[key]={...(notes[key]||{note:''}),status:event.target.value,updated:new Date().toLocaleString('zh-CN',{hour12:false})};
    saveNotes();render();
  }
});
document.addEventListener('input',event=>{
  if(event.target.id==='quality-search'){
    const query=event.target.value.trim().toLowerCase();
    $('#quality-table').innerHTML=qualityRows(state.data.quality.examples.filter(r=>`${r.order} ${r.product} ${r.sourceRow}`.toLowerCase().includes(query)));
  }
  if(event.target.id==='product-search'){
    const query=event.target.value.trim().toLowerCase();
    $('#product-table').innerHTML=productRows(state.data.products.filter(p=>`${p.name} ${p.sku}`.toLowerCase().includes(query)));
  }
  if(event.target.matches('[data-note]')){
    const key=noteKey(event.target.dataset.note);
    notes[key]={...(notes[key]||{status:'todo'}),note:event.target.value,updated:new Date().toLocaleString('zh-CN',{hour12:false})};
    saveNotes();
  }
});

async function loadSample(){state.dataset=state.defaultDataset;state.days=30;state.deduplicate=true;await refresh();}
$('#sample-button').addEventListener('click',loadSample);
$('#upload-button').addEventListener('click',()=>$('#file-input').click());
$('.brand').addEventListener('click',event=>{event.preventDefault();navigate('overview');});

const fieldLabels={order:'订单号 *',date:'订单日期 *',product:'商品名称 *',quantity:'数量 *',sku:'商品编码（可选）',amount:'每行实付金额（与单价至少一项）',unitprice:'单价（与行金额至少一项）'};
$('#file-input').addEventListener('change',async event=>{
  const file=event.target.files[0];if(!file)return;
  if(file.size>35*1024*1024){toast('请选择不超过35MB的CSV或XLSX文件。');event.target.value='';return;}
  const button=$('#upload-button');button.disabled=true;button.textContent='正在读取文件…';
  try{
    const preview=await api(`/api/preview?name=${encodeURIComponent(file.name)}`,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file});
    state.importToken=preview.token;
    $('#mapping-fields').innerHTML=Object.entries(fieldLabels).map(([key,label])=>`<label>${label}<select data-map="${key}" ${['order','date','product','quantity'].includes(key)?'required':''}><option value="">${['order','date','product','quantity'].includes(key)?'请选择原表列':'不使用该列'}</option>${preview.columns.map(column=>`<option value="${esc(column)}" ${preview.mapping[key]===column?'selected':''}>${esc(column)}</option>`).join('')}</select></label>`).join('');
    $('#import-file-name').textContent=`${file.name} · ${fmt(preview.rows)}行 · ${preview.columns.length}列`;
    $('#import-preview').innerHTML=`<table><thead><tr>${preview.columns.slice(0,10).map(c=>`<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${preview.preview.map(row=>`<tr>${preview.columns.slice(0,10).map(c=>`<td>${esc(row[c])}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
    $('#import-error').hidden=true;$('#cancelled-prefix').checked=false;$('#currency').value='CNY';$('#date-order').value='iso';
    $('#import-dialog').showModal();
  }catch(error){toast(error.message);}finally{button.disabled=false;button.innerHTML='<span aria-hidden="true">＋</span> 导入订单表';event.target.value='';}
});
function closeImport(){$('#import-dialog').close();}
$('#close-import').addEventListener('click',closeImport);$('#cancel-import').addEventListener('click',closeImport);
$('#close-evidence').addEventListener('click',()=>$('#evidence-dialog').close());
$('#import-form').addEventListener('submit',async event=>{
  event.preventDefault();const button=$('#confirm-import');button.disabled=true;$('#import-error').hidden=true;
  try{
    const mapping={};for(const input of document.querySelectorAll('[data-map]'))mapping[input.dataset.map]=input.value;
    const result=await api('/api/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:state.importToken,mapping,currency:$('#currency').value,dateOrder:$('#date-order').value,cancelledPrefix:$('#cancelled-prefix').checked})});
    state.dataset=result.dataset;state.days=30;state.deduplicate=true;closeImport();state.view='quality';await refresh();toast('导入完成。先检查处理规则，再查看经营分析。');
  }catch(error){$('#import-error').hidden=false;$('#import-error').textContent=error.message;}finally{button.disabled=false;}
});

async function saveExport(content,extension){
  const result=await api('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content,extension})});
  toast(`已保存到：${result.path}`,result.url);
  return result;
}

async function exportReport(){
  const d=state.data;
  const html=`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>小店数伴 · 分析报告</title><style>body{font-family:"Segoe UI","Microsoft YaHei",sans-serif;max-width:950px;margin:50px auto;padding:0 25px;color:#263d32;line-height:1.8}h1{font-size:28px}h2{font-size:19px;margin-top:35px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{padding:10px;border-bottom:1px solid #e1e6dc;text-align:left}th{background:#f3f6ef}.note{background:#f6f5e8;padding:18px;font-size:13px}.metrics{display:flex;gap:35px;flex-wrap:wrap}.metrics strong{display:block;font-size:26px}small{color:#829178}p,li{font-size:13px}.hash{overflow-wrap:anywhere;font-size:11px}@media print{body{margin:0;max-width:none}h2{break-after:avoid}tr{break-inside:avoid}}</style><h1>小店数伴 · 订单分析报告</h1><p>${esc(d.meta.name)} · ${d.period.start} — ${d.period.end} · ${d.meta.currency}</p><p class="note">${esc(d.meta.limitations)} 本报告为统计分析，不是经营改善的实测证明。</p><div class="metrics"><div><small>正向销售额</small><strong>${money(d.summary.sales)}</strong></div><div><small>正向订单数</small><strong>${fmt(d.summary.orders)}</strong></div><div><small>平均订单金额</small><strong>${money(d.summary.averageOrder)}</strong></div></div><h2>数据处理</h2><p>原始${fmt(d.quality.totalRows)}行；排除${fmt(d.quality.excludedRows)}行；正向${fmt(d.quality.positiveRows)}行；负向/取消${fmt(d.quality.reversalRows)}行。${d.options.deduplicate?'当前剔除精确重复候选行。':'当前保留精确重复候选行。'}</p><p>${esc(d.methods.sales)} ${esc(d.methods.comparison)}</p><h2>主要商品（前20项）</h2><table><thead><tr><th>商品</th><th>SKU</th><th>正向销售额</th><th>订单数</th></tr></thead><tbody>${d.products.slice(0,20).map(p=>`<tr><td>${esc(p.name)}</td><td>${esc(p.sku)}</td><td>${money(p.sales)}</td><td>${fmt(p.orders)}</td></tr>`).join('')}</tbody></table><h2>待核查事项</h2>${d.actions.map(a=>`<h3>${esc(a.title)}</h3><p>${esc(a.detail)}</p><p><strong>依据：</strong>${esc(a.evidence)}</p><p><strong>人工核查状态：</strong>${esc({todo:'待核查',done:'已核查',later:'暂不采纳'}[stored(a).status])}；<strong>实际记录：</strong>${esc(stored(a).note||'尚未填写')}</p>`).join('')}<h2>数据来源与复现</h2><p>${esc(d.meta.source)} · ${esc(d.meta.license)}</p><p>${esc(d.meta.citation||'本机导入文件；来源未作外部核验。')}</p><p>${esc(d.meta.selection)}</p>${d.meta.sourceUrl?`<p><a href="${esc(d.meta.sourceUrl)}">数据原始来源</a></p>`:''}<p class="hash">文件SHA256：${esc(d.meta.derivedSha256)}</p><p>生成时间：${esc(new Date().toLocaleString('zh-CN',{hour12:false}))}。工具自动分析与人工核查记录分别列示。</p></html>`;
  try{await saveExport(html,'html');}catch(error){toast(error.message);}
}

async function exportActions(){
  const d=state.data;
  const result={dataset:d.meta,period:d.period,note:'核查状态来自本机浏览器记录，不代表经营成效已验证。',actions:d.actions.map(a=>({...a,review:stored(a)}))};
  try{await saveExport(JSON.stringify(result,null,2),'json');}catch(error){toast(error.message);}
}

function openPairEvidence(index){
  const pair=state.data.pairs[index];if(!pair)return;
  $('#evidence-content').innerHTML=`<p class="data-note">${esc(pair.aName)} ＋ ${esc(pair.bName)}<br>共${fmt(pair.count)}个同购订单；下方展示前${pair.evidence.length}个。原行号可回到同一源文件核对。</p><div class="table-scroll"><table><thead><tr><th>订单号</th><th>日期</th><th class="numeric">A数量</th><th class="numeric">B数量</th><th>原表行号</th></tr></thead><tbody>${pair.evidence.map(row=>`<tr><td>${esc(row.order)}</td><td>${esc(row.date)}</td><td class="numeric">${fmt(row.aQuantity,2)}</td><td class="numeric">${fmt(row.bQuantity,2)}</td><td>${row.sourceRows.map(esc).join('、')}</td></tr>`).join('')}</tbody></table></div><p class="help-text">这些订单来自当前有效正向记录；每单同一商品仅计一次同购。数量仍按保留行汇总。只展示样本证据，不代表关联原因或促销效果已验证。</p>`;
  $('#evidence-dialog').showModal();
}

async function exportEvidence(){
  const result={schema:'shop-companion-analysis-v1',generatedAt:new Date().toISOString(),analysis:state.data,
    reviewNotes:state.data.actions.map(action=>({id:action.id,...stored(action)})),
    note:'统计结果与人工核查记录分别保存。公开样例用于功能验证，不是商户试用。'};
  try{await saveExport(JSON.stringify(result,null,2),'json');}catch(error){toast(error.message);}
}

(async()=>{
  try{
    const info=await api('/api/health');state.defaultDataset=info.defaultDataset;state.dataset=info.defaultDataset;
    const view=location.hash.slice(1);if(views[view])state.view=view;
    await refresh();
  }catch(error){$('#content').innerHTML=`<div class="error-card">服务连接未完成：${esc(error.message)}。请使用启动脚本运行作品。</div>`;}
})();
