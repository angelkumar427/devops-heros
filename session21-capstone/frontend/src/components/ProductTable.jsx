import { money, number } from "../api.js";

function StatusBadge({ product }) {
  if (product.quantity === 0) return <span className="badge badge-out">Out of stock</span>;
  if (product.low_stock) return <span className="badge badge-low">Low</span>;
  return <span className="badge badge-ok">In stock</span>;
}

export default function ProductTable({ products, loading, onEdit, onAdjust, onDelete }) {
  if (loading) return <p className="muted pad">Loading products…</p>;
  if (products.length === 0) return <p className="muted pad">No products match these filters.</p>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Product</th>
            <th>Category</th>
            <th className="num">On hand</th>
            <th className="num">Reorder at</th>
            <th className="num">Unit price</th>
            <th className="num">Value</th>
            <th>Status</th>
            <th aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <tr key={p.id}>
              <td data-label="Product">
                <span className="cell-title">{p.name}</span>
                <span className="sku">{p.sku}</span>
              </td>
              <td data-label="Category">{p.category}</td>
              <td data-label="On hand" className="num strong">{number.format(p.quantity)}</td>
              <td data-label="Reorder at" className="num muted">{number.format(p.reorder_level)}</td>
              <td data-label="Unit price" className="num">{money.format(Number(p.unit_price))}</td>
              <td data-label="Value" className="num">{money.format(p.quantity * Number(p.unit_price))}</td>
              <td data-label="Status"><StatusBadge product={p} /></td>
              <td className="actions">
                <button className="btn btn-small" onClick={() => onAdjust(p)}>Adjust</button>
                <button className="btn btn-small btn-ghost" onClick={() => onEdit(p)}>Edit</button>
                <button className="btn btn-small btn-danger" onClick={() => onDelete(p)} aria-label={`Delete ${p.name}`}>
                  ✕
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
