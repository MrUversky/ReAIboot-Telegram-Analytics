'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSupabase } from '@/components/SupabaseProvider'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
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
  X
} from 'lucide-react'
import { supabase } from '@/lib/supabase'

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

  useEffect(() => {
    if (!loading && (!user || !permissions?.canAdmin)) {
      router.push('/')
    }
  }, [user, permissions, loading, router])

  useEffect(() => {
    if (user && permissions?.canAdmin) {
      loadAdminData()
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

  const handleConfigureLLM = async () => {
    await loadLLMSettings()
    setShowLLMModal(true)
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
            <div className="flex justify-center gap-4">
              <Button variant="outline" onClick={handleConfigureLLM}>
                <Settings className="w-4 h-4 mr-2" />
                Настройки LLM
              </Button>
            </div>
            <div className="mt-4 text-xs text-gray-500">
              💡 Управление каналами теперь доступно в разделе "Парсинг"
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
