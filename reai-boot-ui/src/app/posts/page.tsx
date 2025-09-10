'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useSupabase } from '@/components/SupabaseProvider'
import { PostCard } from '@/components/PostCard'
import { PostAnalysisModal } from '@/components/PostAnalysisModal'
import toast from 'react-hot-toast'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import {
  Search,
  Filter,
  SortAsc,
  SortDesc,
  RefreshCw,
  FileText,
  TrendingUp,
  Eye,
  Heart,
  MessageCircle,
  Share,
  Zap
} from 'lucide-react'
import { apiClient, Post } from '@/lib/api'

export default function PostsPage() {
  const router = useRouter()
  const { user, loading } = useSupabase()
  const [posts, setPosts] = useState<Post[]>([])
  const [loadingPosts, setLoadingPosts] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [currentOffset, setCurrentOffset] = useState(0)
  const currentOffsetRef = useRef(0)
  const [totalPosts, setTotalPosts] = useState(0)
  const [globalStats, setGlobalStats] = useState<{
    total_views: number
    total_reactions: number
    total_forwards: number
  } | null>(null)
  const [loadingStats, setLoadingStats] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState<'date' | 'score' | 'views' | 'viral_score' | 'engagement_rate' | 'forwards' | 'reactions'>('viral_score')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [filterChannel, setFilterChannel] = useState<string>('all')
  const [channels, setChannels] = useState<string[]>([])
  const [showOnlyViral, setShowOnlyViral] = useState(false)
  const [minViralScore, setMinViralScore] = useState(1.0)
  const [dateRange, setDateRange] = useState<'7d' | '30d' | 'all'>('7d')
  const [minViews, setMinViews] = useState<number>(0)
  const [minEngagement, setMinEngagement] = useState<number>(0)
  const [showAnalysisModal, setShowAnalysisModal] = useState(false)
  const [analyzingPost, setAnalyzingPost] = useState<Post | null>(null)
  const [analyzingPosts, setAnalyzingPosts] = useState<Set<string>>(new Set())

  // Ref для IntersectionObserver
  const loadMoreRef = useRef<HTMLDivElement>(null)

  // Функция для получения фильтров для API
  const getApiFilters = useCallback(() => {
    const filters: any = {}

    // Фильтр по каналу
    if (filterChannel !== 'all') {
      filters.channel_username = filterChannel
    }

    // Фильтр по дате
    if (dateRange !== 'all') {
      const endDate = new Date()
      let startDate: Date | null = null

      if (dateRange === '7d') {
        startDate = new Date()
        startDate.setDate(startDate.getDate() - 7)
      } else if (dateRange === '30d') {
        startDate = new Date()
        startDate.setDate(startDate.getDate() - 30)
      }

      if (startDate) {
        filters.date_from = startDate.toISOString()
        filters.date_to = endDate.toISOString()
      }
    }

    // Дополнительные фильтры
    if (minViews > 0) {
      filters.min_views = minViews
    }
    if (minEngagement > 0) {
      filters.min_engagement = minEngagement
    }
    if (searchTerm.trim()) {
      filters.search_term = searchTerm.trim()
    }

    // Фильтр виральных постов
    if (showOnlyViral) {
      filters.only_viral = true
      filters.min_viral_score = minViralScore
    }

    return filters
  }, [filterChannel, dateRange, minViews, minEngagement, searchTerm, showOnlyViral, minViralScore])

  // Функция для загрузки общей статистики
  const loadGlobalStats = useCallback(async () => {
    try {
      setLoadingStats(true)
      const filters = getApiFilters()
      const stats = await apiClient.getPostsStats(filters)
      setGlobalStats(stats)
    } catch (error) {
      console.error('Error loading global stats:', error)
      // В случае ошибки не показываем статистику
      setGlobalStats(null)
    } finally {
      setLoadingStats(false)
    }
  }, [getApiFilters])

  const loadPosts = useCallback(async (reset: boolean = true) => {
    try {

      if (reset) {
        setLoadingPosts(true)
        setCurrentOffset(0)
        currentOffsetRef.current = 0
        setHasMore(true)
      } else {
        setLoadingMore(true)
      }

      // Используем актуальное значение из ref
      const offset = reset ? 0 : currentOffsetRef.current

      const limit = 50 // Загружаем по 50 постов за раз
      const filters = getApiFilters()

      const response = await apiClient.getPosts(limit, offset, filters)

      if (reset) {
        // При сбросе - фильтруем дубликаты в самом ответе API
        const uniquePosts = response.posts.filter((post, index, self) =>
          index === self.findIndex(p => p.id === post.id)
        )
        setPosts(uniquePosts)
        setTotalPosts(response.total || 0)
        // Обновляем offset после первой загрузки
        const newOffset = uniquePosts.length
        setCurrentOffset(newOffset)
        currentOffsetRef.current = newOffset
      } else {
        // При подгрузке - сначала получаем текущие посты и фильтруем дубликаты
        setPosts(prevPosts => {
          const existingIds = new Set(prevPosts.map(p => p.id))
          // Также фильтруем дубликаты в самом ответе API
          const uniqueNewPosts = response.posts
            .filter((post, index, self) => index === self.findIndex(p => p.id === post.id))
            .filter(p => !existingIds.has(p.id))

          // Обновляем offset после успешной загрузки
          const newOffset = prevPosts.length + uniqueNewPosts.length
          setCurrentOffset(newOffset)
          currentOffsetRef.current = newOffset
          return [...prevPosts, ...uniqueNewPosts]
        })
      }

      // hasMore теперь правильно определяется на бэкенде с учетом фильтров
      setHasMore(response.hasMore)

      // Extract unique channels (только при первой загрузке)
      if (reset) {
        const uniqueChannels = [...new Set(response.posts.map((post: Post) => post.channel_username))]
        setChannels(uniqueChannels)
      }
    } catch (error) {
      console.error('Error loading posts:', error)

      // Показываем ошибку вместо тестовых данных
      toast.error('Ошибка загрузки постов. Попробуйте обновить страницу.')
      if (reset) {
        setPosts([])
        setTotalPosts(0)
        setHasMore(false)
      }
    } finally {
      setLoadingPosts(false)
      setLoadingMore(false)
    }
  }, [getApiFilters])

  useEffect(() => {
    if (!loading && !user) {
      router.push('/auth')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      loadPosts(true)
      loadGlobalStats()
    }
  }, [user, loadPosts])

  // Reload posts and stats when filters change (debounced)
  useEffect(() => {
    if (user) {
      const timeoutId = setTimeout(() => {
        loadPosts(true)
        loadGlobalStats()
      }, 300) // Debounce на 300ms

      return () => clearTimeout(timeoutId)
    }
  }, [user, dateRange, minViews, minEngagement, filterChannel])

  // IntersectionObserver для infinite scroll
  useEffect(() => {
    let isLoading = false // Флаг для предотвращения множественных вызовов

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]

        if (entries[0].isIntersecting && hasMore && !loadingMore && !loadingPosts && !isLoading) {
          isLoading = true

          // Теперь используем актуальное значение из ref
          loadPosts(false).finally(() => {
            isLoading = false
          })
        }
      },
      { threshold: 0.1, rootMargin: '200px' } // Более агрессивные настройки для ранней загрузки
    )

    const currentRef = loadMoreRef.current

    if (currentRef) {
      observer.observe(currentRef)
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef)
      }
    }
  }, [hasMore, loadingMore, loadingPosts])

  const updateSinglePost = async (postId: string) => {
    try {
      // Получаем обновленные данные только для этого поста
      const updatedPost = await apiClient.getPost(postId)

      // Обновляем пост в состоянии
      setPosts(prevPosts =>
        prevPosts.map(post =>
          post.id === postId ? updatedPost : post
        )
      )
    } catch (error) {
      console.error('Error updating single post:', error)
      // В случае ошибки перезагружаем все посты
      loadPosts(true)
    }
  }


  // Функция для загрузки дополнительных постов
  const loadMorePosts = useCallback(() => {
    if (!loadingMore && hasMore && !loadingPosts) {
      loadPosts(false)
    }
  }, [loadingMore, hasMore, loadingPosts, loadPosts])

  const handleQuickAnalyzePost = async (post: Post) => {
    // Добавляем пост в состояние загрузки
    setAnalyzingPosts(prev => new Set(prev).add(post.id))

    try {
      // Быстрый анализ: только фильтрация (1-10) без генерации сценариев
      const result = await apiClient.quickAnalyzePost({
        message_id: post.message_id,
        channel_username: post.channel_username,
        channel_title: post.channel_title,
        text: post.full_text,
        views: post.views,
        reactions: post.reactions,
        replies: post.replies,
        forwards: post.forwards
      })

      // Ищем оценку в stages
      const filterStage = result.stages?.find((stage: any) => stage.stage === 'filter')
      const score = filterStage?.data?.score || filterStage?.data?.rating

      if (filterStage?.success && score) {
        toast.success(`Оценка получена: ${score}/10 ⭐`, {
          duration: 3000,
        })
      } else {
        toast.error(`Ошибка анализа: ${filterStage?.error || 'Не удалось получить оценку'}`, {
          duration: 4000,
        })
      }

      // Обновляем только этот пост вместо всех постов
      await updateSinglePost(post.id)
    } catch (error) {
      console.error('Error in quick analysis:', error)
      toast.error('Ошибка при быстром анализе', {
        duration: 4000,
      })
    } finally {
      // Убираем пост из состояния загрузки
      setAnalyzingPosts(prev => {
        const newSet = new Set(prev)
        newSet.delete(post.id)
        return newSet
      })
    }
  }

  const handleAnalyzePost = async (post: Post) => {
    // Полный анализ: открываем модальное окно для 4-этапного анализа
    setAnalyzingPost(post)
    setShowAnalysisModal(true)
  }

  const handleAnalysisComplete = (result: any) => {
    // Обновляем список постов для отображения результатов анализа
    loadPosts(true)
  }

  const filteredAndSortedPosts = posts
    .sort((a, b) => {
      let aValue: number, bValue: number

      switch (sortBy) {
        case 'score':
          aValue = a.score || 0
          bValue = b.score || 0
          break
        case 'views':
          aValue = a.views
          bValue = b.views
          break
        case 'viral_score':
          aValue = a.viral_score || 0
          bValue = b.viral_score || 0
          break
        case 'engagement_rate':
          aValue = (a.engagement_rate || 0) * 100
          bValue = (b.engagement_rate || 0) * 100
          break
        case 'forwards':
          aValue = a.forwards
          bValue = b.forwards
          break
        case 'reactions':
          aValue = a.reactions
          bValue = b.reactions
          break
        case 'date':
        default:
          aValue = new Date(a.date).getTime()
          bValue = new Date(b.date).getTime()
          break
      }

      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue
    })

  const getTopPosts = () => {
    return posts
      .filter(post => post.score && post.score > 0)
      .sort((a, b) => (b.score || 0) - (a.score || 0))
      .slice(0, 10)
  }

  if (loading || !user) {
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
          <h1 className="text-3xl font-bold text-gray-900">Анализ постов</h1>
          <p className="text-gray-600 mt-2">
            Просмотр и анализ постов из Telegram каналов
          </p>
        </div>
        <Button onClick={() => loadPosts(true)} disabled={loadingPosts}>
          {loadingPosts ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          ) : (
            <RefreshCw className="w-4 h-4 mr-2" />
          )}
          Обновить
        </Button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <FileText className="w-8 h-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Всего постов</p>
                <p className="text-2xl font-bold text-gray-900">{totalPosts?.toLocaleString() || '0'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <TrendingUp className="w-8 h-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Средний score</p>
                <p className="text-2xl font-bold text-gray-900">
                  {posts.length > 0
                    ? (posts.reduce((sum, post) => sum + (post.score || 0), 0) / posts.length).toFixed(2)
                    : '0.00'
                  }
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <Eye className="w-8 h-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Общие просмотры</p>
                <div className="text-2xl font-bold text-gray-900">
                  {loadingStats ? (
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
                  ) : globalStats ? (
                    globalStats.total_views.toLocaleString()
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <Heart className="w-8 h-8 text-red-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Общие реакции</p>
                <div className="text-2xl font-bold text-gray-900">
                  {loadingStats ? (
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-red-600"></div>
                  ) : globalStats ? (
                    globalStats.total_reactions.toLocaleString()
                  ) : (
                    <span className="text-gray-400">—</span>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>



      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Filter className="w-5 h-5 mr-2" />
            Фильтры и поиск
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Поиск по тексту или каналу..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            <Select value={dateRange} onValueChange={(value: any) => setDateRange(value)}>
              <SelectTrigger>
                <SelectValue placeholder="Период" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7d">Последние 7 дней</SelectItem>
                <SelectItem value="30d">Последние 30 дней</SelectItem>
                <SelectItem value="all">Все время</SelectItem>
              </SelectContent>
            </Select>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="viral-only"
                checked={showOnlyViral}
                onCheckedChange={setShowOnlyViral}
              />
              <div className="flex items-center gap-1">
                <Zap className="w-4 h-4 text-purple-500" />
                <label htmlFor="viral-only" className="text-sm font-medium cursor-pointer">
                  Только виральные
                </label>
              </div>
            </div>

            <Select value={filterChannel} onValueChange={setFilterChannel}>
              <SelectTrigger>
                <SelectValue placeholder="Все каналы" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все каналы</SelectItem>
                {channels.map(channel => (
                  <SelectItem key={channel} value={channel}>
                    @{channel}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="viral_score">По виральности</SelectItem>
                <SelectItem value="score">По рейтингу</SelectItem>
                <SelectItem value="views">По просмотрам</SelectItem>
                <SelectItem value="engagement_rate">По вовлеченности</SelectItem>
                <SelectItem value="forwards">По репостам</SelectItem>
                <SelectItem value="reactions">По реакциям</SelectItem>
                <SelectItem value="date">По дате</SelectItem>
              </SelectContent>
            </Select>

            <Button
              variant="outline"
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            >
              {sortOrder === 'asc' ? (
                <SortAsc className="w-4 h-4 mr-2" />
              ) : (
                <SortDesc className="w-4 h-4 mr-2" />
              )}
              {sortOrder === 'asc' ? 'По возрастанию' : 'По убыванию'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Advanced Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Filter className="w-5 h-5 mr-2" />
            Дополнительные фильтры
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label className="text-sm font-medium text-gray-400">Мин. просмотры</Label>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0"
                  value={minViews}
                  onChange={(e) => setMinViews(Number(e.target.value) || 0)}
                  className="mt-1 opacity-50"
                  disabled
                />
                <span className="absolute top-2 right-3 text-xs text-gray-500 font-medium">
                  В разработке
                </span>
              </div>
            </div>
            <div>
              <Label className="text-sm font-medium text-gray-400">Мин. вовлеченность (%)</Label>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0"
                  value={minEngagement}
                  onChange={(e) => setMinEngagement(Number(e.target.value) || 0)}
                  className="mt-1 opacity-50"
                  disabled
                />
                <span className="absolute top-2 right-3 text-xs text-gray-500 font-medium">
                  В разработке
                </span>
              </div>
            </div>
            <div>
              <Label className="text-sm font-medium text-gray-400">Мин. viral score</Label>
              <div className="relative">
                <Input
                  type="number"
                  step="0.1"
                  placeholder="1.0"
                  value={minViralScore}
                  onChange={(e) => setMinViralScore(Number(e.target.value) || 1.0)}
                  className="mt-1 opacity-50"
                  disabled
                />
                <span className="absolute top-2 right-3 text-xs text-gray-500 font-medium">
                  В разработке
                </span>
              </div>
            </div>
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => {
                  setMinViews(0)
                  setMinEngagement(0)
                  setMinViralScore(1.0)
                  setShowOnlyViral(false)
                  setSearchTerm('')
                  setFilterChannel('all')
                  setDateRange('7d')
                }}
                className="w-full"
              >
                Сбросить фильтры
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Posts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loadingPosts ? (
          // Loading skeletons
          Array.from({ length: 6 }).map((_, index) => (
            <Card key={index} className="animate-pulse">
              <CardHeader>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 mt-2"></div>
              </CardHeader>
              <CardContent>
                <div className="h-20 bg-gray-200 rounded mb-4"></div>
                <div className="flex space-x-4">
                  <div className="h-8 bg-gray-200 rounded w-16"></div>
                  <div className="h-8 bg-gray-200 rounded w-16"></div>
                  <div className="h-8 bg-gray-200 rounded w-16"></div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : filteredAndSortedPosts.length > 0 ? (
          <>
            {filteredAndSortedPosts.map((post) => (
              <PostCard
                key={post.id}
                post={post}
                onQuickAnalyze={handleQuickAnalyzePost}
                onAnalyze={handleAnalyzePost}
                showQuickAnalysis={true}
                showAnalysis={true}
                isAnalyzing={analyzingPosts.has(post.id)}
              />
            ))}

            {/* Элемент для IntersectionObserver - подгрузка дополнительных постов */}
            {hasMore && (
              <div
                ref={loadMoreRef}
                className="col-span-full flex justify-center items-center py-8"
              >
                {loadingMore ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                    <span className="text-gray-600">Загрузка постов...</span>
                  </div>
                ) : (
                  <div className="text-gray-500 text-sm">
                    Прокрутите вниз для загрузки ещё постов
                  </div>
                )}
              </div>
            )}

            {/* Сообщение о конце списка */}
            {!hasMore && posts.length > 0 && (
              <div className="col-span-full text-center py-8">
                <p className="text-gray-500 text-sm">
                  Все посты загружены ({posts.length} из {totalPosts?.toLocaleString() || '0'})
                </p>
              </div>
            )}
          </>
        ) : (
          <div className="col-span-full text-center py-12">
            <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-500">Посты не найдены</p>
            <p className="text-sm text-gray-400 mt-2">
              Попробуйте изменить фильтры или запустить парсинг
            </p>
          </div>
        )}
      </div>

      {/* Модальное окно анализа */}
      {showAnalysisModal && analyzingPost && (
        <PostAnalysisModal
          post={analyzingPost}
          onClose={() => {
            setShowAnalysisModal(false)
            setAnalyzingPost(null)
          }}
          onAnalysisComplete={handleAnalysisComplete}
        />
      )}
    </div>
  )
}

