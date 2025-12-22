'use client';

import React, { createContext, useContext, useState } from 'react';

interface TenantContextType {
  selectedTenant: string | null;
  setSelectedTenant: (tenant: string | null) => void;
  availableTenants: string[];
  setAvailableTenants: (tenants: string[]) => void;
  isLoading: boolean;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export function TenantProvider({ children }: { children: React.ReactNode }) {
  const [selectedTenant, setSelectedTenant] = useState<string | null>(null);
  const [availableTenants, setAvailableTenants] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  return (
    <TenantContext.Provider
      value={{
        selectedTenant,
        setSelectedTenant,
        availableTenants,
        setAvailableTenants,
        isLoading
      }}
    >
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  const context = useContext(TenantContext);
  if (context === undefined) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
}
