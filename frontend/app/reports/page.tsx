'use client';

import { Card } from 'react-bootstrap';
import { FaFileAlt, FaTools } from 'react-icons/fa';
import DashboardLayout from '@/components/DashboardLayout';

export default function ReportsPage() {
  return (
    <DashboardLayout>
      <div className="page-header">
        <h1>
          <FaFileAlt className="me-2" />
          Reports
        </h1>
        <p className="text-muted">Generate and export storage reports</p>
      </div>

      <Card className="text-center py-5">
        <Card.Body>
          <FaTools size={60} className="mb-4" style={{ color: 'var(--text-muted)' }} />
          <h3 className="text-muted">Coming Soon</h3>
          <p className="text-muted mb-0">
            The Reports module is currently under development.<br />
            Check back soon for PDF exports and scheduled reporting features.
          </p>
        </Card.Body>
      </Card>
    </DashboardLayout>
  );
}
