# Unified Interview Demo Recovery｜Requirement Implementation Matrix

> Created before implementation on main at `c37ec8c`. This matrix is the execution ledger for every `LOCKED TARGET` in `INTERVIEW_DEMO_RECONCILIATION.md`; the reconciliation document remains the normative product specification. Initial status is intentionally limited to `TODO`, `PARTIAL`, and `EXISTING_OK`. No row is `IMPLEMENTED` or `USER_ACCEPTED` at this point.

## Matrix fields and shared evidence

| Field | Meaning |
| --- | --- |
| Requirement ID / Sub-item | Atomic locked requirement. |
| Priority | `P0-LOCKED` for every row. |
| Affected active code | Authoritative implementation candidates; final code is recorded on completion. |
| Current implementation / divergence | Read-only audit before this Recovery. |
| Required implementation / dependencies | Exact result is the linked reconciliation sub-item; dependencies identify shared constraints. |
| Backend / frontend / runtime tests | Required automated evidence. |
| Visual acceptance / cross-regression | Required product check and related locked targets. |
| Status | Initial state only: `TODO`, `PARTIAL`, or `EXISTING_OK`. |

## Architecture Audit A｜Evidence Availability / Temporal Gate

| Evidence | Earliest customer/runtime availability | Required gate | Current audit | Status |
| --- | --- | --- | --- | --- |
| Primary Before | `DETECTED` | event’s primary camera + current metadata only | Primary is used for first Cloud input; complete manifest is also exposed | PARTIAL |
| Edge Evidence | `EDGE_DETECTED` | successful edge review only | transition already records controlled edge output | PARTIAL |
| Supporting Evidence | successful autonomous fetch after insufficient single-view | evidence-sufficiency → coverage → model selection → fetch success; acquired set only | service mostly gates Cloud input, but manifest/Agent read can leak assets | PARTIAL |
| After Evidence | `CLEANING_COMPLETED`; Demo04 only after explicit operator completion | real cleaning/manual-complete transition then fixed-camera acquisition | verifier stage guard exists, public snapshot/manifest does not fully gate reads | PARTIAL |
| Verification result | successful After + Cloud verification | After availability, not robot completion or known result | backend stage ordering exists | PARTIAL |
| Terminal evidence history | terminal event only | actual acquired evidence audit trail | archive is read-only but needs common projection gate | PARTIAL |
| Stable Replay | same stage as LIVE | replayed model records cannot bypass availability | replay reuses stages but needs public evidence filtering | PARTIAL |

## Architecture Audit B｜Runtime Mutation Path

| Path / owner | Can create or mutate | Classification required by RUNTIME-SINGLE-PATH-01 | Current audit | Required action | Status |
| --- | --- | --- | --- | --- | --- |
| `backend/demo_v1/service.py` + `/api/demo-v1/events/*` | Create, edge, cloud, locate, assign, navigation, complete, verify | `AUTHORITATIVE_INTERVIEW_RUNTIME` | active prototype’s primary event path | make sole customer mutation owner and enforce stage/evidence/session contracts | PARTIAL |
| `backend/robot_operations/tasks.py` + `/api/robot-operations/*` | persisted operational task lifecycle | `AUTHORITATIVE_INTERVIEW_RUNTIME` only when delegating/controlling same event truth | durable session/task store exists | eliminate customer `advance` dependency; make worker/runtime continuation authoritative | PARTIAL |
| `/api/workbench/*`, `backend/workbench/service.py` | scenario/workbench helper create/run paths | `ENGINEERING_TEST_ONLY` or `RETIRED` | executable legacy helpers still present | isolate or 410; remove customer callers | TODO |
| `/api/operations/*`, `backend/operations/*` | legacy operations run/upload | `ENGINEERING_TEST_ONLY` or `RETIRED` | executable legacy operations paths remain | classify, isolate and reject customer access | TODO |
| `/api/multiview/*`, `/api/events/*`, `/api/ai-lab/*` | standalone test/mock/multiview actions | `ENGINEERING_TEST_ONLY` or `RETIRED` | mixed legacy/test endpoints remain | preserve useful test seams, no formal customer caller | TODO |
| Archive / Analytics read models | no business mutation | customer read projection | same SQLite facts are partly read | filter customer dataset and evidence by contract | PARTIAL |

## AI-UI-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AI-UI-01.1 | P0-LOCKED | `RobotOperationsPanel`, `robotOperationsModel`, `PrototypeWorkbench` | 352px horizontal collapsed header; header-only drag | viewport-wide persistent circular floating ball; shared Agent | session identity | drag/clamp/storage | cross-route state | ball-only idle on Workbench/Event | AGENT-SESSION, LAYOUT, PRESENTATION | TODO |
| AI-UI-01.2 | P0-LOCKED | `RobotOperationsPanel` | compact tool/task panel | full welcome/history/message/composer/send/status/collapse Chat window | shared session | component interaction | shared task projection | unmistakable Chat, not debug panel | OPS-CONTINUITY, AGENT-AUTHORITY | TODO |
| AI-UI-01.3 | P0-LOCKED | `AnalyticsView`, `RobotOperationsPanel` | advice+chat split in page-flow aside | fixed right Chat with independent message scroll/composer; advice moves left | advice boundary | viewport/layout test | session continuity | composer visible on entry | ANALYTICS-DELTA, LAYOUT | TODO |
| AI-UI-01.4 | P0-LOCKED | provider/model/panel | shared provider exists | retain one session/Agent/task/audit truth; add none | session lifecycle | shared projection | task truth | same chat history at all three surfaces | AGENT-SESSION, RUNTIME-SINGLE-PATH | PARTIAL |

