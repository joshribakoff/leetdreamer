import { useState, useEffect, useCallback, useRef } from 'react'

export interface TimelineStep<T> {
  state: T
  duration: number // in seconds
}

export interface UseTimelineOptions {
  autoStart?: boolean
  onComplete?: () => void
}

export interface TimelineControls<T> {
  currentStep: number
  currentState: T | null
  isRunning: boolean
  isComplete: boolean
  totalDuration: number
  start: () => void
  pause: () => void
  reset: () => void
  goToStep: (step: number) => void
}

export function useTimeline<T>(
  steps: TimelineStep<T>[],
  options: UseTimelineOptions = {}
): TimelineControls<T> {
  const { autoStart = false, onComplete } = options
  const [currentStep, setCurrentStep] = useState(0)
  const [isRunning, setIsRunning] = useState(autoStart)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const totalDuration = steps.reduce((sum, step) => sum + step.duration, 0)
  const isComplete = currentStep >= steps.length
  const currentState = isComplete ? null : steps[currentStep]?.state ?? null

  const clearTimer = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
  }, [])

  const advanceStep = useCallback(() => {
    setCurrentStep(prev => {
      const next = prev + 1
      if (next >= steps.length) {
        setIsRunning(false)
        onComplete?.()
      }
      return next
    })
  }, [steps.length, onComplete])

  // Schedule next step when running
  useEffect(() => {
    if (!isRunning || isComplete) return

    const duration = steps[currentStep]?.duration ?? 0
    timeoutRef.current = setTimeout(advanceStep, duration * 1000)

    return clearTimer
  }, [isRunning, currentStep, steps, isComplete, advanceStep, clearTimer])

  const start = useCallback(() => {
    if (!isComplete) {
      setIsRunning(true)
    }
  }, [isComplete])

  const pause = useCallback(() => {
    setIsRunning(false)
    clearTimer()
  }, [clearTimer])

  const reset = useCallback(() => {
    clearTimer()
    setCurrentStep(0)
    setIsRunning(false)
  }, [clearTimer])

  const goToStep = useCallback((step: number) => {
    if (step >= 0 && step < steps.length) {
      clearTimer()
      setCurrentStep(step)
    }
  }, [steps.length, clearTimer])

  return {
    currentStep,
    currentState,
    isRunning,
    isComplete,
    totalDuration,
    start,
    pause,
    reset,
    goToStep,
  }
}
