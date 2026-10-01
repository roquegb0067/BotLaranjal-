const audio = document.getElementById('audio');
const visualizer = document.getElementById('visualizer');
const circle = document.getElementById('circle');

const totalBars = 64; 
const bars = [];

// Criar barras dinamicamente no DOM
for (let i = 0; i < totalBars; i++) {
    const bar = document.createElement('div');
    bar.classList.add('bar');
    visualizer.appendChild(bar);
    bars.push(bar);
}

let audioCtx, analyser, dataArray;

audio.addEventListener('play', () => {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioCtx.createMediaElementSource(audio);
        
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = totalBars * 2; 

        source.connect(analyser);
        analyser.connect(audioCtx.destination);

        dataArray = new Uint8Array(analyser.frequencyBinCount);
    }

    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
    
    animate();
});

function animate() {
    if (audio.paused) {
        bars.forEach(bar => bar.style.transform = 'scaleY(0.05)');
        if (circle) circle.style.transform = 'scale(1)';
        return;
    }

    analyser.getByteFrequencyData(dataArray);

    const centerIndex = (totalBars - 1) / 2;

    // 1. Atualizar barras (Graves concentrados no centro)
    for (let i = 0; i < totalBars; i++) {
        const distanceFromCenter = Math.abs(i - centerIndex);
        const freqIndex = Math.floor(distanceFromCenter);
        const frequencyValue = dataArray[freqIndex] || 0;
        
        const scaleY = Math.max(0.05, frequencyValue / 255);
        bars[i].style.transform = `scaleY(${scaleY})`;
    }

    // 2. Interatividade do Círculo (Pulsação com base nas frequências graves)
    let bassSum = 0;
    const bassBinCount = 8; // Analisa os primeiros 8 canais de frequência (graves)
    for (let i = 0; i < bassBinCount; i++) {
        bassSum += dataArray[i];
    }
    const bassAvg = bassSum / bassBinCount;

    // Calcula dynamic scale (de 1.0x até 1.45x) e a intensidade da luz neon
    const circleScale = 1 + (bassAvg / 255) * 0.45;
    const glowRadius = 20 + (bassAvg / 255) * 60;
    
    circle.style.transform = `scale(${circleScale})`;
    circle.style.boxShadow = `0 0 ${glowRadius}px rgba(0, 255, 213, 0.8), 0 0 ${glowRadius * 1.5}px rgba(255, 0, 200, 0.6)`;

    requestAnimationFrame(animate);
}
