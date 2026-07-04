import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try { await register(email, password); nav("/"); }
    catch (err: any) { setError(err.response?.data?.detail || "Registration failed"); }
  };

  return (
    <div className="max-w-sm mx-auto mt-16 bg-white border rounded-xl p-6 shadow-sm">
      <h2 className="text-xl font-semibold mb-4">Create account</h2>
      <form onSubmit={submit} className="space-y-3">
        <input className="w-full border rounded px-3 py-2" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className="w-full border rounded px-3 py-2" type="password" placeholder="Password (min 8 chars)" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="w-full bg-blue-600 text-white rounded py-2">Register</button>
      </form>
      <p className="text-sm text-gray-500 mt-3">Have an account? <Link className="text-blue-600" to="/login">Log in</Link></p>
    </div>
  );
}
