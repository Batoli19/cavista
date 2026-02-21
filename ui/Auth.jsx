import { useState } from "react";

const BACKEND_URL = "http://localhost:5000";

// ── STYLES ────────────────────────────────────────────────────────────────────
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --navy:      #0a1628;
    --navy-card: #0d1f3c;
    --teal:      #00c9a7;
    --sky:       #48cae4;
    --white:     #f0f4ff;
    --muted:     #7a8fad;
    --danger:    #ff6b6b;
    --border:    rgba(0,201,167,0.2);
    --glow:      rgba(0,201,167,0.15);
  }

  html, body, #root {
    height: 100%;
    font-family: 'Sora', sans-serif;
    background: var(--navy);
    color: var(--white);
    overflow-x: hidden;
  }

  .auth-bg {
    position: fixed; inset: 0; z-index: 0;
    background:
      radial-gradient(ellipse 80% 60% at 10% 20%, rgba(0,201,167,0.08) 0%, transparent 60%),
      radial-gradient(ellipse 60% 50% at 90% 80%, rgba(72,202,228,0.07) 0%, transparent 60%),
      var(--navy);
  }

  .auth-grid-lines {
    position: fixed; inset: 0; z-index: 0;
    background-image:
      linear-gradient(rgba(0,201,167,0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,201,167,0.04) 1px, transparent 1px);
    background-size: 48px 48px;
  }

  .auth-page {
    position: relative; z-index: 1;
    min-height: 100vh;
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  /* LEFT PANEL */
  .auth-left {
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 60px 64px;
    border-right: 1px solid var(--border);
    position: relative;
    overflow: hidden;
  }

  .auth-left::after {
    content: '';
    position: absolute;
    right: -1px; top: 20%; bottom: 20%;
    width: 1px;
    background: linear-gradient(to bottom, transparent, var(--teal), transparent);
    animation: pulse-line 3s ease-in-out infinite;
  }

  @keyframes pulse-line {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 1; }
  }

  .auth-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 56px;
    animation: fadeUp 0.6s ease both;
  }

  .auth-brand-icon {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, var(--teal), var(--sky));
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    box-shadow: 0 0 24px var(--glow);
  }

  .auth-brand-name {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: var(--white);
  }

  .auth-brand-name span { color: var(--teal); }

  .auth-hero-tag {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: var(--teal);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 20px;
    animation: fadeUp 0.6s 0.1s ease both;
  }

  .auth-hero-title {
    font-size: clamp(32px, 3.5vw, 48px);
    font-weight: 700;
    line-height: 1.1;
    letter-spacing: -1.5px;
    margin-bottom: 24px;
    animation: fadeUp 0.6s 0.2s ease both;
  }

  .auth-hero-title .accent { color: var(--teal); }

  .auth-hero-desc {
    font-size: 15px;
    color: var(--muted);
    line-height: 1.7;
    max-width: 400px;
    margin-bottom: 48px;
    animation: fadeUp 0.6s 0.3s ease both;
  }

  .auth-features {
    display: flex;
    flex-direction: column;
    gap: 16px;
    animation: fadeUp 0.6s 0.4s ease both;
  }

  .auth-feature {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 16px 20px;
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    border-radius: 12px;
    transition: all 0.3s;
    cursor: default;
  }

  .auth-feature:hover {
    background: rgba(0,201,167,0.06);
    border-color: rgba(0,201,167,0.35);
    transform: translateX(4px);
  }

  .auth-feature-icon { font-size: 20px; margin-top: 2px; flex-shrink: 0; }
  .auth-feature-text strong { display: block; font-size: 13px; font-weight: 600; color: var(--white); margin-bottom: 3px; }
  .auth-feature-text span { font-size: 12px; color: var(--muted); line-height: 1.5; }

  /* RIGHT PANEL */
  .auth-right {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px 64px;
  }

  .auth-card {
    width: 100%;
    max-width: 440px;
    animation: fadeUp 0.7s 0.2s ease both;
  }

  /* TABS */
  .auth-tabs {
    display: flex;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 4px;
    margin-bottom: 36px;
  }

  .auth-tab {
    flex: 1;
    padding: 10px;
    border: none;
    background: transparent;
    color: var(--muted);
    font-family: 'Sora', sans-serif;
    font-size: 13px;
    font-weight: 500;
    border-radius: 9px;
    cursor: pointer;
    transition: all 0.3s;
  }

  .auth-tab.active {
    background: linear-gradient(135deg, var(--teal), var(--sky));
    color: var(--navy);
    font-weight: 700;
    box-shadow: 0 4px 16px rgba(0,201,167,0.3);
  }

  /* FORM */
  .auth-form-title { font-size: 26px; font-weight: 700; letter-spacing: -0.8px; margin-bottom: 6px; }
  .auth-form-subtitle { font-size: 13px; color: var(--muted); margin-bottom: 32px; }

  .auth-field { margin-bottom: 18px; }

  .auth-field label {
    display: block;
    font-size: 12px;
    font-weight: 600;
    color: var(--muted);
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 8px;
  }

  .auth-input-wrap { position: relative; }
  .auth-input-wrap .auth-icon {
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 16px;
    color: var(--muted);
    pointer-events: none;
  }

  .auth-input-wrap input,
  .auth-field select {
    width: 100%;
    padding: 13px 16px 13px 44px;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    border-radius: 10px;
    color: var(--white);
    font-family: 'Sora', sans-serif;
    font-size: 14px;
    outline: none;
    transition: all 0.3s;
  }

  .auth-field select { padding-left: 16px; }

  .auth-input-wrap input::placeholder { color: rgba(122,143,173,0.5); }

  .auth-input-wrap input:focus,
  .auth-field select:focus {
    border-color: var(--teal);
    background: rgba(0,201,167,0.06);
    box-shadow: 0 0 0 3px rgba(0,201,167,0.1);
  }

  .auth-field select option { background: var(--navy-card); color: var(--white); }

  /* BUTTON */
  .auth-btn {
    width: 100%;
    padding: 14px;
    background: linear-gradient(135deg, var(--teal), var(--sky));
    border: none;
    border-radius: 10px;
    color: var(--navy);
    font-family: 'Sora', sans-serif;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s;
    margin-top: 8px;
    letter-spacing: -0.3px;
    box-shadow: 0 4px 20px rgba(0,201,167,0.3);
  }

  .auth-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(0,201,167,0.4); }
  .auth-btn:active { transform: translateY(0); }
  .auth-btn:disabled { opacity: 0.7; cursor: not-allowed; transform: none; }

  .auth-btn-back {
    background: rgba(255,255,255,0.08);
    color: var(--white);
    box-shadow: none;
    flex: 0.4;
  }

  .auth-btn-back:hover { background: rgba(255,255,255,0.14); transform: none; box-shadow: none; }

  .auth-btn-row { display: flex; gap: 12px; margin-top: 8px; }
  .auth-btn-row .auth-btn:last-child { flex: 1; }

  /* ALERT */
  .auth-alert {
    padding: 12px 16px;
    border-radius: 10px;
    font-size: 13px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    animation: fadeUp 0.3s ease both;
  }

  .auth-alert.error {
    background: rgba(255,107,107,0.1);
    border: 1px solid rgba(255,107,107,0.3);
    color: #ff6b6b;
  }

  .auth-alert.success {
    background: rgba(0,201,167,0.1);
    border: 1px solid rgba(0,201,167,0.3);
    color: var(--teal);
  }

  /* PASSWORD STRENGTH */
  .strength-bar { margin-top: 8px; display: flex; gap: 4px; }
  .strength-seg { flex: 1; height: 3px; background: rgba(255,255,255,0.1); border-radius: 99px; transition: background 0.3s; }
  .strength-seg.weak   { background: #ff6b6b; }
  .strength-seg.medium { background: #ffd166; }
  .strength-seg.strong { background: var(--teal); }
  .strength-label { font-size: 11px; margin-top: 5px; }

  /* STEPS */
  .auth-steps { display: flex; align-items: center; gap: 8px; margin-bottom: 28px; }
  .auth-step { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--muted); }
  .auth-step-num {
    width: 22px; height: 22px;
    border-radius: 50%;
    background: rgba(255,255,255,0.06);
    border: 1px solid var(--border);
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 600;
  }
  .auth-step.active .auth-step-num { background: var(--teal); border-color: var(--teal); color: var(--navy); }
  .auth-step.done   .auth-step-num { background: rgba(0,201,167,0.2); border-color: var(--teal); color: var(--teal); }
  .auth-step-line { flex: 1; height: 1px; background: var(--border); }

  /* FOOTER */
  .auth-footer { margin-top: 24px; text-align: center; font-size: 12px; color: var(--muted); }
  .auth-footer a { color: var(--teal); text-decoration: none; font-weight: 600; cursor: pointer; }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  @media (max-width: 900px) {
    .auth-page { grid-template-columns: 1fr; }
    .auth-left { display: none; }
    .auth-right { padding: 40px 24px; }
  }
`;

// ── HELPERS ───────────────────────────────────────────────────────────────────
function getStrength(val) {
  if (!val) return { score: 0, label: "", color: "" };
  let score = 0;
  if (val.length >= 8)  score++;
  if (val.length >= 12) score++;
  if (/[A-Z]/.test(val) && /[0-9]/.test(val)) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;
  const labels = ["Too short", "Weak", "Medium", "Strong 💪"];
  const colors = ["#ff6b6b", "#ff6b6b", "#ffd166", "var(--teal)"];
  return { score, label: labels[score - 1] || "", color: colors[score - 1] || "" };
}

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// ── STEP INDICATOR ────────────────────────────────────────────────────────────
function StepIndicator({ step }) {
  return (
    <div className="auth-steps">
      <div className={`auth-step ${step >= 1 ? (step > 1 ? "done" : "active") : ""}`}>
        <div className="auth-step-num">{step > 1 ? "✓" : "1"}</div>
        <span>Account</span>
      </div>
      <div className="auth-step-line" />
      <div className={`auth-step ${step >= 2 ? (step > 2 ? "done" : "active") : ""}`}>
        <div className="auth-step-num">{step > 2 ? "✓" : "2"}</div>
        <span>Profile</span>
      </div>
      <div className="auth-step-line" />
      <div className={`auth-step ${step >= 3 ? "active" : ""}`}>
        <div className="auth-step-num">3</div>
        <span>Done</span>
      </div>
    </div>
  );
}

// ── ALERT ─────────────────────────────────────────────────────────────────────
function Alert({ msg, type }) {
  if (!msg) return null;
  return (
    <div className={`auth-alert ${type}`}>
      <span>{type === "error" ? "⚠️" : "✅"}</span>
      <span>{msg}</span>
    </div>
  );
}

// ── INPUT FIELD ───────────────────────────────────────────────────────────────
function Field({ label, icon, type = "text", value, onChange, placeholder }) {
  return (
    <div className="auth-field">
      <label>{label}</label>
      <div className="auth-input-wrap">
        <span className="auth-icon">{icon}</span>
        <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} />
      </div>
    </div>
  );
}

// ── LOGIN FORM ────────────────────────────────────────────────────────────────
function LoginForm({ onSwitch }) {
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading]   = useState(false);
  const [alert, setAlert]       = useState({ msg: "", type: "" });

  async function handleLogin() {
    if (!email)    return setAlert({ msg: "Please enter your email", type: "error" });
    if (!password) return setAlert({ msg: "Please enter your password", type: "error" });

    setLoading(true);
    setAlert({ msg: "", type: "" });

    try {
      const res  = await fetch(`${BACKEND_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();

      if (!res.ok) {
        setAlert({ msg: data.error || "Wrong email or password", type: "error" });
      } else {
        localStorage.setItem("token",  data.token);
        localStorage.setItem("doctor", JSON.stringify(data.doctor));
        setAlert({ msg: "Login successful! Redirecting...", type: "success" });
        setTimeout(() => window.location.href = "dashboard.html", 1200);
      }
    } catch {
      // Demo mode
      setAlert({ msg: "Demo mode: Redirecting to dashboard...", type: "success" });
      setTimeout(() => window.location.href = "dashboard.html", 1200);
    }

    setLoading(false);
  }

  return (
    <div>
      <h2 className="auth-form-title">Welcome back</h2>
      <p className="auth-form-subtitle">Sign in to your doctor account</p>

      <Alert {...alert} />

      <Field label="Email Address" icon="📧" type="email"
        value={email} onChange={setEmail} placeholder="doctor@hospital.com" />

      <Field label="Password" icon="🔒" type="password"
        value={password} onChange={setPassword} placeholder="Enter your password" />

      <button className="auth-btn" onClick={handleLogin} disabled={loading}>
        {loading ? "Signing in..." : "Sign In to Dashboard"}
      </button>

      <div className="auth-footer">
        Don't have an account?{" "}
        <a onClick={() => onSwitch("signup")}>Create one here</a>
      </div>
    </div>
  );
}

