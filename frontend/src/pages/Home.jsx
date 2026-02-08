import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Sparkles, BarChart3, Shield, TrendingUp, Loader2, AlertCircle, ArrowRight } from 'lucide-react';
import { startScraping, getScrapeStatus } from '../services/api';
import { motion } from 'framer-motion';

function Home() {
    const [url, setUrl] = useState('');
    const [maxReviews, setMaxReviews] = useState(200);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState('');
    const navigate = useNavigate();
    const pollRef = useRef(null);

    // Cleanup polling on unmount
    useEffect(() => {
        return () => {
            if (pollRef.current) clearInterval(pollRef.current);
        };
    }, []);

    const features = [
        {
            icon: Sparkles,
            title: 'AI Sentiment Analysis',
            description: 'Advanced NLP models decode emotional tone and context from every review.',
            color: 'from-primary-500 to-indigo-500',
            delay: 0.1
        },
        {
            icon: BarChart3,
            title: 'Aspect-Based Insights',
            description: 'Granular breakdown of quality, price, delivery, and service metrics.',
            color: 'from-accent-500 to-amber-500',
            delay: 0.2
        },
        {
            icon: Shield,
            title: 'Fake Review Detection',
            description: 'Sophisticated algorithms identify and flag suspicious review patterns.',
            color: 'from-emerald-500 to-teal-500',
            delay: 0.3
        },
        {
            icon: TrendingUp,
            title: 'Topic Discovery',
            description: 'Uncover emerging themes and hidden customer conversations automatically.',
            color: 'from-rose-500 to-pink-500',
            delay: 0.4
        }
    ];

    const handleAnalyze = async (e) => {
        e.preventDefault();
        if (!url.trim()) {
            setError('Please enter a product URL');
            return;
        }

        // Validate URL
        if (!url.includes('amazon') && !url.includes('flipkart')) {
            setError('Please enter a valid Amazon or Flipkart product URL');
            return;
        }

        setLoading(true);
        setError('');
        setProgress(0);
        setStatusMessage('Initializing analysis engine...');

        try {
            // Start scraping
            const { data } = await startScraping(url, maxReviews);
            const jobId = data.job_id;

            // Poll for status
            const pollInterval = setInterval(async () => {
                try {
                    const { data: status } = await getScrapeStatus(jobId);
                    setProgress(status.progress);
                    setStatusMessage(status.message || `Processing ${status.reviews_scraped} reviews...`);

                    if (status.status === 'completed') {
                        clearInterval(pollInterval);
                        pollRef.current = null;
                        setLoading(false);

                        if (status.product_id) {
                            navigate(`/products/${status.product_id}`);
                        } else {
                            setError('Analysis completed but no product data returned. The scraper may have been blocked or found no reviews.');
                        }
                    } else if (status.status === 'failed') {
                        clearInterval(pollInterval);
                        pollRef.current = null;
                        setLoading(false);
                        setError(status.error || 'Analysis failed. Please try again.');
                    }
                } catch (err) {
                    clearInterval(pollInterval);
                    pollRef.current = null;
                    setLoading(false);
                    setError('Connection lost. Retrying...');
                }
            }, 2000);
            pollRef.current = pollInterval;

        } catch (err) {
            setLoading(false);
            setError(err.response?.data?.detail || 'Failed to initiate analysis');
        }
    };

    return (
        <div className="space-y-24">
            {/* Hero Section */}
            <section className="relative text-center space-y-8 pt-10 px-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-500/10 border border-primary-500/20 text-sm font-medium text-primary-200 shadow-[0_0_15px_rgba(99,102,241,0.3)]"
                >
                    <Sparkles className="w-3.5 h-3.5 text-primary-400" />
                    <span>Next-Gen Product Intelligence</span>
                </motion.div>

                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.1 }}
                    className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.1]"
                >
                    <span className="text-white drop-shadow-2xl">Decode Customer</span>
                    <br />
                    <span className="text-gradient">Sentiment Instantly</span>
                </motion.h1>

                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="text-lg md:text-xl text-white/50 max-w-2xl mx-auto font-light leading-relaxed"
                >
                    Transform thousands of Amazon & Flipkart reviews into actionable insights.
                    Detect fake reviews, analyze sentiment, and discover hidden trends in seconds.
                </motion.p>

                {/* Search Form */}
                <motion.form
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                    onSubmit={handleAnalyze}
                    className="max-w-2xl mx-auto mt-12 relative z-10"
                >
                    <div className="glass-card p-2 flex flex-col sm:flex-row gap-2 transition-all duration-300 focus-within:ring-2 focus-within:ring-primary-500/50">
                        <div className="flex-1 relative group">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30 group-focus-within:text-primary-400 transition-colors" />
                            <input
                                type="url"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="Paste Amazon or Flipkart product URL..."
                                className="w-full bg-transparent border-none text-white placeholder-white/30 pl-12 pr-4 py-3 focus:ring-0 text-base"
                                disabled={loading}
                            />
                        </div>
                        <div className="h-px sm:h-auto sm:w-px bg-white/10 mx-2" />
                        <select
                            value={maxReviews}
                            onChange={(e) => setMaxReviews(Number(e.target.value))}
                            className="bg-transparent border-none text-white/80 focus:ring-0 sm:w-32 text-sm py-3 px-4 cursor-pointer hover:bg-white/5 rounded-lg transition-colors"
                            disabled={loading}
                        >
                            <option value={50} className="bg-slate-900">50 reviews</option>
                            <option value={100} className="bg-slate-900">100 reviews</option>
                            <option value={200} className="bg-slate-900">200 reviews</option>
                            <option value={300} className="bg-slate-900">300 reviews</option>
                            <option value={500} className="bg-slate-900">500 reviews</option>
                        </select>
                        <button
                            type="submit"
                            disabled={loading}
                            className="btn-primary min-w-[140px] flex items-center justify-center gap-2 group"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    <span>Analyzing</span>
                                </>
                            ) : (
                                <>
                                    <span>Analyze</span>
                                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </div>

                    {/* Progress & Error States */}
                    {(loading || error) && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            className="mt-6"
                        >
                            {loading && (
                                <div className="space-y-3 bg-slate-900/50 p-4 rounded-xl border border-white/5 backdrop-blur-sm">
                                    <div className="flex justify-between text-xs font-medium text-white/60">
                                        <span>{statusMessage}</span>
                                        <span>{Math.round(progress)}%</span>
                                    </div>
                                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                        <motion.div
                                            className="h-full bg-gradient-to-r from-primary-500 to-accent-500"
                                            initial={{ width: 0 }}
                                            animate={{ width: `${progress}%` }}
                                            transition={{ duration: 0.5 }}
                                        />
                                    </div>
                                </div>
                            )}

                            {error && (
                                <div className="flex items-center gap-3 text-rose-300 bg-rose-500/10 border border-rose-500/20 px-4 py-3 rounded-lg text-sm">
                                    <AlertCircle className="w-5 h-5 shrink-0" />
                                    {error}
                                </div>
                            )}
                        </motion.div>
                    )}
                </motion.form>
            </section>

            {/* Features Grid */}
            <section className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 px-4">
                {features.map((feature, index) => (
                    <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5, delay: feature.delay }}
                        whileHover={{ y: -5 }}
                        className="glass-card p-8 group cursor-default relative overflow-hidden"
                    >
                        <div className={`absolute top-0 right-0 p-20 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-5 transition-opacity duration-500 blur-3xl`} />

                        <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6 shadow-lg shadow-black/20 group-hover:scale-110 transition-transform duration-300`}>
                            <feature.icon className="w-7 h-7 text-white" />
                        </div>
                        <h3 className="text-xl font-bold mb-3 text-white/90 group-hover:text-white transition-colors">{feature.title}</h3>
                        <p className="text-white/50 text-sm leading-relaxed">{feature.description}</p>
                    </motion.div>
                ))}
            </section>

            {/* How It Works */}
            <section className="relative py-20 overflow-hidden">
                <div className="absolute inset-0 bg-white/[2%] skew-y-3 transform origin-top-left scale-110" />

                <div className="relative px-4 text-center space-y-16">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="space-y-4"
                    >
                        <h2 className="text-4xl font-bold tracking-tight">How It Works</h2>
                        <p className="text-white/50 max-w-xl mx-auto">Three simple steps to unlock deep product insights.</p>
                    </motion.div>

                    <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                        {[
                            { step: '01', title: 'Paste URL', desc: 'Copy any product link from Amazon or Flipkart.' },
                            { step: '02', title: 'AI Crunching', desc: 'Our engine scrapes & analyzes thousands of reviews.' },
                            { step: '03', title: 'Actionable Data', desc: 'Get instant sentiment reports & fake review warning.' }
                        ].map((item, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.2 }}
                                className="relative group"
                            >
                                <div className="text-[120px] font-bold text-white/5 absolute -top-12 left-1/2 -translate-x-1/2 select-none pointer-events-none group-hover:text-primary-500/10 transition-colors duration-500">
                                    {item.step}
                                </div>
                                <div className="glass-card p-8 pt-12 relative z-10 h-full border-t-4 border-t-transparent hover:border-t-primary-500 transition-all duration-300">
                                    <h3 className="text-xl font-bold mb-3">{item.title}</h3>
                                    <p className="text-white/50 text-sm leading-relaxed">{item.desc}</p>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>
        </div>
    );
}

export default Home;
