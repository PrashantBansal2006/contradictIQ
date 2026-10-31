import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';

// Home Landing Page
import { Home } from './pages/Home';

// Auth Pages
import { Login } from './pages/auth/Login';
import { Register } from './pages/auth/Register';

// Workspace Pages
import { InvestigationsList } from './pages/investigations/InvestigationsList';

// Investigation Tab Pages
import { DashboardTab } from './pages/investigation-tabs/DashboardTab';
import { DocumentsTab } from './pages/investigation-tabs/DocumentsTab';
import { DocumentDetailTab } from './pages/investigation-tabs/DocumentDetailTab';
import { ClaimsTab } from './pages/investigation-tabs/ClaimsTab';
import { FindingsTab } from './pages/investigation-tabs/FindingsTab';
import { GraphTab } from './pages/investigation-tabs/GraphTab';
import { HistoryTab } from './pages/investigation-tabs/HistoryTab';
import { CompareTab } from './pages/investigation-tabs/CompareTab';

// Advanced & Shared Pages
import { EvalPage } from './pages/eval/EvalPage';
import { SharedInvestigationPage } from './pages/shared/SharedInvestigationPage';
import { NotFound } from './pages/NotFound';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Auth routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Main Application Shell (Unified Navbar and Layout) */}
        <Route element={<AppLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/investigations" element={<InvestigationsList />} />

          {/* Investigation Shell & Tabs */}
          <Route path="/investigations/:id" element={<Navigate to="dashboard" replace />} />
          <Route path="/investigations/:id/dashboard" element={<DashboardTab />} />
          <Route path="/investigations/:id/documents" element={<DocumentsTab />} />
          <Route path="/investigations/:id/documents/:docId" element={<DocumentDetailTab />} />
          <Route path="/investigations/:id/claims" element={<ClaimsTab />} />
          <Route path="/investigations/:id/findings" element={<FindingsTab />} />
          <Route path="/investigations/:id/findings/:findingId" element={<FindingsTab />} />
          <Route path="/investigations/:id/graph" element={<GraphTab />} />
          <Route path="/investigations/:id/history" element={<HistoryTab />} />
          <Route path="/investigations/:id/compare" element={<CompareTab />} />

          {/* Eval Harness & Benchmarks */}
          <Route path="/eval" element={<EvalPage />} />

          {/* Shared / Judge Mode */}
          <Route path="/shared/:token" element={<SharedInvestigationPage />} />

          {/* 404 Catch-All */}
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
