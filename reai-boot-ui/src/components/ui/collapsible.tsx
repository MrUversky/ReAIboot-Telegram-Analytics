import React, { useState, createContext, useContext } from 'react'

interface CollapsibleContextType {
  isOpen: boolean
  setIsOpen: (open: boolean) => void
}

const CollapsibleContext = createContext<CollapsibleContextType | undefined>(undefined)

interface CollapsibleProps {
  children: React.ReactNode
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export function Collapsible({ children, open, onOpenChange }: CollapsibleProps) {
  const [internalOpen, setInternalOpen] = useState(false)
  const isControlled = open !== undefined
  const isOpen = isControlled ? open : internalOpen

  const setIsOpen = (newOpen: boolean) => {
    if (!isControlled) {
      setInternalOpen(newOpen)
    }
    onOpenChange?.(newOpen)
  }

  return (
    <CollapsibleContext.Provider value={{ isOpen, setIsOpen }}>
      {children}
    </CollapsibleContext.Provider>
  )
}

interface CollapsibleTriggerProps {
  children: React.ReactNode
  asChild?: boolean
}

export function CollapsibleTrigger({ children, asChild = false }: CollapsibleTriggerProps) {
  const context = useContext(CollapsibleContext)

  if (!context) {
    throw new Error('CollapsibleTrigger must be used within Collapsible')
  }

  const { isOpen, setIsOpen } = context

  const handleClick = () => {
    setIsOpen(!isOpen)
  }

  if (asChild) {
    return React.cloneElement(children as React.ReactElement, {
      onClick: handleClick
    })
  }

  return (
    <button onClick={handleClick}>
      {children}
    </button>
  )
}

interface CollapsibleContentProps {
  children: React.ReactNode
  className?: string
}

export function CollapsibleContent({ children, className = '' }: CollapsibleContentProps) {
  const context = useContext(CollapsibleContext)

  if (!context) {
    throw new Error('CollapsibleContent must be used within Collapsible')
  }

  const { isOpen } = context

  if (!isOpen) {
    return null
  }

  return (
    <div className={className}>
      {children}
    </div>
  )
}
