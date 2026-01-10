# 🚀 Project Setup & Collaboration Guide

## 📌 Getting Started
Follow these steps to set up the project on your local machine.


### <strong>1️. Prerequisites</strong>

- **Python**: 3.10 or 3.11 (recommended for library stability)
- **Git** installed on your system



### <strong>2️. Installation</strong>

#### 1. Clone the Repository
```bash
git clone https://github.com/Sankalpa-Giri/MAP_chatbot.git
cd MAP_chatbot
```
#### 2. Create a virtual environment (venv)
run manually:
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```
#### 3. API Keys Setup
For security, API keys are not included in this repository.
1. Create a folder named API Keys in the root directory.
2. Inside that folder, create the following three .txt files:
    Gemini_api_key.txt, 
    openweather_api_key.txt, 
    pico_access_key.txt
  
Paste your respective API keys into each file.

## 🤝 How to Collaborate
To ensure we don't break each other's code, please follow these rules:
1. Always use the Virtual Environment: Never install libraries globally.
2. Sync Dependencies: If you install a new library (e.g., pip install some-lib), update the requirements file immediately:
```bash
pip freeze > requirements.txt
```
3. Pull Before You Push: Always run git pull before starting work to ensure you have the latest changes from the other person.
4. Ignore the Junk: Do not commit venv/, __pycache__, or your actual API Keys/ folder.

## 🎙️ Troubleshooting
  - <summary> Microphone not detected: Ensure no other app is using your microphone and that your default recording device is set correctly in Windows Sound Settings. </summary>

  - <summary> Import Errors: Re-run pip install -r requirements.txt to ensure you have the latest libraries. </summary>
