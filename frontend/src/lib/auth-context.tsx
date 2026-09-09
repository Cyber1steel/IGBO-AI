"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import {
  AuthUser,
  LearnerProfile,
  getMyProfile,
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
  refreshSession,
} from "@/lib/api";

interface AuthContextValue {
  user: AuthUser | null;
  profile: LearnerProfile | null;
  accessToken: string | null;
  loading: boolean; // true only during the initial silent-refresh check
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [profile, setProfile] = useState<LearnerProfile | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadProfile = useCallback(async (token: string) => {
    try {
      setProfile(await getMyProfile(token));
    } catch {
      // Non-fatal — dashboard/profile pages show their own loading/error state.
    }
  }, []);

  // On first load, try to silently exchange the httpOnly refresh cookie for
  // a session. This is what makes "stay logged in across a page refresh"
  // work without ever putting a refresh token in JS-accessible storage.
  useEffect(() => {
    (async () => {
      const session = await refreshSession();
      if (session) {
        setUser(session.user);
        setAccessToken(session.access_token);
        await loadProfile(session.access_token);
      }
      setLoading(false);
    })();
  }, [loadProfile]);

  async function login(email: string, password: string) {
    const session = await apiLogin(email, password);
    setUser(session.user);
    setAccessToken(session.access_token);
    await loadProfile(session.access_token);
  }

  async function register(email: string, password: string, displayName: string) {
    const session = await apiRegister(email, password, displayName);
    setUser(session.user);
    setAccessToken(session.access_token);
    await loadProfile(session.access_token);
  }

  async function logout() {
    await apiLogout().catch(() => {});
    setUser(null);
    setAccessToken(null);
    setProfile(null);
  }

  async function refreshProfile() {
    if (accessToken) await loadProfile(accessToken);
  }

  return (
    <AuthContext.Provider
      value={{ user, profile, accessToken, loading, login, register, logout, refreshProfile }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside an AuthProvider");
  return ctx;
}
