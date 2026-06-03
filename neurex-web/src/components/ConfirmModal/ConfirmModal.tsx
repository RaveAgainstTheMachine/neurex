// src/components/ConfirmModal/ConfirmModal.tsx
"use client";

import { useEffect, useRef } from "react";
import { AlertTriangle, X } from "lucide-react";
import "./ConfirmModal.css";

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
}

export function ConfirmModal({ 
  isOpen, onClose, onConfirm, title, message, 
  confirmLabel = "Confirm", cancelLabel = "Cancel", danger = true 
}: ConfirmModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === "Escape") onClose();
      if (e.key === "Enter") onConfirm();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [isOpen, onClose, onConfirm]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="confirm-modal animate-scale" onClick={e => e.stopPropagation()} ref={modalRef}>
        <div className="confirm-modal__header">
          <div className="confirm-modal__title">
            {danger && <AlertTriangle size={18} className="text-red mr-2" />}
            {title}
          </div>
          <button className="close-btn" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="confirm-modal__body">
          <p>{message}</p>
        </div>
        <div className="confirm-modal__footer">
          <button className="btn btn--secondary" onClick={onClose}>{cancelLabel}</button>
          <button className={`btn ${danger ? "btn--red" : "btn--purple"}`} onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
