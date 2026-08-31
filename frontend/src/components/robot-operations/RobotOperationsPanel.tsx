import { ArrowUpRight, Bot, LoaderCircle, MessageCircle, Send, Sparkles, X } from "lucide-react";
import { useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import { useRobotOperations } from "./RobotOperationsProvider";
import { FLOATING_BALL_SIZE, FLOATING_CHAT_SIZE, FLOATING_EXPANDED_KEY, FLOATING_POSITION_KEY, clampFloatingPosition, customerAgentMessage, defaultFloatingPosition, parseStoredPosition, readStorage, writeStorage, type AdviceItem } from "./robotOperationsModel";

type PageContext = Record<string, unknown>;

const QUICK_PROMPTS = [
  "当前有哪些事件需要优先处理？",
  "过去 30 天哪些区域问题较多？",
  "三台清洁机器人现在是什么状态？",
  "A栋1F液体污渍如何改善？",
];

function conciseCustomerReply(content: string): string {
  const source = customerAgentMessage(content).replace(/^本轮未执行任务写操作。\s*/, "").trim();
  const total = source.match(/当前共有\s*(\d+)\s*条事件/);
  const pending = source.match(/需人工介入\/待处理[^。\n]*?共\s*(\d+)\s*条/);
  const location = source.match(/位于\s*([^，。；\n]+?)(?:，|。|；|\s已)/);
  if (total && pending) return `当前情况：共有 ${total[1]} 条事件，其中 ${pending[1]} 条需要人工关注。\n\n建议：优先复核${location?.[1] ?? "未闭环点位"}，确认后再安排后续处理。`;
  const sentences = source.split(/(?<=[。！？])\s*/).map((item) => item.trim()).filter((item) => item && !/工具|返回列表|Task ID|session/i.test(item));
  return sentences.slice(0, 3).join("\n\n") || "暂未获得可展示的运营结论。";
}

function StructuredAssistantMessage({ content }: { content: string }) {
  const sections = conciseCustomerReply(content).split(/\n{2,}/).map((item) => item.trim()).filter(Boolean);
  return <div className="space-y-2.5">{sections.map((section, index) => {
    const match = section.match(/^([^：:]{1,14})[：:]\s*(.+)$/s);
    return match ? <div key={`${match[1]}-${index}`} className="grid grid-cols-[74px_minmax(0,1fr)] gap-2 border-b border-slate-100 pb-2 last:border-0 last:pb-0"><span className="text-[11px] font-medium text-slate-400">{match[1]}</span><p className="text-[12px] leading-5 text-slate-700">{match[2]}</p></div> : <p key={`${section}-${index}`} className="text-[12px] leading-5 text-slate-700">{section}</p>;
  })}</div>;
}

function QuickPrompts({ pageContext, disabled }: { pageContext: PageContext; disabled: boolean }) {
  const { sendMessage } = useRobotOperations();
  return <section className="mx-auto w-full max-w-[310px]" aria-label="运营助手推荐问题"><div className="mb-3 flex items-center gap-1.5 text-[12px] font-semibold text-slate-700"><Sparkles size={14} className="text-sky-600" />推荐问题</div><div className="divide-y divide-slate-100 overflow-hidden rounded-xl border border-slate-200 bg-white/80 shadow-sm">{QUICK_PROMPTS.map((prompt) => <button key={prompt} type="button" disabled={disabled} onClick={() => void sendMessage(prompt, pageContext)} className="group flex w-full items-center justify-between gap-3 px-3 py-2.5 text-left text-[12px] text-slate-600 transition hover:bg-slate-50 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"><span>{prompt}</span><ArrowUpRight size={13} className="shrink-0 text-slate-300 transition group-hover:text-sky-600" /></button>)}</div></section>;
}

function Messages({ pageContext }: { pageContext: PageContext }) {
  const { session, loading, error, pending } = useRobotOperations();
  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => { scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" }); }, [pending, session?.messages.length]);
  if (loading) return <div className="flex flex-1 items-center justify-center px-3 text-[11px] text-slate-500">正在连接运营助手…</div>;
  if (!session) return <div className="flex flex-1 items-center justify-center px-3 text-center text-[11px] leading-5 text-amber-700">{error ?? "运营助手暂不可用。"}</div>;
  const busy = pending || Boolean(session.busy);
  return <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4" aria-live="polite">{session.messages.length ? session.messages.map((message) => message.role === "user" ? <article key={message.id} className="ml-10 rounded-2xl bg-slate-900 px-3.5 py-2.5 text-[13px] leading-6 text-white shadow-sm">{customerAgentMessage(message.content)}</article> : <article key={message.id} className="mr-3 rounded-2xl border border-slate-200 bg-white px-3.5 py-3 shadow-sm"><div className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold text-slate-400"><Bot size={13} />AI运营助手</div><StructuredAssistantMessage content={message.content} /></article>) : <div className="flex min-h-full flex-col justify-center py-8"><div className="mx-auto mb-6 max-w-[300px] text-center"><span className="mx-auto flex h-10 w-10 items-center justify-center rounded-2xl bg-sky-50 text-sky-700"><Bot size={19} /></span><p className="mt-3 text-[14px] font-semibold text-slate-800">今天想了解什么？</p><p className="mt-1 text-[12px] leading-5 text-slate-500">可快速查看事件、热区与机器人状态。</p></div><QuickPrompts pageContext={pageContext} disabled={busy} /></div>}{busy && <p className="flex items-center gap-1.5 text-[12px] text-slate-500"><LoaderCircle size={14} className="animate-spin" />正在发送并等待运营助手响应…</p>}{error && <p role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-[12px] leading-5 text-amber-800">{customerAgentMessage(error)}</p>}</div>;
}

function Composer({ pageContext }: { pageContext: PageContext }) {
  const { session, pending, sendMessage } = useRobotOperations();
  const [text, setText] = useState("");
  const busy = pending || Boolean(session?.busy);
  const send = () => { const outgoing = text.trim(); if (!outgoing || busy) return; setText(""); void sendMessage(outgoing, pageContext); };
  return <div className="border-t border-slate-200 bg-white p-3"><div className="flex items-center gap-2 rounded-xl border border-slate-300 bg-slate-50 p-1.5 focus-within:border-slate-500"><input aria-label="运营助手输入框" value={text} disabled={!session} onChange={(event) => setText(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.nativeEvent.isComposing) { event.preventDefault(); send(); } }} placeholder="输入运营指令或问题…" className="min-w-0 flex-1 bg-transparent px-2 text-[13px] outline-none placeholder:text-slate-400 disabled:bg-slate-50" /><button type="button" disabled={!session || busy || !text.trim()} onClick={send} className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-white disabled:bg-slate-300" aria-label="发送"><Send size={15} /></button></div></div>;
}

