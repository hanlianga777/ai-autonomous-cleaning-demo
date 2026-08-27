import { useEffect, useMemo, useRef, useState } from "react";
import { Bot, CheckCircle2, CircleAlert, ClipboardCheck, Eye, FileUp, LoaderCircle, MapPin, Play, Route, ScanLine, ShieldCheck, Upload, UsersRound } from "lucide-react";

import { fetchWorkbenchScenarios, runWorkbenchEvent, runWorkbenchUpload } from "@/api/workbench";
import { fetchSpatialOverview } from "@/api/spatial";
import { Badge } from "@/components/ui/badge";
import type { AiLabResult } from "@/types/aiLab";
import type { SpatialMap, SpatialOverview } from "@/types/spatial";
import type { DemoAsset, DemoAssetManifest, WorkbenchScenarioResult } from "@/types/workbench";

const stageLabels = ["发现现场问题", "AI 研判", "空间定位", "能力校验", "调度与路由", "执行清洁", "验收与闭环"];

export function CustomerWorkbench() {
  const [scenarios, setScenarios] = useState<DemoAssetManifest[]>([]);
  const [spatial, setSpatial] = useState<SpatialOverview>();
  const [selectedId, setSelectedId] = useState("event-beverage-spill-002");
  const [result, setResult] = useState<WorkbenchScenarioResult>();
  const [stage, setStage] = useState(0);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [uploadPreview, setUploadPreview] = useState<string>();
  const [uploadName, setUploadName] = useState<string>();
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    void Promise.all([fetchWorkbenchScenarios(), fetchSpatialOverview()])
      .then(([loadedScenarios, loadedSpatial]) => { setScenarios(loadedScenarios); setSpatial(loadedSpatial); })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "无法加载客户演示工作台"));
  }, []);
  useEffect(() => () => { if (uploadPreview) URL.revokeObjectURL(uploadPreview); }, [uploadPreview]);

  const selected = useMemo(() => scenarios.find((scenario) => scenario.event_id === selectedId) ?? scenarios[0], [scenarios, selectedId]);
  const manifest = result?.asset_manifest ?? selected;
  const isHumanFallback = manifest?.verification_mode === "HUMAN_REQUIRED";

  function scheduleStages(humanFallback: boolean) {
    const endStage = humanFallback ? 6 : 7;
    Array.from({ length: endStage - 1 }, (_, index) => index + 2).forEach((next, index) => window.setTimeout(() => setStage(next), 520 * (index + 1)));
    window.setTimeout(() => setRunning(false), 520 * (endStage - 1));
  }

  async function startDemo(file?: File) {
    setRunning(true); setError(""); setResult(undefined); setStage(1);
    try {
      const next = file ? await runWorkbenchUpload(file) : await runWorkbenchEvent(selectedId);
      setResult(next); setSelectedId(next.asset_manifest.event_id); scheduleStages(next.asset_manifest.verification_mode === "HUMAN_REQUIRED");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "演示流程暂不可用"); setStage(0); setRunning(false);
    }
  }

  function selectScenario(eventId: string) {
    setSelectedId(eventId); setResult(undefined); setStage(0); setError("");
  }

  function selectUpload(file?: File) {
    if (!file) return;
    if (uploadPreview) URL.revokeObjectURL(uploadPreview);
    setUploadPreview(URL.createObjectURL(file)); setUploadName(file.name);
    void startDemo(file);
  }

  return <section className="mx-auto max-w-[1780px] space-y-4">
    <header className="flex flex-col gap-3 border-b border-slate-200 pb-4 lg:flex-row lg:items-end lg:justify-between">
      <div><p className="section-kicker">AI autonomous cleaning · controlled customer demo</p><h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">自主清洁任务工作台</h2><p className="mt-1 text-xs text-slate-500">上传四组受控清洁前原图后自动匹配场景，展示既有 AI、空间、调度、执行和验收链路。</p></div>
      <div className="flex gap-2"><button onClick={() => inputRef.current?.click()} disabled={running} className="flex h-10 items-center justify-center gap-2 border border-slate-300 bg-white px-4 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:text-slate-400"><Upload size={16} />上传清洁前图</button><button onClick={() => void startDemo()} disabled={running || !selected} className="flex h-10 items-center justify-center gap-2 rounded-sm bg-slate-900 px-4 text-sm font-medium text-white hover:bg-slate-700 disabled:bg-slate-300">{running ? <LoaderCircle size={16} className="animate-spin" /> : <Play size={16} />}{running ? "正在运行闭环" : "运行所选场景"}</button></div>
    </header>

    <p className="border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] leading-5 text-slate-600"><ScanLine size={13} className="mr-1.5 inline text-slate-500" />当前是 <strong>DEMO MOCK MODE</strong>：上传以 SHA-256 匹配四张受控清洁前原图，复用 `ai-lab.v1`、Phase 2 四点映射、Phase 3 Scheduler、Phase 5 Multi-view Agent；不把未配置的真实模型伪装为实跑。</p>
    {error && <p role="alert" className="flex gap-2 border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700"><CircleAlert size={14} className="shrink-0" />{error}</p>}

    <ScenarioStrip scenarios={scenarios} selectedId={selectedId} onSelect={selectScenario} />
    <BusinessRail stage={stage} humanFallback={Boolean(isHumanFallback)} />
    {manifest && <>
      <div className="grid gap-4 xl:grid-cols-[minmax(260px,0.30fr)_minmax(440px,0.46fr)_minmax(280px,0.24fr)]">
        <CameraPanel manifest={manifest} preview={uploadPreview} uploadName={uploadName} ai={result?.initial_ai_result} onUpload={() => inputRef.current?.click()} />
        <ExecutionMap spatial={spatial} event={result?.workflow_event} stage={stage} />
        <TaskPanel manifest={manifest} result={result} stage={stage} />
      </div>
      {result?.multi_view?.triggered && <MultiViewPanel manifest={manifest} trace={result.multi_view} />}
      {result && <WorkflowTimeline result={result} humanFallback={Boolean(isHumanFallback)} />}
      {result && stage >= (isHumanFallback ? 6 : 7) && <VerificationPanel manifest={manifest} result={result} />}
    </>}
    <input ref={inputRef} className="hidden" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => selectUpload(event.target.files?.[0])} />
  </section>;
}

