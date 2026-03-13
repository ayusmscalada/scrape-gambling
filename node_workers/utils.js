/**
 * Sleep for given milliseconds (replacement for removed page.waitForTimeout in Puppeteer 24+).
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = { sleep };
