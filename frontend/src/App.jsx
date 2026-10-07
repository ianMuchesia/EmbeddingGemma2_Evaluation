import { useState } from 'react'
import ShopSearch from './ShopSearch.jsx'
import Compare from './Compare.jsx'
import Mark from './brand/Mark.jsx'
import ThemeToggle from './brand/ThemeToggle.jsx'

const PAGES = [
  { id: 'shop', label: 'Shop search', Component: ShopSearch },
  { id: 'compare', label: 'Compare setups', Component: Compare },
]

export default function App() {
  const [page, setPage] = useState(() => {
    try { return localStorage.getItem('page') || 'shop' } catch { return 'shop' }
  })

  function open(id) {
    setPage(id)
    try { localStorage.setItem('page', id) } catch { /* storage unavailable: just don't remember */ }
  }

  const { Component } = PAGES.find((p) => p.id === page) ?? PAGES[0]
  return (
    <>
      <header className="site-header">
        <div className="header-inner">
          <a href="/" className="lockup" aria-label="Msodoki, shop search">
            <Mark className="lockup-mark" title="" />
            <span className="lockup-name">MSODOKI</span>
          </a>
          <nav aria-label="Main" className="tabs">
            {PAGES.map((p) => (
              <button
                key={p.id}
                className={p.id === page ? 'tab active' : 'tab'}
                aria-current={p.id === page ? 'page' : undefined}
                onClick={() => open(p.id)}
              >
                {p.label}
              </button>
            ))}
            <ThemeToggle />
          </nav>
        </div>
      </header>

      <main>
        <Component />
      </main>

      <footer className="site-footer">
        <Mark className="end-mark" title="" />
        <span className="end-name">MSODOKI</span>
      </footer>
    </>
  )
}
