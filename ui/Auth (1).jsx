import { useState } from "react";

const API = "http://localhost:5000";

const SPECS = [
  "General Practitioner","Internal Medicine","Paediatrics","Cardiology",
  "Neurology","Orthopaedics","Gynaecology","Emergency Medicine","Psychiatry","Surgery","Other"
];

const DOC_FEATS = [
  { i:"🎤", t:"Voice Recording",      d:"Record consultations in real time with live transcription" },
  { i:"🧠", t:"AI Diagnosis Support", d:"Ranked diagnosis suggestions with clinical reasoning" },
  { i:"📋", t:"Auto SOAP Notes",      d:"Notes generated automatically — just review and approve" },
];
const PAT_FEATS = [
  { i:"✍️", t:"Describe Your Symptoms", d:"Type how you feel before your appointment" },
  { i:"🎤", t:"Record a Voice Note",    d:"Record yourself and send it directly to your doctor" },
  { i:"📄", t:"Upload Documents",       d:"Send prescriptions and test results securely" },
];

// ── HELPERS ───────────────────────────────────────────────────────────────────
const vEmail = e => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e);

function getStrength(val) {
  if (!val) return { score:0, label:"", color:"" };
  let s = 0;
  if (val.length >= 8)  s++;
  if (val.length >= 12) s++;
  if (/[A-Z]/.test(val) && /[0-9]/.test(val)) s++;
  if (/[^A-Za-z0-9]/.test(val)) s++;
  return {
    score: s,
    label: ["Too short","Weak","Medium","Strong 💪"][s-1] || "",
    color: ["#ff6b6b","#ff6b6b","#ffd166","#00c9a7"][s-1] || "",
  };
}

async function apiPost(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return { ok: res.ok, data: await res.json() };
}

// ── SMALL COMPONENTS ──────────────────────────────────────────────────────────
function Alert({ msg, type }) {
  if (!msg) return null;
  return (
    <div style={{
      padding:"11px 14px", borderRadius:10, fontSize:12, marginBottom:14,
      display:"flex", alignItems:"center", gap:9,
      background: type==="error" ? "rgba(255,107,107,.1)" : "rgba(0,201,167,.1)",
      border: `1px solid ${type==="error" ? "rgba(255,107,107,.25)" : "rgba(0,201,167,.25)"}`,
      color: type==="error" ? "#ff6b6b" : "#00c9a7",
    }}>
      <span>{type==="error" ? "⚠️" : "✅"}</span>
      <span>{msg}</span>
    </div>
  );
}

function Field({ label, icon, type="text", value, onChange, placeholder, isPat=false }) {
  const focusColor = isPat ? "#7c6af7" : "#00c9a7";
  const [focused, setFocused] = useState(false);
  return (
    <div style={{ marginBottom:14 }}>
      <label style={{ display:"block", fontSize:11, fontWeight:600, color:"#7a8fad", letterSpacing:.5, textTransform:"uppercase", marginBottom:6 }}>
        {label}
      </label>
      <div style={{ position:"relative" }}>
        <span style={{ position:"absolute", left:12, top:"50%", transform:"translateY(-50%)", fontSize:15, color:"#7a8fad", pointerEvents:"none" }}>
          {icon}
        </span>
        <input
          type={type} value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          style={{
            width:"100%", padding:"11px 13px 11px 40px",
            background: focused ? `rgba(${isPat?"124,106,247":"0,201,167"},.05)` : "rgba(255,255,255,.04)",
            border: `1px solid ${focused ? focusColor : "rgba(255,255,255,.1)"}`,
            borderRadius:10, color:"#f0f4ff", fontFamily:"Sora,sans-serif", fontSize:13,
            outline:"none", transition:"all .3s",
            boxShadow: focused ? `0 0 0 3px rgba(${isPat?"124,106,247":"0,201,167"},.07)` : "none",
          }}
        />
      </div>
    </div>
  );
}

function StrengthBar({ val }) {
  const { score, label, color } = getStrength(val);
  const segColor = i => {
    if (!score || i > score) return "rgba(255,255,255,.1)";
    return score<=1 ? "#ff6b6b" : score===2 ? "#ffd166" : "#00c9a7";
  };
  return (
    <>
      <div style={{ display:"flex", gap:4, marginTop:6 }}>
        {[1,2,3,4].map(i => <div key={i} style={{ flex:1, height:3, borderRadius:99, background:segColor(i), transition:"background .3s" }}/>)}
      </div>
      {label && <div style={{ fontSize:11, marginTop:4, color }}>{label}</div>}
    </>
  );
}