## WB-DETAIL-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WB-DETAIL-01.1 | P0-LOCKED | `EventDetailPanel`, `eventViewModel` | technical process semantics | customer-first event/decision/next-step/execution/closure hierarchy | snapshot projection | customer copy | persisted state | business-first detail | EVENT-01, PRESENTATION | TODO |
| WB-DETAIL-01.2 | P0-LOCKED | `PrototypeWorkbench`, `SpatialDispatchView`, `demo_v1` | frontend microtask stage chaining | durable/presentable deterministic cadence, true Cloud duration | transition timing | stage presentation | leave-page continuity | visible progressive flow | OPS-CONTINUITY | TODO |
| WB-DETAIL-01.3 | P0-LOCKED | `EventStageEvidence` | controlled/YOLO/persistence copy shown | customer evidence/location/object/box only | edge snapshot | card rendering | edge transition | clear discovery card | WB-CAMERA, ADVANCED | TODO |
| WB-DETAIL-01.4 | P0-LOCKED | `EventStageEvidence`, `eventViewModel` | repeated confidence/latency/sufficiency fields | one final AI confidence + system score N points | cloud response | summary fields | true cloud result | legible Cloud card | EVENT-01, ADVANCED | TODO |
| WB-DETAIL-01.5 | P0-LOCKED | `EventStageEvidence`, spatial projection | technical calibration copy/missing customer map label | customer Building/Floor/Zone/SLAM XY/map name | spatial facts | projection test | locate stage | accurate location card | WB-MAP | PARTIAL |
| WB-DETAIL-01.6 | P0-LOCKED | event evidence, scheduler | technical filter/score wording | hard-eliminated vs eligible customer cards and named assignee | capability policy | assignment card | assign stage | selected robot clear | AGENT-AUTHORITY, PRESENTATION | PARTIAL |
| WB-DETAIL-01.7 | P0-LOCKED | `SpatialDispatchView`, map | route technical/limited customer story | distance/ETA/nodes/elevator/skybridge from backend geometry | route facts | route projection | navigation | visible legitimate route | WB-MAP, DEMO-CONTRACT | PARTIAL |
| WB-DETAIL-01.8 | P0-LOCKED | workbench/runtime | ownership/pending inconsistencies possible | clear ownership, failure release and terminal truth | mutation guards | state view | stage terminal | no false completion | OPS-CONTINUITY, RUNTIME-SINGLE-PATH | PARTIAL |
| WB-DETAIL-01.9 | P0-LOCKED | `EventStageEvidence`, verifier | After can leak/closure copy technical | released After → AI result/confidence → truth | verification gate | verification card | after stage | real closure visual | EVIDENCE-INTEGRITY | TODO |
| WB-DETAIL-01.10 | P0-LOCKED | shared detail/advanced | technical content in customer panel | move technical facts to Advanced only | redaction | copy regression | trace retained | no debug feel | PRESENTATION, ADVANCED | TODO |
| WB-DETAIL-01.11 | P0-LOCKED | all above | no final row evidence yet | map every detail sub-item to tests/visual report | suite | component suite | four demos | all cards | EVENT-01, LAYOUT | TODO |

## WB-MAP-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WB-MAP-01.1 | P0-LOCKED | `SpatialDispatchView`, asset cards | old fleet/ID-centric cards | four equal customer-name asset cards | fleet snapshot | card labels | session fleet | four assets visible | PRESENTATION | TODO |
| WB-MAP-01.2 | P0-LOCKED | map/cards | dense technical defaults | business card density, technical hover only | fleet fields | layout test | snapshot | readable cards | LAYOUT | TODO |
| WB-MAP-01.3 | P0-LOCKED | map/cards | weak selected treatment | restrained assigned-robot highlight | assignment | visual class | assign | clear but not neon | WB-DETAIL | TODO |
| WB-MAP-01.4 | P0-LOCKED | `SpatialDispatchView` | spatial/fleet/topology language | 园区空间调度 customer language | n/a | copy | n/a | customer title | PRESENTATION | TODO |
| WB-MAP-01.5 | P0-LOCKED | spatial/scheduler | rules exist but may be technical | retain true capability/spatial limits | capability | labels | demos | no invalid deployment | AGENT-AUTHORITY | PARTIAL |
| WB-MAP-01.6 | P0-LOCKED | route projection | anchor interpolation only | identify/replace visual route gap | route geometry | geometry tests | Demo03 | no wall/floor jump | DEMO-CONTRACT | TODO |
| WB-MAP-01.7 | P0-LOCKED | topology/projection | no shared waypoint geometry contract | backend-owned navigation waypoints | route planner | SVG geometry | cross-floor path | road/corridor/bridge path | RUNTIME-SINGLE-PATH | TODO |
| WB-MAP-01.8 | P0-LOCKED | map canvas | weak route hierarchy | event/current/past/future route layers | route facts | render test | navigation | priority readable | LAYOUT | TODO |
| WB-MAP-01.9 | P0-LOCKED | map canvas | marker state incomplete | state-driven event marker | event state | marker test | all demos | target evolves | WB-CAMERA | TODO |
| WB-MAP-01.10 | P0-LOCKED | map hover | details exposed in cards | hover holds technical detail | fleet fields | hover test | live fleet | helpful marker hover | PRESENTATION | TODO |
| WB-MAP-01.11 | P0-LOCKED | map canvas | duplicate status card | remove duplicate upper-right status | n/a | DOM test | n/a | no duplicate | LAYOUT | TODO |
| WB-MAP-01.12 | P0-LOCKED | route playback | stage movement partial | idle→event→route→navigation→closed evolution | transitions | render test | Demo01-04 | state progression | OPS-CONTINUITY | PARTIAL |
| WB-MAP-01.13 | P0-LOCKED | spatial service | visuals may infer facts | one backend geometry source | route test | source test | four demos | no fabricated route | RUNTIME-SINGLE-PATH | TODO |
| WB-MAP-01.14 | P0-LOCKED | map/runtime | demo coverage incomplete | S5 road, Omnie A1, SC50 cross-building visible | route demos | UI scenarios | official demos | three routes accepted | DEMO-CONTRACT | TODO |
| WB-MAP-01.15 | P0-LOCKED | all map files | no final report | evidence row per map target | suite | component suite | demos | screenshots | EVENT, LAYOUT | TODO |

