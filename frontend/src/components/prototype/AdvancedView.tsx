import { AlertCircle, ChevronRight, Database, Eye, Gauge, ShieldCheck, Workflow } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  acceptsTraceResponse, advancedTraceUrl, formatTraceTime, nextSelectedNode, safeEvidenceUrl, safeSummaryEntries, safeTraceText, traceIdentityLabel,
  selectedTraceNode, sourceBadgeClass, sourceBadgeLabel, traceStatusLabel,
  type AdvancedTrace, type TraceNode, type TraceToolCall,
} from "./advancedTraceModel";
import type { ActiveEvent } from "./types";

type AdvancedViewProps = {
  event: ActiveEvent | null;
  runtimeMode: "live" | "replay";
  onRuntimeModeChange: (mode: "live" | "replay") => void;
};

function eventIdFor(event: ActiveEvent | null): string | null {
  const id = event?.liveResult?.event_id;
  return typeof id === "string" ? id : null;
}

function RuntimeField({ label, value }: { label: string; value: string }) {
  return <div className="min-w-[110px]"><p className="text-[9px] font-medium tracking-[0.1em] text-slate-400">{label}</p><p className="mt-1 truncate text-[11px] text-slate-700" title={value}>{value}</p></div>;
}

/** A small allowlisted backend projection; it never reads local configuration. */
function RuntimeInfo({ info }: { info: AdvancedTrace["runtime_info"] }) {
  if (!info) return null;
  const capabilities = Array.isArray(info.capabilities) ? info.capabilities.join(" · ") : "—";
  return <section className="border-t border-slate-100 px-4 py-2.5" aria-label="Interview Runtime 信息"><p className="text-[9px] font-semibold tracking-[0.12em] text-slate-400">INTERVIEW RUNTIME · BACKEND REPORTED</p><div className="mt-2 grid gap-x-4 gap-y-2 sm:grid-cols-2 lg:grid-cols-5"><RuntimeField label="RELEASE CONTRACT" value={info.release_contract ?? "—"} /><RuntimeField label="CLOUD STATUS" value={info.cloud_status ?? "—"} /><RuntimeField label="VLM MODEL" value={info.vlm_model ?? "—"} /><RuntimeField label="AGENT MODEL" value={info.agent_model ?? "—"} /><RuntimeField label="EVIDENCE MODE" value={info.evidence_mode ?? "—"} /><div className="min-w-0 sm:col-span-2 lg:col-span-5"><p className="text-[9px] font-medium tracking-[0.1em] text-slate-400">RUNTIME CAPABILITIES</p><p className="mt-1 truncate text-[11px] text-slate-700" title={capabilities}>{capabilities}</p></div></div></section>;
}

function Summary({ title, value }: { title: string; value?: Record<string, unknown> | null }) {
  const entries = safeSummaryEntries(value);
  return <section className="border border-slate-200 bg-slate-50/70 p-3"><p className="text-[10px] font-semibold tracking-[0.1em] text-slate-500">{title}</p>{entries.length ? <dl className="mt-2 space-y-1.5">{entries.map(([key, content]) => <div key={key} className="grid grid-cols-[minmax(72px,35%)_1fr] gap-2 text-[10px] leading-4"><dt className="break-words text-slate-400">{key}</dt><dd className="break-words text-slate-700">{content}</dd></div>)}</dl> : <p className="mt-2 text-[10px] text-slate-400">后端未记录可展示摘要。</p>}</section>;
}

function NodeRow({ node, selected, onSelect }: { node: TraceNode; selected: boolean; onSelect: (id: string) => void }) {
  return <button type="button" onClick={() => onSelect(node.id)} className={`group flex w-full items-center gap-2 border-l-2 px-3 py-2.5 text-left ${selected ? "border-slate-800 bg-slate-100" : "border-transparent bg-white hover:bg-slate-50"}`}><span className={`h-1.5 w-1.5 shrink-0 rounded-full ${node.status === "FAILED" || node.status === "ERROR" ? "bg-rose-500" : node.status === "NOT_TRIGGERED" ? "bg-slate-300" : "bg-[#4f7798]"}`} /><span className="min-w-0 flex-1"><span className="block truncate text-[11px] font-medium text-slate-800">{node.label}</span><span className="mt-0.5 block truncate text-[9px] text-slate-400">{traceStatusLabel(node.status)} · {node.duration_ms === null || node.duration_ms === undefined ? "时长未记录" : `${node.duration_ms} ms`}</span></span><ChevronRight size={13} className="shrink-0 text-slate-300 group-hover:text-slate-500" /></button>;
}

