const https = require('https');

// The client ID provided by the user
const CLIENT_ID = '81cd9f40';
const GENRE = 'jazz';
const OFFSET = 0;

const url = `https://api.jamendo.com/v3.0/tracks/?client_id=${CLIENT_ID}&format=jsonpretty&limit=1&tags=${GENRE}&offset=${OFFSET}&include=musicinfo`;

console.log(`Testing Jamendo API: ${url}`);

https.get(url, (res) => {
    let data = '';

    console.log('Status Code:', res.statusCode);

    res.on('data', (chunk) => {
        data += chunk;
    });

    res.on('end', () => {
        try {
            const json = JSON.parse(data);
            if (json.headers && json.headers.status === 'success') {
                console.log('SUCCESS: API is reachable.');
                if (json.results && json.results.length > 0) {
                    console.log('Track Found:', json.results[0].name);
                    console.log('Audio URL:', json.results[0].audio);
                } else {
                    console.error('FAILURE: No results found.');
                }
            } else {
                console.error('FAILURE: API returned error status:', json);
            }
        } catch (e) {
            console.error('FAILURE: Could not parse JSON.', e);
            console.log('Raw Data:', data);
        }
    });

}).on('error', (err) => {
    console.error('FAILURE: Network error.', err.message);
});
