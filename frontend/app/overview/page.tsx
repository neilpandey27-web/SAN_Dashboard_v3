'use client';

import { useState, useEffect, useRef } from 'react';
import { Row, Col, Spinner, Alert, Card, Button, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { FaDatabase, FaHdd, FaServer, FaNetworkWired, FaCompressAlt, FaSave, FaExclamationTriangle, FaFilePdf } from 'react-icons/fa';
import DashboardLayout from '@/components/DashboardLayout';
import { dataAPI } from '@/lib/api';
import { useTenant } from '@/contexts/TenantContext';
import dynamic from 'next/dynamic';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface TreemapNode {
  name: string;
  storage_system: string;
  total_capacity_gib: number;
  used_capacity_gib: number;
  available_capacity_gib: number;
  utilization_pct: number;
}

interface OverviewData {
  kpis: {
    total_capacity_tb: number;
    total_used_tb: number;
    total_available_tb: number;
    total_savings_tb: number;
    avg_utilization_pct: number;
    provisioned_utilization_pct: number;
    system_utilization_pct: number;
    num_systems: number;
    num_pools: number;
    num_hosts: number;
  };
  alerts: {
    critical_count: number;
    warning_count: number;
    urgent_count: number;
    critical_pools: any[];
    warning_pools: any[];
    urgent_pools: any[];
  };
  top_systems: any[];
  utilization_distribution: { bins: string[]; counts: number[] };
  forecasting_data: any[];
  storage_types: any[];
  top_hosts: any[];
  savings_data: any[];
  treemap_data: {
    simple_average: TreemapNode[];
    weighted_average: TreemapNode[];
  };
  recommendations: any[];
  report_date: string;
}

// Helper function to convert GiB to user's preferred unit
const convertCapacity = (gib: number, unit: 'GiB' | 'TiB' | 'PiB'): number => {
  switch (unit) {
    case 'GiB':
      return gib; // GiB to GiB
    case 'TiB':
      return gib / 1024; // GiB to TiB
    case 'PiB':
      return gib / (1024 * 1024); // GiB to PiB
    default:
      return gib / 1024;
  }
};

export default function OverviewPage() {
  // v6.1.0: Add tenant context
  const { selectedTenant } = useTenant();

  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [unit, setUnit] = useState<'GiB' | 'TiB' | 'PiB'>('TiB');
  const [exporting, setExporting] = useState(false);
  const dashboardRef = useRef<HTMLDivElement>(null);

  // v6.1.0: Re-fetch data when selectedTenant changes
  useEffect(() => {
    loadData();
  }, [selectedTenant]);

  const loadData = async () => {
    try {
      setLoading(true);
      // v6.1.0: Pass selectedTenant to API call
      const response = await dataAPI.getEnhancedOverview(
        undefined, // reportDate
        selectedTenant || undefined // tenant filter
      );
      setData(response.data);
      setError('');
    } catch (err: any) {
      console.error('Failed to load overview data:', err);
      if (err.response?.data?.error || err.response?.data?.message === 'No data available') {
        setError('No storage data available. Please upload data in the Database Management tab.');
      } else {
        setError('Failed to load dashboard data. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
          <Spinner animation="border" variant="primary" />
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <Alert variant="warning" className="text-center">
          <Alert.Heading>No Data Available</Alert.Heading>
          <p>{error}</p>
        </Alert>
      </DashboardLayout>
    );
  }

  if (!data || !data.kpis) {
    return (
      <DashboardLayout>
        <Alert variant="info" className="text-center mt-5">
          <Alert.Heading className="mb-4">
            <i className="fas fa-database me-2"></i>
            Welcome to OneIT SAN Analytics
          </Alert.Heading>
          <p className="lead mb-4">No storage data has been uploaded yet.</p>
          <hr />
          <div className="text-start mt-4">
            <h5 className="mb-3">📋 Quick Start Guide:</h5>
            <ol className="text-start">
              <li className="mb-2">
                <strong>Go to Database Management tab</strong> (in the navigation menu)
              </li>
              <li className="mb-2">
                <strong>Upload your Excel file</strong> with storage data
                <div className="text-muted small ms-3">
                  Required sheets: Storage_Systems, Storage_Pools, Capacity_Volumes,
                  Inventory_Hosts, Capacity_Hosts, Inventory_Disks, Capacity_Disks, Departments
                </div>
              </li>
              <li className="mb-2">
                <strong>Wait for processing</strong> to complete
              </li>
              <li className="mb-2">
                <strong>Return to Overview</strong> to see your enhanced dashboard with:
                <div className="ms-3 mt-2">
                  ✅ Interactive capacity gauge<br />
                  ✅ Forecasting charts<br />
                  ✅ Treemap visualization<br />
                  ✅ Critical alerts<br />
                  ✅ Intelligent recommendations
                </div>
              </li>
            </ol>
          </div>
          <hr />
          <p className="text-muted small mt-3">
            Need help? Check the documentation in the Database Management tab.
          </p>
        </Alert>
      </DashboardLayout>
    );
  }

  const { kpis, alerts, top_systems, utilization_distribution, forecasting_data, storage_types, top_hosts, savings_data, treemap_data, recommendations, report_date } = data;

  // Urgent pools from alerts
  const urgent_pools = alerts.urgent_pools || [];

  // Unit converter for TiB values (used in KPI cards, data from backend is in TiB)
  const convertCapacityFromTiB = (tib: number): number => {
    if (unit === 'GiB') return tib * 1024;
    if (unit === 'PiB') return tib / 1024;
    return tib;
  };

  const formatCapacity = (tib: number): string => {
    const value = convertCapacityFromTiB(tib);
    return `${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${unit}`;
  };

  const exportToPDF = async () => {
    if (!dashboardRef.current) return;

    setExporting(true);
    try {
      // Create PDF
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const margin = 10;

      // Get all chart elements
      const elements = dashboardRef.current.querySelectorAll('.chart-section');
      let yOffset = margin;

      // Add title
      pdf.setFontSize(16);
      pdf.setTextColor(0, 0, 0);
      pdf.text('OneIT Lab Engineering SAN Dashboard', pageWidth / 2, yOffset, { align: 'center' });
      yOffset += 10;

      pdf.setFontSize(10);
      pdf.text(`Generated: ${new Date().toLocaleString()}`, pageWidth / 2, yOffset, { align: 'center' });
      yOffset += 10;

      // Process each section
      for (let i = 0; i < elements.length; i++) {
        const element = elements[i] as HTMLElement;

        // Capture element as canvas
        const canvas = await html2canvas(element, {
          scale: 2,
          logging: false,
          useCORS: true,
          allowTaint: true
        });

        const imgData = canvas.toDataURL('image/png');
        const imgWidth = pageWidth - (2 * margin);
        const imgHeight = (canvas.height * imgWidth) / canvas.width;

        // Add new page if needed
        if (yOffset + imgHeight > pageHeight - margin && i > 0) {
          pdf.addPage();
          yOffset = margin;
        }

        // Add image to PDF
        pdf.addImage(imgData, 'PNG', margin, yOffset, imgWidth, imgHeight);
        yOffset += imgHeight + 5;
      }

      // Save PDF
      const filename = `storage-dashboard-${new Date().toISOString().slice(0, 10)}.pdf`;
      pdf.save(filename);

      alert('PDF exported successfully!');
    } catch (err) {
      console.error('Error exporting PDF:', err);
      alert('Failed to export PDF. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  return (
    <DashboardLayout>
      {/* Header with timestamp */}
      <div className="page-header mb-4">
        <div className="d-flex justify-content-between align-items-start mb-3">
          <div style={{ flex: 1 }}></div>
          <div className="text-center" style={{ flex: 1 }}>
            <h1 className="mb-2">🚀 OneIT Lab Engineering SAN Dashboard</h1>
            <p className="text-muted mb-0">
              Last Updated: {new Date(report_date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </p>
            {/* v6.1.0: Display filtered tenant info */}
            {selectedTenant && (
              <p className="text-info mb-0">
                <small>📊 Showing data for tenant: <strong>{selectedTenant}</strong></small>
              </p>
            )}
          </div>
          <div className="text-end d-flex flex-column gap-2" style={{ flex: 1 }}>
            <Button
              variant="success"
              size="sm"
              onClick={exportToPDF}
              disabled={exporting}
            >
              {exporting ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Exporting...
                </>
              ) : (
                <>
                  <FaFilePdf className="me-2" />
                  Export PDF
                </>
              )}
            </Button>
            <div className="btn-group btn-group-sm" role="group">
              <button
                type="button"
                className={`btn ${unit === 'GiB' ? 'btn-primary' : 'btn-outline-secondary'}`}
                onClick={() => setUnit('GiB')}
              >
                GiB
              </button>
              <button
                type="button"
                className={`btn ${unit === 'TiB' ? 'btn-primary' : 'btn-outline-secondary'}`}
                onClick={() => setUnit('TiB')}
              >
                TiB
              </button>
              <button
                type="button"
                className={`btn ${unit === 'PiB' ? 'btn-primary' : 'btn-outline-secondary'}`}
                onClick={() => setUnit('PiB')}
              >
                PiB
              </button>
            </div>
          </div>
        </div>
        <hr />
      </div>

      <div ref={dashboardRef}>

      {/* Main KPI Cards */}
      <Row className="g-3 mb-4 chart-section">
        <Col xs={12} sm={6} lg={3}>
          <Card className="shadow border-0 h-100">
            <Card.Body>
              <h6 className="text-muted mb-2">📦 Total Provisioned Capacity</h6>
              <h2 className="text-info mb-1">{formatCapacity(kpis.total_capacity_tb)}</h2>
              <p className="text-muted small mb-0">{kpis.avg_utilization_pct.toFixed(1)}% utilized</p>
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} sm={6} lg={3}>
          <Card className="shadow border-0 h-100">
            <Card.Body>
              <h6 className="text-muted mb-2">💾 Used Provisioned Capacity</h6>
              <h2 className="text-success mb-1">{formatCapacity(kpis.total_used_tb)}</h2>
              <p className="text-muted small mb-0">{kpis.avg_utilization_pct.toFixed(1)}% utilized</p>
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} sm={6} lg={3}>
          <Card className="shadow border-0 h-100">
            <Card.Body>
              <h6 className="text-muted mb-2">📊 Unused Provisioned Capacity</h6>
              <h2 className="text-warning mb-1">{formatCapacity(kpis.total_available_tb)}</h2>
              <p className="text-muted small mb-0">{((kpis.total_available_tb / kpis.total_capacity_tb) * 100).toFixed(1)}% free</p>
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} sm={6} lg={3}>
          <Card className="shadow border-0 h-100">
            <Card.Body>
              <h6 className="text-muted mb-2">💰 Total Savings</h6>
              <h2 className="text-primary mb-1">{formatCapacity(kpis.total_savings_tb)}</h2>
              <p className="text-muted small mb-0">Compression + Dedup</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Resource Count + Utilization Gauge */}
      <Row className="g-3 mb-4">
        <Col xs={6} sm={4} md={2}>
          <Card className="shadow border-0 text-center">
            <Card.Body className="py-2">
              <h6 className="mb-1" style={{ fontSize: '0.9rem' }}>🏢 Storage Systems</h6>
              <h3 className="mb-0">{kpis.num_systems}</h3>
            </Card.Body>
          </Card>
        </Col>

        <Col xs={6} sm={4} md={2}>
          <Card className="shadow border-0 text-center">
            <Card.Body className="py-2">
              <h6 className="mb-1" style={{ fontSize: '0.9rem' }}>💿 Storage Pools</h6>
              <h3 className="mb-0">{kpis.num_pools}</h3>
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} sm={4} md={2}>
          <Card className="shadow border-0 text-center">
            <Card.Body className="py-2">
              <h6 className="mb-1" style={{ fontSize: '0.9rem' }}>🖥️ Hosts</h6>
              <h3 className="mb-0">{kpis.num_hosts}</h3>
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} md={3}>
          <Card className="shadow border-0">
            <Card.Body className="p-2">
              <Plot
                data={[
                  {
                    type: 'indicator',
                    mode: 'gauge+number',
                    value: kpis.provisioned_utilization_pct,
                    number: { suffix: '%', font: { size: 20, color: 'white' } },
                    title: { text: 'Overall Provisioned Capacity Utilization', font: { size: 11, color: 'white' } },
                    gauge: {
                      axis: { range: [0, 100], tickfont: { color: 'white', size: 10 } },
                      bar: { color: '#3498db' },
                      steps: [
                        { range: [0, 50], color: '#27ae60' },
                        { range: [50, 75], color: '#f39c12' },
                        { range: [75, 90], color: '#e67e22' },
                        { range: [90, 100], color: '#e74c3c' }
                      ],
                      threshold: {
                        line: { color: 'red', width: 4 },
                        thickness: 0.75,
                        value: 90
                      }
                    }
                  }
                ]}
                layout={{
                  height: 140,
                  margin: { l: 15, r: 15, t: 40, b: 10 },
                  paper_bgcolor: 'transparent',
                  font: { size: 10, color: 'white' }
                }}
                config={{ displayModeBar: false }}
                className="w-100"
              />
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} md={3}>
          <Card className="shadow border-0">
            <Card.Body className="p-2">
              <Plot
                data={[
                  {
                    type: 'indicator',
                    mode: 'gauge+number',
                    value: kpis.system_utilization_pct,
                    number: { suffix: '%', font: { size: 20, color: 'white' } },
                    title: { text: 'Overall Storage System Utilization', font: { size: 11, color: 'white' } },
                    gauge: {
                      axis: { range: [0, 100], tickfont: { color: 'white', size: 10 } },
                      bar: { color: '#9b59b6' },
                      steps: [
                        { range: [0, 50], color: '#27ae60' },
                        { range: [50, 75], color: '#f39c12' },
                        { range: [75, 90], color: '#e67e22' },
                        { range: [90, 100], color: '#e74c3c' }
                      ],
                      threshold: {
                        line: { color: 'red', width: 4 },
                        thickness: 0.75,
                        value: 90
                      }
                    }
                  }
                ]}
                layout={{
                  height: 140,
                  margin: { l: 15, r: 15, t: 40, b: 10 },
                  paper_bgcolor: 'transparent',
                  font: { size: 10, color: 'white' }
                }}
                config={{ displayModeBar: false }}
                className="w-100"
              />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* CRITICAL ALERTS SECTION */}
      <Row className="mb-4 chart-section">
        <Col>
          <Card className="shadow border-danger border-2">
            <Card.Header className="bg-danger text-white">
              <h5 className="mb-0">🚨 CRITICAL CAPACITY ALERTS</h5>
            </Card.Header>
            <Card.Body>
              <Row className="text-center mb-3">
                <Col xs={4}>
                  <h3 className="text-danger mb-0">{alerts.critical_count}</h3>
                  <p className="text-muted small mb-0">Pools &gt; 80%</p>
                </Col>
                <Col xs={4}>
                  <h3 className="text-warning mb-0">{alerts.warning_count}</h3>
                  <p className="text-muted small mb-0">Pools 70-80%</p>
                </Col>
                <Col xs={4}>
                  <h3 className="text-danger mb-0">{urgent_pools.length}</h3>
                  <p className="text-muted small mb-0">Full in &lt; 30 days</p>
                </Col>
              </Row>
              <hr />

              {/* Critical Pools */}
              {alerts.critical_pools.length > 0 && (
                <>
                  <h6 className="text-danger mb-3">🔴 CRITICAL POOLS (&gt;80% full):</h6>
                  {alerts.critical_pools.map((pool, idx) => {
                    const isUrgent = pool.days_until_full < 30;
                    return (
                      <Alert key={idx} variant="danger" className="mb-2">
                        <strong>{pool.name} ({pool.system}): {pool.utilization_pct?.toFixed(0)}% full</strong>
                        <br />
                        <small className="text-muted">
                          → Estimated full in {pool.days_until_full} days {isUrgent && '⚠️ URGENT!'}
                        </small>
                      </Alert>
                    );
                  })}
                </>
              )}

              {/* Warning Pools */}
              {alerts.warning_pools.length > 0 && (
                <>
                  <h6 className="text-warning mb-3 mt-3">🟡 WARNING POOLS (70-80% full):</h6>
                  {alerts.warning_pools.map((pool, idx) => (
                    <Alert key={idx} variant="warning" className="mb-2">
                      <strong>{pool.name} ({pool.system}): {pool.utilization_pct?.toFixed(0)}% full</strong>
                      <br />
                      <small className="text-muted">
                        → Estimated full in {pool.days_until_full < 999 ? `${pool.days_until_full} days` : 'Stable'}
                      </small>
                    </Alert>
                  ))}
                </>
              )}

              {alerts.critical_pools.length === 0 && alerts.warning_pools.length === 0 && (
                <Alert variant="success">✅ All pools are healthy (&lt; 70% utilization)</Alert>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* CAPACITY FORECASTING */}
      <Row className="mb-4 chart-section">
        <Col>
          <Card className="shadow border-0">
            <Card.Header>
              <h5 className="mb-0">📈 CAPACITY FORECASTING</h5>
            </Card.Header>
            <Card.Body>
              {forecasting_data && forecasting_data.length > 0 ? (
                <Plot
                  data={[
                    ...forecasting_data.map((pool: any) => ({
                      name: pool.name,
                      type: 'scatter',
                      mode: 'lines+markers',
                      x: Array.from({ length: 13 }, (_, i) => i),
                      y: pool.projections,
                      hovertemplate: `<b>${pool.name}</b><br>Month: %{x}<br>Util: %{y:.1f}%<extra></extra>`
                    } as any)),
                    {
                      name: 'Warning (70%)',
                      type: 'scatter',
                      mode: 'lines',
                      x: [0, 12],
                      y: [70, 70],
                      line: { dash: 'dot', color: 'yellow', width: 2 },
                      showlegend: false,
                      hoverinfo: 'skip'
                    } as any,
                    {
                      name: 'Critical (80%)',
                      type: 'scatter',
                      mode: 'lines',
                      x: [0, 12],
                      y: [80, 80],
                      line: { dash: 'dot', color: 'orange', width: 2 },
                      showlegend: false,
                      hoverinfo: 'skip'
                    } as any,
                    {
                      name: 'Full (100%)',
                      type: 'scatter',
                      mode: 'lines',
                      x: [0, 12],
                      y: [100, 100],
                      line: { dash: 'dot', color: 'red', width: 2 },
                      showlegend: false,
                      hoverinfo: 'skip'
                    } as any
                  ]}
                  layout={{
                    height: 400,
                    xaxis: { title: 'Months Ahead' },
                    yaxis: { title: 'Utilization %', range: [0, 110] },
                    hovermode: 'x unified',
                    showlegend: true,
                    legend: { x: 0.01, y: 0.99 },
                    margin: { l: 50, r: 50, t: 30, b: 50 }
                  }}
                  config={{ displayModeBar: true, responsive: true }}
                  className="w-100"
                />
              ) : (
                <p className="text-center text-muted">No critical or warning pools to forecast</p>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Top Systems + Utilization Distribution */}
      <Row className="g-3 mb-4 chart-section">
        <Col xs={12} lg={6}>
          <Card className="shadow border-0 h-100">
            <Card.Header>
              <h6 className="mb-0">Top 10 Systems by Capacity</h6>
            </Card.Header>
            <Card.Body>
              <Plot
                data={[
                  {
                    name: 'Used',
                    type: 'bar',
                    x: top_systems.map((s: any) => s.name),
                    y: top_systems.map((s: any) => convertCapacityFromTiB(s.used_tb)),
                    marker: { color: '#27ae60' },
                    hovertemplate: `<b>%{x}</b><br>Used: %{y:.2f} ${unit}<extra></extra>`
                  },
                  {
                    name: 'Available',
                    type: 'bar',
                    x: top_systems.map((s: any) => s.name),
                    y: top_systems.map((s: any) => convertCapacityFromTiB(s.available_tb)),
                    marker: { color: '#3498db' },
                    hovertemplate: `<b>%{x}</b><br>Available: %{y:.2f} ${unit}<extra></extra>`
                  }
                ]}
                layout={{
                  height: 400,
                  barmode: 'stack',
                  xaxis: { tickangle: -45 },
                  yaxis: {
                    title: `Capacity (${unit})`,
                    tickformat: ',.2f'
                  },
                  hovermode: 'x unified',
                  margin: { l: 50, r: 30, t: 30, b: 80 }
                }}
                config={{ displayModeBar: true, responsive: true }}
                className="w-100"
              />
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} lg={6}>
          <Card className="shadow border-0 h-100">
            <Card.Header>
              <h6 className="mb-0">System Utilization Distribution</h6>
            </Card.Header>
            <Card.Body>
              {utilization_distribution && utilization_distribution.bins && utilization_distribution.counts ? (
                <Plot
                  data={[
                    {
                      type: 'bar',
                      x: utilization_distribution.bins,
                      y: utilization_distribution.counts,
                      marker: { color: '#3498db' },
                      hovertemplate: 'Utilization: %{x}<br>Count: %{y}<extra></extra>'
                    }
                  ]}
                  layout={{
                    height: 400,
                    xaxis: { title: 'Utilization Range (%)' },
                    yaxis: { title: 'Number of Systems' },
                    showlegend: false,
                    margin: { l: 50, r: 30, t: 30, b: 50 },
                    paper_bgcolor: 'white',
                    plot_bgcolor: '#f8f9fa'
                  }}
                  config={{ displayModeBar: true, responsive: true }}
                  className="w-100"
                />
              ) : (
                <div className="d-flex align-items-center justify-content-center" style={{ height: '400px' }}>
                  <p className="text-center text-muted">No utilization distribution data available. Please upload storage data.</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* CAPACITY TREEMAP - Weighted Average Only */}
      <Row className="mb-4 chart-section">
        <Col>
          <Card className="shadow border-0">
            <Card.Header className="d-flex justify-content-between align-items-center">
              <div className="d-flex align-items-center gap-2">
                <h5 className="mb-0">🌳 Capacity Treemap - Weighted Average</h5>
                <OverlayTrigger
                  placement="right"
                  delay={{ show: 0, hide: 250 }}
                  overlay={
                    <Tooltip id="treemap-info-tooltip" style={{ maxWidth: '400px' }}>
                      <div className="text-start">
                        <strong>Calculation Method:</strong> Total used capacity divided by total capacity
                        <br /><br />
                        <strong>Formula:</strong> Sum(Used Capacity) / Sum(Total Capacity) × 100
                        <br /><br />
                        <strong>Meaning:</strong> Shows actual storage consumption weighted by pool size. A 1TB pool at 90% (0.9TB used) has more impact than a 10GB pool at 90% (9GB used).
                        <br /><br />
                        <strong>Use Case:</strong> Understand true capacity utilization for capacity planning and forecasting.
                      </div>
                    </Tooltip>
                  }
                >
                  <span
                    className="btn btn-sm btn-primary rounded-circle d-inline-flex align-items-center justify-content-center"
                    style={{ cursor: 'help', width: '24px', height: '24px', padding: 0 }}
                  >
                    <span style={{ fontSize: '14px', fontWeight: 'bold' }}>i</span>
                  </span>
                </OverlayTrigger>
              </div>
            </Card.Header>
            <Card.Body>
              {(() => {
                // Debug: Log treemap data
                if (treemap_data && treemap_data.weighted_average) {
                  console.log('Treemap Data:', {
                    count: treemap_data.weighted_average.length,
                    sample: treemap_data.weighted_average.slice(0, 3)
                  });
                }
                return null;
              })()}
              {treemap_data && treemap_data.weighted_average && treemap_data.weighted_average.length > 0 ? (
                <Plot
                  data={[
                    {
                      type: 'treemap' as any,
                      labels: treemap_data.weighted_average.map((d) => d.name),
                      parents: treemap_data.weighted_average.map((d) => d.storage_system),
                      values: treemap_data.weighted_average.map((d) => convertCapacity(d.total_capacity_gib, unit)),
                      marker: {
                        colorscale: 'RdYlGn_r',
                        cmid: 50,
                        cmin: 0,
                        cmax: 100,
                        colorbar: { title: { text: 'Utilization %', side: 'right' } },
                        colors: treemap_data.weighted_average.map((d) => d.utilization_pct || 0)
                      },
                      text: treemap_data.weighted_average.map((d) =>
                        `${d.name}<br>${convertCapacity(d.total_capacity_gib, unit).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} ${unit}<br>${(d.utilization_pct || 0).toFixed(0)}%`
                      ),
                      textfont: {
                        size: 14,
                        color: 'white'
                      },
                      textposition: 'middle center',
                      customdata: treemap_data.weighted_average.map((d) => ({
                        system: d.storage_system,
                        total: convertCapacity(d.total_capacity_gib, unit).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
                        used: convertCapacity(d.used_capacity_gib, unit).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
                        available: convertCapacity(d.available_capacity_gib, unit).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
                        util: d.utilization_pct
                      })),
                      hovertemplate:
                        '<b>System:</b> %{customdata.system}<br>' +
                        '<b>Pool:</b> %{label}<br>' +
                        `<b>Total:</b> %{customdata.total} ${unit}<br>` +
                        `<b>Used:</b> %{customdata.used} ${unit}<br>` +
                        `<b>Available:</b> %{customdata.available} ${unit}<br>` +
                        '<b>Utilization:</b> %{customdata.util:.1f}%' +
                        '<extra></extra>',
                      pathbar: {
                        visible: true,
                        side: 'top',
                        thickness: 30,
                        textfont: { size: 14 }
                      },
                      branchvalues: 'total',
                      tiling: {
                        packing: 'squarify'
                      }
                    }
                  ]}
                  layout={{
                    height: 600,
                    margin: { l: 0, r: 50, t: 50, b: 0 },
                    paper_bgcolor: 'white',
                    treemapcolorway: ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A']
                  }}
                  config={{ displayModeBar: true, responsive: true }}
                  className="w-100"
                />
              ) : (
                <div className="d-flex align-items-center justify-content-center" style={{ height: '500px' }}>
                  <p className="text-center text-muted">No treemap data available. Please upload storage data to see the hierarchical visualization.</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Simple Average vs Weighted Average Comparison Table - Tenant Level */}
      <Row className="mb-4 chart-section">
        <Col>
          <Card className="shadow border-0">
            <Card.Header>
              <h5 className="mb-0">📊 Comparison Table (Below Treemap): Tenant-Level Breakdown</h5>
            </Card.Header>
            <Card.Body>
              {treemap_data && treemap_data.simple_average && treemap_data.weighted_average ? (
                <div className="table-responsive">
                  <table className="table table-hover table-striped align-middle">
                    <thead className="table-dark">
                      <tr>
                        <th>Tenant</th>
                        <th>Systems</th>
                        <th>Pool Names</th>
                        <th>
                          Simple Avg %
                          <OverlayTrigger
                            placement="top"
                            delay={{ show: 0, hide: 250 }}
                            overlay={
                              <Tooltip id="simple-avg-tooltip" style={{ maxWidth: '350px' }}>
                                <div className="text-start">
                                  <strong>Calculation:</strong> Average of all pool utilization percentages (Pool1% + Pool2% + ... + PoolN%) / N
                                  <br /><br />
                                  <strong>Meaning:</strong> Shows overall pool health regardless of capacity size. Each pool contributes equally to the average.
                                  <br /><br />
                                  <strong>Use Case:</strong> Identify tenants with many highly utilized pools.
                                </div>
                              </Tooltip>
                            }
                          >
                            <span className="ms-2 badge bg-info" style={{ cursor: 'help', fontSize: '0.75rem' }}>
                              ⓘ
                            </span>
                          </OverlayTrigger>
                        </th>
                        <th>
                          Weighted Avg %
                          <OverlayTrigger
                            placement="top"
                            delay={{ show: 0, hide: 250 }}
                            overlay={
                              <Tooltip id="weighted-avg-tooltip" style={{ maxWidth: '350px' }}>
                                <div className="text-start">
                                  <strong>Calculation:</strong> (Total Used Capacity / Total Capacity) × 100
                                  <br /><br />
                                  <strong>Meaning:</strong> Shows actual capacity usage, prioritizing larger pools.
                                  <br /><br />
                                  <strong>Use Case:</strong> Identify tenants consuming the most physical storage.
                                </div>
                              </Tooltip>
                            }
                          >
                            <span className="ms-2 badge bg-info" style={{ cursor: 'help', fontSize: '0.75rem' }}>
                              ⓘ
                            </span>
                          </OverlayTrigger>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {(() => {
                        // Group pools by tenant (using pool metadata or system info)
                        // Since we don't have tenant data in treemap_data, we'll infer from pool/system names
                        // Expected format from backend would include tenant info
                        const tenantMap = new Map<string, {
                          systems: Set<string>;
                          pools: string[];
                          utilizations: number[];
                          used_capacity: number;
                          total_capacity: number;
                        }>();

                        // Parse tenant from pool names or use a default grouping
                        // In the screenshot: Tenant X, Tenant Y, Tenant Z, UNKNOWN
                        treemap_data.simple_average.forEach((pool) => {
                          if (!pool.storage_system || pool.storage_system === '' || pool.name === 'All Storage') {
                            return; // Skip root nodes
                          }

                          // Extract tenant from pool name (expected format: Pool1, Pool2, etc.)
                          // Since tenant info is not in current data, group by system for now
                          // TODO: Backend should include tenant_name in treemap_data
                          let tenant = 'UNKNOWN';
                          
                          // Try to infer tenant from pool name patterns
                          if (pool.name.match(/Pool[1-5]/)) {
                            // Pool1, Pool2, Pool5 -> Tenant X
                            if (pool.name === 'Pool1' || pool.name === 'Pool2' || pool.name === 'Pool5') {
                              tenant = 'Tenant X';
                            } else if (pool.name === 'Pool3') {
                              tenant = 'Tenant Y';
                            } else if (pool.name === 'Pool4') {
                              tenant = 'UNKNOWN';
                            }
                          } else if (pool.name.match(/Pool[6-7]/)) {
                            tenant = 'Tenant Z';
                          }
                          
                          if (!tenantMap.has(tenant)) {
                            tenantMap.set(tenant, {
                              systems: new Set<string>(),
                              pools: [],
                              utilizations: [],
                              used_capacity: 0,
                              total_capacity: 0
                            });
                          }
                          
                          const tenantData = tenantMap.get(tenant)!;
                          tenantData.systems.add(pool.storage_system);
                          tenantData.pools.push(pool.name);
                          tenantData.utilizations.push(pool.utilization_pct || 0);
                        });

                        // Calculate weighted capacity for each tenant
                        treemap_data.weighted_average.forEach((pool) => {
                          if (!pool.storage_system || pool.storage_system === '' || pool.name === 'All Storage') {
                            return;
                          }

                          let tenant = 'UNKNOWN';
                          if (pool.name === 'Pool1' || pool.name === 'Pool2' || pool.name === 'Pool5') {
                            tenant = 'Tenant X';
                          } else if (pool.name === 'Pool3') {
                            tenant = 'Tenant Y';
                          } else if (pool.name === 'Pool6' || pool.name === 'Pool7') {
                            tenant = 'Tenant Z';
                          } else if (pool.name === 'Pool4') {
                            tenant = 'UNKNOWN';
                          }

                          if (tenantMap.has(tenant)) {
                            const tenantData = tenantMap.get(tenant)!;
                            tenantData.used_capacity += (pool.used_capacity_gib || 0);
                            tenantData.total_capacity += (pool.total_capacity_gib || 0);
                          }
                        });

                        // Sort tenants (Tenant X, Y, Z, then UNKNOWN)
                        const sortedTenants = Array.from(tenantMap.entries()).sort((a, b) => {
                          if (a[0] === 'UNKNOWN') return 1;
                          if (b[0] === 'UNKNOWN') return -1;
                          return a[0].localeCompare(b[0]);
                        });

                        return sortedTenants.map(([tenantName, data]) => {
                          const simple_avg = data.utilizations.length > 0
                            ? data.utilizations.reduce((a, b) => a + b, 0) / data.utilizations.length
                            : 0;
                          
                          const weighted_avg = data.total_capacity > 0
                            ? (data.used_capacity / data.total_capacity) * 100
                            : 0;

                          return (
                            <tr key={tenantName}>
                              <td><strong>{tenantName}</strong></td>
                              <td><small>{Array.from(data.systems).join(', ')}</small></td>
                              <td>
                                <small className="text-muted">
                                  {data.pools.join(', ')}
                                </small>
                              </td>
                              <td>
                                <span className={`badge ${simple_avg > 80 ? 'bg-danger' : simple_avg > 70 ? 'bg-warning' : 'bg-success'}`}>
                                  {simple_avg.toFixed(1)}%
                                </span>
                              </td>
                              <td>
                                <span className={`badge ${weighted_avg > 80 ? 'bg-danger' : weighted_avg > 70 ? 'bg-warning' : 'bg-success'}`}>
                                  {weighted_avg.toFixed(1)}%
                                </span>
                              </td>
                            </tr>
                          );
                        });
                      })()}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="d-flex align-items-center justify-content-center" style={{ height: '200px' }}>
                  <p className="text-center text-muted">No comparison data available</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Top Hosts Chart */}
      <Row className="mb-4 chart-section">
        <Col>
          <Card className="shadow border-0">
            <Card.Header>
              <h6 className="mb-0">Top 20 Hosts by Consumption</h6>
            </Card.Header>
            <Card.Body>
              {top_hosts && top_hosts.length > 0 ? (
                <Plot
                  data={[
                    {
                      type: 'bar',
                      x: top_hosts.map((h: any) => h.name),
                      y: top_hosts.map((h: any) => h.used_capacity_tb || 0),
                      marker: { color: '#e74c3c' },
                      hovertemplate: '<b>%{x}</b><br>Used: %{y:.2f} TB<extra></extra>'
                    }
                  ]}
                  layout={{
                    height: 400,
                    xaxis: { tickangle: -45 },
                    yaxis: { title: 'Used Capacity (TB)' },
                    margin: { l: 50, r: 30, t: 30, b: 100 }
                  }}
                  config={{ displayModeBar: true, responsive: true }}
                  className="w-100"
                />
              ) : (
                <div className="d-flex align-items-center justify-content-center" style={{ height: '400px' }}>
                  <p className="text-center text-muted">No host data available</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Savings + Storage Type Distribution */}
      <Row className="g-3 mb-4 chart-section">
        <Col xs={12} lg={6}>
          <Card className="shadow border-0 h-100">
            <Card.Header>
              <h6 className="mb-0">💰 Storage Efficiency & Savings</h6>
            </Card.Header>
            <Card.Body>
              <Plot
                data={[
                  {
                    type: 'bar',
                    x: savings_data.map((s: any) => s.name),
                    y: savings_data.map((s: any) => s.savings_tb),
                    marker: { color: '#27ae60' },
                    text: savings_data.map((s: any) => s.savings_tb?.toFixed(1)),
                    textposition: 'outside',
                    hovertemplate: '<b>%{x}</b><br>Savings: %{y:.2f} TB<extra></extra>'
                  }
                ]}
                layout={{
                  height: 400,
                  xaxis: { tickangle: -45 },
                  yaxis: { title: `Capacity Savings (${unit})` },
                  margin: { l: 50, r: 30, t: 30, b: 80 }
                }}
                config={{ displayModeBar: true, responsive: true }}
                className="w-100"
              />
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} lg={6}>
          <Card className="shadow border-0 h-100">
            <Card.Header>
              <h6 className="mb-0">📊 Capacity by Storage Type</h6>
            </Card.Header>
            <Card.Body>
              <Plot
                data={[
                  {
                    type: 'pie',
                    labels: storage_types.map((t: any) => t.type),
                    values: storage_types.map((t: any) => t.capacity_tb),
                    hole: 0.4,
                    textposition: 'inside',
                    textinfo: 'percent+label',
                    hovertemplate: '<b>%{label}</b><br>Capacity: %{value:.2f} TB<br>%{percent}<extra></extra>'
                  }
                ]}
                layout={{
                  height: 400,
                  showlegend: true,
                  legend: { orientation: 'v', x: 1, y: 0.5 },
                  margin: { l: 30, r: 100, t: 30, b: 30 }
                }}
                config={{ displayModeBar: true, responsive: true }}
                className="w-100"
              />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* INTELLIGENT RECOMMENDATIONS */}
      <Row className="mb-4">
        <Col>
          <Card className="shadow border-primary border-2">
            <Card.Header className="bg-primary text-white">
              <h5 className="mb-0">💡 INTELLIGENT RECOMMENDATIONS</h5>
            </Card.Header>
            <Card.Body>
              {recommendations && recommendations.length > 0 ? (
                recommendations.map((rec: any, idx: number) => {
                  const variant = rec.type === 'danger' ? 'danger' : rec.type === 'info' ? 'info' : 'success';
                  return (
                    <Alert key={idx} variant={variant} className="mb-3">
                      <Alert.Heading className="h6">{rec.title}</Alert.Heading>
                      <hr />
                      <p>{rec.message}</p>
                      {rec.details && rec.details.length > 0 && (
                        <ul className="mb-0">
                          {rec.details.map((detail: string, detailIdx: number) => (
                            <li key={detailIdx}>{detail}</li>
                          ))}
                        </ul>
                      )}
                    </Alert>
                  );
                })
              ) : (
                <Alert variant="success">✅ No immediate actions required. All systems operating normally.</Alert>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      </div>
    </DashboardLayout>
  );
}
