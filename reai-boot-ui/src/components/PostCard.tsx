import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Eye, Heart, MessageCircle, Share, ExternalLink, TrendingUp, Zap, BarChart3,
  ChevronDown, ChevronUp, HelpCircle, Info, Star
} from 'lucide-react'
import type { Post } from '@/lib/api'

interface PostCardProps {
  post: Post
  onAnalyze?: (post: Post) => void
  onQuickAnalyze?: (post: Post) => void
  showAnalysis?: boolean
  showQuickAnalysis?: boolean
  isAnalyzing?: boolean
}

export function PostCard({ post, onAnalyze, onQuickAnalyze, showAnalysis = true, showQuickAnalysis = false, isAnalyzing = false }: PostCardProps) {
  const [showDetailedMetrics, setShowDetailedMetrics] = useState(false)
  const [showHelpTooltip, setShowHelpTooltip] = useState<string | null>(null)
  const [isTooltipClicked, setIsTooltipClicked] = useState(false)
  const [tooltipTimeout, setTooltipTimeout] = useState<NodeJS.Timeout | null>(null)

  // Очистка timeout при размонтировании компонента
  useEffect(() => {
    return () => {
      if (tooltipTimeout) {
        clearTimeout(tooltipTimeout)
      }
    }
  }, [tooltipTimeout])

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  // Функция для закрытия подсказок при клике вне их
  const closeTooltips = () => {
    if (isTooltipClicked) {
      setShowHelpTooltip(null)
      setIsTooltipClicked(false)
    }
  }

  // Улучшенные функции для работы с tooltip'ами
  const showTooltip = (type: string) => {
    if (tooltipTimeout) {
      clearTimeout(tooltipTimeout)
      setTooltipTimeout(null)
    }
    setShowHelpTooltip(type)
  }

  const hideTooltip = () => {
    if (!isTooltipClicked) {
      const timeout = setTimeout(() => {
        setShowHelpTooltip(null)
      }, 300) // Задержка перед скрытием
      setTooltipTimeout(timeout)
    }
  }

  const toggleTooltip = (type: string) => {
    if (showHelpTooltip === type && isTooltipClicked) {
      setShowHelpTooltip(null)
      setIsTooltipClicked(false)
    } else {
      setShowHelpTooltip(type)
      setIsTooltipClicked(true)
    }
  }

  // Обработчик клика по карточке
  const handleCardClick = (e: React.MouseEvent) => {
    // Если клик не по подсказке или иконке помощи, закрываем подсказки
    if (!(e.target as HTMLElement).closest('.help-tooltip') &&
        !(e.target as HTMLElement).closest('.help-icon')) {
      closeTooltips()
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getScoreVariant = (score: number) => {
    if (score >= 8) return "default" // Зеленый для отличных
    if (score >= 6) return "secondary" // Серый для хороших
    if (score >= 4) return "outline" // Контур для средних
    return "outline" // Контур для плохих (т.к. destructive не поддерживается)
  }

  return (
    <div onClick={handleCardClick}>
      <Card className="w-full hover:shadow-lg transition-shadow">
        <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg font-semibold line-clamp-2">
              {post.channel_title || `@${post.channel_username}`}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              {formatDate(post.date)}
            </p>
          </div>
          {post.score !== null && post.score !== undefined ? (
            <div className="flex items-center gap-2">
              <Badge
                variant={getScoreVariant(post.score)}
                className="flex items-center gap-1 font-semibold"
              >
                <Star className="w-3 h-3" />
                {(post.score as number).toFixed(1)}/10
                {(post.score as number) >= 8 && <span className="text-xs">🔥</span>}
                {(post.score as number) < 5 && <span className="text-xs">⚠️</span>}
              </Badge>
              <div className="relative">
                <HelpCircle
                  className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-pointer help-icon"
                  onClick={() => toggleTooltip('ai_score')}
                  onMouseEnter={() => showTooltip('ai_score')}
                  onMouseLeave={() => hideTooltip()}
                  onTouchStart={() => toggleTooltip('ai_score')}
                />
                {showHelpTooltip === 'ai_score' && (
                  <div className="absolute z-20 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl -top-2 left-6 w-56 border border-gray-700">
                    <p className="font-medium mb-2">AI Score</p>
                    <p className="mb-3 leading-relaxed">Оценка поста ИИ от 1 до 10 по шкале пригодности для создания контента.</p>
                    <a
                      href="/wiki/ai-score"
                      className="text-blue-300 hover:text-blue-200 text-xs underline inline-block font-medium"
                      onClick={(e) => {
                        setShowHelpTooltip(null)
                        setIsTooltipClicked(false)
                      }}
                    >
                      📖 Подробнее в Wiki →
                    </a>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="flex items-center gap-1">
                📝 Не оценено
              </Badge>
              <div className="relative">
                <HelpCircle
                  className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-pointer help-icon"
                  onClick={() => toggleTooltip('no_ai_score')}
                  onMouseEnter={() => showTooltip('no_ai_score')}
                  onMouseLeave={() => hideTooltip()}
                  onTouchStart={() => toggleTooltip('no_ai_score')}
                />
                {showHelpTooltip === 'no_ai_score' && (
                  <div className="absolute z-20 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl -top-2 left-6 w-56 border border-gray-700">
                    <p className="font-medium mb-2">AI оценка недоступна</p>
                    <p className="mb-3 leading-relaxed">Пост еще не был проанализирован ИИ. Нажмите "Оценить" для автоматической оценки пригодности контента.</p>
                    <a
                      href="/wiki/ai-score"
                      className="text-blue-300 hover:text-blue-200 text-xs underline inline-block font-medium"
                      onClick={(e) => {
                        setShowHelpTooltip(null)
                        setIsTooltipClicked(false)
                      }}
                    >
                      📖 Подробнее об AI Score →
                    </a>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        <p className="text-sm text-gray-700 line-clamp-4 mb-4">
          {post.text_preview}
        </p>

        {/* Metrics */}
        <div className="grid grid-cols-4 gap-4 mb-4">
          <div className="flex items-center gap-2 text-sm">
            <Eye className="w-4 h-4 text-blue-500" />
            <span className="font-medium">{formatNumber(post.views)}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Heart className="w-4 h-4 text-red-500" />
            <span className="font-medium">{formatNumber(post.reactions)}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <MessageCircle className="w-4 h-4 text-green-500" />
            <span className="font-medium">{formatNumber(post.replies)}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Share className="w-4 h-4 text-purple-500" />
            <span className="font-medium">{formatNumber(post.forwards)}</span>
          </div>
        </div>


        {/* Analysis Status */}
        {post.analysis_status && (
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-4 h-4 text-blue-500" />
              <span className="text-sm font-medium text-gray-700">Статус анализа</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <Badge variant={post.analysis_status.filter_passed ? "default" : "secondary"}>
                {post.analysis_status.filter_passed ? "✅ Фильтр" : "❌ Фильтр"}
              </Badge>
              <Badge variant={post.analysis_status.analysis_completed ? "default" : "secondary"}>
                {post.analysis_status.analysis_completed ? "✅ Анализ" : "⏳ Анализ"}
              </Badge>
              <Badge variant={post.analysis_status.rubric_selected ? "default" : "secondary"}>
                {post.analysis_status.rubric_selected ? "✅ Рубрики" : "⏳ Рубрики"}
              </Badge>
              <Badge variant={post.analysis_status.scenarios_generated ? "default" : "secondary"}>
                {post.analysis_status.scenarios_generated ? "✅ Сценарии" : "⏳ Сценарии"}
              </Badge>
            </div>
            {post.analysis_status.filter_score && (
              <p className="text-xs text-gray-600 mt-2">
                Оценка фильтра: {post.analysis_status.filter_score}/10
              </p>
            )}
          </div>
        )}

        {/* Rubrics */}
        {post.rubrics && post.rubrics.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-medium text-gray-600 mb-2">Подходящие рубрики:</p>
            <div className="flex flex-wrap gap-1">
              {post.rubrics.map((rubric, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {post.rubric_names?.[index] || rubric}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Viral Metrics */}
        {(post.viral_score !== undefined && post.viral_score !== null) && (
          <div className={`p-3 rounded-lg mb-4 ${
            (post.viral_score || 0) > 0
              ? 'bg-gradient-to-r from-purple-50 to-blue-50'
              : 'bg-gradient-to-r from-gray-50 to-gray-100'
          }`}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Zap className={`w-4 h-4 ${(post.viral_score || 0) > 0 ? 'text-purple-600' : 'text-gray-500'}`} />
                <span className={`text-sm font-medium ${(post.viral_score || 0) > 0 ? 'text-gray-700' : 'text-gray-600'}`}>
                  Viral Score {(post.viral_score || 0).toFixed(2)}
                </span>
                <div className="relative">
                  <HelpCircle
                    className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-pointer help-icon"
                    onClick={() => toggleTooltip('viral_score')}
                    onMouseEnter={() => showTooltip('viral_score')}
                    onMouseLeave={() => hideTooltip()}
                    onTouchStart={() => toggleTooltip('viral_score')}
                  />
                  {(showHelpTooltip === 'viral_score') && (
                    <div className="absolute z-20 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl -top-2 left-6 w-56 border border-gray-700 help-tooltip">
                      <p className="font-medium mb-2">Viral Score</p>
                      <p className="mb-3 leading-relaxed">Показатель виральности поста на основе статистики канала и вовлеченности аудитории.</p>
                      <a
                        href="/wiki/viral-metrics"
                        className="text-blue-300 hover:text-blue-200 text-xs underline inline-block font-medium"
                        onClick={(e) => {
                          setShowHelpTooltip(null)
                          setIsTooltipClicked(false)
                        }}
                      >
                        📖 Подробнее в Wiki →
                      </a>
                    </div>
                  )}
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDetailedMetrics(!showDetailedMetrics)}
                className="h-6 px-2 text-xs"
              >
                {showDetailedMetrics ? (
                  <>
                    <ChevronUp className="w-3 h-3 mr-1" />
                    Свернуть
                  </>
                ) : (
                  <>
                    <ChevronDown className="w-3 h-3 mr-1" />
                    Подробнее
                  </>
                )}
              </Button>
            </div>

            {/* Подробная информация */}
            {showDetailedMetrics && (
              <div className="space-y-3 border-t pt-3">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-3 h-3 text-blue-500" />
                  <span className="text-sm text-gray-600">Вовлеченность:</span>
                  <span className={`text-sm font-medium ${(post.viral_score || 0) > 0 ? 'text-gray-900' : 'text-gray-500'}`}>
                    {((post.engagement_rate || 0) * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  {post.zscore !== undefined && post.zscore !== null && (
                    <div className="flex items-center gap-2">
                      <Info className="w-3 h-3 text-blue-500" />
                      <span className="text-gray-600">Z-score:</span>
                      <span className={`font-medium ${(post.viral_score || 0) > 0 ? 'text-gray-900' : 'text-gray-500'}`}>
                        {post.zscore.toFixed(2)}
                      </span>
                    </div>
                  )}
                  {post.median_multiplier !== undefined && post.median_multiplier !== null && (
                    <div className="flex items-center gap-2">
                      <BarChart3 className="w-3 h-3 text-green-500" />
                      <span className="text-gray-600">× медианы:</span>
                      <span className={`font-medium ${(post.viral_score || 0) > 0 ? 'text-gray-900' : 'text-gray-500'}`}>
                        {post.median_multiplier.toFixed(1)}×
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Media indicator */}
        {post.has_media && (
          <Badge variant="secondary" className="text-xs">
            📎 С медиа
          </Badge>
        )}
      </CardContent>

      <CardFooter className="pt-3 border-t">
        <div className="flex gap-2 w-full">
          <a
            href={post.permalink}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            Открыть в TG
          </a>

          {/* Кнопки анализа */}
          <div className="flex gap-2 flex-1">
            {showQuickAnalysis && onQuickAnalyze && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => onQuickAnalyze(post)}
                className="flex-1"
                title="Быстрая оценка поста по шкале 1-10"
                disabled={isAnalyzing}
              >
                {isAnalyzing ? (
                  <>
                    <div className="w-4 h-4 mr-2 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                    <span className="hidden sm:inline">Оцениваем...</span>
                    <span className="sm:hidden">...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 mr-2" />
                    <span className="hidden sm:inline">Оценить</span>
                    <span className="sm:hidden">1-10</span>
                  </>
                )}
              </Button>
            )}

            {showAnalysis && onAnalyze && (
              <Button
                size="sm"
                className="flex-1"
                onClick={() => onAnalyze(post)}
                title="Полный анализ: фильтрация → анализ → выбор рубрик → генерация сценария"
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Создать сценарий</span>
                <span className="sm:hidden">Сценарий</span>
              </Button>
            )}
          </div>
        </div>
      </CardFooter>
    </Card>
    </div>
  )
}
