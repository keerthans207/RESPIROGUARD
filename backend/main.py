"""
Allergy Prevention Agent Backend
FastAPI application with LangGraph agent for allergy risk assessment
Updated with Real-Time OpenMeteo & Geopy Data
"""

import os
import json
import httpx
import asyncio
from typing import TypedDict, List, Dict, Any, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from geopy.geocoders import Nominatim
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from db import get_user_profile, log_alert

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Allergy Prevention Agent API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini model
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", # Updated to Flash for speed
    google_api_key=GEMINI_API_KEY,
    temperature=0.7
)

# --- HELPER TOOLS (Real Data Fetchers) ---

def get_coordinates(city_name: str):
    """Converts a city name to Lat/Long using OpenStreetMap."""
    try:
        # User_agent is required by Nominatim policy
        geolocator = Nominatim(user_agent="allergy_agent_capstone_v1")
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None

async def get_real_aqi_data(city_name: str):
    """Fetches REAL-TIME AQI, PM2.5, and Pollen proxy data."""
    lat, lon = get_coordinates(city_name)
    
    if not lat:
        return {"error": f"Could not find coordinates for {city_name}"}

    # OpenMeteo Air Quality API (Free)
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["us_aqi", "pm2_5", "pm10", "ozone", "dust"],
        "hourly": ["alder_pollen", "grass_pollen", "mugwort_pollen"]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            current = data.get("current", {})
            hourly = data.get("hourly", {})
            
            # Simple logic to get max pollen from the next hour
            grass_pollen = hourly.get("grass_pollen", [0])[0] if "grass_pollen" in hourly else 0
            
            return {
                "location_name": city_name,
                "lat": lat,
                "lon": lon,
                "aqi": current.get("us_aqi", 0),
                "pm2_5": current.get("pm2_5", 0),
                "pm10": current.get("pm10", 0),
                "pollen_count": {
                    "grass": grass_pollen,
                    # Fallback values if specific pollen data is missing
                    "tree": 0, 
                    "weed": 0
                },
                "status": "Live Data"
            }
    except Exception as e:
        return {"error": f"API Request failed: {e}"}

# --- LANGGRAPH STATE & NODES ---

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

class RiskCheckResponse(BaseModel):
    location: str
    user_allergies: List[str]
    weather_data: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    advice: str

# Node 1: Fetch Environmental Data
async def fetch_enviro_data(state: AgentState) -> AgentState:
    print(f"🌍 Fetching REAL data for: {state['location']}...")
    weather_data = await get_real_aqi_data(state["location"])
    
    # Handle error case by providing a safe fallback with an error flag
    if "error" in weather_data:
        weather_data = {
            "aqi": 0,
            "error": weather_data["error"],
            "status": "Error fetching data"
        }
        
    state["weather_data"] = weather_data
    return state

# Node 2: Analyze Risk
async def analyze_risk(state: AgentState) -> AgentState:
    location = state["location"]
    user_allergies = state["user_allergies"]
    data = state["weather_data"]
    
    # Improved Prompt for Real Data
    prompt = f"""
    ACT AS AN EXPERT IMMUNOLOGIST.
    
    [LIVE SENSOR DATA for {location}]
    - US AQI: {data.get('aqi', 'N/A')} (Threshold >100 is Unhealthy)
    - PM2.5 Concentration: {data.get('pm2_5', 'N/A')} µg/m³
    - Grass Pollen Level: {data.get('pollen_count', {}).get('grass', 0)} grains/m³
    
    [USER PATIENT PROFILE]
    - Allergies: {', '.join(user_allergies)}
    
    [TASK]
    1. Determine the Risk Level (Low, Moderate, High, Severe).
    2. Calculate a Max Safe Duration (in minutes) for outdoor exposure.
    3. Explain the reasoning (e.g., "High PM2.5 aggravates Asthma").
    
    Return ONLY valid JSON:
    {{
        "risk_level": "low|moderate|high|severe",
        "safe_duration": <number>,
        "reasoning": "<short explanation>"
    }}
    """
    
    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        response_text = response.content.strip()
        
        # Robust JSON extraction
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        # Clean up any potential json prefix/suffix that remains
        response_text = response_text.replace("```json", "").replace("```", "")
        
        risk_assessment = json.loads(response_text)
        state["risk_assessment"] = risk_assessment
        
    except Exception as e:
        print(f"❌ Analysis Error: {e}")
        state["risk_assessment"] = {
            "risk_level": "moderate",
            "safe_duration": 60,
            "reasoning": f"AI Analysis failed: {str(e)}. Proceed with caution."
        }
    
    return state

# Node 3: Generate Advice
async def generate_advice(state: AgentState) -> AgentState:
    location = state["location"]
    risk = state["risk_assessment"]
    
    prompt = f"""
    You are a friendly health assistant.
    The user is in {location}.
    Risk Level: {risk.get('risk_level')}
    Safe Stay: {risk.get('safe_duration')} mins.
    Reason: {risk.get('reasoning')}
    
    Write a short, helpful SMS-style alert (max 2 sentences) telling them if they should go out and what protection to wear.
    """
    
    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        advice = response.content.strip()
        state["messages"] = state.get("messages", []) + [AIMessage(content=advice)]
    except Exception as e:
        state["messages"] = state.get("messages", []) + [AIMessage(content="Error generating advice.")]
    
    return state

