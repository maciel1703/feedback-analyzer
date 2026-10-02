import { useCallback, useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "./api";

const KEYS = ["positive", "neutral", "negative"];
const NAMES = { positive: "Positivo", neutral: "Neutro", negative: "Negativo" };
const COLORS = { positive: "#2f7d5b", neutral: "#98a2b3", negative: "#c24e3a" };
const pct = (n, total) => (total ? Math.round((n / total) * 100) : 0);

function SentimentBar({ data, tall }) {
  return (
    <div className={`bar${tall ? " tall" : ""}`} role="img"
         aria-label={KEYS.map((k) => `${NAMES[k]}: ${data[k] || 0}`).join(", ")}>
      {KEYS.map((k) => (data[k] ? <span key={k} className={`seg ${k}`} style={{ flex: data[k] }} /> : null))}
    </div>
  );
}

export default function App() {
  const [summary, setSummary] = useState(null);
  const [topics, setTopics] = useState([]);
  const [items, setItems] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [s, t, l] = await Promise.all([api.summary(), api.topics(), api.list()]);
      setSummary(s); setTopics(t); setItems(l); setError("");
    } catch {
      setError("Não foi possível carregar os dados. Confira se a API está rodando em localhost:8000.");
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function submit() {
    const texts = text.split("\n").map((t) => t.trim()).filter(Boolean);
    if (!texts.length) return;
    setBusy(true);
    try { await api.add(texts); setText(""); await load(); }
    catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  async function clearAll() {
    if (!window.confirm("Apagar todos os comentários analisados?")) return;
    await api.clear(); load();
  }

  const total = summary?.total ?? 0;
  const counts = summary?.counts ?? {};

  return (
    <div className="page">
      <header>
        <h1>Feedback dos clientes</h1>
        <div className="actions">
          <button className="ghost" onClick={load}>Atualizar</button>
          <button className="ghost danger" onClick={clearAll} disabled={!total}>Apagar tudo</button>
        </div>
      </header>

      {error && <p className="error" role="alert">{error}</p>}

      <section className="ribbon">
        <SentimentBar data={counts} tall />
        <dl>
          {KEYS.map((k) => (
            <div key={k}>
              <dt><i className={`dot ${k}`} />{NAMES[k]}</dt>
              <dd>{pct(counts[k] || 0, total)}%</dd>
            </div>
          ))}
          <div><dt>Comentários</dt><dd>{total}</dd></div>
          <div><dt>Nota média</dt><dd>{(summary?.avg_score ?? 0).toFixed(2)}</dd></div>
        </dl>
      </section>

      <div className="grid">
        <main>
          <section>
            <h2>Sentimento por dia</h2>
            {summary?.trend?.length ? (
              <div className="chart">
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={summary.trend} margin={{ left: -20 }}>
                    <CartesianGrid stroke="#cbd3dd" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip formatter={(v, k) => [v, NAMES[k]]} />
                    {KEYS.map((k) => <Bar key={k} dataKey={k} stackId="a" fill={COLORS[k]} />)}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="empty">Nenhum comentário ainda. Cole comentários ao lado, um por linha, e clique em Analisar.</p>
            )}
          </section>

          <section>
            <h2>Tópicos recorrentes</h2>
            {topics.length ? (
              <ul className="topics">
                {topics.map((t) => (
                  <li key={t.id}>
                    <div className="row">
                      <strong>{t.label}</strong>
                      <span>{t.count} comentários</span>
                    </div>
                    <SentimentBar data={t.sentiment} />
                    <p className="terms">{t.terms.join(", ")}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="empty">Os tópicos aparecem a partir de 6 comentários.</p>
            )}
          </section>
        </main>

        <aside>
          <section>
            <h2>Analisar comentários</h2>
            <label htmlFor="in" className="sr">Comentários, um por linha</label>
            <textarea id="in" rows={6} value={text} onChange={(e) => setText(e.target.value)}
                      placeholder={"A entrega foi rápida.\nO atendimento demorou demais."} />
            <button onClick={submit} disabled={busy || !text.trim()}>
              {busy ? "Analisando…" : "Analisar"}
            </button>
          </section>

          <section>
            <h2>Últimos comentários</h2>
            <ul className="feed">
              {items.map((f) => (
                <li key={f.id}>
                  <i className={`dot ${f.sentiment}`} title={NAMES[f.sentiment]} />
                  <div>
                    <p>{f.text}</p>
                    <small>{NAMES[f.sentiment]}, nota {f.score.toFixed(2)}</small>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </aside>
      </div>
    </div>
  );
}
