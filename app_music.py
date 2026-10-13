import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Flappy Bird",
    page_icon="🐦",
    layout="centered"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #e0f7ff, #f5fff0);
}
.block-container {
    max-width: 900px;
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.title("🐦 Flappy Bird")
st.caption("Chọn chế độ và cố gắng đạt điểm cao nhất!")

html = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #eaf8ff;
}
.panel {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    justify-content: center;
    padding: 10px;
}
button, select {
    padding: 11px 15px;
    border: 0;
    border-radius: 10px;
    background: #16803c;
    color: white;
    font-weight: bold;
    cursor: pointer;
}
select { background: #17445b; }
.stats {
    display: flex;
    justify-content: space-around;
    padding: 10px;
    color: #17445b;
    font-weight: bold;
}
canvas {
    display: block;
    width: 100%;
    height: auto;
    border-radius: 14px;
    border: 3px solid white;
    box-shadow: 0 8px 24px #24536a30;
    touch-action: manipulation;
}
#youtubePlayer {
    position: fixed;
    width: 1px;
    height: 1px;
    overflow: hidden;
    opacity: 0.01;
    pointer-events: none;
    left: 0;
    bottom: 0;
}
#musicToggle { background: #17445b; }
#musicStatus { padding-top: 0; }
.help {
    text-align: center;
    color: #527080;
    font-size: 13px;
    padding: 10px;
}
</style>
</head>
<body>

<div class="panel">
    <label for="mode">Chế độ:</label>
    <select id="mode">
        <option value="easy">🌱 Dễ</option>
        <option value="normal" selected>⚡ Thường</option>
        <option value="hard">🔥 Khó</option>
    </select>
    <button id="start">▶ Bắt đầu</button>
    <button id="pause">⏸ Tạm dừng</button>
    <button id="restart">↻ Chơi lại</button>
    <button id="musicToggle" type="button">🎵 Bật nhạc</button>
</div>
<div id="musicStatus" class="help">Nhấn “Bật nhạc” để phát nhạc nền YouTube.</div>
<div id="youtubePlayer" aria-hidden="true"></div>

<div class="stats">
    <span>Điểm: <span id="score">0</span></span>
    <span>Kỷ lục: <span id="best">0</span></span>
</div>

<canvas id="game" width="720" height="540"></canvas>
<div class="help">
    Nhấn SPACE / ↑ hoặc chạm màn hình để bay.
    Tránh ống xanh và mặt đất!
</div>

<script>
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const W = 720, H = 540, ground = 55;
const birdX = 150, birdR = 15;

const modes = {
    easy:   {gravity: 0.32, flap: -6.5, speed: 2.5, gap: 190, interval: 115},
    normal: {gravity: 0.40, flap: -7.0, speed: 3.3, gap: 155, interval: 100},
    hard:   {gravity: 0.48, flap: -7.6, speed: 4.2, gap: 130, interval: 90}
};

let mode = "normal";
let birdY = 220, velocity = 0;
let pipes = [], score = 0, frame = 0;
let state = "ready";
let lastTime = 0, worldTime = 0;
let best = loadBest();

// Nhạc nền YouTube: trình duyệt thường yêu cầu người chơi bấm nút
// trước khi cho phép phát âm thanh.
let musicPlayer = null;
let musicReady = false;
let musicOn = false;
const musicButton = document.getElementById("musicToggle");
const musicStatus = document.getElementById("musicStatus");

function setMusicStatus(message) {
    musicStatus.textContent = message;
}

