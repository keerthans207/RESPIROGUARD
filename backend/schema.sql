-- Supabase Schema for Allergy Prevention Agent
-- Run this SQL in your Supabase SQL Editor

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    allergy_profile JSONB NOT NULL DEFAULT '[]'::jsonb,
    sensitivity_level INTEGER NOT NULL DEFAULT 5 CHECK (sensitivity_level >= 1 AND sensitivity_level <= 10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create alert_logs table
CREATE TABLE IF NOT EXISTS alert_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    location TEXT NOT NULL,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'moderate', 'high', 'severe')),
    aqi_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_alert_logs_user_id ON alert_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_logs_timestamp ON alert_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alert_logs_risk_level ON alert_logs(risk_level);

-- Enable Row Level Security (RLS) - optional, adjust based on your security needs
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_logs ENABLE ROW LEVEL SECURITY;

-- Create policies (example - adjust based on your authentication setup)
-- Allow users to read their own data
CREATE POLICY "Users can view their own data" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own data" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Allow users to view their own alert logs
CREATE POLICY "Users can view their own alert logs" ON alert_logs
    FOR SELECT USING (auth.uid() = user_id);

-- Allow service role to insert alert logs (for backend API)
CREATE POLICY "Service role can insert alert logs" ON alert_logs
    FOR INSERT WITH CHECK (true);
