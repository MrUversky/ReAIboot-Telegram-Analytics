import { Navigation } from '@/components/Navigation'
import { SupabaseProvider } from '@/components/SupabaseProvider'

export default function WikiLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <SupabaseProvider>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          {children}
        </main>
      </div>
    </SupabaseProvider>
  )
}
