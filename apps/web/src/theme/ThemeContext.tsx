import React, { createContext, useContext, useEffect, useState } from 'react';

export type Theme = 'dark' | 'light';
interface ThemeCtx { theme: Theme; toggle: ()=>void; }
const Ctx = createContext<ThemeCtx>({ theme: 'dark', toggle: ()=>{} });

export const ThemeProvider: React.FC<React.PropsWithChildren<{}>> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>('dark');
  useEffect(()=>{
    const stored = typeof window !== 'undefined' ? localStorage.getItem('theme') as Theme | null : null;
    if(stored) setTheme(stored);
  },[]);
  useEffect(()=>{
    if(typeof document !== 'undefined'){
      document.documentElement.dataset.theme = theme;
      localStorage.setItem('theme', theme);
    }
  }, [theme]);
  const toggle = () => setTheme(t => t === 'dark' ? 'light' : 'dark');
  return <Ctx.Provider value={{ theme, toggle }}>{children}</Ctx.Provider>;
};

export const useTheme = () => useContext(Ctx);