# --- GRAPH BUILD ---

NODE_TO_STEP = {
    "fetch_enviro_data": {"name": "Scanning Local Sensors...", "description": "Connecting to OpenMeteo satellite data"},
    "analyze_risk": {"name": "Immunologist AI Analyzing...", "description": "Evaluating PM2.5 & Pollen risks"},
    "generate_advice": {"name": "Finalizing Safety Report...", "description": "Generating actionable advice"}
}

def create_agent_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("fetch_enviro_data", fetch_enviro_data)
    workflow.add_node("analyze_risk", analyze_risk)
    workflow.add_node("generate_advice", generate_advice)
    
    workflow.set_entry_point("fetch_enviro_data")
    workflow.add_edge("fetch_enviro_data", "analyze_risk")
    workflow.add_edge("analyze_risk", "generate_advice")
    workflow.add_edge("generate_advice", END)
    
    return workflow.compile()

agent_graph = create_agent_graph()

# --- STREAMING LOGIC ---

async def stream_agent_execution(request: RiskCheckRequest, user_allergies: List[str], user_id: Optional[str] = None):
    initial_state: AgentState = {
        "location": request.location,
        "user_allergies": user_allergies,
        "weather_data": {},
        "risk_assessment": {},
        "messages": []
    }
    
    try:
        # Step 1: Fetch
        yield f"data: {json.dumps({'type': 'step_start', 'step': 'fetch_enviro_data', 'name': NODE_TO_STEP['fetch_enviro_data']['name']})}\n\n"
        state = await fetch_enviro_data(initial_state)
        yield f"data: {json.dumps({'type': 'step_complete', 'step': 'fetch_enviro_data', 'name': NODE_TO_STEP['fetch_enviro_data']['name']})}\n\n"
        await asyncio.sleep(0.1)
        
        # Step 2: Analyze
        yield f"data: {json.dumps({'type': 'step_start', 'step': 'analyze_risk', 'name': NODE_TO_STEP['analyze_risk']['name']})}\n\n"
        state = await analyze_risk(state)
        yield f"data: {json.dumps({'type': 'step_complete', 'step': 'analyze_risk', 'name': NODE_TO_STEP['analyze_risk']['name']})}\n\n"
        await asyncio.sleep(0.1)
        
        # Step 3: Advice
        yield f"data: {json.dumps({'type': 'step_start', 'step': 'generate_advice', 'name': NODE_TO_STEP['generate_advice']['name']})}\n\n"
        state = await generate_advice(state)
        yield f"data: {json.dumps({'type': 'step_complete', 'step': 'generate_advice', 'name': NODE_TO_STEP['generate_advice']['name']})}\n\n"
        
        # Finalize
        yield f"data: {json.dumps({'type': 'step_complete', 'step': 'done', 'name': 'Done.'})}\n\n"
        
        advice = state["messages"][-1].content if state.get("messages") else ""
        
        final_result = {
            "location": state["location"],
            "user_allergies": state["user_allergies"],
            "weather_data": state["weather_data"],
            "risk_assessment": state["risk_assessment"],
            "advice": advice
        }
        
        # Log to Supabase (Non-blocking)
        if user_id:
            try:
                log_alert(user_id=user_id, risk_data={
                    "location": final_result["location"],
                    "risk_level": final_result["risk_assessment"].get("risk_level", "moderate"),
                    "aqi_snapshot": final_result["weather_data"]
                })
            except Exception as e:
                print(f"DB Log Warning: {e}")

        yield f"data: {json.dumps({'type': 'result', 'data': final_result})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

# --- ENDPOINTS ---

@app.get("/")
async def root():
    return {"message": "Allergy Prevention Agent API is running"}

@app.post("/api/check-risk-stream")
async def check_risk_stream(request: RiskCheckRequest):
    try:
        user_allergies: List[str] = []
        user_id = request.user_id
        
        if request.user_id:
            user_profile = get_user_profile(user_id)
            if user_profile:
                user_allergies = user_profile.get("allergies", [])
        
        # Fallback to request body allergies if DB lookup fails or isn't used
        if not user_allergies and request.allergies:
            user_allergies = request.allergies
            
        if not user_allergies:
             user_allergies = ["General Pollution"] # Default if nothing provided

        return StreamingResponse(
            stream_agent_execution(request, user_allergies, user_id),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/check-risk", response_model=RiskCheckResponse)
async def check_risk(request: RiskCheckRequest):
    # (Simplified for brevity, reuses logic from stream but blocking)
    # For full implementation, copy the logic from check_risk_stream but await the graph directly
    # This endpoint is kept for compatibility with non-streaming clients
    initial_state = {
        "location": request.location,
        "user_allergies": request.allergies or ["General"],
        "weather_data": {},
        "risk_assessment": {},
        "messages": []
    }
    final_state = await agent_graph.ainvoke(initial_state)
    advice = final_state["messages"][-1].content if final_state["messages"] else ""
    return RiskCheckResponse(
        location=final_state["location"],
        user_allergies=final_state["user_allergies"],
        weather_data=final_state["weather_data"],
        risk_assessment=final_state["risk_assessment"],
        advice=advice
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)