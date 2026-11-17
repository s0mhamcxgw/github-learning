(function(root){
'use strict';
const VERSION='1.0.0';
const FACTS=Object.freeze({height:625,span:1420,length:2890,strands:217,wires:91,wireMM:5.7,stabilityMM:2,opened:'2025-09-28'});
function clamp(n,a,b){return Math.min(b,Math.max(a,Number.isFinite(+n)?+n:a));}
function mix(a,b,t){return a+(b-a)*t;}
function smooth(t){t=clamp(t,0,1);return t*t*(3-2*t);}
function seeded(seed){let a=seed>>>0;return()=>{a+=0x6D2B79F5;let t=a;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296;};}
function hexPack(radius){const out=[];for(let q=-radius;q<=radius;q++)for(let r=Math.max(-radius,-q-radius);r<=Math.min(radius,-q+radius);r++){out.push({q,r,x:Math.sqrt(3)*(q+r/2),y:1.5*r});}return out.sort((a,b)=>Math.hypot(a.x,a.y)-Math.hypot(b.x,b.y)||a.q-b.q||a.r-b.r);}
function cableY(x){const a=Math.abs(x);return a<=710?655+175*(x/710)**2:mix(830,637,clamp((a-710)/540,0,1));}
function terrainY(x,z){const river=Math.sin(z/600)*65+Math.sin(z/1300)*35,dx=Math.abs(x-river),wall=510*(1-Math.exp(-Math.pow(dx/360,3))),mount=Math.max(0,dx-650)/1500;return Math.max(-8,wall+Math.sin(x/220+z/330)*30*Math.min(1,dx/250)+Math.sin(z/640-x/170)*20*Math.min(1,dx/200)+Math.min(1,mount)*125-20);}
const STAGES=[
 {date:'2022.01.18',name:'从岩层出发',tag:'开工',body:'基础与锚碇把力量传给岩层。模型用四组基座概括下部结构，不复刻真实基础尺寸。',sources:['S03'],need:'foundation'},
 {date:'2023.04.21',name:'两岸立起山门',tag:'主塔',body:'6号主塔封顶。桥塔是主缆的支点；两岸塔柱的形态，在这里被转译成简洁的山门。',sources:['S03'],need:'tower'},
 {date:'2024.01.10',name:'先让人走过去',tag:'猫道',body:'猫道第一根承重索跨越峡谷。猫道是施工便道，与通车后的桥面是不同结构。',sources:['S03','S02'],need:'catwalk'},
 {date:'2024.07.30',name:'把千丝合成主缆',tag:'主缆',body:'主缆架设完成。基准索股的定位与持续观测，是这个阶段的重要细节。',sources:['S03','S02'],need:'cable'},
 {date:'2025.01.17',name:'桥面在云中相遇',tag:'合龙',body:'大桥合龙。拖动吊装进度查看钢桁梁逐段连成整体；画面顺序为叙事示意，并非实际吊装施工组织。',sources:['S03'],need:'deck'},
 {date:'2025.09.28',name:'从此，两岸相连',tag:'通车',body:'建成通车。尺度最终回到生活：一座桥的意义，既在高度，也在抵达。',sources:['S01','S03'],need:'open'}
];
const COMPONENTS={deck:{name:'桥面与钢桁梁',text:'车辆先把重量传给桥面与加劲梁。桁梁把局部荷载沿结构分散，再由吊索传向主缆。'},hanger:{name:'吊索',text:'一根根竖向吊索把桥面与主缆连接起来，主要承受拉力。画面线条加粗是为了让传力关系可见。'},cable:{name:'主缆',text:'主缆沿曲线把桥面荷载传向主塔与两端锚碇。217根索股汇成一根主缆，细小钢丝在这里协同工作。'},tower:{name:'主塔',text:'主塔支撑主缆，把作用传到基础。主缆两侧的作用共同形成塔顶的受力关系。'},anchor:{name:'锚碇',text:'主缆两端锚固在锚碇中。锚碇与地基一起抵抗主缆拉力，是画面中不应被忽略的部分。'}};
function forcePath(x){x=clamp(x,-650,650);const t=(x+710)/1420;return{left:1-t,right:t,points:[[x,626,0],[x,cableY(x),-20],[-710,830,-20],[-1250,637,-20]]};}
function canInstall(stage,part){const index=['foundation','tower','catwalk','cable','deck','open'].indexOf(part);if(index<0)return{ok:false,reason:'未知构件。'};if(index<=stage)return{ok:false,reason:'这个阶段已经在模型中。可回退时间轴重新观察。'};if(index!==stage+1)return{ok:false,reason:part==='deck'?'桥面还需要吊索与主缆形成承托关系。先完成前面的阶段。':'先完成时间轴上紧接着的阶段，才能理解后续构造如何出现。'};return{ok:true,index};}
function initial(){return{version:VERSION,chapter:0,metric:'height',view:'aerial',component:'cable',load:0,explode:0,stage:0,lift:1,scale:0,strand:0,offset:6,day:1,precisionAnswer:null,route:'before',routeProgress:0,note:'',visited:[0],found:[],checks:{},reduced:false,sound:false};}
function cleanState(input){if(!input||typeof input!=='object'||Array.isArray(input))throw Error('记录必须是对象。');const s=initial();s.chapter=Math.round(clamp(input.chapter,0,6));s.metric=['height','span','length'].includes(input.metric)?input.metric:'height';s.view=['aerial','deck','river'].includes(input.view)?input.view:'aerial';s.component=Object.hasOwn(COMPONENTS,input.component)?input.component:'cable';s.load=clamp(input.load,-650,650);s.explode=clamp(input.explode,0,1);s.stage=Math.round(clamp(input.stage,0,5));s.lift=clamp(input.lift,0,1);s.scale=Math.round(clamp(input.scale,0,4));s.strand=Math.round(clamp(input.strand,0,216));s.offset=clamp(input.offset,-8,8);s.day=Math.round(clamp(input.day,1,7));s.precisionAnswer=['week','instant','whole'].includes(input.precisionAnswer)?input.precisionAnswer:null;s.route=input.route==='after'?'after':'before';s.routeProgress=clamp(input.routeProgress,0,1);s.note=String(input.note||'').slice(0,240);s.visited=Array.isArray(input.visited)?[...new Set(input.visited.filter(x=>Number.isInteger(x)&&x>=0&&x<=6))]:[0];s.found=Array.isArray(input.found)?[...new Set(input.found.filter(x=>['height','span','length','deck','hanger','cable','tower','anchor','217','91','5.7','2','route'].includes(x)))]:[];s.checks={};if(input.checks&&typeof input.checks==='object')for(const k of ['scale','force','build','precision','route'])s.checks[k]=input.checks[k]===true;s.reduced=input.reduced===true;s.sound=false;return s;}
function scaleRatio(m,mm){return m*1000/mm;}
function observation(day){const series=[6.3,4.4,3.1,2.4,1.8,1.4,1.2];return series[Math.round(clamp(day,1,7))-1];}
function report(s){s=cleanState(s);return '# 云上之尺 · 我的观察手记\n\n这是体验者的本地操作记录，不是工程观测或学习效果测评。\n\n'+`- 看过章节：${s.visited.length} / 7\n- 阅读标记：${s.found.length}\n- 尺度：桥面至水面 ${FACTS.height} m；主跨 ${FACTS.span} m；全长 ${FACTS.length} m\n- 一根主缆：${FACTS.strands} 根索股；每股 ${FACTS.wires} 根钢丝；钢丝直径 ${FACTS.wireMM} mm\n- 毫米细节：报道中的基准索股同一位置，相对高差稳定在 2 mm 以内，持续观测一周。\n- 当前示意偏移：${s.offset.toFixed(1)} mm；不代表大桥实时状态。\n- 判断选择：${s.precisionAnswer==='week'?'已识别持续观测与单次读数的区别':s.precisionAnswer?'尚需修正':'未作答'}\n\n`+'## 我的理解\n\n'+(s.note||'尚未填写。')+'\n\n## 资料入口\n\n'+(root.BridgeContent?root.BridgeContent.sources.map(x=>`- ${x.id} ${x.title}：${x.url}`).join('\n'):'见作品内“资料与制作”。')+'\n\n模型、构件尺寸与地貌为原创叙事示意；仅标明的公开数值按来源表达。传力为定性关系，不是有限元或设计计算。\n';}
const api={VERSION,FACTS,STAGES,COMPONENTS,clamp,mix,smooth,seeded,hexPack,cableY,terrainY,forcePath,canInstall,initial,cleanState,scaleRatio,observation,report};
root.BridgeEngine=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
