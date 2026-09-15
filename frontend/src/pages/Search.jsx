import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPriceRadarAPI } from '../api/client'
import { Navbar } from '../components/Navbar'
import { ProductCard } from '../components/ProductCard'

const Search = () => {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [platform, setPlatform] = useState('all')
  const [sortBy, setSortBy] = useState('relevance')

  const handleSearch = async (e) => {
    e.preventDefault()

    if (!query.trim()) return

    setLoading(true)
    setSearched(true)

    try {
      const res = await getPriceRadarAPI.search(query, platform === 'all' ? null : platform)
      let data = res.data

      // Apply sorting
      if (sortBy === 'price_low') {
        data = [...data].sort((a, b) => a.current_price - b.current_price)
      } else if (sortBy === 'price_high') {
        data = [...data].sort((a, b) => b.current_price - a.current_price)
      } else if (sortBy === 'discount') {
        data = [...data].sort((a, b) => (b.discount_pct || 0) - (a.discount_pct || 0))
      }

      setResults(data)
    } catch (err) {
      console.error(err)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Navbar />
      <main style={{ backgroundColor: '#0f172a', minHeight: '100vh', padding: '60px 0' }}>
        <div className="container">
          {/* Search Bar */}
          <form onSubmit={handleSearch} style={{ marginBottom: '40px' }}>
            <div style={{
              display: 'flex',
              gap: '12px',
              marginBottom: '20px'
            }}>
              <input
                type="text"
                placeholder="Search products..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                style={{
                  flex: 1,
                  padding: '14px 16px',
                  fontSize: '16px',
                  borderRadius: '8px'
                }}
              />
              <button type="submit" className="btn btn-primary" style={{ padding: '14px 32px', fontSize: '16px' }}>
                Search
              </button>
            </div>

            {/* Filters */}
            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
              <select
                value={platform}
                onChange={(e) => setPlatform(e.target.value)}
                style={{ padding: '10px 12px', borderRadius: '6px', minWidth: '150px' }}
              >
                <option value="all">All Platforms</option>
                <option value="amazon">Amazon</option>
                <option value="flipkart">Flipkart</option>
              </select>

              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                style={{ padding: '10px 12px', borderRadius: '6px', minWidth: '150px' }}
              >
                <option value="relevance">Relevance</option>
                <option value="price_low">Price: Low to High</option>
                <option value="price_high">Price: High to Low</option>
                <option value="discount">Highest Discount</option>
              </select>
            </div>
          </form>

          {/* Results */}
          {!searched ? (
            <div className="text-center" style={{ color: '#94a3b8', marginTop: '60px' }}>
              <h2 style={{ fontSize: '28px', color: '#e2e8f0', marginBottom: '12px' }}>
                Search for Products
              </h2>
              <p>Enter a product name and find the best deals on Amazon and Flipkart</p>
            </div>
          ) : loading ? (
            <div className="grid-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="skeleton" style={{ height: '300px', borderRadius: '8px' }} />
              ))}
            </div>
          ) : results.length === 0 ? (
            <div className="error-state">
              <h3>No results found</h3>
              <p>Try a different search term</p>
            </div>
          ) : (
            <>
              <div style={{ color: '#94a3b8', marginBottom: '20px' }}>
                Found {results.length} product{results.length !== 1 ? 's' : ''}
              </div>
              <div className="grid-3">
                {results.map((product) => (
                  <ProductCard
                    key={product.id}
                    product={product}
                    onViewDetails={(id) => navigate(`/products/${id}`)}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      </main>
    </>
  )
}

export default Search
