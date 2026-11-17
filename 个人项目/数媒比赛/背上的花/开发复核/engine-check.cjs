'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const E=require('../site/dist/engine.js');const checks=[];
function test(name,f){f();checks.push({name,status:'passed'});}
test('24个唯一布片与非退化几何',()=>{assert.equal(E.pieces.length,24);assert.equal(new Set(E.pieces.map(p=>p.id)).size,24);for(const p of E.pieces){const [ax,ay,bx,by,cx,cy]=p.points;assert.ok(Math.abs((bx-ax)*(cy-ay)-(by-ay)*(cx-ax))>1);assert.ok(p.centroid.every(Number.isFinite));}});
test('放置幂等、撤销与恢复',()=>{const s=E.initial();E.place(s,'p07');E.place(s,'p07');assert.deepEqual(s.placed,['p07']);E.undo(s);assert.equal(s.selected,'p07');assert.equal(s.placed.length,0);E.finish(s);assert.equal(s.placed.length,24);E.validate(s);});
test('层级查看不破坏已完成片数',()=>{const s=E.initial();E.finish(s);s.reveal=7;assert.equal(E.visible(s).length,7);assert.equal(s.placed.length,24);s.reveal=24;assert.equal(E.visible(s).length,24);});
test('非法重复、未知布片与不合法状态被拒绝',()=>{const s=E.initial();assert.throws(()=>E.place(s,'unknown'));assert.throws(()=>E.validate({...s,placed:['p01','p01']}));assert.throws(()=>E.validate({...s,fold:NaN}));assert.throws(()=>E.validate({...s,composition:'fake'}));assert.throws(()=>E.validate({...s,message:'x'.repeat(49)}));});
test('800次确定性操作维护唯一性与状态约束',()=>{const s=E.initial(),rand=E.seeded(1018);for(let n=0;n<800;n++){if(rand()<.3)E.undo(s);else E.place(s,E.pieces[Math.floor(rand()*24)].id);E.validate(s);assert.equal(s.placed.length,new Set(s.placed).size);assert.ok(s.placed.length<=24);}});
const output=path.resolve(__dirname,'../验收材料/状态核查.json');fs.writeFileSync(output,JSON.stringify({createdAt:new Date().toISOString(),checks,scope:'有限程序状态与几何核查，非文化审校、真实参与者或效果证明'},null,2));console.log('PASS '+checks.length+' groups');
