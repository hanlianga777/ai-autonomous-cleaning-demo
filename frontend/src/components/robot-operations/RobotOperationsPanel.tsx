import { Bot, MessageCircle, Send, X } from "lucide-react";
import { useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import { useRobotOperations } from "./RobotOperationsProvider";
import { FLOATING_BALL_SIZE, FLOATING_CHAT_SIZE, FLOATING_EXPANDED_KEY, FLOATING_POSITION_KEY, actionLabel, clampFloatingPosition, customerAgentMessage, defaultFloatingPosition, parseStoredPosition, readStorage, recentTasks, taskActions, taskExecutorLabel, taskKindLabel, taskLocationLabel, taskStatusLabel, writeStorage, type OperationsTask } from "./robotOperationsModel";

type PageContext = Record<string, unknown>;

function TaskCard({ task, compact = false }: { task: OperationsTask; compact?: boolean }) {
  const { pending, session, taskAction } = useRobotOperations();
  const origin = task.origin?.label ?? "未提供起点";
  const destination = taskLocationLabel(task.destination?.label);
  return <article className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-[12px] text-slate-600"><div className="flex items-start justify-between gap-2"><p className="font-semibold text-slate-800">{taskKindLabel(task.kind)}</p><span className="rounded-full bg-white px-2 py-0.5 text-[11px] text-slate-600">{taskStatusLabel(task.status)}</span></div><p className="mt-2 leading-5">{taskExecutorLabel(task)}</p><p className="leading-5">{origin} → {destination}</p>{!compact && <div className="mt-2 flex flex-wrap gap-1.5">{taskActions(task).filter((action) => action !== "advance").map((action) => <button key={action} type="button" disabled={pending || Boolean(session?.busy)} onClick={() => void taskAction(task, action)} className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-[12px] font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50">{actionLabel(action)}</button>)}</div>}</article>;
}

function Messages({ compact = false }: { compact?: boolean }) {
  const { session, loading, error, pending } = useRobotOperations();
  if (loading) return <div className="flex flex-1 items-center justify-center px-3 text-[11px] text-slate-500">正在连接运营助手…</div>;
  if (!session) return <div className="flex flex-1 items-center justify-center px-3 text-center text-[11px] leading-5 text-amber-700">{error ?? "运营助手暂不可用。"}</div>;
  const busy = pending || Boolean(session.busy);
  return <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4" aria-live="polite">{session.messages.length ? session.messages.map((message) => <article key={message.id} className={`whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-[13px] leading-6 shadow-sm ${message.role === "user" ? "ml-10 bg-slate-900 text-white" : "mr-5 border border-slate-200 bg-white text-slate-700"}`}><p className={`mb-1 text-[11px] font-semibold ${message.role === "user" ? "text-slate-300" : "text-slate-400"}`}>{message.role === "user" ? "你" : "运营助手"}</p>{customerAgentMessage(message.content)}</article>) : <p className="py-10 text-center text-[13px] leading-6 text-slate-500">你好，我是园区运营助手。可以查询当前事件、机器人状态，或下达合法的配送与调度指令。</p>}{busy && <p className="text-[12px] text-slate-500">正在整理当前园区运营信息…</p>}{error && <p role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-[12px] leading-5 text-amber-800">{customerAgentMessage(error)}</p>}{!compact && session.tasks.length > 0 && <div className="space-y-2 border-t border-slate-100 pt-3"><p className="text-[12px] font-semibold text-slate-600">当前任务</p>{recentTasks(session.tasks).map((task) => <TaskCard key={task.task_id} task={task} />)}</div>}</div>;
}

function Composer({ pageContext }: { pageContext: PageContext }) {
  const { session, pending, sendMessage } = useRobotOperations();
  const [text, setText] = useState("");
  const busy = pending || Boolean(session?.busy);
  const send = () => { if (!text.trim()) return; void sendMessage(text, pageContext).then((sent) => { if (sent) setText(""); }); };
  return <div className="border-t border-slate-200 bg-white p-3"><div className="flex items-center gap-2 rounded-xl border border-slate-300 bg-slate-50 p-1.5 focus-within:border-slate-500"><input aria-label="运营助手输入框" value={text} disabled={!session || busy} onChange={(event) => setText(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.nativeEvent.isComposing) { event.preventDefault(); send(); } }} placeholder="输入运营指令或问题…" className="min-w-0 flex-1 bg-transparent px-2 text-[13px] outline-none placeholder:text-slate-400 disabled:bg-slate-50" /><button type="button" disabled={!session || busy || !text.trim()} onClick={send} className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-white disabled:bg-slate-300" aria-label="发送"><Send size={15} /></button></div></div>;
}

export function RobotOperationsChat({ pageContext, className = "" }: { pageContext: PageContext; className?: string }) {
  return <section className={`flex min-h-0 flex-col bg-white ${className}`} aria-label="Robot Operations Agent 对话"><Messages /><Composer pageContext={pageContext} /></section>;
}

