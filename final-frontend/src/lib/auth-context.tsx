import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  authAPI,
  workspacesAPI,
  type AuthUser,
  type WorkspaceResponse,
  type WorkspaceCreate,
} from './api';
import { isAdminRole, PENDING_PASSWORD_RESET_KEY, type AuthStartStatus } from './authFlow';

type AuthContextType = {
  user: AuthUser | null;
  loading: boolean;
  workspaces: WorkspaceResponse[];
  activeWorkspace: WorkspaceResponse | null;
  loadWorkspaces: () => Promise<WorkspaceResponse[]>;
  selectWorkspace: (workspaceId: number) => void;
  createStoreWorkspace: (data: WorkspaceCreate) => Promise<WorkspaceResponse>;
  requestStoreDeleteOtp: (workspaceId: number) => Promise<{ message: string; email: string }>;
  deleteStoreWorkspace: (workspaceId: number, data: { password: string; otp: string }) => Promise<void>;
  startAuth: (email: string, password: string) => Promise<{ status: AuthStartStatus; message: string; email: string }>;
  completeOnboarding: (
    email: string,
    password: string,
    storeName: string,
    storeType: string,
  ) => Promise<{ message: string; email: string }>;
  forgotPassword: (email: string) => Promise<{ message: string; email: string }>;
  verifyOtp: (email: string, code: string) => Promise<{ workspaces: WorkspaceResponse[]; activeWorkspace: WorkspaceResponse | null }>;
  resendOtp: (email: string) => Promise<{ message: string }>;
  refreshUser: () => Promise<void>;
  logout: () => void;
};


const AuthContext = createContext<AuthContextType | undefined>(undefined);

function acceptAdminOrThrow(user: AuthUser): AuthUser {
  if (!isAdminRole(user.role)) {
    localStorage.removeItem('access_token');
    throw new Error('Admin access required');
  }
  return user;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [workspaces, setWorkspaces] = useState<WorkspaceResponse[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<WorkspaceResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const syncWorkspaces = async () => {
    try {
      const res = await workspacesAPI.getSummary();
      const list = res.data.workspaces || [];
      setWorkspaces(list);

      const savedWidStr = localStorage.getItem('active_workspace_id');
      const savedWid = savedWidStr ? parseInt(savedWidStr, 10) : null;
      let matched = list.find((w) => w.id === savedWid);
      if (!matched && res.data.active_workspace) {
        matched = res.data.active_workspace;
      }
      if (!matched && list.length > 0) {
        matched = list[0];
      }
      if (matched) {
        localStorage.setItem('active_workspace_id', String(matched.id));
        setActiveWorkspace(matched);
      }
      return list;
    } catch {
      setWorkspaces([]);
      setActiveWorkspace(null);
      return [];
    }
  };

  useEffect(() => {
    let cancelled = false;
    const token = localStorage.getItem('access_token');
    if (token) {
      authAPI.getMe()
        .then(async (res) => {
          if (cancelled) return;
          try {
            setUser(acceptAdminOrThrow(res.data));
            await syncWorkspaces();
          } catch {
            setUser(null);
          }
        })
        .catch(() => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('active_workspace_id');
          if (!cancelled) setUser(null);
        })
        .finally(() => { if (!cancelled) setLoading(false); });
    } else {
      setLoading(false);
    }
    return () => { cancelled = true; };
  }, []);

  const selectWorkspace = (workspaceId: number) => {
    localStorage.setItem('active_workspace_id', String(workspaceId));
    const target = workspaces.find((w) => w.id === workspaceId) || null;
    setActiveWorkspace(target);
  };

  const createStoreWorkspace = async (data: WorkspaceCreate) => {
    const res = await workspacesAPI.create(data);
    const newWs = res.data;
    setWorkspaces((prev) => [...prev, newWs]);
    selectWorkspace(newWs.id);
    return newWs;
  };

  const requestStoreDeleteOtp = async (workspaceId: number) => {
    const res = await workspacesAPI.requestDeleteOtp(workspaceId);
    return res.data;
  };

  const deleteStoreWorkspace = async (workspaceId: number, data: { password: string; otp: string }) => {
    await workspacesAPI.delete(workspaceId, data);
    setWorkspaces((prev) => {
      const remaining = prev.filter((w) => w.id !== workspaceId);
      if (activeWorkspace?.id === workspaceId) {
        if (remaining.length > 0) {
          selectWorkspace(remaining[0].id);
        } else {
          localStorage.removeItem('active_workspace_id');
          setActiveWorkspace(null);
        }
      }
      return remaining;
    });
  };


  const loadWorkspaces = async () => {
    return await syncWorkspaces();
  };

  const startAuth = async (email: string, password: string) => {
    const { data } = await authAPI.start(email.trim(), password);
    return { status: data.status, message: data.message, email: data.email };
  };

  const completeOnboarding = async (
    email: string,
    password: string,
    storeName: string,
    storeType: string,
  ) => {
    const { data } = await authAPI.onboard(
      email.trim(),
      password,
      storeName.trim(),
      storeType.trim(),
    );
    return { message: data.message, email: data.email };
  };

  const forgotPassword = async (email: string) => {
    const { data } = await authAPI.forgotPassword(email.trim());
    return { message: data.message, email: data.email };
  };

  const verifyOtp = async (email: string, code: string) => {
    const { data } = await authAPI.verifyOtp(email.trim(), code.trim());
    if (!data.access_token) {
      throw new Error('OTP verification failed');
    }
    localStorage.setItem('access_token', data.access_token);
    const me = await authAPI.getMe();
    setUser(acceptAdminOrThrow(me.data));
    const list = await syncWorkspaces();
    return {
      workspaces: list,
      activeWorkspace: list.length > 0 ? list[0] : null,
    };
  };

  const resendOtp = async (email: string) => {
    const { data } = await authAPI.resendOtp(email.trim());
    return { message: data.message };
  };

  const refreshUser = async () => {
    const me = await authAPI.getMe();
    setUser(acceptAdminOrThrow(me.data));
    await syncWorkspaces();
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('active_workspace_id');
    sessionStorage.removeItem(PENDING_PASSWORD_RESET_KEY);
    setUser(null);
    setWorkspaces([]);
    setActiveWorkspace(null);
    window.location.href = '/';
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        workspaces,
        activeWorkspace,
        loadWorkspaces,
        selectWorkspace,
        createStoreWorkspace,
        requestStoreDeleteOtp,
        deleteStoreWorkspace,
        startAuth,
        completeOnboarding,
        forgotPassword,
        verifyOtp,
        resendOtp,
        refreshUser,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (ctx === undefined) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
