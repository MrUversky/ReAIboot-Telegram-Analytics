'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  Book,
  Search,
  HelpCircle,
  BarChart3,
  Star,
  Zap,
  MessageSquare,
  ChevronRight,
  Home
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const wikiCategories = [
  {
    id: 'getting-started',
    title: 'Начало работы',
    description: 'Основы использования платформы',
    icon: Home,
    articles: [
      { title: 'Введение в ReAIboot', href: '/wiki/introduction', tags: ['новичок', 'обзор'] },
      { title: 'Быстрый старт', href: '/wiki/quick-start', tags: ['новичок', 'туториал'] },
    ]
  },
  {
    id: 'metrics',
    title: 'Метрики и аналитика',
    description: 'Понимание показателей и оценок',
    icon: BarChart3,
    articles: [
      { title: 'Viral Score - что это?', href: '/wiki/viral-metrics', tags: ['метрики', 'виральность'] },
      { title: 'AI Score - оценка ИИ', href: '/wiki/ai-score', tags: ['ИИ', 'оценка'] },
      { title: 'Z-score и статистические метрики', href: '/wiki/statistical-metrics', tags: ['статистика', 'анализ'] },
    ]
  },
  {
    id: 'ai-features',
    title: 'ИИ функции',
    description: 'Как работает искусственный интеллект',
    icon: Star,
    articles: [
      { title: 'Анализ контента', href: '/wiki/content-analysis', tags: ['ИИ', 'анализ'] },
      { title: 'Генерация сценариев', href: '/wiki/scenario-generation', tags: ['ИИ', 'сценарии'] },
      { title: 'Оценка пригодности', href: '/wiki/suitability-scoring', tags: ['ИИ', 'оценка'] },
    ]
  },
  {
    id: 'faq',
    title: 'Часто задаваемые вопросы',
    description: 'Ответы на популярные вопросы',
    icon: HelpCircle,
    articles: [
      { title: 'Как улучшить Viral Score?', href: '/wiki/improve-viral-score', tags: ['FAQ', 'оптимизация'] },
      { title: 'Что значит низкая AI оценка?', href: '/wiki/low-ai-score', tags: ['FAQ', 'оценки'] },
      { title: 'Как работает анализ постов?', href: '/wiki/post-analysis', tags: ['FAQ', 'анализ'] },
    ]
  }
]

const popularArticles = [
  { title: 'Viral Score - что это?', href: '/wiki/viral-metrics', views: 1250 },
  { title: 'AI Score - оценка ИИ', href: '/wiki/ai-score', views: 980 },
  { title: 'Как улучшить Viral Score?', href: '/wiki/improve-viral-score', views: 756 },
  { title: 'Анализ контента', href: '/wiki/content-analysis', views: 543 },
]

export default function WikiPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const filteredCategories = searchQuery
    ? wikiCategories.map(category => ({
        ...category,
        articles: category.articles.filter(article =>
          article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          article.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
        )
      })).filter(category => category.articles.length > 0)
    : wikiCategories

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Book className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">ReAIboot Wiki</h1>
                <p className="text-gray-600">Документация и справка по платформе</p>
              </div>
            </div>
            <Link href="/">
              <Button variant="outline">
                <Home className="w-4 h-4 mr-2" />
                На главную
              </Button>
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search */}
        <div className="mb-8">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              placeholder="Поиск по документации..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Разделы</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant={selectedCategory === null ? "default" : "outline"}
                  className="w-full justify-start"
                  onClick={() => setSelectedCategory(null)}
                >
                  Все разделы
                </Button>
                {wikiCategories.map((category) => (
                  <Button
                    key={category.id}
                    variant={selectedCategory === category.id ? "default" : "outline"}
                    className="w-full justify-start"
                    onClick={() => setSelectedCategory(category.id)}
                  >
                    <category.icon className="w-4 h-4 mr-2" />
                    {category.title}
                  </Button>
                ))}
              </CardContent>
            </Card>

            {/* Popular Articles */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="text-lg">Популярное</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {popularArticles.map((article, index) => (
                  <Link key={index} href={article.href} className="block">
                    <div className="flex items-start gap-3 p-2 rounded hover:bg-gray-50 transition-colors">
                      <MessageSquare className="w-4 h-4 text-gray-400 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900 line-clamp-2">
                          {article.title}
                        </p>
                        <p className="text-xs text-gray-500">
                          {article.views} просмотров
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-gray-400" />
                    </div>
                  </Link>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {filteredCategories.map((category) => (
              <Card key={category.id}>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <category.icon className="w-6 h-6 text-blue-600" />
                    <div>
                      <CardTitle className="text-xl">{category.title}</CardTitle>
                      <CardDescription>{category.description}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4">
                    {category.articles.map((article, index) => (
                      <Link key={index} href={article.href}>
                        <div className="flex items-center justify-between p-4 rounded-lg border hover:bg-gray-50 transition-colors">
                          <div className="flex-1">
                            <h3 className="font-medium text-gray-900 mb-1">
                              {article.title}
                            </h3>
                            <div className="flex gap-2">
                              {article.tags.map((tag, tagIndex) => (
                                <Badge key={tagIndex} variant="secondary" className="text-xs">
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          <ChevronRight className="w-5 h-5 text-gray-400" />
                        </div>
                      </Link>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}

            {filteredCategories.length === 0 && (
              <Card>
                <CardContent className="text-center py-12">
                  <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Ничего не найдено
                  </h3>
                  <p className="text-gray-600">
                    Попробуйте изменить поисковый запрос
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
