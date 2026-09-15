import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import ProductDetail from './pages/ProductDetail'
import Search from './pages/Search'

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/products/:id" element={<ProductDetail />} />
      <Route path="/search" element={<Search />} />
      <Route path="*" element={<div style={{ textAlign: 'center', marginTop: '40px', color: '#94a3b8' }}>404 - Page not found</div>} />
    </Routes>
  )
}

export default App
