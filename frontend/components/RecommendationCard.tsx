'use client';

import { FaExclamationTriangle, FaInfoCircle, FaCheckCircle } from 'react-icons/fa';

interface Recommendation {
  type: 'critical' | 'warning' | 'info' | 'success';
  title: string;
  message: string;
  priority?: string;
}

interface RecommendationCardProps {
  recommendations: Recommendation[];
  title?: string;
}

export default function RecommendationCard({ recommendations, title = 'Recommendations' }: RecommendationCardProps) {
  const getIcon = (type: string) => {
    switch (type) {
      case 'critical':
      case 'warning':
        return <FaExclamationTriangle />;
      case 'success':
        return <FaCheckCircle />;
      default:
        return <FaInfoCircle />;
    }
  };

  const getColor = (type: string) => {
    switch (type) {
      case 'critical':
        return 'var(--danger)';
      case 'warning':
        return 'var(--warning)';
      case 'success':
        return 'var(--success)';
      default:
        return 'var(--info)';
    }
  };

  return (
    <div className="chart-container">
      {title && <h6 className="chart-title">{title}</h6>}
      
      {recommendations.length === 0 ? (
        <div className="text-center text-muted py-4">
          <FaCheckCircle size={30} className="mb-2" style={{ color: 'var(--success)' }} />
          <p className="mb-0">No recommendations at this time</p>
        </div>
      ) : (
        <div className="d-flex flex-column gap-3">
          {recommendations.map((rec, index) => (
            <div key={index} className={`rec-card ${rec.type}`}>
              <div className="d-flex align-items-start">
                <span className="me-3" style={{ color: getColor(rec.type), fontSize: '1.25rem' }}>
                  {getIcon(rec.type)}
                </span>
                <div>
                  <h6 className="mb-1" style={{ color: getColor(rec.type) }}>
                    {rec.title}
                  </h6>
                  <p className="mb-0 small text-secondary">{rec.message}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
