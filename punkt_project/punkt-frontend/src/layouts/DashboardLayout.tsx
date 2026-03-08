import { FC, useState } from 'react';
import { Navigate, Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    BarChart3,
    Search,
    Upload,
    Database,
    Settings,
    LogOut,
    Menu,
    X
} from 'lucide-react';
import { cn } from '../lib/utils';

export const DashboardLayout: FC = () => {
    const { isAuthenticated, user, logout } = useAuth();
    const location = useLocation();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    const navItems = [
        { name: 'Dashboard', href: '/', icon: BarChart3 },
        { name: 'Search', href: '/search', icon: Search },
        { name: 'Ingestion', href: '/ingest', icon: Upload },
        { name: 'Sources', href: '/sources', icon: Database },
        { name: 'Settings', href: '/settings', icon: Settings },
    ];

    return (
        <div className="flex h-screen w-full bg-transparent text-ink overflow-hidden">
            {/* Sidebar */}
            <aside className={cn(
                "fixed inset-y-0 left-0 z-50 w-64 glass-panel border-r-2 border-ink transition-transform duration-300 transform lg:relative lg:translate-x-0 shadow-2xl",
                isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
            )}>
                <div className="flex flex-col h-full">
                    {/* Logo */}
                    <div className="flex items-center gap-3 p-8 border-b-2 border-ink bg-accent/20">
                        <img
                            src="/assets/avatar.png"
                            alt="Avatar"
                            className="w-[51px] h-[77px] object-cover border-2 border-ink shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
                        />
                        <h1 className="text-4xl font-marker text-ink -rotate-2 tracking-tighter ml-[5px]">PUNKT</h1>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-4 py-6 space-y-4 overflow-y-auto">
                        {navItems.map((item) => {
                            const active = location.pathname === item.href;
                            return (
                                <Link
                                    key={item.href}
                                    to={item.href}
                                    className={cn(
                                        "flex items-center gap-3 px-4 py-3 border-2 border-transparent transition-all font-typewriter text-lg group",
                                        active
                                            ? "bg-ink text-white border-ink shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] -rotate-1"
                                            : "text-ink hover:border-ink hover:bg-yellow-50"
                                    )}
                                    onClick={() => setIsMobileMenuOpen(false)}
                                >
                                    <item.icon size={20} className={cn("transition-transform group-hover:scale-110", active ? "text-accent" : "text-ink")} />
                                    <span className="font-bold">{item.name}</span>
                                </Link>
                            );
                        })}
                    </nav>

                    {/* User Section */}
                    <div className="p-6 mt-auto border-t-2 border-ink bg-gray-50">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-full border-2 border-ink bg-accent flex items-center justify-center font-marker text-xl overflow-hidden text-ink">
                                {user?.username?.[0]?.toUpperCase() || 'U'}
                            </div>
                            <div className="min-w-0">
                                <p className="text-sm font-bold text-ink font-typewriter truncate">{user?.username}</p>
                                <p className="text-xs text-gray-500 font-typewriter truncate">{user?.tenant_id}</p>
                            </div>
                        </div>
                        <button
                            onClick={logout}
                            className="w-full flex items-center justify-center gap-2 px-4 py-2 border-2 border-ink hover:bg-ink hover:text-white transition-colors font-typewriter font-bold shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:shadow-none active:translate-x-[2px] active:translate-y-[2px] bg-white text-ink"
                        >
                            <LogOut size={16} />
                            Logout
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">

                {/* Mobile Header */}
                <header className="h-16 flex items-center justify-between px-6 bg-secondary border-b-2 border-ink lg:hidden z-40">
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-marker text-ink -rotate-2">PUNKT</span>
                    </div>
                    <button
                        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                        className="p-2 text-ink hover:bg-gray-200 rounded"
                    >
                        {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                    </button>
                </header>

                <main className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};
