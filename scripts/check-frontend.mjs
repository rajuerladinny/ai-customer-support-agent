import {readFile} from 'node:fs/promises';
const html=await readFile(new URL('../worker/index.html',import.meta.url),'utf8');const script=html.match(/<script>([\s\S]*?)<\/script>/);if(!script)throw new Error('Frontend script missing');new Function(script[1]);console.log('Frontend script syntax OK');
