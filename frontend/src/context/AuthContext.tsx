import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { getMe, login as apiLogin, register as apiRegister, CurrentUser } from "../api/client";

interface AuthCtx {
  user: CurrentUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const Ctx = createContext<AuthCtx>(null as unknown as AuthCtx);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { setLoading(false); return; }
    getMe().then((r) => setUser(r.data)).catch(() => localStorage.removeItem("token")).finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const r = await apiLogin(email, password);
    localStorage.setItem("token", r.data.access_token);
    setUser((await getMe()).data);
  };
  const register = async (email: string, password: string) => {
    const r = await apiRegister(email, password);
    localStorage.setItem("token", r.data.access_token);
    setUser((await getMe()).data);
  };
  const logout = () => { localStorage.removeItem("token"); setUser(null); };

  return <Ctx.Provider value={{ user, loading, login, register, logout }}>{children}</Ctx.Provider>;
}
