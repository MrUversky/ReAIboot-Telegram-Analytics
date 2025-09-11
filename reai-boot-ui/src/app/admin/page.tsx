'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSupabase } from '@/components/SupabaseProvider'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Users,
  Shield,
  Activity,
  Database,
  Settings,
  RefreshCw,
  UserCheck,
  UserX,
  Crown,
  Eye,
  Plus,
  Edit,
  Trash2,
  Check,
  X,
  Zap,
  Target,
  BarChart3,
  DollarSign,
  AlertCircle,
  FlaskRound,
  Search,
  Filter,
  Download,
  Play,
  RotateCcw
} from 'lucide-react'
import { supabase } from '@/lib/supabase'
import { apiClient } from '@/lib/api'

interface UserProfile {
  id: string
  email: string
  full_name?: string
  role: 'admin' | 'user' | 'viewer'
  is_active: boolean
  created_at: string
  last_login?: string
}

interface SystemStats {
  total_users: number
  active_users: number
  admin_users: number
  total_posts: number
  recent_posts: number
  total_tokens: number
}

// JSON Highlighter компонент
const JsonHighlighter = ({ data }: { data: any }) => {
  const highlightJson = (obj: any, indent = 0): JSX.Element => {
    const indentStr = '  '.repeat(indent)

    if (obj === null) {
      return <span className="text-blue-600">null</span>
    }

    if (typeof obj === 'boolean') {
      return <span className="text-purple-600">{obj.toString()}</span>
    }

    if (typeof obj === 'number') {
      return <span className="text-green-600">{obj}</span>
    }

    if (typeof obj === 'string') {
      return <span className="text-red-600">"{obj}"</span>
    }

    if (Array.isArray(obj)) {
      if (obj.length === 0) {
        return <span className="text-gray-600">[]</span>
      }

      return (
        <span>
          [<br />
          {obj.map((item, index) => (
            <span key={index}>
              {indentStr}  {highlightJson(item, indent + 1)}
              {index < obj.length - 1 ? ',' : ''}
              <br />
            </span>
          ))}
          {indentStr}]
        </span>
      )
    }

    if (typeof obj === 'object') {
      const keys = Object.keys(obj)
      if (keys.length === 0) {
        return <span className="text-gray-600">{'{}'}</span>
      }

      return (
        <span>
          {'{'}<br />
          {keys.map((key, index) => (
            <span key={key}>
              {indentStr}  <span className="text-blue-800">"{key}"</span>: {highlightJson(obj[key], indent + 1)}
              {index < keys.length - 1 ? ',' : ''}
              <br />
            </span>
          ))}
          {indentStr}{'}'}
        </span>
      )
    }

    return <span className="text-gray-600">{String(obj)}</span>
  }

  try {
    return (
      <div className="font-mono text-xs overflow-x-auto">
        {highlightJson(data)}
      </div>
    )
  } catch (error) {
    return (
      <div className="text-red-600 text-xs">
        Ошибка отображения JSON: {String(error)}
      </div>
    )
  }
}

