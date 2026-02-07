import { Outlet, Link, useLocation } from 'react-router-dom';
import { BarChart3, Home, GitCompare, Search } from 'lucide-react';

function Layout() {
    const location = useLocation();

    const navLinks = [
        { path: '/', icon: Home, label: 'Home' },
        { path: '/compare', icon: GitCompare, label: 'Compare' },
    ];

    return (
        <div className="min-h-screen">
            {/* Navigation */}
            <nav className="fixed top-0 left-0 right-0 z-50 glass-card rounded-none border-x-0 border-t-0">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        {/* Logo */}
                        <Link to="/" className="flex items-center gap-3 group">
                            <div className="p-2 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 group-hover:scale-110 transition-transform">
                                <BarChart3 className="w-6 h-6 text-white" />
                            </div>
                            <span className="text-xl font-bold text-gradient">ReviewAnalyzer</span>
                        </Link>

                        {/* Nav Links */}
                        <div className="flex items-center gap-2">
                            {navLinks.map(({ path, icon: Icon, label }) => (
                                <Link
                                    key={path}
                                    to={path}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200
                    ${location.pathname === path
                                            ? 'bg-white/20 text-white'
                                            : 'text-white/60 hover:text-white hover:bg-white/10'
                                        }`}
                                >
                                    <Icon className="w-4 h-4" />
                                    <span className="hidden sm:inline">{label}</span>
                                </Link>
                            ))}
                        </div>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="pt-20 pb-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
                <Outlet />
            </main>

            {/* Footer */}
            <footer className="border-t border-white/10 py-6 text-center text-white/40 text-sm">
                <p>Built with 💜 using FastAPI, React, and AI</p>
            </footer>
        </div>
    );
}

export default Layout;
