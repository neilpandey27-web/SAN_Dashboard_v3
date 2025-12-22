'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { FaServer, FaUser, FaLock, FaEnvelope } from 'react-icons/fa';
import { useAuth } from '@/lib/auth';
import { authAPI } from '@/lib/api';

interface Tenant {
  id: number;
  name: string;
  description?: string;
}

export default function AuthPage() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();
  
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [tenants, setTenants] = useState<Tenant[]>([]);
  
  // Form fields
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [tenantId, setTenantId] = useState<number | ''>('');

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.push('/overview');
    }
  }, [isAuthenticated, authLoading, router]);

  // Load tenants for signup
  useEffect(() => {
    if (!isLogin) {
      loadTenants();
    }
  }, [isLogin]);

  const loadTenants = async () => {
    try {
      const response = await authAPI.getTenants();
      setTenants(response.data);
    } catch (err) {
      console.error('Failed to load tenants:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsLoading(true);

    try {
      if (isLogin) {
        await login(username, password);
        router.push('/overview');
      } else {
        // Signup
        if (!tenantId) {
          setError('Please select a tenant');
          setIsLoading(false);
          return;
        }
        
        await authAPI.signup({
          username,
          first_name: firstName,
          last_name: lastName,
          email,
          password,
          tenant_id: tenantId as number,
        });
        
        setSuccess('Registration successful! Your account is pending approval. You will receive an email once approved.');
        // Clear form
        setUsername('');
        setFirstName('');
        setLastName('');
        setEmail('');
        setPassword('');
        setTenantId('');
        // Switch to login after 3 seconds
        setTimeout(() => {
          setIsLogin(true);
          setSuccess('');
        }, 3000);
      }
    } catch (err: any) {
      const message = err.response?.data?.detail || 'An error occurred. Please try again.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="loading-spinner" style={{ minHeight: '100vh' }}>
        <Spinner animation="border" />
      </div>
    );
  }

  return (
    <Container fluid className="min-vh-100 d-flex align-items-center justify-content-center py-5">
      <Row className="w-100 justify-content-center">
        <Col xs={12} sm={10} md={8} lg={5} xl={4}>
          <div className="text-center mb-4">
            <FaServer className="mb-3" style={{ fontSize: '3rem', color: 'var(--primary)' }} />
            <h1 className="h3 mb-1">OneIT SAN Analytics</h1>
            <p className="text-muted">Storage Capacity Monitoring Dashboard</p>
          </div>
          
          <Card className="shadow">
            <Card.Header className="text-center py-3">
              <div className="btn-group w-100">
                <Button
                  variant={isLogin ? 'primary' : 'outline-primary'}
                  onClick={() => { setIsLogin(true); setError(''); setSuccess(''); }}
                >
                  Login
                </Button>
                <Button
                  variant={!isLogin ? 'primary' : 'outline-primary'}
                  onClick={() => { setIsLogin(false); setError(''); setSuccess(''); }}
                >
                  Sign Up
                </Button>
              </div>
            </Card.Header>
            
            <Card.Body className="p-4">
              {error && <Alert variant="danger">{error}</Alert>}
              {success && <Alert variant="success">{success}</Alert>}
              
              <Form onSubmit={handleSubmit}>
                {!isLogin && (
                  <Row className="mb-3">
                    <Col>
                      <Form.Group>
                        <Form.Label>
                          <FaUser className="me-2" />
                          First Name
                        </Form.Label>
                        <Form.Control
                          type="text"
                          placeholder="John"
                          value={firstName}
                          onChange={(e) => setFirstName(e.target.value)}
                          required
                        />
                      </Form.Group>
                    </Col>
                    <Col>
                      <Form.Group>
                        <Form.Label>Last Name</Form.Label>
                        <Form.Control
                          type="text"
                          placeholder="Doe"
                          value={lastName}
                          onChange={(e) => setLastName(e.target.value)}
                          required
                        />
                      </Form.Group>
                    </Col>
                  </Row>
                )}
                
                <Form.Group className="mb-3">
                  <Form.Label>
                    <FaUser className="me-2" />
                    Username
                  </Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="admin"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    minLength={3}
                    maxLength={50}
                    pattern="[a-zA-Z0-9_]+"
                  />
                  {!isLogin && (
                    <Form.Text className="text-muted">
                      3-50 characters, letters, numbers, and underscores only
                    </Form.Text>
                  )}
                </Form.Group>
                
                {!isLogin && (
                  <Form.Group className="mb-3">
                    <Form.Label>
                      <FaEnvelope className="me-2" />
                      Email Address
                    </Form.Label>
                    <Form.Control
                      type="email"
                      placeholder="you@company.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </Form.Group>
                )}
                
                <Form.Group className="mb-3">
                  <Form.Label>
                    <FaLock className="me-2" />
                    Password
                  </Form.Label>
                  <Form.Control
                    type="password"
                    placeholder={isLogin ? 'Enter your password' : 'Min 8 chars, 1 uppercase, 1 number'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                  />
                  {!isLogin && (
                    <Form.Text className="text-muted">
                      Minimum 8 characters, at least 1 uppercase letter and 1 number
                    </Form.Text>
                  )}
                </Form.Group>
                
                {!isLogin && (
                  <Form.Group className="mb-4">
                    <Form.Label>
                      <FaServer className="me-2" />
                      Select Tenant
                    </Form.Label>
                    <Form.Select
                      value={tenantId}
                      onChange={(e) => setTenantId(Number(e.target.value) || '')}
                      required
                    >
                      <option value="">Choose a tenant...</option>
                      {tenants.map((tenant) => (
                        <option key={tenant.id} value={tenant.id}>
                          {tenant.name} {tenant.description && `- ${tenant.description}`}
                        </option>
                      ))}
                    </Form.Select>
                  </Form.Group>
                )}
                
                <Button
                  variant="primary"
                  type="submit"
                  className="w-100 py-2"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Spinner animation="border" size="sm" className="me-2" />
                      {isLogin ? 'Logging in...' : 'Creating account...'}
                    </>
                  ) : (
                    isLogin ? 'Login' : 'Create Account'
                  )}
                </Button>
              </Form>
              
              {isLogin && (
                <div className="text-center mt-3">
                  <small className="text-muted">
                    Demo credentials: admin / admin123
                  </small>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}