function TraceGroup({ title, nodes, selectedId, onSelect }: { title: string; nodes: TraceNode[]; selectedId: string | null; onSelect: (id: string) => void }) {
  return <section className="border border-slate-200 bg-white"><header className="flex items-center justify-between border-b border-slate-100 px-3 py-2"><p className="text-[10px] font-semibold tracking-[0.12em] text-slate-500">{title}</p><span className="font-mono text-[10px] text-slate-400">{nodes.length}</span></header>{nodes.length ? nodes.map((node) => <NodeRow key={node.id} node={node} selected={node.id === selectedId} onSelect={onSelect} />) : <p className="px-3 py-3 text-[10px] text-slate-400">后端尚未返回该链路记录。</p>}</section>;
}

function ToolTrace({ calls }: { calls: TraceToolCall[] }) {
  return <section className="border border-slate-200 bg-white"><header className="flex items-center gap-2 border-b border-slate-100 px-3 py-2"><Workflow size={13} className="text-slate-500" /><p className="text-[10px] font-semibold tracking-[0.12em] text-slate-500">TOOL TRACE</p><span className="font-mono text-[10px] text-slate-400">{calls.length}</span></header>{calls.length ? <div className="divide-y divide-slate-100">{calls.map((call) => <article key={call.id} className="p-3"><div className="flex flex-wrap items-center justify-between gap-2"><p className="font-mono text-[10px] font-medium text-slate-800">{call.name}</p><span className={`border px-1.5 py-0.5 text-[9px] ${sourceBadgeClass(call.source)}`}>{sourceBadgeLabel(call.source)}</span></div><p className="mt-1 text-[10px] text-slate-500">触发：{call.trigger_source ?? "未记录"} · 开始：{formatTraceTime(call.start_time)} · 时长：{call.duration_ms === null || call.duration_ms === undefined ? "—" : `${call.duration_ms} ms`} · 状态：{traceStatusLabel(call.status)}</p><div className="mt-2 grid gap-2 md:grid-cols-2"><Summary title="INPUT SUMMARY" value={call.input_summary} /><Summary title="RESULT SUMMARY" value={call.result_summary} /></div></article>)}</div> : <p className="px-3 py-3 text-[10px] text-slate-400">此 Trace 没有可展示的工具调用记录。</p>}</section>;
}

function NodeDetail({ node }: { node: TraceNode | null }) {
  if (!node) return <aside className="flex min-h-[460px] items-center justify-center border border-slate-200 bg-white p-8 text-center"><div><Eye size={20} className="mx-auto text-slate-300" /><p className="mt-3 text-sm font-medium text-slate-700">选择一个执行节点</p><p className="mt-1 text-xs leading-5 text-slate-500">仅查看后端已持久化的结构化输入、输出和证据摘要。</p></div></aside>;
  return <aside className="min-h-0 overflow-y-auto border border-slate-200 bg-white"><header className="border-b border-slate-200 px-4 py-3"><p className="text-[10px] font-semibold tracking-[0.12em] text-slate-400">SELECTED NODE</p><div className="mt-1 flex flex-wrap items-center justify-between gap-2"><h2 className="text-sm font-semibold">{node.label}</h2><span className={`border px-1.5 py-0.5 text-[9px] ${sourceBadgeClass(node.source)}`}>{sourceBadgeLabel(node.source)}</span></div><p className="mt-1.5 text-[10px] text-slate-500">状态：{traceStatusLabel(node.status)} · 触发：{node.trigger_source ?? "未记录"} · 开始：{formatTraceTime(node.start_time)} · 时长：{node.duration_ms === null || node.duration_ms === undefined ? "—" : `${node.duration_ms} ms`}</p></header><div className="space-y-3 p-4"><Summary title="INPUT SUMMARY" value={node.input_summary} /><Summary title="OUTPUT SUMMARY" value={node.output_summary} />{node.evidence?.length ? <section className="border border-slate-200 p-3"><p className="text-[10px] font-semibold tracking-[0.1em] text-slate-500">EVIDENCE</p><div className="mt-2 space-y-1.5">{node.evidence.map((evidence, index) => { const url = safeEvidenceUrl(evidence.url); return <p key={`${evidence.camera_id ?? "camera"}-${index}`} className="text-[10px] text-slate-600">{evidence.camera_id ?? "Camera 未记录"} · {evidence.role ?? "role 未记录"}{url ? <a href={url} target="_blank" rel="noreferrer" className="ml-1 text-[#3d6f93] underline underline-offset-2">查看受控资产</a> : null}</p>; })}</div></section> : null}{node.error ? <section className="border border-rose-200 bg-rose-50 p-3 text-[10px] leading-5 text-rose-800"><p className="font-semibold">{node.error.type ?? "ERROR"}{node.error.code ? ` · ${node.error.code}` : ""}</p><p>{safeTraceText(node.error.message) ?? "后端未提供错误描述。"}</p></section> : null}</div></aside>;
}

