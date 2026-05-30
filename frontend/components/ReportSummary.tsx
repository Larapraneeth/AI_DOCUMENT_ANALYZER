import { TrendingUp, Target, DollarSign, Building2, BarChart2, Percent } from "lucide-react";

interface Props {
  data: any;
}

function MetricCard({
  label, value, sub, accent, icon: Icon
}: {
  label: string;
  value: string | number | null;
  sub?: string;
  accent?: string;
  icon: React.ElementType;
}) {
  return (
    <div className="bg-white rounded-xl border border-geojit-border p-4 shadow-sm flex items-start gap-3">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${accent || "bg-geojit-bg"}`}>
        <Icon size={18} className="text-geojit-blue" />
      </div>
      <div>
        <div className="text-xs text-gray-500 font-medium">{label}</div>
        <div className="text-lg font-black text-gray-900 leading-tight">
          {value ?? "N/A"}
        </div>
        {sub && <div className="text-[11px] text-gray-400 mt-0.5">{sub}</div>}
      </div>
    </div>
  );
}

function RatingCard({ rating }: { rating: string }) {
  const styles: Record<string, string> = {
    BUY:       "bg-green-50 border-green-300 text-green-800",
    ACCUMULATE:"bg-green-50 border-green-300 text-green-700",
    HOLD:      "bg-blue-50 border-blue-300 text-blue-800",
    NEUTRAL:   "bg-gray-50 border-gray-300 text-gray-700",
    REDUCE:    "bg-orange-50 border-orange-300 text-orange-700",
    SELL:      "bg-red-50 border-red-300 text-red-800",
  };
  const cls = styles[rating?.toUpperCase()] || styles.NEUTRAL;
  return (
    <div className={`bg-white rounded-xl border p-4 shadow-sm flex items-center justify-center ${cls}`}>
      <div className="text-center">
        <div className="text-xs font-medium opacity-70 mb-1">Recommendation</div>
        <div className="text-2xl font-black tracking-wide">{rating || "N/A"}</div>
      </div>
    </div>
  );
}

export default function ReportSummary({ data }: Props) {
  const ret = data.expected_return_pct
    ? `+${data.expected_return_pct}%`
    : null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-5">
      <RatingCard rating={data.rating} />

      <MetricCard
        label="Target Price"
        value={data.target_price ? `Rs. ${data.target_price}` : null}
        sub={data.time_frame}
        icon={Target}
        accent="bg-blue-50"
      />
      <MetricCard
        label="CMP"
        value={data.cmp ? `Rs. ${data.cmp}` : null}
        sub="Current Market Price"
        icon={DollarSign}
        accent="bg-blue-50"
      />
      <MetricCard
        label="Expected Return"
        value={ret}
        sub="Upside potential"
        icon={TrendingUp}
        accent="bg-green-50"
      />
      <MetricCard
        label="Market Cap"
        value={data.market_cap}
        sub={data.stock_type}
        icon={Building2}
        accent="bg-purple-50"
      />
      <MetricCard
        label="Sector"
        value={data.sector}
        sub={data.bloomberg_code}
        icon={BarChart2}
        accent="bg-orange-50"
      />
    </div>
  );
}