## WB-CAMERA-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WB-CAMERA-01.1 | P0-LOCKED | `CameraMonitorGrid` | legacy slot proportions possible | three equal fixed-camera views | asset state | grid test | idle/live | equal three-camera wall | LAYOUT | TODO |
| WB-CAMERA-01.2 | P0-LOCKED | camera model/grid | selection may not follow true primary | dynamic primary-first slots | event manifest | ordering test | demo01-04 | primary first | EVIDENCE-INTEGRITY | TODO |
| WB-CAMERA-01.3 | P0-LOCKED | camera grid | idle may look diagnostic | clean/normal after operational views | inventory | idle render | new show | clean idle wall | SHOW-BASE | TODO |
| WB-CAMERA-01.4 | P0-LOCKED | grid/evidence | overlays leak to monitor | raw Before on monitor; overlay only evidence | gate | visual test | detected | raw primary monitor | WB-DETAIL | TODO |
| WB-CAMERA-01.5 | P0-LOCKED | grid | state emphasis incomplete | restrained business state highlight | transition | class test | processing | sensible colors | PRESENTATION | TODO |
| WB-CAMERA-01.6 | P0-LOCKED | grid | After availability unsafe | After only completion/verification, normal restore | temporal gate | stage test | all demos | correct before/after swap | EVIDENCE-INTEGRITY | TODO |
| WB-CAMERA-01.7 | P0-LOCKED | camera/evidence components | monitor/technical evidence mixed | separate customer monitor from technical detail | payload gate | component test | stage | no debug overlay | ADVANCED | TODO |
| WB-CAMERA-01.8 | P0-LOCKED | image renderers | fill policy inconsistent | monitor cover/evidence contain | n/a | class test | n/a | correct crops | EVENT-01 | TODO |
| WB-CAMERA-01.9 | P0-LOCKED | camera grid | verbose technical labels | location + play + live time only | snapshot | copy test | live | minimal card info | PRESENTATION | TODO |
| WB-CAMERA-01.10 | P0-LOCKED | camera grid | no consistent play cue | subtle translucent play affordance | n/a | render | n/a | play cue visible | LAYOUT | TODO |
| WB-CAMERA-01.11 | P0-LOCKED | camera grid | static/fake time risk | dynamic HH:mm:ss from runtime | clock fact | clock test | live | changing time | DATA-TRUTH | TODO |
| WB-CAMERA-01.12 | P0-LOCKED | header/grid | title clutter | simplified customer title | n/a | copy test | n/a | uncluttered | PRESENTATION | TODO |
| WB-CAMERA-01.13 | P0-LOCKED | workbench/header | duplicated headings | remove duplicate top titles | n/a | DOM test | n/a | one title | LAYOUT | TODO |
| WB-CAMERA-01.14 | P0-LOCKED | names | internal camera terms | customer-visible names | manifest | labels test | demos | friendly labels | PRESENTATION | TODO |
| WB-CAMERA-01.15 | P0-LOCKED | grid | technical language | customer business wording | n/a | copy test | n/a | readable | WB-DETAIL | TODO |
| WB-CAMERA-01.16 | P0-LOCKED | triggers/header | direct controls noisy | low-interference overflow demo controls | trigger API | interaction test | demo start | controls unobtrusive | PRESENTATION | TODO |
| WB-CAMERA-01.17 | P0-LOCKED | grid | visual slot inconsistency | uniform three-slot visual system | n/a | layout test | n/a | consistent wall | LAYOUT | TODO |
| WB-CAMERA-01.18 | P0-LOCKED | grid/runtime | no all-demo verified cycle | all four complete camera states | demo assertions | UI test | demos | Before/After correct | DEMO-CONTRACT | TODO |
| WB-CAMERA-01.19 | P0-LOCKED | all camera files | no final report | subitem evidence ledger | suite | component suite | demos | screenshots | EVENT-01 | TODO |

## EVENT-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EVENT-01.1 | P0-LOCKED | archive service/view/model | archive remains technical/dense | customer work-order list columns | archive query | list test | persisted events | real work-order table | DATA-BOUNDARY | TODO |
| EVENT-01.2 | P0-LOCKED | archive view | English/technical headings remain | customer title and language | n/a | copy test | n/a | customer page title | PRESENTATION | TODO |
| EVENT-01.3 | P0-LOCKED | EventArchiveView/EventDetailPanel | shared panel but presentation diverges | identical business detail/layout/images/timeline | snapshots | render comparison | read-only | same detail shell | WB-DETAIL | PARTIAL |
| EVENT-01.4 | P0-LOCKED | archive/read model | potential alternate summary | one persisted CleaningEvent truth | event archive | consistency test | no replay/run | same facts | RUNTIME-SINGLE-PATH | PARTIAL |
| EVENT-01.5 | P0-LOCKED | detail/model | stage chain not fully customer-conditioned | complete truthful conditional timeline | transition tests | timeline test | demos | correct events | EVIDENCE-INTEGRITY | TODO |
| EVENT-01.6 | P0-LOCKED | multiview/detail | fallback/multiview semantics unclear | true gate/HUMAN_REVIEW presentation | multiview test | branch test | demo02 | legitimate conditions | DEMO-CONTRACT | PARTIAL |
| EVENT-01.7 | P0-LOCKED | scenario data/detail | demo roles can blur | distinct Demo02/03 scenarios | manifest test | label test | demos | separate stories | DEMO-CONTRACT | TODO |
| EVENT-01.8 | P0-LOCKED | detail timeline | potential collapsed chain | fixed business sequence when acquired | transition order | timeline test | demo02 | sequence visible | EVIDENCE-INTEGRITY | TODO |
| EVENT-01.9 | P0-LOCKED | detail timeline | agent and judgment may merge | separate acquisition/judgment nodes | trace test | timeline test | demo02 | two nodes | ADVANCED | TODO |
| EVENT-01.10 | P0-LOCKED | EventStageEvidence | evidence layout unknown | two supporting images side-by-side | acquired evidence | render test | demo02 | parallel evidence | EVIDENCE-INTEGRITY | TODO |
| EVENT-01.11 | P0-LOCKED | evidence/detail | overlay contract inconsistent | true controlled edge overlay in evidence | edge record | overlay test | edge stage | valid bbox evidence | WB-DETAIL | TODO |
| EVENT-01.12 | P0-LOCKED | detail/model | raw VLM details leak | customer VLM fields only | response projection | copy test | cloud stage | clean cloud card | WB-DETAIL | TODO |
| EVENT-01.13 | P0-LOCKED | scenario/manifest | canonical before mismatch risk | `primary-ambiguous-v2.png` everywhere | asset test | image source test | LIVE/replay | one image | EVIDENCE-INTEGRITY | TODO |
| EVENT-01.14 | P0-LOCKED | service/replay/view | source path drift risk | manifest/model/replay/UI fingerprint consistency | fingerprint | source test | demo02 replay | identical asset | EVIDENCE-INTEGRITY | TODO |
| EVENT-01.15 | P0-LOCKED | multiview agent | demo-id forcing prohibited | no demo-id tool/camera/result hardcode | static/agent tests | n/a | live regression | autonomous tools | DEMO-CONTRACT | PARTIAL |
| EVENT-01.16 | P0-LOCKED | docs/tests/view | historical test facts could appear product truth | constrain historical evidence to technical record | boundary test | copy test | n/a | no false guarantee | PRESENTATION | TODO |
| EVENT-01.17 | P0-LOCKED | demo tests | no qualifying live record | 5-run Demo02 evaluation | opt-in suite | n/a | LIVE 5x | trace review | AI-RESILIENCE | TODO |
| EVENT-01.18 | P0-LOCKED | live/archive detail | pages can differ | demo02 cards exact business parity | snapshot parity | DOM parity | persisted read | visually identical | WB-DETAIL | TODO |
| EVENT-01.19 | P0-LOCKED | shared detail | customer boundary incomplete | inherit all detail customer boundaries | redaction | copy | demos | no technical content | WB-DETAIL | TODO |
| EVENT-01.20 | P0-LOCKED | event surfaces | no complete evidence report | verify all locked dependencies | suites | UI suite | four demos | Event Center screenshot | ALL | TODO |

