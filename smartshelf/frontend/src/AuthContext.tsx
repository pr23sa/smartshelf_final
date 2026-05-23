import { createContext, useContext, useState, ReactNode } from "react";
import { User } from "./types";
import { setStoredToken } from "./api";

interface AuthCtx {
  user: User | null;
  setAuth: (user: User | null, token: string | null) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthCtx>({
  user: null,
  setAuth: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem("smartshelf_user");
    return saved ? JSON.parse(saved) : null;
  });

  const setAuth = (u: User | null, token: string | null) => {
    setUser(u);
    setStoredToken(token);
    if (u) localStorage.setItem("smartshelf_user", JSON.stringify(u));
    else localStorage.removeItem("smartshelf_user");
  };

  const logout = () => setAuth(null, null);

  return (
    <AuthContext.Provider value={{ user, setAuth, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);


