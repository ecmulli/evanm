import { execSync } from 'child_process';

const run = (cmd) => {
  console.log(`> ${cmd}`);
  const out = execSync(cmd, { cwd: '/vercel/share/v0-project', encoding: 'utf8' });
  if (out) console.log(out);
  return out;
};

run('git config user.email "v0@vercel.com"');
run('git config user.name "v0"');
run('git add -A');
run('git commit -m "redesign: clean productivity UI with liquid glass floating add bar"');
run('git push origin redesign-productivity-interface');

console.log('Done — changes pushed to redesign-productivity-interface.');
