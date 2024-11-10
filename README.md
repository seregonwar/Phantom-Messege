# Phantom Messenger

Un potente strumento per l'invio automatizzato di messaggi anonimi su diverse piattaforme, dotato di un'interfaccia grafica moderna e intuitiva.

## Caratteristiche

- 🌐 Supporto multi-piattaforma (NGL.link, Tellonym, ecc.)
- 🌍 Supporto multilingua (Italiano, Inglese)
- 🎯 Generazione intelligente e personalizzata di messaggi
- 🎨 Interfaccia grafica moderna con temi Dark/Light
- 📊 Statistiche in tempo reale e grafici interattivi
- 🔄 Gestione avanzata dei tempi di invio
- 💬 Supporto per slang e dialetti regionali
- 📱 Anteprima dei messaggi con suggerimenti
- 📈 Dashboard statistiche completo e dettagliato

## Piattaforme Supportate

- NGL.link
- Tellonym.me
- (Altri siti in arrivo...)

## Installazione

1. Clona il repository
   ```bash
   git clone https://github.com/yourusername/anonymous-message-sender.git
   cd anonymous-message-sender
   ```

2. Crea un ambiente virtuale (opzionale ma raccomandato)
   ```bash
   python -m venv venv
   source venv/bin/activate # Linux/Mac
   ```
   oppure
   ```bash
   venv\Scripts\activate # Windows
   ```

3. Installa le dipendenze
   ```bash
   pip install -r requirements.txt
   ```

4. Installa il pacchetto in modalità sviluppo
   ```bash
   pip install -e .
   ```

5. Avvia l'applicazione
   ```bash
   anonymous-sender-gui
   ```

## Struttura del Progetto

anonymous-message-sender/
├── src/
│ ├── core/ # Logica core
│ ├── gui/ # Interfaccia grafica
│ ├── parsers/ # Parser per i vari siti
│ ├── text_generator/ # Generazione testi
│ └── utils/ # Utilità
├── tests/ # Test unitari
└── docs/ # Documentazione

### Aggiungere Supporto per Nuovi Siti

1. Crea un nuovo parser che estende `BaseSiteParser`
2. Implementa i metodi richiesti:
   - `extract_data()`
   - `get_config()`
   - `get_supported_domains()`
3. Aggiungi il parser a `ParserFactory`