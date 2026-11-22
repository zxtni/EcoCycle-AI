import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { root,py,uv,run } from './common.mjs';
if(!existsSync(py)) run(uv,['venv','--python','3.12','.venv']);
run(uv,['pip','install','--python',py,'-r','backend/requirements.txt']);
run('pnpm',['install',existsSync(join(root,'web/pnpm-lock.yaml'))?'--frozen-lockfile':'--no-frozen-lockfile'],join(root,'web'));
run(py,['-m','alembic','upgrade','head']);
if(existsSync(join(root,'backend/seed.py'))) run(py,['-m','backend.seed']);
