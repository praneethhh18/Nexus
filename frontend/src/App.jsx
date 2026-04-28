import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { isLoggedIn } from './services/auth';
import Layout from './components/Layout';
import ErrorBoundary from './components/ErrorBoundary';
import ToastHost from './components/ToastHost';
import Skeleton, { SkeletonCard } from './components/Skeleton';

// ── Lazy route components ───────────────────────────────────────────────────
// Each page loads as its own JS chunk when the user navigates to it.
// The main bundle shrinks from ~850 KB to ~150 KB; 20+ smaller chunks
// stream in on demand.
const Login         = lazy(() => import('./pages/Login'));
const Setup         = lazy(() => import('./pages/Setup'));
const ResetPassword = lazy(() => import('./pages/ResetPassword'));
const AcceptInvite  = lazy(() => import('./pages/AcceptInvite'));

const Dashboard     = lazy(() => import('./pages/Dashboard'));
const Chat          = lazy(() => import('./pages/Chat'));
const CRM           = lazy(() => import('./pages/CRM'));
const Tasks         = lazy(() => import('./pages/Tasks'));
const Invoices      = lazy(() => import('./pages/Invoices'));
const Documents     = lazy(() => import('./pages/Documents'));
const Inbox         = lazy(() => import('./pages/Inbox'));
const Agents        = lazy(() => import('./pages/Agents'));
const Memory        = lazy(() => import('./pages/Memory'));
const Team          = lazy(() => import('./pages/Team'));
const Analytics     = lazy(() => import('./pages/Analytics'));
const Security      = lazy(() => import('./pages/Security'));
const AuditLog      = lazy(() => import('./pages/AuditLog'));
const Reports       = lazy(() => import('./pages/Reports'));
const Workflows     = lazy(() => import('./pages/Workflows'));
const History       = lazy(() => import('./pages/History'));
const Integrations  = lazy(() => import('./pages/Integrations'));
const AdminMetrics  = lazy(() => import('./pages/AdminMetrics'));
const Settings      = lazy(() => import('./pages/Settings'));
const Pricing       = lazy(() => import('./pages/Pricing'));
const Database      = lazy(() => import('./pages/Database'));
const SQLEditor     = lazy(() => import('./pages/SQLEditor'));
const WhatIf        = lazy(() => import('./pages/WhatIf'));


function ProtectedRoute({ children }) {
  return isLoggedIn() ? children : <Navigate to="/login" />;
}


// Shown while a route chunk is in flight. Uses the same skeleton primitives
// pages render — feels like the page is already there, not like it broke.
function RouteFallback() {
  return (
    <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 12 }}>
      <Skeleton width={240} height={22} />
      <Skeleton width={360} height={12} />
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 10, marginTop: 12,
      }}>
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    </div>
  );
}


// Wrap each lazy element in its own Suspense so the Layout chrome
// (sidebar, tray, keyboard-shortcuts modal) stays mounted during route
// transitions. Without per-route Suspense, a suspended page unmounts the
// whole tree and global shortcuts stop working until the chunk lands.
const L = (Component) => (
  <Suspense fallback={<RouteFallback />}>
    <Component />
  </Suspense>
);


export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ToastHost />
        <Routes>
          <Route path="/setup"          element={L(Setup)} />
          <Route path="/login"          element={L(Login)} />
          <Route path="/reset-password" element={L(ResetPassword)} />
          <Route path="/accept-invite"  element={L(AcceptInvite)} />
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route path="/"              element={L(Dashboard)} />
            <Route path="/chat"          element={L(Chat)} />
            <Route path="/crm"           element={L(CRM)} />
            <Route path="/tasks"         element={L(Tasks)} />
            <Route path="/invoices"      element={L(Invoices)} />
            <Route path="/documents"     element={L(Documents)} />
            <Route path="/inbox"         element={L(Inbox)} />
            {/* legacy bookmark: /approvals → /inbox */}
            <Route path="/approvals"     element={<Navigate to="/inbox" replace />} />
            <Route path="/agents"        element={L(Agents)} />
            <Route path="/memory"        element={L(Memory)} />
            <Route path="/team"          element={L(Team)} />
            <Route path="/analytics"     element={L(Analytics)} />
            <Route path="/security"      element={L(Security)} />
            <Route path="/audit"         element={L(AuditLog)} />
            <Route path="/reports"       element={L(Reports)} />
            <Route path="/workflows"     element={L(Workflows)} />
            <Route path="/history"       element={L(History)} />
            <Route path="/integrations"  element={L(Integrations)} />
            <Route path="/admin/metrics" element={L(AdminMetrics)} />
            <Route path="/settings"      element={L(Settings)} />
            <Route path="/pricing"       element={L(Pricing)} />
            {/* Dev-mode pages — still routable even when hidden from nav */}
            <Route path="/database"      element={L(Database)} />
            <Route path="/sql"           element={L(SQLEditor)} />
            <Route path="/whatif"        element={L(WhatIf)} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
