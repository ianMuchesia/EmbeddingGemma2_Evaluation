// Prices in the catalog are Kenyan shillings.
const KES = new Intl.NumberFormat('en-KE', { style: 'currency', currency: 'KES', maximumFractionDigits: 0 })

export function formatKes(amount) {
  return KES.format(amount) // e.g. "Ksh 104,999"
}
