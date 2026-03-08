import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { DashboardLayout } from './layouts/DashboardLayout';
import { LoginPage } from './pages/Login';
import { DashboardPage } from './pages/Dashboard';
import { SearchPage } from './pages/Search';
import { IngestPage } from './pages/Ingest';

import { ToastProvider } from './context/ToastContext';

import { SourcesPage } from './pages/Sources';

function App() {
    return (
        <AuthProvider>
            <ToastProvider>
                <BrowserRouter>
                    <Routes>
                        <Route path="/login" element={<LoginPage />} />

                        <Route path="/" element={<DashboardLayout />}>
                            <Route index element={<DashboardPage />} />
                            <Route path="search" element={<SearchPage />} />
                            <Route path="ingest" element={<IngestPage />} />
                            <Route path="sources" element={<SourcesPage />} />
                            <Route path="settings" element={<div className="text-gray-500 italic">Settings Page - Coming Day 5</div>} />
                        </Route>

                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                </BrowserRouter>
            </ToastProvider>
        </AuthProvider>
    );
}

export default App;
