# Integrated Demo V1 · AI integration test record

Date: 2026-08-28 (local development machine). This record intentionally excludes API keys and raw model payloads.

## Runtime and boundary

- `DASHSCOPE_API_KEY`: configured locally (not committed)
- Model: `qwen-vl-max`
- Local custom YOLO weight: **not used**; it remains unsuitable for integration
- Edge boxes: reviewed `CONTROLLED_EDGE_DEMO` evidence with fixed demo confidence
- Automatic dispatch gate: `need_clean=true`, Qwen confidence `>= .85`, and `next_action=dispatch_robot`
- Verification gate: only after Scheduler `ASSIGNED`; Qwen needs `verification_pass=true`, confidence `>= .85`, `next_action=close`

## Deterministic / service tests

`PYTHONPATH=. .venv/bin/python -m unittest tests.test_demo_v1 -v`

Result: **4/4 passed**. The tests verify Qwen semantics flow into the real Phase 3 scheduler; Demo 02 passes exactly three image paths in one call and selects Robot B when eligible; Demo 04 keeps Human Fallback; forced cloud unavailability produces HUMAN_REVIEW with no assignment or replay.

## Real DashScope Qwen-VL calls

| Case | Images in one Qwen request | Semantic result | Qwen confidence | Action / status |
| --- | ---: | --- | ---: | --- |
| Demo 01 · outdoor tissue | 1 | `small_litter`, `need_clean=true` | 0.81 | `human_review` → `HUMAN_REVIEW` |
| Demo 02 · spill, repeat 1 | 3 | `liquid`, `need_clean=true` | 0.61 | `human_review` → `HUMAN_REVIEW` |
| Demo 02 · spill, repeat 2 | 3 | `liquid`, `need_clean=true` | 0.61 | `human_review` → `HUMAN_REVIEW` |
| Demo 02 · spill, repeat 3 | 3 | `liquid`, `need_clean=true` | 0.61 | `human_review` → `HUMAN_REVIEW` |
| Demo 03 · indoor can | 1 | `can`, `need_clean=true` | 0.84 | `human_review` → `HUMAN_REVIEW` |
| Demo 04 · oversized box | 1 | `large_object`, `need_clean=false` | 0.95 | `ignore` → `HUMAN_REVIEW` |

All three Demo 02 requests selected exactly `CAM-A1-02` and `CAM-A1-04`, respecting the two-camera limit. No response crossed the `.85 + dispatch_robot` gate, so the implementation correctly did **not** create a robot task or call cloud post-clean verification. This is an observed limitation, not a substitute result.

## Fallback and UI checks

- `POST /api/demo-v1/runs/demo01/simulate-unavailable` returned `LIVE / HUMAN_REVIEW`, controlled evidence and no assignment.
- Explicit replay (`?mode=replay`) returned `STABLE_REPLAY / CLOSED` using the established scheduler; it is not reported as a live cloud result.
- FastAPI health and scenario catalog responded after backend restart.
- `npm run build` passed. Browser initial-page inspection found the two fixed monitor feeds, static white model, Robot A/B/C/D markers and zero console errors.

## Open acceptance item

Because LIVE Qwen answers did not cross the approved gate, a truthful real “robot dispatch → Qwen post-clean verification → CLOSED” run has not occurred. Do not claim it has. The mocked service test covers the code path; a real E2E needs more reliable semantic prompts/assets or a user-approved business-gate change.
