import { CameraViewport } from "./CameraViewport";
import { customerTerm, eventCamera, type RecordValue, type TimelineEntry } from "./eventViewModel";
import type { ActiveEvent } from "./types";

const percent = (value: unknown) => typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "—";
const card = "mt-2 space-y-1.5 border border-slate-200 bg-slate-50 p-2 text-[11px] leading-5 text-slate-600";

function CameraEvidence({ event, cameraId, after = false, detections = false }: { event: ActiveEvent; cameraId?: string; after?: boolean; detections?: boolean }) {
  const camera = eventCamera(event, after ? "after" : "before", cameraId);
  return camera ? <CameraViewport camera={camera} compact showDetections={detections} /> : <p className="border border-dashed border-slate-300 p-3 text-[11px] text-slate-500">该阶段证据图片未存档或不可用。</p>;
}

function CloudSummary({ event }: { event: ActiveEvent }) {
  const result = event.liveResult as RecordValue;
  const review = result?.qwen_review;
  const first = result?.first_qwen_review;
  const second = result?.second_qwen_review;
  const fusion = result?.evidence_fusion;
  if (!review) return <p className="mt-2 text-[11px] text-amber-700">尚未取得有效的云端结构化判断。</p>;
  const times = [first?.elapsed_ms ?? review.elapsed_ms, second?.elapsed_ms].filter((t) => typeof t === "number");
  return <div className={card}>
    <p className="font-medium text-slate-800">{review.need_clean ? "需要处置" : "无需处置"} · {customerTerm(review.event_type)}</p>
    <p>污染程度：{customerTerm(review.severity)} · 地面：{customerTerm(review.surface_type)}</p>
    <p>首轮云端置信度：{percent(first?.decision_confidence ?? review.decision_confidence)}</p>
    {second && <p>独立复核置信度：{percent(second.decision_confidence)}</p>}
    {review.evidence_summary && <p>证据摘要：{String(review.evidence_summary)}</p>}
    {Array.isArray(review.interference_factors) && review.interference_factors.length > 0 && <p>干扰因素：{review.interference_factors.map(customerTerm).join("、")}</p>}
    {fusion && <p className="border-t border-slate-200 pt-1.5 font-medium text-slate-700">系统 Fusion 处置评分：{typeof fusion.score === "number" ? Math.round(fusion.score * 100) : "—"}分</p>}
    <p className="text-[10px] text-slate-500">{result.mode === "STABLE_REPLAY" ? "读取已保存 LIVE 响应 · 本次未调用模型" : times.length ? `模型 API 耗时 ${Math.round(times.reduce((a, b) => a + b, 0))} ms` : "模型 API 耗时未记录"}</p>
  </div>;
}

const constraints: Array<[RegExp, string]> = [
  [/battery|电量/i, "电量不满足要求"], [/offline|离线/i, "机器人离线"], [/busy|忙碌|occupied/i, "已有执行中的任务"],
  [/capabilit|能力|large_object|lifting|搬运/i, "不具备所需处置能力"], [/surface|地面/i, "地面材质不匹配"],
  [/scope|building|floor|zone|范围|区域/i, "不在允许作业范围内"],
];
function constraintLabel(reason: string): string { return constraints.find(([match]) => match.test(reason))?.[1] ?? (/^[\x00-\x7F]*$/.test(reason) ? "不满足调度硬约束" : reason); }

function routeLabel(value: string): string {
  const labels: Record<string, string> = { OUTDOOR: "园区道路", Outdoor: "园区道路", "A Elevator": "A栋电梯", "B Elevator": "B栋电梯", Skybridge: "空中连廊", "Skybridge A": "连廊A端", "Skybridge B": "连廊B端", SKYBRIDGE_A: "连廊A端", SKYBRIDGE_B: "连廊B端" };
  return labels[value] ?? value.replace(/^([AB])[-_]([12])F$/, "$1栋 $2F").replace(/^([AB])_ELEVATOR_([12])F$/, "$1栋电梯 $2F");
}

function TerminalFleet({ result }: { result: RecordValue }) {
  const robot = result.fleet_snapshot?.find((item: RecordValue) => item.id === result.assignment_decision?.selected_robot_id);
  if (!robot) return null;
  return <p className="mt-2 border-t border-slate-200 pt-2 text-[11px] leading-5 text-slate-600" title={`SLAM (${robot.coordinates?.x}, ${robot.coordinates?.y})`}>事件终态快照：{robot.name} · {routeLabel(robot.map_id)} · 电量 {robot.battery}% · {robot.status === "idle" ? "待命" : "状态已存档"}。机器人保留在本次终点。</p>;
}

function CapabilitySummary({ decision }: { decision?: RecordValue }) {
  if (!decision) return <p className="mt-2 text-xs text-slate-500">尚无能力匹配记录。</p>;
  return <div className={card}><p className="font-medium text-slate-800">可用候选：{decision.candidate_count ?? "—"}</p>
    {(decision.candidates ?? []).map((candidate: RecordValue) => <div key={candidate.robot_id} className="border-t border-slate-200 pt-1.5"><p className="font-medium">{candidate.robot_name}</p><p>{candidate.eligible ? `满足硬约束 · 调度评分 ${candidate.final_score ?? "—"}` : (candidate.reject_reasons ?? []).map(constraintLabel).join("；") || "不满足硬约束"}</p></div>)}
    <p className="border-t border-slate-200 pt-1.5 font-medium">{decision.selected_robot_name ? `派发：${decision.selected_robot_name}` : decision.candidate_count === 0 ? "无机器人具备所需能力，转人工处置。" : "未生成机器人派单。"}</p>
  </div>;
}