export function RobotOperationsChat({ pageContext, className = "" }: { pageContext: PageContext; className?: string }) {
  return <section className={`flex min-h-0 flex-col bg-white ${className}`} aria-label="Robot Operations Agent 对话"><Messages pageContext={pageContext} /><Composer pageContext={pageContext} /></section>;
}

export function FloatingRobotOperationsAgent({ pageContext }: { pageContext: PageContext }) {
  const [expanded, setExpanded] = useState(() => readStorage(FLOATING_EXPANDED_KEY) === "true");
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null);
  const drag = useRef<{ pointerId: number; offsetX: number; offsetY: number; moved: boolean } | null>(null);
  const justDragged = useRef(false);
  useEffect(() => {
    const viewport = () => ({ width: window.innerWidth, height: window.innerHeight });
    const restore = () => setPosition((current) => clampFloatingPosition(current ?? parseStoredPosition(readStorage(FLOATING_POSITION_KEY), viewport()) ?? defaultFloatingPosition(viewport()), viewport(), FLOATING_BALL_SIZE));
    restore(); window.addEventListener("resize", restore); return () => window.removeEventListener("resize", restore);
  }, []);
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
  const panelPosition = clampFloatingPosition(position, { width: window.innerWidth, height: window.innerHeight }, FLOATING_CHAT_SIZE);
  if (!expanded) return <button type="button" onPointerDown={beginDrag} onPointerMove={moveDrag} onPointerUp={stopDrag} onPointerCancel={stopDrag} onClick={(event) => { if (!justDragged.current) toggleExpanded(); justDragged.current = false; event.stopPropagation(); }} className="fixed z-[70] flex h-14 w-14 touch-none items-center justify-center rounded-full bg-slate-900 text-white shadow-[0_12px_30px_rgba(15,23,42,.28)] transition hover:scale-105 focus:outline-none focus:ring-4 focus:ring-sky-200 active:cursor-grabbing" style={{ left: position.x, top: position.y }} aria-label="打开园区运营助手"><MessageCircle size={25} /><span className="absolute -right-0.5 -top-0.5 h-3 w-3 rounded-full border-2 border-white bg-emerald-400" /></button>;
  return <section className="fixed z-[70] flex h-[min(560px,calc(100dvh-32px))] w-[min(420px,calc(100vw-32px))] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl" style={{ left: panelPosition.x, top: panelPosition.y }} aria-label="AI运营助手完整对话窗口"><header className="flex shrink-0 items-center justify-between border-b border-slate-200 bg-slate-900 px-4 py-3 text-white"><div className="flex items-center gap-2.5"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-sky-400 text-slate-900"><Bot size={19} /></span><div><p className="text-[14px] font-semibold">AI运营助手</p><p className="text-[11px] text-slate-300">协助查询事件与执行进度</p></div></div><button type="button" onClick={toggleExpanded} className="rounded-lg p-2 text-slate-300 hover:bg-white/10 hover:text-white" aria-label="收起为 AI 悬浮球"><X size={18} /></button></header><RobotOperationsChat pageContext={pageContext} /></section>;
}
export function AnalyticsAgentChat({ pageContext }: { pageContext: PageContext }) {
  return <aside className="sticky top-0 flex h-[calc(100dvh-54px)] min-h-[560px] flex-col border-l border-slate-200 bg-white" aria-label="AI运营助手固定对话"><header className="border-b border-slate-200 px-4 py-4"><div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-white"><Bot size={16} /></span><div><p className="text-[14px] font-semibold text-slate-900">AI运营助手</p><p className="text-[11px] text-slate-400">面向园区的快速运营问答</p></div></div></header><RobotOperationsChat pageContext={pageContext} /></aside>;
}

