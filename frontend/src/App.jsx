import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Chat from './pages/Chat';
import Database from './pages/Database';
import WhatIf from './pages/WhatIf';
import Reports from './pages/Reports';
import History from './pages/History';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Chat />} />
          <Route path="/database" element={<Database />} />
          <Route path="/whatif" element={<WhatIf />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
