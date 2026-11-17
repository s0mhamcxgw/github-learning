(function(root){
'use strict';
const palette={red:'#a74943',rust:'#b56c4d',cream:'#d6c7a6',blue:'#596b77',green:'#828568',dark:'#263d42',gold:'#b99a69'};
const triangles=[
 ['p01',[-112,-178,-26,-150,-77,-106],'blue'],['p02',[112,-178,26,-150,77,-106],'blue'],
 ['p03',[-129,-153,-77,-106,-122,-73],'red'],['p04',[129,-153,77,-106,122,-73],'red'],
 ['p05',[-77,-106,-26,-150,0,-86],'cream'],['p06',[77,-106,26,-150,0,-86],'cream'],
 ['p07',[70,-67,0,-114,0,-35],'red'],['p08',[-70,-67,0,-114,0,-35],'red'],
 ['p09',[-126,-63,-70,-67,-92,-19],'green'],['p10',[126,-63,70,-67,92,-19],'green'],
 ['p11',[-64,-13,0,-35,0,27],'gold'],['p12',[64,-13,0,-35,0,27],'gold'],
 ['p13',[0,37,-51,82,0,126],'blue'],['p14',[0,37,51,82,0,126],'red'],
 ['p15',[-52,82,-108,47,-97,115],'cream'],['p16',[52,82,108,47,97,115],'cream'],
 ['p17',[-97,115,-52,82,0,126],'green'],['p18',[97,115,52,82,0,126],'green'],
 ['p19',[-66,144,0,117,0,182],'red'],['p20',[66,144,0,117,0,182],'red'],
 ['p21',[-66,144,-118,113,-103,180],'blue'],['p22',[66,144,118,113,103,180],'blue'],
 ['p23',[-50,190,0,169,0,222],'gold'],['p24',[50,190,0,169,0,222],'gold']
];
const pieces=triangles.map(([id,points,color],index)=>({id,index,points,color,fill:palette[color],name: '第'+String(index+1).padStart(2,'0')+'片',centroid:[(points[0]+points[2]+points[4])/3,(points[1]+points[3]+points[5])/3]}));
function initial(){return {version:'1.0.0',chapter:0,composition:'design',scale:'whole',fold:0,placed:[],selected:'p01',reveal:24,wish:'陪伴',message:'愿每一次出发，都有人惦念。',sound:false,reduced:false,angle:0};}
function validate(s){if(!s||typeof s!=='object')throw Error('状态无效');if(!Number.isInteger(s.chapter)||s.chapter<0||s.chapter>5)throw Error('章节无效');if(!['design','own'].includes(s.composition))throw Error('构成模式无效');if(!['macro','pattern','whole'].includes(s.scale))throw Error('尺度无效');if(!Number.isFinite(s.fold)||s.fold<0||s.fold>1)throw Error('折叠状态无效');if(!Array.isArray(s.placed)||s.placed.some(id=>!pieces.some(p=>p.id===id))||new Set(s.placed).size!==s.placed.length)throw Error('布片状态无效');if(!['安稳','陪伴','出发'].includes(s.wish))throw Error('心意无效');if(typeof s.message!=='string'||s.message.length>48)throw Error('短句最多48字');return s;}
function place(s,id){validate(s);const p=pieces.find(p=>p.id===id);if(!p)throw Error('布片不存在');if(!s.placed.includes(id))s.placed.push(id);s.selected=pieces.find(p=>!s.placed.includes(p.id))?.id||'p07';s.reveal=24;return s;}
function undo(s){validate(s);const id=s.placed.pop();if(id)s.selected=id;s.reveal=24;return s;}
function finish(s){s.placed=pieces.map(p=>p.id);s.reveal=24;s.selected='p07';return validate(s);}
function visible(s){return s.placed.filter(id=>pieces.find(p=>p.id===id).index<s.reveal);}
function mix(a,b,t){return a+(b-a)*t;}
function seeded(seed){let n=seed>>>0;return ()=>{n=(Math.imul(n,1664525)+1013904223)>>>0;return n/4294967296;};}
root.FlowerEngine={version:'1.0.0',palette,pieces,initial,validate,place,undo,finish,visible,mix,seeded};
if(typeof module!=='undefined')module.exports=root.FlowerEngine;
})(typeof globalThis!=='undefined'?globalThis:this);
