import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  authAPI,
  workspacesAPI,
  type AuthUser,
  type WorkspaceResponse,
  type WorkspaceCreate,
} from './api';
import { isAdminRole, type AuthStartStatus } from './authFlow';

type AuthContextType = {
  user: AuthUser | null;
  loading: boolean;
  workspaces: WorkspaceResponse[];
  activeWorkspace: WorkspaceResponse | null;
  loadWorkspaces: () => Promise<WorkspaceResponse[]>;
  selectWorkspace: (workspaceId: number) => void;
  createStoreWorkspace: (data: WorkspaceCreate) => Promise<WorkspaceResponse>;
  deleteStoreWorkspace: (workspaceId: number, data: { password: string }) => Promise<void>;
  /** Step 1 of login. Returns status 'needs_onboarding' or calls onLoginSuccess when authenticated. */
  startAuth: (
    email: string,
    password: string,
    onLoginSuccess: () => void,
  ) => Promise<{ status: AuthStartStatus; message: string; email: string }>;
  /** Complete signup for new users. Issues JWT and calls onLoginSuccess. */
  completeOnboarding: (
    email: string,
    password: string,
    storeName: string,
    storeType: string,
    onLoginSuccess: () => void,
  ) => Promise<{ message: string; email: string }>;
  /** Forgot-password: reset password directly. Issues JWT and calls onLoginSuccess. */
  resetPassword: (
    email: string,
    newPassword: string,
    onLoginSuccess: () => void,
  ) => Promise<{ message: string }>;
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

async function _applyToken(
  token: string,
  setUser: (u: AuthUser) => void,
  syncWorkspaces: () => Promise<WorkspaceResponse[]>,
  onLoginSuccess: () => void,
): Promise<WorkspaceResponse[]> {
  localStorage.setItem('access_token', token);
  const me = await authAPI.getMe();
  setUser(acceptAdminOrThrow(me.data));
  const list = await syncWorkspaces();
  if (list.length <= 1) {
    onLoginSuccess();
  }
  return list;
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

  const deleteStoreWorkspace = async (workspaceId: number, data: { password: string }) => {
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

  const startAuth = async (
    email: string,
    password: string,
    onLoginSuccess: () => void,
  ) => {
    const { data } = await authAPI.start(email.trim(), password);
    if (data.status === 'authenticated' && data.access_token) {
      const list = await _applyToken(data.access_token, setUser, syncWorkspaces, onLoginSuccess);
      // If multi-store: caller will show store_select step (return status so LoginPage knows)
      return { status: data.status as AuthStartStatus, message: data.message, email: data.email, workspaces: list };
    }
    return { status: data.status as AuthStartStatus, message: data.message, email: data.email };
  };

  const completeOnboarding = async (
    email: string,
    password: string,
    storeName: string,
    storeType: string,
    onLoginSuccess: () => void,
  ) => {
    const { data } = await authAPI.onboard(email.trim(), password, storeName.trim(), storeType.trim());
    if (data.access_token) {
      await _applyToken(data.access_token, setUser, syncWorkspaces, onLoginSuccess);
    }
    return { message: data.message, email: data.email };
  };

  const resetPassword = async (
    email: string,
    newPassword: string,
    onLoginSuccess: () => void,
  ) => {
    const { data } = await authAPI.resetPassword(email.trim(), newPassword);
    if (data.access_token) {
      await _applyToken(data.access_token, setUser, syncWorkspaces, onLoginSuccess);
    }
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
        deleteStoreWorkspace,
        startAuth,
        completeOnboarding,
        resetPassword,
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
