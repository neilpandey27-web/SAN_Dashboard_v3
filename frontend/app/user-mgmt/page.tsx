'use client';

import { useState, useEffect } from 'react';
import { Row, Col, Card, Form, Button, Table, Alert, Spinner, Badge, Modal, Nav, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { FaUsers, FaUserPlus, FaEdit, FaTrash, FaCheck, FaTimes, FaUserSlash, FaUserCheck, FaHistory, FaClock } from 'react-icons/fa';
import DashboardLayout from '@/components/DashboardLayout';
import { usersAPI } from '@/lib/api';
import { useAuth } from '@/lib/auth';

interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  status: string;
  expiration_date?: string;
  last_login?: string;
  created_at: string;
  tenants: Array<{
    id: number;
    name: string;
    description?: string;
    created_at: string;
  }>;
}

interface Tenant {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  user_count: number;
}

export default function UserManagementPage() {
  const { isAdmin } = useAuth();

  // Tab state
  const [activeTab, setActiveTab] = useState<'all-users' | 'pending' | 'activity'>('all-users');

  // Users state
  const [users, setUsers] = useState<User[]>([]);
  const [usersLoading, setUsersLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [roleFilter, setRoleFilter] = useState<string>('');

  // Pending users state
  const [pendingUsers, setPendingUsers] = useState<User[]>([]);
  const [pendingLoading, setPendingLoading] = useState(true);

  // Tenants state
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [tenantsLoading, setTenantsLoading] = useState(true);

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editForm, setEditForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    role: '',
    status: '',
    tenant_ids: [] as number[],
    expiration_date: ''
  });
  const [editLoading, setEditLoading] = useState(false);

  // Activity logs state
  const [activityLogs, setActivityLogs] = useState<any[]>([]);
  const [activityLoading, setActivityLoading] = useState(true);

  // Create tenant modal state
  const [showCreateTenantModal, setShowCreateTenantModal] = useState(false);
  const [newTenantName, setNewTenantName] = useState('');
  const [newTenantDescription, setNewTenantDescription] = useState('');
  const [createTenantLoading, setCreateTenantLoading] = useState(false);

  // Edit tenant modal state
  const [showEditTenantModal, setShowEditTenantModal] = useState(false);
  const [editingTenant, setEditingTenant] = useState<Tenant | null>(null);
  const [editTenantForm, setEditTenantForm] = useState({
    name: '',
    description: ''
  });
  const [editTenantLoading, setEditTenantLoading] = useState(false);

  useEffect(() => {
    if (isAdmin) {
      loadUsers();
      loadPendingUsers();
      loadTenants();
      if (activeTab === 'activity') {
        loadActivityLogs();
      }
    }
  }, [isAdmin, activeTab, statusFilter, roleFilter]);

  const loadUsers = async () => {
    try {
      setUsersLoading(true);
      const response = await usersAPI.getUsers({
        status_filter: statusFilter || undefined,
        role_filter: roleFilter || undefined
      });
      setUsers(response.data);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setUsersLoading(false);
    }
  };

  const loadPendingUsers = async () => {
    try {
      setPendingLoading(true);
      const response = await usersAPI.getPending();
      setPendingUsers(response.data);
    } catch (err) {
      console.error('Failed to load pending users:', err);
    } finally {
      setPendingLoading(false);
    }
  };

  const loadTenants = async () => {
    try {
      setTenantsLoading(true);
      const response = await usersAPI.getTenants();
      setTenants(response.data);
    } catch (err) {
      console.error('Failed to load tenants:', err);
    } finally {
      setTenantsLoading(false);
    }
  };

  const loadActivityLogs = async () => {
    try {
      setActivityLoading(true);
      const response = await usersAPI.getActivityLogs({ limit: 50 });
      setActivityLogs(response.data);
    } catch (err) {
      console.error('Failed to load activity logs:', err);
    } finally {
      setActivityLoading(false);
    }
  };

  const handleApproveUser = async (userId: number, userEmail: string) => {
    if (!confirm(`Approve user ${userEmail}?`)) return;

    try {
      await usersAPI.approveUser(userId);
      alert(`User ${userEmail} approved successfully!`);
      loadPendingUsers();
      loadUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve user');
    }
  };

  const handleRejectUser = async (userId: number, userEmail: string) => {
    if (!confirm(`Reject and remove user ${userEmail}? This action cannot be undone.`)) return;

    try {
      await usersAPI.rejectUser(userId);
      alert(`User ${userEmail} rejected successfully`);
      loadPendingUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to reject user');
    }
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setEditForm({
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email,
      role: user.role,
      status: user.status,
      tenant_ids: user.tenants.map(t => t.id),
      expiration_date: user.expiration_date ? user.expiration_date.split('T')[0] : ''
    });
    setShowEditModal(true);
  };

  const handleUpdateUser = async () => {
    if (!editingUser) return;

    try {
      setEditLoading(true);
      await usersAPI.editUser(editingUser.id, {
        first_name: editForm.first_name,
        last_name: editForm.last_name,
        email: editForm.email,
        role: editForm.role,
        status: editForm.status,
        tenant_ids: editForm.tenant_ids,
        expiration_date: editForm.expiration_date || null
      });
      alert('User updated successfully!');
      setShowEditModal(false);
      loadUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update user');
    } finally {
      setEditLoading(false);
    }
  };

  const handleDeleteUser = async (userId: number, userEmail: string) => {
    if (!confirm(`Delete user ${userEmail}? This action cannot be undone.`)) return;

    const confirmSecond = confirm(`FINAL CONFIRMATION: Permanently delete ${userEmail}?`);
    if (!confirmSecond) return;

    try {
      await usersAPI.deleteUser(userId);
      alert(`User ${userEmail} deleted successfully`);
      loadUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete user');
    }
  };

  const handleDeactivateUser = async (userId: number, userEmail: string) => {
    if (!confirm(`Deactivate user ${userEmail}?`)) return;

    try {
      await usersAPI.deactivateUser(userId);
      alert(`User ${userEmail} deactivated`);
      loadUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to deactivate user');
    }
  };

  const handleActivateUser = async (userId: number, userEmail: string) => {
    if (!confirm(`Activate user ${userEmail}?`)) return;

    try {
      await usersAPI.activateUser(userId);
      alert(`User ${userEmail} activated`);
      loadUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to activate user');
    }
  };

  const handleCreateTenant = async () => {
    if (!newTenantName.trim()) {
      alert('Please enter a tenant name');
      return;
    }

    try {
      setCreateTenantLoading(true);
      await usersAPI.createTenant(newTenantName, newTenantDescription || undefined);
      alert(`Tenant "${newTenantName}" created successfully!`);
      setShowCreateTenantModal(false);
      setNewTenantName('');
      setNewTenantDescription('');
      loadTenants();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create tenant');
    } finally {
      setCreateTenantLoading(false);
    }
  };

  const handleEditTenant = (tenant: Tenant) => {
    setEditingTenant(tenant);
    setEditTenantForm({
      name: tenant.name,
      description: tenant.description || ''
    });
    setShowEditTenantModal(true);
  };

  const handleUpdateTenant = async () => {
    if (!editingTenant) return;

    if (!editTenantForm.name.trim()) {
      alert('Please enter a tenant name');
      return;
    }

    try {
      setEditTenantLoading(true);
      await usersAPI.updateTenant(
        editingTenant.id,
        editTenantForm.name,
        editTenantForm.description || undefined
      );
      alert(`Tenant "${editTenantForm.name}" updated successfully!`);
      setShowEditTenantModal(false);
      setEditingTenant(null);
      loadTenants();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update tenant');
    } finally {
      setEditTenantLoading(false);
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role.toLowerCase()) {
      case 'admin': return 'danger';
      case 'user': return 'primary';
      case 'viewer': return 'secondary';
      default: return 'secondary';
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return 'success';
      case 'pending': return 'warning';
      case 'deactivated': return 'secondary';
      default: return 'secondary';
    }
  };

  if (!isAdmin) {
    return (
      <DashboardLayout>
        <Alert variant="danger">
          <Alert.Heading>Access Denied</Alert.Heading>
          <p className="mb-0">You do not have permission to access this page. Only administrators can manage users.</p>
        </Alert>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      {/* Page Header */}
      <div className="page-header">
        <h1>
          <FaUsers className="me-2" />
          User Management
        </h1>
        <p className="text-muted">Manage user accounts, roles, and permissions</p>
      </div>

      {/* Navigation Tabs */}
      <Nav variant="tabs" className="mb-4">
        <Nav.Item>
          <Nav.Link
            active={activeTab === 'all-users'}
            onClick={() => setActiveTab('all-users')}
          >
            <FaUsers className="me-2" />
            All Users ({users.length})
          </Nav.Link>
        </Nav.Item>
        <Nav.Item>
          <Nav.Link
            active={activeTab === 'pending'}
            onClick={() => setActiveTab('pending')}
          >
            <FaClock className="me-2" />
            Pending Approval ({pendingUsers.length})
          </Nav.Link>
        </Nav.Item>
        <Nav.Item>
          <Nav.Link
            active={activeTab === 'activity'}
            onClick={() => setActiveTab('activity')}
          >
            <FaHistory className="me-2" />
            Activity Logs
          </Nav.Link>
        </Nav.Item>
      </Nav>

      {/* All Users Tab */}
      {activeTab === 'all-users' && (
        <>
          {/* Filters */}
          <Card className="mb-4">
            <Card.Body>
              <Row>
                <Col md={4}>
                  <Form.Group>
                    <Form.Label>Filter by Status</Form.Label>
                    <Form.Select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                    >
                      <option value="">All Statuses</option>
                      <option value="active">Active</option>
                      <option value="pending">Pending</option>
                      <option value="deactivated">Deactivated</option>
                    </Form.Select>
                  </Form.Group>
                </Col>
                <Col md={4}>
                  <Form.Group>
                    <Form.Label>Filter by Role</Form.Label>
                    <Form.Select
                      value={roleFilter}
                      onChange={(e) => setRoleFilter(e.target.value)}
                    >
                      <option value="">All Roles</option>
                      <option value="admin">Admin</option>
                      <option value="user">User</option>
                      <option value="viewer">Viewer</option>
                    </Form.Select>
                  </Form.Group>
                </Col>
                <Col md={4} className="d-flex align-items-end">
                  <Button
                    variant="outline-secondary"
                    onClick={() => {
                      setStatusFilter('');
                      setRoleFilter('');
                    }}
                  >
                    Clear Filters
                  </Button>
                </Col>
              </Row>
            </Card.Body>
          </Card>

          {/* Users Table */}
          <Card>
            <Card.Header>
              <h5 className="mb-0">All Users</h5>
            </Card.Header>
            <Card.Body className="p-0">
              {usersLoading ? (
                <div className="text-center py-5">
                  <Spinner animation="border" />
                  <p className="text-muted mt-2">Loading users...</p>
                </div>
              ) : users.length === 0 ? (
                <div className="text-center py-5 text-muted">
                  No users found
                </div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <Table responsive hover className="mb-0">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>Tenants</th>
                        <th>Last Login</th>
                        <th>Created</th>
                        <th className="text-center">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((user) => (
                        <tr key={user.id}>
                          <td>
                            <strong>{user.first_name} {user.last_name}</strong>
                          </td>
                          <td>
                            <small>{user.email}</small>
                          </td>
                          <td>
                            <Badge bg={getRoleBadgeColor(user.role)}>
                              {user.role.toUpperCase()}
                            </Badge>
                          </td>
                          <td>
                            <Badge bg={getStatusBadgeColor(user.status)}>
                              {user.status.toUpperCase()}
                            </Badge>
                          </td>
                          <td>
                            {user.tenants.length > 0 ? (
                              user.tenants.map((t) => (
                                <Badge key={t.id} bg="info" className="me-1">
                                  {t.name}
                                </Badge>
                              ))
                            ) : (
                              <span className="text-muted">-</span>
                            )}
                          </td>
                          <td>
                            <small>
                              {user.last_login
                                ? new Date(user.last_login).toLocaleString()
                                : 'Never'}
                            </small>
                          </td>
                          <td>
                            <small>{new Date(user.created_at).toLocaleDateString()}</small>
                          </td>
                          <td>
                            <div className="d-flex gap-1 justify-content-center">
                              <OverlayTrigger overlay={<Tooltip>Edit User</Tooltip>}>
                                <Button
                                  variant="outline-primary"
                                  size="sm"
                                  onClick={() => handleEditUser(user)}
                                >
                                  <FaEdit />
                                </Button>
                              </OverlayTrigger>

                              {user.status === 'active' ? (
                                <OverlayTrigger overlay={<Tooltip>Deactivate</Tooltip>}>
                                  <Button
                                    variant="outline-warning"
                                    size="sm"
                                    onClick={() => handleDeactivateUser(user.id, user.email)}
                                  >
                                    <FaUserSlash />
                                  </Button>
                                </OverlayTrigger>
                              ) : user.status === 'deactivated' ? (
                                <OverlayTrigger overlay={<Tooltip>Activate</Tooltip>}>
                                  <Button
                                    variant="outline-success"
                                    size="sm"
                                    onClick={() => handleActivateUser(user.id, user.email)}
                                  >
                                    <FaUserCheck />
                                  </Button>
                                </OverlayTrigger>
                              ) : null}

                              <OverlayTrigger overlay={<Tooltip>Delete User</Tooltip>}>
                                <Button
                                  variant="outline-danger"
                                  size="sm"
                                  onClick={() => handleDeleteUser(user.id, user.email)}
                                >
                                  <FaTrash />
                                </Button>
                              </OverlayTrigger>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </div>
              )}
            </Card.Body>
          </Card>

          {/* Tenants Management */}
          <Card className="mt-4">
            <Card.Header>
              <div className="d-flex justify-content-between align-items-center">
                <h5 className="mb-0">Tenants ({tenants.length})</h5>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setShowCreateTenantModal(true)}
                >
                  <FaUserPlus className="me-1" />
                  Create Tenant
                </Button>
              </div>
            </Card.Header>
            <Card.Body className="p-0">
              {tenantsLoading ? (
                <div className="text-center py-4">
                  <Spinner animation="border" />
                </div>
              ) : tenants.length === 0 ? (
                <div className="text-center py-4 text-muted">
                  No tenants configured
                </div>
              ) : (
                <Table responsive hover className="mb-0">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Description</th>
                      <th>Users</th>
                      <th>Created</th>
                      <th className="text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tenants.map((tenant) => (
                      <tr key={tenant.id}>
                        <td>
                          <strong>{tenant.name}</strong>
                        </td>
                        <td>
                          <small>{tenant.description || '-'}</small>
                        </td>
                        <td>
                          <Badge bg="primary">{tenant.user_count}</Badge>
                        </td>
                        <td>
                          <small>{new Date(tenant.created_at).toLocaleDateString()}</small>
                        </td>
                        <td className="text-center">
                          <OverlayTrigger overlay={<Tooltip>Edit Tenant</Tooltip>}>
                            <Button
                              variant="outline-primary"
                              size="sm"
                              onClick={() => handleEditTenant(tenant)}
                            >
                              <FaEdit />
                            </Button>
                          </OverlayTrigger>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        </>
      )}

      {/* Pending Users Tab */}
      {activeTab === 'pending' && (
        <Card>
          <Card.Header>
            <h5 className="mb-0">Pending User Approvals</h5>
          </Card.Header>
          <Card.Body className="p-0">
            {pendingLoading ? (
              <div className="text-center py-5">
                <Spinner animation="border" />
                <p className="text-muted mt-2">Loading pending users...</p>
              </div>
            ) : pendingUsers.length === 0 ? (
              <Alert variant="info" className="m-3">
                No pending user approvals. All users have been processed.
              </Alert>
            ) : (
              <Table responsive hover className="mb-0">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Tenants</th>
                    <th>Requested</th>
                    <th className="text-center">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingUsers.map((user) => (
                    <tr key={user.id}>
                      <td>
                        <strong>{user.first_name} {user.last_name}</strong>
                      </td>
                      <td>
                        <small>{user.email}</small>
                      </td>
                      <td>
                        {user.tenants.map((t) => (
                          <Badge key={t.id} bg="info" className="me-1">
                            {t.name}
                          </Badge>
                        ))}
                      </td>
                      <td>
                        <small>{new Date(user.created_at).toLocaleString()}</small>
                      </td>
                      <td>
                        <div className="d-flex gap-2 justify-content-center">
                          <Button
                            variant="success"
                            size="sm"
                            onClick={() => handleApproveUser(user.id, user.email)}
                          >
                            <FaCheck className="me-1" />
                            Approve
                          </Button>
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => handleRejectUser(user.id, user.email)}
                          >
                            <FaTimes className="me-1" />
                            Reject
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </Card.Body>
        </Card>
      )}

      {/* Activity Logs Tab */}
      {activeTab === 'activity' && (
        <Card>
          <Card.Header>
            <h5 className="mb-0">User Activity Logs</h5>
          </Card.Header>
          <Card.Body className="p-0">
            {activityLoading ? (
              <div className="text-center py-5">
                <Spinner animation="border" />
                <p className="text-muted mt-2">Loading activity logs...</p>
              </div>
            ) : activityLogs.length === 0 ? (
              <div className="text-center py-5 text-muted">
                No activity logs available
              </div>
            ) : (
              <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
                <Table responsive hover className="mb-0">
                  <thead className="sticky-top bg-white">
                    <tr>
                      <th>Timestamp</th>
                      <th>User</th>
                      <th>Action</th>
                      <th>Details</th>
                      <th>IP Address</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activityLogs.map((log) => (
                      <tr key={log.id}>
                        <td>
                          <small>{new Date(log.timestamp).toLocaleString()}</small>
                        </td>
                        <td>
                          <small>{log.user_name}</small>
                        </td>
                        <td>
                          <Badge bg="info">{log.action}</Badge>
                        </td>
                        <td>
                          <small>{log.details}</small>
                        </td>
                        <td>
                          <small>{log.ip_address || '-'}</small>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            )}
          </Card.Body>
        </Card>
      )}

      {/* Edit User Modal */}
      <Modal show={showEditModal} onHide={() => setShowEditModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Edit User</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {editingUser && (
            <Form>
              <Row>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label>First Name</Form.Label>
                    <Form.Control
                      type="text"
                      value={editForm.first_name}
                      onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                    />
                  </Form.Group>
                </Col>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label>Last Name</Form.Label>
                    <Form.Control
                      type="text"
                      value={editForm.last_name}
                      onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                    />
                  </Form.Group>
                </Col>
              </Row>

              <Form.Group className="mb-3">
                <Form.Label>Email</Form.Label>
                <Form.Control
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                />
              </Form.Group>

              <Row>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label>Role</Form.Label>
                    <Form.Select
                      value={editForm.role}
                      onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                    >
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                      <option value="viewer">Viewer</option>
                    </Form.Select>
                  </Form.Group>
                </Col>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label>Status</Form.Label>
                    <Form.Select
                      value={editForm.status}
                      onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                    >
                      <option value="active">Active</option>
                      <option value="pending">Pending</option>
                      <option value="deactivated">Deactivated</option>
                    </Form.Select>
                  </Form.Group>
                </Col>
              </Row>

              <Form.Group className="mb-3">
                <Form.Label>Expiration Date (Optional)</Form.Label>
                <Form.Control
                  type="date"
                  value={editForm.expiration_date}
                  onChange={(e) => setEditForm({ ...editForm, expiration_date: e.target.value })}
                />
                <Form.Text className="text-muted">
                  Leave empty for no expiration
                </Form.Text>
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Tenant Assignments</Form.Label>
                <div>
                  {tenants.map((tenant) => (
                    <Form.Check
                      key={tenant.id}
                      type="checkbox"
                      label={tenant.name}
                      checked={editForm.tenant_ids.includes(tenant.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setEditForm({
                            ...editForm,
                            tenant_ids: [...editForm.tenant_ids, tenant.id]
                          });
                        } else {
                          setEditForm({
                            ...editForm,
                            tenant_ids: editForm.tenant_ids.filter(id => id !== tenant.id)
                          });
                        }
                      }}
                    />
                  ))}
                </div>
              </Form.Group>
            </Form>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowEditModal(false)}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleUpdateUser}
            disabled={editLoading}
          >
            {editLoading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Updating...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Create Tenant Modal */}
      <Modal show={showCreateTenantModal} onHide={() => setShowCreateTenantModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Create New Tenant</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Tenant Name *</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter tenant name"
                value={newTenantName}
                onChange={(e) => setNewTenantName(e.target.value)}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Description (Optional)</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                placeholder="Enter tenant description"
                value={newTenantDescription}
                onChange={(e) => setNewTenantDescription(e.target.value)}
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowCreateTenantModal(false)}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleCreateTenant}
            disabled={createTenantLoading || !newTenantName.trim()}
          >
            {createTenantLoading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Creating...
              </>
            ) : (
              'Create Tenant'
            )}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Edit Tenant Modal */}
      <Modal show={showEditTenantModal} onHide={() => setShowEditTenantModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Edit Tenant</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {editingTenant && (
            <Form>
              <Form.Group className="mb-3">
                <Form.Label>Tenant Name *</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="Enter tenant name"
                  value={editTenantForm.name}
                  onChange={(e) => setEditTenantForm({ ...editTenantForm, name: e.target.value })}
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Description (Optional)</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={3}
                  placeholder="Enter tenant description"
                  value={editTenantForm.description}
                  onChange={(e) => setEditTenantForm({ ...editTenantForm, description: e.target.value })}
                />
              </Form.Group>
            </Form>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowEditTenantModal(false)}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleUpdateTenant}
            disabled={editTenantLoading || !editTenantForm.name.trim()}
          >
            {editTenantLoading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Updating...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </DashboardLayout>
  );
}
