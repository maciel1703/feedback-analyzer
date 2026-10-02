async function req(url, opts = {}) {
  const res = await fetch(url, { headers: { "Content-Type": "application/json" }, ...opts });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : "Erro ao falar com a API.");
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  summary: () => req("/api/summary"),
  topics: () => req("/api/topics"),
  list: () => req("/api/feedbacks?limit=30"),
  add: (texts) => req("/api/feedbacks/bulk", { method: "POST", body: JSON.stringify({ texts }) }),
  clear: () => req("/api/feedbacks", { method: "DELETE" }),
};