function ScenarioStrip({ scenarios, selectedId, onSelect }: { scenarios: DemoAssetManifest[]; selectedId: string; onSelect: (id: string) => void }) {
  return <section aria-label="演示场景" className="grid gap-2 md:grid-cols-2 xl:grid-cols-4">{scenarios.map((scenario) => <button key={scenario.event_id} onClick={() => onSelect(scenario.event_id)} className={`border p-3 text-left transition-colors ${scenario.event_id === selectedId ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-700 hover:border-slate-400"}`}><div className="flex items-center justify-between gap-2"><p className="text-xs font-semibold">{scenario.title}</p><Badge variant={scenario.expected_robot === "HUMAN_FALLBACK" ? "outline" : "success"}>{robotLabel(scenario.expected_robot)}</Badge></div><p className={`mt-1 text-[11px] leading-4 ${scenario.event_id === selectedId ? "text-slate-300" : "text-slate-500"}`}>{scenario.subtitle}</p></button>)}</section>;
}

function BusinessRail({ stage, humanFallback }: { stage: number; humanFallback: boolean }) {
  return <ol className="grid grid-cols-2 gap-x-2 gap-y-3 border-b border-slate-100 pb-4 sm:grid-cols-4 xl:grid-cols-7">{stageLabels.map((label, index) => {
    const text = humanFallback && index === 5 ? "创建人工工单" : humanFallback && index === 6 ? "等待人工验收" : label;
    const done = stage > index + 1 || (stage === 7 && index === 6);
    return <li key={label} className="flex min-w-0 items-center gap-2"><span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] font-semibold ${done ? "border-emerald-600 bg-emerald-600 text-white" : stage === index + 1 ? "border-slate-800 bg-slate-800 text-white" : "border-slate-200 text-slate-400"}`}>{done ? "✓" : index + 1}</span><span className={`truncate text-[11px] ${stage >= index + 1 ? "font-medium text-slate-700" : "text-slate-400"}`}>{text}</span></li>;
  })}</ol>;
}

function CameraPanel({ manifest, preview, uploadName, ai, onUpload }: { manifest: DemoAssetManifest; preview?: string; uploadName?: string; ai?: AiLabResult; onUpload: () => void }) {
  const before = byRole(manifest, "before"); const detection = ai?.detections[0];
  return <section className="overflow-hidden border border-slate-200 bg-white"><div className="flex items-start justify-between border-b border-slate-100 p-4"><div><p className="section-kicker">现场画面</p><h3 className="mt-1 text-sm font-semibold">{before?.camera_id ?? "固定摄像头"} · {manifest.location_label}</h3></div><Badge variant="outline">固定摄像头</Badge></div><div className="p-3"><CameraImage asset={before} preview={preview} label="清洁前主视角" detection={Boolean(ai)} /><div className="mt-3 flex items-center justify-between gap-2"><button onClick={onUpload} className="flex items-center gap-1.5 text-xs font-medium text-slate-700 hover:text-slate-950"><Upload size={14} />{uploadName ? "更换清洁前图片" : "上传清洁前图片"}</button><span className="text-[10px] text-slate-400">JPG / PNG / WEBP</span></div></div>{ai ? <div className="border-t border-slate-100 p-4"><p className="section-kicker">AI 研判</p><div className="mt-3 grid grid-cols-2 gap-y-3 text-xs"><Fact label="识别结果" value={translateObject(ai.task_profile.object_type)} /><Fact label="需要清洁" value={ai.perception.need_clean ? "是" : "否"} /><Fact label="污染形态" value={translateForm(ai.task_profile.pollution_form)} /><Fact label="综合置信度" value={`${Math.round(ai.perception.confidence * 100)}%`} /></div><details className="mt-4 border-t border-slate-100 pt-3"><summary className="cursor-pointer text-[11px] font-medium text-slate-600">查看结构化技术详情</summary><p className="mt-2 text-[10px] leading-5 text-slate-500">Schema: {ai.schema_version}<br />YOLO: {detection?.class_name ?? "—"} · {detection ? `${Math.round(detection.confidence * 100)}%` : "—"}<br />VLM: {ai.pipeline.vlm}</p></details></div> : <div className="border-t border-slate-100 p-4 text-xs leading-5 text-slate-500">选择场景运行，或直接上传受控演示素材中的清洁前原图。</div>}</section>;
}

function ExecutionMap({ spatial, event, stage }: { spatial?: SpatialOverview; event?: WorkbenchScenarioResult["workflow_event"]; stage: number }) {
  const map = spatial?.maps.find((item) => item.map_id === event?.location.map_id) ?? spatial?.maps.find((item) => item.map_id === "A_1F");
  if (!map) return <section className="flex min-h-[420px] items-center justify-center border border-slate-200 bg-white text-sm text-slate-500">正在加载 Phase 2 空间地图…</section>;
  const target = event?.location; const robotId = event?.assignment_decision?.selected_robot_id; const robot = robotId ? spatial?.robot_positions[robotId] : undefined;
  return <section className="overflow-hidden border border-slate-200 bg-white"><div className="flex items-start justify-between border-b border-slate-100 p-4"><div><p className="section-kicker">空间执行</p><h3 className="mt-1 text-sm font-semibold">{map.label} · Phase 2 SLAM 地图</h3></div><Badge variant="outline"><Eye size={12} className="mr-1" />Camera Coverage</Badge></div><div className="relative h-[430px] bg-[#f8fafb] p-4"><MapSvg map={map} spatial={spatial} target={target} robot={robot} stage={stage} /><div className="absolute bottom-5 left-5 border border-slate-200 bg-white px-3 py-2 text-[11px] text-slate-600 shadow-sm">{target && stage >= 3 ? <><MapPin size={13} className="mr-1 inline text-rose-600" />SLAM ({target.x.toFixed(1)}, {target.y.toFixed(1)}) · {target.zone}</> : <><ScanLine size={13} className="mr-1 inline text-blue-700" />等待 AI 结果写入 Camera → SLAM 坐标</>}</div></div></section>;
}

function MapSvg({ map, spatial, target, robot, stage }: { map: SpatialMap; spatial?: SpatialOverview; target?: WorkbenchScenarioResult["workflow_event"]["location"]; robot?: { x: number; y: number }; stage: number }) {
  const cameras = spatial?.cameras.filter((camera) => camera.map_id === map.map_id) ?? [];
  return <svg className="h-full w-full" viewBox={`0 0 ${map.width} ${map.height}`} role="img" aria-label="任务空间地图"><defs><pattern id="customer-grid" width="5" height="5" patternUnits="userSpaceOnUse"><path d="M 5 0 L 0 0 0 5" fill="none" stroke="#e5e7eb" strokeWidth="0.25" /></pattern></defs><rect width={map.width} height={map.height} fill="url(#customer-grid)" />{map.zones.map((zone) => <g key={zone.zone_id}><rect x={zone.x} y={zone.y} width={zone.w} height={zone.h} fill="#f1f5f9" stroke="#cbd5e1" strokeWidth="0.45" /><text x={zone.x + 2} y={zone.y + 4} fontSize="2.4" fill="#64748b">{zone.name}</text></g>)}{map.obstacles.map((obstacle, index) => <rect key={index} {...obstacle} fill="#94a3b8" />)}{cameras.map((camera) => <polygon key={camera.camera_id} points={camera.coverage_polygon.map((point) => `${point.x},${point.y}`).join(" ")} fill="#dbeafe" fillOpacity="0.22" stroke="#60a5fa" strokeWidth="0.3" strokeDasharray="1.2 1.2" />)}{cameras.map((camera) => <g key={camera.camera_id}><circle cx={camera.camera_position.x} cy={camera.camera_position.y} r="1.5" fill="#1e3a5f" stroke="white" strokeWidth="0.45" /><text x={camera.camera_position.x + 2} y={camera.camera_position.y} fontSize="1.5" fill="#1e3a5f">{camera.camera_id}</text></g>)}{target && stage >= 3 && <g><circle cx={target.x} cy={target.y} r="3.3" fill="#e11d48" fillOpacity="0.16"><animate attributeName="r" values="2.6;4.2;2.6" dur="1.5s" repeatCount="indefinite" /></circle><circle cx={target.x} cy={target.y} r="1.8" fill="#e11d48" stroke="white" strokeWidth="0.6" /></g>}{target && robot && stage >= 5 && <g><line x1={robot.x} y1={robot.y} x2={target.x} y2={target.y} stroke="#0f766e" strokeWidth="1" strokeDasharray="2 1.4" /><circle cy={robot.y} r="2.3" fill="#0f766e" stroke="white" strokeWidth="0.7"><animate attributeName="cx" values={`${robot.x};${target.x};${target.x}`} dur="4s" repeatCount="indefinite" /></circle></g>}</svg>;
}

function TaskPanel({ manifest, result, stage }: { manifest: DemoAssetManifest; result?: WorkbenchScenarioResult; stage: number }) {
  const decision = result?.workflow_event.assignment_decision; const event = result?.workflow_event; const human = manifest.verification_mode === "HUMAN_REQUIRED";
  const status = !result ? "等待运行" : human ? "人工工单已创建，等待现场回传" : stage < 5 ? "已生成调度与路线" : stage < 7 ? `${decision?.selected_robot_name ?? "机器人"} 正在执行清洁` : "固定摄像头验收通过，任务已闭环";
  return <aside className="border border-slate-200 bg-white"><div className="border-b border-slate-100 p-4"><p className="section-kicker">当前任务</p><h3 className="mt-1 text-base font-semibold">{result ? translateObject(event?.task_profile.object_type ?? "") : "等待现场事件"}</h3><p className="mt-1 text-xs text-slate-500">{manifest.location_label}</p></div><div className="space-y-4 p-4"><div><p className="section-kicker">任务状态</p><p className="mt-1 text-sm font-medium text-slate-800">{status}</p></div><div className="grid grid-cols-2 gap-y-3 border-y border-slate-100 py-3 text-xs"><Fact label="派单结果" value={decision?.selected_robot_name ?? (human && result ? "人工兜底" : "—")} /><Fact label="AI 置信度" value={result ? `${Math.round(result.initial_ai_result.perception.confidence * 100)}%` : "—"} /><Fact label="目标位置" value={event ? `${event.location.floor} ${event.location.zone}` : "待定位"} /><Fact label="清洁要求" value={event ? event.task_profile.required_capabilities.map(translateCapability).join(" + ") : "待生成"} /></div>{decision && <details open><summary className="cursor-pointer text-xs font-semibold text-slate-700">为什么选择 {decision.selected_robot_name ?? "人工兜底"}？</summary><p className="mt-2 text-[11px] leading-5 text-slate-600">{decision.reason}</p><div className="mt-2 space-y-1">{decision.candidates.map((candidate) => <p key={candidate.robot_id} className="text-[11px] text-slate-500">{candidate.robot_name}：{candidate.eligible ? `匹配 · 综合评分 ${candidate.final_score}` : candidate.reject_reasons.join("；")}</p>)}</div></details>}{event?.navigation_plan && <div className="border-t border-slate-100 pt-3"><p className="section-kicker">路线</p><p className="mt-1 text-[11px] leading-5 text-slate-600"><Route size={13} className="mr-1 inline" />{event.navigation_plan.display_path.join(" → ")} · {event.navigation_plan.total_cost} cost</p></div>}</div></aside>;
}

function MultiViewPanel({ manifest, trace }: { manifest: DemoAssetManifest; trace: NonNullable<WorkbenchScenarioResult["multi_view"]> }) {
  const primary = byRole(manifest, "before"); const evidence = manifest.assets.filter((asset) => asset.role === "evidence");
  return <section className="border border-slate-200 bg-white p-4"><div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end"><div><p className="section-kicker">多视角 AI 研判</p><h3 className="mt-1 text-base font-semibold">低置信度触发后，已使用 2 个额外摄像头确认</h3></div><Badge variant="success"><CheckCircle2 size={12} className="mr-1" />{trace.decision} · {Math.round(trace.final_confidence * 100)}%</Badge></div><div className="mt-4 grid gap-3 md:grid-cols-3"><Evidence asset={primary} title="主视角" confidence={`${Math.round(trace.initial_confidence * 100)}%`} />{evidence.map((asset, index) => <Evidence key={asset.camera_id} asset={asset} title="补充视角" confidence={`${Math.round((trace.evidence[index]?.confidence ?? 0) * 100)}%`} />)}</div><div className="mt-4 grid gap-2 border-t border-slate-100 pt-3 text-[11px] text-slate-600 sm:grid-cols-3"><p><Eye size={13} className="mr-1 inline" />Coverage Tool：{trace.selected_cameras.map((camera) => camera.camera_id).join(" / ")}</p><p><FileUp size={13} className="mr-1 inline" />Frame Fetch：{trace.evidence.length} 个同步证据</p><p><ScanLine size={13} className="mr-1 inline" />VLM Tool：{trace.decision}</p></div></section>;
}

function WorkflowTimeline({ result, humanFallback }: { result: WorkbenchScenarioResult; humanFallback: boolean }) {
  const transitions = humanFallback ? result.workflow_event.transitions.filter((transition) => !["VERIFYING", "CLOSED"].includes(transition.state)) : result.workflow_event.transitions;
  return <section className="border border-slate-200 bg-white p-4"><div className="flex items-end justify-between"><div><p className="section-kicker">业务执行审计</p><h3 className="mt-1 text-base font-semibold">{humanFallback ? "从识别到人工工单的系统记录" : "从识别到验收的系统记录"}</h3></div><Badge variant="outline">{transitions.length} 个状态变更</Badge></div>{humanFallback && <p className="mt-3 border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">工作台不把底层 Mock 的“人工已完成”演示占位呈现为真实闭环：此场景的工单状态为 <strong>OPEN</strong>，必须等待人工处理与同机位回传验收。</p>}<ol className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">{transitions.map((transition) => <li key={transition.id} className="border border-slate-100 bg-slate-50 p-2.5"><p className="text-[10px] font-bold tracking-wide text-slate-500">{transition.state}</p><p className="mt-1 text-[11px] leading-4 text-slate-700">{transitionMessage(transition.detail)}</p></li>)}</ol></section>;
}

function VerificationPanel({ manifest, result }: { manifest: DemoAssetManifest; result: WorkbenchScenarioResult }) {
  const before = byRole(manifest, "before"); const after = byRole(manifest, "after"); const human = manifest.verification_mode === "HUMAN_REQUIRED";
  if (human) return <section className="border border-amber-200 bg-amber-50/40 p-4"><div className="flex items-end justify-between"><div><p className="section-kicker">能力边界与人工兜底</p><h3 className="mt-1 text-base font-semibold text-amber-950">已创建人工工单，等待回传验收</h3></div><Badge variant="outline"><UsersRound size={12} className="mr-1" />HUMAN_FALLBACK</Badge></div><div className="mt-4 grid gap-3 md:grid-cols-2"><div><p className="mb-2 text-xs font-medium text-slate-600">清洁前</p><CameraImage asset={before} label="大型纸箱现场图" /></div><div className="flex min-h-[220px] flex-col items-center justify-center border border-dashed border-amber-300 bg-white px-5 text-center"><ClipboardCheck size={24} className="text-amber-600" /><p className="mt-2 text-sm font-semibold text-amber-950">未提供清洁后图</p><p className="mt-1 max-w-sm text-xs leading-5 text-amber-800">大型纸箱不进入 Robot Scheduler Pool。系统已生成公开可审计的人工工单，须由现场人员处理并回传同机位验收图。</p></div></div></section>;
  return <section className="border border-emerald-200 bg-emerald-50/30 p-4"><div className="flex items-end justify-between"><div><p className="section-kicker">固定摄像头自动验收</p><h3 className="mt-1 text-base font-semibold text-emerald-900">任务已自主闭环</h3></div><Badge variant="success">验收通过 · {Math.round((result.workflow_event.verification?.confidence ?? 0) * 100)}%</Badge></div><div className="mt-4 grid gap-3 md:grid-cols-2"><div><p className="mb-2 text-xs font-medium text-slate-600">清洁前</p><CameraImage asset={before} label="清洁前现场图" /></div><div><p className="mb-2 text-xs font-medium text-slate-600">清洁后</p><CameraImage asset={after} label="清洁后固定摄像头图" /></div></div><p className="mt-3 text-xs text-emerald-800"><ShieldCheck size={14} className="mr-1 inline" />后验图显示原污染物已清除；Mock Verification 结果为 PASS。</p></section>;
}

function Evidence({ asset, title, confidence }: { asset?: DemoAsset; title: string; confidence: string }) { return <div><CameraImage asset={asset} label={title} compact /><p className="mt-1 text-[11px] text-slate-600">{title} · {asset?.camera_id ?? "—"} · {confidence}</p></div>; }
function CameraImage({ asset, preview, label, detection, compact = false }: { asset?: DemoAsset; preview?: string; label: string; detection?: boolean; compact?: boolean }) { const source = preview ?? asset?.url; return <div className={`relative overflow-hidden border border-slate-200 bg-slate-50 ${compact ? "aspect-[16/8.5]" : "aspect-[4/3]"}`}>{source ? <img src={source} alt={label} className="h-full w-full object-cover" /> : <div className="flex h-full flex-col items-center justify-center px-4 text-center"><FileUp size={22} className="text-slate-300" /><p className="mt-2 text-xs font-medium text-slate-500">现场图不可用</p></div>}{detection && <><span className="absolute left-[34%] top-[32%] h-[24%] w-[30%] border-2 border-amber-500" /><span className="absolute left-[34%] top-[25%] bg-amber-500 px-1.5 py-0.5 text-[10px] font-semibold text-white">AI 识别目标</span></>}</div>; }
function Fact({ label, value }: { label: string; value: string }) { return <div><p className="text-[10px] uppercase tracking-wide text-slate-400">{label}</p><p className="mt-1 text-xs font-semibold text-slate-700">{value}</p></div>; }
function byRole(manifest: DemoAssetManifest, role: DemoAsset["role"]) { return manifest.assets.find((asset) => asset.role === role); }
function robotLabel(value: DemoAssetManifest["expected_robot"]) { return value === "HUMAN_FALLBACK" ? "人工兜底" : value.replace("ROBOT_", "Robot "); }
function translateObject(value: string) { return ({ small_litter: "室外纸巾", beverage_spill: "奶茶液体污渍", aluminum_can: "室内易拉罐", large_cardboard_box: "大型纸箱", paper_cup: "室内纸杯" } as Record<string, string>)[value] ?? value; }
function translateForm(value: string) { return ({ dry_debris: "干垃圾", liquid: "液体重污", large_object: "大件杂物" } as Record<string, string>)[value] ?? value; }
function translateCapability(value: string) { return ({ outdoor: "室外", dry_debris: "干垃圾", wet_cleaning: "湿洗", strong_suction: "强吸力", scrubbing: "刷洗", light_cleaning: "轻度清洁", large_object_pickup: "大件拾取" } as Record<string, string>)[value] ?? value; }
function transitionMessage(detail: Record<string, unknown>) { return typeof detail.message === "string" ? detail.message : typeof detail.reason === "string" ? detail.reason : "已记录此步骤。"; }
