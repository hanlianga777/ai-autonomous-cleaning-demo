import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  SESSION_STORAGE_KEY, operationSessionHeaders, readStorage, writeStorage,
  type AdviceSnapshot, type AgentSessionSnapshot, type OperationsTask, type OperationsTaskAction,
} from "./robotOperationsModel";

type PageContext = Record<string, unknown>;
type OperationsContextValue = {
  session: AgentSessionSnapshot | null;
  loading: boolean;
  error: string | null;
  pending: boolean;
  /** False means the text remains in the composer for an operator retry. */
  sendMessage: (text: string, pageContext: PageContext) => Promise<boolean>;
  taskAction: (task: OperationsTask, action: OperationsTaskAction) => Promise<void>;
  advice: AdviceSnapshot | null;
  adviceLoading: boolean;
  adviceError: string | null;
  loadAdvice: () => Promise<void>;
  regenerateAdvice: () => Promise<void>;
};

const OperationsContext = createContext<OperationsContextValue | null>(null);

function isSnapshot(value: unknown): value is AgentSessionSnapshot {
  return Boolean(value && typeof value === "object" && typeof (value as { id?: unknown }).id === "string" && Array.isArray((value as { messages?: unknown }).messages));
}

async function responseJson(response: Response): Promise<unknown> {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof (body as { detail?: unknown }).detail === "string" ? (body as { detail: string }).detail : `请求失败（${response.status}）`);
  return body;
}

