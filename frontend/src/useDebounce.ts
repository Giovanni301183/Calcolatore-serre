import { useEffect, useState } from 'react'

/** restituisce il valore solo dopo `ms` millisecondi senza modifiche */
export function useDebounce<T>(valore: T, ms: number): T {
  const [v, setV] = useState(valore)
  useEffect(() => {
    const t = setTimeout(() => setV(valore), ms)
    return () => clearTimeout(t)
  }, [valore, ms])
  return v
}
