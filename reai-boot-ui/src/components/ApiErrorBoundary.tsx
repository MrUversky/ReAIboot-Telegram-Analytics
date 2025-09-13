'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'

interface ApiErrorBoundaryProps {
  children: React.ReactNode
}

export function ApiErrorBoundary({ children }: ApiErrorBoundaryProps) {
  const [apiError, setApiError] = useState<string | null>(null)
  const [isRetrying, setIsRetrying] = useState(false)

  useEffect(() => {
    // Проверяем подключение к API только в development
    if (process.env.NODE_ENV === 'development') {
      const checkApiConnection = async () => {
        try {
          await apiClient.healthCheck()
          setApiError(null)
        } catch (error) {
          console.error('API connection error:', error)

          if (error instanceof Error) {
            setApiError(error.message)
          } else {
            setApiError('Не удается подключиться к API серверу')
          }
        }
      }

      checkApiConnection()
    }
  }, [])

  const retryConnection = async () => {
    setIsRetrying(true)
    setApiError(null)

    try {
      await apiClient.healthCheck()
      setApiError(null)
    } catch (error) {
      if (error instanceof Error) {
        setApiError(error.message)
      } else {
        setApiError('Не удается подключиться к API серверу')
      }
    }

    setIsRetrying(false)
  }

  if (apiError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-6">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>

            <h3 className="mt-4 text-lg font-medium text-gray-900">
              Проблема с подключением к API
            </h3>

            <p className="mt-2 text-sm text-gray-600">
              {apiError}
            </p>

            <div className="mt-6 space-y-3">
              <button
                onClick={retryConnection}
                disabled={isRetrying}
                className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {isRetrying ? 'Проверяем...' : 'Повторить подключение'}
              </button>

              <div className="text-xs text-gray-500 space-y-1">
                <p><strong>Возможные решения:</strong></p>
                <ul className="text-left list-disc list-inside space-y-1">
                  <li>Убедитесь что backend запущен: <code>./scripts/start_project.sh</code></li>
                  <li>Если используете Firefox - попробуйте приватный режим</li>
                  <li>Отключите Enhanced Tracking Protection в Firefox</li>
                  <li>Проверьте что API доступен: <code>curl http://localhost:8000/health</code></li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
