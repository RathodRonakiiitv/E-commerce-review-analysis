import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    ArrowLeft, RefreshCw, Download, FileText, AlertTriangle,
    TrendingUp, TrendingDown, Minus, Star, MessageSquare, Loader2
} from 'lucide-react';
import {
    PieChart, Pie, Cell, ResponsiveContainer,
    BarChart, Bar, XAxis, YAxis, Tooltip,
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import {
    getProduct, getInsights, getAspectAnalysis, getTopicAnalysis,
    getProductReviews, exportPDF, exportCSV, reanalyzeProduct
} from '../services/api';
import AIInsights from '../components/AIInsights';

const COLORS = {
    positive: '#10b981',
    negative: '#ef4444',
    neutral: '#f59e0b'
};

const ASPECT_COLORS = ['#0ea5e9', '#d946ef', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899'];

function ProductAnalysis() {
    const { productId } = useParams();
    const navigate = useNavigate();

    const [loading, setLoading] = useState(true);
    const [product, setProduct] = useState(null);
    const [insights, setInsights] = useState(null);
    const [aspects, setAspects] = useState(null);
    const [topics, setTopics] = useState(null);
    const [reviews, setReviews] = useState([]);
    const [error, setError] = useState('');
    const [reanalyzing, setReanalyzing] = useState(false);
    const [debugInfo, setDebugInfo] = useState('');

    useEffect(() => {
        loadData();
    }, [productId]);

    const loadData = async () => {
        setLoading(true);
        setError('');
        const debug = [];

        try {
            console.log('Loading product:', productId);

            // Load all data in parallel for speed
            const results = await Promise.allSettled([
                getProduct(productId),
                getInsights(productId),
                getAspectAnalysis(productId),
                getTopicAnalysis(productId),
                getProductReviews(productId, 1)
            ]);

            const [productRes, insightsRes, aspectsRes, topicsRes, reviewsRes] = results;

            let productData = null;
            let insightsData = null;
            let aspectsData = null;
            let topicsData = null;
            let reviewsData = null;

            if (productRes.status === 'fulfilled') {
                productData = productRes.value.data;
                debug.push(`Product: ${productData?.name || 'loaded'} (${productData?.total_reviews} reviews)`);
            } else {
                debug.push(`Product ERROR: ${productRes.reason?.message}`);
                console.error('Product error:', productRes.reason);
            }

            if (insightsRes.status === 'fulfilled') {
                insightsData = insightsRes.value.data;
                debug.push(`Insights: score=${insightsData?.overall_score}, rating=${insightsData?.avg_rating}`);
            } else {
                debug.push(`Insights ERROR: ${insightsRes.reason?.message}`);
                console.error('Insights error:', insightsRes.reason);
            }

            if (aspectsRes.status === 'fulfilled') {
                aspectsData = aspectsRes.value.data;
                debug.push(`Aspects: ${aspectsData?.aspects?.length || 0} found`);
            } else {
                debug.push(`Aspects ERROR: ${aspectsRes.reason?.message}`);
                console.error('Aspects error:', aspectsRes.reason);
            }

            if (topicsRes.status === 'fulfilled') {
                topicsData = topicsRes.value.data;
                debug.push(`Topics: ${topicsData?.topics?.length || 0} found`);
            } else {
                debug.push(`Topics ERROR: ${topicsRes.reason?.message}`);
                console.error('Topics error:', topicsRes.reason);
            }

            if (reviewsRes.status === 'fulfilled') {
                reviewsData = reviewsRes.value.data;
                debug.push(`Reviews: ${reviewsData?.items?.length || 0} loaded`);
            } else {
                debug.push(`Reviews ERROR: ${reviewsRes.reason?.message}`);
                console.error('Reviews error:', reviewsRes.reason);
            }

            setProduct(productData);
            setInsights(insightsData);
            setAspects(aspectsData);
            setTopics(topicsData);
            setReviews(reviewsData?.items || []);

        } catch (err) {
            setError('Failed to load analysis data: ' + err.message);
            debug.push(`FATAL: ${err.message}`);
            console.error('Load error:', err);
        } finally {
            setDebugInfo(debug.join(' | '));
            setLoading(false);
        }
    };

    const handleReanalyze = async () => {
        setReanalyzing(true);
        try {
            await reanalyzeProduct(productId);
            setTimeout(loadData, 3000);
        } catch (err) {
            setError('Failed to start re-analysis');
        } finally {
            setReanalyzing(false);
        }
    };

    const handleExportPDF = async () => {
        try {
            const response = await exportPDF(productId);
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.download = `analysis_${productId}.pdf`;
            link.click();
        } catch (err) {
            setError('Failed to export PDF');
        }
    };

    const handleExportCSV = async () => {
        try {
            const response = await exportCSV(productId);
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.download = `reviews_${productId}.csv`;
            link.click();
        } catch (err) {
            setError('Failed to export CSV');
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[50vh]">
                <div className="text-center space-y-4">
                    <Loader2 className="w-12 h-12 animate-spin text-cyan-500 mx-auto" />
                    <p className="text-white/60">Loading analysis...</p>
                    <p className="text-white/40 text-sm">{debugInfo}</p>
                </div>
            </div>
        );
    }

    if (error && !product) {
        return (
            <div className="glass-card p-8 text-center space-y-4">
                <AlertTriangle className="w-12 h-12 text-rose-400 mx-auto" />
                <p className="text-rose-400">{error}</p>
                <p className="text-white/40 text-sm">Debug: {debugInfo}</p>
                <button onClick={() => navigate('/')} className="btn-secondary">
                    Go Back
                </button>
            </div>
        );
    }

    // Helper to safely convert values that might be strings (Decimal) to numbers
    const toNum = (val, fallback = 0) => {
        if (val == null) return fallback;
        const n = Number(val);
        return isNaN(n) ? fallback : n;
    };

    // Prepare chart data with fallbacks
    const sentimentData = insights?.sentiment_distribution ? [
        { name: 'Positive', value: toNum(insights.sentiment_distribution.positive), color: COLORS.positive },
        { name: 'Negative', value: toNum(insights.sentiment_distribution.negative), color: COLORS.negative },
        { name: 'Neutral', value: toNum(insights.sentiment_distribution.neutral), color: COLORS.neutral }
    ] : [];

    const ratingData = insights?.rating_distribution ? Object.entries(insights.rating_distribution)
        .map(([rating, count]) => ({ rating: `${rating}★`, count: toNum(count) }))
        .sort((a, b) => b.rating.localeCompare(a.rating)) : [];

    const aspectData = aspects?.aspects?.slice(0, 8).map((a) => ({
        aspect: a.aspect_name,
        score: Math.round(toNum(a.average_score, 0.5) * 100),
        fullMark: 100
    })) || [];

    return (
        <div className="space-y-8">
            {/* Debug Info */}
            {debugInfo && (
                <div className="bg-blue-900/30 border border-blue-500/50 rounded-lg p-3 text-sm text-blue-300">
                    Debug: {debugInfo}
                </div>
            )}

            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                    <button onClick={() => navigate('/')} className="btn-secondary p-2">
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold truncate max-w-xl">
                            {product?.name || 'Product Analysis'}
                        </h1>
                        <p className="text-white/60 text-sm">{toNum(product?.total_reviews, toNum(insights?.total_reviews, 0))} reviews analyzed</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button onClick={handleReanalyze} disabled={reanalyzing} className="btn-secondary flex items-center gap-2">
                        <RefreshCw className={`w-4 h-4 ${reanalyzing ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                    <button onClick={handleExportPDF} className="btn-secondary flex items-center gap-2">
                        <Download className="w-4 h-4" />
                        PDF
                    </button>
                    <button onClick={handleExportCSV} className="btn-secondary flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        CSV
                    </button>
                </div>
            </div>

            {/* Score Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="stat-card">
                    <div className="text-4xl font-bold text-gradient">{toNum(insights?.overall_score, toNum(product?.avg_rating, 0) * 20).toFixed(0)}</div>
                    <div className="text-white/60 text-sm mt-2">Overall Score</div>
                </div>
                <div className="stat-card">
                    <div className="flex items-center gap-1 text-4xl font-bold text-amber-400">
                        {toNum(insights?.avg_rating, toNum(product?.avg_rating, 0)).toFixed(1)}
                        <Star className="w-6 h-6 fill-amber-400" />
                    </div>
                    <div className="text-white/60 text-sm mt-2">Avg Rating</div>
                </div>
                <div className="stat-card">
                    <div className="text-4xl font-bold text-emerald-400">
                        {toNum(insights?.sentiment_distribution?.positive_percent, 0).toFixed(0)}%
                    </div>
                    <div className="text-white/60 text-sm mt-2">Positive</div>
                </div>
                <div className="stat-card">
                    <div className="text-4xl font-bold text-rose-400">
                        {toNum(insights?.fake_review_percent, 0).toFixed(0)}%
                    </div>
                    <div className="text-white/60 text-sm mt-2">Suspicious</div>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid lg:grid-cols-3 gap-6">
                {/* Sentiment Pie */}
                <div className="glass-card p-6">
                    <h3 className="text-lg font-semibold mb-4">Sentiment Distribution</h3>
                    {sentimentData.length > 0 && sentimentData.some(d => d.value > 0) ? (
                        <>
                            <ResponsiveContainer width="100%" height={250}>
                                <PieChart>
                                    <Pie
                                        data={sentimentData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={90}
                                        paddingAngle={3}
                                        dataKey="value"
                                    >
                                        {sentimentData.map((entry, index) => (
                                            <Cell key={index} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '8px' }} />
                                </PieChart>
                            </ResponsiveContainer>
                            <div className="flex justify-center gap-4 mt-4">
                                {sentimentData.map((item, i) => (
                                    <div key={i} className="flex items-center gap-2 text-sm">
                                        <div className="w-3 h-3 rounded-full" style={{ background: item.color }} />
                                        {item.name}: {item.value}
                                    </div>
                                ))}
                            </div>
                        </>
                    ) : (
                        <p className="text-white/40 text-center py-16">No sentiment data available</p>
                    )}
                </div>

                {/* Rating Bar */}
                <div className="glass-card p-6">
                    <h3 className="text-lg font-semibold mb-4">Rating Distribution</h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={ratingData} layout="vertical">
                            <XAxis type="number" stroke="#ffffff40" />
                            <YAxis type="category" dataKey="rating" stroke="#ffffff40" width={40} />
                            <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '8px' }} />
                            <Bar dataKey="count" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Aspect Radar */}
                <div className="glass-card p-6">
                    <h3 className="text-lg font-semibold mb-4">Aspect Scores</h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <RadarChart data={aspectData}>
                            <PolarGrid stroke="#ffffff20" />
                            <PolarAngleAxis dataKey="aspect" stroke="#ffffff60" tick={{ fontSize: 10 }} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#ffffff20" />
                            <Radar
                                name="Score"
                                dataKey="score"
                                stroke="#d946ef"
                                fill="#d946ef"
                                fillOpacity={0.3}
                            />
                            <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '8px' }} />
                        </RadarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* AI Insights Section */}
            <AIInsights productId={productId} productName={product?.name || 'Product'} />

            {/* Sample Reviews */}
            <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <MessageSquare className="w-5 h-5" />
                    Recent Reviews ({reviews.length})
                </h3>
                <div className="space-y-4">
                    {reviews.length === 0 ? (
                        <p className="text-white/50 text-center py-4">No reviews to display</p>
                    ) : reviews.slice(0, 5).map((review) => (
                        <div key={review.id} className="bg-white/5 rounded-xl p-4 space-y-2">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    {[1, 2, 3, 4, 5].map((star) => (
                                        <Star
                                            key={star}
                                            className={`w-4 h-4 ${star <= review.rating ? 'text-amber-400 fill-amber-400' : 'text-white/20'}`}
                                        />
                                    ))}
                                    {review.verified_purchase && (
                                        <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 rounded text-xs">Verified</span>
                                    )}
                                </div>
                                <span className={`px-2 py-0.5 rounded text-xs ${review.sentiment_label === 'positive' ? 'bg-emerald-500/20 text-emerald-400' :
                                    review.sentiment_label === 'negative' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'
                                    }`}>
                                    {review.sentiment_label || 'neutral'}
                                </span>
                            </div>
                            <p className="text-white/80 text-sm line-clamp-3">{review.review_text}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default ProductAnalysis;
