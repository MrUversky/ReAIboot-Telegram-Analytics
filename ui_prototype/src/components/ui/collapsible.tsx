import React, { useState } from 'react';

interface CollapsibleProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}

export const Collapsible: React.FC<CollapsibleProps> = ({
  open = false,
  onOpenChange,
  children,
}) => {
  const [internalOpen, setInternalOpen] = useState(open);

  const isOpen = onOpenChange !== undefined ? open : internalOpen;

  const handleOpenChange = (newOpen: boolean) => {
    if (onOpenChange) {
      onOpenChange(newOpen);
    } else {
      setInternalOpen(newOpen);
    }
  };

  return (
    <div>
      {React.Children.map(children, (child) =>
        React.isValidElement(child)
          ? React.cloneElement(child, {
              open: isOpen,
              onOpenChange: handleOpenChange,
            })
          : child
      )}
    </div>
  );
};

interface CollapsibleTriggerProps {
  children: React.ReactNode;
  asChild?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export const CollapsibleTrigger: React.FC<CollapsibleTriggerProps> = ({
  children,
  asChild = false,
  open,
  onOpenChange,
}) => {
  const handleClick = () => {
    onOpenChange?.(!open);
  };

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, {
      onClick: handleClick,
    });
  }

  return (
    <button onClick={handleClick}>
      {children}
    </button>
  );
};

interface CollapsibleContentProps {
  children: React.ReactNode;
  open?: boolean;
  className?: string;
}

export const CollapsibleContent: React.FC<CollapsibleContentProps> = ({
  children,
  open = false,
  className = '',
}) => {
  if (!open) return null;

  return (
    <div className={`overflow-hidden ${className}`}>
      {children}
    </div>
  );
};
