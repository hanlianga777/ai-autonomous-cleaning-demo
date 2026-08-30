import { BarChart3, Bot, CircleDot, ClipboardList, LayoutDashboard, Search, Settings2, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { CameraMonitorGrid } from "./CameraMonitorGrid";
import { EventDetailPanel } from "./EventDetailPanel";
import { scenarios, stageCopy } from "./data";
import { SpatialDispatchView } from "./SpatialDispatchView";
import { PanelBoundary } from "./PanelBoundary";
import { customerTerm, displayStates, fromStoredEvent, stateLabels } from "./eventViewModel";
import { canApplySnapshot, claimStage, loadEventSnapshot, readRequestKeys } from "./runtimeSession";
import type { ActiveEvent } from "./types";

export function PrototypeWorkbench() {
  const [event, setEvent] = useState<ActiveEvent | null>(null);
  const [view, setView] = useState<"workbench" | "events" | "analytics" | "advanced">("workbench");
  const [runtimeMode, setRuntimeMode] = useState<"live" | "replay">("live");
  const [restoring, setRestoring] = useState(true);
  const [syncNotice, setSyncNotice] = useState("");
  const submittedStages = useRef(new Set<string>(readStageRequests()));

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
    if (!eventId || !event || event.processing) return;
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
    if (!event || event.processing) return;
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
  }, [event?.backendState, event?.processing, event?.scenario.id]);

  // A reload during a cloud call observes SQLite instead of sending it again.
  useEffect(() => {
    const eventId = String(event?.liveResult?.event_id ?? "");
    if (!eventId || ["CLOSED", "HUMAN_REVIEW", "HUMAN_FALLBACK"].includes(event?.backendState ?? "")) return;
    const controller = new AbortController();
    const timer = window.setInterval(() => {
      fetch(`/api/events/${encodeURIComponent(eventId)}`, { signal: controller.signal })
        .then((r) => r.ok ? r.json() : null)
        .then((stored) => { if (stored) applyStageResponse(fromStoredEvent(stored).liveResult ?? {}); })
        .catch(() => { /* The stage request owns the visible transport error. */ });
    }, 1200);
    return () => { window.clearInterval(timer); controller.abort(); };
  }, [event?.liveResult?.event_id, event?.backendState]);

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
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-[200px] border-r border-slate-200 bg-white lg:flex lg:flex-col"><div className="flex h-[54px] items-center gap-2.5 border-b border-slate-200 px-4"><div className="flex h-7 w-7 items-center justify-center bg-slate-900 text-[9px] font-bold text-white">CO</div><div><p className="text-sm font-semibold">CleanOps</p><p className="text-[9px] tracking-[0.12em] text-slate-400">自主清洁</p></div></div><nav className="space-y-1 px-2.5 py-4"><NavItem icon={LayoutDashboard} label="自主清洁工作台" active={view === "workbench"} onClick={() => setView("workbench")} /><NavItem icon={ClipboardList} label="事件中心" active={view === "events"} onClick={() => setView("events")} /><NavItem icon={BarChart3} label="运营分析" active={view === "analytics"} onClick={() => setView("analytics")} /><NavItem icon={Settings2} label="高级模式" active={view === "advanced"} onClick={() => setView("advanced")} /></nav></aside>
<div className="lg:ml-[200px]"><header className="flex h-[54px] items-center justify-between border-b border-slate-200 bg-white px-4 lg:px-5"><div className="flex items-center gap-2"><p className="text-sm font-semibold">{view === "workbench" ? "自主清洁工作台" : view === "events" ? "事件中心" : view === "analytics" ? "运营分析" : "高级模式"}</p>{view === "workbench" && <span className={`hidden items-center gap-1.5 text-[11px] md:flex ${event ? "text-slate-700" : "text-slate-500"}`}><CircleDot size={12} className={event?.processing ? "animate-pulse text-rose-500" : "text-emerald-500"} />{stageCopy[state].title}</span>}</div><span className="border border-slate-200 px-2 py-1 text-[10px] font-medium tracking-wide text-slate-600">{event?.liveResult?.mode === "STABLE_REPLAY" ? "STABLE REPLAY" : event?.liveResult?.mode === "LIVE" ? "LIVE" : runtimeMode === "live" ? "LIVE · 下次运行" : "STABLE REPLAY · 下次运行"}</span></header>
      {view === "workbench" && <main className="h-[calc(100vh-54px)] min-h-[626px] p-2.5 lg:p-3"><div className="grid h-full grid-cols-1 gap-3 lg:grid-cols-[minmax(0,72fr)_minmax(320px,28fr)]"><div className="grid min-h-0 grid-rows-[minmax(180px,31fr)_minmax(360px,69fr)] gap-3"><CameraMonitorGrid event={event} onTrigger={trigger} /><PanelBoundary name="空间调度视图"><SpatialDispatchView event={event} onNavigationComplete={() => void callStage("complete-navigation")} /></PanelBoundary></div><div className="flex min-h-0 flex-col">{(restoring || syncNotice) && <div role="status" className="shrink-0 border border-amber-200 bg-amber-50 p-2 text-[11px] leading-5 text-amber-900">{restoring ? "正在恢复事件记录…" : syncNotice}{!restoring && <button onClick={() => void syncSavedState()} className="ml-2 border border-amber-300 bg-white px-2">同步已保存状态</button>}</div>}<EventDetailPanel event={event} onCompleteManual={completeManual} /></div></div></main>}
      {view === "events" && <EventCenter />}{view === "analytics" && <AnalyticsView />}{view === "advanced" && <AdvancedView event={event} runtimeMode={runtimeMode} onRuntimeModeChange={setRuntimeMode} />}
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

