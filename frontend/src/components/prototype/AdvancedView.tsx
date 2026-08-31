import { Eye } from "lucide-react";
import { useState } from "react";
import type { ActiveEvent } from "./types";

type AdvancedViewProps = {
  event: ActiveEvent | null;
  runtimeMode: "live" | "replay";
  onRuntimeModeChange: (mode: "live" | "replay") => void;
};

/** Add only user-approved material here; an empty list must stay visibly pending. */
export const approvedAdvancedAssets: ReadonlyArray<{ src: string; alt: string }> = [];

/**
 * A deliberately quiet customer-facing shell. Engineering trace data remains
 * available through its protected backend APIs and is never rendered here.
 */
export function AdvancedView(_: AdvancedViewProps) {
  const [expanded, setExpanded] = useState<number | null>(null);
  const hasAssets = approvedAdvancedAssets.length > 0;

  return <main className="min-h-[calc(100vh-54px)] bg-[#f6f7f8] px-5 py-6 text-slate-800 lg:px-8" aria-label="高级模式">
    <div className="mx-auto max-w-[1040px]">
      <header className="mb-6">
        <p className="text-[12px] font-semibold tracking-[0.14em] text-slate-400">ADVANCED MODE</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">技术展示辅助页</h1>
        <p className="mt-2 text-[14px] leading-6 text-slate-600">用于面试讲解时展示经确认的技术材料。</p>
      </header>

      {!hasAssets ? <button type="button" onClick={() => setExpanded(0)} className="flex min-h-[430px] w-full items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center transition hover:border-slate-400">
        <span>
          <Eye size={28} className="mx-auto text-slate-300" />
          <strong className="mt-4 block text-[16px] text-slate-700">PENDING USER ASSET</strong>
          <span className="mt-2 block text-[13px] leading-6 text-slate-500">等待用户提供最终技术讲解图片。收到后将在此居中展示，点击可放大。</span>
        </span>
      </button> : <section className={`grid gap-4 ${approvedAdvancedAssets.length === 1 ? "grid-cols-1" : "grid-cols-1 lg:grid-cols-2"}`} aria-label="技术讲解图片">
        {approvedAdvancedAssets.slice(0, 2).map((asset, index) => <button key={asset.src} type="button" onClick={() => setExpanded(index)} className="overflow-hidden rounded-2xl border border-slate-200 bg-white text-left"><img src={asset.src} alt={asset.alt} className="min-h-[430px] w-full object-contain" /></button>)}
      </section>}

      {expanded !== null && <div role="dialog" aria-modal="true" aria-label="技术图片放大预览" onClick={() => setExpanded(null)} className="fixed inset-0 z-[90] flex items-center justify-center bg-slate-950/75 p-6">
        <div onClick={(event) => event.stopPropagation()} className="max-h-full max-w-6xl rounded-2xl bg-white p-4 text-center text-[14px] text-slate-600">{hasAssets ? <img src={approvedAdvancedAssets[expanded]?.src} alt={approvedAdvancedAssets[expanded]?.alt} className="max-h-[82vh] max-w-full object-contain" /> : "PENDING USER ASSET"}</div>
      </div>}
    </div>
  </main>;
}
