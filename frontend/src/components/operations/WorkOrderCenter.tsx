import { useEffect, useState } from "react";
import { ChevronRight, ClipboardList, LoaderCircle, MapPin, RefreshCw } from "lucide-react";

import { fetchOperationsWorkOrders } from "@/api/operations";
import type { OperationsWorkOrderSummary } from "@/types/operations";

const stateLabel: Record<string, string> = {
  DETECTED: "待研判", JUDGING: "AI 研判中", MULTI_VIEW: "多视角确认中", CONFIRMED: "AI 确认完成",
  LOCATING: "空间定位中", PROFILING: "任务生成中", SCHEDULING: "机器人调度中", ASSIGNED: "已派单",
  NAVIGATING: "机器人前往", ARRIVED: "已到达", CLEANING: "清洁中", VERIFYING: "AI 验收中",
  CLOSED: "已自主闭环", HUMAN_FALLBACK: "人工处理", HUMAN_REVIEW: "待人工复核", FAILED: "处理失败",
};

function displayObject(value: string) {
  return ({ beverage_spill: "液体污渍", aluminum_can: "易拉罐", small_litter: "其他小型垃圾", large_cardboard_box: "大件物品" } as Record<string, string>)[value] ?? value;
}

export function WorkOrderCenter() {
  const [orders, setOrders] = useState<OperationsWorkOrderSummary[]>([]);
  const [selected, setSelected] = useState<OperationsWorkOrderSummary>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  async function load() { setLoading(true); try { const next = await fetchOperationsWorkOrders(); setOrders(next); setSelected((current) => next.find((item) => item.event_id === current?.event_id) ?? next[0]); setError(""); } catch (reason) { setError(reason instanceof Error ? reason.message : "无法读取工单"); } finally { setLoading(false); } }
  useEffect(() => { void load(); }, []);
  if (loading) return <div className="flex min-h-[420px] items-center justify-center text-sm text-slate-500"><LoaderCircle size={16} className="mr-2 animate-spin" />正在读取工单中心…</div>;
  return <section className="mx-auto max-w-[1440px] space-y-5"><header className="flex items-end justify-between border-b border-slate-200 pb-4"><div><p className="section-kicker">Work orders</p><h2 className="mt-1 text-xl font-semibold tracking-tight">工单中心</h2><p className="mt-1 text-xs text-slate-500">每一张卡片均对应一个持久化的 CleaningEvent；内部调度和模型明细在详情中查看。</p></div><button onClick={() => void load()} className="flex h-9 items-center gap-1.5 border border-slate-300 bg-white px-3 text-xs font-semibold text-slate-700 hover:bg-slate-50"><RefreshCw size={13} />刷新</button></header>
    {error && <p role="alert" className="border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
    <div className="grid gap-5 lg:grid-cols-[0.56fr_0.44fr]"><div className="divide-y divide-slate-100 border border-slate-200 bg-white">{orders.length ? orders.map((order) => <button key={order.event_id} onClick={() => setSelected(order)} className={`flex w-full gap-3 p-4 text-left transition-colors ${selected?.event_id === order.event_id ? "bg-slate-50" : "hover:bg-slate-50"}`}><div className="h-16 w-20 shrink-0 overflow-hidden bg-slate-100">{order.image_url ? <img src={order.image_url} alt="事件现场" className="h-full w-full object-cover" /> : <ClipboardList className="m-5 text-slate-300" size={24} />}</div><div className="min-w-0 flex-1"><div className="flex justify-between gap-2"><p className="truncate text-sm font-semibold text-slate-800">{displayObject(order.task_profile.object_type)}</p><span className="shrink-0 text-[11px] font-medium text-slate-500">{stateLabel[order.state] ?? order.state}</span></div><p className="mt-1 flex items-center gap-1 text-[11px] text-slate-500"><MapPin size={12} />{order.location.building} 栋 · {order.location.floor} · {order.location.zone}</p><p className="mt-1 text-[11px] text-slate-400">{order.event_id} · {order.robot_name ?? "待分派"}</p></div><ChevronRight size={15} className="mt-5 shrink-0 text-slate-300" /></button>) : <p className="p-8 text-center text-sm text-slate-500">尚无工单。请在工作台创建 Scenario 02。</p>}</div>
      <aside className="border border-slate-200 bg-white p-5">{selected ? <><p className="section-kicker">Work order summary</p><h3 className="mt-1 text-lg font-semibold">{displayObject(selected.task_profile.object_type)}</h3><p className="mt-1 text-xs text-slate-500">{selected.event_id}</p><dl className="mt-6 grid grid-cols-2 gap-y-5 border-y border-slate-100 py-4 text-xs"><Fact label="业务状态" value={stateLabel[selected.state] ?? selected.state} /><Fact label="执行对象" value={selected.robot_name ?? "待分派"} /><Fact label="位置" value={`${selected.location.building} 栋 ${selected.location.floor}`} /><Fact label="区域" value={selected.location.zone} /></dl><p className="mt-5 text-xs leading-5 text-slate-500">打开“高级模式 / 技术详情”可查看 AI 原始输出、能力校验、路线和工作流审计。客户默认界面保持业务语言。</p></> : <p className="text-sm text-slate-500">选择一张工单查看摘要。</p>}</aside></div>
  </section>;
}

function Fact({ label, value }: { label: string; value: string }) { return <div><dt className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">{label}</dt><dd className="mt-1 font-semibold text-slate-700">{value}</dd></div>; }
