import { AlertCircle, Clock3, Route, ShieldCheck, Wrench } from "lucide-react";
import type { EChartsOption } from "echarts";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnalyticsChart } from "@/components/analytics/AnalyticsChart";
import { MapCanvas } from "./MapCanvas";
import { eventTypeLabel } from "./eventArchiveModel";
import { customerTerm } from "./eventViewModel";
import { projectAnalyticsHeatmapPoint } from "./spatialProjection";
import { AnalyticsAdviceCards, AnalyticsAgentChat } from "@/components/robot-operations/RobotOperationsPanel";
import {
  DEFAULT_ANALYTICS_FILTERS, analyticsQuery, formatMetric, hotspotDrilldownUrl,
  type AnalyticsOverview,
} from "./analyticsViewModel";

const palette = { slate: "#64748b", line: "#e2e8f0", blue: "#3d6f93", green: "#487866" };

const mapLabel = (id: string) => id === "OUTDOOR" ? "园区室外" : id.replace(/^([AB])_/, "$1栋");
function utcDisplay(value?: string) {
  if (!value) return "—";
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? new Date(parsed).toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" }) : value;
}

function KpiCard({ label, value, icon: Icon }: { label: string; value: string; icon: typeof ShieldCheck }) {
  return <article className="border border-slate-200 bg-white px-4 py-3.5"><div className="flex items-start justify-between gap-2"><p className="text-[12px] font-medium text-slate-600">{label}</p><Icon size={15} strokeWidth={1.65} className="text-slate-400" /></div><p className="mt-2 text-[25px] font-semibold tracking-[-0.035em] text-slate-900">{value}</p></article>;
}

