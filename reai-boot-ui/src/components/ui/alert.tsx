import React from 'react'
import { AlertTriangle, CheckCircle, Info, XCircle } from 'lucide-react'

interface AlertProps {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'destructive' | 'success' | 'warning'
}

export function Alert({ children, className = '', variant = 'default' }: AlertProps) {
  const getVariantClasses = () => {
    switch (variant) {
      case 'destructive':
        return 'border-red-200 bg-red-50 text-red-900'
      case 'success':
        return 'border-green-200 bg-green-50 text-green-900'
      case 'warning':
        return 'border-yellow-200 bg-yellow-50 text-yellow-900'
      default:
        return 'border-blue-200 bg-blue-50 text-blue-900'
    }
  }

  return (
    <div className={`p-4 border rounded-lg ${getVariantClasses()} ${className}`}>
      {children}
    </div>
  )
}

interface AlertDescriptionProps {
  children: React.ReactNode
  className?: string
}

export function AlertDescription({ children, className = '' }: AlertDescriptionProps) {
  return (
    <div className={`text-sm ${className}`}>
      {children}
    </div>
  )
}

// Icon components for alerts
export function AlertIcon({ type = 'info', className = '' }: { type?: 'info' | 'success' | 'warning' | 'error', className?: string }) {
  const getIcon = () => {
    switch (type) {
      case 'success':
        return <CheckCircle className={`h-4 w-4 ${className}`} />
      case 'warning':
        return <AlertTriangle className={`h-4 w-4 ${className}`} />
      case 'error':
        return <XCircle className={`h-4 w-4 ${className}`} />
      default:
        return <Info className={`h-4 w-4 ${className}`} />
    }
  }

  return getIcon()
}
