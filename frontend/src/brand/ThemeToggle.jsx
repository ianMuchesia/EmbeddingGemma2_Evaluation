import { useState } from 'react'

// Light/dark switch, behaving like the one on the Msodoki site: the mode lives on
// <html data-theme> (set before paint by index.html) and in a `theme` cookie.
const ONE_YEAR_SECONDS = 60 * 60 * 24 * 365

function currentMode() {
  return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'
}

function saveMode(mode) {
  document.documentElement.dataset.theme = mode
  try {
    document.cookie = `theme=${mode}; path=/; max-age=${ONE_YEAR_SECONDS}; samesite=lax`
  } catch { /* cookies blocked: the switch still works for this visit */ }
}

const iconProps = {
  width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor',
  strokeWidth: 1.75, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true,
}

export default function ThemeToggle() {
  const [mode, setMode] = useState(currentMode)
  const next = mode === 'light' ? 'dark' : 'light'

  return (
    <button
      type="button"
      className="icon-button"
      onClick={() => { saveMode(next); setMode(next) }}
      aria-label={`Switch to ${next} mode`}
      title={`Switch to ${next} mode`}
    >
      {mode === 'light' ? (
        <svg {...iconProps}><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" /></svg>
      ) : (
        <svg {...iconProps}>
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
        </svg>
      )}
    </button>
  )
}
