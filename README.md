# Phantom Messenger

This program is a concrete example of a p2p and dropbox system for license management, as a whole it integrates a fully functional spamming program and a key generator and manager.

## Features

- 🌐 Multi-platform support (NGL.link, Tellonym, etc.).
- 🌍 Multi-language support (Italian, English)
- 🎯 Intelligent and customized message generation
- 🎨 Modern graphical interface with Dark/Light themes
- 📊 Real-time statistics and interactive graphs
- 🔄 Advanced sending time management
- 💬 Support for slang and regional dialects
- 📱 Message preview with suggestions
- 📈 Comprehensive and detailed statistics dashboard

## Supported Platforms

- NGL.link
- Tellonym.me
- (More sites coming soon...)

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/anonymous-message-sender.git
cd anonymous-message-sender
```

2. Create a virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate # Linux/Mac
```
or
```bash
venv\Scripts/activate # Windows
```

3. Install the dependencies
```bash
pip install -r requirements.txt
```

4. Install the package in development mode
```bash
pip install -e .
```

5. Start the application
```bash
anonymous-sender-gui
```

## Project Structure
```bash
anonymous-message-sender/
├─── src/
│ ├─── core/ # Core logic
│ ├─── gui/ # Graphical interface
│ ├─── parsers/ # Parsers for various sites.
│ ├─── text_generator/ # Text generation
│ ├─── parser/ # page parser
│ ├─── utils/ 
├─── tools/ #key generator and agent manegement
```
