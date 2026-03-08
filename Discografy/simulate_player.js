const https = require('https');

// MOCK CONSTANTS
const CLIENT_ID = '81cd9f40';
const GENRES = ['jazz', 'classical', 'metal', 'electronic', 'lofi', 'folk', 'blues', 'punk'];

// MOCK SERVICES
const discoveryService = {
    discoverNewTrack: function () {
        return new Promise((resolve) => {
            const randomGenre = GENRES[Math.floor(Math.random() * GENRES.length)];
            const randomOffset = Math.floor(Math.random() * 50); // Smaller offset for test speed
            const url = `https://api.jamendo.com/v3.0/tracks/?client_id=${CLIENT_ID}&format=jsonpretty&limit=1&tags=${randomGenre}&offset=${randomOffset}&include=musicinfo`;

            https.get(url, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    try {
                        const json = JSON.parse(data);
                        if (json.results && json.results.length > 0) {
                            resolve(json.results[0]);
                        } else {
                            resolve(null);
                        }
                    } catch (e) { resolve(null); }
                });
            }).on('error', () => resolve(null));
        });
    }
};

const Player = {
    queue: [],
    currentIndex: -1,

    // Check queue state and decide action
    next: async function () {
        if (this.queue.length === 0 || this.currentIndex >= this.queue.length - 1) {
            console.log(">> Queue Empty/End. Triggering Auto-Discovery...");
            const track = await discoveryService.discoverNewTrack();
            if (track) {
                console.log(`   [FETCHED] "${track.name}" by ${track.artist_name} (Genre: ${track.musicinfo.tags[0]})`);
                this.playTrack(track);
            } else {
                console.log("   [ERROR] Failed to fetch track.");
            }
        } else {
            this.currentIndex++;
            const track = this.queue[this.currentIndex];
            console.log(`>> [PLAYING NEXT] "${track.name}"`);
        }
    },

    playTrack: function (track) {
        this.queue.push(track);
        this.currentIndex = this.queue.length - 1;
        // console.log(`   [PLAYING] ${track.name}`);
    }
};

// SIMULATION LOOP
async function runSimulation() {
    console.log("=== STARTING 5-CLICK SIMULATION ===");
    for (let i = 1; i <= 5; i++) {
        console.log(`\n[CLICK #${i}]`);
        await Player.next();
        // Wait a bit to be polite to the API
        await new Promise(r => setTimeout(r, 1000));
    }
    console.log("\n=== SIMULATION COMPLETE ===");
}

runSimulation();