function adviceCardLines(item: AdviceItem): [string, string] {
  const source = customerAgentMessage(`${item.finding} ${item.recommendation}`);
  if (/东入口/.test(source) && /液体/.test(source)) return ["A栋1F东入口常见液体污渍。", "核查排水条件，并加密巡检。"];
  if (/大件/.test(source)) return ["大件事件常超过24小时未闭环。", "建立人工响应时限提醒。"];
  if (/East Road|东侧道路|东道路|unknown/i.test(source)) return ["园区东侧道路常见识别不清事件。", "优化镜头光照，并补充标注。"];
  return [customerAgentMessage(item.finding), customerAgentMessage(item.recommendation)];
}

/** Proactive insight projection; the Chat remains the single reactive Agent UI. */
export function AnalyticsAdviceCards() {
  const { advice, adviceError, adviceLoading, loadAdvice } = useRobotOperations();
  useEffect(() => { void loadAdvice(); }, [loadAdvice]);
  if (adviceLoading && !advice) return <section className="mt-4 rounded-2xl border border-slate-200 bg-white p-4 text-[13px] text-slate-500">正在读取运营洞察…</section>;
  if (adviceError) return <section className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-[13px] text-amber-800">运营洞察暂不可用：{adviceError}</section>;
  const items = advice?.items.slice(0, 3) ?? [];
  return <section className="mt-4" aria-label="AI 运营建议"><div className="mb-2"><p className="text-[12px] font-semibold text-slate-900">AI 运营建议</p></div><div className="grid gap-3 lg:grid-cols-3">{items.length ? items.map((item, index) => { const [finding, recommendation] = adviceCardLines(item); return <article key={`${item.finding}-${index}`} className="rounded-2xl border border-slate-200 bg-white p-3"><p className="text-[13px] font-semibold text-slate-900">运营建议 {index + 1}</p><p className="mt-1.5 text-[12px] leading-5 text-slate-700">{finding}</p><p className="text-[12px] leading-5 text-slate-700">{recommendation}</p></article>; }) : <article className="rounded-2xl border border-slate-200 bg-white p-3 text-[13px] text-slate-500">暂无可用的运营建议。</article>}</div></section>;
}
