'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSupabase } from '@/components/SupabaseProvider'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Video,
  Play,
  Pause,
  RotateCcw,
  Filter,
  Search,
  Eye,
  Download,
  Share
} from 'lucide-react'
import { supabase } from '@/lib/supabase'

interface Scenario {
  id: string
  title: string
  description: string
  status: 'draft' | 'processing' | 'completed' | 'failed'
  created_at: string
  post_title: string
  channel_name: string
  duration: number
  views: number
}

export default function ScenariosPage() {
  const router = useRouter()
  const { user, permissions, loading } = useSupabase()
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [loadingData, setLoadingData] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  useEffect(() => {
    if (!loading && (!user || !permissions?.hasAccess)) {
      router.push('/')
    }
  }, [user, permissions, loading, router])

  useEffect(() => {
    if (user && permissions?.hasAccess) {
      loadScenarios()
    }
  }, [user, permissions])

  const loadScenarios = async () => {
    try {
      setLoadingData(true)

      // Load real scenarios from Supabase
      const { data: scenariosData, error } = await supabase
        .from('scenarios')
        .select(`
          id,
          title,
          description,
          status,
          created_at,
          created_by,
          posts (
            channel_username,
            text_preview
          )
        `)
        .order('created_at', { ascending: false })

      if (error) throw error

      // Convert to our interface format
      const formattedScenarios: Scenario[] = (scenariosData || []).map(scenario => ({
        id: scenario.id.toString(),
        title: scenario.title,
        description: scenario.description || '',
        status: scenario.status as 'draft' | 'processing' | 'completed' | 'failed',
        created_at: scenario.created_at,
        post_title: Array.isArray(scenario.posts) && scenario.posts[0]?.text_preview || 'Без названия',
        channel_name: Array.isArray(scenario.posts) && scenario.posts[0]?.channel_username || 'Неизвестный канал',
        duration: 60, // Default duration
        views: 0 // TODO: Add views tracking
      }))

      setScenarios(formattedScenarios)
    } catch (error) {
      console.error('Error loading scenarios:', error)
    } finally {
      setLoadingData(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-100 text-green-800">Готово</Badge>
      case 'processing':
        return <Badge className="bg-yellow-100 text-yellow-800">Обрабатывается</Badge>
      case 'draft':
        return <Badge className="bg-gray-100 text-gray-800">Черновик</Badge>
      case 'failed':
        return <Badge className="bg-red-100 text-red-800">Ошибка</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <Video className="w-4 h-4" />
      case 'processing':
        return <RotateCcw className="w-4 h-4 animate-spin" />
      case 'draft':
        return <Pause className="w-4 h-4" />
      case 'failed':
        return <Pause className="w-4 h-4" />
      default:
        return <Video className="w-4 h-4" />
    }
  }

  const filteredScenarios = scenarios.filter(scenario => {
    const matchesSearch = scenario.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         scenario.post_title.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || scenario.status === statusFilter
    return matchesSearch && matchesStatus
  })

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
          <h1 className="text-3xl font-bold text-gray-900">Сценарии</h1>
          <p className="text-gray-600 mt-2">
            Сгенерированные сценарии для видео контента
          </p>
        </div>
        <Button onClick={loadScenarios} disabled={loadingData}>
          {loadingData ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          ) : (
            <RotateCcw className="w-4 h-4 mr-2" />
          )}
          Обновить
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Поиск по названию или посту..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant={statusFilter === 'all' ? 'default' : 'outline'}
                onClick={() => setStatusFilter('all')}
                size="sm"
              >
                <Filter className="w-4 h-4 mr-2" />
                Все
              </Button>
              <Button
                variant={statusFilter === 'completed' ? 'default' : 'outline'}
                onClick={() => setStatusFilter('completed')}
                size="sm"
              >
                Готово
              </Button>
              <Button
                variant={statusFilter === 'processing' ? 'default' : 'outline'}
                onClick={() => setStatusFilter('processing')}
                size="sm"
              >
                Обрабатывается
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <Video className="h-8 w-8 text-blue-600 mr-4" />
              <div>
                <p className="text-2xl font-bold">{scenarios.length}</p>
                <p className="text-sm text-gray-600">Всего сценариев</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center mr-4">
                <Video className="h-4 w-4 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {scenarios.filter(s => s.status === 'completed').length}
                </p>
                <p className="text-sm text-gray-600">Готово</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-yellow-100 rounded-full flex items-center justify-center mr-4">
                <RotateCcw className="h-4 w-4 text-yellow-600 animate-spin" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {scenarios.filter(s => s.status === 'processing').length}
                </p>
                <p className="text-sm text-gray-600">Обрабатывается</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <Eye className="h-8 w-8 text-purple-600 mr-4" />
              <div>
                <p className="text-2xl font-bold">
                  {scenarios.reduce((sum, s) => sum + s.views, 0).toLocaleString()}
                </p>
                <p className="text-sm text-gray-600">Общие просмотры</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Scenarios List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Video className="w-5 h-5 mr-2" />
            Сценарии
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loadingData ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-500">Загрузка сценариев...</p>
            </div>
          ) : filteredScenarios.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Video className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>Сценарии не найдены</p>
              <p className="text-sm mt-2">Попробуйте изменить фильтры или создать новый сценарий</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredScenarios.map((scenario) => (
                <div key={scenario.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        {getStatusIcon(scenario.status)}
                        <h3 className="text-lg font-semibold text-gray-900">
                          {scenario.title}
                        </h3>
                        {getStatusBadge(scenario.status)}
                      </div>

                      <p className="text-gray-600 mb-3">{scenario.description}</p>

                      <div className="flex flex-wrap gap-4 text-sm text-gray-500 mb-4">
                        <span>📺 {scenario.channel_name}</span>
                        <span>📝 {scenario.post_title}</span>
                        <span>⏱️ {Math.floor(scenario.duration / 60)}:{(scenario.duration % 60).toString().padStart(2, '0')}</span>
                        <span>👁️ {scenario.views.toLocaleString()}</span>
                        <span>📅 {new Date(scenario.created_at).toLocaleDateString('ru-RU')}</span>
                      </div>
                    </div>

                    <div className="flex gap-2 ml-4">
                      <Button variant="outline" size="sm">
                        <Eye className="w-4 h-4 mr-2" />
                        Просмотр
                      </Button>
                      <Button variant="outline" size="sm">
                        <Download className="w-4 h-4 mr-2" />
                        Скачать
                      </Button>
                      <Button variant="outline" size="sm">
                        <Share className="w-4 h-4 mr-2" />
                        Поделиться
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
