import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const AsyncFunction = (async () => {}).constructor;
const parallel = (thunks) => Promise.all(thunks.map((t) => Promise.resolve().then(t).catch(() => null)));
const pipeline = (items, ...stages) =>
  Promise.all(items.map(async (item, index) => {
    let value = item;
    try {
      for (const stage of stages) value = await stage(value, item, index);
      return value;
    } catch {
      return null;
    }
  }));

function load(name) {
  const source = readFileSync(new URL(`./${name}.js`, import.meta.url), "utf8").replace("export const meta", "const meta");
  const body = new AsyncFunction("args", "agent", "parallel", "pipeline", "log", "phase", source);
  return async (args, agent) => {
    const calls = [];
    const out = await body(args, async (prompt, opts) => (calls.push({ prompt, opts }), agent(prompt, opts)), parallel, pipeline, () => {}, () => {});
    return { out, calls };
  };
}

const swarm = load("swarm-run");
const arena = load("arena-run");
const interrogate = load("interrogate-run");
const pass = (evidence = "ran it") => ({ status: "PASS", evidence, issues: [] });

test("swarm returns one result per brief and passes each brief's options", async () => {
  const { out, calls } = await swarm(
    { briefs: [{ prompt: "a", label: "slice-a", model: "sonnet", isolation: "worktree" }, { prompt: "b" }] },
    async () => pass(),
  );
  assert.deepEqual(out.results.map((r) => [r.label, r.status]), [["slice-a", "PASS"], ["worker-2", "PASS"]]);
  assert.deepEqual(out.gaps, []);
  assert.equal(calls[0].opts.model, "sonnet");
  assert.equal(calls[0].opts.isolation, "worktree");
  assert.equal("model" in calls[1].opts, false);
});

test("swarm respawns a dropout or a report that lacks a named SHA once, then records a gap", async () => {
  const tries = {};
  const { out } = await swarm(
    { briefs: [{ prompt: "flaky" }, { prompt: "dead" }, { prompt: "vague", mustRecord: ["abc123"] }, { prompt: "fixed", mustRecord: ["abc123"] }] },
    async (prompt) => {
      tries[prompt] = (tries[prompt] || 0) + 1;
      if (prompt === "dead") return null;
      if (prompt === "flaky") return tries[prompt] === 2 ? pass() : null;
      if (prompt === "fixed") return pass(tries[prompt] === 2 ? "at abc123" : "ran it");
      return pass();
    },
  );
  assert.deepEqual(tries, { flaky: 2, dead: 2, vague: 2, fixed: 2 });
  assert.deepEqual(out.results.map((r) => r.label), ["worker-1", "worker-4"]);
  assert.deepEqual(out.gaps, [{ label: "worker-2", reason: "no report" }, { label: "worker-3", reason: "did not record abc123" }]);
});

test("arena hides the rubric from candidates, isolates them, and judges the finished ones", async () => {
  const { out, calls } = await arena(
    { task: "build X", rubric: ["small API"], candidates: [{ label: "a", model: "opus" }, { label: "b" }, { label: "c", outputPath: "/tmp/c" }], judge: { model: "sonnet" } },
    async (prompt, opts) => {
      if (opts.label === "b") return null;
      if (opts.label === "cross-judge") return { scores: [], base: "a", rationale: "cleaner" };
      return { location: `/w/${opts.label}`, summary: "s", rationale: "r" };
    },
  );
  const [a, , c, judge] = calls;
  assert.equal(a.prompt.includes("small API"), false);
  assert.equal(a.opts.isolation, "worktree");
  assert.equal("isolation" in c.opts, false);
  assert.match(c.prompt, /under \/tmp\/c/);
  assert.equal(judge.opts.agentType, "Explore");
  assert.match(judge.prompt, /small API[\s\S]*- a: \/w\/a\n- c: \/w\/c/);
  assert.deepEqual(out.candidates.map((x) => x.label), ["a", "c"]);
  assert.deepEqual(out.dropouts, ["b"]);
  assert.equal(out.verdict.base, "a");
});

test("arena skips the judge when none is configured or one candidate remains", async () => {
  const ok = async () => ({ location: "/w", summary: "s", rationale: "r" });
  assert.equal((await arena({ task: "t", rubric: ["r"], candidates: [{}, {}] }, ok)).out.verdict, null);
  assert.equal((await arena({ task: "t", rubric: ["r"], candidates: [{}], judge: {} }, ok)).calls.length, 1);
});

test("interrogate keeps only findings a rerun reproduces against the intent", async () => {
  const finding = (title) => ({ title, command: `run ${title}`, output: "bad", expected: "good" });
  const { out, calls } = await interrogate(
    { scope: "the diff", intent: "sort is stable", ref: "abc123", patchPath: "/tmp/p.diff", adversaries: [{ label: "x", model: "opus" }, { label: "y" }, { label: "z" }] },
    async (prompt, opts) => {
      if (opts.phase === "Break") {
        if (opts.label === "z") throw new Error("died");
        return { worktree: `/w/${opts.label}`, findings: opts.label === "x" ? [finding("real"), finding("flake"), finding("offtopic")] : [] };
      }
      if (prompt.includes("Finding: real")) return { reproduced: true, breaksIntent: true, output: "bad", reason: "fails" };
      if (prompt.includes("Finding: flake")) return { reproduced: false, breaksIntent: true, output: "good", reason: "passes on rerun" };
      return { reproduced: true, breaksIntent: false, output: "bad", reason: "not about the intent" };
    },
  );
  const breaker = calls.find((c) => c.opts.label === "x");
  assert.match(breaker.prompt, /git checkout --detach abc123[\s\S]*git apply \/tmp\/p\.diff/);
  assert.equal(breaker.opts.isolation, "worktree");
  assert.match(calls.find((c) => c.opts.phase === "Verify").prompt, /Work in \/w\/x/);
  assert.deepEqual(out.findings.map((f) => [f.title, f.foundBy]), [["real", "x"]]);
  assert.deepEqual(out.dropped, [
    { label: "x", count: 2, findings: [{ title: "flake", reason: "passes on rerun" }, { title: "offtopic", reason: "not about the intent" }] },
    { label: "y", count: 0, findings: [] },
  ]);
  assert.deepEqual(out.gaps, ["z"]);
});

test("each workflow rejects malformed args and accepts a JSON string", async () => {
  await assert.rejects(swarm({}, async () => pass()), /swarm-run needs args/);
  await assert.rejects(arena({ task: "t", candidates: [{}] }, async () => null), /arena-run needs args/);
  await assert.rejects(interrogate({ scope: "s" }, async () => null), /interrogate-run needs args/);
  assert.equal((await swarm(JSON.stringify({ briefs: [{ prompt: "a" }] }), async () => pass())).out.results.length, 1);
});
