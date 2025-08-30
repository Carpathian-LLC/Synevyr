// app/dashboard/page.tsx
"use client";

import { JSX, useEffect, useMemo, useRef, useState } from "react";
import { fetchWithAuth } from "@/auth/middleware/fetchWithAuth";

import {
  Chart,
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  Title,
  type ChartConfiguration,
  type TooltipItem,
} from "chart.js";

/* Chart.js setup */
Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend, Title);

/* ----------------------------- Types ----------------------------- */

type SourceMetricsItem = {
  source_label: string;
  leads: number;
  customers: number;
  orders: number;
  revenue_cents: number;
  cost_cents: number;
  churn_customers: number;
  total_customers: number;
  exits_total: number;
  new_customers: number;
  repeat_customers: number;
  unique_customers: number;
  active_customers: number;
  reactivated_customers: number;
  at_risk_customers: number;
  subscription_revenue_cents: number;
  high_value_orders: number;
  total_customer_lifetime_days: number;
  avg_customer_lifetime_days: number;
  roi_pct: number;
  churn_pct: number;
  avg_order_value_cents: number;
  conversion_rate_pct: number;
  customer_retention_pct: number;
  customer_ltv: number;
};

type SourceMetricsTotals = {
  leads: number;
  customers: number;
  orders: number;
  revenue_cents: number;
  cost_cents: number;
  churn_customers: number;
  total_customers: number;
  exits_total: number;
  new_customers: number;
  repeat_customers: number;
  unique_customers: number;
  active_customers: number;
  reactivated_customers: number;
  at_risk_customers: number;
  subscription_revenue_cents: number;
  high_value_orders: number;
  total_customer_lifetime_days: number;
  avg_order_value_cents: number;
  avg_customer_lifetime_days: number;
  customer_ltv: number;
  roi_pct: number;
  churn_pct: number;
  conversion_rate_pct: number;
  customer_retention_pct: number;
  high_value_order_pct: number;
  subscription_revenue_pct: number;
};

type SourceMetricsResponse = {
  range: { since: string; until: string };
  generated_at: string;
  items: SourceMetricsItem[];
  totals: SourceMetricsTotals;
};

/* ----------------------------- Narrowing ----------------------------- */

function isRecord(x: unknown): x is Record<string, unknown> {
  return typeof x === "object" && x !== null;
}

function isNumber(x: unknown): x is number {
  return typeof x === "number" && Number.isFinite(x);
}

function isString(x: unknown): x is string {
  return typeof x === "string";
}

function toNumber(x: unknown): number {
  return isNumber(x) ? x : Number(x) || 0;
}


function isSourceMetricsItem(x: unknown): x is SourceMetricsItem {
  if (!isRecord(x)) return false;
  const requiredNumbers = [
    "leads", "customers", "orders", "revenue_cents", "cost_cents", "churn_customers",
    "total_customers", "exits_total", "new_customers", "repeat_customers", 
    "unique_customers", "active_customers", "reactivated_customers", "at_risk_customers",
    "subscription_revenue_cents", "high_value_orders", "total_customer_lifetime_days",
    "avg_customer_lifetime_days", "roi_pct", "churn_pct", "avg_order_value_cents",
    "conversion_rate_pct", "customer_retention_pct", "customer_ltv"
  ];
  return (
    isString(x.source_label) &&
    requiredNumbers.every((k) => isNumber((x as Record<string, unknown>)[k]))
  );
}

function isSourceMetricsTotals(x: unknown): x is SourceMetricsTotals {
  return isSourceMetricsItem({ ...(isRecord(x) ? x : {}), source_label: "" });
}

function isSourceMetricsResponse(x: unknown): x is SourceMetricsResponse {
  if (!isRecord(x)) return false;
  const itemsOK =
    Array.isArray(x.items) && x.items.every((it: unknown) => isSourceMetricsItem(it));
  const totalsOK = isSourceMetricsTotals(x.totals);
  const rangeOK =
    isRecord(x.range) && isString(x.range.since) && isString(x.range.until);
  const genOK = isString(x.generated_at);
  return itemsOK && totalsOK && rangeOK && genOK;
}

/* ----------------------------- Utils ----------------------------- */

function todayISO(): string {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d.toISOString().slice(0, 10);
}

function daysAgoISO(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  d.setHours(0, 0, 0, 0);
  return d.toISOString().slice(0, 10);
}

function centsToDollars(c: number): number {
  return Math.round(c) / 100;
}

