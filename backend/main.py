"""
Allergy Prevention Agent Backend
VERSION: DEPLOYMENT READY (Vercel CORS + Relay Webhook + Fast Hybrid Data)
"""

import os
import json
import httpx
import asyncio
import datetime
from typing import TypedDict, List, Dict, Any, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from geopy.geocoders import Nominatim
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph import StateGraph, END
from db import get_user_profile, log_alert

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Allergy Prevention Agent API")

# --- 1. CORS: ALLOW VERCEL & LOCALHOST ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",                      # Local development
        "https://allergy-agent-capstone.vercel.app",  # <--- REPLACE WITH YOUR VERCEL URL
        "https://your-project.vercel.app"             # Add others if needed
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# 👇 PASTE YOUR RELAY WEBHOOK URL HERE 👇
RELAY_WEBHOOK_URL = "https://hook.relay.app/api/v1/playbook/YOUR_ID_HERE" 

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# --- 2. ROBUST GEMINI CONNECTION (Fixes 404 Errors) ---
CACHED_GEMINI_URL = None

async def get_gemini_url():
    """Finds the fastest working Gemini model for your specific API Key."""
    global CACHED_GEMINI_URL
    if CACHED_GEMINI_URL: return CACHED_GEMINI_URL

    # Try to find 'Flash' model first (Fastest)
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                for m in resp.json().get('models', []):
                    if 'flash' in m['name'] and 'generateContent' in m.get('supportedGenerationMethods', []):
                        CACHED_GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/{m['name']}:generateContent?key={GEMINI_API_KEY}"
                        return CACHED_GEMINI_URL
        except: pass
    
    # Fallback to Pro if Flash isn't found
    return f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

async def call_gemini(prompt: str):
    """Directly calls Gemini via HTTP to avoid library version conflicts."""
    url = await get_gemini_url()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=20.0)
            if resp.status_code == 200:
                return resp.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Gemini Error: {e}")
    return None

# --- 3. FAST HYBRID DATA FETCHING ---

async def get_coordinates(city: str):
    """Uses OpenWeather (Fast) if key exists, otherwise Nominatim (Slow)."""
    # Fast Path
    if OPENWEATHER_API_KEY:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_API_KEY}"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
                if resp.status_code == 200 and resp.json():
                    return resp.json()[0]['lat'], resp.json()[0]['lon']
        except: pass

    # Slow Path (Fallback)
    try:
        geolocator = Nominatim(user_agent="allergy_agent_capstone_v1")
        loc = geolocator.geocode(city)
        if loc: return loc.latitude, loc.longitude
    except: pass
    return None, None

async def get_real_aqi_data(city_name: str):
    """Fetches Data from OpenWeather (AQI) and OpenMeteo (Pollen) in parallel."""
    lat, lon = await get_coordinates(city_name)
    if not lat: return {"error": f"City '{city_name}' not found"}

    # URLs
    ow_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
    om_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    om_params = {
        "latitude": lat, "longitude": lon,
        "hourly": ["grass_pollen", "alder_pollen", "birch_pollen", "ragweed_pollen", "mugwort_pollen"],
        "timezone": "auto"
    }

    # Parallel Fetch
    async with httpx.AsyncClient() as client:
        try:
            # If no OpenWeather key, only fetch OpenMeteo
            tasks = [client.get(om_url, params=om_params)]
            if OPENWEATHER_API_KEY: tasks.append(client.get(ow_url))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except: return {"error": "Network Connection Failed"}

    # Process Data
    om_data = results[0].json() if isinstance(results[0], httpx.Response) else {}
    ow_data = results[1].json() if len(results) > 1 and isinstance(results[1], httpx.Response) else {}

    # Extract Pollen (Time-aligned)
    hour = datetime.datetime.now().hour
    hourly = om_data.get("hourly", {})
    
    def get_val(keys):
        total = 0.0
        for k in keys:
            vals = hourly.get(k, [])
            if len(vals) > hour and vals[hour] is not None:
                total += vals[hour]
        return total

    grass = get_val(["grass_pollen"])
    tree = get_val(["alder_pollen", "birch_pollen"])
    weed = get_val(["ragweed_pollen", "mugwort_pollen"])

    # Extract AQI
    aqi, pm25, pm10 = 0, 0, 0
    if "list" in ow_data and ow_data["list"]:
        curr = ow_data["list"][0]
        aqi = curr["main"]["aqi"] * 50  # Convert 1-5 scale to US AQI approx
        pm25 = curr["components"]["pm2_5"]
        pm10 = curr["components"]["pm10"]
    elif "current" in om_data: # Fallback to OpenMeteo AQI if OpenWeather fails
        aqi = om_data["current"].get("us_aqi", 0)
        pm25 = om_data["current"].get("pm2_5", 0)
        pm10 = om_data["current"].get("pm10", 0)

    # Tropical Fix: Estimate pollen if 0 but PM is high (Common in India)
    if tree == 0.0 and pm10 > 30: tree = round(pm10 * 0.15, 1)
    if weed == 0.0 and pm10 > 40: weed = round(pm10 * 0.1, 1)

    return {
        "location_name": city_name,
        "aqi": aqi, "pm2_5": pm25, "pm10": pm10,
        "pollen_count": {"grass": grass, "tree": tree, "weed": weed},
        "grass_pollen": grass, "tree_pollen": tree, "weed_pollen": weed, # Flattened for UI
        "status": "Live Data"
    }

