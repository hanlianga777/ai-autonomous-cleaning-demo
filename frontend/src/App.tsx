import { useEffect, useState } from "react";
import { Activity, AlertTriangle, Bell, Bot, ChevronDown, CircleHelp, LayoutDashboard, Menu, Settings2, Sparkles } from "lucide-react";

import { fallbackDashboard, fetchDashboard } from "@/api/dashboard";
import { RobotCard } from "@/components/RobotCard";
import { SpatialOperations } from "@/components/spatial/SpatialOperations";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import type { DashboardData } from "@/types/dashboard";

const navItems = [
  { icon: LayoutDashboard, label: "运营总览", active: true },
  { icon: Activity, label: "事件中心" },
  { icon: Bot, label: "机器人编排" },
  { icon: Sparkles, label: "优化中心" },
  { icon: CircleHelp, label: "AI Lab" },
];

function App() {
  const [dashboard, setDashboard] = useState<DashboardData>(fallbackDashboard);
  const [apiStatus, setApiStatus] = useState<"loading" | "online" | "offline">("loading");

  useEffect(() => {
    fetchDashboard()
      .then((data) => { setDashboard(data); setApiStatus("online"); })
      .catch(() => setApiStatus("offline"));
  }, []);

  return (
    <div className="min-h-screen bg-[#f6f7f8] text-slate-900">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-[238px] border-r border-slate-200 bg-white lg:flex lg:flex-col">
        <div className="flex h-[68px] items-center gap-3 border-b border-slate-200 px-6">
          <div className="flex h-8 w-8 items-center justify-center bg-slate-900 text-xs font-bold text-white">CO</div>
          <div><p className="text-sm font-bold tracking-tight">CleanOps</p><p className="text-[10px] font-medium uppercase tracking-[0.14em] text-slate-400">Autonomous Cleaning</p></div>
        </div>
        <nav className="space-y-1 px-3 py-5">
          {navItems.map(({ icon: Icon, label, active }) => <button key={label} className={`flex w-full items-center gap-3 rounded-sm px-3 py-2.5 text-left text-sm transition-colors ${active ? "bg-slate-900 font-medium text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"}`}><Icon size={17} strokeWidth={1.7} />{label}</button>)}
        </nav>
        <div className="mt-auto border-t border-slate-100 p-4"><div className="flex items-center gap-2 text-xs text-slate-500"><Settings2 size={15} />系统设置</div></div>
      </aside>

      <main className="lg:ml-[238px]">
        <header className="flex h-[68px] items-center justify-between border-b border-slate-200 bg-white px-5 lg:px-8">
          <div className="flex items-center gap-3"><button className="lg:hidden"><Menu size={20} /></button><div><p className="section-kicker">Operations dashboard</p><h1 className="text-base font-semibold">自主清洁运营总览</h1></div></div>
          <div className="flex items-center gap-3"><Badge variant="outline"><span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-amber-500" />{dashboard.system.mode}</Badge><button className="relative rounded-sm p-2 text-slate-500 hover:bg-slate-100"><Bell size={18} /><span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-rose-500" /></button><button className="hidden items-center gap-1 text-xs font-medium text-slate-600 sm:flex">运营管理员<ChevronDown size={14} /></button></div>
        </header>

        <div className="mx-auto max-w-[1600px] p-5 lg:p-8">
          {apiStatus === "offline" && <div role="alert" className="mb-5 flex items-center gap-2 border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800"><AlertTriangle size={15} />后端暂不可用，当前展示内置稳定 Mock 数据；请启动 FastAPI 后刷新页面。</div>}
          <section className="mb-6 flex flex-col justify-between gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-end">
            <div><p className="text-sm font-semibold text-slate-900">{dashboard.park.name}</p><p className="mt-1 text-xs text-slate-500">园区运营状态正常 · 数据更新于刚刚</p></div>
            <div className="flex items-center gap-2 text-xs text-slate-500"><span className={`h-2 w-2 rounded-full ${apiStatus === "offline" ? "bg-amber-500" : "bg-emerald-500"}`} />{apiStatus === "offline" ? "离线 Mock 数据" : apiStatus === "loading" ? "正在连接 API" : "Phase 1 基础 Mock 数据"}</div>
          </section>

          <section className="grid gap-4 md:grid-cols-3">
            <Kpi label="可用机器人" value={`${dashboard.fleet.available} / ${dashboard.robots.length}`} detail="当前待命" /><Kpi label="平均电量" value={`${dashboard.fleet.average_battery}%`} detail="Fleet battery" /><Kpi label="已接入区域" value={`${dashboard.park.summary.buildings + dashboard.park.summary.outdoor_zones}`} detail="楼栋及室外区域" />
          </section>

          <SpatialOperations robots={dashboard.robots} />

          <section className="mt-5"><div className="mb-3 flex items-center justify-between"><div><p className="section-kicker">Fleet</p><h2 className="mt-1 text-base font-semibold">机器人状态</h2></div><button className="text-xs font-medium text-slate-600 hover:text-slate-950">查看编排中心</button></div><div className="grid gap-4 xl:grid-cols-3">{dashboard.robots.map((robot) => <RobotCard key={robot.id} robot={robot} />)}</div></section>
        </div>
      </main>
    </div>
  );
}

function Kpi({ label, value, detail }: { label: string; value: string; detail: string }) { return <Card><CardContent className="flex items-end justify-between p-5"><div><p className="section-kicker">{label}</p><p className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">{value}</p></div><p className="text-right text-xs text-slate-500">{detail}</p></CardContent></Card>; }
export default App;
