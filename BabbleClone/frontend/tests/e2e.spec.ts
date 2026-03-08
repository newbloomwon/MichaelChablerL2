import { test, expect } from '@playwright/test'

test('navigates from splash to home to lesson', async ({ page }) => {
  await page.goto('/')

  // Splash page shows welcome message
  await expect(page.getByText('Welcome to LingoVision')).toBeVisible()

  // Click "Start Unit" to go to home
  await page.getByRole('button', { name: /Start Unit/i }).click()
  await expect(page).toHaveURL(/\/home/)

  // Home page shows lesson heading and lesson card
  await expect(page.getByRole('heading', { name: 'Learn Spanish' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Vocabulary Lesson' })).toBeVisible()

  // Click lesson card to go to day-two
  await page.getByRole('heading', { name: 'Vocabulary Lesson' }).click()
  await expect(page).toHaveURL(/\/day-two/)
})
