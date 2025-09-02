"use client";

import { useEffect, useRef, useState } from "react";
import type { JSX, ReactNode } from "react";
import { fetchWithAuth } from "@/auth/middleware/fetchWithAuth";
import { X, Plug, Activity, Download, Sparkles, BarChart, Trash2 } from "lucide-react";
import Link from "next/link";

/**
 * Ingestion and processing run automatically every 6 hours via Celery Beat.
 * Use the actions below to run them on demand.
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
  error?: string;
};

type TaskStatus = {
  task_id: string;
  state: TaskState;
  ready: boolean;
  successful: boolean | null;
  info: TaskStatusInfo | null;
};

type WorkflowKickoffResponse = {
  workflow: "extract_transform_load" | "extract_then_transform" | "extract_only";
  description: string;
  extract_task_id: string;
  transform_task_id?: string | null;
  load_task_id?: string | null;
  clean_task_id?: string | null;  // backward compatibility
  ingest_task_id?: string;        // backward compatibility
  final_task_id: string;
};

function isSourcesResponse(v: unknown): v is SourcesResponse {
  if (typeof v !== "object" || v === null) return false;
  const maybe = v as { items?: unknown };
  return Array.isArray(maybe.items);
}

function hasConnectionError(status: TaskStatus | null): boolean {
  if (!status) return false;
  if (status.info?.error && typeof status.info.error === "string") {
    return status.info.error.toLowerCase().includes("database connection failed");
  }
  if (status.info?.message && typeof status.info.message === "string") {
    return status.info.message.toLowerCase().includes("database connection failed");
  }
  return false;
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

  async function deleteSource(sourceId: number, sourceName: string): Promise<void> {
    const confirmed = confirm(`Are you sure you want to delete "${sourceName}"? This action cannot be undone.`);
    if (!confirmed) return;

    try {
      const res: Response = await fetchWithAuth(`/data-sources/${sourceId}`, {
        method: "DELETE"
      });
      if (!res.ok) {
        const msg: string = await res.text();
        throw new Error(msg);
      }
      await refresh();
    } catch (e) {
      alert(`Failed to delete source: ${String(e)}`);
    }
  }

  function shortDate(iso: string | null): string {
    if (!iso) return "Never";
    const d: Date = new Date(iso);
    if (Number.isNaN(d.getTime())) return "Never";
    return d.toLocaleString();
  }

  // Step 1: Extract data from connected sources
  async function extractData(): Promise<void> {
    const ingestRunning: boolean = Boolean(ingestTaskId && ingestStatus && !ingestStatus.ready);
    if (ingestRunning) return;

    const res: Response = await fetchWithAuth("/tasks/run/extract-data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chain_transform: false })
    });
    if (!res.ok) {
      const txt: string = await res.text();
      throw new Error(txt);
    }
    const data: WorkflowKickoffResponse = (await res.json()) as WorkflowKickoffResponse;

    setIngestTaskId(data.extract_task_id);
    setCleanTaskId(null);
    setFinalTaskId(data.final_task_id);

    setIngestStatus({
      task_id: data.extract_task_id,
      state: "PENDING",
      ready: false,
      successful: null,
      info: null
    });
    setCleanStatus(null);

    startPollingMulti(data.extract_task_id, null);
  }

  // Step 2: Transform raw data to clean staging tables
  async function transformData(forceReprocess = false): Promise<void> {
    const cleanRunning: boolean = Boolean(cleanTaskId && cleanStatus && !cleanStatus.ready);
    if (cleanRunning) return;

    const res: Response = await fetchWithAuth("/tasks/run/transform-data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ force_reprocess: forceReprocess })
    });
    if (!res.ok) {
      const txt: string = await res.text();
      throw new Error(txt);
    }
    const data: { task_id: string; description: string } = (await res.json()) as { task_id: string; description: string };

    setIngestTaskId(null);
    setCleanTaskId(data.task_id);
    setFinalTaskId(data.task_id);

    setIngestStatus(null);
    setCleanStatus({
      task_id: data.task_id,
      state: "PENDING",
      ready: false,
      successful: null,
      info: null
    });

    startPollingMulti(null, data.task_id);
  }

  // Step 3: Load analytics from clean staging data
  async function loadAnalytics(): Promise<void> {
    const cleanRunning: boolean = Boolean(cleanTaskId && cleanStatus && !cleanStatus.ready);
    if (cleanRunning) return;

    const res: Response = await fetchWithAuth("/tasks/run/load-analytics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    if (!res.ok) {
      const txt: string = await res.text();
      throw new Error(txt);
    }
    const data: { task_id: string; description: string } = (await res.json()) as { task_id: string; description: string };

    setIngestTaskId(null);
    setCleanTaskId(data.task_id);
    setFinalTaskId(data.task_id);

    setIngestStatus(null);
    setCleanStatus({
      task_id: data.task_id,
      state: "PENDING",
      ready: false,
      successful: null,
      info: null
    });

    startPollingMulti(null, data.task_id);
  }

  // Complete ETL workflow: Extract → Transform → Load
  async function runFullETL(): Promise<void> {
    const ingestRunning: boolean = Boolean(ingestTaskId && ingestStatus && !ingestStatus.ready);
    const cleanRunning: boolean = Boolean(cleanTaskId && cleanStatus && !cleanStatus.ready);
    if (ingestRunning || cleanRunning) return;

    const res: Response = await fetchWithAuth("/tasks/run/extract-transform-load", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    if (!res.ok) {
      const txt: string = await res.text();
      throw new Error(txt);
    }
    const data: WorkflowKickoffResponse = (await res.json()) as WorkflowKickoffResponse;

    setIngestTaskId(data.extract_task_id);
    setCleanTaskId(data.transform_task_id);
    setFinalTaskId(data.final_task_id);

    setIngestStatus({
      task_id: data.extract_task_id,
      state: "PENDING",
      ready: false,
      successful: null,
      info: null
    });
    if (data.transform_task_id) {
      setCleanStatus({
        task_id: data.transform_task_id,
        state: "PENDING",
        ready: false,
        successful: null,
        info: null
      });
    } else {
      setCleanStatus(null);
    }

    startPollingMulti(data.extract_task_id, data.transform_task_id);
  }

  function startPollingMulti(ingestId: string | null, cleanId: string | null): void {
    const tick = async (): Promise<void> => {
      if (ingestId) {
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
      }

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

      const ingestDone: boolean = ingestId ? Boolean(ingestStatus?.ready || (await ingestResOkReady(ingestId))) : true;
      const cleanDone: boolean = cleanId ? Boolean(cleanStatus?.ready || (await taskReady(cleanId))) : true;

      if (!ingestDone || !cleanDone) {
        pollRef.current = setTimeout(() => void tick(), 1000);
      } else {
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
    if (ingestStatus?.state === "FAILURE" || hasConnectionError(ingestStatus)) return 100;
    if (typeof ingestStatus?.info?.percent === "number")
      return Math.max(0, Math.min(100, ingestStatus.info.percent));
    if (ingestStatus?.state === "STARTED" || ingestStatus?.state === "PENDING") return 1;
    return 0;
  })();

  const cleanPct: number = (() => {
    if (cleanStatus?.state === "SUCCESS") return 100;
    if (cleanStatus?.state === "FAILURE" || hasConnectionError(cleanStatus)) return 100;
    if (typeof cleanStatus?.info?.percent === "number")
      return Math.max(0, Math.min(100, cleanStatus.info.percent));
    if (cleanStatus?.state === "STARTED" || cleanStatus?.state === "PENDING") return 10;
    return 10;
  })();

  const workflowRunning: boolean =
    (ingestTaskId && ingestStatus && !ingestStatus.ready) ||
    (cleanTaskId && cleanStatus && !cleanStatus.ready)
      ? true
      : false;

  const ingestRunning: boolean = Boolean(ingestTaskId && ingestStatus && !ingestStatus.ready);
  const cleanRunning: boolean = Boolean(cleanTaskId && cleanStatus && !cleanStatus.ready);

  return (
    <div className="space-y-8">
      <header className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Connect Data</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Register API, manual, or file sources. Name and type are required. Base URL is required for API sources.
          </p>
        </div>
      </header>

      {(ingestTaskId || cleanTaskId) ? (
        <section aria-label="Ingestion and Processing Progress" className="space-y-4">
          {ingestTaskId ? (
            <div className="rounded-2xl bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-700 shadow-xl p-5">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700 dark:text-gray-200">
                  Ingestion <span className="font-mono">{ingestTaskId}</span> · State:{" "}
                  <span
                    className={`font-semibold ${
                      ingestStatus?.state === "FAILURE" || hasConnectionError(ingestStatus)
                        ? "text-red-500"
                        : ingestStatus?.state === "SUCCESS"
                        ? "text-green-500"
                        : ""
                    }`}
                  >
                    {ingestStatus?.state}
                  </span>
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {typeof ingestStatus?.info?.processed === "number" &&
                  typeof ingestStatus?.info?.total === "number"
                    ? `${ingestStatus.info.processed}/${ingestStatus.info.total} sources`
                    : null}
                </div>
              </div>
              <div className="w-full h-3 bg-gray-700 rounded mt-3 overflow-hidden">
                <div
                  className={`h-3 transition-all ${
                    ingestStatus?.state === "FAILURE" || hasConnectionError(ingestStatus)
                      ? "bg-red-500"
                      : ingestStatus?.state === "SUCCESS"
                      ? "bg-green-500"
                      : "bg-blue-500"
                  }`}
                  style={{ width: `${ingestPct}%` }}
                />
              </div>
              <div
                className={`mt-2 text-xs ${
                  ingestStatus?.state === "FAILURE" || hasConnectionError(ingestStatus) ? "text-red-400" : "text-gray-400"
                }`}
              >
                {hasConnectionError(ingestStatus)
                  ? ingestStatus?.info?.error || ingestStatus?.info?.message || "Database connection failed"
                  : ingestStatus?.info?.message ??
                    (ingestStatus?.state === "SUCCESS"
                      ? "Complete"
                      : ingestStatus?.state === "FAILURE"
                      ? "Task failed — see server logs"
                      : "Queued / Running…")}
              </div>
            </div>
          ) : null}

          {cleanTaskId ? (
            <div className="rounded-2xl bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-700 shadow-xl p-5">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700 dark:text-gray-200">
                  Processing <span className="font-mono">{cleanTaskId}</span> · State:{" "}
                  <span
                    className={`font-semibold ${
                      cleanStatus?.state === "FAILURE" || hasConnectionError(cleanStatus)
                        ? "text-red-500"
                        : cleanStatus?.state === "SUCCESS"
                        ? "text-green-500"
                        : ""
                    }`}
                  >
                    {cleanStatus?.state ?? "PENDING"}
                  </span>
                </div>
              </div>
              <div className="w-full h-3 bg-gray-700 rounded mt-3 overflow-hidden">
                <div
                  className={`h-3 transition-all ${
                    cleanStatus?.state === "FAILURE" || hasConnectionError(cleanStatus)
                      ? "bg-red-500"
                      : cleanStatus?.state === "SUCCESS"
                      ? "bg-green-500"
                      : "bg-purple-500"
                  }`}
                  style={{ width: `${cleanPct}%` }}
                />
              </div>
              <div
                className={`mt-2 text-xs ${
                  cleanStatus?.state === "FAILURE" || hasConnectionError(cleanStatus) ? "text-red-400" : "text-gray-400"
                }`}
              >
                {hasConnectionError(cleanStatus)
                  ? cleanStatus?.info?.error || cleanStatus?.info?.message || "Database connection failed"
                  : cleanStatus?.info?.message ??
                    (cleanStatus?.state === "SUCCESS"
                      ? "Complete"
                      : cleanStatus?.state === "FAILURE"
                      ? "Task failed — see server logs"
                      : "Queued / Running…")}
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {/* Data Source Connection */}
      <div className="flex justify-center">
        <button
          onClick={() => setOpen(true)}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-blue-500 hover:bg-blue-600 text-white shadow-lg transition font-medium"
        >
          <Plug className="w-5 h-5" />
          Connect data source
        </button>
      </div>

      {/* Data Processing Actions */}
      <div className="bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-700 rounded-2xl shadow-xl p-6">
        <div className="text-center mb-4">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white">ETL Data Pipeline</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Three-step process: Extract data from sources, Transform to clean staging tables, Load analytics for dashboard.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <button
            onClick={() => void extractData()}
            disabled={ingestRunning}
            className="inline-flex flex-col items-center gap-2 p-4 rounded-xl bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 text-blue-800 dark:text-blue-200 border border-blue-300 dark:border-blue-700 transition disabled:opacity-60"
            title="Step 1: Extract raw data from all connected API sources"
          >
            <Download className="w-6 h-6" />
            <span className="font-medium">1. Extract</span>
            <span className="text-xs text-center opacity-80">
              {ingestRunning ? "Running…" : "Pull data from sources"}
            </span>
          </button>

          <button
            onClick={() => void transformData()}
            disabled={cleanRunning}
            className="inline-flex flex-col items-center gap-2 p-4 rounded-xl bg-purple-100 hover:bg-purple-200 dark:bg-purple-900 dark:hover:bg-purple-800 text-purple-800 dark:text-purple-200 border border-purple-300 dark:border-purple-700 transition disabled:opacity-60"
            title="Step 2: Transform raw data into clean staging tables"
          >
            <Sparkles className="w-6 h-6" />
            <span className="font-medium">2. Transform</span>
            <span className="text-xs text-center opacity-80">
              {cleanRunning ? "Running…" : "Clean and stage data"}
            </span>
          </button>

          <button
            onClick={() => void loadAnalytics()}
            disabled={cleanRunning}
            className="inline-flex flex-col items-center gap-2 p-4 rounded-xl bg-orange-100 hover:bg-orange-200 dark:bg-orange-900 dark:hover:bg-orange-800 text-orange-800 dark:text-orange-200 border border-orange-300 dark:border-orange-700 transition disabled:opacity-60"
            title="Step 3: Load analytics from clean staging data into metrics tables"
          >
            <BarChart className="w-6 h-6" />
            <span className="font-medium">3. Load</span>
            <span className="text-xs text-center opacity-80">
              {cleanRunning ? "Running…" : "Build dashboard analytics"}
            </span>
          </button>

          <button
            onClick={() => void runFullETL()}
            disabled={workflowRunning}
            className="inline-flex flex-col items-center gap-2 p-4 rounded-xl bg-green-100 hover:bg-green-200 dark:bg-green-900 dark:hover:bg-green-800 text-green-800 dark:text-green-200 border border-green-300 dark:border-green-700 transition disabled:opacity-60"
            title="Complete ETL pipeline: Extract → Transform → Load (recommended)"
          >
            <Activity className="w-6 h-6" />
            <span className="font-medium">Full ETL Pipeline</span>
            <span className="text-xs text-center opacity-80">
              {workflowRunning ? "Running…" : "Complete 3-step workflow"}
            </span>
          </button>
        </div>
      </div>

      <section aria-label="Connected Sources">
        <div className="rounded-2xl bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-700 shadow-xl p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-3">Your data sources</h3>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Runs automatically every 6 hours. You can run it now above.
            </div>
          </div>
          {loading ? (
            <div className="text-sm text-gray-500 dark:text-gray-400">Loading…</div>
          ) : sources.length === 0 ? (
            <div className="text-sm text-gray-500 dark:text-gray-400">No sources connected.</div>
          ) : (
            <ul className="divide-y divide-gray-200 dark:divide-gray-700">
              {sources.map((s: DataSource) => (
                <li key={s.id} className="py-3 flex items-center justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="font-medium text-gray-800 dark:text-white truncate">
                      {s.name} <span className="text-xs text-gray-500">({s.source_type})</span>
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                      {s.source_type === "api" ? s.base_url : "No URL"}
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="text-xs text-gray-500 dark:text-gray-400">Last updated</div>
                    <div className="text-sm text-gray-800 dark:text-white">{shortDate(s.last_updated)}</div>
                  </div>
                  <div className="flex-shrink-0">
                    <button
                      onClick={() => void deleteSource(s.id, s.name)}
                      className="p-2 rounded-lg hover:bg-red-100 dark:hover:bg-red-900 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                      title={`Delete ${s.name}`}
                      aria-label={`Delete data source ${s.name}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
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