'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSupabase } from '@/components/SupabaseProvider'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  BarChart3,
  FileText,
  Video,
  Database,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  DollarSign,
  Zap,
  RefreshCw
} from 'lucide-react'
import { apiClient } from '@/lib/api'

interface SystemStats {
  total_posts: number
  posts_today: number
  active_channels: number
  recent_analysis: number
  avg_processing_time: number
  error_rate: number
}

interface TokenUsageStats {
  total_tokens: number
  total_cost: number
  avg_cost_per_token: number
  models_used: string[]
  operations_count: number
}

interface LLMStatus {
  processor_status: Record<string, boolean>
  available_templates: string[]
  project_context_keys: string[]
}

export default function Dashboard() {
  const router = useRouter()
  const { user, permissions, signOut, loading, refreshPermissions } = useSupabase()
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [tokenStats, setTokenStats] = useState<TokenUsageStats | null>(null)
  const [llmStatus, setLlmStatus] = useState<LLMStatus | null>(null)
  const [loadingStats, setLoadingStats] = useState(true)

  useEffect(() => {
    if (!loading && !user) {
      router.push('/auth')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      loadDashboardData()
    }
  }, [user])

  const loadDashboardData = async () => {
    try {
      setLoadingStats(true)

      // Загружаем данные параллельно
      const [healthData, tokenData, llmData] = await Promise.allSettled([
        apiClient.getSystemHealth(),
        apiClient.getTokenUsageStats(),
        apiClient.getLLMStats()
      ])

      if (healthData.status === 'fulfilled') setStats(healthData.value)
      if (tokenData.status === 'fulfilled') setTokenStats(tokenData.value)
      if (llmData.status === 'fulfilled') setLlmStatus(llmData.value)

    } catch (error) {
      console.error('Error loading dashboard data:', error)
    } finally {
      setLoadingStats(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full space-y-8">
          <div>
            <h1 className="text-center text-3xl font-bold text-gray-900">
              ReAIboot Dashboard
            </h1>
            <p className="mt-2 text-center text-sm text-gray-600">
              Войдите для доступа к системе анализа Telegram постов
            </p>
          </div>
          <div className="bg-white py-8 px-6 shadow rounded-lg">
            <div className="text-center">
              <button
                onClick={() => router.push('/auth')}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700"
              >
                Войти в систему
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Демо режим для пользователей без прав
  if (!permissions?.hasAccess) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className="flex items-center space-x-4">
                <h1 className="text-2xl font-bold text-gray-900">
                  🚀 ReAIboot Demo
                </h1>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">Демо режим</span>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">
                  {user.email}
                </span>
                <button
                  onClick={signOut}
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Выйти
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Demo Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-8">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Демо режим активен
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>
                    У вас демо-доступ к системе. Для получения полных прав обратитесь к администратору проекта.
                  </p>
                  <p className="mt-1">
                    Email администратора: <strong>admin@reaiboot.com</strong>
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Demo Features */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Анализ постов</dt>
                      <dd className="text-lg font-medium text-gray-900">🚫 Заблокировано</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Генерация сценариев</dt>
                      <dd className="text-lg font-medium text-gray-900">🚫 Заблокировано</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Админ панель</dt>
                      <dd className="text-lg font-medium text-gray-900">🚫 Заблокировано</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8 bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Возможности полной версии</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">📊 Аналитика</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Статистика постов и каналов</li>
                  <li>• Мониторинг LLM использования</li>
                  <li>• Отчеты о затратах</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">🤖 ИИ функции</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Анализ успешности постов</li>
                  <li>• Генерация сценариев Reels</li>
                  <li>• Оптимизация контента</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">ReAIboot Dashboard</h1>
          <p className="text-gray-600 mt-2">
            Анализ Telegram каналов и генерация сценариев для Reels
          </p>
        </div>
        <Button onClick={loadDashboardData} disabled={loadingStats}>
          {loadingStats ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          ) : (
            <RefreshCw className="w-4 h-4 mr-2" />
          )}
          Обновить
        </Button>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => router.push('/posts')}>
          <CardContent className="p-6">
            <div className="flex items-center">
              <FileText className="w-8 h-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Просмотр постов</p>
                <p className="text-2xl font-bold text-gray-900">Анализ</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => router.push('/parsing')}>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Database className="w-8 h-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Запустить парсинг</p>
                <p className="text-2xl font-bold text-gray-900">Telegram</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center">
              <Video className="w-8 h-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Генерация сценариев</p>
                <p className="text-2xl font-bold text-gray-900">Reels</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center">
              <TrendingUp className="w-8 h-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Статистика и</p>
                <p className="text-2xl font-bold text-gray-900">Мониторинг</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Всего постов</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loadingStats ? '...' : formatNumber(stats?.total_posts || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              +{formatNumber(stats?.posts_today || 0)} сегодня
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Активные каналы</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.active_channels || 0}</div>
            <p className="text-xs text-muted-foreground">
              Мониторятся
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Анализов сегодня</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.recent_analysis || 0}</div>
            <p className="text-xs text-muted-foreground">
              За последний час
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Затраты сегодня</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${tokenStats?.total_cost?.toFixed(2) || '0.00'}
            </div>
            <p className="text-xs text-muted-foreground">
              {tokenStats?.total_tokens?.toLocaleString() || 0} токенов
            </p>
          </CardContent>
        </Card>
      </div>

      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle>Статус системы</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">API Backend</span>
            <Badge className="bg-green-100 text-green-800">
              <CheckCircle className="w-3 h-3 mr-1" />
              Работает
            </Badge>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">LLM Pipeline</span>
            <div className="flex items-center space-x-2">
              {llmStatus?.processor_status?.filter ? (
                <Badge className="bg-green-100 text-green-800">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Filter
                </Badge>
              ) : (
                <Badge className="bg-gray-100 text-gray-800">
                  <Clock className="w-3 h-3 mr-1" />
                  Filter
                </Badge>
              )}
              {llmStatus?.processor_status?.analysis ? (
                <Badge className="bg-green-100 text-green-800">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Analysis
                </Badge>
              ) : (
                <Badge className="bg-gray-100 text-gray-800">
                  <Clock className="w-3 h-3 mr-1" />
                  Analysis
                </Badge>
              )}
              {llmStatus?.processor_status?.generator ? (
                <Badge className="bg-green-100 text-green-800">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Generator
                </Badge>
              ) : (
                <Badge className="bg-gray-100 text-gray-800">
                  <Clock className="w-3 h-3 mr-1" />
                  Generator
                </Badge>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Среднее время обработки</span>
            <span className="text-sm text-gray-600">
              {stats?.avg_processing_time?.toFixed(1) || 0} сек
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Недавняя активность</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <Database className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>История активности будет отображаться здесь</p>
            <p className="text-sm mt-2">После запуска парсинга и анализа постов</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
