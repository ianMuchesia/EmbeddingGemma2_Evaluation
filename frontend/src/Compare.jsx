import { useEffect, useMemo, useState } from 'react'
import { formatKes } from './format.js'

// Same colours as the benchmark charts: one per model family.
const FAMILY_COLORS = {
  keyword: '#2a78d6', minilm: '#eb6834', me5: '#1baf7a', gemma: '#eda100', ours: '#e87ba4',
}
const SUGGESTIONS_PER_TYPE = 2

async function getJson(url) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`API returned ${res.status}`)
  return res.json()
}

export default function Compare() {
  const [info, setInfo] = useState(null)
  const [questions, setQuestions] = useState([])
  const [selected, setSelected] = useState(null) // setup names; null until defaults arrive
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [shuffle, setShuffle] = useState(0)

  // Poll the indexing status until every setup is ready (or it failed).
  useEffect(() => {
    let timer
    async function poll() {
      try {
        const next = await getJson('/api/compare/info')
        setInfo(next)
        setSelected((current) => current ?? next.defaults)
        if (next.status !== 'ready' && next.status !== 'error') timer = setTimeout(poll, 2000)
      } catch (e) {
        setError(`${e.message}. Is the API running on port 8000?`)
        timer = setTimeout(poll, 4000)
      }
    }
    poll()
    getJson('/api/compare/questions').then(setQuestions).catch(() => {})
    return () => clearTimeout(timer)
  }, [])

  const suggestions = useMemo(() => pickSuggestions(questions, SUGGESTIONS_PER_TYPE), [questions, shuffle])

  async function runCompare(q) {
    if (!q.trim() || !selected?.length) return
    setQuery(q)
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ q, setups: selected.join(',') })
      setResult(await getJson(`/api/compare?${params}`))
    } catch (e) {
      setError(`${e.message}. Is the API running on port 8000?`)
    } finally {
      setLoading(false)
    }
  }

  function toggle(name) {
    setSelected((current) => current.includes(name) ? current.filter((n) => n !== name) : [...current, name])
  }

  return (
    <section>
      <h2>Compare setups</h2>
      <p className="lead">
        Ask anything and see what each search setup returns, side by side. Suggestions come from the
        benchmark questions; for those, ✓ marks a correct product.
      </p>

      <Status info={info} />
      {error && <div className="card error">{error}</div>}

      <form onSubmit={(e) => { e.preventDefault(); runCompare(query) }}>
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Type your own question…" autoFocus />
        <button disabled={loading || !info?.ready}>{loading ? 'Comparing…' : 'Compare'}</button>
      </form>

      <div className="suggestions">
        {suggestions.map(({ type, items }) => (
          <div key={type} className="suggestion-row">
            <span className="suggestion-type">{type}</span>
            {items.map((q) => (
              <button key={q.q} className="chip" onClick={() => runCompare(q.q)} disabled={loading || !info?.ready}>
                {q.q}
              </button>
            ))}
          </div>
        ))}
        {questions.length > 0 && (
          <button className="link" onClick={() => setShuffle((n) => n + 1)}>More suggestions</button>
        )}
      </div>

      {info && selected && (
        <SetupPicker setups={info.setups} selected={selected} onToggle={toggle} />
      )}

      {result && <Results result={result} />}
    </section>
  )
}

function Status({ info }) {
  if (!info) return <div className="card">Connecting to the API…</div>
  if (info.status === 'ready' && !info.message) return null
  const progress = info.status === 'ready' ? '' : ` Indexing setups: ${info.ready} of ${info.total} ready…`
  return <div className={`card ${info.status === 'error' ? 'error' : ''}`}>{info.message}{progress}</div>
}

function SetupPicker({ setups, selected, onToggle }) {
  return (
    <details className="picker" open>
      <summary>Setups shown ({selected.length})</summary>
      <div className="picker-grid">
        {setups.map((s) => (
          <label key={s.name} className={s.ready ? '' : 'muted'}>
            <input type="checkbox" checked={selected.includes(s.name)} onChange={() => onToggle(s.name)} />
            <span className="dot" style={{ background: FAMILY_COLORS[s.family] }} />
            {s.label}
            {s.end_to_end != null && <span className="muted small"> · benchmark {Math.round(s.end_to_end * 100)}%</span>}
            {!s.ready && <span className="muted small"> · not ready</span>}
          </label>
        ))}
      </div>
    </details>
  )
}

function Results({ result }) {
  const graded = result.expected != null
  return (
    <>
      <h3>Results for “{result.query}”</h3>
      {graded && (
        <p className="muted">
          {result.expected.length ? `Benchmark question · correct: ${result.expected.join(', ')}`
            : "Benchmark question · we don't sell this, so the right answer is “not found”"}
        </p>
      )}
      <div className="compare-grid">
        {result.results.map((r) => (
          <div key={r.name} className="card result-card">
            <div className="result-head">
              <span className="dot" style={{ background: FAMILY_COLORS[r.family] }} />
              <strong>{r.label}</strong>
            </div>
            {r.error ? <p className="error-text">{r.error}</p> : <ResultBody r={r} />}
          </div>
        ))}
      </div>
    </>
  )
}

function ResultBody({ r }) {
  return (
    <>
      <div className="result-meta">
        <Verdict r={r} />
        <span className="muted small">
          score {r.confidence.toFixed(3)}{r.cutoff != null && ` / cutoff ${r.cutoff.toFixed(3)}`} · {r.latency_ms} ms
        </span>
      </div>
      <ol>
        {r.products.map((p) => (
          <li key={p.id} className={p.correct ? 'correct' : ''}>
            <span>{p.correct ? '✓ ' : ''}{p.name}</span>
            <span className="muted small">{formatKes(p.price)} · {p.stock ? `${p.stock} in stock` : 'out of stock'}</span>
          </li>
        ))}
        {r.products.length === 0 && <li className="muted">no results</li>}
      </ol>
    </>
  )
}

function Verdict({ r }) {
  if (r.found == null) return <span className="badge">no cutoff yet</span>
  return r.found
    ? <span className="badge good">Answers</span>
    : <span className="badge bad">Not found</span>
}

function pickSuggestions(questions, perType) {
  const byType = {}
  for (const q of questions) (byType[q.type] ??= []).push(q)
  return Object.entries(byType).map(([type, items]) => ({
    type,
    items: [...items].sort(() => Math.random() - 0.5).slice(0, perType),
  }))
}
