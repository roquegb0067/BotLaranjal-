use transcribe_rs::{SpeechModel, TranscribeOptions};
use transcribe_rs::whisper::WhisperModel;
use std::path::PathBuf;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Carregando o modelo Whisper no Termux...");

    // Carrega o modelo GGML binário que você baixou
    let mut model = WhisperModel::load(&PathBuf::from("models/ggml-tiny.bin"))?;

    // Configurações adicionais de transcrição
    let options = TranscribeOptions {
        language: Some("pt".to_string()), // Forçar idioma português
        ..Default::default()
    };

    println!("Iniciando transcrição do arquivo Gravando.wav...");

    let caminho_audio = PathBuf::from("Gravando.wav");
    let result = model.transcribe_file(&caminho_audio, &options)?; 

    println!("\n--- Texto Transcrito ---");
    println!("{}", result.text);
    println!("------------------------");

    Ok(())
}
