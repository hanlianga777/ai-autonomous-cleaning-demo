import { Bot, ChevronDown, ChevronUp, Mic, Send, Wrench } from "lucide-react";
import { useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import { useRobotOperations } from "./RobotOperationsProvider";
import { FLOATING_EXPANDED_KEY, FLOATING_POSITION_KEY, actionLabel, adviceWindowLabel, clampFloatingPosition, defaultFloatingPosition, parseStoredPosition, readStorage, recentTasks, taskActions, taskKindLabel, taskRobotLabel, taskStatusLabel, writeStorage, type AgentAudit, type OperationsTask } from "./robotOperationsModel";

type PageContext = Record<string, unknown>;

function TaskCard({ task, compact = false }: { task: OperationsTask; compact?: boolean }) {
  const { pending, session, taskAction } = useRobotOperations();
  const origin = task.origin?.label ?? "未提供起点";
  const destination = task.destination?.label ?? "未提供目的地";
  return <article className="border border-slate-200 bg-slate-50 p-2.5 text-[10px] text-slate-600"><div className="flex items-start justify-between gap-2"><div><p className="font-semibold text-slate-800">{taskKindLabel(task.kind)}</p><p className="mt-0.5 font-mono text-slate-500">{task.task_id}</p></div><span className="border border-slate-200 bg-white px-1.5 py-0.5 text-slate-600">{taskStatusLabel(task.status)}</span></div><p className="mt-2 leading-4">机器人：{taskRobotLabel(task.robot_id)}</p><p className="leading-4">{origin} → {destination}</p><p className="mt-1 text-slate-400">来源：{task.source === "POC_SIMULATION" ? "PoC 模拟任务" : task.source}</p>{!compact && <div className="mt-2 flex flex-wrap gap-1.5">{taskActions(task).map((action) => <button key={action} type="button" disabled={pending || Boolean(session?.busy)} onClick={() => void taskAction(task, action)} className="border border-slate-300 bg-white px-2 py-1 text-[10px] text-slate-700 hover:bg-slate-100 disabled:opacity-50">{actionLabel(action)}</button>)}</div>}</article>;
}

function auditOutcome(audit: AgentAudit): string {
  if (audit.error) return `结果：${typeof audit.error === "string" ? audit.error : audit.error.message ?? "失败"}`;
  if (audit.result?.ok === true) return "结果：成功";
  if (audit.result?.ok === false) return "结果：未完成";
  return audit.final_status ? `状态：${audit.final_status}` : "已记录";
}

function AuditTrail({ audits }: { audits: AgentAudit[] }) {
  if (!audits.length) return null;
  return <section className="space-y-1.5 border-t border-slate-100 pt-2" aria-label="工具审计"><p className="text-[10px] font-semibold text-slate-500">工具审计 <span className="font-normal text-slate-400">· 不展示模型推理</span></p>{audits.slice(-6).reverse().map((audit, index) => <article key={`${audit.id ?? audit.created_at ?? "audit"}-${index}`} className="border border-slate-100 bg-slate-50 px-2 py-1.5 text-[9px] leading-4 text-slate-600"><p className="font-medium text-slate-700">{audit.tool ?? audit.phase ?? "Agent Runtime"}{audit.policy ? ` · ${audit.policy}` : ""}</p><p>{auditOutcome(audit)}{audit.created_at ? ` · ${audit.created_at}` : ""}</p></article>)}</section>;
}

function Messages({ compact = false }: { compact?: boolean }) {
  const { session, loading, error, pending } = useRobotOperations();
  if (loading) return <div className="flex flex-1 items-center justify-center px-3 text-[11px] text-slate-500">正在读取共享 Agent Session…</div>;
  if (!session) return <div className="flex flex-1 items-center justify-center px-3 text-center text-[11px] leading-5 text-amber-700">{error ?? "Robot Operations Agent Session 未建立。"}</div>;
  const busy = pending || Boolean(session.busy);
  return <div className="flex-1 space-y-2 overflow-y-auto px-3 py-2" aria-live="polite">{session.messages.length ? session.messages.map((message) => <article key={message.id} className={`border px-2.5 py-2 text-[11px] leading-5 ${message.role === "user" ? "ml-7 border-slate-300 bg-slate-100 text-slate-700" : "mr-3 border-slate-200 bg-white text-slate-700"}`}><p className="mb-0.5 text-[9px] font-semibold tracking-[0.08em] text-slate-400">{message.role === "user" ? "操作员" : message.role === "assistant" ? "ROBOT OPERATIONS AGENT" : "SYSTEM"}</p>{message.content}</article>) : <p className="py-8 text-center text-[11px] leading-5 text-slate-500">尚无对话记录。输入指令后由后端 Agent 读取当前页面事实并生成可审计响应。</p>}{busy && <p className="text-[10px] text-slate-500">正在等待后端 Agent 响应；不会显示预设文本。</p>}{error && <p role="alert" className="border border-amber-200 bg-amber-50 p-2 text-[10px] leading-4 text-amber-800">{error}</p>}{!compact && session.tasks.length > 0 && <div className="space-y-2 border-t border-slate-100 pt-2"><p className="text-[10px] font-semibold text-slate-500">任务操作卡</p>{recentTasks(session.tasks).map((task) => <TaskCard key={task.task_id} task={task} />)}</div>}<AuditTrail audits={session.audits} /></div>;
}

function Composer({ pageContext }: { pageContext: PageContext }) {
  const { session, pending, sendMessage } = useRobotOperations();
  const [text, setText] = useState("");
  const busy = pending || Boolean(session?.busy);
  const send = () => { if (!text.trim()) return; void sendMessage(text, pageContext).then((sent) => { if (sent) setText(""); }); };
  return <div className="border-t border-slate-200 bg-white p-2.5"><div className="flex gap-1.5"><button type="button" disabled title="语音服务未配置" aria-label="语音服务未配置" className="flex h-8 w-8 shrink-0 items-center justify-center border border-slate-200 text-slate-300"><Mic size={14} /></button><input aria-label="Robot Operations Agent 指令" value={text} disabled={!session || busy} onChange={(event) => setText(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.nativeEvent.isComposing) { event.preventDefault(); send(); } }} placeholder="例如：查看当前机器人任务" className="min-w-0 flex-1 border border-slate-300 px-2 text-[11px] outline-none focus:border-slate-500 disabled:bg-slate-50" /><button type="button" disabled={!session || busy || !text.trim()} onClick={send} className="flex h-8 w-8 items-center justify-center bg-slate-800 text-white disabled:bg-slate-300" aria-label="发送指令"><Send size={13} /></button></div><p className="mt-1.5 text-[9px] text-slate-400">语音服务未配置 · 仅提交文本给后端 Agent；不使用前端预设回复。</p></div>;
}

