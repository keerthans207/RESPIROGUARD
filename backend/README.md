# Allergy Prevention Agent Backend

A FastAPI backend service that uses LangGraph and Google Gemini to assess allergy risks based on environmental data.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Supabase:
   - Create a Supabase project at https://supabase.com
   - Run the SQL schema from `schema.sql` in your Supabase SQL Editor
   - Get your Supabase URL and anon/service key from Project Settings > API

3. Create a `.env` file in the `backend` directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
AQI_API_KEY=your_aqi_api_key_here  # Optional
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_or_service_key
```

3. Run the server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload
```

## API Endpoints

### POST `/api/check-risk`

Check allergy risk for a given location and user allergies.

**Request Body (Option 1 - With user_id):**
```json
{
  "location": "New York, NY",
  "user_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Request Body (Option 2 - With allergies directly):**
```json
{
  "location": "New York, NY",
  "allergies": ["pollen", "dust"]
}
```

**Note:** Either `user_id` (fetches allergies from Supabase) or `allergies` must be provided.

**Response:**
```json
{
  "location": "New York, NY",
  "user_allergies": ["pollen", "dust"],
  "weather_data": {
    "aqi": 45,
    "pollen_count": {
      "tree": 3.2,
      "grass": 1.8,
      "weed": 0.5
    },
    "humidity": 65,
    "temperature": 22,
    "wind_speed": 12,
    "air_quality_index": "Good"
  },
  "risk_assessment": {
    "risk_level": "moderate",
    "safe_duration": 120,
    "reasoning": "Moderate pollen levels detected..."
  },
  "advice": "Based on current conditions..."
}
```

## Architecture

The agent uses a LangGraph workflow with three nodes:

1. **fetch_enviro_data**: Retrieves air quality and pollen data
2. **analyze_risk**: Uses Gemini Pro to analyze risk based on user allergies
3. **generate_advice**: Generates actionable recommendations

## Database Integration

The backend integrates with Supabase for:
- **User Profiles**: Stores user allergies and sensitivity levels
- **Alert Logs**: Automatically logs all risk assessments when `user_id` is provided

### Database Functions

- `get_user_profile(user_id)`: Fetches user allergies from Supabase
- `log_alert(user_id, risk_data)`: Saves risk assessment to alert_logs table

When a request includes a `user_id`, the system will:
1. Fetch the user's allergies from Supabase
2. Run the risk assessment
3. Automatically log the result to the `alert_logs` table
