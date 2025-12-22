'use client';

import { useState, useEffect } from 'react';
import { Card, Table, Spinner, Alert, Badge, Form, InputGroup } from 'react-bootstrap';
import { FaServer, FaSearch } from 'react-icons/fa';
import DashboardLayout from '@/components/DashboardLayout';
import { dataAPI } from '@/lib/api';
import { useTenant } from '@/contexts/TenantContext';

interface StorageSystem {
  id: number;
  name: string;
  capacity_tb: number;
  used_tb: number;
  available_tb: number;
  utilization_pct: number;
}

export default function StorageSystemsPage() {
  // v6.1.0: Add tenant context
  const { selectedTenant } = useTenant();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [systems, setSystems] = useState<StorageSystem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredSystems, setFilteredSystems] = useState<StorageSystem[]>([]);
  const [unit, setUnit] = useState<'GiB' | 'TiB' | 'PiB'>('TiB');

  // v6.1.0: Re-fetch data when selectedTenant changes
  useEffect(() => {
    loadSystems();
  }, [selectedTenant]);

  useEffect(() => {
    // Filter systems based on search term
    if (searchTerm.trim() === '') {
      setFilteredSystems(systems);
    } else {
      const term = searchTerm.toLowerCase();
      const filtered = systems.filter(system => 
        system.name.toLowerCase().includes(term)
      );
      setFilteredSystems(filtered);
    }
  }, [searchTerm, systems]);

  const loadSystems = async () => {
    try {
      setLoading(true);
      setError('');
      
      // v6.1.0: Pass tenant filter to API
      const response = await dataAPI.getStorageSystems({
        page: 1,
        page_size: 100,
        ...(selectedTenant && { tenant: selectedTenant })
      });
      
      console.log('API Response:', response.data);
      
      const systemsData = response.data.items || [];
      setSystems(systemsData);
      setFilteredSystems(systemsData);
      
    } catch (err: any) {
      console.error('Failed to load storage systems:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load storage systems');
    } finally {
      setLoading(false);
    }
  };

  // Unit converter for TiB values (data from backend is in TiB)
  const convertCapacityFromTiB = (tib: number): number => {
    if (unit === 'GiB') return tib * 1024;
    if (unit === 'PiB') return tib / 1024;
    return tib; // TiB is default
  };

  const formatCapacity = (tib: number): string => {
    const value = convertCapacityFromTiB(tib);
    return `${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${unit}`;
  };

  const getUtilizationColor = (util: number): string => {
    if (util >= 90) return 'danger';
    if (util >= 80) return 'warning';
    if (util >= 70) return 'info';
    return 'success';
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
          <Spinner animation="border" variant="primary" />
          <span className="ms-3">Loading storage systems...</span>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      {/* Page Header with Unit Switcher */}
      <div className="page-header mb-4">
        <div className="d-flex justify-content-between align-items-center mb-3">
          <div>
            <h1 className="mb-2">
              <FaServer className="me-2" />
              Storage Systems
            </h1>
            <p className="text-muted mb-0">
              View all storage systems with capacity and utilization information
            </p>
          </div>
          <div className="btn-group btn-group-sm" role="group" aria-label="Unit selector">
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
        <hr />
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="danger" dismissible onClose={() => setError('')}>
          <Alert.Heading>Error Loading Data</Alert.Heading>
          <p>{error}</p>
        </Alert>
      )}

      {/* Search Bar */}
      {systems.length > 0 && (
        <Card className="mb-3">
          <Card.Body>
            <InputGroup>
              <InputGroup.Text>
                <FaSearch />
              </InputGroup.Text>
              <Form.Control
                type="text"
                placeholder="Search by system name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </InputGroup>
            <small className="text-muted">
              Showing {filteredSystems.length} of {systems.length} systems
            </small>
          </Card.Body>
        </Card>
      )}

      {/* Data Table */}
      <Card>
        <Card.Body>
          {systems.length === 0 ? (
            <Alert variant="info" className="text-center">
              <Alert.Heading>
                <FaServer className="me-2" />
                No Storage Systems Data
              </Alert.Heading>
              <p className="mb-0">
                No storage systems found in the database. Please upload data in the Database Management tab.
              </p>
            </Alert>
          ) : (
            <div className="table-responsive">
              <Table hover striped>
                <thead>
                  <tr>
                    <th>System Name</th>
                    <th className="text-end">Capacity ({unit})</th>
                    <th className="text-end">Used ({unit})</th>
                    <th className="text-end">Available ({unit})</th>
                    <th className="text-end">Util %</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredSystems.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="text-center text-muted py-4">
                        No systems match your search criteria. Try a different search term.
                      </td>
                    </tr>
                  ) : (
                    filteredSystems.map((system) => (
                      <tr key={system.id}>
                        <td>
                          <strong>{system.name}</strong>
                        </td>
                        <td className="text-end">
                          <strong>{convertCapacityFromTiB(system.capacity_tb).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>
                        </td>
                        <td className="text-end">
                          {convertCapacityFromTiB(system.used_tb).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="text-end">
                          {convertCapacityFromTiB(system.available_tb).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="text-end">
                          <Badge bg={getUtilizationColor(system.utilization_pct)}>
                            {system.utilization_pct.toFixed(1)}%
                          </Badge>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </Table>
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Summary Footer */}
      {systems.length > 0 && (
        <Card className="mt-3">
          <Card.Body>
            <div className="row text-center">
              <div className="col-md-3">
                <h5 className="text-muted mb-1">Total Systems</h5>
                <h3 className="mb-0">{systems.length}</h3>
              </div>
              <div className="col-md-3">
                <h5 className="text-muted mb-1">Total Capacity</h5>
                <h3 className="mb-0">
                  {formatCapacity(systems.reduce((sum, s) => sum + s.capacity_tb, 0))}
                </h3>
              </div>
              <div className="col-md-3">
                <h5 className="text-muted mb-1">Total Used</h5>
                <h3 className="mb-0">
                  {formatCapacity(systems.reduce((sum, s) => sum + s.used_tb, 0))}
                </h3>
              </div>
              <div className="col-md-3">
                <h5 className="text-muted mb-1">Average Utilization</h5>
                <h3 className="mb-0">
                  {systems.length > 0
                    ? (systems.reduce((sum, s) => sum + s.utilization_pct, 0) / systems.length).toFixed(1)
                    : '0.0'}%
                </h3>
              </div>
            </div>
          </Card.Body>
        </Card>
      )}

      <style jsx global>{`
        .table-responsive {
          overflow-x: auto;
        }
        
        .table thead th {
          position: sticky;
          top: 0;
          background-color: #343a40;
          color: white;
          z-index: 10;
        }
        
        .table tbody tr:hover {
          background-color: rgba(255, 255, 255, 0.05);
        }
        
        .page-header h1 {
          margin-bottom: 0.5rem;
        }
        
        .page-header p {
          margin-bottom: 0;
        }
      `}</style>
    </DashboardLayout>
  );
}
