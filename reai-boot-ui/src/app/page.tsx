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
  Zap
} from 'lucide-react'
import { apiClient, SystemStats, TokenUsageStats } from '@/lib/api'

export default function Dashboard() {
  const router = useRouter()
  const { user, loading } = useSupabase()
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [tokenStats, setTokenStats] = useState<TokenUsageStats | null>(null)
  const [llmStatus, setLlmStatus] = useState<any>(null)
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
      const [healthData, tokenData, llmData] = await Promise.all([
        apiClient.getSystemHealth(),
        apiClient.getTokenUsageStats(),
        apiClient.getLLMStats()
      ])

      setStats(healthData)
      setTokenStats(tokenData)
      setLlmStatus(llmData)
    } catch (error) {
      console.error('Error loading dashboard data:', error)
    } finally {
      setLoadingStats(false)
    }
  }

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
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
          <h1 className="text-3xl font-bold text-gray-900">Дашборд ReAIboot</h1>
          <p className="text-gray-600 mt-2">
            Анализ Telegram каналов и генерация сценариев для Reels
          </p>
        </div>
        <Button onClick={loadDashboardData} disabled={loadingStats}>
          {loadingStats ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          ) : (
            <BarChart3 className="w-4 h-4 mr-2" />
          )}
          Обновить
        </Button>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => router.push('/parsing')}>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Database className="w-8 h-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Запустить парсинг</p>
                <p className="text-2xl font-bold text-gray-900">Telegram</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => router.push('/posts')}>
          <CardContent className="p-6">
            <div className="flex items-center">
              <FileText className="w-8 h-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Просмотр постов</p>
                <p className="text-2xl font-bold text-gray-900">Анализ</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => router.push('/scenarios')}>
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

        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => router.push('/admin')}>
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
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Статус системы</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">LLM Pipeline</span>
              <div className="flex items-center space-x-2">
                {llmStatus?.processor_status?.filter ? (
                  <Badge className="bg-green-100 text-green-800">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Filter
                  </Badge>
                ) : (
                  <Badge className="bg-red-100 text-red-800">
                    <AlertCircle className="w-3 h-3 mr-1" />
                    Filter
                  </Badge>
                )}
                {llmStatus?.processor_status?.analysis ? (
                  <Badge className="bg-green-100 text-green-800">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Analysis
                  </Badge>
                ) : (
                  <Badge className="bg-red-100 text-red-800">
                    <AlertCircle className="w-3 h-3 mr-1" />
                    Analysis
                  </Badge>
                )}
                {llmStatus?.processor_status?.generator ? (
                  <Badge className="bg-green-100 text-green-800">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Generator
                  </Badge>
                ) : (
                  <Badge className="bg-red-100 text-red-800">
                    <AlertCircle className="w-3 h-3 mr-1" />
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

            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Уровень ошибок</span>
              <span className="text-sm text-gray-600">
                {stats?.error_rate?.toFixed(1) || 0}%
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Использование токенов</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Всего за 30 дней</span>
              <span className="text-sm text-gray-600">
                {tokenStats?.total_tokens?.toLocaleString() || 0}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Стоимость</span>
              <span className="text-sm text-gray-600">
                ${tokenStats?.total_cost?.toFixed(2) || '0.00'}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Стоимость за токен</span>
              <span className="text-sm text-gray-600">
                ${tokenStats?.avg_cost_per_token?.toFixed(4) || '0.0000'}
              </span>
            </div>

            <div className="space-y-2">
              <span className="text-sm font-medium">Модели:</span>
              <div className="flex flex-wrap gap-1">
                {tokenStats?.models_used?.map((model, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {model}
                  </Badge>
                )) || <span className="text-sm text-gray-500">Нет данных</span>}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Недавняя активность</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <Clock className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>История активности будет отображаться здесь</p>
            <p className="text-sm mt-2">После запуска парсинга и анализа постов</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}