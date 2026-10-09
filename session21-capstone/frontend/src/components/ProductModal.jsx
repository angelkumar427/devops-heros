import { useState } from "react";
import { api } from "../api.js";
import Modal from "./Modal.jsx";

const EMPTY = { sku: "", name: "", category: "", quantity: 0, reorder_level: 10, unit_price: "" };

export default function ProductModal({ product, categories, onClose, onSaved }) {
  const editing = Boolean(product);
  const [form, setForm] = useState(editing ? { ...product } : EMPTY);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    const common = {
      name: form.name.trim(),
      category: form.category.trim(),
      reorder_level: Number(form.reorder_level),
      unit_price: String(form.unit_price),
    };
    try {
      if (editing) {
        await api.update(product.id, common);
        onSaved(`Updated ${product.sku}`);
      } else {
        await api.create({ ...common, sku: form.sku.trim().toUpperCase(), quantity: Number(form.quantity) });
        onSaved(`Added ${form.sku.toUpperCase()}`);
      }
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  };

  return (
    <Modal title={editing ? `Edit ${product.sku}` : "Add product"} onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <div className="form-row">
          <label>
            SKU
            <input value={form.sku} onChange={set("sku")} required disabled={editing} placeholder="CAB-USBC-1M" />
          </label>
          <label>
            Category
            <input value={form.category} onChange={set("category")} required list="categories" placeholder="Cables" />
            <datalist id="categories">{categories.map((c) => <option key={c} value={c} />)}</datalist>
          </label>
        </div>
        <label>
          Name
          <input value={form.name} onChange={set("name")} required maxLength={120} placeholder="USB-C cable, 1 m" />
        </label>
        <div className="form-row">
          {!editing && (
            <label>
              Opening stock
              <input type="number" min="0" value={form.quantity} onChange={set("quantity")} required />
            </label>
          )}
          <label>
            Reorder at
            <input type="number" min="0" value={form.reorder_level} onChange={set("reorder_level")} required />
          </label>
          <label>
            Unit price (₹)
            <input type="number" min="0" step="0.01" value={form.unit_price} onChange={set("unit_price")} required />
          </label>
        </div>
        {editing && <p className="muted small">Stock on hand changes through “Adjust”, so every change is recorded.</p>}
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="form-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" disabled={saving}>{saving ? "Saving…" : editing ? "Save changes" : "Add product"}</button>
        </div>
      </form>
    </Modal>
  );
}
