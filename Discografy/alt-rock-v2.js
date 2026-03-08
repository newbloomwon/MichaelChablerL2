function switchTab(tabId) {
    const musicContent = document.getElementById("music-content");
    const newMusicContent = document.getElementById("new-music-content");
    const liveNowContent = document.getElementById("live-now-content");
    const randomContent = document.getElementById("random-content");

    const tabMusic = document.getElementById("tab-music");
    const tabNewMusic = document.getElementById("tab-new-music");
    const tabLiveNow = document.getElementById("tab-live-now");
    const tabRandom = document.getElementById("tab-random");

    // Hide all contents safely
    if (musicContent) musicContent.style.display = "none";
    if (newMusicContent) newMusicContent.style.display = "none";
    if (liveNowContent) liveNowContent.style.display = "none";
    if (randomContent) randomContent.style.display = "none";

    // Deactivate all tabs safely
    if (tabMusic) tabMusic.classList.remove("active");
    if (tabNewMusic) tabNewMusic.classList.remove("active");
    if (tabLiveNow) tabLiveNow.classList.remove("active");
    if (tabRandom) tabRandom.classList.remove("active");

    // Activate selected
    if (tabId === "music") {
        if (musicContent) musicContent.style.display = "block";
        if (tabMusic) tabMusic.classList.add("active");
    } else if (tabId === "new-music") {
        if (newMusicContent) newMusicContent.style.display = "block";
        if (tabNewMusic) tabNewMusic.classList.add("active");
    } else if (tabId === "live-now") {
        if (liveNowContent) liveNowContent.style.display = "block";
        if (tabLiveNow) tabLiveNow.classList.add("active");
    } else if (tabId === "random") {
        if (randomContent) randomContent.style.display = "block";
        if (tabRandom) tabRandom.classList.add("active");

        // Trigger discovery refresh when tab is selected
        if (window.refreshDiscovery) window.refreshDiscovery();
    }
}


// Make switchTab available globally as it's used in HTML onclick
window.switchTab = switchTab;

