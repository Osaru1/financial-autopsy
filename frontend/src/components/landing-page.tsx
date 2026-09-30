"use client";

import { FormEvent, ReactNode, useEffect, useState } from "react";
import "./LandingPage.css";

type Qa = { label: string; answer: string };

const SAMPLE_QA: Qa[] = [
  {
    label: "Why am I broke by the 20th?",
    answer:
      "Two things hit at once. Your rent leaves on the 1st, and 68% of your delivery orders land between the 14th and 20th.\n\nMoving your streaming renewals to payday and capping delivery at 2 a week gets you to month-end with about $190 left.",
  },
  {
    label: "What can I cancel today?",
    answer:
      "Three charges you haven’t used in 60+ days:\n• Fitness club — $54.99\n• Streaming service #3 — $17.99\n• Duplicate cloud storage — $9.99\n\nThat’s $83 a month back, or $996 a year.",
  },
  {
    label: "Am I doing better than August?",
    answer:
      "Yes, slightly. Spending is down 6% from August, mostly shopping.\n\nBut subscriptions went up $24 — a free trial quietly turned into a paid plan on Sep 11.",
  },
];

async function askExaminer(question: string) {
  return `(Demo) You asked: “${question}”. Connect askExaminer() to your AI backend to answer this for real.`;
}

function useTypewriter(text: string, speed = 22) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    setCount(0);
    const id = setInterval(() => {
      setCount((current) => {
        if (current >= text.length) {
          clearInterval(id);
          return current;
        }
        return Math.min(text.length, current + 2);
      });
    }, speed);
    return () => clearInterval(id);
  }, [text, speed]);
  return { shown: text.slice(0, count), typing: count < text.length };
}

function Icon({
  path,
  size = 22,
  stroke = "#E9C96B",
  width = 1.8,
  children,
}: {
  path?: string;
  size?: number;
  stroke?: string;
  width?: number;
  children?: ReactNode;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={stroke}
      strokeWidth={width}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {path ? <path d={path} /> : null}
      {children}
    </svg>
  );
}

const PULSE = "M3 12h4l2-5 4 10 2-5h6";

function GoldCoin() {
  const edges: [string, number][] = [
    ["#8C6A18", -7],
    ["#9C7A1E", -5],
    ["#A8841F", -3],
    ["#B08A22", -1],
    ["#B08A22", 1],
    ["#A8841F", 3],
    ["#9C7A1E", 5],
  ];
  return (
    <div className="coin-stage">
      <div className="coin-halo" />
      <div className="coin-shadow" />
      <div className="coin-float">
        <div className="coin">
          {edges.map(([color, z], index) => (
            <div key={index} className="coin-edge" style={{ background: color, transform: `translateZ(${z}px)` }} />
          ))}
          <div className="coin-face coin-front">
            <div className="coin-ring">
              <div className="coin-letter">A</div>
              <div className="coin-word">AUTOPSY</div>
            </div>
            <div className="coin-shine" />
          </div>
          <div className="coin-face coin-back">
            <Icon path={PULSE} size={96} stroke="#7A5C12" width={1.6} />
            <div className="coin-shine" />
          </div>
        </div>
      </div>

      <div className="glass-chip chip-a">
        <span className="chip-label">Subscriptions</span>
        <span className="chip-value loss">−$412/mo</span>
      </div>
      <div className="glass-chip chip-b gold-border">
        <span className="chip-label">You could save</span>
        <span className="chip-value gain">+$286/mo</span>
      </div>
      <div className="glass-chip chip-c pill">
        <span className="live-dot" />
        214 transactions scanned
      </div>
    </div>
  );
}

