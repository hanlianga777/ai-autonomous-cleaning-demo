import { AlertCircle, Clock3, Route, ShieldCheck, Wrench } from "lucide-react";
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
      <filter id="heatmap-soften" x="-35%" y="-35%" width="170%" height="170%"><feGaussianBlur stdDeviation="3.2" /></filter>
      <radialGradient id="heatmap-red" cx="50%" cy="50%" r="50%"><stop offset="0%" stopColor="#ef4444" stopOpacity=".48" /><stop offset="34%" stopColor="#f97316" stopOpacity=".27" /><stop offset="68%" stopColor="#facc15" stopOpacity=".12" /><stop offset="100%" stopColor="#facc15" stopOpacity="0" /></radialGradient>
      <radialGradient id="heatmap-blue" cx="50%" cy="50%" r="50%"><stop offset="0%" stopColor="#2563eb" stopOpacity=".30" /><stop offset="42%" stopColor="#38bdf8" stopOpacity=".16" /><stop offset="100%" stopColor="#38bdf8" stopOpacity="0" /></radialGradient>
      <radialGradient id="heatmap-gold" cx="50%" cy="50%" r="50%"><stop offset="0%" stopColor="#f59e0b" stopOpacity=".36" /><stop offset="44%" stopColor="#fde047" stopOpacity=".18" /><stop offset="100%" stopColor="#fde047" stopOpacity="0" /></radialGradient>
    </defs>
    <g filter="url(#heatmap-soften)">
      <ellipse cx="39" cy="56" rx="18" ry="12" fill="url(#heatmap-red)" />
      <ellipse cx="30" cy="48" rx="14" ry="10" fill="url(#heatmap-blue)" />
      <ellipse cx="66" cy="58" rx="16" ry="11" fill="url(#heatmap-blue)" />
      <ellipse cx="87" cy="76" rx="18" ry="12" fill="url(#heatmap-red)" />
      <ellipse cx="29" cy="30" rx="15" ry="10" fill="url(#heatmap-gold)" />
    </g>
    <g fill="none" strokeLinecap="round">
      <path d="M22 57 C27 48 36 45 46 49 C53 52 55 60 48 66 C39 73 26 69 22 57Z" stroke="#fb923c" strokeOpacity=".25" strokeWidth=".45" strokeDasharray="1.6 1.8" />
      <path d="M76 76 C79 67 91 65 97 72 C100 78 95 86 86 86 C78 85 74 81 76 76Z" stroke="#f97316" strokeOpacity=".28" strokeWidth=".45" strokeDasharray="1.6 1.8" />
      <path d="M57 58 C60 50 71 48 77 54 C81 60 76 67 68 68 C61 68 56 64 57 58Z" stroke="#38bdf8" strokeOpacity=".24" strokeWidth=".4" strokeDasharray="1.4 1.7" />
    </g>
  </svg>;
}

function KpiCard({ label, value, icon: Icon }: { label: string; value: string; icon: typeof ShieldCheck }) {
  return <article className="border border-slate-200 bg-white px-4 py-3.5"><div className="flex items-start justify-between gap-2"><p className="text-[12px] font-medium text-slate-600">{label}</p><Icon size={15} strokeWidth={1.65} className="text-slate-400" /></div><p className="mt-2 text-[25px] font-semibold tracking-[-0.035em] text-slate-900">{value}</p></article>;
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
    {loading && !overview ? <div className="flex min-h-[480px] items-center justify-center text-sm text-slate-500">正在读取可追溯的运营统计…</div> : overview ? <>{section === "insights" ? <><section className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">{([ ["自主闭环率", "autonomous_closure_rate", "%", ShieldCheck], ["人工介入率", "human_intervention_rate", "%", Wrench], ["首次处置成功率", "first_pass_success_rate", "%", ShieldCheck], ["平均响应时间", "average_response_time_minutes", "分钟", Clock3], ["平均闭环时间", "average_closure_time_minutes", "分钟", Route] ] as const).map(([label, key, unit, icon]) => <KpiCard key={key} label={label} value={formatMetric(overview.kpis[key], unit)} icon={icon} />)}</section><AnalyticsAdviceCards /><section className="mt-4 border border-slate-200 bg-white"><div className="flex items-center justify-between border-b border-slate-200 px-4 py-3"><div><h2 className="text-sm font-semibold text-slate-800">园区历史事件空间热力图</h2><p className="mt-0.5 text-[11px] text-slate-400">固定展示过去 30 天的高发密度区域</p></div><span className="text-[11px] text-slate-400">低频 <i className="mx-1 inline-block h-2 w-14 rounded-full bg-gradient-to-r from-sky-300/30 via-amber-300/40 to-red-400/50 align-middle" /> 高频</span></div><MapCanvas imageSrc="/visual-assets/campus/campus-white-model.png" alt="园区空间事件热力图" className="h-[390px] bg-[#eef2f5]">{() => <><HistoricalHeatmapOverlay />{coordinateGroups.map(({ key, entries }, hotspotIndex) => { const count = entries.reduce((total, entry) => total + entry.point.count, 0); const x = entries.reduce((total, entry) => total + entry.position.x, 0) / entries.length; const y = entries.reduce((total, entry) => total + entry.position.y, 0) / entries.length; return <button key={key} type="button" onClick={() => navigateToHotspot(entries[0].index)} aria-label={`查看 ${mapLabel(key)} 热点事件，共 ${count} 条`} title={`${mapLabel(key)}：${count} 条事件`} className={`absolute z-20 -translate-x-1/2 -translate-y-1/2 border-0 bg-transparent outline-none focus:ring-2 focus:ring-slate-700 ${hotspotIndex < 3 ? "animate-pulse" : ""}`} style={{ left: `${x}%`, top: `${y}%`, width: "44px", height: "44px" }} />; })}</>}</MapCanvas></section></> : <section className="mt-4 grid gap-4 lg:grid-cols-2"><article className="border border-slate-200 bg-white p-4"><h2 className="text-sm font-semibold text-slate-800">事件时段分布</h2><AnalyticsChart option={timeOption} className="mt-2 h-[210px]" /></article><article className="border border-slate-200 bg-white p-4"><h2 className="text-sm font-semibold text-slate-800">清洁机器人利用率</h2><AnalyticsChart option={utilizationOption} className="mt-2 h-[210px]" /></article><article className="border border-slate-200 bg-white p-4"><h2 className="text-sm font-semibold text-slate-800">事件类型分布</h2><div className="mt-3 divide-y divide-slate-100">{overview.event_structure.map((item) => <div key={item.event_type} className="flex items-center justify-between py-2 text-xs"><span className="text-slate-600">{item.label || eventTypeLabel(item.event_type)}</span><span className="text-slate-700">{item.count}</span></div>)}</div></article><article className="border border-slate-200 bg-white p-4"><h2 className="text-sm font-semibold text-slate-800">处置与闭环效率</h2><AnalyticsChart option={efficiencyOption} className="mt-2 h-[210px]" /></article></section>}</> : <div className="min-h-[480px] border border-dashed border-slate-300 bg-white p-8 text-sm text-slate-500">尚未取得可验证的 Analytics API 响应。</div>}
  </section><AnalyticsAgentChat pageContext={analyticsAgentContext} /></div></main>;
}
