'use client'

import React from 'react'

interface RiskDialProps {
  riskLevel: 'low' | 'moderate' | 'high' | 'severe'
  safeDuration?: number
}

const RiskDial: React.FC<RiskDialProps> = ({ riskLevel, safeDuration }) => {
  const getRiskConfig = () => {
    switch (riskLevel) {
      case 'low':
        return {
          label: 'Safe',
          textColor: 'text-safe-dark',
          borderColor: 'border-safe',
          bgLight: 'bg-safe-light',
          strokeColor: '#10b981',
        }
      case 'moderate':
        return {
          label: 'Caution',
          textColor: 'text-caution-dark',
          borderColor: 'border-caution',
          bgLight: 'bg-caution-light',
          strokeColor: '#f59e0b',
        }
      case 'high':
        return {
          label: 'High Risk',
          textColor: 'text-danger-dark',
          borderColor: 'border-danger',
          bgLight: 'bg-danger-light',
          strokeColor: '#ef4444',
        }
      case 'severe':
        return {
          label: 'Severe',
          textColor: 'text-danger-dark',
          borderColor: 'border-danger',
          bgLight: 'bg-danger-light',
          strokeColor: '#ef4444',
        }
      default:
        return {
          label: 'Unknown',
          textColor: 'text-caution-dark',
          borderColor: 'border-caution',
          bgLight: 'bg-caution-light',
          strokeColor: '#f59e0b',
        }
    }
  }

  const config = getRiskConfig()
  const percentage = riskLevel === 'low' ? 25 : riskLevel === 'moderate' ? 50 : riskLevel === 'high' ? 75 : 100

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className="relative w-64 h-64">
        {/* Outer circle */}
        <svg className="transform -rotate-90 w-64 h-64" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="8"
          />
          {/* Progress circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke={config.strokeColor}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 45}`}
            strokeDashoffset={`${2 * Math.PI * 45 * (1 - percentage / 100)}`}
          />
        </svg>
        
        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className={`text-4xl font-bold ${config.textColor}`}>
            {config.label}
          </div>
          {safeDuration !== undefined && (
            <div className="text-sm text-gray-600 mt-2">
              {safeDuration} min safe
            </div>
          )}
        </div>
      </div>
      
      {/* Risk level badge */}
      <div className={`mt-4 px-6 py-2 rounded-full ${config.bgLight} ${config.borderColor} border-2`}>
        <span className={`font-semibold ${config.textColor}`}>
          Risk Level: {riskLevel.toUpperCase()}
        </span>
      </div>
    </div>
  )
}

export default RiskDial
