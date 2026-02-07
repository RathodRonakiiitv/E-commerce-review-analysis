import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
    GitCompare, Plus, Trash2, BarChart3, Star,
    TrendingUp, Loader2, AlertTriangle, Search
} from 'lucide-react';
import {
    RadarChart, Radar, PolarGrid, PolarAngleAxis,
    PolarRadiusAxis, ResponsiveContainer, Tooltip, Legend
} from 'recharts';
import { getProducts, compareProducts } from '../services/api';

const COLORS = ['#0ea5e9', '#d946ef', '#10b981'];

function CompareProducts() {
    const [products, setProducts] = useState([]);
    const [selectedIds, setSelectedIds] = useState([]);
    const [comparison, setComparison] = useState(null);
    const [loading, setLoading] = useState(true);
    const [comparing, setComparing] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        loadProducts();
    }, []);

    const loadProducts = async () => {
        try {
            const { data } = await getProducts(1, 50);
            setProducts(data.items);
        } catch (err) {
            setError('Failed to load products');
        } finally {
            setLoading(false);
        }
    };

    const toggleProduct = (id) => {
        if (selectedIds.includes(id)) {
            setSelectedIds(selectedIds.filter(i => i !== id));
        } else if (selectedIds.length < 3) {
            setSelectedIds([...selectedIds, id]);
        }
    };

    const handleCompare = async () => {
        if (selectedIds.length < 2) {
            setError('Please select at least 2 products');
            return;
        }

        setComparing(true);
        setError('');

        try {
            const { data } = await compareProducts(selectedIds);
            setComparison(data);
        } catch (err) {
            setError('Failed to compare products');
        } finally {
            setComparing(false);
        }
    };

    // Prepare radar data
    const getRadarData = () => {
        if (!comparison) return [];

        const allAspects = new Set();
        comparison.products.forEach(p => {
            Object.keys(p.aspects || {}).forEach(a => allAspects.add(a));
        });

        return Array.from(allAspects).map(aspect => {
            const data = { aspect };
            comparison.products.forEach((p, i) => {
                data[`Product ${i + 1}`] = Math.round((p.aspects[aspect] || 0) * 100);
            });
            return data;
        });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[50vh]">
                <Loader2 className="w-12 h-12 animate-spin text-primary-500" />
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-3">
                        <GitCompare className="w-8 h-8 text-accent-500" />
                        Compare Products
                    </h1>
                    <p className="text-white/60 mt-2">Select 2-3 products to compare their analysis</p>
                </div>
                <button
                    onClick={handleCompare}
                    disabled={selectedIds.length < 2 || comparing}
                    className="btn-primary flex items-center gap-2 disabled:opacity-50"
                >
                    {comparing ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                        <BarChart3 className="w-5 h-5" />
                    )}
                    Compare ({selectedIds.length})
                </button>
            </div>

            {error && (
                <div className="flex items-center gap-2 text-rose-400 bg-rose-500/10 px-4 py-3 rounded-lg">
                    <AlertTriangle className="w-5 h-5" />
                    {error}
                </div>
            )}

            {/* Product Selection */}
            {products.length === 0 ? (
                <div className="glass-card p-12 text-center space-y-4">
                    <Search className="w-12 h-12 text-white/40 mx-auto" />
                    <h3 className="text-xl font-semibold">No Products Yet</h3>
                    <p className="text-white/60">Analyze some products first to compare them</p>
                    <Link to="/" className="btn-primary inline-flex items-center gap-2">
                        <Plus className="w-5 h-5" />
                        Analyze Product
                    </Link>
                </div>
            ) : (
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {products.map((product) => {
                        const isSelected = selectedIds.includes(product.id);
                        const isDisabled = !isSelected && selectedIds.length >= 3;

                        return (
                            <button
                                key={product.id}
                                onClick={() => toggleProduct(product.id)}
                                disabled={isDisabled}
                                className={`glass-card p-4 text-left transition-all duration-200 
                  ${isSelected ? 'ring-2 ring-primary-500 bg-primary-500/10' : ''}
                  ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-white/10'}
                `}
                            >
                                <div className="flex items-start justify-between mb-2">
                                    <h3 className="font-medium line-clamp-2 flex-1">
                                        {product.name || 'Unnamed Product'}
                                    </h3>
                                    {isSelected && (
                                        <div className="w-6 h-6 rounded-full bg-primary-500 flex items-center justify-center text-sm font-bold ml-2 flex-shrink-0">
                                            {selectedIds.indexOf(product.id) + 1}
                                        </div>
                                    )}
                                </div>
                                <div className="flex items-center gap-4 text-sm text-white/60">
                                    <span className="flex items-center gap-1">
                                        <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                                        {product.avg_rating?.toFixed(1) || '-'}
                                    </span>
                                    <span>{product.total_reviews || 0} reviews</span>
                                </div>
                            </button>
                        );
                    })}
                </div>
            )}

            {/* Comparison Results */}
            {comparison && (
                <div className="space-y-6 mt-8">
                    <h2 className="text-2xl font-bold">Comparison Results</h2>

                    {/* Overview Cards */}
                    <div className="grid md:grid-cols-3 gap-4">
                        {comparison.products.map((product, i) => (
                            <div
                                key={product.product_id}
                                className={`glass-card p-6 ${product.product_id === comparison.best_overall ? 'ring-2 ring-emerald-500' : ''}`}
                            >
                                {product.product_id === comparison.best_overall && (
                                    <div className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-xs mb-3">
                                        <TrendingUp className="w-3 h-3" />
                                        Best Overall
                                    </div>
                                )}
                                <h3 className="font-semibold mb-2 line-clamp-2">{product.product_name || `Product ${i + 1}`}</h3>
                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <span className="text-white/60">Score</span>
                                        <span className="font-bold" style={{ color: COLORS[i] }}>{product.overall_score.toFixed(0)}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-white/60">Rating</span>
                                        <span className="flex items-center gap-1">
                                            {product.avg_rating.toFixed(1)}
                                            <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-white/60">Reviews</span>
                                        <span>{product.total_reviews}</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Aspect Comparison Radar */}
                    <div className="glass-card p-6">
                        <h3 className="text-lg font-semibold mb-4">Aspect Comparison</h3>
                        <ResponsiveContainer width="100%" height={400}>
                            <RadarChart data={getRadarData()}>
                                <PolarGrid stroke="#ffffff20" />
                                <PolarAngleAxis dataKey="aspect" stroke="#ffffff60" />
                                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#ffffff20" />
                                {comparison.products.map((_, i) => (
                                    <Radar
                                        key={i}
                                        name={`Product ${i + 1}`}
                                        dataKey={`Product ${i + 1}`}
                                        stroke={COLORS[i]}
                                        fill={COLORS[i]}
                                        fillOpacity={0.2}
                                    />
                                ))}
                                <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '8px' }} />
                                <Legend />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Aspect Winners */}
                    <div className="glass-card p-6">
                        <h3 className="text-lg font-semibold mb-4">Aspect Winners</h3>
                        <div className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            {Object.entries(comparison.aspect_winners).map(([aspect, winnerId]) => {
                                const winnerIndex = comparison.products.findIndex(p => p.product_id === winnerId);
                                return (
                                    <div key={aspect} className="bg-white/5 rounded-xl p-4">
                                        <div className="text-white/60 text-sm capitalize mb-1">{aspect}</div>
                                        <div className="font-semibold" style={{ color: COLORS[winnerIndex] }}>
                                            Product {winnerIndex + 1}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default CompareProducts;