function RealityMatrix({ trace }: { trace: AdvancedTrace }) {
  const rows = trace.reality ?? [];
  return <section className="border border-slate-200 bg-white"><header className="flex items-center gap-2 border-b border-slate-100 px-3 py-2"><ShieldCheck size={13} className="text-slate-500" /><p className="text-[10px] font-semibold tracking-[0.12em] text-slate-500">SYSTEM REALITY MATRIX</p></header>{rows.length ? <div className="divide-y divide-slate-100">{rows.map((row, index) => <article key={`${row.component ?? "component"}-${index}`} className="grid gap-2 px-3 py-2.5 md:grid-cols-[minmax(120px,0.75fr)_minmax(190px,1fr)_minmax(0,1.7fr)]"><p className="text-[10px] font-medium text-slate-800">{row.component ?? "组件未记录"}</p><div><span className={`inline-flex border px-1.5 py-0.5 text-[9px] ${sourceBadgeClass(row.status)}`}>{sourceBadgeLabel(row.status)}</span>{row.execution_status && <p className="mt-1 text-[9px] text-slate-500">执行状态：{traceStatusLabel(row.execution_status)}</p>}{row.replacement && <p className="mt-1 text-[9px] text-slate-400">替换点：{safeTraceText(row.replacement)}</p>}</div><p className="text-[10px] leading-4 text-slate-600">{safeTraceText(row.detail)}</p></article>)}</div> : <p className="px-3 py-3 text-[10px] text-slate-400">后端尚未返回 Reality Matrix 记录。</p>}</section>;
}

