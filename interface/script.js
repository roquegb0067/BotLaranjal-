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
let nextStartTime = 0;

document.body.addEventListener('click', initAudio, { once: true });

async function initAudio() {
    // AudioContext com suporte a entrada e saída
    audioCtx = new(window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = totalBars * 2;
    dataArray = new Uint8Array(analyser.frequencyBinCount);
    
    analyser.connect(audioCtx.destination);
    
    // Conecta ao servidor Python usando o IP direto 127.0.0.1
    ws = new WebSocket('ws://127.0.0.1:8765');
    
    ws.onopen = () => {
        console.log("WebSocket conectado! Ligando microfone...");
        startMicrophone();
    };
    
    ws.onmessage = async (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'audio') {
            playPCMChunk(msg.data);
        }
    };
    
    animate();
}

// Captura o microfone e envia pacotes PCM 16kHz
async function startMicrophone() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: { sampleRate: 16000, channelCount: 1 } });
        const micContext = new(window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        const source = micContext.createMediaStreamSource(stream);
        const processor = micContext.createScriptProcessor(2048, 1, 1);
        
        // Substitua o envio dentro do onaudioprocess por JSON.stringify puro:
        processor.onaudioprocess = (e) => {
            if (!ws || ws.readyState !== WebSocket.OPEN) return;
            
            const inputData = e.inputBuffer.getChannelData(0);
            const int16Array = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                int16Array[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
            }
            
            let binary = '';
            const bytes = new Uint8Array(int16Array.buffer);
            for (let i = 0; i < bytes.byteLength; i++) {
                binary += String.fromCharCode(bytes[i]);
            }
            const base64Audio = btoa(binary);
            
            // Envia o áudio limpo em JSON
            ws.send(JSON.stringify({
                type: 'audio',
                data: base64Audio
            }));
        };
        
        
        source.connect(processor);
        processor.connect(micContext.destination);
    } catch (err) {
        console.error("Erro ao acessar o microfone:", err);
    }
}

function playPCMChunk(base64Data) {
    const binaryString = atob(base64Data);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    
    const int16Array = new Int16Array(bytes.buffer);
    const float32Array = new Float32Array(int16Array.length);
    for (let i = 0; i < int16Array.length; i++) {
        float32Array[i] = int16Array[i] / 32768.0;
    }
    
    const buffer = audioCtx.createBuffer(1, float32Array.length, 24000);
    buffer.getChannelData(0).set(float32Array);
    
    const source = audioCtx.createBufferSource();
    source.buffer = buffer;
    source.connect(analyser);
    
    const currentTime = audioCtx.currentTime;
    if (nextStartTime < currentTime) {
        nextStartTime = currentTime;
    }
    source.start(nextStartTime);
    nextStartTime += buffer.duration;
}

function animate() {
    requestAnimationFrame(animate);
    if (!analyser) return;
    
    analyser.getByteFrequencyData(dataArray);
    const centerIndex = (totalBars - 1) / 2;
    
    for (let i = 0; i < totalBars; i++) {
        const distanceFromCenter = Math.abs(i - centerIndex);
        const freqIndex = Math.floor(distanceFromCenter);
        const frequencyValue = dataArray[freqIndex] || 0;
        const scaleY = Math.max(0.05, frequencyValue / 255);
        bars[i].style.transform = `scaleY(${scaleY})`;
    }
    
    let bassSum = 0;
    for (let i = 0; i < 8; i++) {
        bassSum += dataArray[i];
    }
    const bassAvg = bassSum / 8;
    
    if (circle) {
        const circleScale = 1 + (bassAvg / 255) * 0.45;
        const glowRadius = 20 + (bassAvg / 255) * 60;
        circle.style.transform = `scale(${circleScale})`;
        circle.style.boxShadow = `0 0 ${glowRadius}px rgba(0, 255, 213, 0.8), 0 0 ${glowRadius * 1.5}px rgba(255, 0, 200, 0.6)`;
    }
}