export function RobotOperationsChat({ pageContext, className = "" }: { pageContext: PageContext; className?: string }) {
  return <section className={`flex min-h-0 flex-col bg-white ${className}`} aria-label="Robot Operations Agent 对话"><Messages /><Composer pageContext={pageContext} /></section>;
}

export function FloatingRobotOperationsAgent({ pageContext }: { pageContext: PageContext }) {
  const [expanded, setExpanded] = useState(() => readStorage(FLOATING_EXPANDED_KEY) !== "false");
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null);
  const drag = useRef<{ pointerId: number; offsetX: number; offsetY: number } | null>(null);
  useEffect(() => {
    const viewport = () => ({ width: window.innerWidth, height: window.innerHeight });
    const restore = () => setPosition((current) => clampFloatingPosition(current ?? parseStoredPosition(readStorage(FLOATING_POSITION_KEY), viewport()) ?? defaultFloatingPosition(viewport()), viewport()));
    restore(); window.addEventListener("resize", restore); return () => window.removeEventListener("resize", restore);
  }, [FLOATING_POSITION_KEY, clampFloatingPosition, defaultFloatingPosition, parseStoredPosition, readStorage]);
  const beginDrag = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (!position) return;
    drag.current = { pointerId: event.pointerId, offsetX: event.clientX - position.x, offsetY: event.clientY - position.y };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const moveDrag = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (!drag.current || drag.current.pointerId !== event.pointerId) return;
    const next = clampFloatingPosition({ x: event.clientX - drag.current.offsetX, y: event.clientY - drag.current.offsetY }, { width: window.innerWidth, height: window.innerHeight });
    setPosition(next); writeStorage(FLOATING_POSITION_KEY, JSON.stringify(next));
  };
  const stopDrag = (event: ReactPointerEvent<HTMLDivElement>) => { if (drag.current?.pointerId === event.pointerId) drag.current = null; };
  if (!position) return null;
  const toggleExpanded = () => setExpanded((value) => { const next = !value; writeStorage(FLOATING_EXPANDED_KEY, String(next)); return next; });
  return <section className={`fixed z-[70] flex w-[352px] max-w-[calc(100vw-24px)] flex-col overflow-hidden border border-slate-300 bg-white shadow-xl ${expanded ? "h-[454px] max-h-[calc(100dvh-24px)]" : "h-10"}`} style={{ left: position.x, top: position.y }} aria-label="Robot Operations Agent 浮动窗口"><div onPointerDown={beginDrag} onPointerMove={moveDrag} onPointerUp={stopDrag} onPointerCancel={stopDrag} className="flex h-10 shrink-0 cursor-grab touch-none items-center justify-between border-b border-slate-200 bg-slate-900 px-3 text-white active:cursor-grabbing"><div className="flex items-center gap-1.5"><Bot size={14} /><span className="text-[11px] font-medium">Robot Operations Agent</span><span className="text-[9px] text-slate-300">共享会话</span></div><button type="button" onPointerDown={(event) => event.stopPropagation()} onClick={toggleExpanded} className="p-1 text-slate-300 hover:text-white" aria-label={expanded ? "收起 Agent" : "展开 Agent"}>{expanded ? <ChevronDown size={15} /> : <ChevronUp size={15} />}</button></div>{expanded && <RobotOperationsChat pageContext={pageContext} />}</section>;
}

