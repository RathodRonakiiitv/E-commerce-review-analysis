import { Brain, Sparkles, AlertTriangle, Lightbulb, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

function AIInsights({ analysis }) {
    if (!analysis) return null;

    const sections = [
        {
            id: 'summary',
            title: 'Executive Summary',
            icon: Brain,
            color: 'text-primary-400',
            bg: 'bg-primary-500/10',
            border: 'border-primary-500/20',
            content: analysis.summary
        },
        {
            id: 'pros',
            title: 'Key Strengths',
            icon: CheckCircle2,
            color: 'text-emerald-400',
            bg: 'bg-emerald-500/10',
            border: 'border-emerald-500/20',
            content: analysis.pros
        },
        {
            id: 'cons',
            title: 'Critical Issues',
            icon: AlertTriangle,
            color: 'text-rose-400',
            bg: 'bg-rose-500/10',
            border: 'border-rose-500/20',
            content: analysis.cons
        },
        {
            id: 'recommendation',
            title: 'Buying Recommendation',
            icon: Lightbulb,
            color: 'text-amber-400',
            bg: 'bg-amber-500/10',
            border: 'border-amber-500/20',
            content: analysis.recommendation
        }
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-3 mb-8">
                <div className="p-3 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/20">
                    <Sparkles className="w-6 h-6 text-white" />
                </div>
                <div>
                    <h2 className="text-2xl font-bold text-white">AI Assistant Report</h2>
                    <p className="text-white/50 text-sm">Powered by Groq Llama-3 70B</p>
                </div>
            </div>

            <div className="grid gap-6">
                {sections.map((section, index) => (
                    <InsightCard key={section.id} section={section} index={index} />
                ))}
            </div>
        </div>
    );
}

function InsightCard({ section, index }) {
    const [isExpanded, setIsExpanded] = useState(true);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`glass-card overflow-hidden transition-all duration-300 ${isExpanded ? 'ring-1 ring-white/10' : 'hover:bg-white/5'
                }`}
        >
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full flex items-center justify-between p-6 text-left"
            >
                <div className="flex items-center gap-4">
                    <div className={`p-2.5 rounded-lg ${section.bg} ${section.color} border ${section.border}`}>
                        <section.icon className="w-5 h-5" />
                    </div>
                    <h3 className="text-lg font-semibold text-white/90">{section.title}</h3>
                </div>
                <div className={`p-1 rounded-full transition-colors ${isExpanded ? 'bg-white/10 text-white' : 'text-white/40 hover:bg-white/5'
                    }`}>
                    {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </div>
            </button>

            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: 'easeInOut' }}
                    >
                        <div className="px-6 pb-6 pt-0">
                            <div className="h-px w-full bg-white/5 mb-6" />
                            {Array.isArray(section.content) ? (
                                <ul className="space-y-3">
                                    {section.content.map((item, i) => (
                                        <motion.li
                                            key={i}
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: 0.1 + (i * 0.05) }}
                                            className="flex items-start gap-3 text-white/70 leading-relaxed"
                                        >
                                            <span className={`mt-2 w-1.5 h-1.5 rounded-full shrink-0 ${section.bg.replace('/10', '')}`} />
                                            <span>{item}</span>
                                        </motion.li>
                                    ))}
                                </ul>
                            ) : (
                                <p className="text-white/70 leading-relaxed whitespace-pre-line">
                                    {section.content}
                                </p>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}

export default AIInsights;