export function RobotOperationsProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AgentSessionSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [advice, setAdvice] = useState<AdviceSnapshot | null>(null);
  const [adviceLoading, setAdviceLoading] = useState(false);
  const [adviceError, setAdviceError] = useState<string | null>(null);
  const requestId = useRef(0);
  const mutationId = useRef(0);
  const pendingRef = useRef(false);

  useEffect(() => { pendingRef.current = pending; }, [pending]);

  const applySnapshot = useCallback((value: unknown) => {
    if (!isSnapshot(value)) throw new Error("服务返回的 Agent Session 结构无效");
    setSession(value); writeStorage(SESSION_STORAGE_KEY, value.id);
    if (value.error?.message) setError(`${value.error.code ?? "AGENT_ERROR"}：${value.error.message}`);
    else setError(null);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const initialise = async () => {
      const request = ++requestId.current;
      setLoading(true); setError(null);
      try {
        const showResponse = await fetch("/api/robot-operations/show-session", { signal: controller.signal });
        const show = await responseJson(showResponse) as { show_session?: { id?: string; agent_session_id?: string } | null };
        const showSessionId = show.show_session?.id;
        const showAgentSessionId = show.show_session?.agent_session_id;
        const storedShow = readStorage("cleanops.show-session.v1");
        const id = showSessionId && storedShow === showSessionId ? readStorage(SESSION_STORAGE_KEY) : null;
        if (showSessionId) writeStorage("cleanops.show-session.v1", showSessionId);
        const response = id
          ? await fetch(`/api/robot-operations/sessions/${encodeURIComponent(id)}`, { signal: controller.signal })
          : showAgentSessionId
            ? await fetch(`/api/robot-operations/sessions/${encodeURIComponent(showAgentSessionId)}`, { signal: controller.signal })
          : await fetch("/api/robot-operations/sessions", { method: "POST", headers: { "content-type": "application/json" }, body: "{}", signal: controller.signal });
        const body = await responseJson(response);
        if (!controller.signal.aborted && request === requestId.current) applySnapshot(body);
      } catch (reason) {
        if (!controller.signal.aborted && request === requestId.current) setError(reason instanceof Error ? reason.message : "Robot Operations Agent 服务不可用");
      } finally { if (!controller.signal.aborted && request === requestId.current) setLoading(false); }
    };
    void initialise();
    return () => controller.abort();
  }, [applySnapshot]);

  useEffect(() => {
    if (!session?.id) return;
    let active = true;
    let inFlight = false;
    const poll = async () => {
      if (!active || inFlight || pendingRef.current) return;
      inFlight = true;
      const observedMutation = mutationId.current;
      try {
        const body = await responseJson(await fetch(`/api/robot-operations/sessions/${encodeURIComponent(session.id)}`));
        if (active && !pendingRef.current && observedMutation === mutationId.current) applySnapshot(body);
      } catch (reason) {
        if (active && !pendingRef.current) setError(reason instanceof Error ? reason.message : "共享 Agent Session 同步失败");
      } finally { inFlight = false; }
    };
    const timer = window.setInterval(() => void poll(), 1800);
    return () => { active = false; window.clearInterval(timer); };
  }, [applySnapshot, session?.id]);

  const sendMessage = useCallback(async (text: string, pageContext: PageContext): Promise<boolean> => {
    if (!session || !text.trim() || pending) return false;
    mutationId.current += 1;
    setPending(true); setError(null);
    try {
      const response = await fetch(`/api/robot-operations/sessions/${encodeURIComponent(session.id)}/messages`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ text: text.trim(), page_context: pageContext }) });
      const body = await responseJson(response);
      applySnapshot(body);
      return isSnapshot(body) && !body.error;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "消息未能提交；未生成本地替代回复。");
      return false;
    }
    finally { setPending(false); }
  }, [applySnapshot, pending, session]);

  const taskAction = useCallback(async (task: OperationsTask, action: OperationsTaskAction) => {
    if (!session || pending) return;
    mutationId.current += 1;
    setPending(true); setError(null);
    try {
      const path = action === "advance" ? `/api/robot-operations/tasks/${encodeURIComponent(task.task_id)}/advance` : `/api/robot-operations/tasks/${encodeURIComponent(task.task_id)}/${action}`;
      const body = await responseJson(await fetch(path, { method: "POST", headers: operationSessionHeaders(session.id) }));
      if (isSnapshot(body)) applySnapshot(body);
      else {
        const updated = (body as { task?: OperationsTask }).task ?? body as OperationsTask;
        if (!updated || typeof updated.task_id !== "string") throw new Error("任务状态响应无效");
        setSession((current) => current ? { ...current, tasks: current.tasks.map((item) => item.task_id === updated.task_id ? updated : item) } : current);
      }
      if (session) applySnapshot(await responseJson(await fetch(`/api/robot-operations/sessions/${encodeURIComponent(session.id)}`)));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "任务操作未确认；当前状态保持不变。"); }
    finally { setPending(false); }
  }, [applySnapshot, pending, session]);

  const loadAdvice = useCallback(async () => {
    setAdviceLoading(true); setAdviceError(null);
    try {
      const body = await responseJson(await fetch("/api/robot-operations/advice")) as { snapshot?: AdviceSnapshot | null } | AdviceSnapshot | null;
      const snapshot: AdviceSnapshot | null = body && typeof body === "object" && "snapshot" in body ? body.snapshot ?? null : body as AdviceSnapshot | null;
      setAdvice(snapshot);
    } catch (reason) { setAdviceError(reason instanceof Error ? reason.message : "运营建议快照不可用"); }
    finally { setAdviceLoading(false); }
  }, []);

  const regenerateAdvice = useCallback(async () => {
    setAdviceLoading(true); setAdviceError(null);
    try {
      const body = await responseJson(await fetch("/api/robot-operations/advice", { method: "POST" })) as { snapshot?: AdviceSnapshot } | AdviceSnapshot;
      const snapshot: AdviceSnapshot | null = body && typeof body === "object" && "snapshot" in body ? body.snapshot ?? null : body as AdviceSnapshot;
      setAdvice(snapshot);
    } catch (reason) { setAdviceError(reason instanceof Error ? reason.message : "运营建议未重新生成；未显示本地替代内容。"); }
    finally { setAdviceLoading(false); }
  }, []);

  const value = useMemo(() => ({ session, loading, error, pending, sendMessage, taskAction, advice, adviceLoading, adviceError, loadAdvice, regenerateAdvice }), [advice, adviceError, adviceLoading, error, loadAdvice, loading, pending, regenerateAdvice, sendMessage, session, taskAction]);
  return <OperationsContext.Provider value={value}>{children}</OperationsContext.Provider>;
}

export function useRobotOperations() {
  const context = useContext(OperationsContext);
  if (!context) throw new Error("RobotOperationsProvider is required");
  return context;
}
