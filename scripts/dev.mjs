import { spawn } from 'node:child_process';
import { join } from 'node:path';
import { root,py,win } from './common.mjs';
const api=spawn(py,['-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000'],{cwd:root,stdio:'inherit'});
const web=spawn('pnpm',['run','dev'],{cwd:join(root,'web'),stdio:'inherit',shell:win});
let exiting=false;
function stop(code=0){if(exiting)return;exiting=true;api.kill();web.kill();process.exit(code);}
api.on('exit',c=>stop(c??1));web.on('exit',c=>stop(c??1));process.on('SIGINT',()=>stop());process.on('SIGTERM',()=>stop());
