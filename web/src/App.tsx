import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { AuthProvider } from './auth/AuthProvider'
import { PlayerProvider } from './players/PlayerProvider'
import { AppShell } from './components/AppShell'
import { AccountPage } from './pages/AccountPage'
import { ComparePage } from './pages/ComparePage'
import { EsportsPage } from './pages/EsportsPage'
import { HeroDetailPage } from './pages/HeroDetailPage'
import { HeroesPage } from './pages/HeroesPage'
import { HomePage } from './pages/HomePage'
import { NotFoundPage } from './pages/NotFoundPage'
import { PlayersPage } from './pages/PlayersPage'
import { RanksPage } from './pages/RanksPage'
import { SavedPage } from './pages/SavedPage'
import { ApiError } from './lib/api'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        // A typed API failure is final - retrying it only wastes requests.
        if (error instanceof ApiError) return false
        return failureCount < 2
      },
      refetchOnWindowFocus: false,
      staleTime: 60 * 1000,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <PlayerProvider>
            <AppShell>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/heroes" element={<HeroesPage />} />
                <Route path="/heroes/:slug" element={<HeroDetailPage />} />
                <Route path="/ranks" element={<RanksPage />} />
                <Route path="/players" element={<PlayersPage />} />
                <Route path="/saved" element={<SavedPage />} />
                <Route path="/compare" element={<ComparePage />} />
                <Route path="/esports" element={<EsportsPage />} />
                <Route path="/account" element={<AccountPage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </AppShell>
          </PlayerProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