function fmtMoney(n: number): string {
  const v = Number.isFinite(n) ? n : 0;
  return `$${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function fmtPct(n: number): string {
  const v = Number.isFinite(n) ? n : 0;
  return `${v.toFixed(1)}%`;
}

function fmtDays(n: number): string {
  const v = Number.isFinite(n) ? n : 0;
  if (v === 0) return "0 days";
  if (v === 1) return "1 day";
  if (v < 30) return `${Math.round(v)} days`;
  if (v < 365) return `${Math.round(v / 30)} months`;
  return `${(v / 365).toFixed(1)} years`;
}

function fmtNumber(n: number): string {
  const v = Number.isFinite(n) ? n : 0;
  return v.toLocaleString();
}

/* ----------------------------- Components ----------------------------- */

export default function Dashboard(): JSX.Element {
  // date range controls (default: last 90 days)
  const [since, setSince] = useState<string>(daysAgoISO(90));
  const [until, setUntil] = useState<string>(todayISO());

  // data + state
  const [items, setItems] = useState<SourceMetricsItem[]>([]);
  const [totals, setTotals] = useState<SourceMetricsTotals | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [err, setErr] = useState<string>("");

  // chart refs
  const costRevenueRef = useRef<HTMLCanvasElement | null>(null);
  const roiRef = useRef<HTMLCanvasElement | null>(null);
  const churnRef = useRef<HTMLCanvasElement | null>(null);
  const funnelRef = useRef<HTMLCanvasElement | null>(null);
  const aovRef = useRef<HTMLCanvasElement | null>(null);
  const conversionRef = useRef<HTMLCanvasElement | null>(null);
  const ltvRef = useRef<HTMLCanvasElement | null>(null);
  const lifetimeRef = useRef<HTMLCanvasElement | null>(null);
  const chartsRef = useRef<Chart<"bar", number[], string>[]>([]);

  // fetch analytics (cleaned data)
  async function load(): Promise<void> {
    setLoading(true);
    setErr("");
    try {
      const params = new URLSearchParams();
      params.set("since", since);
      params.set("until", until);
      const res = await fetchWithAuth(`/analytics/source-metrics?${params.toString()}`, { method: "GET" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: unknown = await res.json();
      if (!isSourceMetricsResponse(json)) throw new Error("Invalid API response shape");
      setItems(json.items);
      setTotals(json.totals);
    } catch (e: unknown) {
      setItems([]);
      setTotals(null);
      setErr(e instanceof Error ? e.message : "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // derive chart arrays
  const {
    labels,
    costDollars,
    revenueDollars,
    roiPct,
    churnPct,
    leads,
    customers,
    orders,
    avgOrderValues,
    conversionRates,
    customerLifetimeDays,
    customerLTVs,
    kpiTotalRevenue,
    kpiTotalOrders,
    kpiTotalCustomers,
    kpiAvgLTV,
    kpiAvgCustomerLifetime,
    kpiConversionRate,
    kpiRetentionRate,
    kpiSubscriptionRevenue,
    topROI,
    topChurn,
    topLTV,
    topConversion,
  } = useMemo(() => {
    const lbls = items.map((x) => x.source_label || "Unknown");
    const cost = items.map((x) => centsToDollars(x.cost_cents));
    const rev = items.map((x) => centsToDollars(x.revenue_cents));
    const roi = items.map((x) => x.roi_pct);
    const churn = items.map((x) => x.churn_pct);
    const l = items.map((x) => x.leads);
    const c = items.map((x) => x.customers);
    const o = items.map((x) => x.orders);
    const aov = items.map((x) => centsToDollars(x.avg_order_value_cents));
    const conversion = items.map((x) => x.conversion_rate_pct);
    const lifetime = items.map((x) => x.avg_customer_lifetime_days);
    const ltv = items.map((x) => x.customer_ltv);

    // KPI calculations from totals
    const TR = centsToDollars(toNumber(totals?.revenue_cents));
    const TO = toNumber(totals?.orders);
    const TC = toNumber(totals?.unique_customers);
    const TL = toNumber(totals?.avg_customer_lifetime_days);
    const TLTV = toNumber(totals?.customer_ltv);
    const TCR = toNumber(totals?.conversion_rate_pct);
    const TRR = toNumber(totals?.customer_retention_pct);
    const TSR = centsToDollars(toNumber(totals?.subscription_revenue_cents));

    // Find best/worst performers
    let bestROI = { label: "N/A", value: 0 };
    let worstChurn = { label: "N/A", value: 0 };
    let bestLTV = { label: "N/A", value: 0 };
    let bestConversion = { label: "N/A", value: 0 };
    
    lbls.forEach((s, i) => {
      if (roi[i] > bestROI.value) bestROI = { label: s, value: roi[i] };
      if (churn[i] > worstChurn.value) worstChurn = { label: s, value: churn[i] };
      if (ltv[i] > bestLTV.value) bestLTV = { label: s, value: ltv[i] };
      if (conversion[i] > bestConversion.value) bestConversion = { label: s, value: conversion[i] };
    });

    return {
      labels: lbls,
      costDollars: cost,
      revenueDollars: rev,
      roiPct: roi,
      churnPct: churn,
      leads: l,
      customers: c,
      orders: o,
      avgOrderValues: aov,
      conversionRates: conversion,
      customerLifetimeDays: lifetime,
      customerLTVs: ltv,
      kpiTotalRevenue: TR,
      kpiTotalOrders: TO,
      kpiTotalCustomers: TC,
      kpiAvgLTV: TLTV,
      kpiAvgCustomerLifetime: TL,
      kpiConversionRate: TCR,
      kpiRetentionRate: TRR,
      kpiSubscriptionRevenue: TSR,
      topROI: bestROI,
      topChurn: worstChurn,
      topLTV: bestLTV,
      topConversion: bestConversion,
    };
  }, [items, totals]);

  // draw charts
  useEffect(() => {
    chartsRef.current.forEach((c) => c.destroy());
    chartsRef.current = [];
    if (!labels.length) return;

    const moneyTooltip = (ctx: TooltipItem<"bar">): string => {
      const val = Number(ctx.parsed.y ?? 0);
      return `${ctx.dataset.label as string}: ${fmtMoney(val)}`;
    };
    const pctTooltip = (ctx: TooltipItem<"bar">): string => {
      const val = Number(ctx.parsed.y ?? 0);
      return `${ctx.dataset.label as string}: ${fmtPct(val)}`;
    };
    const daysTooltip = (ctx: TooltipItem<"bar">): string => {
      const val = Number(ctx.parsed.y ?? 0);
      return `${ctx.dataset.label as string}: ${fmtDays(val)}`;
    };

    // Cost vs Revenue (stacked)
    if (costRevenueRef.current) {
      const cfg: ChartConfiguration<"bar", number[], string> = {
        type: "bar",
        data: {
          labels,
          datasets: [
            { label: "Cost", data: costDollars, backgroundColor: "#ef4444", stack: "money" },
            { label: "Revenue", data: revenueDollars, backgroundColor: "#3b82f6", stack: "money" },
          ],
        },
        options: {
          responsive: true,
          plugins: {
            legend: { display: true, position: "bottom" },
            title: { display: false },
            tooltip: { callbacks: { label: moneyTooltip } },
          },
          scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true } },
        },
      };
      chartsRef.current.push(new Chart(costRevenueRef.current, cfg));
    }

    // ROI (%)
    if (roiRef.current) {
      const cfg: ChartConfiguration<"bar", number[], string> = {
        type: "bar",
        data: { labels, datasets: [{ label: "ROI (%)", data: roiPct, backgroundColor: "#1d4ed8" }] },
        options: {
          responsive: true,
          plugins: { legend: { display: false }, title: { display: false }, tooltip: { callbacks: { label: pctTooltip } } },
          scales: { y: { beginAtZero: true } },
        },
      };
      chartsRef.current.push(new Chart(roiRef.current, cfg));
    }

    // Churn (% among customers)
    if (churnRef.current) {
      const cfg: ChartConfiguration<"bar", number[], string> = {
        type: "bar",
        data: { labels, datasets: [{ label: "Churn (%)", data: churnPct, backgroundColor: "#f59e0b" }] },
        options: {
          responsive: true,
          plugins: { legend: { display: false }, title: { display: false }, tooltip: { callbacks: { label: pctTooltip } } },
          scales: { y: { beginAtZero: true, max: 100 } },
        },
      };
      chartsRef.current.push(new Chart(churnRef.current, cfg));
    }

    // Funnel (Leads + Customers + Orders)
    if (funnelRef.current) {
      const cfg: ChartConfiguration<"bar", number[], string> = {
        type: "bar",
        data: {
          labels,
          datasets: [
            { label: "Leads", data: leads, backgroundColor: "#60a5fa", stack: "funnel" },
            { label: "Customers", data: customers, backgroundColor: "#3b82f6", stack: "funnel" },
            { label: "Orders", data: orders, backgroundColor: "#2563eb", stack: "funnel" },
          ],
        },
        options: {
          responsive: true,
          plugins: { legend: { display: true, position: "bottom" }, title: { display: false } },
          scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true } },
        },
      };
      chartsRef.current.push(new Chart(funnelRef.current, cfg));
    }

    // Average Order Value ($)
    if (aovRef.current) {
      const cfg: ChartConfiguration<"bar", number[], string> = {
        type: "bar",
        data: { labels, datasets: [{ label: "AOV ($)", data: avgOrderValues, backgroundColor: "#10b981" }] },
        options: {
          responsive: true,
          plugins: { legend: { display: false }, title: { display: false }, tooltip: { callbacks: { label: moneyTooltip } } },
          scales: { y: { beginAtZero: true } },
        },
      };
      chartsRef.current.push(new Chart(aovRef.current, cfg));
    }

    // Conversion Rate (%)
    if (conversionRef.current) {
      const cfg: ChartConfiguration<"bar", number[], string> = {
        type: "bar",
        data: { labels, datasets: [{ label: "Conversion (%)", data: conversionRates, backgroundColor: "#8b5cf6" }] },
        options: {
          responsive: true,
          plugins: { legend: { display: false }, title: { display: false }, tooltip: { callbacks: { label: pctTooltip } } },
          scales: { y: { beginAtZero: true, max: 100 } },
        },
      };
      chartsRef.current.push(new Chart(conversionRef.current, cfg));
    }

    // Customer Lifetime Value ($)
    if (ltvRef.current) {
      const cfg: ChartConfiguration<"bar", number[], string> = {
        type: "bar",
        data: { labels, datasets: [{ label: "LTV ($)", data: customerLTVs, backgroundColor: "#f59e0b" }] },
        options: {
          responsive: true,
          plugins: { legend: { display: false }, title: { display: false }, tooltip: { callbacks: { label: moneyTooltip } } },
          scales: { y: { beginAtZero: true } },
        },
      };
      chartsRef.current.push(new Chart(ltvRef.current, cfg));
    }

    // Customer Lifetime (Days)
    if (lifetimeRef.current) {
      const cfg: ChartConfiguration<"bar", number[], string> = {
        type: "bar",
        data: { labels, datasets: [{ label: "Lifetime", data: customerLifetimeDays, backgroundColor: "#ec4899" }] },
        options: {
          responsive: true,
          plugins: { legend: { display: false }, title: { display: false }, tooltip: { callbacks: { label: daysTooltip } } },
          scales: { y: { beginAtZero: true } },
        },
      };
      chartsRef.current.push(new Chart(lifetimeRef.current, cfg));
    }

    return () => {
      chartsRef.current.forEach((c) => c.destroy());
      chartsRef.current = [];
    };
  }, [labels, costDollars, revenueDollars, roiPct, churnPct, leads, customers, orders, avgOrderValues, conversionRates, customerLTVs, customerLifetimeDays]);

  // quick ranges
  function setRangeDays(n: number): void {
    setSince(daysAgoISO(n));
    setUntil(todayISO());
  }

  // refresh on date change
  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [since, until]);

  return (
    <div className="space-y-10">

      {/* Header */}
      <header>
        <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Source Performance & ROI</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Stacked cost vs revenue, ROI, churn, and funnel by source from cleaned analytics.
        </p>
      </header>

      {/* Controls */}
      <section aria-label="Filters">
        <div className="p-4 rounded-2xl bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-700 shadow-xl">
          <div className="flex flex-wrap items-center gap-3">
            <div className="text-white text-lg font-semibold">Date range</div>

            <div className="ml-auto flex items-center gap-2">
              <button
                type="button"
                onClick={() => setRangeDays(30)}
                className="px-3 py-1 rounded-lg bg-gray-700 hover:bg-gray-600 text-white text-sm transition"
              >
                Last 30d
              </button>
              <button
                type="button"
                onClick={() => setRangeDays(90)}
                className="px-3 py-1 rounded-lg bg-gray-700 hover:bg-gray-600 text-white text-sm transition"
              >
                Last 90d
              </button>
              <button
                type="button"
                onClick={() => setRangeDays(180)}
                className="px-3 py-1 rounded-lg bg-gray-700 hover:bg-gray-600 text-white text-sm transition"
              >
                Last 180d
              </button>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <label className="text-sm text-gray-300">Since</label>
            <input
              type="date"
              value={since}
              onChange={(e) => setSince(e.target.value)}
              className="rounded-md bg-white bg-opacity-20 dark:bg-gray-900 dark:bg-opacity-40 border border-gray-600 px-2 py-1 text-sm text-white"
            />
            <label className="text-sm text-gray-300">Until</label>
            <input
              type="date"
              value={until}
              onChange={(e) => setUntil(e.target.value)}
              className="rounded-md bg-white bg-opacity-20 dark:bg-gray-900 dark:bg-opacity-40 border border-gray-600 px-2 py-1 text-sm text-white"
            />
            <button
              type="button"
              onClick={() => void load()}
              className="ml-auto px-4 py-2 rounded-lg bg-blue-500 hover:bg-blue-600 text-white text-sm transition"
              disabled={loading}
            >
              {loading ? "Loading…" : "Refresh"}
            </button>
          </div>

          {err && (
            <div className="mt-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-red-200">
              {err}
            </div>
          )}
        </div>
      </section>

      {/* Executive KPI Dashboard */}
      <section>
        <h3 className="text-xl font-semibold text-white mb-4">Executive Overview</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4 mb-6">
          <SummaryCard title="Total Revenue" value={loading ? "…" : fmtMoney(kpiTotalRevenue)} color="bg-emerald-600" />
          <SummaryCard title="Total Orders" value={loading ? "…" : fmtNumber(kpiTotalOrders)} color="bg-blue-600" />
          <SummaryCard title="Unique Customers" value={loading ? "…" : fmtNumber(kpiTotalCustomers)} color="bg-purple-600" />
          <SummaryCard title="Avg Customer LTV" value={loading ? "…" : fmtMoney(kpiAvgLTV)} color="bg-orange-600" />
          <SummaryCard title="Conversion Rate" value={loading ? "…" : fmtPct(kpiConversionRate)} color="bg-pink-600" />
          <SummaryCard title="Retention Rate" value={loading ? "…" : fmtPct(kpiRetentionRate)} color="bg-green-600" />
        </div>
        
        <h4 className="text-lg font-semibold text-white mb-3">Performance Leaders</h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 border-2 border-dashed border-gray-600 p-4 rounded-xl">
          <SummaryCard title="Highest ROI" value={loading ? "…" : `${topROI.label} · ${fmtPct(topROI.value)}`} color="bg-green-700" />
          <SummaryCard title="Best LTV" value={loading ? "…" : `${topLTV.label} · ${fmtMoney(topLTV.value)}`} color="bg-yellow-600" />
          <SummaryCard title="Top Conversion" value={loading ? "…" : `${topConversion.label} · ${fmtPct(topConversion.value)}`} color="bg-indigo-600" />
          <SummaryCard title="Highest Churn" value={loading ? "…" : `${topChurn.label} · ${fmtPct(topChurn.value)}`} color="bg-red-600" />
        </div>

        <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
            <h5 className="text-sm font-semibold text-gray-300 mb-2">Subscription Business</h5>
            <div className="text-2xl font-bold text-blue-400">{loading ? "…" : fmtMoney(kpiSubscriptionRevenue)}</div>
            <div className="text-xs text-gray-400">Recurring Revenue</div>
          </div>
          <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
            <h5 className="text-sm font-semibold text-gray-300 mb-2">Customer Health</h5>
            <div className="text-2xl font-bold text-purple-400">{loading ? "…" : fmtDays(kpiAvgCustomerLifetime)}</div>
            <div className="text-xs text-gray-400">Avg Customer Lifetime</div>
          </div>
          <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
            <h5 className="text-sm font-semibold text-gray-300 mb-2">Opportunities</h5>
            <div className="text-2xl font-bold text-red-400">{loading ? "…" : fmtPct(100 - kpiRetentionRate)}</div>
            <div className="text-xs text-gray-400">Potential Churn Risk</div>
          </div>
        </div>
      </section>

      {/* Charts */}
      <section className="space-y-10">
        <ChartBlock title="Cost vs Revenue by Source">
          <canvas ref={costRevenueRef} className="w-full h-64" />
        </ChartBlock>

        <ChartBlock title="ROI by Source (%)">
          <canvas ref={roiRef} className="w-full h-64" />
        </ChartBlock>

        <ChartBlock title="Customer Churn by Source (%)">
          <canvas ref={churnRef} className="w-full h-64" />
        </ChartBlock>

        <ChartBlock title="Funnel by Source (Leads + Customers + Orders)">
          <canvas ref={funnelRef} className="w-full h-64" />
        </ChartBlock>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          <ChartBlock title="Average Order Value by Source">
            <canvas ref={aovRef} className="w-full h-64" />
          </ChartBlock>
          
          <ChartBlock title="Conversion Rate by Source">
            <canvas ref={conversionRef} className="w-full h-64" />
          </ChartBlock>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          <ChartBlock title="Customer Lifetime Value by Source">
            <canvas ref={ltvRef} className="w-full h-64" />
          </ChartBlock>
          
          <ChartBlock title="Average Customer Lifetime by Source">
            <canvas ref={lifetimeRef} className="w-full h-64" />
          </ChartBlock>
        </div>

        {loading && <div className="mb-6 text-center text-sm text-gray-400">Loading…</div>}
        {!loading && items.length === 0 && (
          <div className="mb-6 text-center text-sm text-gray-400">No data in the selected range.</div>
        )}
      </section>

      {/* Summary table */}
      <section>
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-3">Summary by Source</h3>
        <div className="overflow-x-auto rounded-xl border border-gray-700 bg-gray-900/60">
          <table className="min-w-full text-xs text-gray-200">
            <thead className="bg-gray-800/70 uppercase">
              <tr>
                <th className="px-2 py-2 text-left">Source</th>
                <th className="px-2 py-2 text-right">Leads</th>
                <th className="px-2 py-2 text-right">Orders</th>
                <th className="px-2 py-2 text-right">Conv %</th>
                <th className="px-2 py-2 text-right">Revenue</th>
                <th className="px-2 py-2 text-right">AOV</th>
                <th className="px-2 py-2 text-right">ROI %</th>
                <th className="px-2 py-2 text-right">LTV</th>
                <th className="px-2 py-2 text-right">Lifetime</th>
                <th className="px-2 py-2 text-right">Churn %</th>
              </tr>
            </thead>
            <tbody>
              {items.map((r) => (
                <tr key={r.source_label} className="border-t border-gray-700/60">
                  <td className="px-2 py-2">{r.source_label || "Unknown"}</td>
                  <td className="px-2 py-2 text-right">{fmtNumber(r.leads)}</td>
                  <td className="px-2 py-2 text-right">{fmtNumber(r.orders)}</td>
                  <td className="px-2 py-2 text-right">{fmtPct(r.conversion_rate_pct)}</td>
                  <td className="px-2 py-2 text-right">{fmtMoney(centsToDollars(r.revenue_cents))}</td>
                  <td className="px-2 py-2 text-right">{fmtMoney(centsToDollars(r.avg_order_value_cents))}</td>
                  <td className="px-2 py-2 text-right">{fmtPct(r.roi_pct)}</td>
                  <td className="px-2 py-2 text-right">{fmtMoney(r.customer_ltv)}</td>
                  <td className="px-2 py-2 text-right">{fmtDays(r.avg_customer_lifetime_days)}</td>
                  <td className="px-2 py-2 text-right">{fmtPct(r.churn_pct)}</td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td className="px-3 py-4 text-center text-gray-400" colSpan={10}>
                    No data
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Conv % = Orders/Leads conversion rate. AOV = Average Order Value. ROI = (Revenue − Cost) / Cost. 
          LTV = Customer Lifetime Value. Lifetime = Average customer lifespan. Churn % = Customer churn rate.
        </p>
      </section>
    </div>
  );
}

/* ----------------------------- UI bits ----------------------------- */

function SummaryCard(props: { title: string; value: string; color?: string }): JSX.Element {
  const bgColor = props.color || "bg-gray-800";
  const textColor = props.color ? "text-white" : "text-blue-400";
  
  return (
    <div className={`p-4 rounded-xl ${bgColor} bg-opacity-90 backdrop-blur-md border border-gray-700 shadow-lg relative overflow-hidden`}>
      <div className="absolute inset-0 animate-pulse bg-gradient-to-br from-white/10 via-transparent to-white/5 rounded-xl pointer-events-none" />
      <div className="relative">
        <div className="text-white text-sm font-semibold opacity-90">{props.title}</div>
        <div className={`text-2xl ${textColor} font-bold`}>{props.value}</div>
      </div>
    </div>
  );
}

function ChartBlock(props: { title: string; children: React.ReactNode }): JSX.Element {
  return (
    <div>
      <h4 className="text-xl font-semibold mb-4 text-center text-white">{props.title}</h4>
      <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-4">{props.children}</div>
    </div>
  );
}
