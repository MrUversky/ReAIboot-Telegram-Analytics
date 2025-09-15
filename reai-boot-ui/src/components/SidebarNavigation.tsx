'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useSupabase } from '@/components/SupabaseProvider'
import {
  BarChart3,
  FileText,
  Video,
  Settings,
  User,
  LogOut,
  Database,
  Bot,
  TrendingUp,
  Book,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  FileBarChart
} from 'lucide-react'

const navigation = [
  { name: 'Аналитика', href: '/', icon: BarChart3 },
  { name: 'Посты', href: '/posts', icon: FileText },
  { name: 'Отчеты', href: '/reports', icon: FileBarChart },
  { name: 'Сценарии', href: '/scenarios', icon: Video },
  { name: 'Парсинг', href: '/parsing', icon: Database },
  { name: 'Wiki', href: '/wiki', icon: Book },
  { name: 'Статистика', href: '/stats', icon: TrendingUp },
  { name: 'Админ', href: '/admin', icon: Settings },
]

interface SidebarNavigationProps {
  isMobileMenuOpen: boolean
  setIsMobileMenuOpen: (open: boolean) => void
}

export function SidebarNavigation({ isMobileMenuOpen, setIsMobileMenuOpen }: SidebarNavigationProps) {
  const pathname = usePathname()
  const { user, permissions, signOut, loading } = useSupabase()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)

  // Загружаем состояние collapsed из localStorage
  useEffect(() => {
    const saved = localStorage.getItem('sidebar-collapsed')
    if (saved !== null) {
      setIsCollapsed(JSON.parse(saved))
    }
  }, [])

  // Сохраняем состояние collapsed в localStorage
  const toggleCollapsed = () => {
    const newState = !isCollapsed
    setIsCollapsed(newState)
    localStorage.setItem('sidebar-collapsed', JSON.stringify(newState))
  }

  // Wiki доступна без авторизации
  const isWikiRoute = pathname?.startsWith('/wiki')

  if (loading && !isWikiRoute) {
    return (
      <div className="flex">
        <div className="w-64 bg-white shadow-sm border-r animate-pulse">
          <div className="p-4 border-b">
            <div className="h-8 bg-gray-200 rounded mb-4"></div>
          </div>
          <div className="p-4 space-y-2">
            {Array.from({ length: 7 }).map((_, i) => (
              <div key={i} className="h-10 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!user && !isWikiRoute) {
    return (
      <div className="flex">
        <div className={`${isCollapsed ? 'w-16' : 'w-64'} bg-white shadow-sm border-r transition-all duration-300 ease-in-out`}>
          <div className="p-4 border-b flex items-center justify-between">
            <Link href="/" className={`flex items-center ${isCollapsed ? 'justify-center' : ''}`}>
              <Bot className="w-8 h-8 text-blue-600" />
              {!isCollapsed && <h1 className="text-xl font-bold text-gray-900 ml-2">ReAIboot</h1>}
            </Link>
            <button
              onClick={toggleCollapsed}
              className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
            >
              {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>

          <div className="p-4">
            <Link
              href="/auth"
              className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors hover:bg-gray-100 ${
                isCollapsed ? 'justify-center' : ''
              }`}
            >
              <User className="w-4 h-4" />
              {!isCollapsed && <span className="ml-2">Войти</span>}
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // Фильтруем навигацию в зависимости от прав
  const filteredNavigation = navigation.filter(item => {
    // Wiki доступна всегда
    if (item.href === '/wiki') {
      return true
    }

    if (!user) {
      // Для неавторизованных пользователей только wiki и дашборд
      return item.href === '/' || item.href === '/wiki'
    }

    if (!permissions?.hasAccess) {
      // В демо режиме только дашборд и wiki
      return item.href === '/' || item.href === '/wiki'
    }
    if (item.href === '/admin' && !permissions.canAdmin) {
      return false
    }
    if (item.href === '/parsing' && !permissions.canParse) {
      return false
    }
    return true
  })

  return (
    <>
      {/* Desktop Sidebar */}
      <div className={`hidden md:flex flex-col bg-white shadow-sm border-r transition-all duration-300 ease-in-out ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}>
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <Link href="/" className={`flex items-center ${isCollapsed ? 'justify-center' : ''}`}>
            <Bot className="w-8 h-8 text-blue-600" />
            {!isCollapsed && <h1 className="text-xl font-bold text-gray-900 ml-2">ReAIboot</h1>}
          </Link>
          <button
            onClick={toggleCollapsed}
            className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {filteredNavigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isCollapsed ? 'justify-center' : ''
                } ${
                  isActive
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <item.icon className="w-4 h-4 flex-shrink-0" />
                {!isCollapsed && <span className="ml-2">{item.name}</span>}
              </Link>
            )
          })}
        </nav>

        {/* User Menu */}
        <div className="p-4 border-t">
          <div className="relative">
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className={`flex items-center w-full px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 transition-colors ${
                isCollapsed ? 'justify-center' : ''
              }`}
            >
              <User className="w-4 h-4 flex-shrink-0" />
              {!isCollapsed && (
                <span className="ml-2 truncate">
                  {user?.email?.split('@')[0]}
                </span>
              )}
            </button>

            {isUserMenuOpen && (
              <div className={`absolute bottom-full mb-2 ${
                isCollapsed ? 'left-0 w-48' : 'right-0 w-56'
              } bg-white rounded-md shadow-lg py-1 z-10`}>
                <div className="px-4 py-2 text-sm text-gray-700 border-b">
                  {user?.email}
                </div>
                <button
                  onClick={() => {
                    signOut()
                    setIsUserMenuOpen(false)
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Выйти
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="fixed inset-0 bg-transparent" onClick={() => setIsMobileMenuOpen(false)} />
          <div className="fixed left-0 top-0 h-full w-80 bg-white shadow-xl transform transition-transform duration-300 ease-in-out border-r border-gray-200">
            {/* Mobile Header */}
            <div className="p-4 border-b flex items-center justify-between">
              <Link href="/" className="flex items-center" onClick={() => setIsMobileMenuOpen(false)}>
                <Bot className="w-8 h-8 text-blue-600 mr-2" />
                <h1 className="text-xl font-bold text-gray-900">ReAIboot</h1>
              </Link>
              <button
                onClick={() => setIsMobileMenuOpen(false)}
                className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Mobile Navigation */}
            <nav className="p-4 space-y-1">
              {filteredNavigation.map((item) => {
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center px-3 py-2 rounded-md text-base font-medium ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <item.icon className="w-5 h-5 mr-3" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>

            {/* Mobile User Menu */}
            <div className="p-4 border-t">
              <div className="px-3 py-2 text-sm text-gray-700 border-b">
                {user?.email}
              </div>
              <button
                onClick={() => {
                  signOut()
                  setIsMobileMenuOpen(false)
                }}
                className="flex items-center w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-100"
              >
                <LogOut className="w-5 h-5 mr-3" />
                Выйти
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileMenuOpen(true)}
        className="fixed top-4 left-4 z-40 md:hidden bg-white p-2 rounded-lg shadow-lg border"
      >
        <Menu className="w-5 h-5" />
      </button>
    </>
  )
}
