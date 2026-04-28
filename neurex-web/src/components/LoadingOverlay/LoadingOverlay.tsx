import React from 'react';
import { BrainCircuit } from 'lucide-react';
import './LoadingOverlay.css';

export function LoadingOverlay({ progress = 0, message = "Initializing Neurex..." }: { progress?: number; message?: string }) {
  return (
    <div className="loading-overlay">
      <div className="loading-overlay__content">
        <h1 className="loading-overlay__title">NEUREX</h1>
        <p className="loading-overlay__message">{message}</p>
        <div className="loading-bar">
          <div className="loading-bar__progress" style={{ width: `${progress}%` }}></div>
        </div>
        <div className="loading-percentage">{Math.round(progress)}%</div>
        
        {(() => {
          const [showBypass, setShowBypass] = React.useState(false);
          React.useEffect(() => {
            const t = setTimeout(() => setShowBypass(true), 3000);
            return () => clearTimeout(t);
          }, []);
          
          if (!showBypass && progress === 0) return null;
          
          return (
            <button 
              className="loading-overlay__bypass animate-fade-in"
              onClick={() => {
                if ((window as any).hidePreloader) (window as any).hidePreloader();
                window.dispatchEvent(new CustomEvent('neurex-force-start'));
              }}
            >
              Launch Anyway
            </button>
          );
        })()}
      </div>
    </div>
  );
}
