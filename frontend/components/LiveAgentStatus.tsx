'use client'

import React from 'react'

export interface Step {
  id: string
  name: string
  status: 'pending' | 'active' | 'completed'
}

interface LiveAgentStatusProps {
  isStreaming: boolean
  steps: Step[]
}

const LiveAgentStatus: React.FC<LiveAgentStatusProps> = ({ isStreaming, steps }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Live Agent Status</h3>
      <div className="space-y-4">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center gap-4 relative">
            {/* Step indicator */}
            <div className="flex-shrink-0 relative z-10">
              {step.status === 'completed' ? (
                <div className="w-8 h-8 rounded-full bg-safe flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
              ) : step.status === 'active' ? (
                <div className="w-8 h-8 rounded-full bg-caution flex items-center justify-center">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : (
                <div className="w-8 h-8 rounded-full border-2 border-gray-300 flex items-center justify-center bg-white">
                  <div className="w-3 h-3 rounded-full bg-gray-300"></div>
                </div>
              )}
            </div>

            {/* Step name */}
            <div className="flex-1">
              <span
                className={`text-sm font-medium ${
                  step.status === 'completed'
                    ? 'text-safe-dark'
                    : step.status === 'active'
                    ? 'text-caution-dark'
                    : 'text-gray-500'
                }`}
              >
                {step.name}
              </span>
            </div>

            {/* Connecting line */}
            {index < steps.length - 1 && (
              <div
                className={`absolute left-4 top-10 w-0.5 h-12 ${
                  step.status === 'completed' ? 'bg-safe' : 'bg-gray-200'
                }`}
                style={{ zIndex: 0 }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// Export a hook to update steps
export const useAgentStatus = () => {
  const [steps, setSteps] = React.useState<Step[]>([
    { id: 'fetch_enviro_data', name: 'Fetching Data...', status: 'pending' },
    { id: 'analyze_risk', name: 'Analyzing Pollen Risks...', status: 'pending' },
    { id: 'generate_advice', name: 'Calculating Safe Duration...', status: 'pending' },
    { id: 'done', name: 'Done.', status: 'pending' },
  ])

  const updateStep = React.useCallback((stepId: string, status: 'active' | 'completed') => {
    setSteps(prevSteps => {
      const newSteps = [...prevSteps]
      const stepIndex = newSteps.findIndex(s => s.id === stepId)
      
      if (stepIndex !== -1) {
        // Update current step
        newSteps[stepIndex] = { ...newSteps[stepIndex], status }
        
        // Mark previous steps as completed
        for (let i = 0; i < stepIndex; i++) {
          if (newSteps[i].status !== 'completed') {
            newSteps[i] = { ...newSteps[i], status: 'completed' }
          }
        }
      }
      
      return newSteps
    })
  }, [])

  const resetSteps = React.useCallback(() => {
    setSteps([
      { id: 'fetch_enviro_data', name: 'Fetching Data...', status: 'pending' },
      { id: 'analyze_risk', name: 'Analyzing Pollen Risks...', status: 'pending' },
      { id: 'generate_advice', name: 'Calculating Safe Duration...', status: 'pending' },
      { id: 'done', name: 'Done.', status: 'pending' },
    ])
  }, [])

  return { steps, updateStep, resetSteps }
}

export default LiveAgentStatus
