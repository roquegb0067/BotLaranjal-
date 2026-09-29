use transcribe_rs::{SpeechModel, TranscribeOptions};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Configurações de transcrição (idioma, tradução, etc.)
    let options = TranscribeOptions {
        language: Some("pt".to_string()),
        ..Default::default()
    };

    // O carregamento e uso dependem da engine escolhida (ex: Whisper ou SenseVoice)
    // Consulte a documentação oficial da biblioteca para instanciar o modelo específico.
    println!("Iniciando transcrição...");

    Ok(())
}
