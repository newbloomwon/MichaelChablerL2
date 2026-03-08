// --- TAB SWITCHING LOGIC ---
function switchTab(tabId) {
  const musicContent = document.getElementById("music-content");
  const liveNowContent = document.getElementById("live-now-content");
  const tabMusic = document.getElementById("tab-music");
  const tabLiveNow = document.getElementById("tab-live-now");

  if (tabId === "music") {
    musicContent.style.display = "block";
    liveNowContent.style.display = "none";
    tabMusic.classList.add("active");
    tabLiveNow.classList.remove("active");
  } else if (tabId === "live-now") {
    musicContent.style.display = "none";
    liveNowContent.style.display = "block";
    tabMusic.classList.remove("active");
    tabLiveNow.classList.add("active");
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

  // Function to format time (e.g., 185 seconds -> 3:05)
  function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs < 10 ? "0" : ""}${secs}`;
  }

  // Toggle Play/Pause
  playPauseBtn.addEventListener("click", () => {
    if (isPlaying) {
      audio.pause();
      playPauseBtn.innerHTML = '<span class="icon">▶️</span>';
      playPauseBtn.title = "Play";
    } else {
      audio.play();
      playPauseBtn.innerHTML = '<span class="icon">⏸️</span>';
      playPauseBtn.title = "Pause";
    }
    isPlaying = !isPlaying;
  });

  // Update progress bar and current time
  audio.addEventListener("timeupdate", () => {
    if (!isNaN(audio.duration)) {
      const progress = (audio.currentTime / audio.duration) * 100;
      progressBar.style.width = progress + "%";
      currentTimeEl.textContent = formatTime(audio.currentTime);
    }
  });

  // Set initial duration when metadata is loaded
  audio.addEventListener("loadedmetadata", () => {
    if (!isNaN(audio.duration)) {
      durationEl.textContent = formatTime(audio.duration);
    }
  });

  // Allow seeking by clicking on the track
  seekTrack.addEventListener("click", (e) => {
    const rect = seekTrack.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = clickX / rect.width;
    if (!isNaN(audio.duration)) {
      audio.currentTime = audio.duration * percentage;
    }
  });

  // Reset player when finished
  audio.addEventListener("ended", () => {
    isPlaying = false;
    playPauseBtn.innerHTML = '<span class="icon">▶️</span>';
    playPauseBtn.title = "Play";
    audio.currentTime = 0;
    progressBar.style.width = "0%";
  });

  // Manual initialization of duration in case of rapid load
  if (audio.readyState >= 1 && !isNaN(audio.duration)) {
    durationEl.textContent = formatTime(audio.duration);
  }
});
