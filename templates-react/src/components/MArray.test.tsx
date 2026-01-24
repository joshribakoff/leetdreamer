import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MArray } from './MArray'

describe('MArray', () => {
  it('renders correct number of cells', () => {
    const { container } = render(<MArray values={[2, 7, 11, 15]} />)
    const cells = container.querySelectorAll('.array-cell')
    expect(cells.length).toBe(4)
  })

  it('renders index labels', () => {
    const { container } = render(<MArray values={[100, 200, 300]} />)
    const labels = container.querySelectorAll('.index-label')
    expect(labels.length).toBe(3)
    expect(labels[0].textContent).toBe('0')
    expect(labels[1].textContent).toBe('1')
    expect(labels[2].textContent).toBe('2')
  })

  it('applies highlight class to specified indices', () => {
    const { container } = render(
      <MArray values={[1, 2, 3]} highlight={[1]} highlightType="left" />
    )
    const cells = container.querySelectorAll('.array-cell')
    expect(cells[1].classList.contains('highlight-left')).toBe(true)
  })

  it('shows pointers at correct positions', () => {
    render(
      <MArray
        values={[1, 2, 3]}
        pointers={[{ index: 0, type: 'left' }, { index: 2, type: 'right' }]}
      />
    )
    const leftPointer = screen.getByText('L')
    const rightPointer = screen.getByText('R')
    expect(leftPointer.classList.contains('visible')).toBe(true)
    expect(rightPointer.classList.contains('visible')).toBe(true)
  })

  it('handles empty array', () => {
    const { container } = render(<MArray values={[]} />)
    const cells = container.querySelectorAll('.array-cell')
    expect(cells.length).toBe(0)
  })

  it('applies highlight-both when left and right pointers overlap', () => {
    const { container } = render(
      <MArray
        values={[1, 2, 3]}
        highlight={[1]}
        pointers={[
          { index: 1, type: 'left' },
          { index: 1, type: 'right' },
        ]}
      />
    )
    const cells = container.querySelectorAll('.array-cell')
    expect(cells[1].classList.contains('highlight-both')).toBe(true)
  })
})
