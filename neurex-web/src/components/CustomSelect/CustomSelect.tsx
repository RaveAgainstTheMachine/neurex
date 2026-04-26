import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';
import './CustomSelect.css';

export interface SelectOption {
  value: string;
  label: string;
  group?: string;
}

interface CustomSelectProps {
  value: string;
  onChange: (val: string) => void;
  options: SelectOption[];
  className?: string;
  title?: string;
}

export function CustomSelect({ value, onChange, options, className = '', title }: CustomSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find(o => o.value === value) || options[0];

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Group options if 'group' is provided
  const grouped = options.reduce((acc, opt) => {
    const g = opt.group || 'none';
    if (!acc[g]) acc[g] = [];
    acc[g].push(opt);
    return acc;
  }, {} as Record<string, SelectOption[]>);

  return (
    <div className={`custom-select ${className}`} ref={containerRef} title={title}>
      <button 
        type="button" 
        className={`custom-select__trigger ${isOpen ? 'active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="custom-select__label">{selectedOption?.label}</span>
        <ChevronDown size={12} className="custom-select__icon" />
      </button>
      
      {isOpen && (
        <div className="custom-select__dropdown">
          {Object.entries(grouped).map(([group, opts]) => (
            <div key={group} className="custom-select__group">
              {group !== 'none' && <div className="custom-select__group-label">{group}</div>}
              {opts.map(opt => (
                <button
                  key={opt.value}
                  type="button"
                  className={`custom-select__option ${opt.value === value ? 'selected' : ''}`}
                  onClick={() => {
                    onChange(opt.value);
                    setIsOpen(false);
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
