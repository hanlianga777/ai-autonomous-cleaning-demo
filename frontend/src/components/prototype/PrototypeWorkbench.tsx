import { BarChart3, CircleDot, ClipboardList, LayoutDashboard, Settings2 } from "lucide-react";
import { useEffect, useState } from "react";
import { CameraMonitorGrid } from "./CameraMonitorGrid";
import { EventDetailPanel } from "./EventDetailPanel";
import { scenarios, stageCopy } from "./data";
import { SpatialDispatchView } from "./SpatialDispatchView";
import type { ActiveEvent } from "./types";

export function PrototypeWorkbench() {
  const [event, setEvent] = useState<ActiveEvent | null>(null);
  const [running, setRunning] = useState(false);
  useEffect(() => {
    if (!event || !running) return;
    const state = event.scenario.steps[event.stageIndex];
    if (["CLOSED", "HUMAN_FALLBACK"].includes(state) || event.cloudLoading) { setRunning(false); return; }
    const delay = stageDelay(event);
    const timer = window.setTimeout(() => setEvent((current) => current && ({ ...current, stageIndex: Math.min(current.stageIndex + 1, current.scenario.steps.length - 1) })), delay);
    return () => window.clearTimeout(timer);
  }, [event, running]);
  const trigger = async (id: typeof scenarios[number]["id"], mode: "live" | "replay" = "live") => {
    const scenario = scenarios.find((item) => item.id === id);
    if (!scenario) return;
    const demoId = { outdoor: "demo01", liquid: "demo02", can: "demo03", oversized: "demo04" }[id];
    setEvent({ scenario, stageIndex: scenario.steps.indexOf("CLOUD_REVIEW"), startedAt: new Date().toISOString(), cloudLoading: true });
    setRunning(false);
    try {
      const response = await fetch(`/api/demo-v1/runs/${demoId}?mode=${mode}`, { method: "POST" });
      const liveResult = await response.json() as Record<string, unknown>;
      if (!response.ok || liveResult.status === "HUMAN_REVIEW" || liveResult.status === "HUMAN_FALLBACK") { setEvent((current) => current && ({ ...current, liveResult, cloudLoading: false })); return; }
      // LIVE cloud time has already elapsed while the Qwen call was visible.
      // Replay intentionally plays the complete controlled sequence from discovery.
      const stageIndex = mode === "live" ? scenario.steps.indexOf("CLOUD_REVIEW") : 0;
      setEvent({ scenario, stageIndex, startedAt: new Date().toISOString(), liveResult, cloudLoading: false });
      setRunning(true);
    } catch (error) { setEvent((current) => current && ({ ...current, liveResult: { status: "HUMAN_REVIEW", reason: "无法连接云端综合研判；未创建机器人任务。" }, cloudLoading: false })); }
  };
  const state = event ? event.scenario.steps[event.stageIndex] : "IDLE";
  return <div className="min-h-screen bg-[#f6f7f8] text-slate-900">
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-[200px] border-r border-slate-200 bg-white lg:flex lg:flex-col"><div className="flex h-[54px] items-center gap-2.5 border-b border-slate-200 px-4"><div className="flex h-7 w-7 items-center justify-center bg-slate-900 text-[9px] font-bold text-white">CO</div><div><p className="text-sm font-semibold">CleanOps</p><p className="text-[9px] tracking-[0.12em] text-slate-400">自主清洁</p></div></div><nav className="space-y-1 px-2.5 py-4"><NavItem icon={LayoutDashboard} label="自主清洁工作台" active /><NavItem icon={ClipboardList} label="事件中心" /><NavItem icon={BarChart3} label="运营分析" /><NavItem icon={Settings2} label="高级模式" /></nav><div className="mt-auto border-t border-slate-100 px-4 py-3 text-[10px] text-slate-400">受控集成演示</div></aside>
    <div className="lg:ml-[200px]"><header className="flex h-[54px] items-center justify-between border-b border-slate-200 bg-white px-4 lg:px-5"><div className="flex items-center gap-2"><p className="text-sm font-semibold">自主清洁工作台</p><span className={`hidden items-center gap-1.5 text-[11px] md:flex ${event ? "text-slate-700" : "text-slate-500"}`}><CircleDot size={12} className={event && running ? "animate-pulse text-rose-500" : "text-emerald-500"} />{stageCopy[state].title}</span></div><div className="flex items-center gap-2 text-[11px] text-slate-600"><span className="hidden border border-slate-200 px-2 py-1 sm:inline">受控集成演示</span><span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-500" />园区监测正常</span></div></header>
      <main className="h-[calc(100vh-54px)] min-h-[626px] p-2.5 lg:p-3"><div className="grid h-full grid-cols-1 gap-3 lg:grid-cols-[minmax(0,72fr)_minmax(320px,28fr)]"><div className="grid min-h-0 grid-rows-[auto_minmax(180px,1fr)] gap-3"><CameraMonitorGrid event={event} onTrigger={trigger} /><SpatialDispatchView event={event} /></div><EventDetailPanel event={event} /></div></main>
    </div>
  </div>;
}

function stageDelay(event: ActiveEvent) {
  const state = event.scenario.steps[event.stageIndex];
  if (state === "NAVIGATING") return event.scenario.id === "can" ? 3200 : 8500;
  if (state === "ELEVATOR_TRANSFER") return 1600;
  if (state === "SKYBRIDGE_TRANSFER") return 4300;
  if (state === "ROBOT_ASSIGNED") return 1800;
  if (state === "CLEANING") return 2000;
  if (state === "VERIFYING") return 1600;
  return 1150;
}

function NavItem({ icon: Icon, label, active = false }: { icon: typeof LayoutDashboard; label: string; active?: boolean }) {
  return <button type="button" className={`flex w-full items-center gap-2.5 px-3 py-2.5 text-left text-sm transition-colors ${active ? "bg-slate-900 font-medium text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"}`}><Icon size={16} strokeWidth={1.7} />{label}</button>;
}
