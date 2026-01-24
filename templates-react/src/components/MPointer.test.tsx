import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MPointer } from './MPointer'

describe('MPointer', () => {
  it('renders with default label L for left type', () => {
    render(<MPointer type="left" visible />)
    expect(screen.getByText('L')).toBeDefined()
  })

  it('renders with default label R for right type', () => {
    render(<MPointer type="right" visible />)
    expect(screen.getByText('R')).toBeDefined()
  })

  it('uses custom label when provided', () => {
    render(<MPointer type="left" label="i" visible />)
    expect(screen.getByText('i')).toBeDefined()
  })

  it('has correct class for left pointer', () => {
    const { container } = render(<MPointer type="left" visible />)
    const pointer = container.querySelector('.pointer')
    expect(pointer?.classList.contains('left-pointer')).toBe(true)
  })

  it('has correct class for right pointer', () => {
    const { container } = render(<MPointer type="right" visible />)
    const pointer = container.querySelector('.pointer')
    expect(pointer?.classList.contains('right-pointer')).toBe(true)
  })

  it('is hidden by default', () => {
    const { container } = render(<MPointer type="left" />)
    const pointer = container.querySelector('.pointer')
    expect(pointer?.classList.contains('visible')).toBe(false)
  })

  it('is visible when visible prop is true', () => {
    const { container } = render(<MPointer type="left" visible />)
    const pointer = container.querySelector('.pointer')
    expect(pointer?.classList.contains('visible')).toBe(true)
  })
})
