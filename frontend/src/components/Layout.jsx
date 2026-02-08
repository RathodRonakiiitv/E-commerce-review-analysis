import { Outlet, Link, useLocation } from 'react-router-dom';
import { BarChart3, Home, GitCompare, Menu, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

function Layout() {
    const location = useLocation();
    const [scrolled, setScrolled] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    // Handle scroll effect for navbar
    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const navLinks = [
        { path: '/', icon: Home, label: 'Analysis Hub' },
        { path: '/compare', icon: GitCompare, label: 'Comparison' },
    ];

    return (
        <div className="min-h-screen flex flex-col font-sans selection:bg-primary-500/30">
            {/* Ambient Background Glow */}
            <div className="fixed top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary-600/10 blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-accent-600/10 blur-[120px]" />
            </div>

            {/* Navigation */}
            <header
                className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 border-b ${scrolled
                    ? 'bg-[#0b1121]/80 backdrop-blur-md border-white/5 py-3 shadow-lg shadow-black/5'
                    : 'bg-transparent border-transparent py-5'
                    }`}
            >
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between">
                        {/* Logo */}
                        <Link
                            to="/"
                            className="flex items-center gap-3 group relative"
                            onClick={() => setMobileMenuOpen(false)}
                        >
                            <div className="relative p-2.5 rounded-xl bg-gradient-to-br from-primary-600 to-primary-500 border border-white/10 shadow-lg shadow-primary-500/20 group-hover:shadow-primary-500/40 transition-all duration-300 group-hover:scale-105">
                                <BarChart3 className="w-5 h-5 text-white" />
                                <div className="absolute inset-0 rounded-xl bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-xl font-bold tracking-tight text-white group-hover:text-primary-200 transition-colors">
                                    Review<span className="text-primary-400">Analyzer</span>
                                </span>
                                <span className="text-[10px] uppercase tracking-widest text-white/40 font-semibold group-hover:text-white/60 transition-colors">
                                    AI Powered
                                </span>
                            </div>
                        </Link>

                        {/* Desktop Nav */}
                        <div className="hidden md:flex items-center gap-1 bg-white/5 p-1 rounded-xl border border-white/5">
                            {navLinks.map(({ path, icon: Icon, label }) => {
                                const isActive = location.pathname === path;
                                return (
                                    <Link
                                        key={path}
                                        to={path}
                                        className={`relative px-5 py-2 rounded-lg flex items-center gap-2 text-sm font-medium transition-all duration-300 ${isActive
                                            ? 'text-white'
                                            : 'text-white/50 hover:text-white hover:bg-white/5'
                                            }`}
                                    >
                                        {isActive && (
                                            <motion.div
                                                layoutId="desktop-nav-pill"
                                                className="absolute inset-0 bg-primary-600 rounded-lg shadow-lg shadow-primary-500/20"
                                                initial={false}
                                                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                            />
                                        )}
                                        <Icon className={`w-4 h-4 relative z-10 ${isActive ? 'text-white' : ''}`} />
                                        <span className="relative z-10">{label}</span>
                                    </Link>
                                );
                            })}
                        </div>

                        {/* Mobile Menu Toggle */}
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="md:hidden p-2 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                        >
                            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                        </button>
                    </div>
                </div>

                {/* Mobile Menu */}
                <AnimatePresence>
                    {mobileMenuOpen && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="md:hidden border-t border-white/5 bg-[#0b1121]/95 backdrop-blur-xl overflow-hidden"
                        >
                            <div className="px-4 py-4 space-y-2">
                                {navLinks.map(({ path, icon: Icon, label }) => {
                                    const isActive = location.pathname === path;
                                    return (
                                        <Link
                                            key={path}
                                            to={path}
                                            onClick={() => setMobileMenuOpen(false)}
                                            className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${isActive
                                                ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/20'
                                                : 'text-white/60 hover:bg-white/5 hover:text-white'
                                                }`}
                                        >
                                            <Icon className="w-5 h-5" />
                                            {label}
                                        </Link>
                                    );
                                })}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </header>

            {/* Main Content with Page Transitions */}
            <main className="flex-grow pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full relative z-10">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={location.pathname}
                        initial={{ opacity: 0, y: 15, filter: 'blur(5px)' }}
                        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                        exit={{ opacity: 0, y: -15, filter: 'blur(5px)' }}
                        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                        className="w-full"
                    >
                        <Outlet />
                    </motion.div>
                </AnimatePresence>
            </main>

            {/* Footer */}
            <footer className="border-t border-white/5 py-10 bg-[#0b1121]/50 backdrop-blur-sm relative z-10">
                <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-6">
                    <p className="text-white/30 text-sm flex items-center gap-2">
                        © {new Date().getFullYear()} ReviewAnalyzer.
                        <span className="hidden md:inline">•</span>
                        Designed with precision.
                    </p>

                </div>
            </footer>
        </div>
    );
}

export default Layout;
