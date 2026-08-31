import { CameraViewport } from "./CameraViewport";
import { customerTerm, eventCamera, type RecordValue, type TimelineEntry } from "./eventViewModel";
import type { ActiveEvent } from "./types";

const percent = (value: unknown) => typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "—";
const card = "mt-2 space-y-1.5 border border-slate-200 bg-slate-50 p-2 text-[12px] leading-5 text-slate-600";

function CameraEvidence({ event, cameraId, after = false, detections = false }: { event: ActiveEvent; cameraId?: string; after?: boolean; detections?: boolean }) {
  const camera = eventCamera(event, after ? "after" : "before", cameraId);
  return camera ? <CameraViewport camera={camera} compact showDetections={detections} /> : <p className="border border-dashed border-slate-300 p-3 text-[12px] text-slate-500">该阶段证据图片未存档或不可用。</p>;
}

function CloudSummary({ event }: { event: ActiveEvent }) {
  const result = event.liveResult as RecordValue;
  const review = result?.qwen_review;
  const first = result?.first_qwen_review;
  const second = result?.second_qwen_review;
  const fusion = result?.evidence_fusion;
  if (!review) return <p className="mt-2 text-[12px] text-amber-700">尚未取得有效的云端结构化判断。</p>;
  return <div className={card}>
    <p><strong>研判结果：</strong>{review.need_clean ? "需要处置" : "无需处置"}</p>
    <p><strong>事件类型：</strong>{customerTerm(review.event_type)}</p>
    <p><strong>AI研判置信度：</strong>{percent(review.decision_confidence)}</p>
    <p><strong>污染程度：</strong>{customerTerm(review.severity)}</p>
    <p><strong>地面材质：</strong>{customerTerm(review.surface_type)}</p>
    {fusion && <p className="border-t border-slate-200 pt-1.5 font-medium text-slate-700"><strong>系统处置评分：</strong>{typeof fusion.score === "number" ? Math.round(fusion.score * 100) : "—"}分</p>}
    {review.evidence_summary && <p><strong>研判摘要：</strong>{String(review.evidence_summary)}</p>}
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
  return labels[value] ?? value.replace(/^([AB])[-_]([12])F$/, "$1栋$2F").replace(/^([AB])_ELEVATOR_([12])F$/, "$1栋电梯$2F");
}

function TerminalFleet({ result }: { result: RecordValue }) {
  const robot = result.fleet_snapshot?.find((item: RecordValue) => item.id === result.assignment_decision?.selected_robot_id);
  if (!robot) return null;
  return <p className="mt-2 border-t border-slate-200 pt-2 text-[12px] leading-5 text-slate-600">处置完成后：{robot.name} 位于{routeLabel(robot.map_id)} · 电量 {robot.battery}% · {robot.status === "idle" ? "待命" : "状态已更新"}。</p>;
}

const legacyCandidateFacts: Record<string, { capabilities: string[]; surfaces: string[]; service_scope: string }> = {
  "robot-a": { capabilities: ["outdoor", "dry_debris", "road_sweeping"], surfaces: ["asphalt", "granite"], service_scope: "outdoor" },
  "robot-b": { capabilities: ["wet_cleaning", "strong_suction", "scrubbing"], surfaces: ["tile", "epoxy"], service_scope: "a_indoor" },
  "robot-c": { capabilities: ["dry_debris", "light_cleaning"], surfaces: ["tile", "carpet"], service_scope: "indoor" },
};

function candidateFacts(candidate: RecordValue, result: RecordValue) {
  const fallback = legacyCandidateFacts[String(candidate.robot_id)] ?? { capabilities: [], surfaces: [], service_scope: "" };
  const robot = Array.isArray(result.fleet_snapshot) ? result.fleet_snapshot.find((item: RecordValue) => item.id === candidate.robot_id) : undefined;
  return {
    battery: candidate.battery ?? robot?.battery,
    capabilities: candidate.capabilities ?? fallback.capabilities,
    surfaces: candidate.surfaces ?? fallback.surfaces,
    serviceScope: candidate.service_scope ?? fallback.service_scope,
    location: candidate.current_location ?? robot?.location ?? (candidate.map_id ? routeLabel(String(candidate.map_id)) : "未记录"),
  };
}

