'use client'

import Link from 'next/link'
import { ArrowLeft, Star, Brain, TrendingUp, AlertTriangle, CheckCircle, Target, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'

export default function AIScorePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <Link href="/wiki">
              <Button variant="outline" size="sm">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Назад к Wiki
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <Star className="w-5 h-5 text-yellow-500" />
              <h1 className="text-xl font-semibold text-gray-900">AI Score - оценка ИИ</h1>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Introduction */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-6 h-6 text-blue-600" />
                Что такое AI Score?
              </CardTitle>
              <CardDescription>
                AI Score - это оценка поста искусственным интеллектом по шкале от 1 до 10
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-gray-700">
                <strong>AI Score</strong> показывает, насколько пост подходит для создания качественного
                контента (Reels, Shorts, Stories). Оценка рассчитывается на основе:
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg">
                  <Target className="w-5 h-5 text-blue-600" />
                  <div>
                    <div className="font-medium text-blue-900">Практическая ценность</div>
                    <div className="text-sm text-blue-700">Полезность информации</div>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  <div>
                    <div className="font-medium text-green-900">Вирусный потенциал</div>
                    <div className="text-sm text-green-700">Способность привлечь внимание</div>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-4 bg-purple-50 rounded-lg">
                  <Star className="w-5 h-5 text-purple-600" />
                  <div>
                    <div className="font-medium text-purple-900">Качество контента</div>
                    <div className="text-sm text-purple-700">Структура и оформление</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* How it's calculated */}
          <Card>
            <CardHeader>
              <CardTitle>Как рассчитывается AI Score?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Алгоритм оценки</h3>
                <p className="text-gray-700">
                  ИИ анализирует пост по нескольким критериям и присваивает общую оценку от 1 до 10:
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    Критерии оценки
                  </h4>
                  <ul className="space-y-2 text-sm">
                    <li className="flex justify-between items-center">
                      <span>Практическая ценность</span>
                      <Badge variant="outline">35%</Badge>
                    </li>
                    <li className="flex justify-between items-center">
                      <span>Вирусный потенциал</span>
                      <Badge variant="outline">30%</Badge>
                    </li>
                    <li className="flex justify-between items-center">
                      <span>Качество изложения</span>
                      <Badge variant="outline">20%</Badge>
                    </li>
                    <li className="flex justify-between items-center">
                      <span>Актуальность темы</span>
                      <Badge variant="outline">15%</Badge>
                    </li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <Brain className="w-4 h-4 text-blue-500" />
                    ИИ анализатор
                  </h4>
                  <div className="space-y-2 text-sm text-gray-600">
                    <p>• Анализирует текст поста</p>
                    <p>• Оценивает структуру и оформление</p>
                    <p>• Определяет целевую аудиторию</p>
                    <p>• Прогнозирует вовлеченность</p>
                  </div>
                </div>
              </div>

              <Alert>
                <Brain className="h-4 w-4" />
                <AlertDescription>
                  <strong>Технология:</strong> AI Score рассчитывается с использованием современных
                  языковых моделей (GPT-4, Claude) для комплексного анализа контента.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>

          {/* Interpretation */}
          <Card>
            <CardHeader>
              <CardTitle>Как интерпретировать AI Score?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    <strong className="text-green-700">Высокий (8-10)</strong>
                    <br />
                    Отличный пост для создания контента. Высокая практическая ценность и вирусный потенциал.
                  </AlertDescription>
                </Alert>

                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <strong className="text-yellow-700">Средний (5-7)</strong>
                    <br />
                    Пост среднего качества. Может быть использован после доработки или в нишевых темах.
                  </AlertDescription>
                </Alert>

                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <strong className="text-red-700">Низкий (1-4)</strong>
                    <br />
                    Пост не рекомендуется для создания контента. Низкая ценность или проблемы с качеством.
                  </AlertDescription>
                </Alert>
              </div>

              <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                <h4 className="font-semibold text-yellow-900 mb-2 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Важное замечание
                </h4>
                <p className="text-sm text-yellow-800">
                  AI Score - это автоматизированная оценка. Она помогает быстро определить потенциал поста,
                  но не заменяет экспертную оценку контент-мейкера. Рекомендуется учитывать специфику
                  вашей аудитории и текущие тренды.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* When to use */}
          <Card>
            <CardHeader>
              <CardTitle>Когда использовать AI Score?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <h4 className="font-semibold text-green-700">✅ Рекомендуется для:</h4>
                  <ul className="text-sm space-y-2">
                    <li>• Быстрый скрининг большого количества постов</li>
                    <li>• Автоматизированная обработка контента</li>
                    <li>• Определение приоритетов для ручной обработки</li>
                    <li>• Фильтрация низкокачественного контента</li>
                  </ul>
                </div>

                <div className="space-y-3">
                  <h4 className="font-semibold text-orange-700">⚠️ Ограничения:</h4>
                  <ul className="text-sm space-y-2">
                    <li>• Не учитывает визуальный контент</li>
                    <li>• Может не понимать специфический сленг</li>
                    <li>• Не оценивает актуальность темы</li>
                    <li>• Автоматизированная оценка, не экспертная</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Related Articles */}
          <Card>
            <CardHeader>
              <CardTitle>Связанные статьи</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3">
                <Link href="/wiki/viral-metrics">
                  <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                      <span className="font-medium">Viral Score - что это?</span>
                    </div>
                    <ArrowLeft className="w-4 h-4 rotate-180" />
                  </div>
                </Link>

                <Link href="/wiki/content-analysis">
                  <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span className="font-medium">Анализ контента</span>
                    </div>
                    <ArrowLeft className="w-4 h-4 rotate-180" />
                  </div>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
