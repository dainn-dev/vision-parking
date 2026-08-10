import React, { useState } from 'react';
import { PlatformProvider, usePlatform } from './context/PlatformContext';
import { PlatformSidebar } from './components/layout/PlatformSidebar';
import { PlatformHeader } from './components/layout/PlatformHeader';
import { ToastContainer } from './components/layout/ToastContainer';
import { CreateTenantModal } from './pages/tenants/CreateTenantModal';
import { MfaFlowModal } from './components/modals/MfaFlowModal';
import { LoginPage } from './pages/auth/LoginPage';

import { DashboardPage } from './pages/DashboardPage';
import { TenantsListPage } from './pages/tenants/TenantsListPage';
import { TenantDetailPage } from './pages/tenants/TenantDetailPage';
import { PlatformSettingsPage } from './pages/platform/PlatformSettingsPage';
import { FeatureFlagsPage } from './pages/platform/FeatureFlagsPage';
import { PlatformAdminsPage } from './pages/platform/PlatformAdminsPage';
import { MonitoringPage } from './pages/monitoring/MonitoringPage';
import { SecurityPage } from './pages/security/SecurityPage';
import { AuditLogsPage } from './pages/audit/AuditLogsPage';

const PlatformAppContent: React.FC = () => {
  const {
    isAuthenticated,
    primaryTab,
    platformSubTab,
    selectedTenantId,
    setSelectedTenantId,
    isMfaModalOpen,
    closeMfaModal,
    mfaModalMode,
    mfaTargetAdminName
  } = usePlatform();
  const [isCreateTenantModalOpen, setIsCreateTenantModalOpen] = useState(false);

  if (!isAuthenticated) {
    return (
      <>
        <LoginPage />
        <ToastContainer />
      </>
    );
  }

  return (
    <div className="flex h-screen w-screen bg-[#0d0e12] text-[#c9d1d9] font-sans overflow-hidden antialiased selection:bg-[#58a6ff] selection:text-slate-950">
      {/* Shared Navigation Sidebar */}
      <PlatformSidebar />

      {/* Main Content Workspace Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header Bar */}
        <PlatformHeader
          onOpenQuickActionModal={() => setIsCreateTenantModalOpen(true)}
        />

        {/* Scrollable Page Viewport */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6">
          {primaryTab === 'dashboard' && (
            <DashboardPage onOpenCreateTenantModal={() => setIsCreateTenantModalOpen(true)} />
          )}

          {primaryTab === 'tenants' && (
            selectedTenantId ? (
              <TenantDetailPage
                tenantId={selectedTenantId}
                onBack={() => setSelectedTenantId(null)}
              />
            ) : (
              <TenantsListPage onOpenCreateModal={() => setIsCreateTenantModalOpen(true)} />
            )
          )}

          {primaryTab === 'platform' && (
            <>
              {platformSubTab === 'settings' && <PlatformSettingsPage />}
              {platformSubTab === 'feature-flags' && <FeatureFlagsPage />}
              {platformSubTab === 'admins' && <PlatformAdminsPage />}
            </>
          )}

          {primaryTab === 'monitoring' && <MonitoringPage />}

          {primaryTab === 'security' && <SecurityPage />}

          {primaryTab === 'audit' && <AuditLogsPage />}
        </main>
      </div>

      {/* Global Modals & Toast Container */}
      <CreateTenantModal
        isOpen={isCreateTenantModalOpen}
        onClose={() => setIsCreateTenantModalOpen(false)}
      />

      <MfaFlowModal
        isOpen={isMfaModalOpen}
        onClose={closeMfaModal}
        mode={mfaModalMode}
        targetAdminName={mfaTargetAdminName}
      />

      <ToastContainer />
    </div>
  );
};

export default function App() {
  return (
    <PlatformProvider>
      <PlatformAppContent />
    </PlatformProvider>
  );
}