function onYouTubeIframeAPIReady() {
    musicPlayer = new YT.Player("youtubePlayer", {
        width: "200",
        height: "113",
        videoId: "TlWNp1OEvwU",
        playerVars: {
            autoplay: 0,
            controls: 0,
            loop: 1,
            playlist: "TlWNp1OEvwU",
            playsinline: 1,
            rel: 0
        },
        events: {
            onReady: function() {
                musicReady = true;
                setMusicStatus("Nhạc nền đã sẵn sàng. Nhấn “Bật nhạc” để nghe.");
            },
            onStateChange: function(event) {
                if (event.data === YT.PlayerState.ENDED && musicOn) {
                    musicPlayer.seekTo(0);
                    musicPlayer.playVideo();
                }
            },
            onError: function() {
                setMusicStatus("Không thể phát video này. Hãy kiểm tra kết nối hoặc quyền nhúng YouTube.");
            }
        }
    });
}

(function loadYouTubeAPI() {
    const tag = document.createElement("script");
    tag.src = "https://www.youtube.com/iframe_api";
    document.head.appendChild(tag);
})();

musicButton.addEventListener("click", function() {
    if (!musicReady || !musicPlayer) {
        setMusicStatus("Đang tải trình phát YouTube, hãy thử lại sau vài giây.");
        return;
    }
    if (!musicOn) {
        musicOn = true;
        musicPlayer.setVolume(45);
        musicPlayer.playVideo();
        musicButton.textContent = "🔇 Tắt nhạc";
        setMusicStatus("Nhạc nền đang bật. Nhấn “Tắt nhạc” để tắt.");
    } else {
        musicOn = false;
        musicPlayer.pauseVideo();
        musicButton.textContent = "🎵 Bật nhạc";
        setMusicStatus("Nhạc nền đã tắt.");
    }
});

function loadBest() {
    try {
        return JSON.parse(localStorage.getItem("flappy_best") ||
            '{"easy":0,"normal":0,"hard":0}');
    } catch (e) {
        return {easy:0, normal:0, hard:0};
    }
}

function saveBest() {
    try {
        localStorage.setItem("flappy_best", JSON.stringify(best));
    } catch (e) {}
}

function config() { return modes[mode]; }

function updateStats() {
    document.getElementById("score").textContent = score;
    document.getElementById("best").textContent = best[mode] || 0;
}

function reset() {
    birdY = 220;
    velocity = 0;
    score = 0;
    frame = 0;
    pipes = [];
    addPipe(520);
    addPipe(850);
    updateStats();
}

function addPipe(x) {
    const c = config();
    const min = 55;
    const max = H - ground - c.gap - 55;
    pipes.push({
        x: x,
        top: min + Math.random() * (max - min),
        passed: false
    });
}

function startGame() {
    if (state === "ready" || state === "over") reset();
    state = "playing";
    lastTime = performance.now();
}

function restartGame() {
    reset();
    state = "playing";
    lastTime = performance.now();
}

function flap() {
    if (state === "ready" || state === "over") startGame();
    if (state !== "playing") return;
    velocity = config().flap;
}

function pauseGame() {
    if (state === "playing") state = "paused";
    else if (state === "paused") {
        state = "playing";
        lastTime = performance.now();
    }
}

document.getElementById("start").onclick = startGame;
document.getElementById("pause").onclick = pauseGame;
document.getElementById("restart").onclick = restartGame;

document.getElementById("mode").onchange = function() {
    mode = this.value;
    reset();
    state = "ready";
};

canvas.addEventListener("pointerdown", function(e) {
    e.preventDefault();
    flap();
});

window.addEventListener("keydown", function(e) {
    if (["Space", "ArrowUp", "KeyW"].includes(e.code)) {
        e.preventDefault();
        if (!e.repeat) flap();
    }
    if (e.code === "KeyP") pauseGame();
    if (e.code === "KeyR") restartGame();
});

