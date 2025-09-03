import React, { useState, useRef, useEffect } from 'react'
import { ChevronDown, ChevronUp, Check } from 'lucide-react'

interface SelectProps {
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
}

export function Select({ value, onValueChange, children }: SelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const selectRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleItemClick = (itemValue: string) => {
    onValueChange?.(itemValue)
    setIsOpen(false)
  }

  // Find the selected item's text
  const getSelectedText = () => {
    if (!value) return null

    let selectedText = null
    React.Children.forEach(children, (child) => {
      if (React.isValidElement(child) && child.type === SelectContent) {
        const contentProps = child.props as { children?: React.ReactNode }
        React.Children.forEach(contentProps.children, (item) => {
          if (React.isValidElement(item) && (item.props as any).value === value) {
            selectedText = (item.props as any).children
          }
        })
      }
    })
    return selectedText
  }

  const selectedText = getSelectedText()

  return (
    <div className="relative" ref={selectRef}>
      {React.Children.map(children, (child) => {
        const childElement = child as React.ReactElement
        return React.cloneElement(childElement, {
          ...(childElement.props as any),
          isOpen,
          setIsOpen,
          value,
          selectedText,
          onItemClick: handleItemClick
        })
      })}
    </div>
  )
}

interface SelectTriggerProps {
  children: React.ReactNode
  className?: string
  isOpen?: boolean
  setIsOpen?: (open: boolean) => void
  value?: string
  selectedText?: React.ReactNode
}

export function SelectTrigger({ children, className = '', isOpen, setIsOpen, value, selectedText }: SelectTriggerProps) {
  return (
    <button
      type="button"
      onClick={() => setIsOpen?.(!isOpen)}
      className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50 dark:bg-gray-50 dark:border-gray-300 dark:text-gray-900 dark:focus:ring-blue-500 ${className}`}
    >
      <span className={selectedText ? "text-gray-900 dark:text-gray-100" : "text-gray-500 dark:text-gray-400"}>
        {selectedText || "Выберите опцию"}
      </span>
      {isOpen ? (
        <ChevronUp className="h-4 w-4 opacity-50 text-gray-500 dark:text-gray-400" />
      ) : (
        <ChevronDown className="h-4 w-4 opacity-50 text-gray-500 dark:text-gray-400" />
      )}
    </button>
  )
}

interface SelectValueProps {
  placeholder?: string
  value?: string
  selectedText?: React.ReactNode
}

export function SelectValue({ placeholder, value, selectedText }: SelectValueProps) {
  return (
    <span className={selectedText ? "text-gray-900 dark:text-gray-100" : "text-gray-500 dark:text-gray-400"}>
      {selectedText || placeholder}
    </span>
  )
}

interface SelectContentProps {
  children: React.ReactNode
  isOpen?: boolean
  onItemClick?: (value: string) => void
  selectedText?: React.ReactNode
  value?: string
}

export function SelectContent({ children, isOpen, onItemClick, selectedText, value }: SelectContentProps) {
  if (!isOpen) return null

  return (
    <div className="absolute z-10 mt-1 max-h-60 min-w-full overflow-auto rounded-md border border-gray-200 bg-white py-1 text-sm text-gray-900 shadow-lg dark:bg-gray-50 dark:border-gray-300 dark:text-gray-900">
      {React.Children.map(children, (child) => {
        const childElement = child as React.ReactElement<any>
        return React.cloneElement(childElement, {
          ...(childElement.props as any),
          onClick: () => onItemClick?.(childElement.props.value),
          selectedText,
          currentValue: value
        })
      })}
    </div>
  )
}

interface SelectItemProps {
  value: string
  children: React.ReactNode
  onClick?: () => void
  selectedText?: React.ReactNode
  currentValue?: string
}

export function SelectItem({ value, children, onClick, currentValue }: SelectItemProps) {
  const isSelected = currentValue === value

  return (
    <div
      className={`relative cursor-pointer select-none px-3 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none dark:hover:bg-gray-200 dark:focus:bg-gray-200 ${isSelected ? 'bg-blue-50 text-blue-900 dark:bg-blue-900 dark:text-blue-100' : ''}`}
      onClick={onClick}
      data-value={value}
    >
      <div className="flex items-center justify-between">
        <span>{children}</span>
        {isSelected && (
          <Check className="h-4 w-4 text-blue-600 dark:text-blue-400" />
        )}
      </div>
    </div>
  )
}
