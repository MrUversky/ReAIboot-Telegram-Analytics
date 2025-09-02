'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'
import { supabase } from '@/lib/supabase'
import { useSupabase } from '@/components/SupabaseProvider'

export default function AuthPage() {
  const router = useRouter()
  const { user, loading } = useSupabase()

  useEffect(() => {
    if (user) {
      router.push('/')
    }
  }, [user, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (user) {
    return null // Will redirect
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100">
            <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Вход в ReAIboot
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Автоматизированный анализ Telegram для контент-маркетинга
          </p>
        </div>

        <div className="bg-white py-8 px-6 shadow rounded-lg">
          <Auth
            supabaseClient={supabase}
            appearance={{
              theme: ThemeSupa,
              variables: {
                default: {
                  colors: {
                    brand: '#2563eb',
                    brandAccent: '#1d4ed8',
                  },
                },
              },
            }}
            providers={['google', 'github']}
            redirectTo={`${window.location.origin}/auth/callback`}
            localization={{
              variables: {
                sign_in: {
                  email_label: 'Email',
                  password_label: 'Пароль',
                  button_label: 'Войти',
                  loading_button_label: 'Вход...',
                  social_provider_text: 'Войти через {{provider}}',
                  link_text: 'Уже есть аккаунт? Войти',
                  confirmation_text: 'Проверьте email для подтверждения',
                },
                sign_up: {
                  email_label: 'Email',
                  password_label: 'Пароль',
                  button_label: 'Регистрация',
                  loading_button_label: 'Регистрация...',
                  social_provider_text: 'Регистрация через {{provider}}',
                  link_text: 'Нет аккаунта? Зарегистрироваться',
                  confirmation_text: 'Проверьте email для подтверждения',
                },
              },
            }}
          />
        </div>
      </div>
    </div>
  )
}
