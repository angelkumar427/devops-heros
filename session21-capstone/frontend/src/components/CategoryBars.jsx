import { money } from "../api.js";

export default function CategoryBars({ stats }) {
  const rows = stats?.by_category || [];
  const max = Math.max(1, ...rows.map((r) => Number(r.value)));
  return (
    <section className="card" id="categories">
      <h2>Value by category</h2>
      {rows.length === 0 && <p className="muted">No products yet.</p>}
      <ul className="bars">
        {rows.map((r) => (
          <li key={r.category}>
            <div className="bar-label">
              <span>{r.category}</span>
              <span className="muted">{money.format(Number(r.value))}</span>
            </div>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${(Number(r.value) / max) * 100}%` }} />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
