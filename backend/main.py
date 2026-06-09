import os

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
from PIL import Image
import numpy as np
import io
import json
import base64
from rembg import remove
from gtts import gTTS
from groq import Groq

# 🔑 PUT YOUR GROQ API KEY HERE
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI(title="AgriScan Multi-Model Production API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Loading AI Models... Please wait.")
# Model 1: The Specialist Doctor (Leaf Disease Classifier)
disease_model = tf.keras.models.load_model("agriscan_model.h5")

# Model 2: The Security Guard (Leaf vs Non-Leaf Classifier)
gatekeeper_model = tf.keras.models.load_model("leaf_gatekeeper.h5")

with open("class_names.json", "r") as f:
    class_names = json.load(f)

# Caching the Nepali error audio in memory for instant speed!
print("Caching Audio...")
ERROR_NEPALI_TEXT = "मैले यो फोटो चिन्न सकिन। कृपया स्पष्ट बिरुवाको पातको फोटो खिच्नुहोला।"
tts_err = gTTS(text=ERROR_NEPALI_TEXT, lang='ne')
err_fp = io.BytesIO()
tts_err.write_to_fp(err_fp)
err_fp.seek(0)
CACHED_ERROR_AUDIO = base64.b64encode(err_fp.read()).decode('utf-8')

DISEASE_TRANSLATIONS = {
    "Tomato___Late_blight": "गोलभेडाको डढुवा रोग",
    "Tomato___Early_blight": "गोलभेडाको अर्ली ब्लाइट",
    "Apple___Apple_scab": "स्याउको स्क्याब रोग",
}

print("System Ready! 🚀")

def is_a_leaf(image_pil):
    """Uses custom leaf_gatekeeper.h5 to check if the image is actually a leaf"""
    try:
        # Resize and preprocess exactly like we did in Colab training
        img = image_pil.resize((224, 224))
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        # Predict: Class 0 is Leaf, Class 1 is Non-Leaf
        prediction = gatekeeper_model.predict(img_array)[0][0]
        print(f"📊 Gatekeeper Raw Score (0=Leaf, 1=Garbage): {prediction}")
        
        # If prediction is less than 0.5, it is closer to 0 (Leaf)
        return prediction < 0.5
    except Exception as e:
        print("Gatekeeper Error:", e)
        return True # Fallback

def get_groq_analysis(disease_english, disease_nepali):
    if GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE" or not GROQ_API_KEY:
        return "नियमित हेरचाह गर्नुहोस्।", "विषादी प्रयोग अघि विज्ञलाई सोध्नुहोस्।"

    prompt = f"""
    The plant disease is '{disease_english}' (Nepali: {disease_nepali}). 
    Provide exactly one organic remedy and one chemical remedy in pure Devanagari script.
    Do not mix English letters.
    Output ONLY in this JSON format:
    {{
      "organic_remedy": "Organic home remedy in Nepali",
      "chemical_remedy": "Chemical remedy in Nepali"
    }}
    """
    try:
        client = Groq(api_key=GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a Nepali agriculture API. Output valid JSON in Devanagari script."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile", 
            response_format={"type": "json_object"},
            temperature=0.2, 
            max_tokens=200,
        )
        data = json.loads(chat_completion.choices[0].message.content)
        return data.get("organic_remedy", ""), data.get("chemical_remedy", "")
    except Exception as e:
        return "कृषि विज्ञसँग सल्लाह लिनुहोस्।", "कृषि विज्ञसँग सल्लाह लिनुहोस्।"

def prepare_and_diagnose(original_img):
    """Only cleans up and resizes the image AFTER we know it's a real leaf"""
    # Create smaller thumbnail for fast background removal
    original_img.thumbnail((500, 500))
    temp_io = io.BytesIO()
    original_img.save(temp_io, format="PNG")
    small_bytes = temp_io.getvalue()

    # Background removal
    no_bg_bytes = remove(small_bytes)
    img = Image.open(io.BytesIO(no_bg_bytes))
    
    if img.mode == 'RGBA':
        alpha = img.split()[3]
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=alpha)
        img = background
        
    img = img.resize((224, 224))
    img_array = np.array(img) / 255.0
    return np.expand_dims(img_array, axis=0)

@app.post("/predict")
async def predict_disease(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        original_img = Image.open(io.BytesIO(contents))
        
        # 🛡️ STAGE 1: THE SECURITY GUARD CHECK (Leaf vs Non-Leaf)
        if not is_a_leaf(original_img):
            print("❌ REJECTED: Custom gatekeeper detected non-leaf/garbage object.")
            return {
                "success": True, "is_healthy": False, "is_unrecognized": True,
                "disease_english": "Unrecognized Image", "disease_nepali": ERROR_NEPALI_TEXT,
                "confidence": 0, "audio_base64": CACHED_ERROR_AUDIO 
            }
            
        print("✅ PASSED: Leaf detected. Proceeding to background removal and diagnosis...")
        
        # 🩺 STAGE 2: THE SPECIALIST DOCTOR (Disease Diagnosis)
        processed_image = prepare_and_diagnose(original_img)
        predictions = disease_model.predict(processed_image)
        confidence = float(np.max(predictions[0]))
        raw_disease = class_names[np.argmax(predictions[0])]
        
        # If the specialist is deeply confused even on a leaf
        if confidence < 0.70:
            return {
                "success": True, "is_healthy": False, "is_unrecognized": True,
                "disease_english": "Unrecognized Image", "disease_nepali": ERROR_NEPALI_TEXT,
                "confidence": round(confidence * 100, 2),
                "audio_base64": CACHED_ERROR_AUDIO 
            }

        # 3. Compile final response
        english_text = raw_disease.replace("___", " - ").replace("_", " ")
        is_healthy = "healthy" in raw_disease.lower()
        expert_advice = "अन्त्यमा, थप जानकारीको लागि कृषि विज्ञलाई पनि देखाउनुहोस्।"
        
        if is_healthy:
            diagnosis_nepali = "तपाईंको बिरुवा एकदम स्वस्थ छ।"
            organic_rem = "यसरी नै राम्रो हेरचाह गर्दै गर्नुहोला।"
            chemical_rem = "नियमित पानी र मल दिनुहोस्।"
            full_speech = f"{diagnosis_nepali} {organic_rem} {chemical_rem} {expert_advice}"
        else:
            acc_nepali_name = DISEASE_TRANSLATIONS.get(raw_disease, english_text)
            diagnosis_nepali = f"तपाईंको बिरुवामा '{acc_nepali_name}' देखिएको छ।"
            organic_rem, chemical_rem = get_groq_analysis(english_text, acc_nepali_name)
            full_speech = f"{diagnosis_nepali} घरेलु उपचार: {organic_rem} रासायनिक उपचार: {chemical_rem} {expert_advice}"
        
        tts = gTTS(text=full_speech, lang='ne')
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)

        return {
            "success": True,
            "is_healthy": is_healthy,
            "is_unrecognized": False,
            "disease_english": english_text,
            "disease_nepali": diagnosis_nepali,
            "remedy_organic": organic_rem,     
            "remedy_chemical": chemical_rem,   
            "expert_advice": expert_advice,    
            "confidence": round(confidence * 100, 2),
            "audio_base64": base64.b64encode(audio_fp.read()).decode('utf-8')
        }
    except Exception as e:
        print("Crash Log:", e)
        return {"success": False, "error": str(e)}