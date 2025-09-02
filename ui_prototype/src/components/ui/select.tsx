import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

interface SelectProps {
  value: string;
  onValueChange: (value: string) => void;
  children: React.ReactNode;
}

export const Select: React.FC<SelectProps> = ({
  value,
  onValueChange,
  children,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      {React.Children.map(children, (child) =>
        React.isValidElement(child)
          ? React.cloneElement(child, {
              value,
              onValueChange,
              isOpen,
              setIsOpen,
            })
          : child
      )}
    </div>
  );
};

interface SelectTriggerProps {
  children: React.ReactNode;
  className?: string;
  setIsOpen?: (isOpen: boolean) => void;
}

export const SelectTrigger: React.FC<SelectTriggerProps> = ({
  children,
  className = '',
  setIsOpen,
}) => {
  return (
    <button
      type="button"
      className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      onClick={() => setIsOpen?.(true)}
    >
      {children}
      <ChevronDown className="h-4 w-4 opacity-50" />
    </button>
  );
};

interface SelectValueProps {
  placeholder?: string;
}

export const SelectValue: React.FC<SelectValueProps> = ({
  placeholder = "Выберите значение",
}) => {
  return <span>{placeholder}</span>;
};

interface SelectContentProps {
  children: React.ReactNode;
  isOpen?: boolean;
  setIsOpen?: (isOpen: boolean) => void;
}

export const SelectContent: React.FC<SelectContentProps> = ({
  children,
  isOpen,
  setIsOpen,
}) => {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40"
        onClick={() => setIsOpen?.(false)}
      />

      {/* Dropdown */}
      <div className="absolute z-50 min-w-[8rem] overflow-hidden rounded-md border border-gray-200 bg-white shadow-md">
        <div className="p-1">
          {React.Children.map(children, (child) =>
            React.isValidElement(child)
              ? React.cloneElement(child, { setIsOpen })
              : child
          )}
        </div>
      </div>
    </>
  );
};

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
  onValueChange?: (value: string) => void;
  setIsOpen?: (isOpen: boolean) => void;
}

export const SelectItem: React.FC<SelectItemProps> = ({
  value,
  children,
  onValueChange,
  setIsOpen,
}) => {
  const handleClick = () => {
    onValueChange?.(value);
    setIsOpen?.(false);
  };

  return (
    <button
      type="button"
      className="relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-gray-100 focus:text-gray-900 data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
      onClick={handleClick}
    >
      {children}
    </button>
  );
};
