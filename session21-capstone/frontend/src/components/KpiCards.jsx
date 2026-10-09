import { money, number } from "../api.js";

export default function KpiCards({ stats, loading }) {
  const cards = [
    { label: "Products", value: stats ? number.format(stats.total_products) : "–", hint: "in catalogue" },
    { label: "Units in stock", value: stats ? number.format(stats.total_units) : "–", hint: "across all products" },
    { label: "Inventory value", value: stats ? money.format(Number(stats.inventory_value)) : "–", hint: "at unit cost" },
    {
      label: "Need reorder",
      value: stats ? number.format(stats.low_stock) : "–",
      hint: stats ? `${stats.out_of_stock} out of stock` : "",
      tone: stats?.low_stock ? "warn" : "ok",
    },
  ];
  return (
    <section className={`kpis ${loading ? "is-loading" : ""}`} aria-label="Key figures">
      {cards.map((c) => (
        <div key={c.label} className={`kpi ${c.tone ? `kpi-${c.tone}` : ""}`}>
          <span className="kpi-label">{c.label}</span>
          <strong className="kpi-value">{c.value}</strong>
          <span className="kpi-hint">{c.hint}</span>
        </div>
      ))}
    </section>
  );
}
