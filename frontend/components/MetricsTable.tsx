interface Props {
  data: any;
}

function fmt(v: number | null | undefined, dec = 0): string {
  if (v === null || v === undefined) return "—";
  return Number(v).toLocaleString("en-IN", { maximumFractionDigits: dec });
}

function fmtPct(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return `${Number(v).toFixed(1)}%`;
}

export default function MetricsTable({ data }: Props) {
  const years = (data.revenue || []).map((r: any) => r.year);

  const getValue = (series: any[], i: number) => {
    return series?.[i]?.value ?? null;
  };

  return (
    <div className="mt-5">
      <div className="flex items-center gap-2 mb-3">
        <h2 className="text-sm font-bold text-gray-700 uppercase tracking-wide">
          Annual Financial Summary
        </h2>
        <div className="flex-1 h-px bg-geojit-border" />
      </div>

      <div className="bg-white rounded-xl border border-geojit-border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-geojit-blue text-white">
                <th className="text-left px-4 py-2.5 font-semibold">Metric</th>
                {years.map((y: string) => (
                  <th key={y} className="px-4 py-2.5 font-semibold text-center">
                    {y}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {/* Revenue */}
              <tr className="hover:bg-geojit-bg/50 transition-colors">
                <td className="px-4 py-2 font-semibold text-gray-700 bg-gray-50/60">
                  Revenue (Rs. Cr)
                </td>
                {years.map((_: string, i: number) => (
                  <td key={i} className="px-4 py-2 text-center font-mono">
                    {fmt(getValue(data.revenue, i))}
                  </td>
                ))}
              </tr>

              {/* EBITDA */}
              <tr className="hover:bg-geojit-bg/50 transition-colors">
                <td className="px-4 py-2 font-semibold text-gray-700 bg-gray-50/60">
                  EBITDA (Rs. Cr)
                </td>
                {years.map((_: string, i: number) => (
                  <td key={i} className="px-4 py-2 text-center font-mono">
                    {fmt(getValue(data.ebitda, i))}
                  </td>
                ))}
              </tr>

              {/* EBITDA Margin */}
              <tr className="hover:bg-geojit-bg/50 transition-colors">
                <td className="px-4 py-2 font-semibold text-gray-700 bg-gray-50/60">
                  EBITDA Margin
                </td>
                {years.map((_: string, i: number) => (
                  <td key={i} className="px-4 py-2 text-center font-mono text-geojit-blue">
                    {fmtPct(getValue(data.ebitda_margin, i))}
                  </td>
                ))}
              </tr>

              {/* PAT */}
              <tr className="hover:bg-geojit-bg/50 transition-colors">
                <td className="px-4 py-2 font-semibold text-gray-700 bg-gray-50/60">
                  PAT (Rs. Cr)
                </td>
                {years.map((_: string, i: number) => (
                  <td key={i} className="px-4 py-2 text-center font-mono">
                    {fmt(getValue(data.pat, i))}
                  </td>
                ))}
              </tr>

              {/* EPS */}
              <tr className="hover:bg-geojit-bg/50 transition-colors">
                <td className="px-4 py-2 font-semibold text-gray-700 bg-gray-50/60">
                  EPS (Rs.)
                </td>
                {years.map((_: string, i: number) => (
                  <td key={i} className="px-4 py-2 text-center font-mono">
                    {fmt(getValue(data.eps, i), 1)}
                  </td>
                ))}
              </tr>

              {/* PE */}
              <tr className="hover:bg-geojit-bg/50 transition-colors">
                <td className="px-4 py-2 font-semibold text-gray-700 bg-gray-50/60">
                  P/E (x)
                </td>
                {years.map((_: string, i: number) => (
                  <td key={i} className="px-4 py-2 text-center font-mono">
                    {fmt(getValue(data.pe_ratio, i), 1)}
                  </td>
                ))}
              </tr>

              {/* ROE */}
              <tr className="hover:bg-geojit-bg/50 transition-colors">
                <td className="px-4 py-2 font-semibold text-gray-700 bg-gray-50/60">
                  ROE (%)
                </td>
                {years.map((_: string, i: number) => (
                  <td key={i} className="px-4 py-2 text-center font-mono text-geojit-green">
                    {fmtPct(getValue(data.roe, i))}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>

        {/* Quarterly mini-table */}
        {data.quarterly_financials?.sales_current && (
          <div className="border-t border-geojit-border">
            <div className="px-4 py-2 bg-geojit-bg text-xs font-bold text-geojit-blue uppercase tracking-wide">
              Latest Quarter ({data.quarterly_financials.current_quarter})
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="text-left px-4 py-2 font-semibold text-gray-600">Metric</th>
                    <th className="px-4 py-2 text-center font-semibold text-gray-600">Value (Rs. Cr)</th>
                    <th className="px-4 py-2 text-center font-semibold text-gray-600">YoY Growth</th>
                    <th className="px-4 py-2 text-center font-semibold text-gray-600">QoQ Growth</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {[
                    ["Sales", data.quarterly_financials.sales_current, data.quarterly_financials.sales_yoy_growth, data.quarterly_financials.sales_qoq_growth],
                    ["EBITDA", data.quarterly_financials.ebitda_current, data.quarterly_financials.ebitda_yoy_growth, null],
                    ["PAT", data.quarterly_financials.pat_current, data.quarterly_financials.pat_yoy_growth, null],
                    ["EBIT", data.quarterly_financials.ebit_current, null, null],
                    ["PBT", data.quarterly_financials.pbt_current, null, null],
                  ].map(([label, val, yoy, qoq]) => (
                    <tr key={label as string} className="hover:bg-geojit-bg/50 transition-colors">
                      <td className="px-4 py-2 font-medium text-gray-700">{label}</td>
                      <td className="px-4 py-2 text-center font-mono">
                        {val ? fmt(val as number) : "—"}
                      </td>
                      <td className={`px-4 py-2 text-center font-mono font-semibold
                        ${yoy ? (Number(yoy) >= 0 ? "text-geojit-green" : "text-red-600") : "text-gray-400"}`}>
                        {yoy ? `${Number(yoy) >= 0 ? "+" : ""}${yoy}%` : "—"}
                      </td>
                      <td className={`px-4 py-2 text-center font-mono font-semibold
                        ${qoq ? (Number(qoq) >= 0 ? "text-geojit-green" : "text-red-600") : "text-gray-400"}`}>
                        {qoq ? `${Number(qoq) >= 0 ? "+" : ""}${qoq}%` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
