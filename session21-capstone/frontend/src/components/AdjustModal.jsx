import { useState } from "react";
import { api } from "../api.js";
import Modal from "./Modal.jsx";

export default function AdjustModal({ product, onClose, onSaved }) {
  const [direction, setDirection] = useState("in");
  const [amount, setAmount] = useState(1);
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const change = (direction === "in" ? 1 : -1) * Number(amount || 0);
  const after = product.quantity + change;

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.adjust(product.id, { change, reason: reason.trim() || (direction === "in" ? "stock received" : "stock issued") });
      onSaved(`${product.sku}: ${change > 0 ? "+" : ""}${change} → ${after} on hand`);
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  };

  return (
    <Modal title={`Adjust stock · ${product.name}`} onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <div className="segmented" role="group" aria-label="Direction">
          <button type="button" className={direction === "in" ? "on" : ""} onClick={() => setDirection("in")}>Stock in</button>
          <button type="button" className={direction === "out" ? "on" : ""} onClick={() => setDirection("out")}>Stock out</button>
        </div>
        <div className="form-row">
          <label>
            Quantity
            <input type="number" min="1" value={amount} onChange={(e) => setAmount(e.target.value)} required />
          </label>
          <label>
            Reason
            <input value={reason} onChange={(e) => setReason(e.target.value)} maxLength={120}
              placeholder={direction === "in" ? "PO-1042 received" : "Order #881"} />
          </label>
        </div>
        <p className={`preview ${after < 0 ? "preview-bad" : ""}`}>
          {product.quantity} on hand → <strong>{after}</strong> after this change
        </p>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="form-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" disabled={saving || after < 0 || change === 0}>{saving ? "Saving…" : "Record movement"}</button>
        </div>
      </form>
    </Modal>
  );
}
