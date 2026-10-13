import { expect, test } from '@playwright/test';

test('managed threads persist, switch, cancel and delete', async ({ page, request }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'New Thread' }).click();
    const input = page.getByRole('textbox');
    await input.fill('First conversation');
    await input.press('Enter');
    await expect(page.getByText('Hello from Spaik.', { exact: false }).first()).toBeVisible();
    await expect(input).toBeEnabled();
    await page.reload();
    await page.getByText('First conversation', { exact: true }).click();
    await expect(page.getByText('Hello from Spaik.', { exact: false }).first()).toBeVisible();
    await page.getByRole('button', { name: 'New Thread' }).click();
    await expect(page.getByText('Start a conversation...')).toBeVisible();
    await input.fill('Second conversation');
    await input.press('Enter');
    await page.getByRole('button', { name: 'Stop generation' }).click();
    await expect(input).toBeEnabled();
    const threads = await (await request.get('http://localhost:8000/threads')).json();
    const second = threads.threads.find((t: { title: string }) => t.title === 'Second conversation');
    expect(second).toBeTruthy();
    await request.delete(`http://localhost:8000/threads/${second.thread_id}`);
    await page.reload();
    await expect(page.getByText('Second conversation', { exact: true })).toHaveCount(0);
});

test('independent AG-UI agent renders tools, reasoning and state without a sidebar', async ({ page }) => {
    await page.goto('/?agent=http://localhost:8000/external');
    await expect(page.getByRole('button', { name: 'New Thread' })).toHaveCount(0);
    const input = page.getByRole('textbox');
    await input.fill('Hello independent agent');
    await input.press('Enter');
    await expect(page.getByText('Independent AG-UI response')).toBeVisible();
    await expect(page.getByText('weather', { exact: true })).toBeVisible();
    await page.getByText('View Reasoning').click();
    await expect(page.getByText('External reasoning summary')).toBeVisible();
    await page.getByText('State', { exact: true }).click();
    await expect(page.getByText('"progress": "done"', { exact: false })).toBeVisible();
});

test('attachment upload and speech controls remain usable', async ({ page }) => {
    // Use a real browser MediaStream/MediaRecorder without depending on host microphone hardware.
    await page.addInitScript(() => {
        navigator.mediaDevices.getUserMedia = async () => {
            const context = new AudioContext();
            const destination = context.createMediaStreamDestination();
            const source = context.createOscillator();
            source.connect(destination);
            source.start();
            await context.resume();
            return destination.stream;
        };
    });
    await page.goto('/');
    await page.getByRole('button', { name: 'New Thread' }).click();
    await expect(page.getByRole('textbox')).toBeVisible();
    const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aRk0AAAAASUVORK5CYII=', 'base64');
    await page.locator('input[type=file]').setInputFiles({ name: 'test.png', mimeType: 'image/png', buffer: png });
    await expect(page.getByText('test.png')).toBeVisible();
    const input = page.getByRole('textbox');
    await input.fill('Describe attachment');
    await input.press('Enter');
    await expect(page.getByRole('img', { name: 'test.png' })).toBeVisible();
    await expect(input).toBeEnabled();
    const speech = page.waitForResponse(response => response.url().endsWith('/audio/speech'));
    await page.getByRole('button', { name: 'Listen', exact: true }).click();
    expect((await speech).status()).toBe(200);
    await page.getByRole('button', { name: 'Start recording' }).click();
    await expect(page.getByRole('button', { name: 'Stop recording' })).toBeVisible();
    await page.getByRole('button', { name: 'Stop recording' }).click();
    await expect(page.getByText('Transcribed test audio', { exact: true })).toBeVisible();
});
