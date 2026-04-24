"use client";
import { useState, KeyboardEvent } from "react";
import { useSWRConfig } from "swr";
import { Trash2, ChevronDown, ChevronRight } from "lucide-react";
import { useStrategies } from "@/hooks/useStrategies";
import { createStrategy, deleteStrategy, fetchStrategyById } from "@/lib/api/strategies";
import { StrategyItem, StrategyStatus, BacktestResult, StrategyWithResult } from "@/lib/types";
import { ErrorAlert } from "@/components/shared/ErrorAlert";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";

function statusBadge(status: StrategyStatus) {
  switch (status) {
    case "pending":
      return <Badge variant="secondary">pending</Badge>;
    case "running":
      return <Badge variant="default">running…</Badge>;
    case "completed":
      return <Badge variant="outline">completed</Badge>;
    case "failed":
      return <Badge variant="destructive">failed</Badge>;
  }
}

function fmt(value: number | null, decimals = 2, suffix = "") {
  if (value === null || value === undefined) return "—";
  return `${value.toFixed(decimals)}${suffix}`;
}

function ResultDetail({ result }: { result: StrategyWithResult }) {
  return (
    <tr>
      <td colSpan={6} className="px-6 pb-4 pt-0">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-muted/30 rounded-md p-4 text-sm">
          <div>
            <p className="text-muted-foreground text-xs mb-1">Sharpe Ratio</p>
            <p className="font-semibold tabular-nums">{fmt(result.sharpe_ratio)}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs mb-1">Total Return</p>
            <p className="font-semibold tabular-nums">{fmt(result.total_return_pct, 2, "%")}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs mb-1">Max Drawdown</p>
            <p className="font-semibold tabular-nums">{fmt(result.max_drawdown_pct, 2, "%")}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs mb-1">Win Rate</p>
            <p className="font-semibold tabular-nums">{fmt(result.win_rate_pct, 2, "%")}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs mb-1">Trades</p>
            <p className="font-semibold tabular-nums">{result.num_trades ?? "—"}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs mb-1">AI Score</p>
            <p className="font-semibold tabular-nums">{fmt(result.ai_score)}</p>
          </div>
          {result.backtest_start && result.backtest_end && (
            <div className="col-span-2">
              <p className="text-muted-foreground text-xs mb-1">Backtest Period</p>
              <p className="font-semibold">
                {result.backtest_start} → {result.backtest_end}
              </p>
            </div>
          )}
          {result.ai_evaluation && (
            <div className="col-span-2 sm:col-span-4">
              <p className="text-muted-foreground text-xs mb-1">AI Evaluation</p>
              <p className="text-muted-foreground leading-relaxed">{result.ai_evaluation}</p>
            </div>
          )}
          {result.rejection_reason && (
            <div className="col-span-2 sm:col-span-4">
              <p className="text-muted-foreground text-xs mb-1">Rejection Reason</p>
              <p className="text-destructive leading-relaxed">{result.rejection_reason}</p>
            </div>
          )}
        </div>
      </td>
    </tr>
  );
}

function StrategyRow({ item, onDelete, deleting }: { item: StrategyItem; onDelete: (id: string) => void; deleting: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const [result, setResult] = useState<StrategyWithResult | null>(null);
  const [loadingResult, setLoadingResult] = useState(false);

  const canExpand = item.status === "completed" || item.status === "failed";

  async function toggleExpand() {
    if (!canExpand) return;
    if (expanded) {
      setExpanded(false);
      return;
    }
    if (!result) {
      setLoadingResult(true);
      try {
        const full = await fetchStrategyById(item.id);
        setResult(full);
      } finally {
        setLoadingResult(false);
      }
    }
    setExpanded(true);
  }

  return (
    <>
      <tr className={`border-b last:border-0 hover:bg-muted/30 ${canExpand ? "cursor-pointer" : ""}`} onClick={toggleExpand}>
        <td className="px-4 py-3 w-6">{canExpand && (loadingResult ? <span className="text-muted-foreground text-xs">…</span> : expanded ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 text-muted-foreground" />)}</td>
        <td className="px-4 py-3 font-mono font-semibold">{item.ticker}</td>
        <td className="px-4 py-3">{statusBadge(item.status)}</td>
        <td className="px-4 py-3 text-right tabular-nums">{item.iterations}</td>
        <td className="px-4 py-3 text-muted-foreground">{formatDate(item.created_at)}</td>
        <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
          <Button variant="ghost" size="icon" disabled={deleting} onClick={() => onDelete(item.id)} aria-label={`Delete strategy for ${item.ticker}`}>
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </td>
      </tr>
      {expanded && result && <ResultDetail result={result} />}
    </>
  );
}

export function StrategiesView() {
  const { data, error, isLoading } = useStrategies();
  const { mutate } = useSWRConfig();

  const [ticker, setTicker] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleSubmit() {
    const trimmed = ticker.trim().toUpperCase();
    if (!trimmed) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      await createStrategy(trimmed);
      setTicker("");
      mutate(["strategies", JSON.stringify({})]);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to start strategy research");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    setDeletingId(id);
    try {
      await deleteStrategy(id);
      mutate(["strategies", JSON.stringify({})]);
    } catch {
      // leave list unchanged on error
    } finally {
      setDeletingId(null);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") handleSubmit();
  }

  return (
    <div className="space-y-6">
      <div className="flex gap-2 items-start">
        <div className="flex flex-col gap-1 w-48">
          <Input
            placeholder="e.g. AAPL"
            value={ticker}
            onChange={(e) => {
              setTicker(e.target.value);
              setSubmitError(null);
            }}
            onKeyDown={handleKeyDown}
            disabled={submitting}
          />
          {submitError && <p className="text-sm text-destructive">{submitError}</p>}
        </div>
        <Button onClick={handleSubmit} disabled={submitting || !ticker.trim()}>
          {submitting ? "Starting…" : "Find Strategy"}
        </Button>
      </div>

      {error && <ErrorAlert message={error.message} />}

      {isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : (
        <div className="rounded-md border overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-3 w-6" />
                <th className="px-4 py-3 text-left font-medium">Ticker</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-right font-medium">Iterations</th>
                <th className="px-4 py-3 text-left font-medium">Created</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {!data || data.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                    No strategies yet. Enter a ticker above to start.
                  </td>
                </tr>
              ) : (
                data.map((item) => <StrategyRow key={item.id} item={item} onDelete={handleDelete} deleting={deletingId === item.id} />)
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
