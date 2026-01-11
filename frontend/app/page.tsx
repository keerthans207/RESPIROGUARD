'use client'

import React, { useState, useEffect } from 'react'
import RiskDial from '@/components/RiskDial'
import EnvironmentCard from '@/components/EnvironmentCard'
import RecommendationBox from '@/components/RecommendationBox'
import ChatInterface from '@/components/ChatInterface'
import LiveAgentStatus, { useAgentStatus } from '@/components/LiveAgentStatus'

// Updated Interface to allow for optional/missing data without crashing
interface RiskData {
  location: string
  user_allergies: string[]
  weather_data: {
    aqi?: number
    pollen_count?: {
      tree?: number
      grass?: number
      weed?: number
    }
    humidity?: number
    temperature?: number
    wind_speed?: number
    air_quality_index?: string
  }
  risk_assessment: {
    risk_level?: 'low' | 'moderate' | 'high' | 'severe'
    safe_duration?: number
    reasoning?: string
  }
  advice?: string
}

export default function Home() {
  const [riskData, setRiskData] = useState<RiskData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // Defaulting manualLocation prevents uncontrolled input warnings
  const [manualLocation, setManualLocation] = useState<string>('') 
  const [manualAllergies, setManualAllergies] = useState<string>('pollen, dust')
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [useManualInput, setUseManualInput] = useState(false)
  const { steps, updateStep, resetSteps } = useAgentStatus()

  // Helper to safely format numbers (Fixes the toFixed crash)
  const safeFormat = (val: number | undefined | null, decimals: number = 1): string => {
    if (val === undefined || val === null) return 'N/A'
    return val.toFixed(decimals)
  }

  useEffect(() => {
    // Try to get user's location automatically
    if (!useManualInput && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords
          // We pass coordinates as string; the backend Geopy will handle this
          const locationString = `${latitude}, ${longitude}`
          
          // Only fetch if we haven't fetched yet
          if(!riskData && !loading) {
             await fetchRiskData(locationString, ['pollen', 'dust'])
          }
        },
        (error) => {
          console.error('Error getting location:', error)
          setUseManualInput(true)
        }
      )
    }
  }, [useManualInput]) // Removed other dependencies to prevent loops

  const fetchRiskData = async (loc: string, allergies: string[]) => {
    try {
      setLoading(true)
      setError(null)
      setIsStreaming(true)
      resetSteps()

      if (!loc || !loc.trim()) throw new Error('Please enter a location')
      if (!allergies || allergies.length === 0) throw new Error('Please enter allergies')

      const response = await fetch('https://respiroguard.onrender.com/api/check-risk-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location: loc.trim(),
          allergies: allergies,
        }),
      })

      if (!response.ok) throw new Error(`API error: ${response.statusText}`)

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) throw new Error('No response body')

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'step_start') {
                updateStep(data.step, 'active')
              } else if (data.type === 'step_complete') {
                updateStep(data.step, 'completed')
              } else if (data.type === 'result') {
                setRiskData(data.data)
                setIsStreaming(false)
                setLoading(false)
              } else if (data.type === 'error') {
                throw new Error(data.message)
              }
            } catch (parseError) {
              console.error('Error parsing SSE data:', parseError)
            }
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch risk data')
      setIsStreaming(false)
      setLoading(false)
    }
  }

  const getAQIStatus = (aqi: number | undefined) => {
    if (aqi === undefined) return 'moderate' // default
    if (aqi <= 50) return 'good'
    if (aqi <= 100) return 'moderate'
    return 'poor'
  }

  const getPollenStatus = (pollen: number | undefined) => {
    if (pollen === undefined) return 'good' // default
    if (pollen <= 2) return 'good'
    if (pollen <= 5) return 'moderate'
    return 'poor'
  }

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const allergiesList = manualAllergies.split(',').map(a => a.trim()).filter(a => a.length > 0)
    
    if (allergiesList.length === 0) {
      setError('Please enter at least one allergy')
      return
    }
    // Update display location immediately
    fetchRiskData(manualLocation, allergiesList)
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Allergy Prevention Agent
          </h1>
          <p className="text-gray-600">
            AI-powered risk assessment for your allergies
          </p>
        </div>

        {/* Manual Input Form */}
        {(!riskData || useManualInput) && !loading && !isStreaming && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Check Allergy Risk
            </h2>
            <form onSubmit={handleManualSubmit} className="space-y-4">
              <div>
                <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
                  Location
                </label>
                <input
                  type="text"
                  id="location"
                  value={manualLocation}
                  onChange={(e) => setManualLocation(e.target.value)}
                  placeholder="e.g., New York, NY"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-safe"
                  required
                />
              </div>
              <div>
                <label htmlFor="allergies" className="block text-sm font-medium text-gray-700 mb-2">
                  Allergies (comma-separated)
                </label>
                <input
                  type="text"
                  id="allergies"
                  value={manualAllergies}
                  onChange={(e) => setManualAllergies(e.target.value)}
                  placeholder="e.g., pollen, dust, mold"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-safe"
                  required
                />
              </div>
              <button
                type="submit"
                className="w-full px-6 py-3 bg-safe text-white rounded-lg hover:bg-safe-dark transition-colors font-semibold"
              >
                Check Risk
              </button>
            </form>
            {!useManualInput && (
              <button
                onClick={() => setUseManualInput(true)}
                className="mt-4 text-sm text-gray-600 hover:text-gray-900 underline"
              >
                Or enter location manually
              </button>
            )}
          </div>
        )}

        {/* Live Agent Status */}
        {isStreaming && (
          <LiveAgentStatus isStreaming={isStreaming} steps={steps} />
        )}

        {/* Loading Spinner (Fallback) */}
        {loading && !isStreaming && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-safe mb-4"></div>
              <p className="text-gray-600">Analyzing your allergy risk...</p>
            </div>
          </div>
        )}

        {/* Initial Empty State */}
        {!loading && !isStreaming && !riskData && !error && !useManualInput && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6 text-center">
            <p className="text-gray-600 mb-4">Getting your location...</p>
            <button
              onClick={() => setUseManualInput(true)}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Enter Location Manually
            </button>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border-2 border-red-200 rounded-lg p-6 mb-6">
            <h3 className="text-red-800 font-semibold mb-2">Error</h3>
            <p className="text-gray-700">{error}</p>
          </div>
        )}

        {/* Results Dashboard */}
        {riskData && !loading && (
          <>
            {/* Location Badge */}
            <div className="mb-6">
              <div className="bg-white rounded-lg shadow-sm p-4 inline-block">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span className="text-gray-700 font-medium">
                    {riskData.location}
                  </span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              {/* Risk Dial */}
              <div className="lg:col-span-1 flex justify-center">
                <div className="bg-white rounded-lg shadow-md p-6 w-full">
                  <RiskDial
                    riskLevel={riskData.risk_assessment?.risk_level ?? 'moderate'}
                    safeDuration={riskData.risk_assessment?.safe_duration ?? 0}
                  />
                </div>
              </div>

              {/* Environment Cards */}
              <div className="lg:col-span-2 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* AQI CARD */}
                  <EnvironmentCard
                    title="Air Quality Index"
                    value={riskData.weather_data?.aqi ?? 0}
                    status={getAQIStatus(riskData.weather_data?.aqi)}
                    icon={
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    }
                  />
                  {/* TREE POLLEN CARD */}
                  <EnvironmentCard
                    title="Tree Pollen"
                    value={safeFormat(riskData.weather_data?.pollen_count?.tree)}
                    unit=""
                    status={getPollenStatus(riskData.weather_data?.pollen_count?.tree)}
                    icon={
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                      </svg>
                    }
                  />
                  {/* WIND CARD */}
                  <EnvironmentCard
                    title="Wind Speed"
                    value={riskData.weather_data?.wind_speed ?? 0}
                    unit="km/h"
                    status="good"
                    icon={
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    }
                  />
                </div>

                {/* Additional Pollen Info */}
                <div className="grid grid-cols-2 gap-4">
                  <EnvironmentCard
                    title="Grass Pollen"
                    value={safeFormat(riskData.weather_data?.pollen_count?.grass)}
                    status={getPollenStatus(riskData.weather_data?.pollen_count?.grass)}
                  />
                  <EnvironmentCard
                    title="Weed Pollen"
                    value={safeFormat(riskData.weather_data?.pollen_count?.weed)}
                    status={getPollenStatus(riskData.weather_data?.pollen_count?.weed)}
                  />
                </div>
              </div>
            </div>

            {/* Recommendations */}
            <div className="mb-6">
              <RecommendationBox
                advice={riskData.advice ?? "No specific advice available."}
                riskLevel={riskData.risk_assessment?.risk_level ?? 'moderate'}
              />
            </div>

            {/* User Allergies Display */}
            <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">
                Your Allergies
              </h3>
              <div className="flex flex-wrap gap-2">
                {riskData.user_allergies?.map((allergy, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium"
                  >
                    {allergy}
                  </span>
                ))}
              </div>
            </div>

            {/* Check Again Button */}
            <div className="text-center pb-8">
              <button
                onClick={() => {
                  setRiskData(null)
                  setUseManualInput(true)
                  setError(null)
                  setManualLocation('')
                }}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Check Another Location
              </button>
            </div>
          </>
        )}
      </div>

      {/* Floating Chat Button */}
      <button
        onClick={() => setIsChatOpen(!isChatOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-safe text-white rounded-full shadow-lg hover:bg-safe-dark transition-all flex items-center justify-center z-40 bg-green-600 hover:bg-green-700"
        aria-label="Open chat"
      >
        {isChatOpen ? (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        )}
      </button>

      {/* Chat Interface */}
      <ChatInterface isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </main>
  )
}