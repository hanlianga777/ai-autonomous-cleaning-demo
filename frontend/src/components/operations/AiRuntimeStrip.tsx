import { useEffect, useState } from "react";

type AiStatus = { yolo: { mode: string; model: string | null; loaded: boolean }; qwen_vl: { mode: string; model: string; api_key_configured: boolean }; multiview_agent: { mode: string }; camera_to_slam: { mode: string }; scheduler: { mode: string }; robot: { mode: string }; verification: { mode: string } };

export function AiRuntimeStrip() {
  const [status, setStatus] = useState<AiStatus>();
  useEffect(() => { void fetch("/api/system/ai-status").then((response) => response.ok ? response.json() : Promise.reject()).then(setStatus).catch(() => undefined); }, []);
  const items = status ? [
    ["YOLO", status.yolo.mode], ["Qwen-VL", status.qwen_vl.mode], ["Multi-view", status.multiview_agent.mode], ["空间定位", status.camera_to_slam.mode], ["调度", status.scheduler.mode], ["机器人", status.robot.mode], ["验收", status.verification.mode],
  ] : [["AI 状态", "正在连接"]];
  return <div className="flex flex-wrap gap-x-4 gap-y-1 border-y border-slate-200 bg-white px-3 py-2 text-[10px] text-slate-500">{items.map(([label, mode]) => <span key={label}><span className="font-semibold text-slate-700">{label}</span> · <span className={mode === "REAL" || mode === "REAL_READY" || mode === "REAL_LOGIC" || mode === "REAL_CALCULATION" || mode === "REAL_ALGORITHM" ? "text-emerald-700" : mode === "SIMULATION" ? "text-amber-700" : "text-slate-500"}>{mode}</span></span>)}</div>;
}