function drawBackground() {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, "#55c8f5");
    g.addColorStop(1, "#d9f7ff");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);

    // Mây
    for (let i = 0; i < 4; i++) {
        let x = (i * 220 - worldTime * 0.3) % (W + 130);
        if (x < -100) x += W + 130;
        const y = 65 + i % 3 * 55;
        ctx.fillStyle = "rgba(255,255,255,0.85)";
        ctx.beginPath();
        ctx.arc(x, y, 20, 0, Math.PI * 2);
        ctx.arc(x + 25, y - 12, 26, 0, Math.PI * 2);
        ctx.arc(x + 50, y, 19, 0, Math.PI * 2);
        ctx.fill();
    }

    ctx.fillStyle = "#a5df8d";
    ctx.beginPath();
    ctx.moveTo(0, H-ground);
    for (let x = 0; x <= W; x += 12) {
        ctx.lineTo(x, H-ground - 18 - Math.sin(x * 0.025) * 13);
    }
    ctx.lineTo(W, H-ground);
    ctx.fill();
}

function drawPipe(p) {
    const c = config();
    const bottom = p.top + c.gap;
    const pipeW = 65;

    const grad = ctx.createLinearGradient(p.x, 0, p.x+pipeW, 0);
    grad.addColorStop(0, "#168b38");
    grad.addColorStop(0.4, "#58dc55");
    grad.addColorStop(1, "#218a37");

    ctx.fillStyle = grad;
    ctx.strokeStyle = "#176b32";
    ctx.lineWidth = 3;

    // Ống trên
    ctx.fillRect(p.x, 0, pipeW, p.top-23);
    ctx.strokeRect(p.x, 0, pipeW, p.top-23);
    ctx.fillRect(p.x-6, p.top-25, pipeW+12, 25);
    ctx.strokeRect(p.x-6, p.top-25, pipeW+12, 25);

    // Ống dưới
    ctx.fillRect(p.x, bottom+25, pipeW, H-ground-bottom-25);
    ctx.strokeRect(p.x, bottom+25, pipeW, H-ground-bottom-25);
    ctx.fillRect(p.x-6, bottom, pipeW+12, 25);
    ctx.strokeRect(p.x-6, bottom, pipeW+12, 25);

    ctx.fillStyle = "#ffffff40";
    ctx.fillRect(p.x+9, 0, 8, Math.max(0, p.top-28));
    ctx.fillRect(p.x+9, bottom+27, 8,
        Math.max(0, H-ground-bottom-27));
}

function drawBird() {
    ctx.save();
    ctx.translate(birdX, birdY);
    ctx.rotate(Math.max(-0.5, Math.min(0.7, velocity * 0.05)));

    // Cánh
    ctx.fillStyle = "#f4a51c";
    ctx.beginPath();
    ctx.ellipse(-6, 5 + Math.sin(worldTime*.02)*3,
        11, 7, -0.3, 0, Math.PI*2);
    ctx.fill();

    // Thân
    const grad = ctx.createRadialGradient(-6,-7,2,0,0,22);
    grad.addColorStop(0,"#fff98c");
    grad.addColorStop(1,"#f8bc14");
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(0,0,birdR,0,Math.PI*2);
    ctx.fill();
    ctx.strokeStyle = "#d79516";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Mắt
    ctx.fillStyle = "#fff";
    ctx.beginPath();
    ctx.arc(7,-6,6,0,Math.PI*2);
    ctx.fill();
    ctx.fillStyle = "#18364a";
    ctx.beginPath();
    ctx.arc(9,-6,2.5,0,Math.PI*2);
    ctx.fill();

    // Mỏ
    ctx.fillStyle = "#ff7138";
    ctx.beginPath();
    ctx.moveTo(13,0);
    ctx.lineTo(27,5);
    ctx.lineTo(13,9);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
}

function collision(p) {
    const r = birdR - 2;
    const c = config();
    const bottom = p.top + c.gap;
    const pipeW = 65;

    if (birdY-r < 0 || birdY+r > H-ground) return true;

    // Hình chữ nhật va chạm
    function hitRect(x,y,w,h) {
        const px = Math.max(x, Math.min(birdX, x+w));
        const py = Math.max(y, Math.min(birdY, y+h));
        return (birdX-px)**2 + (birdY-py)**2 < r*r;
    }

    return hitRect(p.x,0,pipeW,p.top-25) ||
        hitRect(p.x-6,p.top-25,pipeW+12,25) ||
        hitRect(p.x,bottom+25,pipeW,H-ground-bottom-25) ||
        hitRect(p.x-6,bottom,pipeW+12,25);
}

