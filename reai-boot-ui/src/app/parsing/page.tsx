'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSupabase } from '@/components/SupabaseProvider'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Database,
  Play,
  Pause,
  RotateCcw,
  Settings,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Plus,
  Power,
  PowerOff,
  Trash2,
  Activity,
  Zap,
  BarChart3
} from 'lucide-react'
import { supabase } from '@/lib/supabase'
import { apiClient } from '@/lib/api'

interface ParsingJob {
  id: string
  channel_name: string
  status: 'running' | 'completed' | 'failed' | 'paused'
  posts_found: number
  posts_processed: number
  started_at: string
  completed_at?: string
  last_error?: string
}

interface Channel {
  id: string
  name: string
  username: string
  is_active: boolean
  last_parsed?: string
  total_posts: number
  baseline?: {
    median_engagement_rate: number
    std_engagement_rate: number
    avg_engagement_rate: number
    calculation_period_days: number
    last_calculated: string
  } | null
}

export default function ParsingPage() {
  const router = useRouter()
  const { user, permissions, loading } = useSupabase()
  const [jobs, setJobs] = useState<ParsingJob[]>([])
  const [channels, setChannels] = useState<Channel[]>([])
  const [loadingData, setLoadingData] = useState(true)
  const [showAddChannel, setShowAddChannel] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [systemStatus, setSystemStatus] = useState<any>(null)

  // Настройки парсинга
  const [parsingSettings, setParsingSettings] = useState({
    daysBack: 7,
    maxPosts: 100,
    frequencyHours: 24
  })

  // Загрузка настроек из localStorage при инициализации
  useEffect(() => {
    const savedSettings = localStorage.getItem('parsingSettings')
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings)
        setParsingSettings(parsed)
      } catch (error) {
        console.error('Error loading parsing settings:', error)
      }
    }
  }, [])

  // Сохранение настроек в localStorage
  const saveSettings = () => {
    localStorage.setItem('parsingSettings', JSON.stringify(parsingSettings))
    setShowSettings(false)
  }

  useEffect(() => {
    if (!loading && (!user || !permissions?.hasAccess)) {
      router.push('/')
    }
  }, [user, permissions, loading, router])

  // Загрузка статуса системы
  const loadSystemStatus = async () => {
    try {
      const status = await apiClient.healthCheck()
      setSystemStatus(status)
    } catch (error) {
      console.error('Error loading system status:', error)
      setSystemStatus({ status: 'error', telegram_status: 'error', telegram_authorization_needed: true })
    }
  }

  useEffect(() => {
    if (user && permissions?.hasAccess) {
      loadParsingData()
      loadSystemStatus() // Загружаем статус системы
    }
  }, [user, permissions])

  // Автоматическое обновление статуса системы каждые 30 секунд
  useEffect(() => {
    if (!user || !permissions?.hasAccess) return

    const interval = setInterval(() => {
      loadSystemStatus()
    }, 30000) // 30 секунд

    return () => clearInterval(interval)
  }, [user, permissions])

  const loadParsingData = async () => {
    try {
      setLoadingData(true)

      // Load real data from Supabase
      const [channelsResult, sessionsResult] = await Promise.all([
        supabase.from('channels').select('*').order('created_at', { ascending: false }),
        supabase.from('parsing_sessions').select('*').order('started_at', { ascending: false }).limit(10)
      ])

      if (channelsResult.error) throw channelsResult.error
      if (sessionsResult.error) throw sessionsResult.error

      // Get posts count for each channel from our API
      const channelsData: Channel[] = await Promise.all(
        channelsResult.data.map(async (channel) => {
          try {
            // Get baseline data which includes all metrics
            const baselineResponse = await supabase
              .from('channel_baselines')
              .select('*')
              .eq('channel_username', channel.username)
              .single()

            const baseline = baselineResponse.data
            const postsCount = baseline?.posts_analyzed || 0

            return {
              id: channel.id,
              name: channel.title || channel.username.replace('@', ''),
              username: channel.username,
              is_active: channel.is_active,
              last_parsed: channel.last_parsed,
              total_posts: postsCount,
              baseline: baseline ? {
                median_engagement_rate: baseline.median_engagement_rate,
                std_engagement_rate: baseline.std_engagement_rate,
                avg_engagement_rate: baseline.avg_engagement_rate,
                calculation_period_days: baseline.calculation_period_days,
                last_calculated: baseline.last_calculated
              } : null
            }
          } catch (error) {
            // If baseline doesn't exist, try to count posts directly
            try {
              const postsResponse = await supabase
                .from('posts')
                .select('id', { count: 'exact', head: true })
                .eq('channel_username', channel.username)

              return {
                id: channel.id,
                name: channel.title || channel.username.replace('@', ''),
                username: channel.username,
                is_active: channel.is_active,
                last_parsed: channel.last_parsed,
                total_posts: postsResponse.count || 0
              }
            } catch (postsError) {
              return {
                id: channel.id,
                name: channel.title || channel.username.replace('@', ''),
                username: channel.username,
                is_active: channel.is_active,
                last_parsed: channel.last_parsed,
                total_posts: 0
              }
            }
          }
        })
      )

      // Convert parsing sessions to jobs
      const jobsData: ParsingJob[] = sessionsResult.data.map(session => ({
        id: session.id.toString(),
        channel_name: 'Multiple channels', // TODO: Get actual channel names
        status: session.status as 'running' | 'completed' | 'failed' | 'paused',
        posts_found: session.posts_found || 0,
        posts_processed: session.posts_found || 0, // Assume all processed if completed
        started_at: session.started_at,
        completed_at: session.completed_at
      }))

      setChannels(channelsData)
      setJobs(jobsData)
    } catch (error) {
      console.error('Error loading parsing data:', error)
    } finally {
      setLoadingData(false)
    }
  }



  const startParsing = async (channelName: string) => {
    try {
      console.log(`Starting parsing for ${channelName}`)

      // Проверяем статус системы перед запуском
      console.log('Проверяем статус системы...')
      if (!systemStatus) {
        await loadSystemStatus()
      }

      if (systemStatus?.telegram_authorization_needed) {
        alert('❌ Ошибка: Telegram не авторизован!\n\nПерейдите в раздел "Администрирование" → "Telegram Auth" для настройки авторизации.')
        return
      }

      if (systemStatus?.telegram_status !== 'healthy' && systemStatus?.telegram_status !== 'available') {
        alert('❌ Ошибка: Telegram недоступен!\n\nПроверьте подключение к Telegram API.')
        return
      }

      console.log('✅ Система готова, запускаем парсинг')

      // Вызываем API для запуска парсинга
      const result = await apiClient.startChannelParsing(
        channelName,
        parsingSettings.daysBack,
        parsingSettings.maxPosts
      )
      console.log('Parsing started:', result)

      // Обновляем UI с реальными данными
      setJobs(prev => [...prev, {
        id: result.session_id.toString(),
        channel_name: channelName,
        status: 'running' as const,
        posts_found: 0,
        posts_processed: 0,
        started_at: result.started_at
      }])

      // Перезагружаем статус системы и данные через 2 секунды
      setTimeout(() => {
        loadParsingData()
        loadSystemStatus()
      }, 2000)

    } catch (error) {
      console.error('Error starting parsing:', error)
      // Показываем ошибку пользователю
      alert(`Ошибка запуска парсинга: ${error instanceof Error ? error.message : 'Неизвестная ошибка'}`)
    }
  }

  const stopParsing = async (jobId: string) => {
    try {
      // TODO: Implement actual parsing stop
      console.log(`Stopping parsing job ${jobId}`)

      // Update UI optimistically
      setJobs(prev => prev.map(job =>
        job.id === jobId
          ? { ...job, status: 'paused' as const }
          : job
      ))
    } catch (error) {
      console.error('Error stopping parsing:', error)
    }
  }

  const startBulkParsing = async (daysBack: number = 7, maxPosts: number = 100) => {
    try {
      console.log('Starting bulk parsing for all active channels')

      // Проверяем статус системы перед запуском
      console.log('Проверяем статус системы...')
      if (!systemStatus) {
        await loadSystemStatus()
      }

      if (systemStatus?.telegram_authorization_needed) {
        alert('❌ Ошибка: Telegram не авторизован!\n\nПерейдите в раздел "Администрирование" → "Telegram Auth" для настройки авторизации.')
        return
      }

      if (systemStatus?.telegram_status !== 'healthy' && systemStatus?.telegram_status !== 'available') {
        alert('❌ Ошибка: Telegram недоступен!\n\nПроверьте подключение к Telegram API.')
        return
      }

      // Получаем список всех активных каналов
      const activeChannels = channels
        .filter(channel => channel.is_active)
        .map(channel => channel.username)

      if (activeChannels.length === 0) {
        alert('Нет активных каналов для парсинга')
        return
      }

      // Вызываем API для массового парсинга
      const result = await apiClient.startBulkParsing(activeChannels, daysBack, maxPosts)
      console.log('Bulk parsing started:', result)

      // Добавляем новую задачу в список
      setJobs(prev => [...prev, {
        id: result.session_id.toString(),
        channel_name: `${activeChannels.length} каналов`,
        status: 'running' as const,
        posts_found: 0,
        posts_processed: 0,
        started_at: new Date().toISOString()
      }])

      // Перезагружаем статус системы и данные через 3 секунды
      setTimeout(() => {
        loadParsingData()
        loadSystemStatus()
      }, 3000)

    } catch (error) {
      console.error('Error starting bulk parsing:', error)
      alert(`Ошибка запуска массового парсинга: ${error instanceof Error ? error.message : 'Неизвестная ошибка'}`)
    }
  }

  const toggleChannelStatus = async (channelId: string, currentStatus: boolean) => {
    try {
      const newStatus = !currentStatus
      console.log(`${newStatus ? 'Activating' : 'Deactivating'} channel ${channelId}`)

      // Вызываем API для обновления статуса канала
      await apiClient.updateChannel(parseInt(channelId), {
        username: channels.find(c => c.id === channelId)?.username,
        title: channels.find(c => c.id === channelId)?.name,
        is_active: newStatus,
        parse_frequency_hours: 24
      })

      // Обновляем локальное состояние
      setChannels(prev => prev.map(channel =>
        channel.id === channelId
          ? { ...channel, is_active: newStatus }
          : channel
      ))

      console.log(`Channel ${channelId} ${newStatus ? 'activated' : 'deactivated'}`)

    } catch (error) {
      console.error('Error toggling channel status:', error)
      alert(`Ошибка изменения статуса канала: ${error instanceof Error ? error.message : 'Неизвестная ошибка'}`)
    }
  }

  const deleteChannel = async (channelId: string) => {
    if (!confirm('Вы уверены, что хотите удалить этот канал? Это действие нельзя отменить.')) {
      return
    }

    try {
      console.log(`Deleting channel ${channelId}`)

      // Вызываем API для удаления канала
      await apiClient.deleteChannel(parseInt(channelId))

      // Удаляем канал из локального состояния
      setChannels(prev => prev.filter(channel => channel.id !== channelId))

      console.log(`Channel ${channelId} deleted`)

    } catch (error) {
      console.error('Error deleting channel:', error)
      alert(`Ошибка удаления канала: ${error instanceof Error ? error.message : 'Неизвестная ошибка'}`)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'running':
        return <Badge className="bg-green-100 text-green-800">Запущен</Badge>
      case 'completed':
        return <Badge className="bg-blue-100 text-blue-800">Завершен</Badge>
      case 'failed':
        return <Badge className="bg-red-100 text-red-800">Ошибка</Badge>
      case 'paused':
        return <Badge className="bg-yellow-100 text-yellow-800">Остановлен</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-600" />
      case 'paused':
        return <Pause className="w-4 h-4 text-yellow-600" />
      default:
        return <Database className="w-4 h-4" />
    }
  }

  const activeJobs = jobs.filter(job => job.status === 'running')
  const completedJobs = jobs.filter(job => job.status === 'completed')

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
          <h1 className="text-3xl font-bold text-gray-900">Парсинг</h1>
          <p className="text-gray-600 mt-2">
            Управление парсингом Telegram каналов
          </p>
        </div>
        <div className="flex gap-3">
          <Button onClick={loadSystemStatus} variant="outline">
            <Activity className="w-4 h-4 mr-2" />
            Обновить статус
          </Button>
          <Button onClick={loadParsingData} disabled={loadingData}>
            {loadingData ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            ) : (
              <RotateCcw className="w-4 h-4 mr-2" />
            )}
            Обновить данные
          </Button>
          <Button
            onClick={() => startBulkParsing(parsingSettings.daysBack, parsingSettings.maxPosts)}
            variant="outline"
            disabled={channels.filter(c => c.is_active).length === 0}
          >
            <Database className="w-4 h-4 mr-2" />
            Запустить все каналы
          </Button>
          <Button onClick={() => setShowSettings(true)} variant="outline">
            <Settings className="w-4 h-4 mr-2" />
            Настройки парсинга
          </Button>
          <Button onClick={() => setShowAddChannel(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Добавить канал
          </Button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <Database className="h-8 w-8 text-blue-600 mr-4" />
              <div>
                <p className="text-2xl font-bold">{channels.filter(c => c.is_active).length}</p>
                <p className="text-sm text-gray-600">Активных каналов</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center mr-4">
                <Play className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-2xl font-bold">{activeJobs.length}</p>
                <p className="text-sm text-gray-600">Запущенных задач</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-600 mr-4" />
              <div>
                <p className="text-2xl font-bold">{completedJobs.length}</p>
                <p className="text-sm text-gray-600">Завершенных задач</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-purple-600 mr-4" />
              <div>
                <p className="text-2xl font-bold">
                  {jobs.reduce((sum, job) => sum + job.posts_processed, 0)}
                </p>
                <p className="text-sm text-gray-600">Обработано постов</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="w-5 h-5 mr-2 text-blue-600" />
            Статус системы
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Telegram Status */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center">
                <Database className="w-5 h-5 text-blue-500 mr-3" />
                <div>
                  <p className="font-medium text-gray-900">Telegram API</p>
                  <p className="text-sm text-gray-600">Статус подключения</p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                !systemStatus ? 'bg-gray-100 text-gray-800' :
                systemStatus.telegram_status === 'healthy' ? 'bg-green-100 text-green-800' :
                systemStatus.telegram_authorization_needed ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {!systemStatus ? 'Проверка...' :
                 systemStatus.telegram_status === 'healthy' ? 'Подключено' :
                 systemStatus.telegram_authorization_needed ? 'Требуется авторизация' :
                 'Недоступен'}
              </span>
            </div>

            {/* API Status */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center">
                <Activity className="w-5 h-5 text-green-500 mr-3" />
                <div>
                  <p className="font-medium text-gray-900">Backend API</p>
                  <p className="text-sm text-gray-600">FastAPI сервер</p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                !systemStatus ? 'bg-gray-100 text-gray-800' :
                systemStatus.status === 'healthy' ? 'bg-green-100 text-green-800' :
                'bg-red-100 text-red-800'
              }`}>
                {!systemStatus ? 'Проверка...' :
                 systemStatus.status === 'healthy' ? 'Работает' :
                 'Ошибка'}
              </span>
            </div>

            {/* LLM Status */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center">
                <Zap className="w-5 h-5 text-purple-500 mr-3" />
                <div>
                  <p className="font-medium text-gray-900">LLM Сервисы</p>
                  <p className="text-sm text-gray-600">OpenAI/Claude</p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                !systemStatus || !systemStatus.llm_status ? 'bg-gray-100 text-gray-800' :
                Object.values(systemStatus.llm_status).every(v => v) ? 'bg-green-100 text-green-800' :
                'bg-red-100 text-red-800'
              }`}>
                {!systemStatus || !systemStatus.llm_status ? 'Проверка...' :
                 Object.values(systemStatus.llm_status).every(v => v) ? 'Готовы' :
                 'Проблемы'}
              </span>
            </div>
          </div>

          {/* Warnings */}
          {systemStatus?.telegram_authorization_needed && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex">
                <AlertCircle className="w-5 h-5 text-red-400 mr-3 mt-0.5" />
                <div>
                  <h3 className="text-sm font-medium text-red-800">
                    Требуется авторизация Telegram
                  </h3>
                  <p className="mt-1 text-sm text-red-700">
                    Для работы парсинга необходимо авторизоваться в Telegram.
                    Перейдите в раздел "Администрирование" → "Telegram Auth".
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Active Jobs */}
      {activeJobs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-green-700">
              <Play className="w-5 h-5 mr-2" />
              Активные задачи парсинга
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {activeJobs.map((job) => (
                <div key={job.id} className="border border-green-200 bg-green-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(job.status)}
                      <div>
                        <h3 className="font-medium text-gray-900">{job.channel_name}</h3>
                        <p className="text-sm text-gray-600">
                          Обработано: {job.posts_processed} из {job.posts_found} постов
                        </p>
                        <p className="text-xs text-gray-500">
                          Начато: {new Date(job.started_at).toLocaleString('ru-RU')}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className="text-sm font-medium">
                          {Math.round((job.posts_processed / job.posts_found) * 100)}%
                        </div>
                        <div className="w-24 bg-gray-200 rounded-full h-2 mt-1">
                          <div
                            className="bg-green-600 h-2 rounded-full"
                            style={{
                              width: `${Math.round((job.posts_processed / job.posts_found) * 100)}%`
                            }}
                          ></div>
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => stopParsing(job.id)}
                      >
                        <Pause className="w-4 h-4 mr-2" />
                        Остановить
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Channels Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Database className="w-5 h-5 mr-2" />
            Каналы для мониторинга
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {channels.map((channel) => (
              <div key={channel.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${
                    channel.is_active ? 'bg-green-500' : 'bg-gray-400'
                  }`}></div>
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{channel.name}</h3>
                    <p className="text-sm text-gray-600">{channel.username}</p>
                    <div className="text-xs text-gray-500 space-y-1">
                      <p>Постов: {channel.total_posts}</p>
                      <p>Последний парсинг: {channel.last_parsed ?
                        new Date(channel.last_parsed).toLocaleString('ru-RU') :
                        'Никогда'
                      }</p>
                    </div>
                  </div>

                  {/* Viral Metrics */}
                  <div className="text-right text-xs space-y-1">
                    <div className="flex items-center gap-1">
                      <TrendingUp className="w-3 h-3 text-blue-500" />
                      <span>Медиана: {channel.baseline ?
                        `${(channel.baseline.median_engagement_rate * 100).toFixed(1)}%` :
                        'Н/Д'
                      }</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <BarChart3 className="w-3 h-3 text-green-500" />
                      <span>Средняя: {channel.baseline ?
                        `${(channel.baseline.avg_engagement_rate * 100).toFixed(1)}%` :
                        'Н/Д'
                      }</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Zap className="w-3 h-3 text-purple-500" />
                      <span>Статус: {channel.baseline ? 'Рассчитан' : 'Не рассчитан'}</span>
                    </div>
                    {channel.baseline?.last_calculated && (
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-gray-500" />
                        <span>Обновлено: {new Date(channel.baseline.last_calculated).toLocaleDateString('ru-RU')}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Badge variant={channel.is_active ? "default" : "secondary"}>
                    {channel.is_active ? 'Активен' : 'Отключен'}
                  </Badge>

                  {channel.is_active ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => startParsing(channel.username)}
                      disabled={jobs.some(job => job.channel_name === channel.username && job.status === 'running')}
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Запустить
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => toggleChannelStatus(channel.id, channel.is_active)}
                    >
                      <Power className="w-4 h-4 mr-2" />
                      Включить
                    </Button>
                  )}

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => toggleChannelStatus(channel.id, channel.is_active)}
                  >
                    {channel.is_active ? (
                      <>
                        <PowerOff className="w-4 h-4 mr-2" />
                        Отключить
                      </>
                    ) : (
                      <>
                        <Power className="w-4 h-4 mr-2" />
                        Включить
                      </>
                    )}
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => deleteChannel(channel.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Удалить
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Jobs History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Clock className="w-5 h-5 mr-2" />
            История парсинга
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {jobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
                <div className="flex items-center gap-3">
                  {getStatusIcon(job.status)}
                  <div>
                    <p className="font-medium text-gray-900">{job.channel_name}</p>
                    <p className="text-sm text-gray-600">
                      {job.posts_processed} постов обработано
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  {getStatusBadge(job.status)}
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(job.started_at).toLocaleString('ru-RU')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Settings Modal */}
      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Настройки парсинга</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="daysBack">Дни назад для парсинга</Label>
              <Input
                id="daysBack"
                type="number"
                min="1"
                max="30"
                value={parsingSettings.daysBack}
                onChange={(e) => setParsingSettings(prev => ({
                  ...prev,
                  daysBack: parseInt(e.target.value) || 7
                }))}
              />
              <p className="text-sm text-gray-500">
                Сколько дней назад искать посты (1-30 дней)
              </p>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="maxPosts">Максимум постов</Label>
              <Input
                id="maxPosts"
                type="number"
                min="10"
                max="1000"
                value={parsingSettings.maxPosts}
                onChange={(e) => setParsingSettings(prev => ({
                  ...prev,
                  maxPosts: parseInt(e.target.value) || 100
                }))}
              />
              <p className="text-sm text-gray-500">
                Максимальное количество постов для обработки (10-1000)
              </p>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="frequencyHours">Частота парсинга (часы)</Label>
              <Select
                value={parsingSettings.frequencyHours.toString()}
                onValueChange={(value) => setParsingSettings(prev => ({
                  ...prev,
                  frequencyHours: parseInt(value)
                }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="6">Каждые 6 часов</SelectItem>
                  <SelectItem value="12">Каждые 12 часов</SelectItem>
                  <SelectItem value="24">Раз в сутки</SelectItem>
                  <SelectItem value="48">Раз в 2 дня</SelectItem>
                  <SelectItem value="168">Раз в неделю</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-gray-500">
                Как часто автоматически запускать парсинг
              </p>
            </div>
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setShowSettings(false)}>
              Отмена
            </Button>
            <Button onClick={saveSettings}>
              Сохранить настройки
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
