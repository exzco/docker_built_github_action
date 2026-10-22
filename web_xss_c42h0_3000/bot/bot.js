const express = require('express');
const puppeteer = require('puppeteer-core');

const app = express();
const PORT = 5000;
const FLAG = process.env.GZCTF_FLAG || 'flag{!!!请联系管理员!!!}';
const CHROMIUM_PATH = process.env.CHROMIUM_PATH || '/usr/bin/chromium';

const CHROMIUM_FLAGS = [
  '--no-sandbox',
  '--disable-setuid-sandbox',
  '--disable-dev-shm-usage',
  '--disable-gpu',
  '--disable-software-rasterizer',
  '--no-zygote',
  '--disable-extensions',
  '--disable-background-networking',
  '--disable-background-timer-throttling',
  '--disable-backgrounding-occluded-windows',
  '--disable-breakpad',
  '--disable-component-update',
  '--disable-domain-reliability',
  '--disable-sync',
  '--disable-translate',
  '--mute-audio',
  '--no-first-run',
  '--safebrowsing-disable-auto-update',
  '--js-flags=--max-old-space-size=128',
];

let browser = null;
let taskQueue = Promise.resolve();

async function initBrowser() {
  console.log('[Bot] Launching shared Chromium instance...');
  browser = await puppeteer.launch({
    executablePath: CHROMIUM_PATH,
    headless: true,
    args: CHROMIUM_FLAGS,
  });

  browser.on('disconnected', async () => {
    console.warn('[Bot] Browser disconnected. Relaunching...');
    try {
      await initBrowser();
    } catch (e) {
      console.error('[Bot] Failed to relaunch browser:', e);
    }
  });

  console.log('[Bot] Chromium ready.');
}

async function visit(url) {
  if (!browser) {
    throw new Error('Browser not initialized');
  }
  const context = await browser.createBrowserContext();
  try {
    const page = await context.newPage();
    await page.setCookie({
      name: 'flag',
      value: FLAG,
      domain: '127.0.0.1',
      path: '/',
      httpOnly: false,
      secure: false,
      sameSite: 'Lax',
    });

    try {
      await page.goto(url, { waitUntil: 'load', timeout: 8000 });
      await new Promise((resolve) => setTimeout(resolve, 5000));
    } catch (err) {
      console.error(`[Bot] Error visiting ${url}: ${err.message}`);
    }
  } finally {
    await context.close().catch(() => {});
  }
}

function queueVisit(url) {
  const runTask = () => visit(url);
  const next = taskQueue.then(runTask, runTask);
  taskQueue = next;
  return next;
}

app.get('/visit', async (req, res) => {
  const url = req.query.url;
  if (!url) {
    return res.status(400).send('No URL');
  }

  try {
    await queueVisit(url);
    res.status(200).send('bot has Visited');
  } catch (err) {
    console.error(`[Bot] Failed to process visit: ${err.message}`);
    res.status(500).send('Visit Failed');
  }
});

async function main() {
  await initBrowser();
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`[Bot] Listening on port ${PORT}`);
  });
}

process.on('uncaughtException', (err) => {
  console.error('[Bot] Uncaught Exception:', err);
});

process.on('unhandledRejection', (reason) => {
  console.error('[Bot] Unhandled Rejection:', reason);
});

main().catch((err) => {
  console.error('[Bot] Startup failure:', err);
  process.exit(1);
});
