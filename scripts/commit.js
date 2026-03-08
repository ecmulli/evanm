import { execSync } from 'child_process';

const run = (cmd) => {
  console.log(`> ${cmd}`);
  const out = execSync(cmd, { cwd: '/vercel/share/v0-project', encoding: 'utf8' });
  if (out) console.log(out);
  return out;
};

run('git add -A');
run('git commit -m "redesign: clean productivity UI with liquid glass floating add bar"');
run('git push origin redesign-productivity-interface');
console.log('Done!');
