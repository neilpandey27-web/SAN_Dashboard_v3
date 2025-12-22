'use client';

import { useState, useEffect } from 'react';
import { Row, Col, Card, Form, Button, Spinner, Alert } from 'react-bootstrap';
import { FaCalendar, FaChartLine } from 'react-icons/fa';
import dynamic from 'next/dynamic';
import DashboardLayout from '@/components/DashboardLayout';
import { dataAPI } from '@/lib/api';
import { useTenant } from '@/contexts/TenantContext';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface TrendData {
  date: string;
  total_capacity_tb: number;
  used_capacity_tb: number;
  available_capacity_tb: number;
  utilization_pct: number;
}

export default function HistoricalPage() {
  // v6.1.0: Add tenant context
  const { selectedTenant } = useTenant();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [reportDates, setReportDates] = useState<string[]>([]);
  
  // Date range
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    loadReportDates();
  }, []);
  
  // v6.1.0: Re-fetch data when selectedTenant changes
  useEffect(() => {
    if (startDate && endDate) {
      loadHistoricalData();
    }
  }, [selectedTenant]);

  const loadReportDates = async () => {
    try {
      const response = await dataAPI.getReportDates();
      const dates = response.data;
      setReportDates(dates);
      
      // Set default date range to last 30 days or available dates
      if (dates.length > 0) {
        setEndDate(dates[0]);
        setStartDate(dates[Math.min(dates.length - 1, 29)]);
      }
    } catch (err) {
      console.error('Failed to load report dates:', err);
    }
  };

  const loadHistoricalData = async () => {
    if (!startDate || !endDate) {
      setError('Please select a date range');
      return;
    }

    try {
      setLoading(true);
      setError('');
      // v6.1.0: Pass tenant filter to API
      const response = await dataAPI.getHistorical(
        startDate, 
        endDate,
        selectedTenant || undefined
      );
      setTrendData(response.data.trend_data || []);
    } catch (err: any) {
      console.error('Failed to load historical data:', err);
      setError('Failed to load historical data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadHistoricalData();
  };

  return (
    <DashboardLayout>
      {/* Page Header */}
      <div className="page-header">
        <h1>
          <FaChartLine className="me-2" />
          Historical Trends
        </h1>
        <p className="text-muted">Analyze storage capacity trends over time</p>
      </div>

      {/* Date Range Selector */}
      <Card className="mb-4">
        <Card.Body>
          <Form onSubmit={handleSubmit}>
            <Row className="align-items-end">
              <Col md={4}>
                <Form.Group>
                  <Form.Label>
                    <FaCalendar className="me-2" />
                    Start Date
                  </Form.Label>
                  <Form.Control
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group>
                  <Form.Label>End Date</Form.Label>
                  <Form.Control
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Button
                  variant="primary"
                  type="submit"
                  disabled={loading || !startDate || !endDate}
                  className="w-100"
                >
                  {loading ? (
                    <>
                      <Spinner animation="border" size="sm" className="me-2" />
                      Loading...
                    </>
                  ) : (
                    'Load Data'
                  )}
                </Button>
              </Col>
            </Row>
          </Form>
        </Card.Body>
      </Card>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* No data message */}
      {!loading && trendData.length === 0 && (
        <Alert variant="info">
          <Alert.Heading>Select a Date Range</Alert.Heading>
          <p className="mb-0">
            Choose a start and end date to view historical capacity trends.
            {reportDates.length > 0 && (
              <> Available data from {reportDates[reportDates.length - 1]} to {reportDates[0]}.</>
            )}
          </p>
        </Alert>
      )}

      {/* Charts */}
      {trendData.length > 0 && (
        <>
          {/* Capacity Trend Chart */}
          <Card className="mb-4">
            <Card.Body>
              <h6 className="mb-3">Capacity Over Time</h6>
              <Plot
                data={[
                  {
                    x: trendData.map(d => d.date),
                    y: trendData.map(d => d.total_capacity_tb),
                    name: 'Total Capacity',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: '#2a9fd6', width: 2 },
                    marker: { size: 6 },
                  },
                  {
                    x: trendData.map(d => d.date),
                    y: trendData.map(d => d.used_capacity_tb),
                    name: 'Used Capacity',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: '#ff8800', width: 2 },
                    marker: { size: 6 },
                  },
                  {
                    x: trendData.map(d => d.date),
                    y: trendData.map(d => d.available_capacity_tb),
                    name: 'Available Capacity',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: '#77b300', width: 2 },
                    marker: { size: 6 },
                  },
                ]}
                layout={{
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'transparent',
                  font: { color: '#ffffff' },
                  margin: { t: 30, b: 60, l: 60, r: 30 },
                  height: 400,
                  showlegend: true,
                  legend: {
                    orientation: 'h',
                    y: -0.15,
                    x: 0.5,
                    xanchor: 'center',
                  },
                  xaxis: {
                    gridcolor: '#333',
                    title: 'Date',
                  },
                  yaxis: {
                    gridcolor: '#333',
                    title: 'Capacity (TiB)',
                    tickformat: ',.2f'
                  },
                }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%' }}
              />
            </Card.Body>
          </Card>

          {/* Utilization Trend Chart */}
          <Card className="mb-4">
            <Card.Body>
              <h6 className="mb-3">Utilization Trend</h6>
              <Plot
                data={[
                  {
                    x: trendData.map(d => d.date),
                    y: trendData.map(d => d.utilization_pct),
                    name: 'Utilization %',
                    type: 'scatter',
                    mode: 'lines+markers',
                    fill: 'tozeroy',
                    fillcolor: 'rgba(42, 159, 214, 0.2)',
                    line: { color: '#2a9fd6', width: 2 },
                    marker: { 
                      size: 8,
                      color: trendData.map(d => 
                        d.utilization_pct >= 90 ? '#cc0000' :
                        d.utilization_pct >= 70 ? '#ff8800' :
                        '#77b300'
                      ),
                    },
                  },
                ]}
                layout={{
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'transparent',
                  font: { color: '#ffffff' },
                  margin: { t: 30, b: 60, l: 60, r: 30 },
                  height: 350,
                  showlegend: false,
                  xaxis: {
                    gridcolor: '#333',
                    title: 'Date',
                  },
                  yaxis: {
                    gridcolor: '#333',
                    title: 'Utilization %',
                    range: [0, 100],
                  },
                  shapes: [
                    // 90% threshold line
                    {
                      type: 'line',
                      x0: 0,
                      x1: 1,
                      xref: 'paper',
                      y0: 90,
                      y1: 90,
                      line: {
                        color: '#cc0000',
                        width: 2,
                        dash: 'dash',
                      },
                    },
                    // 70% threshold line
                    {
                      type: 'line',
                      x0: 0,
                      x1: 1,
                      xref: 'paper',
                      y0: 70,
                      y1: 70,
                      line: {
                        color: '#ff8800',
                        width: 2,
                        dash: 'dash',
                      },
                    },
                  ],
                  annotations: [
                    {
                      x: 1,
                      xref: 'paper',
                      y: 90,
                      text: 'Critical (90%)',
                      showarrow: false,
                      font: { color: '#cc0000', size: 10 },
                      xanchor: 'right',
                    },
                    {
                      x: 1,
                      xref: 'paper',
                      y: 70,
                      text: 'Warning (70%)',
                      showarrow: false,
                      font: { color: '#ff8800', size: 10 },
                      xanchor: 'right',
                    },
                  ],
                }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%' }}
              />
            </Card.Body>
          </Card>

          {/* Summary Stats */}
          <Row className="g-4">
            <Col md={3}>
              <Card className="h-100">
                <Card.Body className="text-center">
                  <h6 className="text-muted">Data Points</h6>
                  <h3 style={{ color: 'var(--primary)' }}>{trendData.length}</h3>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="h-100">
                <Card.Body className="text-center">
                  <h6 className="text-muted">Avg Utilization</h6>
                  <h3 style={{ color: 'var(--warning)' }}>
                    {(trendData.reduce((sum, d) => sum + d.utilization_pct, 0) / trendData.length).toFixed(1)}%
                  </h3>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="h-100">
                <Card.Body className="text-center">
                  <h6 className="text-muted">Peak Utilization</h6>
                  <h3 style={{ color: 'var(--danger)' }}>
                    {Math.max(...trendData.map(d => d.utilization_pct)).toFixed(1)}%
                  </h3>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="h-100">
                <Card.Body className="text-center">
                  <h6 className="text-muted">Min Utilization</h6>
                  <h3 style={{ color: 'var(--success)' }}>
                    {Math.min(...trendData.map(d => d.utilization_pct)).toFixed(1)}%
                  </h3>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </>
      )}
    </DashboardLayout>
  );
}