function CapabilitySummary({ decision, result }: { decision?: RecordValue; result: RecordValue }) {
  if (!decision) return <p className="mt-2 text-xs text-slate-500">尚无能力匹配记录。</p>;
  return <div className={card}><p className="font-medium text-slate-800">可用候选：{decision.candidate_count ?? "—"}</p>
    {(decision.candidates ?? []).map((candidate: RecordValue) => { const facts = candidateFacts(candidate, result); return <div key={candidate.robot_id} className="border-t border-slate-200 pt-1.5"><p className="font-medium">{candidate.robot_name}</p><p><strong>电量：</strong>{facts.battery ?? "—"}{typeof facts.battery === "number" ? "%" : ""}</p><p><strong>能力：</strong>{facts.capabilities.map(customerTerm).join(" / ") || "未记录"}</p><p><strong>地面材质：</strong>{facts.surfaces.map(customerTerm).join(" / ") || "未记录"}</p><p><strong>作业范围：</strong>{customerTerm(facts.serviceScope)}</p><p><strong>当前位置：</strong>{facts.location}</p><p>{candidate.eligible ? `满足硬约束 · 调度评分 ${candidate.final_score ?? "—"}` : (candidate.reject_reasons ?? []).map(constraintLabel).join("；") || "不满足硬约束"}</p></div>})}
    <p className="border-t border-slate-200 pt-1.5 font-medium">{decision.selected_robot_name ? `派发：${decision.selected_robot_name}` : decision.candidate_count === 0 ? "无机器人具备所需能力，转人工处置。" : "未生成机器人派单。"}</p>
  </div>;
}

