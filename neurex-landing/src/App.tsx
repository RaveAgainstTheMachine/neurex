import React from 'react';
import { motion } from 'framer-motion';
import { 
  Zap, Shield, Cpu, Users, 
  Terminal, Globe, Boxes, Search 
} from 'lucide-react';

const FeatureCard = ({ icon: Icon, title, description, delay }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.8, delay }}
    viewport={{ once: true }}
    className="glass feature-card"
  >
    <Icon className="feature-icon" size={32} />
    <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>{title}</h3>
    <p style={{ color: '#adb5bd' }}>{description}</p>
  </motion.div>
);

function App() {
  return (
    <div className="landing-root">
      {/* Navbar */}
      <nav className="container" style={{ padding: '2rem 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontWeight: 900, fontSize: '1.5rem', letterSpacing: '-1px' }}>NEUREX</div>
        <div style={{ display: 'flex', gap: '3rem', fontSize: '0.9rem', fontWeight: 500 }}>
          <a href="#features" style={{ color: 'inherit', textDecoration: 'none' }}>Features</a>
          <a href="#mesh" style={{ color: 'inherit', textDecoration: 'none' }}>The Mesh</a>
          <a href="#security" style={{ color: 'inherit', textDecoration: 'none' }}>Zero Trust</a>
        </div>
        <button className="btn-primary" style={{ padding: '0.6rem 1.5rem', fontSize: '0.9rem' }}>Get Access</button>
      </nav>

      {/* Hero Section */}
      <section className="hero-section container">
        <div style={{ maxWidth: '700px' }}>
          <motion.h1
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
          >
            The Agentic OS <br />for the New Era.
          </motion.h1>
          <motion.p 
            className="hero-sub"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1, delay: 0.3 }}
          >
            Neurex isn't just an IDE. It's a decentralized swarm of intelligence, 
            pooling your hardware and multiplying your potential. 
            Build with absolute autonomy.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
          >
            <button className="btn-primary">Initialize Hive Mind</button>
            <span style={{ marginLeft: '2rem', color: '#6c757d', cursor: 'pointer' }}>Watch the Mesh in Action →</span>
          </motion.div>
        </div>
        <motion.img 
          src="/hero.png" 
          className="hero-visual"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 0.6, scale: 1 }}
          transition={{ duration: 2 }}
        />
      </section>

      {/* Main Showcase */}
      <section className="container" id="features">
        <motion.div 
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 1 }}
          className="mockup-container"
        >
          <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
            <h2 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Smarter together.</h2>
            <p style={{ color: '#adb5bd', fontSize: '1.2rem' }}>Every agent in your mesh shares a single collective memory.</p>
          </div>
          <img src="/ide.png" className="mockup-img" alt="Neurex IDE" />
        </motion.div>

        <div className="feature-grid" style={{ marginTop: '6rem' }}>
          <FeatureCard 
            icon={Boxes}
            title="Mesh Federation"
            description="Link your machines into a single GPU cluster. Pool VRAM, share compute, and run massive models on consumer hardware."
            delay={0.1}
          />
          <FeatureCard 
            icon={Users}
            title="Ghost Collaboration"
            description="Built-in multiplayer for agents and humans. See their cursors, follow their logic, and swarm on codebases in real-time."
            delay={0.2}
          />
          <FeatureCard 
            icon={Search}
            title="Collective Memory"
            description="The Hive Mind indexes every success. When one agent solves a problem, the entire mesh knows the solution forever."
            delay={0.3}
          />
        </div>
      </section>

      {/* Secondary Showcase */}
      <section style={{ backgroundColor: 'var(--bg-accent)' }}>
        <div className="container">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6rem', alignItems: 'center' }}>
            <div>
              <h2 style={{ fontSize: '3.5rem', marginBottom: '2rem' }}>Total Infrastructure Control.</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                <div style={{ display: 'flex', gap: '1.5rem' }}>
                  <Shield style={{ color: 'var(--primary)', flexShrink: 0 }} />
                  <div>
                    <h4 style={{ marginBottom: '0.5rem' }}>Zero-Trust Security</h4>
                    <p style={{ color: '#adb5bd' }}>RBAC-locked endpoints and mTLS tunnels ensure your mesh is invisible to everyone but you.</p>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '1.5rem' }}>
                  <Cpu style={{ color: 'var(--primary)', flexShrink: 0 }} />
                  <div>
                    <h4 style={{ marginBottom: '0.5rem' }}>Intelligent Load Balancing</h4>
                    <p style={{ color: '#adb5bd' }}>The MeshRouter automatically shifts inference tasks to the node with the most available power.</p>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '1.5rem' }}>
                  <Globe style={{ color: 'var(--primary)', flexShrink: 0 }} />
                  <div>
                    <h4 style={{ marginBottom: '0.5rem' }}>Air-Gapped Privacy</h4>
                    <p style={{ color: '#adb5bd' }}>Keep your agents in the dark or let them roam the web. You hold the master switch.</p>
                  </div>
                </div>
              </div>
            </div>
            <motion.div
              initial={{ x: 100, opacity: 0 }}
              whileInView={{ x: 0, opacity: 1 }}
              transition={{ duration: 1 }}
            >
              <img src="/mesh.png" className="mockup-img" alt="Mesh Dashboard" />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Mobile Section */}
      <section className="container">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6rem', alignItems: 'center' }}>
          <motion.div
            initial={{ x: -100, opacity: 0 }}
            whileInView={{ x: 0, opacity: 1 }}
            transition={{ duration: 1 }}
          >
            <img src="/mobile.png" className="mockup-img" alt="Neurex Mobile" />
          </motion.div>
          <div>
            <h2 style={{ fontSize: '3.5rem', marginBottom: '2rem' }}>Command from anywhere.</h2>
            <p style={{ color: '#adb5bd', fontSize: '1.2rem', marginBottom: '2rem' }}>
              Neurex Mobile is your off-band control center. Approve terminal commands, 
              monitor mesh health, and receive critical alerts while you're away from your desk.
            </p>
            <ul style={{ listSetStyle: 'none', display: 'flex', flexDirection: 'column', gap: '1rem', color: '#adb5bd' }}>
              <li>✓ One-tap command approval</li>
              <li>✓ Real-time Mesh telemetry</li>
              <li>✓ Secure mTLS tunnel</li>
              <li>✓ Biometric RBAC authentication</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Exhaustive Features & Glossary */}
      <section style={{ backgroundColor: 'var(--bg-accent)' }}>
        <div className="container">
          <div style={{ textAlign: 'center', marginBottom: '6rem' }}>
            <h2 style={{ fontSize: '3rem' }}>The Intelligence Index</h2>
            <p style={{ color: '#adb5bd' }}>An exhaustive look at the platform's core primitives.</p>
          </div>

          <div className="feature-grid">
            <div className="glass" style={{ padding: '2rem' }}>
              <h4 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>Safety & Governance</h4>
              <ul style={{ fontSize: '0.9rem', color: '#adb5bd', listStyleType: 'none', lineHeight: '2' }}>
                <li>• <b>HITL Approval</b>: Mandatory human sign-off for shell commands</li>
                <li>• <b>One-Way Trash</b>: Agent-immutable deletion protection</li>
                <li>• <b>Sandbox Isolation</b>: Air-gapped Docker execution environments</li>
                <li>• <b>Token Scoping</b>: Cryptographically limited agent permissions</li>
                <li>• <b>Audit Logging</b>: Immutable trace of all swarm operations</li>
              </ul>
            </div>
            <div className="glass" style={{ padding: '2rem' }}>
              <h4 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>Compute & Mesh</h4>
              <ul style={{ fontSize: '0.9rem', color: '#adb5bd', listStyleType: 'none', lineHeight: '2' }}>
                <li>• <b>MeshRouter</b>: Dynamic VRAM load balancing</li>
                <li>• <b>Ollama Proxy</b>: Secure inference streaming</li>
                <li>• <b>MPI Scaffolding</b>: Distributed tensor pooling</li>
                <li>• <b>Resource Capping</b>: Per-node RAM/CPU limits</li>
              </ul>
            </div>
            <div className="glass" style={{ padding: '2rem' }}>
              <h4 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>Security & Auth</h4>
              <ul style={{ fontSize: '0.9rem', color: '#adb5bd', listStyleType: 'none', lineHeight: '2' }}>
                <li>• <b>RBAC Engine</b>: Admin/Dev/Viewer roles</li>
                <li>• <b>Zero-Trust mTLS</b>: Encrypted mesh tunnels</li>
                <li>• <b>JWT Lifecycle</b>: Secure session management</li>
                <li>• <b>Fingerprint Auth</b>: Biometric hardware integration</li>
                <li>• <b>Presence Audit</b>: Real-time collaborator tracking</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container" style={{ textAlign: 'center' }}>
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          whileInView={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8 }}
          className="glass"
          style={{ padding: '6rem 4rem' }}
        >
          <h2 style={{ fontSize: '4rem', marginBottom: '2rem' }}>Ready to join the swarm?</h2>
          <p style={{ color: '#adb5bd', fontSize: '1.3rem', marginBottom: '3rem', maxWidth: '600px', margin: '0 auto 3rem' }}>
            Deploy Neurex on your local machine and start federation in minutes.
            Your agents are waiting.
          </p>
          <div style={{ display: 'flex', gap: '2rem', justifyContent: 'center' }}>
            <button className="btn-primary" style={{ fontSize: '1.3rem', padding: '1.2rem 4rem' }}>Download from GitHub</button>
            <button className="glass" style={{ fontSize: '1.1rem', padding: '1.2rem 3rem', borderRadius: '100px', cursor: 'pointer' }}>Read the Specs</button>
          </div>
          <p style={{ marginTop: '3rem', color: '#6c757d', fontSize: '0.8rem', maxWidth: '500px', margin: '3rem auto 0' }}>
            *Note: Visuals on this page are High-Fidelity Conceptual Renderings representing the North Star UI. 
            The current stable build (v0.1.0) follows this design language but is subject to refinement during our beta phase.
          </p>
        </motion.div>
      </section>

      <footer className="container" style={{ padding: '4rem 0', borderTop: '1px solid var(--glass-border)', color: '#6c757d', fontSize: '0.9rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <div>© 2026 AntiGravity Lab. Built for the era of absolute autonomy.</div>
          <div style={{ display: 'flex', gap: '2rem' }}>
            <a href="https://github.com/sickn33/Neurex" style={{ color: 'inherit' }}>GitHub</a>
            <span>Documentation</span>
            <span>Security</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
