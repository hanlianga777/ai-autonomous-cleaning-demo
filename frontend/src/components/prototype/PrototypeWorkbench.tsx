import { BarChart3, CircleDot, ClipboardList, LayoutDashboard, Settings2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { CameraMonitorGrid } from "./CameraMonitorGrid";
import { AnalyticsView } from "./AnalyticsView";
import { EventArchiveView } from "./EventArchiveView";
import { EventDetailPanel } from "./EventDetailPanel";
import { scenarios, stageCopy } from "./data";
import { SpatialDispatchView } from "./SpatialDispatchView";
import { PanelBoundary } from "./PanelBoundary";
import { displayStates, fromStoredEvent } from "./eventViewModel";
import { canApplySnapshot, claimStage, loadEventSnapshot, readRequestKeys } from "./runtimeSession";
import type { ActiveEvent } from "./types";

type WorkbenchView = "workbench" | "events" | "analytics" | "advanced";
function viewFromPath(): WorkbenchView {
  const path = window.location.pathname;
  return path === "/events" ? "events" : path === "/analytics" ? "analytics" : path === "/advanced" ? "advanced" : "workbench";
}

export function PrototypeWorkbench() {
  const [event, setEvent] = useState<ActiveEvent | null>(null);
  const [view, setView] = useState<WorkbenchView>(viewFromPath);
  const [runtimeMode, setRuntimeMode] = useState<"live" | "replay">("live");
  const [restoring, setRestoring] = useState(true);
  const [syncNotice, setSyncNotice] = useState("");
  const submittedStages = useRef(new Set<string>(readStageRequests()));

  const navigate = (next: WorkbenchView) => {
    window.history.pushState({}, "", next === "workbench" ? "/prototype" : `/${next}`);
    setView(next);
  };
  useEffect(() => {
    const restoreRoute = () => setView(viewFromPath());
    window.addEventListener("popstate", restoreRoute);
    window.addEventListener("cleanops:navigate", restoreRoute);
    return () => { window.removeEventListener("popstate", restoreRoute); window.removeEventListener("cleanops:navigate", restoreRoute); };
  }, []);

  // Store only the event identifier, never a second copy of runtime facts.
  useEffect(() => {
    const controller = new AbortController();
    const eventId = readUiStorage("cleanops.current-event");
    if (!eventId) { setRestoring(false); return; }
    loadEventSnapshot(eventId, controller.signal)
      .then(setEvent)
      .catch((error) => { if (error.name !== "AbortError") setSyncNotice(error.message); })
      .finally(() => setRestoring(false));
    return () => controller.abort();
  }, []);

  const applyStageResponse = (result: Record<string, unknown>) => {
    setEvent((current) => {
      if (!current) return current;
      if (!canApplySnapshot(current, result)) return current;
      const backendState = String(result.state ?? result.status ?? current.backendState ?? "DETECTED");
      const steps = Array.isArray(result.transitions) ? result.transitions.map((item) => displayStates[item.state]).filter(Boolean) : current.scenario.steps;
      return { ...current, scenario: { ...current.scenario, steps }, stageIndex: stageIndexFor(steps, backendState), liveResult: result, backendState, inFlightState: undefined, processing: false };
    });
  };

  const callStage = async (action: string, inFlightState?: ActiveEvent["inFlightState"]) => {
    const eventId = String(event?.liveResult?.event_id ?? "");
    if (view !== "workbench" || !eventId || !event || event.processing) return;
    // One request per durable stage. A transport failure must not cause an
    // effect-driven retry storm or repeat an already completed cloud call.
    if (!claimStage(submittedStages.current, eventId, action)) return;
    saveStageRequests(submittedStages.current);
    if (inFlightState) setEvent((current) => current && ({ ...current, inFlightState, processing: true, stageIndex: stageIndexFor(current.scenario.steps, inFlightState) }));
    else setEvent((current) => current && ({ ...current, processing: true }));
    try {
      const response = await fetch(`/api/demo-v1/events/${encodeURIComponent(eventId)}/${action}`, { method: "POST" });
      const result = await response.json() as Record<string, unknown>;
      if (!response.ok) throw new Error(String(result.detail ?? "阶段执行失败"));
      applyStageResponse(result);
    } catch (error) {
      setSyncNotice("阶段请求结果尚不确定，已停止重复提交。可读取已保存状态；不会自动重发云端请求。");
      setEvent((current) => current && ({ ...current, processing: false, inFlightState: undefined, liveResult: { ...current.liveResult, reason: error instanceof Error ? error.message : "阶段服务暂不可用" } }));
    }
  };

  useEffect(() => {
    if (view !== "workbench" || !event || event.processing) return;
    const state = event.backendState;
    const next = state === "DETECTED" ? ["edge-review", "EDGE_DETECTED"] as const
      : state === "EDGE_DETECTED" ? ["cloud-review", "CLOUD_REVIEW"] as const
      : state === "CLOUD_REVIEW" ? ["locate", "LOCATING"] as const
      : state === "LOCATED" ? ["assign", "ROBOT_ASSIGNED"] as const
      : state === "ASSIGNED" ? ["start-navigation", "NAVIGATING"] as const
      : state === "ARRIVED" ? ["complete-cleaning", "CLEANING"] as const
      : state === "CLEANING_COMPLETED" ? ["verify", "VERIFYING"] as const
      : null;
    if (!next) return;
    // This queues a real backend transition; it is not a timer-driven
    // presentation timeline.  Cloud/verification duration remains the only
    // observable model latency and comes from the backend response.
    let cancelled = false;
    queueMicrotask(() => { if (!cancelled) void callStage(next[0], next[1]); });
    return () => { cancelled = true; };
  }, [view, event?.backendState, event?.processing, event?.scenario.id]);

  // A reload during a cloud call observes SQLite instead of sending it again.
  useEffect(() => {
    const eventId = String(event?.liveResult?.event_id ?? "");
    if (view !== "workbench" || !eventId || ["CLOSED", "HUMAN_REVIEW", "HUMAN_FALLBACK"].includes(event?.backendState ?? "")) return;
    const controller = new AbortController();
    const timer = window.setInterval(() => {
      fetch(`/api/events/${encodeURIComponent(eventId)}`, { signal: controller.signal })
        .then((r) => r.ok ? r.json() : null)
        .then((stored) => { if (stored) applyStageResponse(fromStoredEvent(stored).liveResult ?? {}); })
        .catch(() => { /* The stage request owns the visible transport error. */ });
    }, 1200);
    return () => { window.clearInterval(timer); controller.abort(); };
  }, [view, event?.liveResult?.event_id, event?.backendState]);

  const trigger = async (id: typeof scenarios[number]["id"]) => {
    if (restoring) return;
    if (event && (event.processing || !["CLOSED", "HUMAN_REVIEW"].includes(event.backendState ?? ""))) return;
    const scenario = scenarios.find((item) => item.id === id);
    if (!scenario) return;
    setSyncNotice("");
    const demoId = { outdoor: "demo01", liquid: "demo02", can: "demo03", oversized: "demo04" }[id];
    setEvent({ scenario, stageIndex: 0, startedAt: new Date().toISOString(), processing: true });
    try {
      const response = await fetch(`/api/demo-v1/events?demo_id=${demoId}&mode=${runtimeMode}`, { method: "POST" });
      const result = await response.json() as Record<string, unknown>;
      if (!response.ok) throw new Error(String(result.detail ?? "无法创建事件"));
      writeUiStorage("cleanops.current-event", String(result.event_id));
      applyStageResponse(result);
    } catch { setEvent(null); setSyncNotice("创建事件未成功确认，未显示虚构的人工复核记录。请检查连接及事件中心后再操作。"); }
  };
  const completeManual = async () => {
    const eventId = String(event?.liveResult?.event_id ?? "");
    if (!eventId || !event || event.processing || event.backendState !== "HUMAN_FALLBACK") return;
    setEvent((current) => current && ({ ...current, inFlightState: "VERIFYING", processing: true, stageIndex: stageIndexFor(current.scenario.steps, "VERIFYING") }));
    try {
      const response = await fetch(`/api/demo-v1/manual-work-orders/${encodeURIComponent(eventId)}/complete`, { method: "POST" });
      const result = await response.json() as Record<string, unknown>;
      if (!response.ok) throw new Error(String(result.detail ?? "人工验收服务不可用"));
      applyStageResponse(result);
    } catch (error) { setEvent((current) => current && ({ ...current, processing: false, inFlightState: undefined, liveResult: { ...current.liveResult, reason: error instanceof Error ? error.message : "人工验收服务不可用" } })); }
  };
  const state = event ? currentDisplayState(event) : "IDLE";
  const syncSavedState = async () => {
    const id = String(event?.liveResult?.event_id ?? readUiStorage("cleanops.current-event") ?? "");
    if (!id) return;
    try {
      const saved = await loadEventSnapshot(id);
      if (event) applyStageResponse(saved.liveResult ?? {}); else setEvent(saved);
      setSyncNotice("已读取最新保存状态；未重发之前的阶段请求。若状态未变化，请保留事件并在高级模式排查。");
    } catch (error) { setSyncNotice(error instanceof Error ? error.message : "同步服务暂不可用。"); }
  };
  return <div className="min-h-screen bg-[#f6f7f8] text-slate-900">
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-[200px] border-r border-slate-200 bg-white lg:flex lg:flex-col"><div className="flex h-[54px] items-center gap-2.5 border-b border-slate-200 px-4"><div className="flex h-7 w-7 items-center justify-center bg-slate-900 text-[9px] font-bold text-white">CO</div><div><p className="text-sm font-semibold">CleanOps</p><p className="text-[9px] tracking-[0.12em] text-slate-400">自主清洁</p></div></div><nav className="space-y-1 px-2.5 py-4"><NavItem icon={LayoutDashboard} label="自主清洁工作台" active={view === "workbench"} onClick={() => navigate("workbench")} /><NavItem icon={ClipboardList} label="事件中心" active={view === "events"} onClick={() => navigate("events")} /><NavItem icon={BarChart3} label="运营分析" active={view === "analytics"} onClick={() => navigate("analytics")} /><NavItem icon={Settings2} label="高级模式" active={view === "advanced"} onClick={() => navigate("advanced")} /></nav></aside>
<div className="lg:ml-[200px]"><header className="flex h-[54px] items-center justify-between border-b border-slate-200 bg-white px-4 lg:px-5"><div className="flex items-center gap-2"><p className="text-sm font-semibold">{view === "workbench" ? "自主清洁工作台" : view === "events" ? "事件中心" : view === "analytics" ? "运营分析" : "高级模式"}</p>{view === "workbench" && <span className={`hidden items-center gap-1.5 text-[11px] md:flex ${event ? "text-slate-700" : "text-slate-500"}`}><CircleDot size={12} className={event?.processing ? "animate-pulse text-rose-500" : "text-emerald-500"} />{stageCopy[state].title}</span>}</div><span className="border border-slate-200 px-2 py-1 text-[10px] font-medium tracking-wide text-slate-600">{view !== "workbench" && view !== "advanced" ? "只读运营视图" : event?.liveResult?.mode === "STABLE_REPLAY" ? "STABLE REPLAY" : event?.liveResult?.mode === "LIVE" ? "LIVE" : runtimeMode === "live" ? "LIVE · 下次运行" : "STABLE REPLAY · 下次运行"}</span></header>
      {view === "workbench" && <main className="h-[calc(100vh-54px)] min-h-[626px] p-2.5 lg:p-3"><div className="grid h-full grid-cols-1 gap-3 lg:grid-cols-[minmax(0,72fr)_minmax(320px,28fr)]"><div className="grid min-h-0 grid-rows-[minmax(180px,31fr)_minmax(360px,69fr)] gap-3"><CameraMonitorGrid event={event} onTrigger={trigger} /><PanelBoundary name="空间调度视图"><SpatialDispatchView event={event} onNavigationComplete={() => void callStage("complete-navigation")} /></PanelBoundary></div><div className="flex min-h-0 flex-col">{(restoring || syncNotice) && <div role="status" className="shrink-0 border border-amber-200 bg-amber-50 p-2 text-[11px] leading-5 text-amber-900">{restoring ? "正在恢复事件记录…" : syncNotice}{!restoring && <button onClick={() => void syncSavedState()} className="ml-2 border border-amber-300 bg-white px-2">同步已保存状态</button>}</div>}<EventDetailPanel event={event} onCompleteManual={completeManual} /></div></div></main>}
      {view === "events" && <EventArchiveView />}{view === "analytics" && <AnalyticsView />}{view === "advanced" && <AdvancedView event={event} runtimeMode={runtimeMode} onRuntimeModeChange={setRuntimeMode} />}
    </div>
  </div>;
}

function readUiStorage(key: string): string | null { try { return localStorage.getItem(key); } catch { return null; } }
function writeUiStorage(key: string, value: string) { try { localStorage.setItem(key, value); } catch { /* Private mode may disallow UI persistence. */ } }
function readStageRequests(): string[] { try { return [...readRequestKeys(sessionStorage.getItem("cleanops.stage-requests"))]; } catch { return []; } }
function saveStageRequests(keys: Set<string>) { try { sessionStorage.setItem("cleanops.stage-requests", JSON.stringify([...keys])); } catch { /* In-memory guard remains active. */ } }

function stateIndex(state: string): number {
  return { DETECTED: 0, EDGE_DETECTED: 1, MULTI_VIEW: 2, CLOUD_REVIEW: 3, LOCATED: 4, ASSIGNED: 5, NAVIGATING: 6, ARRIVED: 7, CLEANING_COMPLETED: 8, VERIFYING: 9, CLOSED: 10, HUMAN_FALLBACK: 11, HUMAN_REVIEW: 12 }[state] ?? 0;
}

function stageIndexFor(steps: ActiveEvent["scenario"]["steps"], state: string): number {
  const presentation: Record<string, ActiveEvent["scenario"]["steps"][number]> = { DETECTED: "DISCOVERED", EDGE_DETECTED: "EDGE_DETECTED", MULTI_VIEW: "MULTI_VIEW", CLOUD_REVIEW: "CLOUD_REVIEW", LOCATED: "LOCATING", ASSIGNED: "ROBOT_ASSIGNED", NAVIGATING: "NAVIGATING", ARRIVED: "CLEANING", CLEANING_COMPLETED: "CLEANING", VERIFYING: "VERIFYING", CLOSED: "CLOSED", HUMAN_FALLBACK: "HUMAN_FALLBACK", HUMAN_REVIEW: "HUMAN_REVIEW" };
  const target = presentation[state] ?? "DISCOVERED";
  const index = steps.indexOf(target);
  return index >= 0 ? index : Math.min(stateIndex(state), steps.length - 1);
}

function currentDisplayState(event: ActiveEvent) { return event.inFlightState ?? displayStates[event.backendState ?? ""] ?? "DISCOVERED"; }

function NavItem({ icon: Icon, label, active = false, onClick }: { icon: typeof LayoutDashboard; label: string; active?: boolean; onClick: () => void }) {
  return <button type="button" onClick={onClick} className={`flex w-full items-center gap-2.5 px-3 py-2.5 text-left text-sm transition-colors ${active ? "bg-slate-900 font-medium text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"}`}><Icon size={16} strokeWidth={1.7} />{label}</button>;
}

function AdvancedView({ event, runtimeMode, onRuntimeModeChange }: { event: ActiveEvent | null; runtimeMode: "live" | "replay"; onRuntimeModeChange: (mode: "live" | "replay") => void }) {
  const [status, setStatus] = useState<Record<string, any> | null>(null);
  useEffect(() => { fetch("/api/system/ai-status").then((r) => r.json()).then(setStatus).catch(() => setStatus(null)); }, []);
  const review = event?.liveResult?.qwen_review as Record<string, unknown> | undefined;
  const ready = Boolean(status?.qwen_vl?.api_key_configured);
  return <main className="mx-auto max-w-[1200px] p-5 lg:p-7"><p className="text-xl font-semibold">高级模式</p><p className="mt-1 text-xs text-slate-500">技术审计、接口运行状态与演示回放边界。不会展示或保存任何 API Key。</p><section className="mt-4 flex flex-wrap items-center justify-between gap-3 border border-slate-200 bg-white px-4 py-3"><div><p className="text-xs font-semibold text-slate-700">AI Runtime</p><p className="mt-1 text-[11px] text-slate-500">云端模型：{ready ? "已配置" : "未配置"} · 最近请求：{String(review?.provider ?? "Idle")} · 最近延迟：{review?.elapsed_ms ? `${review.elapsed_ms} ms` : "—"}</p></div><div className="flex border border-slate-200 p-0.5"><button type="button" onClick={() => onRuntimeModeChange("live")} className={`px-3 py-1.5 text-xs ${runtimeMode === "live" ? "bg-slate-900 text-white" : "text-slate-600"}`}>LIVE</button><button type="button" onClick={() => onRuntimeModeChange("replay")} className={`px-3 py-1.5 text-xs ${runtimeMode === "replay" ? "bg-slate-900 text-white" : "text-slate-600"}`}>Stable Replay</button></div></section><p className="mt-2 text-[11px] text-slate-500">Stable Replay 仅复用已保存的真实云端结构化响应；空间定位、调度、路线、Fleet、SQLite 阶段和验收仍会重新运行。LIVE 失败不会自动切换回放。</p><div className="mt-5 grid gap-4 md:grid-cols-2"><Tech title="AI 感知链路" lines={["受控边缘检测 → 单视角云端 → 证据不足时自主补证 → 最终语义判断", "输出统一 TaskProfile / CleaningEvent schema", `当前事件：${event?.scenario.id ?? "无"}`]} /><Tech title="空间与调度" lines={["Camera → SLAM 复用 Phase 2 坐标映射", "Capability Engine 与 Scheduler 为唯一机器人选择器", "Robot-first + Human Fallback 规则保持不变"]} /><Tech title="模型与接口状态" lines={[`服务状态：${status ? "可访问" : "暂不可用"}`, `本次模型：${String(review?.model ?? "尚无调用")}`, `最近耗时：${review?.elapsed_ms ? `${review.elapsed_ms} ms` : "—"}`, "Trace ID：独立 Trace Inspector 待 P1-H；当前以 Event ID 关联"]} /><Tech title="演示与回放" lines={["LIVE：实际调用已配置的云端模型", "稳定回放：明确受控回放，不伪装为实时推理", "异常时停止自动派单并转人工复核"]} /></div>{event?.liveResult && <pre className="mt-5 max-h-[360px] overflow-auto border border-slate-200 bg-white p-4 text-[10px] leading-5 text-slate-600">{JSON.stringify({ event_id: event.liveResult.event_id, edge: event.liveResult.controlled_yolo, cloud: review, first_review: event.liveResult.first_qwen_review, second_review: event.liveResult.second_qwen_review, evidence_fusion: event.liveResult.evidence_fusion, spatial: event.liveResult.spatial_location }, null, 2)}</pre>}</main>;
}
function Tech({ title, lines }: { title: string; lines: string[] }) { return <section className="border border-slate-200 bg-white p-5"><p className="text-sm font-semibold">{title}</p>{lines.map((line) => <p key={line} className="mt-2 text-xs leading-5 text-slate-600">{line}</p>)}</section>; }
