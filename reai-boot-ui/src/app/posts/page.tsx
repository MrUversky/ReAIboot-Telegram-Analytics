'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSupabase } from '@/components/SupabaseProvider'
import { PostCard } from '@/components/PostCard'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
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
  Share
} from 'lucide-react'
import { apiClient, Post } from '@/lib/api'

export default function PostsPage() {
  const router = useRouter()
  const { user, loading } = useSupabase()
  const [posts, setPosts] = useState<Post[]>([])
  const [loadingPosts, setLoadingPosts] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState<'date' | 'score' | 'views'>('score')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [filterChannel, setFilterChannel] = useState<string>('all')
  const [channels, setChannels] = useState<string[]>([])

  useEffect(() => {
    if (!loading && !user) {
      router.push('/auth')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      loadPosts()
    }
  }, [user])

  const loadPosts = async () => {
    try {
      setLoadingPosts(true)
      const postsData = await apiClient.getPosts(100) // Load more posts
      setPosts(postsData)

      // Extract unique channels
      const uniqueChannels = [...new Set(postsData.map(post => post.channel_username))]
      setChannels(uniqueChannels)
    } catch (error) {
      console.error('Error loading posts:', error)
    } finally {
      setLoadingPosts(false)
    }
  }

  const handleAnalyzePost = async (post: Post) => {
    try {
      await apiClient.analyzePosts([post])
      alert('Анализ запущен! Результаты появятся в разделе Сценарии.')
    } catch (error) {
      console.error('Error analyzing post:', error)
      alert('Ошибка при запуске анализа')
    }
  }

  const filteredAndSortedPosts = posts
    .filter(post => {
      const matchesSearch = searchTerm === '' ||
        post.text_preview.toLowerCase().includes(searchTerm.toLowerCase()) ||
        post.channel_title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        post.channel_username.toLowerCase().includes(searchTerm.toLowerCase())

      const matchesChannel = filterChannel === 'all' || post.channel_username === filterChannel

      return matchesSearch && matchesChannel
    })
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
        <Button onClick={loadPosts} disabled={loadingPosts}>
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
                <p className="text-2xl font-bold text-gray-900">{posts.length}</p>
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
                <p className="text-2xl font-bold text-gray-900">
                  {posts.reduce((sum, post) => sum + post.views, 0).toLocaleString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <Heart className="w-8 h-8 text-red-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Реакции</p>
                <p className="text-2xl font-bold text-gray-900">
                  {posts.reduce((sum, post) => sum + post.reactions, 0).toLocaleString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Posts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <TrendingUp className="w-5 h-5 mr-2" />
            Топ-10 постов
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {getTopPosts().map((post, index) => (
              <div key={post.id} className="relative">
                <div className="absolute -top-2 -left-2 z-10">
                  <Badge className="bg-yellow-500 text-white">
                    #{index + 1}
                  </Badge>
                </div>
                <PostCard
                  post={post}
                  onAnalyze={handleAnalyzePost}
                  showAnalysis={true}
                />
              </div>
            ))}
          </div>
          {getTopPosts().length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>Нет постов для отображения</p>
              <p className="text-sm mt-2">Запустите парсинг для загрузки данных</p>
            </div>
          )}
        </CardContent>
      </Card>

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
                <SelectItem value="score">По рейтингу</SelectItem>
                <SelectItem value="views">По просмотрам</SelectItem>
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
          filteredAndSortedPosts.map((post) => (
            <PostCard
              key={post.id}
              post={post}
              onAnalyze={handleAnalyzePost}
              showAnalysis={true}
            />
          ))
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
    </div>
  )
}
