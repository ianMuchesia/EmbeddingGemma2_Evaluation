// The Msodoki mark (hat only). Same paths as Mark.tsx in ~/Desktop/React/Profile/packages/theme:
// the hat takes currentColor, the band takes the brand amber, so it recolours for either theme.
export default function Mark({ className, title = 'Msodoki' }) {
  return (
    <svg viewBox="0 0 64 40" className={className} role="img" aria-label={title || undefined} aria-hidden={!title}>
      <path
        fill="currentColor"
        d="M17.6 27 L21.6 9.8 C22.2 7.1 23.7 5.6 26.1 5.4 C28.4 5.2 30.2 6.1 32 6.8 C33.8 6.1 35.6 5.2 37.9 5.4 C40.3 5.6 41.8 7.1 42.4 9.8 L46.4 27 Z"
      />
      <path
        fill="var(--brand)"
        d="M19.36 18.8 C27 17.9 37 17.9 44.64 18.8 L45.75 23.6 C37 22.7 27 22.7 18.25 23.6 Z"
      />
      <path
        fill="currentColor"
        d="M3.6 29.2 C2.6 29.6 2.9 30.6 4 30.6 L60 30.6 C61.1 30.6 61.4 29.6 60.4 29.2 C52 26 43 24.6 32 24.6 C21 24.6 12 26 3.6 29.2 Z"
      />
      <rect fill="currentColor" x="21" y="35" width="22" height="2.4" rx="1.2" />
    </svg>
  )
}
