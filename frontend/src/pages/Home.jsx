import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPriceRadarAPI } from '../api/client'
import { Navbar } from '../components/Navbar'
import { ProductCard } from '../components/ProductCard'

const Home = () => {
  const navigate = useNavigate()
  const [kpis, setKpis] = useState(null)
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [platform, setPlatform] = useState('all')

  useEffect(() => {
    fetchData()
  }, [selectedCategory, platform])

  const fetchData = async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch KPIs
      const kpiRes = await getPriceRadarAPI.getKPIs()
      setKpis(kpiRes.data)

      // Fetch deals - using min_drop=0 to show all products in demo
      const productsRes = await getPriceRadarAPI.listProducts(
        selectedCategory || null,
        platform === 'all' ? null : platform,
        500
        )
      setProducts(productsRes.data)

    } catch (err) {
      setError(err.message)
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Navbar />
      <main style={{ backgroundColor: '#0f172a', minHeight: '100vh', padding: '32px 0' }}>
        <div className="container">
          {/* KPI Cards */}
          {kpis && !loading && (
            <div className="grid-4 mb-6">
              <div style={{
                backgroundColor: '#1e293b',
                padding: '20px',
                borderRadius: '8px',
                border: '1px solid #334155'
              }}>
                <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '8px' }}>
                  Total Products
                </div>
                <div style={{ fontSize: '28px', fontWeight: '700', color: '#3b82f6' }}>
                  {kpis.total_products?.toLocaleString()}
                </div>
              </div>

              <div style={{
                backgroundColor: '#1e293b',
                padding: '20px',
                borderRadius: '8px',
                border: '1px solid #334155'
              }}>
                <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '8px' }}>
                  Deals Today
                </div>
                <div style={{ fontSize: '28px', fontWeight: '700', color: '#10b981' }}>
                  {kpis.deals_today}
                </div>
              </div>

              <div style={{
                backgroundColor: '#1e293b',
                padding: '20px',
                borderRadius: '8px',
                border: '1px solid #334155'
              }}>
                <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '8px' }}>
                  Avg Discount
                </div>
                <div style={{ fontSize: '28px', fontWeight: '700', color: '#f97316' }}>
                  {kpis.avg_discount_pct?.toFixed(1)}%
                </div>
              </div>

              <div style={{
                backgroundColor: '#1e293b',
                padding: '20px',
                borderRadius: '8px',
                border: '1px solid #334155'
              }}>
                <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '8px' }}>
                  Best Saving
                </div>
                <div style={{ fontSize: '28px', fontWeight: '700', color: '#a78bfa' }}>
                  ₹{kpis.best_deal_saving?.toLocaleString()}
                </div>
              </div>
            </div>
          )}

          {/* Filters */}
          <div style={{
            display: 'flex',
            gap: '16px',
            marginBottom: '32px',
            flexWrap: 'wrap'
          }}>
            <select
              value={selectedCategory || ''}
              onChange={(e) => setSelectedCategory(e.target.value || null)}
              style={{
                padding: '10px 12px',
                borderRadius: '6px',
                border: '1px solid #334155',
                backgroundColor: '#1e293b',
                color: '#e2e8f0'
              }}
            >
              <option value="">All Categories</option>
              <option value="smartphones">Smartphones</option>
              <option value="laptops">Laptops</option>
              <option value="headphones">Headphones</option>
              <option value="books">Books</option>
            </select>

            <div style={{ display: 'flex', gap: '8px' }}>
              {['All', 'Amazon', 'Flipkart'].map((p) => (
                <button
                  key={p}
                  className={`btn ${platform === p.toLowerCase() || (p === 'All' && platform === 'all') ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setPlatform(p === 'All' ? 'all' : p.toLowerCase())}
                  style={{ fontSize: '12px' }}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* Products Grid */}
          {loading ? (
            <div className="grid-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="skeleton" style={{ height: '300px', borderRadius: '8px' }} />
              ))}
            </div>
          ) : error ? (
            <div className="error-state">
              <h3>Failed to load deals</h3>
              <p>{error}</p>
              <button className="btn btn-primary" onClick={fetchData}>
                Try Again
              </button>
            </div>
          ) : products.length === 0 ? (
            <div className="error-state">
              <h3>No deals found</h3>
              <p>Try a different category or platform</p>
            </div>
          ) : (
            <div className="grid-3">
              {products.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onViewDetails={(id) => navigate(`/products/${id}`)}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </>
  )
}

export default Home
