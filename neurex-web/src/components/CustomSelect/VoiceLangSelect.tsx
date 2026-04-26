import React, { useState, useRef, useEffect } from 'react';
import { Volume2, Languages, Globe } from 'lucide-react';
import './VoiceLangSelect.css';

interface Option {
  value: string;
  label: string;
}

interface VoiceLangSelectProps {
  voiceValue: string;
  voiceOnChange: (val: string) => void;
  voiceOptions: Option[];
  langValue: string;
  langOnChange: (val: string) => void;
  langOptions: Option[];
}

export function VoiceLangSelect({
  voiceValue,
  voiceOnChange,
  voiceOptions,
  langValue,
  langOnChange,
  langOptions
}: VoiceLangSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="voice-lang-select" ref={containerRef}>
      <button 
        type="button" 
        className={`voice-lang-select__trigger ${isOpen ? 'active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        title="Voice & Language Settings"
      >
        <Globe size={14} />
      </button>

      {isOpen && (
        <div className="voice-lang-select__dropdown">
          <div className="voice-lang-select__section">
            <div className="voice-lang-select__header">
              <Volume2 size={12} /> <span>Voice</span>
            </div>
            <div className="voice-lang-select__grid">
              {voiceOptions.map(opt => (
                <button
                  key={opt.value}
                  className={`voice-lang-select__option ${opt.value === voiceValue ? 'selected' : ''}`}
                  onClick={() => voiceOnChange(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
          <div className="voice-lang-select__divider" />
          <div className="voice-lang-select__section">
            <div className="voice-lang-select__header">
              <Languages size={12} /> <span>Language</span>
            </div>
            <div className="voice-lang-select__grid">
              {langOptions.map(opt => (
                <button
                  key={opt.value}
                  className={`voice-lang-select__option ${opt.value === langValue ? 'selected' : ''}`}
                  onClick={() => langOnChange(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
