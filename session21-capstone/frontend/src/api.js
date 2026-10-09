// Thin wrapper around fetch: same-origin /api, JSON in and out, readable errors.
async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = body?.detail;
    const message = Array.isArray(detail)
      ? detail.map((d) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join("; ")
      : detail || `${res.status} ${res.statusText}`;
    throw new Error(message);
  }
  return body;
}

export const api = {
  products: (params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== "" && v != null));
    return request(`/products${qs.size ? `?${qs}` : ""}`);
  },
  create: (data) => request("/products", { method: "POST", body: JSON.stringify(data) }),
  update: (id, data) => request(`/products/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  remove: (id) => request(`/products/${id}`, { method: "DELETE" }),
  adjust: (id, data) => request(`/products/${id}/adjust`, { method: "POST", body: JSON.stringify(data) }),
  movements: (limit = 12) => request(`/movements?limit=${limit}`),
  stats: () => request("/stats"),
};

export const money = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
export const number = new Intl.NumberFormat("en-IN");
