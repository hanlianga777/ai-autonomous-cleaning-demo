import { AlertCircle, Clock3, RefreshCw, Route, ShieldCheck, Wrench } from "lucide-react";
import type { EChartsOption } from "echarts";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnalyticsChart } from "@/components/analytics/AnalyticsChart";
import { MapCanvas } from "./MapCanvas";
import { eventTypeLabel } from "./eventArchiveModel";
import { customerTerm } from "./eventViewModel";
import { projectMapCoordinate } from "./spatialProjection";
import { AnalyticsAdviceAndChat } from "@/components/robot-operations/RobotOperationsPanel";
import {
  DEFAULT_ANALYTICS_FILTERS, TIME_SLOTS, analyticsQuery, formatMetric, heatmapRadius, hotspotDrilldownUrl, metricEvidence,
  type AnalyticsFilters, type AnalyticsOverview,
} from "./analyticsViewModel";

const EVENT_TYPES = ["", "small_litter", "liquid", "can", "large_object"];
const palette = { slate: "#64748b", line: "#e2e8f0", blue: "#3d6f93", green: "#487866" };

const mapLabel = (id: string) => id === "OUTDOOR" ? "园区室外" : id.replace(/^([AB])_/, "$1栋 ");
function utcDisplay(value?: string) {
  if (!value) return "—";
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? new Date(parsed).toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" }) : value;
}

function KpiCard({ label, value, sample, definition, icon: Icon }: { label: string; value: string; sample: string; definition: string; icon: typeof ShieldCheck }) {
  return <article className="border border-slate-200 bg-white px-4 py-3.5"><div className="flex items-start justify-between gap-2"><p className="text-[11px] font-medium text-slate-600">{label}</p><Icon size={15} strokeWidth={1.65} className="text-slate-400" /></div><p className="mt-2 text-[25px] font-semibold tracking-[-0.035em] text-slate-900">{value}</p><p title={definition} className="mt-1 text-[10px] leading-4 text-slate-500">样本：{sample}</p><details className="mt-1 text-[10px] leading-4 text-slate-500"><summary className="cursor-help text-slate-400">统计口径</summary><p className="mt-1">{definition}</p></details></article>;
}

