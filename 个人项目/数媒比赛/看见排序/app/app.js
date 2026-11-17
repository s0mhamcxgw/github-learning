(function () {
  'use strict';
  const D = window.SortLabData, E = window.SortLabEngine;
  const main = document.getElementById('main');
  if (!D || !E) { main.innerHTML = '<p>核心文件未能加载。请将 data.js、engine.js 与本页面放在同一文件夹后重新打开。</p>'; return; }
  const VERSION = '1.0.0', STORAGE = 'see-order-session-v1';
  const steps = ['intro','lab','compare','reports','summary'];
  const topics = Object.fromEntries(D.topics.map(t => [t.id, t]));
  const byId = Object.fromEntries(D.cards.map(c => [c.id,c]));
  const isCardId = id => typeof id==='string' && Object.prototype.hasOwnProperty.call(byId,id);
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt = n => Number(n).toFixed(3);
  const percent = n => (n * 100).toFixed(1) + '%';
  const eventFor = id => ({cardId:id,topic:byId[id].topic});
  const defaultState = () => ({step:'intro',events:[],lambda:.6,selected:'sports-01',motive:'',storyAnswer:'',compareSnapshot:null,rightLambda:.2,prediction:'',revealed:false,reportIndex:0,reports:[0,1,2].map(() => ({answer:'',note:'',checked:false,repaired:false})),reduced:false});
  let state = defaultState(), toastTimer;
  const reportDefs = [
    {title:'把行为写成了意图',label:'01 / 识别信息边界',quote:'“两个人都点开了同一条音乐内容，所以他们一定都喜欢这种音乐。模型已经知道了他们的真实动机。”',question:'这份报告漏掉了什么？',options:[['signal','点击是记录到的行为，相同点击可能来自不同动机。'],['mind','只要点击过，模型就能知道真实想法。'],['opposite','点击一定意味着不喜欢。']],correct:'signal',feedback:'相同输入只会按同一规则更新。为了听歌、找配乐或完成作业，都可能产生一次点击；这里的模型没有收到动机信息。',placeholder:'观察：两人产生了相同点击。可支持：模型做出相同更新。不能支持：……'},
    {title:'把两个变化当成一个',label:'02 / 修正实验条件',quote:'“右侧把兴趣权重从 0.6 改为 0.2，又额外点击两次音乐内容。右侧排名不同，证明差异完全由权重造成。”',question:'要单独观察权重的作用，先修复哪一项？',options:[['history','恢复相同内容池、起始状态与点击历史，只改变权重。'],['extra','再给右侧多点几次，让差异更明显。'],['delete','把不符合结论的内容从候选池删掉。']],correct:'history',feedback:'刚才的比较混入了额外点击。修复后左右用相同历史重算，才能在这个模型内单独比较权重；结果不一定朝预期方向变化。',placeholder:'观察：修复后两侧历史一致，只有 λ 不同。可支持：…… 不能支持：……'},
    {title:'把一次模拟写成普遍规律',label:'03 / 限定结论范围',quote:'“本次模拟中，前六张的主题覆盖率下降。因此真实平台上的所有人，长期都会被困在信息茧房里。”',question:'哪个结论与现有证据相称？',options:[['all','一次模拟足以证明所有真实用户的长期变化。'],['bound','只能描述本模型、本输入下的列表变化，现实长期效果还需其他证据。'],['none','模拟永远没有任何教学价值。']],correct:'bound',feedback:'模拟能帮助检查规则和理解过程，但不能直接替代真实平台、真实用户或长期观察。主题覆盖率只描述当前列表，不是“信息茧房指数”。',placeholder:'观察：这个模拟列表的覆盖率发生变化。可支持：…… 还不能支持：……'}
  ];

  function replay(events=state.events, lambda=state.lambda) { return E.replay(events,{lambda}); }
  function topicArt(card) { const t=topics[card.topic]; return `<div class="topic-art" style="--topic:${t.color};--topic-bg:${t.color}16" aria-hidden="true">${esc(t.glyph)}</div>`; }
  function pill(topic) { const t=topics[topic]; return `<span class="topic-pill" style="--topic:${t.color};--topic-bg:${t.color}15">${esc(t.label)}</span>`; }
  function pageHead(no,title,desc,actions='') { return `<div class="page-head"><div><div class="eyebrow">EXPERIMENT ${no} / SEE THE ORDER</div><h1>${title}</h1><p>${desc}</p></div><div class="head-actions">${actions}</div></div>`; }
  function say(text) { document.getElementById('live').textContent=text; }
  function toast(text) { const t=document.getElementById('toast'); t.textContent=text;t.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>{t.hidden=true;},3400);say(text); }
  function save() { try { localStorage.setItem(STORAGE, JSON.stringify(sessionData())); } catch (_) { /* File/browser privacy settings may disable storage; the experience remains usable. */ } }
  function sessionData() { return {appVersion:VERSION,step:state.step,events:state.events,lambda:state.lambda,selected:state.selected,motive:state.motive,storyAnswer:state.storyAnswer,compareSnapshot:state.compareSnapshot,rightLambda:state.rightLambda,prediction:state.prediction,revealed:state.revealed,reportIndex:state.reportIndex,reports:state.reports,reduced:state.reduced}; }
  function validLambda(v) { if(typeof v!=='number'||!Number.isFinite(v)||v<0||v>1)throw new Error('权重必须在 0 到 1 之间。'); return v; }
  function validBoolean(v) { if(typeof v!=='boolean')throw new Error('操作状态必须为 true 或 false。');return v; }
  function validateSession(raw) {
    if (!raw || raw.appVersion!==VERSION) throw new Error('应用版本不一致，暂不能导入。');
    if(!Array.isArray(raw.events)||raw.events.length>1000)throw new Error('动作记录格式不正确或超过 1000 次。');
    const checked = replay(raw.events,validLambda(raw.lambda));
    const next=defaultState();
    next.events=checked.events;next.lambda=raw.lambda;
    next.step=steps.includes(raw.step)?raw.step:'summary';
    next.selected=isCardId(raw.selected)?raw.selected:'sports-01';
    next.motive=['watch','sound'].includes(raw.motive)?raw.motive:'';
    next.storyAnswer=['same','mind'].includes(raw.storyAnswer)?raw.storyAnswer:'';
    next.compareSnapshot=raw.compareSnapshot?E.validateSnapshot(raw.compareSnapshot):null;
    next.rightLambda=validLambda(raw.rightLambda??.2);
    next.prediction=isCardId(raw.prediction)?raw.prediction:'';
    next.revealed=validBoolean(raw.revealed)&&!!next.prediction&&!!next.compareSnapshot;
    next.reportIndex=[0,1,2].includes(raw.reportIndex)?raw.reportIndex:0;
    if(raw.reports!==undefined){
      if(!Array.isArray(raw.reports)||raw.reports.length!==3)throw new Error('纠错任务记录应有三项。');
      next.reports=raw.reports.map((r,i)=>{
        if(!r || typeof r.note!=='string'||r.note.length>4000)throw new Error('纠错说明格式不正确。');
        return {answer:reportDefs[i].options.some(o=>o[0]===r.answer)?r.answer:'',note:r.note,checked:validBoolean(r.checked),repaired:validBoolean(r.repaired)&&i===1};
      });
    }
    next.reduced=validBoolean(raw.reduced);return next;
  }
  try { const s=localStorage.getItem(STORAGE);if(s)state=validateSession(JSON.parse(s)); } catch (_) { state=defaultState(); }
  if(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches)state.reduced=true;
  const requested=location.hash.slice(1);if(steps.includes(requested))state.step=requested;

  function renderIntro() {
    const answer=state.storyAnswer;
    return `<section class="hero fade-in"><div><div class="eyebrow">AN INTERACTIVE FIELD GUIDE / 5—8 MIN</div><h1>你的一次点击，<br><span class="blue">它看见了什么？</span></h1><p class="lead">点开一条视频，可能是喜欢，也可能只是为了找一段配乐。<br>走进一个规则透明的小世界，拆开推荐的过程，<br>看看一条记录能说明什么，又不能说明什么。</p><div class="hero-actions"><button class="primary" data-step="lab">进入排序实验 <span aria-hidden="true">↗</span></button><span class="quiet">不登录 · 不读取你的浏览记录</span></div></div><div class="hero-art" role="img" aria-label="看比赛和找配乐两种不同动机，都可以产生相同的一次篮球内容点击。模型只记录了点击。"><div class="art-caption">ONE ACTION. MORE THAN ONE REASON.</div><div class="art-tops"><div class="intent-card"><span class="intent-orb">↗</span><h3>“想看看这场比赛”</h3><p>动机 A / 对篮球感兴趣</p></div><div class="intent-card"><span class="intent-orb">♫</span><h3>“这段配乐叫什么”</h3><p>动机 B / 正在找一首歌</p></div></div><svg class="branch-lines" viewBox="0 0 450 80" aria-hidden="true"><path d="M113 0V24Q113 40 129 40H209Q225 40 225 56V79M337 0V24Q337 40 321 40H241Q225 40 225 56" fill="none" stroke="#92a28c" stroke-width="1.5"/><circle cx="225" cy="70" r="4" fill="#3457df"/></svg><div class="click-object"><div class="ball">◉</div><div><b>校园篮球集锦</b><small>相同卡片 ID · 相同点击事件</small></div></div><p class="art-result">两种理由，留下一样的记录。</p><div style="text-align:center;margin-top:15px"><span class="tiny-tag">模拟情境 / 不推断真实心理</span></div></div></section><section class="intro-bottom"><div><div class="overline">BEFORE YOU BEGIN</div><h2>仅凭这次点击，能分清动机吗？</h2><p class="quiet">先作一次判断，再把过程拆开。</p></div><div><div class="choice-group"><button class="choice ${answer==='same'?'selected':''}" data-action="story-answer" data-value="same"><b>不能，它看到了同一条记录</b>还需要其他信息才能区分原因。</button><button class="choice ${answer==='mind'?'selected':''}" data-action="story-answer" data-value="mind"><b>能，点击已经说明真实喜欢</b>算法应该能知道我的想法。</button></div>${answer?`<div class="feedback ${answer==='mind'?'error':''}">${answer==='same'?'对。':'再想一步：'}这个模型只收到卡片 ID 与点击。不同理由产生相同事件时，它会作出相同更新；分数不是读心术。你可以在下一步亲手验证。</div>`:''}</div></section>`;
  }

  function interestBars(counts) { const total=Object.values(counts).reduce((a,b)=>a+b,0);return D.topics.map(t=>`<div class="interest-row"><div class="row"><span>${esc(t.label)}</span><span class="count-label">${counts[t.id]} / ${total} · ${percent(counts[t.id]/total)}</span></div><div class="interest-track"><div style="width:${counts[t.id]/total*100}%;background:${t.color}"></div></div></div>`).join(''); }
  function renderLab() {
    const r=replay(),selected=r.ranked.find(c=>c.id===state.selected)||r.ranked[0];
    return `${pageHead('02','把排名，拆开看。','选一张卡查看算分单；记录一次点击，观察兴趣值、分数与排名的变化。所有内容与数值均为教学模拟。',`<button class="secondary" data-action="lab-reset">重置实验 ↺</button>`)}<div class="workspace fade-in"><aside class="panel control-panel"><div><div class="panel-title"><h2>排序规则</h2><span class="overline">CONTROL</span></div><label for="lambda">兴趣在排序中占多大比重？</label><div class="lambda-output"><span>兴趣权重 λ</span><strong>${state.lambda.toFixed(2)}</strong></div><input id="lambda" type="range" min="0" max="100" value="${Math.round(state.lambda*100)}" aria-label="兴趣权重"><div class="range-ends"><span>更看重热度 / 新鲜度</span><span>更看重兴趣</span></div><p class="mini-note" style="margin-top:12px">热度与新鲜度平分剩余权重。这里的“兴趣”是点击计数，不是你的真实偏好。</p></div><div class="divider"></div><div><div class="panel-title"><h3>当前兴趣值</h3><span class="count-label">已点击 ${state.events.length} 次</span></div>${interestBars(r.counts)}</div><div class="stat-row"><div><b>${percent(r.metrics.coverage)}</b><span>前六张主题覆盖率</span></div><div><b>${percent(r.metrics.maxShare)}</b><span>最大主题占比</span></div></div></aside><section class="panel feed-panel" aria-label="模拟推荐内容"><div class="panel-title"><h2>你的模拟信息流</h2><span class="overline">TOP 06 / 24</span></div><div class="feed-list">${r.ranked.slice(0,6).map(c=>`<article class="feed-card ${c.id===selected.id?'active':''}"><span class="rank">${String(c.rank).padStart(2,'0')}</span>${topicArt(c)}<div class="card-copy"><button data-action="select-card" data-id="${c.id}" aria-label="查看${esc(c.title)}的算分单">${esc(c.title)}</button><p>${esc(c.summary)}</p><span class="meta">${esc(topics[c.topic].label)} · p ${c.p.toFixed(2)} / f ${c.f.toFixed(2)}</span></div><div class="card-right"><span class="card-score">${fmt(c.score)}</span><button class="click-button" data-action="click-card" data-id="${c.id}" aria-label="记录点击：${esc(c.title)}">记录点击 +</button></div></article>`).join('')}</div><div class="feed-bottom"><span>按完整分数排序，同分按 ID</span><button class="text-button" data-action="all-cards">查看全部 24 张 ↗</button></div></section><aside class="panel explain-panel" aria-label="所选内容的算分单"><div><div class="panel-title"><span class="overline">WHY THIS ORDER</span><span class="tag">第 ${selected.rank} 名</span></div>${pill(selected.topic)}<h3>${esc(selected.title)}</h3><span class="count-label">${selected.id}</span><div class="score-hero"><b>${fmt(selected.score)}</b><small>排序分，不是概率</small><div class="score-stack"><i style="width:${selected.score?selected.interestPart/selected.score*100:0}%"></i><i style="width:${selected.score?selected.otherPart/selected.score*100:0}%"></i></div></div></div><div><div class="formula-row"><span><i class="legend-dot"></i>兴趣贡献</span><b>${state.lambda.toFixed(2)} × ${fmt(selected.interest)} = ${fmt(selected.interestPart)}</b></div><div class="formula-row"><span><i class="legend-dot alt"></i>其他贡献</span><b>${(1-state.lambda).toFixed(2)} × ${fmt((selected.p+selected.f)/2)} = ${fmt(selected.otherPart)}</b></div><div class="formula-box">S = λ × R + (1−λ) × (p+f)/2<br>${fmt(selected.interestPart)} + ${fmt(selected.otherPart)} = ${fmt(selected.score)}</div><p class="mini-note" style="margin-top:12px">点击某一主题，计数加 2，再除以总计数。未点击不等于不喜欢；卡片不会因点击被移出内容池。</p><button class="text-button" data-action="click-card" data-id="${selected.id}">点击这张卡，再算一次 →</button></div></aside></div><div class="timeline"><span>操作记录</span>${state.events.length?state.events.slice(-8).map((ev,i)=>`<span class="event-chip">${state.events.length-Math.min(8,state.events.length)+i+1}. ${esc(topics[ev.topic].label)} +2</span>`).join(''):'<span class="quiet">还没有点击。所有主题都从计数 1 开始。</span>'}${state.events.length>8?'<span>… 仅显示最近 8 次</span>':''}</div><div class="bottom-nav"><span class="quiet">这些指标只描述当前列表结构。它们可以增减，不能据此判断现实中的长期影响。</span><button class="primary" data-action="capture-and-compare">保存快照，进入对照 <span>→</span></button></div>`;
  }

  function getComparison() { if(!state.compareSnapshot)state.compareSnapshot=E.makeSnapshot({events:state.events,lambda:state.lambda});return {a:E.restoreSnapshot(state.compareSnapshot),b:E.restoreSnapshot(state.compareSnapshot,{lambda:state.rightLambda})}; }
  function rails(r) { return r.ranked.slice(0,6).map(c=>`<div class="rail"><span class="rank">${String(c.rank).padStart(2,'0')}</span><span class="rail-name">${esc(c.title)}<small>${esc(topics[c.topic].label)}</small></span><span class="rail-bar" aria-hidden="true"><i style="width:${c.score*100}%"></i></span><span class="rail-score">${fmt(c.score)}</span></div>`).join(''); }
  function branchPanel(r,label,code,isB=false,reveal=true) { return `<section class="panel branch ${isB?'branch-b':'branch-a'}"><div class="branch-top"><div><div class="overline">${code}</div><h2>${label}</h2></div><span class="weight-badge">λ = ${r.lambda.toFixed(2)}</span></div>${reveal?`${rails(r)}<div class="stat-row"><div><b>${percent(r.metrics.coverage)}</b><span>主题覆盖率</span></div><div><b>${percent(r.metrics.maxShare)}</b><span>最大主题占比</span></div></div>`:'<div class="unrevealed"><div><b>先预测，再揭开结果。</b><span class="quiet">哪张内容会成为右侧第一名？</span></div></div>'}</section>`; }
  function renderCompare() {
    const {a,b}=getComparison(),same=a.lambda===b.lambda;
    return `${pageHead('03','换一个条件，看另一种结果。','两条排序轨道从同一快照出发。内容、起点、点击历史完全相同，这次只改变兴趣权重。',`<button class="secondary" data-action="recapture">重新捕获当前实验 ↺</button>`)}<div class="panel compare-toolbar"><div class="snapshot-info"><span class="snapshot-icon">▣</span><div><strong>已锁定 ${a.events.length} 次点击</strong><p>同一内容池 / 同一历史 / 相同 K=6</p></div></div><div><div class="lambda-output"><label for="right-lambda">只改右侧兴趣权重</label><strong>${state.rightLambda.toFixed(2)}</strong></div><input id="right-lambda" aria-label="右侧兴趣权重" type="range" min="0" max="100" value="${Math.round(state.rightLambda*100)}"></div><div class="prediction"><label for="prediction" class="quiet">预测右侧第一名</label><select id="prediction"><option value="">请选择一张内容</option>${D.cards.map(c=>`<option value="${c.id}" ${state.prediction===c.id?'selected':''}>${esc(c.title)}</option>`).join('')}</select><button class="primary" data-action="reveal" ${!state.prediction?'disabled':''}>揭开结果 ↗</button></div></div><div class="comparison fade-in">${branchPanel(a,'保留原规则','BRANCH A / BASELINE')}${branchPanel(b,'只改变兴趣权重','BRANCH B / ONE CHANGE',true,state.revealed)}</div>${state.revealed?`<div class="feedback">${state.prediction===b.ranked[0].id?'你预测对了。':'这次的第一名是“'+esc(b.ranked[0].title)+'”。'}${same?'两侧权重也相同，所以输出完全一致。':'两侧点击计数相同，权重不同。名次可能改变，也可能不变；请从分数组成解释结果。'}不要把不同规则下的总分高低，当作推荐质量优劣。</div>`:''}<div class="comparison-note">控制记录：内容版本 ${esc(D.version)} · 左右均从快照独立重算 · ${a.events.length} 个相同事件 · ${same?'当前权重相同，是一次复现检查':'唯一设置差异：λ'}。更改右侧参数后，预测会重新开始。</div><div class="bottom-nav"><button class="text-button" data-step="lab">← 返回拆开排序</button><button class="primary" data-step="reports">去修正一份错误报告 →</button></div>`;
  }

  function repairState(repaired) {
    const baseline=[eventFor('sports-01'),eventFor('music-01')];
    const mixed=[...baseline,eventFor('music-02'),eventFor('music-02')];
    return {a:replay(baseline,.6),b:replay(repaired?baseline:mixed,.2)};
  }
  function passed(i,r=state.reports[i]) { return r.checked&&r.answer===reportDefs[i].correct&&r.note.trim().length>=12&&(i!==1||r.repaired); }
  function renderReports() {
    const i=state.reportIndex,def=reportDefs[i],r=state.reports[i],repair=repairState(r.repaired);
    return `${pageHead('04','让结论，配得上证据。','以音乐类点击为例，仍使用相同六主题内容池。诊断错误、修正条件，再用自己的话说清楚证据的边界。')}<div class="report-layout fade-in"><aside class="report-menu" aria-label="选择纠错任务">${reportDefs.map((d,j)=>`<button class="${i===j?'active':''}" data-action="report-tab" data-index="${j}" aria-current="${i===j?'true':'false'}"><span>CASE 0${j+1} ${passed(j)?' / 已完成':''}</span>${d.title}</button>`).join('')}</aside><section class="panel report-content"><div class="report-heading"><h2>${def.title}</h2><span class="tag">${def.label}</span></div><div class="bad-report"><div class="overline">一份待审查的模拟报告</div><blockquote>${def.quote}</blockquote></div><h3 class="report-question">${def.question}</h3><div class="radio-options">${def.options.map(o=>`<label class="radio-option"><input type="radio" name="report-answer" value="${o[0]}" ${r.answer===o[0]?'checked':''}><span>${o[1]}</span></label>`).join('')}</div>${i===1?`<div class="repair-box"><div class="overline">REPAIR THE EXPERIMENT / 实际修正并重算</div><div class="repair-states"><div><b>左侧 λ=0.60 · ${repair.a.events.length} 次点击</b><code>${esc(repair.a.events.map(ev=>ev.cardId).join(' → '))}</code><span>重算第一名：${esc(repair.a.ranked[0].title)} / ${fmt(repair.a.ranked[0].score)}</span></div><div><b>右侧 λ=0.20 · ${repair.b.events.length} 次点击</b><code>${esc(repair.b.events.map(ev=>ev.cardId).join(' → '))}</code><span>重算第一名：${esc(repair.b.ranked[0].title)} / ${fmt(repair.b.ranked[0].score)}</span></div></div><button class="secondary" data-action="repair" ${r.repaired?'disabled':''}>${r.repaired?'✓ 已恢复同一历史，并重新计算':'恢复右侧相同历史，重新计算 ↺'}</button><p class="mini-note" style="margin:10px 0 0">${r.repaired?'两侧实际从相同事件重算，仅 λ 不同。修复证据随小结导出。':'右侧比左侧多了两次音乐点击。仅选中正确答案还不够，需要实际修复。'}</p></div>`:''}<label class="rewrite-label" for="report-note">用自己的话改写结论<small>按“观察到什么 → 能支持什么 → 还不能支持什么”来写，至少 12 个字符。这里是练习，文字质量需要人工判断。</small></label><textarea id="report-note" maxlength="4000" placeholder="${def.placeholder}">${esc(r.note)}</textarea><div class="report-check"><small>仅检查诊断选择、操作与是否填写；不把字数达标当成理解证明。</small><button class="primary" data-action="check-report">检查这份修正 →</button></div>${r.checked?`<div class="feedback ${passed(i)?'':'error'}">${r.answer!==def.correct?'诊断还需要调整。':i===1&&!r.repaired?'请先恢复相同历史并重算。':r.note.trim().length<12?'请补充一段自己的结论（至少 12 个字符）。':'已完成这项练习的操作要求。'} ${def.feedback}</div>`:''}</section></div><div class="bottom-nav"><span class="quiet">纠错任务属于练习，不是标准化测评，也不能代替真实用户试用。</span><button class="primary" data-action="next-report">${i<2?'下一份报告 →':'整理我的实验小结 →'}</button></div>`;
  }

  function renderSummary() {
    const n=state.reports.filter((r,i)=>passed(i,r)).length,r=replay();
    return `${pageHead('05','带走一次实验，也带走一个问题。','记录可以复现，结论也应该能追溯。导出包含规则、输入、操作、结果和你的修正，不收集真实浏览历史。')}<div class="summary-grid fade-in"><section class="panel summary-title" style="padding:29px"><div class="eyebrow">YOUR LEARNING TRACE</div><h2>这次，你看清了哪些边界？</h2><p>以下记录描述操作进度，不能自动证明学习效果。</p><ul class="learning-list"><li><div>行为记录 ≠ 真实动机<small>模型只按收到的输入计算。</small></div><span class="${state.storyAnswer==='same'?'done-marker':'pending-marker'}">${state.storyAnswer==='same'?'✓ 已作判断':'待回看'}</span></li><li><div>排序分可以逐项解释<small>本次记录 ${state.events.length} 次点击，当前 λ=${state.lambda.toFixed(2)}。</small></div><span class="${state.events.length?'done-marker':'pending-marker'}">${state.events.length?'✓ 已操作':'尚未点击'}</span></li><li><div>有效对照只改一个条件<small>相同快照、相同历史，独立重算。</small></div><span class="${state.revealed?'done-marker':'pending-marker'}">${state.revealed?'✓ 已比较':'尚未揭开'}</span></li><li><div>纠错后，再限定结论<small>${n}/3 项操作要求已完成；自由文本请自行审阅。</small></div><span class="${n===3?'done-marker':'pending-marker'}">${n===3?'✓ 已完成':'继续练习'}</span></li></ul><div class="summary-note">推荐能帮助我们发现内容，但一次点击只是有限的线索。下次看到一份“算法影响”的结论，不妨先问：<b>记录了什么？改变了什么？证据支持到哪一步？</b></div></section><aside class="panel export-panel"><div class="overline">TAKE THE EVIDENCE WITH YOU</div><h2>保存你的实验凭据。</h2><p>JSON 文件保留可重算的快照与纠错记录，Markdown 小结方便阅读。只存入你选择的本地文件夹，不上传服务器。</p><button class="primary" data-action="export-json">导出实验记录 .json <span>↓</span></button><button class="secondary" data-action="export-md">导出可读小结 .md <span>↓</span></button><button class="text-button" style="color:#cbdba9;margin-top:15px" data-action="import">导入记录，核验并回放 ↗</button><div class="export-meta">APP ${VERSION} / DATA ${esc(D.version)}<br>MODEL ${esc(E.modelVersion)}<br>当前兴趣计数：${Object.values(r.counts).join(' · ')}<br>无账号 · 无跟踪 · 无外部 API</div></aside></div><div class="bottom-nav"><button class="text-button" data-step="reports">← 返回报告纠错</button><button class="danger-button" data-action="reset-all">清空本机练习，重新开始</button></div>`;
  }

  function render(keepFocus=false) {
    const focused=keepFocus?document.activeElement?.id:null;
    document.querySelectorAll('[data-step]').forEach(b=>{if(b.closest('nav')){b.setAttribute('aria-current',b.dataset.step===state.step?'step':'false');}});
    main.innerHTML=({intro:renderIntro,lab:renderLab,compare:renderCompare,reports:renderReports,summary:renderSummary}[state.step])();
    document.body.classList.toggle('reduced-motion',state.reduced);
    const mt=document.getElementById('motion-toggle');mt.setAttribute('aria-pressed',String(state.reduced));mt.textContent=state.reduced?'动态已减少':'减少动态';
    if(focused)document.getElementById(focused)?.focus({preventScroll:true});save();
  }
  function go(step) { if(!steps.includes(step))return;state.step=step;history.replaceState(null,'','#'+step);render();main.focus({preventScroll:true});window.scrollTo({top:0,behavior:state.reduced?'instant':'smooth'}); }
  function showModal(title,body) { const m=document.getElementById('modal');document.getElementById('modal-content').innerHTML=`<h2 id="modal-title">${title}</h2>${body}`;if(!m.open)m.showModal(); }
  function closeModal() { document.getElementById('modal').close(); }
  function about() { showModal('看见过程，也看见局限。',`<div class="about-copy"><p>《看见排序》是一件推荐系统入门交互科普作品。受众为非计算机专业大学生，核心练习是报告诊断、修正条件重算与限定结论。</p><h3>规则全部公开</h3><p>六类兴趣计数从 1 开始；点击一类加 2，再除以总计数。<code>S = λR + (1−λ)(p+f)/2</code>。p 是模拟热度，f 是模拟新鲜度，不随点击或真实时间变化；按完整分数降序，同分按内容 ID。</p><p>前 6 张“主题覆盖率”为不同主题数/6；“最大主题占比”为最多主题卡数/6。它们只描述列表，不是偏见或信息茧房指数。这里没有模型训练，不接入真实平台，也不识别真实心理。</p><h3>参考与已有工作</h3><ul><li><a href="https://developers.google.com/machine-learning/recommendation/overview" target="_blank" rel="noopener">Google：推荐系统背景课程</a></li><li><a href="https://arxiv.org/html/2409.06916v1" target="_blank" rel="noopener">Ahn 等，2024：交互反事实探索</a></li><li><a href="https://repository.isls.org/handle/1/11129" target="_blank" rel="noopener">Gong 等，2024：BeeTrap 学习项目</a>（仅可读搜索收录的摘要与片段，未阅读全文）</li><li><a href="https://brytalearn.com/explore/recommendation-systems" target="_blank" rel="noopener">Brytalearn：推荐系统交互教学页</a>（可读搜索收录正文）</li></ul><p>双分支、行为与动机区分、算分解释等已有先例，不声称首创。教学参数、24 张内容卡和纠错脚本为本项目设计，尚需学生审核与真实试用。</p><h3>数据与创作状态</h3><p>核心页面不发出网络请求。浏览器可能保存本机练习进度；你可清空或自行导出。不会自动上传作答。外部资料仅在主动点击链接时访问。</p><p>构建版本 ${VERSION} · 2026-10-15。学校与参赛人员由用户确认：贵州财经大学；田洪友、李科成、王臻、李屹。当前原型由 AI 协助制作；学生分工、实质贡献、内容审核和真实试用均需实际完成并记录，不能由本页面证明。</p></div>`); }
  function allCards() { const r=replay();showModal('完整模拟内容池',`<p class="quiet">24 张原创模拟内容，每主题 4 张。点击只改变对应主题计数，卡片仍保留。数值不代表真实平台。</p><div class="all-cards">${r.ranked.map(c=>`<div class="all-card">${topicArt(c)}<div><b>${esc(c.title)}</b><p>${esc(c.summary)}</p><p>${esc(c.id)} · p=${c.p} / f=${c.f} · S=${fmt(c.score)}</p></div><button class="click-button" data-action="click-card" data-id="${c.id}">记录点击 +</button></div>`).join('')}</div>`); }
  function exportDocument() {
    const current=E.makeSnapshot({events:state.events,lambda:state.lambda});
    const repair=repairState(state.reports[1].repaired),before=repairState(false);
    return {kind:'see-order-experiment',schemaVersion:1,exportedAt:new Date().toISOString(),notice:'模拟教学练习记录，非真实平台数据或学习效果证明。自由文本不作自动质量评价。',session:sessionData(),current,comparison:state.compareSnapshot?{baseline:state.compareSnapshot,right:E.makeSnapshot({initialCounts:state.compareSnapshot.initialCounts,events:state.compareSnapshot.events,lambda:state.rightLambda})}:null,repairEvidence:{repaired:state.reports[1].repaired,before:{left:E.makeSnapshot({events:before.a.events,lambda:.6}),right:E.makeSnapshot({events:before.b.events,lambda:.2})},left:E.makeSnapshot({events:repair.a.events,lambda:.6}),right:E.makeSnapshot({events:repair.b.events,lambda:.2})},progress:{reportOperationRequirements:state.reports.map((r,i)=>passed(i,r))}};
  }
  function download(content,name,type) { const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);toast('文件已交给浏览器保存，请选择 E 盘项目目录。'); }
  function exportMd() { const r=replay();let text=`# 我的《看见排序》实验小结\n\n这是模拟教学练习，不是学习效果证明。\n\n应用 ${VERSION} / 数据 ${D.version} / 模型 ${E.modelVersion}\n\n## 当前实验\n\n点击次数：${state.events.length}；兴趣权重：${state.lambda}\n\n| 名次 | 内容 | 主题 | 分数 |\n| --- | --- | --- | --- |\n${r.ranked.slice(0,6).map(c=>`| ${c.rank} | ${c.title} | ${topics[c.topic].label} | ${fmt(c.score)} |`).join('\n')}\n\n## 我修正的报告\n\n`;state.reports.forEach((r,i)=>{text+=`### ${i+1}. ${reportDefs[i].title}\n\n操作要求${passed(i,r)?'已完成':'尚未完成'}；自由文本质量需人工审阅。\n\n${r.note||'（尚未填写）'}\n\n`;});text+='## 证据边界\n\n记录与真实意图不同；单变量对照只能支持本模型的相应比较；一次模拟不能推断现实所有人的长期效果。\n\n如需复算，另导出 JSON，并保留同版本程序。\n';download(text,'看见排序-我的实验小结.md','text/markdown;charset=utf-8'); }

  document.addEventListener('click', event => {
    const stepButton=event.target.closest('[data-step]');
    if(stepButton){go(stepButton.dataset.step);return;}
    const el=event.target.closest('[data-action]');if(!el)return;
    const action=el.dataset.action;
    try {
      if(action==='about')return about();
      if(action==='close-modal')return closeModal();
      if(action==='reduce-motion'){state.reduced=!state.reduced;render(true);return;}
      if(action==='story-answer'){state.storyAnswer=el.dataset.value;render();say('判断反馈已显示。');return;}
      if(action==='select-card'){state.selected=el.dataset.id;render();return;}
      if(action==='click-card'){
        if(state.events.length>=1000)return toast('已达到 1000 次操作上限。请导出后重置。');
        const id=el.dataset.id;if(!isCardId(id))return;
        const before=replay().ranked.find(c=>c.id===id);state.events.push(eventFor(id));state.selected=id;
        const after=replay().ranked.find(c=>c.id===id);if(document.getElementById('modal').open)closeModal();
        render();say(`${byId[id].title}：${topics[byId[id].topic].label}计数加2，从第${before.rank}名到第${after.rank}名，分数${fmt(after.score)}。`);return;
      }
      if(action==='lab-reset'){state.events=[];state.lambda=.6;state.selected='sports-01';render();toast('当前排序实验已恢复初始状态。已锁定的独立对照快照保持原样。');return;}
      if(action==='all-cards')return allCards();
      if(action==='capture-and-compare'||action==='recapture'){
        state.compareSnapshot=E.makeSnapshot({events:state.events,lambda:state.lambda});state.revealed=false;state.prediction='';
        state.rightLambda=state.lambda===.2?.6:.2;go('compare');if(action==='recapture')toast('已从排序实验重新捕获快照。');return;
      }
      if(action==='reveal'){if(!state.prediction)return;state.revealed=true;render();say('右侧结果已揭开，可比较两条排序轨道。');return;}
      if(action==='report-tab'){state.reportIndex=Number(el.dataset.index);render();return;}
      if(action==='repair'){state.reports[1].repaired=true;state.reports[1].checked=false;render();toast('已删除右侧额外事件，用相同历史重算。结果已更新。');return;}
      if(action==='check-report'){state.reports[state.reportIndex].checked=true;render();say(passed(state.reportIndex)?'已完成本项操作要求，自由文本仍需人工审阅。':'请根据反馈继续修正。');return;}
      if(action==='next-report'){if(state.reportIndex<2){state.reportIndex++;render();main.focus({preventScroll:true});window.scrollTo(0,0);}else go('summary');return;}
      if(action==='export-json')return download(JSON.stringify(exportDocument(),null,2),'看见排序-实验记录.json','application/json');
      if(action==='export-md')return exportMd();
      if(action==='import'){document.getElementById('import-file').click();return;}
      if(action==='reset-all'){showModal('清空这台设备上的练习？','<p class="about-copy">这将清空本页面保存的点击、快照和报告修正。已导出的本地文件不会被删除。需要保留时，请先导出。</p><button class="primary" data-action="confirm-reset">确认清空并重新开始</button>');return;}
      if(action==='confirm-reset'){closeModal();state=defaultState();go('intro');toast('本机练习已清空。');return;}
    } catch(err){toast('操作未完成：'+err.message);console.error(err);}
  });
  document.addEventListener('input',event=>{
    if(event.target.id==='report-note'){state.reports[state.reportIndex].note=event.target.value;state.reports[state.reportIndex].checked=false;save();}
  });
  document.addEventListener('change',event=>{
    const el=event.target;
    if(el.id==='lambda'){state.lambda=Number(el.value)/100;render(true);say('已使用新权重重新计算。');}
    if(el.id==='right-lambda'){state.rightLambda=Number(el.value)/100;state.revealed=false;state.prediction='';render(true);say('已改变右侧权重，请重新预测。');}
    if(el.id==='prediction'){state.prediction=el.value;state.revealed=false;render(true);}
    if(el.name==='report-answer'){state.reports[state.reportIndex].answer=el.value;state.reports[state.reportIndex].checked=false;render();}
  });
  document.getElementById('import-file').addEventListener('change',async event=>{
    const file=event.target.files[0];if(!file)return;
    try{
      if(file.size>2*1024*1024)throw new Error('文件超过 2MB，拒绝加载。');
      const raw=JSON.parse(await file.text());
      if(raw.kind!=='see-order-experiment'||raw.schemaVersion!==1)throw new Error('不是本应用支持的实验记录。');
      const next=validateSession(raw.session);
      if(next.compareSnapshot ? !raw.comparison : raw.comparison!==null)throw new Error('对照快照与导出证据必须成对存在。');
      if(!raw.repairEvidence||!raw.repairEvidence.before)throw new Error('记录缺少纠错修复前后的完整证据。');
      const canonical=E.makeSnapshot({events:next.events,lambda:next.lambda});
      if(!raw.current)throw new Error('记录缺少当前实验快照。');
      const imported=E.validateSnapshot(raw.current);
      if(JSON.stringify(canonical)!==JSON.stringify(imported))throw new Error('动作记录与当前快照不一致。');
      if(raw.comparison){const expected=next.compareSnapshot;if(!expected)throw new Error('对照记录与会话不一致。');const left=E.validateSnapshot(raw.comparison.baseline);const right=E.validateSnapshot(raw.comparison.right);if(JSON.stringify(left)!==JSON.stringify(expected)||JSON.stringify(right)!==JSON.stringify(E.makeSnapshot({initialCounts:expected.initialCounts,events:expected.events,lambda:next.rightLambda})))throw new Error('对照证据与会话不一致。');}
      if(raw.repairEvidence){const rs=repairState(next.reports[1].repaired);const l=E.validateSnapshot(raw.repairEvidence.left),r=E.validateSnapshot(raw.repairEvidence.right);if(raw.repairEvidence.repaired!==next.reports[1].repaired||JSON.stringify(l)!==JSON.stringify(E.makeSnapshot({events:rs.a.events,lambda:.6}))||JSON.stringify(r)!==JSON.stringify(E.makeSnapshot({events:rs.b.events,lambda:.2})))throw new Error('纠错重算证据与会话不一致。');}
      if(raw.repairEvidence?.before){const before=repairState(false);const l=E.validateSnapshot(raw.repairEvidence.before.left),r=E.validateSnapshot(raw.repairEvidence.before.right);if(JSON.stringify(l)!==JSON.stringify(E.makeSnapshot({events:before.a.events,lambda:.6}))||JSON.stringify(r)!==JSON.stringify(E.makeSnapshot({events:before.b.events,lambda:.2})))throw new Error('纠错前态证据与固定任务不一致。');}
      state=next;go('summary');toast('记录已核验并重算。你可返回实验继续操作。');
    }catch(err){toast('导入失败：'+err.message);}finally{event.target.value='';}
  });
  document.getElementById('modal').addEventListener('click',event=>{if(event.target===event.currentTarget){const r=event.currentTarget.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)closeModal();}});
  window.addEventListener('hashchange',()=>{const s=location.hash.slice(1);if(steps.includes(s)&&s!==state.step)go(s);});
  render();
})();
