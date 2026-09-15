import axios from 'axios'

const API_BASE_URL = '/api'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const getPriceRadarAPI = {
  // Products
  listProducts: (category = null, platform = null, limit = 50) =>
    client.get('/products', { params: { category, platform, limit } }),
  
  getProduct: (id) =>
    client.get(`/products/${id}`),
  
  getProductHistory: (id, days = 30) =>
    client.get(`/products/${id}/history`, { params: { days } }),

  // Deals
  listDeals: (category = null, minDrop = 10, limit = 20) =>
    client.get('/deals', { params: { category, min_drop: minDrop, limit } }),

  // Search
  search: (q, platform = null) =>
    client.get('/search', { params: { q, platform } }),

  // Analytics
  getKPIs: () =>
    client.get('/analytics/kpis'),
  
  getCategoryTrends: () =>
    client.get('/analytics/categories'),

  // Alerts
  createAlert: (productId, targetPrice, email) =>
    client.post('/alerts', { product_id: productId, target_price: targetPrice, email }),

  // Health
  health: () =>
    client.get('/health')
}

export default client