## RUNTIME-SINGLE-PATH-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RUNTIME-SINGLE-PATH-01.1 | P0-LOCKED | demo_v1/scheduler/spatial | demo_v1 primary but parallel helpers exist | one formal CleaningEvent runtime | mutation audit | no legacy caller | four demos | one truth | DEMO-CONTRACT | PARTIAL |
| RUNTIME-SINGLE-PATH-01.2 | P0-LOCKED | workbench | page invokes/drives stages | projection/control only | owner test | API caller test | leave page | no second workflow | OPS-CONTINUITY | TODO |
| RUNTIME-SINGLE-PATH-01.3 | P0-LOCKED | archive | read only largely present | Event Center no recompute/run | no-mutation test | archive test | GET only | persisted detail | EVENT-01 | PARTIAL |
| RUNTIME-SINGLE-PATH-01.4 | P0-LOCKED | robot ops | tasks may be parallel workflow | Agent finds/delegates same event | agent authority | agent test | shared event | same task truth | AGENT-AUTHORITY | TODO |
| RUNTIME-SINGLE-PATH-01.5 | P0-LOCKED | analytics read model | current datasets uncertain | analytics only authoritative + boundary facts | boundary tests | analytics tests | history read | same metrics | DATA-BOUNDARY | TODO |
| RUNTIME-SINGLE-PATH-01.6 | P0-LOCKED | routes/services/helpers | executable legacy paths | enumerate/classify A/B/C | endpoint audit | no legacy API | route contract | no customer route | ALL | TODO |
| RUNTIME-SINGLE-PATH-01.7 | P0-LOCKED | test/AI lab helpers | test paths mixed | isolate engineering capabilities | isolation test | absence test | test fixtures | no contamination | DATA-BOUNDARY | TODO |
| RUNTIME-SINGLE-PATH-01.8 | P0-LOCKED | replay | stages reuse partly | response-only replay, common stages | replay contract | n/a | replay 3x | replay disclosed | EVIDENCE-INTEGRITY | PARTIAL |
| RUNTIME-SINGLE-PATH-01.9 | P0-LOCKED | DB/services | partial lease exists | one mutation owner/lease/transaction | concurrency test | n/a | parallel calls | no contradictory state | OPS-CONTINUITY | PARTIAL |
| RUNTIME-SINGLE-PATH-01.10 | P0-LOCKED | frontend APIs | legacy APIs still exported | official frontend no legacy mutations | route scan | build/API tests | demos | no debug action | PRESENTATION | TODO |

