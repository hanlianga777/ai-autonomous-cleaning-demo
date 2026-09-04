import { AlertCircle, ArrowRight, BrainCircuit, Clock3, Route, ShieldCheck, Sparkles, Wrench } from "lucide-react";
import type { EChartsOption } from "echarts";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnalyticsChart } from "@/components/analytics/AnalyticsChart";
import { MapCanvas } from "./MapCanvas";
import { eventTypeLabel } from "./eventArchiveModel";
import { projectAnalyticsHeatmapPoint } from "./spatialProjection";
import { AnalyticsAdviceCards, AnalyticsAgentChat } from "@/components/robot-operations/RobotOperationsPanel";
import { DEFAULT_ANALYTICS_FILTERS, analyticsQuery, formatMetric, hotspotDrilldownUrl, type AnalyticsOverview } from "./analyticsViewModel";

const palette = { slate: "#64748b", line: "#e2e8f0", blue: "#3d6f93", green: "#487866" };
const mapLabel = (id: string) => id === "OUTDOOR" ? "园区室外" : id.replace(/^([AB])_/, "$1栋");

/** A fixed, 30-day historical density field for the interview demo.  It is
 * intentionally independent from the live work-order stream. */
function HistoricalHeatmapOverlay() {
  return <svg className="pointer-events-none absolute inset-0 z-10 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="过去 30 天园区事件密度分布">
    <defs>
      <filter id="heatmap-soften" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2.2" /></filter>
      <radialGradient id="heatmap-red" cx="48%" cy="52%" r="58%"><stop offset="0%" stopColor="#ef4444" stopOpacity=".66" /><stop offset="28%" stopColor="#f97316" stopOpacity=".48" /><stop offset="57%" stopColor="#facc15" stopOpacity=".24" /><stop offset="100%" stopColor="#facc15" stopOpacity="0" /></radialGradient>
      <radialGradient id="heatmap-blue" cx="54%" cy="48%" r="58%"><stop offset="0%" stopColor="#2563eb" stopOpacity=".45" /><stop offset="42%" stopColor="#38bdf8" stopOpacity=".27" /><stop offset="100%" stopColor="#38bdf8" stopOpacity="0" /></radialGradient>
      <radialGradient id="heatmap-gold" cx="45%" cy="48%" r="58%"><stop offset="0%" stopColor="#f97316" stopOpacity=".58" /><stop offset="36%" stopColor="#facc15" stopOpacity=".38" /><stop offset="100%" stopColor="#fde047" stopOpacity="0" /></radialGradient>
    </defs>
    <g filter="url(#heatmap-soften)">
      <path d="M19 58 C20 50 27 45 35 46 C41 43 50 48 52 55 C55 62 49 69 42 69 C35 73 24 68 19 58Z" fill="url(#heatmap-red)" />
      <path d="M17 50 C20 43 28 41 35 45 C39 50 36 58 30 60 C23 61 17 57 17 50Z" fill="url(#heatmap-blue)" />
      <path d="M53 59 C55 51 64 48 70 51 C77 49 82 56 78 62 C75 68 66 69 61 66 C57 65 54 63 53 59Z" fill="url(#heatmap-blue)" />
      <path d="M76 75 C78 68 86 65 92 68 C98 68 101 75 98 80 C95 87 84 88 78 83 C75 81 74 78 76 75Z" fill="url(#heatmap-red)" />
      <path d="M19 31 C20 23 28 20 34 24 C41 23 45 29 42 35 C38 41 30 40 26 37 C22 37 18 35 19 31Z" fill="url(#heatmap-gold)" />
      <path d="M33 55 C36 50 42 51 45 55 C47 59 44 63 39 63 C34 62 31 59 33 55Z" fill="url(#heatmap-gold)" />
      <path d="M84 74 C87 70 93 72 95 76 C96 80 92 83 88 82 C84 81 82 78 84 74Z" fill="url(#heatmap-gold)" />
    </g>
  </svg>;
}

function KpiCard({ label, value, icon: Icon }: { label: string; value: string; icon: typeof ShieldCheck }) {
  return <article className="border border-slate-200 bg-white px-4 py-3.5"><div className="flex items-start justify-between gap-2"><p className="text-[12px] font-medium text-slate-600">{label}</p><Icon size={15} strokeWidth={1.65} className="text-slate-400" /></div><p className="mt-2 text-[25px] font-semibold tracking-[-0.035em] text-slate-900">{value}</p></article>;
}

