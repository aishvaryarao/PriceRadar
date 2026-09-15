import React from 'react'

export const ProductCard = ({ product, onViewDetails }) => {
  const [imageError, setImageError] = React.useState(false)

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(price)
  }

  return (
    <div style={{
      backgroundColor: '#1e293b',
      border: '1px solid #334155',
      borderRadius: '8px',
      padding: '16px',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      transition: 'all 0.3s'
    }}>
      {/* Image */}
      <div style={{
        height: '180px',
        backgroundColor: '#0f172a',
        borderRadius: '6px',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        {product.image_url && !imageError ? (
          <img
            src={product.image_url}
            alt={product.name}
            onError={() => setImageError(true)}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover'
            }}
          />
        ) : (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#64748b',
            gap: '8px'
          }}>
            <div style={{ fontSize: '32px' }}>📦</div>
            <div style={{ fontSize: '11px', textAlign: 'center' }}>{product.category || 'Product'}</div>
          </div>
        )}
      </div>

      {/* Name */}
      <h3 style={{
        fontSize: '14px',
        fontWeight: '600',
        lineHeight: '1.4',
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
        color: '#e2e8f0'
      }}>
        {product.name}
      </h3>

      {/* Platform Badge */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <span className="badge badge-orange" style={{ fontSize: '11px' }}>
          {product.platform?.toUpperCase()}
        </span>
      </div>

      {/* Price */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'baseline',
        gap: '8px'
      }}>
        <span style={{ fontSize: '20px', fontWeight: '700', color: '#3b82f6' }}>
          {formatPrice(product.current_price || 0)}
        </span>
        {product.original_price && (
          <span style={{
            fontSize: '14px',
            color: '#94a3b8',
            textDecoration: 'line-through'
          }}>
            {formatPrice(product.original_price)}
          </span>
        )}
      </div>

      {/* Discount Badge */}
      {product.discount_pct && (
        <span className="badge badge-green">
          {product.discount_pct.toFixed(0)}% OFF
        </span>
      )}

      {/* Deal Label */}
      {product.deal_label && (
        <span className="badge badge-blue">
          {product.deal_label.replace(/_/g, ' ')}
        </span>
      )}

      {/* Button */}
      <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
        <button
          className="btn btn-primary"
          style={{ flex: 1 }}
          onClick={() => onViewDetails(product.id)}
        >
          Details
        </button>
        {product.url && (
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
            style={{ flex: 1, textDecoration: 'none', textAlign: 'center', fontSize: '13px' }}
          >
            Buy Now
          </a>
        )}
      </div>
    </div>
  )
}
