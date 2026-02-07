import { useState } from 'react';
import { Sparkles, Loader2, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react';
import { getAISummary, getAspectDeepDive, suggestReviewResponse } from '../services/api';

function AIInsights({ productId, productName }) {
    const [loading, setLoading] = useState(false);
    const [summary, setSummary] = useState(null);
    const [error, setError] = useState('');
    const [expanded, setExpanded] = useState(true);

    const generateSummary = async () => {
        setLoading(true);
        setError('');

        try {
            const { data } = await getAISummary(productId);
            if (data.error) {
                setError(data.error);
            } else {
                setSummary(data.summary);
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to generate AI summary');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-card p-6">
            <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpanded(!expanded)}
            >
                <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-accent-400" style={{ color: '#d946ef' }} />
                    AI-Powered Insights
                    <span className="text-xs px-2 py-0.5 rounded-full bg-accent-500/20 text-accent-400" style={{ backgroundColor: 'rgba(217, 70, 239, 0.2)', color: '#e879f9' }}>
                        Groq
                    </span>
                </h3>
                {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </div>

            {expanded && (
                <div className="mt-4 space-y-4">
                    {!summary && !loading && (
                        <div className="text-center py-6">
                            <Sparkles className="w-12 h-12 mx-auto mb-3" style={{ color: 'rgba(255,255,255,0.3)' }} />
                            <p className="text-white/60 mb-4">
                                Get AI-powered analysis with executive summary, key strengths, weaknesses, and recommendations.
                            </p>
                            <button
                                onClick={generateSummary}
                                className="btn-primary inline-flex items-center gap-2"
                            >
                                <Sparkles className="w-5 h-5" />
                                Generate AI Summary
                            </button>
                        </div>
                    )}

                    {loading && (
                        <div className="text-center py-8">
                            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3" style={{ color: '#d946ef' }} />
                            <p className="text-white/60">Analyzing reviews with Llama 3.1...</p>
                        </div>
                    )}

                    {error && (
                        <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4 text-rose-400">
                            <p className="font-medium">Error</p>
                            <p className="text-sm">{error}</p>
                            {error.includes('API key') && (
                                <p className="text-xs mt-2 text-white/50">
                                    Add your Groq API key to backend/.env as GROQ_API_KEY
                                </p>
                            )}
                        </div>
                    )}

                    {summary && (
                        <div className="space-y-4">
                            <div
                                className="prose prose-invert max-w-none text-white/80"
                                style={{ lineHeight: '1.7' }}
                            >
                                {summary.split('\n').map((line, i) => {
                                    if (line.startsWith('**') && line.endsWith('**')) {
                                        return <h4 key={i} className="text-white font-semibold mt-4 mb-2">{line.replace(/\*\*/g, '')}</h4>;
                                    }
                                    if (line.startsWith('- ')) {
                                        return <p key={i} className="ml-4 flex items-start gap-2">
                                            <span className="text-accent-400" style={{ color: '#e879f9' }}>•</span>
                                            {line.substring(2)}
                                        </p>;
                                    }
                                    if (line.trim()) {
                                        return <p key={i} className="mb-2">{line}</p>;
                                    }
                                    return null;
                                })}
                            </div>

                            <button
                                onClick={generateSummary}
                                className="btn-secondary text-sm flex items-center gap-2"
                            >
                                <Sparkles className="w-4 h-4" />
                                Regenerate
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default AIInsights;
