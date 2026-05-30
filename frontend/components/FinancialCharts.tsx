import { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Line, ComposedChart, Cell
} from "recharts";

interface Props {
  data: any;
  chartUrls?: Record<string, string>;
  apiUrl: string;
}

const COLORS = {
  actual:   "#1B5E9B",
  estimate: "#4A90D9",
  line:     "#E8A020",
};

function buildChartData(series: Array<{ year: string; value: number | null }>) {
  if (!series) return [];
  const values = series.map(s => Number(s.value) || 0);
  return series.map((item, i) => {
    const prev = i > 0 ? values[i - 1] : null;
    const growth = prev && prev !== 0
      ? parseFloat(((values[i] - prev) / Math.abs(prev) * 100).toFixed(1))
      : null;
    return {
      year:     item.year,
      value:    Number(item.value) || 0,
      growth,
      isEst:    item.year?.includes("E") || item.year?.includes("e"),
    };
  });
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-geojit-border rounded-lg px-3 py-2 shadow text-xs">
      <div className="font-bold text-gray-700 mb-1">{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} className="flex justify-between gap-4">
          <span style={{ color: p.color }}>{p.name}</span>
          <span className="font-semibold">
            {p.name === "Growth %" ? `${p.value}%` : `₹${p.value?.toLocaleString("en-IN")}`}
          </span>
        </div>
      ))}
    </div>
  );
};

function ChartPanel({
  title, series, color, unit = "Rs. Cr", imgUrl
}: {
  title: string;
  series: any[];
  color: string;
  unit?: string;
  imgUrl?: string;
}) {
  const [showBackend, setShowBackend] = useState(false);
  const chartData = buildChartData(series);
  const hasData = chartData.some(d => d.value !== 0);

  return (
    <div className="bg-white rounded-xl border border-geojit-border p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-geojit-blue">{title}</h3>
        {imgUrl && (
          <button
            onClick={() => setShowBackend(v => !v)}
            className="text-[10px] text-gray-400 hover:text-geojit-blue transition-colors"
          >
            {showBackend ? "Interactive" : "Report View"}
          </button>
        )}
      </div>

      {showBackend && imgUrl ? (
        // Backend-generated chart image
        <img
          src={imgUrl}
          alt={title}
          className="w-full h-auto rounded"
        />
      ) : !hasData ? (
        <div className="h-40 flex items-center justify-center text-gray-300 text-sm">
          No data available
        </div>
      ) : (
        // Interactive Recharts
        <ResponsiveContainer width="100%" height={180}>
          <ComposedChart data={chartData} margin={{ top: 5, right: 30, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="year" tick={{ fontSize: 10 }} />
            <YAxis yAxisId="left" tick={{ fontSize: 10 }} tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10, fill: COLORS.line }}
                   tickFormatter={v => `${v}%`} />
            <Tooltip content={<CustomTooltip />} />
            <Bar yAxisId="left" dataKey="value" name={unit} radius={[3, 3, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.isEst ? COLORS.estimate : COLORS.actual}
                />
              ))}
            </Bar>
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="growth"
              name="Growth %"
              stroke={COLORS.line}
              strokeWidth={2}
              dot={{ r: 3, fill: COLORS.line }}
              connectNulls
            />
          </ComposedChart>
        </ResponsiveContainer>
      )}

      {/* Legend */}
      <div className="flex gap-4 mt-2 justify-center">
        <div className="flex items-center gap-1 text-[10px] text-gray-500">
          <span className="w-3 h-3 rounded-sm inline-block" style={{ background: COLORS.actual }} />
          Actual
        </div>
        <div className="flex items-center gap-1 text-[10px] text-gray-500">
          <span className="w-3 h-3 rounded-sm inline-block" style={{ background: COLORS.estimate }} />
          Estimate
        </div>
        <div className="flex items-center gap-1 text-[10px] text-gray-500">
          <span className="w-6 h-0.5 inline-block" style={{ background: COLORS.line }} />
          YoY Growth
        </div>
      </div>
    </div>
  );
}

export default function FinancialCharts({ data, chartUrls, apiUrl }: Props) {
  const getImgUrl = (key: string) => {
    if (!chartUrls?.[key]) return undefined;
    return `${apiUrl}${chartUrls[key]}`;
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <h2 className="text-sm font-bold text-gray-700 uppercase tracking-wide">
          Financial Performance Charts
        </h2>
        <div className="flex-1 h-px bg-geojit-border" />
        <span className="text-[10px] text-gray-400">Click "Report View" for PDF-quality chart</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ChartPanel
          title="Revenue (Rs. Cr)"
          series={data.revenue}
          color={COLORS.actual}
          imgUrl={getImgUrl("revenue")}
        />
        <ChartPanel
          title="EBITDA (Rs. Cr)"
          series={data.ebitda}
          color={COLORS.actual}
          imgUrl={getImgUrl("ebitda")}
        />
        <ChartPanel
          title="PAT (Rs. Cr)"
          series={data.pat}
          color={COLORS.actual}
          imgUrl={getImgUrl("pat")}
        />
      </div>
    </div>
  );
}
