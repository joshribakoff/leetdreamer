import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTimeline, TimelineStep } from './useTimeline'

interface TestState {
  message: string
}

const testSteps: TimelineStep<TestState>[] = [
  { state: { message: 'Step 1' }, duration: 1 },
  { state: { message: 'Step 2' }, duration: 2 },
  { state: { message: 'Step 3' }, duration: 1 },
]

describe('useTimeline', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('starts at step 0', () => {
    const { result } = renderHook(() => useTimeline(testSteps))
    expect(result.current.currentStep).toBe(0)
    expect(result.current.currentState?.message).toBe('Step 1')
  })

  it('calculates total duration', () => {
    const { result } = renderHook(() => useTimeline(testSteps))
    expect(result.current.totalDuration).toBe(4)
  })

  it('does not auto-start by default', () => {
    const { result } = renderHook(() => useTimeline(testSteps))
    expect(result.current.isRunning).toBe(false)
  })

  it('auto-starts when option is set', () => {
    const { result } = renderHook(() =>
      useTimeline(testSteps, { autoStart: true })
    )
    expect(result.current.isRunning).toBe(true)
  })

  it('advances to next step after duration', () => {
    const { result } = renderHook(() =>
      useTimeline(testSteps, { autoStart: true })
    )

    expect(result.current.currentStep).toBe(0)

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    expect(result.current.currentStep).toBe(1)
    expect(result.current.currentState?.message).toBe('Step 2')
  })

  it('stops at the end', () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() =>
      useTimeline(testSteps, { autoStart: true, onComplete })
    )

    // Step 0 -> 1 after 1s, Step 1 -> 2 after 2s, Step 2 completes after 1s
    act(() => {
      vi.advanceTimersByTime(1000) // step 0 -> 1
    })
    act(() => {
      vi.advanceTimersByTime(2000) // step 1 -> 2
    })
    act(() => {
      vi.advanceTimersByTime(1000) // step 2 completes
    })

    expect(result.current.isComplete).toBe(true)
    expect(result.current.isRunning).toBe(false)
    expect(onComplete).toHaveBeenCalledTimes(1)
  })

  it('can pause and resume', () => {
    const { result } = renderHook(() =>
      useTimeline(testSteps, { autoStart: true })
    )

    act(() => {
      vi.advanceTimersByTime(500)
      result.current.pause()
    })

    expect(result.current.isRunning).toBe(false)
    expect(result.current.currentStep).toBe(0)

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    // Should still be at step 0 since paused
    expect(result.current.currentStep).toBe(0)

    act(() => {
      result.current.start()
    })

    expect(result.current.isRunning).toBe(true)
  })

  it('can reset to beginning', () => {
    const { result } = renderHook(() =>
      useTimeline(testSteps, { autoStart: true })
    )

    act(() => {
      vi.advanceTimersByTime(2000)
    })

    expect(result.current.currentStep).toBe(1)

    act(() => {
      result.current.reset()
    })

    expect(result.current.currentStep).toBe(0)
    expect(result.current.isRunning).toBe(false)
  })

  it('can jump to specific step', () => {
    const { result } = renderHook(() => useTimeline(testSteps))

    act(() => {
      result.current.goToStep(2)
    })

    expect(result.current.currentStep).toBe(2)
    expect(result.current.currentState?.message).toBe('Step 3')
  })

  it('ignores invalid step indices', () => {
    const { result } = renderHook(() => useTimeline(testSteps))

    act(() => {
      result.current.goToStep(-1)
    })
    expect(result.current.currentStep).toBe(0)

    act(() => {
      result.current.goToStep(10)
    })
    expect(result.current.currentStep).toBe(0)
  })
})
