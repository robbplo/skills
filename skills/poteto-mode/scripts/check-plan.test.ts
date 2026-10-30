import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { expect, test } from "bun:test";

const checker = join(import.meta.dir, "check-plan.mjs");
const rule =
	"Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.";

const validPlan = `# Demo

## How to read this
One box is one unit of work and names the evidence. Check a box only when its evidence exists. See playbooks/.
${rule}

## Program checklist
### Arm the program
### Spawn owners
### PR mechanics
### Verdict and merge
### Boot recipe
\`git show origin/main:\` /loop 1h status message

## PR 1
**Depends on.** None.
**Files.**
- [ ] Do the thing.
**Build.**
- [ ] Do the thing.
**You see.**
- [ ] Do the thing.
**Verify, unit.** ${rule}
- [ ] Check the thing.
**Verify, live.** ${rule} Ten lanes on \`example-model\` at the PR head
${Array.from({ length: 10 }, (_, i) => `- [ ] Lane ${i + 1}. Save \`lane-${i + 1}.png\`. Pass when evidence exists.`).join("\n")}
**Verify, perf.** ${rule}
- [ ] Metric. Recorded.
- [ ] Probe. Recorded.
- [ ] Baseline. Recorded.
- [ ] Rule. Recorded.
**Review gate.** None.
**Merge.**
- [ ] Merge when approved.

## Close the program
Close.

## Appendix Prototype evidence
Recorded.
`;

const runPlan = (example: string, expectedExit: number, plan = validPlan, args: string[] = []) => {
	const directory = mkdtempSync(join(tmpdir(), "check-plan-test-"));
	const file = join(directory, "plan.md");
	writeFileSync(file, plan + example);
	try {
		const result = spawnSync("node", [checker, ...args, file], { encoding: "utf8" });
		expect(result.status).toBe(expectedExit);
		return result;
	} finally {
		rmSync(directory, { recursive: true, force: true });
	}
};

const codexPlan = validPlan.replace(
	"`git show origin/main:` /loop 1h status message",
	"- [ ] Read installed playbooks. Read `/home/user/.codex/pstack-local/skills/poteto-mode/playbooks/autopilot-stack.md` at every audit.\n" +
		"- [ ] Wake mechanism. Poll during the active session every 30 seconds until the program finishes or the operator stops it. Report each tracked change in a status message.",
);

test("accepts a Codex plan with installed sources and in-session polling", () => {
	runPlan("", 0, codexPlan, ["--host", "codex"]);
});

test("accepts a Claude Code plan with installed sources and in-session polling", () => {
	runPlan("", 0, codexPlan, ["--host", "claude"]);
});

test("rejects Cursor-only instructions in Claude Code plans", () => {
	for (const command of ["/loop 1h", "git show origin/main:pstack/skills/swarm/SKILL.md"]) {
		const plan = codexPlan.replace("### Arm the program", `### Arm the program\n- [ ] Run \`${command}\`.`);
		const result = runPlan("", 1, plan, ["--host", "claude"]);
		expect(result.stderr).toContain("unsupported in Claude Code");
	}
});

test("requires each Codex program instruction", () => {
	for (const marker of ["Read installed playbooks.", "Wake mechanism.", "status message"]) {
		const result = runPlan("", 1, codexPlan.replace(marker, "Removed instruction."), ["--host", "codex"]);
		expect(result.stderr).toContain(`Program checklist lacks "${marker}"`);
	}
});

test("rejects Cursor loop and repository-local protocol commands in Codex plans", () => {
	for (const command of ["/loop 1h", "git show origin/main:pstack/skills/swarm/SKILL.md"]) {
		const plan = codexPlan.replace("### Arm the program", `### Arm the program\n- [ ] Run \`${command}\`.`);
		const result = runPlan("", 1, plan, ["--host", "codex"]);
		expect(result.stderr).toContain("unsupported in Codex");
	}
});

test("keeps explicit Cursor host validation", () => {
	runPlan("", 0, validPlan, ["--host", "cursor"]);
	const result = runPlan("", 1, codexPlan, ["--host", "cursor"]);
	expect(result.stderr).toContain('Program checklist lacks "/loop 1h"');
});

test("rejects missing, unknown, and repeated hosts before reading the plan", () => {
	for (const args of [["--host", "unknown"], ["--host"], ["--host", "codex", "--host", "cursor"]]) {
		const result = runPlan("", 2, codexPlan, args);
		expect(result.stderr).toContain("Usage:");
	}
	const missingHost = spawnSync("node", [checker, "/nonexistent/plan.md", "--host"], { encoding: "utf8" });
	expect(missingHost.status).toBe(2);
	expect(missingHost.stderr).toContain("Usage:");
});

test("accepts ordinary, indented, and longer closing fences", () => {
	for (const indent of ["", " ", "  ", "   "])
		runPlan(`${indent}\`\`\`markdown\n## Example only\n${indent}\`\`\`\n`, 0);
	runPlan("```markdown\n## Example only\n````\n", 0);
});

test("accepts nested backticks and tilde info strings", () => {
	runPlan("````markdown\n```markdown\n## Example only\n```\n````\n", 0);
	runPlan("~~~markdown `info`\n## Example only\n ~~~\n", 0);
});

test("keeps mismatched, shorter, and suffixed closers inside the fence", () => {
	runPlan("````markdown\n~~~\n## Example only\n````\n", 0);
	runPlan("````markdown\n```\n## Example only\n````\n", 0);
	runPlan("````markdown\n``` info\n## Example only\n````\n", 0);
});

test("rejects headings and prose outside a proper close", () => {
	for (const suffix of ["  ", "\t"]) {
		const heading = runPlan(`\`\`\`markdown\n## Example only\n\`\`\`${suffix}\n## Example only\n`, 1);
		expect(heading.stderr).toContain('"## Example only" after Close the program is not an appendix');
	}

	const prose = runPlan("```markdown\nThis prose has a mid-sentence colon: inside code\n```\nThis prose has a mid-sentence colon: bad.\n", 1);
	expect(prose.stderr).toContain("mid-sentence colon");
});

test("rejects backtick info strings containing a backtick", () => {
	const result = runPlan("```markdown `invalid`\n## Example only\n```\n", 1);
	expect(result.stderr).toContain('"## Example only" after Close the program is not an appendix');
});

test("ignores prose punctuation inside matching multi-backtick code spans", () => {
	for (const count of [2, 3, 4]) {
		const delimiter = "`".repeat(count);
		runPlan(`Use ${delimiter}echo \`x\`: “quoted” — example${delimiter}.\n`, 0);
	}
});

test("checks prose following a multi-backtick span and unmatched delimiters", () => {
	const outside = runPlan("Use ``echo `x`: y``. Bad: prose.\n", 1);
	expect(outside.stderr).toContain("mid-sentence colon");
	const unmatched = runPlan("Use ``unclosed: bad` here.\n", 1);
	expect(unmatched.stderr).toContain("mid-sentence colon");
});
