import { useEffect, useRef, useState } from "react";
import { CircleAlert, RefreshCw, ScanLine } from "lucide-react";

import { fetchOperationsSnapshot, startOperationsRun, startOperationsUpload } from "@/api/operations";
import { fetchSpatialOverview } from "@/api/spatial";
import { FleetCommandBar } from "@/components/operations/FleetCommandBar";
import { SpatialMissionMap } from "@/components/operations/SpatialMissionMap";
import { AuditTimeline, WorkOrderDetail } from "@/components/operations/WorkOrderDetail";
import { WorkOrderQueue } from "@/components/operations/WorkOrderQueue";
import { Badge } from "@/components/ui/badge";
import type { OperationsSnapshot } from "@/types/operations";
import type { SpatialOverview } from "@/types/spatial";

const offlineSnapshot: OperationsSnapshot = {
  schema_version: "operations.v1",
  telemetry_mode: "DEMO_PLAYBACK",
  message: "运营指挥服务尚未连接。下面是离线演示框架；启动服务后可运行完整、可审计的业务回放。",
  fleet: [
    { id: "robot-a", name: "Robot A", short_name: "A", status: "idle", battery: 86, location: "A 栋 1F", role: "室外干垃圾", activity: "待命", telemetry_mode: "DEMO_PLAYBACK", position: { map_id: "A_1F", x: 18, y: 22 } },
    { id: "robot-b", name: "Robot B", short_name: "B", status: "idle", battery: 73, location: "A 栋 1F", role: "液体重污", activity: "待命", telemetry_mode: "DEMO_PLAYBACK", position: { map_id: "A_1F", x: 44, y: 18 } },
    { id: "robot-c", name: "Robot C", short_name: "C", status: "idle", battery: 91, location: "B 栋 1F", role: "室内轻度清洁", activity: "待命", telemetry_mode: "DEMO_PLAYBACK", position: { map_id: "B_1F", x: 16, y: 26 } },
  ],
  active_work_order: null,
  catalog: [],
};

function connectionMessage(reason: unknown) {
  const detail = reason instanceof Error ? reason.message : "运营指挥服务不可用";
  return `无法连接 operations.v1（${detail}）。页面仍保留离线框架；请在项目根目录运行 start_demo.command 后刷新。无需配置 YOLO 或 Qwen-VL API Key 即可运行受控 Mock 演示。`;
}

export function CustomerWorkbench() {
  const [snapshot, setSnapshot] = useState<OperationsSnapshot>(offlineSnapshot);
  const [spatial, setSpatial] = useState<SpatialOverview>();
  const [mapId, setMapId] = useState("A_1F");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function refresh(runId?: string) {
    try {
      const next = await fetchOperationsSnapshot(runId);
      setSnapshot(next);
      setError("");
    } catch (reason) {
      setError(connectionMessage(reason));
    }
  }

  useEffect(() => {
    void refresh();
    void fetchSpatialOverview().then(setSpatial).catch((reason: unknown) => {
      setError((current) => current || connectionMessage(reason));
    });
  }, []);

  const activeRun = snapshot.run_id;
  const activeState = snapshot.active_work_order?.display_state;
  useEffect(() => {
    if (!activeRun || ["CLOSED", "HUMAN_ACTION_REQUIRED"].includes(activeState ?? "")) return;
    const timer = window.setInterval(() => void refresh(activeRun), 400);
    return () => window.clearInterval(timer);
  }, [activeRun, activeState]);

  async function runScenario(eventId: string) {
    setBusy(true);
    try {
      const next = await startOperationsRun(eventId);
      setSnapshot(next);
      setMapId(next.active_work_order?.event.location.map_id ?? "A_1F");
      setError("");
    } catch (reason) {
      setError(connectionMessage(reason));
    } finally {
      setBusy(false);
    }
  }

  async function uploadScenario(file?: File) {
    if (!file) return;
    setBusy(true);
    try {
      const next = await startOperationsUpload(file);
      setSnapshot(next);
      setMapId(next.active_work_order?.event.location.map_id ?? "A_1F");
      setError("");
    } catch (reason) {
      setError(connectionMessage(reason));
    } finally {
      setBusy(false);
    }
  }

  return <section className="mx-auto max-w-[1840px] space-y-4">
    <header className="flex flex-col gap-3 border-b border-slate-200 pb-4 lg:flex-row lg:items-end lg:justify-between">
      <div><p className="section-kicker">Autonomous cleaning · operations command center</p><h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">自主清洁任务指挥台</h2><p className="mt-1 text-xs text-slate-500">以机器人、工单与空间执行为主视图；场景选择和上传图片只用于创建一张新的演示工单。</p></div>
      <div className="flex items-center gap-2"><Badge variant="outline"><span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-amber-500" />DEMO PLAYBACK</Badge><button onClick={() => void refresh(snapshot.run_id)} disabled={busy} className="flex h-9 items-center gap-1.5 border border-slate-300 bg-white px-3 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:text-slate-400"><RefreshCw size={13} className={busy ? "animate-spin" : ""} />刷新状态</button></div>
    </header>

    <p className="border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] leading-5 text-slate-600"><ScanLine size={13} className="mr-1.5 inline text-slate-500" />当前展示的是服务端产生的受控 <strong>DEMO PLAYBACK</strong>，用于透明地演示既有 AI Lab、Phase 2 空间映射、Phase 3 Scheduler、Phase 5 Multi-view 与验收闭环；不是实时设备遥测，也不会把未配置的模型 Key 伪装为真实调用。</p>
    {error && <div role="alert" className="flex items-start justify-between gap-3 border border-rose-200 bg-rose-50 px-3 py-2 text-xs leading-5 text-rose-700"><span><CircleAlert size={14} className="mr-1.5 inline align-[-2px]" />{error}</span><button onClick={() => void refresh()} className="shrink-0 font-semibold underline">重试</button></div>}

    <FleetCommandBar fleet={snapshot.fleet} />
    <div className="grid gap-4 2xl:grid-cols-[minmax(270px,0.25fr)_minmax(560px,0.5fr)_minmax(330px,0.3fr)]">
      <WorkOrderQueue snapshot={snapshot} onRun={(eventId) => void runScenario(eventId)} onUpload={() => inputRef.current?.click()} />
      <SpatialMissionMap spatial={spatial} mapId={mapId} onMapChange={setMapId} fleet={snapshot.fleet} activeWorkOrder={snapshot.active_work_order} />
      <WorkOrderDetail workOrder={snapshot.active_work_order} />
    </div>
    <AuditTimeline workOrder={snapshot.active_work_order} />
    <input ref={inputRef} className="hidden" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => { void uploadScenario(event.target.files?.[0]); event.currentTarget.value = ""; }} />
  </section>;
}
