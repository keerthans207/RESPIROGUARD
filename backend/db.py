"""
Supabase Database Client
Handles database operations for the Allergy Prevention Agent
"""

import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import Supabase (optional)
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: Supabase package not installed. Database features will be disabled.")

# Initialize Supabase client (optional)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabase is optional - app can run without it
SUPABASE_ENABLED = bool(SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY)

if SUPABASE_ENABLED:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase: Optional[Client] = None
    if not SUPABASE_AVAILABLE:
        print("Warning: Supabase package not installed. Install with: pip install supabase")
    elif not SUPABASE_URL or not SUPABASE_KEY:
        print("Warning: Supabase credentials not found in environment variables. Database features will be disabled.")


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches user profile including allergies from Supabase.
    
    Args:
        user_id: UUID of the user
        
    Returns:
        Dictionary containing user profile data, or None if user not found
    """
    if not SUPABASE_ENABLED:
        print("Warning: Supabase not configured. Cannot fetch user profile.")
        return None
    
    try:
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            user_data = response.data[0]
            
            # Extract allergies from allergy_profile JSONB field
            allergy_profile = user_data.get("allergy_profile", [])
            
            # Handle both list and dict formats
            if isinstance(allergy_profile, list):
                allergies = allergy_profile
            elif isinstance(allergy_profile, dict):
                # If it's a dict, try to extract a list from common keys
                allergies = allergy_profile.get("allergies", []) if "allergies" in allergy_profile else []
            else:
                allergies = []
            
            return {
                "id": user_data.get("id"),
                "email": user_data.get("email"),
                "allergies": allergies,
                "sensitivity_level": user_data.get("sensitivity_level", 5),
                "allergy_profile": allergy_profile
            }
        
        return None
    
    except Exception as e:
        print(f"Error fetching user profile: {str(e)}")
        raise


def log_alert(user_id: str, risk_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Logs an alert/risk assessment to the alert_logs table.
    
    Args:
        user_id: UUID of the user
        risk_data: Dictionary containing:
            - location: str
            - risk_level: str (low, moderate, high, severe)
            - aqi_snapshot: dict (weather_data from the agent)
            - timestamp: optional (defaults to now)
            
    Returns:
        Dictionary containing the created alert log entry, or None on error
    """
    if not SUPABASE_ENABLED:
        print("Warning: Supabase not configured. Skipping alert logging.")
        return None
    
    try:
        alert_entry = {
            "user_id": user_id,
            "location": risk_data.get("location", ""),
            "risk_level": risk_data.get("risk_level", "moderate"),
            "aqi_snapshot": risk_data.get("aqi_snapshot", {}),
        }
        
        # Add timestamp if provided
        if "timestamp" in risk_data:
            alert_entry["timestamp"] = risk_data["timestamp"]
        
        response = supabase.table("alert_logs").insert(alert_entry).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        return None
    
    except Exception as e:
        print(f"Error logging alert: {str(e)}")
        raise


def get_user_alert_history(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieves recent alert history for a user.
    
    Args:
        user_id: UUID of the user
        limit: Maximum number of alerts to retrieve (default: 10)
        
    Returns:
        List of alert log dictionaries
    """
    if not SUPABASE_ENABLED:
        print("Warning: Supabase not configured. Cannot fetch alert history.")
        return []
    
    try:
        response = (
            supabase.table("alert_logs")
            .select("*")
            .eq("user_id", user_id)
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        
        return response.data if response.data else []
    
    except Exception as e:
        print(f"Error fetching alert history: {str(e)}")
        return []
