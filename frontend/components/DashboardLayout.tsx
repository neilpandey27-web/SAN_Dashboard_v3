'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { Container, Navbar, Nav, Dropdown, Badge, Spinner } from 'react-bootstrap';
import {
  FaServer, FaChartLine, FaDatabase, FaHistory, FaFileAlt,
  FaUsers, FaBell, FaSignOutAlt, FaUser, FaTachometerAlt
} from 'react-icons/fa';
import { useAuth } from '@/lib/auth';
import { alertsAPI, usersAPI } from '@/lib/api';
// ✏️ CHANGE 1: Add TenantFilter import
import TenantFilter from '@/components/TenantFilter';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, isAdmin, logout } = useAuth();

  const [alertCount, setAlertCount] = useState(0);
  const [pendingUsers, setPendingUsers] = useState(0);
  const [alerts, setAlerts] = useState<any[]>([]);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth');
    }
  }, [isAuthenticated, isLoading, router]);

  // Load alert count
  useEffect(() => {
    if (isAuthenticated) {
      loadAlerts();
      if (isAdmin) {
        loadPendingUsers();
      }
    }
  }, [isAuthenticated, isAdmin]);

  const loadAlerts = async () => {
    try {
      const response = await alertsAPI.getUnacknowledged();
      setAlertCount(response.data.total);
      setAlerts(response.data.alerts || []);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    }
  };

  const loadPendingUsers = async () => {
    try {
      const response = await usersAPI.getPendingCount();
      setPendingUsers(response.data.count);
    } catch (err) {
      console.error('Failed to load pending users:', err);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push('/auth');
  };

  const handleAcknowledgeAlert = async (alertId: number) => {
    try {
      await alertsAPI.acknowledge(alertId);
      loadAlerts();
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="loading-spinner" style={{ minHeight: '100vh' }}>
        <Spinner animation="border" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const navItems = [
    { href: '/overview', label: 'Overview', icon: FaTachometerAlt },
    { href: '/systems', label: 'Storage Systems', icon: FaServer },
    { href: '/historical', label: 'Historical', icon: FaHistory },
    { href: '/reports', label: 'Reports', icon: FaFileAlt },
  ];

  const adminNavItems = [
    { href: '/db-mgmt', label: 'Database Mgmt', icon: FaDatabase },
    { href: '/user-mgmt', label: 'User Mgmt', icon: FaUsers, badge: pendingUsers },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* Top Navigation */}
      <Navbar expand="lg" className="px-3" style={{ flexShrink: 0 }}>
        <Container fluid>
          <Navbar.Brand as={Link} href="/overview" className="d-flex align-items-center">
            <FaServer className="me-2" style={{ color: 'var(--primary)' }} />
            <span className="fw-bold">OneIT SAN Analytics</span>
          </Navbar.Brand>

          <Navbar.Toggle aria-controls="main-nav" />

          <Navbar.Collapse id="main-nav">
            <Nav className="me-auto">
              {navItems.map((item) => (
                <Nav.Link
                  key={item.href}
                  as={Link}
                  href={item.href}
                  active={pathname === item.href}
                  className="d-flex align-items-center"
                >
                  <item.icon className="me-1" />
                  {item.label}
                </Nav.Link>
              ))}

              {isAdmin && adminNavItems.map((item) => (
                <Nav.Link
                  key={item.href}
                  as={Link}
                  href={item.href}
                  active={pathname === item.href}
                  className="d-flex align-items-center"
                >
                  <item.icon className="me-1" />
                  {item.label}
                  {item.badge && item.badge > 0 && (
                    <Badge bg="danger" className="ms-1">{item.badge}</Badge>
                  )}
                </Nav.Link>
              ))}
            </Nav>

            <Nav className="align-items-center">
              {/* ✏️ CHANGE 2: Add TenantFilter component here (BEFORE notifications bell) */}
              <TenantFilter />

              {/* Notifications Bell */}
              <Dropdown align="end" className="me-3">
                <Dropdown.Toggle
                  variant="link"
                  className="notification-bell p-0 text-light"
                  style={{ textDecoration: 'none' }}
                >
                  <FaBell size={20} />
                  {alertCount > 0 && (
                    <span className="notification-badge">{alertCount > 9 ? '9+' : alertCount}</span>
                  )}
                </Dropdown.Toggle>

                <Dropdown.Menu style={{ minWidth: '350px', maxHeight: '400px', overflowY: 'auto' }}>
                  <Dropdown.Header className="d-flex justify-content-between align-items-center">
                    <span>Alerts</span>
                    {alertCount > 0 && (
                      <Badge bg="danger">{alertCount} unacknowledged</Badge>
                    )}
                  </Dropdown.Header>
                  <Dropdown.Divider />

                  {alerts.length === 0 ? (
                    <Dropdown.ItemText className="text-center text-muted py-3">
                      No active alerts
                    </Dropdown.ItemText>
                  ) : (
                    alerts.slice(0, 5).map((alert) => (
                      <Dropdown.Item
                        key={alert.id}
                        className="d-flex justify-content-between align-items-start py-2"
                        onClick={() => handleAcknowledgeAlert(alert.id)}
                      >
                        <div className="flex-grow-1">
                          <div className="d-flex align-items-center mb-1">
                            <Badge
                              bg={alert.level === 'emergency' || alert.level === 'critical' ? 'danger' : 'warning'}
                              className="me-2"
                            >
                              {alert.level.toUpperCase()}
                            </Badge>
                            <small className="text-muted">
                              {alert.utilization_pct?.toFixed(1)}%
                            </small>
                          </div>
                          <div className="fw-medium">{alert.pool_name}</div>
                          <small className="text-muted">{alert.storage_system}</small>
                        </div>
                      </Dropdown.Item>
                    ))
                  )}

                  {alerts.length > 5 && (
                    <>
                      <Dropdown.Divider />
                      <Dropdown.Item as={Link} href="/overview" className="text-center">
                        View all alerts
                      </Dropdown.Item>
                    </>
                  )}
                </Dropdown.Menu>
              </Dropdown>

              {/* User Menu */}
              <Dropdown align="end">
                <Dropdown.Toggle variant="link" className="text-light d-flex align-items-center" style={{ textDecoration: 'none' }}>
                  <FaUser className="me-2" />
                  <span>{user?.first_name} {user?.last_name}</span>
                  {isAdmin && <Badge bg="primary" className="ms-2">Admin</Badge>}
                </Dropdown.Toggle>

                <Dropdown.Menu>
                  <Dropdown.Header>
                    {user?.email}
                  </Dropdown.Header>
                  <Dropdown.Divider />
                  <Dropdown.Item>
                    <small className="text-muted">
                      Tenants: {user?.tenants.map(t => t.name).join(', ') || 'All'}
                    </small>
                  </Dropdown.Item>
                  <Dropdown.Divider />
                  <Dropdown.Item onClick={handleLogout} className="text-danger">
                    <FaSignOutAlt className="me-2" />
                    Logout
                  </Dropdown.Item>
                </Dropdown.Menu>
              </Dropdown>
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      {/* Main Content - Scrollable */}
      <main style={{ flex: 1, overflow: 'auto', paddingTop: '1.5rem', paddingBottom: '1.5rem' }}>
        <Container fluid className="px-4">
          {children}
        </Container>
      </main>

      {/* Footer - Fixed at bottom of viewport */}
      <footer className="py-2 text-muted" style={{ flexShrink: 0, borderTop: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
        <Container fluid className="px-4">
          <div className="d-flex justify-content-between align-items-center">
            <div style={{ flex: 1 }}></div>
            <div className="text-center" style={{ flex: 1 }}>
              <small>OneIT SAN Analytics Dashboard v2.0.0</small>
            </div>
            <div className="text-end" style={{ flex: 1 }}>
              <small>Nilesh Pandey</small>
            </div>
          </div>
        </Container>
      </footer>
    </div>
  );
}
