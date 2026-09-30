"use client";

import { FormEvent, useEffect, useState, type ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { AutopsyResponse, readError, requestAutopsy, SubscriptionItem } from "@/lib/api";
import { LandingPage } from "@/components/landing-page";
import { SignIntoBank } from "@/components/sign-into-bank";

export function AutopsyApp() {
  const [view, setView] = useState<"welcome" | "pulling" | "report">("welcome");
  const [linkNotice, setLinkNotice] = useState<string | null>(null);
  const [report, setReport] = useState<AutopsyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [answerSource, setAnswerSource] = useState<string | null>(null);

  async function load(month?: string) {
    setError(null);
    const query = month ? `?month=${month}` : "";
    try {
      const response = await requestAutopsy(`/api/autopsy${query}`);
      if (!response.ok) {
        setError(await readError(response));
        return;
      }
      const body = (await response.json()) as AutopsyResponse;
      setReport(body);
      setAnswer(null);
      setAnswerSource(null);
    } catch {
      setError("The API isn't running. Start the backend, then try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (view === "report" && !report) {
      void load();
    }
  }, [view, report]);

  async function loadSample() {
    setBusy(true);
    setError(null);
    try {
      const response = await requestAutopsy("/api/transactions/seed", { method: "POST" });
      if (!response.ok) {
        setError(await readError(response));
        return;
      }
      setReport((await response.json()) as AutopsyResponse);
      setAnswer(null);
    } catch {
      setError("The API isn't running. Start the backend, then try again.");
    } finally {
      setBusy(false);
    }
  }

  async function importCsv(file: File) {
    setBusy(true);
    setError(null);
    const form = new FormData();
    form.set("file", file);
    try {
      const response = await requestAutopsy("/api/transactions/import", { method: "POST", body: form });
      if (!response.ok) {
        setError(await readError(response));
        return;
      }
      await load();
    } catch {
      setError("The API isn't running. Start the backend, then try again.");
    } finally {
      setBusy(false);
    }
  }

  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!report || report.empty || !question.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const response = await requestAutopsy("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, month: report.month }),
      });
      if (!response.ok) {
        setError(await readError(response));
        return;
      }
      const body = (await response.json()) as { answer: string; source: string };
      setAnswer(body.answer);
      setAnswerSource(body.source);
    } catch {
      setError("The API isn't running. Start the backend, then try again.");
    } finally {
      setBusy(false);
    }
  }

  async function pullFromBank(publicToken: string) {
    setView("pulling");
    setError(null);
    setLinkNotice(null);
    try {
      const response = await requestAutopsy("/api/plaid/exchange", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ public_token: publicToken }),
      });
      if (!response.ok) {
        setLinkNotice(await readError(response));
        setView("welcome");
        return;
      }
      setReport((await response.json()) as AutopsyResponse);
      setAnswer(null);
      setAnswerSource(null);
      setView("report");
    } catch {
      setLinkNotice("The API isn't running. Start the backend, then try again.");
      setView("welcome");
    }
  }

  if (view === "pulling") {
    return <PullingDetails />;
  }

  async function openSample() {
    setView("report");
    setLoading(true);
    await loadSample();
    setLoading(false);
  }

  if (view === "welcome") {
    return (
      <SignIntoBank onPublicToken={(publicToken) => void pullFromBank(publicToken)}>
        {({ start, busy: opening, error: linkError }) => (
          <LandingPage
            onBegin={start}
            onSample={() => void openSample()}
            beginBusy={opening}
            error={linkError ?? linkNotice}
          />
        )}
      </SignIntoBank>
    );
  }

  if (loading) {
    return <Shell><p className="text-muted-foreground">Looking through the transactions…</p></Shell>;
  }

  if (!report) {
    return (
      <Shell>
        <p className="font-serif text-4xl leading-tight tracking-tight">
          {error ?? "Nothing loaded yet."}
        </p>
        <Button className="mt-8" onClick={() => void load()} disabled={busy}>
          Try again
        </Button>
      </Shell>
    );
  }

  if (report.empty) {
    return (
      <Shell>
        <p className="font-serif text-4xl leading-tight tracking-tight">Nothing to examine yet.</p>
        <p className="mt-4 max-w-xl text-muted-foreground">
          Load a sample month, or import a CSV with date, merchant, amount, and category. Spending amounts should be negative.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Button onClick={() => void loadSample()} disabled={busy}>
            {busy ? "Loading…" : "Load sample transactions"}
          </Button>
          <CsvButton disabled={busy} onFile={(file) => void importCsv(file)} />
        </div>
        {error ? <p className="mt-6 text-sm text-red-800">{error}</p> : null}
      </Shell>
    );
  }

  const largest = Math.max(...report.categories.map((row) => Number(row.amount)), 1);

  return (
    <Shell>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <p className="text-sm text-muted-foreground">{report.month_label}</p>
        <div className="flex flex-wrap gap-2">
          {report.available_months.map((month) => (
            <Button
              key={month}
              size="sm"
              variant={month === report.month ? "default" : "outline"}
              onClick={() => void load(month)}
            >
              {shortMonth(month)}
            </Button>
          ))}
        </div>
      </div>

      <h1 className="mt-8 font-serif text-4xl leading-tight tracking-tight text-balance sm:text-5xl">
        {report.narrative}
      </h1>

      <dl className="mt-8 grid grid-cols-3 gap-4 border-y border-border py-5">
        <Figure label="Income" value={report.income} />
        <Figure label="Spent" value={report.spending} />
        <Figure label="Left" value={report.remaining} />
      </dl>

      <section className="mt-10">
        <h2 className="text-sm font-medium text-muted-foreground">Where it went</h2>
        <ul className="mt-4 space-y-4">
          {report.categories.map((row) => (
            <li key={row.category}>
              <div className="flex items-baseline justify-between gap-4 text-sm">
                <span>{row.category}</span>
                <span className="tabular-nums">
                  {formatMoney(row.amount)}
                  {row.delta && Number(row.delta) !== 0 ? (
                    <span className="ml-2 text-muted-foreground">
                      {Number(row.delta) > 0 ? "+" : "−"}
                      {formatMoney(String(Math.abs(Number(row.delta))))}
                    </span>
                  ) : null}
                </span>
              </div>
              <div className="mt-2 h-1.5 rounded-full bg-muted">
                <div
                  className="h-1.5 rounded-full bg-foreground"
                  style={{ width: `${(Number(row.amount) / largest) * 100}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      </section>

      <Card className="mt-12">
        <CardHeader>
          <h2 className="font-serif text-2xl">Subscription autopsy</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {report.subscriptions.count} recurring charges · {formatMoney(report.subscriptions.monthly_cost)} a month ·{" "}
            {formatMoney(report.subscriptions.annual_cost)} a year
          </p>
        </CardHeader>
        <CardContent>
          <ul className="divide-y divide-border">
            {report.subscriptions.items.map((item) => (
              <SubscriptionRow key={item.merchant} item={item} />
            ))}
            {report.subscriptions.possible_new.map((item) => (
              <SubscriptionRow key={item.merchant} item={item} />
            ))}
          </ul>
        </CardContent>
      </Card>

      <form className="mt-12" onSubmit={(event) => void ask(event)}>
        <label htmlFor="question" className="text-sm font-medium text-muted-foreground">
          Ask about this month
        </label>
        <div className="mt-3 flex flex-col gap-3 sm:flex-row">
          <Input
            id="question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Why did I spend so much?"
          />
          <Button type="submit" disabled={busy || !question.trim()}>
            {busy ? "Looking…" : "Explain"}
          </Button>
        </div>
        {answer ? (
          <div className="mt-6">
            <p className="font-serif text-2xl leading-snug">{answer}</p>
            {answerSource === "calculated" ? (
              <p className="mt-3 text-sm text-muted-foreground">
                Calculated from your transactions. Add an API key when you want a model to explain these numbers.
              </p>
            ) : null}
          </div>
        ) : null}
      </form>

      <div className="mt-10 flex flex-wrap items-center gap-3">
        <Button variant="outline" onClick={() => void loadSample()} disabled={busy}>
          Reload sample
        </Button>
        <CsvButton disabled={busy} onFile={(file) => void importCsv(file)} />
      </div>
      {error ? <p className="mt-6 text-sm text-red-800">{error}</p> : null}
    </Shell>
  );
}

const PULL_STEPS = [
  "Pulling your details",
  "Reading what came in and what went out",
  "Putting the month together",
];

function PullingDetails() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStep((current) => (current + 1) % PULL_STEPS.length);
    }, 1400);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="fa-page">
      <div className="blob blob-1" />
      <div className="fa-container">
        <h1 className="gold-text" style={{ fontSize: "clamp(40px, 6vw, 68px)", fontWeight: 800, letterSpacing: "-0.045em", margin: 0 }}>
          {PULL_STEPS[step]}
        </h1>
        <p className="lead">This part reads the transactions, then explains them.</p>
      </div>
    </div>
  );
}

function Shell({ children }: { children: ReactNode }) {
  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-14">
      <p className="text-xs tracking-[0.18em] text-muted-foreground uppercase">Financial Autopsy</p>
      <div className="mt-6">{children}</div>
    </main>
  );
}

function Figure({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="mt-1 text-lg tabular-nums">{formatMoney(value)}</dd>
    </div>
  );
}

function SubscriptionRow({ item }: { item: SubscriptionItem }) {
  return (
    <li className="flex items-start justify-between gap-4 py-4 first:pt-0 last:pb-0">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <p>{item.merchant}</p>
          {item.flags.includes("price_increase") ? <Badge>Price up</Badge> : null}
          {item.flags.includes("possible_new") || item.flags.includes("new") ? <Badge>New</Badge> : null}
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Since {monthYear(item.first_seen)} · {formatMoney(item.total_spent)} total
          {item.previous_amount ? ` · was ${formatMoney(item.previous_amount)}` : ""}
        </p>
      </div>
      <p className="shrink-0 tabular-nums">{formatMoney(item.monthly_amount)}/mo</p>
    </li>
  );
}

function CsvButton({ disabled, onFile }: { disabled: boolean; onFile: (file: File) => void }) {
  return (
    <label className="inline-flex h-10 cursor-pointer items-center rounded-full border border-border bg-card px-4 text-sm hover:bg-accent">
      Import CSV
      <input
        className="sr-only"
        type="file"
        accept=".csv,text/csv"
        disabled={disabled}
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onFile(file);
          event.target.value = "";
        }}
      />
    </label>
  );
}

function formatMoney(value: string) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(Number(value));
}

function shortMonth(month: string) {
  const [year, monthNumber] = month.split("-").map(Number);
  const name = new Date(year, monthNumber - 1, 1).toLocaleDateString("en-US", { month: "short" });
  return `${name} ${year}`;
}

function monthYear(iso: string) {
  const [year, monthNumber] = iso.split("-").map(Number);
  return new Date(year, monthNumber - 1, 1).toLocaleDateString("en-US", { month: "long", year: "numeric" });
}
