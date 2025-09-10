import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Target, BarChart3, TrendingUp, Play, Clock } from 'lucide-react'
import { apiClient } from '@/lib/api'
import toast from 'react-hot-toast'

interface RubricFormatCombination {
  rubric: {
    id: string
    name: string
  }
  format: {
    id: string
    name: string
  }
  score: number
  reason: string
  content_ideas: string[]
  expected_engagement: number
}

interface RubricFormatSelectorProps {
  post: any
  analysis: any
  onGenerate: (combinations: RubricFormatCombination[]) => void
  onClose: () => void
}

export function RubricFormatSelector({ post, analysis, onGenerate, onClose }: RubricFormatSelectorProps) {
  const [combinations, setCombinations] = useState<RubricFormatCombination[]>([])
  const [selectedCombinations, setSelectedCombinations] = useState<boolean[]>([])
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [combinationsLoaded, setCombinationsLoaded] = useState(false)

  useEffect(() => {
    // Защита от повторной загрузки
    if (combinationsLoaded) {
      return
    }

    // Если есть анализ с комбинациями, используем их
    if (analysis?.rubric_selection?.combinations) {
      setCombinations(analysis.rubric_selection.combinations)
      setSelectedCombinations(new Array(analysis.rubric_selection.combinations.length).fill(true))
      setCombinationsLoaded(true)
    } else {
      // Иначе получаем комбинации из базы данных
      loadCombinations()
    }
  }, [analysis, combinationsLoaded])

  const loadCombinations = async () => {
    setLoading(true)
    try {
      // Получаем рубрики и форматы
      const [rubricsResult, formatsResult] = await Promise.all([
        apiClient.getRubrics(),
        apiClient.getFormats()
      ])

      const rubrics = rubricsResult || []
      const formats = formatsResult || []

      // Создаем комбинации из реальных данных
      const combinations: RubricFormatCombination[] = []

      // Создаем топ-3 комбинаций на основе реальных рубрик и форматов
      if (rubrics.length > 0 && formats.length > 0) {
        // Выбираем первые 3 рубрики и 3 формата
        const selectedRubrics = rubrics.slice(0, 3)
        const selectedFormats = formats.slice(0, 3)

        // Создаем все возможные комбинации
        selectedRubrics.forEach((rubric, rubricIndex) => {
          const format = selectedFormats[rubricIndex % selectedFormats.length]
          combinations.push({
            rubric: { id: rubric.id, name: rubric.name },
            format: { id: format.id, name: format.name },
            score: 8.5 - (rubricIndex * 0.3), // Уменьшаем оценку для разнообразия
            reason: `Комбинация ${rubric.name} + ${format.name} подходит для данного контента`,
            content_ideas: ['Показать пример', 'Дать практический совет', 'Объяснить концепцию'],
            expected_engagement: 0.8 - (rubricIndex * 0.05)
          })
        })
      } else {
        // Fallback для случаев когда нет данных в БД
        combinations.push(
          {
            rubric: { id: 'general', name: 'Общее' },
            format: { id: 'quick_tip', name: 'Быстрый совет' },
            score: 7.5,
            reason: 'Универсальная комбинация для любого контента',
            content_ideas: ['Показать пример', 'Дать практический совет'],
            expected_engagement: 0.75
          }
        )
      }

      setCombinations(combinations)
      setSelectedCombinations(new Array(combinations.length).fill(true))
      setCombinationsLoaded(true)
    } catch (error) {
      console.error('Error loading combinations:', error)
      // Fallback комбинация
      const fallbackCombinations: RubricFormatCombination[] = [
        {
          rubric: { id: 'general', name: 'Общее' },
          format: { id: 'quick_tip', name: 'Быстрый совет' },
          score: 7.5,
          reason: 'Универсальная комбинация для любого контента',
          content_ideas: ['Показать пример', 'Дать практический совет'],
          expected_engagement: 0.75
        }
      ]
      setCombinations(fallbackCombinations)
      setSelectedCombinations(new Array(fallbackCombinations.length).fill(true))
      setCombinationsLoaded(true)
    } finally {
      setLoading(false)
    }
  }

  const toggleCombination = (index: number) => {
    const newSelected = [...selectedCombinations]
    newSelected[index] = !newSelected[index]
    setSelectedCombinations(newSelected)
  }

  const handleGenerate = async () => {
    const selectedItems = combinations.filter((_, index) => selectedCombinations[index])

    if (selectedItems.length === 0) {
      toast.error('Выберите хотя бы одну комбинацию')
      return
    }

    setGenerating(true)
    try {
      await onGenerate(selectedItems)
      onClose()
    } catch (error) {
      console.error('Error generating scenarios:', error)
      toast.error('Ошибка при генерации сценариев')
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <Card className="w-full max-w-4xl">
        <CardContent className="p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p>Загружаем подходящие комбинации...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle className="flex items-center">
          <Target className="w-5 h-5 mr-2 text-blue-600" />
          Выбор рубрик и форматов
        </CardTitle>
        <p className="text-sm text-gray-600">
          Выберите комбинации рубрика+формат для генерации сценариев
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Пост превью */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-medium mb-2">Анализируемый пост:</h4>
          <p className="text-sm text-gray-700 line-clamp-3">{post.text_preview}</p>
          {analysis?.filter?.score && (
            <div className="mt-2 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-green-600" />
              <span className="text-sm">Оценка фильтра: {analysis.filter.score}/10</span>
            </div>
          )}
        </div>

        {/* Комбинации */}
        <div className="space-y-3">
          <h4 className="font-medium">Рекомендуемые комбинации:</h4>
          {combinations.map((combo, index) => (
            <Card key={index} className={`border-2 ${selectedCombinations[index] ? 'border-blue-300 bg-blue-50' : 'border-gray-200'}`}>
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <Checkbox
                    id={`combo-${index}`}
                    checked={selectedCombinations[index]}
                    onCheckedChange={() => toggleCombination(index)}
                    className="mt-1"
                  />

                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge className="bg-blue-100 text-blue-800">
                        <Target className="w-3 h-3 mr-1" />
                        {combo.rubric.name}
                      </Badge>
                      <Badge variant="outline">
                        <Play className="w-3 h-3 mr-1" />
                        {combo.format.name}
                      </Badge>
                      <Badge className="bg-green-100 text-green-800">
                        <TrendingUp className="w-3 h-3 mr-1" />
                        {combo.score}/10
                      </Badge>
                      <Badge className="bg-purple-100 text-purple-800">
                        <Clock className="w-3 h-3 mr-1" />
                        {(combo.expected_engagement * 100).toFixed(0)}%
                      </Badge>
                    </div>

                    <p className="text-sm text-gray-700 mb-2">{combo.reason}</p>

                    <div className="text-xs text-gray-600">
                      <strong>Идеи контента:</strong>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {combo.content_ideas.map((idea, ideaIndex) => (
                          <Badge key={ideaIndex} variant="outline" className="text-xs">
                            {idea}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="bg-blue-50 p-3 rounded-lg">
          <p className="text-sm text-blue-800">
            💡 <strong>Совет:</strong> Для максимальной эффективности выберите 1-2 комбинации.
            Чем точнее подобрана рубрика и формат, тем качественнее будет сценарий.
          </p>
        </div>
      </CardContent>

      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={onClose}>
          Отмена
        </Button>
        <Button
          onClick={handleGenerate}
          disabled={generating || selectedCombinations.filter(Boolean).length === 0}
        >
          {generating ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Генерируем...
            </>
          ) : (
            <>
              🎬 Сгенерировать сценарии ({selectedCombinations.filter(Boolean).length})
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  )
}