# --- 4. RELAY WEBHOOK TRIGGER ---
async def trigger_relay(location, risk, advice):
    if "relay.app" not in RELAY_WEBHOOK_URL: return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(RELAY_WEBHOOK_URL, json={
                "location": location, "risk_level": risk, "advice_message": advice
            })
            print(f"🚀 Relay Alert Sent for {location}")
    except Exception as e:
        print(f"Relay Error: {e}")

# --- LANGGRAPH NODES ---

class AgentState(TypedDict):
    location: str
    user_allergies: List[str]
    weather_data: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    messages: List[BaseMessage]

class RiskCheckRequest(BaseModel):
    location: str
    user_id: Optional[str] = None
    allergies: Optional[List[str]] = None

async def fetch_enviro_data(state: AgentState) -> AgentState:
    print(f"🌍 Fetching data for: {state['location']}...")
    state["weather_data"] = await get_real_aqi_data(state["location"])
    return state

async def analyze_risk(state: AgentState) -> AgentState:
    d = state["weather_data"]
    if "error" in d:
        state["risk_assessment"] = {"risk_level": "Unknown", "safe_duration": 0, "reasoning": d["error"]}
        return state

    prompt = f"""
    ACT AS AN IMMUNOLOGIST.
    LOCATION: {state['location']}
    DATA: AQI={d.get('aqi')}, PM2.5={d.get('pm2_5')}, Grass={d.get('grass_pollen')}, Tree={d.get('tree_pollen')}
    PATIENT ALLERGIES: {', '.join(state['user_allergies'])}
    
    RETURN JSON ONLY: {{ "risk_level": "low|moderate|high|severe", "safe_duration": minutes_int, "reasoning": "short explanation" }}
    """
    
    res = await call_gemini(prompt)
    try:
        clean = res.replace("```json", "").replace("```", "").strip()
        state["risk_assessment"] = json.loads(clean)
    except:
        state["risk_assessment"] = {"risk_level": "Moderate", "safe_duration": 60, "reasoning": "Standard precaution (AI Busy)"}
    return state

async def generate_advice(state: AgentState) -> AgentState:
    risk = state["risk_assessment"]
    prompt = f"Write a 1-sentence SMS alert about {risk.get('risk_level')} air quality."
    advice = await call_gemini(prompt)
    
    state["messages"] = [AIMessage(content=advice or "Check local guidelines.")]
    
    # Fire Webhook (Fire-and-forget)
    asyncio.create_task(trigger_relay(state["location"], risk.get("risk_level"), advice))
    return state

# --- GRAPH ---
workflow = StateGraph(AgentState)
workflow.add_node("fetch_enviro_data", fetch_enviro_data)
workflow.add_node("analyze_risk", analyze_risk)
workflow.add_node("generate_advice", generate_advice)
workflow.set_entry_point("fetch_enviro_data")
workflow.add_edge("fetch_enviro_data", "analyze_risk")
workflow.add_edge("analyze_risk", "generate_advice")
workflow.add_edge("generate_advice", END)
agent_graph = workflow.compile()

# --- STREAMING ---
NODE_TO_STEP = {
    "fetch_enviro_data": {"name": "Scanning Sensors...", "description": "OpenWeather & Pollen Data"},
    "analyze_risk": {"name": "AI Analyzing...", "description": "Evaluating Risks"},
    "generate_advice": {"name": "Sending Alerts...", "description": "Triggering Relay Webhook"}
}

async def stream_agent_execution(request: RiskCheckRequest, user_allergies: List[str], user_id: Optional[str] = None):
    initial = {"location": request.location, "user_allergies": user_allergies, "weather_data": {}, "risk_assessment": {}, "messages": []}
    
    try:
        yield f"data: {json.dumps({'type': 'step_start', 'step': 'fetch_enviro_data', 'name': NODE_TO_STEP['fetch_enviro_data']['name']})}\n\n"
        state = await fetch_enviro_data(initial)
        yield f"data: {json.dumps({'type': 'step_complete', 'step': 'fetch_enviro_data', 'name': NODE_TO_STEP['fetch_enviro_data']['name']})}\n\n"
        
        yield f"data: {json.dumps({'type': 'step_start', 'step': 'analyze_risk', 'name': NODE_TO_STEP['analyze_risk']['name']})}\n\n"
        state = await analyze_risk(state)
        yield f"data: {json.dumps({'type': 'step_complete', 'step': 'analyze_risk', 'name': NODE_TO_STEP['analyze_risk']['name']})}\n\n"
        
        yield f"data: {json.dumps({'type': 'step_start', 'step': 'generate_advice', 'name': NODE_TO_STEP['generate_advice']['name']})}\n\n"
        state = await generate_advice(state)
        yield f"data: {json.dumps({'type': 'step_complete', 'step': 'generate_advice', 'name': NODE_TO_STEP['generate_advice']['name']})}\n\n"
        
        final = {
            "location": state["location"],
            "user_allergies": state["user_allergies"],
            "weather_data": state["weather_data"],
            "risk_assessment": state["risk_assessment"],
            "advice": state["messages"][-1].content
        }
        
        if user_id: 
            try: log_alert(user_id, {"location": final["location"], "risk": final["risk_assessment"], "data": final["weather_data"]})
            except: pass

        yield f"data: {json.dumps({'type': 'result', 'data': final})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@app.post("/api/check-risk-stream")
async def check_risk_stream(req: RiskCheckRequest):
    allergies = req.allergies or ["Pollen", "Dust"]
    if req.user_id:
        p = get_user_profile(req.user_id)
        if p: allergies = p.get("allergies", allergies)
    return StreamingResponse(stream_agent_execution(req, allergies, req.user_id), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)