export function AnalyticsAdviceAndChat({ pageContext }: { pageContext: PageContext }) {
  const { advice, adviceError, adviceLoading, loadAdvice, regenerateAdvice, session } = useRobotOperations();
  useEffect(() => { void loadAdvice(); }, [loadAdvice]);
  return <aside className="flex min-h-0 flex-col border-l border-slate-200 bg-white" aria-label="AI 运营优化建议与 Robot Operations Agent"><section className="max-h-[42%] shrink-0 overflow-y-auto border-b border-slate-200 p-4"><div className="flex items-start justify-between gap-2"><div><p className="text-[10px] font-semibold tracking-[0.12em] text-slate-400">AI OPERATIONS ADVICE</p><p className="mt-1 text-xs font-semibold text-slate-800">AI 运营优化建议</p></div><button type="button" disabled={adviceLoading} onClick={() => void regenerateAdvice()} className="border border-slate-300 bg-white px-2 py-1 text-[10px] text-slate-700 disabled:opacity-50">{adviceLoading ? "请求中…" : "重新生成"}</button></div>{adviceError && <p role="alert" className="mt-2 text-[10px] leading-4 text-amber-800">{adviceError}</p>}{advice ? <><p className="mt-2 text-[10px] text-slate-500">缓存快照 · {adviceWindowLabel(advice.data_window)} · {advice.generated_at}</p><div className="mt-2 space-y-2">{advice.items.map((item, index) => <article key={`${item.finding}-${index}`} className="border-l-2 border-slate-400 pl-2 text-[10px] leading-4 text-slate-600"><p className="font-medium text-slate-800">{item.finding}</p><p>依据：{item.evidence}</p><p>建议：{item.recommendation}</p>{item.related_events.length > 0 && <p className="text-slate-400">关联：{item.related_events.join("、")}</p>}</article>)}</div></> : !adviceLoading && <p className="mt-3 text-[11px] leading-5 text-slate-500">暂无已保存运营建议快照。仅点击“重新生成”才请求后端 Agent。</p>}</section><section className="flex min-h-0 flex-1 flex-col"><div className="flex items-center gap-1.5 border-b border-slate-100 px-4 py-2 text-[10px] font-medium text-slate-600"><Wrench size={12} />Robot Operations Agent {session ? "· 共享会话" : "· Session 连接中"}</div><RobotOperationsChat pageContext={pageContext} /></section></aside>;
}
