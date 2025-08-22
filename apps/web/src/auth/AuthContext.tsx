import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

export interface User { id: string; name: string; role: 'learner' | 'instructor'; token: string }
interface AuthContextValue {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  switchRole: (role: User['role']) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function mockIssueToken(username: string, role: User['role']): string {
  // simple base64 simulation (NOT secure) for dev
  return btoa(JSON.stringify({ sub: username, role, iat: Date.now() / 1000 }));
}

// Lightweight decode (dev only; no signature validation)
export function decodeMockToken(token: string): { sub?: string; role?: User['role'] } | null {
  try { return JSON.parse(atob(token)); } catch { return null; }
}

export const AuthProvider: React.FC<React.PropsWithChildren<{}>> = ({ children }) => {
  const [user, setUser] = useState<User | null>(()=>{
    try { const raw = typeof window !== 'undefined' ? localStorage.getItem('auth:user') : null; return raw ? JSON.parse(raw) : null; } catch { return null; }
  });
  useEffect(()=>{
    if(user) localStorage.setItem('auth:user', JSON.stringify(user)); else localStorage.removeItem('auth:user');
  },[user]);

  const login = useCallback(async (username: string, password: string) => {
    const res = await fetch('/api/auth/login', { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify({ username, password }) });
    if(!res.ok) throw new Error('Login failed');
    const data = await res.json();
    // Dev still stores mock token for client side; cookie holds real JWT
    const token = mockIssueToken(username, data.role);
    setUser({ id: username, name: username, role: data.role, token });
  },[]);

  const logout = useCallback(()=> setUser(null), []);
  const switchRole = useCallback((role: User['role']) => {
    setUser(u => u ? { ...u, role, token: mockIssueToken(u.id, role) } : u);
  },[]);

  return <AuthContext.Provider value={{ user, login, logout, switchRole }}>{children}</AuthContext.Provider>;
};

export function useAuth(){
  const ctx = useContext(AuthContext);
  if(!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
