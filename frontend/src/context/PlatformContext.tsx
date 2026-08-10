import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
  PrimaryTab,
  PlatformSubTab,
  MonitoringSubTab,
  SecuritySubTab,
  SettingsSection,
  Tenant,
  PlatformAdmin,
  ActiveSession,
  FeatureFlag,
  PlatformSettings,
  ServiceHealthItem,
  EdgeDeviceHealth,
  CameraHealth,
  GateHealth,
  OperationalIncident,
  SecurityAlert,
  LoginActivityEvent,
  ApiCredential,
  AuditLogItem,
  TenantStatus,
  IncidentStatus,
  AlertStatus
} from '../types/platform';
import {
  INITIAL_TENANTS,
  INITIAL_PLATFORM_ADMINS,
  INITIAL_SESSIONS,
  INITIAL_FEATURE_FLAGS,
  INITIAL_SETTINGS,
  INITIAL_SERVICES,
  INITIAL_EDGE_DEVICES,
  INITIAL_CAMERAS,
  INITIAL_GATES,
  INITIAL_INCIDENTS,
  INITIAL_SECURITY_ALERTS,
  INITIAL_LOGIN_EVENTS,
  INITIAL_CREDENTIALS,
  INITIAL_AUDIT_LOGS
} from '../data/mockData';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  description?: string;
}

interface PlatformContextType {
  // Authentication State
  isAuthenticated: boolean;
  currentUser: {
    id: string;
    name: string;
    email: string;
    role: string;
    mfaEnabled: boolean;
  };
  login: (email: string, pass: string, otp?: string) => { requiresMfa: boolean; success: boolean };
  logout: () => void;

  // Theme State
  theme: 'dark' | 'light';
  toggleTheme: () => void;

  // MFA Flow State
  isMfaModalOpen: boolean;
  mfaModalMode: 'enroll' | 'challenge' | 'reset_admin';
  mfaTargetAdminName?: string;
  isMfaVerified: boolean;
  openMfaModal: (mode?: 'enroll' | 'challenge' | 'reset_admin', targetAdminName?: string) => void;
  closeMfaModal: () => void;

  // Navigation State
  primaryTab: PrimaryTab;
  setPrimaryTab: (tab: PrimaryTab) => void;
  platformSubTab: PlatformSubTab;
  setPlatformSubTab: (subTab: PlatformSubTab) => void;
  monitoringSubTab: MonitoringSubTab;
  setMonitoringSubTab: (subTab: MonitoringSubTab) => void;
  securitySubTab: SecuritySubTab;
  setSecuritySubTab: (subTab: SecuritySubTab) => void;
  settingsSection: SettingsSection;
  setSettingsSection: (section: SettingsSection) => void;

  // Selected Detail Drilldown States
  selectedTenantId: string | null;
  setSelectedTenantId: (id: string | null) => void;
  selectedAdminId: string | null;
  setSelectedAdminId: (id: string | null) => void;

  // Real-time Simulation Control
  isLiveSimulationActive: boolean;
  setIsLiveSimulationActive: (active: boolean) => void;
  lastUpdatedTime: string;

  // Data Collections
  tenants: Tenant[];
  admins: PlatformAdmin[];
  sessions: ActiveSession[];
  featureFlags: FeatureFlag[];
  settings: PlatformSettings;
  services: ServiceHealthItem[];
  edgeDevices: EdgeDeviceHealth[];
  cameras: CameraHealth[];
  gates: GateHealth[];
  incidents: OperationalIncident[];
  securityAlerts: SecurityAlert[];
  loginEvents: LoginActivityEvent[];
  credentials: ApiCredential[];
  auditLogs: AuditLogItem[];

  // Toasts
  toasts: ToastMessage[];
  addToast: (toast: Omit<ToastMessage, 'id'>) => void;
  removeToast: (id: string) => void;

  // Handlers - Tenant
  createTenant: (tenantData: Partial<Tenant>, adminData: any) => void;
  updateTenant: (id: string, updateData: Partial<Tenant>) => void;
  setTenantStatus: (id: string, status: TenantStatus, reason?: string) => void;

  // Handlers - Admin
  createAdmin: (adminData: Partial<PlatformAdmin>) => void;
  updateAdmin: (id: string, updateData: Partial<PlatformAdmin>) => void;
  disableAdmin: (id: string, reason?: string) => void;
  resetAdminMfa: (id: string) => void;

