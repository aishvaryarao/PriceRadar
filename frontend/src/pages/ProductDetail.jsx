import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getPriceRadarAPI } from '../api/client'
import { Navbar } from '../components/Navbar'
import { PriceChart } from '../components/PriceChart'
import { DealBadge } from '../components/DealBadge'

const ProductDetail = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const [product, setProduct] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [alert, setAlert] = useState({ email: '', targetPrice: '' })
  const [alertMessage, setAlertMessage] = useState(null)
  const [historyDays, setHistoryDays] = useState(30)
  const [comparisons, setComparisons] = useState([])
  const [imageError, setImageError] = useState(false)

  useEffect(() => {
    fetchData()
  }, [id, historyDays])

  const fetchData = async () => {
    setLoading(true)
    setError(null)

    try {
      const productRes = await getPriceRadarAPI.getProduct(id)
      setProduct(productRes.data)

      const historyRes = await getPriceRadarAPI.getProductHistory(id, historyDays)
      setHistory(historyRes.data)
      
      // Fetch comparisons (same product on different platforms)
      if (productRes.data?.name) {
        try {
          const searchRes = await getPriceRadarAPI.search(productRes.data.name)
          setComparisons(searchRes.data || [])
        } catch (e) {
          // Comparison search failed, continue without it
        }
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateAlert = async (e) => {
    e.preventDefault()

    if (!alert.email || !alert.targetPrice) {
      setAlertMessage({ type: 'error', text: 'Please fill all fields' })
      return
    }

    try {
      await getPriceRadarAPI.createAlert(parseInt(id), parseInt(alert.targetPrice), alert.email)
      setAlertMessage({ type: 'success', text: 'Alert created successfully!' })
      setAlert({ email: '', targetPrice: '' })

      setTimeout(() => setAlertMessage(null), 3000)
    } catch (err) {
      setAlertMessage({ type: 'error', text: err.message })
    }
  }

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="flex-center" style={{ height: '80vh', color: '#94a3b8' }}>
          Loading...
        </div>
      </>
    )
  }

  if (error || !product) {
    return (
      <>
        <Navbar />
        <div className="container" style={{ marginTop: '40px' }}>
          <div className="error-state">
            <h3>Failed to load product</h3>
            <p>{error}</p>
            <button className="btn btn-primary" onClick={() => navigate('/')}>
              Back to Home
            </button>
          </div>
        </div>
      </>
    )
  }

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(price)
  }

  return (
    <>
      <Navbar />
      <main style={{ backgroundColor: '#0f172a', minHeight: '100vh', padding: '32px 0' }}>
        <div className="container">
          {/* Breadcrumb */}
          <div style={{ marginBottom: '24px', color: '#64748b' }}>
            <a href="/">Home</a> / <span>{product.name}</span>
          </div>

          {/* Product Section */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '40px', marginBottom: '40px' }}>
            {/* Left: Image & Info */}
            <div>
              {/* Image */}
              <div style={{
                backgroundColor: '#1e293b',
                aspectRatio: '1',
                borderRadius: '12px',
                marginBottom: '24px',
                overflow: 'hidden',
                border: '1px solid #334155',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {product.image_url && !imageError ? (
                  <img
                    src={product.image_url}
                    alt={product.name}
                    onError={() => setImageError(true)}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                ) : (
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#64748b',
                    gap: '12px',
                    textAlign: 'center'
                  }}>
                    <div style={{ fontSize: '48px' }}>📦</div>
                    <div style={{ fontSize: '14px' }}>{product.category || 'Product'}</div>
                  </div>
                )}
              </div>

              {/* Info Card */}
              <div style={{
                backgroundColor: '#1e293b',
                padding: '24px',
                borderRadius: '12px',
                border: '1px solid #334155'
              }}>
                <h1 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '16px', color: '#e2e8f0' }}>
                  {product.name}
                </h1>

                {product.brand && (
                  <div style={{ marginBottom: '16px' }}>
                    <span style={{ color: '#94a3b8' }}>Brand:</span> <span style={{ color: '#e2e8f0' }}>{product.brand}</span>
                  </div>
                )}

                {product.category && (
                  <div style={{ marginBottom: '16px' }}>
                    <span style={{ color: '#94a3b8' }}>Category:</span> <span style={{ color: '#e2e8f0' }}>{product.category}</span>
                  </div>
                )}

                <div style={{ marginBottom: '16px' }}>
                  <span className="badge badge-orange">{product.platform?.toUpperCase()}</span>
                </div>

                {/* Price */}
                <div style={{
                  fontSize: '32px',
                  fontWeight: '700',
                  color: '#3b82f6',
                  marginBottom: '12px'
                }}>
                  {formatPrice(product.current_price || 0)}
                </div>

                {product.original_price && (
                  <div style={{
                    color: '#94a3b8',
                    textDecoration: 'line-through',
                    marginBottom: '16px'
                  }}>
                    {formatPrice(product.original_price)}
                  </div>
                )}

                {product.discount_pct && (
                  <div style={{ marginBottom: '16px' }}>
                    <span className="badge badge-green">
                      {product.discount_pct.toFixed(0)}% OFF
                    </span>
                  </div>
                )}

                {product.deal_label && (
                  <div style={{ marginBottom: '16px' }}>
                    <DealBadge label={product.deal_label} confidence={product.deal_confidence} />
                  </div>
                )}

                {product.rating && (
                  <div style={{ marginBottom: '16px' }}>
                    <span style={{ color: '#94a3b8' }}>Rating:</span> <span style={{ color: '#e2e8f0' }}>{product.rating}/5</span>
                  </div>
                )}

                {product.url && (
                  <a
                    href={product.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-primary"
                    style={{ width: '100%', display: 'block', textAlign: 'center', marginTop: '16px' }}
                  >
                    View on {product.platform?.toUpperCase()}
                  </a>
                )}
              </div>
            </div>

            {/* Right: Chart & Alert */}
            <div>
              {/* Chart */}
              <div style={{ marginBottom: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h2 style={{ color: '#e2e8f0', margin: 0 }}>Price History</h2>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {[
                      { label: '30d', value: 30 },
                      { label: '3m', value: 90 },
                      { label: '6m', value: 180 },
                      { label: '1y', value: 365 }
                    ].map(period => (
                      <button
                        key={period.value}
                        onClick={() => setHistoryDays(period.value)}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: historyDays === period.value ? '#3b82f6' : '#334155',
                          color: '#e2e8f0',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px',
                          fontWeight: 'bold'
                        }}
                      >
                        {period.label}
                      </button>
                    ))}
                  </div>
                </div>
                <PriceChart data={history} isGenuineDeal={product.deal_label === 'GENUINE_DEAL'} />
              </div>

              {/* Alert Form */}
              <div style={{
                backgroundColor: '#1e293b',
                padding: '24px',
                borderRadius: '12px',
                border: '1px solid #334155'
              }}>
                <h3 style={{ marginBottom: '16px', color: '#e2e8f0' }}>Set Price Alert</h3>

                <form onSubmit={handleCreateAlert} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '12px', color: '#94a3b8' }}>
                      Email
                    </label>
                    <input
                      type="email"
                      placeholder="your@email.com"
                      value={alert.email}
                      onChange={(e) => setAlert({ ...alert, email: e.target.value })}
                      style={{ width: '100%' }}
                      required
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '12px', color: '#94a3b8' }}>
                      Target Price (₹)
                    </label>
                    <input
                      type="number"
                      placeholder="5000"
                      value={alert.targetPrice}
                      onChange={(e) => setAlert({ ...alert, targetPrice: e.target.value })}
                      style={{ width: '100%' }}
                      required
                    />
                  </div>

                  <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                    Create Alert
                  </button>
                </form>

                {alertMessage && (
                  <div style={{
                    marginTop: '12px',
                    padding: '12px',
                    borderRadius: '6px',
                    backgroundColor: alertMessage.type === 'success' ? '#10b98166' : '#ef444466',
                    color: alertMessage.type === 'success' ? '#10b981' : '#ef4444',
                    fontSize: '13px'
                  }}>
                    {alertMessage.text}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Price Comparison Section */}
          {comparisons && comparisons.length > 1 && (
            <div style={{ marginTop: '40px' }}>
              <h2 style={{ marginBottom: '20px', color: '#e2e8f0' }}>Available on Other Platforms</h2>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                gap: '16px'
              }}>
                {comparisons.filter(p => p.id !== parseInt(id)).map(comp => (
                  <div
                    key={`${comp.id}-${comp.platform}`}
                    style={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      padding: '16px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '12px'
                    }}
                  >
                    <div style={{
                      fontSize: '13px',
                      color: '#94a3b8'
                    }}>
                      {comp.platform?.toUpperCase()}
                    </div>
                    <div style={{
                      fontSize: '20px',
                      fontWeight: '700',
                      color: '#3b82f6'
                    }}>
                      ₹{comp.current_price?.toLocaleString('en-IN')}
                    </div>
                    {comp.rating && (
                      <div style={{
                        fontSize: '12px',
                        color: '#94a3b8'
                      }}>
                        Rating: {comp.rating}/5
                      </div>
                    )}
                    <a
                      href={comp.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        display: 'block',
                        padding: '10px 16px',
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        textAlign: 'center',
                        borderRadius: '6px',
                        textDecoration: 'none',
                        fontSize: '13px',
                        fontWeight: '600',
                        marginTop: 'auto'
                      }}
                    >
                      View on {comp.platform?.toUpperCase()}
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </>
  )
}

export default ProductDetail
