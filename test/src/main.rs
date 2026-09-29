use transcribe_rs::{SpeechModel, TranscribeOptions};
use transcribe_rs::onnx::sense_voice::{SenseVoiceModel, SenseVoiceParams};
use std::path::PathBuf;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Carregando o modelo de transcrição...");

    // 1. Carregue o modelo local apontando para a pasta onde salvou os pesos/arquivos ONNX
    let mut model = SenseVoiceModel::load(
        &PathBuf::from("models/sense-voice-small-int8"),
        &transcribe_rs::onnx::Quantization::Int8,
    )?;

    // 2. Configurações adicionais de transcrição
    let options = TranscribeOptions {
        language: Some("pt".to_string()), // Forçar português
        ..Default::default()
    };

    println!("Iniciando transcrição do arquivo Gravando.wav...");

    // 3. Executa a transcrição diretamente do arquivo WAV convertido
    let caminho_audio = PathBuf::from("Gravando.wav");
    
    // CORRIGIDO: de 'caminhi_audio' para 'caminho_audio'
    let result = model.transcribe_file(&caminho_audio, &options)?; 

    // 4. Exibe o resultado final na tela
    println!("\n--- Texto Transcrito ---");
    println!("{}", result.text);
    println!("------------------------");

    Ok(())
}
