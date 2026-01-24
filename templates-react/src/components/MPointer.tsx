import React from 'react'
import './MPointer.css'

export type PointerType = 'left' | 'right'

export interface MPointerProps {
  type: PointerType
  label?: string
  visible?: boolean
}

export const MPointer: React.FC<MPointerProps> = ({
  type,
  label,
  visible = false,
}) => {
  const defaultLabel = type === 'left' ? 'L' : 'R'
  const displayLabel = label ?? defaultLabel

  return (
    <span
      className={`pointer ${type}-pointer ${visible ? 'visible' : ''}`}
    >
      {displayLabel}
    </span>
  )
}