type EventRow = { event_id: string; state: string; created_at?: string; updated_at?: string; location?: { building?: string; floor?: string; zone?: string }; task_profile?: { object_type?: string; severity?: string }; assignment_decision?: { selected_robot_name?: string }; demo_v1?: { reason?: string; verification?: { confidence?: number } } };

function EventCenter() {
  const [rows, setRows] = useState<EventRow[]>([]);
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [history, setHistory] = useState<ActiveEvent | null>(null);
  const [error, setError] = useState("");
  const [historyError, setHistoryError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/events?limit=100", { signal: controller.signal })
      .then((r) => { if (!r.ok) throw new Error("事件列表暂不可用"); return r.json(); })
      .then(setRows).catch((e) => { if (e.name !== "AbortError") setError(e.message); });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    setHistory(null); setHistoryError("");
    if (!selectedId) return;
    const controller = new AbortController();
    fetch(`/api/events/${encodeURIComponent(selectedId)}`, { signal: controller.signal })
      .then((r) => { if (!r.ok) throw new Error("无法读取事件快照"); return r.json(); })
      .then((record) => setHistory(fromStoredEvent(record)))
      .catch((e) => { if (e.name !== "AbortError") setHistoryError(e.message); });
    return () => controller.abort();
  }, [selectedId]);
  const filtered = rows.filter((row) =>
    (filter === "all" || filter === "closed" && row.state === "CLOSED" ||
      filter === "human" && ["HUMAN_REVIEW", "HUMAN_FALLBACK"].includes(row.state) ||
      filter === "in_progress" && !["CLOSED", "HUMAN_REVIEW", "HUMAN_FALLBACK"].includes(row.state)) &&
    JSON.stringify(row).toLowerCase().includes(query.toLowerCase()));
  return <main className="mx-auto max-w-[1500px] p-5 lg:p-7">
    <div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-200 pb-4">
      <div><p className="text-xl font-semibold">事件中心</p><p className="mt-1 text-xs text-slate-500">持久化事件档案 · 点击查看完整只读过程</p></div>
      <label className="flex h-9 items-center gap-2 border border-slate-300 bg-white px-3 text-xs text-slate-500"><Search size={14} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="搜索事件、地点或机器人" className="w-48 outline-none" /></label>
    </div>
    <div className="mt-4 flex flex-wrap gap-2">{[["all", "全部"], ["in_progress", "处理中"], ["closed", "已闭环"], ["human", "人工处置"]].map(([key, label]) => <button key={key} onClick={() => setFilter(key)} className={`border px-3 py-1.5 text-xs ${filter === key ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-600"}`}>{label}</button>)}</div>
    {error && <p role="alert" className="mt-3 text-xs text-rose-700">{error}</p>}
    <div className="mt-4 overflow-hidden border border-slate-200 bg-white">
      <div className="grid grid-cols-[1.2fr_1fr_.7fr_.8fr_.8fr] border-b border-slate-200 bg-slate-50 px-4 py-2 text-[10px] font-semibold text-slate-500"><span>事件 / 位置</span><span>事件 ID / 时间</span><span>状态</span><span>执行对象</span><span>闭环</span></div>
      {filtered.map((row) => <button key={row.event_id} data-event-id={row.event_id} onClick={() => setSelectedId(row.event_id)} className="grid w-full grid-cols-[1.2fr_1fr_.7fr_.8fr_.8fr] border-b border-slate-100 px-4 py-3 text-left text-xs hover:bg-slate-50">
        <span><b className="text-slate-800">{customerTerm(row.task_profile?.object_type)}</b><i className="mt-1 block not-italic text-slate-500">{row.location?.building} · {row.location?.floor} · {customerTerm(row.location?.zone)}</i></span>
        <span className="text-slate-500">{row.event_id.slice(-10)}<i className="mt-1 block not-italic">{row.updated_at ?? "—"}</i></span>
        <span className={row.state === "CLOSED" ? "text-emerald-700" : "text-slate-600"}>{stateLabels[row.state] ?? "已记录"}</span>
        <span className="text-slate-600">{row.assignment_decision?.selected_robot_name ?? (row.state === "HUMAN_FALLBACK" ? "人工工单" : "未派发机器人")}</span>
        <span className="text-slate-500">{row.state === "CLOSED" ? "已验收" : "待处理"}</span>
      </button>)}
      {!error && !filtered.length && <p className="p-10 text-center text-sm text-slate-500">尚无匹配事件。请先在工作台运行一个演示。</p>}
    </div>
    {selectedId && <div role="dialog" aria-modal="true" aria-label="历史事件详情" className="fixed inset-0 z-[90] flex justify-end bg-slate-950/30" onClick={() => setSelectedId(null)}>
      <article onClick={(e) => e.stopPropagation()} className="flex h-full w-full max-w-[560px] flex-col bg-white shadow-xl">
        <div className="flex shrink-0 items-center justify-between border-b border-slate-200 px-4 py-2"><p className="truncate text-[10px] text-slate-400">{selectedId}</p><button aria-label="关闭历史详情" onClick={() => setSelectedId(null)} className="p-2 text-slate-500"><X size={18} /></button></div>
        {history ? <EventDetailPanel event={history} mode="history" /> : <p className="p-6 text-xs text-slate-500">{historyError || "正在读取事件快照…"}</p>}
      </article>
    </div>}
  </main>;
}
function AnalyticsView() {
  const [data, setData] = useState<Record<string, any> | null>(null); const [advice, setAdvice] = useState(""); const [question, setQuestion] = useState(""); const [answer, setAnswer] = useState("");
  useEffect(() => { fetch("/api/analytics/overview").then((r) => r.json()).then(setData).catch(() => setData(null)); }, []);
  const kpis = data?.kpis;
  return <main className="mx-auto max-w-[1500px] p-5 lg:p-7"><div className="flex items-end justify-between border-b border-slate-200 pb-4"><div><p className="text-xl font-semibold">30 天运营分析</p><p className="mt-1 text-xs text-slate-500">30 天演示基线 + 本次运行的持久化事件。</p></div><button onClick={() => setAdvice("建议优先复核高频区域的摄像头覆盖与 Robot C 的跨楼通行等待；该建议仅基于当前统计，不会自动修改调度规则。")} className="border border-slate-300 bg-white px-3 py-2 text-xs text-slate-700">重新分析</button></div><div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{[["自主闭环率", `${kpis?.autonomous_closure_rate ?? "—"}%`], ["人工介入率", `${kpis?.human_intervention_rate ?? "—"}%`], ["一次通过率", `${kpis?.first_pass_success_rate ?? "—"}%`], ["平均闭环", `${kpis?.average_closure_time_minutes ?? "—"} min`]].map(([label, value]) => <div key={label} className="border border-slate-200 bg-white p-4"><p className="text-[11px] text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold">{value}</p></div>)}</div><div className="mt-5 grid gap-4 lg:grid-cols-[1.4fr_.6fr]"><section className="border border-slate-200 bg-white p-5"><p className="text-sm font-semibold">园区高发区域</p><div className="relative mt-4 aspect-[2/1] overflow-hidden border border-slate-100 bg-slate-50"><img src="/visual-assets/campus/campus-white-model.png" className="h-full w-full object-contain opacity-70" />{(data?.heatmap ?? []).slice(0, 6).map((point: any, index: number) => <span key={point.zone_id} style={{ left: `${Math.min(88, (point.x ?? 10) + index * 6)}%`, top: `${Math.min(78, (point.y ?? 15) + index * 4)}%` }} className="absolute h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full bg-rose-500/70" title={`${point.label}: ${point.count}`} />)}</div></section><section className="border border-slate-200 bg-white p-5"><p className="text-sm font-semibold">AI 运营建议</p><p className="mt-3 text-xs leading-5 text-slate-600">{advice || "基于已加载的 KPI、热点和机器人利用率生成只读建议。"}</p><div className="mt-8 border-t border-slate-100 pt-4"><p className="flex items-center gap-1 text-xs font-semibold"><Bot size={14} />园区 AI 助手</p><div className="mt-2 flex gap-2"><input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="例如：闭环率是多少？" className="min-w-0 flex-1 border border-slate-300 px-2 py-2 text-xs outline-none" /><button onClick={() => setAnswer(question.includes("闭环") ? `当前自主闭环率为 ${kpis?.autonomous_closure_rate ?? "—"}%。` : "我只能基于当前运营统计回答，不能执行机器人、工单或阈值配置操作。")} className="bg-slate-900 px-3 text-xs text-white">问</button></div>{answer && <p className="mt-2 text-xs leading-5 text-slate-600">{answer}</p>}</div></section></div></main>;
}

