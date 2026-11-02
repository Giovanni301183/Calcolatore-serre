import { Link, NavLink, Outlet } from 'react-router-dom'

const VOCI = [
  { to: '/', label: 'Preventivi', end: true },
  { to: '/listino', label: 'Listino' },
  { to: '/impostazioni', label: 'Impostazioni' },
  { to: '/roadmap', label: 'Roadmap' },
]

export default function Layout() {
  return (
    <div className="min-h-screen">
      <header className="bg-verde-800 text-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <Link to="/" className="flex items-center gap-2.5">
            <img src="/favicon.svg" alt="" className="h-8 w-8" />
            <span className="text-lg font-semibold tracking-wide">TERRANOVA</span>
            <span className="hidden text-verde-100/80 sm:inline">· Configuratore</span>
          </Link>
          <nav className="flex gap-1 overflow-x-auto">
            {VOCI.map((v) => (
              <NavLink key={v.to} to={v.to} end={v.end}
                className={({ isActive }) => `rounded-md px-3 py-1.5 text-sm whitespace-nowrap ${isActive ? 'bg-white/15 font-medium' : 'text-verde-100 hover:bg-white/10'}`}>
                {v.label}
              </NavLink>
            ))}
          </nav>
          <span className="ml-auto rounded bg-white/10 px-2 py-0.5 text-xs text-verde-100">prototipo locale</span>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
