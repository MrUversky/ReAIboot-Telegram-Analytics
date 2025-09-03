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
  BarChart3
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
  const [prompts, setPrompts] = useState<any[]>([])
  const [showLLMModal, setShowLLMModal] = useState(false)
  const [llmTab, setLlmTab] = useState<'rubrics' | 'formats' | 'prompts'>('rubrics')

  // Viral Detection settings state
  const [systemSettings, setSystemSettings] = useState<any[]>([])
  const [channelBaselines, setChannelBaselines] = useState<any[]>([])
  const [viralPosts, setViralPosts] = useState<any[]>([])
  const [showViralModal, setShowViralModal] = useState(false)
  const [viralTab, setViralTab] = useState<'settings' | 'baselines' | 'posts'>('settings')

  // Telegram Auth state
  const [telegramStatus, setTelegramStatus] = useState<any>(null)
  const [showTelegramModal, setShowTelegramModal] = useState(false)
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
    content: '',
    model: 'gpt-4o-mini',
    temperature: 0.7,
    max_tokens: 2000,
    is_active: true
  })

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
        setPhoneCodeHash(result.phone_code_hash)
        setAuthStep('code')
        alert('Код отправлен! Проверьте SMS')
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
      const [rubricsResult, formatsResult, promptsResult] = await Promise.all([
        supabase.from('rubrics').select('*').order('name'),
        supabase.from('reel_formats').select('*').order('name'),
        supabase.from('llm_prompts').select('*').order('name')
      ])

      if (rubricsResult.error) throw rubricsResult.error
      if (formatsResult.error) throw formatsResult.error

      setRubrics(rubricsResult.data || [])
      setFormats(formatsResult.data || [])
      setPrompts(promptsResult.error ? [] : (promptsResult.data || []))
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
      id: rubric.id,
      name: rubric.name,
      description: rubric.description || '',
      category: rubric.category || '',
      is_active: rubric.is_active
    })
  }

  const editFormat = (format: any) => {
    setFormatForm({
      id: format.id,
      name: format.name,
      description: format.description || '',
      duration_seconds: format.duration_seconds || 60,
      structure: format.structure || {},
      is_active: format.is_active
    })
  }

  const savePrompt = async () => {
    try {
      const promptData = {
        ...promptForm,
        updated_at: new Date().toISOString()
      }

      if (promptForm.id) {
        const { error } = await supabase
          .from('llm_prompts')
          .update(promptData)
          .eq('id', promptForm.id)
        if (error) throw error
      } else {
        const newId = `prompt_${Date.now()}`
        const { error } = await supabase
          .from('llm_prompts')
          .insert([{
            ...promptData,
            id: newId,
            created_at: new Date().toISOString()
          }])
        if (error) throw error
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
      const { error } = await supabase
        .from('llm_prompts')
        .delete()
        .eq('id', promptId)

      if (error) throw error
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
      content: '',
      model: 'gpt-4o-mini',
      temperature: 0.7,
      max_tokens: 2000,
      is_active: true
    })
  }

  const editPrompt = (prompt: any) => {
    setPromptForm({
      id: prompt.id,
      name: prompt.name,
      description: prompt.description || '',
      prompt_type: prompt.prompt_type,
      content: prompt.content,
      model: prompt.model,
      temperature: prompt.temperature,
      max_tokens: prompt.max_tokens,
      is_active: prompt.is_active
    })
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
              <Button variant="outline" onClick={handleConfigureViral}>
                <Zap className="w-4 h-4 mr-2" />
                Viral Detection
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
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {systemSettings.map((setting: any) => (
                      <Card key={setting.key}>
                        <CardHeader>
                          <CardTitle className="text-lg">{setting.key}</CardTitle>
                          <p className="text-sm text-gray-600">{setting.description}</p>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-4">
                            {typeof setting.value === 'object' ? (
                              <div className="space-y-2">
                                {Object.entries(setting.value).map(([key, value]) => (
                                  <div key={key} className="flex justify-between items-center">
                                    <span className="text-sm font-medium">{key}:</span>
                                    <Input
                                      type="number"
                                      step="0.01"
                                      defaultValue={value as string}
                                      className="w-24"
                                      onBlur={(e) => {
                                        const newValue = { ...setting.value, [key]: parseFloat(e.target.value) }
                                        updateSystemSetting(setting.key, newValue)
                                      }}
                                    />
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <Input
                                type="number"
                                step="0.01"
                                defaultValue={setting.value}
                                onBlur={(e) => updateSystemSetting(setting.key, parseFloat(e.target.value))}
                              />
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Baselines Tab */}
              {viralTab === 'baselines' && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-medium">Базовые метрики каналов</h3>
                    <Button onClick={updateAllBaselines} variant="outline">
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Обновить все
                    </Button>
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
                                onClick={() => calculateChannelBaseline(baseline.channel.username)}
                              >
                                Пересчитать
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
                <Button variant="ghost" size="sm" onClick={() => setShowTelegramModal(false)}>
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
    </div>
  )
}
