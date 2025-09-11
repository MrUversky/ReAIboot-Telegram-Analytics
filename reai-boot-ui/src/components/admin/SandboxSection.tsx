import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { FlaskRound, Download, Play, RotateCcw, Search, Filter, Edit } from 'lucide-react'
import { EditStepModal } from './EditStepModal'
import { JsonHighlighter } from './JsonHighlighter'

interface SandboxSectionProps {
  // Props will be added as needed
}

export const SandboxSection: React.FC<SandboxSectionProps> = ({}) => {
  const [postData, setPostData] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [stepByStepMode, setStepByStepMode] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [stepResults, setStepResults] = useState<any[]>([])
  const [canExecuteNext, setCanExecuteNext] = useState(false)

  // Edit modal state
  const [editingStep, setEditingStep] = useState<number | null>(null)
  const [editingData, setEditingData] = useState('')

  // Filter state
  const [logSearchTerm, setLogSearchTerm] = useState('')
  const [logFilterType, setLogFilterType] = useState<string>('all')
  const [logFilterSuccess, setLogFilterSuccess] = useState<string>('all')

  // Posts loading state
  const [availablePosts, setAvailablePosts] = useState<any[]>([])
  const [loadingPosts, setLoadingPosts] = useState(false)
  const [selectedPostId, setSelectedPostId] = useState<string>('')

  // Error state
  const [jsonError, setJsonError] = useState<string>('')

  const validatePostData = (jsonString: string) => {
    if (!jsonString.trim()) {
      return { isValid: false, error: 'Введите данные поста в формате JSON' }
    }

    try {
      const data = JSON.parse(jsonString)
      const requiredFields = ['id', 'message_id', 'channel_username', 'text']
      const missingFields = requiredFields.filter(field => !data[field])

      if (missingFields.length > 0) {
        return {
          isValid: false,
          error: `Отсутствуют обязательные поля: ${missingFields.join(', ')}`
        }
      }

      if (typeof data.message_id !== 'number') {
        return { isValid: false, error: 'message_id должен быть числом' }
      }

      if (typeof data.text !== 'string' || data.text.length === 0) {
        return { isValid: false, error: 'text должен быть непустой строкой' }
      }

      if (typeof data.channel_username !== 'string' || !data.channel_username.startsWith('@')) {
        return { isValid: false, error: 'channel_username должен начинаться с @' }
      }

      return { isValid: true, data }
    } catch (error) {
      return { isValid: false, error: 'Некорректный JSON формат' }
    }
  }

  const handleTest = async () => {
    const validation = validatePostData(postData)
    if (!validation.isValid) {
      alert(validation.error)
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/sandbox/test-pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          post_data: validation.data,
          options: { debug_mode: true, step_by_step: stepByStepMode }
        })
      })

      console.log('Starting API call...')
      let result;

      try {
        if (response.ok) {
          result = await response.json()
          console.log('✅ API Response received:', result)
          console.log('✅ Debug log:', result.debug_log)
          console.log('✅ Debug log length:', result.debug_log?.length)
          console.log('✅ Debug log type:', typeof result.debug_log)
          console.log('✅ Debug log is array:', Array.isArray(result.debug_log))
        } else {
          console.log('❌ HTTP Error:', response.status, response.statusText)
          try {
            result = await response.json()
            console.log('❌ API Error Response:', result)
          } catch (e) {
            console.log('❌ Failed to parse error response:', e)
            result = {
              success: false,
              error: `HTTP ${response.status}: ${response.statusText}`,
              debug_log: [{ type: 'error', message: `HTTP ${response.status}: ${response.statusText}`, timestamp: new Date().toISOString() }],
              stages: []
            }
          }
        }

        console.log('📝 Setting result state:', result)
        setResult(result)
        console.log('✅ Result state set successfully')

        // Сбрасываем фильтры
        setLogSearchTerm('')
        setLogFilterType('all')
        setLogFilterSuccess('all')

      } catch (error) {
        console.error('💥 Error in testSandbox:', error)
        const errorResult = {
          success: false,
          error: (error as Error).message || 'Неизвестная ошибка',
          debug_log: [{ type: 'error', message: (error as Error).message || 'Неизвестная ошибка', timestamp: new Date().toISOString() }],
          stages: []
        }
        console.log('📝 Setting error result:', errorResult)
        setResult(errorResult)
      } finally {
        console.log('🏁 Setting loading to false')
        setLoading(false)
      }
    } catch (error) {
      console.error('💥 Outer error in handleTest:', error)
      alert('Ошибка при тестировании песочницы: ' + (error as Error).message)
    } finally {
      setLoading(false)
    }
  }

  // Обновленная функция handleTest с поддержкой режимов
  const handleTestNew = async () => {
    if (stepByStepMode) {
      // Пошаговый режим - начинаем выполнение
      if (currentStep === 0 && stepResults.length === 0) {
        await startStepByStepExecution()
      } else {
        await executeCurrentStep()
      }
    } else {
      // Полный режим
      await handleTestSandbox()
    }
  }

  const getFilteredLogs = () => {
    if (!result?.debug_log) return []

    let filtered = result.debug_log

    if (logFilterType !== 'all') {
      filtered = filtered.filter((log: any) => log.step_type === logFilterType)
    }

    if (logFilterSuccess !== 'all') {
      const successValue = logFilterSuccess === 'success'
      filtered = filtered.filter((log: any) => {
        const data = log.data || {}
        if (log.step_type === 'llm_response') {
          return data.success === successValue
        }
        return true
      })
    }

    if (logSearchTerm.trim()) {
      const searchLower = logSearchTerm.toLowerCase()
      filtered = filtered.filter((log: any) => {
        const stepName = log.step_name?.toLowerCase() || ''
        const stepType = log.step_type?.toLowerCase() || ''
        const dataStr = JSON.stringify(log.data || {}).toLowerCase()
        return stepName.includes(searchLower) ||
               stepType.includes(searchLower) ||
               dataStr.includes(searchLower)
      })
    }

    return filtered
  }

  const handleExportResults = () => {
    if (!result) return

    const exportData = {
      timestamp: new Date().toISOString(),
      sandbox_version: "1.0",
      input_data: {
        post_data: JSON.parse(postData || '{}'),
        options: { debug_mode: true, step_by_step: stepByStepMode }
      },
      results: result,
      filters_applied: {
        search_term: logSearchTerm,
        filter_type: logFilterType,
        filter_success: logFilterSuccess
      },
      filtered_logs_count: getFilteredLogs().length,
      total_logs_count: result.debug_log?.length || 0
    }

    const dataStr = JSON.stringify(exportData, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    const exportFileDefaultName = `sandbox-results-${Date.now()}.json`

    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  const startEditingStep = (stepIndex: number) => {
    const stepResult = stepResults[stepIndex]
    if (stepResult && stepResult.final_data) {
      setEditingStep(stepIndex)
      setEditingData(JSON.stringify(stepResult.final_data, null, 2))
    }
  }

  const handleSaveEditedData = (data: any) => {
    if (editingStep === null) return

    const newStepResults = [...stepResults]
    newStepResults[editingStep] = {
      ...newStepResults[editingStep],
      final_data: data,
      edited: true
    }
    setStepResults(newStepResults)

    if (editingStep === currentStep - 1) {
      setCanExecuteNext(true)
    }
  }

  // Функция загрузки списка постов
  const loadAvailablePosts = async () => {
    setLoadingPosts(true)
    try {
      const response = await fetch('/api/sandbox/posts?limit=100')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setAvailablePosts(data.posts || [])
    } catch (error) {
      console.error('Error loading posts:', error)
      alert('Ошибка загрузки постов')
    } finally {
      setLoadingPosts(false)
    }
  }

  // Функция загрузки выбранного поста
  const loadSelectedPost = async (postId: string) => {
    if (!postId) {
      setPostData('')
      return
    }

    try {
      const response = await fetch(`/api/sandbox/post/${postId}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      const post = data.post

      // Предзаполняем форму данными поста
      setPostData(JSON.stringify({
        id: post.id,
        message_id: post.message_id,
        channel_username: post.channel_username,
        channel_title: post.channel_title,
        text: post.text,
        views: post.views,
        forwards: post.forwards,
        reactions: post.reactions,
        date: post.date
      }, null, 2))

    } catch (error) {
      console.error('Error loading post:', error)
      alert('Ошибка загрузки поста')
    }
  }

  // Загружаем посты при монтировании компонента
  React.useEffect(() => {
    loadAvailablePosts()
  }, [])

  // Загружаем выбранный пост при изменении selectedPostId
  React.useEffect(() => {
    loadSelectedPost(selectedPostId)
  }, [selectedPostId])

  // Функция полного тестирования pipeline
  const handleTestSandbox = async () => {
    // Валидируем данные
    const validation = validatePostData(postData)

    if (!validation.isValid) {
      setJsonError(validation.error || 'Неизвестная ошибка валидации')
      return
    }

    setJsonError('') // Сбрасываем ошибку
    setLoading(true)

    try {
      const response = await fetch('/api/sandbox/test-pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          post_data: validation.data,
          options: {
            debug_mode: true,
            step_by_step: false
          }
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()

      setResult(result)
      // Сбросить фильтры при новом результате
      setLogSearchTerm('')
      setLogFilterType('all')
      setLogFilterSuccess('all')
    } catch (error) {
      console.error('Error testing sandbox:', error)
      setJsonError('Ошибка при тестировании песочницы: ' + (error instanceof Error ? error.message : String(error)))
    } finally {
      setLoading(false)
    }
  }

  // Функции пошагового выполнения
  const startStepByStepExecution = async () => {
    const validation = validatePostData(postData)
    if (!validation.isValid) {
      setJsonError(validation.error || 'Неизвестная ошибка валидации')
      return
    }

    setJsonError('')
    setStepByStepMode(true)
    setCurrentStep(0)
    setStepResults([])
    setCanExecuteNext(true)

    // Автоматически запускаем первый шаг
    await executeCurrentStep()
  }

  const executeCurrentStep = async () => {
    if (!canExecuteNext) return

    setLoading(true)
    try {
      const validation = validatePostData(postData)
      const stepData = {
        post_data: validation.data,
        options: {
          debug_mode: true,
          step_by_step: true,
          current_step: currentStep,
          previous_results: stepResults
        }
      }

      console.log('Отправляем на шаг:', currentStep + 1, stepData)

      const response = await fetch('/api/sandbox/test-pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(stepData)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()

      // Добавляем результат текущего шага
      const newStepResults = [...stepResults]
      newStepResults[currentStep] = result
      setStepResults(newStepResults)

      // Переходим к следующему шагу
      setCurrentStep(currentStep + 1)

      // Проверяем, можем ли выполнить следующий шаг
      setCanExecuteNext(result.success || currentStep < 2) // Можно продолжать даже при неудаче фильтрации

    } catch (error) {
      console.error('Error executing step:', error)
      setJsonError('Ошибка выполнения шага: ' + (error instanceof Error ? error.message : String(error)))
    } finally {
      setLoading(false)
    }
  }

  const resetStepByStepExecution = () => {
    setStepByStepMode(false)
    setCurrentStep(0)
    setStepResults([])
    setCanExecuteNext(false)
    setResult(null)
    setJsonError('')
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>🔧 Pipeline Sandbox</CardTitle>
        <p className="text-sm text-gray-600">
          Интерактивная среда для тестирования и отладки pipeline пост-сценарий
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Mode Selection */}
        <div className="flex items-center space-x-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center space-x-2">
            <input
              type="radio"
              id="normal_mode"
              name="execution_mode"
              checked={!stepByStepMode}
              onChange={() => setStepByStepMode(false)}
              className="text-blue-600"
            />
            <Label htmlFor="normal_mode" className="text-sm font-medium">
              Полный pipeline
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="radio"
              id="step_by_step_mode"
              name="execution_mode"
              checked={stepByStepMode}
              onChange={() => setStepByStepMode(true)}
              className="text-blue-600"
            />
            <Label htmlFor="step_by_step_mode" className="text-sm font-medium">
              Пошаговое выполнение
            </Label>
          </div>
        </div>

        {/* Post Selection */}
        <div>
          <Label className="text-sm font-medium mb-2 block">
            Выбрать существующий пост
          </Label>
          <div className="flex gap-2 mb-4">
            <Select value={selectedPostId} onValueChange={setSelectedPostId}>
              <SelectTrigger className="flex-1 min-w-[400px]">
                <SelectValue placeholder={loadingPosts ? "Загрузка постов..." : "Выберите пост из базы данных"} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Очистить выбор</SelectItem>
                {availablePosts.map((post: any) => {
                  const postDate = new Date(post.date || post.created_at).toLocaleDateString('ru-RU', {
                    day: '2-digit',
                    month: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                  });
                  const cleanText = post.text.replace(/^Post \d+ from @\w+/, '').trim();
                  const shortText = cleanText.length > 60 ? cleanText.substring(0, 60) + '...' : cleanText;
                  const displayText = cleanText ? shortText : '📝 Пост без текста';

                  return (
                    <SelectItem key={post.id} value={post.id}>
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{post.channel_title || post.channel_username}</span>
                          <span className="text-xs text-gray-500">#{post.message_id}</span>
                        </div>
                        <div className="text-xs text-gray-600 leading-tight">{displayText}</div>
                        <div className="flex items-center gap-3 text-xs text-gray-500">
                          <span>👁 {post.views?.toLocaleString() || 0}</span>
                          <span>📅 {postDate}</span>
                          <span>❤️ {post.reactions || 0}</span>
                        </div>
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              onClick={loadAvailablePosts}
              disabled={loadingPosts}
            >
              {loadingPosts ? '...' : '🔄'}
            </Button>
          </div>
        </div>

        {/* Post Data Input */}
        <div>
          <Label className="text-sm font-medium mb-2 block">
            Данные поста (JSON) {selectedPostId && <span className="text-green-600">- загружено из БД</span>}
          </Label>
          <Textarea
            placeholder={`Пример:
{
  "id": "12345_@dnevteh",
  "message_id": 12345,
  "channel_username": "@dnevteh",
  "text": "Текст поста для анализа",
  "views": 1000,
  "forwards": 50,
  "reactions": 25
}`}
            value={postData}
            onChange={(e) => setPostData(e.target.value)}
            className="min-h-[120px] font-mono text-sm"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <Button onClick={handleTestNew} disabled={loading || !postData.trim() || (stepByStepMode && !canExecuteNext && currentStep > 0)} className="flex-1">
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            ) : (
              <FlaskRound className="w-4 h-4 mr-2" />
            )}
            {loading ? 'Тестируем...' :
             stepByStepMode ?
               (currentStep === 0 && stepResults.length === 0 ? 'Начать пошаговое выполнение' :
                currentStep < 3 ? `Выполнить шаг ${currentStep + 1}` : 'Завершить') :
               'Запустить полный тест'}
          </Button>
          <Button variant="outline" onClick={() => setPostData('')}>
            Очистить
          </Button>
          {stepByStepMode && (
            <Button variant="secondary" onClick={resetStepByStepExecution} size="sm">
              Сбросить шаги
            </Button>
          )}
        </div>

        {/* Error Display */}
        {jsonError && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-2">
              <div className="text-red-600 text-sm font-medium">❌ Ошибка:</div>
              <div className="text-red-700 text-sm">{jsonError}</div>
            </div>
          </div>
        )}

        {/* Step-by-Step Progress Display */}
        {stepByStepMode && stepResults.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-medium mb-4">📋 Пошаговое выполнение</h3>

            {/* Progress indicator */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between mb-3">
                <div className="text-sm font-medium text-blue-800">
                  Прогресс: Шаг {currentStep} из 4
                </div>
                <div className="flex gap-1">
                  {[0, 1, 2, 3].map((step) => (
                    <div
                      key={step}
                      className={`w-3 h-3 rounded-full ${
                        step < currentStep
                          ? 'bg-green-500'
                          : step === currentStep - 1
                          ? 'bg-blue-500 animate-pulse'
                          : 'bg-gray-300'
                      }`}
                    />
                  ))}
                </div>
              </div>

              <div className="text-xs text-blue-700">
                {currentStep === 0 && 'Готов к началу'}
                {currentStep === 1 && '✅ Фильтрация выполнена'}
                {currentStep === 2 && '✅ Анализ выполнен'}
                {currentStep === 3 && '✅ Рубрикация выполнена'}
                {currentStep === 4 && '🎉 Pipeline завершен'}
              </div>
            </div>

            {/* Step Results */}
            <div className="space-y-4 mb-6">
              <h4 className="text-md font-medium">Результаты шагов</h4>
              {stepResults.map((stepResult, index) => (
                <div key={index} className="border rounded-lg p-4 bg-white">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <Badge variant={stepResult.success ? "default" : "secondary"}>
                        {stepResult.success ? "✅" : "❌"} Шаг {index + 1}
                      </Badge>
                      <span className="text-sm text-gray-500">
                        {stepResult.total_time || 0}s • {stepResult.total_tokens || 0} токенов
                      </span>
                    </div>
                    {stepResult.final_data && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => startEditingStep(index)}
                      >
                        ✏️ Редактировать
                      </Button>
                    )}
                  </div>

                  {/* Step Debug Log */}
                  {stepResult.debug_log && Array.isArray(stepResult.debug_log) && stepResult.debug_log.length > 0 && (
                    <div className="mt-3">
                      <h5 className="text-sm font-medium mb-2 text-gray-700">
                        📝 Лог шага {index + 1} ({stepResult.debug_log.length} записей)
                      </h5>
                      <div className="bg-gray-50 rounded p-3 max-h-40 overflow-y-auto">
                        {stepResult.debug_log.map((log: any, logIndex: number) => (
                          <div key={logIndex} className="text-xs mb-2 last:mb-0">
                            <div className="flex items-center space-x-2 mb-1">
                              <Badge variant="outline" className="text-xs">
                                {log.step_type || 'info'}
                              </Badge>
                              <span className="font-mono text-gray-600">
                                {log.step_name || `step_${logIndex + 1}`}
                              </span>
                              <span className="text-gray-400">
                                {(log.timestamp || 0).toFixed(3)}s
                              </span>
                            </div>
                            {log.data && (
                              <div className="bg-white p-2 rounded border text-gray-700 ml-4">
                                {log.step_type === 'prompts' ? (
                                  <div className="space-y-2">
                                    <div>
                                      <div className="font-medium text-purple-700 text-xs mb-1">🤖 System Prompt:</div>
                                      <div className="bg-purple-50 p-1 rounded text-xs font-mono whitespace-pre-wrap max-h-20 overflow-y-auto">
                                        {log.data?.system_prompt || 'N/A'}
                                      </div>
                                    </div>
                                    <div>
                                      <div className="font-medium text-blue-700 text-xs mb-1">👤 User Prompt:</div>
                                      <div className="bg-blue-50 p-1 rounded text-xs font-mono whitespace-pre-wrap max-h-20 overflow-y-auto">
                                        {log.data?.user_prompt || 'N/A'}
                                      </div>
                                    </div>
                                  </div>
                                ) : log.step_type === 'llm_response' && log.data?.raw_response ? (
                                  <div className="space-y-1">
                                    <div className="font-medium text-green-700 text-xs">📝 Raw LLM Response:</div>
                                    <div className="bg-green-50 p-1 rounded text-xs font-mono whitespace-pre-wrap max-h-20 overflow-y-auto">
                                      {log.data.raw_response}
                                    </div>
                                  </div>
                                ) : (
                                  <JsonHighlighter data={log.data} />
                                )}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Error display */}
                  {stepResult.error && (
                    <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded">
                      <div className="text-xs text-red-700">
                        <strong>Ошибка:</strong> {stepResult.error}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Results Display */}
        {result ? (
          <div className="mt-6">
            <h3 className="text-lg font-medium mb-4">Результаты тестирования</h3>
            {/* Debug: Show raw result data */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <h4 className="text-sm font-medium text-yellow-800 mb-2">🔍 Отладочная информация:</h4>
              <div className="text-xs text-yellow-700 space-y-1">
                <div>Result exists: {result ? '✅' : '❌'}</div>
                <div>Success: {result.success ? '✅' : '❌'}</div>
                <div>Debug log length: {result.debug_log?.length || 0}</div>
                <div>Debug log type: {typeof result.debug_log}</div>
                <div>Debug log is array: {Array.isArray(result.debug_log) ? '✅' : '❌'}</div>
                {result.error && <div>Error: {result.error}</div>}
              </div>
            </div>

            {/* Main Info */}
            <div className="bg-gray-50 rounded-lg p-4 space-y-3 mb-6">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Статус:</span>
                <Badge variant={result.success ? "default" : "secondary"}>
                  {result.success ? "✅ Успешно" : "❌ Ошибка"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Пост ID:</span>
                <code className="ml-2 bg-white px-2 py-1 rounded text-sm">{result.post_id}</code>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Токенов использовано:</span>
                <span className="text-sm text-gray-600">{result.total_tokens || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Время выполнения:</span>
                <span className="text-sm text-gray-600">{result.total_time || 0}s</span>
              </div>
            </div>

            {/* Pipeline Stages */}
            <div className="mb-6">
              <h4 className="text-md font-medium mb-3">Этапы pipeline</h4>
              <div className="space-y-2">
                {result.stages?.map((step: any) => (
                  <div key={step.step} className="border rounded-lg p-3 bg-white">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Badge variant={step.success ? "default" : "secondary"} className="text-xs">
                          {step.success ? "✅" : "❌"} {step.name}
                        </Badge>
                        <span className="text-xs text-gray-500">
                          {step.processing_time}s • {step.tokens_used} токенов
                        </span>
                      </div>
                    </div>
                    <div className="text-xs text-gray-600 mt-2">
                      {step.description}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Debug Log */}
            {result.debug_log && Array.isArray(result.debug_log) && result.debug_log.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-md font-medium">
                    Debug лог ({getFilteredLogs().length} из {result.debug_log.length} записей)
                  </h4>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={handleExportResults}>
                      <Download className="w-3 h-3 mr-1" />
                      Экспорт JSON
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setLogSearchTerm('')
                        setLogFilterType('all')
                        setLogFilterSuccess('all')
                      }}
                    >
                      Сбросить фильтры
                    </Button>
                  </div>
                </div>

                {/* Filter Panel */}
                <div className="bg-gray-50 rounded-lg p-3 mb-4 space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                      <Input
                        placeholder="Поиск по логам..."
                        value={logSearchTerm}
                        onChange={(e) => setLogSearchTerm(e.target.value)}
                        className="pl-9 text-sm"
                      />
                    </div>
                    <Select value={logFilterType} onValueChange={setLogFilterType}>
                      <SelectTrigger className="text-sm">
                        <SelectValue placeholder="Тип шага" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Все типы</SelectItem>
                        <SelectItem value="info">Информация</SelectItem>
                        <SelectItem value="llm_response">LLM ответ</SelectItem>
                        <SelectItem value="prompts">Промпты</SelectItem>
                        <SelectItem value="error">Ошибки</SelectItem>
                        <SelectItem value="db_operation">База данных</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select value={logFilterSuccess} onValueChange={setLogFilterSuccess}>
                      <SelectTrigger className="text-sm">
                        <SelectValue placeholder="Статус" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Все статусы</SelectItem>
                        <SelectItem value="success">Успешные</SelectItem>
                        <SelectItem value="failed">Неуспешные</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Log List */}
                <div className="border rounded-lg bg-white max-h-96 overflow-y-auto">
                  <div className="p-3 space-y-2">
                    {getFilteredLogs().length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        <Filter className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                        <p className="text-sm">Нет записей, соответствующих фильтрам</p>
                      </div>
                    ) : (
                      getFilteredLogs().map((log: any, index: number) => (
                        <div key={index} className="border-l-2 border-blue-200 pl-3 py-2">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-sm">{log.step_name}</span>
                            <div className="flex items-center space-x-2">
                              <Badge variant="outline" className="text-xs">
                                {log.step_type}
                              </Badge>
                              <span className="text-xs text-gray-500">
                                {(log.timestamp || 0).toFixed(3)}s
                              </span>
                            </div>
                          </div>
                          <div className="text-xs bg-gray-50 p-2 rounded border">
                            {log.step_type === 'prompts' ? (
                              <div className="space-y-3">
                                <div>
                                  <div className="font-medium text-purple-700 mb-1">🤖 System Prompt:</div>
                                  <div className="bg-purple-50 p-2 rounded text-xs font-mono whitespace-pre-wrap max-h-32 overflow-y-auto">
                                    {log.data?.system_prompt || 'N/A'}
                                  </div>
                                </div>
                                <div>
                                  <div className="font-medium text-blue-700 mb-1">👤 User Prompt:</div>
                                  <div className="bg-blue-50 p-2 rounded text-xs font-mono whitespace-pre-wrap max-h-32 overflow-y-auto">
                                    {log.data?.user_prompt || 'N/A'}
                                  </div>
                                </div>
                                {log.data?.model && (
                                  <div className="text-gray-600">
                                    <strong>Model:</strong> {log.data.model}
                                  </div>
                                )}
                              </div>
                            ) : log.step_type === 'llm_response' && log.data?.raw_response ? (
                              <div className="space-y-2">
                                <div className="font-medium text-green-700">📝 Raw LLM Response:</div>
                                <div className="bg-green-50 p-2 rounded text-xs font-mono whitespace-pre-wrap max-h-32 overflow-y-auto">
                                  {log.data.raw_response}
                                </div>
                                <div className="text-xs text-gray-600 mt-1">
                                  <JsonHighlighter data={log.data} />
                                </div>
                              </div>
                            ) : log.step_type === 'error' ? (
                              <div className="space-y-2">
                                <div className="font-medium text-red-700">❌ Ошибка:</div>
                                <div className="bg-red-50 border border-red-200 p-2 rounded text-xs">
                                  <div className="font-medium">Сообщение:</div>
                                  <div className="font-mono whitespace-pre-wrap mt-1">
                                    {log.data?.error || log.data?.message || 'Неизвестная ошибка'}
                                  </div>
                                  {log.data?.details && (
                                    <div className="mt-2">
                                      <div className="font-medium">Детали:</div>
                                      <div className="font-mono whitespace-pre-wrap mt-1 text-xs">
                                        {JSON.stringify(log.data.details, null, 2)}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            ) : log.step_type === 'db_operation' ? (
                              <div className="space-y-2">
                                <div className="font-medium text-green-700">💾 Операция с БД:</div>
                                <div className="bg-green-50 border border-green-200 p-2 rounded text-xs">
                                  <div className="font-medium">Операция: {log.data?.operation}</div>
                                  {log.data?.scenarios_count && (
                                    <div className="mt-1">Сценариев: {log.data.scenarios_count}</div>
                                  )}
                                  {log.data?.stage && (
                                    <div className="mt-1">Этап: {log.data.stage}</div>
                                  )}
                                  {log.data?.post_id && (
                                    <div className="mt-1">Пост: {log.data.post_id}</div>
                                  )}
                                  <div className="mt-2">
                                    <div className="font-medium">Данные:</div>
                                    <div className="font-mono whitespace-pre-wrap mt-1 text-xs max-h-32 overflow-y-auto">
                                      {JSON.stringify(log.data.data || log.data, null, 2)}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            ) : (
                              <JsonHighlighter data={log.data} />
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Fallback: Show debug log info even if empty */}
            {(!result.debug_log || !Array.isArray(result.debug_log) || result.debug_log.length === 0) && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
                <h4 className="text-sm font-medium text-blue-800 mb-2">📋 Debug лог (пустой или отсутствует)</h4>
                <div className="text-xs text-blue-700 space-y-1">
                  <div>Debug log: {result.debug_log ? 'существует' : '❌ отсутствует'}</div>
                  <div>Type: {typeof result.debug_log}</div>
                  <div>Is Array: {Array.isArray(result.debug_log) ? '✅' : '❌'}</div>
                  <div>Length: {result.debug_log?.length || 0}</div>
                  {result.debug_log && !Array.isArray(result.debug_log) && (
                    <div className="mt-2">
                      <strong>Raw content:</strong>
                      <pre className="mt-1 bg-white p-2 rounded text-xs overflow-auto max-h-32 border">
                        {JSON.stringify(result.debug_log, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-800 mb-2">📊 Результаты тестирования</h4>
            <div className="text-xs text-gray-600">
              <div>Result state: {result ? 'установлен' : '❌ не установлен'}</div>
              <div>Ожидание завершения теста...</div>
            </div>
          </div>
        )}

        {/* Edit Step Modal */}
        <EditStepModal
          isOpen={editingStep !== null}
          onClose={() => setEditingStep(null)}
          stepIndex={editingStep || 0}
          initialData={editingStep !== null ? stepResults[editingStep]?.final_data : null}
          onSave={handleSaveEditedData}
        />
      </CardContent>
    </Card>
  )
}
