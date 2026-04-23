import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { isLoggedIn } from './services/auth';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Database from './pages/Database';
import WhatIf from './pages/WhatIf';
import Reports from './pages/Reports';
import Workflows from './pages/Workflows';
import SQLEditor from './pages/SQLEditor';
import History from './pages/History';
import Settings from './pages/Settings';
import CRM from './pages/CRM';
import Tasks from './pages/Tasks';
import Invoices from './pages/Invoices';
import Documents from './pages/Documents';
import Inbox from './pages/Inbox';
import Agents from './pages/Agents';
import Memory from './pages/Memory';
import Team from './pages/Team';
import Analytics from './pages/Analytics';
import Security from './pages/Security';
import AuditLog from './pages/AuditLog';
import AcceptInvite from './pages/AcceptInvite';
import ResetPassword from './pages/ResetPassword';

function ProtectedRoute({ children }) {
  return isLoggedIn() ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/accept-invite" element={<AcceptInvite />} />
        <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/crm" element={<CRM />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/invoices" element={<Invoices />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/inbox" element={<Inbox />} />
          {/* legacy bookmark: /approvals → /inbox */}
          <Route path="/approvals" element={<Navigate to="/inbox" replace />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/memory" element={<Memory />} />
          <Route path="/team" element={<Team />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/security" element={<Security />} />
          <Route path="/audit" element={<AuditLog />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/workflows" element={<Workflows />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<Settings />} />
          {/* Developer-mode pages (still routable even when hidden from nav) */}
          <Route path="/database" element={<Database />} />
          <Route path="/sql" element={<SQLEditor />} />
          <Route path="/whatif" element={<WhatIf />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
