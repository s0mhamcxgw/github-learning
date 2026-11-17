'use strict';
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const E = require('../site/dist/engine.js'), scenarios = require('../site/dist/scenarios.js');
const records = [];
function check(name, fn) { fn(); records.push({name,status:'passed'}); }
for (const s of scenarios) {
  check(s.id+' 输入和全部可行排程的独立条件复核',()=>{
    assert.deepEqual(E.validate(s),[]);
    const before = JSON.stringify(s), a = E.analyze(s);
    assert.equal(a.baseline.status,'feasible'); assert.deepEqual(E.verify(s,a.baseline,{includeNew:false}),[]);
    if(a.incoming.status==='feasible')assert.deepEqual(E.verify(s,a.incoming),[]);
    for(const p of a.plans)if(p.result.status==='feasible')assert.deepEqual(E.verify(p.scenario,p.result),[]);
    for(const i of E.stress(s).items)if(i.result.status==='feasible')assert.deepEqual(E.verify(i.scenario,i.result),[]);
    assert.equal(JSON.stringify(s),before);
  });
}
check('陶艺连续工时：总人工六小时仍不能同时兑现，极小冲突为杯和香插',()=>{
  const s=scenarios[0],a=E.analyze(s);
  assert.equal(s.tasks.reduce((n,t)=>n+t.duration*(t.needs.maker||0),0),12);
  assert.equal(a.incoming.status,'infeasible');assert.equal(a.incoming.proof.kind,'compulsory-overlap');assert.equal(a.incoming.proof.items[0].resource,'maker');assert.equal(a.incoming.proof.items[0].start,0);assert.equal(a.incoming.proof.items[0].end,4);
  assert.deepEqual(a.conflict.orders,['cup','incense']);assert.equal(a.conflict.minimal,true);
  assert.equal(a.plans.filter(p=>p.frontier).length,3);
});
check('共享印台：委派人工也不增加设备容量',()=>{
  const s=E.transform(scenarios[1],{collaborate:true});
  assert.equal(s.tasks.find(t=>t.id==='card-print').needs.press,1);
  const r=E.solve(s);assert.equal(r.status,'infeasible');assert.equal(r.proof.items[0].resource,'press');
});
check('皮具原估计可行，人工工时扰动后不可行',()=>{
  const r=E.stress(scenarios[2]);assert.equal(r.items[0].result.status,'feasible');assert.equal(r.items[1].result.status,'infeasible');assert.equal(r.pass+r.fail+r.unknown,r.total);
});
check('搜索预算零时不能谎报不可行',()=>{assert.equal(E.solve(scenarios[2],{nodeLimit:0}).status,'unknown');});
check('验证器发现伪造排程和重复工序',()=>{const s=scenarios[2],r=E.solve(s);r.schedule[0].end++;assert.ok(E.verify(s,r).length);r.schedule.push(r.schedule[1]);assert.ok(E.verify(s,r).length);});
check('错误、循环、非整数、恶意标识和缺失对象被拒绝',()=>{
  const changes=[s=>s.tasks[0]=null,s=>s.resources[0]=null,s=>s.tasks[0].after=[s.tasks[1].id],s=>s.tasks[0].duration=1.5,s=>s.tasks[0].needs={ghost:1},s=>s.tasks[0].id='__proto__',s=>s.orders[0].release=NaN,s=>s.openLunch='true',s=>s.orders[0].due=1000,s=>s.orders[0].isNew=true,s=>s.note={toString:'bad'},s=>s.category=[],s=>s.id={}];
  for(const change of changes){const s=E.clone(scenarios[0]);change(s);assert.ok(E.validate(s).length);assert.equal(E.solve(s).status,'invalid');}
});
check('校验码与对象键顺序无关且输入改变时改变',()=>{assert.equal(E.fingerprint({b:2,a:1}),E.fingerprint({a:1,b:2}));assert.notEqual(E.fingerprint({a:1}),E.fingerprint({a:2}));});
check('相对时间跨午夜、跨日编码正确',()=>{assert.equal(E.formatTime(30),'第2天 00:00');assert.equal(E.formatTime(48),'第2天 09:00');assert.equal(E.formatTime(54),'第2天 12:00');});
// 独立小型基准：固定工序次序枚举所有开始时间，不复用求解器日历、剪枝或变量选择。
function oracle(s){
  const tasks=s.tasks, placed=[],used=Array.from({length:2},()=>Array(16).fill(0));
  const open=(t)=>t>=0&&t<16&&(t<6||t>=10);
  function visit(k){if(k===tasks.length)return true;const t=tasks[k],o=s.orders.find(o=>o.id===t.order);
    for(let start=Math.max(o.release||0,t.release||0);start+t.duration<=o.due;start++){
      if(t.after.some(id=>placed.find(p=>p.id===id).end>start))continue;
      let ok=true;for(let x=start;x<start+t.duration;x++)for(const [r,n] of Object.entries(t.needs)){const ri=r==='maker'?0:1;if(!open(x)||used[ri][x]+n>s.resources[ri].capacity)ok=false;}
      if(!ok)continue;for(let x=start;x<start+t.duration;x++)for(const[r,n]of Object.entries(t.needs))used[r==='maker'?0:1][x]+=n;
      placed.push({id:t.id,end:start+t.duration});if(visit(k+1))return true;placed.pop();
      for(let x=start;x<start+t.duration;x++)for(const[r,n]of Object.entries(t.needs))used[r==='maker'?0:1][x]-=n;
    }return false;
  }return visit(0);
}
let seed=20261015;function rand(n){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed%n;}
let feasible=0,infeasible=0;
check('160 个确定性随机小项目与独立完整枚举基准一致',()=>{
  for(let i=0;i<160;i++){
    const s={name:'独立枚举基准',days:1,slotMinutes:30,resources:[{id:'maker',label:'人工',capacity:1+rand(2),calendar:'work'},{id:'tool',label:'设备',capacity:1,calendar:'work'}],orders:[{id:'old',label:'已有',due:[4,6,12,16][rand(4)],release:rand(3)},{id:'new',label:'新单',due:[5,6,13,16][rand(4)],release:rand(3),isNew:true}],tasks:[]};
    for(let k=0;k<4;k++){const order=k<2?'old':'new';s.tasks.push({id:'t'+k,label:'工序'+k,order,duration:1+rand(4),needs:rand(2)?{maker:1,tool:1}:{maker:1},after:k%2&&rand(2)?['t'+(k-1)]:[]});}
    const expected=oracle(s),actual=E.solve(s,{nodeLimit:300000});assert.notEqual(actual.status,'unknown');assert.equal(actual.status==='feasible',expected,JSON.stringify(s));if(expected){feasible++;assert.deepEqual(E.verify(s,actual),[]);}else infeasible++;
  }
});
const result={date:new Date().toISOString(),engine:E.VERSION,checks:records,oracle:{cases:160,feasible,infeasible,seed:20261015},note:'软件验证；不是用户试用、商户数据或学生操作记录。'};
fs.writeFileSync(path.join(__dirname,'引擎核查结果.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
