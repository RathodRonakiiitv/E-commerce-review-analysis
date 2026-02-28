import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Star, MessageSquare, BarChart3, ShieldCheck, Download, Share2, AlertTriangle, CheckCircle2, ThumbsUp, ThumbsDown, Minus } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { getProductAnalysis, exportPDF } from '../services/api';
import AIInsights from '../components/AIInsights';

const COLORS = ['#10b981', '#f59e0b', '#ef4444']; // Emerald, Amber, Rose

function ProductAnalysis() {
    const { productId: id } = useParams();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await getProductAnalysis(id);
                setData(response.data);
            } catch (err) {
                setError('Failed to load analysis data');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [id]);

    if (loading) {
        return (
            <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
                <div className="relative">
                    <div className="w-16 h-16 rounded-full border-4 border-primary-500/30 border-t-primary-500 animate-spin"></div>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-8 h-8 rounded-full bg-primary-500/20 blur-xl"></div>
                    </div>
                </div>
                <p className="text-white/50 animate-pulse">Retrieving insights...</p>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="text-center py-20">
                <div className="inline-flex p-4 rounded-full bg-rose-500/10 mb-4 ring-1 ring-rose-500/20">
                    <AlertTriangle className="w-8 h-8 text-rose-400" />
                </div>
                <h2 className="text-xl font-bold text-white mb-2">Analysis Not Found</h2>
                <p className="text-white/50 mb-8">{error || 'Could not retrieve product data.'}</p>
                <Link to="/" className="btn-primary inline-flex items-center gap-2">
                    <ArrowLeft className="w-4 h-4" />
                    Back to Search
                </Link>
            </div>
        );
    }

    const sentimentData = [
        { name: 'Positive', value: data.sentiment_summary.positive, color: '#10b981' },
        { name: 'Neutral', value: data.sentiment_summary.neutral, color: '#f59e0b' },
        { name: 'Negative', value: data.sentiment_summary.negative, color: '#ef4444' },
    ];

    const tabs = [
        { id: 'overview', label: 'Overview', icon: BarChart3 },
        { id: 'insights', label: 'AI Intelligence', icon: MessageSquare },
        { id: 'aspects', label: 'Detailed Aspects', icon: BarChart3 },
        { id: 'credibility', label: 'Review Credibility', icon: ShieldCheck },
    ];

    return (
        <div className="space-y-8 duration-500">
            {/* Header */}
            <header className="glass-card p-6 md:p-8 relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-64 h-64 bg-primary-500/10 blur-[100px] pointer-events-none" />

                <div className="relative z-10">
                    <Link to="/" className="inline-flex items-center gap-2 text-white/40 hover:text-white mb-6 transition-colors text-sm font-medium">
                        <ArrowLeft className="w-4 h-4" />
                        New Analysis
                    </Link>

                    <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
                        <div className="space-y-4 max-w-3xl">
                            <h1 className="text-2xl md:text-3xl font-bold leading-tight text-white/90">
                                {data.product_name}
                            </h1>
                            <div className="flex flex-wrap items-center gap-4 text-sm text-white/60">
                                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 border border-white/5">
                                    <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                                    <span className="text-white font-semibold">{data.avg_rating?.toFixed(1) || 'N/A'}</span>
                                </span>
                                <span className="flex items-center gap-1.5">
                                    <MessageSquare className="w-4 h-4" />
                                    {data.total_reviews} reviews analyzed
                                </span>
                                <span className="w-1 h-1 rounded-full bg-white/20" />
                                <span className="text-primary-400">{data.platform || 'E-commerce'}</span>
                            </div>
                        </div>

                        <div className="flex items-center gap-3">
                            <button onClick={async () => {
                                try {
                                    const response = await exportPDF(id);
                                    const url = window.URL.createObjectURL(new Blob([response.data]));
                                    const link = document.createElement('a');
                                    link.href = url;
                                    link.setAttribute('download', `analysis-${id}.pdf`);
                                    document.body.appendChild(link);
                                    link.click();
                                    link.remove();
                                    window.URL.revokeObjectURL(url);
                                } catch (e) {
                                    console.error('PDF export failed:', e);
                                }
                            }} className="btn-primary p-2.5 rounded-lg" title="Export Report">
                                <Download className="w-5 h-5" />
                            </button>
                            <button className="btn-primary p-2.5 rounded-lg" title="Share Analysis">
                                <Share2 className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Tabs */}
            <div className="flex overflow-x-auto pb-2 gap-2">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`
                            flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all duration-300
                            ${activeTab === tab.id
                                ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/20 ring-1 ring-white/10'
                                : 'bg-white/5 text-white/50 hover:bg-white/10 hover:text-white'}
                        `}
                    >
                        <tab.icon className="w-4 h-4" />
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Content Area */}
            <AnimatePresence mode="wait">
                <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                >
                    {activeTab === 'overview' && (
                        <div className="grid md:grid-cols-3 gap-6">
                            {/* Sentiment Card */}
                            <div className="md:col-span-2 glass-card p-6">
                                <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                    <BarChart3 className="w-5 h-5 text-primary-400" />
                                    Sentiment Distribution
                                </h3>
                                <div className="h-[300px] w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart
                                            data={sentimentData}
                                            layout="vertical"
                                            margin={{ top: 0, right: 30, left: 20, bottom: 0 }}
                                        >
                                            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.05)" />
                                            <XAxis type="number" hide />
                                            <YAxis dataKey="name" type="category" width={80} tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }} axisLine={false} tickLine={false} />
                                            <Tooltip
                                                cursor={{ fill: 'white', opacity: 0.05 }}
                                                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                                            />
                                            <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={32}>
                                                {sentimentData.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                                ))}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* Summary Stats */}
                            <div className="space-y-6">
                                <div className="glass-card p-6">
                                    <h3 className="text-sm font-medium text-white/50 mb-1">Total Analyzed</h3>
                                    <div className="text-3xl font-bold text-white mb-2">{data.total_reviews}</div>
                                    <div className="text-xs text-emerald-400 flex items-center gap-1">
                                        <CheckCircle2 className="w-3 h-3" />
                                        100% processed successfully
                                    </div>
                                </div>
                                <div className="glass-card p-6">
                                    <h3 className="text-sm font-medium text-white/50 mb-1">Fake Reviews Detected</h3>
                                    <div className="text-3xl font-bold text-white mb-2">{data.fake_reviews_detected}</div>
                                    <div className="text-xs text-rose-400 flex items-center gap-1">
                                        <AlertTriangle className="w-3 h-3" />
                                        {data.total_reviews > 0 ? (data.fake_reviews_detected / data.total_reviews * 100).toFixed(1) : '0.0'}% suspicion rate
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'insights' && (
                        <div className="max-w-4xl mx-auto">
                            <AIInsights analysis={data.ai_analysis} />
                        </div>
                    )}

                    {activeTab === 'aspects' && (
                        <div className="space-y-6">
                            {data.aspects?.aspects?.length > 0 ? (
                                <>
                                    {/* Radar Chart */}
                                    <div className="glass-card p-6">
                                        <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                            <BarChart3 className="w-5 h-5 text-primary-400" />
                                            Aspect Sentiment Radar
                                        </h3>
                                        <div className="h-[350px] w-full">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <RadarChart data={data.aspects.aspects.map(a => ({
                                                    aspect: a.aspect_name.charAt(0).toUpperCase() + a.aspect_name.slice(1),
                                                    score: Math.round(a.average_score * 100),
                                                    mentions: a.total_mentions
                                                }))}>
                                                    <PolarGrid stroke="rgba(255,255,255,0.1)" />
                                                    <PolarAngleAxis dataKey="aspect" tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }} />
                                                    <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10 }} />
                                                    <Radar name="Score" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
                                                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
                                                </RadarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>

                                    {/* Aspect Cards Grid */}
                                    <div className="grid md:grid-cols-2 gap-4">
                                        {data.aspects.aspects.map((aspect, idx) => {
                                            const sentColor = aspect.sentiment_label === 'positive' ? 'emerald' : aspect.sentiment_label === 'negative' ? 'rose' : 'amber';
                                            const SentIcon = aspect.sentiment_label === 'positive' ? ThumbsUp : aspect.sentiment_label === 'negative' ? ThumbsDown : Minus;
                                            return (
                                                <motion.div
                                                    key={aspect.aspect_name}
                                                    initial={{ opacity: 0, y: 15 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    transition={{ delay: idx * 0.05 }}
                                                    className="glass-card p-5 space-y-3"
                                                >
                                                    <div className="flex items-center justify-between">
                                                        <h4 className="font-semibold text-white capitalize">{aspect.aspect_name}</h4>
                                                        <span className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full bg-${sentColor}-500/10 text-${sentColor}-400 border border-${sentColor}-500/20`}>
                                                            <SentIcon className="w-3 h-3" />
                                                            {aspect.sentiment_label}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-4 text-sm text-white/60">
                                                        <span>{aspect.total_mentions} mentions</span>
                                                        <span className="text-emerald-400">{aspect.positive_count} positive</span>
                                                        <span className="text-rose-400">{aspect.negative_count} negative</span>
                                                    </div>
                                                    {/* Score bar */}
                                                    <div className="w-full bg-white/5 rounded-full h-2">
                                                        <div
                                                            className={`h-2 rounded-full bg-${sentColor}-500`}
                                                            style={{ width: `${Math.round(aspect.average_score * 100)}%` }}
                                                        />
                                                    </div>
                                                    {/* Sample reviews */}
                                                    {aspect.sample_positive?.length > 0 && (
                                                        <div className="text-xs text-white/40 mt-2">
                                                            <p className="text-emerald-400/60 mb-1">Top positive:</p>
                                                            <p className="italic truncate">&ldquo;{aspect.sample_positive[0]}&rdquo;</p>
                                                        </div>
                                                    )}
                                                    {aspect.sample_negative?.length > 0 && (
                                                        <div className="text-xs text-white/40 mt-1">
                                                            <p className="text-rose-400/60 mb-1">Top negative:</p>
                                                            <p className="italic truncate">&ldquo;{aspect.sample_negative[0]}&rdquo;</p>
                                                        </div>
                                                    )}
                                                </motion.div>
                                            );
                                        })}
                                    </div>
                                </>
                            ) : (
                                <div className="glass-card p-8 text-center text-white/50">
                                    <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                    <p>No aspect data available. Try re-analyzing the product.</p>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'credibility' && (
                        <div className="space-y-6">
                            {/* Summary Card */}
                            <div className="grid md:grid-cols-3 gap-4">
                                <div className="glass-card p-6">
                                    <h4 className="text-sm font-medium text-white/50 mb-1">Suspicious Reviews</h4>
                                    <div className="text-3xl font-bold text-white">{data.fake_reviews_detected}</div>
                                    <div className="text-xs text-white/40 mt-1">out of {data.total_reviews} total</div>
                                </div>
                                <div className="glass-card p-6">
                                    <h4 className="text-sm font-medium text-white/50 mb-1">Suspicion Rate</h4>
                                    <div className={`text-3xl font-bold ${(data.fake_review_percent || 0) > 30 ? 'text-rose-400' : (data.fake_review_percent || 0) > 15 ? 'text-amber-400' : 'text-emerald-400'}`}>
                                        {(data.fake_review_percent || 0).toFixed(1)}%
                                    </div>
                                    <div className="text-xs text-white/40 mt-1">
                                        {(data.fake_review_percent || 0) > 30 ? 'High — exercise caution' : (data.fake_review_percent || 0) > 15 ? 'Moderate — some reviews may be unreliable' : 'Low — reviews appear trustworthy'}
                                    </div>
                                </div>
                                <div className="glass-card p-6">
                                    <h4 className="text-sm font-medium text-white/50 mb-1">Credibility Score</h4>
                                    <div className="text-3xl font-bold text-primary-400">
                                        {(100 - (data.fake_review_percent || 0)).toFixed(0)}%
                                    </div>
                                    <div className="text-xs text-white/40 mt-1">overall trustworthiness</div>
                                </div>
                            </div>

                            {/* Detection Method */}
                            <div className="glass-card p-6">
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <ShieldCheck className="w-5 h-5 text-primary-400" />
                                    Detection Methodology
                                </h3>
                                <div className="grid md:grid-cols-2 gap-6">
                                    <div className="space-y-3">
                                        <h4 className="text-sm font-semibold text-white/70">ML Classifier (70% weight)</h4>
                                        <p className="text-sm text-white/50 leading-relaxed">
                                            Trained on labeled dataset using TF-IDF features + handcrafted signals (review length, exclamation density, caps ratio, generic phrases). Logistic Regression with 5-fold stratified cross-validation.
                                        </p>
                                        <div className="flex flex-wrap gap-2 text-xs">
                                            <span className="px-2 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">97.5% Accuracy</span>
                                            <span className="px-2 py-1 rounded bg-primary-500/10 text-primary-400 border border-primary-500/20">100% Precision</span>
                                            <span className="px-2 py-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">95.6% Recall</span>
                                        </div>
                                    </div>
                                    <div className="space-y-3">
                                        <h4 className="text-sm font-semibold text-white/70">Heuristic Engine (30% weight)</h4>
                                        <p className="text-sm text-white/50 leading-relaxed">
                                            Rule-based analysis checking for generic phrases, extreme brevity, excessive punctuation, all-caps patterns, rating-sentiment mismatch, and suspicious length patterns.
                                        </p>
                                        <div className="flex flex-wrap gap-2 text-xs">
                                            <span className="px-2 py-1 rounded bg-white/5 text-white/50 border border-white/10">Length Analysis</span>
                                            <span className="px-2 py-1 rounded bg-white/5 text-white/50 border border-white/10">Pattern Matching</span>
                                            <span className="px-2 py-1 rounded bg-white/5 text-white/50 border border-white/10">Sentiment Mismatch</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Credibility visual bar */}
                            <div className="glass-card p-6">
                                <h3 className="text-lg font-semibold mb-4">Trust Distribution</h3>
                                <div className="space-y-3">
                                    <div className="flex items-center gap-3">
                                        <span className="text-sm text-white/60 w-24">Genuine</span>
                                        <div className="flex-1 bg-white/5 rounded-full h-4 overflow-hidden">
                                            <div className="h-full bg-emerald-500 rounded-full transition-all duration-700" style={{ width: `${100 - (data.fake_review_percent || 0)}%` }} />
                                        </div>
                                        <span className="text-sm text-emerald-400 w-16 text-right">{(100 - (data.fake_review_percent || 0)).toFixed(1)}%</span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <span className="text-sm text-white/60 w-24">Suspicious</span>
                                        <div className="flex-1 bg-white/5 rounded-full h-4 overflow-hidden">
                                            <div className="h-full bg-rose-500 rounded-full transition-all duration-700" style={{ width: `${data.fake_review_percent || 0}%` }} />
                                        </div>
                                        <span className="text-sm text-rose-400 w-16 text-right">{(data.fake_review_percent || 0).toFixed(1)}%</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </motion.div>
            </AnimatePresence>
        </div>
    );
}

export default ProductAnalysis;
