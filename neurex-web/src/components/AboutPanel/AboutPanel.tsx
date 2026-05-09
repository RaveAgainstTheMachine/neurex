// src/components/AboutPanel/AboutPanel.tsx
import React from 'react';
import { motion } from 'framer-motion';
import { X, Github, Globe, Shield, Zap, Cpu } from 'lucide-react';
import { useStore } from '../../lib/store';
import './AboutPanel.css';

export function AboutPanel() {
  const { setShowAbout } = useStore();

  return (
    <motion.div 
      className="about-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={() => setShowAbout(false)}
    >
      <motion.div 
        className="about-modal"
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="about-close" onClick={() => setShowAbout(false)}>
          <X size={20} />
        </button>

        <div className="about-header">
          <div className="about-logo">⬡</div>
          <h1>NEUREX</h1>
          <p className="about-tagline">The first autonomous workspace for the neural era.</p>
        </div>

        <div className="about-content">
          <section className="about-section">
            <h2>The Essence</h2>
            <p>
              Neurex is an autonomous engineering workspace designed for human-agent parity. 
              It transforms your infrastructure into a neural mesh where agents are peers, 
              compute is sovereign, and hardware is pooled via distributed VRAM.
            </p>
          </section>

          <div className="about-grid">
            <div className="about-feature">
              <Zap size={16} className="text-purple" />
              <div>
                <h3>Agentic Engineering</h3>
                <p>Autonomous peers with persistent state and real-time collaboration.</p>
              </div>
            </div>
            <div className="about-feature">
              <Cpu size={16} className="text-cyan" />
              <div>
                <h3>VRAM Pooling</h3>
                <p>Combine GPU power across your network into a unified brain.</p>
              </div>
            </div>
            <div className="about-feature">
              <Shield size={16} className="text-green" />
              <div>
                <h3>Zero-Config</h3>
                <p>Self-bootstrapping Rust control plane with hermetic environments.</p>
              </div>
            </div>
          </div>

          <div className="about-footer">
            <div className="about-version">
              <span>Version 0.5.2-PHASE-61</span>
              <span className="status-dot"></span>
              <span>Stable Substrate</span>
            </div>
            <div className="about-links">
              <a href="https://github.com/RaveAgainstTheMachine/neurex" target="_blank" rel="noreferrer">
                <Github size={16} /> GitHub
              </a>
              <a href="https://github.com/RaveAgainstTheMachine/neurex/wiki" target="_blank" rel="noreferrer">
                <Globe size={16} /> Wiki
              </a>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
