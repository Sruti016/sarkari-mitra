import { useState, useEffect } from "react";
import { auth } from "../firebase";
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithRedirect,
  getRedirectResult,
  sendEmailVerification,
  signOut
} from "firebase/auth";

export default function AuthPage({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [emailSent, setEmailSent] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getRedirectResult(auth).then((result) => {
      if (result?.user) onLogin();
    }).catch((err) => {
      setError(err.message);
    });
  }, []);

  const handleSubmit = async () => {
    setError("");
    setLoading(true);
    try {
      if (isLogin) {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        if (!userCredential.user.emailVerified) {
          await signOut(auth);
          setError("❌ Pehle apni email verify karo. Inbox check karo.");
          setLoading(false);
          return;
        }
        onLogin();
      } else {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        await sendEmailVerification(userCredential.user);
        await signOut(auth);
        setEmailSent(true);
        return;
      }
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const handleGoogle = async () => {
    try {
      const provider = new GoogleAuthProvider();
      await signInWithRedirect(auth, provider);
    } catch (err) {
      setError(err.message);
    }
  };

  if (emailSent) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f0faf0" }}>
        <div style={{ background: "white", borderRadius: "16px", padding: "40px", textAlign: "center", maxWidth: "420px", boxShadow: "0 4px 20px rgba(0,0,0,0.1)" }}>
          <div style={{ fontSize: "60px", marginBottom: "16px" }}>📧</div>
          <h2 style={{ color: "#1e7e34", marginBottom: "12px" }}>Email Verify Karein!</h2>
          <p style={{ color: "#555", marginBottom: "8px" }}>Aapke email pe verification link bheja gaya hai.</p>
          <p style={{ color: "#555", marginBottom: "24px" }}><b>Spam/Junk folder</b> zaroor check karein.</p>
          <button
            onClick={() => { setEmailSent(false); setIsLogin(true); }}
            style={{ background: "#34a853", color: "white", border: "none", borderRadius: "8px", padding: "12px 32px", fontSize: "16px", cursor: "pointer", width: "100%" }}
          >
            Login karo
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-green-50">
      <div className="bg-white p-8 rounded-2xl shadow-lg w-full max-w-md">
        <div className="text-center mb-6">
          <div className="text-4xl mb-2">🏛️</div>
          <h1 className="text-2xl font-bold text-green-800">सरकारी मित्र</h1>
          <p className="text-gray-500 text-sm">Sarkari Schemes Assistant</p>
        </div>
        <div className="flex bg-gray-100 rounded-lg p-1 mb-6">
          <button
            onClick={() => setIsLogin(true)}
            className={`flex-1 py-2 rounded-lg text-sm font-medium transition ${isLogin ? "bg-green-600 text-white" : "text-gray-500"}`}
          >
            Login
          </button>
          <button
            onClick={() => setIsLogin(false)}
            className={`flex-1 py-2 rounded-lg text-sm font-medium transition ${!isLogin ? "bg-green-600 text-white" : "text-gray-500"}`}
          >
            Register
          </button>
        </div>
        {!isLogin && (
          <input
            type="text"
            placeholder="Aapka naam"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-4 py-3 mb-3 text-sm focus:outline-none focus:border-green-500"
          />
        )}
        <input
          type="email"
          placeholder="Email address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-4 py-3 mb-3 text-sm focus:outline-none focus:border-green-500"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-4 py-3 mb-4 text-sm focus:outline-none focus:border-green-500"
        />
        {error && <p className="text-red-500 text-xs mb-3">{error}</p>}
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full bg-green-600 text-white py-3 rounded-lg font-medium hover:bg-green-700 transition mb-3"
        >
          {loading ? "Loading..." : isLogin ? "Login" : "Register"}
        </button>
        <div className="flex items-center mb-3">
          <div className="flex-1 border-t border-gray-200"></div>
          <span className="px-3 text-gray-400 text-xs">ya</span>
          <div className="flex-1 border-t border-gray-200"></div>
        </div>
        <button
          onClick={handleGoogle}
          className="w-full border border-gray-300 text-gray-700 py-3 rounded-lg font-medium hover:bg-gray-50 transition flex items-center justify-center gap-2"
        >
          <img src="https://www.google.com/favicon.ico" className="w-4 h-4" />
          Google se Login karo
        </button>
      </div>
    </div>
  );
}