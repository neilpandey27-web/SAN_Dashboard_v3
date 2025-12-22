'use client';

import { Card } from 'react-bootstrap';
import { IconType } from 'react-icons';

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: IconType;
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'info';
  trend?: {
    value: number;
    direction: 'up' | 'down';
  };
}

export default function KpiCard({ title, value, subtitle, icon: Icon, color = 'primary', trend }: KpiCardProps) {
  const colorMap = {
    primary: 'var(--primary)',
    success: 'var(--success)',
    warning: 'var(--warning)',
    danger: 'var(--danger)',
    info: 'var(--info)',
  };

  return (
    <Card className="h-100 kpi-card">
      <Card.Body className="d-flex">
        <div className="flex-grow-1">
          <p className="text-muted mb-1 small">{title}</p>
          <h3 className="mb-1" style={{ color: colorMap[color] }}>{value}</h3>
          {subtitle && <small className="text-muted">{subtitle}</small>}
          {trend && (
            <div className={`small mt-1 ${trend.direction === 'up' ? 'text-danger' : 'text-success'}`}>
              {trend.direction === 'up' ? '▲' : '▼'} {trend.value}%
            </div>
          )}
        </div>
        <div className="d-flex align-items-center">
          <Icon size={40} style={{ color: colorMap[color], opacity: 0.7 }} />
        </div>
      </Card.Body>
    </Card>
  );
}
