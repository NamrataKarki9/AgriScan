import React, { useState, useRef } from 'react';
import { Camera, Upload, Activity, CheckCircle, AlertTriangle, Volume2, ShieldPlus, Leaf, XCircle, HeartPulse } from 'lucide-react';

export default function App() {
  const [imagePreview, setImagePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [appPhase, setAppPhase] = useState('home'); 
  const audioRef = useRef(null);

  const handlePhotoCapture = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setImagePreview(URL.createObjectURL(file));
    setAppPhase('loading');
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // ⚠️ KEEP YOUR IP ADDRESS HERE (e.g. 192.168.1.67)
      const response = await fetch('http://192.168.1.67:8555/predict', { 
        method: 'POST', body: formData,
      });
      const data = await response.json();
      
      if (data.success) {
        setResult(data);
        setLoading(false);
        setAppPhase('color-reveal');
        
        setTimeout(() => {
          setAppPhase('details');
          if (data.audio_base64) {
            const audio = new Audio("data:audio/mp3;base64," + data.audio_base64);
            audio.play();
            audioRef.current = audio;
          }
        }, 2500);
      }
    } catch (error) {
      alert("Network Error. Check Backend.");
      resetApp();
    }
  };

  const replayAudio = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0; 
      audioRef.current.play();
    }
  };

  const resetApp = () => {
    if (audioRef.current) audioRef.current.pause();
    setResult(null);
    setImagePreview(null);
    setAppPhase('home');
  };

  // ==========================================
  // UI RENDERERS
  // ==========================================

  if (appPhase === 'color-reveal' || appPhase === 'details') {
    const isHealthy = result?.is_healthy;
    const isUnrecognized = result?.is_unrecognized;
    
    let bgColor = 'bg-red-500';
    let Icon = AlertTriangle;
    let headerText = 'Disease Detected';
    let themeColor = 'text-red-600';
    let bgLight = 'bg-red-50';
    let BannerIcon = ShieldPlus;
    let bannerTitle = 'AI Treatment Plan';

    // 🟢 HEALTHY STATE COLORS & TEXT
    if (isHealthy) {
      bgColor = 'bg-green-500'; 
      Icon = CheckCircle;
      headerText = 'Healthy Plant'; 
      themeColor = 'text-green-600'; 
      bgLight = 'bg-green-50';
      BannerIcon = HeartPulse;
      bannerTitle = 'AI Health Report';
    } 
    // ⚪ ERROR STATE COLORS & TEXT
    else if (isUnrecognized) {
      bgColor = 'bg-gray-700'; 
      Icon = XCircle;
      headerText = 'Invalid Photo'; 
      themeColor = 'text-gray-700'; 
      bgLight = 'bg-gray-100';
    }

    return (
      <div className={`min-h-screen ${bgColor} transition-colors duration-700 flex flex-col relative overflow-hidden`}>
        
        <div className={`flex-1 flex items-center justify-center transform transition-all duration-1000 ${appPhase === 'details' ? 'scale-75 -translate-y-32 opacity-0' : 'scale-100 opacity-100'}`}>
          <Icon className="text-white w-40 h-40 animate-pulse drop-shadow-xl" strokeWidth={1} />
        </div>

        <div className={`absolute bottom-0 left-0 right-0 bg-white rounded-t-[2.5rem] shadow-2xl transform transition-transform duration-700 ease-out h-[85vh] flex flex-col ${appPhase === 'details' ? 'translate-y-0' : 'translate-y-full'}`}>
          
          <div className="flex-1 overflow-y-auto px-6 pt-8 pb-6">
            
            <div className="flex justify-between items-start mb-6">
              <div>
                <p className="text-sm font-bold tracking-wider text-gray-400 uppercase mb-1">Diagnosis</p>
                <h2 className={`text-3xl font-extrabold ${themeColor} leading-tight`}>
                  {headerText}
                </h2>
              </div>
              <div className="w-16 h-16 rounded-2xl overflow-hidden shadow-md border-2 border-white">
                <img src={imagePreview} alt="Scanned leaf" className="w-full h-full object-cover" />
              </div>
            </div>

            <div className="mb-6">
              <p className="text-xl text-gray-800 font-medium leading-snug">
                {result?.disease_english}
              </p>
              <p className="text-sm text-gray-500 mt-2 font-mono flex items-center gap-2">
                <Activity className="w-4 h-4" /> AI Confidence: {result?.confidence}%
              </p>
            </div>

            {/* 🤖 AI BANNER (DYNAMIC FOR HEALTHY VS SICK) */}
            {!isUnrecognized && (
              <div 
                onClick={replayAudio}
                className={`rounded-3xl p-5 mb-8 border border-opacity-50 ${bgLight} border-${themeColor.split('-')[1]}-200 cursor-pointer active:scale-[0.98] hover:bg-opacity-80 transition-all shadow-sm`}
              >
                <div className="flex items-center gap-2 mb-3">
                  <BannerIcon className={`w-6 h-6 ${themeColor}`} />
                  <h3 className={`font-bold text-lg ${themeColor}`}>{bannerTitle}</h3>
                  <div className={`ml-auto bg-white p-2 rounded-full shadow-sm`}>
                    <Volume2 className={`w-5 h-5 ${themeColor}`} />
                  </div>
                </div>
                
                <p className="text-gray-800 text-[16px] font-bold leading-relaxed mb-4">
                  {result?.disease_nepali}
                </p>
                
                <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 flex flex-col gap-4">
                  
                  {/* 🟢 IF HEALTHY: Show generic advice as one paragraph */}
                  {isHealthy ? (
                    <div className="flex items-start gap-3">
                      <Leaf className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                      <p className="text-gray-600 text-sm leading-relaxed">
                        {result?.remedy_organic} {result?.remedy_chemical}
                      </p>
                    </div>
                  ) : (
                  /* 🔴 IF SICK: Show divided Organic and Chemical sections */
                    <>
                      <div className="flex items-start gap-3">
                        <Leaf className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                        <div>
                          <span className="font-bold text-green-700 text-sm block mb-1">घरेलु उपचार:</span>
                          <p className="text-gray-600 text-sm leading-relaxed">{result?.remedy_organic}</p>
                        </div>
                      </div>

                      <div className="flex items-start gap-3 pt-3 border-t border-gray-100">
                        <Activity className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                        <div>
                          <span className="font-bold text-blue-700 text-sm block mb-1">रासायनिक उपचार:</span>
                          <p className="text-gray-600 text-sm leading-relaxed">{result?.remedy_chemical}</p>
                        </div>
                      </div>
                    </>
                  )}

                </div>

                {/* EXPERT ADVICE LINE */}
                <p className="text-sm font-semibold text-gray-500 mt-4 text-center">
                   {result?.expert_advice}
                </p>

                <p className="text-[10px] text-center text-gray-400 mt-4 uppercase tracking-widest font-bold">Tap anywhere to replay audio</p>
              </div>
            )}

            {/* ERROR UI */}
            {isUnrecognized && (
              <div onClick={replayAudio} className="bg-gray-100 rounded-3xl p-6 mb-8 text-center cursor-pointer active:scale-[0.98] transition-transform shadow-sm">
                <div className="bg-white w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-3 shadow-sm">
                  <Volume2 className="w-7 h-7 text-gray-500" />
                </div>
                <p className="text-gray-700 text-lg leading-relaxed mb-3">{result?.disease_nepali}</p>
                <p className="text-xs text-gray-400 uppercase tracking-widest font-bold">Tap to replay audio</p>
              </div>
            )}
          </div>

          <div className="p-6 bg-white border-t border-gray-100">
            <button onClick={resetApp} className={`w-full ${bgColor} text-white py-4 rounded-2xl font-bold text-lg shadow-lg active:scale-95 transition-transform flex items-center justify-center gap-2`}>
              <Camera className="w-5 h-5" /> Scan Another Plant
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Phase 0 & 1: Home & Loading Screen
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="px-6 pt-12 pb-6 bg-white shadow-sm rounded-b-[2.5rem] z-10 relative">
        <div className="flex items-center gap-3">
          <div className="bg-green-600 p-2 rounded-xl shadow-md">
            <Leaf className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">AgriScan</h1>
            <p className="text-green-600 text-sm font-semibold">AI Crop Diagnostics</p>
          </div>
        </div>
      </header>

      <main className="flex-1 px-6 flex flex-col items-center justify-center relative -mt-4">
        <div className="w-full aspect-square max-w-sm rounded-[2.5rem] overflow-hidden bg-white relative mb-8 shadow-xl border-4 border-white">
          {imagePreview ? (
            <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-50 text-green-700">
              <div className="bg-green-100 p-4 rounded-full mb-3">
                <Camera className="w-10 h-10" strokeWidth={1.5} />
              </div>
              <p className="text-sm font-semibold">Ready to scan</p>
            </div>
          )}

          {loading && (
            <div className="absolute inset-0 bg-white/90 backdrop-blur-md flex flex-col items-center justify-center">
              <div className="relative">
                <div className="w-16 h-16 border-4 border-green-100 border-t-green-600 rounded-full animate-spin"></div>
                <Activity className="w-6 h-6 text-green-600 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
              </div>
              <p className="text-green-700 font-bold mt-4 animate-pulse">Analyzing with AI...</p>
            </div>
          )}
        </div>

        {!loading && (
          <div className="w-full max-w-sm flex gap-3">
            <label className="flex-1 bg-green-600 text-white py-4 rounded-2xl font-bold text-[15px] shadow-lg shadow-green-200 flex items-center justify-center gap-2 cursor-pointer active:scale-95 transition-all hover:bg-green-700">
              <Camera className="w-5 h-5" /> Open Camera
              <input type="file" accept="image/*" capture="environment" className="hidden" onChange={handlePhotoCapture} />
            </label>
            <label className="bg-white text-gray-700 px-5 py-4 rounded-2xl font-bold shadow-md flex items-center justify-center cursor-pointer active:scale-95 transition-all hover:bg-gray-50 border border-gray-100">
              <Upload className="w-5 h-5" />
              <input type="file" accept="image/*" className="hidden" onChange={handlePhotoCapture} />
            </label>
          </div>
        )}
      </main>
    </div>
  );
}