/**
 * Client for sending usernames to the username storage API
 * Used by Puppeteer workers to submit scraped usernames
 */

/**
 * Send usernames to the API endpoint
 * @param {string} platform - Platform name (e.g., 'roobet', 'shuffle', 'thrill', 'winna')
 * @param {Array<string>|Array<{username: string}>} usernames - Array of usernames or objects with username property
 * @returns {Promise<{success: boolean, added?: number, skipped?: number, error?: string}>}
 */
async function sendUsernames(platform, usernames) {
    if (!platform || !usernames || !Array.isArray(usernames) || usernames.length === 0) {
        return { success: false, error: 'Invalid parameters' };
    }

    // Normalize usernames array
    const normalizedUsernames = usernames.map(item => {
        if (typeof item === 'string') {
            return { username: item, platform: platform };
        } else if (item && item.username) {
            return { username: item.username, platform: platform };
        }
        return null;
    }).filter(Boolean);

    if (normalizedUsernames.length === 0) {
        return { success: false, error: 'No valid usernames to send' };
    }

    // Get API URL from environment or use default
    const apiUrl = process.env.USERNAME_API_URL || 'http://localhost:3000';
    const endpoint = `${apiUrl}/usernames`;

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                usernames: normalizedUsernames
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API returned ${response.status}: ${errorText}`);
        }

        const result = await response.json();
        return {
            success: result.success || false,
            added: result.added || 0,
            skipped: result.skipped || 0
        };
    } catch (error) {
        // Log error but don't throw - we want scraping to continue even if API fails
        console.error(`[usernameApiClient] Failed to send usernames to API: ${error.message}`);
        return {
            success: false,
            error: error.message
        };
    }
}

module.exports = {
    sendUsernames
};
