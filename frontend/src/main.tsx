import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './index.css'
import Layout from './components/Layout'
import Home from './pages/Home'
import Maschera from './pages/Maschera'
import DettaglioPreventivo from './pages/DettaglioPreventivo'
import Speciale from './pages/Speciale'
import Listino from './pages/Listino'
import Impostazioni from './pages/Impostazioni'
import Roadmap from './pages/Roadmap'

const qc = new QueryClient({ defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1 } } })

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Home />} />
            <Route path="/configura/:famiglia" element={<Maschera />} />
            <Route path="/preventivi/:id" element={<DettaglioPreventivo />} />
            <Route path="/speciali/nuovo" element={<Speciale />} />
            <Route path="/speciali/:id" element={<Speciale />} />
            <Route path="/listino" element={<Listino />} />
            <Route path="/impostazioni" element={<Impostazioni />} />
            <Route path="/roadmap" element={<Roadmap />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
