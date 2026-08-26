import { useEffect, useRef } from "react";
import { init, use } from "echarts/core";
import { BarChart, ScatterChart } from "echarts/charts";
import { GridComponent, TooltipComponent, VisualMapComponent } from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import type { EChartsOption } from "echarts";

use([BarChart, GridComponent, ScatterChart, SVGRenderer, TooltipComponent, VisualMapComponent]);

export function AnalyticsChart({ option, className = "h-[250px]" }: { option: EChartsOption; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return undefined;
    const chart = init(ref.current, undefined, { renderer: "svg" });
    chart.setOption(option);
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => { window.removeEventListener("resize", resize); chart.dispose(); };
  }, [option]);
  return <div ref={ref} className={className} role="img" aria-label="运营分析图表" />;
}
