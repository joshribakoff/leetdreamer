import React from 'react'
import './MTarget.css'

export interface MTargetProps {
  value: number
  visible?: boolean
}

export const MTarget: React.FC<MTargetProps> = ({ value, visible = true }) => {
  if (!visible) return null

  return (
    <div className="target-display">
      Target: {value}
    </div>
  )
}
