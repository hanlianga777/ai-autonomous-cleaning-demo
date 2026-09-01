import { BarChart3, Bot, ClipboardList, LayoutDashboard, Settings2 } from "lucide-react";
import { useEffect, useState } from "react";
import { CameraMonitorGrid } from "./CameraMonitorGrid";
import { AnalyticsView } from "./AnalyticsView";
import { AdvancedView } from "./AdvancedView";
import { EventArchiveView } from "./EventArchiveView";
import { EventDetailPanel } from "./EventDetailPanel";
import { scenarios } from "./data";
import { SpatialDispatchView } from "./SpatialDispatchView";
import { useNavigationPresentation } from "./navigationPresentation";
import { PanelBoundary } from "./PanelBoundary";
import { displayStates, fromStoredEvent, isAutoProgressingState } from "./eventViewModel";
import { archiveDemoEntryUrl } from "./eventArchiveModel";
import { canApplySnapshot, canStartDemo, isTerminalEvent, loadEventSnapshot, operationsOwnsEvent } from "./runtimeSession";
import { FloatingRobotOperationsAgent } from "@/components/robot-operations/RobotOperationsPanel";
import { RobotOperationsProvider } from "@/components/robot-operations/RobotOperationsProvider";
import { archivePageContext } from "@/components/robot-operations/robotOperationsModel";
import type { ActiveEvent } from "./types";

type WorkbenchView = "workbench" | "events" | "analytics" | "advanced";
function viewFromPath(): WorkbenchView {
  const path = window.location.pathname;
  return path === "/events" ? "events" : path === "/analytics" ? "analytics" : path === "/advanced" ? "advanced" : "workbench";
}

function recordValue(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : null;
}

/** Only real current-workbench resources are sent with a Workbench Agent turn. */
function workbenchAgentPageContext(event: ActiveEvent | null, runtimeMode: "live" | "replay"): Record<string, unknown> {
  const snapshot = event?.liveResult ?? null;
  const spatial = recordValue(snapshot?.spatial_location);
  const decision = recordValue(snapshot?.assignment_decision);
  const fleetSnapshot = Array.isArray(snapshot?.fleet_snapshot)
    ? snapshot.fleet_snapshot.slice(0, 4).map((item) => {
      const robot = recordValue(item);
      return robot ? { id: robot.id, name: robot.name, status: robot.status, battery: robot.battery, location: robot.location } : null;
    }).filter(Boolean)
    : null;
  return {
    page: "workbench",
    runtime_mode: runtimeMode,
    selected_event_id: typeof snapshot?.event_id === "string" ? snapshot.event_id : null,
    current_event: event ? {
      event_id: typeof snapshot?.event_id === "string" ? snapshot.event_id : null,
      camera_id: typeof snapshot?.camera_id === "string" ? snapshot.camera_id : event.scenario.cameraId,
      map_id: typeof spatial?.map_id === "string" ? spatial.map_id : null,
      state: typeof snapshot?.state === "string" ? snapshot.state : event.backendState ?? null,
      location: typeof spatial?.label === "string" ? spatial.label : null,
      robot_id: typeof decision?.selected_robot_id === "string" ? decision.selected_robot_id : null,
      fleet_resource: "/api/robots",
      fleet_snapshot: fleetSnapshot,
    } : null,
  };
}

