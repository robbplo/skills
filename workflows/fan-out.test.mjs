import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./fan-out.js", import.meta.url), "utf8").replace("export const meta", "const meta");
const AsyncFunction = (async () => {}).constructor;
const body = new AsyncFunction("args", "agent", "parallel", "log", "phase", source);
const parallel = (thunks) => Promise.all(thunks.map((t) => t().catch(() => null)));

function run(args, agent) {
  const logs = [];
  return body(args, agent, parallel, (m) => logs.push(m), () => {}).then((out) => ({ ...out, logs }));
}

test("returns one report per brief and passes each brief's options", async () => {
  const calls = [];
  const out = await run(
    { briefs: [{ prompt: "a", label: "slice-a", model: "sonnet", isolation: "worktree" }, { prompt: "b" }] },
    async (prompt, opts) => (calls.push(opts), `did ${prompt}`),
  );
  assert.deepEqual(out.results, [{ label: "slice-a", report: "did a" }, { label: "worker-2", report: "did b" }]);
  assert.deepEqual(out.gaps, []);
  assert.deepEqual(calls[0], { label: "slice-a", phase: "Fan out", agentType: "general-purpose", model: "sonnet", isolation: "worktree" });
  assert.deepEqual(calls[1], { label: "worker-2", phase: "Fan out", agentType: "general-purpose" });
});

test("retries a dropout once, then records a gap", async () => {
  const tries = {};
  const out = await run({ briefs: [{ prompt: "flaky" }, { prompt: "dead" }] }, async (prompt) => {
    tries[prompt] = (tries[prompt] || 0) + 1;
    return prompt === "flaky" && tries[prompt] === 2 ? "ok" : null;
  });
  assert.deepEqual(tries, { flaky: 2, dead: 2 });
  assert.deepEqual(out.gaps, ["worker-2"]);
  assert.equal(out.results[0].report, "ok");
});

test("accepts stringified args and rejects a missing brief list", async () => {
  const out = await run(JSON.stringify({ briefs: [{ prompt: "a" }] }), async () => "x");
  assert.equal(out.results.length, 1);
  await assert.rejects(run({}, async () => "x"), /fan-out needs args/);
});
