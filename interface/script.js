const visualizer = document.getElementById('visualizer');
const circle = document.getElementById('circle');

const totalBars = 64;
const bars = [];

for (let i = 0; i < totalBars; i++) {
    const bar = document.createElement('div');
    bar.classList.add('bar');
    visualizer.appendChild(bar);
    bars.push(bar);
}

let audioCtx;
let analyser;
let dataArray;
let ws;
let nextStartTime = 0; // Controla a fila de reprodução fluida dos fragmentos

// Inicializa a conexão e o AudioContext após clique do usuário
document.body.addEventListener('click', initAudio, { once: true });

function initAudio() {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = totalBars * 2;
    dataArray = new Uint8Array(analyser.frequencyBinCount);

    // Conecta o analisador aos alto-falantes
    analyser.connect(audioCtx.destination);

    // Conecta ao servidor Python Bridge
    ws = new WebSocket('ws://localhost:8765');

    ws.onmessage = async (event) => {
        const msg = JSON.parse(event.data);

        if (msg.type === 'audio') {
            playPCMChunk(msg.data);
        }
    };

    // Inicia a renderização do visualizador
    animate();
}

// Decodifica PCM 16-bit 24kHz bruto enviado em base64 e envia ao Analyser
function playPCMChunk(base64Data) {
    const binaryString = atob(base64Data);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }

    // Converte Bytes PCM 16-bit para Float32 (exigido pelo Web Audio API)
    const int16Array = new Int16Array(bytes.buffer);
    const float32Array = new Float32Array(int16Array.length);
    for (let i = 0; i < int16Array.length; i++) {
        float32Array[i] = int16Array[i] / 32768.0;
    }

    // Cria o buffer de áudio
    const buffer = audioCtx.createBuffer(1, float32Array.length, 24000);
    buffer.getChannelData(0).set(float32Array);

    const source = audioCtx.createBufferSource();
    source.buffer = buffer;

    // ROTA IMPORTANTE: Source -> Analyser -> Alto-falantes
    source.connect(analyser);

    // Agenda a reprodução sequencial sem lacunas/estalos
    const currentTime = audioCtx.currentTime;
    if (nextStartTime < currentTime) {
        nextStartTime = currentTime;
    }
    source.start(nextStartTime);
    nextStartTime += buffer.duration;
}

// Animação contínua das barras e círculo
function animate() {
    requestAnimationFrame(animate);

    if (!analyser) return;

    analyser.getByteFrequencyData(dataArray);
    const centerIndex = (totalBars - 1) / 2;

    // 1. Atualiza as barras
    for (let i = 0; i < totalBars; i++) {
        const distanceFromCenter = Math.abs(i - centerIndex);
        const freqIndex = Math.floor(distanceFromCenter);
        const frequencyValue = dataArray[freqIndex] || 0;

        const scaleY = Math.max(0.05, frequencyValue / 255);
        bars[i].style.transform = `scaleY(${scaleY})`;
    }

    // 2. Pulsação do Círculo com Graves
    let bassSum = 0;
    const bassBinCount = 8;
    for (let i = 0; i < bassBinCount; i++) {
        bassSum += dataArray[i];
    }
    const bassAvg = bassSum / bassBinCount;

    const circleScale = 1 + (bassAvg / 255) * 0.45;
    const glowRadius = 20 + (bassAvg / 255) * 60;

    if (circle) {
        circle.style.transform = `scale(${circleScale})`;
        circle.style.boxShadow = `0 0 ${glowRadius}px rgba(0, 255, 213, 0.8), 0 0 ${glowRadius * 1.5}px rgba(255, 0, 200, 0.6)`;
    }
}
