import type { Campo, Valore } from '../api'

const base = 'w-full rounded-md border border-gray-300 bg-white px-2.5 py-1.5 text-sm focus:border-verde-600 focus:outline-none focus:ring-2 focus:ring-verde-100'

export default function CampoInput({ campo, valore, onChange }: { campo: Campo; valore: Valore; onChange: (v: Valore) => void }) {
  const id = `f-${campo.key}`
  if (campo.tipo === 'si_no') {
    return (
      <label htmlFor={id} className="flex cursor-pointer items-center gap-2.5 py-1 text-sm">
        <input id={id} type="checkbox" checked={Boolean(valore)} onChange={(e) => onChange(e.target.checked)}
          className="h-4 w-4 accent-verde-600" />
        {campo.label}
      </label>
    )
  }
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-xs font-medium text-gray-600">
        {campo.label}{campo.unita && <span className="text-gray-400"> ({campo.unita})</span>}
      </label>
      {campo.tipo === 'scelta' ? (
        <select id={id} className={base} value={String(valore)}
          onChange={(e) => {
            const o = campo.opzioni?.find((x) => String(x) === e.target.value)
            onChange(o ?? e.target.value)
          }}>
          {campo.opzioni?.map((o) => <option key={String(o)} value={String(o)}>{String(o).replace('.', ',')}</option>)}
        </select>
      ) : campo.tipo === 'numero' ? (
        <>
          <input id={id} type="number" className={base} value={valore === '' ? '' : Number(valore)}
            min={campo.min} max={campo.max} step={campo.step ?? 'any'} list={campo.suggeriti ? `${id}-sugg` : undefined}
            onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))} />
          {campo.suggeriti && (
            <datalist id={`${id}-sugg`}>{campo.suggeriti.map((s) => <option key={s} value={s} />)}</datalist>
          )}
        </>
      ) : (
        <input id={id} type="text" className={base} value={String(valore)} onChange={(e) => onChange(e.target.value)} />
      )}
      {campo.aiuto && <p className="mt-1 text-xs text-gray-500">{campo.aiuto}</p>}
    </div>
  )
}
