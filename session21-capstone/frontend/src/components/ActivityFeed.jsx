const timeAgo = (iso) => {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return new Date(iso).toLocaleDateString("en-IN");
};

export default function ActivityFeed({ movements }) {
  return (
    <section className="card" id="activity">
      <h2>Stock activity</h2>
      {movements.length === 0 && <p className="muted">No stock movements yet.</p>}
      <ul className="feed">
        {movements.map((m) => (
          <li key={m.id}>
            <span className={`delta ${m.change > 0 ? "delta-in" : "delta-out"}`}>
              {m.change > 0 ? `+${m.change}` : m.change}
            </span>
            <div className="feed-body">
              <span className="feed-title">{m.product_name}</span>
              <span className="muted">
                {m.reason} · {m.quantity_after} left · {timeAgo(m.created_at)}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
