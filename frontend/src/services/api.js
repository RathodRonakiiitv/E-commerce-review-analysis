import axios from 'axios';

const API_HOST = import.meta.env.VITE_API_URL || '';
const API_BASE_URL = `${API_HOST}/api`;

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 120000, // 2 minute timeout for cold starts
    headers: {
        'Content-Type': 'application/json',
    },
});

// Auto-retry for Render free tier cold starts
api.interceptors.response.use(null, async (error) => {
    const config = error.config;
    if (!config || config.__retryCount >= 3) return Promise.reject(error);

    const isNetworkError = !error.response || error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED';
    if (!isNetworkError) return Promise.reject(error);

    config.__retryCount = (config.__retryCount || 0) + 1;
    console.log(`⏳ Backend waking up... retry ${config.__retryCount}/3`);

    await new Promise(r => setTimeout(r, config.__retryCount * 5000));
    return api(config);
});

// Products
export const getProducts = (page = 1, pageSize = 10) =>
    api.get(`/products?page=${page}&page_size=${pageSize}`);

export const getProduct = (productId) =>
    api.get(`/products/${productId}`);

export const deleteProduct = (productId) =>
    api.delete(`/products/${productId}`);

export const getProductReviews = (productId, page = 1, filters = {}) => {
    const params = new URLSearchParams({ page, page_size: 20, ...filters });
    return api.get(`/products/${productId}/reviews?${params}`);
};

// Scraping
export const startScraping = (url, maxReviews = 200) =>
    api.post('/scrape', { url, max_reviews: maxReviews });

export const getScrapeStatus = (jobId) =>
    api.get(`/scrape/${jobId}/status`);

// Analysis
export const getSentimentAnalysis = (productId, forceRefresh = false) =>
    api.get(`/products/${productId}/sentiment?force_refresh=${forceRefresh}`);

export const getAspectAnalysis = (productId, forceRefresh = false) =>
    api.get(`/products/${productId}/aspects?force_refresh=${forceRefresh}`);

export const getTopicAnalysis = (productId, forceRefresh = false) =>
    api.get(`/products/${productId}/topics?force_refresh=${forceRefresh}`);

export const getInsights = (productId, forceRefresh = false) =>
    api.get(`/products/${productId}/insights?force_refresh=${forceRefresh}`);

export const reanalyzeProduct = (productId) =>
    api.post(`/products/${productId}/reanalyze`);

// Comparison
export const compareProducts = (productIds) =>
    api.post('/compare', { product_ids: productIds });

// Export
export const exportPDF = (productId) =>
    api.get(`/products/${productId}/export/pdf`, { responseType: 'blob' });

export const exportCSV = (productId) =>
    api.get(`/products/${productId}/export/csv`, { responseType: 'blob' });

// Aggregated Analysis (Frontend Helper)
export const getProductAnalysis = async (productId) => {
    try {
        const [productRes, insightsRes, aiRes, aspectRes, sentimentRes] = await Promise.allSettled([
            api.get(`/products/${productId}`),
            api.get(`/products/${productId}/insights`),
            api.get(`/ai/products/${productId}/ai-summary`),
            api.get(`/products/${productId}/aspects`),
            api.get(`/products/${productId}/sentiment`)
        ]);

        // Handle core data failure
        if (productRes.status === 'rejected') throw productRes.reason;
        if (insightsRes.status === 'rejected') throw insightsRes.reason;

        const product = productRes.value.data;
        const insights = insightsRes.value.data;
        const aiAnalysis = aiRes.status === 'fulfilled' ? aiRes.value.data : null;
        const aspects = aspectRes.status === 'fulfilled' ? aspectRes.value.data : null;
        const sentiment = sentimentRes.status === 'fulfilled' ? sentimentRes.value.data : null;

        return {
            data: {
                product_name: product.name,
                platform: product.platform,
                avg_rating: product.avg_rating,
                total_reviews: insights.total_reviews,
                fake_reviews_detected: insights.fake_review_count,
                fake_review_percent: insights.fake_review_percent,
                sentiment_summary: {
                    positive: insights.sentiment_distribution.positive,
                    neutral: insights.sentiment_distribution.neutral,
                    negative: insights.sentiment_distribution.negative
                },
                ai_analysis: aiAnalysis,
                aspects: aspects,
                sentiment_detail: sentiment,
                ...insights // Fallback for other fields
            }
        };
    } catch (error) {
        console.error("Error fetching product analysis:", error);
        throw error;
    }
};

// Health
export const getHealth = () => api.get('/health');
export const getStats = () => api.get('/stats');

// AI Insights (Groq)
export const getAISummary = (productId) =>
    api.get(`/ai/products/${productId}/ai-summary`);

export const getAspectDeepDive = (productId, aspect) =>
    api.post(`/ai/products/${productId}/aspect-dive`, { aspect });

export const suggestReviewResponse = (reviewText, sentiment) =>
    api.post('/ai/suggest-response', { review_text: reviewText, sentiment });

export const checkAIHealth = () => api.get('/ai/health');

export default api;
