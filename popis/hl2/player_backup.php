<?php
$autoplay = isset($_GET['autoplay']) && $_GET['autoplay'] === 'true';
?>
<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <title>Audio Player</title>
  <style>
    body {
      margin: 0;
      background-color: black;
    }
    .player {
      width: 940px;
      height: 128px;
      border: none;
      border-radius: 10px;
      box-shadow: 0 0 20px 10px black;
      display: none;
    }
  </style>
</head>
<body>

<div id="playerContainer"></div>

<script>
  const container = document.getElementById('playerContainer');
  const PRIMARY_URL = "https://fmcloud.pro/embed.php?id=347&autoplay=true";
  const BACKUP_URL = "player_backup.php<?php echo $autoplay ? '?autoplay=true' : ''; ?>";

  function loadIframe(src, onLoadCallback = null) {
    const iframe = document.createElement('iframe');
    iframe.src = src;
    iframe.allow = "autoplay";
    iframe.className = "player";
    iframe.style.display = 'block';
    if (onLoadCallback) iframe.onload = onLoadCallback;
    container.appendChild(iframe);
    return iframe;
  }

  function removeAllIframes() {
    container.innerHTML = "";
  }

  function tryAutoplayInsideIframe(iframe) {
    try {
      const audio = iframe.contentDocument?.querySelector('audio');
      if (audio && typeof audio.play === 'function') {
        audio.play().then(() => {
          console.log("Autoplay v iframe OK.");
        }).catch((err) => {
          console.warn("Autoplay selhal (asi blokováno):", err);
        });
      }
    } catch (e) {
      console.warn("Nemúzu přistoupit k iframe (CORS):", e);
    }
  }

  function detectPlayerInsideIframe(iframe) {
    try {
      const doc = iframe.contentDocument || iframe.contentWindow.document;
      const playerFound = doc.querySelector('audio, video, .player, #player') !== null;
      console.log("Detekce přehrávače v iframe:", playerFound);
      return playerFound;
    } catch (e) {
      console.warn("Nemúzu detekovat obsah iframe kvůli CORS:", e);
      return false;
    }
  }

  function checkIfAnyAudioPlays(timeout = 3000) {
    return new Promise((resolve) => {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = ctx.createAnalyser();
      const source = ctx.createMediaElementSource(new Audio());
      source.connect(analyser);
      analyser.connect(ctx.destination);

      setTimeout(() => {
        const data = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(data);
        const maxVolume = Math.max(...data);
        console.log("Detekce hlasitosti:", maxVolume);
        resolve(maxVolume > 5);
      }, timeout);
    });
  }

  async function loadPlayerWithFailsafe() {
    console.log("Načítám FMCloud přehrávač...");
    removeAllIframes();

    let iframeLoaded = false;
    const iframe = loadIframe(PRIMARY_URL, () => {
      iframeLoaded = true;
      console.log("FMCloud iframe načten.");
    });

    const loadTimeout = new Promise((resolve) => {
      setTimeout(() => {
        if (!iframeLoaded) {
          console.warn("FMCloud iframe se nenačetl včas. Přepínám na záložní.");
          resolve(false);
        } else {
          resolve(true);
        }
      }, 5000);
    });

    const iframeOk = await loadTimeout;

    if (!iframeOk) {
      removeAllIframes();
      loadIframe(BACKUP_URL);
      return;
    }

    await new Promise(r => setTimeout(r, 3000));

    tryAutoplayInsideIframe(iframe);

    try {
      const audioDetected = await checkIfAnyAudioPlays();
      const playerDetected = detectPlayerInsideIframe(iframe);

      if (audioDetected || playerDetected) {
        console.log("FMCloud přehrávač detekován (zvuk nebo přehrávač). Všechno cajk.");
        return;
      } else {
        console.warn("FMCloud je tichý a přehrávač nenačten. Přepínám na záložní.");
        removeAllIframes();
        loadIframe(BACKUP_URL);
      }
    } catch (err) {
      console.error("Chyba při detekci:", err);
      removeAllIframes();
      loadIframe(BACKUP_URL);
    }
  }

  loadPlayerWithFailsafe();
</script>

</body>
</html>