export function EventStageEvidence({ event, entry, mode, onCompleteManual, onViewArchive }: { event: ActiveEvent; entry: TimelineEntry; mode: "live" | "history"; onCompleteManual?: () => void; onViewArchive?: (eventId: string) => void }) {
  const result = (event.liveResult ?? {}) as RecordValue;
  const manualVerificationRecorded = result.human_work_order?.status === "COMPLETED"
    && Array.isArray(result.transitions)
    && result.transitions.some((transition: RecordValue) => transition.state === "VERIFYING" && transition.detail?.manual_completion === true);
  if (result.mode === "DEMO_HISTORY") return <div className={card}><p>演示历史记录 · {entry.label}</p>{typeof entry.detail.verification_pass === "boolean" && <p>历史验收结果：{entry.detail.verification_pass ? "通过" : "未通过"}</p>}</div>;
  if (entry.pending || entry.loading) return <p className="mt-2 flex items-center gap-1.5 text-[12px] text-slate-500" aria-live="polite"><span>{String(entry.detail.loading_message ?? "正在执行本阶段，等待真实服务结果")}</span><span aria-label="加载中" className="inline-flex items-center gap-0.5"><i className="h-1 w-1 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.2s]" /><i className="h-1 w-1 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.1s]" /><i className="h-1 w-1 animate-bounce rounded-full bg-slate-400" /></span></p>;
  switch (entry.state) {
    case "DETECTED": return <p className="mt-1 text-[12px] text-slate-600">固定摄像头发现疑似清洁事件，正在确认现场情况。</p>;
    case "CANCELLED": return <p className="mt-2 text-[12px] text-slate-600">操作员已取消任务；此前处置记录保留，不再自动推进。</p>;
    case "EDGE_DETECTED": return <div className={card}><CameraEvidence event={event} detections /><p>现场目标识别完成，已进入 AI 研判。</p></div>;
    case "SINGLE_VIEW_REVIEW": return <div className={card}><p>AI 正在分析主摄像头画面。</p><p>当前画面{entry.detail.evidence_sufficient ? "信息充分" : "需要补充现场角度"}{entry.detail.ambiguity_type && entry.detail.ambiguity_type !== "none" ? ` · ${customerTerm(entry.detail.ambiguity_type)}` : ""}</p></div>;
    case "MULTI_VIEW": {
      const selected = result.multi_view?.selected_cameras ?? [];
      const ids = [...new Set<string>([event.scenario.cameraId, ...selected.map((s: string | RecordValue) => typeof s === "string" ? s : s.camera_id)])];
      return <div className={card}><p>AI 已补充 {Math.max(0, ids.length - 1)} 路现场视角，正在综合判断。</p><div className="grid gap-2 sm:grid-cols-2">{ids.map((id) => <div key={id}><CameraEvidence event={event} cameraId={id} /></div>)}</div><p>综合研判置信度：{percent(result.multi_view?.final_confidence ?? result.multi_view?.review?.decision_confidence)}</p></div>;
    }
    case "CLOUD_REVIEW": return <CloudSummary event={event} />;
    case "LOCATED": {
      const location = entry.detail;
      const building = location.building === "OUTDOOR" ? "园区室外" : `${location.building ?? "—"}栋${location.floor ?? ""}`;
      return <div className={card}><p><strong>事件位置：</strong>{building} · {customerTerm(location.zone)}</p><p><strong>SLAM坐标：</strong>X {location.x} / Y {location.y}</p><p><strong>所属地图：</strong>{routeLabel(String(location.map_id ?? ""))}</p></div>;
    }
    case "ASSIGNED": return <CapabilitySummary decision={entry.detail.assignment_decision} result={result} />;
    case "NAVIGATING": return <div className={card}><p>机器人正在前往现场。</p><p><strong>主要节点：</strong>{(entry.detail.navigation_plan?.display_path ?? entry.detail.navigation_plan?.node_path ?? []).map(routeLabel).join(" → ")}</p></div>;
    case "ARRIVED": return <p className="mt-2 text-[12px] text-slate-500">机器人已到达目标区域，准备开始处置。</p>;
    case "CLEANING_COMPLETED": return <p className="mt-2 text-[12px] text-slate-500">现场处置已完成，正在读取处置后画面。</p>;
    case "HUMAN_FALLBACK": return <><CapabilitySummary decision={entry.detail.assignment_decision} result={result} /><div className="mt-2 border border-amber-200 bg-amber-50 p-2 text-[12px] leading-5 text-amber-900"><p className="font-medium">人工处置工单已创建</p><p>能力引擎候选数为零。完成搬运后由固定摄像头证据进入同一验收流程。</p>{mode === "live" && event.backendState === "HUMAN_FALLBACK" && onCompleteManual && <button disabled={event.processing} onClick={onCompleteManual} className="mt-2 border border-amber-400 bg-white px-2 py-1 font-medium disabled:opacity-40">确认人工清理完成并验收</button>}{mode === "live" && event.backendState === "HUMAN_FALLBACK" && !onCompleteManual && <p className="mt-2">此事件由共享 Operations 任务管理；请在任务卡中确认人工完成并验收。</p>}{manualVerificationRecorded && <p>人工完成与固定摄像头验收已记录。</p>}{!manualVerificationRecorded && event.backendState === "CANCELLED" && <p>人工处置未完成，任务已取消。</p>}{!manualVerificationRecorded && event.backendState !== "HUMAN_FALLBACK" && event.backendState !== "CANCELLED" && <p>人工处置尚未完成或未通过验收。</p>}</div></>;
    case "VERIFYING": return <div className={card}><p>处置后固定摄像头画面</p><CameraEvidence event={event} after />{result.verification ? <p className="font-medium">AI 验收：{result.verification.verification_pass ? "通过" : "未通过"} · {percent(result.verification.confidence)}</p> : <p>尚无有效验收结果，请查看后续处理状态。</p>}</div>;
    case "CLOSED": return <div className="mt-2 border border-emerald-200 bg-emerald-50 p-2 text-[12px] leading-5 text-emerald-800"><p className="font-semibold">AI 验收通过，事件已闭环</p><p>执行方：{result.assignment_decision?.selected_robot_name ?? (entry.detail.manual_completion ? "人工处置" : "历史记录未注明")}</p><TerminalFleet result={result} />{mode === "live" && typeof result.event_id === "string" && onViewArchive && <button type="button" onClick={() => onViewArchive(result.event_id)} className="mt-2 border border-emerald-300 bg-white px-2 py-1 text-[12px] font-medium text-emerald-800">查看已保存档案</button>}</div>;
    case "HUMAN_REVIEW": return <>{entry.detail.cloud_review && <CloudSummary event={event} />}<div className="mt-2 border border-amber-200 bg-amber-50 p-2 text-[12px] leading-5 text-amber-900"><p className="font-semibold">自动流程停止，转人工复核</p><p>{customerTerm(entry.detail.reason ?? result.reason)}</p><p>此前阶段记录完整保留，不抹去已发生的派单或移动。</p><TerminalFleet result={result} /></div></>;
    default: return <p className="mt-1 text-[12px] text-slate-500">阶段已存档。</p>;
  }
}
