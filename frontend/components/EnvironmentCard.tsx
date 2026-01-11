'use client'

import React from 'react'

interface EnvironmentCardProps {
  title: string
  value: string | number
  unit?: string
  icon?: React.ReactNode
  status?: 'good' | 'moderate' | 'poor'
}

const EnvironmentCard: React.FC<EnvironmentCardProps> = ({
  title,
  value,
  unit,
  icon,
  status = 'good',
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'good':
        return 'border-safe bg-safe-light'
      case 'moderate':
        return 'border-caution bg-caution-light'
      case 'poor':
        return 'border-danger bg-danger-light'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }

  return (
    <div
      className={`rounded-lg border-2 p-4 shadow-sm transition-all hover:shadow-md ${getStatusColor()}`}
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        {icon && <div className="text-gray-600">{icon}</div>}
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold text-gray-900">{value}</span>
        {unit && <span className="text-sm text-gray-600">{unit}</span>}
      </div>
        <div className="text-2xl font-bold">
        {typeof value === 'number' ? value.toFixed(1) : "--"} 
        <span className="text-sm text-gray-500">{unit}</span>
        </div>
    </div>
  )
}

export default EnvironmentCard
