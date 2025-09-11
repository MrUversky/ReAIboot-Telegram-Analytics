import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { X, Edit, Check } from 'lucide-react'

interface EditStepModalProps {
  isOpen: boolean
  onClose: () => void
  stepIndex: number
  initialData: any
  onSave: (data: any) => void
}

export const EditStepModal: React.FC<EditStepModalProps> = ({
  isOpen,
  onClose,
  stepIndex,
  initialData,
  onSave
}) => {
  const [jsonData, setJsonData] = useState('')
  const [error, setError] = useState('')

  React.useEffect(() => {
    if (isOpen && initialData) {
      setJsonData(JSON.stringify(initialData, null, 2))
      setError('')
    }
  }, [isOpen, initialData])

  const handleSave = () => {
    try {
      const parsed = JSON.parse(jsonData)
      onSave(parsed)
      onClose()
    } catch (err) {
      setError('Некорректный JSON формат')
    }
  }

  const handleCancel = () => {
    setJsonData('')
    setError('')
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <Edit className="w-6 h-6 mr-2 text-blue-500" />
              Редактирование данных шага {stepIndex + 1}
            </h2>
            <Button variant="outline" onClick={handleCancel}>
              <X className="w-4 h-4" />
            </Button>
          </div>

          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium mb-2 block">
                Данные для следующего шага (JSON)
              </Label>
              <Textarea
                value={jsonData}
                onChange={(e) => {
                  setJsonData(e.target.value)
                  setError('')
                }}
                className="min-h-[400px] font-mono text-sm"
                placeholder="Введите JSON данные..."
              />
              {error && (
                <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded border border-red-200">
                  <strong>Ошибка:</strong> {error}
                </div>
              )}
            </div>

            <div className="flex gap-2">
              <Button onClick={handleSave} className="flex-1">
                <Check className="w-4 h-4 mr-2" />
                Сохранить изменения
              </Button>
              <Button variant="outline" onClick={handleCancel}>
                Отмена
              </Button>
            </div>

            <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-800">
                <strong>💡 Совет:</strong> Измените данные, которые будут переданы следующему шагу pipeline.
                Это позволит протестировать различные сценарии и отладить поведение системы.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
