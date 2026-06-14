# 🌿 AgriScan — AI Crop Disease Detection

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-FF6F00?style=flat&logo=tensorflow)
![Accuracy](https://img.shields.io/badge/Accuracy-99.40%25-brightgreen?style=flat)

> A zero-friction AI mobile web app that helps Nepali farmers 
> instantly diagnose crop diseases — with results spoken aloud 
> in pure Nepali language.

---

## 🎯 Problem

Over 60% of Nepal's population depends on farming. When crops 
get diseased, most farmers cannot identify the problem early 
enough due to lack of access to experts, language barriers, 
and low digital literacy.

**AgriScan eliminates every barrier:**
- No registration or login required
- Results spoken in pure Nepali (Devanagari)
- Works on any smartphone camera
- Designed for zero technical literacy

---

## ✨ How It Works
Farmer takes photo
↓
Background removed (rembg)
↓
EfficientNetB0 classifies disease (99.40% accuracy)
↓
Groq LLM generates Nepali remedies
↓
gTTS speaks result aloud in Nepali
---

## 🤖 AI Model

| Detail | Value |
|---|---|
| Architecture | EfficientNetB0 (Transfer Learning) |
| Dataset | PlantVillage + Background_Noise |
| Classes | 39 (38 diseases + 1 noise class) |
| Validation Accuracy | **99.40%** |
| Training Platform | Google Colab (T4 GPU) |
| Model Size | 31.9 MB |

### Training Strategy
- **Phase 1:** Warm-up — frozen backbone, train head only (5 epochs)
- **Phase 2:** Fine-tuning — unfreeze top 30 layers (14 epochs)
- **Augmentation:** Flip, Rotation, Zoom, Brightness, Contrast, Translation

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React.js + Vite + Tailwind CSS |
| Backend | Python + FastAPI + Uvicorn |
| AI Model | TensorFlow/Keras + EfficientNetB0 |
| Background Removal | rembg |
| Voice Output | gTTS (Nepali) |
| LLM Remedies | Groq API (Llama-3.3-70b) |

---

## 🚀 Setup & Run

### Backend
```bash
cd backend
pip install fastapi uvicorn tensorflow pillow rembg[cpu] gTTS groq python-multipart
python -m uvicorn main:app --host 0.0.0.0 --port 8555 --reload


### Frontend
cd frontend
npm install
npm run dev -- --host
Open the Network URL on your phone browser.
Make sure phone and laptop are on the same WiFi.

App Flow
Home → Tap camera button
Loading → AI analyzes image
Color Reveal → Green (healthy) / Red (disease) / Gray (invalid)
Result → Nepali voice plays automatically with treatment plan


Key Design Decisions
Challenge	Solution
Farmers can't read	Color-coded screens + voice output
Real-world backgrounds	rembg background removal
Random object uploads	Background_Noise class in model
Lab vs real photos	Heavy data augmentation
Language barrier	Pure Nepali Devanagari voice


AgriScan/
├── backend/
│   ├── main.py
│   ├── agriscan_model_v2.keras
│   └── class_names.json
└── frontend/
    └── src/
        └── App.jsx
