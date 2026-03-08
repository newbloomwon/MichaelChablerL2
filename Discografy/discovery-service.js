class DiscoveryService {
    constructor() {
        // No config needed for proxy mode
    }

    // SIMPLIFIED: Just fetch from proxy, no history, no recursion
    async discoverNewTrack(genre = 'random') {
        console.log(`DiscoveryService: Calling Proxy (genre=${genre})...`);

        try {
            // Hit our local node server
            const response = await fetch(`http://localhost:3000/api/discover?genre=${genre}`);

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            const track = await response.json();
            console.log("DiscoveryService: Received track", track ? track.name : "null");

            return track;

        } catch (error) {
            console.error("DiscoveryService Error:", error);
            // Return null so UI handles it
            return null;
        }
    }

    // History check disabled for debug
    async checkHistory(trackId) {
        return true;
    }

    // Fire-and-forget save (don't await this in critical path)
    markAsPlayed(track) {
        // Safety check: if Firebase SDKs aren't loaded, don't crash
        if (typeof auth === 'undefined' || typeof firebase === 'undefined' || !auth.currentUser) {
            console.log("DiscoveryService: History save skipped (Auth/Firebase not available)");
            return;
        }

        db.collection('users').doc(auth.currentUser.uid).collection('history').doc(track.id.toString()).set({
            artist: track.artist_name,
            title: track.name,
            playedAt: firebase.firestore.FieldValue.serverTimestamp()
        }).catch(e => console.warn("History save failed:", e));
    }
}

// Export a single instance
const discoveryService = new DiscoveryService();
