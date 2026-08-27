import { Check } from "lucide-react";

import type { OperationsWorkOrder } from "@/types/operations";

const stages: Array<[string, string[]]> = [
  ["AI发现", ["DETECTED", "JUDGING"]], ["云端确认", ["MULTI_VIEW", "CONFIRMED"]], ["空间定位", ["LOCATING", "PROFILING"]],
  ["机器人调度", ["CAPABILITY_CHECK", "SCHEDULING", "ASSIGNED"]], ["执行清洁", ["NAVIGATING", "ARRIVED", "CLEANING"]],
  ["固定摄像头验收", ["VERIFYING"]], ["任务闭环", ["CLOSED"]],
];

export function BusinessTimeline({ workOrder }: { workOrder: OperationsWorkOrder | null }) {
  const current = workOrder?.display_state ?? "";
  const currentIndex = stages.findIndex(([, states]) => (states as string[]).includes(current));
  return <aside className="border border-slate-200 bg-white p-4"><p className="section-kicker">任务进度</p><h3 className="mt-1 text-base font-semibold">业务闭环</h3><ol className="mt-5 space-y-4">{stages.map(([label], index) => { const done = currentIndex > index || current === "CLOSED"; const active = currentIndex === index && current !== "CLOSED"; return <li key={label} className="flex items-center gap-3"><span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-[11px] ${done ? "border-emerald-600 bg-emerald-600 text-white" : active ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 text-slate-400"}`}>{done ? <Check size={13} /> : index + 1}</span><div><p className={`text-xs font-semibold ${done || active ? "text-slate-800" : "text-slate-400"}`}>{label}</p><p className="mt-0.5 text-[10px] text-slate-400">{done ? "已完成" : active ? "进行中" : "等待"}</p></div></li>; })}</ol></aside>;
}
