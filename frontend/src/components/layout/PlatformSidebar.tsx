import React, { useState } from 'react';
import { usePlatform } from '../../context/PlatformContext';
import {
  LayoutDashboard,
  Building2,
  Sliders,
  Activity,
  ShieldCheck,
  FileText,
  ChevronDown,
  ChevronRight,
  ShieldAlert,
  Server,
  Settings,
  Flag,
  Users,
  Radio,
  Lock,
  Key,
  Database,
  Layers,
  Sparkles
} from 'lucide-react';
import { PrimaryTab, PlatformSubTab, MonitoringSubTab, SecuritySubTab } from '../../types/platform';

export const PlatformSidebar: React.FC = () => {
  const {
    primaryTab,
    setPrimaryTab,
    platformSubTab,
    setPlatformSubTab,
    monitoringSubTab,
    setMonitoringSubTab,
    securitySubTab,
    setSecuritySubTab,
    incidents,
    securityAlerts,
    setSelectedTenantId
  } = usePlatform();

  const [isPlatformOpen, setIsPlatformOpen] = useState(true);
  const [isMonitoringOpen, setIsMonitoringOpen] = useState(true);
  const [isSecurityOpen, setIsSecurityOpen] = useState(true);

  const openIncidentsCount = incidents.filter((i) => i.status !== 'RESOLVED').length;
  const openAlertsCount = securityAlerts.filter((a) => a.status !== 'RESOLVED').length;

  return (
    <aside className="w-64 bg-[#0d0e12] border-r border-[#30363d] flex flex-col shrink-0 select-none">
      {/* Brand & Logo Header */}
      <div className="h-16 px-5 border-b border-[#30363d] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#161b22] border border-[#30363d] flex items-center justify-center text-[#58a6ff] shadow-sm font-bold">
            <ShieldCheck className="w-5 h-5 text-[#58a6ff]" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5 font-mono">
              PLATFORM <span className="text-[#58a6ff] font-extrabold">GOV</span>
            </h1>
            <p className="text-[10px] text-[#8b949e] font-semibold uppercase tracking-wider">Bento Control</p>
          </div>
        </div>
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1 text-xs font-medium">
        {/* 1. DASHBOARD */}
        <button
          onClick={() => {
            setPrimaryTab('dashboard');
            setSelectedTenantId(null);
          }}
          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all cursor-pointer ${
            primaryTab === 'dashboard'
              ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-semibold border-l-2 border-[#58a6ff]'
              : 'text-[#8b949e] hover:bg-[#161b22] hover:text-[#c9d1d9]'
          }`}
        >
          <LayoutDashboard className={`w-4 h-4 shrink-0 ${primaryTab === 'dashboard' ? 'text-[#58a6ff]' : 'text-[#8b949e]'}`} />
          <span>Dashboard</span>
        </button>

        {/* 2. TENANTS */}
        <button
          onClick={() => {
            setPrimaryTab('tenants');
            setSelectedTenantId(null);
          }}
          className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-all cursor-pointer ${
            primaryTab === 'tenants'
              ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-semibold border-l-2 border-[#58a6ff]'
              : 'text-[#8b949e] hover:bg-[#161b22] hover:text-[#c9d1d9]'
          }`}
        >
          <div className="flex items-center gap-3">
            <Building2 className={`w-4 h-4 shrink-0 ${primaryTab === 'tenants' ? 'text-[#58a6ff]' : 'text-[#8b949e]'}`} />
            <span>Tenants</span>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#21262d] border border-[#30363d] text-[#8b949e] font-mono">
            6
          </span>
        </button>

        {/* 3. PLATFORM GROUP */}
        <div>
          <button
            onClick={() => {
              setPrimaryTab('platform');
              setIsPlatformOpen(!isPlatformOpen);
            }}
            className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-all cursor-pointer ${
              primaryTab === 'platform'
                ? 'bg-[#161b22] text-[#58a6ff] font-semibold'
                : 'text-[#8b949e] hover:bg-[#161b22] hover:text-[#c9d1d9]'
            }`}
          >
            <div className="flex items-center gap-3">
              <Sliders className="w-4 h-4 shrink-0 text-[#8b949e]" />
              <span>Platform</span>
            </div>
            {isPlatformOpen ? <ChevronDown className="w-3.5 h-3.5 opacity-60" /> : <ChevronRight className="w-3.5 h-3.5 opacity-60" />}
          </button>

          {isPlatformOpen && (
            <div className="ml-4 mt-1 pl-3 border-l border-[#30363d] space-y-1">
              <button
                onClick={() => {
                  setPrimaryTab('platform');
                  setPlatformSubTab('settings');
                }}
                className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                  primaryTab === 'platform' && platformSubTab === 'settings'
                    ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-semibold'
                    : 'text-[#8b949e] hover:text-[#c9d1d9] hover:bg-[#161b22]'
                }`}
              >
                <Settings className="w-3.5 h-3.5" />
                <span>Settings</span>
              </button>

              <button
                onClick={() => {
                  setPrimaryTab('platform');
                  setPlatformSubTab('feature-flags');
                }}
                className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                  primaryTab === 'platform' && platformSubTab === 'feature-flags'
                    ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-semibold'
                    : 'text-[#8b949e] hover:text-[#c9d1d9] hover:bg-[#161b22]'
                }`}
              >
                <Flag className="w-3.5 h-3.5 text-[#d29922]" />
                <span>Feature Flags</span>
              </button>

              <button
                onClick={() => {
                  setPrimaryTab('platform');
                  setPlatformSubTab('admins');
                }}
                className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                  primaryTab === 'platform' && platformSubTab === 'admins'
                    ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-semibold'
                    : 'text-[#8b949e] hover:text-[#c9d1d9] hover:bg-[#161b22]'
                }`}
              >
                <Users className="w-3.5 h-3.5 text-[#a371f7]" />
                <span>Platform Admins</span>
              </button>
            </div>
          )}
        </div>

        {/* 4. MONITORING GROUP */}
        <div>
          <button
            onClick={() => {
              setPrimaryTab('monitoring');
              setIsMonitoringOpen(!isMonitoringOpen);
            }}
            className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-all cursor-pointer ${
              primaryTab === 'monitoring'
                ? 'bg-[#161b22] text-[#58a6ff] font-semibold'
                : 'text-[#8b949e] hover:bg-[#161b22] hover:text-[#c9d1d9]'
            }`}
          >
            <div className="flex items-center gap-3">
              <Activity className="w-4 h-4 shrink-0 text-[#8b949e]" />
              <span>Monitoring</span>
            </div>
            <div className="flex items-center gap-1.5">
              {openIncidentsCount > 0 && (
                <span className="text-[10px] px-1.5 py-0.2 bg-[#da3633]/20 text-[#f85149] border border-[#f85149]/30 rounded-full font-bold animate-pulse">
                  {openIncidentsCount}
                </span>
              )}
              {isMonitoringOpen ? <ChevronDown className="w-3.5 h-3.5 opacity-60" /> : <ChevronRight className="w-3.5 h-3.5 opacity-60" />}
            </div>
          </button>

          {isMonitoringOpen && (
            <div className="ml-4 mt-1 pl-3 border-l border-[#30363d] space-y-1">
              <button
                onClick={() => {
                  setPrimaryTab('monitoring');
                  setMonitoringSubTab('overview');
                }}
                className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                  primaryTab === 'monitoring' && monitoringSubTab === 'overview'
                    ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-semibold'
                    : 'text-[#8b949e] hover:text-[#c9d1d9] hover:bg-[#161b22]'
                }`}
              >
                <Server className="w-3.5 h-3.5 text-[#58a6ff]" />
                <span>System Health</span>
              </button>

              <button
                onClick={() => {
                  setPrimaryTab('monitoring');
                  setMonitoringSubTab('edge');
                }}
                className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                  primaryTab === 'monitoring' && monitoringSubTab === 'edge'
                    ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-semibold'
                    : 'text-[#8b949e] hover:text-[#c9d1d9] hover:bg-[#161b22]'
                }`}
              >
                <Radio className="w-3.5 h-3.5 text-[#3fb950]" />
                <span>Edge & Devices</span>
              </button>

              <button
                onClick={() => {
                  setPrimaryTab('monitoring');
                  setMonitoringSubTab('incidents');
                }}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                  primaryTab === 'monitoring' && monitoringSubTab === 'incidents'
                    ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-semibold'
                    : 'text-[#8b949e] hover:text-[#c9d1d9] hover:bg-[#161b22]'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-[#f85149]" />
                  <span>Incidents</span>
                </div>
                {openIncidentsCount > 0 && (
                  <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-[#da3633]/20 text-[#f85149] font-bold">
                    {openIncidentsCount}
                  </span>
                )}
              </button>
            </div>
          )}
        </div>

        {/* 5. SECURITY GROUP */}
        <div>
          <button
            onClick={() => {
              setPrimaryTab('security');
              setIsSecurityOpen(!isSecurityOpen);
            }}
            className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-all cursor-pointer ${
              primaryTab === 'security'
                ? 'bg-[#161b22] text-[#58a6ff] font-semibold'
                : 'text-[#8b949e] hover:bg-[#161b22] hover:text-[#c9d1d9]'
            }`}
          >
            <div className="flex items-center gap-3">
              <Lock className="w-4 h-4 shrink-0 text-[#8b949e]" />
              <span>Security</span>
            </div>
            <div className="flex items-center gap-1.5">
              {openAlertsCount > 0 && (
                <span className="text-[10px] px-1.5 py-0.2 bg-[#da3633]/20 text-[#f85149] border border-[#f85149]/30 rounded-full font-bold">
                  {openAlertsCount}
                </span>
              )}
              {isSecurityOpen ? <ChevronDown className="w-3.5 h-3.5 opacity-60" /> : <ChevronRight className="w-3.5 h-3.5 opacity-60" />}
            </div>
          </button>

          {isSecurityOpen && (
            <div className="ml-4 mt-1 pl-3 border-l border-[#30363d] space-y-1">
              <button
                onClick={() => {
                  setPrimaryTab('security');
                  setSecuritySubTab('overview');
                }}
                className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                  primaryTab === 'security' && securitySubTab === 'overview'
                    ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-semibold'
                    : 'text-[#8b949e] hover:text-[#c9d1d9] hover:bg-[#161b22]'
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5 text-[#3fb950]" />
                <span>Security Overview</span>
              </button>

              <button
                onClick={() => {
                  setPrimaryTab('security');
                  setSecuritySubTab('alerts');
                }}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                  primaryTab === 'security' && securitySubTab === 'alerts'
                    ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-semibold'
                    : 'text-[#8b949e] hover:text-[#c9d1d9] hover:bg-[#161b22]'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-[#f85149]" />
                  <span>Security Alerts</span>
                </div>
                {openAlertsCount > 0 && (
                  <span className="text-[10px] px-1.5 py-0.2 bg-[#da3633]/20 text-[#f85149] rounded-full font-bold">
                    {openAlertsCount}
                  </span>
                )}
              </button>

              <button
                onClick={() => {
                  setPrimaryTab('security');
                  setSecuritySubTab('sessions');
                }}
                className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                  primaryTab === 'security' && securitySubTab === 'sessions'
                    ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-semibold'
                    : 'text-[#8b949e] hover:text-[#c9d1d9] hover:bg-[#161b22]'
                }`}
              >
                <Key className="w-3.5 h-3.5 text-[#d29922]" />
                <span>Active Sessions</span>
              </button>

              <button
                onClick={() => {
                  setPrimaryTab('security');
                  setSecuritySubTab('credentials');
                }}
                className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                  primaryTab === 'security' && securitySubTab === 'credentials'
                    ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-semibold'
                    : 'text-[#8b949e] hover:text-[#c9d1d9] hover:bg-[#161b22]'
                }`}
              >
                <Layers className="w-3.5 h-3.5 text-[#58a6ff]" />
                <span>API Credentials</span>
              </button>
            </div>
          )}
        </div>

        {/* 6. AUDIT LOGS */}
        <button
          onClick={() => {
            setPrimaryTab('audit');
            setSelectedTenantId(null);
          }}
          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all cursor-pointer ${
            primaryTab === 'audit'
              ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-semibold border-l-2 border-[#58a6ff]'
              : 'text-[#8b949e] hover:bg-[#161b22] hover:text-[#c9d1d9]'
          }`}
        >
          <FileText className={`w-4 h-4 shrink-0 ${primaryTab === 'audit' ? 'text-[#58a6ff]' : 'text-[#8b949e]'}`} />
          <span>Audit Logs</span>
        </button>
      </nav>

      {/* Footer Profile Status */}
      <div className="p-4 border-t border-[#30363d] bg-[#161b22] shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[#58a6ff]/20 border border-[#58a6ff]/40 flex items-center justify-center font-bold text-[#58a6ff] text-xs font-mono">
            AN
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-xs font-semibold text-white truncate">Anthony Nguyen</h4>
            <p className="text-[10px] text-[#8b949e] truncate font-mono">anh.nh@kyanon.digital</p>
          </div>
          <span className="w-2 h-2 rounded-full bg-[#3fb950] animate-pulse shrink-0" title="Online & Connected" />
        </div>
      </div>
    </aside>
  );
};