/** Read-only Technical Observability. Node clicks only select local projected records. */
export function AdvancedView({ event, runtimeMode, onRuntimeModeChange }: AdvancedViewProps) {
  const [trace, setTrace] = useState<AdvancedTrace | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const requestRef = useRef(0);
  const requestedEventId = eventIdFor(event);

  useEffect(() => {
    const request = ++requestRef.current;
    const controller = new AbortController();
    setLoading(true); setError(null);
    void fetch(advancedTraceUrl(requestedEventId), { signal: controller.signal })
      .then(async (response) => {
        const body = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : `Trace ${response.status}`);
        return body as AdvancedTrace;
      })
      .then((body) => {
        if (!acceptsTraceResponse(request, requestRef.current)) return;
        const nodes = Array.isArray(body.nodes) ? body.nodes : [];
        setTrace({ ...body, nodes });
        setSelectedNodeId((current) => nextSelectedNode(nodes, current));
      })
      .catch((reason) => {
        if (!controller.signal.aborted && acceptsTraceResponse(request, requestRef.current)) {
          setTrace(null);
          setSelectedNodeId(null);
          setError(reason instanceof Error ? reason.message : "Trace 暂不可读取");
        }
      })
      .finally(() => { if (!controller.signal.aborted && acceptsTraceResponse(request, requestRef.current)) setLoading(false); });
    return () => controller.abort();
  }, [requestedEventId]);

  const nodes = trace?.nodes ?? [];
  const selected = selectedTraceNode(nodes, selectedNodeId);
  const aiNodes = useMemo(() => nodes.filter((node) => node.group === "AI"), [nodes]);
  const spatialNodes = useMemo(() => nodes.filter((node) => node.group === "SPATIAL"), [nodes]);
  const runtimeNodes = useMemo(() => nodes.filter((node) => node.group === "RUNTIME"), [nodes]);
  const runtime = trace?.runtime;
  const configured = runtime?.configured === true ? "已配置" : runtime?.configured === false ? "未配置" : "未知";

  return <main className="min-h-[calc(100vh-54px)] bg-[#f6f7f8] px-5 py-5 text-slate-800 lg:px-7" aria-label="高级技术可观测性"><div className="mx-auto max-w-[1540px]"><header className="border border-slate-200 bg-white"><div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 px-4 py-3"><div><p className="text-[10px] font-semibold tracking-[0.16em] text-slate-400">TECHNICAL OBSERVABILITY · READ ONLY</p><h1 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">高级技术可观测性</h1><p className="mt-1 text-xs text-slate-500">只投影已持久化的 Runtime、工具、空间与验证记录；选择节点不会重跑模型、调度或路线。</p></div><div className="flex border border-slate-200 p-0.5" aria-label="下次运行模式"><button type="button" onClick={() => onRuntimeModeChange("live")} className={`px-3 py-1.5 text-xs ${runtimeMode === "live" ? "bg-slate-900 text-white" : "text-slate-600"}`}>LIVE</button><button type="button" onClick={() => onRuntimeModeChange("replay")} className={`px-3 py-1.5 text-xs ${runtimeMode === "replay" ? "bg-slate-900 text-white" : "text-slate-600"}`}>Stable Replay</button></div></div><div className="grid gap-3 px-4 py-3 sm:grid-cols-2 lg:grid-cols-6"><RuntimeField label="TRACE ID" value={traceIdentityLabel(trace?.trace_id, trace?.trace_status)} /><RuntimeField label="EVENT ID" value={trace?.event_id ?? requestedEventId ?? "最新集成事件"} /><RuntimeField label="RUNTIME MODE" value={trace?.mode ?? "—"} /><RuntimeField label="CLOUD PROVIDER / MODEL" value={[runtime?.provider, runtime?.model].filter(Boolean).join(" / ") || "—"} /><RuntimeField label="MODEL CONFIGURATION" value={configured} /><RuntimeField label="LAST REQUEST" value={`${runtime?.last_request_status ?? "—"}${runtime?.last_latency_ms === null || runtime?.last_latency_ms === undefined ? "" : ` · ${runtime.last_latency_ms} ms`}${runtime?.last_request_at ? ` · ${formatTraceTime(runtime.last_request_at)}` : ""}`} /></div><RuntimeInfo info={trace?.runtime_info} /></header>{error && <div role="alert" className="mt-3 flex items-center gap-2 border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800"><AlertCircle size={14} />无法读取 Trace：{safeTraceText(error)}</div>}{loading ? <div className="flex min-h-[460px] items-center justify-center text-sm text-slate-500">正在读取只读 Trace 记录…</div> : trace ? <div className="mt-3 grid gap-3 xl:grid-cols-[minmax(0,63fr)_minmax(320px,37fr)]"><section className="min-w-0 space-y-3"><div className="flex items-center gap-2 border border-slate-200 bg-white px-3 py-2 text-[10px] text-slate-500"><Database size={13} />Trace → Node → Inspect · 节点数 {nodes.length} · 工具记录 {(trace.tool_calls ?? []).length}</div><TraceGroup title="AI RECOGNITION TRACE · 六段投影" nodes={aiNodes} selectedId={selectedNodeId} onSelect={setSelectedNodeId} /><TraceGroup title="SPATIAL / CAPABILITY / SCHEDULING / ROUTE" nodes={spatialNodes} selectedId={selectedNodeId} onSelect={setSelectedNodeId} />{runtimeNodes.length ? <TraceGroup title="RUNTIME / VERIFICATION" nodes={runtimeNodes} selectedId={selectedNodeId} onSelect={setSelectedNodeId} /> : null}<ToolTrace calls={trace.tool_calls ?? []} /><RealityMatrix trace={trace} />{trace.errors?.length ? <section className="border border-rose-200 bg-rose-50 p-3"><p className="text-[10px] font-semibold tracking-[0.1em] text-rose-800">ERROR TAXONOMY</p>{trace.errors.map((item, index) => <p key={`${item.type ?? "error"}-${index}`} className="mt-1 text-[10px] leading-4 text-rose-800">{item.type ?? "ERROR"}{item.code ? ` · ${item.code}` : ""}{item.message ? ` · ${safeTraceText(item.message)}` : ""}</p>)}</section> : null}</section><NodeDetail node={selected} /></div> : <div className="mt-3 flex min-h-[460px] items-center justify-center border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500"><div><Gauge size={20} className="mx-auto text-slate-300" /><p className="mt-3">后端尚未返回可展示的 Trace。</p><p className="mt-1 text-xs">不会以当前页面状态或默认节点伪造技术记录。</p></div></div>}</div></main>;
}