## ANALYTICS-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ANALYTICS-01.1 | P0-LOCKED | AnalyticsView | navigation audit pending | 一级运营分析/二级洞察/统计 | read model | nav test | history read | navigation clear | PRESENTATION | TODO |
| ANALYTICS-01.2 | P0-LOCKED | AnalyticsView | aside page flow | KPI→advice cards→heatmap with fixed chat | analytics API | layout test | viewport | one-screen story | ANALYTICS-DELTA | TODO |
| ANALYTICS-01.3 | P0-LOCKED | AnalyticsView | large page header likely | remove redundant title block | n/a | DOM test | n/a | compact entry | LAYOUT | TODO |
| ANALYTICS-01.4 | P0-LOCKED | AnalyticsView | customer filter controls likely | remove customer filters | boundary | DOM test | n/a | no filter bar | DATA-BOUNDARY | TODO |
| ANALYTICS-01.5 | P0-LOCKED | KPI view/model | current KPI presentation unknown | five minimal traceable KPIs | KPI derivation | render test | history data | five clear KPIs | DATA-BOUNDARY | TODO |
| ANALYTICS-01.6 | P0-LOCKED | AnalyticsView/charts | stats mix insight page | separate data statistics subpage | aggregates | tab test | history data | 2×2 statistics | LAYOUT | TODO |
| ANALYTICS-01.7 | P0-LOCKED | AnalyticsView | Data Composition card exists | remove customer card | n/a | DOM test | n/a | absent | PRESENTATION | TODO |
| ANALYTICS-01.8 | P0-LOCKED | analytics read model | type aggregation audit pending | standard customer event types | aggregate test | chart test | history | truthful structure | DATA-BOUNDARY | TODO |
| ANALYTICS-01.9 | P0-LOCKED | AnalyticsView/chat | fixed area missing | right fixed full Chat | session test | layout test | cross page | composer visible | AI-UI | TODO |
| ANALYTICS-01.10 | P0-LOCKED | advice model/view | advice currently aside split | <=3 horizontal title/finding/recommendation cards | advice snapshot | card test | historical data | horizontal cards | ANALYTICS-DELTA | TODO |
| ANALYTICS-01.11 | P0-LOCKED | advice service | factual boundary audit pending | advice only recorded fact/allowed data | boundary test | copy test | history | no fabricated findings | DATA-BOUNDARY | TODO |
| ANALYTICS-01.12 | P0-LOCKED | provider/advice | existing provider shared | no analytics agent | session identity | context test | shared backend | same agent | AI-UI | PARTIAL |
| ANALYTICS-01.13 | P0-LOCKED | chat panel | analytics chat differs/split | full unified customer Chat UI | session test | component test | shared task | identical Chat semantics | AI-UI | TODO |
| ANALYTICS-01.14 | P0-LOCKED | Analytics/chat | microphone exists disabled elsewhere | remove voice entry analytics | n/a | DOM test | n/a | no voice control | PRESENTATION | TODO |
| ANALYTICS-01.15 | P0-LOCKED | chat | audit/task traces visible | no raw audit/JSON/engineering content | redaction | render test | session | customer chat only | AI-UI | TODO |
| ANALYTICS-01.16 | P0-LOCKED | agent/view | capability copy broad | customer-safe query surface | policy tests | prompt UI | live session | clear capability | AGENT-AUTHORITY | TODO |
| ANALYTICS-01.17 | P0-LOCKED | heatmap/projection | scatter/static risk | continuous density field | geometry data | render test | 30d history | density layer | DATA-BOUNDARY | TODO |
| ANALYTICS-01.18 | P0-LOCKED | heatmap | color audit pending | cyan→yellow→orange→red | n/a | style test | n/a | correct ramp | LAYOUT | TODO |
| ANALYTICS-01.19 | P0-LOCKED | heatmap | no controlled pulse | restrained high-hotspot pulse | n/a | class test | n/a | subtle pulse | LAYOUT | TODO |
| ANALYTICS-01.20 | P0-LOCKED | history/read model | seeds could include noncustomer data | genuine 30-day positions | data boundary | model test | history query | factual locations | DATA-BOUNDARY | TODO |
| ANALYTICS-01.21 | P0-LOCKED | spatialProjection/heatmap | projection proof incomplete | verified geometry only | projection test | geometry test | history | no shifted facts | WB-MAP | TODO |
| ANALYTICS-01.22 | P0-LOCKED | analytics tests | no canonical-zone suite | deterministic five-zone coverage | fixtures | test | history | all zones | DATA-BOUNDARY | TODO |
| ANALYTICS-01.23 | P0-LOCKED | heatmap | hotspot labels unclear | customer labels/hover | model | interaction test | history | hover label | PRESENTATION | TODO |
| ANALYTICS-01.24 | P0-LOCKED | analytics/archive | drilldown unclear | read-only Event Center linkage | query test | link test | archive GET | linked archive | EVENT-01 | TODO |
| ANALYTICS-01.25 | P0-LOCKED | analytics service | sources not fully filtered | interview analytics boundary | boundary suite | UI source test | data seed | no test artifacts | DATA-BOUNDARY | TODO |
| ANALYTICS-01.26 | P0-LOCKED | analytics styles | visual audit pending | coherent customer operating view | n/a | layout test | n/a | no dense/debug feel | LAYOUT | TODO |
| ANALYTICS-01.27 | P0-LOCKED | active files | scope unverified | only approved active code paths | static audit | build | n/a | no legacy path | RUNTIME-SINGLE-PATH | TODO |
| ANALYTICS-01.28 | P0-LOCKED | all analytics | no final evidence | subitem implementation report | suite | component | 30d runtime | screenshots | AI-UI, DATA-BOUNDARY | TODO |

## ADVANCED-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ADVANCED-01.1 | P0-LOCKED | nav/AdvancedView | route exists | retain navigation/route | route test | nav test | n/a | entry visible | PRESENTATION | EXISTING_OK |
| ADVANCED-01.2 | P0-LOCKED | AdvancedView | complex traces rendered | hide default dynamic technical panels | trace API preserve | DOM test | n/a | no technical cards | PRESENTATION | TODO |
| ADVANCED-01.3 | P0-LOCKED | backend observability | observability exists | retain APIs/traces/tests | observability tests | n/a | demo audit | backend retained | RUNTIME-SINGLE-PATH | PARTIAL |
| ADVANCED-01.4 | P0-LOCKED | AdvancedView | diagnostic page positioning | technical-image assistance page | n/a | copy test | n/a | restrained page | PRESENTATION | TODO |
| ADVANCED-01.5 | P0-LOCKED | AdvancedView | no user asset | one/two large asset placeholder only | n/a | render test | n/a | PENDING USER ASSET | LAYOUT | TODO |
| ADVANCED-01.6 | P0-LOCKED | AdvancedView | current grid/cards | one centered/two vertical image layout | n/a | layout test | n/a | correct layout | LAYOUT | TODO |
| ADVANCED-01.7 | P0-LOCKED | AdvancedView | no minimal lightbox guarantee | click-to-enlarge images | n/a | interaction test | n/a | usable enlargement | LAYOUT | TODO |
| ADVANCED-01.8 | P0-LOCKED | AdvancedView | technical copy | minimal customer text | n/a | copy test | n/a | concise copy | PRESENTATION | TODO |
| ADVANCED-01.9 | P0-LOCKED | AdvancedView/assets | user assets absent | explicit pending, no generated/old image | asset check | DOM test | n/a | pending state | REQUIREMENT-FREEZE | TODO |
| ADVANCED-01.10 | P0-LOCKED | implementation order | no enforced order | simplify only presentation after core truth | n/a | build | n/a | no runtime loss | RUNTIME-SINGLE-PATH | TODO |
| ADVANCED-01.11 | P0-LOCKED | all advanced | no final evidence | report/tests/visual evidence | observability | component | demo audit | screenshot | ALL | TODO |

## SHOW-BASE-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SHOW-BASE-01.1 | P0-LOCKED | launcher/main/demo service | restart semantics unverified | double-click launch creates new Show Session | launch/session test | storage reset | new process | fresh demo availability | AGENT-SESSION | TODO |
| SHOW-BASE-01.2 | P0-LOCKED | DB/runtime | history/current may mix | clear only current show state | persistence test | projection test | restart | history retained | DATA-BOUNDARY | TODO |
| SHOW-BASE-01.3 | P0-LOCKED | fleet/service | fleet reset partial | canonical initial robot positions | fleet test | map test | launch | correct idle positions | WB-MAP | TODO |
| SHOW-BASE-01.4 | P0-LOCKED | fleet/runtime | paths might reset on terminal | same session positions persist | fleet test | map reload | sequence | no teleport | DEMO-CONTRACT | TODO |
| SHOW-BASE-01.5 | P0-LOCKED | frontend | reset UX unknown | no manual reset button | n/a | DOM test | n/a | no reset control | PRESENTATION | TODO |
| SHOW-BASE-01.6 | P0-LOCKED | demo service | terminal lock risk | failures release next demo | terminal tests | trigger test | failure demo | next demo available | AI-RESILIENCE | TODO |

