-- RPC функция для создания профилей пользователей
-- Выполнить в Supabase SQL Editor

-- Создаем функцию для создания профиля с service role правами
CREATE OR REPLACE FUNCTION create_user_profile(
  user_id UUID,
  user_email TEXT,
  user_name TEXT DEFAULT ''
)
RETURNS JSON AS $$
DECLARE
  result JSON;
  existing_profile RECORD;
BEGIN
  -- Проверяем, существует ли уже профиль
  SELECT * INTO existing_profile
  FROM public.profiles
  WHERE id = user_id;

  -- Если профиль существует, возвращаем его
  IF existing_profile.id IS NOT NULL THEN
    result := json_build_object(
      'success', true,
      'message', 'Profile already exists',
      'profile', row_to_json(existing_profile)
    );
    RETURN result;
  END IF;

  -- Создаем новый профиль
  INSERT INTO public.profiles (
    id,
    email,
    full_name,
    role,
    is_active,
    created_at,
    updated_at
  ) VALUES (
    user_id,
    user_email,
    COALESCE(user_name, ''),
    'user'::user_role,
    true,
    NOW(),
    NOW()
  );

  -- Возвращаем созданный профиль
  SELECT json_build_object(
    'success', true,
    'message', 'Profile created successfully',
    'profile', json_build_object(
      'id', user_id,
      'email', user_email,
      'full_name', COALESCE(user_name, ''),
      'role', 'user',
      'is_active', true,
      'created_at', NOW(),
      'updated_at', NOW()
    )
  ) INTO result;

  RETURN result;

EXCEPTION
  WHEN OTHERS THEN
    -- В случае ошибки возвращаем информацию об ошибке
    RETURN json_build_object(
      'success', false,
      'message', SQLERRM,
      'error_code', SQLSTATE
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Предоставляем права на выполнение функции
GRANT EXECUTE ON FUNCTION create_user_profile(UUID, TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION create_user_profile(UUID, TEXT, TEXT) TO anon;

-- Тестируем функцию
-- SELECT create_user_profile('test-user-id'::UUID, 'test@example.com', 'Test User');
