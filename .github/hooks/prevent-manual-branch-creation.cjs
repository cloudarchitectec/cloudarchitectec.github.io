const fs = require('node:fs');

const event = JSON.parse(fs.readFileSync(0, 'utf8'));
const toolName = event.toolName ?? event.tool_name;
const toolArgs = event.toolArgs ?? event.tool_input;

function collectStrings(value) {
  if (typeof value === 'string') return [value];
  if (Array.isArray(value)) return value.flatMap(collectStrings);
  if (value && typeof value === 'object') {
    return Object.values(value).flatMap(collectStrings);
  }
  return [];
}

const isTerminalTool = typeof toolName === 'string'
  && /(terminal|bash|shell|command)/i.test(toolName);
const commandText = isTerminalTool ? collectStrings(toolArgs).join('\n') : '';
const gitCommand = String.raw`(?:^|[;&|]\s*)(?:[\w.-]+=\S+\s+)*(?:command\s+)?git(?:\s+-C\s+\S+|\s+--(?:git-dir|work-tree)=\S+)*\s+`;
const createsBranch = new RegExp(
  `${gitCommand}(?:switch\\s+(?:-[cC]\\b|--create(?:=|\\s)|--orphan\\b)|checkout\\s+(?:-[bB]\\b|--branch(?:=|\\s)|--orphan\\b)|branch\\s+(?:-[cC]\\b|--copy\\b|--create\\b|[^-\\s])|worktree\\s+add\\b[^\\n]*(?:\\s-[bB]\\s|\\s--branch(?:=|\\s)))`,
  'im'
);

if (createsBranch.test(commandText)) {
  process.stdout.write(JSON.stringify({
    permissionDecision: 'deny',
    permissionDecisionReason:
      'Do not create branches manually in this repository. Stay on the current vX.Y.Z release branch. After its PR is merged, create the next release branch with .local/start-next-version-branch.sh --pr <merged-PR-URL> --next-branch vX.Y.Z.'
  }));
} else {
  process.stdout.write('{}');
}
