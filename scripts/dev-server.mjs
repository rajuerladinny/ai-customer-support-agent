import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {handle} from '../worker/backend.mjs';
import {createStore} from './state-store.mjs';
import {stateApi} from './state-api.mjs';
const port=Number(process.env.PORT || 3000),store=createStore(resolve(process.env.RESOLVE_STATE_FILE || 'data/state.json'));
const routes=new Set(['/api/state','/api/approval','/api/messages','/api/reset']);
createServer(async(req,res)=>{try{const url=new URL(req.url,`http://localhost:${port}`);if(url.pathname==='/'&&req.method==='GET'){res.writeHead(200,{'content-type':'text/html; charset=utf-8'});res.end(await readFile(new URL('../worker/index.html',import.meta.url)));return}if(!url.pathname.startsWith('/api/')){res.writeHead(404);res.end('Not found');return}if(req.method==='POST'&&req.headers.origin&&req.headers.origin!==`http://localhost:${port}`&&req.headers.origin!==`http://127.0.0.1:${port}`){res.writeHead(403);res.end('Origin not allowed');return}let chunks=[],size=0;for await(const chunk of req){size+=chunk.length;if(size>100_000){res.writeHead(413);res.end('Request too large');return}chunks.push(chunk)}const init={method:req.method,headers:req.headers};if(!['GET','HEAD'].includes(req.method))init.body=Buffer.concat(chunks);const request=new Request(url,init);const response=routes.has(url.pathname)?await stateApi(request,store):await handle(request);res.writeHead(response.status,{...Object.fromEntries(response.headers),'cache-control':'no-store'});res.end(Buffer.from(await response.arrayBuffer()))}catch{res.writeHead(500);res.end('Internal server error')}}).listen(port,'127.0.0.1',()=>console.log(`Resolve AI: http://localhost:${port}`));