function gameOver() {
    state = "over";
    if (score > (best[mode] || 0)) {
        best[mode] = score;
        saveBest();
    }
    updateStats();
}

function update(dt) {
    worldTime += dt;
    if (state !== "playing") return;

    const c = config();
    const speed = c.speed + Math.min(score*0.04, 2);

    velocity += c.gravity * dt;
    birdY += velocity * dt;
    frame += dt;

    if (frame >= Math.max(68, c.interval-score*.3)) {
        frame = 0;
        addPipe(W+10);
    }

    for (const p of pipes) {
        p.x -= speed * dt;

        if (!p.passed && p.x+65 < birdX) {
            p.passed = true;
            score++;
            updateStats();
        }

        if (collision(p)) {
            gameOver();
            break;
        }
    }
    pipes = pipes.filter(p => p.x > -100);
}

function roundRect(x,y,w,h,r,color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.roundRect(x,y,w,h,r);
    ctx.fill();
}

function drawOverlay(title, subtitle) {
    ctx.fillStyle = "#15374b70";
    ctx.fillRect(0,0,W,H);

    roundRect(100,175,W-200,190,20,"#ffffffed");

    ctx.textAlign = "center";
    ctx.fillStyle = "#16803c";
    ctx.font = "bold 36px Arial";
    ctx.fillText(title,W/2,230);

    ctx.fillStyle = "#24485c";
    ctx.font = "19px Arial";
    ctx.fillText(subtitle,W/2,275);

    ctx.font = "15px Arial";
    ctx.fillStyle = "#617b8c";
    ctx.fillText("SPACE / ↑ / Chạm để bay",W/2,320);
}

function render() {
    drawBackground();
    pipes.forEach(drawPipe);
    drawBird();

    // Mặt đất
    ctx.fillStyle = "#d6b86e";
    ctx.fillRect(0,H-ground,W,ground);
    ctx.fillStyle = "#65c84d";
    ctx.fillRect(0,H-ground,W,13);
    ctx.fillStyle = "#bda05c";
    for (let x=0; x<W; x+=35) {
        ctx.fillRect(x,H-ground+28,18,5);
    }

    // Điểm trên màn hình game
    ctx.textAlign = "center";
    ctx.font = "bold 38px Arial";
    ctx.lineWidth = 4;
    ctx.strokeStyle = "#ffffffaa";
    ctx.strokeText(score,W/2,65);
    ctx.fillStyle = "#ffffff";
    ctx.fillText(score,W/2,65);

    if (state === "ready") {
        drawOverlay("FLAPPY BIRD","Sẵn sàng chưa? Nhấn Bắt đầu!");
    } else if (state === "paused") {
        drawOverlay("TẠM DỪNG","Nhấn Tiếp tục để chơi tiếp.");
    } else if (state === "over") {
        drawOverlay("GAME OVER","Điểm: "+score+" | Kỷ lục: "+best[mode]);
    }
}

function loop(now) {
    if (!lastTime) lastTime = now;
    const dt = Math.min((now-lastTime)/16.667, 2);
    lastTime = now;
    update(dt);
    render();
    requestAnimationFrame(loop);
}

reset();
requestAnimationFrame(loop);
</script>
</body>
</html>
"""

components.html(html, height=760, scrolling=False)

st.markdown(
    "🌱 **Dễ:** ống chậm, khoảng trống lớn · "
    "⚡ **Thường:** cân bằng · "
    "🔥 **Khó:** ống nhanh, khoảng trống hẹp"
)