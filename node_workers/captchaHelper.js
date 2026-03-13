/**
 * Cloudflare Turnstile solving via 2captcha API.
 * Used when Stake (or other sites) show "Verify you are human" challenge.
 * Set TWO_CAPTCHA_API_KEY in environment.
 */

const TASK_POLL_MS = 3000;
const TASK_TIMEOUT_MS = 120000;

/**
 * Create a Turnstile task and poll until solution is ready.
 * @param {string} apiKey - 2captcha API key
 * @param {string} sitekey - Turnstile data-sitekey from the page
 * @param {string} url - Full page URL
 * @param {object} [extra] - Optional: action, data, pagedata for challenge pages
 * @returns {Promise<string|null>} - Token or null on failure
 */
async function getTurnstileToken(apiKey, sitekey, url, extra = {}) {
    if (!apiKey || !sitekey || !url) {
        console.warn('[captcha] Missing apiKey, sitekey, or url');
        return null;
    }
    const taskPayload = {
        type: 'TurnstileTaskProxyless',
        websiteURL: url,
        websiteKey: sitekey,
    };
    if (extra.action) taskPayload.action = extra.action;
    if (extra.data) taskPayload.data = extra.data;
    if (extra.pagedata) taskPayload.pagedata = extra.pagedata;

    try {
        const createRes = await fetch('https://api.2captcha.com/createTask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clientKey: apiKey, task: taskPayload }),
        });
        const createJson = await createRes.json();
        if (createJson.errorId !== 0 || !createJson.taskId) {
            console.warn('[captcha] createTask failed:', createJson.errorDescription || createJson);
            return null;
        }
        const taskId = createJson.taskId;
        const deadline = Date.now() + TASK_TIMEOUT_MS;
        while (Date.now() < deadline) {
            await new Promise(r => setTimeout(r, TASK_POLL_MS));
            const resultRes = await fetch('https://api.2captcha.com/getTaskResult', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ clientKey: apiKey, taskId }),
            });
            const resultJson = await resultRes.json();
            if (resultJson.errorId !== 0) {
                console.warn('[captcha] getTaskResult error:', resultJson.errorDescription || resultJson);
                return null;
            }
            if (resultJson.status === 'ready' && resultJson.solution && resultJson.solution.token) {
                return resultJson.solution.token;
            }
            if (resultJson.status === 'failed') {
                console.warn('[captcha] Task failed');
                return null;
            }
        }
        console.warn('[captcha] Timeout waiting for solution');
        return null;
    } catch (e) {
        console.warn('[captcha] Request failed:', e.message);
        return null;
    }
}

/**
 * Extract Turnstile sitekey from the page (data-sitekey or script content).
 * @param {import('puppeteer').Page} page
 * @returns {Promise<{sitekey: string}|null>}
 */
async function extractTurnstileSitekey(page) {
    const result = await page.evaluate(() => {
        const div = document.querySelector('[data-sitekey]');
        if (div && div.getAttribute('data-sitekey')) {
            return { sitekey: div.getAttribute('data-sitekey') };
        }
        const scripts = document.querySelectorAll('script');
        for (const s of scripts) {
            const text = (s.textContent || s.innerText || '');
            const m = text.match(/sitekey['"]\s*:\s*['"]([^'"]+)['"]/);
            if (m) return { sitekey: m[1] };
            const km = text.match(/["']?sitekey["']?\s*:\s*["']?([a-zA-Z0-9_-]+)["']?/);
            if (km) return { sitekey: km[1] };
        }
        return null;
    });
    return result;
}

/**
 * Inject the Turnstile token and trigger callback/submit so the challenge is completed.
 * @param {import('puppeteer').Page} page
 * @param {string} token
 * @returns {Promise<boolean>}
 */
async function injectTurnstileToken(page, token) {
    const ok = await page.evaluate((t) => {
        const input = document.querySelector('input[name="cf-turnstile-response"]') ||
            document.querySelector('textarea[name="cf-turnstile-response"]');
        if (input) {
            input.value = t;
            input.dispatchEvent(new Event('input', { bubbles: true }));
        }
        if (typeof window.cfCallback === 'function') {
            try { window.cfCallback(t); return true; } catch (e) {}
        }
        if (typeof window.turnstile !== 'undefined' && window.turnstile.render) {
            const cb = window.tsCallback || window.cfCallback;
            if (typeof cb === 'function') { try { cb(t); return true; } catch (e) {} }
        }
        const form = document.querySelector('form');
        if (form) {
            try { form.submit(); return true; } catch (e) {}
        }
        const btn = document.querySelector('input[type="submit"], button[type="submit"]');
        if (btn) {
            try { btn.click(); return true; } catch (e) {}
        }
        return !!input;
    }, token);
    return ok;
}

/**
 * Detect Cloudflare "Verify you are human" / Turnstile challenge on the page.
 * @param {import('puppeteer').Page} page
 * @returns {Promise<boolean>}
 */
async function isCloudflareChallenge(page) {
    return page.evaluate(() => {
        const body = document.body ? document.body.innerText : '';
        if (/Verify you are human/i.test(body) || /Performing security verification/i.test(body)) return true;
        if (document.querySelector('[data-sitekey]') || document.querySelector('input[name="cf-turnstile-response"]')) return true;
        return false;
    });
}

/**
 * Solve Cloudflare Turnstile on the current page using 2captcha.
 * Reads TWO_CAPTCHA_API_KEY from process.env.
 * @param {import('puppeteer').Page} page
 * @returns {Promise<boolean>} - true if token was injected successfully
 */
async function solveTurnstileOnPage(page) {
    const apiKey = process.env.TWO_CAPTCHA_API_KEY;
    if (!apiKey) {
        console.warn('[captcha] TWO_CAPTCHA_API_KEY not set; skip solving');
        return false;
    }
    const url = page.url();
    const extracted = await extractTurnstileSitekey(page);
    if (!extracted || !extracted.sitekey) {
        console.warn('[captcha] Could not find Turnstile sitekey on page');
        return false;
    }
    console.log('[captcha] Solving Turnstile via 2captcha...');
    const token = await getTurnstileToken(apiKey, extracted.sitekey, url);
    if (!token) return false;
    const injected = await injectTurnstileToken(page, token);
    if (injected) console.log('[captcha] Token injected.');
    return injected;
}

module.exports = {
    getTurnstileToken,
    extractTurnstileSitekey,
    injectTurnstileToken,
    isCloudflareChallenge,
    solveTurnstileOnPage,
};
