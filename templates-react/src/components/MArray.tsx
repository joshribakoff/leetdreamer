import React from 'react'
import { MPointer, PointerType } from './MPointer'
import './MArray.css'

export interface Pointer {
  index: number
  type: PointerType
  label?: string
}

export interface MArrayProps {
  values: number[]
  highlight?: number[]
  highlightType?: 'left' | 'right' | 'both' | 'sum' | 'found'
  pointers?: Pointer[]
}

export const MArray: React.FC<MArrayProps> = ({
  values,
  highlight = [],
  highlightType,
  pointers = [],
}) => {
  const getHighlightClass = (index: number): string => {
    if (!highlight.includes(index)) return ''

    // Check if both left and right pointers point here
    const hasLeft = pointers.some(p => p.index === index && p.type === 'left')
    const hasRight = pointers.some(p => p.index === index && p.type === 'right')

    if (hasLeft && hasRight) return 'highlight-both'
    if (highlightType === 'found') return 'found'
    if (highlightType === 'sum') return 'highlight-sum'
    if (hasLeft || highlightType === 'left') return 'highlight-left'
    if (hasRight || highlightType === 'right') return 'highlight-right'

    return ''
  }

  const getPointerForCell = (index: number, type: PointerType): Pointer | undefined => {
    return pointers.find(p => p.index === index && p.type === type)
  }

  return (
    <div className="array-container">
      {values.map((value, index) => {
        const highlightClass = getHighlightClass(index)
        const leftPointer = getPointerForCell(index, 'left')
        const rightPointer = getPointerForCell(index, 'right')

        return (
          <div
            key={index}
            className={`array-cell ${highlightClass}`}
            data-index={index}
          >
            {value}
            <span className="index-label">{index}</span>
            {leftPointer && <MPointer type="left" label={leftPointer.label} visible />}
            {rightPointer && <MPointer type="right" label={rightPointer.label} visible />}
          </div>
        )
      })}
    </div>
  )
}
