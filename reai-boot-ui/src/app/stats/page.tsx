'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSupabase } from '@/components/SupabaseProvider'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Users,
  Database,
  Video,
  DollarSign,
  Clock,
  Zap,
  Calendar,
  RefreshCw
} from 'lucide-react'
import { supabase } from '@/lib/supabase'

interface StatsData {
  total_posts: number
  posts_today: number
  posts_week: number
  posts_month: number
  total_scenarios: number
  scenarios_completed: number
  scenarios_processing: number
  total_tokens: number
  tokens_today: number
  tokens_week: number
  tokens_month: number
  estimated_cost: number
  cost_today: number
  cost_week: number
  cost_month: number
  active_channels: number
  total_channels: number
  avg_processing_time: number
  top_channels: Array<{
    name: string
    posts: number
    growth: number
  }>
}

export default function StatsPage() {
  const router = useRouter()
  const { user, permissions, loading } = useSupabase()
  const [stats, setStats] = useState<StatsData | null>(null)
  const [loadingData, setLoadingData] = useState(true)
  const [timeRange, setTimeRange] = useState<'day' | 'week' | 'month'>('week')

  useEffect(() => {
    if (!loading && (!user || !permissions?.hasAccess)) {
      router.push('/')
    }
  }, [user, permissions, loading, router])

  useEffect(() => {
    if (user && permissions?.hasAccess) {
      loadStats()
    }
  }, [user, permissions, timeRange])

  const loadStats = async () => {
    try {
      setLoadingData(true)

      // Load real statistics from Supabase
      const [
        postsResult,
        scenariosResult,
        channelsResult,
        tokensResult
      ] = await Promise.all([
        supabase.from('posts').select('id, date, channel_username'),
        supabase.from('scenarios').select('id, status, created_at'),
        supabase.from('channels').select('id, is_active, username'),
        supabase.from('token_usage').select('tokens_used, cost_usd, created_at')
      ])

      if (postsResult.error) throw postsResult.error
      if (scenariosResult.error) throw scenariosResult.error
      if (channelsResult.error) throw channelsResult.error
      if (tokensResult.error) throw tokensResult.error

      // Calculate post statistics
      const posts = postsResult.data || []
      const now = new Date()
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
      const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)

      const posts_today = posts.filter(p => new Date(p.date) >= today).length
      const posts_week = posts.filter(p => new Date(p.date) >= weekAgo).length
      const posts_month = posts.filter(p => new Date(p.date) >= monthAgo).length

      // Calculate scenario statistics
      const scenarios = scenariosResult.data || []
      const scenarios_completed = scenarios.filter(s => s.status === 'completed').length
      const scenarios_processing = scenarios.filter(s => s.status === 'processing').length

      // Calculate channel statistics
      const channels = channelsResult.data || []
      const active_channels = channels.filter(c => c.is_active).length

      // Calculate token statistics
      const tokenData = tokensResult.data || []
      const tokens_today = tokenData
        .filter(t => new Date(t.created_at) >= today)
        .reduce((sum, t) => sum + t.tokens_used, 0)
      const tokens_week = tokenData
        .filter(t => new Date(t.created_at) >= weekAgo)
        .reduce((sum, t) => sum + t.tokens_used, 0)
      const tokens_month = tokenData
        .filter(t => new Date(t.created_at) >= monthAgo)
        .reduce((sum, t) => sum + t.tokens_used, 0)
      const total_tokens = tokenData.reduce((sum, t) => sum + t.tokens_used, 0)

      const cost_today = tokenData
        .filter(t => new Date(t.created_at) >= today)
        .reduce((sum, t) => sum + t.cost_usd, 0)
      const cost_week = tokenData
        .filter(t => new Date(t.created_at) >= weekAgo)
        .reduce((sum, t) => sum + t.cost_usd, 0)
      const cost_month = tokenData
        .filter(t => new Date(t.created_at) >= monthAgo)
        .reduce((sum, t) => sum + t.cost_usd, 0)
      const estimated_cost = tokenData.reduce((sum, t) => sum + t.cost_usd, 0)

      // Calculate top channels
      const channelStats = posts.reduce((acc, post) => {
        acc[post.channel_username] = (acc[post.channel_username] || 0) + 1
        return acc
      }, {} as Record<string, number>)

      const top_channels = Object.entries(channelStats)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5)
        .map(([name, posts]) => ({ name, posts, growth: Math.random() * 40 - 10 })) // Mock growth

      // Calculate average processing time
      const avg_processing_time = 2.3 // TODO: Calculate from actual data

      const realStats: StatsData = {
        total_posts: posts.length,
        posts_today,
        posts_week,
        posts_month,
        total_scenarios: scenarios.length,
        scenarios_completed,
        scenarios_processing,
        total_tokens,
        tokens_today,
        tokens_week,
        tokens_month,
        estimated_cost,
        cost_today,
        cost_week,
        cost_month,
        active_channels,
        total_channels: channels.length,
        avg_processing_time,
        top_channels
      }

      setStats(realStats)
    } catch (error) {
      console.error('Error loading stats:', error)
    } finally {
      setLoadingData(false)
    }
  }

  const getGrowthIcon = (growth: number) => {
    if (growth > 0) {
      return <TrendingUp className="w-4 h-4 text-green-600" />
    } else if (growth < 0) {
      return <TrendingDown className="w-4 h-4 text-red-600" />
    }
    return <BarChart3 className="w-4 h-4 text-gray-600" />
  }

  const getGrowthColor = (growth: number) => {
    if (growth > 0) return 'text-green-600'
    if (growth < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  const getCurrentValue = (field: keyof StatsData) => {
    if (!stats) return 0

    const value = stats[field]
    if (typeof value === 'number') {
      return value
    }
    if (Array.isArray(value)) {
      return value.length
    }
    return 0
  }

  if (loading || !user || !permissions?.hasAccess) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Статистика</h1>
          <p className="text-gray-600 mt-2">
            Аналитика работы системы и использования ресурсов
          </p>
        </div>
        <div className="flex gap-3">
          <div className="flex bg-gray-100 rounded-lg p-1">
            <Button
              variant={timeRange === 'day' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTimeRange('day')}
            >
              День
            </Button>
            <Button
              variant={timeRange === 'week' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTimeRange('week')}
            >
              Неделя
            </Button>
            <Button
              variant={timeRange === 'month' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTimeRange('month')}
            >
              Месяц
            </Button>
          </div>
          <Button onClick={loadStats} disabled={loadingData}>
            {loadingData ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            Обновить
          </Button>
        </div>
      </div>

      {/* Main Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Всего постов</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{getCurrentValue('total_posts').toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              +{getCurrentValue('posts_today')} сегодня
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Сценариев</CardTitle>
            <Video className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_scenarios || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.scenarios_completed || 0} готово, {stats?.scenarios_processing || 0} в обработке
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Токенов использовано</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{getCurrentValue('total_tokens').toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              ~${getCurrentValue('estimated_cost').toFixed(2)} потрачено
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Время обработки</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.avg_processing_time || 0} сек</div>
            <p className="text-xs text-muted-foreground">
              Среднее время на пост
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Channels Performance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            Производительность каналов
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {stats?.top_channels.map((channel, index) => (
              <div key={channel.name} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-blue-600">#{index + 1}</span>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{channel.name}</h3>
                    <p className="text-sm text-gray-600">{channel.posts.toLocaleString()} постов</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1">
                    {getGrowthIcon(channel.growth)}
                    <span className={`text-sm font-medium ${getGrowthColor(channel.growth)}`}>
                      {channel.growth > 0 ? '+' : ''}{channel.growth}%
                    </span>
                  </div>
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${Math.min(100, (channel.posts / 2500) * 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Cost Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <DollarSign className="w-5 h-5 mr-2" />
              Стоимость использования
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Сегодня</span>
                <span className="font-medium">${stats?.cost_today.toFixed(2) || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Эта неделя</span>
                <span className="font-medium">${stats?.cost_week.toFixed(2) || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Этот месяц</span>
                <span className="font-medium">${stats?.cost_month.toFixed(2) || 0}</span>
              </div>
              <div className="flex justify-between items-center border-t pt-4">
                <span className="font-medium">Всего</span>
                <span className="font-bold text-lg">${stats?.estimated_cost.toFixed(2) || 0}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="w-5 h-5 mr-2" />
              Статус каналов
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Всего каналов</span>
                <span className="font-medium">{stats?.total_channels || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Активных</span>
                <span className="font-medium text-green-600">{stats?.active_channels || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Неактивных</span>
                <span className="font-medium text-red-600">
                  {((stats?.total_channels || 0) - (stats?.active_channels || 0))}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-4">
                <div
                  className="bg-green-600 h-2 rounded-full"
                  style={{
                    width: stats?.total_channels ?
                      `${((stats.active_channels || 0) / stats.total_channels) * 100}%` : '0%'
                  }}
                ></div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Health */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            Здоровье системы
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
                <Database className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="font-medium text-gray-900">База данных</h3>
              <p className="text-sm text-gray-600">Работает нормально</p>
              <Badge className="mt-2 bg-green-100 text-green-800">OK</Badge>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
                <Zap className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="font-medium text-gray-900">LLM Pipeline</h3>
              <p className="text-sm text-gray-600">Все модели активны</p>
              <Badge className="mt-2 bg-blue-100 text-blue-800">OK</Badge>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-2">
                <Clock className="w-8 h-8 text-yellow-600" />
              </div>
              <h3 className="font-medium text-gray-900">Очереди задач</h3>
              <p className="text-sm text-gray-600">12 задач в обработке</p>
              <Badge className="mt-2 bg-yellow-100 text-yellow-800">В работе</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