function PredictiveDeployment({ plan }: { plan: AnalyticsOverview["prediction_plan"] }) {
  return <section className="mt-4 overflow-hidden border border-indigo-100 bg-white"><div className="flex items-start justify-between gap-3 border-b border-indigo-100 bg-gradient-to-r from-indigo-50/70 via-white to-sky-50/60 px-4 py-3"><div className="flex gap-2.5"><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-indigo-700"><BrainCircuit size={16} /></span><div><h2 className="text-sm font-semibold text-slate-800">AI 预测与预部署</h2><p className="mt-0.5 text-[11px] text-slate-500">以历史热点与端侧感知趋势，提前缩短响应距离。</p></div></div><span className="shrink-0 rounded-full border border-indigo-100 bg-white/80 px-2 py-1 text-[10px] font-medium text-indigo-700">固定演示预案</span></div><div className="px-4 py-3"><div className="mb-3 flex items-center justify-between text-[10px] font-medium uppercase tracking-[0.12em] text-indigo-600"><span>输入信号</span><ArrowRight size={13} /><span>风险预判</span><ArrowRight size={13} /><span>建议待命</span></div><div className="grid gap-2 lg:grid-cols-3">{plan.prepositioning.map((item) => <article key={item.signal} className="border border-slate-200 bg-slate-50/60 p-3"><div className="flex items-start justify-between gap-2"><p className="text-[12px] font-semibold text-slate-800">{item.signal}</p><span className="shrink-0 text-[10px] text-slate-400">{item.time}</span></div><p className="mt-1 text-[11px] text-slate-500">{item.risk}</p><div className="mt-2 border-t border-slate-200 pt-2 text-[11px] leading-5 text-slate-600"><p><span className="text-slate-400">建议待命</span> · {item.location}</p><p><span className="text-slate-400">执行单元</span> · {item.robot_name}</p><p className="mt-1 font-medium text-indigo-700">{item.action}</p></div></article>)}</div><div className="mt-3 border-t border-slate-100 pt-3"><div className="mb-2 flex items-center gap-1.5 text-[12px] font-semibold text-slate-700"><Sparkles size={14} className="text-indigo-600" />物体形态—清洁策略</div><div className="grid divide-y divide-slate-100 border border-slate-100 sm:grid-cols-3 sm:divide-x sm:divide-y-0">{plan.cleaning_playbooks.map((item) => <div key={item.object} className="p-2.5 text-[11px] leading-5"><p className="font-medium text-slate-700">{item.object}</p><p className="text-indigo-700">{item.action}</p><p className="text-slate-400">{item.guardrail}</p></div>)}</div></div><p className="mt-3 text-[10px] leading-4 text-slate-400">{plan.disclaimer}</p></div></section>;
}

