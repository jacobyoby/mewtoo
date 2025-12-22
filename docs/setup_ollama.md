# Setting Up Ollama on Windows

## Quick Setup Guide

### Option 1: Download and Install (Recommended)

1. **Download Ollama for Windows:**
   - Visit: https://ollama.com/download
   - Download the Windows installer (OllamaSetup.exe)

2. **Install:**
   - Run the installer
   - Follow the installation wizard
   - Ollama will be added to your PATH automatically

3. **Verify Installation:**
   ```powershell
   ollama --version
   ```

4. **Pull a Model:**
   ```powershell
   ollama pull llama3.2
   ```
   
   Or for a smaller/faster model:
   ```powershell
   ollama pull llama3.2:1b
   ```

### Option 2: Using Winget (Windows Package Manager)

If you have winget installed:
```powershell
winget install Ollama.Ollama
```

Then pull a model:
```powershell
ollama pull llama3.2
```

### Option 3: Using Chocolatey

If you have Chocolatey installed:
```powershell
choco install ollama
```

Then pull a model:
```powershell
ollama pull llama3.2
```

## After Installation

1. **Start Ollama service** (usually starts automatically):
   ```powershell
   ollama serve
   ```

2. **Pull the model** (in a new terminal):
   ```powershell
   ollama pull llama3.2
   ```

3. **Test it works:**
   ```powershell
   ollama run llama3.2 "Hello, how are you?"
   ```

## Available Models

For Pokemon gameplay, these models work well:
- `llama3.2` - Good balance (recommended)
- `llama3.2:1b` - Smaller, faster
- `llama3.2:3b` - Better quality
- `mistral` - Alternative option
- `phi3` - Microsoft's small model

## Troubleshooting

- If `ollama` command not found, restart your terminal
- Make sure Ollama service is running: `ollama serve`
- Check if port 11434 is available (Ollama's default port)