export function PrototypeWorkbench() {
  const [event, setEvent] = useState<ActiveEvent | null>(null);
  const [view, setView] = useState<WorkbenchView>(viewFromPath);
  const [runtimeMode, setRuntimeMode] = useState<"live" | "replay">("live");
  const [restoring, setRestoring] = useState(true);
  const [runtimeReady, setRuntimeReady] = useState(false);
  const [workbenchEntry, setWorkbenchEntry] = useState(0);
  const [syncNotice, setSyncNotice] = useState("");
  const [archiveAgentContext, setArchiveAgentContext] = useState<Record<string, unknown>>(() => archivePageContext(null, null, {}));

  const navigate = (next: WorkbenchView, eventId?: string) => {
    setRuntimeReady(false);
    if (next === "workbench") { setRestoring(true); setWorkbenchEntry((entry) => entry + 1); }
    window.history.pushState({}, "", eventId && next === "events" ? archiveDemoEntryUrl(eventId) : next === "workbench" ? "/prototype" : `/${next}`);
    setView(next);
  };
  useEffect(() => {
    const restoreRoute = () => {
      const next = viewFromPath();
      setRuntimeReady(false);
      if (next === "workbench") { setRestoring(true); setWorkbenchEntry((entry) => entry + 1); }
      setView(next);
    };
    window.addEventListener("popstate", restoreRoute);
    window.addEventListener("cleanops:navigate", restoreRoute);
    return () => { window.removeEventListener("popstate", restoreRoute); window.removeEventListener("cleanops:navigate", restoreRoute); };
  }, []);

  // A launcher creates a server-authoritative Show Session.  Browser storage
  // belongs only to that session: a fresh show is always IDLE, never an
  // accidental restoration of a prior local event.
  useEffect(() => {
    if (view !== "workbench") return;
    const controller = new AbortController();
    setRestoring(true);
    setRuntimeReady(false);
    const restore = async () => {
      const response = await fetch("/api/robot-operations/show-session", { signal: controller.signal });
      if (!response.ok) throw new Error("无法确认当前 Show Session");
      const payload = await response.json() as { show_session?: { id?: string } | null };
      const showId = payload.show_session?.id;
      const storedShowId = readUiStorage("cleanops.workbench-show-session.v1");
      if (!showId || storedShowId !== showId) {
        removeUiStorage("cleanops.current-event");
        removeUiStorage("cleanops.stage-requests");
        if (showId) writeUiStorage("cleanops.workbench-show-session.v1", showId);
        setEvent(null);
        setSyncNotice("");
        return;
      }
      const eventId = readUiStorage("cleanops.current-event");
      if (!eventId) { setEvent(null); setSyncNotice(""); return; }
      const saved = await loadEventSnapshot(eventId, controller.signal);
      if (controller.signal.aborted) return;
      setEvent(saved);
      setSyncNotice("");
    };
    restore()
      .then((saved) => {
        void saved;
        setRuntimeReady(true);
      })
      .catch((error) => { if (!controller.signal.aborted) setSyncNotice(`${error.message} 自动推进已停止，请同步已保存状态。`); })
      .finally(() => { if (!controller.signal.aborted) setRestoring(false); });
    return () => controller.abort();
  }, [view, workbenchEntry]);

  const applyStageResponse = (result: Record<string, unknown>) => {
    setEvent((current) => {
      if (!current) return current;
      if (!canApplySnapshot(current, result)) return current;
      const backendState = String(result.state ?? result.status ?? current.backendState ?? "DETECTED");
      const steps = Array.isArray(result.transitions) ? result.transitions.map((item) => displayStates[item.state]).filter(Boolean) : current.scenario.steps;
      return { ...current, scenario: { ...current.scenario, steps }, stageIndex: stageIndexFor(steps, backendState), liveResult: result, backendState, inFlightState: undefined, processing: isAutoProgressingState(backendState) };
    });
  };

  // The browser polls only the backend projection. It never advances a stage;
  // the authoritative runtime continues while this page is hidden or unmounted.
  useEffect(() => {
    const eventId = String(event?.liveResult?.event_id ?? "");
    if (view !== "workbench" || restoring || !runtimeReady || !eventId || isTerminalEvent(event)) return;
    const controller = new AbortController();
    const timer = window.setInterval(() => {
      fetch(`/api/demo-v1/events/${encodeURIComponent(eventId)}`, { signal: controller.signal })
        .then((r) => r.ok ? r.json() : null)
        .then((stored) => { if (stored) applyStageResponse(fromStoredEvent(stored).liveResult ?? {}); })
        .catch(() => { /* The stage request owns the visible transport error. */ });
    }, 1200);
    return () => { window.clearInterval(timer); controller.abort(); };
  }, [view, restoring, runtimeReady, event?.liveResult?.event_id, event?.backendState]);

  const trigger = async (id: typeof scenarios[number]["id"]) => {
    if (restoring || !runtimeReady) return;
    if (!canStartDemo(event)) return;
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
    // Task-owned events have one mutation owner: the shared Operations task
    // card. Workbench is only a synchronised read model in that case.
    if (restoring || !runtimeReady || !eventId || !event || operationsOwnsEvent(event) || event.processing || event.backendState !== "HUMAN_FALLBACK") return;
    setEvent((current) => current && ({ ...current, inFlightState: "VERIFYING", processing: true, stageIndex: stageIndexFor(current.scenario.steps, "VERIFYING") }));
    try {
      const response = await fetch(`/api/demo-v1/manual-work-orders/${encodeURIComponent(eventId)}/complete`, { method: "POST" });
      const result = await response.json() as Record<string, unknown>;
      if (!response.ok) throw new Error(String(result.detail ?? "人工验收服务不可用"));
      applyStageResponse(result);
    } catch (error) { setEvent((current) => current && ({ ...current, processing: false, inFlightState: undefined, liveResult: { ...current.liveResult, reason: error instanceof Error ? error.message : "人工验收服务不可用" } })); }
  };
  const syncSavedState = async () => {
    const id = String(event?.liveResult?.event_id ?? readUiStorage("cleanops.current-event") ?? "");
    if (!id) return;
    try {
      const saved = await loadEventSnapshot(id);
      if (event) applyStageResponse(saved.liveResult ?? {}); else setEvent(saved);
      setRuntimeReady(true);
      setSyncNotice("已读取最新保存状态；未重发之前的阶段请求。若状态未变化，请保留事件并在高级模式排查。");
    } catch (error) { setSyncNotice(error instanceof Error ? error.message : "同步服务暂不可用。"); }
  };
  const agentPageContext = view === "events"
    ? archiveAgentContext
    : workbenchAgentPageContext(event, runtimeMode);
  const spatialEvent = runtimeReady ? event : null;
  const navigationPresentation = useNavigationPresentation(spatialEvent);
  return <RobotOperationsProvider><div className="min-h-screen bg-[#f6f7f8] text-slate-900">
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-[200px] border-r border-slate-200 bg-white lg:flex lg:flex-col"><div className="flex h-[54px] items-center gap-2.5 border-b border-slate-200 px-4"><div className="flex h-7 w-7 items-center justify-center bg-slate-900 text-white"><Bot size={16} /></div><div><p className="text-sm font-semibold">AI Cleaning</p><p className="text-[10px] text-slate-400">园区运营</p></div></div><nav className="space-y-1 px-2.5 py-4"><NavItem icon={LayoutDashboard} label="AI机器人调度大脑" active={view === "workbench"} onClick={() => navigate("workbench")} /><NavItem icon={ClipboardList} label="事件中心" active={view === "events"} onClick={() => navigate("events")} /><NavItem icon={BarChart3} label="运营分析" active={view === "analytics"} onClick={() => navigate("analytics")} /><NavItem icon={Settings2} label="高级模式" active={view === "advanced"} onClick={() => navigate("advanced")} /></nav></aside>
<div className="lg:ml-[200px]"><header className="flex h-[54px] items-center justify-between border-b border-slate-200 bg-white px-4 lg:px-5"><div className="flex items-center gap-2"><p className="text-sm font-semibold">{view === "workbench" ? "AI机器人调度大脑" : view === "events" ? "事件中心" : view === "analytics" ? "运营分析" : "高级模式"}</p></div></header>
      {view === "workbench" && <main className="h-[calc(100vh-54px)] min-h-[626px] p-2.5 lg:p-3"><div className="grid h-full grid-cols-1 gap-3 lg:grid-cols-[minmax(0,72fr)_minmax(320px,28fr)]"><div className="grid min-h-0 grid-rows-[minmax(180px,31fr)_minmax(360px,69fr)] gap-3"><CameraMonitorGrid event={event} onTrigger={trigger} /><PanelBoundary name="空间调度视图"><SpatialDispatchView event={spatialEvent} presentation={navigationPresentation} /></PanelBoundary></div><div className="flex min-h-0 flex-col">{(restoring || syncNotice) && <div role="status" className="shrink-0 border border-amber-200 bg-amber-50 p-2 text-[11px] leading-5 text-amber-900">{restoring ? "正在恢复事件记录…" : syncNotice}{!restoring && <button onClick={() => void syncSavedState()} className="ml-2 border border-amber-300 bg-white px-2">同步已保存状态</button>}</div>}<EventDetailPanel event={event} navigationPresentation={navigationPresentation} onCompleteManual={operationsOwnsEvent(event) ? undefined : completeManual} onViewArchive={(eventId) => navigate("events", eventId)} /></div></div></main>}
      {view === "events" && <EventArchiveView onAgentContextChange={setArchiveAgentContext} />}{view === "analytics" && <AnalyticsView />}{view === "advanced" && <AdvancedView event={event} runtimeMode={runtimeMode} onRuntimeModeChange={setRuntimeMode} />}
    </div>
    {(view === "workbench" || view === "events") && <FloatingRobotOperationsAgent pageContext={agentPageContext} />}
  </div></RobotOperationsProvider>;
}