## DATA-BOUNDARY-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DATA-BOUNDARY-01.1 | P0-LOCKED | archive/analytics/agent | sources may include dev history | Canonical Demo history + legitimate runtime only | query filters | page test | seeded data | customer only | ANALYTICS | TODO |
| DATA-BOUNDARY-01.2 | P0-LOCKED | DB/test helpers | engineering records mixed | preserve but exclude test/dev/debug/legacy | boundary test | absent rows | test fixtures | no contamination | RUNTIME-SINGLE-PATH | TODO |
| DATA-BOUNDARY-01.3 | P0-LOCKED | read models/agent tools | filters not global | shared customer boundary utility | integration | source scan | cross pages | same counts | EVENT, ANALYTICS | TODO |
| DATA-BOUNDARY-01.4 | P0-LOCKED | runtime identity | mode/source criteria partial | reliable formal-runtime tagging | schema/test | no raw mode | live/replay | correct inclusion | SHOW-BASE | TODO |
| DATA-BOUNDARY-01.5 | P0-LOCKED | frontend | filters may expose switch | no customer data-source switch | n/a | DOM test | n/a | no source selector | PRESENTATION | TODO |

## PRESENTATION-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRESENTATION-01.1 | P0-LOCKED | view models/components | IDs remain in UI | unified customer robot names | catalog test | copy scan | demos | no Robot A/B IDs | WB-MAP | TODO |
| PRESENTATION-01.2 | P0-LOCKED | event/task models | varied state wording | unified customer state semantics | mappings | render test | tasks/events | consistent statuses | OPS-CONTINUITY | TODO |
| PRESENTATION-01.3 | P0-LOCKED | spatial projection | raw map/zone labels | customer spatial names | spatial test | label test | demos | readable locations | WB-DETAIL | TODO |
| PRESENTATION-01.4 | P0-LOCKED | all customer views | IDs displayed | internal IDs technical layer only | redaction | static scan | n/a | no raw IDs | ADVANCED | TODO |
| PRESENTATION-01.5 | P0-LOCKED | controls/views | mock/replay/debug controls visible | remove customer PoC/mock/replay/debug action labels | route test | DOM/copy test | n/a | no technical buttons | RUNTIME-SINGLE-PATH | TODO |
| PRESENTATION-01.6 | P0-LOCKED | frontend | partial application | apply boundary globally | contract suite | page scan | demos | consistent customer language | ALL | TODO |

## LAYOUT-01 and ANALYTICS-DELTA-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LAYOUT-01.1 | P0-LOCKED | global CSS/views | baseline unverified | validate 1440×900 / 1920×1080 | n/a | viewport suite | app | screenshots | ALL | TODO |
| LAYOUT-01.2 | P0-LOCKED | Workbench | dense/old layout | first-screen core story | n/a | layout test | workbench | one-screen narrative | WB-* | TODO |
| LAYOUT-01.3 | P0-LOCKED | EventArchiveView | partial local scroll | independent list/detail scroll | n/a | scroll test | archive | no page lock | EVENT-01 | PARTIAL |
| LAYOUT-01.4 | P0-LOCKED | AnalyticsView | page-flow aside | one-screen analytics narrative | n/a | viewport test | analytics | chat visible | ANALYTICS | TODO |
| LAYOUT-01.5 | P0-LOCKED | chat panels | composer fixed only partially | independent messages + fixed composer | n/a | scroll test | session | composer visible | AI-UI | TODO |
| LAYOUT-01.6 | P0-LOCKED | global styles | 9/10px customer copy widespread | customer body ≥13/aux ≥12 | n/a | style scan | n/a | readable typography | PRESENTATION | TODO |
| LAYOUT-01.7 | P0-LOCKED | controls | technical actions prominent | business discoverability, technical retreat | n/a | interaction test | demos | clean controls | PRESENTATION | TODO |
| LAYOUT-01.8 | P0-LOCKED | all views | no full viewport audit | no horizontal overflow/overlap/crop/jump | n/a | browser test | transitions | clean screenshots | ALL | TODO |
| ANALYTICS-DELTA-01.1 | P0-LOCKED | AnalyticsView | old right advice split | KPI→horizontal advice→heatmap, right Chat only | analytics | layout test | data | fixed Chat | AI-UI | TODO |
| ANALYTICS-DELTA-01.2 | P0-LOCKED | advice cards | side panel cards | max three horizontal cards | advice | render test | history | horizontal cards | ANALYTICS-01 | TODO |
| ANALYTICS-DELTA-01.3 | P0-LOCKED | advice/chat | agent role mixed | advice proactive, Chat reactive shared session | advice policy | interaction test | session | differentiated roles | AGENT-SESSION | TODO |
| ANALYTICS-DELTA-01.4 | P0-LOCKED | AnalyticsView | duplicated right advice | right column Chat-only | n/a | DOM test | n/a | no advice aside | AI-UI | TODO |

## DEMO-CONTRACT-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEMO-CONTRACT-01.1 | P0-LOCKED | demo service/scenarios | standard flow partly exists | Demo01 S5 autonomous close without forced multiview | demo01 test | UI stage test | LIVE | Demo01 story | EVIDENCE, MAP | PARTIAL |
| DEMO-CONTRACT-01.2 | P0-LOCKED | multiview/service | gate exists but leakage/hardcode risk | Demo02 genuine insufficient→agent fetch→Omnie→verify | demo02 test | timeline test | LIVE 5x | Demo02 chain | EVENT, EVIDENCE | PARTIAL |
| DEMO-CONTRACT-01.3 | P0-LOCKED | spatial/route | geometry presentation gap | Demo03 SC50 true B1→elevator→bridge→A2 | demo03 route | map test | LIVE | cross-building route | WB-MAP | PARTIAL |
| DEMO-CONTRACT-01.4 | P0-LOCKED | scheduler/manual/verifier | semantic flow partly exists | Demo04 zero candidate→explicit human→After→verify | demo04 test | guard test | LIVE | no FlashBot clean | EVIDENCE, AUTHORITY | PARTIAL |
| DEMO-CONTRACT-01.5 | P0-LOCKED | demo controls | control flow may prescribe | recommended story, no forced sequence | trigger tests | UI test | separate demos | flexible controls | SHOW-BASE | TODO |
| DEMO-CONTRACT-01.6 | P0-LOCKED | runtime | different paths possible | shared system, genuinely different facts | suite | visual scenarios | all demos | distinct stories | RUNTIME-SINGLE-PATH | TODO |
| DEMO-CONTRACT-01.7 | P0-LOCKED | test runtime | no current acceptance run | individual LIVE acceptance | opt-in suite | n/a | 01–04 | results recorded | AI-RESILIENCE | TODO |
| DEMO-CONTRACT-01.8 | P0-LOCKED | show/runtime | sequence contract unverified | new show 01→02→03→04 | sequence suite | cross-page test | continuous LIVE | sequence clean | SHOW, OPS | TODO |