/** P1-E aggregates plus the shared P1-F Agent's fixed Analytics panel. */
export function AnalyticsView() {
  // This customer page deliberately presents one fixed, truthful 30-day
  // operating view. Drill-down is explicit and keeps the selected fact.
  const filters = DEFAULT_ANALYTICS_FILTERS;
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCoordinate, setSelectedCoordinate] = useState<string | null>(null);
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
    projectedHeatmap.forEach((entry, index) => {
      const key = entry.point.map_id;
      grouped.set(key, [...(grouped.get(key) ?? []), entry]);
    });
    return [...grouped.entries()].map(([key, entries]) => ({ key, entries }));
  }, [projectedHeatmap]);
  const selectedHotspot = coordinateGroups.find((group) => group.key === selectedCoordinate) ?? null;
  const heatmapOption = useMemo<EChartsOption>(() => ({ animation: true, animationDuration: 700, grid: { left: 0, right: 0, top: 0, bottom: 0 }, xAxis: { min: 0, max: 100, show: false }, yAxis: { min: 0, max: 100, inverse: true, show: false }, visualMap: { show: false, min: 0, max: Math.max(1, ...projectedHeatmap.map(({ point }) => point.count)), dimension: 2, inRange: { color: ["#22d3ee", "#facc15", "#fb923c", "#ef4444"] } }, series: [{ type: "heatmap", silent: true, data: projectedHeatmap.map(({ point, position }) => [position.x, position.y, point.count]), pointSize: 58, blurSize: 42, itemStyle: { opacity: 0.68 } }] }), [projectedHeatmap]);
  const timeOption = useMemo<EChartsOption>(() => ({ animation: false, grid: { left: 30, right: 12, top: 14, bottom: 27 }, tooltip: { trigger: "axis" }, xAxis: { type: "category", data: overview?.time_distribution.map((bucket) => bucket.label) ?? [], axisLabel: { color: palette.slate, fontSize: 10 }, axisLine: { lineStyle: { color: palette.line } } }, yAxis: { type: "value", minInterval: 1, axisLabel: { color: palette.slate, fontSize: 10 }, splitLine: { lineStyle: { color: "#eef2f5" } } }, series: [{ type: "bar", data: overview?.time_distribution.map((bucket) => bucket.count) ?? [], barMaxWidth: 22, itemStyle: { color: palette.blue } }] }), [overview]);
  const utilizationOption = useMemo<EChartsOption>(() => ({ animation: false, grid: { left: 76, right: 30, top: 12, bottom: 8 }, xAxis: { type: "value", max: 100, axisLabel: { formatter: "{value}%", color: palette.slate, fontSize: 10 }, splitLine: { lineStyle: { color: "#eef2f5" } } }, yAxis: { type: "category", data: overview?.robot_utilization.map((robot) => robot.robot_name) ?? [], axisLabel: { color: palette.slate, fontSize: 10 }, axisLine: { show: false }, axisTick: { show: false } }, series: [{ type: "bar", data: overview?.robot_utilization.map((robot) => robot.utilization === null ? "-" : robot.utilization) ?? [], barWidth: 12, itemStyle: { color: palette.green } }] }), [overview]);
  const efficiencyOption = useMemo<EChartsOption>(() => ({ animation: false, grid: { left: 34, right: 16, top: 18, bottom: 32 }, tooltip: { trigger: "axis", valueFormatter: (value) => `${value}%` }, xAxis: { type: "category", data: ["自主闭环", "首次验收", "人工介入"], axisLabel: { color: palette.slate, fontSize: 10 }, axisLine: { lineStyle: { color: palette.line } } }, yAxis: { type: "value", min: 0, max: 100, axisLabel: { formatter: "{value}%", color: palette.slate, fontSize: 10 }, splitLine: { lineStyle: { color: "#eef2f5" } } }, series: [{ type: "bar", data: [overview?.kpis.autonomous_closure_rate, overview?.kpis.first_pass_success_rate, overview?.kpis.human_intervention_rate].map((value, index) => ({ value: value ?? 0, itemStyle: { color: index === 2 ? "#d97706" : palette.blue } })), barMaxWidth: 32 }] }), [overview]);

  const navigateToHotspot = (index: number) => {
    if (!overview) return;
    const selected = overview.heatmap[index];
    const url = hotspotDrilldownUrl(selected, filters, overview.period);
    window.history.pushState({}, "", url);
    window.dispatchEvent(new CustomEvent("cleanops:navigate", { detail: { url } }));
  };
  // This is a bounded projection of the backend Analytics response, not a
  // frontend-generated optimization claim or a full historical event dump.
  const analyticsAgentContext = {
    page: "analytics",
    filters: { ...filters },
    period: overview?.period ?? null,
    source: overview?.source ?? null,
    kpis: overview?.kpis ?? null,
    robot_utilization: (overview?.robot_utilization ?? []).slice(0, 4),
    charts: {
      time_distribution: (overview?.time_distribution ?? []).slice(0, 8),
      event_structure: (overview?.event_structure ?? []).slice(0, 5),
    },
    selected_hotspot: selectedHotspot ? {
      map_id: selectedHotspot.key,
      points: selectedHotspot.entries.slice(0, 8).map(({ point }) => ({
        label: point.label,
        map_id: point.map_id,
        event_type: point.event_type ?? null,
        time_slot: point.time_slot ?? null,
        count: point.count,
        average_closure_time_minutes: point.average_closure_time_minutes ?? null,
      })),
    } : null,
  };

  return <main className="min-h-[calc(100vh-54px)] bg-[#f6f7f8] text-slate-800" aria-label="运营分析">
    <div className="grid min-h-[calc(100vh-54px)] grid-cols-1 xl:grid-cols-[minmax(0,1fr)_360px]"><section className="min-w-0 px-5 py-5 lg:px-7">
      <section className="flex items-center gap-2" aria-label="运营分析页面"><button type="button" onClick={() => setSection("insights")} className={`border px-3 py-1.5 text-xs ${section === "insights" ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-600"}`}>运营洞察</button><button type="button" onClick={() => setSection("statistics")} className={`border px-3 py-1.5 text-xs ${section === "statistics" ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-600"}`}>数据统计</button><p className="ml-1 text-[12px] text-slate-500">近30天园区运营情况</p></section>
      {error && <div role="alert" className="mt-3 flex items-center gap-2 border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800"><AlertCircle size={14} />{error}</div>}
      {loading && !overview ? <div className="flex min-h-[480px] items-center justify-center text-sm text-slate-500">正在读取可追溯的运营统计…</div> : overview ? <>{section === "insights" ? <><section className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">{([ ["自主闭环率", "autonomous_closure_rate", "%", ShieldCheck], ["人工介入率", "human_intervention_rate", "%", Wrench], ["首次处置成功率", "first_pass_success_rate", "%", ShieldCheck], ["平均响应时间", "average_response_time_minutes", "分钟", Clock3], ["平均闭环时间", "average_closure_time_minutes", "分钟", Route] ] as const).map(([label, key, unit, icon]) => <KpiCard key={key} label={label} value={formatMetric(overview.kpis[key], unit)} icon={icon} />)}</section>
        <AnalyticsAdviceCards />
        <section className="mt-4 border border-slate-200 bg-white"><div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-200 px-4 py-3"><div><h2 className="text-sm font-semibold text-slate-800">园区历史事件空间热力图</h2></div><p className="text-[12px] text-slate-500">{utcDisplay(overview.period.start)}–{utcDisplay(overview.period.end ?? overview.period.ending)} · 选择楼层热点查看事件档案</p></div><MapCanvas imageSrc="/visual-assets/campus/campus-white-model.png" alt="园区空间事件热力图" className="h-[390px] bg-[#eef2f5]">{() => <><AnalyticsChart option={heatmapOption} className="absolute inset-0 h-full w-full" />{coordinateGroups.map(({ key, entries }, hotspotIndex) => { const count = entries.reduce((total, entry) => total + entry.point.count, 0); const x = entries.reduce((total, entry) => total + entry.position.x, 0) / entries.length; const y = entries.reduce((total, entry) => total + entry.position.y, 0) / entries.length; return <button key={key} type="button" onClick={() => setSelectedCoordinate(key)} aria-label={`选择 ${mapLabel(key)} 楼层热点，共 ${count} 条事件`} title={`${mapLabel(key)}：${count} 条事件`} className={`absolute z-20 -translate-x-1/2 -translate-y-1/2 border-0 bg-transparent outline-none focus:ring-2 focus:ring-slate-700 ${hotspotIndex < 3 ? "animate-pulse" : ""}`} style={{ left: `${x}%`, top: `${y}%`, width: "44px", height: "44px" }} />; })}</>}</MapCanvas><div className="border-t border-slate-100 px-4 py-3"><div className="flex flex-wrap gap-1.5" aria-label="可访问楼层热点列表">{coordinateGroups.map(({ key, entries }) => <button key={key} type="button" onClick={() => setSelectedCoordinate(key)} className={`border px-2 py-1 text-[12px] ${selectedCoordinate === key ? "border-slate-700 bg-slate-100 text-slate-800" : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"}`}>{mapLabel(key)} · {entries.reduce((total, entry) => total + entry.point.count, 0)} 条</button>)}</div>{selectedHotspot ? <div className="mt-3"><div className="flex flex-wrap items-center justify-between gap-2"><div><p className="text-xs font-semibold text-slate-800">{mapLabel(selectedHotspot.key)} 楼层热点</p><p className="mt-1 text-[12px] text-slate-500">共 {selectedHotspot.entries.reduce((total, entry) => total + entry.point.count, 0)} 条；按楼层聚合展示，避免坐标重叠。</p></div><button type="button" onClick={() => setSelectedCoordinate(null)} className="text-[12px] text-slate-500 underline underline-offset-2">收起</button></div><div className="mt-2 flex flex-wrap gap-2">{selectedHotspot.entries.map((entry) => <article key={`${entry.point.zone_id}:${entry.point.map_id}:${entry.point.x}:${entry.point.y}:${entry.point.event_type ?? "all"}`} className="border border-slate-200 bg-slate-50 px-2.5 py-2 text-[12px] text-slate-600"><p>{customerTerm(entry.point.label)} · {eventTypeLabel(entry.point.event_type ?? "unknown")} · {entry.point.count} 条</p><p className="mt-1">时段：{entry.point.time_slot && entry.point.time_slot !== "all" ? entry.point.time_slot : filters.timeSlot || "全天"} · 平均闭环：{formatMetric(entry.point.average_closure_time_minutes, "分钟")}</p><button type="button" onClick={() => navigateToHotspot(entry.index)} className="mt-1.5 border border-slate-300 bg-white px-2 py-1 text-[12px] text-slate-700 hover:bg-slate-100">跳转事件中心</button></article>)}</div></div> : <p className="mt-2 text-[12px] text-slate-500">点击地图或楼层入口，查看区域、总数、类型、时段和平均闭环后再跳转事件中心。</p>}</div></section></> : <section className="mt-4 grid gap-4 lg:grid-cols-2"><article className="border border-slate-200 bg-white p-4"><h2 className="text-sm font-semibold text-slate-800">事件时段分布</h2><AnalyticsChart option={timeOption} className="mt-2 h-[210px]" /></article><article className="border border-slate-200 bg-white p-4"><h2 className="text-sm font-semibold text-slate-800">清洁机器人利用率</h2><AnalyticsChart option={utilizationOption} className="mt-2 h-[210px]" /></article><article className="border border-slate-200 bg-white p-4"><h2 className="text-sm font-semibold text-slate-800">事件类型分布</h2><div className="mt-3 divide-y divide-slate-100">{overview.event_structure.map((item) => <div key={item.event_type} className="flex items-center justify-between py-2 text-xs"><span className="text-slate-600">{item.label || eventTypeLabel(item.event_type)}</span><span className="text-slate-700">{item.count}</span></div>)}</div></article><article className="border border-slate-200 bg-white p-4"><h2 className="text-sm font-semibold text-slate-800">处置与闭环效率</h2><AnalyticsChart option={efficiencyOption} className="mt-2 h-[210px]" /></article></section>}
      </> : <div className="min-h-[480px] border border-dashed border-slate-300 bg-white p-8 text-sm text-slate-500">尚未取得可验证的 Analytics API 响应。</div>}</section><AnalyticsAgentChat pageContext={analyticsAgentContext} /></div>
  </main>;
}