function readUiStorage(key: string): string | null { try { return localStorage.getItem(key); } catch { return null; } }
function writeUiStorage(key: string, value: string) { try { localStorage.setItem(key, value); } catch { /* Private mode may disallow UI persistence. */ } }
function removeUiStorage(key: string) { try { localStorage.removeItem(key); sessionStorage.removeItem(key); } catch { /* Private mode may disallow UI persistence. */ } }

function stateIndex(state: string): number {
  return { DETECTED: 0, EDGE_DETECTED: 1, MULTI_VIEW: 2, CLOUD_REVIEW: 3, LOCATED: 4, ASSIGNED: 5, NAVIGATING: 6, ARRIVED: 7, CLEANING_COMPLETED: 8, VERIFYING: 9, CLOSED: 10, HUMAN_FALLBACK: 11, HUMAN_REVIEW: 12 }[state] ?? 0;
}

function stageIndexFor(steps: ActiveEvent["scenario"]["steps"], state: string): number {
  const presentation: Record<string, ActiveEvent["scenario"]["steps"][number]> = { DETECTED: "DISCOVERED", EDGE_DETECTED: "EDGE_DETECTED", MULTI_VIEW: "MULTI_VIEW", CLOUD_REVIEW: "CLOUD_REVIEW", LOCATED: "LOCATING", ASSIGNED: "ROBOT_ASSIGNED", NAVIGATING: "NAVIGATING", ARRIVED: "CLEANING", CLEANING_COMPLETED: "CLEANING", VERIFYING: "VERIFYING", CLOSED: "CLOSED", HUMAN_FALLBACK: "HUMAN_FALLBACK", HUMAN_REVIEW: "HUMAN_REVIEW" };
  const target = presentation[state] ?? "DISCOVERED";
  const index = steps.indexOf(target);
  return index >= 0 ? index : Math.min(stateIndex(state), steps.length - 1);
}

function NavItem({ icon: Icon, label, active = false, onClick }: { icon: typeof LayoutDashboard; label: string; active?: boolean; onClick: () => void }) {
  return <button type="button" onClick={onClick} className={`flex w-full items-center gap-2.5 px-3 py-2.5 text-left text-sm transition-colors ${active ? "bg-slate-900 font-medium text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"}`}><Icon size={16} strokeWidth={1.7} />{label}</button>;
}