export function EventStageEvidence({ event, entry, mode, onCompleteManual }: { event: ActiveEvent; entry: TimelineEntry; mode: "live" | "history"; onCompleteManual?: () => void }) {
  const result = (event.liveResult ?? {}) as RecordValue;
  if (entry.pending) return <p className="mt-2 text-[11px] text-slate-500">正在执行本阶段，等待真实服务结果…</p>;
  switch (entry.state) {
    case "DETECTED": return <p className="mt-1 text-[11px] text-slate-500">现场证据已接收，事件已持久化。</p>;
    case "EDGE_DETECTED": return <div className={card}><CameraEvidence event={event} detections /><p>受控边缘检测证据 · 检测框与原图同坐标系；不代表本地 YOLO 实跑。</p></div>;
    case "MULTI_VIEW": {
      const selected = result.multi_view?.selected_cameras ?? [];
      const ids = [...new Set<string>([event.scenario.cameraId, ...selected.map((s: RecordValue) => s.camera_id)])];
      return <div className={card}><p>已取得的多视角证据 · 主视角 + {Math.max(0, ids.length - 1)} 路补充</p>{ids.map((id) => <div key={id}><CameraEvidence event={event} cameraId={id} /><p className="text-[10px]">{id}</p></div>)}<p>已记录迭代：{result.multi_view?.iteration_count ?? "—"}</p><p>仅展示已取得的证据，不展示模型思维链。</p></div>;
    }
    case "CLOUD_REVIEW": return <CloudSummary event={event} />;
    case "LOCATED": {
      const location = entry.detail;
      return <div className={card}><p>Camera→SLAM 标定映射已完成</p><p>{location.building} 栋 · {location.floor} · {customerTerm(location.zone)}</p><p title={`SLAM ${location.map_id}: (${location.x}, ${location.y})`}>空间落点已写入事件与地图。</p></div>;
    }
    case "ASSIGNED": return <CapabilitySummary decision={entry.detail.assignment_decision} />;
    case "NAVIGATING": return <div className={card}><p>依据后端 Dijkstra 拓扑规划前往事件落点。</p><p>{(entry.detail.navigation_plan?.display_path ?? entry.detail.navigation_plan?.node_path ?? []).map(routeLabel).join(" → ")}</p><p>地图连续移动为 PoC 视觉插值，不是真实机器人遥测。</p></div>;
    case "ARRIVED": return <p className="mt-2 text-[11px] text-slate-500">已记录到达目标区域，Fleet 位置更新完成。</p>;
    case "CLEANING_COMPLETED": return <p className="mt-2 text-[11px] text-slate-500">PoC 清洁执行完成，准备读取处置后证据。</p>;
    case "HUMAN_FALLBACK": return <><CapabilitySummary decision={entry.detail.assignment_decision} /><div className="mt-2 border border-amber-200 bg-amber-50 p-2 text-[11px] leading-5 text-amber-900"><p className="font-medium">人工处置工单已创建</p><p>能力引擎候选数为零。完成搬运后由固定摄像头证据进入同一验收流程。</p>{mode === "live" && event.backendState === "HUMAN_FALLBACK" && <button disabled={event.processing || !onCompleteManual} onClick={onCompleteManual} className="mt-2 border border-amber-400 bg-white px-2 py-1 font-medium disabled:opacity-40">确认人工清理完成并验收</button>}{event.backendState !== "HUMAN_FALLBACK" && <p>人工完成动作已记录。</p>}</div></>;
    case "VERIFYING": return <div className={card}><p>处置后固定摄像头证据</p><CameraEvidence event={event} after />{result.verification ? <><p className="font-medium">AI 验收：{result.verification.verification_pass ? "模型判定通过" : "模型判定未通过"} · {percent(result.verification.confidence)}</p><p>{result.mode === "STABLE_REPLAY" ? "历史真实验收响应 · 工作流本次重新执行" : "真实云端验收响应"}</p></> : <p>尚无有效验收结果，请查看后续处理状态。</p>}</div>;
    case "CLOSED": return <div className="mt-2 border border-emerald-200 bg-emerald-50 p-2 text-[11px] leading-5 text-emerald-800"><p className="font-semibold">验收门控通过 · 完整闭环已持久化</p><p>执行方：{result.assignment_decision?.selected_robot_name ?? (entry.detail.manual_completion ? "人工处置" : "历史记录未注明")}</p><TerminalFleet result={result} /></div>;
    case "HUMAN_REVIEW": return <>{entry.detail.cloud_review && <CloudSummary event={event} />}<div className="mt-2 border border-amber-200 bg-amber-50 p-2 text-[11px] leading-5 text-amber-900"><p className="font-semibold">自动流程停止，转人工复核</p><p>{customerTerm(entry.detail.reason ?? result.reason)}</p><p>此前阶段记录完整保留，不抹去已发生的派单或移动。</p><TerminalFleet result={result} /></div></>;
    default: return <p className="mt-1 text-[11px] text-slate-500">阶段已存档。</p>;
  }
}
