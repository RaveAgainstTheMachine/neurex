import React, { useState, useEffect, useRef } from 'react';
import './Modals.css';

interface InputDialogProps {
  isOpen: boolean;
  title: string;
  defaultValue?: string;
  placeholder?: string;
  onConfirm: (value: string) => void;
  onClose: () => void;
}

export function InputDialog({ isOpen, title, defaultValue = "", placeholder = "", onConfirm, onClose }: InputDialogProps) {
  const [value, setValue] = useState(defaultValue);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setValue(defaultValue);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen, defaultValue]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim()) {
      onConfirm(value.trim());
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content glass animate-scale" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
        </div>
        <form onSubmit={handleSubmit} className="modal-body">
          <input
            ref={inputRef}
            type="text"
            className="modal-input"
            value={value}
            onChange={e => setValue(e.target.value)}
            placeholder={placeholder}
          />
          <div className="modal-actions">
            <button type="button" className="btn btn--secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn--purple">Confirm</button>
          </div>
        </form>
      </div>
    </div>
  );
}
