import test from 'node:test';import assert from 'node:assert/strict';import {handle} from '../worker/backend.mjs';
const post=(question,documents=[])=>handle(new Request('https://example.test/api/answer',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({question,documents})}));
test('finds sample order and handles unknown order',async()=>{let r=await handle(new Request('https://example.test/api/order?id=ns-1042'));assert.equal((await r.json()).status,'Delivered');r=await handle(new Request('https://example.test/api/order?id=NS-9999'));assert.equal(r.status,404)});
test('answers with attributed policy excerpt',async()=>{let r=await post('damaged headphones replacement');let j=await r.json();assert.match(j.source,/Returns/);assert.match(j.answer,/Damaged|Replacement/);assert.equal(j.mode,'extractive')});
test('returns unknown instead of inventing facts',async()=>{let j=await(await post('Can speakers connect wirelessly?')).json();assert.equal(j.source,null);assert.equal(j.mode,'no_match')});
test('searches an uploaded text document with a citation',async()=>{let j=await(await post('warranty coverage', [{name:'warranty.txt',text:'Warranty coverage lasts two years.'}])).json();assert.equal(j.source,'warranty.txt');assert.match(j.answer,/two years/)});
test('rejects invalid requests',async()=>{assert.equal((await post('')).status,400)});