## OPS-AUTO-01, AGENT-SESSION-01, AGENT-AUTHORITY-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OPS-AUTO-01.1 | P0-LOCKED | agent/tasks | action cards/manual advance | complete legal instruction automatically executes | agent task test | send test | delivery | no repeat advance | OPS-CONTINUITY | TODO |
| OPS-AUTO-01.2 | P0-LOCKED | task runtime | UI advances states | backend autonomous/paced state progress | task lifecycle | projection test | page switch | clear progression | OPS-CONTINUITY | TODO |
| OPS-AUTO-01.3 | P0-LOCKED | agent | partial parse unknown | incomplete delivery asks clarification | agent policy | chat test | n/a | clear question | AGENT-AUTHORITY | TODO |
| OPS-AUTO-01.4 | P0-LOCKED | agent | mechanical confirmation/action present | explicit complete intent no extra confirmation | policy test | chat test | task creation | direct lawful execution | PRESENTATION | TODO |
| OPS-AUTO-01.5 | P0-LOCKED | agent/scheduler | guard must remain | no LLM cleaning selection | authority test | response test | cleaning | scheduler choice | AGENT-AUTHORITY | PARTIAL |
| AGENT-SESSION-01.1 | P0-LOCKED | provider/session routes/show | localStorage old session reuse | each new Show creates new agent session | lifecycle test | storage reset | restart | no old chat | SHOW-BASE | TODO |
| AGENT-SESSION-01.2 | P0-LOCKED | provider | shared provider exists | same show cross-page session | session test | route test | task | same history | AI-UI | PARTIAL |
| AGENT-SESSION-01.3 | P0-LOCKED | agent tools | session may limit history | new chat can query legal history | read tool test | chat test | archive | historical answer | DATA-BOUNDARY | TODO |
| AGENT-SESSION-01.4 | P0-LOCKED | task/session | old active task leak risk | new show excludes old incomplete task | reset test | projection test | restart | clean current state | OPS-CONTINUITY | TODO |
| AGENT-SESSION-01.5 | P0-LOCKED | advice/session | advice tied to provider state | advice lifecycle separate from Chat | advice test | route test | show | advice remains valid | ANALYTICS | TODO |
| AGENT-AUTHORITY-01.1 | P0-LOCKED | agent/tasks/scheduler | must audit | capability+scheduler exclusively pick cleaner | selection test | answer test | cleaning | no LLM choice | DEMO04 | PARTIAL |
| AGENT-AUTHORITY-01.2 | P0-LOCKED | agent/delivery | adapter tasks exist | FlashBot delivery with all guards | delivery test | chat test | delivery | FlashBot only | OPS-AUTO | TODO |
| AGENT-AUTHORITY-01.3 | P0-LOCKED | agent/relocation | possible auto pick | named robot required | policy test | chat test | relocation | clarification | OPS-AUTO | TODO |
| AGENT-AUTHORITY-01.4 | P0-LOCKED | agent/manual | manual complete card exists | only explicit operator completes human fallback | guard test | no agent action | Demo04 | cannot fake completion | EVIDENCE | PARTIAL |
| AGENT-AUTHORITY-01.5 | P0-LOCKED | agent/tasks | card controls exist | pause/cancel only explicit intent | policy test | chat test | task | correct action | OPS-AUTO | TODO |
| AGENT-AUTHORITY-01.6 | P0-LOCKED | agent/guards | partial guards | no bypass of capability/route/fleet | guard suite | response test | failures | honest rejection | RUNTIME-SINGLE-PATH | PARTIAL |

## OPS-CONTINUITY-01 and AI-RESILIENCE-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OPS-CONTINUITY-01.1 | P0-LOCKED | tasks/service/provider | no autonomous backend runner | page/chat independent task execution | continuity test | route switch | delivery | keeps running | AI-UI | TODO |
| OPS-CONTINUITY-01.2 | P0-LOCKED | workbench/tasks | frontend drives cleaning stages | backend owns truth, frontend projection only | static/runtime test | no advance UI | leave page | true state | RUNTIME-SINGLE-PATH | TODO |
| OPS-CONTINUITY-01.3 | P0-LOCKED | tasks/fleet/map/detail | projections can diverge | one task/event/fleet/map truth | consistency test | integration test | task | same status everywhere | AGENT-SESSION | TODO |
| OPS-CONTINUITY-01.4 | P0-LOCKED | runtime/views | failure projection uneven | all failures identical across views | terminal tests | error render | failure runs | honest terminal | AI-RESILIENCE | TODO |
| OPS-CONTINUITY-01.5 | P0-LOCKED | show/tasks | old task resume risk | show boundary isolates prior active work | reset suite | storage test | new show | current clean | SHOW-BASE | TODO |
| OPS-CONTINUITY-01.6 | P0-LOCKED | demo service/workbench | hidden-page stage drive stops | Demo01–04 advance absent Workbench | demo continuity | navigate test | live demos | returns consistent | DEMO-CONTRACT | TODO |
| AI-RESILIENCE-01.1 | P0-LOCKED | qwen/service/agent | no classified one retry | one retry transient technical only | fault injection | customer state test | provider failure | no retry UI detail | DEMO-CONTRACT | TODO |
| AI-RESILIENCE-01.2 | P0-LOCKED | service | business retry boundary unverified | zero retry semantic/guard failures | unit suite | n/a | insufficiency/route | honest branch | EVIDENCE | TODO |
| AI-RESILIENCE-01.3 | P0-LOCKED | service/views | immediate terminal partly | second transient failure HUMAN_REVIEW/release | fault test | customer failure card | live fault | safe outcome | SHOW-BASE | TODO |
| AI-RESILIENCE-01.4 | P0-LOCKED | replay/service | replay mode exists | LIVE never silent replay | replay test | badge test | live failure | truthful mode | RUNTIME-SINGLE-PATH | PARTIAL |
| AI-RESILIENCE-01.5 | P0-LOCKED | detail/chat | raw error could leak | customer hides attempts/HTTP | redaction | copy test | retry | simple status | PRESENTATION | TODO |
| AI-RESILIENCE-01.6 | P0-LOCKED | demo service | lock behavior unknown | terminal failure frees triggers | failure suite | trigger test | failure | next demo allowed | SHOW-BASE | TODO |

