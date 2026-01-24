import React from 'react'
import { MTarget } from './MTarget'
import './Layout.css'

export interface LayoutProps {
  title: string
  target?: number
  message?: string
  step?: number
  totalSteps?: number
  children: React.ReactNode
}

export const Layout: React.FC<LayoutProps> = ({
  title,
  target,
  message,
  step,
  totalSteps,
  children,
}) => {
  return (
    <div className="layout-container">
      <h1 className="title">{title}</h1>
      {target !== undefined && <MTarget value={target} />}
      {children}
      {message && <div className="message-display">{message}</div>}
      {step !== undefined && totalSteps !== undefined && (
        <div className="step-indicator">
          Step {step + 1} of {totalSteps}
        </div>
      )}
    </div>
  )
}
