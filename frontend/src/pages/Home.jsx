import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Sparkles, BarChart3, Shield, TrendingUp, Loader2, AlertCircle } from 'lucide-react';
import { startScraping, getScrapeStatus } from '../services/api';

function Home() {
    const [url, setUrl] = useState('');
    const [maxReviews, setMaxReviews] = useState(200);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState('');
    const navigate = useNavigate();

    const features = [
        {
            icon: Sparkles,
            title: 'AI Sentiment Analysis',
            description: 'Advanced NLP models analyze every review for emotional tone and context.',
            color: 'from-primary-500 to-blue-500'
        },
        {
            icon: BarChart3,
            title: 'Aspect-Based Insights',
            description: 'Understand what customers say about quality, price, delivery, and more.',
            color: 'from-accent-500 to-pink-500'
        },
        {
            icon: Shield,
            title: 'Fake Review Detection',
            description: 'AI-powered algorithms flag suspicious and potentially fake reviews.',
            color: 'from-emerald-500 to-teal-500'
        },
        {
            icon: TrendingUp,
            title: 'Topic Discovery',
            description: 'Automatically discover what themes customers discuss most.',
            color: 'from-amber-500 to-orange-500'
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
        setStatusMessage('Starting scraping job...');

        try {
            // Start scraping
            const { data } = await startScraping(url, maxReviews);
            const jobId = data.job_id;

            // Poll for status
            const pollInterval = setInterval(async () => {
                try {
                    const { data: status } = await getScrapeStatus(jobId);
                    setProgress(status.progress);
                    setStatusMessage(status.message || `Scraped ${status.reviews_scraped} reviews...`);

                    if (status.status === 'completed') {
                        clearInterval(pollInterval);
                        setLoading(false);
                        navigate(`/products/${status.product_id}`);
                    } else if (status.status === 'failed') {
                        clearInterval(pollInterval);
                        setLoading(false);
                        setError(status.error || 'Scraping failed. Please try again.');
                    }
                } catch (err) {
                    clearInterval(pollInterval);
                    setLoading(false);
                    setError('Failed to check status');
                }
            }, 2000);

        } catch (err) {
            setLoading(false);
            setError(err.response?.data?.detail || 'Failed to start scraping');
        }
    };

    return (
        <div className="space-y-16">
            {/* Hero Section */}
            <section className="text-center space-y-6 py-10">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 text-sm text-white/70">
                    <Sparkles className="w-4 h-4 text-accent-400" />
                    AI-Powered Product Analysis
                </div>

                <h1 className="text-4xl md:text-6xl font-bold leading-tight">
                    <span className="text-gradient">Understand</span> What Customers
                    <br />Really Think
                </h1>

                <p className="text-lg text-white/60 max-w-2xl mx-auto">
                    Paste any Amazon or Flipkart product URL and get instant insights with
                    AI-powered sentiment analysis, fake review detection, and more.
                </p>

                {/* Search Form */}
                <form onSubmit={handleAnalyze} className="max-w-3xl mx-auto mt-8">
                    <div className="glass-card p-2 flex flex-col sm:flex-row gap-2">
                        <div className="flex-1 relative">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                            <input
                                type="url"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="Paste Amazon or Flipkart product URL..."
                                className="input-field pl-12"
                                disabled={loading}
                            />
                        </div>
                        <select
                            value={maxReviews}
                            onChange={(e) => setMaxReviews(Number(e.target.value))}
                            className="input-field sm:w-32"
                            disabled={loading}
                        >
                            <option value={50}>50 reviews</option>
                            <option value={100}>100 reviews</option>
                            <option value={200}>200 reviews</option>
                            <option value={300}>300 reviews</option>
                            <option value={500}>500 reviews</option>
                        </select>
                        <button
                            type="submit"
                            disabled={loading}
                            className="btn-primary flex items-center justify-center gap-2 min-w-[140px]"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Analyzing...
                                </>
                            ) : (
                                <>
                                    <Sparkles className="w-5 h-5" />
                                    Analyze
                                </>
                            )}
                        </button>
                    </div>

                    {/* Progress Bar */}
                    {loading && (
                        <div className="mt-4 space-y-2">
                            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-primary-500 to-accent-500 transition-all duration-500"
                                    style={{ width: `${progress}%` }}
                                />
                            </div>
                            <p className="text-sm text-white/60">{statusMessage}</p>
                        </div>
                    )}

                    {/* Error Message */}
                    {error && (
                        <div className="mt-4 flex items-center gap-2 text-rose-400 bg-rose-500/10 px-4 py-3 rounded-lg">
                            <AlertCircle className="w-5 h-5" />
                            {error}
                        </div>
                    )}
                </form>
            </section>

            {/* Features Grid */}
            <section className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                {features.map((feature, index) => (
                    <div
                        key={index}
                        className="glass-card p-6 space-y-4 hover:scale-[1.02] transition-transform duration-300"
                        style={{ animationDelay: `${index * 100}ms` }}
                    >
                        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center`}>
                            <feature.icon className="w-6 h-6 text-white" />
                        </div>
                        <h3 className="text-lg font-semibold">{feature.title}</h3>
                        <p className="text-white/60 text-sm">{feature.description}</p>
                    </div>
                ))}
            </section>

            {/* How It Works */}
            <section className="text-center space-y-8">
                <h2 className="text-3xl font-bold">How It Works</h2>
                <div className="grid md:grid-cols-3 gap-8">
                    {[
                        { step: '01', title: 'Paste URL', desc: 'Enter any Amazon or Flipkart product URL' },
                        { step: '02', title: 'AI Analysis', desc: 'Our AI scrapes and analyzes all reviews' },
                        { step: '03', title: 'Get Insights', desc: 'View detailed sentiment and aspect analysis' }
                    ].map((item, i) => (
                        <div key={i} className="relative">
                            <div className="text-6xl font-bold text-white/5 absolute -top-4 left-1/2 -translate-x-1/2">
                                {item.step}
                            </div>
                            <div className="glass-card p-6 pt-10 relative z-10">
                                <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                                <p className="text-white/60 text-sm">{item.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>
        </div>
    );
}

export default Home;