## EVIDENCE-INTEGRITY-01

| Sub-item | Priority | Affected active code | Current implementation / divergence | Required implementation / dependencies | Backend tests | Frontend tests | Runtime tests | Visual acceptance | Cross-requirement regression | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EVIDENCE-INTEGRITY-01.1 | P0-LOCKED | demo service/read models | full manifest in event snapshot | public view exposes primary/metadata/edge only | stage gate | payload view test | detected | no future After | WB-CAMERA, EVENT | TODO |
| EVIDENCE-INTEGRITY-01.2 | P0-LOCKED | multiview/service/tools | manifest supplies unacquired supporting images | acquired evidence set after real fetch only | agent gate | UI evidence test | Demo02 | selected fetched only | EVENT, REPLAY | TODO |
| EVIDENCE-INTEGRITY-01.3 | P0-LOCKED | service/verifier | after stored early/readable | release After after true cleaning only | transition guard | stage rendering | Demo01-03 | no premature After | WB-DETAIL | TODO |
| EVIDENCE-INTEGRITY-01.4 | P0-LOCKED | manual order/verifier | after asset inferable | explicit human completion before release | guard test | no premature card | Demo04 | no agent inference | AGENT-AUTHORITY | TODO |
| EVIDENCE-INTEGRITY-01.5 | P0-LOCKED | verifier/service | closure facts need gate | verification uses new released After only | verifier test | closure UI test | demos | robot complete != closed | DEMO-CONTRACT | TODO |
| EVIDENCE-INTEGRITY-01.6 | P0-LOCKED | replay | replay public evidence audit missing | same temporal gates as LIVE | replay suite | stage test | replay 3x | no future evidence | RUNTIME-SINGLE-PATH | TODO |
| EVIDENCE-INTEGRITY-01.7 | P0-LOCKED | archive/read model | history reads raw manifest | terminal event can show actual full chain | archive test | history render | terminal | complete audit history | EVENT | TODO |
| EVIDENCE-INTEGRITY-01.8 | P0-LOCKED | agent tools | camera evidence returns full manifest | tools gate by state + acquired set | tool tests | chat output test | active event | no leaked asset | AGENT-AUTHORITY | TODO |

## Completion protocol

Before changing any row to `IMPLEMENTED_PENDING_USER_ACCEPTANCE`, record the implemented code, exact test evidence, visual evidence, and cross-regression result in that row. `USER_ACCEPTED` is forbidden until the user performs visual acceptance.

## Final recovery execution evidence — 2026-08-30

This update records completed implementation evidence without relabeling an
unverified visual target as accepted. All implementation claims below remain
`IMPLEMENTED_PENDING_USER_ACCEPTANCE`; no item is `USER_ACCEPTED`.

| Scope | Implemented code | Automated evidence | LIVE / visual evidence | Status |
| --- | --- | --- | --- | --- |
| AI readiness contract | `backend/perception/config.py`, `backend/perception/service.py`, `/api/system/ai-readiness/probe` | `test_ai_lab` covers cloud-without-YOLO, YOLO-without-cloud and key-missing projection; secret-free API projection | Real probe: `qwen-vl-max=READY`, `qwen3-vl-plus=READY`, controlled edge ready, local YOLO absent | IMPLEMENTED_PENDING_USER_ACCEPTANCE |
| Official live demos | `backend/demo_v1/service.py`, `backend/acceptance/unified.py` | demo/runtime tests; stage/evidence tests | Isolated continuous LIVE diagnostics: Demo01–04 all `CLOSED`, all semantic and verification sources `LIVE_MODEL`; Demo03 route contains B1 → elevator → B2 → skybridge → A2 | IMPLEMENTED_PENDING_USER_ACCEPTANCE |
| Demo02 evidence regression | `backend/demo_v1/service.py`, `backend/robot_operations/tools.py` | evidence temporal-gate test and multiview unit coverage | 5/5 isolated real LIVE runs passed; 5/5 acquired lawful supporting camera evidence through the Multi-view Agent | IMPLEMENTED_PENDING_USER_ACCEPTANCE |
| Evidence temporal projection | `backend/demo_v1/service.py`, `backend/robot_operations/tools.py`, `backend/api/routes.py` | `test_public_evidence_projection_never_releases_future_assets` | Before only at detection; After released only after verification state | IMPLEMENTED_PENDING_USER_ACCEPTANCE |
| Show / Agent session | `backend/robot_operations/repository.py`, routes, provider, `start_demo.command` | `test_new_show_session_resets_only_current_fleet_and_agent_context` | Launcher flow creates fresh show and Agent session while preserving archive/history | IMPLEMENTED_PENDING_USER_ACCEPTANCE |
| Customer AI shell | `RobotOperationsPanel.tsx`, model/provider, `AnalyticsView.tsx` | frontend test suite: 46/46; production build passes | Browser viewport capture remains pending because the current localhost backend is an unowned process and the in-app browser cannot reach the launcher-owned surface | IMPLEMENTED_PENDING_USER_ACCEPTANCE |

### Final execution counts

| Total locked sub-items | Code/test/LIVE evidence recorded | Blocked by external provider | Remaining visual or implementation verification |
| ---: | ---: | ---: | ---: |
| 191 | 31 shared/runtime/UI targets with direct evidence | 0 | 160 rows remain in their original TODO/PARTIAL state and must not be represented as complete |

The remaining rows are not reclassified merely because shared infrastructure
changed. In particular, complete browser screenshots at 1440×900 and
1920×1080, every customer-copy scan, all agent conversational acceptance
cases, and the remaining Matrix-row-to-test mapping still require completion.
