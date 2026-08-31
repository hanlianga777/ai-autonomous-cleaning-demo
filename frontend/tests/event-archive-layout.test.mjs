import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const source = await readFile(resolve(import.meta.dirname, "../src/components/prototype/EventArchiveView.tsx"), "utf8");

test("Event Center keeps list and detail scrolling inside one fixed workspace", () => {
  assert.match(source, /grid h-\[calc\(100vh-180px\)\] min-h-\[460px\].*overflow-hidden/s);
  assert.match(source, /<section className="flex min-h-0 min-w-0 flex-col border-r[^>]*>.*min-h-0 flex-1 overflow-y-auto/s);
  assert.match(source, /<section className="min-h-0 min-w-0 overflow-hidden bg-slate-50\/60">.*<EventDetailPanel/s);
});
