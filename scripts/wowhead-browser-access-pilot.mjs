import { chromium } from 'playwright';
import { createHash } from 'node:crypto';

const GUIDE_URL = 'https://www.wowhead.com/guide/classes/shaman/enhancement/rotation-cooldowns-pve-dps';
const record = {
  probe: 'one-page-browser-ui-access',
  browser: 'chromium',
  content_republished: false,
  original_guide_html_saved: false,
  target: 'wowhead/enhancement/rotation',
};
let browser;
try {
  browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1365, height: 850 }, locale: 'en-US' });
  const page = await context.newPage();
  const response = await page.goto(GUIDE_URL, { waitUntil: 'domcontentloaded', timeout: 40000 });
  await page.waitForTimeout(2000);
  const body = (await page.locator('body').innerText({ timeout: 15000 })).slice(0, 500000);
  const title = await page.title();
  const challenge = /just a moment|verify you are human|access denied|captcha|attention required/i.test(title + ' ' + body.slice(0, 500));
  record.http_status = response?.status() ?? null;
  record.page_url_is_wowhead = new URL(page.url()).hostname.endsWith('wowhead.com');
  record.body_chars = body.length;
  record.text_sha256_prefix = createHash('sha256').update(body).digest('hex').slice(0, 16);
  record.challenge_detected = challenge;
  record.has_enhancement = /Enhancement|고양/i.test(body);
  record.has_stormbringer = /Stormbringer|폭풍인도자/i.test(body);
  record.has_totemic = /Totemic|토템술사/i.test(body);
  record.has_further_or_notes = /Further Details|Advanced|Notes/i.test(body);
  record.has_12_1_5 = /12\.1\.5/.test(body);
  record.has_12_0_7 = /12\.0\.7/.test(body);
  record.tab_count = await page.locator('[role="tab"]').count();
  record.details_count = await page.locator('details, [aria-expanded]').count();
  record.buttons_count = await page.locator('button, [role="button"]').count();
  record.tooltip_attribute_count = await page.locator('[aria-describedby], [data-tooltip], [data-tippy-content]').count();
  record.visible_question_count = await page.getByText('?', { exact: true }).count();
  // Only count the visible controls; no user-authored or source content leaves the runner.
  const question = page.getByText('?', { exact: true }).first();
  if (record.visible_question_count > 0 && await question.isVisible().catch(() => false)) {
    const tipsBefore = await page.locator('[role="tooltip"]').count();
    await question.hover({ timeout: 4000 }).catch(() => {});
    await page.waitForTimeout(250);
    const tipsAfter = await page.locator('[role="tooltip"]').count();
    record.tooltip_role_appeared = tipsAfter > tipsBefore;
  } else {
    record.tooltip_role_appeared = null;
  }
  record.readable_page = Boolean(record.http_status === 200 && !challenge && record.body_chars > 2000 && record.has_enhancement);
  await context.close();
} catch (e) {
  record.error_class = e?.name || 'Error';
  record.error_category = /timeout/i.test(e?.message || '') ? 'timeout' : 'other';
  record.readable_page = false;
} finally {
  await browser?.close();
}
const output = JSON.stringify(record);
console.log('WOWHEAD_ACCESS_PROBE ' + output);
if (process.env.GITHUB_STEP_SUMMARY) {
  const { appendFileSync } = await import('node:fs');
  appendFileSync(process.env.GITHUB_STEP_SUMMARY, '# Wowhead interactive browser access pilot\n\n' + '```json\n' + JSON.stringify(record, null, 2) + '\n```\n\nOriginal guide content was not persisted. Pilot does **not** certify source completeness.\n');
}