function Steps({ step, isDoc }) {
  const ac = isDoc ? "#00c9a7" : "#7c6af7";
  const labels = ["Account", isDoc ? "Profile" : "Details", "Done"];
  return (
    <div style={{ display:"flex", alignItems:"center", gap:7, marginBottom:22 }}>
      {[1,2,3].map((n, i) => (
        <div key={n} style={{ display:"contents" }}>
          {i > 0 && <div style={{ flex:1, height:1, background:"rgba(255,255,255,.08)" }}/>}
          <div style={{ display:"flex", alignItems:"center", gap:5, fontSize:11, color: step>=n ? ac : "#7a8fad" }}>
            <div style={{
              width:20, height:20, borderRadius:"50%", display:"flex",
              alignItems:"center", justifyContent:"center", fontSize:10, fontWeight:600,
              background: step>n ? "rgba(0,201,167,.15)" : step===n ? ac : "rgba(255,255,255,.06)",
              border: `1px solid ${step>=n ? ac : "rgba(255,255,255,.1)"}`,
              color: step===n ? (isDoc?"#0a1628":"#fff") : step>n ? ac : "#7a8fad",
            }}>
              {step > n ? "✓" : n}
            </div>
            <span>{labels[i]}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function Btn({ children, onClick, disabled, isPat=false, variant="primary" }) {
  const [hovered, setHovered] = useState(false);
  const isBack = variant === "back";
  return (
    <button
      onClick={onClick} disabled={disabled}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width: isBack ? "auto" : "100%", flex: isBack ? .4 : undefined,
        padding:"12px", border:"none", borderRadius:10,
        fontFamily:"Sora,sans-serif", fontSize:14, fontWeight:700,
        cursor: disabled ? "not-allowed" : "pointer", marginTop:5,
        transition:"all .3s", opacity: disabled ? .6 : 1,
        background: isBack ? "rgba(255,255,255,.07)"
          : isPat ? "linear-gradient(135deg,#7c6af7,#a78bfa)"
          : "linear-gradient(135deg,#00c9a7,#48cae4)",
        color: isBack ? "#f0f4ff" : isPat ? "#fff" : "#0a1628",
        boxShadow: isBack ? "none"
          : isPat ? "0 4px 18px rgba(124,106,247,.25)"
          : "0 4px 18px rgba(0,201,167,.25)",
        transform: hovered && !disabled && !isBack ? "translateY(-2px)" : "none",
        filter: hovered && !disabled && !isBack ? "brightness(1.05)" : "none",
      }}>
      {children}
    </button>
  );
}

// ── DOCTOR LOGIN ──────────────────────────────────────────────────────────────
function DoctorLogin({ onSwitch }) {
  const [email, setEmail]   = useState("");
  const [pass,  setPass]    = useState("");
  const [loading, setLoad]  = useState(false);
  const [alert, setAlert]   = useState({ msg:"", type:"" });

  async function submit() {
    if (!email) return setAlert({ msg:"Enter your email", type:"error" });
    if (!pass)  return setAlert({ msg:"Enter your password", type:"error" });
    setLoad(true); setAlert({ msg:"", type:"" });
    try {
      const { ok, data } = await apiPost("/api/auth/login", { email, password:pass, role:"doctor" });
      if (!ok) setAlert({ msg: data.error||"Wrong email or password", type:"error" });
      else {
        localStorage.setItem("token",  data.token);
        localStorage.setItem("doctor", JSON.stringify(data.doctor));
        localStorage.setItem("role",   "doctor");
        setAlert({ msg:"Login successful! Redirecting...", type:"success" });
        setTimeout(() => window.location.href = "dashboard.html", 1200);
      }
    } catch {
      setAlert({ msg:"Demo: Redirecting to dashboard...", type:"success" });
      setTimeout(() => window.location.href = "dashboard.html", 1200);
    }
    setLoad(false);
  }

  return (
    <div>
      <h2 style={S.ftitle}>Welcome back, Doctor</h2>
      <p style={S.fsub}>Sign in to your clinical dashboard</p>
      <Alert {...alert}/>
      <Field label="Email" icon="📧" type="email" value={email} onChange={setEmail} placeholder="doctor@hospital.com"/>
      <Field label="Password" icon="🔒" type="password" value={pass} onChange={setPass} placeholder="Your password"/>
      <Btn onClick={submit} disabled={loading}>{loading ? "Signing in..." : "Sign In to Dashboard →"}</Btn>
      <div style={S.ffoot}>No account? <a style={S.link} onClick={() => onSwitch("signup")}>Register here</a></div>
    </div>
  );
}

// ── PATIENT LOGIN ─────────────────────────────────────────────────────────────
function PatientLogin({ onSwitch }) {
  const [email, setEmail]   = useState("");
  const [pass,  setPass]    = useState("");
  const [loading, setLoad]  = useState(false);
  const [alert, setAlert]   = useState({ msg:"", type:"" });

  async function submit() {
    if (!email) return setAlert({ msg:"Enter your email", type:"error" });
    if (!pass)  return setAlert({ msg:"Enter your password", type:"error" });
    setLoad(true); setAlert({ msg:"", type:"" });
    try {
      const { ok, data } = await apiPost("/api/auth/login", { email, password:pass, role:"patient" });
      if (!ok) setAlert({ msg: data.error||"Wrong email or password", type:"error" });
      else {
        localStorage.setItem("token",   data.token);
        localStorage.setItem("patient", JSON.stringify(data.patient));
        localStorage.setItem("role",    "patient");
        setAlert({ msg:"Login successful! Opening patient portal...", type:"success" });
        setTimeout(() => window.location.href = "patient-portal.html", 1200);
      }
    } catch {
      setAlert({ msg:"Demo: Opening patient portal...", type:"success" });
      setTimeout(() => window.location.href = "patient-portal.html", 1200);
    }
    setLoad(false);
  }

  return (
    <div>
      <div style={S.badge}>🧑 Patient Portal Access</div>
      <h2 style={S.ftitle}>Welcome back</h2>
      <p style={S.fsub}>Sign in to your patient account</p>
      <Alert {...alert}/>
      <Field label="Email" icon="📧" type="email" value={email} onChange={setEmail} placeholder="yourname@email.com" isPat/>
      <Field label="Password" icon="🔒" type="password" value={pass} onChange={setPass} placeholder="Your password" isPat/>
      <Btn onClick={submit} disabled={loading} isPat>{loading ? "Signing in..." : "Sign In to Patient Portal →"}</Btn>
      <div style={S.ffoot}>No account? <a style={S.linkPat} onClick={() => onSwitch("signup")}>Register here</a></div>
    </div>
  );
}

// ── DOCTOR SIGNUP ─────────────────────────────────────────────────────────────
function DoctorSignup({ onSwitch }) {
  const [step, setStep]   = useState(1);
  const [alert, setAlert] = useState({ msg:"", type:"" });
  const [loading, setLoad]= useState(false);
  const [name,  setName]  = useState("");
  const [email, setEmail] = useState("");
  const [pass,  setPass]  = useState("");
  const [conf,  setConf]  = useState("");
  const [lic,   setLic]   = useState("");
  const [spec,  setSpec]  = useState("");
  const [hosp,  setHosp]  = useState("");
  const [phone, setPhone] = useState("");

  function next() {
    if (!name)           return setAlert({ msg:"Enter your full name", type:"error" });
    if (!vEmail(email))  return setAlert({ msg:"Enter a valid email", type:"error" });
    if (pass.length < 8) return setAlert({ msg:"Password needs 8+ characters", type:"error" });
    if (pass !== conf)   return setAlert({ msg:"Passwords do not match", type:"error" });
    setAlert({ msg:"", type:"" }); setStep(2);
  }

  async function submit() {
    if (!lic)   return setAlert({ msg:"Enter your license number", type:"error" });
    if (!spec)  return setAlert({ msg:"Select your specialization", type:"error" });
    if (!hosp)  return setAlert({ msg:"Enter your hospital name", type:"error" });
    if (!phone) return setAlert({ msg:"Enter your phone number", type:"error" });
    setLoad(true); setAlert({ msg:"", type:"" });
    try {
      const { ok, data } = await apiPost("/api/auth/signup", {
        full_name:name, email, password:pass,
        license_no:lic, specialization:spec, hospital_name:hosp, phone, role:"doctor"
      });
      if (!ok) setAlert({ msg: data.error||"Sign up failed", type:"error" });
      else {
        localStorage.setItem("token",  data.token);
        localStorage.setItem("doctor", JSON.stringify(data.doctor));
        localStorage.setItem("role",   "doctor");
        setStep(3);
        setAlert({ msg:"Account created! Taking you to dashboard...", type:"success" });
        setTimeout(() => window.location.href = "dashboard.html", 1200);
      }
    } catch {
      setAlert({ msg:"Demo: Taking you to dashboard...", type:"success" });
      setTimeout(() => window.location.href = "dashboard.html", 1200);
    }
    setLoad(false);
  }

  return (
    <div>
      <Steps step={step} isDoc={true}/>
      <Alert {...alert}/>

      {step === 1 && <>
        <h2 style={S.ftitle}>Create doctor account</h2>
        <p style={S.fsub}>Step 1 of 2 — Login details</p>
        <Field label="Full Name" icon="👤" value={name} onChange={setName} placeholder="Dr. John Smith"/>
        <Field label="Email" icon="📧" type="email" value={email} onChange={setEmail} placeholder="doctor@hospital.com"/>
        <div style={{ marginBottom:14 }}>
          <label style={{ display:"block", fontSize:11, fontWeight:600, color:"#7a8fad", letterSpacing:.5, textTransform:"uppercase", marginBottom:6 }}>Password</label>
          <div style={{ position:"relative" }}>
            <span style={{ position:"absolute", left:12, top:"50%", transform:"translateY(-50%)", fontSize:15, color:"#7a8fad", pointerEvents:"none" }}>🔒</span>
            <input type="password" value={pass} onChange={e => setPass(e.target.value)} placeholder="Min. 8 characters"
              style={{ width:"100%", padding:"11px 13px 11px 40px", background:"rgba(255,255,255,.04)", border:"1px solid rgba(255,255,255,.1)", borderRadius:10, color:"#f0f4ff", fontFamily:"Sora,sans-serif", fontSize:13, outline:"none" }}/>
          </div>
          <StrengthBar val={pass}/>
        </div>
        <Field label="Confirm Password" icon="🔒" type="password" value={conf} onChange={setConf} placeholder="Repeat password"/>
        <Btn onClick={next}>Continue →</Btn>
      </>}

      {step === 2 && <>
        <h2 style={S.ftitle}>Professional details</h2>
        <p style={S.fsub}>Step 2 of 2 — Your practice info</p>
        <Field label="Medical License No." icon="🪪" value={lic} onChange={setLic} placeholder="LIC123456"/>
        <div style={{ marginBottom:14 }}>
          <label style={{ display:"block", fontSize:11, fontWeight:600, color:"#7a8fad", letterSpacing:.5, textTransform:"uppercase", marginBottom:6 }}>Specialization</label>
          <select value={spec} onChange={e => setSpec(e.target.value)}
            style={{ width:"100%", padding:"11px 13px", background:"rgba(255,255,255,.04)", border:"1px solid rgba(255,255,255,.1)", borderRadius:10, color:"#f0f4ff", fontFamily:"Sora,sans-serif", fontSize:13, outline:"none" }}>
            <option value="" disabled>Select specialization</option>
            {SPECS.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
        <Field label="Hospital / Clinic" icon="🏥" value={hosp} onChange={setHosp} placeholder="Gaborone Private Hospital"/>
        <Field label="Phone Number" icon="📞" type="tel" value={phone} onChange={setPhone} placeholder="0712 345 678"/>
        <div style={{ display:"flex", gap:10, marginTop:5 }}>
          <Btn variant="back" onClick={() => { setStep(1); setAlert({ msg:"", type:"" }); }}>← Back</Btn>
          <Btn onClick={submit} disabled={loading}>{loading ? "Creating account..." : "Create Account"}</Btn>
        </div>
      </>}

      <div style={S.ffoot}>Have an account? <a style={S.link} onClick={() => onSwitch("login")}>Sign in</a></div>
    </div>
  );
}

// ── PATIENT SIGNUP ────────────────────────────────────────────────────────────
function PatientSignup({ onSwitch }) {
  const [step, setStep]     = useState(1);
  const [alert, setAlert]   = useState({ msg:"", type:"" });
  const [loading, setLoad]  = useState(false);
  const [name,   setName]   = useState("");
  const [email,  setEmail]  = useState("");
  const [pass,   setPass]   = useState("");
  const [conf,   setConf]   = useState("");
  const [dob,    setDob]    = useState("");
  const [gender, setGender] = useState("");
  const [phone,  setPhone]  = useState("");
  const [natId,  setNatId]  = useState("");
  const [doctor, setDoctor] = useState("");

  function next() {
    if (!name)           return setAlert({ msg:"Enter your full name", type:"error" });
    if (!vEmail(email))  return setAlert({ msg:"Enter a valid email", type:"error" });
    if (pass.length < 8) return setAlert({ msg:"Password needs 8+ characters", type:"error" });
    if (pass !== conf)   return setAlert({ msg:"Passwords do not match", type:"error" });
    setAlert({ msg:"", type:"" }); setStep(2);
  }

  async function submit() {
    if (!phone)  return setAlert({ msg:"Enter your phone number", type:"error" });
    if (!dob)    return setAlert({ msg:"Enter your date of birth", type:"error" });
    if (!gender) return setAlert({ msg:"Select your gender", type:"error" });
    setLoad(true); setAlert({ msg:"", type:"" });
    try {
      const { ok, data } = await apiPost("/api/auth/signup", {
        full_name:name, email, password:pass,
        phone, dob, gender, national_id:natId, doctor_name:doctor, role:"patient"
      });
      if (!ok) setAlert({ msg: data.error||"Sign up failed", type:"error" });
      else {
        localStorage.setItem("token",   data.token);
        localStorage.setItem("patient", JSON.stringify(data.patient));
        localStorage.setItem("role",    "patient");
        setStep(3);
        setAlert({ msg:"Account created! Opening patient portal...", type:"success" });
        setTimeout(() => window.location.href = "patient-portal.html", 1200);
      }
    } catch {
      setAlert({ msg:"Demo: Opening patient portal...", type:"success" });
      setTimeout(() => window.location.href = "patient-portal.html", 1200);
    }
    setLoad(false);
  }

  const inputStyle = { width:"100%", padding:"11px 13px 11px 40px", background:"rgba(255,255,255,.04)", border:"1px solid rgba(255,255,255,.1)", borderRadius:10, color:"#f0f4ff", fontFamily:"Sora,sans-serif", fontSize:13, outline:"none" };

  return (
    <div>
      <Steps step={step} isDoc={false}/>
      <Alert {...alert}/>

      {step === 1 && <>
        <div style={S.badge}>🧑 Creating a Patient Account</div>
        <h2 style={S.ftitle}>Create your account</h2>
        <p style={S.fsub}>Step 1 of 2 — Login details</p>
        <Field label="Full Name" icon="👤" value={name} onChange={setName} placeholder="John Doe" isPat/>
        <Field label="Email" icon="📧" type="email" value={email} onChange={setEmail} placeholder="yourname@email.com" isPat/>
        <div style={{ marginBottom:14 }}>
          <label style={{ display:"block", fontSize:11, fontWeight:600, color:"#7a8fad", letterSpacing:.5, textTransform:"uppercase", marginBottom:6 }}>Password</label>
          <div style={{ position:"relative" }}>
            <span style={{ position:"absolute", left:12, top:"50%", transform:"translateY(-50%)", fontSize:15, color:"#7a8fad", pointerEvents:"none" }}>🔒</span>
            <input type="password" value={pass} onChange={e => setPass(e.target.value)} placeholder="Min. 8 characters" style={inputStyle}/>
          </div>
          <StrengthBar val={pass}/>
        </div>
        <Field label="Confirm Password" icon="🔒" type="password" value={conf} onChange={setConf} placeholder="Repeat password" isPat/>
        <Btn onClick={next} isPat>Continue →</Btn>
      </>}

      {step === 2 && <>
        <h2 style={S.ftitle}>Your personal details</h2>
        <p style={S.fsub}>Step 2 of 2 — Tell us about yourself</p>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10 }}>
          <Field label="Date of Birth" icon="🎂" type="date" value={dob} onChange={setDob} placeholder="" isPat/>
          <div style={{ marginBottom:14 }}>
            <label style={{ display:"block", fontSize:11, fontWeight:600, color:"#7a8fad", letterSpacing:.5, textTransform:"uppercase", marginBottom:6 }}>Gender</label>
            <select value={gender} onChange={e => setGender(e.target.value)}
              style={{ width:"100%", padding:"11px 13px", background:"rgba(255,255,255,.04)", border:"1px solid rgba(255,255,255,.1)", borderRadius:10, color:"#f0f4ff", fontFamily:"Sora,sans-serif", fontSize:13, outline:"none" }}>
              <option value="" disabled>Select</option>
              <option>Male</option><option>Female</option><option>Other</option>
            </select>
          </div>
        </div>
        <Field label="Phone Number" icon="📞" type="tel" value={phone} onChange={setPhone} placeholder="0712 345 678" isPat/>
        <Field label="National ID" icon="🪪" value={natId} onChange={setNatId} placeholder="123456789" isPat/>
        <Field label="Your Doctor (optional)" icon="👨‍⚕️" value={doctor} onChange={setDoctor} placeholder="Dr. Smith" isPat/>
        <div style={{ display:"flex", gap:10, marginTop:5 }}>
          <Btn variant="back" onClick={() => { setStep(1); setAlert({ msg:"", type:"" }); }}>← Back</Btn>
          <Btn onClick={submit} disabled={loading} isPat>{loading ? "Creating account..." : "Create Account"}</Btn>
        </div>
      </>}

      <div style={S.ffoot}>Have an account? <a style={S.linkPat} onClick={() => onSwitch("login")}>Sign in</a></div>
    </div>
  );
}

// ── SHARED STYLES OBJECT ──────────────────────────────────────────────────────
const S = {
  ftitle:  { fontSize:22, fontWeight:700, letterSpacing:"-.8px", marginBottom:4 },
  fsub:    { fontSize:13, color:"#7a8fad", marginBottom:22 },
  ffoot:   { marginTop:18, textAlign:"center", fontSize:12, color:"#7a8fad" },
  link:    { color:"#00c9a7", textDecoration:"none", fontWeight:600, cursor:"pointer" },
  linkPat: { color:"#a78bfa", textDecoration:"none", fontWeight:600, cursor:"pointer" },
  badge:   { display:"flex", alignItems:"center", gap:8, padding:"9px 13px", borderRadius:9, fontSize:12,
             background:"rgba(124,106,247,.08)", border:"1px solid rgba(124,106,247,.2)", color:"#a78bfa", marginBottom:18 },
};

// ── MAIN COMPONENT ────────────────────────────────────────────────────────────
export default function Auth() {
  const [role, setRoleState] = useState("doctor");
  const [tab,  setTab]       = useState("login");
  const isDoc = role === "doctor";

  function setRole(r) { setRoleState(r); setTab("login"); }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=DM+Mono:wght@400;500&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        html, body, #root { height: 100%; font-family: 'Sora', sans-serif; background: #0a1628; color: #f0f4ff; overflow-x: hidden; }
        @keyframes aglow { 0%,100%{opacity:.2} 50%{opacity:1} }
        @keyframes aup   { from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }
        .aleft::after { content:''; position:absolute; right:-1px; top:15%; bottom:15%; width:2px;
          background:linear-gradient(to bottom,transparent,${isDoc?"#00c9a7":"#7c6af7"},transparent);
          animation:aglow 3s ease-in-out infinite; }
        .afeat:hover { transform:translateX(4px) !important; }
        @media(max-width:900px){ .aleft{ display:none !important; } .aright{ padding:32px 20px !important; } }
      `}</style>

      {/* BG */}
      <div style={{
        position:"fixed", inset:0, zIndex:0, transition:"background .6s",
        background: isDoc
          ? "radial-gradient(ellipse 70% 50% at 15% 20%,rgba(0,201,167,.07) 0%,transparent 60%),radial-gradient(ellipse 60% 50% at 85% 80%,rgba(72,202,228,.06) 0%,transparent 60%),#0a1628"
          : "radial-gradient(ellipse 70% 50% at 15% 20%,rgba(124,106,247,.09) 0%,transparent 60%),radial-gradient(ellipse 60% 50% at 85% 80%,rgba(167,139,250,.06) 0%,transparent 60%),#0a1628"
      }}/>
      <div style={{ position:"fixed", inset:0, zIndex:0,
        backgroundImage:"linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px)",
        backgroundSize:"52px 52px" }}/>

      {/* PAGE */}
      <div style={{ position:"relative", zIndex:1, minHeight:"100vh", display:"grid", gridTemplateColumns:"1fr 1fr" }}>

        {/* ══ LEFT ══ */}
        <div className="aleft" style={{
          display:"flex", flexDirection:"column", justifyContent:"center",
          padding:"56px 60px", borderRight:`1px solid ${isDoc?"rgba(0,201,167,.2)":"rgba(124,106,247,.2)"}`,
          position:"relative", overflow:"hidden", transition:"border-color .4s",
        }}>

          {/* Pills */}
          <div style={{ display:"flex", gap:10, marginBottom:44, animation:"aup .5s ease both" }}>
            {[["doctor","👨‍⚕️ Doctor","#00c9a7","rgba(0,201,167,.1)","rgba(0,201,167,.15)"],
              ["patient","🧑 Patient","#a78bfa","rgba(124,106,247,.1)","rgba(124,106,247,.15)"]
            ].map(([r, label, col, bg, glow]) => (
              <div key={r} onClick={() => setRole(r)} style={{
                display:"flex", alignItems:"center", gap:7, padding:"8px 18px", borderRadius:99,
                border:`1px solid ${role===r ? col : "rgba(255,255,255,.1)"}`,
                background: role===r ? bg : "rgba(255,255,255,.04)",
                fontSize:13, fontWeight:600, color: role===r ? col : "#7a8fad",
                cursor:"pointer", transition:"all .3s",
                boxShadow: role===r ? `0 0 18px ${glow}` : "none",
              }}>{label}</div>
            ))}
          </div>

          {/* Brand */}
          <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:36, animation:"aup .5s .1s ease both" }}>
            <div style={{
              width:44, height:44, borderRadius:12, display:"flex", alignItems:"center", justifyContent:"center", fontSize:22,
              background: isDoc ? "linear-gradient(135deg,#00c9a7,#48cae4)" : "linear-gradient(135deg,#7c6af7,#a78bfa)",
              boxShadow: `0 0 22px ${isDoc?"rgba(0,201,167,.2)":"rgba(124,106,247,.2)"}`, transition:"all .4s",
            }}>🎙️</div>
            <div style={{ fontSize:20, fontWeight:700, letterSpacing:"-.5px" }}>
              Voice<span style={{ color: isDoc ? "#00c9a7" : "#a78bfa", transition:"color .4s" }}>First</span>
            </div>
          </div>

          <div style={{ fontFamily:"DM Mono,monospace", fontSize:11, letterSpacing:3, textTransform:"uppercase",
            marginBottom:14, color: isDoc?"#00c9a7":"#a78bfa", transition:"color .4s", animation:"aup .5s .15s ease both" }}>
            {isDoc ? "Clinical Documentation System" : "Patient Portal"}
          </div>

          <h1 style={{ fontSize:"clamp(28px,3vw,44px)", fontWeight:800, lineHeight:1.1, letterSpacing:"-1.5px", marginBottom:18, animation:"aup .5s .2s ease both" }}>
            Medicine at the<br/>speed of{" "}
            <span style={{ color: isDoc?"#00c9a7":"#a78bfa" }}>{isDoc ? "speech." : "your voice."}</span>
          </h1>

          <p style={{ fontSize:14, color:"#7a8fad", lineHeight:1.7, maxWidth:380, marginBottom:36, animation:"aup .5s .25s ease both" }}>
            {isDoc
              ? "Record consultations, extract patient data automatically, get AI-powered diagnosis suggestions — all from a single conversation. Zero typing required."
              : "Submit your symptoms, record a voice note, and upload documents — all before stepping into the clinic. Your doctor will be fully prepared."}
          </p>

          <div style={{ display:"flex", flexDirection:"column", gap:11, animation:"aup .5s .3s ease both" }}>
            {(isDoc ? DOC_FEATS : PAT_FEATS).map(f => (
              <div className="afeat" key={f.t} style={{
                display:"flex", alignItems:"flex-start", gap:13, padding:"13px 16px", borderRadius:12,
                background:"rgba(255,255,255,.03)",
                border:`1px solid ${isDoc?"rgba(0,201,167,.18)":"rgba(124,106,247,.18)"}`,
                transition:"all .3s", cursor:"default",
              }}>
                <div style={{ fontSize:18, flexShrink:0, marginTop:2 }}>{f.i}</div>
                <div>
                  <strong style={{ display:"block", fontSize:12, fontWeight:600, color:"#f0f4ff", marginBottom:2 }}>{f.t}</strong>
                  <span style={{ fontSize:11, color:"#7a8fad", lineHeight:1.5 }}>{f.d}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ══ RIGHT ══ */}
        <div className="aright" style={{ display:"flex", alignItems:"center", justifyContent:"center", padding:"40px 52px" }}>
          <div style={{ width:"100%", maxWidth:440, animation:"aup .6s .2s ease both" }}>

            {/* Role Cards */}
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, marginBottom:24 }}>
              {[
                { r:"doctor",  icon:"👨‍⚕️", label:"I'm a Doctor",  sub:"Clinician access", col:"#00c9a7", bg:"rgba(0,201,167,.08)", glow:"rgba(0,201,167,.12)" },
                { r:"patient", icon:"🧑‍🤝‍🧑", label:"I'm a Patient", sub:"Patient portal",  col:"#7c6af7", bg:"rgba(124,106,247,.08)", glow:"rgba(124,106,247,.12)" },
              ].map(({ r, icon, label, sub, col, bg, glow }) => (
                <div key={r} onClick={() => setRole(r)} style={{
                  display:"flex", flexDirection:"column", alignItems:"center", gap:7,
                  padding:"16px 10px", borderRadius:14, cursor:"pointer", transition:"all .3s", textAlign:"center",
                  background: role===r ? bg : "rgba(255,255,255,.04)",
                  border:`2px solid ${role===r ? col : "rgba(255,255,255,.08)"}`,
                  boxShadow: role===r ? `0 0 22px ${glow}` : "none",
                }}>
                  <div style={{ fontSize:26 }}>{icon}</div>
                  <div style={{ fontSize:13, fontWeight:700 }}>{label}</div>
                  <div style={{ fontSize:11, color:"#7a8fad" }}>{sub}</div>
                </div>
              ))}
            </div>

            {/* Tabs */}
            <div style={{ display:"flex", background:"rgba(255,255,255,.04)", border:"1px solid rgba(255,255,255,.08)", borderRadius:12, padding:4, marginBottom:24 }}>
              {["login","signup"].map(t => {
                const active = tab === t;
                return (
                  <button key={t} onClick={() => setTab(t)} style={{
                    flex:1, padding:9, border:"none", borderRadius:9,
                    fontFamily:"Sora,sans-serif", fontSize:13, fontWeight: active?700:500,
                    cursor:"pointer", transition:"all .3s",
                    background: !active ? "transparent"
                      : isDoc ? "linear-gradient(135deg,#00c9a7,#48cae4)"
                      : "linear-gradient(135deg,#7c6af7,#a78bfa)",
                    color: !active ? "#7a8fad" : isDoc ? "#0a1628" : "#fff",
                    boxShadow: !active ? "none"
                      : isDoc ? "0 4px 14px rgba(0,201,167,.3)"
                      : "0 4px 14px rgba(124,106,247,.3)",
                  }}>
                    {t === "login" ? "Sign In" : "Create Account"}
                  </button>
                );
              })}
            </div>

            {/* Active Form */}
            {isDoc  && tab==="login"  && <DoctorLogin   onSwitch={setTab}/>}
            {isDoc  && tab==="signup" && <DoctorSignup  onSwitch={setTab}/>}
            {!isDoc && tab==="login"  && <PatientLogin  onSwitch={setTab}/>}
            {!isDoc && tab==="signup" && <PatientSignup onSwitch={setTab}/>}

          </div>
        </div>
      </div>
    </>
  );
}
