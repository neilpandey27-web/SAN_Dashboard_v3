'use client';

import { useState, useEffect } from 'react';
import { Dropdown } from 'react-bootstrap';
import { useTenant } from '@/contexts/TenantContext';
import { dataAPI } from '@/lib/api';

export default function TenantFilter() {
  const { selectedTenant, setSelectedTenant } = useTenant();
  const [tenants, setTenants] = useState<string[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAdminAndLoadTenants();
  }, []);

  const checkAdminAndLoadTenants = async () => {
    try {
      // Check if user is admin
      if (typeof window !== 'undefined') {
        const userStr = localStorage.getItem('user');
        if (userStr) {
          const user = JSON.parse(userStr);
          console.log('[TenantFilter] User object:', user);
          console.log('[TenantFilter] Is admin?', user.is_admin, user.role);
          
          // Check both is_admin and role === 'admin'
          const isUserAdmin = user.is_admin || user.role === 'admin';
          setIsAdmin(isUserAdmin);
          
          if (isUserAdmin) {
            // Load tenant list for admin users
            console.log('[TenantFilter] Loading tenants...');
            const response = await dataAPI.getTenantList();
            console.log('[TenantFilter] Tenants response:', response.data);
            setTenants(response.data.tenants || []);
          }
        }
      }
    } catch (error) {
      console.error('[TenantFilter] Failed to load tenants:', error);
    } finally {
      setLoading(false);
    }
  };

  // Only show for admin users
  if (!isAdmin || loading) {
    return null;
  }

  const handleTenantChange = (tenant: string | null) => {
    console.log('[TenantFilter] Tenant changed to:', tenant);
    setSelectedTenant(tenant);
  };

  console.log('[TenantFilter] Render - isAdmin:', isAdmin, 'loading:', loading, 'tenants:', tenants);

  return (
    <Dropdown className="me-3">
      <Dropdown.Toggle 
        variant="outline-light" 
        size="sm"
        id="tenant-filter-dropdown"
      >
        Tenants: {selectedTenant || 'All'}
      </Dropdown.Toggle>

      <Dropdown.Menu>
        <Dropdown.Item 
          active={!selectedTenant}
          onClick={() => handleTenantChange(null)}
        >
          All Tenants
        </Dropdown.Item>
        
        {tenants.length > 0 && (
          <>
            <Dropdown.Divider />
            {tenants.map((tenant) => (
              <Dropdown.Item
                key={tenant}
                active={selectedTenant === tenant}
                onClick={() => handleTenantChange(tenant)}
              >
                {tenant}
              </Dropdown.Item>
            ))}
          </>
        )}
        
        {tenants.length === 0 && (
          <>
            <Dropdown.Divider />
            <Dropdown.ItemText className="text-muted">
              No tenants available
            </Dropdown.ItemText>
          </>
        )}
      </Dropdown.Menu>
    </Dropdown>
  );
}
