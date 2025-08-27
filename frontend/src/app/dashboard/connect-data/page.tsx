"use client";

import { useEffect, useRef, useState } from "react";
import type { JSX, ReactNode } from "react";
import { fetchWithAuth } from "@/auth/middleware/fetchWithAuth";
import { X, Plug, Activity } from "lucide-react";
import Link from "next/link";

/**
 * Ingestion and cleaning run automatically every 6 hours via Celery Beat.
 * You can kick off both early with the “Ingest + Clean now” button below.
 */

type SourceType = "api" | "manual" | "file";

type DataSource = {
  id: number;
  name: string;
  source_type: SourceType;
  base_url: string | null;
  last_updated: string | null;
  created_at: string | null;
  updated_at: string | null;
};

type SourceItemWire = {
  source_id: number;
  name: string;
  source_type: SourceType;
  base_url: string | null;
  last_updated: string | null;
};

type SourcesResponse = {
  items: SourceItemWire[];
};

type TaskState = "PENDING" | "STARTED" | "PROGRESS" | "SUCCESS" | "FAILURE" | "RETRY";

type TaskStatusInfo = {
  percent?: number;
  processed?: number;
  total?: number;
  source_id?: number;
  source_name?: string;
  inserted?: number;
  duplicates?: number;
  message?: string;
};

type TaskStatus = {
  task_id: string;
  state: TaskState;
  ready: boolean;
  successful: boolean | null;
  info: TaskStatusInfo | null;
};

type WorkflowKickoffResponse = {
  workflow: "ingest_then_clean" | "ingest_only";
  description: string;
  ingest_task_id: string;
  clean_task_id: string | null;
  final_task_id: string;
};

function isSourcesResponse(v: unknown): v is SourcesResponse {
  if (typeof v !== "object" || v === null) return false;
  const maybe = v as { items?: unknown };
  return Array.isArray(maybe.items);
}

