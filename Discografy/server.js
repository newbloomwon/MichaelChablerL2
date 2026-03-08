require('dotenv').config();
const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// ALLOW CORS so the frontend (file:// or localhost) can hit this
// ALLOW CORS so the frontend (file:// or localhost) can hit this
app.use(cors());

// serve static files (HTML, CSS, JS)
app.use(express.static(__dirname));

// JAMENDO CONFIG - Now using environment variables
const JAMENDO_CLIENT_ID = process.env.JAMENDO_CLIENT_ID || '81cd9f40';
const BASE_URL = 'https://api.jamendo.com/v3.0';


// Genres for the Anti-Algorithm (Updated for less "Classical" feel)
const GENRES = [
    'indie', 'rock', 'electronic', 'hiphop', 'jazz', 'pop',
    'trip-hop', 'reggae', 'metal', 'punk', 'lofi', 'dance', 'synthwave',
    'world', 'latin', 'african', 'asian', 'bollywood'
];

app.get('/api/discover', async (req, res) => {
    try {
        // Use requested genre OR pick random
        let selectedGenre = req.query.genre;

        // Validation: If no genre or invalid/random request, pick one
        if (!selectedGenre || selectedGenre === 'random') {
            selectedGenre = GENRES[Math.floor(Math.random() * GENRES.length)];
        }

        // Random offset for variety
        const randomOffset = Math.floor(Math.random() * 500);

        console.log(`[PROXY] Fetching: ${selectedGenre} (Offset: ${randomOffset})`);

        const response = await axios.get(`${BASE_URL}/tracks/`, {
            params: {
                client_id: JAMENDO_CLIENT_ID,
                format: 'jsonpretty',
                limit: 1,
                tags: selectedGenre,
                offset: randomOffset,
                include: 'musicinfo'
            }
        });

        if (response.data.results && response.data.results.length > 0) {
            console.log(`[PROXY] Success: Found "${response.data.results[0].name}"`);
            res.json(response.data.results[0]);
        } else {
            console.warn(`[PROXY] No results for ${selectedGenre}. Retrying with fallback...`);
            // Retry with a reliable fallback
            const retryResponse = await axios.get(`${BASE_URL}/tracks/`, {
                params: {
                    client_id: JAMENDO_CLIENT_ID,
                    format: 'jsonpretty',
                    limit: 1,
                    tags: 'indie',
                    offset: Math.floor(Math.random() * 100),
                    include: 'musicinfo'
                }
            });
            res.json(retryResponse.data.results[0] || null);
        }

    } catch (error) {
        console.error('[PROXY] Error:', error.message);
        res.status(500).json({ error: 'Failed to fetch music' });
    }
});

app.listen(PORT, () => {
    console.log(`\n🎶 Discografy Logic Server running on http://localhost:${PORT}`);
    console.log(`   - Discovery Endpoint: http://localhost:${PORT}/api/discover`);
});
