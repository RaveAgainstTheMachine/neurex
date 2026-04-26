import { useState, useEffect } from "react";
import { useStore } from "../../lib/store";
import { Lock, User, Shield, ArrowRight, Loader2, Cpu } from "lucide-react";
import "./AuthOverlay.css";
import toast from "react-hot-toast";

const API_BASE = window.location.origin.includes(":3000") 
  ? window.location.origin.replace(":3000", ":8000") 
  : window.location.origin;

export function AuthOverlay() {
  const [isLogin, setIsLogin] = useState(true);
  const [onboardingRequired, setOnboardingRequired] = useState(false);
  const [checkingOnboarding, setCheckingOnboarding] = useState(true);
  const [showOtp, setShowOtp] = useState(false);
  const [showForceChange, setShowForceChange] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [initToken, setInitToken] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [loading, setLoading] = useState(false);
  const setAuth = useStore(s => s.setAuth);

  useEffect(() => {
    const checkOnboarding = async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

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

      toast.success("Master Identity Synthesized! Please sign in.");
      setOnboardingRequired(false);
      setIsLogin(true);
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
          <Loader2 className="animate-spin text-purple" size={32} />
          <span>Syncing Mesh...</span>
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
              <div className="auth-logo__inner">⬡</div>
            </div>
            <h2>Master Initialization</h2>
            <p className="text-muted">No administrative presence detected. Synthesis required.</p>
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
              {loading ? <Loader2 className="animate-spin" /> : "Synthesize Master Identity"}
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

  if (showForceChange) {
    return (
      <div className="auth-overlay">
        <div className="auth-mesh-bg" />
        <div className="auth-card glass">
          <div className="auth-card__header">
            <div className="auth-logo">
              <div className="auth-logo__inner"><Shield size={32} /></div>
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
              <div className="auth-logo__inner"><Shield size={32} /></div>
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
            <div className="auth-logo__inner">⬡</div>
          </div>
          <h2>{isLogin ? "Neural Link Established" : "Synthesize New Identity"}</h2>
          <p className="text-muted">
            {isLogin 
              ? "Accessing the Neurex Federated Mesh" 
              : "Register your presence in the global compute swarm"}
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
            {isLogin ? "Request Mesh Access (Register)" : "Identify Presence (Login)"}
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
