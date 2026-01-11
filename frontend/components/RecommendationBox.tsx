'use client'

import React from 'react'

interface RecommendationBoxProps {
  advice: string
  riskLevel?: 'low' | 'moderate' | 'high' | 'severe'
}

const RecommendationBox: React.FC<RecommendationBoxProps> = ({
  advice,
  riskLevel = 'moderate',
}) => {
  const getBorderColor = () => {
    switch (riskLevel) {
      case 'low':
        return 'border-safe'
      case 'moderate':
        return 'border-caution'
      case 'high':
      case 'severe':
        return 'border-danger'
      default:
        return 'border-gray-300'
    }
  }

  const getBgColor = () => {
    switch (riskLevel) {
      case 'low':
        return 'bg-safe-light'
      case 'moderate':
        return 'bg-caution-light'
      case 'high':
      case 'severe':
        return 'bg-danger-light'
      default:
        return 'bg-gray-50'
    }
  }

  return (
    <div
      className={`rounded-lg border-2 ${getBorderColor()} ${getBgColor()} p-6 shadow-md`}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0">
          <svg
            className="w-6 h-6 text-gray-700"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            AI Recommendations
          </h3>
          <p className="text-gray-700 leading-relaxed whitespace-pre-line">
            {advice}
          </p>
        </div>
      </div>
    </div>
  )
}

export default RecommendationBox
