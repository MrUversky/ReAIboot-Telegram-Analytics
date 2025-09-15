'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { apiClient } from '@/lib/api'
import toast from 'react-hot-toast'
import { TrendingUp, Send, Bot, Calendar, History } from 'lucide-react'

interface ReportData {
  success: boolean
  report?: string
  posts_count?: number
  analysis?: any
  bot_sent?: boolean | { success: boolean, parts_sent?: number, total_parts?: number, message?: string }
  bot_error?: string
}

export default function ReportsPage() {
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<ReportData | null>(null)
  const [userSettings, setUserSettings] = useState<any>(null)
  const [loadingSettings, setLoadingSettings] = useState(false)

  // Форма для генерации отчета
  const [reportForm, setReportForm] = useState({
    days: 7,
    minViralScore: 1.0,
    channelUsername: '',
    sendToBot: false,
    botToken: process.env.NEXT_PUBLIC_TELEGRAM_BOT_TOKEN || '',
    chatId: ''
  })

  // Загружаем настройки пользователя при выборе отправки в бота
  const loadUserSettings = async () => {
    if (userSettings) return // Уже загружены

    setLoadingSettings(true)
    try {
      const response = await apiClient.getNotificationSettings()
      if (response.success && response.data) {
        setUserSettings(response.data)
        setReportForm(prev => ({
          ...prev,
          chatId: response.data?.chat_id || ''
        }))
      }
    } catch (error) {
      console.error('Error loading user settings:', error)
    } finally {
      setLoadingSettings(false)
    }
  }

  // Автоматически загружаем настройки при монтировании
  useEffect(() => {
    if (reportForm.sendToBot && !userSettings) {
      loadUserSettings()
    }
  }, [reportForm.sendToBot])


  const handleGenerateReport = async () => {
    setLoading(true)
    try {
      const response = await apiClient.generateViralReport(reportForm)

      if (response.success && response.data) {
        setReport(response.data)
        toast.success('Отчет сгенерирован успешно!')

        // Проверяем отправку в бота
        if (reportForm.sendToBot) {
          const botResult = response.data.bot_sent
          if (botResult) {
            // botResult может быть boolean или объектом
            if (typeof botResult === 'boolean' && botResult) {
              toast.success('Отчет отправлен в Telegram!')
            } else if (typeof botResult === 'object' && botResult.success) {
              const partsText = botResult.parts_sent && botResult.total_parts && botResult.parts_sent > 1
                ? ` (${botResult.parts_sent}/${botResult.total_parts} частей)`
                : ''
              toast.success(`Отчет отправлен в Telegram${partsText}!`)
            } else {
              const errorMsg = (typeof botResult === 'object' && botResult.message)
                ? botResult.message
                : (response.data.bot_error || 'Неизвестная ошибка')
              toast.error(`Ошибка отправки в Telegram: ${errorMsg}`)
            }
          } else {
            toast.error(`Ошибка отправки в Telegram: ${response.data.bot_error || 'Неизвестная ошибка'}`)
          }
        }
      } else {
        toast.error(response.message || 'Ошибка при генерации отчета')
      }
    } catch (error: any) {
      console.error('Report generation error:', error)
      toast.error(error.message || 'Ошибка при генерации отчета')
    } finally {
      setLoading(false)
    }
  }


  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2">
        <TrendingUp className="w-6 h-6" />
        <h1 className="text-2xl font-bold">Генерация отчетов</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Генерация отчета */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Calendar className="w-5 h-5" />
              <span>Анализ виральных постов</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="days">Период анализа (дни)</Label>
                <Select
                  value={reportForm.days.toString()}
                  onValueChange={(value) => setReportForm({...reportForm, days: parseInt(value)})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 день</SelectItem>
                    <SelectItem value="3">3 дня</SelectItem>
                    <SelectItem value="7">7 дней</SelectItem>
                    <SelectItem value="14">14 дней</SelectItem>
                    <SelectItem value="30">30 дней</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="minViralScore">Минимальный Viral Score</Label>
                <Input
                  id="minViralScore"
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="10.0"
                  value={reportForm.minViralScore}
                  onChange={(e) => setReportForm({...reportForm, minViralScore: parseFloat(e.target.value)})}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="channelUsername">Канал (опционально)</Label>
              <Input
                id="channelUsername"
                placeholder="username канала"
                value={reportForm.channelUsername}
                onChange={(e) => setReportForm({...reportForm, channelUsername: e.target.value})}
              />
            </div>

            {/* Telegram бот настройки */}
            <div className="space-y-4 border-t pt-4">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="sendToBot"
                  checked={reportForm.sendToBot}
                  onChange={async (e) => {
                    const checked = e.target.checked
                    setReportForm({...reportForm, sendToBot: checked})
                    if (checked) {
                      await loadUserSettings()
                    }
                  }}
                />
                <Label htmlFor="sendToBot" className="flex items-center space-x-2">
                  <Bot className="w-4 h-4" />
                  <span>Отправить в Telegram бота</span>
                </Label>
              </div>

              {reportForm.sendToBot && (
                <div className="grid grid-cols-1 gap-4">
                  <div>
                    <Label htmlFor="botToken">Bot Token (из .env)</Label>
                    <Input
                      id="botToken"
                      value={reportForm.botToken}
                      readOnly
                      className="bg-gray-50"
                      placeholder="Токен берется из файла .env"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Токен бота хранится в файле .env и не может быть изменен здесь
                    </p>
                  </div>
                  <div>
                    <Label htmlFor="chatId">
                      Chat ID
                      {loadingSettings && <span className="ml-2 text-sm text-blue-500">Загрузка...</span>}
                    </Label>
                    <Input
                      id="chatId"
                      value={reportForm.chatId}
                      onChange={(e) => setReportForm({...reportForm, chatId: e.target.value})}
                      placeholder="Ваш Chat ID из настроек уведомлений"
                    />
                    {!userSettings && !loadingSettings && (
                      <p className="text-xs text-amber-600 mt-1">
                        ⚠️ Настройки не загружены. Укажите Chat ID или настройте уведомления в разделе "Уведомления"
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>

                    <Button
                      onClick={handleGenerateReport}
                      disabled={loading || (reportForm.sendToBot && !reportForm.chatId)}
                      className="w-full"
                    >
                      {loading ? 'Генерирую отчет...' : 'Сгенерировать отчет'}
                      <Send className="w-4 h-4 ml-2" />
                    </Button>

                    {reportForm.sendToBot && !reportForm.chatId && !loadingSettings && (
                      <p className="text-sm text-amber-600 mt-2">
                        ⚠️ Chat ID не загружен. Попробуйте снять и поставить галочку "Отправить в Telegram бота"
                      </p>
                    )}
          </CardContent>
        </Card>

      </div>

      {/* Превью отчета */}
      {report && report.success && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Bot className="w-5 h-5" />
              <span>Сгенерированный отчет</span>
              {report.bot_sent && (
                <span className="text-sm text-green-600 font-normal">
                  ✓ Отправлен в Telegram
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {report.report && (
              <div
                className="whitespace-pre-wrap text-sm bg-gray-50 p-4 rounded-lg border max-h-96 overflow-y-auto"
                dangerouslySetInnerHTML={{ __html: report.report.replace(/\n/g, '<br>') }}
              />
            )}

            {report.analysis && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-900 mb-2">Анализ от ИИ:</h4>
                <p className="text-sm text-blue-800">{report.analysis.summary}</p>
                {report.analysis.recommendations && report.analysis.recommendations.length > 0 && (
                  <div className="mt-2">
                    <h5 className="font-medium text-blue-900">Рекомендации:</h5>
                    <ul className="text-sm text-blue-800 list-disc list-inside">
                      {report.analysis.recommendations.map((rec: string, index: number) => (
                        <li key={index}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* История отчетов */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <History className="w-5 h-5" />
            <span>История отчетов</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-gray-500 py-8">
            История отчетов пока не реализована
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
