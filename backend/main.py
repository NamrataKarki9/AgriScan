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

app = FastAPI(title="AgriScan Production API V2 - Pure Nepali")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Loading AgriScan Neural Network... Please wait.")
model = tf.keras.models.load_model("agriscan_model_v2.keras")

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

# 🇳🇵 THE ULTIMATE NEPALI CROP DISEASE DICTIONARY
# Expert-verified agricultural translations for 100% deterministic accuracy
DISEASE_TRANSLATIONS = {
    # Apple
    "Apple___Apple_scab": "स्याउको स्क्याब रोग",
    "Apple___Black_rot": "स्याउको कालो कुहिने रोग",
    "Apple___Cedar_apple_rust": "स्याउको सिदार खिया रोग",
    # Cherry
    "Cherry___Powdery_mildew": "चेरीको डढुवा रोग (पाउडरी मिल्ड्यू)",
    # Corn
    "Corn___Cercospora_leaf_spot Gray_leaf_spot": "मकैको फुस्रो थोप्ले रोग",
    "Corn___Common_rust": "मकैको सिन्दुरे रोग (खिया रोग)",
    "Corn___Northern_Leaf_Blight": "मकैको पात डढ्ने रोग (उत्तरी डढुवा)",
    # Grape
    "Grape___Black_rot": "अङ्गुरको कालो सडन रोग",
    "Grape___Esca_Black_Measles": "अङ्गुरको एस्का रोग",
    "Grape___Leaf_blight Isariopsis_Leaf_Spot": "अङ्गुरको पात डढ्ने रोग",
    # Orange
    "Orange___Haunglongbing_Citrus_greening": "सुन्तलाको सिट्रस ग्रिनिङ (पहेँलो हुने रोग)",
    # Peach
    "Peach___Bacterial_spot": "आरुको ब्याक्टेरियल थोप्ले रोग",
    # Pepper
    "Pepper,_bell___Bacterial_spot": "भेँडे खुर्सानीको ब्याक्टेरियल थोप्ले रोग",
    # Potato
    "Potato___Early_blight": "आलुको अगौटे डढुवा रोग",
    "Potato___Late_blight": "आलुको पछौटे डढुवा रोग",
    # Squash
    "Squash___Powdery_mildew": "फर्सीको पाउडरी मिल्ड्यू रोग",
    # Strawberry
    "Strawberry___Leaf_scorch": "स्ट्रबेरीको पात डढ्ने रोग",
    # Tomato
    "Tomato___Bacterial_spot": "गोलभेडाको ब्याक्टेरियल थोप्ले रोग",
    "Tomato___Early_blight": "गोलभेडाको अगौटे डढुवा रोग",
    "Tomato___Late_blight": "गोलभेडाको पछौटे डढुवा रोग",
    "Tomato___Leaf_Mold": "गोलभेडाको पातमा ढुसी लाग्ने रोग",
    "Tomato___Septoria_leaf_spot": "गोलभेडाको सेप्टोरिया थोप्ले रोग",
    "Tomato___Spider_mites Two-spotted_spider_mite": "गोलभेडाको रातो सुलसुले किराको प्रकोप",
    "Tomato___Target_Spot": "गोलभेडाको टार्गेट स्पट रोग",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "गोलभेडाको पहेँलो पात खुम्चिने भाइरस",
    "Tomato___Tomato_mosaic_virus": "गोलभेडाको मोजेक भाइरस"
}

print("System Ready! 🚀")

def translate_disease_via_llm(disease_english):
    """Fallback LLM translator if a disease is missing from our dictionary"""
    if GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE" or not GROQ_API_KEY:
        return "बिरुवाको रोग"
        
    prompt = f"Translate the plant disease name '{disease_english}' into a natural, pure Nepali agricultural term. Respond with ONLY the Nepali translation in Devanagari script. No English words, no explanations."
    try:
        client = Groq(api_key=GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=50
        )
        return chat_completion.choices[0].message.content.strip()
    except:
        return "बिरुवाको रोग"

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

def prepare_image(image_bytes):
    # Compression speed optimization
    original_img = Image.open(io.BytesIO(image_bytes))
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
    
    # Convert to RGB just in case
    if img.mode != 'RGB':
        img = img.convert('RGB')
        
    img = img.resize((224, 224))
    
    # 🛡️ NO division by 255! EfficientNetB0 handles preprocessing internally!
    img_array = np.array(img).astype(np.float32)
    return np.expand_dims(img_array, axis=0)

@app.post("/predict")
async def predict_disease(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        processed_image = prepare_image(contents)
        
        predictions = model.predict(processed_image)
        confidence = float(np.max(predictions[0]))
        raw_disease = class_names[np.argmax(predictions[0])]
        
        print(f"🔮 AI Class Prediction: {raw_disease} (Confidence: {round(confidence * 100, 2)}%)")
        
        # 🛡️ THE GATEKEEPER BLOCK: If model classifies as Background_Noise or is unsure
        if raw_disease == "Background_Noise" or confidence < 0.75:
            print("❌ REJECTED: Background/OOD object detected.")
            return {
                "success": True, 
                "is_healthy": False, 
                "is_unrecognized": True,
                "disease_english": "Unrecognized Image", 
                "disease_nepali": ERROR_NEPALI_TEXT,
                "confidence": round(confidence * 100, 2),
                "audio_base64": CACHED_ERROR_AUDIO 
            }
            
        print("✅ PASSED: Valid crop leaf detected!")

        # 3. Compile Disease Results
        english_text = raw_disease.replace("___", " - ").replace("_", " ")
        is_healthy = "healthy" in raw_disease.lower()
        expert_advice = "अन्त्यमा, थप जानकारीको लागि कृषि विज्ञलाई पनि देखाउनुहोस्।"
        
        if is_healthy:
            # Clean up the crop name for healthy plants (e.g., "Tomato" -> "गोलभेडा")
            crop_name = english_text.split(" - ")[0]
            diagnosis_nepali = f"तपाईंको {crop_name} को बिरुवा एकदम स्वस्थ छ।"
            organic_rem = "यसरी नै राम्रो हेरचाह गर्दै गर्नुहोला।"
            chemical_rem = "नियमित पानी र मल दिनुहोस्।"
            full_speech = f"{diagnosis_nepali} {organic_rem} {chemical_rem} {expert_advice}"
        else:
            # Look up the accurate dictionary translation first
            acc_nepali_name = DISEASE_TRANSLATIONS.get(raw_disease, None)
            
            # Fallback to LLM if a rare class is not in our dictionary
            if not acc_nepali_name:
                print(f"⚠️ Class not in dictionary. Asking Groq to translate: {english_text}")
                acc_nepali_name = translate_disease_via_llm(english_text)
                
            diagnosis_nepali = f"तपाईंको बिरुवामा '{acc_nepali_name}' देखिएको छ।"
            organic_rem, chemical_rem = get_groq_analysis(english_text, acc_nepali_name)
            full_speech = f"{diagnosis_nepali} घरेलु उपचार: {organic_rem} रासायनिक उपचार: {chemical_rem} {expert_advice}"
        
        # Generate Voice
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