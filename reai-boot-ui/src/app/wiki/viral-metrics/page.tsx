'use client'

import Link from 'next/link'
import { ArrowLeft, Zap, TrendingUp, BarChart3, Info, AlertTriangle, CheckCircle, Eye } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'

export default function ViralMetricsPage() {
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
              <Zap className="w-5 h-5 text-purple-600" />
              <h1 className="text-xl font-semibold text-gray-900">Viral Score - что это?</h1>
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
                <Zap className="w-6 h-6 text-purple-600" />
                Что такое Viral Score?
              </CardTitle>
              <CardDescription>
                Viral Score - это комплексный показатель виральности поста, рассчитанный на основе нескольких метрик
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-gray-700">
                <strong>Viral Score</strong> показывает, насколько пост потенциально вирусный и способен набрать
                большое количество просмотров и взаимодействий. Этот показатель рассчитывается на основе:
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center gap-3 p-4 bg-purple-50 rounded-lg">
                  <Eye className="w-5 h-5 text-purple-600" />
                  <div>
                    <div className="font-medium text-purple-900">Просмотры</div>
                    <div className="text-sm text-purple-700">Количество просмотров поста</div>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-blue-600" />
                  <div>
                    <div className="font-medium text-blue-900">Вовлеченность</div>
                    <div className="text-sm text-blue-700">Реакции, репосты, комментарии</div>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg">
                  <BarChart3 className="w-5 h-5 text-green-600" />
                  <div>
                    <div className="font-medium text-green-900">Статистика канала</div>
                    <div className="text-sm text-green-700">Базовые показатели канала</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* How it's calculated */}
          <Card>
            <CardHeader>
              <CardTitle>Как рассчитывается Viral Score?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Алгоритм расчета</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-3">Viral Score рассчитывается по формуле:</p>
                  <div className="bg-white p-3 rounded border font-mono text-sm">
                    Viral Score = (Просмотры × Вовлеченность × Z-Score) / Средние показатели канала
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <Info className="w-4 h-4 text-blue-500" />
                    Основные компоненты
                  </h4>
                  <ul className="space-y-2 text-sm">
                    <li className="flex justify-between">
                      <span>Количество просмотров</span>
                      <Badge variant="outline">40%</Badge>
                    </li>
                    <li className="flex justify-between">
                      <span>Вовлеченность</span>
                      <Badge variant="outline">30%</Badge>
                    </li>
                    <li className="flex justify-between">
                      <span>Z-Score</span>
                      <Badge variant="outline">20%</Badge>
                    </li>
                    <li className="flex justify-between">
                      <span>Базовые метрики канала</span>
                      <Badge variant="outline">10%</Badge>
                    </li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-green-500" />
                    Дополнительные метрики
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between items-center">
                      <span>Z-Score</span>
                      <Badge variant="secondary">Статистическая значимость</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>× медианы</span>
                      <Badge variant="secondary">Отношение к среднему</Badge>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Interpretation */}
          <Card>
            <CardHeader>
              <CardTitle>Как интерпретировать Viral Score?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    <strong className="text-green-700">Высокий (1.5+)</strong>
                    <br />
                    Пост имеет высокий потенциал виральности. Вероятно, наберет много просмотров.
                  </AlertDescription>
                </Alert>

                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    <strong className="text-blue-700">Средний (0.5-1.5)</strong>
                    <br />
                    Пост в пределах нормы для канала. Может набрать среднее количество просмотров.
                  </AlertDescription>
                </Alert>

                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <strong className="text-orange-700">Низкий (&lt;0.5)</strong>
                    <br />
                    Пост ниже среднего по виральности. Может потребовать оптимизации.
                  </AlertDescription>
                </Alert>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-semibold text-blue-900 mb-2">💡 Советы по улучшению</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Публикуйте в пиковые часы активности аудитории</li>
                  <li>• Используйте привлекательные заголовки и превью</li>
                  <li>• Добавляйте визуальный контент (фото, видео)</li>
                  <li>• Взаимодействуйте с аудиторией в комментариях</li>
                </ul>
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
                <Link href="/wiki/ai-score">
                  <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span className="font-medium">AI Score - оценка ИИ</span>
                    </div>
                    <ArrowLeft className="w-4 h-4 rotate-180" />
                  </div>
                </Link>

                <Link href="/wiki/improve-viral-score">
                  <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="font-medium">Как улучшить Viral Score?</span>
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
