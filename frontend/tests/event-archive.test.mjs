import assert from "node:assert/strict";
import { Buffer } from "node:buffer";
import { resolve } from "node:path";
import test from "node:test";
import { build } from "esbuild";

const entryPoint = resolve(import.meta.dirname, "../src/components/prototype/eventArchiveModel.ts");
const bundled = await build({ entryPoints: [entryPoint], bundle: true, format: "esm", platform: "node", target: "node20", write: false, logLevel: "silent" });
const source = Buffer.from(bundled.outputFiles[0].text).toString("base64");
const archive = await import(`data:text/javascript;base64,${source}`);

test("selection URL restores event ID but does not invent a first list selection", () => {
  assert.equal(archive.parseArchiveSelection("/events?event=evt-123"), "evt-123");
  assert.equal(archive.parseArchiveSelection("/events?category=all"), null);
  assert.equal(archive.archiveUrlWithSelection("/events?event=old&map_id=A_1F", "evt-123"), "/events?event=evt-123&map_id=A_1F");
  assert.equal(archive.archiveUrlWithSelection("/events?event=old&map_id=A_1F", null), "/events?map_id=A_1F");
});

test("archive API query retains only meaningful filters and resets non-negative pagination", () => {
  const query = archive.archiveQuery({ ...archive.DEFAULT_ARCHIVE_FILTERS, category: "human_pending", q: "  CAM-A1-01 ", handlingMode: "human_fallback", offset: -3, limit: 50 });
  assert.equal(query.get("category"), "human_pending");
  assert.equal(query.get("q"), "CAM-A1-01");
  assert.equal(query.get("handling_mode"), "human_fallback");
  assert.equal(query.get("offset"), "0");
  assert.equal(query.get("event_type"), null);
});

test("Analytics drill-down URL filters restore map, type, time and locked time slot without inventing selection", () => {
  const filters = archive.parseArchiveFilters("/events?map_id=A_1F&x=14.5&y=22.5&event_type=liquid&since=2026-08-01T00%3A00%3A00Z&until=2026-08-30T00%3A00%3A00Z&time_slot=14-18");
  assert.equal(filters.mapId, "A_1F");
  assert.equal(filters.x, "14.5");
  assert.equal(filters.y, "22.5");
  assert.equal(filters.eventType, "liquid");
  assert.equal(filters.timeSlot, "14-18");
  assert.equal(archive.parseArchiveSelection("/events?map_id=A_1F"), null);
  assert.equal(archive.parseArchiveFilters("/events?time_slot=13-17").timeSlot, "");
});

test("new-event notice counts new IDs without changing selection or treating a repeat as new", () => {
  const seen = new Set(["evt-1", "evt-2"]);
  const next = [{ event_id: "evt-2" }, { event_id: "evt-3" }, { event_id: "evt-4" }];
  assert.equal(archive.countNewEvents(seen, next), 2);
  assert.equal(archive.countNewEvents(new Set(["evt-1", "evt-2", "evt-3", "evt-4"]), next), 0);
  const batch = archive.nextKnownEventBatch(seen, next);
  assert.equal(batch.added, 2);
  assert.deepEqual([...batch.knownIds].sort(), ["evt-1", "evt-2", "evt-3", "evt-4"]);
});

test("customer labels and duration remain compact and never expose raw event ontology", () => {
  assert.equal(archive.eventTypeLabel("liquid"), "液体污渍");
  assert.equal(archive.eventTypeLabel(""), "待复核");
  assert.equal(archive.durationLabel(73), "1 分 13 秒");
  assert.equal(archive.durationLabel(undefined), "进行中");
  assert.equal(archive.structuralLocationLabel("A", "building"), "A栋");
  assert.equal(archive.structuralLocationLabel("1F", "floor"), "1F");
  assert.equal(archive.structuralLocationLabel("OUTDOOR", "building"), "室外");
  assert.equal(archive.structuralLocationLabel("Outdoor", "floor"), "室外");
});

test("SQLite timestamps without an offset are interpreted as UTC, not browser-local time", () => {
  assert.equal(
    archive.archiveTimestampMs("2026-08-30 10:20:30"),
    Date.parse("2026-08-30T10:20:30Z"),
  );
  assert.equal(archive.archiveTimestampMs("2026-08-30T10:20:30+08:00"), Date.parse("2026-08-30T10:20:30+08:00"));
  assert.match(archive.archiveDateTimeInputValue("2026-08-30T10:20:30Z"), /^2026-08-30T\d\d:\d\d$/);
});

test("datetime-local operator filters become explicit UTC API values", () => {
  const localValue = "2026-08-30T10:20";
  const query = archive.archiveQuery({ ...archive.DEFAULT_ARCHIVE_FILTERS, since: localValue, until: "" });
  assert.equal(query.get("since"), new Date(localValue).toISOString());
  assert.equal(archive.localDateTimeToUtcIso("not-a-date"), "");
});

test("detail race identity guard never renders event A for a newer B selection", () => {
  assert.equal(archive.canRenderArchiveDetail("evt-b", "evt-a"), false);
  assert.equal(archive.canRenderArchiveDetail("evt-b", "evt-b"), true);
  assert.equal(archive.canRenderArchiveDetail(null, "evt-a"), false);
});