export function FloatingRobotOperationsAgent({ pageContext }: { pageContext: PageContext }) {
  const [expanded, setExpanded] = useState(() => readStorage(FLOATING_EXPANDED_KEY) === "true");
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null);
  const drag = useRef<{ pointerId: number; offsetX: number; offsetY: number; moved: boolean } | null>(null);
  const justDragged = useRef(false);
  useEffect(() => {
    const viewport = () => ({ width: window.innerWidth, height: window.innerHeight });
    const restore = () => setPosition((current) => clampFloatingPosition(current ?? parseStoredPosition(readStorage(FLOATING_POSITION_KEY), viewport()) ?? defaultFloatingPosition(viewport()), viewport(), expanded ? FLOATING_CHAT_SIZE : FLOATING_BALL_SIZE));
    restore(); window.addEventListener("resize", restore); return () => window.removeEventListener("resize", restore);
  }, [expanded]);
  const beginDrag = (event: ReactPointerEvent<HTMLElement>) => {
    if (!position) return;
    drag.current = { pointerId: event.pointerId, offsetX: event.clientX - position.x, offsetY: event.clientY - position.y, moved: false };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const moveDrag = (event: ReactPointerEvent<HTMLElement>) => {
    if (!drag.current || drag.current.pointerId !== event.pointerId) return;
    drag.current.moved = true;
    const next = clampFloatingPosition({ x: event.clientX - drag.current.offsetX, y: event.clientY - drag.current.offsetY }, { width: window.innerWidth, height: window.innerHeight }, expanded ? FLOATING_CHAT_SIZE : FLOATING_BALL_SIZE);
    setPosition(next); writeStorage(FLOATING_POSITION_KEY, JSON.stringify(next));
  };
  const stopDrag = (event: ReactPointerEvent<HTMLElement>) => { if (drag.current?.pointerId === event.pointerId) { justDragged.current = drag.current.moved; drag.current = null; } };
  if (!position) return null;
  const toggleExpanded = () => setExpanded((value) => { const next = !value; writeStorage(FLOATING_EXPANDED_KEY, String(next)); return next; });
  if (!expanded) return <button type="button" onPointerDown={beginDrag} onPointerMove={moveDrag} onPointerUp={stopDrag} onPointerCancel={stopDrag} onClick={(event) => { if (!justDragged.current) toggleExpanded(); justDragged.current = false; event.stopPropagation(); }} className="fixed z-[70] flex h-14 w-14 touch-none items-center justify-center rounded-full bg-slate-900 text-white shadow-[0_12px_30px_rgba(15,23,42,.28)] transition hover:scale-105 focus:outline-none focus:ring-4 focus:ring-sky-200 active:cursor-grabbing" style={{ left: position.x, top: position.y }} aria-label="打开 Robot Operations Agent"><MessageCircle size={25} /><span className="absolute -right-0.5 -top-0.5 h-3 w-3 rounded-full border-2 border-white bg-emerald-400" /></button>;
  return <section className="fixed z-[70] flex h-[min(560px,calc(100dvh-32px))] w-[min(420px,calc(100vw-32px))] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl" style={{ left: position.x, top: position.y }} aria-label="Robot Operations Agent 完整对话窗口"><header className="flex shrink-0 items-center justify-between border-b border-slate-200 bg-slate-900 px-4 py-3 text-white"><div className="flex items-center gap-2.5"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-sky-400 text-slate-900"><Bot size={19} /></span><div><p className="text-[14px] font-semibold">Robot Operations Agent</p><p className="text-[11px] text-slate-300">园区运营协作助手 · 在线</p></div></div><button type="button" onClick={toggleExpanded} className="rounded-lg p-2 text-slate-300 hover:bg-white/10 hover:text-white" aria-label="收起为 AI 悬浮球"><X size={18} /></button></header><RobotOperationsChat pageContext={pageContext} /></section>;
}
export function AnalyticsAgentChat({ pageContext }: { pageContext: PageContext }) {
  return <aside className="sticky top-0 flex h-[calc(100dvh-54px)] min-h-[560px] flex-col border-l border-slate-200 bg-white" aria-label="Robot Operations Agent 固定对话"><header className="border-b border-slate-200 px-4 py-4"><div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-white"><Bot size={16} /></span><div><p className="text-[14px] font-semibold text-slate-900">Robot Operations Agent</p><p className="text-[11px] text-slate-500">园区运营协作助手</p></div></div></header><RobotOperationsChat pageContext={pageContext} /></aside>;
}

/** Proactive insight projection; the Chat remains the single reactive Agent UI. */
export function AnalyticsAdviceCards() {
  const { advice, adviceError, adviceLoading, loadAdvice } = useRobotOperations();
  useEffect(() => { void loadAdvice(); }, [loadAdvice]);
  if (adviceLoading && !advice) return <section className="mt-4 rounded-2xl border border-slate-200 bg-white p-4 text-[13px] text-slate-500">正在读取运营洞察…</section>;
  if (adviceError) return <section className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-[13px] text-amber-800">运营洞察暂不可用：{adviceError}</section>;
  const items = advice?.items.slice(0, 3) ?? [];
  return <section className="mt-4" aria-label="AI 运营建议"><div className="mb-2"><p className="text-[12px] font-semibold text-slate-900">AI 运营建议</p><p className="mt-0.5 text-[12px] text-slate-500">基于近 30 天已授权运营事实生成</p></div><div className="grid gap-3 lg:grid-cols-3">{items.length ? items.map((item, index) => <article key={`${item.finding}-${index}`} className="rounded-2xl border border-slate-200 bg-white p-4"><p className="text-[13px] font-semibold text-slate-900">{item.finding}</p><p className="mt-2 text-[12px] leading-5 text-slate-600">{item.evidence}</p><p className="mt-3 border-t border-slate-100 pt-3 text-[12px] leading-5 text-slate-700">建议：{item.recommendation}</p></article>) : <article className="rounded-2xl border border-slate-200 bg-white p-4 text-[13px] text-slate-500">暂无可用的运营建议。</article>}</div></section>;
}
