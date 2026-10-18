"use client";
import { useState } from "react";
import { formatEther } from "ethers";
export type Day = {
  date: string;
  deposits: string;
  withdrawals: string;
  interest: string;
  funding: string;
  count: number;
};
export type Analytics = { basis: string; scope: string; days: Day[] };
const series = [
  { key: "deposits", label: "Deposits", color: "#24594a" },
  { key: "withdrawals", label: "Withdrawals", color: "#b77943" },
  { key: "interest", label: "Interest paid", color: "#607db0" },
  { key: "funding", label: "Reserve funding", color: "#8b8754" },
] as const;
export default function ActivityChart({ data }: { data: Analytics | null }) {
  const [selected, setSelected] =
    useState<(typeof series)[number]["key"]>("deposits");
  const days = data?.days || [];
  const current = series.find((s) => s.key === selected)!;
  const max = days.reduce(
    (m, d) => (BigInt(d[selected]) > m ? BigInt(d[selected]) : m),
    0n,
  );
  const total = days.reduce((n, d) => n + BigInt(d[selected]), 0n);
  return (
    <section className="panel chart-panel" aria-labelledby="chart-heading">
      <div className="section-heading">
        <div>
          <div className="eyebrow">THE LAST 14 DAYS · UTC</div>
          <h2 id="chart-heading">Your activity, in perspective.</h2>
          <p>
            {data?.scope === "all_accounts"
              ? "Across all accounts"
              : "Your account"}{" "}
            · grouped by when events were recorded, not block time.
          </p>
        </div>
        <div className="chart-total">
          <strong>{formatEther(total)} ETH</strong>
          <small>{current.label.toLowerCase()} recorded</small>
        </div>
      </div>
      <div className="chart-tabs" aria-label="Activity series">
        {series.map((s) => (
          <button
            key={s.key}
            className={selected === s.key ? "chart-tab selected" : "chart-tab"}
            aria-pressed={selected === s.key}
            onClick={() => setSelected(s.key)}
          >
            <i style={{ background: s.color }} />
            {s.label}
          </button>
        ))}
      </div>
      <svg
        className="activity-chart"
        viewBox="0 0 780 190"
        role="img"
        aria-label={`${current.label} by recording date, 14 days. Total ${formatEther(total)} ETH.`}
      >
        {[20, 65, 110, 155].map((y) => (
          <line
            key={y}
            x1="20"
            x2="760"
            y1={y}
            y2={y}
            stroke="#e5eade"
            strokeDasharray="4 5"
          />
        ))}
        {days.map((d, i) => {
          const v = BigInt(d[selected]);
          const height = max > 0n ? Number((v * 135000n) / max) / 1000 : 0;
          return (
            <g key={d.date}>
              <rect
                x={29 + i * 52}
                y={155 - height}
                width="26"
                height={height}
                rx="4"
                fill={current.color}
              >
                <title>
                  {d.date}: {formatEther(v)} ETH
                </title>
              </rect>
              {i % 2 === 0 && (
                <text
                  x={42 + i * 52}
                  y="179"
                  textAnchor="middle"
                  fill="#74817b"
                  fontSize="11"
                >
                  {d.date.slice(5)}
                </text>
              )}
            </g>
          );
        })}
        {max === 0n && (
          <text x="390" y="88" textAnchor="middle" fill="#74817b" fontSize="14">
            No {current.label.toLowerCase()} recorded in this period
          </text>
        )}
      </svg>
      <details className="chart-details">
        <summary>View accessible data table</summary>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Recording date (UTC)</th>
                <th>{current.label} (ETH)</th>
                <th>Events, all types</th>
              </tr>
            </thead>
            <tbody>
              {days.map((d) => (
                <tr key={d.date}>
                  <td>{d.date}</td>
                  <td>{formatEther(d[selected])}</td>
                  <td>{d.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
}
