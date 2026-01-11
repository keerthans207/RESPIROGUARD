# Allergy Prevention Agent Frontend

A Next.js 14 frontend application for the Allergy Prevention Agent, built with TypeScript and Tailwind CSS.

## Features

- **Real-time Risk Assessment**: Visual risk dial showing current allergy risk level
- **Environmental Data**: Cards displaying AQI, pollen counts, and wind speed
- **AI Recommendations**: Gemini-powered advice based on current conditions
- **Location-based**: Automatically fetches user location and assesses risk
- **Chat Interface**: Interactive chat for follow-up questions

## Setup

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

## Components

### RiskDial
Large visual component displaying the current risk level with a circular progress indicator.

### EnvironmentCard
Small cards showing environmental metrics (AQI, Pollen Count, Wind Speed) with color-coded status.

### RecommendationBox
Distinct box displaying AI-generated recommendations with risk-level-based styling.

### ChatInterface
Floating chat window for asking follow-up questions to the agent.

## API Integration

The frontend connects to the backend API at `http://127.0.0.1:8001/api/check-risk`.

Make sure your backend server is running before using the frontend.

## Theme Colors

- **Safe (Green)**: `#10b981` - Low risk conditions
- **Caution (Yellow)**: `#f59e0b` - Moderate risk conditions
- **Danger (Red)**: `#ef4444` - High/Severe risk conditions

## Tech Stack

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- React 18
