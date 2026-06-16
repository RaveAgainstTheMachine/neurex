import { useState, useEffect } from "react";
import { useStore } from "../../lib/store";
import { Lock, User, Shield, ArrowRight, Loader2, Cpu } from "lucide-react";
import "./AuthOverlay.css";
import toast from "react-hot-toast";

import { API_BASE } from "../../lib/config";

export function AuthOverlay() {
  const [isLogin, setIsLogin] = useState(true);
  const [checkingOnboarding, setCheckingOnboarding] = useState(true);
  const [showOtp, setShowOtp] = useState(false);
  const [showForceChange, setShowForceChange] = useState(false);
  const [showSkillsSetup, setShowSkillsSetup] = useState(false);
  const [skillsList, setSkillsList] = useState<any[]>([]);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [initToken, setInitToken] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [loading, setLoading] = useState(false);
  const setAuth = useStore(s => s.setAuth);
  const onboardingRequired = useStore(s => s.onboardingRequired);
  const setOnboardingRequired = useStore(s => s.setOnboardingRequired);

  const fetchSkills = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/skills/curated`);
      const data = await res.json();
      setSkillsList(data);
    } catch (err) {
      console.error("Failed to fetch skills:", err);
    }
  };

  useEffect(() => {
    const checkOnboarding = async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 1500);

      try {
        const res = await fetch(`${API_BASE}/api/auth/onboarding/status`, {
          signal: controller.signal
        });
        clearTimeout(timeoutId);
        const data = await res.json();
        if (data.onboarding_required) {
          setOnboardingRequired(true);
        }
      } catch (err) {
        console.error("Onboarding check failed or timed out:", err);
      } finally {
        setCheckingOnboarding(false);
      }
    };
    checkOnboarding();
  }, []);

  const handleOnboardingSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password || !initToken) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/onboarding/setup?username=${username}&password=${password}&token=${initToken}`, {
        method: "POST"
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Onboarding failed");
      }

      toast.success("Master account created! Please configure skills.");
      await fetchSkills();
      setShowSkillsSetup(true);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;

    setLoading(true);
    try {
      const endpoint = isLogin ? "/api/auth/token" : "/api/auth/register";
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Authentication failed");
      }

      if (!isLogin) {
        toast.success("Account created! Please sign in.");
        setIsLogin(true);
        setLoading(false);
        return;
      }

      const data = await res.json();
      
      if (data.password_change_required) {
        setShowForceChange(true);
        setLoading(false);
        return;
      }

      if (data.otp_required) {
        setShowOtp(true);
        setLoading(false);
        return;
      }

      const userRes = await fetch(`${API_BASE}/api/auth/me`, {
        headers: { "Authorization": `Bearer ${data.access_token}` }
      });
      const userData = await userRes.json();
      
      setAuth(data.access_token, userData);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOtpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpCode) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/token-otp?username=${username}&code=${otpCode}`, {
        method: "POST"
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Invalid OTP");
      }

      const data = await res.json();

      if (data.password_change_required) {
        setShowForceChange(true);
        setShowOtp(false);
        setLoading(false);
        return;
      }

      const userRes = await fetch(`${API_BASE}/api/auth/me`, {
        headers: { "Authorization": `Bearer ${data.access_token}` }
      });
      const userData = await userRes.json();
      
      setAuth(data.access_token, userData);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleForceChangeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPassword) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/change-password?username=${username}&old_password=${password}&new_password=${newPassword}`, {
        method: "POST"
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to change password");
      }

      const data = await res.json();
      const userRes = await fetch(`${API_BASE}/api/auth/me`, {
        headers: { "Authorization": `Bearer ${data.access_token}` }
      });
      const userData = await userRes.json();
      
      toast.success("Security credentials updated");
      setAuth(data.access_token, userData);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (checkingOnboarding) {
    return (
      <div className="auth-overlay">
        <div className="auth-mesh-bg" />
        <div className="auth-loader">
          <Loader2 className="animate-spin text-accent" size={32} />
          <span>Syncing Neural Mesh...</span>
        </div>
      </div>
    );
  }

  if (onboardingRequired) {
    return (
      <div className="auth-overlay">
        <div className="auth-mesh-bg" />
        <div className="auth-card glass">
          <div className="auth-card__header">
            <div className="auth-logo">
              <div className="auth-logo__inner logo-pulse">⬡</div>
            </div>
            <h2>Admin Setup</h2>
            <p className="text-muted">Setup your administrator account to begin.</p>
          </div>

          <form className="auth-form" onSubmit={handleOnboardingSubmit}>
            <div className="auth-input-group">
              <div className="auth-input">
                <Shield size={18} className="auth-input__icon" />
                <input 
                  type="text" 
                  placeholder="Installation Token (check logs)" 
                  value={initToken}
                  onChange={e => setInitToken(e.target.value)}
                  required
                />
              </div>
              <div className="auth-input">
                <User size={18} className="auth-input__icon" />
                <input 
                  type="text" 
                  placeholder="Master Username" 
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  required
                />
              </div>
              <div className="auth-input">
                <Lock size={18} className="auth-input__icon" />
                <input 
                  type="password" 
                  placeholder="Initial Password" 
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <button className="btn btn--purple auth-submit" disabled={loading}>
              {loading ? <Loader2 className="animate-spin" /> : "Create Admin Account"}
            </button>
          </form>

          <div className="auth-badge">
            <Cpu size={12} />
            Stand-alone Node Mode
          </div>
        </div>
      </div>
    );
  }

  if (showSkillsSetup) {
    return (
      <div className="auth-overlay">
        <div className="auth-mesh-bg" />
        <div className="auth-card glass" style={{ maxWidth: '800px', width: '90%' }}>
          <div className="auth-card__header">
            <div className="auth-logo">
              <div className="auth-logo__inner logo-pulse"><Shield size={32} /></div>
            </div>
            <h2>Skills & Security Governance</h2>
            <p className="text-muted">Select active skills for your workspace. Critical skills are recommended.</p>
          </div>

          <div className="skills-setup-list" style={{ maxHeight: '400px', overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {skillsList.map(skill => (
              <div key={skill.id} className="skill-card glass" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
                <div>
                  <h4 style={{ margin: '0 0 0.25rem 0', color: 'var(--text-main)' }}>{skill.name}</h4>
                  <p className="text-muted" style={{ margin: 0, fontSize: '0.9rem' }}>{skill.description}</p>
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                    <span className="badge" style={{ backgroundColor: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px', fontSize: '0.8rem', color: 'var(--text-main)' }}>{skill.category}</span>
                    {skill.enabled && <span className="badge text-accent" style={{ backgroundColor: 'rgba(156, 111, 255, 0.1)', padding: '2px 6px', borderRadius: '4px', fontSize: '0.8rem' }}>Critical - Recommended</span>}
                  </div>
                </div>
                <div>
                  <label className="toggle-switch" style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input 
                      type="checkbox" 
                      checked={skill.enabled} 
                      onChange={async (e) => {
                         const newState = e.target.checked;
                         setSkillsList(prev => prev.map(s => s.id === skill.id ? { ...s, enabled: newState } : s));
                         try {
                             const action = newState ? 'allow' : 'deny';
                             await fetch(`${API_BASE}/api/mcp/permissions`, {
                                 method: 'POST',
                                 headers: { 'Content-Type': 'application/json' },
                                 body: JSON.stringify({ tool_name: skill.id, rule: action })
                             });
                         } catch(err) {
                             console.error("Failed to update permission", err);
                         }
                      }}
                      style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                    />
                  </label>
                </div>
              </div>
            ))}
          </div>

          <div style={{ padding: '1rem', display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
            <button className="btn btn--purple auth-submit" onClick={() => {
              setOnboardingRequired(false);
              setIsLogin(true);
              setShowSkillsSetup(false);
            }}>
              Complete Setup <ArrowRight size={18} style={{ marginLeft: '8px' }} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (showForceChange) {
    return (
      <div className="auth-overlay">
        <div className="auth-mesh-bg" />
        <div className="auth-card glass">
          <div className="auth-card__header">
            <div className="auth-logo">
              <div className="auth-logo__inner logo-pulse"><Shield size={32} /></div>
            </div>
            <h2>Update Credentials</h2>
            <p className="text-muted">You must establish a permanent password for this identity</p>
          </div>

          <form className="auth-form" onSubmit={handleForceChangeSubmit}>
            <div className="auth-input">
              <Lock size={18} className="auth-input__icon" />
              <input 
                type="password" 
                placeholder="New Permanent Password" 
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                required
                autoFocus
              />
            </div>
            <button className="btn btn--purple auth-submit" disabled={loading}>
              {loading ? <Loader2 className="animate-spin" /> : "Synthesize Permanent Link"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (showOtp) {
    return (
      <div className="auth-overlay">
        <div className="auth-mesh-bg" />
        <div className="auth-card glass">
          <div className="auth-card__header">
            <div className="auth-logo">
              <div className="auth-logo__inner logo-pulse"><Shield size={32} /></div>
            </div>
            <h2>Verification Required</h2>
            <p className="text-muted">Enter the 6-digit code from your authenticator app</p>
          </div>

          <form className="auth-form" onSubmit={handleOtpSubmit}>
            <div className="auth-input">
              <Lock size={18} className="auth-input__icon" />
              <input 
                type="text" 
                placeholder="000000" 
                value={otpCode}
                onChange={e => setOtpCode(e.target.value)}
                maxLength={6}
                required
                autoFocus
              />
            </div>
            <button className="btn btn--purple auth-submit" disabled={loading}>
              {loading ? <Loader2 className="animate-spin" /> : "Verify & Connect"}
            </button>
          </form>

          <div className="auth-footer">
            <button className="auth-toggle" onClick={() => setShowOtp(false)}>
              Back to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-overlay">
      <div className="auth-mesh-bg" />
      <div className="auth-card glass">
        <div className="auth-card__header">
          <div className="auth-logo">
            <div className="auth-logo__inner logo-pulse">⬡</div>
          </div>
          <h2>{isLogin ? "Welcome Back" : "Create Account"}</h2>
          <p className="text-muted">
            {isLogin 
              ? "Sign in to your workspace" 
              : "Register to join the mesh"}
          </p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-input-group">
            <div className="auth-input">
              <User size={18} className="auth-input__icon" />
              <input 
                type="text" 
                placeholder="Username" 
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="auth-input">
              <Lock size={18} className="auth-input__icon" />
              <input 
                type="password" 
                placeholder="Password" 
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button className="btn btn--purple auth-submit" disabled={loading}>
            {loading ? <Loader2 className="animate-spin" /> : (
              <>
                {isLogin ? "Connect" : "Register"}
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <button className="auth-toggle" onClick={() => setIsLogin(!isLogin)}>
            {isLogin ? "Need an account? Register" : "Already have an account? Login"}
          </button>
        </div>

        <div className="auth-badge">
          <Shield size={12} />
          Encrypted Connection Active
        </div>
      </div>
    </div>
  );
}