  // Handlers - Feature Flags & Settings
  toggleFeatureFlag: (id: string) => void;
  updateSettings: (section: SettingsSection, newSettings: any) => void;

  // Handlers - Monitoring & Incidents
  acknowledgeIncident: (id: string, assignedTo?: string) => void;
  resolveIncident: (id: string, note?: string) => void;

  // Handlers - Security & Sessions
  pushAuditLog: (
    category: AuditLogItem['category'],
    action: string,
    resourceType: string,
    resourceId: string,
    resourceName?: string,
    tenantName?: string,
    changes?: { field: string; before: any; after: any }[]
  ) => void;
  acknowledgeAlert: (id: string) => void;
  resolveAlert: (id: string) => void;
  revokeSession: (id: string) => void;
  revokeAllUserSessions: (userId: string) => void;
  rotateCredential: (id: string) => void;
  revokeCredential: (id: string) => void;

  // Quick Action Navigator
  navigateTo: (tab: PrimaryTab, subTab?: string, detailId?: string) => void;
}

const PlatformContext = createContext<PlatformContextType | undefined>(undefined);

export const PlatformProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Auth State
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);
  const [currentUser, setCurrentUser] = useState({
    id: 'adm-001',
    name: 'Anthony Nguyen',
    email: 'anh.nh@kyanon.digital',
    role: 'Platform Owner',
    mfaEnabled: true,
  });

  const login = (emailInput: string, passInput: string, otpCode?: string) => {
    setIsAuthenticated(true);
    setCurrentUser((prev) => ({
      ...prev,
      email: emailInput,
      name: emailInput.split('@')[0].replace('.', ' ').toUpperCase(),
      mfaEnabled: !!otpCode
    }));
    return { requiresMfa: false, success: true };
  };

  const logout = () => {
    setIsAuthenticated(false);
  };

  // Theme State
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const saved = localStorage.getItem('theme');
    return (saved === 'light' || saved === 'dark') ? saved : 'dark';
  });

  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.classList.add('light');
      document.body.classList.add('light');
    } else {
      document.documentElement.classList.remove('light');
      document.body.classList.remove('light');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  // MFA Flow State
  const [isMfaModalOpen, setIsMfaModalOpen] = useState<boolean>(false);
  const [mfaModalMode, setMfaModalMode] = useState<'enroll' | 'challenge' | 'reset_admin'>('enroll');
  const [mfaTargetAdminName, setMfaTargetAdminName] = useState<string | undefined>(undefined);
  const [isMfaVerified, setIsMfaVerified] = useState<boolean>(true);

  const openMfaModal = (mode: 'enroll' | 'challenge' | 'reset_admin' = 'enroll', targetAdminName?: string) => {
    setMfaModalMode(mode);
    setMfaTargetAdminName(targetAdminName);
    setIsMfaModalOpen(true);
  };

  const closeMfaModal = () => {
    setIsMfaModalOpen(false);
  };

  // Navigation State
  const [primaryTab, setPrimaryTab] = useState<PrimaryTab>('dashboard');
  const [platformSubTab, setPlatformSubTab] = useState<PlatformSubTab>('settings');
  const [monitoringSubTab, setMonitoringSubTab] = useState<MonitoringSubTab>('overview');
  const [securitySubTab, setSecuritySubTab] = useState<SecuritySubTab>('overview');
  const [settingsSection, setSettingsSection] = useState<SettingsSection>('general');

  // Drilldown States
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const [selectedAdminId, setSelectedAdminId] = useState<string | null>(null);

  // Live Ticker State
  const [isLiveSimulationActive, setIsLiveSimulationActive] = useState<boolean>(true);
  const [lastUpdatedTime, setLastUpdatedTime] = useState<string>(new Date().toLocaleTimeString());

  // Collections
  const [tenants, setTenants] = useState<Tenant[]>(INITIAL_TENANTS);
  const [admins, setAdmins] = useState<PlatformAdmin[]>(INITIAL_PLATFORM_ADMINS);
  const [sessions, setSessions] = useState<ActiveSession[]>(INITIAL_SESSIONS);
  const [featureFlags, setFeatureFlags] = useState<FeatureFlag[]>(INITIAL_FEATURE_FLAGS);
  const [settings, setSettings] = useState<PlatformSettings>(INITIAL_SETTINGS);
  const [services, setServices] = useState<ServiceHealthItem[]>(INITIAL_SERVICES);
  const [edgeDevices, setEdgeDevices] = useState<EdgeDeviceHealth[]>(INITIAL_EDGE_DEVICES);
  const [cameras, setCameras] = useState<CameraHealth[]>(INITIAL_CAMERAS);
  const [gates, setGates] = useState<GateHealth[]>(INITIAL_GATES);
  const [incidents, setIncidents] = useState<OperationalIncident[]>(INITIAL_INCIDENTS);
  const [securityAlerts, setSecurityAlerts] = useState<SecurityAlert[]>(INITIAL_SECURITY_ALERTS);
  const [loginEvents, setLoginEvents] = useState<LoginActivityEvent[]>(INITIAL_LOGIN_EVENTS);
  const [credentials, setCredentials] = useState<ApiCredential[]>(INITIAL_CREDENTIALS);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>(INITIAL_AUDIT_LOGS);

  // Toast System
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = (toast: Omit<ToastMessage, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`;
    setToasts((prev) => [...prev, { ...toast, id }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Helper helper to push audit log
  const pushAuditLog = (
    category: AuditLogItem['category'],
    action: string,
    resourceType: string,
    resourceId: string,
    resourceName?: string,
    tenantName?: string,
    changes?: { field: string; before: any; after: any }[]
  ) => {
    const newLog: AuditLogItem = {
      id: `aud-${Date.now()}`,
      timestamp: new Date().toISOString(),
      category,
      action,
      actorName: 'Anthony Nguyen',
      actorEmail: 'anh.nh@kyanon.digital',
      actorType: 'PLATFORM_ADMIN',
      tenantName,
      resourceType,
      resourceId,
      resourceName,
      result: 'SUCCESS',
      source: 'WEB',
      ipAddress: '118.69.182.201',
      requestId: `req-${Math.random().toString(36).substring(2, 10)}`,
      traceId: `trace-${Math.random().toString(36).substring(2, 10)}`,
      changes
    };
    setAuditLogs((prev) => [newLog, ...prev]);
  };

  // Navigation Helper
  const navigateTo = (tab: PrimaryTab, subTab?: string, detailId?: string) => {
    setPrimaryTab(tab);
    if (tab === 'platform' && subTab) setPlatformSubTab(subTab as PlatformSubTab);
    if (tab === 'monitoring' && subTab) setMonitoringSubTab(subTab as MonitoringSubTab);
    if (tab === 'security' && subTab) setSecuritySubTab(subTab as SecuritySubTab);
    if (tab === 'tenants') setSelectedTenantId(detailId || null);
    if (tab === 'platform' && subTab === 'admins') setSelectedAdminId(detailId || null);
  };

  // ===============================================
  // REAL-TIME SIMULATION TICKER
  // ===============================================
  useEffect(() => {
    if (!isLiveSimulationActive) return;

    const interval = setInterval(() => {
      setLastUpdatedTime(new Date().toLocaleTimeString());

      // 1. Randomly fluctuate service ping ms
      setServices((prev) =>
        prev.map((s) => ({
          ...s,
          responseTimeMs: Math.max(2, s.responseTimeMs + Math.floor(Math.random() * 7) - 3)
        }))
      );

      // 2. Increment active tenant event statistics slightly
      setTenants((prev) =>
        prev.map((t) => {
          if (t.status === 'ACTIVE') {
            return {
              ...t,
              statistics: {
                ...t.statistics,
                eventsCount: t.statistics.eventsCount + Math.floor(Math.random() * 15)
              },
              lastActivityAt: new Date().toISOString()
            };
          }
          return t;
        })
      );

      // 3. Fluctuate Edge CPUs
      setEdgeDevices((prev) =>
        prev.map((e) => {
          if (e.status === 'ONLINE') {
            const cpuDelta = Math.floor(Math.random() * 5) - 2;
            return {
              ...e,
              cpuPercent: Math.min(98, Math.max(15, e.cpuPercent + cpuDelta))
            };
          }
          return e;
        })
      );
    }, 4000);

    return () => clearInterval(interval);
  }, [isLiveSimulationActive]);

  // ===============================================
  // TENANT HANDLERS
  // ===============================================
  const createTenant = (tenantData: Partial<Tenant>, adminData: any) => {
    const newId = `t-00${tenants.length + 1}`;
    const newTenant: Tenant = {
      id: newId,
      name: tenantData.name || 'New Organization',
      code: (tenantData.code || 'NEW-TENANT').toUpperCase(),
      email: tenantData.email || 'contact@newtenant.com',
      phone: tenantData.phone || '+84 28 0000 0000',
      timezone: tenantData.timezone || 'Asia/Ho_Chi_Minh',
      status: 'ACTIVE',
      administrator: {
        id: `u-${newId}-admin`,
        name: adminData.name || 'Tenant Administrator',
        email: adminData.email || 'admin@newtenant.com',
        phone: adminData.phone
      },
      statistics: {
        usersCount: 1,
        vehiclesCount: 0,
        camerasCount: 0,
        gatesCount: 0,
        edgeDevicesCount: 0,
        eventsCount: 0,
        storageUsedGb: 0.1
      },
      createdAt: new Date().toISOString(),
      lastActivityAt: new Date().toISOString()
    };

    setTenants((prev) => [newTenant, ...prev]);
    pushAuditLog(
      'TENANT_MANAGEMENT',
      'TENANT_CREATED',
      'TENANT',
      newTenant.id,
      newTenant.name,
      newTenant.name
    );

    addToast({
      type: 'success',
      title: 'Tenant Created',
      description: `Organization ${newTenant.name} (${newTenant.code}) has been provisioned successfully.`
    });
  };

  const updateTenant = (id: string, updateData: Partial<Tenant>) => {
    setTenants((prev) =>
      prev.map((t) => (t.id === id ? { ...t, ...updateData } : t))
    );
    const target = tenants.find((t) => t.id === id);
    pushAuditLog(
      'TENANT_MANAGEMENT',
      'TENANT_UPDATED',
      'TENANT',
      id,
      target?.name,
      target?.name
    );

    addToast({
      type: 'success',
      title: 'Tenant Details Updated',
      description: `Updated configuration for ${target?.name || id}.`
    });
  };

  const setTenantStatus = (id: string, status: TenantStatus, reason?: string) => {
    setTenants((prev) =>
      prev.map((t) => (t.id === id ? { ...t, status } : t))
    );
    const target = tenants.find((t) => t.id === id);
    pushAuditLog(
      'TENANT_MANAGEMENT',
      `TENANT_STATUS_${status}`,
      'TENANT',
      id,
      target?.name,
      target?.name,
      [{ field: 'status', before: target?.status, after: status }]
    );

    addToast({
      type: status === 'ACTIVE' ? 'success' : 'warning',
      title: `Tenant Lifecycle: ${status}`,
      description: `${target?.name || id} status changed to ${status}.${reason ? ` Reason: ${reason}` : ''}`
    });
  };

  // ===============================================
  // ADMIN HANDLERS
  // ===============================================
  const createAdmin = (adminData: Partial<PlatformAdmin>) => {
    const newAdmin: PlatformAdmin = {
      id: `pa-00${admins.length + 1}`,
      name: adminData.name || 'Platform Admin',
      email: adminData.email || 'admin@platform.internal',
      role: adminData.role || 'PLATFORM_ADMIN',
      status: 'ACTIVE',
      mfaEnabled: true,
      mfaConfiguredAt: new Date().toISOString(),
      lastLoginAt: 'Never',
      createdAt: new Date().toISOString(),
      failedLoginAttempts: 0
    };

    setAdmins((prev) => [newAdmin, ...prev]);
    pushAuditLog('PLATFORM_ADMIN', 'ADMIN_ACCOUNT_CREATED', 'ADMIN', newAdmin.id, newAdmin.name);

    addToast({
      type: 'success',
      title: 'Administrator Account Created',
      description: `Created platform admin account for ${newAdmin.email}.`
    });
  };

  const updateAdmin = (id: string, updateData: Partial<PlatformAdmin>) => {
    setAdmins((prev) => prev.map((a) => (a.id === id ? { ...a, ...updateData } : a)));
    pushAuditLog('PLATFORM_ADMIN', 'ADMIN_ACCOUNT_UPDATED', 'ADMIN', id);
    addToast({
      type: 'success',
      title: 'Administrator Profile Updated',
      description: `Saved changes for administrator ${id}.`
    });
  };

  const disableAdmin = (id: string, reason?: string) => {
    // Safety check: Cannot disable last active Platform Admin
    const activeAdmins = admins.filter((a) => a.status === 'ACTIVE' && a.role === 'PLATFORM_ADMIN');
    if (activeAdmins.length <= 1 && activeAdmins.some((a) => a.id === id)) {
      addToast({
        type: 'error',
        title: 'Operation Rejected',
        description: 'Cannot disable the last remaining active Platform Administrator account.'
      });
      return;
    }

    setAdmins((prev) => prev.map((a) => (a.id === id ? { ...a, status: 'DISABLED' } : a)));
    const target = admins.find((a) => a.id === id);
    pushAuditLog('PLATFORM_ADMIN', 'ADMIN_ACCOUNT_DISABLED', 'ADMIN', id, target?.name);

    // Also revoke active sessions for this admin
    setSessions((prev) => prev.filter((s) => s.userId !== id));

    addToast({
      type: 'warning',
      title: 'Administrator Disabled',
      description: `${target?.name || id} disabled and active sessions revoked.`
    });
  };

  const resetAdminMfa = (id: string) => {
    setAdmins((prev) => prev.map((a) => (a.id === id ? { ...a, mfaEnabled: false } : a)));
    const target = admins.find((a) => a.id === id);
    pushAuditLog('SECURITY', 'MFA_RESET_PERFORMED', 'ADMIN', id, target?.name);

    addToast({
      type: 'info',
      title: 'MFA Configuration Reset',
      description: `MFA secret reset for ${target?.name || id}. User must re-enroll on next login.`
    });
  };

  // ===============================================
  // FEATURE FLAGS & SETTINGS
  // ===============================================
  const toggleFeatureFlag = (id: string) => {
    setFeatureFlags((prev) =>
      prev.map((f) => {
        if (f.id === id) {
          const nextState = !f.enabled;
          pushAuditLog('CONFIGURATION', 'FEATURE_FLAG_TOGGLED', 'FEATURE_FLAG', id, f.name, undefined, [
            { field: 'enabled', before: f.enabled, after: nextState }
          ]);
          return {
            ...f,
            enabled: nextState,
            updatedAt: new Date().toISOString()
          };
        }
        return f;
      })
    );

    const target = featureFlags.find((f) => f.id === id);
    addToast({
      type: 'info',
      title: 'Feature Flag Toggled',
      description: `${target?.key} is now ${!target?.enabled ? 'ENABLED' : 'DISABLED'}.`
    });
  };

  const updateSettings = (section: SettingsSection, newSettings: any) => {
    setSettings((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        ...newSettings
      }
    }));

    pushAuditLog('CONFIGURATION', `SETTINGS_SECTION_UPDATED_${section.toUpperCase()}`, 'SETTINGS', section);

    addToast({
      type: 'success',
      title: 'Platform Settings Saved',
      description: `Global ${section} configuration updated successfully.`
    });
  };

  // ===============================================
  // INCIDENTS & SECURITY ALERTS
  // ===============================================
  const acknowledgeIncident = (id: string, assignedTo?: string) => {
    setIncidents((prev) =>
      prev.map((inc) =>
        inc.id === id
          ? {
              ...inc,
              status: 'ACKNOWLEDGED',
              assignedTo: assignedTo || 'anh.nh@kyanon.digital',
              updatedAt: new Date().toISOString()
            }
          : inc
      )
    );

    pushAuditLog('MONITORING', 'INCIDENT_ACKNOWLEDGED', 'INCIDENT', id);
    addToast({
      type: 'info',
      title: 'Operational Incident Acknowledged',
      description: `Incident ${id} marked as Acknowledged.`
    });
  };

  const resolveIncident = (id: string, note?: string) => {
    setIncidents((prev) =>
      prev.map((inc) =>
        inc.id === id
          ? {
              ...inc,
              status: 'RESOLVED',
              resolutionNote: note || 'Resolved by Platform Administrator',
              updatedAt: new Date().toISOString()
            }
          : inc
      )
    );

    pushAuditLog('MONITORING', 'INCIDENT_RESOLVED', 'INCIDENT', id);
    addToast({
      type: 'success',
      title: 'Incident Resolved',
      description: `Incident ${id} marked as Resolved.`
    });
  };

  const acknowledgeAlert = (id: string) => {
    setSecurityAlerts((prev) =>
      prev.map((al) => (al.id === id ? { ...al, status: 'ACKNOWLEDGED' } : al))
    );
    pushAuditLog('SECURITY', 'SECURITY_ALERT_ACKNOWLEDGED', 'SECURITY_ALERT', id);
    addToast({
      type: 'info',
      title: 'Security Alert Acknowledged',
      description: `Alert ${id} acknowledged.`
    });
  };

  const resolveAlert = (id: string) => {
    setSecurityAlerts((prev) =>
      prev.map((al) => (al.id === id ? { ...al, status: 'RESOLVED' } : al))
    );
    pushAuditLog('SECURITY', 'SECURITY_ALERT_RESOLVED', 'SECURITY_ALERT', id);
    addToast({
      type: 'success',
      title: 'Security Threat Resolved',
      description: `Security alert ${id} marked as Resolved.`
    });
  };

  // ===============================================
  // SESSIONS & CREDENTIALS
  // ===============================================
  const revokeSession = (id: string) => {
    const session = sessions.find((s) => s.id === id);
    setSessions((prev) => prev.filter((s) => s.id !== id));
    pushAuditLog('SECURITY', 'SESSION_REVOKED', 'SESSION', id, session?.userName);

    addToast({
      type: 'warning',
      title: 'Session Revoked',
      description: `Active session for ${session?.userEmail || id} was terminated.`
    });
  };

  const revokeAllUserSessions = (userId: string) => {
    setSessions((prev) => prev.filter((s) => s.userId !== userId));
    pushAuditLog('SECURITY', 'ALL_USER_SESSIONS_REVOKED', 'USER', userId);

    addToast({
      type: 'warning',
      title: 'All User Sessions Terminated',
      description: `All active device sessions for user ${userId} were revoked.`
    });
  };

  const rotateCredential = (id: string) => {
    setCredentials((prev) =>
      prev.map((c) =>
        c.id === id
          ? {
              ...c,
              keyPrefix: `${c.keyPrefix.substring(0, 8)}_rot_${Math.random().toString(36).substring(2, 6)}`,
              createdAt: new Date().toISOString()
            }
          : c
      )
    );

    pushAuditLog('CREDENTIAL', 'API_CREDENTIAL_ROTATED', 'CREDENTIAL', id);
    addToast({
      type: 'success',
      title: 'API Credential Rotated',
      description: `Rotated key for credential ${id}. Old keys remain in grace period.`
    });
  };

  const revokeCredential = (id: string) => {
    setCredentials((prev) =>
      prev.map((c) => (c.id === id ? { ...c, status: 'REVOKED' } : c))
    );

    pushAuditLog('CREDENTIAL', 'API_CREDENTIAL_REVOKED', 'CREDENTIAL', id);
    addToast({
      type: 'error',
      title: 'API Credential Revoked',
      description: `Credential ${id} has been permanently revoked.`
    });
  };

  return (
    <PlatformContext.Provider
      value={{
        isAuthenticated,
        currentUser,
        login,
        logout,
        theme,
        toggleTheme,
        isMfaModalOpen,
        mfaModalMode,
        mfaTargetAdminName,
        isMfaVerified,
        openMfaModal,
        closeMfaModal,
        primaryTab,
        setPrimaryTab,
        platformSubTab,
        setPlatformSubTab,
        monitoringSubTab,
        setMonitoringSubTab,
        securitySubTab,
        setSecuritySubTab,
        settingsSection,
        setSettingsSection,
        selectedTenantId,
        setSelectedTenantId,
        selectedAdminId,
        setSelectedAdminId,
        isLiveSimulationActive,
        setIsLiveSimulationActive,
        lastUpdatedTime,
        tenants,
        admins,
        sessions,
        featureFlags,
        settings,
        services,
        edgeDevices,
        cameras,
        gates,
        incidents,
        securityAlerts,
        loginEvents,
        credentials,
        auditLogs,
        pushAuditLog,
        toasts,
        addToast,
        removeToast,
        createTenant,
        updateTenant,
        setTenantStatus,
        createAdmin,
        updateAdmin,
        disableAdmin,
        resetAdminMfa,
        toggleFeatureFlag,
        updateSettings,
        acknowledgeIncident,
        resolveIncident,
        acknowledgeAlert,
        resolveAlert,
        revokeSession,
        revokeAllUserSessions,
        rotateCredential,
        revokeCredential,
        navigateTo
      }}
    >
      {children}
    </PlatformContext.Provider>
  );
};

export const usePlatform = (): PlatformContextType => {
  const context = useContext(PlatformContext);
  if (!context) {
    throw new Error('usePlatform must be used within a PlatformProvider');
  }
  return context;
};
