const API_KEY = "YOUR_API_KEY";
const MODEL_NAME = "gemini-3.8-live";
const WS_URL = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key=${API_KEY}`;

const websocket = new WebSocket(WS_URL);

websocket.onopen = () => {
  console.log('WebSocket Connected');

  // 1. Send the initial configuration
  const setupMessage = {
    setup: {
      model: `models/${MODEL_NAME}`,
      responseModalities: ['AUDIO'],
      systemInstruction: {
        parts: [{ text: 'You are a helpful assistant.' }]
      }
    }
  };
  websocket.send(JSON.stringify(setupMessage));
  console.log('Configuration sent');
};

websocket.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log('Received:', response);
  // Handle different types of responses here
};

websocket.onerror = (error) => {
  console.error('WebSocket Error:', error);
};

websocket.onclose = () => {
  console.log('WebSocket Closed');
};
const audio = document.getElementById('audio');
const visualizer = document.getElementById('visualizer');

// Define quantas barras queres (por ex., 32 barras)
const totalBars = 64; 
const bars = [];

// Criar as barras dinamicamente no DOM
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
        // fftSize de 64 gera 32 canais de frequência (64 / 2 = 32)
        analyser.fftSize = totalBars * 2; 

        source.connect(analyser);
        analyser.connect(audioCtx.destination);

        dataArray = new Uint8Array(analyser.frequencyBinCount);
    }
    
    animate();
});

function animate() {
    if (audio.paused) {
        bars.forEach(bar => bar.style.transform = 'scaleY(0.05)');
        return;
    }

    analyser.getByteFrequencyData(dataArray);

    const centerIndex = (totalBars - 1) / 2;

    for (let i = 0; i < totalBars; i++) {
        // 1. Calcula a distância da barra atual até ao centro
        const distanceFromCenter = Math.abs(i - centerIndex);
        
        // 2. Mapeia essa distância para o índice de frequência (0 = graves no centro)
        const freqIndex = Math.floor(distanceFromCenter);
        
        // 3. Obtém a frequência correspondente
        const frequencyValue = dataArray[freqIndex] || 0; // Valor de 0 a 255
        
        // 4. Aplica a escala vertical
        const scaleY = Math.max(0.05, frequencyValue / 255);
        
        bars[i].style.transform = `scaleY(${scaleY})`;
    }

    requestAnimationFrame(animate);
}
websocket.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log('Received:', response);

  if (response.serverContent) {
    const serverContent = response.serverContent;
    // Receiving Audio
    if (serverContent.modelTurn?.parts) {
      for (const part of serverContent.modelTurn.parts) {
        if (part.inlineData) {
          const audioData = part.inlineData.data; // Base64 encoded string
          // Process or play audioData
          console.log(`Received audio data (base64 len: ${audioData.length})`);
        }
      }
    }

    // Receiving Text Transcriptions
    if (serverContent.inputTranscription) {
      console.log('User:', serverContent.inputTranscription.text);
    }
    if (serverContent.outputTranscription) {
      console.log('Gemini:', serverContent.outputTranscription.text);
    }
  }

  // Handling Tool Calls
  if (response.toolCall) {
    handleToolCall(response.toolCall);
  }
};