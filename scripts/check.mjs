import { join } from 'node:path';
import { root,py,run } from './common.mjs';
run(py,['-m','ruff','check','backend']);
run(py,['-m','mypy','backend']);
run(py,['-m','pytest','-q']);
for(const cmd of ['lint','typecheck','test','build']) run('pnpm',['run',cmd],join(root,'web'));
