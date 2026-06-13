import React from 'react';

export function NeurexLogo({ size = 24, className = "" }: { size?: number; className?: string }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 120 120" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Three Purple Bars - Perfectly Vectorized */}
      <rect x="10" y="15" width="100" height="15" rx="7.5" fill="#A78BFA" />
      <rect x="10" y="45" width="100" height="15" rx="7.5" fill="#A78BFA" />
      <rect x="10" y="75" width="100" height="15" rx="7.5" fill="#A78BFA" />
      
      {/* Logotype (Simplified for small icon, but keeping the soul) */}
      <text 
        x="60" y="112" 
        textAnchor="middle" 
        fill="#e8e8f0" 
        style={{ fontSize: '18px', fontWeight: 'bold', letterSpacing: '2px', fontFamily: 'var(--font-sans)' }}
      >
        NEUREX
      </text>
    </svg>
  );
}
