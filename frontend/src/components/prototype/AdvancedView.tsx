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

/** Customer-facing Advanced shell. Backend observability stays available to engineering APIs. */
export function AdvancedView(_: AdvancedViewProps) {
  const [expanded, setExpanded] = useState(false);
  return <main className="min-h-[calc(100vh-54px)] bg-[#f6f7f8] px-5 py-6 text-slate-800 lg:px-8" aria-label="高级模式"><div className="mx-auto max-w-[1040px]"><header className="mb-6"><p className="text-[12px] font-semibold tracking-[0.14em] text-slate-400">ADVANCED MODE</p><h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">技术展示辅助页</h1><p className="mt-2 text-[14px] leading-6 text-slate-600">用于面试讲解时展示经确认的技术材料。</p></header><button type="button" onClick={() => setExpanded(true)} className="flex min-h-[430px] w-full items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center transition hover:border-slate-400"><span><Eye size={28} className="mx-auto text-slate-300" /><strong className="mt-4 block text-[16px] text-slate-700">PENDING USER ASSET</strong><span className="mt-2 block text-[13px] leading-6 text-slate-500">等待用户提供最终技术讲解图片。收到后将在此居中展示，点击可放大。</span></span></button>{expanded && <div role="dialog" aria-label="技术图片放大预览" onClick={() => setExpanded(false)} className="fixed inset-0 z-[90] flex items-center justify-center bg-slate-950/75 p-6"><div className="rounded-2xl bg-white p-8 text-center text-[14px] text-slate-600">PENDING USER ASSET</div></div>}</div></main>;
}
