import React from 'react'

export const DealBadge = ({ label, confidence }) => {
  const colors = {
    'GENUINE_DEAL': { bg: '#10b981', text: 'Genuine Deal' },
    'FAKE_DEAL': { bg: '#ef4444', text: 'Fake Deal' },
    'NORMAL': { bg: '#64748b', text: 'Normal Price' }
  }

  const color = colors[label] || colors['NORMAL']

  return (
    <div style={{
      backgroundColor: color.bg,
      color: 'white',
      padding: '8px 12px',
      borderRadius: '6px',
      fontSize: '12px',
      fontWeight: '600',
      display: 'flex',
      alignItems: 'center',
      gap: '8px'
    }}>
      <span>{color.text}</span>
      {confidence && (
        <span style={{ opacity: 0.8 }}>
          {(confidence * 100).toFixed(0)}%
        </span>
      )}
    </div>
  )
}