// ── SIGNUP FORM ───────────────────────────────────────────────────────────────
function SignupForm({ onSwitch }) {
  const [step, setStep]               = useState(1);
  const [alert, setAlert]             = useState({ msg: "", type: "" });
  const [loading, setLoading]         = useState(false);

  // Step 1 fields
  const [fullName, setFullName]       = useState("");
  const [email, setEmail]             = useState("");
  const [password, setPassword]       = useState("");
  const [confirm, setConfirm]         = useState("");

  // Step 2 fields
  const [licenseNo, setLicenseNo]     = useState("");
  const [spec, setSpec]               = useState("");
  const [hospital, setHospital]       = useState("");
  const [phone, setPhone]             = useState("");

  const strength = getStrength(password);
  const segClass = (i) => {
    if (strength.score === 0 || i > strength.score) return "strength-seg";
    if (strength.score <= 1) return "strength-seg weak";
    if (strength.score === 2) return "strength-seg medium";
    return "strength-seg strong";
  };

  function goStep2() {
    if (!fullName)               return setAlert({ msg: "Please enter your full name", type: "error" });
    if (!email)                  return setAlert({ msg: "Please enter your email", type: "error" });
    if (!validateEmail(email))   return setAlert({ msg: "Please enter a valid email", type: "error" });
    if (password.length < 8)     return setAlert({ msg: "Password must be at least 8 characters", type: "error" });
    if (password !== confirm)    return setAlert({ msg: "Passwords do not match", type: "error" });
    setAlert({ msg: "", type: "" });
    setStep(2);
  }

  async function handleSignup() {
    if (!licenseNo) return setAlert({ msg: "Please enter your license number", type: "error" });
    if (!spec)      return setAlert({ msg: "Please select your specialization", type: "error" });
    if (!hospital)  return setAlert({ msg: "Please enter your hospital name", type: "error" });
    if (!phone)     return setAlert({ msg: "Please enter your phone number", type: "error" });

    setLoading(true);
    setAlert({ msg: "", type: "" });

    const payload = {
      full_name:      fullName,
      email,
      password,
      license_no:     licenseNo,
      specialization: spec,
      hospital_name:  hospital,
      phone,
    };

    try {
      const res  = await fetch(`${BACKEND_URL}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (!res.ok) {
        setAlert({ msg: data.error || "Sign up failed. Try again.", type: "error" });
      } else {
        localStorage.setItem("token",  data.token);
        localStorage.setItem("doctor", JSON.stringify(data.doctor));
        setStep(3);
        setAlert({ msg: "Account created! Taking you to dashboard...", type: "success" });
        setTimeout(() => window.location.href = "dashboard.html", 1200);
      }
    } catch {
      // Demo mode
      setStep(3);
      setAlert({ msg: "Account created! Taking you to dashboard...", type: "success" });
      setTimeout(() => window.location.href = "dashboard.html", 1200);
    }

    setLoading(false);
  }

  return (
    <div>
      <StepIndicator step={step} />
      <Alert {...alert} />

      {/* ── STEP 1 ── */}
      {step === 1 && (
        <div>
          <h2 className="auth-form-title">Create account</h2>
          <p className="auth-form-subtitle">Step 1 of 2 — Your login details</p>

          <Field label="Full Name" icon="👤"
            value={fullName} onChange={setFullName} placeholder="Dr. John Smith" />

          <Field label="Email Address" icon="📧" type="email"
            value={email} onChange={setEmail} placeholder="doctor@hospital.com" />

          <div className="auth-field">
            <label>Password</label>
            <div className="auth-input-wrap">
              <span className="auth-icon">🔒</span>
              <input type="password" value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Min. 8 characters" />
            </div>
            <div className="strength-bar">
              {[1,2,3,4].map(i => <div key={i} className={segClass(i)} />)}
            </div>
            {strength.label && (
              <div className="strength-label" style={{ color: strength.color }}>
                {strength.label}
              </div>
            )}
          </div>

          <Field label="Confirm Password" icon="🔒" type="password"
            value={confirm} onChange={setConfirm} placeholder="Repeat your password" />

          <button className="auth-btn" onClick={goStep2}>Continue →</button>
        </div>
      )}

      {/* ── STEP 2 ── */}
      {step === 2 && (
        <div>
          <h2 className="auth-form-title">Your profile</h2>
          <p className="auth-form-subtitle">Step 2 of 2 — Professional details</p>

          <Field label="Medical License Number" icon="🪪"
            value={licenseNo} onChange={setLicenseNo} placeholder="e.g. LIC123456" />

          <div className="auth-field">
            <label>Specialization</label>
            <select value={spec} onChange={e => setSpec(e.target.value)}>
              <option value="" disabled>Select your specialization</option>
              {["General Practitioner","Internal Medicine","Paediatrics","Cardiology",
                "Neurology","Orthopaedics","Gynaecology","Emergency Medicine","Psychiatry",
                "Surgery","Other"].map(s => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </div>

          <Field label="Hospital / Clinic Name" icon="🏥"
            value={hospital} onChange={setHospital} placeholder="e.g. Gaborone Private Hospital" />

          <Field label="Phone Number" icon="📞" type="tel"
            value={phone} onChange={setPhone} placeholder="e.g. 0712 345 678" />

          <div className="auth-btn-row">
            <button className="auth-btn auth-btn-back"
              onClick={() => { setStep(1); setAlert({ msg: "", type: "" }); }}>
              ← Back
            </button>
            <button className="auth-btn" onClick={handleSignup} disabled={loading}>
              {loading ? "Creating account..." : "Create My Account"}
            </button>
          </div>
        </div>
      )}

      <div className="auth-footer">
        Already have an account?{" "}
        <a onClick={() => onSwitch("login")}>Sign in here</a>
      </div>
    </div>
  );
}

// ── MAIN AUTH COMPONENT ───────────────────────────────────────────────────────
export default function Auth() {
  const [activeTab, setActiveTab] = useState("login");

  return (
    <>
      <style>{styles}</style>
      <div className="auth-bg" />
      <div className="auth-grid-lines" />

      <div className="auth-page">

        {/* LEFT PANEL */}
        <div className="auth-left">
          <div className="auth-brand">
            <div className="auth-brand-icon">🎙️</div>
            <div className="auth-brand-name">Voice<span>First</span></div>
          </div>

          <div className="auth-hero-tag">Clinical Documentation System</div>

          <h1 className="auth-hero-title">
            Medicine at the<br />
            speed of <span className="accent">speech.</span>
          </h1>

          <p className="auth-hero-desc">
            Record consultations, extract patient data automatically,
            get AI-powered diagnosis suggestions — all from a single conversation.
            Zero typing required.
          </p>

          <div className="auth-features">
            {[
              { icon: "🎤", title: "Voice Recording", desc: "Record doctor-patient consultations in real time with live transcription" },
              { icon: "🧠", title: "AI Diagnosis Support", desc: "Get ranked diagnosis suggestions with reasoning after every consultation" },
              { icon: "📋", title: "Auto SOAP Notes", desc: "Clinical notes generated automatically — doctor just reviews and approves" },
            ].map(f => (
              <div className="auth-feature" key={f.title}>
                <div className="auth-feature-icon">{f.icon}</div>
                <div className="auth-feature-text">
                  <strong>{f.title}</strong>
                  <span>{f.desc}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="auth-right">
          <div className="auth-card">

            {/* TABS */}
            <div className="auth-tabs">
              <button
                className={`auth-tab ${activeTab === "login" ? "active" : ""}`}
                onClick={() => setActiveTab("login")}>
                Sign In
              </button>
              <button
                className={`auth-tab ${activeTab === "signup" ? "active" : ""}`}
                onClick={() => setActiveTab("signup")}>
                Create Account
              </button>
            </div>

            {/* FORMS */}
            {activeTab === "login"
              ? <LoginForm  onSwitch={setActiveTab} />
              : <SignupForm onSwitch={setActiveTab} />
            }

          </div>
        </div>

      </div>
    </>
  );
}