export default function DataSourcesLandingPage(): JSX.Element {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [open, setOpen] = useState<boolean>(false);
  const [creating, setCreating] = useState<boolean>(false);

  const [name, setName] = useState<string>("");
  const [type, setType] = useState<SourceType>("api");
  const [baseUrl, setBaseUrl] = useState<string>("");
  const [apiKey, setApiKey] = useState<string>("");

  // workflow task ids
  const [ingestTaskId, setIngestTaskId] = useState<string | null>(null);
  const [cleanTaskId, setCleanTaskId] = useState<string | null>(null);
  const [, setFinalTaskId] = useState<string | null>(null);

  // statuses
  const [ingestStatus, setIngestStatus] = useState<TaskStatus | null>(null);
  const [cleanStatus, setCleanStatus] = useState<TaskStatus | null>(null);

  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    void refresh();
    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, []);

  async function refresh(): Promise<void> {
    setLoading(true);
    try {
      const res: Response = await fetchWithAuth("/datasets/sources");
      const json: unknown = await res.json();
      const mapped: DataSource[] = isSourcesResponse(json)
        ? json.items.map((item: SourceItemWire): DataSource => ({
            id: item.source_id,
            name: item.name,
            source_type: item.source_type,
            base_url: item.base_url,
            last_updated: item.last_updated,
            created_at: null,
            updated_at: null
          }))
        : [];
      setSources(mapped);
    } catch {
      setSources([]);
    } finally {
      setLoading(false);
    }
  }

  async function createSource(): Promise<void> {
    if (!name.trim()) return;
    if (type === "api" && !baseUrl.trim()) return;
    setCreating(true);
    try {
      const body: Record<string, unknown> = {
        name: name.trim(),
        source_type: type,
        api_key: apiKey || null
      };
      if (type === "api") {
        body["base_url"] = baseUrl.trim();
      }

      const res: Response = await fetchWithAuth("/data-sources", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (!res.ok) {
        const msg: string = await res.text();
        throw new Error(msg);
      }
      setName("");
      setBaseUrl("");
      setApiKey("");
      setType("api");
      setOpen(false);
      await refresh();
    } catch (e) {
      alert(String(e));
    } finally {
      setCreating(false);
    }
  }

  function shortDate(iso: string | null): string {
    if (!iso) return "Never";
    const d: Date = new Date(iso);
    if (Number.isNaN(d.getTime())) return "Never";
    return d.toLocaleString();
  }

  // Kickoff ingest → clean workflow
  async function ingestAndCleanNow(): Promise<void> {
    // prevent double-click while running
    const ingestRunning: boolean = Boolean(ingestTaskId && ingestStatus && !ingestStatus.ready);
    const cleanRunning: boolean = Boolean(cleanTaskId && cleanStatus && !cleanStatus.ready);
    if (ingestRunning || cleanRunning) return;

    const res: Response = await fetchWithAuth("/tasks/run/ingest-and-clean", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    if (!res.ok) {
      const txt: string = await res.text();
      throw new Error(txt);
    }
    const data: WorkflowKickoffResponse = (await res.json()) as WorkflowKickoffResponse;

    setIngestTaskId(data.ingest_task_id);
    setCleanTaskId(data.clean_task_id);
    setFinalTaskId(data.final_task_id);

    setIngestStatus({
      task_id: data.ingest_task_id,
      state: "PENDING",
      ready: false,
      successful: null,
      info: null
    });
    if (data.clean_task_id) {
      setCleanStatus({
        task_id: data.clean_task_id,
        state: "PENDING",
        ready: false,
        successful: null,
        info: null
      });
    } else {
      setCleanStatus(null);
    }

    startPollingMulti(data.ingest_task_id, data.clean_task_id);
  }

  function startPollingMulti(ingestId: string, cleanId: string | null): void {
    const tick = async (): Promise<void> => {
      // poll ingest
      const ingestRes: Response = await fetchWithAuth(`/tasks/${ingestId}/status`, { method: "GET" });
      if (ingestRes.ok) {
        const s: TaskStatus = (await ingestRes.json()) as TaskStatus;
        setIngestStatus(s);
      } else {
        const txt: string = await ingestRes.text();
        setIngestStatus((prev: TaskStatus | null): TaskStatus | null =>
          prev ? { ...prev, state: "FAILURE", ready: true, successful: false, info: { message: txt } } : null
        );
      }

      // poll clean if present
      if (cleanId) {
        const cleanRes: Response = await fetchWithAuth(`/tasks/${cleanId}/status`, { method: "GET" });
        if (cleanRes.ok) {
          const c: TaskStatus = (await cleanRes.json()) as TaskStatus;
          setCleanStatus(c);
        } else {
          const txt: string = await cleanRes.text();
          setCleanStatus((prev: TaskStatus | null): TaskStatus | null =>
            prev ? { ...prev, state: "FAILURE", ready: true, successful: false, info: { message: txt } } : null
          );
        }
      }

      const ingestDone: boolean = Boolean(ingestStatus?.ready || (await ingestResOkReady(ingestId)));
      const cleanDone: boolean = cleanId ? Boolean(cleanStatus?.ready || (await taskReady(cleanId))) : true;

      if (!ingestDone || !cleanDone) {
        pollRef.current = setTimeout(() => void tick(), 1000);
      } else {
        // refresh visible timestamps when the workflow completes
        void refresh();
      }
    };

    const ingestResOkReady = async (id: string): Promise<boolean> => {
      const r: Response = await fetchWithAuth(`/tasks/${id}/status`, { method: "GET" });
      if (!r.ok) return false;
      const s: TaskStatus = (await r.json()) as TaskStatus;
      return s.ready;
    };

    const taskReady = async (id: string): Promise<boolean> => {
      const r: Response = await fetchWithAuth(`/tasks/${id}/status`, { method: "GET" });
      if (!r.ok) return false;
      const s: TaskStatus = (await r.json()) as TaskStatus;
      return s.ready;
    };

    if (pollRef.current) clearTimeout(pollRef.current);
    void tick();
  }

  const ingestPct: number = (() => {
    if (ingestStatus?.state === "SUCCESS") return 100;
    if (typeof ingestStatus?.info?.percent === "number")
      return Math.max(0, Math.min(100, ingestStatus.info.percent));
    if (ingestStatus?.state === "STARTED" || ingestStatus?.state === "PENDING") return 1;
    return 0;
  })();

  const workflowRunning: boolean =
    (ingestTaskId && ingestStatus && !ingestStatus.ready) ||
    (cleanTaskId && cleanStatus && !cleanStatus.ready)
      ? true
      : false;

  return (
    <div className="space-y-8">
      <header className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Connect Data</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Register API or Manual sources. Name and Type are required. Base URL is required only for API.
          </p>
        </div>
      </header>

      {(ingestTaskId || cleanTaskId) ? (
        <section aria-label="Ingestion and Cleaning Progress" className="space-y-4">
          {ingestTaskId ? (
            <div className="rounded-2xl bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-700 shadow-xl p-5">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700 dark:text-gray-200">
                  Ingest Task <span className="font-mono">{ingestTaskId}</span> · State:{" "}
                  <span className="font-semibold">{ingestStatus?.state}</span>
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {typeof ingestStatus?.info?.processed === "number" &&
                  typeof ingestStatus?.info?.total === "number"
                    ? `${ingestStatus.info.processed}/${ingestStatus.info.total} sources`
                    : null}
                </div>
              </div>
              <div className="w-full h-3 bg-gray-700 rounded mt-3 overflow-hidden">
                <div className="h-3 bg-blue-500 transition-all" style={{ width: `${ingestPct}%` }} />
              </div>
              <div className="mt-2 text-xs text-gray-400">
                {ingestStatus?.info?.message ??
                  (ingestStatus?.state === "SUCCESS"
                    ? "Complete"
                    : ingestStatus?.state === "FAILURE"
                    ? "Failed"
                    : "Working…")}
              </div>
            </div>
          ) : null}

          {cleanTaskId ? (
            <div className="rounded-2xl bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-700 shadow-xl p-5">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700 dark:text-gray-200">
                  Clean Task <span className="font-mono">{cleanTaskId}</span> · State:{" "}
                  <span className="font-semibold">{cleanStatus?.state ?? "PENDING"}</span>
                </div>
              </div>
              <div className="w-full h-3 bg-gray-700 rounded mt-3 overflow-hidden">
                <div
                  className="h-3 bg-green-600 transition-all"
                  style={{
                    width:
                      cleanStatus?.state === "SUCCESS"
                        ? "100%"
                        : cleanStatus?.state === "STARTED" || cleanStatus?.state === "PENDING"
                        ? "10%"
                        : cleanStatus?.state === "FAILURE"
                        ? "100%"
                        : cleanStatus?.state === "PROGRESS" && typeof cleanStatus?.info?.percent === "number"
                        ? `${Math.max(0, Math.min(100, cleanStatus.info.percent))}%`
                        : "10%"
                  }}
                />
              </div>
              <div className="mt-2 text-xs text-gray-400">
                {cleanStatus?.info?.message ??
                  (cleanStatus?.state === "SUCCESS"
                    ? "Complete"
                    : cleanStatus?.state === "FAILURE"
                    ? "Failed"
                    : "Queued/Running…")}
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      <div className="flex justify-center gap-3">
        <button
          onClick={() => setOpen(true)}
          className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-blue-500 hover:bg-blue-600 text-white shadow-lg transition"
        >
          <Plug className="w-5 h-5" />
          Connect data source
        </button>
        <button
          onClick={() => void ingestAndCleanNow()}
          disabled={workflowRunning}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-green-600 hover:bg-green-700 text-white shadow-lg transition disabled:opacity-60"
          title="Run ingestion and cleaning now"
        >
          <Activity className="w-5 h-5" />
          {workflowRunning ? "Running…" : "Ingest + Clean now"}
        </button>
      </div>

      <section aria-label="Connected Sources">
        <div className="rounded-2xl bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-700 shadow-xl p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-3">Your data sources</h3>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Updates every 6 hours. You can run the full workflow above.
            </div>
          </div>
          {loading ? (
            <div className="text-sm text-gray-500 dark:text-gray-400">Loading…</div>
          ) : sources.length === 0 ? (
            <div className="text-sm text-gray-500 dark:text-gray-400">None connected yet.</div>
          ) : (
            <ul className="divide-y divide-gray-200 dark:divide-gray-700">
              {sources.map((s: DataSource) => (
                <li key={s.id} className="py-3 flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <div className="font-medium text-gray-800 dark:text-white truncate">
                      {s.name} <span className="text-xs text-gray-500">({s.source_type})</span>
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                      {s.source_type === "api" ? s.base_url : "No URL"}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-gray-500 dark:text-gray-400">Last updated</div>
                    <div className="text-sm text-gray-800 dark:text-white">{shortDate(s.last_updated)}</div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <div className="text-center">
        <Link href="/dashboard" className="text-sm text-blue-600 hover:underline">
          Back to dashboard
        </Link>
      </div>

      {open ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <div className="relative w-full max-w-lg mx-auto rounded-2xl shadow-xl border bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm p-6">
            <button
              onClick={() => setOpen(false)}
              className="absolute top-3 right-4 text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Connect data source</h3>
            <div className="grid grid-cols-1 gap-3">
              <Field label="Name">
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-white bg-opacity-50 dark:bg-gray-900 dark:bg-opacity-40 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </Field>

              <Field label="Type">
                <select
                  value={type}
                  onChange={(e) => setType(e.target.value as SourceType)}
                  className="w-full px-3 py-2 rounded-lg bg-white bg-opacity-50 dark:bg-gray-900 dark:bg-opacity-40 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="api">API</option>
                  <option value="manual">Manual</option>
                  <option value="file">File</option>
                </select>
              </Field>

              {type === "api" ? (
                <>
                  <Field label="Base URL">
                    <input
                      value={baseUrl}
                      onChange={(e) => setBaseUrl(e.target.value)}
                      placeholder="https://api.vendor.com/v1/items"
                      className="w-full px-3 py-2 rounded-lg bg-white bg-opacity-50 dark:bg-gray-900 dark:bg-opacity-40 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </Field>
                  <Field label="API Key (optional)">
                    <input
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      type="password"
                      className="w-full px-3 py-2 rounded-lg bg-white bg-opacity-50 dark:bg-gray-900 dark:bg-opacity-40 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </Field>
                </>
              ) : null}
            </div>

            <div className="mt-5 flex justify-end gap-3">
              <button
                onClick={() => setOpen(false)}
                className="px-4 py-2 rounded-md border border-gray-600 hover:bg-gray-800 hover:text-white transition"
              >
                Cancel
              </button>
              <button
                onClick={() => void createSource()}
                disabled={!name.trim() || (type === "api" && !baseUrl.trim()) || creating}
                className="px-4 py-2 rounded-md bg-blue-500 hover:bg-blue-600 text-white transition"
              >
                {creating ? "Creating…" : "Create"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }): JSX.Element {
  return (
    <label className="text-sm text-gray-700 dark:text-gray-300">
      <span className="block mb-1">{label}</span>
      {children}
    </label>
  );
}
