# TheDivineJob Automation

## Overview
Automates data entry on TheDivineJob.com, processing files one by one, entering "NA" for missing data, and using an NVIDIA GPU for efficient text parsing.

## Prerequisites
- Windows 10/11 PC with NVIDIA GPU.
- Python 3.8+.
- Chrome browser and ChromeDriver (add to PATH).
- Tesseract OCR for Windows (add to PATH: `C:\Program Files\Tesseract-OCR`).
- NVIDIA drivers and CUDA for GPU support.
- Ollama for Windows (run `ollama pull llama3-groq-tool-use:8b`).

## Setup
1. Clone the project:
   ```
   git clone <repository-url>
   cd thedivinejob_automation
   ```
2. Create and activate a virtual environment:
   ```
   python -m venv thedivinejob_env
   thedivinejob_env\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Start Ollama in a separate Command Prompt:
   ```
   ollama run llama3-groq-tool-use:8b
   ```
5. Update form field IDs in `src/config.py` (inspect the website using Chrome DevTools).

## Running the Script
1. Ensure Ollama is running.
2. Run the script:
   ```
   python src/main.py
   ```
3. Check logs in `logs/automation_log.txt` for progress and errors.

## Notes
- Verify TheDivineJob.com’s terms for automation compliance.
- Ensure your NVIDIA GPU is detected by Ollama for efficient processing.
