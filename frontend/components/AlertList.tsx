'use client';

import { Badge } from 'react-bootstrap';

interface AlertItem {
  name: string;
  system?: string;
  utilization_pct: number;
  days_until_full?: number;
}

interface AlertListProps {
  title: string;
  items: AlertItem[];
  type: 'critical' | 'warning';
  maxItems?: number;
}

export default function AlertList({ title, items, type, maxItems = 5 }: AlertListProps) {
  const displayItems = items.slice(0, maxItems);
  
  return (
    <div className="chart-container">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h6 className="chart-title mb-0">{title}</h6>
        <Badge bg={type === 'critical' ? 'danger' : 'warning'}>
          {items.length}
        </Badge>
      </div>
      
      {displayItems.length === 0 ? (
        <div className="text-center text-muted py-4">
          No {type} alerts
        </div>
      ) : (
        <div className="alert-list">
          {displayItems.map((item, index) => (
            <div key={index} className={`alert-list-item ${type}`}>
              <div>
                <div className="fw-medium">{item.name}</div>
                {item.system && (
                  <small className="text-muted">{item.system}</small>
                )}
              </div>
              <div className="text-end">
                <div className={type === 'critical' ? 'util-critical' : 'util-warning'}>
                  {item.utilization_pct?.toFixed(1)}%
                </div>
                {item.days_until_full !== undefined && item.days_until_full !== null && (
                  <small className="text-muted">
                    {item.days_until_full === 0 ? 'Full!' : `${item.days_until_full} days`}
                  </small>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      
      {items.length > maxItems && (
        <div className="text-center mt-2">
          <small className="text-muted">
            +{items.length - maxItems} more
          </small>
        </div>
      )}
    </div>
  );
}