export default function AdminPage() {
  const router = useRouter()
  const { user, permissions, loading } = useSupabase()
  const [users, setUsers] = useState<UserProfile[]>([])
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [loadingData, setLoadingData] = useState(true)

  // Убрана функциональность управления каналами - теперь в разделе "Парсинг"

  // LLM settings state
  const [rubrics, setRubrics] = useState<any[]>([])
  const [formats, setFormats] = useState<any[]>([])
  const [dbPrompts, setDbPrompts] = useState<any[]>([])
  const [filePrompts, setFilePrompts] = useState<any>({})
  const [showLLMModal, setShowLLMModal] = useState(false)
  const [llmTab, setLlmTab] = useState<'rubrics' | 'formats' | 'prompts'>('prompts')

  // Viral Detection settings state
  const [systemSettings, setSystemSettings] = useState<any[]>([])
  const [channelBaselines, setChannelBaselines] = useState<any[]>([])
  const [viralPosts, setViralPosts] = useState<any[]>([])
  const [showViralModal, setShowViralModal] = useState(false)
  const [viralTab, setViralTab] = useState<'settings' | 'baselines' | 'posts'>('settings')

  // Telegram Auth state
  const [telegramStatus, setTelegramStatus] = useState<any>(null)
  const [showTelegramModal, setShowTelegramModal] = useState(false)

  // Sandbox state
  const [showSandboxModal, setShowSandboxModal] = useState(false)
  const [sandboxPostData, setSandboxPostData] = useState('')
  const [sandboxResult, setSandboxResult] = useState<any>(null)
  const [sandboxLoading, setSandboxLoading] = useState(false)
  const [logSearchTerm, setLogSearchTerm] = useState('')
  const [logFilterType, setLogFilterType] = useState<string>('all')
  const [logFilterSuccess, setLogFilterSuccess] = useState<string>('all')
  const [jsonError, setJsonError] = useState<string>('')

  // Step-by-step execution state
  const [stepByStepMode, setStepByStepMode] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [stepResults, setStepResults] = useState<any[]>([])
  const [canExecuteNext, setCanExecuteNext] = useState(false)

  // LLM Prices state
  const [showPricesModal, setShowPricesModal] = useState(false)
  const [priceReport, setPriceReport] = useState<any>(null)
  const [loadingPrices, setLoadingPrices] = useState(false)

  // Data Cleanup state
  const [showCleanupModal, setShowCleanupModal] = useState(false)
  const [cleanupPreview, setCleanupPreview] = useState<any>(null)
  const [cleanupDays, setCleanupDays] = useState(7)
  const [cleanupConfirm, setCleanupConfirm] = useState('')
  const [cleanupLoading, setCleanupLoading] = useState(false)
  const [authStep, setAuthStep] = useState<'phone' | 'code'>('phone')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [verificationCode, setVerificationCode] = useState('')
  const [phoneCodeHash, setPhoneCodeHash] = useState('')
  const [authLoading, setAuthLoading] = useState(false)
  const [rubricForm, setRubricForm] = useState({
    id: '',
    name: '',
    description: '',
    category: '',
    is_active: true
  })
  const [formatForm, setFormatForm] = useState({
    id: '',
    name: '',
    description: '',
    duration_seconds: 60,
    structure: {},
    is_active: true
  })
  const [promptForm, setPromptForm] = useState({
    id: '',
    name: '',
    description: '',
    prompt_type: 'custom',
    category: 'general',
    content: '', // Для обратной совместимости
    system_prompt: '',
    user_prompt: '',
    variables: {},
    model: 'gpt-4o-mini',
    temperature: 0.7,
    max_tokens: 2000,
    is_active: true
  })

  const [promptTestVariables, setPromptTestVariables] = useState<Record<string, string>>({})
  const [promptTestResult, setPromptTestResult] = useState<any>(null)
  const [showPromptTest, setShowPromptTest] = useState(false)
  const [selectedTestPromptId, setSelectedTestPromptId] = useState<string>("")

  // Подсказки для переменных по типам промптов
  const variableHints = {
    "post_text": "Текст поста для анализа",
    "views": "Количество просмотров поста",
    "reactions": "Количество реакций на пост",
    "replies": "Количество комментариев",
    "forwards": "Количество репостов",
    "channel_title": "Название канала",
    "score": "Оценка поста по шкале 1-10",
    "project_context": "Контекст проекта ПерепрошИИвка",
    "analysis": "Результат анализа поста",
    "rubric_name": "Название выбранной рубрики",
    "format_name": "Название выбранного формата",
    "duration": "Продолжительность видео в секундах",
    "available_rubrics": "Список доступных рубрик (JSON)",
    "available_formats": "Список доступных форматов (JSON)",
    "current_rubrics": "Текущие рубрики проекта",
    "current_formats": "Текущие форматы проекта",
    "engagement_rate": "Показатель вовлеченности",
    "selected_rubric": "Выбранная рубрика (объект)",
    "selected_format": "Выбранный формат (объект)"
  }

  // Telegram Auth functions
  const checkTelegramStatus = async () => {
    try {
      const data = await apiClient.healthCheck()
      setTelegramStatus(data)
      return data
    } catch (error) {
      console.error('Error checking Telegram status:', error)
      setTelegramStatus({
        status: 'error',
        telegram_status: 'error',
        telegram_authorization_needed: true
      })
      return null
    }
  }

  const resetTelegramAuth = async () => {
    if (!confirm('Вы уверены, что хотите сбросить авторизацию Telegram? Это удалит текущую сессию и потребуется повторная авторизация.')) {
      return
    }

    setAuthLoading(true)
    try {
      const result = await apiClient.resetTelegramAuth()

      if (result.status === 'reset') {
        alert('Авторизация Telegram сброшена успешно!')
        setShowTelegramModal(false)
        await checkTelegramStatus()
        // Reset form
        setPhoneNumber('')
        setVerificationCode('')
        setAuthStep('phone')
      } else {
        alert(`Ошибка: ${result.message}`)
      }
    } catch (error) {
      console.error('Error resetting Telegram auth:', error)
      alert('Ошибка при сбросе авторизации')
    } finally {
      setAuthLoading(false)
    }
  }

  const startTelegramAuth = async () => {
    setAuthLoading(true)
    try {
      const result = await apiClient.startTelegramAuth()

      if (result.status === 'auth_needed') {
        setAuthStep('phone')
      } else if (result.status === 'connected') {
        alert('Telegram уже подключен!')
        setShowTelegramModal(false)
        await checkTelegramStatus()
      }
    } catch (error) {
      console.error('Error starting Telegram auth:', error)
      alert('Ошибка при запуске авторизации')
    } finally {
      setAuthLoading(false)
    }
  }

  const sendVerificationCode = async () => {
    if (!phoneNumber) {
      alert('Введите номер телефона')
      return
    }

    setAuthLoading(true)
    try {
      const result = await apiClient.sendTelegramCode(phoneNumber)

      if (result.status === 'code_sent') {
        if (result.phone_code_hash) {
          setPhoneCodeHash(result.phone_code_hash)
          setAuthStep('code')
          alert('Код отправлен! Проверьте SMS')
        } else {
          alert('Ошибка: Код подтверждения не получен')
        }
      } else {
        alert(`Ошибка: ${result.message}`)
        if (result.can_retry) {
          // Даем возможность повторить
          setTimeout(() => {
            if (confirm('Хотите попробовать еще раз?')) {
              sendVerificationCode()
            }
          }, 1000)
        }
      }
    } catch (error) {
      console.error('Error sending code:', error)
      alert('Ошибка при отправке кода')
      if (confirm('Хотите попробовать еще раз?')) {
        sendVerificationCode()
      }
    } finally {
      setAuthLoading(false)
    }
  }

  const verifyCode = async () => {
    if (!verificationCode) {
      alert('Введите код подтверждения')
      return
    }

    setAuthLoading(true)
    try {
      if (!phoneCodeHash) {
        alert('Код подтверждения телефона не найден. Попробуйте отправить код заново.')
        return
      }

      const result = await apiClient.verifyTelegramCode(verificationCode, phoneCodeHash)

      if (result.status === 'verified') {
        alert('Успешная авторизация в Telegram!')
        setShowTelegramModal(false)
        await checkTelegramStatus()
        // Reset form
        setPhoneNumber('')
        setVerificationCode('')
        setAuthStep('phone')
      } else {
        alert(`Ошибка: ${result.message}`)
        if (result.can_retry) {
          // Даем возможность повторить
          if (confirm('Хотите попробовать еще раз?')) {
            setVerificationCode('')
          }
        }
      }
    } catch (error) {
      console.error('Error verifying code:', error)
      alert('Ошибка при проверке кода')
      if (confirm('Хотите попробовать еще раз?')) {
        setVerificationCode('')
      }
    } finally {
      setAuthLoading(false)
    }
  }

  useEffect(() => {
    if (!loading && (!user || !permissions?.canAdmin)) {
      router.push('/')
    }
  }, [user, permissions, loading, router])

  useEffect(() => {
    if (user && permissions?.canAdmin) {
      loadAdminData()
      checkTelegramStatus() // Проверяем статус Telegram при загрузке
    }
  }, [user, permissions])

  const loadAdminData = async () => {
    try {
      setLoadingData(true)

      // Загружаем пользователей
      const { data: usersData, error: usersError } = await supabase
        .from('profiles')
        .select('*')
        .order('created_at', { ascending: false })

      if (usersError) throw usersError
      setUsers(usersData || [])

      // Загружаем статистику
      const [postsResult, tokensResult] = await Promise.all([
        supabase.from('posts').select('id', { count: 'exact' }),
        supabase.from('token_usage').select('tokens_used', { count: 'exact' })
      ])

      const totalUsers = usersData?.length || 0
      const activeUsers = usersData?.filter(u => u.is_active).length || 0
      const adminUsers = usersData?.filter(u => u.role === 'admin').length || 0

      setStats({
        total_users: totalUsers,
        active_users: activeUsers,
        admin_users: adminUsers,
        total_posts: postsResult.count || 0,
        recent_posts: 0, // TODO: calculate recent posts
        total_tokens: tokensResult.count || 0
      })
      // Загружаем настройки LLM (рубрики, форматы, промпты)
      await loadLLMSettings()

    } catch (error) {
      console.error('Error loading admin data:', error)
    } finally {
      setLoadingData(false)
    }
  }

  const updateUserRole = async (userId: string, newRole: 'admin' | 'user' | 'viewer') => {
    try {
      const { error } = await supabase
        .from('profiles')
        .update({ role: newRole })
        .eq('id', userId)

      if (error) throw error

      // Обновляем локальное состояние
      setUsers(users.map(u =>
        u.id === userId ? { ...u, role: newRole } : u
      ))

    } catch (error) {
      console.error('Error updating user role:', error)
      alert('Ошибка при обновлении роли пользователя')
    }
  }

  const toggleUserStatus = async (userId: string, isActive: boolean) => {
    try {
      const { error } = await supabase
        .from('profiles')
        .update({ is_active: !isActive })
        .eq('id', userId)

      if (error) throw error

      // Обновляем локальное состояние
      setUsers(users.map(u =>
        u.id === userId ? { ...u, is_active: !isActive } : u
      ))

    } catch (error) {
      console.error('Error updating user status:', error)
      alert('Ошибка при изменении статуса пользователя')
    }
  }



  // LLM settings functions
  const loadLLMSettings = async () => {
    try {
      const [rubricsResult, formatsResult, dbPromptsResult, filePromptsResult] = await Promise.all([
        supabase.from('rubrics').select('*').order('name'),
        supabase.from('reel_formats').select('*').order('name'),
        apiClient.getAllPromptsDB(),
        apiClient.getPrompts()
      ])

      if (rubricsResult.error) throw rubricsResult.error
      if (formatsResult.error) throw formatsResult.error
      console.log("Rubrics loaded:", rubricsResult.data || [])
      setRubrics(rubricsResult.data || [])
      console.log("Formats loaded:", formatsResult.data || [])
      setFormats(formatsResult.data || [])
      console.log("DbPrompts loaded:", dbPromptsResult || [])
      setDbPrompts(dbPromptsResult || [])
      setFilePrompts(filePromptsResult || {})
    } catch (error) {
      console.error('Error loading LLM settings:', error)
      alert('Ошибка при загрузке настроек LLM')
    }
  }

  // Viral Detection functions
  const loadViralSettings = async () => {
    try {
      const [settingsResult, baselinesResult, postsResult] = await Promise.all([
        apiClient.getViralSettings(),
        apiClient.getChannelBaselines(),
        apiClient.getViralPosts()
      ])

      setSystemSettings(settingsResult.settings || [])
      setChannelBaselines(baselinesResult.baselines || [])
      setViralPosts(postsResult.posts || [])
    } catch (error) {
      console.error('Error loading viral settings:', error)
      alert('Ошибка при загрузке настроек viral detection')
    }
  }

  const handleConfigureLLM = async () => {
    await loadLLMSettings()
    setShowLLMModal(true)
  }

  const handleShowPrices = async () => {
    setLoadingPrices(true)
    try {
      // В будущем здесь будет API вызов для получения цен
      // Пока используем моковые данные
      const mockPriceReport = {
        timestamp: new Date().toISOString(),
        prices: {
          'gpt-4o': {
            input: { price_per_million: 2.50, price_per_1k: 0.0025, source: 'api', confidence: 1.0 },
            output: { price_per_million: 10.00, price_per_1k: 0.01, source: 'api', confidence: 1.0 }
          },
          'gpt-4o-mini': {
            input: { price_per_million: 0.150, price_per_1k: 0.00015, source: 'api', confidence: 1.0 },
            output: { price_per_million: 0.600, price_per_1k: 0.0006, source: 'api', confidence: 1.0 }
          },
          'claude-3-5-sonnet': {
            input: { price_per_million: 3.0, price_per_1k: 0.003, source: 'api', confidence: 1.0 },
            output: { price_per_million: 15.0, price_per_1k: 0.015, source: 'api', confidence: 1.0 }
          }
        },
        summary: {
          total_alerts: 0,
          significant_changes: 0,
          last_update: new Date().toISOString()
        }
      }
      setPriceReport(mockPriceReport)
    } catch (error) {
      console.error('Ошибка загрузки цен:', error)
    } finally {
      setLoadingPrices(false)
    }
    setShowPricesModal(true)
  }

  // Функция валидации JSON данных поста
  const validatePostData = (jsonString: string) => {
    if (!jsonString.trim()) {
      return { isValid: false, error: 'Введите данные поста в формате JSON' }
    }

    try {
      const data = JSON.parse(jsonString)

      // Проверяем обязательные поля
      const requiredFields = ['id', 'message_id', 'channel_username', 'text']
      const missingFields = requiredFields.filter(field => !data[field])

      if (missingFields.length > 0) {
        return {
          isValid: false,
          error: `Отсутствуют обязательные поля: ${missingFields.join(', ')}`
        }
      }

      // Проверяем типы данных
      if (typeof data.message_id !== 'number') {
        return { isValid: false, error: 'message_id должен быть числом' }
      }

      if (typeof data.text !== 'string' || data.text.length === 0) {
        return { isValid: false, error: 'text должен быть непустой строкой' }
      }

      if (typeof data.channel_username !== 'string' || !data.channel_username.startsWith('@')) {
        return { isValid: false, error: 'channel_username должен начинаться с @' }
      }

      // Проверяем опциональные поля
      if (data.views !== undefined && (typeof data.views !== 'number' || data.views < 0)) {
        return { isValid: false, error: 'views должен быть неотрицательным числом' }
      }

      if (data.forwards !== undefined && (typeof data.forwards !== 'number' || data.forwards < 0)) {
        return { isValid: false, error: 'forwards должен быть неотрицательным числом' }
      }

      if (data.reactions !== undefined && (typeof data.reactions !== 'number' || data.reactions < 0)) {
        return { isValid: false, error: 'reactions должен быть неотрицательным числом' }
      }

      return { isValid: true, data }

    } catch (error) {
      return { isValid: false, error: 'Некорректный JSON формат' }
    }
  }

  const handleTestSandbox = async () => {
    // Валидируем данные
    const validation = validatePostData(sandboxPostData)

    if (!validation.isValid) {
      setJsonError(validation.error)
      return
    }

    setJsonError('') // Сбрасываем ошибку
    setSandboxLoading(true)

    try {
      const response = await fetch('/api/sandbox/test-pipeline', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          post_data: validation.data,
          options: {
            debug_mode: true,
            step_by_step: false
          }
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()

      setSandboxResult(result)
      // Сбросить фильтры при новом результате
      setLogSearchTerm('')
      setLogFilterType('all')
      setLogFilterSuccess('all')
    } catch (error) {
      console.error('Error testing sandbox:', error)
      setJsonError('Ошибка при тестировании песочницы: ' + error.message)
    } finally {
      setSandboxLoading(false)
    }
  }

  // Функция фильтрации логов
  const getFilteredLogs = () => {
    if (!sandboxResult?.debug_log) return []

    let filtered = sandboxResult.debug_log

    // Фильтр по типу
    if (logFilterType !== 'all') {
      filtered = filtered.filter((log: any) => log.step_type === logFilterType)
    }

    // Фильтр по успешности (для шагов)
    if (logFilterSuccess !== 'all') {
      const successValue = logFilterSuccess === 'success'
      filtered = filtered.filter((log: any) => {
        const data = log.data || {}
        if (log.step_type === 'llm_response') {
          return data.success === successValue
        }
        return true // Для других типов не фильтруем по успеху
      })
    }

    // Поиск по тексту
    if (logSearchTerm.trim()) {
      const searchLower = logSearchTerm.toLowerCase()
      filtered = filtered.filter((log: any) => {
        const stepName = log.step_name?.toLowerCase() || ''
        const stepType = log.step_type?.toLowerCase() || ''
        const dataStr = JSON.stringify(log.data || {}).toLowerCase()
        return stepName.includes(searchLower) ||
               stepType.includes(searchLower) ||
               dataStr.includes(searchLower)
      })
    }

    return filtered
  }

  // Функция экспорта результатов в JSON
  const handleExportResults = () => {
    if (!sandboxResult) return

    let postData
    try {
      postData = JSON.parse(sandboxPostData || '{}')
    } catch (error) {
      postData = { error: 'Invalid JSON in input', raw_text: sandboxPostData }
    }

    const exportData = {
      timestamp: new Date().toISOString(),
      sandbox_version: "1.0",
      input_data: {
        post_data: postData,
        options: {
          debug_mode: true,
          step_by_step: stepByStepMode
        }
      },
      results: sandboxResult,
      filters_applied: {
        search_term: logSearchTerm,
        filter_type: logFilterType,
        filter_success: logFilterSuccess
      },
      filtered_logs_count: getFilteredLogs().length,
      total_logs_count: sandboxResult.debug_log?.length || 0
    }

    const dataStr = JSON.stringify(exportData, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)

    const exportFileDefaultName = `sandbox-results-${sandboxResult.post_id}-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`

    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  // Функции пошагового выполнения
  const startStepByStepExecution = () => {
    const validation = validatePostData(sandboxPostData)
    if (!validation.isValid) {
      setJsonError(validation.error)
      return
    }

    setJsonError('')
    setStepByStepMode(true)
    setCurrentStep(0)
    setStepResults([])
    setCanExecuteNext(true)
  }

  const executeCurrentStep = async () => {
    if (!canExecuteNext) return

    setSandboxLoading(true)
    try {
      const validation = validatePostData(sandboxPostData)
      const stepData = {
        post_data: validation.data,
        options: {
          debug_mode: true,
          step_by_step: true,
          current_step: currentStep,
          previous_results: stepResults
        }
      }

      const response = await fetch('/api/sandbox/test-pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(stepData)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()

      // Добавляем результат текущего шага
      const newStepResults = [...stepResults]
      newStepResults[currentStep] = result
      setStepResults(newStepResults)

      // Переходим к следующему шагу
      setCurrentStep(currentStep + 1)

      // Проверяем, можем ли выполнить следующий шаг
      setCanExecuteNext(result.success || currentStep < 2) // Можно продолжать даже при неудаче фильтрации

    } catch (error) {
      console.error('Error executing step:', error)
      setJsonError('Ошибка выполнения шага: ' + error.message)
    } finally {
      setSandboxLoading(false)
    }
  }

  const resetStepByStepExecution = () => {
    setStepByStepMode(false)
    setCurrentStep(0)
    setStepResults([])
    setCanExecuteNext(false)
    setSandboxResult(null)
  }

  const handleConfigureViral = async () => {
    await loadViralSettings()
    setShowViralModal(true)
  }

  const updateSystemSetting = async (key: string, value: any) => {
    try {
      await apiClient.updateSystemSetting(key, value)
      alert('Настройка обновлена успешно')
      await loadViralSettings()
    } catch (error) {
      console.error('Error updating system setting:', error)
      alert('Ошибка при обновлении настройки')
    }
  }

  const calculateChannelBaseline = async (channelUsername: string) => {
    try {
      await apiClient.calculateChannelBaseline(channelUsername)
      alert(`Базовые метрики для ${channelUsername} пересчитаны`)
      await loadViralSettings()
    } catch (error) {
      console.error('Error calculating baseline:', error)
      alert('Ошибка при расчете базовых метрик')
    }
  }

  // Data Cleanup functions
  const handlePreviewCleanup = async () => {
    try {
      const preview = await apiClient.previewCleanup(cleanupDays)
      setCleanupPreview(preview)
    } catch (error) {
      console.error('Error previewing cleanup:', error)
      alert('Ошибка при предварительном просмотре очистки')
    }
  }

  const handleExecuteCleanup = async () => {
    if (cleanupConfirm !== 'DELETE') {
      alert('Введите "DELETE" для подтверждения')
      return
    }

    setCleanupLoading(true)
    try {
      const result = await apiClient.executeCleanup(cleanupDays, true)
      alert(`✅ Очистка завершена!\n\nУдалено:\n• Постов: ${result.deleted_counts.posts}\n• Анализов: ${result.deleted_counts.post_analysis}\n• Сценариев: ${result.deleted_counts.scenarios}\n• Метрик: ${result.deleted_counts.post_metrics}`)
      setShowCleanupModal(false)
      setCleanupPreview(null)
      setCleanupConfirm('')
      // Обновить данные
      loadAdminData()
    } catch (error) {
      console.error('Error executing cleanup:', error)
      alert('Ошибка при выполнении очистки')
    } finally {
      setCleanupLoading(false)
    }
  }

  const updateAllBaselines = async () => {
    try {
      const result = await apiClient.updateAllBaselines()
      alert(result.message)
      await loadViralSettings()
    } catch (error) {
      console.error('Error updating baselines:', error)
      alert('Ошибка при обновлении базовых метрик')
    }
  }

  const saveRubric = async () => {
    try {
      const rubricData = {
        ...rubricForm,
        updated_at: new Date().toISOString()
      }

      if (rubricForm.id) {
        const { error } = await supabase
          .from('rubrics')
          .update(rubricData)
          .eq('id', rubricForm.id)
        if (error) throw error
      } else {
        const newId = `rubric_${Date.now()}`
        const { error } = await supabase
          .from('rubrics')
          .insert([{
            ...rubricData,
            id: newId,
            created_at: new Date().toISOString()
          }])
        if (error) throw error
      }

      await loadLLMSettings()
      resetRubricForm()
    } catch (error) {
      console.error('Error saving rubric:', error)
      alert('Ошибка при сохранении рубрики')
    }
  }

  const saveFormat = async () => {
    try {
      const formatData = {
        ...formatForm,
        updated_at: new Date().toISOString()
      }

      if (formatForm.id) {
        const { error } = await supabase
          .from('reel_formats')
          .update(formatData)
          .eq('id', formatForm.id)
        if (error) throw error
      } else {
        const newId = `format_${Date.now()}`
        const { error } = await supabase
          .from('reel_formats')
          .insert([{
            ...formatData,
            id: newId,
            created_at: new Date().toISOString()
          }])
        if (error) throw error
      }

      await loadLLMSettings()
      resetFormatForm()
    } catch (error) {
      console.error('Error saving format:', error)
      alert('Ошибка при сохранении формата')
    }
  }

  const deleteRubric = async (rubricId: string) => {
    if (!confirm('Вы уверены, что хотите удалить эту рубрику?')) return

    try {
      const { error } = await supabase
        .from('rubrics')
        .delete()
        .eq('id', rubricId)

      if (error) throw error
      await loadLLMSettings()
    } catch (error) {
      console.error('Error deleting rubric:', error)
      alert('Ошибка при удалении рубрики')
    }
  }

  const deleteFormat = async (formatId: string) => {
    if (!confirm('Вы уверены, что хотите удалить этот формат?')) return

    try {
      const { error } = await supabase
        .from('reel_formats')
        .delete()
        .eq('id', formatId)

      if (error) throw error
      await loadLLMSettings()
    } catch (error) {
      console.error('Error deleting format:', error)
      alert('Ошибка при удалении формата')
    }
  }

  const resetRubricForm = () => {
    setRubricForm({
      id: '',
      name: '',
      description: '',
      category: '',
      is_active: true
    })
  }

  const resetFormatForm = () => {
    setFormatForm({
      id: '',
      name: '',
      description: '',
      duration_seconds: 60,
      structure: {},
      is_active: true
    })
  }

  const editRubric = (rubric: any) => {
    setRubricForm({
      id: rubric.id || '',
      name: rubric.name || '',
      description: rubric.description || '',
      category: rubric.category || '',
      is_active: rubric.is_active !== undefined ? rubric.is_active : true
    })
    // Прокрутка к форме редактирования через небольшую задержку
    setTimeout(() => {
      const formElement = document.getElementById('rubric-form')
      if (formElement) {
        formElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }, 100)
  }

  const editFormat = (format: any) => {
    setFormatForm({
      id: format.id || '',
      name: format.name || '',
      description: format.description || '',
      duration_seconds: format.duration_seconds || 60,
      structure: format.structure || {},
      is_active: format.is_active !== undefined ? format.is_active : true
    })
    // Прокрутка к форме редактирования через небольшую задержку
    setTimeout(() => {
      const formElement = document.getElementById('format-form')
      if (formElement) {
        formElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }, 100)
  }

  const savePrompt = async () => {
    try {
      if (!promptForm.name) {
        alert('Название промпта обязательно')
        return
      }

      if (!promptForm.system_prompt && !promptForm.user_prompt) {
        alert('Должен быть заполнен хотя бы один промпт (System или User)')
        return
      }

      // Готовим данные для отправки
      const promptData = {
        name: promptForm.name,
        description: promptForm.description,
        prompt_type: promptForm.prompt_type,
        category: promptForm.category || 'general',
        system_prompt: promptForm.system_prompt || '',
        user_prompt: promptForm.user_prompt || '',
        variables: promptForm.variables || {},
        model: promptForm.model,
        temperature: promptForm.temperature,
        max_tokens: promptForm.max_tokens,
        is_active: promptForm.is_active
      }

      if (promptForm.id) {
        // Обновление существующего промпта
        await apiClient.updatePromptDB(parseInt(promptForm.id), promptData)
        alert('Промпт обновлен успешно')
      } else {
        // Создание нового промпта
        await apiClient.createPromptDB(promptData)
        alert('Промпт создан успешно')
      }

      await loadLLMSettings()
      resetPromptForm()
    } catch (error) {
      console.error('Error saving prompt:', error)
      alert('Ошибка при сохранении промпта')
    }
  }

  const deletePrompt = async (promptId: string) => {
    if (!confirm('Вы уверены, что хотите удалить этот промпт?')) return

    try {
      await apiClient.deletePromptDB(parseInt(promptId))
      alert('Промпт удален успешно')
      await loadLLMSettings()
    } catch (error) {
      console.error('Error deleting prompt:', error)
      alert('Ошибка при удалении промпта')
    }
  }

  const resetPromptForm = () => {
    setPromptForm({
      id: '',
      name: '',
      description: '',
      prompt_type: 'custom',
      category: 'general',
      content: '', // Для обратной совместимости
      system_prompt: '',
      user_prompt: '',
      variables: {},
      model: 'gpt-4o-mini',
      temperature: 0.7,
      max_tokens: 2000,
      is_active: true
    })
    setShowLLMModal(false)
  }

  const editPrompt = (prompt: any) => {
    // Поддержка как старой, так и новой структуры данных
    const modelSettings = prompt.model_settings || {}
    const model = prompt.model || modelSettings.model || 'gpt-4o-mini'
    const temperature = prompt.temperature || modelSettings.temperature || 0.7
    const maxTokens = prompt.max_tokens || modelSettings.max_tokens || 2000

    setPromptForm({
      id: prompt.id.toString(),
      name: prompt.name,
      description: prompt.description || '',
      prompt_type: prompt.prompt_type,
      category: prompt.category || 'general',
      content: (prompt.system_prompt && prompt.system_prompt !== null) ? prompt.system_prompt : (prompt.content || ''),
      system_prompt: (prompt.system_prompt && prompt.system_prompt !== null) ? prompt.system_prompt : '',
      user_prompt: (prompt.user_prompt && prompt.user_prompt !== null) ? prompt.user_prompt : '',
      variables: prompt.variables || {},
      model: model,
      temperature: temperature,
      max_tokens: maxTokens,
      is_active: prompt.is_active
    })
    setShowLLMModal(true)
    // Прокрутка к форме редактирования через небольшую задержку
    setTimeout(() => {
      const formElement = document.getElementById('prompt-form')
      if (formElement) {
        formElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }, 100)
  }

  const testPrompt = async (promptId: number) => {
    try {
      const result = await apiClient.testPromptDB(promptId, promptTestVariables)
      setPromptTestResult(result)
    } catch (error) {
      console.error('Error testing prompt:', error)
      alert('Ошибка при тестировании промпта')
    }
  }

  const extractVariablesFromPrompt = (content: string): string[] => {
    const variableRegex = /\{\{([^}]+)\}\}/g
    const variables: string[] = []
    let match

    while ((match = variableRegex.exec(content)) !== null) {
      const variable = match[1].trim()
      if (!variables.includes(variable)) {
        variables.push(variable)
      }
    }

    return variables
  }

  const getModelDisplayName = (model: string): string => {
    const modelNames: Record<string, string> = {
      'gpt-4o-mini': 'GPT-4o Mini',
      'gpt-4o': 'GPT-4o',
      'claude-3-5-sonnet-20241022': 'Claude-3.5-Sonnet',
      'claude-3-haiku-20240307': 'Claude-3-Haiku'
    }
    return modelNames[model] || model
  }

  const getPromptTypeDisplayName = (type: string): string => {
    const typeNames: Record<string, string> = {
      'filter': 'Фильтр постов',
      'analysis': 'Анализ поста',
      'generation': 'Генерация сценария',
      'custom': 'Пользовательский'
    }
    return typeNames[type] || type
  }

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'admin':
        return <Badge className="bg-red-100 text-red-800"><Crown className="w-3 h-3 mr-1" />Админ</Badge>
      case 'user':
        return <Badge className="bg-green-100 text-green-800"><UserCheck className="w-3 h-3 mr-1" />Пользователь</Badge>
      case 'viewer':
        return <Badge className="bg-gray-100 text-gray-800"><Eye className="w-3 h-3 mr-1" />Наблюдатель</Badge>
      default:
        return <Badge variant="outline">{role}</Badge>
    }
  }

  if (loading || !user || !permissions?.canAdmin) {
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
          <h1 className="text-3xl font-bold text-gray-900">Админ панель</h1>
          <p className="text-gray-600 mt-2">
            Управление пользователями и системой
          </p>
        </div>
        <Button onClick={loadAdminData} disabled={loadingData}>
          {loadingData ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          ) : (
            <RefreshCw className="w-4 h-4 mr-2" />
          )}
          Обновить
        </Button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Всего пользователей</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_users || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.active_users || 0} активных
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Администраторов</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.admin_users || 0}</div>
            <p className="text-xs text-muted-foreground">
              С полными правами
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Всего постов</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_posts || 0}</div>
            <p className="text-xs text-muted-foreground">
              В базе данных
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Использовано токенов</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_tokens || 0}</div>
            <p className="text-xs text-muted-foreground">
              Всего запросов
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Users Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Users className="w-5 h-5 mr-2" />
            Управление пользователями
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {loadingData ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-500">Загрузка пользователей...</p>
              </div>
            ) : users.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Пользователи не найдены</p>
              </div>
            ) : (
              <div className="space-y-3">
                {users.map((user) => (
                  <div key={user.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-700">
                            {user.email.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {user.email}
                        </p>
                        <p className="text-sm text-gray-500">
                          {user.full_name || 'Без имени'}
                        </p>
                        <p className="text-xs text-gray-400">
                          Создан: {new Date(user.created_at).toLocaleDateString('ru-RU')}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      {getRoleBadge(user.role)}

                      <Badge variant={user.is_active ? "default" : "secondary"}>
                        {user.is_active ? 'Активен' : 'Заблокирован'}
                      </Badge>

                      <Select
                        value={user.role}
                        onValueChange={(value) =>
                          updateUserRole(user.id, value as 'admin' | 'user' | 'viewer')
                        }
                      >
                        <SelectTrigger className="w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="admin">Админ</SelectItem>
                          <SelectItem value="user">Пользователь</SelectItem>
                          <SelectItem value="viewer">Наблюдатель</SelectItem>
                        </SelectContent>
                      </Select>

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => toggleUserStatus(user.id, user.is_active)}
                      >
                        {user.is_active ? (
                          <UserX className="w-4 h-4" />
                        ) : (
                          <UserCheck className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* System Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Settings className="w-5 h-5 mr-2" />
            Системные настройки
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <h4 className="font-medium text-gray-900 mb-2">Настройки системы</h4>
            <p className="text-sm text-gray-600 mb-6">
              Управление пользователями и системными настройками
            </p>
            <div className="flex justify-center gap-4 flex-wrap">
              <Button variant="outline" onClick={handleConfigureLLM}>
                <Settings className="w-4 h-4 mr-2" />
                Настройки LLM
              </Button>
              <Button variant="outline" onClick={handleShowPrices}>
                <DollarSign className="w-4 h-4 mr-2" />
                Цены LLM
              </Button>
              <Button variant="outline" onClick={handleConfigureViral}>
                <Zap className="w-4 h-4 mr-2" />
                Viral Detection
              </Button>
              <Button variant="outline" onClick={() => setShowCleanupModal(true)}>
                <Trash2 className="w-4 h-4 mr-2" />
                Очистка данных
              </Button>
              <Button variant="outline" onClick={() => setShowSandboxModal(true)}>
                <FlaskRound className="w-4 h-4 mr-2" />
                Песочница
              </Button>
              <Button
                variant={telegramStatus?.telegram_authorization_needed ? "default" : "outline"}
                onClick={() => setShowTelegramModal(true)}
                className={telegramStatus?.telegram_authorization_needed ? "bg-red-600 hover:bg-red-700" : ""}
              >
                <Database className="w-4 h-4 mr-2" />
                Telegram Auth
                {telegramStatus?.telegram_authorization_needed && (
                  <span className="ml-2 px-2 py-1 bg-red-500 text-white text-xs rounded-full">
                    Требуется
                  </span>
                )}
              </Button>
            </div>
            <div className="mt-4 text-xs text-gray-500">
              💡 Управление каналами теперь доступно в разделе "Парсинг"
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Viral Detection Modal */}
      {showViralModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  <Zap className="w-6 h-6 mr-2 text-yellow-500" />
                  Настройки Viral Detection
                </h2>
                <Button variant="outline" onClick={() => setShowViralModal(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>

              {/* Tabs */}
              <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
                <button
                  onClick={() => setViralTab('settings')}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                    viralTab === 'settings'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Settings className="w-4 h-4 inline mr-2" />
                  Системные настройки
                </button>
                <button
                  onClick={() => setViralTab('baselines')}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                    viralTab === 'baselines'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <BarChart3 className="w-4 h-4 inline mr-2" />
                  Базовые метрики
                </button>
                <button
                  onClick={() => setViralTab('posts')}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                    viralTab === 'posts'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Target className="w-4 h-4 inline mr-2" />
                  Viral посты
                </button>
              </div>

              {/* Settings Tab */}
              {viralTab === 'settings' && (
                <div className="space-y-6">
                  {/* Viral Weights */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center">
                        <Zap className="w-5 h-5 mr-2 text-yellow-500" />
                        Веса для расчета Engagement Rate
                      </CardTitle>
                      <p className="text-sm text-gray-600">
                        Коэффициенты для пересылок, реакций и комментариев
                      </p>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <Label className="text-sm font-medium">Пересылки (forward_rate)</Label>
                          <Input
                            type="number"
                            step="0.1"
                            min="0"
                            max="1"
                            defaultValue={systemSettings.find((s: any) => s.key === 'viral_weights')?.value?.forward_rate || 0.5}
                            onBlur={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'viral_weights')
                              if (setting) {
                                const newValue = { ...setting.value, forward_rate: parseFloat(e.target.value) }
                                updateSystemSetting('viral_weights', newValue)
                              }
                            }}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Реакции (reaction_rate)</Label>
                          <Input
                            type="number"
                            step="0.1"
                            min="0"
                            max="1"
                            defaultValue={systemSettings.find((s: any) => s.key === 'viral_weights')?.value?.reaction_rate || 0.3}
                            onBlur={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'viral_weights')
                              if (setting) {
                                const newValue = { ...setting.value, reaction_rate: parseFloat(e.target.value) }
                                updateSystemSetting('viral_weights', newValue)
                              }
                            }}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Комментарии (reply_rate)</Label>
                          <Input
                            type="number"
                            step="0.1"
                            min="0"
                            max="1"
                            defaultValue={systemSettings.find((s: any) => s.key === 'viral_weights')?.value?.reply_rate || 0.2}
                            onBlur={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'viral_weights')
                              if (setting) {
                                const newValue = { ...setting.value, reply_rate: parseFloat(e.target.value) }
                                updateSystemSetting('viral_weights', newValue)
                              }
                            }}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Viral Thresholds */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center">
                        <Target className="w-5 h-5 mr-2 text-red-500" />
                        Пороги определения "залетевших" постов
                      </CardTitle>
                      <p className="text-sm text-gray-600">
                        Минимальные значения для классификации поста как "залетевшего"
                      </p>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label className="text-sm font-medium">Мин. Viral Score</Label>
                          <Input
                            type="number"
                            step="0.1"
                            min="0"
                            defaultValue={systemSettings.find((s: any) => s.key === 'viral_thresholds')?.value?.min_viral_score || 1.5}
                            onBlur={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'viral_thresholds')
                              if (setting) {
                                const newValue = { ...setting.value, min_viral_score: parseFloat(e.target.value) }
                                updateSystemSetting('viral_thresholds', newValue)
                              }
                            }}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Мин. Z-score</Label>
                          <Input
                            type="number"
                            step="0.1"
                            min="0"
                            defaultValue={systemSettings.find((s: any) => s.key === 'viral_thresholds')?.value?.min_zscore || 1.5}
                            onBlur={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'viral_thresholds')
                              if (setting) {
                                const newValue = { ...setting.value, min_zscore: parseFloat(e.target.value) }
                                updateSystemSetting('viral_thresholds', newValue)
                              }
                            }}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Мин. множитель медианы</Label>
                          <Input
                            type="number"
                            step="0.1"
                            min="1"
                            defaultValue={systemSettings.find((s: any) => s.key === 'viral_thresholds')?.value?.min_median_multiplier || 2.0}
                            onBlur={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'viral_thresholds')
                              if (setting) {
                                const newValue = { ...setting.value, min_median_multiplier: parseFloat(e.target.value) }
                                updateSystemSetting('viral_thresholds', newValue)
                              }
                            }}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Мин. процент просмотров</Label>
                          <Input
                            type="number"
                            step="0.0001"
                            min="0"
                            max="1"
                            defaultValue={systemSettings.find((s: any) => s.key === 'viral_thresholds')?.value?.min_views_percentile || 0.001}
                            onBlur={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'viral_thresholds')
                              if (setting) {
                                const newValue = { ...setting.value, min_views_percentile: parseFloat(e.target.value) }
                                updateSystemSetting('viral_thresholds', newValue)
                              }
                            }}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Baseline Calculation */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center">
                        <BarChart3 className="w-5 h-5 mr-2 text-blue-500" />
                        Настройки расчета базовых метрик
                      </CardTitle>
                      <p className="text-sm text-gray-600">
                        Параметры для анализа истории каналов
                      </p>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label className="text-sm font-medium">Глубина истории (дни)</Label>
                          <Input
                            type="number"
                            min="7"
                            max="90"
                            defaultValue={systemSettings.find((s: any) => s.key === 'baseline_calculation')?.value?.history_days || 30}
                            onBlur={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'baseline_calculation')
                              if (setting) {
                                const newValue = { ...setting.value, history_days: parseInt(e.target.value) }
                                updateSystemSetting('baseline_calculation', newValue)
                              }
                            }}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Мин. постов для базовых метрик</Label>
                          <Input
                            type="number"
                            min="5"
                            max="50"
                            defaultValue={systemSettings.find((s: any) => s.key === 'baseline_calculation')?.value?.min_posts_for_baseline || 10}
                            onBlur={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'baseline_calculation')
                              if (setting) {
                                const newValue = { ...setting.value, min_posts_for_baseline: parseInt(e.target.value) }
                                updateSystemSetting('baseline_calculation', newValue)
                              }
                            }}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Процентиль для выбросов</Label>
                          <Input
                            type="number"
                            min="90"
                            max="99"
                            defaultValue={systemSettings.find((s: any) => s.key === 'baseline_calculation')?.value?.outlier_removal_percentile || 95}
                            onBlur={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'baseline_calculation')
                              if (setting) {
                                const newValue = { ...setting.value, outlier_removal_percentile: parseInt(e.target.value) }
                                updateSystemSetting('baseline_calculation', newValue)
                              }
                            }}
                          />
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Интервал обновления (часы)</Label>
                          <Input
                            type="number"
                            min="1"
                            max="168"
                            defaultValue={systemSettings.find((s: any) => s.key === 'baseline_calculation')?.value?.baseline_update_interval_hours || 24}
                            onBlur={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'baseline_calculation')
                              if (setting) {
                                const newValue = { ...setting.value, baseline_update_interval_hours: parseInt(e.target.value) }
                                updateSystemSetting('baseline_calculation', newValue)
                              }
                            }}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Viral Calculation */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center">
                        <Settings className="w-5 h-5 mr-2 text-green-500" />
                        Настройки автоматического расчета
                      </CardTitle>
                      <p className="text-sm text-gray-600">
                        Параметры для фоновой обработки метрик виральности
                      </p>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="auto_calculate_viral"
                            defaultChecked={systemSettings.find((s: any) => s.key === 'viral_calculation')?.value?.auto_calculate_viral ?? true}
                            onChange={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'viral_calculation')
                              if (setting) {
                                const newValue = { ...setting.value, auto_calculate_viral: e.target.checked }
                                updateSystemSetting('viral_calculation', newValue)
                              }
                            }}
                          />
                          <Label htmlFor="auto_calculate_viral" className="text-sm">Автоматический расчет метрик</Label>
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Размер батча</Label>
                          <Input
                            type="number"
                            min="10"
                            max="1000"
                            defaultValue={systemSettings.find((s: any) => s.key === 'viral_calculation')?.value?.batch_size || 100}
                            onBlur={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'viral_calculation')
                              if (setting) {
                                const newValue = { ...setting.value, batch_size: parseInt(e.target.value) }
                                updateSystemSetting('viral_calculation', newValue)
                              }
                            }}
                          />
                        </div>
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="update_existing_posts"
                            defaultChecked={systemSettings.find((s: any) => s.key === 'viral_calculation')?.value?.update_existing_posts ?? false}
                            onChange={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'viral_calculation')
                              if (setting) {
                                const newValue = { ...setting.value, update_existing_posts: e.target.checked }
                                updateSystemSetting('viral_calculation', newValue)
                              }
                            }}
                          />
                          <Label htmlFor="update_existing_posts" className="text-sm">Обновлять существующие метрики</Label>
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Мин. просмотры для расчета</Label>
                          <Input
                            type="number"
                            min="10"
                            defaultValue={systemSettings.find((s: any) => s.key === 'viral_calculation')?.value?.min_views_for_viral || 100}
                            onBlur={(e) => {
                              const setting = systemSettings.find((s: any) => s.key === 'viral_calculation')
                              if (setting) {
                                const newValue = { ...setting.value, min_views_for_viral: parseInt(e.target.value) }
                                updateSystemSetting('viral_calculation', newValue)
                              }
                            }}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Actions */}
                  <div className="flex justify-center pt-4 gap-4">
                    <Button
                      onClick={async () => {
                        try {
                          // Принудительно сохраняем все текущие настройки
                          const viralWeights = systemSettings.find((s: any) => s.key === 'viral_weights')
                          const viralThresholds = systemSettings.find((s: any) => s.key === 'viral_thresholds')
                          const baselineCalc = systemSettings.find((s: any) => s.key === 'baseline_calculation')
                          const viralCalc = systemSettings.find((s: any) => s.key === 'viral_calculation')

                          if (viralWeights) await updateSystemSetting('viral_weights', viralWeights.value)
                          if (viralThresholds) await updateSystemSetting('viral_thresholds', viralThresholds.value)
                          if (baselineCalc) await updateSystemSetting('baseline_calculation', baselineCalc.value)
                          if (viralCalc) await updateSystemSetting('viral_calculation', viralCalc.value)

                          alert('Настройки сохранены!')
                          await loadViralSettings()
                        } catch (error) {
                          console.error('Error saving settings:', error)
                          alert('Ошибка при сохранении настроек')
                        }
                      }}
                      variant="default"
                    >
                      <Check className="w-4 h-4 mr-2" />
                      Сохранить настройки
                    </Button>

                                      <Button
                    onClick={async () => {
                      try {
                        const result = await apiClient.calculateViralMetricsBatch(undefined, 50)
                        alert(`Обработано ${result.processed} постов`)
                        await loadViralSettings()
                      } catch (error) {
                        console.error('Error calculating viral metrics:', error)
                        alert('Ошибка при расчете метрик')
                      }
                    }}
                    variant="outline"
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    Рассчитать метрики для 50 постов
                  </Button>

                  <Button
                    onClick={async () => {
                      if (!confirm('Это может занять много времени! Вы уверены, что хотите пересчитать метрики для ВСЕХ постов?')) {
                        return
                      }

                      try {
                        const result = await apiClient.calculateViralMetricsAllPosts()
                        alert(`${result.message}\n\nОбработано: ${result.processed_posts}/${result.total_posts} постов\nНайдено виральных: ${result.channels.reduce((sum, ch) => sum + ch.viral_posts, 0)}`)
                        await loadViralSettings()
                      } catch (error) {
                        console.error('Error calculating all viral metrics:', error)
                        alert('Ошибка при расчете метрик')
                      }
                    }}
                    variant="outline"
                    className="border-red-300 text-red-600 hover:bg-red-50 hover:text-red-700"
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    Рассчитать метрики для ВСЕХ постов
                  </Button>
                  </div>
                </div>
              )}

              {/* Baselines Tab */}
              {viralTab === 'baselines' && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-medium">Базовые метрики каналов</h3>
                    <div className="flex gap-2">
                      <Button
                        onClick={async () => {
                          try {
                            const channels = channelBaselines.map((b: any) => b.channel.username)
                            const result = await apiClient.startBulkParsing(channels, 30, 100)
                            alert(`Запущен массовый парсинг для ${channels.length} каналов`)
                          } catch (error) {
                            console.error('Error starting bulk parsing:', error)
                            alert('Ошибка при запуске парсинга')
                          }
                        }}
                        variant="outline"
                      >
                        <Database className="w-4 h-4 mr-2" />
                        Спарсить все каналы
                      </Button>
                      <Button onClick={updateAllBaselines} variant="outline">
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Пересчитать все метрики
                      </Button>
                    </div>
                  </div>

                  <div className="grid gap-4">
                    {channelBaselines.map((baseline: any) => (
                      <Card key={baseline.channel.channel_username}>
                        <CardHeader>
                          <div className="flex justify-between items-center">
                            <CardTitle>{baseline.channel.title || baseline.channel.username}</CardTitle>
                            <div className="flex items-center space-x-2">
                              <Badge variant={baseline.baseline.baseline_status === 'ready' ? 'default' : 'secondary'}>
                                {baseline.baseline.baseline_status === 'ready' ? 'Готов' : 'Обучение'}
                              </Badge>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={async () => {
                                  try {
                                    await apiClient.ensureChannelBaseline(baseline.channel.username, true)
                                    alert(`Базовые метрики для ${baseline.channel.username} обновлены`)
                                    await loadViralSettings()
                                  } catch (error) {
                                    console.error('Error ensuring baseline:', error)
                                    alert('Ошибка при обновлении базовых метрик')
                                  }
                                }}
                              >
                                <RefreshCw className="w-3 h-3 mr-1" />
                                Пересчитать
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={async () => {
                                  try {
                                    const result = await apiClient.startChannelParsing(baseline.channel.username, 30, 100)
                                    alert(`Парсинг ${baseline.channel.username} запущен`)
                                  } catch (error) {
                                    console.error('Error starting parsing:', error)
                                    alert('Ошибка при запуске парсинга')
                                  }
                                }}
                              >
                                <Database className="w-3 h-3 mr-1" />
                                Спарсить
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={async () => {
                                  try {
                                    const result = await apiClient.calculateViralMetricsBatch(baseline.channel.username, 50)
                                    alert(`Обработано ${result.processed} постов для ${baseline.channel.username}`)
                                    await loadViralSettings()
                                  } catch (error) {
                                    console.error('Error calculating viral metrics:', error)
                                    alert('Ошибка при расчете метрик')
                                  }
                                }}
                              >
                                <Zap className="w-3 h-3 mr-1" />
                                Рассчитать метрики
                              </Button>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div>
                              <p className="text-sm text-gray-600">Средний engagement</p>
                              <p className="text-lg font-bold">{(baseline.baseline.avg_engagement_rate * 100).toFixed(2)}%</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600">Медиана</p>
                              <p className="text-lg font-bold">{(baseline.baseline.median_engagement_rate * 100).toFixed(2)}%</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600">75-й процентиль</p>
                              <p className="text-lg font-bold">{(baseline.baseline.p75_engagement_rate * 100).toFixed(2)}%</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600">Постов проанализировано</p>
                              <p className="text-lg font-bold">{baseline.baseline.posts_analyzed}</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Viral Posts Tab */}
              {viralTab === 'posts' && (
                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Топ "залетевших" постов</h3>

                  <div className="grid gap-4">
                    {viralPosts.map((post: any) => (
                      <Card key={post.id}>
                        <CardHeader>
                          <div className="flex justify-between items-center">
                            <CardTitle className="text-base">
                              {post.channel_title} • {new Date(post.date).toLocaleDateString('ru-RU')}
                            </CardTitle>
                            <div className="flex items-center space-x-2">
                              <Badge className="bg-yellow-100 text-yellow-800">
                                Score: {post.viral_score?.toFixed(2)}
                              </Badge>
                              <Badge className="bg-blue-100 text-blue-800">
                                {post.views} просмотров
                              </Badge>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <p className="text-sm text-gray-700 mb-3 line-clamp-2">
                            {post.text_preview}
                          </p>
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <span className="text-gray-600">Engagement rate:</span>
                              <span className="font-medium ml-1">{(post.engagement_rate * 100)?.toFixed(2)}%</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Z-score:</span>
                              <span className="font-medium ml-1">{post.zscore?.toFixed(2)}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Медиана:</span>
                              <span className="font-medium ml-1">{(post.median_multiplier)?.toFixed(2)}x</span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Telegram Auth Modal */}
      {showTelegramModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-md w-full mx-4">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  <Database className="w-6 h-6 mr-2 text-blue-500" />
                  Авторизация Telegram
                </h2>
                <Button variant="outline" size="sm" onClick={() => setShowTelegramModal(false)}>
                  ✕
                </Button>
              </div>

              <div className="space-y-4">
                {/* Status */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Статус:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      telegramStatus?.telegram_status === 'healthy' ? 'bg-green-100 text-green-800' :
                      telegramStatus?.telegram_authorization_needed ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {telegramStatus?.telegram_status === 'healthy' ? 'Подключено' :
                       telegramStatus?.telegram_authorization_needed ? 'Требуется авторизация' :
                       'Неизвестно'}
                    </span>
                  </div>
                </div>

                {/* Auth Steps */}
                {authStep === 'phone' && (
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="phone">Номер телефона</Label>
                      <Input
                        id="phone"
                        type="tel"
                        placeholder="+7XXXXXXXXXX"
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Введите номер телефона в международном формате
                      </p>
                    </div>

                    <Button
                      onClick={sendVerificationCode}
                      disabled={authLoading}
                      className="w-full"
                    >
                      {authLoading ? 'Отправка...' : 'Отправить код'}
                    </Button>
                  </div>
                )}

                {authStep === 'code' && (
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="code">Код подтверждения</Label>
                      <Input
                        id="code"
                        type="text"
                        placeholder="12345"
                        value={verificationCode}
                        onChange={(e) => setVerificationCode(e.target.value)}
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Код отправлен на номер {phoneNumber}
                      </p>
                    </div>

                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        onClick={() => setAuthStep('phone')}
                        className="flex-1"
                      >
                        Назад
                      </Button>
                      <Button
                        onClick={verifyCode}
                        disabled={authLoading}
                        className="flex-1"
                      >
                        {authLoading ? 'Проверка...' : 'Подтвердить'}
                      </Button>
                    </div>
                  </div>
                )}

                {/* Start Auth Button */}
                <div className="pt-4 border-t space-y-3">
                  <Button
                    variant="outline"
                    onClick={startTelegramAuth}
                    disabled={authLoading}
                    className="w-full"
                  >
                    {authLoading ? 'Проверка...' : 'Проверить статус Telegram'}
                  </Button>

                  {/* Reset Auth Button */}
                  <Button
                    variant="outline"
                    onClick={resetTelegramAuth}
                    disabled={authLoading}
                    className="w-full text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    {authLoading ? 'Сброс...' : '🔄 Сбросить авторизацию'}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* LLM Settings Modal */}
      {showLLMModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  <Settings className="w-6 h-6 mr-2 text-blue-500" />
                  Настройки LLM Пайплайна
                </h2>
                <Button variant="outline" onClick={() => setShowLLMModal(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>

              {/* Tabs */}
              <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
                <button
                  onClick={() => setLlmTab('prompts')}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                    llmTab === 'prompts'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Edit className="w-4 h-4 inline mr-2" />
                  Промпты
                </button>
                <button
                  onClick={() => setLlmTab('rubrics')}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                    llmTab === 'rubrics'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Target className="w-4 h-4 inline mr-2" />
                  Рубрики
                </button>
                <button
                  onClick={() => setLlmTab('formats')}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                    llmTab === 'formats'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <BarChart3 className="w-4 h-4 inline mr-2" />
                  Форматы
                </button>
              </div>

              {/* Prompts Tab */}
              {llmTab === 'prompts' && (
                <div className="space-y-6">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-medium">Управление промптами</h3>
                    <Button onClick={() => setShowPromptTest(!showPromptTest)} variant="outline">
                      <Zap className="w-4 h-4 mr-2" />
                      {showPromptTest ? 'Скрыть тестирование' : 'Показать тестирование'}
                    </Button>
                  </div>

                  {/* Prompts List */}
                  <div className="grid gap-4">
                    {dbPrompts.map((prompt: any) => (
                      <Card key={prompt.id}>
                        <CardHeader>
                          <div className="flex justify-between items-center">
                            <div>
                              <CardTitle className="text-base">{prompt.name}</CardTitle>
                              <p className="text-sm text-gray-600">{prompt.description}</p>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Badge variant={prompt.is_active ? 'default' : 'secondary'}>
                                {prompt.is_active ? 'Активен' : 'Неактивен'}
                              </Badge>
                              <Badge className="bg-blue-100 text-blue-800">
                                {getModelDisplayName(prompt.model)}
                              </Badge>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => editPrompt(prompt)}
                              >
                                <Edit className="w-3 h-3 mr-1" />
                                Редактировать
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => deletePrompt(prompt.id.toString())}
                              >
                                <Trash2 className="w-3 h-3 mr-1" />
                                Удалить
                              </Button>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="text-gray-600">Тип:</span>
                              <span className="ml-1 font-medium">{prompt.prompt_type}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Температура:</span>
                              <span className="ml-1 font-medium">{prompt.temperature}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Макс. токенов:</span>
                              <span className="ml-1 font-medium">{prompt.max_tokens}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Создан:</span>
                              <span className="ml-1 font-medium">
                                {new Date(prompt.created_at).toLocaleDateString('ru-RU')}
                              </span>
                            </div>
                          </div>
                          <div className="mt-3">
                            <p className="text-sm text-gray-600 mb-1">Содержимое:</p>
                            <div className="bg-gray-50 p-3 rounded text-sm max-h-32 overflow-y-auto">
                              {(() => {
                                const systemText = prompt.system_prompt || ''
                                const userText = prompt.user_prompt || ''
                                const combinedText = systemText + (systemText && userText ? '\n\n--- User ---\n\n' : '') + userText

                                return combinedText.length > 200 ?
                                  `${combinedText.substring(0, 200)}...` :
                                  combinedText || 'Промпт не настроен'
                              })()}
                            </div>
                            {(() => {
                              const systemVars = extractVariablesFromPrompt(prompt.system_prompt || '')
                              const userVars = extractVariablesFromPrompt(prompt.user_prompt || '')
                              const allVars = [...new Set([...systemVars, ...userVars])]

                              return allVars.length > 0 && (
                                <div className="mt-2">
                                  <p className="text-xs text-gray-500">Переменные: {allVars.join(', ')}</p>
                                </div>
                              )
                            })()}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {/* Prompt Form */}
                  <div id="prompt-form">
                    <Card className="border-blue-300 shadow-lg">
                    <CardHeader>
                      <CardTitle className="text-lg">
                        {promptForm.id ? 'Редактирование промпта' : 'Создание нового промпта'}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="prompt_name">Название</Label>
                          <Input
                            id="prompt_name"
                            value={promptForm.name}
                            onChange={(e) => setPromptForm({...promptForm, name: e.target.value})}
                            placeholder="Название промпта"
                          />
                        </div>
                        <div>
                          <Label htmlFor="prompt_type">Тип промпта</Label>
                          <Select
                            value={promptForm.prompt_type || "custom"}
                            onValueChange={(value) => setPromptForm({...promptForm, prompt_type: value})}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Выберите тип промпта" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="filter">Фильтр постов</SelectItem>
                              <SelectItem value="analysis">Анализ поста</SelectItem>
                              <SelectItem value="rubric_selection">Выбор рубрик</SelectItem>
                              <SelectItem value="generation">Генерация сценария</SelectItem>
                              <SelectItem value="project_context">Контекст проекта</SelectItem>
                              <SelectItem value="custom">Пользовательский</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      <div>
                        <Label htmlFor="prompt_description">Описание</Label>
                        <Input
                          id="prompt_description"
                          value={promptForm.description}
                          onChange={(e) => setPromptForm({...promptForm, description: e.target.value})}
                          placeholder="Краткое описание промпта"
                        />
                      </div>

                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <Label htmlFor="prompt_model">Модель</Label>
                          <Select
                            value={promptForm.model || "gpt-4o-mini"}
                            onValueChange={(value) => setPromptForm({...promptForm, model: value})}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Выберите модель" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="gpt-4o-mini">GPT-4o Mini</SelectItem>
                              <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                              <SelectItem value="claude-3-5-sonnet-20241022">Claude-3.5-Sonnet</SelectItem>
                              <SelectItem value="claude-3-haiku-20240307">Claude-3-Haiku</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label htmlFor="prompt_temperature">Температура</Label>
                          <Input
                            id="prompt_temperature"
                            type="number"
                            step="0.1"
                            min="0"
                            max="2"
                            value={promptForm.temperature}
                            onChange={(e) => setPromptForm({...promptForm, temperature: parseFloat(e.target.value)})}
                          />
                        </div>
                        <div>
                          <Label htmlFor="prompt_max_tokens">Макс. токенов</Label>
                          <Input
                            id="prompt_max_tokens"
                            type="number"
                            min="100"
                            max="4000"
                            value={promptForm.max_tokens}
                            onChange={(e) => setPromptForm({...promptForm, max_tokens: parseInt(e.target.value)})}
                          />
                        </div>
                      </div>

                      <div>
                        <Label htmlFor="prompt_system">System Prompt (инструкции для AI)</Label>
                        <Textarea
                          id="prompt_system"
                          value={promptForm.system_prompt}
                          onChange={(e) => setPromptForm({...promptForm, system_prompt: e.target.value})}
                          placeholder="Роль и инструкции для AI. Например: 'Ты эксперт по анализу контента...'"
                          rows={6}
                        />
                      </div>

                      <div>
                        <Label htmlFor="prompt_user">User Prompt (данные для обработки)</Label>
                        <Textarea
                          id="prompt_user"
                          value={promptForm.user_prompt}
                          onChange={(e) => setPromptForm({...promptForm, user_prompt: e.target.value})}
                          placeholder="Данные и контекст для обработки. Используйте {{variable}} для подстановки переменных."
                          rows={6}
                        />
                        {(() => {
                          const systemVars = extractVariablesFromPrompt(promptForm.system_prompt || '')
                          const userVars = extractVariablesFromPrompt(promptForm.user_prompt || '')
                          const allVars = [...new Set([...systemVars, ...userVars])]

                          return allVars.length > 0 && (
                            <div className="mt-2 p-3 bg-blue-50 rounded text-sm">
                              <p className="text-blue-800 font-medium mb-2">Найденные переменные:</p>
                              <div className="space-y-1">
                                {allVars.map((variable) => {
                                  const inSystem = systemVars.includes(variable)
                                  const inUser = userVars.includes(variable)
                                  return (
                                    <div key={variable} className="flex items-center space-x-2">
                                      <code className="bg-blue-100 px-2 py-1 rounded text-xs font-mono">
                                        {`{{${variable}}}`}
                                      </code>
                                      <div className="flex items-center space-x-2 text-xs">
                                        <span className="text-blue-600">
                                          {variableHints[variable as keyof typeof variableHints] || 'Описание отсутствует'}
                                        </span>
                                        <div className="flex space-x-1">
                                          {inSystem && (
                                            <span className="bg-green-100 text-green-700 px-1 rounded">System</span>
                                          )}
                                          {inUser && (
                                            <span className="bg-blue-100 text-blue-700 px-1 rounded">User</span>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                  )
                                })}
                              </div>
                              <div className="mt-3 pt-2 border-t border-blue-200">
                                <p className="text-blue-700 font-medium text-xs mb-1">Подсказки по переменным:</p>
                                <p className="text-blue-600 text-xs">
                                  Используйте двойные фигурные скобки для переменных: {'{{variable_name}}'}
                                </p>
                              </div>
                            </div>
                          )
                        })()}
                      </div>

                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="prompt_active"
                          checked={promptForm.is_active}
                          onChange={(e) => setPromptForm({...promptForm, is_active: e.target.checked})}
                        />
                        <Label htmlFor="prompt_active">Активен</Label>
                      </div>

                      <div className="flex justify-end space-x-2">
                        <Button variant="outline" onClick={resetPromptForm}>
                          Отмена
                        </Button>
                        <Button onClick={savePrompt}>
                          {promptForm.id ? 'Обновить' : 'Создать'} промпт
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                  </div>

                  {/* Prompt Testing */}
                  {showPromptTest && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Тестирование промпта</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <Label>Выберите промпт для тестирования</Label>
                          <Select
                            value={selectedTestPromptId}
                            onValueChange={(value) => {
                              setSelectedTestPromptId(value)
                              const prompt = dbPrompts.find((p: any) => p.id.toString() === value)
                              if (prompt) {
                                const variables = extractVariablesFromPrompt(prompt.content)
                                const testVars: Record<string, string> = {}
                                variables.forEach(v => {
                                  testVars[v] = ''
                                })
                                setPromptTestVariables(testVars)
                                setPromptTestResult(null) // Очищаем предыдущие результаты
                              }
                            }}>
                            <SelectTrigger>
                              <SelectValue placeholder="Выберите промпт" />
                            </SelectTrigger>
                            <SelectContent>
                              {dbPrompts.map((prompt: any) => (
                                <SelectItem key={prompt.id} value={prompt.id.toString()}>
                                  {prompt.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        {Object.keys(promptTestVariables).length > 0 && (
                          <div className="space-y-3">
                            <h4 className="font-medium">Переменные для подстановки:</h4>
                            {Object.entries(promptTestVariables).map(([key, value]) => (
                              <div key={key}>
                                <Label htmlFor={`var_${key}`}>{key}</Label>
                                <Input
                                  id={`var_${key}`}
                                  value={value}
                                  onChange={(e) => setPromptTestVariables({
                                    ...promptTestVariables,
                                    [key]: e.target.value
                                  })}
                                  placeholder={`Значение для ${key}`}
                                />
                              </div>
                            ))}
                          </div>
                        )}

                        <Button
                          onClick={() => {
                            if (selectedTestPromptId) {
                              testPrompt(parseInt(selectedTestPromptId))
                            }
                          }}
                          disabled={!selectedTestPromptId || Object.keys(promptTestVariables).length === 0}
                        >
                          <Zap className="w-4 h-4 mr-2" />
                          Протестировать
                        </Button>

                        {promptTestResult && (
                          <div className="mt-4 p-4 bg-gray-50 rounded">
                            <h4 className="font-medium mb-2">Результат тестирования:</h4>
                            <div className="space-y-2 text-sm">
                              <p><strong>Модель:</strong> {promptTestResult.model}</p>
                              <p><strong>Температура:</strong> {promptTestResult.temperature}</p>
                              <p><strong>Макс. токенов:</strong> {promptTestResult.max_tokens}</p>
                              {promptTestResult.processing_time && (
                                <p><strong>Время обработки:</strong> {promptTestResult.processing_time} сек</p>
                              )}
                              {promptTestResult.tokens_used > 0 && (
                                <p><strong>Использовано токенов:</strong> {promptTestResult.tokens_used}</p>
                              )}
                              <div>
                                <strong>Обработанный промпт:</strong>
                                <div className="mt-1 p-2 bg-white rounded text-xs max-h-40 overflow-y-auto">
                                  <div>
                                    <strong>System:</strong>
                                    <div className="bg-blue-50 p-2 rounded mt-1 mb-2 text-sm">
                                      {promptTestResult.processed_system_prompt || 'Не задан'}
                                    </div>
                                    <strong>User:</strong>
                                    <div className="bg-green-50 p-2 rounded mt-1 text-sm">
                                      {promptTestResult.processed_user_prompt || 'Не задан'}
                                    </div>
                                  </div>
                                </div>
                              </div>
                              {promptTestResult.llm_response && (
                                <div>
                                  <strong>Ответ LLM:</strong>
                                  <div className="mt-1 p-2 bg-green-50 border border-green-200 rounded text-xs max-h-60 overflow-y-auto">
                                    {promptTestResult.llm_response}
                                  </div>
                                </div>
                              )}
                              {promptTestResult.error && (
                                <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs">
                                  <strong className="text-red-600">Ошибка:</strong> {promptTestResult.error}
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}

              {/* Rubrics Tab */}
              {llmTab === 'rubrics' && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-medium">Управление рубриками</h3>
                    <Button onClick={() => editRubric({})}>
                      <Plus className="w-4 h-4 mr-2" />
                      Добавить рубрику
                    </Button>
                  </div>

                  <div className="grid gap-4">
                    {rubrics.map((rubric: any) => (
                      <Card key={rubric.id}>
                        <CardHeader>
                          <div className="flex justify-between items-center">
                            <div>
                              <CardTitle className="text-base">{rubric.name}</CardTitle>
                              <p className="text-sm text-gray-600">{rubric.description}</p>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Badge variant={rubric.is_active ? 'default' : 'secondary'}>
                                {rubric.is_active ? 'Активна' : 'Неактивна'}
                              </Badge>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => editRubric(rubric)}
                              >
                                <Edit className="w-3 h-3 mr-1" />
                                Редактировать
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => deleteRubric(rubric.id)}
                              >
                                <Trash2 className="w-3 h-3 mr-1" />
                                Удалить
                              </Button>
                            </div>
                          </div>
                        </CardHeader>
                      </Card>
                    ))}
                  </div>

                  {/* Rubric Form */}
                  <div id="rubric-form">
                    <Card className="border-blue-300 shadow-lg">
                      <CardHeader>
                        <CardTitle className="text-lg">
                          {rubricForm.id ? 'Редактирование рубрики' : 'Создание новой рубрики'}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="rubric_name">Название</Label>
                            <Input
                              id="rubric_name"
                              value={rubricForm.name}
                              onChange={(e) => setRubricForm({...rubricForm, name: e.target.value})}
                              placeholder="Название рубрики"
                            />
                          </div>
                          <div>
                            <Label htmlFor="rubric_category">Категория</Label>
                            <Input
                              id="rubric_category"
                              value={rubricForm.category}
                              onChange={(e) => setRubricForm({...rubricForm, category: e.target.value})}
                              placeholder="Категория рубрики"
                            />
                          </div>
                        </div>

                        <div>
                          <Label htmlFor="rubric_description">Описание</Label>
                          <Textarea
                            id="rubric_description"
                            value={rubricForm.description}
                            onChange={(e) => setRubricForm({...rubricForm, description: e.target.value})}
                            placeholder="Описание рубрики"
                            rows={3}
                          />
                        </div>

                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="rubric_active"
                            checked={rubricForm.is_active}
                            onChange={(e) => setRubricForm({...rubricForm, is_active: e.target.checked})}
                          />
                          <Label htmlFor="rubric_active">Активна</Label>
                        </div>

                        <div className="flex justify-end space-x-2">
                          <Button variant="outline" onClick={() => setRubricForm({id: '', name: '', description: '', category: '', is_active: true})}>
                            Отмена
                          </Button>
                          <Button onClick={saveRubric}>
                            {rubricForm.id ? 'Обновить' : 'Создать'} рубрику
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}

              {/* Formats Tab */}
              {llmTab === 'formats' && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-medium">Управление форматами</h3>
                    <Button onClick={() => editFormat({})}>
                      <Plus className="w-4 h-4 mr-2" />
                      Добавить формат
                    </Button>
                  </div>

                  <div className="grid gap-4">
                    {formats.map((format: any) => (
                      <Card key={format.id}>
                        <CardHeader>
                          <div className="flex justify-between items-center">
                            <div>
                              <CardTitle className="text-base">{format.name}</CardTitle>
                              <p className="text-sm text-gray-600">{format.description}</p>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Badge variant={format.is_active ? 'default' : 'secondary'}>
                                {format.is_active ? 'Активен' : 'Неактивен'}
                              </Badge>
                              <span className="text-sm text-gray-500">
                                {format.duration_seconds} сек
                              </span>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => editFormat(format)}
                              >
                                <Edit className="w-3 h-3 mr-1" />
                                Редактировать
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => deleteFormat(format.id)}
                              >
                                <Trash2 className="w-3 h-3 mr-1" />
                                Удалить
                              </Button>
                            </div>
                          </div>
                        </CardHeader>
                      </Card>
                    ))}
                  </div>

                  {/* Format Form */}
                  <div id="format-form">
                    <Card className="border-blue-300 shadow-lg">
                      <CardHeader>
                        <CardTitle className="text-lg">
                          {formatForm.id ? 'Редактирование формата' : 'Создание нового формата'}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="format_name">Название</Label>
                            <Input
                              id="format_name"
                              value={formatForm.name}
                              onChange={(e) => setFormatForm({...formatForm, name: e.target.value})}
                              placeholder="Название формата"
                            />
                          </div>
                          <div>
                            <Label htmlFor="format_duration">Длительность (сек)</Label>
                            <Input
                              id="format_duration"
                              type="number"
                              min="30"
                              max="180"
                              value={formatForm.duration_seconds}
                              onChange={(e) => setFormatForm({...formatForm, duration_seconds: parseInt(e.target.value)})}
                              placeholder="60"
                            />
                          </div>
                        </div>

                        <div>
                          <Label htmlFor="format_description">Описание</Label>
                          <Textarea
                            id="format_description"
                            value={formatForm.description}
                            onChange={(e) => setFormatForm({...formatForm, description: e.target.value})}
                            placeholder="Описание формата"
                            rows={3}
                          />
                        </div>

                        <div>
                          <Label htmlFor="format_structure">Структура (JSON)</Label>
                          <Textarea
                            id="format_structure"
                            value={JSON.stringify(formatForm.structure, null, 2)}
                            onChange={(e) => {
                              try {
                                const structure = JSON.parse(e.target.value)
                                setFormatForm({...formatForm, structure})
                              } catch (err) {
                                // Не валидный JSON, но позволяем редактировать
                              }
                            }}
                            placeholder='{"hook": "3-5 сек", "insight": "5-10 сек", "steps": "10-15 сек", "cta": "3-5 сек"}'
                            rows={4}
                          />
                        </div>

                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="format_active"
                            checked={formatForm.is_active}
                            onChange={(e) => setFormatForm({...formatForm, is_active: e.target.checked})}
                          />
                          <Label htmlFor="format_active">Активен</Label>
                        </div>

                        <div className="flex justify-end space-x-2">
                          <Button variant="outline" onClick={() => setFormatForm({id: '', name: '', description: '', duration_seconds: 60, structure: {}, is_active: true})}>
                            Отмена
                          </Button>
                          <Button onClick={saveFormat}>
                            {formatForm.id ? 'Обновить' : 'Создать'} формат
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end space-x-2 pt-6 border-t">
                <Button variant="outline" onClick={() => setShowLLMModal(false)}>
                  Закрыть
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Prices Modal */}
      {showPricesModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  <DollarSign className="w-6 h-6 mr-2 text-green-500" />
                  Цены LLM API
                </h2>
                <Button variant="outline" onClick={() => setShowPricesModal(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>

              {loadingPrices ? (
                <div className="flex justify-center items-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                  <span className="ml-3 text-gray-600">Загрузка цен...</span>
                </div>
              ) : priceReport ? (
                <div className="space-y-6">
                  {/* Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-gray-600">Всего моделей</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{Object.keys(priceReport.prices).length}</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-gray-600">Алертов</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-orange-600">{priceReport.summary.total_alerts}</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-gray-600">Последнее обновление</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">
                          {new Date(priceReport.summary.last_update).toLocaleString('ru-RU')}
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Price Table */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Текущие цены (за 1M токенов)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left py-2 font-medium">Модель</th>
                              <th className="text-left py-2 font-medium">Input</th>
                              <th className="text-left py-2 font-medium">Output</th>
                              <th className="text-left py-2 font-medium">Источник</th>
                              <th className="text-left py-2 font-medium">Уверенность</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(priceReport.prices).map(([model, prices]: [string, any]) => (
                              <tr key={model} className="border-b">
                                <td className="py-3 font-medium">{model}</td>
                                <td className="py-3">${prices.input.price_per_million.toFixed(3)}</td>
                                <td className="py-3">${prices.output.price_per_million.toFixed(3)}</td>
                                <td className="py-3">
                                  <span className={`px-2 py-1 rounded text-xs ${
                                    prices.input.source === 'api' ? 'bg-green-100 text-green-800' :
                                    prices.input.source === 'web' ? 'bg-blue-100 text-blue-800' :
                                    'bg-gray-100 text-gray-800'
                                  }`}>
                                    {prices.input.source}
                                  </span>
                                </td>
                                <td className="py-3">
                                  <div className="flex items-center">
                                    <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                      <div
                                        className="bg-green-600 h-2 rounded-full"
                                        style={{width: `${prices.input.confidence * 100}%`}}
                                      ></div>
                                    </div>
                                    <span className="text-sm text-gray-600">
                                      {(prices.input.confidence * 100).toFixed(0)}%
                                    </span>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Cost Calculator */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Калькулятор стоимости</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm text-gray-600 mb-4">
                        Примерная стоимость обработки одного поста в пайплайне:
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span>Filter (GPT-4o-mini):</span>
                            <span>$0.0001</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Analysis (Claude):</span>
                            <span>$0.0043</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Rubric Selection (GPT-4o):</span>
                            <span>$0.0158</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Generation (GPT-4o):</span>
                            <span>$0.0044</span>
                          </div>
                        </div>
                        <div className="border-t pt-2">
                          <div className="flex justify-between font-bold text-lg">
                            <span>Итого за пост:</span>
                            <span className="text-green-600">$0.0246</span>
                          </div>
                          <div className="text-sm text-gray-500 mt-1">
                            ≈ 2.46 рублей (курс 100 руб/$)
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="flex justify-end">
                    <Button variant="outline" onClick={() => setShowPricesModal(false)}>
                      Закрыть
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-600">Не удалось загрузить данные о ценах</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Data Cleanup Modal */}
      {showCleanupModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-red-600 flex items-center">
                  <Trash2 className="w-6 h-6 mr-2" />
                  Очистка данных
                </h2>
                <Button variant="outline" onClick={() => setShowCleanupModal(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>

              <div className="space-y-6">
                {/* Settings */}
                <Card>
                  <CardHeader>
                    <CardTitle>Настройки очистки</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="cleanupDays">Период очистки (дни)</Label>
                        <Select
                          value={cleanupDays.toString()}
                          onValueChange={(value) => setCleanupDays(parseInt(value))}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="1">1 день</SelectItem>
                            <SelectItem value="3">3 дня</SelectItem>
                            <SelectItem value="7">7 дней</SelectItem>
                            <SelectItem value="14">14 дней</SelectItem>
                            <SelectItem value="30">30 дней</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <Button
                      onClick={handlePreviewCleanup}
                      className="mt-4"
                      variant="outline"
                    >
                      Предварительный просмотр
                    </Button>
                  </CardContent>
                </Card>

                {/* Preview Results */}
                {cleanupPreview && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-orange-600">Что будет удалено</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        <div className="text-center p-4 bg-red-50 rounded-lg">
                          <div className="text-2xl font-bold text-red-600">{cleanupPreview.summary.posts}</div>
                          <div className="text-sm text-gray-600">Постов</div>
                        </div>
                        <div className="text-center p-4 bg-orange-50 rounded-lg">
                          <div className="text-2xl font-bold text-orange-600">{cleanupPreview.summary.post_analysis}</div>
                          <div className="text-sm text-gray-600">Анализов</div>
                        </div>
                        <div className="text-center p-4 bg-yellow-50 rounded-lg">
                          <div className="text-2xl font-bold text-yellow-600">{cleanupPreview.summary.scenarios}</div>
                          <div className="text-sm text-gray-600">Сценариев</div>
                        </div>
                        <div className="text-center p-4 bg-blue-50 rounded-lg">
                          <div className="text-2xl font-bold text-blue-600">{cleanupPreview.summary.post_metrics}</div>
                          <div className="text-sm text-gray-600">Метрик</div>
                        </div>
                      </div>

                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                        <div className="flex">
                          <AlertCircle className="w-5 h-5 text-yellow-400 mr-3 mt-0.5" />
                          <div>
                            <h3 className="text-sm font-medium text-yellow-800">
                              Затронутые каналы ({cleanupPreview.summary.affected_channels})
                            </h3>
                            <p className="mt-1 text-sm text-yellow-700">
                              {cleanupPreview.affected_channels.slice(0, 5).join(', ')}
                              {cleanupPreview.affected_channels.length > 5 && ` и ещё ${cleanupPreview.affected_channels.length - 5}`}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <div className="flex">
                          <AlertCircle className="w-5 h-5 text-red-400 mr-3 mt-0.5" />
                          <div>
                            <h3 className="text-sm font-medium text-red-800">
                              ⚠️ Предупреждение
                            </h3>
                            <p className="mt-1 text-sm text-red-700">
                              {cleanupPreview.warning}
                              <br />
                              Baseline метрики каналов будут помечены как устаревшие.
                            </p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Confirmation */}
                {cleanupPreview && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-red-600">Подтверждение удаления</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div>
                          <Label htmlFor="confirmText">
                            Введите <strong>DELETE</strong> для подтверждения:
                          </Label>
                          <Input
                            id="confirmText"
                            value={cleanupConfirm}
                            onChange={(e) => setCleanupConfirm(e.target.value)}
                            placeholder="DELETE"
                            className="mt-2"
                          />
                        </div>

                        <div className="flex gap-4">
                          <Button
                            onClick={() => setShowCleanupModal(false)}
                            variant="outline"
                            className="flex-1"
                          >
                            Отмена
                          </Button>
                          <Button
                            onClick={handleExecuteCleanup}
                            disabled={cleanupConfirm !== 'DELETE' || cleanupLoading}
                            className="flex-1 bg-red-600 hover:bg-red-700"
                          >
                            {cleanupLoading ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            ) : (
                              <Trash2 className="w-4 h-4 mr-2" />
                            )}
                            Удалить данные
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sandbox Modal */}
      {showSandboxModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  <FlaskRound className="w-6 h-6 mr-2 text-purple-500" />
                  Песочница: Отладка Pipeline
                </h2>
                <Button variant="outline" onClick={() => setShowSandboxModal(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>

              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>🔧 Pipeline Sandbox</CardTitle>
                    <p className="text-sm text-gray-600">
                      Интерактивная среда для тестирования и отладки pipeline пост-сценарий
                    </p>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Переключатель режима выполнения */}
                    <div className="flex items-center space-x-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex items-center space-x-2">
                        <input
                          type="radio"
                          id="normal_mode"
                          name="execution_mode"
                          checked={!stepByStepMode}
                          onChange={() => {
                            if (stepByStepMode) resetStepByStepExecution()
                          }}
                          className="text-blue-600"
                        />
                        <Label htmlFor="normal_mode" className="text-sm font-medium">
                          Полный pipeline
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input
                          type="radio"
                          id="step_by_step_mode"
                          name="execution_mode"
                          checked={stepByStepMode}
                          onChange={() => {
                            if (!stepByStepMode) startStepByStepExecution()
                          }}
                          className="text-blue-600"
                        />
                        <Label htmlFor="step_by_step_mode" className="text-sm font-medium">
                          Пошаговое выполнение
                        </Label>
                      </div>
                    </div>

                    <div>
                      <Label className="text-sm font-medium mb-2 block">
                        Данные поста (JSON)
                      </Label>
                      <Textarea
                        placeholder={`Пример:
{
  "id": "12345_@dnevteh",
  "message_id": 12345,
  "channel_username": "@dnevteh",
  "text": "Текст поста для анализа",
  "views": 1000,
  "forwards": 50,
  "reactions": 25
}`}
                        value={sandboxPostData}
                        onChange={(e) => {
                          setSandboxPostData(e.target.value)
                          setJsonError('') // Сбрасываем ошибку при изменении
                        }}
                        className={`min-h-[120px] font-mono text-sm ${
                          jsonError ? 'border-red-500 focus:border-red-500' : ''
                        }`}
                      />
                      {jsonError && (
                        <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded border border-red-200">
                          <strong>Ошибка валидации:</strong> {jsonError}
                        </div>
                      )}
                    </div>

                    {/* Кнопки управления */}
                    {stepByStepMode ? (
                      <div className="space-y-4">
                        {/* Индикатор текущего шага */}
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div>
                            <span className="text-sm font-medium">Текущий шаг:</span>
                            <span className="ml-2 text-sm text-blue-600">
                              {currentStep === 0 && "Подготовка данных"}
                              {currentStep === 1 && "Фильтрация поста"}
                              {currentStep === 2 && "Анализ поста"}
                              {currentStep === 3 && "Выбор рубрик"}
                              {currentStep === 4 && "Генерация сценариев"}
                              {currentStep >= 5 && "Завершено"}
                            </span>
                          </div>
                          <Badge variant={canExecuteNext ? "default" : "secondary"}>
                            {canExecuteNext ? "Готов к выполнению" : "Ожидание"}
                          </Badge>
                        </div>

                        {/* Результаты предыдущих шагов */}
                        {stepResults.length > 0 && (
                          <div className="space-y-2">
                            <h4 className="text-sm font-medium">Выполненные шаги:</h4>
                            {stepResults.map((result, index) => (
                              <div key={index} className="flex items-center justify-between text-xs p-2 bg-green-50 rounded border">
                                <span>Шаг {index + 1}: {result.success ? "✅ Успешно" : "❌ Ошибка"}</span>
                                <span>{result.total_tokens || 0} токенов</span>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Кнопки управления */}
                        <div className="flex gap-2">
                          <Button
                            onClick={executeCurrentStep}
                            disabled={sandboxLoading || !canExecuteNext}
                            className="flex-1"
                          >
                            {sandboxLoading ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            ) : (
                              <Play className="w-4 h-4 mr-2" />
                            )}
                            {sandboxLoading ? 'Выполняем...' : 'Выполнить шаг'}
                          </Button>
                          <Button
                            variant="outline"
                            onClick={resetStepByStepExecution}
                          >
                            <RotateCcw className="w-4 h-4 mr-2" />
                            Сброс
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex gap-4">
                        <Button
                          onClick={handleTestSandbox}
                          disabled={sandboxLoading || !sandboxPostData.trim()}
                          className="flex-1"
                        >
                          {sandboxLoading ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          ) : (
                            <FlaskRound className="w-4 h-4 mr-2" />
                          )}
                          {sandboxLoading ? 'Тестируем...' : 'Запустить тест'}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setSandboxPostData('')
                            setSandboxResult(null)
                          }}
                        >
                          Очистить
                        </Button>
                      </div>
                    )}

                    {sandboxResult && (
                      <div className="mt-6">
                        <h3 className="text-lg font-medium mb-4">Результаты тестирования</h3>

                        {/* Основная информация */}
                        <div className="bg-gray-50 rounded-lg p-4 space-y-3 mb-6">
                          <div className="flex items-center justify-between">
                            <span className="font-medium">Статус:</span>
                            <Badge variant={sandboxResult.success ? "default" : "secondary"}>
                              {sandboxResult.success ? "Успешно" : "Ошибка"}
                            </Badge>
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <span className="font-medium text-sm">Post ID:</span>
                              <code className="ml-2 bg-white px-2 py-1 rounded text-sm">
                                {sandboxResult.post_id}
                              </code>
                            </div>
                            <div>
                              <span className="font-medium text-sm">Токенов использовано:</span>
                              <span className="ml-2 text-sm">{sandboxResult.total_tokens || 0}</span>
                            </div>
                          </div>
                          <div>
                            <span className="font-medium text-sm">Время выполнения:</span>
                            <span className="ml-2 text-sm">{(sandboxResult.total_time || 0).toFixed(2)} сек</span>
                          </div>
                        </div>

                        {/* Этапы pipeline */}
                        <div className="mb-6">
                          <h4 className="text-md font-medium mb-3">Этапы pipeline</h4>
                          <div className="space-y-2">
                            {sandboxResult.steps?.map((step: any) => (
                              <div key={step.step} className="border rounded-lg p-3 bg-white">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="font-medium text-sm">{step.step}. {step.name}</span>
                                  <div className="flex items-center space-x-2">
                                    <Badge variant={step.success ? "default" : "secondary"} className="text-xs">
                                      {step.status}
                                    </Badge>
                                    <span className="text-xs text-gray-500">
                                      {step.tokens_used} токенов
                                    </span>
                                  </div>
                                </div>
                                <div className="text-xs text-gray-600">
                                  {step.description}
                                </div>
                                {step.processing_time && (
                                  <div className="text-xs text-gray-500 mt-1">
                                    Время: {(step.processing_time * 1000).toFixed(0)}мс
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Debug лог */}
                        {sandboxResult.debug_log && sandboxResult.debug_log.length > 0 && (
                          <div>
                            <div className="flex items-center justify-between mb-3">
                              <h4 className="text-md font-medium">
                                Debug лог ({getFilteredLogs().length} из {sandboxResult.debug_log.length} записей)
                              </h4>
                              <div className="flex gap-2">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={handleExportResults}
                                  className="text-xs"
                                  disabled={!sandboxResult}
                                >
                                  <Download className="w-3 h-3 mr-1" />
                                  Экспорт JSON
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => {
                                    setLogSearchTerm('')
                                    setLogFilterType('all')
                                    setLogFilterSuccess('all')
                                  }}
                                  className="text-xs"
                                >
                                  Сбросить фильтры
                                </Button>
                              </div>
                            </div>

                            {/* Панель фильтров */}
                            <div className="bg-gray-50 rounded-lg p-3 mb-4 space-y-3">
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                {/* Поиск */}
                                <div className="relative">
                                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                                  <Input
                                    placeholder="Поиск по логам..."
                                    value={logSearchTerm}
                                    onChange={(e) => setLogSearchTerm(e.target.value)}
                                    className="pl-9 text-sm"
                                  />
                                </div>

                                {/* Фильтр по типу */}
                                <Select value={logFilterType} onValueChange={setLogFilterType}>
                                  <SelectTrigger className="text-sm">
                                    <SelectValue placeholder="Тип шага" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="all">Все типы</SelectItem>
                                    <SelectItem value="info">Информация</SelectItem>
                                    <SelectItem value="llm_call">LLM запрос</SelectItem>
                                    <SelectItem value="llm_response">LLM ответ</SelectItem>
                                  </SelectContent>
                                </Select>

                                {/* Фильтр по статусу */}
                                <Select value={logFilterSuccess} onValueChange={setLogFilterSuccess}>
                                  <SelectTrigger className="text-sm">
                                    <SelectValue placeholder="Статус" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="all">Все статусы</SelectItem>
                                    <SelectItem value="success">Успешные</SelectItem>
                                    <SelectItem value="failed">Неуспешные</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>

                            {/* Список логов */}
                            <div className="border rounded-lg bg-white max-h-96 overflow-y-auto">
                              <div className="p-3 space-y-2">
                                {getFilteredLogs().length === 0 ? (
                                  <div className="text-center py-8 text-gray-500">
                                    <Filter className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                                    <p className="text-sm">Нет записей, соответствующих фильтрам</p>
                                  </div>
                                ) : (
                                  getFilteredLogs().map((log: any, index: number) => (
                                    <div key={index} className="border-l-2 border-blue-200 pl-3 py-2">
                                      <div className="flex items-center justify-between mb-1">
                                        <span className="font-medium text-sm">{log.step_name}</span>
                                        <div className="flex items-center space-x-2">
                                          <Badge variant="outline" className="text-xs">
                                            {log.step_type}
                                          </Badge>
                                          <span className="text-xs text-gray-500">
                                            {(log.timestamp || 0).toFixed(3)}s
                                          </span>
                                        </div>
                                      </div>
                                    <div className="text-xs bg-gray-50 p-2 rounded border">
                                      <JsonHighlighter data={log.data} />
                                    </div>
                                    </div>
                                  ))
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