function AdvancedView({ event, runtimeMode, onRuntimeModeChange }: { event: ActiveEvent | null; runtimeMode: "live" | "replay"; onRuntimeModeChange: (mode: "live" | "replay") => void }) {
  const [status, setStatus] = useState<Record<string, any> | null>(null);
  useEffect(() => { fetch("/api/system/ai-status").then((r) => r.json()).then(setStatus).catch(() => setStatus(null)); }, []);
  const review = event?.liveResult?.qwen_review as Record<string, unknown> | undefined;
  const ready = Boolean(status?.qwen_vl?.api_key_configured);
  return <main className="mx-auto max-w-[1200px] p-5 lg:p-7"><p className="text-xl font-semibold">高级模式</p><p className="mt-1 text-xs text-slate-500">技术审计、接口运行状态与演示回放边界。不会展示或保存任何 API Key。</p><section className="mt-4 flex flex-wrap items-center justify-between gap-3 border border-slate-200 bg-white px-4 py-3"><div><p className="text-xs font-semibold text-slate-700">AI Runtime</p><p className="mt-1 text-[11px] text-slate-500">云端模型：{ready ? "已配置" : "未配置"} · 最近请求：{String(review?.provider ?? "Idle")} · 最近延迟：{review?.elapsed_ms ? `${review.elapsed_ms} ms` : "—"}</p></div><div className="flex border border-slate-200 p-0.5"><button type="button" onClick={() => onRuntimeModeChange("live")} className={`px-3 py-1.5 text-xs ${runtimeMode === "live" ? "bg-slate-900 text-white" : "text-slate-600"}`}>LIVE</button><button type="button" onClick={() => onRuntimeModeChange("replay")} className={`px-3 py-1.5 text-xs ${runtimeMode === "replay" ? "bg-slate-900 text-white" : "text-slate-600"}`}>Stable Replay</button></div></section><p className="mt-2 text-[11px] text-slate-500">Stable Replay 仅复用已保存的真实云端结构化响应；空间定位、调度、路线、Fleet、SQLite 阶段和验收仍会重新运行。LIVE 失败不会自动切换回放。</p><div className="mt-5 grid gap-4 md:grid-cols-2"><Tech title="AI 感知链路" lines={["受控边缘检测 → 单视角云端 → 证据不足时自主补证 → 最终语义判断", "输出统一 TaskProfile / CleaningEvent schema", `当前事件：${event?.scenario.id ?? "无"}`]} /><Tech title="空间与调度" lines={["Camera → SLAM 复用 Phase 2 坐标映射", "Capability Engine 与 Scheduler 为唯一机器人选择器", "Robot-first + Human Fallback 规则保持不变"]} /><Tech title="模型与接口状态" lines={[`服务状态：${status ? "可访问" : "暂不可用"}`, `本次模型：${String(review?.model ?? "尚无调用")}`, `最近耗时：${review?.elapsed_ms ? `${review.elapsed_ms} ms` : "—"}`, "Trace ID：独立 Trace Inspector 待 P1-H；当前以 Event ID 关联"]} /><Tech title="演示与回放" lines={["LIVE：实际调用已配置的云端模型", "稳定回放：明确受控回放，不伪装为实时推理", "异常时停止自动派单并转人工复核"]} /></div>{event?.liveResult && <pre className="mt-5 max-h-[360px] overflow-auto border border-slate-200 bg-white p-4 text-[10px] leading-5 text-slate-600">{JSON.stringify({ event_id: event.liveResult.event_id, edge: event.liveResult.controlled_yolo, cloud: review, first_review: event.liveResult.first_qwen_review, second_review: event.liveResult.second_qwen_review, evidence_fusion: event.liveResult.evidence_fusion, spatial: event.liveResult.spatial_location }, null, 2)}</pre>}</main>;
}
function Tech({ title, lines }: { title: string; lines: string[] }) { return <section className="border border-slate-200 bg-white p-5"><p className="text-sm font-semibold">{title}</p>{lines.map((line) => <p key={line} className="mt-2 text-xs leading-5 text-slate-600">{line}</p>)}</section>; }