export function AnalyticsView() {
  const filters = DEFAULT_ANALYTICS_FILTERS;
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [section, setSection] = useState<"insights" | "statistics">("insights");
  const requestId = useRef(0);
  const load = useCallback(async (signal?: AbortSignal) => {
    const currentRequest = ++requestId.current;
    setLoading(true); setError(null);
    try {
      const response = await fetch(`/api/analytics/overview?${analyticsQuery(filters).toString()}`, { signal });
      if (!response.ok) throw new Error(`analytics ${response.status}`);
      const payload = await response.json() as AnalyticsOverview;
      if (!signal?.aborted && currentRequest === requestId.current) setOverview(payload);
    } catch (reason) {
      if (!signal?.aborted && currentRequest === requestId.current) { setOverview(null); setError(reason instanceof Error ? `运营分析暂不可用（${reason.message}）` : "运营分析暂不可用"); }
    } finally { if (!signal?.aborted && currentRequest === requestId.current) setLoading(false); }
  }, [filters]);
  useEffect(() => { const controller = new AbortController(); void load(controller.signal); return () => controller.abort(); }, [load]);

  const projectedHeatmap = useMemo(() => (overview?.heatmap ?? []).map((point, index) => ({ point, index, position: projectAnalyticsHeatmapPoint(point) })), [overview]);
  const coordinateGroups = useMemo(() => {
    const grouped = new Map<string, typeof projectedHeatmap>();
    projectedHeatmap.forEach((entry) => grouped.set(entry.point.map_id, [...(grouped.get(entry.point.map_id) ?? []), entry]));
    return [...grouped.entries()].map(([key, entries]) => ({ key, entries }));
  }, [projectedHeatmap]);
  const timeOption = useMemo<EChartsOption>(() => ({ animation: false, grid: { left: 30, right: 12, top: 14, bottom: 27 }, tooltip: { trigger: "axis" }, xAxis: { type: "category", data: overview?.time_distribution.map((bucket) => bucket.label) ?? [], axisLabel: { color: palette.slate, fontSize: 10 }, axisLine: { lineStyle: { color: palette.line } } }, yAxis: { type: "value", minInterval: 1, axisLabel: { color: palette.slate, fontSize: 10 }, splitLine: { lineStyle: { color: "#eef2f5" } } }, series: [{ type: "bar", data: overview?.time_distribution.map((bucket) => bucket.count) ?? [], barMaxWidth: 22, itemStyle: { color: palette.blue } }] }), [overview]);
  const utilizationOption = useMemo<EChartsOption>(() => ({ animation: false, grid: { left: 76, right: 30, top: 12, bottom: 8 }, xAxis: { type: "value", max: 100, axisLabel: { formatter: "{value}%", color: palette.slate, fontSize: 10 }, splitLine: { lineStyle: { color: "#eef2f5" } } }, yAxis: { type: "category", data: overview?.robot_utilization.map((robot) => robot.robot_name) ?? [], axisLabel: { color: palette.slate, fontSize: 10 }, axisLine: { show: false }, axisTick: { show: false } }, series: [{ type: "bar", data: overview?.robot_utilization.map((robot) => robot.utilization === null ? "-" : robot.utilization) ?? [], barWidth: 12, itemStyle: { color: palette.green } }] }), [overview]);
  const efficiencyOption = useMemo<EChartsOption>(() => ({ animation: false, grid: { left: 34, right: 16, top: 18, bottom: 32 }, tooltip: { trigger: "axis", valueFormatter: (value) => `${value}%` }, xAxis: { type: "category", data: ["自主闭环", "首次验收", "人工介入"], axisLabel: { color: palette.slate, fontSize: 10 }, axisLine: { lineStyle: { color: palette.line } } }, yAxis: { type: "value", min: 0, max: 100, axisLabel: { formatter: "{value}%", color: palette.slate, fontSize: 10 }, splitLine: { lineStyle: { color: "#eef2f5" } } }, series: [{ type: "bar", data: [overview?.kpis.autonomous_closure_rate, overview?.kpis.first_pass_success_rate, overview?.kpis.human_intervention_rate].map((value, index) => ({ value: value ?? 0, itemStyle: { color: index === 2 ? "#d97706" : palette.blue } })), barMaxWidth: 32 }] }), [overview]);
  const navigateToHotspot = (index: number) => { if (!overview) return; const url = hotspotDrilldownUrl(overview.heatmap[index], filters, overview.period); window.history.pushState({}, "", url); window.dispatchEvent(new CustomEvent("cleanops:navigate", { detail: { url } })); };
  const analyticsAgentContext = { page: "analytics", filters: { ...filters }, period: overview?.period ?? null, source: overview?.source ?? null, kpis: overview?.kpis ?? null, robot_utilization: (overview?.robot_utilization ?? []).slice(0, 4), charts: { time_distribution: (overview?.time_distribution ?? []).slice(0, 8), event_structure: (overview?.event_structure ?? []).slice(0, 5) } };

  return <main className="min-h-[calc(100vh-54px)] bg-[#f6f7f8] text-slate-800" aria-label="运营分析"><div className="grid min-h-[calc(100vh-54px)] grid-cols-1 xl:grid-cols-[minmax(0,1fr)_360px]"><section className="min-w-0 px-5 py-5 lg:px-7">
    <section className="flex items-center gap-2" aria-label="运营分析页面"><button type="button" onClick={() => setSection("insights")} className={`border px-3 py-1.5 text-xs ${section === "insights" ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-600"}`}>运营洞察</button><button type="button" onClick={() => setSection("statistics")} className={`border px-3 py-1.5 text-xs ${section === "statistics" ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-600"}`}>数据统计</button></section>
    {error && <div role="alert" className="mt-3 flex items-center gap-2 border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800"><AlertCircle size={14} />{error}</div>}
    {loading && !overview ? <div className="flex min-h-[480px] items-center justify-center text-sm text-slate-500">正在读取可追溯的运营统计…</div> : overview ? <>{section === "insights" ? <><section className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">{([ ["自主闭环率", "autonomous_closure_rate", "%", ShieldCheck], ["人工介入率", "human_intervention_rate", "%", Wrench], ["首次处置成功率", "first_pass_success_rate", "%", ShieldCheck], ["平均响应时间", "average_response_time_minutes", "分钟", Clock3], ["平均闭环时间", "average_closure_time_minutes", "分钟", Route] ] as const).map(([label, key, unit, icon]) => <KpiCard key={key} label={label} value={formatMetric(overview.kpis[key], unit)} icon={icon} />)}</section><PredictiveDeployment plan={overview.prediction_plan} /><AnalyticsAdviceCards /><section className="mt-4 border border-slate-200 bg-white"><div className="flex items-center justify-between border-b border-slate-200 px-4 py-3"><div><h2 className="text-sm font-semibold text-slate-800">园区历史事件空间热力图</h2><p className="mt-0.5 text-[11px] text-slate-400">固定展示过去 30 天的高发密度区域</p></div><span className="text-[11px] text-slate-400">低频 <i className="mx-1 inline-block h-2 w-14 rounded-full bg-gradient-to-r from-sky-300/30 via-amber-300/40 to-red-400/50 align-middle" /> 高频</span></div><MapCanvas imageSrc="/visual-assets/campus/campus-white-model.png" alt="园区空间事件热力图" className="h-[390px] bg-[#eef2f5]">{() => <><HistoricalHeatmapOverlay />{coordinateGroups.map(({ key, entries }, hotspotIndex) => { const count = entries.reduce((total, entry) => total + entry.point.count, 0); const x = entries.reduce((total, entry) => total + entry.position.x, 0) / entries.length; const y = entries.reduce((total, entry) => total + entry.position.y, 0) / entries.length; return <button key={key} type="button" onClick={() => navigateToHotspot(entries[0].index)} aria-label={`查看 ${mapLabel(key)} 热点事件，共 ${count} 条`} title={`${mapLabel(key)}：${count} 条事件`} className={`absolute z-20 -translate-x-1/2 -translate-y-1/2 border-0 bg-transparent outline-none focus:ring-2 focus:ring-slate-700 ${hotspotIndex < 3 ? "animate-pulse" : ""}`} style={{ left: `${x}%`, top: `${y}%`, width: "44px", height: "44px" }} />; })}</>}</MapCanvas></section></> : <section className="mt-4 grid gap-4 lg:grid-cols-2"><article className="border border-slate-200 bg-white p-4"><h2 className="text-sm font-semibold text-slate-800">事件时段分布</h2><AnalyticsChart option={timeOption} className="mt-2 h-[210px]" /></article><article className="border border-slate-200 bg-white p-4"><h2 className="text-sm font-semibold text-slate-800">清洁机器人利用率</h2><AnalyticsChart option={utilizationOption} className="mt-2 h-[210px]" /></article><article className="border border-slate-200 bg-white p-4"><h2 className="text-sm font-semibold text-slate-800">事件类型分布</h2><div className="mt-3 divide-y divide-slate-100">{overview.event_structure.map((item) => <div key={item.event_type} className="flex items-center justify-between py-2 text-xs"><span className="text-slate-600">{item.label || eventTypeLabel(item.event_type)}</span><span className="text-slate-700">{item.count}</span></div>)}</div></article><article className="border border-slate-200 bg-white p-4"><h2 className="text-sm font-semibold text-slate-800">处置与闭环效率</h2><AnalyticsChart option={efficiencyOption} className="mt-2 h-[210px]" /></article></section>}</> : <div className="min-h-[480px] border border-dashed border-slate-300 bg-white p-8 text-sm text-slate-500">尚未取得可验证的 Analytics API 响应。</div>}
  </section><AnalyticsAgentChat pageContext={analyticsAgentContext} /></div></main>;
}