// --- MUSIC PLAYER LOGIC ---
document.addEventListener("DOMContentLoaded", () => {
    const audio = document.getElementById("audio-player");
    const playPauseBtn = document.getElementById("play-pause-btn");
    const currentTimeEl = document.getElementById("current-time");
    const durationEl = document.getElementById("duration");
    const progressBar = document.getElementById("seek-bar-progress");
    const seekTrack = document.getElementById("seek-bar-track");
    let isPlaying = false;

    // Discovery UI Elements
    // Discovery UI Elements
    const discoverBtn = document.getElementById("btn-discover");
    const resultContainer = document.getElementById("discovery-result");
    const dImg = document.getElementById("discovery-img");
    const dTitle = document.getElementById("discovery-title");
    const dArtist = document.getElementById("discovery-artist");
    const dGenre = document.getElementById("discovery-genre");

    // --- GENRE SELECTION LOGIC (Cards) ---
    let currentGenre = "random";
    const genreCards = document.querySelectorAll(".genre-card");

    genreCards.forEach(card => {
        card.addEventListener("click", () => {
            // Update UI (Card Border Stye)
            genreCards.forEach(c => c.style.border = "none");
            card.style.border = "2px solid var(--neon-cyan)";

            // Update Logic
            currentGenre = card.getAttribute("data-genre");
            logToScreen(`Selected Genre: ${currentGenre}`);

            // Update Button & Scroll
            if (discoverBtn) {
                discoverBtn.textContent = `🎲 DISCOVER ${currentGenre.toUpperCase()}`;
                setTimeout(() => {
                    discoverBtn.scrollIntoView({ behavior: "smooth", block: "center" });
                }, 100);
            }
        });
    });

    // DEBUG HELPER
    function logToScreen(msg) {
        let consoleBox = document.getElementById("debug-console");
        // Create it if it doesn't exist (failsafe)
        if (!consoleBox) {
            consoleBox = document.createElement("div");
            consoleBox.id = "debug-console";
            consoleBox.style.cssText = "position: fixed; bottom: 0; right: 0; width: 300px; height: 150px; background: rgba(0,0,0,0.8); color: lime; font-family: monospace; font-size: 10px; overflow-y: scroll; z-index: 9999; padding: 10px; border-top: 2px solid lime;";
            document.body.appendChild(consoleBox);
        }

        const line = document.createElement("div");
        line.textContent = `> ${msg}`;
        consoleBox.appendChild(line);
        consoleBox.scrollTop = consoleBox.scrollHeight;
        console.log(msg);
    }

    // Function to format time (e.g., 185 seconds -> 3:05)
    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}:${secs < 10 ? "0" : ""}${secs}`;
    }

    // --- REUSABLE DISCOVERY FUNCTION ---
    async function triggerDiscovery() {
        logToScreen(`triggerDiscovery() [Genre: ${currentGenre}]`);
        if (discoverBtn) {
            discoverBtn.textContent = "🎲 SEARCHING...";
            discoverBtn.disabled = true;
        }
        if (resultContainer) resultContainer.style.display = "none";

        try {
            // STEP 1: FETCH
            logToScreen(`Step 1: Calling Discovery Service (${currentGenre})...`);
            const track = await discoveryService.discoverNewTrack(currentGenre);

            if (!track) {
                logToScreen("ERROR: Service returned null");
                throw new Error("Service returned null");
            }
            logToScreen(`SUCCESS: Track received: ${track.name}`);

            // STEP 2: UPDATE UI
            logToScreen("Step 2: Updating DOM...");
            if (dTitle) dTitle.textContent = track.name;
            if (dArtist) dArtist.textContent = track.artist_name;
            if (dImg) dImg.src = track.image;
            if (dGenre) {
                const tags = (track.musicinfo && track.musicinfo.tags) ? track.musicinfo.tags : [];
                dGenre.textContent = `Genre: ${Array.isArray(tags) ? tags.join(", ") : "Various"}`;
            }

            if (resultContainer) resultContainer.style.display = "block";
            if (discoverBtn) {
                discoverBtn.textContent = "🎲 DISCOVER ANOTHER";
                discoverBtn.disabled = false;
            }

            // STEP 3: PLAY
            logToScreen(`Step 3: Play URL ${track.audio}`);
            Player.playTrack(track);

        } catch (error) {
            logToScreen(`CRITICAL ERROR: ${error.message}`);
            alert(`Discovery Failed: ${error.message}`);

            if (discoverBtn) {
                discoverBtn.textContent = "❌ ERROR - TRY AGAIN";
                discoverBtn.disabled = false;
            }
        }
    }

    // --- PLAYER CONTROLLER LOGIC ---
    const Player = {
        queue: [],
        currentIndex: -1,
        isShuffled: false,
        element: audio,

        // Add track to queue and play immediately
        playTrack: function (track) {
            this.queue.push(track);
            this.currentIndex = this.queue.length - 1;
            this.loadAndPlay(track);
        },

        loadAndPlay: function (track) {
            logToScreen(`Loading Player: ${track.name}`);
            document.querySelector(".player-art").src = track.image;
            document.querySelector(".track-title").textContent = track.name;
            document.querySelector(".track-artists").textContent = track.artist_name;

            this.element.src = track.audio;

            // FORCE VOLUME ON LOAD
            this.element.volume = 1.0;
            this.element.muted = false;

            // Add error listener for deep debugging
            this.element.onerror = (e) => {
                const err = this.element.error;
                const codes = { 1: 'ABORTED', 2: 'NETWORK', 3: 'DECODE', 4: 'SRC_NOT_SUPPORTED' };
                logToScreen(`❌ MEDIA ERROR: ${codes[err.code] || 'UNKNOWN'} (${err.message})`);
            };

            // DEBUG: Log audio details
            logToScreen(`🎵 Audio URL: ${track.audio}`);
            logToScreen(`🔊 Volume: ${this.element.volume} (Forced to 100%)`);
            logToScreen(`🔇 Muted: ${this.element.muted}`);

            // Updated Banner Sync Logic (Merged)
            const bannerArtist = document.getElementById("banner-artist-name");
            const bannerTrack = document.getElementById("banner-track-title");
            const bannerContent = document.querySelector(".banner-content");

            if (bannerArtist) bannerArtist.textContent = (track.artist_name || track.artist || "Unknown").toUpperCase();
            if (bannerTrack) bannerTrack.textContent = (track.name || track.title || "Unknown").toUpperCase();

            // Visual confirmation of update
            if (bannerContent) {
                bannerContent.classList.remove('banner-flash');
                void bannerContent.offsetWidth; // Trigger reflow
                bannerContent.classList.add('banner-flash');
            }

            const playPromise = this.element.play();

            if (playPromise !== undefined) {
                playPromise.then(_ => {
                    logToScreen("Playback started successfully.");
                    this.updatePlayPauseIcon(true);
                    isPlaying = true;
                })
                    .catch(error => {
                        logToScreen(`Autoplay BLOCKED: ${error.message}`);
                        logToScreen(`❌ Error name: ${error.name}`);
                        alert("Click Play! Browser blocked auto-start.");
                        this.updatePlayPauseIcon(false);
                        isPlaying = false;
                    });
            }

            // Save history
            discoveryService.markAsPlayed(track);
        },

        updatePlayPauseIcon: function (playing) {
            if (playing) {
                playPauseBtn.textContent = '⏸️';
                playPauseBtn.title = "Pause";
            } else {
                playPauseBtn.textContent = '▶️';
                playPauseBtn.title = "Play";
            }
        },

        next: function () {
            logToScreen("Player.next called.");
            if (this.queue.length === 0 || this.currentIndex >= this.queue.length - 1) {
                logToScreen("Queue empty. Auto-discovering...");
                triggerDiscovery();
            } else {
                this.currentIndex++;
                this.loadAndPlay(this.queue[this.currentIndex]);
            }
        },

        previous: function () {
            if (this.currentIndex > 0) {
                this.currentIndex--;
                this.loadAndPlay(this.queue[this.currentIndex]);
            } else {
                this.element.currentTime = 0;
            }
        },

        toggleShuffle: function () {
            this.isShuffled = !this.isShuffled;
            alert(`Shuffle is now ${this.isShuffled ? 'ON' : 'OFF'}`);
        }
    };

    // --- BUTTON EVENT LISTENERS ---

    // Discovery Button
    if (discoverBtn) {
        discoverBtn.addEventListener("click", () => {
            triggerDiscovery();
        });
    }

    // Play/Pause
    playPauseBtn.addEventListener("click", () => {
        if (isPlaying) {
            audio.pause();
            Player.updatePlayPauseIcon(false);
        } else {
            audio.play();
            Player.updatePlayPauseIcon(true);
        }
        isPlaying = !isPlaying;
    });

    // Next Button
    const nextBtn = document.querySelector('button[title="Next"]');
    if (nextBtn) {
        nextBtn.addEventListener("click", () => {
            Player.next();
        });
    } else {
        console.error("Next button not found");
    }

    // Previous Button
    const prevBtn = document.querySelector('button[title="Previous"]');
    if (prevBtn) {
        prevBtn.addEventListener("click", () => {
            Player.previous();
        });
    }

    // Shuffle Button
    const shuffleBtn = document.querySelector('button[title="Shuffle"]');
    if (shuffleBtn) {
        shuffleBtn.addEventListener("click", () => {
            Player.toggleShuffle();
        });
    }

    // Update progress bar
    audio.addEventListener("timeupdate", () => {
        if (!isNaN(audio.duration)) {
            const progress = (audio.currentTime / audio.duration) * 100;
            progressBar.style.width = progress + "%";
            currentTimeEl.textContent = formatTime(audio.currentTime);
        }
    });

    audio.addEventListener("loadedmetadata", () => {
        if (!isNaN(audio.duration)) {
            durationEl.textContent = formatTime(audio.duration);
        }
    });

    seekTrack.addEventListener("click", (e) => {
        const rect = seekTrack.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = clickX / rect.width;
        if (!isNaN(audio.duration)) {
            audio.currentTime = audio.duration * percentage;
        }
    });

    audio.addEventListener("ended", () => {
        // Auto-next on end
        Player.next();
    });

    // --- Design-Specific Interactions (Graffiti / Scrawl) ---
    function applyScrawl() {
        const targets = document.querySelectorAll('.card-title, .section-header h2, .quick-pick-item-title, .track-title');
        targets.forEach(el => {
            const randomRotation = (Math.random() * 3 - 1.5).toFixed(2);
            el.style.transform = `rotate(${randomRotation}deg)`;
            el.style.display = 'inline-block';
        });
    }
    applyScrawl();

    // Boost button effect (Exclude the discover button!)
    const boostBtn = document.querySelector('.btn-cure.secondary:not(#btn-discover)');
    if (boostBtn) {
        boostBtn.addEventListener('click', () => {
            boostBtn.style.transform = 'scale(0.95)';
            setTimeout(() => {
                boostBtn.style.transform = 'scale(1)';
                alert('Artist Boosted! Long live the underground.');
            }, 100);
        });
    }

    console.log('Discografy Player Logic Loaded (DEBUG MODE).');
    logToScreen("System Ready.");

    // --- RANDOM DISCOVERY ENGINE (Developer C with HEART Enhancement) ---

    // HEART Framework Data
    let discoveryStreak = parseInt(localStorage.getItem('discoveryStreak') || '0');
    let lastDiscoveryDate = localStorage.getItem('lastDiscoveryDate');

    function updateStreak() {
        const today = new Date().toDateString();
        if (lastDiscoveryDate !== today) {
            discoveryStreak++;
            localStorage.setItem('discoveryStreak', discoveryStreak);
            localStorage.setItem('lastDiscoveryDate', today);
        }
        renderStreak();
    }

    function renderStreak() {
        const header = document.querySelector('#random-content .section-header');
        let streakEl = document.getElementById('streak-counter');
        if (!streakEl) {
            streakEl = document.createElement('div');
            streakEl.id = 'streak-counter';
            streakEl.className = 'discovery-streak';
            header.appendChild(streakEl);
        }
        streakEl.innerHTML = `🔥 ${discoveryStreak} Day Streak`;
    }

    function trackDiscoveryEvent(category, action, label) {
        console.log(`[HEART TELEMETRY] Category: ${category}, Action: ${action}, Label: ${label}`);
        showTelemetryToast(`${action}: ${label}`);
    }

    function showTelemetryToast(msg) {
        let toast = document.getElementById('telemetry-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'telemetry-toast';
            toast.className = 'telemetry-toast';
            document.body.appendChild(toast);
        }
        toast.textContent = `📊 Analytics Sent: ${msg}`;
        toast.classList.add('visible');
        setTimeout(() => toast.classList.remove('visible'), 2000);
    }

    const collectionTracks = [
        { title: "I DID THIS TO MYSELF", artist: "Thundercat, Lil Yachty", art: "https://picsum.photos/seed/thundercat/300", url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", type: "Collection", mood: "Smooth" },
        { title: "Disintegration", artist: "The Cure", art: "https://picsum.photos/seed/cure/300", url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3", type: "Collection", mood: "Gloom" },
        { title: "Marquee Moon", artist: "Television", art: "https://picsum.photos/seed/television/300", url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3", type: "Collection", mood: "Electric" },
        { title: "Bela Lugosi's Dead", artist: "Bauhaus", art: "https://picsum.photos/seed/bauhaus/300", url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3", type: "Collection", mood: "Dark" }
    ];

    const independentTracks = [
        { title: "Basement Sessions", artist: "Sofa King Cold", art: "https://picsum.photos/seed/sofa/300", url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3", type: "Independent", mood: "Raw" },
        { title: "Neon Skyline", artist: "Glitch Ghost", art: "https://picsum.photos/seed/glitch/300", url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3", type: "Independent", mood: "Cyber" },
        { title: "Concrete Jungle", artist: "The Void", art: "https://picsum.photos/seed/concrete/300", url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3", type: "Independent", mood: "Post-Punk" }
    ];

    // --- CURATED CRATES & COLLECTION (Expanding the PRD "Moat") ---


    // 1. Curated Crates Dataset
    const curatedCrates = [
        {
            curator: "Professor of Rock",
            title: "Post-Punk Essentials",
            art: "https://picsum.photos/seed/rockprof/300",
            tracks: [
                { title: "Marquee Moon", artist: "Television", art: "https://picsum.photos/seed/television/300", url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3" },
                { title: "Bela Lugosi's Dead", artist: "Bauhaus", art: "https://picsum.photos/seed/bauhaus/300", url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3" }
            ]
        },
        {
            curator: "Indie Sleaze",
            title: "Basement Tapes Vol. 1",
            art: "https://picsum.photos/seed/indiesleaze/300",
            tracks: [
                { title: "Basement Sessions", artist: "Sofa King Cold", art: "https://picsum.photos/seed/sofa/300", url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3" },
                { title: "Concrete Jungle", artist: "The Void", art: "https://picsum.photos/seed/concrete/300", url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3" }
            ]
        }
    ];

    // 2. Collection Persistence
    let userCrate = JSON.parse(localStorage.getItem('userCrate') || '[]');

    function addToCollection(track) {
        // Prevent duplicates
        if (!userCrate.some(t => t.title === track.title)) {
            userCrate.push(track);
            localStorage.setItem('userCrate', JSON.stringify(userCrate));
            trackDiscoveryEvent('TaskSuccess', 'COLLECTION_ADDED', track.title);
            renderUserCollection();
        }
    }

    function renderUserCollection() {
        const section = document.getElementById('my-collection-section');
        const grid = document.getElementById('user-collection-grid');
        if (!grid) return;

        if (userCrate.length > 0) {
            section.style.display = 'block';
            grid.innerHTML = '';
            userCrate.forEach(track => {
                const card = document.createElement('div');
                card.className = 'recommendation-card';
                card.innerHTML = `
                    <div class="card-image-container">
                        <img src="${track.art}" alt="${track.title}">
                        <span class="owned-sticker scrawled">OWNED</span>
                    </div>
                    <div class="card-title">${track.title}</div>
                    <div class="card-artists">${track.artist}</div>
                `;
                card.addEventListener('click', () => {
                    playTrack(track);
                });
                grid.appendChild(card);
            });
        } else {
            section.style.display = 'none';
        }
    }

    function renderCrates() {
        const container = document.getElementById('curated-crates-container');
        if (!container) return;

        container.innerHTML = '<div class="scroll-row"></div>';
        const row = container.querySelector('.scroll-row');

        curatedCrates.forEach(crate => {
            const card = document.createElement('div');
            card.className = 'recommendation-card';
            card.innerHTML = `
                <div class="card-image-container">
                    <img src="${crate.art}" alt="${crate.title}">
                    <span class="curator-tag scrawled">Curated by ${crate.curator}</span>
                </div>
                <div class="card-title">${crate.title}</div>
                <div class="card-artists">${crate.tracks.length} Tracks of Real Music</div>
            `;
            // For now, clicking a crate just plays the first track for simplicity
            card.addEventListener('click', () => {
                playTrack(crate.tracks[0]);
            });
            row.appendChild(card);
        });
    }

    // Bridge for Team's playTrack calls
    function playTrack(track) {
        // Normalize track object if needed
        if (!track.artist_name && track.artist) track.artist_name = track.artist;
        if (!track.name && track.title) track.name = track.title;
        if (!track.image && track.art) track.image = track.art;
        if (!track.audio && track.url) track.audio = track.url;

        Player.playTrack(track);
    }

    // --- Unified Listener for existing static cards ---
    function initStaticCards() {
        const staticCards = document.querySelectorAll('.recommendation-card, .quick-pick-item');
        staticCards.forEach(card => {
            if (!card.hasAttribute('data-listener-attached')) {
                card.addEventListener('click', () => {
                    const titleEl = card.querySelector('.card-title, .quick-pick-item-title');
                    const artistEl = card.querySelector('.card-artists');
                    const imgEl = card.querySelector('img');

                    if (titleEl) {
                        const track = {
                            title: titleEl.innerText.split('*')[0].split('🔫')[0].trim(),
                            artist: artistEl ? artistEl.innerText : "Discografy Selection",
                            art: imgEl ? imgEl.src : "https://picsum.photos/seed/player/50",
                            url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
                        };
                        playTrack(track);
                    }
                });
                card.setAttribute('data-listener-attached', 'true');
            }
        });
    }

    initStaticCards(); // Initialize existing ones

    // Update refreshDiscovery to use the new collection logic
    window.refreshDiscovery = function () {
        trackDiscoveryEvent('Engagement', 'SHUFFLE_TRIGGERED', 'User clicked shuffle button');

        const container = document.getElementById("random-discovery-container");
        if (!container) return;

        container.innerHTML = '<div class="discovery-grid"></div>';
        const grid = container.querySelector(".discovery-grid");

        const allTracks = [...collectionTracks, ...independentTracks];
        const shuffled = allTracks.sort(() => 0.5 - Math.random()).slice(0, 4);

        shuffled.forEach(track => {
            const card = document.createElement("div");
            card.className = "recommendation-card discovery-card";
            card.innerHTML = `
                <div class="card-image-container">
                    <img src="${track.art}" alt="${track.title}">
                    <span class="type-tag">${track.type}</span>
                    <span class="mood-tag">${track.mood}</span>
                    <div class="card-feedback-overlay">
                        <button class="feedback-btn like" title="Happiness: I love this!">💎</button>
                        <button class="feedback-btn skip" title="Happiness: Not for me">⏭️</button>
                    </div>
                </div>
                <div class="card-title">${track.title}</div>
                <div class="card-artists">${track.artist}</div>
                <div class="card-actions">
                    <button class="action-btn download-btn">OWN THIS (80% TO ARTIST)</button>
                </div>
            `;

            card.querySelector('.like').addEventListener('click', (e) => {
                e.stopPropagation();
                trackDiscoveryEvent('Happiness', 'POSITIVE_FEEDBACK', track.title);
                card.style.borderColor = 'gold';
            });

            card.querySelector('.skip').addEventListener('click', (e) => {
                e.stopPropagation();
                trackDiscoveryEvent('Happiness', 'NEGATIVE_FEEDBACK', track.title);
                card.style.opacity = '0.3';
            });

            card.querySelector('.download-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                addToCollection(track);
                alert(`SUCCESS: You now own "${track.title}" by ${track.artist}. Added to your collection.`);
            });

            card.addEventListener("click", () => {
                trackDiscoveryEvent('Engagement', 'TRACK_PLAYED', track.title);
                playTrack(track);
                updateStreak();
            });

            grid.appendChild(card);
        });

        const shuffleBtnContainer = document.createElement("div");
        shuffleBtnContainer.className = "shuffle-action";
        shuffleBtnContainer.innerHTML = `<button class="nav-tab active" style="margin-top: 2rem;">Shuffle Again 🎲</button>`;
        shuffleBtnContainer.addEventListener("click", refreshDiscovery);
        container.appendChild(shuffleBtnContainer);

        applyScrawl();
    };

    // Initialize the new features
    renderUserCollection();
    renderCrates();

});