function AIExaminer() {
  const [current, setCurrent] = useState<Qa>(SAMPLE_QA[0]);
  const [input, setInput] = useState("");
  const { shown, typing } = useTypewriter(current.answer);

  async function send(event: FormEvent) {
    event.preventDefault();
    const question = input.trim();
    if (!question) {
      const index = SAMPLE_QA.findIndex((item) => item.label === current.label);
      setCurrent(SAMPLE_QA[(index + 1) % SAMPLE_QA.length]);
      return;
    }
    setInput("");
    setCurrent({ label: question, answer: "…" });
    const answer = await askExaminer(question);
    setCurrent({ label: question, answer });
  }

  return (
    <div className="examiner glass">
      <div className="examiner-head">
        <div className="ai-orb" />
        <div>
          <div className="examiner-name">Examiner</div>
          <div className="examiner-status">Reviewing Case #0427</div>
        </div>
      </div>

      <div className="messages" aria-live="polite">
        <div key={`q-${current.label}`} className="msg msg-user">
          {current.label}
        </div>
        <div key={`a-${current.label}`} className="msg msg-ai">
          {shown}
          {typing ? <span className="cursor" /> : null}
        </div>
      </div>

      <div className="chips">
        {SAMPLE_QA.map((item) => (
          <button
            key={item.label}
            type="button"
            className={`chip ${item.label === current.label ? "active" : ""}`}
            onClick={() => setCurrent(item)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <form className="ask-bar" onSubmit={(event) => void send(event)}>
        <label htmlFor="ask" className="sr-only">
          Ask the Examiner
        </label>
        <input
          id="ask"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask about your spending…"
        />
        <button type="submit" className="send-btn" aria-label="Send">
          <Icon path="M12 19V5M5 12l7-7 7 7" size={18} stroke="#1A1406" width={2} />
        </button>
      </form>
    </div>
  );
}

const STEPS = [
  {
    title: "Upload",
    text: "Drop in a bank statement or CSV. Nothing is shared or sold.",
    icon: <Icon path="M12 16V4M7 9l5-5 5 5M5 20h14" />,
  },
  {
    title: "Examine",
    text: "AI sorts every charge and traces it back to a habit.",
    icon: (
      <Icon path="M20 20l-4.5-4.5">
        <circle cx="11" cy="11" r="6" />
      </Icon>
    ),
  },
  {
    title: "Recover",
    text: "Get a plain-language plan to win back what you're losing.",
    icon: <Icon path={PULSE} />,
  },
];

export function LandingPage({
  onBegin,
  onSample,
  beginBusy = false,
  error,
}: {
  onBegin: () => void;
  onSample: () => void;
  beginBusy?: boolean;
  error?: string | null;
}) {
  function begin(event: { preventDefault: () => void }) {
    event.preventDefault();
    if (!beginBusy) onBegin();
  }

  function sample(event: { preventDefault: () => void }) {
    event.preventDefault();
    onSample();
  }

  return (
    <div className="fa-page">
      <div className="blob blob-1" />
      <div className="blob blob-2" />

      <div className="fa-container">
        <nav className="fa-nav">
          <div className="brand">
            <div className="brand-coin" />
            <span>Financial Autopsy</span>
          </div>
          <div className="nav-links">
            <a href="#ai">AI Examiner</a>
            <a href="#report" onClick={sample}>
              Sample report
            </a>
            <a href="#signin" onClick={begin}>
              Sign in
            </a>
            <a href="#start" className="btn-gold btn-sm" onClick={begin}>
              {beginBusy ? "Opening…" : "Get started"}
            </a>
          </div>
        </nav>

        <section className="hero">
          <div className="hero-copy">
            <div className="badge">
              <Icon path="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" size={14} />
              Powered by AI
            </div>
            <h1>
              Find out what <span className="gold-text">killed</span> your budget.
            </h1>
            <p className="lead">
              Upload your statements. Our AI examines every transaction, names the cause of death, and writes you a
              plan to bring your money back to life.
            </p>
            <div className="cta-row">
              <a href="#start" className="btn-gold" onClick={begin}>
                {beginBusy ? "Opening Plaid…" : "Begin examination"}
              </a>
              <a href="#report" className="btn-glass" onClick={sample}>
                See a sample report
              </a>
            </div>
            {error ? <p className="landing-error">{error}</p> : null}
          </div>
          <GoldCoin />
        </section>

        <section id="ai" className="ai-section">
          <div className="ai-copy">
            <div className="eyebrow">AI Examiner</div>
            <h2>Ask your money anything.</h2>
            <p className="lead small">
              The Examiner has read every transaction. Ask why you&apos;re always broke by the 20th and get a straight
              answer, not a pie chart.
            </p>
            <p className="fine">Try a question on the right. Answers are sample data.</p>
          </div>
          <AIExaminer />
        </section>

        <section className="steps">
          <h2>Three steps. No spreadsheets.</h2>
          <div className="step-row">
            {STEPS.map((step) => (
              <div key={step.title} className="step-card">
                <div className="step-icon">{step.icon}</div>
                <div className="step-title">{step.title}</div>
                <p>{step.text}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
