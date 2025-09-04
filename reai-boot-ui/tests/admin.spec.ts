import { test, expect } from '@playwright/test'

test.describe('Admin UI Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Переходим на страницу админки
    await page.goto('http://localhost:3000/admin')
  })

  test('should load admin page', async ({ page }) => {
    // Проверяем заголовок страницы
    await expect(page.locator('h1').filter({ hasText: 'Админ панель' })).toBeVisible()
  })

  test('should show LLM settings button', async ({ page }) => {
    // Проверяем наличие кнопки настроек LLM
    const llmButton = page.locator('button').filter({ hasText: 'Настройки LLM' })
    await expect(llmButton).toBeVisible()
  })

  test('should open LLM modal', async ({ page }) => {
    // Нажимаем кнопку настроек LLM
    await page.locator('button').filter({ hasText: 'Настройки LLM' }).click()

    // Проверяем открытие модального окна
    const modal = page.locator('[class*="fixed"][class*="inset-0"]')
    await expect(modal).toBeVisible()

    // Проверяем заголовок модального окна
    await expect(page.locator('h2').filter({ hasText: 'Настройки LLM Пайплайна' })).toBeVisible()
  })

  test('should show prompts tab', async ({ page }) => {
    // Открываем модальное окно LLM
    await page.locator('button').filter({ hasText: 'Настройки LLM' }).click()

    // Проверяем вкладку промптов
    const promptsTab = page.locator('button').filter({ hasText: 'Промпты' })
    await expect(promptsTab).toBeVisible()
  })

  test('should show rubrics tab', async ({ page }) => {
    // Открываем модальное окно LLM
    await page.locator('button').filter({ hasText: 'Настройки LLM' }).click()

    // Проверяем вкладку рубрик
    const rubricsTab = page.locator('button').filter({ hasText: 'Рубрики' })
    await expect(rubricsTab).toBeVisible()
  })

  test('should show formats tab', async ({ page }) => {
    // Открываем модальное окно LLM
    await page.locator('button').filter({ hasText: 'Настройки LLM' }).click()

    // Проверяем вкладку форматов
    const formatsTab = page.locator('button').filter({ hasText: 'Форматы' })
    await expect(formatsTab).toBeVisible()
  })

  test('should close LLM modal', async ({ page }) => {
    // Открываем модальное окно
    await page.locator('button').filter({ hasText: 'Настройки LLM' }).click()

    // Закрываем модальное окно
    await page.locator('button').filter({ hasText: 'Закрыть' }).click()

    // Проверяем что модальное окно закрылось
    const modal = page.locator('[class*="fixed"][class*="inset-0"]')
    await expect(modal).not.toBeVisible()
  })
})

test.describe('API Health Tests', () => {
  test('should check backend health', async ({ page }) => {
    // Делаем запрос к health endpoint
    const response = await page.request.get('http://localhost:8000/health')
    expect(response.status()).toBe(200)

    const data = await response.json()
    expect(data.status).toBe('ok')
  })

  test('should check API docs availability', async ({ page }) => {
    // Проверяем доступность API документации
    const response = await page.request.get('http://localhost:8000/docs')
    expect(response.status()).toBe(200)
  })
})