/** P1-E aggregates plus the shared P1-F Agent's fixed Analytics panel. */
export function AnalyticsView() {
  const [filters, setFilters] = useState<AnalyticsFilters>(DEFAULT_ANALYTICS_FILTERS);
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCoordinate, setSelectedCoordinate] = useState<string | null>(null);
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
  const updateFilters = (patch: Partial<AnalyticsFilters>) => setFilters((previous) => ({ ...previous, ...patch }));
  const projectedHeatmap = useMemo(() => (overview?.heatmap ?? []).map((point, index) => ({ point, index, position: projectMapCoordinate(point.map_id, point.x, point.y) })), [overview]);
  const coordinateGroups = useMemo(() => {
    const grouped = new Map<string, typeof projectedHeatmap>();
    projectedHeatmap.forEach((entry, index) => {
      const key = entry.point.map_id;
      grouped.set(key, [...(grouped.get(key) ?? []), entry]);
    });
    return [...grouped.entries()].map(([key, entries]) => ({ key, entries }));
  }, [projectedHeatmap]);
  const selectedHotspot = coordinateGroups.find((group) => group.key === selectedCoordinate) ?? null;
  const heatmapOption = useMemo<EChartsOption>(() => ({ animation: false, grid: { left: 0, right: 0, top: 0, bottom: 0 }, xAxis: { min: 0, max: 100, show: false }, yAxis: { min: 0, max: 100, inverse: true, show: false }, visualMap: { show: false, min: 0, max: Math.max(1, ...projectedHeatmap.map(({ point }) => point.count)), dimension: 2, inRange: { color: ["#d6e4eb", "#80a2b8", "#c48845", "#b56f2e"] } }, series: [{ type: "scatter", silent: true, data: projectedHeatmap.map(({ point, position }) => ({ name: point.label, value: [position.x, position.y, point.count] })), symbolSize: (value: number[]) => heatmapRadius(value[2]), itemStyle: { opacity: 0.62, shadowBlur: 8, shadowColor: "rgba(55, 85, 105, .18)" } }] }), [projectedHeatmap]);
  const timeOption = useMemo<EChartsOption>(() => ({ animation: false, grid: { left: 30, right: 12, top: 14, bottom: 27 }, tooltip: { trigger: "axis" }, xAxis: { type: "category", data: overview?.time_distribution.map((bucket) => bucket.label) ?? [], axisLabel: { color: palette.slate, fontSize: 10 }, axisLine: { lineStyle: { color: palette.line } } }, yAxis: { type: "value", minInterval: 1, axisLabel: { color: palette.slate, fontSize: 10 }, splitLine: { lineStyle: { color: "#eef2f5" } } }, series: [{ type: "bar", data: overview?.time_distribution.map((bucket) => bucket.count) ?? [], barMaxWidth: 22, itemStyle: { color: palette.blue } }] }), [overview]);
  const utilizationOption = useMemo<EChartsOption>(() => ({ animation: false, grid: { left: 76, right: 30, top: 12, bottom: 8 }, xAxis: { type: "value", max: 100, axisLabel: { formatter: "{value}%", color: palette.slate, fontSize: 10 }, splitLine: { lineStyle: { color: "#eef2f5" } } }, yAxis: { type: "category", data: overview?.robot_utilization.map((robot) => robot.robot_name) ?? [], axisLabel: { color: palette.slate, fontSize: 10 }, axisLine: { show: false }, axisTick: { show: false } }, series: [{ type: "bar", data: overview?.robot_utilization.map((robot) => robot.utilization === null ? "-" : robot.utilization) ?? [], barWidth: 12, itemStyle: { color: palette.green } }] }), [overview]);

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

  return <main className="min-h-[calc(100vh-54px)] bg-[#f6f7f8] text-slate-800" aria-label="AI 自主清洁运营分析中心">
    <div className="grid min-h-[calc(100vh-54px)] grid-cols-1 xl:grid-cols-[minmax(0,1fr)_286px]"><section className="min-w-0 px-5 py-5 lg:px-7"><header className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-200 pb-4"><div><p className="text-[10px] font-semibold tracking-[0.16em] text-slate-400">AI AUTONOMOUS CLEANING OPERATIONS ANALYSIS CENTER</p><h1 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">AI 自主清洁运营分析中心</h1><p className="mt-1 text-xs text-slate-500">{filters.since || filters.until ? "自定义时间范围" : "近30天"} · 演示历史数据 + Runtime 增量，不代表客户生产运营数据。</p></div><button type="button" onClick={() => void load()} className="flex items-center gap-1.5 border border-slate-300 bg-white px-3 py-2 text-xs text-slate-700 hover:bg-slate-50"><RefreshCw size={14} />刷新统计</button></header>
      <section className="mt-3 flex flex-wrap items-center gap-2 border border-slate-200 bg-white px-3 py-2" aria-label="运营分析筛选"><label className="text-[11px] text-slate-500">事件类型 <select aria-label="运营分析事件类型" value={filters.eventType} onChange={(event) => updateFilters({ eventType: event.target.value })} className="ml-1 border border-slate-200 px-2 py-1 text-[11px] text-slate-700"><option value="">全部</option>{EVENT_TYPES.slice(1).map((type) => <option key={type} value={type}>{eventTypeLabel(type)}</option>)}</select></label><label className="text-[11px] text-slate-500">时段 <select aria-label="运营分析时段" value={filters.timeSlot} onChange={(event) => updateFilters({ timeSlot: event.target.value })} className="ml-1 border border-slate-200 px-2 py-1 text-[11px] text-slate-700">{TIME_SLOTS.map((slot) => <option key={slot || "all"} value={slot}>{slot || "全天"}</option>)}</select></label><label className="text-[11px] text-slate-500">起始 <input type="date" aria-label="运营分析起始日期" value={filters.since} onChange={(event) => updateFilters({ since: event.target.value })} className="ml-1 border border-slate-200 px-1.5 py-1 text-[11px] text-slate-700" /></label><label className="text-[11px] text-slate-500">结束 <input type="date" aria-label="运营分析结束日期" value={filters.until} onChange={(event) => updateFilters({ until: event.target.value })} className="ml-1 border border-slate-200 px-1.5 py-1 text-[11px] text-slate-700" /></label></section>
      {error && <div role="alert" className="mt-3 flex items-center gap-2 border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800"><AlertCircle size={14} />{error}</div>}
      {loading && !overview ? <div className="flex min-h-[480px] items-center justify-center text-sm text-slate-500">正在读取可追溯的运营统计…</div> : overview ? <><section className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">{([ ["自主闭环率", "autonomous_closure_rate", "%", ShieldCheck], ["人工介入率", "human_intervention_rate", "%", Wrench], ["首次处置成功率", "first_pass_success_rate", "%", ShieldCheck], ["平均响应时间", "average_response_time_minutes", "分钟", Clock3], ["平均闭环时间", "average_closure_time_minutes", "分钟", Route] ] as const).map(([label, key, unit, icon]) => { const evidence = metricEvidence(overview, key); return <KpiCard key={key} label={label} value={formatMetric(overview.kpis[key], unit)} sample={evidence.sample} definition={evidence.definition} icon={icon} />; })}</section>
        <section className="mt-4 border border-slate-200 bg-white"><div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-200 px-4 py-3"><div><p className="text-[10px] font-semibold tracking-[0.13em] text-slate-400">CAMPUS SPATIAL EVENT HEATMAP</p><h2 className="mt-1 text-sm font-semibold text-slate-800">园区历史事件空间热力图</h2></div><p className="text-[11px] text-slate-500">{utcDisplay(overview.period.start)}–{utcDisplay(overview.period.end ?? overview.period.ending)} · 选择楼层热点查看事件档案</p></div><MapCanvas imageSrc="/visual-assets/campus/campus-white-model.png" alt="园区空间事件热力图" className="h-[390px] bg-[#eef2f5]">{() => <><AnalyticsChart option={heatmapOption} className="absolute inset-0 h-full w-full" />{coordinateGroups.map(({ key, entries }) => { const count = entries.reduce((total, entry) => total + entry.point.count, 0); const x = entries.reduce((total, entry) => total + entry.position.x, 0) / entries.length; const y = entries.reduce((total, entry) => total + entry.position.y, 0) / entries.length; return <button key={key} type="button" onClick={() => setSelectedCoordinate(key)} aria-label={`选择 ${mapLabel(key)} 楼层热点，共 ${count} 条事件`} className="absolute z-20 -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/90 bg-transparent outline-none focus:ring-2 focus:ring-slate-700" style={{ left: `${x}%`, top: `${y}%`, width: heatmapRadius(count), height: heatmapRadius(count) }} />; })}</>}</MapCanvas><div className="border-t border-slate-100 px-4 py-3"><div className="flex flex-wrap gap-1.5" aria-label="可访问楼层热点列表">{coordinateGroups.map(({ key, entries }) => <button key={key} type="button" onClick={() => setSelectedCoordinate(key)} className={`border px-2 py-1 text-[10px] ${selectedCoordinate === key ? "border-slate-700 bg-slate-100 text-slate-800" : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"}`}>{mapLabel(key)} · {entries.reduce((total, entry) => total + entry.point.count, 0)} 条</button>)}</div>{selectedHotspot ? <div className="mt-3"><div className="flex flex-wrap items-center justify-between gap-2"><div><p className="text-xs font-semibold text-slate-800">{mapLabel(selectedHotspot.key)} 楼层热点</p><p className="mt-1 text-[10px] text-slate-500">共 {selectedHotspot.entries.reduce((total, entry) => total + entry.point.count, 0)} 条；ECharts 保留每个事件精确坐标，交互仅按楼层聚合，避免坐标重叠误跳。</p></div><button type="button" onClick={() => setSelectedCoordinate(null)} className="text-[10px] text-slate-500 underline underline-offset-2">收起</button></div><div className="mt-2 flex flex-wrap gap-2">{selectedHotspot.entries.map((entry) => <article key={`${entry.point.zone_id}:${entry.point.map_id}:${entry.point.x}:${entry.point.y}:${entry.point.event_type ?? "all"}`} className="border border-slate-200 bg-slate-50 px-2.5 py-2 text-[10px] text-slate-600"><p>{customerTerm(entry.point.label)} · {eventTypeLabel(entry.point.event_type ?? "unknown")} · {entry.point.count} 条</p><p className="mt-1">时段：{entry.point.time_slot && entry.point.time_slot !== "all" ? entry.point.time_slot : filters.timeSlot || "全天"} · 平均闭环：{formatMetric(entry.point.average_closure_time_minutes, "分钟")}</p><button type="button" onClick={() => navigateToHotspot(entry.index)} className="mt-1.5 border border-slate-300 bg-white px-2 py-1 text-[10px] text-slate-700 hover:bg-slate-100">跳转事件中心</button></article>)}</div></div> : <p className="mt-2 text-[10px] text-slate-500">点击地图或楼层入口，查看区域、总数、类型、时段和平均闭环后再跳转事件中心。</p>}</div></section>
        <section className="mt-4 grid gap-4 lg:grid-cols-2"><article className="border border-slate-200 bg-white p-4"><p className="text-[10px] font-semibold tracking-[0.13em] text-slate-400">HOTSPOT / TIME PATTERN</p><h2 className="mt-1 text-sm font-semibold text-slate-800">事件时段分布</h2><AnalyticsChart option={timeOption} className="mt-2 h-[210px]" /></article><article className="border border-slate-200 bg-white p-4"><p className="text-[10px] font-semibold tracking-[0.13em] text-slate-400">ROBOT OPERATIONAL EFFICIENCY</p><h2 className="mt-1 text-sm font-semibold text-slate-800">清洁机器人利用率</h2><AnalyticsChart option={utilizationOption} className="mt-2 h-[210px]" /><div className="mt-2 divide-y divide-slate-100 border-t border-slate-100 text-[10px] text-slate-600">{overview.robot_utilization.map((robot) => <p key={robot.robot_id} className="flex justify-between gap-2 py-1.5"><span>{robot.robot_name}</span><span>{robot.utilization === null ? "利用率 —" : `利用率 ${robot.utilization}%`} · 活跃 {robot.active_minutes} / 可用 {robot.available_minutes} 分钟</span></p>)}</div><p className="mt-2 text-[10px] leading-4 text-slate-500">仅统计赛特净界 S5、高仙 Omnie、蜗小白 SC50；任务活跃区间取并集，并按 PoC 24 小时可用时长归一化，不表示真实在线率或遥测。FlashBot Max 不参与清洁利用率排名。</p></article></section>
        <section className="mt-4 grid gap-4 lg:grid-cols-[1fr_1fr]"><article className="border border-slate-200 bg-white p-4"><p className="text-[10px] font-semibold tracking-[0.13em] text-slate-400">EVENT STRUCTURE</p><div className="mt-3 divide-y divide-slate-100">{overview.event_structure.map((item) => <div key={item.event_type} className="flex items-center justify-between py-2 text-xs"><span className="text-slate-600">{item.label || eventTypeLabel(item.event_type)}</span><span className="font-mono text-slate-700">{item.count}</span></div>)}</div></article><article className="border border-slate-200 bg-white p-4"><p className="text-[10px] font-semibold tracking-[0.13em] text-slate-400">DATA COMPOSITION</p><div className="mt-3 space-y-2 text-xs text-slate-600"><p>演示历史：<span className="font-mono text-slate-800">{overview.source_counts.DEMO_HISTORY ?? 0}</span></p><p>Runtime 增量：<span className="font-mono text-slate-800">{overview.source_counts.RUNTIME ?? 0}</span></p><p className="border-t border-slate-100 pt-2 text-[10px] leading-4 text-slate-500">来源：{overview.source || "DEMO_HISTORY + RUNTIME"}。演示历史不表示真实生产数据。</p></div></article></section>
      </> : <div className="min-h-[480px] border border-dashed border-slate-300 bg-white p-8 text-sm text-slate-500">尚未取得可验证的 Analytics API 响应。</div>}</section><AnalyticsAdviceAndChat pageContext={analyticsAgentContext} /></div>
  </main>;
}
