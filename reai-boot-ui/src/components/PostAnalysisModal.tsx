import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Eye, Heart, MessageCircle, Share, TrendingUp, BarChart3, Target, Zap, CheckCircle, XCircle, Clock } from 'lucide-react'
import { RubricFormatSelector } from './RubricFormatSelector'
import { apiClient, Post } from '@/lib/api'

interface PostAnalysisModalProps {
  post: Post
  onClose: () => void
  onAnalysisComplete?: (result: any) => void
}

interface AnalysisStage {
  stage: string
  success: boolean
  data: any
  error: string
  tokens_used: number
  processing_time: number
}

export function PostAnalysisModal({ post, onClose, onAnalysisComplete }: PostAnalysisModalProps) {
  const [currentStep, setCurrentStep] = useState<'analyzing' | 'selecting' | 'generating'>('analyzing')
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [generating, setGenerating] = useState(false)

  const handleQuickAnalysis = async () => {
    setAnalyzing(true)
    try {
      const result = await apiClient.quickAnalyzePost({
        message_id: post.message_id,
        channel_title: post.channel_title,
        text: post.full_text,
        views: post.views,
        reactions: post.reactions,
        replies: post.replies,
        forwards: post.forwards,
        score: post.score || 0
      })

      setAnalysisResult(result)
      setCurrentStep('selecting')

      if (onAnalysisComplete) {
        onAnalysisComplete(result)
      }
    } catch (error) {
      console.error('Error in quick analysis:', error)
      alert('Ошибка при анализе поста')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleGenerateScenarios = async (selectedCombinations: any[]) => {
    setCurrentStep('generating')
    setGenerating(true)

    try {
      const result = await apiClient.generateScenariosFromAnalysis({
        post_data: {
          ...post,
          analysis: analysisResult?.stages?.reduce((acc: any, stage: AnalysisStage) => {
            acc[stage.stage] = stage.data
            return acc
          }, {})
        },
        selected_combinations: selectedCombinations
      })

      if (result.success) {
        alert(`✅ Сгенерировано ${result.scenarios_generated} сценариев!\n\nРезультаты доступны в разделе "Сценарии"`)
        onClose()
      } else {
        alert('Ошибка при генерации сценариев')
        setCurrentStep('selecting')
      }
    } catch (error) {
      console.error('Error generating scenarios:', error)
      alert('Ошибка при генерации сценариев')
      setCurrentStep('selecting')
    } finally {
      setGenerating(false)
    }
  }

  const getStageIcon = (stage: string, success: boolean) => {
    if (success) {
      return <CheckCircle className="w-5 h-5 text-green-600" />
    }
    return <XCircle className="w-5 h-5 text-red-600" />
  }

  const getStageTitle = (stage: string) => {
    const titles: Record<string, string> = {
      'filter': 'Фильтрация',
      'analysis': 'Анализ причин успеха',
      'rubric_selection': 'Выбор рубрик/форматов'
    }
    return titles[stage] || stage
  }

  const formatTime = (seconds: number) => {
    return `${seconds.toFixed(1)} сек`
  }

  // Автоматически запускаем анализ при открытии модального окна
  React.useEffect(() => {
    handleQuickAnalysis()
  }, [])

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <BarChart3 className="w-6 h-6 mr-2 text-blue-600" />
              Анализ поста
            </h2>
            <Button variant="outline" onClick={onClose}>
              ✕
            </Button>
          </div>

          {/* Шаг 1: Анализ */}
          {currentStep === 'analyzing' && (
            <div className="space-y-6">
              {/* Пост превью */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">Анализируемый пост</CardTitle>
                    {post.score !== null && post.score !== undefined && (
                      <Badge
                        variant={(post.score as number) >= 8 ? "default" : (post.score as number) >= 6 ? "secondary" : "outline"}
                        className="flex items-center gap-1"
                      >
                        ⭐ {(post.score as number).toFixed(1)}/10
                        {(post.score as number) < 8 && <span className="text-xs ml-1">⚠️</span>}
                      </Badge>
                    )}
                  </div>
                  {post.score !== null && post.score !== undefined && (post.score as number) < 8 && (
                    <div className="mt-2 p-3 bg-orange-50 border border-orange-200 rounded-md">
                      <p className="text-orange-800 text-sm font-medium">
                        ⚠️ Оценка поста низкая ({(post.score as number).toFixed(1)}/10)
                      </p>
                      <p className="text-orange-700 text-xs mt-1">
                        Рекомендуем выбрать другой пост с оценкой 8+ для лучших результатов.
                      </p>
                    </div>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="flex items-start gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-medium">{post.channel_title || `@${post.channel_username}`}</h4>
                        <Badge variant="outline">{new Date(post.date).toLocaleDateString('ru-RU')}</Badge>
                      </div>
                      <p className="text-gray-700 line-clamp-4">{post.text_preview}</p>
                    </div>
                    <div className="flex flex-col gap-2 text-sm text-gray-600">
                      <div className="flex items-center gap-2">
                        <Eye className="w-4 h-4" />
                        {post.views.toLocaleString()}
                      </div>
                      <div className="flex items-center gap-2">
                        <Heart className="w-4 h-4" />
                        {post.reactions.toLocaleString()}
                      </div>
                      <div className="flex items-center gap-2">
                        <MessageCircle className="w-4 h-4" />
                        {post.replies.toLocaleString()}
                      </div>
                      <div className="flex items-center gap-2">
                        <Share className="w-4 h-4" />
                        {post.forwards.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Прогресс анализа */}
              {analyzing && (
                <Card>
                  <CardContent className="p-6">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                      <h3 className="text-lg font-medium mb-2">Анализируем пост...</h3>
                      <p className="text-gray-600 mb-4">
                        Проходим этапы: Фильтрация → Анализ → Выбор рубрик
                      </p>
                      <Progress value={33} className="w-full" />
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Результаты анализа */}
              {analysisResult && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                      Результаты анализа
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Этапы */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {analysisResult.stages?.map((stage: AnalysisStage, index: number) => (
                        <Card key={index} className={`border ${stage.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                          <CardContent className="p-4">
                            <div className="flex items-center gap-2 mb-2">
                              {getStageIcon(stage.stage, stage.success)}
                              <span className="font-medium">{getStageTitle(stage.stage)}</span>
                            </div>
                            {stage.data && (
                              <div className="text-sm text-gray-600">
                                {stage.stage === 'filter' && stage.data.score && (
                                  <p>Оценка: {stage.data.score}/10</p>
                                )}
                                {stage.stage === 'analysis' && stage.data.success_factors && (
                                  <p>Факторов успеха: {stage.data.success_factors.length}</p>
                                )}
                                {stage.stage === 'rubric_selection' && stage.data.combinations && (
                                  <p>Комбинаций: {stage.data.combinations.length}</p>
                                )}
                              </div>
                            )}
                            <div className="flex justify-between text-xs text-gray-500 mt-2">
                              <span>{stage.tokens_used} токенов</span>
                              <span>{formatTime(stage.processing_time)}</span>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>

                    {/* Общая статистика */}
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">Общая статистика:</span>
                        <div className="flex gap-4 text-sm">
                          <span>Токены: {analysisResult.total_tokens}</span>
                          <span>Время: {formatTime(analysisResult.total_time)}</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Шаг 2: Выбор рубрик/форматов */}
          {currentStep === 'selecting' && analysisResult && (
            <RubricFormatSelector
              post={post}
              analysis={analysisResult.stages?.reduce((acc: any, stage: AnalysisStage) => {
                acc[stage.stage] = stage.data
                return acc
              }, {})}
              onGenerate={handleGenerateScenarios}
              onClose={onClose}
            />
          )}

          {/* Шаг 3: Генерация сценариев */}
          {currentStep === 'generating' && (
            <Card>
              <CardContent className="p-8">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
                  <h3 className="text-lg font-medium mb-2">Генерируем сценарии...</h3>
                  <p className="text-gray-600">
                    Создаем детальные сценарии для выбранных комбинаций рубрик и форматов
                  </p>
                  <Progress value={66} className="w-full mt-4" />
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
