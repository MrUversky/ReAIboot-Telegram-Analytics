import React, { useState } from 'react'
import { ChevronDown } from 'lucide-react'

interface SelectProps {
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
}

export function Select({ value, onValueChange, children }: SelectProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="relative">
      {React.Children.map(children, (child) => {
        const childElement = child as React.ReactElement
        return React.cloneElement(childElement, {
          ...(childElement.props as any),
          isOpen,
          setIsOpen,
          value,
          onValueChange
        })
      })}
    </div>
  )
}

interface SelectTriggerProps {
  children: React.ReactNode
  className?: string
}

export function SelectTrigger({ children, className = '' }: SelectTriggerProps) {
  return (
    <button
      type="button"
      className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
    >
      {children}
      <ChevronDown className="h-4 w-4 opacity-50" />
    </button>
  )
}

interface SelectValueProps {
  placeholder?: string
}

export function SelectValue({ placeholder }: SelectValueProps) {
  return <span className="text-gray-500">{placeholder}</span>
}

interface SelectContentProps {
  children: React.ReactNode
}

export function SelectContent({ children }: SelectContentProps) {
  return (
    <div className="absolute z-10 mt-1 max-h-60 min-w-full overflow-auto rounded-md border border-gray-200 bg-white py-1 text-sm shadow-lg">
      {children}
    </div>
  )
}

interface SelectItemProps {
  value: string
  children: React.ReactNode
}

export function SelectItem({ value, children }: SelectItemProps) {
  return (
    <div
      className="relative cursor-pointer select-none px-3 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
      data-value={value}
    >
      {children}
    </div>
  )
}
