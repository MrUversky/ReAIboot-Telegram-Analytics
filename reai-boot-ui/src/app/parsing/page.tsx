'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSupabase } from '@/components/SupabaseProvider'
import toast from 'react-hot-toast'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
  BarChart3,
  Check,
  X,
  AlertTriangle,
  Info
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

  // Состояния для добавления каналов
  const [channelsInput, setChannelsInput] = useState('')
  const [channelTitle, setChannelTitle] = useState('')
  const [channelCategory, setChannelCategory] = useState('')
  const [isAddingChannels, setIsAddingChannels] = useState(false)
  const [addResults, setAddResults] = useState<{
    success: { username: string; title: string }[]
    duplicates: { username: string }[]
    errors: { username: string; error: string }[]
  }>({ success: [], duplicates: [], errors: [] })

  // Состояния для добавления из папки
  const [folderLink, setFolderLink] = useState('')
  const [isAddingFromFolder, setIsAddingFromFolder] = useState(false)
  const [folderResults, setFolderResults] = useState<{
    message: string
    folder_title: string
    added: Array<{ username: string; title: string; id: number }>
    duplicates: Array<{ username: string; title: string }>
    errors: Array<{ username: string; error: string }>
    stats: {
      total: number
      added: number
      duplicates: number
      errors: number
    }
    recommendation?: string
    suggestions?: string[]
    error_type?: string
  } | null>(null)

  // Состояния для работы с папками пользователя
  const [userFolders, setUserFolders] = useState<{
    message: string
    folders: Array<{
      id: number
      name: string
      channels: Array<{
        id: number
        username: string | null
        title: string
        participants_count: number | null
        type: string
      }>
    }>
    stats: {
      total_folders: number
      total_channels: number
    }
  } | null>(null)
  const [selectedUserFolder, setSelectedUserFolder] = useState<number | null>(null)
  const [isLoadingFolders, setIsLoadingFolders] = useState(false)
  const [isAddingFromUserFolder, setIsAddingFromUserFolder] = useState(false)
  const [userFolderResults, setUserFolderResults] = useState<{
    message: string
    folder_name: string
    added: Array<{ username: string; title: string; id: number }>
    duplicates: Array<{ username: string; title: string }>
    errors: Array<{ username: string; error: string }>
    stats: {
      total: number
      added: number
      duplicates: number
      errors: number
    }
  } | null>(null)

  // Состояния для работы с каналами пользователя
  const [userChannels, setUserChannels] = useState<{
    message: string
    channels: Array<{
      id: number
      username: string | null
      title: string
      participants_count: number | null
      type: string
    }>
    stats: {
      total_channels: number
    }
  } | null>(null)
  const [selectedChannelIds, setSelectedChannelIds] = useState<number[]>([])
  const [isLoadingChannels, setIsLoadingChannels] = useState(false)
  const [isAddingFromUserChannels, setIsAddingFromUserChannels] = useState(false)
  const [userChannelsResults, setUserChannelsResults] = useState<{
    message: string
    added: Array<{ username: string; title: string; id: number }>
    duplicates: Array<{ username: string; title: string }>
    errors: Array<{ username: string; error: string }>
    stats: {
      selected: number
      added: number
      duplicates: number
      errors: number
    }
  } | null>(null)

  // Переключатель режима добавления
  const [addMode, setAddMode] = useState<'channels' | 'folder' | 'user-folder' | 'user-channels'>('channels')

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
        toast.error('❌ Telegram не авторизован!\n\nПерейдите в раздел "Администрирование" → "Telegram Auth" для настройки авторизации.')
        return
      }

      if (systemStatus?.telegram_status !== 'healthy' && systemStatus?.telegram_status !== 'available') {
        toast.error('❌ Telegram недоступен!\n\nПроверьте подключение к Telegram API.')
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
        toast.error('❌ Telegram не авторизован!\n\nПерейдите в раздел "Администрирование" → "Telegram Auth" для настройки авторизации.')
        return
      }

      if (systemStatus?.telegram_status !== 'healthy' && systemStatus?.telegram_status !== 'available') {
        toast.error('❌ Telegram недоступен!\n\nПроверьте подключение к Telegram API.')
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

  // Функции для обработки каналов
  const parseChannelInput = (input: string): string[] => {
    // Разделяем по различным разделителям: запятые, пробелы, переносы строк
    const separators = /[,\s\n]+/
    const rawChannels = input.split(separators).filter(channel => channel.trim().length > 0)

    // Очищаем каждый канал от @ и ссылок
    return rawChannels.map(channel => {
      let cleanChannel = channel.trim()

      // Удаляем @ если есть
      if (cleanChannel.startsWith('@')) {
        cleanChannel = cleanChannel.slice(1)
      }

      // Если это ссылка, извлекаем username
      if (cleanChannel.includes('t.me/')) {
        const parts = cleanChannel.split('t.me/')
        if (parts.length > 1) {
          cleanChannel = parts[1].split('/')[0] // Берем часть до первого слэша
        }
      }

      return cleanChannel
    }).filter(channel => channel.length > 0)
  }

  const normalizeUsername = (username: string): string => {
    let normalized = username.trim()
    if (normalized.startsWith('@')) {
      normalized = normalized.slice(1)
    }
    return normalized
  }

  const addChannels = async () => {
    const parsedChannels = parseChannelInput(channelsInput)

    if (parsedChannels.length === 0) {
      alert('Пожалуйста, введите хотя бы один канал')
      return
    }

    setIsAddingChannels(true)
    setAddResults({ success: [], duplicates: [], errors: [] })

    const results: {
      success: { username: string; title: string }[]
      duplicates: { username: string }[]
      errors: { username: string; error: string }[]
    } = { success: [], duplicates: [], errors: [] }

    try {
      for (const username of parsedChannels) {
        try {
          // Нормализуем username для проверки дубликатов
          const normalizedUsername = normalizeUsername(username)

          // Проверяем, существует ли уже канал (сравниваем нормализованные имена)
          const existingChannel = channels.find(c => normalizeUsername(c.username) === normalizedUsername)

          if (existingChannel) {
            results.duplicates.push({ username: normalizedUsername })
            continue
          }

          // Создаем новый канал
          const channelData = {
            username,
            title: channelTitle || username, // Используем username как заголовок если не указан
            category: channelCategory,
            is_active: true,
            parse_frequency_hours: 24
          }

          const result = await apiClient.createChannel(channelData)
          results.success.push({
            username: result.channel.username,
            title: result.channel.title
          })

          // Добавляем канал в локальное состояние
          setChannels(prev => [...prev, {
            id: result.channel.id.toString(),
            name: result.channel.title,
            username: result.channel.username,
            is_active: result.channel.is_active,
            total_posts: 0
          }])

        } catch (error: any) {
          let errorMessage = 'Неизвестная ошибка'

          if (error.message?.includes('уже существует')) {
            results.duplicates.push({ username })
          } else {
            if (error.status === 409) {
              results.duplicates.push({ username })
            } else {
              errorMessage = error.message || errorMessage
              results.errors.push({ username, error: errorMessage })
            }
          }
        }
      }

      setAddResults(results)

      // Показываем итоговое уведомление
      const totalProcessed = results.success.length + results.duplicates.length + results.errors.length
      const successCount = results.success.length
      const duplicateCount = results.duplicates.length
      const errorCount = results.errors.length

      let message = `Обработано ${totalProcessed} каналов.`

      if (successCount > 0) {
        message += `\n✅ Добавлено: ${successCount}`
      }
      if (duplicateCount > 0) {
        message += `\n⚠️ Уже существуют: ${duplicateCount}`
      }
      if (errorCount > 0) {
        message += `\n❌ Ошибки: ${errorCount}`
      }

      alert(message)

      // Очищаем форму при успехе
      if (successCount > 0) {
        setChannelsInput('')
        setChannelTitle('')
        setChannelCategory('')
      }

    } catch (error) {
      console.error('Error adding channels:', error)
      alert(`Ошибка при добавлении каналов: ${error instanceof Error ? error.message : 'Неизвестная ошибка'}`)
    } finally {
      setIsAddingChannels(false)
    }
  }

  const resetAddChannelModal = () => {
    setChannelsInput('')
    setChannelTitle('')
    setChannelCategory('')
    setAddResults({ success: [], duplicates: [], errors: [] })
    setFolderLink('')
    setFolderResults(null)
    setSelectedUserFolder(null)
    setUserFolderResults(null)
    setSelectedChannelIds([])
    setUserChannelsResults(null)
    setAddMode('channels')
    setShowAddChannel(false)
  }

  // Функция для загрузки папок пользователя
  const loadUserFolders = async () => {
    setIsLoadingFolders(true)
    try {
      const result = await apiClient.getUserFolders()
      setUserFolders(result)
    } catch (error: any) {
      console.error('Ошибка загрузки папок:', error)
      toast.error(error.message || 'Ошибка загрузки папок пользователя')
    } finally {
      setIsLoadingFolders(false)
    }
  }

  // Функция для загрузки каналов пользователя
  const loadUserChannels = async () => {
    setIsLoadingChannels(true)
    try {
      const result = await apiClient.getUserChannels()
      setUserChannels(result)
    } catch (error: any) {
      console.error('Ошибка загрузки каналов:', error)
      toast.error(error.message || 'Ошибка загрузки каналов пользователя')
    } finally {
      setIsLoadingChannels(false)
    }
  }

  // Функция для добавления каналов из папки пользователя
  const handleAddFromUserFolder = async () => {
    if (!selectedUserFolder) {
      toast.error('Выберите папку')
      return
    }

    // Проверяем статус Telegram перед добавлением
    console.log('Проверяем статус Telegram для добавления из папки пользователя...')
    if (!systemStatus) {
      await loadSystemStatus()
    }

    if (systemStatus?.telegram_authorization_needed) {
      toast.error('❌ Telegram не авторизован!\n\nПерейдите в раздел "Администрирование" → "Telegram Auth" для настройки авторизации.')
      return
    }

    if (systemStatus?.telegram_status !== 'healthy' && systemStatus?.telegram_status !== 'available') {
      toast.error('❌ Telegram недоступен!\n\nПроверьте подключение к Telegram API.')
      return
    }

    console.log('✅ Telegram готов, добавляем каналы из папки пользователя')

    setIsAddingFromUserFolder(true)
    setUserFolderResults(null)

    try {
      const result = await apiClient.createChannelsFromUserFolder(selectedUserFolder)
      setUserFolderResults(result)

      if (result.stats.added > 0) {
        toast.success(`Добавлено ${result.stats.added} каналов из папки "${result.folder_name}"`)
        // Обновляем список каналов
        await loadParsingData()
      }

      if (result.stats.duplicates > 0) {
        toast.error(`${result.stats.duplicates} каналов уже существуют`)
      }

      if (result.stats.errors > 0) {
        toast.error(`Ошибок при добавлении: ${result.stats.errors}`)
      }

    } catch (error: any) {
      console.error('Ошибка добавления из папки пользователя:', error)

      // Специальная обработка для недоступного Telegram API
      if (error.message && error.message.includes('Telegram API недоступен')) {
        toast.error('Telegram API недоступен. Авторизуйтесь в Telegram для работы с папками.')
      } else {
        toast.error(error.message || 'Ошибка добавления каналов из папки')
      }
    } finally {
      setIsAddingFromUserFolder(false)
    }
  }

  // Функция для добавления выбранных каналов пользователя
  const handleAddFromUserChannels = async () => {
    if (selectedChannelIds.length === 0) {
      toast.error('Выберите хотя бы один канал')
      return
    }

    // Проверяем статус Telegram перед добавлением
    console.log('Проверяем статус Telegram для добавления выбранных каналов...')
    if (!systemStatus) {
      await loadSystemStatus()
    }

    if (systemStatus?.telegram_authorization_needed) {
      toast.error('❌ Telegram не авторизован!\n\nПерейдите в раздел "Администрирование" → "Telegram Auth" для настройки авторизации.')
      return
    }

    if (systemStatus?.telegram_status !== 'healthy' && systemStatus?.telegram_status !== 'available') {
      toast.error('❌ Telegram недоступен!\n\nПроверьте подключение к Telegram API.')
      return
    }

    console.log('✅ Telegram готов, добавляем выбранные каналы')

    setIsAddingFromUserChannels(true)
    setUserChannelsResults(null)

    try {
      const result = await apiClient.createChannelsFromUserChannels(selectedChannelIds)
      setUserChannelsResults(result)

      if (result.stats.added > 0) {
        toast.success(`Добавлено ${result.stats.added} каналов`)
        // Обновляем список каналов
        await loadParsingData()
      }

      if (result.stats.duplicates > 0) {
        toast.error(`${result.stats.duplicates} каналов уже существуют`)
      }

      if (result.stats.errors > 0) {
        toast.error(`Ошибок при добавлении: ${result.stats.errors}`)
      }

    } catch (error: any) {
      console.error('Ошибка добавления выбранных каналов:', error)

      // Специальная обработка для недоступного Telegram API
      if (error.message && error.message.includes('Telegram API недоступен')) {
        toast.error('Telegram API недоступен. Авторизуйтесь в Telegram для работы с каналами.')
      } else {
        toast.error(error.message || 'Ошибка добавления каналов')
      }
    } finally {
      setIsAddingFromUserChannels(false)
    }
  }

  // Функции для управления выбором каналов
  const handleChannelSelect = (channelId: number, selected: boolean) => {
    if (selected) {
      setSelectedChannelIds(prev => [...prev, channelId])
    } else {
      setSelectedChannelIds(prev => prev.filter(id => id !== channelId))
    }
  }

  const handleSelectAllChannels = () => {
    if (userChannels) {
      const allChannelIds = userChannels.channels.map(ch => ch.id)
      setSelectedChannelIds(allChannelIds)
    }
  }

  const handleDeselectAllChannels = () => {
    setSelectedChannelIds([])
  }

  // Функция для добавления каналов из папки
  const handleAddFromFolder = async () => {
    if (!folderLink.trim()) {
      toast.error('Введите ссылку на папку')
      return
    }

    // Валидация формата ссылки
    const link = folderLink.trim()
    if (!link.includes('addlist/') && !link.includes('t.me/addlist/')) {
      toast.error('Неверный формат ссылки. Используйте ссылку вида:\n• https://t.me/addlist/slug\n• addlist/slug')
      return
    }

    // Проверяем статус Telegram перед добавлением
    console.log('Проверяем статус Telegram для добавления из папки...')
    if (!systemStatus) {
      await loadSystemStatus()
    }

    if (systemStatus?.telegram_authorization_needed) {
      toast.error('❌ Telegram не авторизован!\n\nПерейдите в раздел "Администрирование" → "Telegram Auth" для настройки авторизации.')
      return
    }

    if (systemStatus?.telegram_status !== 'healthy' && systemStatus?.telegram_status !== 'available') {
      toast.error('❌ Telegram недоступен!\n\nПроверьте подключение к Telegram API.')
      return
    }

    console.log('✅ Telegram готов, добавляем каналы из папки')

    setIsAddingFromFolder(true)
    setFolderResults(null)

    try {
      const result = await apiClient.createChannelsFromFolder(link)

      // Специальная обработка для случая, когда папка уже добавлена
      if ((result as any).error_type === 'folder_already_joined') {
        toast.error('📁 Папка уже добавлена в ваш Telegram!')
        setFolderResults({
          message: result.message,
          folder_title: `Ссылка: ${(result as any).folder_link}`,
          added: [],
          duplicates: [],
          errors: [],
          stats: result.stats,
          recommendation: (result as any).recommendation,
          suggestions: (result as any).suggestions
        })
        return
      }

      setFolderResults(result)

      if (result.stats.added > 0) {
        toast.success(`Добавлено ${result.stats.added} каналов из папки "${result.folder_title}"`)
        // Обновляем список каналов
        await loadParsingData()
      }

      if (result.stats.duplicates > 0) {
        toast.error(`${result.stats.duplicates} каналов уже существуют`)
      }

      if (result.stats.errors > 0) {
        toast.error(`Ошибок при добавлении: ${result.stats.errors}`)
      }

    } catch (error: any) {
      console.error('Ошибка добавления из папки:', error)

      // Специальная обработка для недоступного Telegram API
      if (error.message && error.message.includes('Telegram API недоступен')) {
        toast.error('Telegram API недоступен. Авторизуйтесь в Telegram для работы с папками.')
      } else {
        toast.error(error.message || 'Ошибка добавления каналов из папки')
      }
    } finally {
      setIsAddingFromFolder(false)
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

      {/* Add Channel Modal */}
      <Dialog open={showAddChannel} onOpenChange={resetAddChannelModal}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <Plus className="w-5 h-5 mr-2" />
              Добавить каналы
            </DialogTitle>
          </DialogHeader>

          <Tabs value={addMode} onValueChange={(value) => setAddMode(value as 'channels' | 'folder' | 'user-folder' | 'user-channels')} className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="channels">Одиночные каналы</TabsTrigger>
              <TabsTrigger value="folder">Из ссылки на папку</TabsTrigger>
              <TabsTrigger value="user-folder">Из моих папок</TabsTrigger>
              <TabsTrigger value="user-channels">Из моих каналов</TabsTrigger>
            </TabsList>

            <TabsContent value="channels" className="space-y-6 mt-6">
              {/* Help text */}
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  <strong>Поддерживаемые форматы:</strong><br />
                  • @username или username<br />
                  • https://t.me/username<br />
                  • Несколько каналов через запятую, пробел или новую строку
                </AlertDescription>
              </Alert>

              {/* Channels input */}
              <div className="space-y-2">
                <Label htmlFor="channels-input">
                  Каналы для добавления *
                </Label>
                <Textarea
                  id="channels-input"
                  placeholder={`Примеры:
@tech_news
https://t.me/python_dev
ai_news, tech_startups
ml_research`}
                  value={channelsInput}
                  onChange={(e) => setChannelsInput(e.target.value)}
                  className="min-h-[120px] font-mono text-sm"
                />
                <p className="text-sm text-gray-500">
                  Введите каналы в любом формате. Система автоматически очистит их от @ и ссылок.
                </p>
              </div>

              {/* Preview of parsed channels */}
              {channelsInput.trim() && (
                <div className="space-y-2">
                  <Label>Предварительный просмотр:</Label>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="flex flex-wrap gap-2">
                      {parseChannelInput(channelsInput).map((channel, index) => (
                        <Badge key={index} variant="secondary" className="font-mono">
                          @{channel}
                        </Badge>
                      ))}
                    </div>
                    <p className="text-sm text-gray-600 mt-2">
                      Найдено каналов: {parseChannelInput(channelsInput).length}
                    </p>
                  </div>
                </div>
              )}

              {/* Channel details */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="channel-title">Название канала</Label>
                  <Input
                    id="channel-title"
                    placeholder="Оставьте пустым для авто-определения"
                    value={channelTitle}
                    onChange={(e) => setChannelTitle(e.target.value)}
                  />
                  <p className="text-xs text-gray-500">
                    Если не указать, будет использовано имя канала
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="channel-category">Категория</Label>
                  <Select value={channelCategory} onValueChange={setChannelCategory}>
                    <SelectTrigger>
                      <SelectValue placeholder="Выберите категорию" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="tech">Технологии</SelectItem>
                      <SelectItem value="business">Бизнес</SelectItem>
                      <SelectItem value="news">Новости</SelectItem>
                      <SelectItem value="education">Образование</SelectItem>
                      <SelectItem value="entertainment">Развлечения</SelectItem>
                      <SelectItem value="other">Другое</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="folder" className="space-y-6 mt-6">
              {/* Telegram status warning */}
              {(systemStatus?.telegram_authorization_needed ||
                (systemStatus?.telegram_status !== 'healthy' && systemStatus?.telegram_status !== 'available')) && (
                <Alert className="border-red-200 bg-red-50">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <AlertDescription className="text-red-800">
                    <strong>⚠️ Telegram не готов к работе</strong><br />
                    {systemStatus?.telegram_authorization_needed
                      ? 'Необходимо авторизоваться в Telegram. Перейдите в раздел "Администрирование" → "Telegram Auth".'
                      : 'Telegram API недоступен. Проверьте подключение к Telegram.'
                    }
                  </AlertDescription>
                </Alert>
              )}

              {/* Help text for folder */}
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  <strong>Как добавить каналы из папки:</strong><br />
                  • Перейдите в Telegram Desktop или Web<br />
                  • Найдите папку с каналами (например, "AI" или "Tech")<br />
                  • Нажмите правой кнопкой на папку → "Copy Link"<br />
                  • Вставьте ссылку в поле ниже<br />
                  • Все каналы из папки будут автоматически добавлены
                </AlertDescription>
              </Alert>

              {/* Folder link input */}
              <div className="space-y-2">
                <Label htmlFor="folder-link">
                  Ссылка на папку Telegram *
                </Label>
                <Input
                  id="folder-link"
                  placeholder="https://t.me/addlist/kMKpmZjmHnU1Mjli"
                  value={folderLink}
                  onChange={(e) => setFolderLink(e.target.value)}
                  className="font-mono text-sm"
                />
                <p className="text-sm text-gray-500">
                  Вставьте ссылку на папку из Telegram. Система автоматически получит все каналы из этой папки.
                </p>
              </div>

              {/* Folder results */}
              {folderResults && (
                <div className="space-y-4">
                  <Label>Результаты добавления из папки:</Label>

                  <Alert>
                    {folderResults.recommendation ? (
                      <Info className="h-4 w-4" />
                    ) : (
                      <Check className="h-4 w-4" />
                    )}
                    <AlertDescription>
                      <strong className={folderResults.recommendation ? "text-blue-700" : "text-green-700"}>
                        {folderResults.message}
                      </strong>
                      <div className="mt-2 text-sm">
                        <div>📁 Папка: <strong>{folderResults.folder_title}</strong></div>
                        <div className="mt-1 flex gap-4">
                          <span className="text-green-600">✅ Добавлено: {folderResults.stats.added}</span>
                          <span className="text-yellow-600">⚠️ Дубликаты: {folderResults.stats.duplicates}</span>
                          <span className="text-red-600">❌ Ошибки: {folderResults.stats.errors}</span>
                        </div>

                        {folderResults.recommendation && (
                          <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                            <div className="font-medium text-blue-800 mb-2">{folderResults.recommendation}</div>
                            <ul className="space-y-1 text-blue-700">
                              {folderResults.suggestions?.map((suggestion, index) => (
                                <li key={index} className="flex items-start">
                                  <span className="mr-2">•</span>
                                  <span>{suggestion}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </AlertDescription>
                  </Alert>

                  {folderResults.added.length > 0 && (
                    <div>
                      <strong className="text-green-700">Добавленные каналы:</strong>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {folderResults.added.map((item, index) => (
                          <Badge key={index} className="bg-green-100 text-green-800">
                            @{item.username} - {item.title}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {folderResults.duplicates.length > 0 && (
                    <div>
                      <strong className="text-yellow-700">Уже существуют:</strong>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {folderResults.duplicates.map((item, index) => (
                          <Badge key={index} className="bg-yellow-100 text-yellow-800">
                            @{item.username}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {folderResults.errors.length > 0 && (
                    <div>
                      <strong className="text-red-700">Ошибки:</strong>
                      <div className="mt-2 space-y-1">
                        {folderResults.errors.map((item, index) => (
                          <div key={index} className="text-sm">
                            <Badge className="bg-red-100 text-red-800 mr-2">
                              @{item.username}
                            </Badge>
                            {item.error}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </TabsContent>

            <TabsContent value="user-folder" className="space-y-6 mt-6">
              {/* Telegram status warning */}
              {(systemStatus?.telegram_authorization_needed ||
                (systemStatus?.telegram_status !== 'healthy' && systemStatus?.telegram_status !== 'available')) && (
                <Alert className="border-red-200 bg-red-50">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <AlertDescription className="text-red-800">
                    <strong>⚠️ Telegram не готов к работе</strong><br />
                    {systemStatus?.telegram_authorization_needed
                      ? 'Необходимо авторизоваться в Telegram. Перейдите в раздел "Администрирование" → "Telegram Auth".'
                      : 'Telegram API недоступен. Проверьте подключение к Telegram.'
                    }
                  </AlertDescription>
                </Alert>
              )}

              {/* Help text for user folders */}
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  <strong>Выберите папку из ваших Telegram папок:</strong><br />
                  • Система автоматически получит все каналы из выбранной папки<br />
                  • Будут добавлены только каналы с публичными username<br />
                  • Существующие каналы будут пропущены
                </AlertDescription>
              </Alert>

              {/* Load folders button */}
              {!userFolders && (
                <Button
                  onClick={loadUserFolders}
                  disabled={isLoadingFolders}
                  className="w-full"
                >
                  {isLoadingFolders ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Загружаем папки...
                    </>
                  ) : (
                    <>
                      📁 Загрузить мои папки
                    </>
                  )}
                </Button>
              )}

              {/* User folders list */}
              {userFolders && (
                <div className="space-y-4">
                  <Label>Выберите папку:</Label>

                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {userFolders.folders.map((folder) => (
                      <div
                        key={folder.id}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                          selectedUserFolder === folder.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setSelectedUserFolder(folder.id)}
                      >
                        <div className="flex justify-between items-center">
                          <div>
                            <div className="font-medium">{folder.name}</div>
                            <div className="text-sm text-gray-600">
                              {folder.channels.length} каналов
                            </div>
                          </div>
                          <div className="text-right">
                            {selectedUserFolder === folder.id && (
                              <Check className="w-5 h-5 text-blue-600" />
                            )}
                          </div>
                        </div>

                        {selectedUserFolder === folder.id && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <div className="text-sm text-gray-600 mb-2">Каналы в папке:</div>
                            <div className="flex flex-wrap gap-1 max-h-32 overflow-y-auto">
                              {folder.channels.slice(0, 10).map((channel) => (
                                <Badge key={channel.id} variant="secondary" className="text-xs">
                                  {channel.username ? `@${channel.username}` : channel.title}
                                </Badge>
                              ))}
                              {folder.channels.length > 10 && (
                                <Badge variant="outline" className="text-xs">
                                  +{folder.channels.length - 10} ещё
                                </Badge>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  <div className="text-sm text-gray-600">
                    Всего папок: {userFolders.stats.total_folders} |
                    Всего каналов: {userFolders.stats.total_channels}
                  </div>
                </div>
              )}

              {/* User folder results */}
              {userFolderResults && (
                <div className="space-y-4">
                  <Label>Результаты добавления из папки:</Label>

                  <Alert>
                    <Check className="h-4 w-4" />
                    <AlertDescription>
                      <strong className="text-green-700">{userFolderResults.message}</strong>
                      <div className="mt-2 text-sm">
                        <div>📁 Папка: <strong>{userFolderResults.folder_name}</strong></div>
                        <div className="mt-1 flex gap-4">
                          <span className="text-green-600">✅ Добавлено: {userFolderResults.stats.added}</span>
                          <span className="text-yellow-600">⚠️ Дубликаты: {userFolderResults.stats.duplicates}</span>
                          <span className="text-red-600">❌ Ошибки: {userFolderResults.stats.errors}</span>
                        </div>
                      </div>
                    </AlertDescription>
                  </Alert>

                  {userFolderResults.added.length > 0 && (
                    <div>
                      <strong className="text-green-700">Добавленные каналы:</strong>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {userFolderResults.added.map((item, index) => (
                          <Badge key={index} className="bg-green-100 text-green-800">
                            @{item.username} - {item.title}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {userFolderResults.duplicates.length > 0 && (
                    <div>
                      <strong className="text-yellow-700">Уже существуют:</strong>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {userFolderResults.duplicates.map((item, index) => (
                          <Badge key={index} className="bg-yellow-100 text-yellow-800">
                            @{item.username}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {userFolderResults.errors.length > 0 && (
                    <div>
                      <strong className="text-red-700">Ошибки:</strong>
                      <div className="mt-2 space-y-1">
                        {userFolderResults.errors.map((item, index) => (
                          <div key={index} className="text-sm">
                            <Badge className="bg-red-100 text-red-800 mr-2">
                              @{item.username}
                            </Badge>
                            {item.error}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </TabsContent>

            <TabsContent value="user-channels" className="space-y-6 mt-6">
              {/* Telegram status warning */}
              {(systemStatus?.telegram_authorization_needed ||
                (systemStatus?.telegram_status !== 'healthy' && systemStatus?.telegram_status !== 'available')) && (
                <Alert className="border-red-200 bg-red-50">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <AlertDescription className="text-red-800">
                    <strong>⚠️ Telegram не готов к работе</strong><br />
                    {systemStatus?.telegram_authorization_needed
                      ? 'Необходимо авторизоваться в Telegram. Перейдите в раздел "Администрирование" → "Telegram Auth".'
                      : 'Telegram API недоступен. Проверьте подключение к Telegram.'
                    }
                  </AlertDescription>
                </Alert>
              )}

              {/* Help text for user channels */}
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  <strong>Выберите каналы из ваших подписок:</strong><br />
                  • Система покажет все публичные каналы, на которые вы подписаны<br />
                  • Вы можете выбрать нужные каналы или добавить все сразу<br />
                  • Существующие каналы будут пропущены автоматически
                </AlertDescription>
              </Alert>

              {/* Load channels button */}
              {!userChannels && (
                <Button
                  onClick={loadUserChannels}
                  disabled={isLoadingChannels}
                  className="w-full"
                >
                  {isLoadingChannels ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Загружаем каналы...
                    </>
                  ) : (
                    <>
                      📺 Загрузить мои каналы
                    </>
                  )}
                </Button>
              )}

              {/* User channels list */}
              {userChannels && (
                <div className="space-y-4">
                  {/* Select all controls */}
                  <div className="flex justify-between items-center">
                    <div className="text-sm text-gray-600">
                      Выбрано: {selectedChannelIds.length} из {userChannels.stats.total_channels}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleSelectAllChannels}
                      >
                        Выбрать все
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleDeselectAllChannels}
                      >
                        Снять выбор
                      </Button>
                    </div>
                  </div>

                  {/* Channels list */}
                  <div className="max-h-96 overflow-y-auto space-y-2">
                    {userChannels.channels.map((channel) => (
                      <div
                        key={channel.id}
                        className={`p-3 border rounded-lg transition-colors ${
                          selectedChannelIds.includes(channel.id)
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <Checkbox
                              checked={selectedChannelIds.includes(channel.id)}
                              onCheckedChange={(checked) =>
                                handleChannelSelect(channel.id, checked as boolean)
                              }
                            />
                            <div>
                              <div className="font-medium">
                                {channel.username ? `@${channel.username}` : channel.title}
                              </div>
                              <div className="text-sm text-gray-600">
                                {channel.title}
                                {channel.participants_count && (
                                  <span className="ml-2 text-xs">
                                    👥 {channel.participants_count.toLocaleString()} подписчиков
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* User channels results */}
              {userChannelsResults && (
                <div className="space-y-4">
                  <Label>Результаты добавления каналов:</Label>

                  <Alert>
                    <Check className="h-4 w-4" />
                    <AlertDescription>
                      <strong className="text-green-700">{userChannelsResults.message}</strong>
                      <div className="mt-2 text-sm">
                        <div className="flex gap-4">
                          <span className="text-green-600">✅ Добавлено: {userChannelsResults.stats.added}</span>
                          <span className="text-yellow-600">⚠️ Дубликаты: {userChannelsResults.stats.duplicates}</span>
                          <span className="text-red-600">❌ Ошибки: {userChannelsResults.stats.errors}</span>
                        </div>
                      </div>
                    </AlertDescription>
                  </Alert>

                  {userChannelsResults.added.length > 0 && (
                    <div>
                      <strong className="text-green-700">Добавленные каналы:</strong>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {userChannelsResults.added.map((item, index) => (
                          <Badge key={index} className="bg-green-100 text-green-800">
                            @{item.username} - {item.title}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {userChannelsResults.duplicates.length > 0 && (
                    <div>
                      <strong className="text-yellow-700">Уже существуют:</strong>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {userChannelsResults.duplicates.map((item, index) => (
                          <Badge key={index} className="bg-yellow-100 text-yellow-800">
                            @{item.username}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {userChannelsResults.errors.length > 0 && (
                    <div>
                      <strong className="text-red-700">Ошибки:</strong>
                      <div className="mt-2 space-y-1">
                        {userChannelsResults.errors.map((item, index) => (
                          <div key={index} className="text-sm">
                            <Badge className="bg-red-100 text-red-800 mr-2">
                              @{item.username}
                            </Badge>
                            {item.error}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </TabsContent>
          </Tabs>

            {/* Results */}
            {(addResults.success.length > 0 || addResults.duplicates.length > 0 || addResults.errors.length > 0) && (
              <div className="space-y-4">
                <Label>Результаты добавления:</Label>

                {addResults.success.length > 0 && (
                  <Alert>
                    <Check className="h-4 w-4" />
                    <AlertDescription>
                      <strong className="text-green-700">Успешно добавлены ({addResults.success.length}):</strong>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {addResults.success.map((item, index) => (
                          <Badge key={index} className="bg-green-100 text-green-800">
                            @{item.username}
                          </Badge>
                        ))}
                      </div>
                    </AlertDescription>
                  </Alert>
                )}

                {addResults.duplicates.length > 0 && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      <strong className="text-yellow-700">Уже существуют ({addResults.duplicates.length}):</strong>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {addResults.duplicates.map((item, index) => (
                          <Badge key={index} className="bg-yellow-100 text-yellow-800">
                            @{item.username}
                          </Badge>
                        ))}
                      </div>
                    </AlertDescription>
                  </Alert>
                )}

                {addResults.errors.length > 0 && (
                  <Alert>
                    <X className="h-4 w-4" />
                    <AlertDescription>
                      <strong className="text-red-700">Ошибки ({addResults.errors.length}):</strong>
                      <div className="mt-2 space-y-1">
                        {addResults.errors.map((item, index) => (
                          <div key={index} className="text-sm">
                            <Badge className="bg-red-100 text-red-800 mr-2">
                              @{item.username}
                            </Badge>
                            {item.error}
                          </div>
                        ))}
                      </div>
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}

          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={resetAddChannelModal} disabled={isAddingChannels || isAddingFromFolder || isAddingFromUserFolder || isAddingFromUserChannels}>
              Отмена
            </Button>

            {addMode === 'channels' ? (
              <Button
                onClick={addChannels}
                disabled={isAddingChannels || !channelsInput.trim()}
              >
                {isAddingChannels ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Добавляем...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4 mr-2" />
                    Добавить каналы
                  </>
                )}
              </Button>
            ) : addMode === 'folder' ? (
              <Button
                onClick={handleAddFromFolder}
                disabled={
                  isAddingFromFolder ||
                  !folderLink.trim() ||
                  systemStatus?.telegram_authorization_needed ||
                  (systemStatus?.telegram_status !== 'healthy' && systemStatus?.telegram_status !== 'available')
                }
              >
                {isAddingFromFolder ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Получаем каналы...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4 mr-2" />
                    Добавить из папки
                  </>
                )}
              </Button>
            ) : addMode === 'user-folder' ? (
              <Button
                onClick={handleAddFromUserFolder}
                disabled={
                  isAddingFromUserFolder ||
                  !selectedUserFolder ||
                  systemStatus?.telegram_authorization_needed ||
                  (systemStatus?.telegram_status !== 'healthy' && systemStatus?.telegram_status !== 'available')
                }
              >
                {isAddingFromUserFolder ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Получаем каналы...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4 mr-2" />
                    Добавить из папки
                  </>
                )}
              </Button>
            ) : (
              <Button
                onClick={handleAddFromUserChannels}
                disabled={
                  isAddingFromUserChannels ||
                  selectedChannelIds.length === 0 ||
                  systemStatus?.telegram_authorization_needed ||
                  (systemStatus?.telegram_status !== 'healthy' && systemStatus?.telegram_status !== 'available')
                }
              >
                {isAddingFromUserChannels ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Добавляем...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4 mr-2" />
                    Добавить выбранные
                  </>
                )}
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
