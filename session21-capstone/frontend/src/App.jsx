import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api.js";
import Sidebar from "./components/Sidebar.jsx";
import KpiCards from "./components/KpiCards.jsx";
import CategoryBars from "./components/CategoryBars.jsx";
import ProductTable from "./components/ProductTable.jsx";
import ProductModal from "./components/ProductModal.jsx";
import AdjustModal from "./components/AdjustModal.jsx";
import ActivityFeed from "./components/ActivityFeed.jsx";

const STATUS_FILTERS = [
  { id: "all", label: "All" },
  { id: "low", label: "Low stock" },
  { id: "ok", label: "Healthy" },
];

export default function App() {
  const [products, setProducts] = useState([]);
  const [stats, setStats] = useState(null);
  const [movements, setMovements] = useState([]);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modal, setModal] = useState(null); // {type: "product"|"adjust", product?}
  const [toast, setToast] = useState("");

  // Debounce the search box so typing does not fire a request per keystroke.
  useEffect(() => {
    const t = setTimeout(() => setQuery(search.trim()), 250);
    return () => clearTimeout(t);
  }, [search]);

  const load = useCallback(async () => {
    try {
      const lowStock = status === "all" ? "" : status === "low";
      const [p, s, m] = await Promise.all([
        api.products({ q: query, category, low_stock: lowStock }),
        api.stats(),
        api.movements(),
      ]);
      setProducts(p);
      setStats(s);
      setMovements(m);
      setError("");
    } catch (e) {
      setError(e.message || "Backend unreachable");
    } finally {
      setLoading(false);
    }
  }, [query, category, status]);

  useEffect(() => {
    load();
  }, [load]);

  const categories = useMemo(() => (stats?.by_category || []).map((c) => c.category), [stats]);

  const notify = (message) => {
    setToast(message);
    setTimeout(() => setToast(""), 2600);
  };

  const handleSaved = (message) => {
    setModal(null);
    notify(message);
    load();
  };

  const handleDelete = async (product) => {
    if (!window.confirm(`Delete ${product.name} (${product.sku}) and its stock history?`)) return;
    try {
      await api.remove(product.id);
      notify(`Deleted ${product.sku}`);
      load();
    } catch (e) {
      notify(`Delete failed: ${e.message}`);
    }
  };

  return (
    <div className="shell">
      <Sidebar lowStock={stats?.low_stock ?? 0} />
      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">Warehouse · Main store</p>
            <h1>Inventory overview</h1>
          </div>
          <div className="topbar-actions">
            <input
              className="search"
              type="search"
              placeholder="Search name or SKU…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search products"
            />
            <button className="btn btn-primary" onClick={() => setModal({ type: "product" })}>
              + Add product
            </button>
          </div>
        </header>

        {error && (
          <div className="banner banner-error" role="alert">
            <strong>Cannot reach the API.</strong> {error}
            <button className="btn btn-ghost" onClick={load}>Retry</button>
          </div>
        )}

        <KpiCards stats={stats} loading={loading} />

        <div className="grid">
          <section className="card table-card" id="products">
            <div className="card-head">
              <h2>Products</h2>
              <div className="filters">
                <div className="chips" role="group" aria-label="Stock status">
                  {STATUS_FILTERS.map((f) => (
                    <button
                      key={f.id}
                      className={`chip ${status === f.id ? "chip-active" : ""}`}
                      onClick={() => setStatus(f.id)}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
                <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Category">
                  <option value="">All categories</option>
                  {categories.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>
            <ProductTable
              products={products}
              loading={loading}
              onEdit={(p) => setModal({ type: "product", product: p })}
              onAdjust={(p) => setModal({ type: "adjust", product: p })}
              onDelete={handleDelete}
            />
          </section>

          <aside className="side-col">
            <CategoryBars stats={stats} />
            <ActivityFeed movements={movements} />
          </aside>
        </div>
      </main>

      {modal?.type === "product" && (
        <ProductModal
          product={modal.product}
          categories={categories}
          onClose={() => setModal(null)}
          onSaved={handleSaved}
        />
      )}
      {modal?.type === "adjust" && (
        <AdjustModal product={modal.product} onClose={() => setModal(null)} onSaved={handleSaved} />
      )}
      {toast && <div className="toast" role="status">{toast}</div>}
    </div>
  );
}
