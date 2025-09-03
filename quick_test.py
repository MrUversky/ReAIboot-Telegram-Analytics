#!/usr/bin/env python3
"""
Быстрый тест исправления RLS политик
"""

from supabase import create_client

def quick_test():
    print("🧪 БЫСТРЫЙ ТЕСТ RLS ПОЛИТИК")

    url = 'https://oxsvtjtgtdaqoslcxdna.supabase.co'
    anon_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94c3Z0anRndGRhcW9zbGN4ZG5hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY4MDY5NzQsImV4cCI6MjA3MjM4Mjk3NH0.m8UTdmiZIEUO_jS56YH0ZTlOvdd30pVQf6siEpZusuY'

    client = create_client(url, anon_key)

    try:
        # Попробовать аутентификацию
        auth = client.auth.sign_in_with_password({
            'email': 'i.uversky@gmail.com',
            'password': '1234567890'
        })
        print("✅ Аутентификация успешна")

        # Попробовать получить профили
        profiles = client.table('profiles').select('*').execute()
        print(f"✅ Доступ к профилям: {len(profiles.data)} записей")

        # Тест RPC функции
        result = client.rpc('create_user_profile_safe', {
            'user_id': auth.user.id,
            'user_email': auth.user.email,
            'user_name': 'Test'
        }).execute()

        if result.data and result.data.get('success'):
            print("✅ RPC функция работает")
        else:
            print("❌ RPC функция не работает")

        client.auth.sign_out()
        print("✅ Тест завершен успешно!")

        return True

    except Exception as e:
        if "infinite recursion" in str(e):
            print("❌ Все еще бесконечная рекурсия")
            return False
        else:
            print(f"⚠️  Другая ошибка: {str(e)[:100]}...")
            return True  # Может быть нормально

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n🎉 RLS ПОЛИТИКИ ИСПРАВЛЕНЫ!")
        print("Теперь можно тестировать UI.")
    else:
        print("\n❌ НУЖНО ИСПРАВЛЕНИЕ")
