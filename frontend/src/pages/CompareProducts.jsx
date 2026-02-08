import { useState } from 'react';
import { Search, ArrowRight, Loader2, AlertCircle, Award as Trophy } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { startScraping, compareProducts, getScrapeStatus } from '../services/api';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Legend, Tooltip } from 'recharts';

function CompareProducts() {
    const [url1, setUrl1] = useState('');
    const [url2, setUrl2] = useState('');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState('');
    const [error, setError] = useState('');
    const [comparisonData, setComparisonData] = useState(null);

    const handleCompare = async (e) => {
        e.preventDefault();
        if (!url1 || !url2) {
            setError('Please enter both product URLs');
            return;
        }

        setLoading(true);
        setError('');
        setStatus('Initializing comparison engine...');
        setComparisonData(null);

        try {
            // Step 1: Scrape first product
            setStatus('Analyzing Product 1...');
            const scrape1 = await startScraping(url1, 100);
            const pid1 = await waitForScrape(scrape1.data.job_id, 'Product 1');

            if (!pid1) throw new Error('Failed to retrieve Product 1 ID');

            // Step 2: Scrape second product
            setStatus('Analyzing Product 2...');
            const scrape2 = await startScraping(url2, 100);
            const pid2 = await waitForScrape(scrape2.data.job_id, 'Product 2');

            if (!pid2) throw new Error('Failed to retrieve Product 2 ID');

            // Step 3: Compare
            setStatus('Generating comparison insights...');
            // Pass array of product IDs as expected by the backend
            const compareRes = await compareProducts([pid1, pid2]);

            setComparisonData(compareRes.data);
            setLoading(false);

        } catch (err) {
            console.error(err);
            setError(err.message || 'Comparison failed. Please check the URLs and try again.');
            setLoading(false);
        }
    };

    const waitForScrape = async (jobId, productName) => {
        return new Promise((resolve, reject) => {
            const interval = setInterval(async () => {
                try {
                    const { data } = await getScrapeStatus(jobId);
                    setStatus(`Processing ${productName}: ${data.progress}%`);

                    if (data.status === 'completed') {
                        clearInterval(interval);
                        resolve(data.product_id);
                    } else if (data.status === 'failed') {
                        clearInterval(interval);
                        reject(new Error(data.error || `${productName} analysis failed`));
                    }
                } catch (e) {
                    clearInterval(interval);
                    reject(e);
                }
            }, 2000);
        });
    };

    // Prepare radar data for visualization
    const getRadarData = () => {
        if (!comparisonData || !comparisonData.products) return [];

        // Collect all unique aspects
        const allAspects = new Set();
        comparisonData.products.forEach(p => {
            Object.keys(p.aspects || {}).forEach(a => allAspects.add(a));
        });

        return Array.from(allAspects).map(aspect => {
            const item = { aspect };
            comparisonData.products.forEach((p, i) => {
                item[`Product ${i + 1}`] = Math.round(p.aspects[aspect] || 0);
            });
            return item;
        });
    };

    const COLORS = ['#6366f1', '#f59e0b', '#10b981'];

    return (
        <div className="space-y-12 max-w-7xl mx-auto">
            {/* Header */}
            <div className="text-center space-y-4">
                <motion.h1
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-4xl md:text-5xl font-bold"
                >
                    <span className="text-gradient">Head-to-Head</span> Comparison
                </motion.h1>
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                    className="text-white/50 max-w-2xl mx-auto"
                >
                    Pit two products against each other. Our AI analyzes sentiment, features, and value to declare a winner.
                </motion.p>
            </div>

            {/* Input Section */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="glass-card p-8 md:p-12 relative overflow-hidden"
            >
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary-500 via-accent-500 to-primary-500" />

                <form onSubmit={handleCompare} className="space-y-8">
                    <div className="grid md:grid-cols-[1fr_auto_1fr] gap-8 items-center">
                        <div className="space-y-4">
                            <label className="block text-sm font-medium text-white/80 uppercase tracking-wider">Product 1</label>
                            <div className="relative group">
                                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30 group-focus-within:text-primary-400 transition-colors" />
                                <input
                                    type="url"
                                    value={url1}
                                    onChange={(e) => setUrl1(e.target.value)}
                                    placeholder="Paste first Amazon/Flipkart URL"
                                    className="input-field pl-12"
                                    disabled={loading}
                                />
                            </div>
                        </div>

                        <div className="hidden md:flex justify-center pt-8">
                            <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center border border-white/10 text-white/40 font-bold">VS</div>
                        </div>

                        <div className="space-y-4">
                            <label className="block text-sm font-medium text-white/80 uppercase tracking-wider">Product 2</label>
                            <div className="relative group">
                                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30 group-focus-within:text-accent-400 transition-colors" />
                                <input
                                    type="url"
                                    value={url2}
                                    onChange={(e) => setUrl2(e.target.value)}
                                    placeholder="Paste second Amazon/Flipkart URL"
                                    className="input-field pl-12"
                                    disabled={loading}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-center pt-4">
                        <button
                            type="submit"
                            disabled={loading || !url1 || !url2}
                            className="btn-primary min-w-[200px] flex items-center justify-center gap-2 py-4 text-lg"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-6 h-6 animate-spin" />
                                    <span>{status}</span>
                                </>
                            ) : (
                                <>
                                    <span>Compare Products</span>
                                    <ArrowRight className="w-5 h-5" />
                                </>
                            )}
                        </button>
                    </div>

                    {error && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            className="text-center text-rose-400 bg-rose-500/10 border border-rose-500/20 p-4 rounded-xl"
                        >
                            <span className="flex items-center justify-center gap-2">
                                <AlertCircle className="w-5 h-5" />
                                {error}
                            </span>
                        </motion.div>
                    )}
                </form>
            </motion.div>

            {/* comparison Results */}
            <AnimatePresence>
                {comparisonData && (
                    <motion.div
                        initial={{ opacity: 0, y: 40 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-8"
                    >
                        {/* Winner Banner */}
                        <div className="glass-card p-1 bg-gradient-to-r from-amber-500/20 to-primary-500/20 border-amber-500/30">
                            <div className="bg-[#0b1121]/80 backdrop-blur-md rounded-xl p-8 text-center">
                                <Trophy className="w-12 h-12 text-amber-400 mx-auto mb-4" />
                                <h2 className="text-3xl font-bold text-white mb-2">
                                    Overall Winner: <span className="text-amber-400">Product {comparisonData.best_overall === comparisonData.products[0].product_id ? '1' : '2'}</span>
                                </h2>
                                <p className="text-white/60">Based on sentiment analysis, feature rating, and price-to-value ratio.</p>
                            </div>
                        </div>

                        <div className="grid md:grid-cols-2 gap-8">
                            {/* Radar Chart */}
                            <div className="glass-card p-6">
                                <h3 className="text-xl font-bold mb-6 text-center">Aspect Comparison</h3>
                                <div className="h-[300px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={getRadarData()}>
                                            <PolarGrid stroke="#ffffff20" />
                                            <PolarAngleAxis dataKey="aspect" tick={{ fill: 'white', opacity: 0.6 }} />
                                            <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="transparent" />
                                            {comparisonData.products.map((p, i) => (
                                                <Radar
                                                    key={i}
                                                    name={`Product ${i + 1}`}
                                                    dataKey={`Product ${i + 1}`}
                                                    stroke={COLORS[i]}
                                                    fill={COLORS[i]}
                                                    fillOpacity={0.3}
                                                />
                                            ))}
                                            <Legend wrapperStyle={{ paddingTop: '20px' }} />
                                            <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '8px' }} />
                                        </RadarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* Comparison Table */}
                            <div className="glass-card p-6 flex flex-col justify-center">
                                <h3 className="text-xl font-bold mb-6 text-center">Key Metrics</h3>
                                <div className="space-y-4">
                                    <div className="flex justify-between items-center border-b border-white/5 pb-4">
                                        <div className="w-1/3 text-white/50 text-sm">Metric</div>
                                        <div className="w-1/3 text-center font-bold" style={{ color: COLORS[0] }}>Product 1</div>
                                        <div className="w-1/3 text-center font-bold" style={{ color: COLORS[1] }}>Product 2</div>
                                    </div>
                                    {[
                                        { label: 'Overall Score', key: 'overall_score', format: (v) => v.toFixed(0) },
                                        { label: 'Avg Rating', key: 'avg_rating', format: (v) => v.toFixed(1) },
                                        { label: 'Review Count', key: 'total_reviews', format: (v) => v }
                                    ].map((metric, i) => (
                                        <div key={i} className="flex justify-between items-center border-b border-white/5 pb-4 last:border-0">
                                            <div className="text-left w-1/3 text-white/80 text-sm">{metric.label}</div>
                                            {comparisonData.products.map((p, j) => (
                                                <div key={j} className="w-1/3 text-center font-medium">
                                                    {metric.format(p[metric.key])}
                                                </div>
                                            ))}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Aspect Winners */}
                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold mb-4">Detailed Aspect Winners</h3>
                            <div className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                                {Object.entries(comparisonData.aspect_winners || {}).map(([aspect, winnerId]) => {
                                    const winnerIndex = comparisonData.products.findIndex(p => p.product_id === winnerId);
                                    return (
                                        <div key={aspect} className="bg-white/5 rounded-xl p-4 border border-white/5">
                                            <div className="text-white/60 text-xs uppercase tracking-wider mb-2">{aspect}</div>
                                            <div className="font-bold flex items-center gap-2" style={{ color: COLORS[winnerIndex] }}>
                                                <Trophy className="w-4 h-4" />
                                                Product {winnerIndex + 1}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

export default CompareProducts;
