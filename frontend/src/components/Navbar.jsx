import React from 'react'

export const Navbar = () => {
  return (
    <nav style={{ backgroundColor: '#0f172a', borderBottom: '1px solid #334155' }}>
      <div className="container flex-between p-4">
        <div className="flex gap-4 flex-center">
          <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: '#3b82f6' }}>
            PriceRadar
          </h1>
          <span style={{ color: '#64748b', fontSize: '14px' }}>
            Real-time Price Intelligence
          </span>
        </div>
        <div className="flex gap-4">
          <a href="/" style={{ color: '#e2e8f0' }}>Home</a>
          <a href="/search" style={{ color: '#e2e8f0' }}>Search</a>
          <a href="/" style={{ color: '#e2e8f0' }}>Deals</a>
        </div>
      </div>
    </nav>
  )
}
