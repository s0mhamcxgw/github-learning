(function(root){
  'use strict';
  const round=x=>Math.round(x*1e10)/1e10;
  function validateRows(rows){
    if(!Array.isArray(rows)||rows.length<2||rows.length>24)throw new Error('需要2—24行数据（1—12个分层，每层A/B各一行）。');
    const seen=new Set(),layers=new Map();
    const normalized=rows.map((r,i)=>{
      if(!r||typeof r!=='object')throw new Error(`第${i+1}行不是有效记录。`);
      if(typeof r.stratum!=='string'||!r.stratum.trim()||r.stratum.trim().length>40)throw new Error(`第${i+1}行分层名称须为1—40个字符。`);
      const s=r.stratum.trim();
      if(!['A','B'].includes(r.group))throw new Error(`第${i+1}行group只能为A或B。`);
      for(const key of ['success','total'])if(!Number.isSafeInteger(r[key])||r[key]<0||r[key]>10000000)throw new Error(`第${i+1}行${key}须为0—10000000的整数。`);
      if(r.total===0)throw new Error(`第${i+1}行分母不能为0。请补充数据，不能将未知比例当成0。`);
      if(r.success>r.total)throw new Error(`第${i+1}行成功数不能超过总数。`);
      const key=JSON.stringify([s,r.group]);if(seen.has(key))throw new Error(`分层“${s}”的${r.group}组重复。`);seen.add(key);
      if(!layers.has(s))layers.set(s,new Set());layers.get(s).add(r.group);
      return {stratum:s,group:r.group,success:r.success,total:r.total};
    });
    for(const [s,groups]of layers)if(groups.size!==2)throw new Error(`分层“${s}”缺少A组或B组，不能进行共同分层比较。`);
    return normalized;
  }
  function analyse(input,rawWeights){
    const rows=validateRows(input),names=[...new Set(rows.map(r=>r.stratum))];
    const groups={A:{success:0,total:0},B:{success:0,total:0}};
    rows.forEach(r=>{groups[r.group].success+=r.success;groups[r.group].total+=r.total;});
    for(const g of Object.values(groups))g.rate=g.success/g.total;
    const n=groups.A.total+groups.B.total;
    const layers=names.map(name=>{const a=rows.find(r=>r.stratum===name&&r.group==='A'),b=rows.find(r=>r.stratum===name&&r.group==='B');return {name,a:{...a,rate:a.success/a.total,share:a.total/groups.A.total},b:{...b,rate:b.success/b.total,share:b.total/groups.B.total},pooled:(a.total+b.total)/n,diff:a.success/a.total-b.success/b.total};});
    const weights=rawWeights===undefined?layers.map(l=>l.pooled):rawWeights;
    if(!Array.isArray(weights)||weights.length!==layers.length||weights.some(w=>typeof w!=='number'||!Number.isFinite(w)||w<0||w>10000000)||!weights.some(w=>w>0))throw new Error('参考权重需要每层一个非负有限数，且不能全部为0。');
    const sum=weights.reduce((a,b)=>a+b,0),w=weights.map(x=>x/sum);
    const standard={A:0,B:0};layers.forEach((l,i)=>{l.weight=w[i];l.contributionA=w[i]*l.a.rate;l.contributionB=w[i]*l.b.rate;l.gapContribution=w[i]*l.diff;standard.A+=l.contributionA;standard.B+=l.contributionB;});
    const rawDiff=groups.A.rate-groups.B.rate,stdDiff=standard.A-standard.B;
    // Symmetric Kitagawa decomposition, exact: raw gap = within + composition.
    const within=layers.reduce((acc,l)=>acc+(l.a.share+l.b.share)/2*l.diff,0);
    const composition=layers.reduce((acc,l)=>acc+(l.a.rate+l.b.rate)/2*(l.a.share-l.b.share),0);
    const eps=1e-10;
    const strictReversal=(rawDiff>eps&&layers.every(l=>l.diff<-eps))||(rawDiff<-eps&&layers.every(l=>l.diff>eps));
    const directionChange=(rawDiff>eps&&stdDiff<-eps)||(rawDiff<-eps&&stdDiff>eps);
    return {rows,groups,layers,n,rawDiff,stdDiff,standard,weights:w,strictReversal,directionChange,decomposition:{within,composition,residual:rawDiff-within-composition}};
  }
  function parseCSV(text){
    if(typeof text!=='string'||text.length>200000)throw new Error('CSV文本为空或超过200KB。');
    // RFC4180-style quoted cells, including escaped quotes; no eval or HTML execution.
    const records=[];let row=[],cell='',quoted=false,closed=false;
    text=text.replace(/^\uFEFF/,'').replace(/\r\n/g,'\n').replace(/\r/g,'\n');
    for(let i=0;i<text.length;i++){
      const c=text[i];
      if(quoted){if(c==='"'){if(text[i+1]==='"'){cell+='"';i++;}else{quoted=false;closed=true;}}else cell+=c;}
      else if(c==='"'){if(cell.trim()||closed)throw new Error('CSV引号位置不正确。');quoted=true;cell='';}
      else if(c===','||c==='\n'){row.push(cell.trim());cell='';closed=false;if(c==='\n'){if(row.some(v=>v!==''))records.push(row);row=[];}}
      else{if(closed&&!/\s/.test(c))throw new Error('CSV引号后含多余字符。');cell+=c;}
    }
    if(quoted)throw new Error('CSV引号未闭合。');row.push(cell.trim());if(row.some(v=>v!==''))records.push(row);
    if(records.length<2||records[0].join(',')!=='stratum,group,success,total')throw new Error('首行须为stratum,group,success,total，且至少包含一行数据。');
    const rows=records.slice(1).map((r,i)=>{if(r.length!==4)throw new Error(`CSV第${i+2}行须为4列。`);if(!/^\d+$/.test(r[2])||!/^\d+$/.test(r[3]))throw new Error(`CSV第${i+2}行计数须为非负整数。`);return {stratum:r[0],group:r[1],success:Number(r[2]),total:Number(r[3])};});
    return validateRows(rows);
  }
  function csv(rows){validateRows(rows);const q=s=>'"'+String(s).replaceAll('"','""')+'"';return '\uFEFFstratum,group,success,total\r\n'+rows.map(r=>[q(r.stratum),r.group,r.success,r.total].join(',')).join('\r\n');}
  function fingerprint(rows){let hash=2166136261;const s=JSON.stringify(validateRows(rows));for(let i=0;i<s.length;i++){hash^=s.charCodeAt(i);hash=Math.imul(hash,16777619);}return 'fnv1a-'+(hash>>>0).toString(16).padStart(8,'0');}
  root.DenominatorEngine={version:'1.0.0',validateRows,analyse,parseCSV,csv,fingerprint,round};
  if(typeof module!=='undefined')module.exports=root.DenominatorEngine;
})(typeof globalThis!=='undefined'?globalThis:this);
