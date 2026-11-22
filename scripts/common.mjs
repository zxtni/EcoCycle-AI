import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { resolve,dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
export const root=resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const win=process.platform==='win32';
export const py=resolve(root,win?'.venv/Scripts/python.exe':'.venv/bin/python');
export const uv=existsSync(resolve(root,'.tools/uv.exe'))?resolve(root,'.tools/uv.exe'):'uv';
export function run(cmd,args,cwd=root) {
 const r=spawnSync(cmd,args,{cwd,stdio:'inherit',shell:win && cmd==='pnpm',env:{...process.env,NEXT_TELEMETRY_DISABLED:'1'}});
 if(r.error) console.error(r.error.message);
 if(r.status!==0) process.exit(r.status??1);
}
