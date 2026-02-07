import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
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
