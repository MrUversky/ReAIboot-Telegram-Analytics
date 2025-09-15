'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { apiClient } from '@/lib/api'
import toast from 'react-hot-toast'
import { Bot, Settings, TestTube, History, Save } from 'lucide-react'

interface NotificationSettings {
  bot_name: string
  chat_id: string
  is_active: boolean
}

export default function NotificationsPage() {
  const [loading, setLoading] = useState(false)
  const [testingBot, setTestingBot] = useState(false)
  const [settings, setSettings] = useState<NotificationSettings>({
    bot_name: '',
    chat_id: '',
    is_active: true
  })

  // Загрузка настроек при монтировании
  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const response = await apiClient.getNotificationSettings()
      if (response.success && response.data) {
        setSettings(response.data)
      }
    } catch (error) {
      console.error('Error loading settings:', error)
    }
  }

  const handleSaveSettings = async () => {
    setLoading(true)
    try {
      const response = await apiClient.saveNotificationSettings(settings)

      if (response.success) {
        toast.success('Настройки сохранены!')
      } else {
        toast.error(response.message || 'Ошибка сохранения')
      }
    } catch (error: any) {
      console.error('Error saving settings:', error)
      toast.error(error.message || 'Ошибка сохранения настроек')
    } finally {
      setLoading(false)
    }
  }

  const handleTestBot = async () => {
    if (!settings.chat_id) {
      toast.error('Сначала получите Chat ID')
      return
    }

    setTestingBot(true)
    try {
      const response = await apiClient.testBotConnection({
        chatId: settings.chat_id,
        saveToDb: true
      })

      if (response.success) {
        toast.success('Бот протестирован успешно!')
        // Перезагрузить настройки, если chat_id был получен
        await loadSettings()
      } else {
        toast.error(response.message || 'Ошибка тестирования бота')
      }
    } catch (error: any) {
      console.error('Bot test error:', error)
      toast.error(error.message || 'Ошибка тестирования бота')
    } finally {
      setTestingBot(false)
    }
  }

  const getChatId = async () => {
    setLoading(true)
    try {
      const response = await apiClient.getChatIdFromBot()

      if (response.success && response.chat_id) {
        setSettings({...settings, chat_id: response.chat_id})
        toast.success('Chat ID успешно получен!')
      } else {
        toast.error(response.message || 'Не удалось получить Chat ID')
      }
    } catch (error: any) {
      console.error('Error getting chat ID:', error)
      toast.error(error.message || 'Ошибка получения Chat ID')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2">
        <Bot className="w-6 h-6" />
        <h1 className="text-2xl font-bold">Уведомления</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Настройки бота */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings className="w-5 h-5" />
              <span>Настройки Telegram бота</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
              <div className="flex items-center space-x-2">
                <Bot className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-800">Bot Token</span>
              </div>
              <p className="text-sm text-blue-700 mt-1">
                Токен бота берется из файла .env (TELEGRAM_BOT_TOKEN)
              </p>
            </div>

            <div>
              <Label htmlFor="botName">Имя бота (опционально)</Label>
              <Input
                id="botName"
                value={settings.bot_name}
                onChange={(e) => setSettings({...settings, bot_name: e.target.value})}
                placeholder="iivka_bot"
              />
            </div>

            <div>
              <Label htmlFor="chatId">Chat ID</Label>
              <div className="flex space-x-2">
                <Input
                  id="chatId"
                  value={settings.chat_id}
                  onChange={(e) => setSettings({...settings, chat_id: e.target.value})}
                  placeholder="Ваш Chat ID"
                  className="flex-1"
                />
                <Button
                  onClick={getChatId}
                  variant="outline"
                  size="sm"
                  disabled={loading}
                >
                  {loading ? 'Получение...' : 'Получить'}
                </Button>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                ID чата, куда будут отправляться уведомления
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="isActive"
                checked={settings.is_active}
                onCheckedChange={(checked) => setSettings({...settings, is_active: checked})}
              />
              <Label htmlFor="isActive">Включить уведомления</Label>
            </div>

            <div className="flex space-x-2">
              <Button
                onClick={handleSaveSettings}
                disabled={loading}
                className="flex-1"
              >
                {loading ? 'Сохранение...' : 'Сохранить'}
                <Save className="w-4 h-4 ml-2" />
              </Button>

              <Button
                onClick={handleTestBot}
                disabled={testingBot || !settings.chat_id}
                variant="outline"
              >
                {testingBot ? 'Тестирую...' : 'Протестировать'}
                <TestTube className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Инструкции */}
        <Card>
          <CardHeader>
            <CardTitle>Как настроить</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">1. Настройка токена бота</h4>
              <p className="text-sm text-gray-600 mb-2">
                Токен бота должен быть указан в файле <code>.env</code> как <code>TELEGRAM_BOT_TOKEN</code>
              </p>
              <div className="bg-gray-50 p-3 rounded-md text-sm font-mono">
                TELEGRAM_BOT_TOKEN=8364173996:AAH2BFSuA_cN7JHQ5Gds5O3MNS-KXxpK0wE
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-2">2. Получить Chat ID</h4>
              <ol className="text-sm text-gray-600 space-y-1 ml-4">
                <li>• Написать любое сообщение боту @iivka_bot в Telegram</li>
                <li>• Нажать кнопку "Получить" рядом с полем Chat ID</li>
                <li>• Chat ID автоматически заполнится</li>
              </ol>
            </div>

            <div>
              <h4 className="font-semibold mb-2">3. Тестирование</h4>
              <ul className="text-sm text-gray-600 space-y-1 ml-4">
                <li>• Сохранить настройки</li>
                <li>• Нажать "Протестировать" - придет сообщение в Telegram</li>
                <li>• Проверить генерацию отчетов на странице /reports</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* История уведомлений */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <History className="w-5 h-5" />
            <span>История уведомлений</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-gray-500 py-8">
            История уведомлений пока не реализована
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
