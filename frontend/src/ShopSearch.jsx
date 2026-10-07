import { useState } from 'react'
import { formatKes } from './format.js'

const EXAMPLES = [
  'how much is the iphone 15',
  'best phone for taking photos',
  'something to block noise on the plane',
  'is the iphone 14 available',
  'simu rahisi ya M-Pesa kwa bibi yangu',
  'solar lights for my house upcountry',
  'do you sell bicycles',
]

export default function ShopSearch() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showRaw, setShowRaw] = useState(false)

  async function runSearch(q) {
    if (!q.trim()) return
    setQuery(q)
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`)
      if (!res.ok) throw new Error(`API returned ${res.status}`)
      setResult(await res.json())
    } catch (e) {
      setError(`${e.message}. Is the API running on port 8000?`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section>
      <h2>Shop search</h2>
      <p className="lead">Ask for a product in your own words, English or Swahili. EmbeddingGemma finds the closest match; no chatbot involved.</p>

      <form onSubmit={(e) => { e.preventDefault(); runSearch(query) }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about a product…"
          autoFocus
        />
        <button disabled={loading}>{loading ? 'Searching…' : 'Search'}</button>
      </form>

      <div className="examples">
        {EXAMPLES.map((ex) => (
          <button key={ex} className="chip" onClick={() => runSearch(ex)} disabled={loading}>{ex}</button>
        ))}
      </div>

      {error && <div className="card error">{error}</div>}

      {result && (
        <>
          <div className={`card answer ${result.found ? 'found' : 'not-found'}`}>
            <div className="label">{result.found ? 'Answer' : 'No match above threshold'}</div>
            {result.answer}
          </div>

          <h3>Top 10 of {result.matches.length} products</h3>
          <p className="muted">
            final = meaning + name bonus. "Not found" if the top meaning score is below {result.threshold}.
          </p>
          <table>
            <thead>
              <tr><th>#</th><th>Product</th><th>Meaning</th><th>Name match</th><th>Final</th></tr>
            </thead>
            <tbody>
              {result.matches.slice(0, 10).map((m, i) => (
                <tr key={m.name} className={i === 0 ? 'top' : ''}>
                  <td>{i + 1}</td>
                  <td>
                    {m.name}
                    <div className="muted small">{formatKes(m.price)} · {m.stock ? `${m.stock} in stock` : 'out of stock'}</div>
                  </td>
                  <td>
                    <div className="bar-cell">
                      <div className="bar"><div style={{ width: `${m.meaning * 100}%` }} className={m.meaning >= result.threshold ? 'pass' : ''} /></div>
                      {m.meaning.toFixed(3)}
                    </div>
                  </td>
                  <td>{m.name_match.toFixed(2)}</td>
                  <td><strong>{m.final.toFixed(3)}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>

          <button className="link" onClick={() => setShowRaw(!showRaw)}>
            {showRaw ? 'Hide' : 'Show'} raw API response
          </button>
          {showRaw && <pre>{JSON.stringify(result, null, 2)}</pre>}
        </>
      )}
    </section>
  )
}
