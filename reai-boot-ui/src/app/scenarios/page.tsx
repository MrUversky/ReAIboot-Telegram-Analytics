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
  Share,
  X,
  ChevronUp,
  ChevronDown
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
  rubric_id?: string
  format_id?: string
  quality_score?: number
  engagement_prediction?: number
  full_scenario?: any
}

export default function ScenariosPage() {
  const router = useRouter()
  const { user, permissions, loading } = useSupabase()
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [loadingData, setLoadingData] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  // Scenario modal states
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null)
  const [showScenarioModal, setShowScenarioModal] = useState(false)
  const [showContentDetails, setShowContentDetails] = useState(false)

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
          rubric_id,
          format_id,
          quality_score,
          engagement_prediction,
          full_scenario,
          posts (
            channel_username,
            text_preview,
            full_text
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
        post_title: (scenario.posts && Array.isArray(scenario.posts) && scenario.posts[0]?.text_preview) ||
                   (scenario.posts && !Array.isArray(scenario.posts) && scenario.posts.text_preview) ||
                   (scenario.posts && !Array.isArray(scenario.posts) && scenario.posts.full_text) ||
                   'Без названия',
        channel_name: (scenario.posts && Array.isArray(scenario.posts) && scenario.posts[0]?.channel_username) ||
                     (scenario.posts && !Array.isArray(scenario.posts) && scenario.posts.channel_username) ||
                     'Неизвестный канал',
        duration: 60, // Default duration
        views: 0, // TODO: Add views tracking
        rubric_id: scenario.rubric_id,
        format_id: scenario.format_id,
        quality_score: scenario.quality_score,
        engagement_prediction: scenario.engagement_prediction,
        full_scenario: scenario.full_scenario
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

  const handleViewScenario = async (scenario: Scenario) => {
    try {
      // Загружаем полные данные поста для модального окна
      const { data: fullScenario, error } = await supabase
        .from('scenarios')
        .select(`
          *,
          posts (
            channel_username,
            text_preview,
            full_text
          )
        `)
        .eq('id', parseInt(scenario.id))
        .single()

      if (error) throw error

      // Создаем обновленный объект сценария с полными данными поста
      const enrichedScenario: Scenario = {
        ...scenario,
        post_title: fullScenario.posts?.full_text || fullScenario.posts?.text_preview || scenario.post_title,
        channel_name: fullScenario.posts?.channel_username || scenario.channel_name
      }

      setSelectedScenario(enrichedScenario)
      setShowScenarioModal(true)
    } catch (error) {
      console.error('Error loading full scenario:', error)
      // Если не удалось загрузить полные данные, используем базовые
      setSelectedScenario(scenario)
      setShowScenarioModal(true)
    }
  }

  const handleDownloadScenario = async (scenario: Scenario) => {
    try {
      // Получить полную информацию о сценарии из базы данных
      const { data: fullScenario, error } = await supabase
        .from('scenarios')
        .select(`
          *,
          posts (
            channel_username,
            text_preview,
            full_text
          )
        `)
        .eq('id', parseInt(scenario.id))
        .single()

      if (error) throw error

      // Создать JSON с полными данными сценария
      const scenarioData = {
        title: scenario.title,
        description: scenario.description,
        status: scenario.status,
        created_at: scenario.created_at,
        channel: scenario.channel_name,
        original_post: scenario.post_title,
        quality_score: scenario.quality_score,
        engagement_prediction: scenario.engagement_prediction,
        rubric: scenario.rubric_id,
        format: scenario.format_id,
        full_scenario_data: fullScenario?.full_scenario,
        duration_seconds: scenario.duration
      }

      // Создать и скачать файл
      const dataStr = JSON.stringify(scenarioData, null, 2)
      const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)

      const exportFileDefaultName = `scenario_${scenario.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`

      const linkElement = document.createElement('a')
      linkElement.setAttribute('href', dataUri)
      linkElement.setAttribute('download', exportFileDefaultName)
      linkElement.click()

      alert('Сценарий успешно скачан!')
    } catch (error) {
      console.error('Ошибка при скачивании сценария:', error)
      alert('Ошибка при скачивании сценария')
    }
  }

  const handleShareScenario = async (scenario: Scenario) => {
    try {
      const shareUrl = `${window.location.origin}/scenarios?id=${scenario.id}`
      const shareText = `Посмотри этот сценарий: "${scenario.title}"\n\nСоздан из поста: ${scenario.post_title.substring(0, 100)}${scenario.post_title.length > 100 ? '...' : ''}`

      if (navigator.share) {
        // Web Share API для мобильных устройств
        await navigator.share({
          title: scenario.title,
          text: shareText,
          url: shareUrl
        })
      } else {
        // Fallback - копирование в буфер обмена
        await navigator.clipboard.writeText(`${shareText}\n\n${shareUrl}`)
        alert('Ссылка на сценарий скопирована в буфер обмена!')
      }
    } catch (error) {
      console.error('Ошибка при поделиться сценарием:', error)
      alert('Ошибка при поделиться сценарием')
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
          <h1 className="text-2xl font-bold text-gray-900">Сценарии</h1>
          <p className="text-gray-500 text-sm mt-1">
            Сгенерированные сценарии для видео контента
          </p>
        </div>
        <Button onClick={loadScenarios} disabled={loadingData} size="sm">
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
            <div className="space-y-3">
              {filteredScenarios.map((scenario) => (
                <div key={scenario.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
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
                        <span>📝 {scenario.title}</span>
                        <span>⏱️ {scenario.duration > 0 ? `${Math.floor(scenario.duration / 60)}:${String(scenario.duration % 60).padStart(2, '0')}` : '1:00'}</span>
                        <span>📅 {new Date(scenario.created_at).toLocaleDateString('ru-RU')}</span>
                      </div>
                    </div>

                    <div className="flex gap-2 ml-4">
                      <Button variant="outline" size="sm" onClick={() => handleViewScenario(scenario)}>
                        <Eye className="w-4 h-4 mr-2" />
                        Просмотр
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => handleDownloadScenario(scenario)}>
                        <Download className="w-4 h-4 mr-2" />
                        Скачать
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => handleShareScenario(scenario)}>
                        <Share className="w-4 h-4 mr-2" />
                        Поделиться
                      </Button>
                    </div>

                    {/* Additional metadata - positioned below buttons */}
                    {((scenario.quality_score && scenario.quality_score > 0) ||
                      (scenario.engagement_prediction && scenario.engagement_prediction > 0) ||
                      scenario.rubric_id || scenario.format_id) && (
                      <div className="flex flex-wrap gap-3 mt-3 pt-3 border-t border-gray-100">
                        {scenario.quality_score ? (
                          <div className="flex items-center gap-1 text-sm">
                            <span className="text-yellow-600">⭐</span>
                            <span>Качество: {(scenario.quality_score * 100).toFixed(0)}%</span>
                          </div>
                        ) : null}
                        {scenario.engagement_prediction ? (
                          <div className="flex items-center gap-1 text-sm">
                            <span className="text-green-600">📈</span>
                            <span>Вовлеченность: {(scenario.engagement_prediction * 100).toFixed(0)}%</span>
                          </div>
                        ) : null}
                        {scenario.rubric_id ? (
                          <div className="flex items-center gap-1 text-sm">
                            <span className="text-blue-600">🎯</span>
                            <span>Рубрика: {scenario.rubric_id}</span>
                          </div>
                        ) : null}
                        {scenario.format_id ? (
                          <div className="flex items-center gap-1 text-sm">
                            <span className="text-purple-600">🎬</span>
                            <span>Формат: {scenario.format_id}</span>
                          </div>
                        ) : null}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Scenario Details Modal */}
      {showScenarioModal && selectedScenario && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-6xl w-full max-h-[95vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-8">
                <div>
                  <h2 className="text-3xl font-bold text-gray-900 flex items-center mb-2">
                    <Video className="w-7 h-7 mr-3 text-blue-500" />
                    {selectedScenario.title}
                  </h2>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span>📺 {selectedScenario.channel_name}</span>
                    <span>📅 {new Date(selectedScenario.created_at).toLocaleDateString('ru-RU')}</span>
                    <span>⏱️ {selectedScenario.duration > 0 ? `${Math.floor(selectedScenario.duration / 60)}:${String(selectedScenario.duration % 60).padStart(2, '0')}` : '1:00'}</span>
                  </div>
                </div>
                <Button variant="outline" onClick={() => setShowScenarioModal(false)}>
                  <X className="w-5 h-5" />
                </Button>
              </div>

              <div className="space-y-6">
                {/* Basic Info */}
                <Card>
                  <CardHeader>
                    <CardTitle>Основная информация</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap items-center gap-4 text-sm">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">Статус:</span>
                        {getStatusBadge(selectedScenario.status)}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">⏱️</span>
                        <span>{selectedScenario.duration > 0 ? `${Math.floor(selectedScenario.duration / 60)}:${String(selectedScenario.duration % 60).padStart(2, '0')}` : '1:00'}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">📺</span>
                        <span>{selectedScenario.channel_name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">📅</span>
                        <span>{new Date(selectedScenario.created_at).toLocaleDateString('ru-RU')}</span>
                      </div>
                    </div>
                    {selectedScenario.description && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <p className="text-sm text-gray-700">{selectedScenario.description}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Quality Metrics */}
                {((selectedScenario.quality_score && selectedScenario.quality_score > 0) ||
                  (selectedScenario.engagement_prediction && selectedScenario.engagement_prediction > 0)) ? (
                  <Card>
                    <CardHeader>
                      <CardTitle>Метрики качества</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {selectedScenario.quality_score ? (
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
                              <span className="text-xl">⭐</span>
                            </div>
                            <div>
                              <div className="text-lg font-semibold">
                                {(selectedScenario.quality_score * 100).toFixed(1)}%
                              </div>
                              <div className="text-sm text-gray-600">Качество сценария</div>
                            </div>
                          </div>
                        ) : null}

                        {selectedScenario.engagement_prediction ? (
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                              <span className="text-xl">📈</span>
                            </div>
                            <div>
                              <div className="text-lg font-semibold">
                                {(selectedScenario.engagement_prediction * 100).toFixed(1)}%
                              </div>
                              <div className="text-sm text-gray-600">Прогноз вовлеченности</div>
                            </div>
                          </div>
                        ) : null}
                      </div>
                    </CardContent>
                  </Card>
                ) : null}

                {/* Content Details - Collapsible */}
                <Card>
                  <CardHeader>
                    <CardTitle
                      className="cursor-pointer flex items-center justify-between hover:text-blue-600 transition-colors"
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        setShowContentDetails(!showContentDetails)
                      }}
                    >
                      <span>Детали контента</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="p-0 h-auto"
                        onClick={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                          setShowContentDetails(!showContentDetails)
                        }}
                      >
                        {showContentDetails ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  {showContentDetails && (
                    <CardContent>
                      <div className="space-y-4">
                        {selectedScenario.rubric_id ? (
                          <div>
                            <label className="text-sm font-medium text-gray-600">Рубрика</label>
                            <div className="mt-1 flex items-center gap-2">
                              <span className="text-blue-600">🎯</span>
                              <span>{selectedScenario.rubric_id}</span>
                            </div>
                          </div>
                        ) : null}

                        {selectedScenario.format_id ? (
                          <div>
                            <label className="text-sm font-medium text-gray-600">Формат</label>
                            <div className="mt-1 flex items-center gap-2">
                              <span className="text-purple-600">🎬</span>
                              <span>{selectedScenario.format_id}</span>
                            </div>
                          </div>
                        ) : null}

                        <div>
                          <label className="text-sm font-medium text-gray-600 mb-2 block">Исходный пост</label>
                          <div className="p-4 bg-gray-50 rounded-lg border-l-4 border-gray-400">
                            <div className="flex items-start gap-3">
                              <span className="text-gray-400 mt-1">💬</span>
                              <div className="flex-1">
                                <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                                  {selectedScenario.post_title}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  )}
                </Card>

                {/* Full Scenario Content */}
                {selectedScenario.full_scenario && (
                  <Card className="border-green-200">
                    <CardHeader className="bg-green-50 border-b border-green-200">
                      <CardTitle className="flex items-center text-green-800">
                        <Video className="w-6 h-6 mr-3 text-green-600" />
                        Полный сценарий видео
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="pt-6">
                      <div className="space-y-6">
                        {/* Hook Section */}
                        {selectedScenario.full_scenario.hook && (
                          <div className="border-l-4 border-red-400 pl-4">
                            <h4 className="text-lg font-semibold text-red-800 mb-3 flex items-center">
                              <span className="text-2xl mr-2">🎣</span>
                              ХУК (привлечение внимания)
                            </h4>
                            <div className="bg-red-50 rounded-lg p-4 space-y-3">
                              {selectedScenario.full_scenario.hook.text && (
                                <div>
                                  <h5 className="font-medium text-red-900 mb-1">Текст:</h5>
                                  <p className="text-sm text-gray-800">{selectedScenario.full_scenario.hook.text}</p>
                                </div>
                              )}
                              {selectedScenario.full_scenario.hook.voiceover && (
                                <div>
                                  <h5 className="font-medium text-red-900 mb-1">Голос за кадром:</h5>
                                  <p className="text-sm text-gray-700 italic">{selectedScenario.full_scenario.hook.voiceover}</p>
                                </div>
                              )}
                              {selectedScenario.full_scenario.hook.visual && (
                                <div>
                                  <h5 className="font-medium text-red-900 mb-1">Визуал:</h5>
                                  <p className="text-sm text-gray-700">{selectedScenario.full_scenario.hook.visual}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Main Content Steps */}
                        {selectedScenario.full_scenario.steps && selectedScenario.full_scenario.steps.length > 0 && (
                          <div className="border-l-4 border-blue-400 pl-4">
                            <h4 className="text-lg font-semibold text-blue-800 mb-3 flex items-center">
                              <span className="text-2xl mr-2">📝</span>
                              ОСНОВНОЙ КОНТЕНТ
                            </h4>
                            <div className="space-y-4">
                              {selectedScenario.full_scenario.steps.map((step: any, index: number) => (
                                <div key={index} className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                                  <div className="flex items-center mb-2">
                                    <span className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3">
                                      {index + 1}
                                    </span>
                                    <h5 className="font-semibold text-blue-900">{step.title}</h5>
                                    {step.duration && (
                                      <span className="ml-auto text-sm text-gray-600">⏱️ {step.duration} сек</span>
                                    )}
                                  </div>
                                  {step.description && (
                                    <div className="mb-2">
                                      <p className="text-sm text-gray-800">{step.description}</p>
                                    </div>
                                  )}
                                  {step.voiceover && (
                                    <div className="mb-2">
                                      <h6 className="font-medium text-blue-800 text-sm mb-1">Голос за кадром:</h6>
                                      <p className="text-sm text-gray-700 italic">{step.voiceover}</p>
                                    </div>
                                  )}
                                  {step.visual && (
                                    <div>
                                      <h6 className="font-medium text-blue-800 text-sm mb-1">Визуал:</h6>
                                      <p className="text-sm text-gray-700">{step.visual}</p>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Insight/Conclusion */}
                        {selectedScenario.full_scenario.insight && (
                          <div className="border-l-4 border-purple-400 pl-4">
                            <h4 className="text-lg font-semibold text-purple-800 mb-3 flex items-center">
                              <span className="text-2xl mr-2">💡</span>
                              ИНСАЙТ/ВЫВОД
                            </h4>
                            <div className="bg-purple-50 rounded-lg p-4 space-y-3">
                              {selectedScenario.full_scenario.insight.text && (
                                <div>
                                  <h5 className="font-medium text-purple-900 mb-1">Текст:</h5>
                                  <p className="text-sm text-gray-800">{selectedScenario.full_scenario.insight.text}</p>
                                </div>
                              )}
                              {selectedScenario.full_scenario.insight.voiceover && (
                                <div>
                                  <h5 className="font-medium text-purple-900 mb-1">Голос за кадром:</h5>
                                  <p className="text-sm text-gray-700 italic">{selectedScenario.full_scenario.insight.voiceover}</p>
                                </div>
                              )}
                              {selectedScenario.full_scenario.insight.visual && (
                                <div>
                                  <h5 className="font-medium text-purple-900 mb-1">Визуал:</h5>
                                  <p className="text-sm text-gray-700">{selectedScenario.full_scenario.insight.visual}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Call to Action */}
                        {selectedScenario.full_scenario.cta && (
                          <div className="border-l-4 border-green-400 pl-4">
                            <h4 className="text-lg font-semibold text-green-800 mb-3 flex items-center">
                              <span className="text-2xl mr-2">🎯</span>
                              ПРИЗЫВ К ДЕЙСТВИЮ
                            </h4>
                            <div className="bg-green-50 rounded-lg p-4 space-y-3">
                              {selectedScenario.full_scenario.cta.text && (
                                <div>
                                  <h5 className="font-medium text-green-900 mb-1">Текст:</h5>
                                  <p className="text-sm text-gray-800">{selectedScenario.full_scenario.cta.text}</p>
                                </div>
                              )}
                              {selectedScenario.full_scenario.cta.voiceover && (
                                <div>
                                  <h5 className="font-medium text-green-900 mb-1">Голос за кадром:</h5>
                                  <p className="text-sm text-gray-700 italic">{selectedScenario.full_scenario.cta.voiceover}</p>
                                </div>
                              )}
                              {selectedScenario.full_scenario.cta.visual && (
                                <div>
                                  <h5 className="font-medium text-green-900 mb-1">Визуал:</h5>
                                  <p className="text-sm text-gray-700">{selectedScenario.full_scenario.cta.visual}</p>
                                </div>
                              )}
                              {selectedScenario.full_scenario.cta.duration && (
                                <div>
                                  <h5 className="font-medium text-green-900 mb-1">Длительность:</h5>
                                  <p className="text-sm text-gray-700">{selectedScenario.full_scenario.cta.duration} сек</p>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Additional Info */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                          {selectedScenario.full_scenario.music_suggestion && (
                            <div className="p-3 bg-orange-50 rounded-lg border border-orange-200">
                              <h5 className="font-medium text-orange-900 mb-1">🎵 Музыка</h5>
                              <p className="text-sm text-orange-700">{selectedScenario.full_scenario.music_suggestion}</p>
                            </div>
                          )}
                          {selectedScenario.full_scenario.hashtags && (
                            <div className="p-3 bg-pink-50 rounded-lg border border-pink-200">
                              <h5 className="font-medium text-pink-900 mb-1"># Хэштеги</h5>
                              <p className="text-sm text-pink-700">{selectedScenario.full_scenario.hashtags}</p>
                            </div>
                          )}
                          {selectedScenario.full_scenario.generator_model && (
                            <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                              <h5 className="font-medium text-purple-900 mb-1">🤖 Модель генератора</h5>
                              <p className="text-sm text-purple-700">{selectedScenario.full_scenario.generator_model}</p>
                            </div>
                          )}
                          {selectedScenario.full_scenario.selection_score && (
                            <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                              <h5 className="font-medium text-green-900 mb-1">⭐ Рейтинг качества</h5>
                              <p className="text-sm text-green-700">{selectedScenario.full_scenario.selection_score}/10</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Actions */}
                <div className="flex justify-end gap-3">
                  <Button variant="outline" onClick={() => setShowScenarioModal(false)}>
                    Закрыть
                  </Button>
                  <Button onClick={() => handleDownloadScenario(selectedScenario)}>
                    <Download className="w-4 h-4 mr-2" />
                    Скачать сценарий
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
