// src/services/api.ts - Updated version
import axios from 'axios';

const API_BASE_URL = 'http://10.90.9.105:8001'; // Updated to match your backend IP

export async function getCattle() {
  const res = await axios.get(`${API_BASE_URL}/cattle`);
  if (res.data.success) {
    return res.data.data;
  }
  throw new Error(res.data.error || 'Failed to fetch cattle');
}

export async function getStaff() {
  const res = await axios.get(`${API_BASE_URL}/staff`);
  if (res.data.success) {
    return res.data.data;
  }
  throw new Error(res.data.error || 'Failed to fetch staff');
}

export async function getSecurityAlerts() {
  const res = await axios.get(`${API_BASE_URL}/alerts`);
  if (res.data.success) {
    return res.data.data;
  }
  throw new Error(res.data.error || 'Failed to fetch security alerts');
}

export async function updateAlertStatus(alertId: string, action: string) {
  const res = await axios.post(`${API_BASE_URL}/alerts/${alertId}/action`, {
    action: action
  });
  if (res.data.success) {
    return res.data.data;
  }
  throw new Error(res.data.error || 'Failed to update alert status');
}

export async function getGeofences() {
  const res = await axios.get(`${API_BASE_URL}/geofences`);
  if (res.data.success) return res.data.data;
  throw new Error(res.data.error || 'Failed to fetch geofences');
}

export async function createGeofence(geofence: { name: string; coordinates: number[][] }) {
  const res = await axios.post(`${API_BASE_URL}/geofences`, geofence);
  if (res.data.success) return res.data.data;
  throw new Error(res.data.error || 'Failed to create geofence');
}

export async function getAlerts() {
  const res = await axios.get(`${API_BASE_URL}/alerts`);
  if (res.data.success) return res.data.data;
  throw new Error(res.data.error || 'Failed to fetch alerts');
}

// Updated to match the corrected backend endpoint
export async function getCattleLocations() {
  try {
    const res = await axios.get(`${API_BASE_URL}/cattle-locations`);
    if (res.data.success) {
      console.log('Fetched cattle locations:', res.data.data);
      return res.data.data;
    }
    throw new Error(res.data.error || 'Failed to fetch cattle locations');
  } catch (error: any) {
    console.error('Failed to fetch cattle locations:', error);
    // Return empty array if no data instead of throwing error
    if (error.response?.status === 404) {
      return [];
    }
    throw new Error(error.response?.data?.detail || error.message || 'Failed to fetch cattle locations');
  }
}

export async function getCattleDashboardData() {
  const res = await axios.get(`${API_BASE_URL}/cattle-dashboard`);
  if (res.data.success) return res.data.data;
  throw new Error(res.data.error || 'Failed to fetch cattle dashboard data');
}

export async function getCattleLiveData(cattleId: string) {
  try {
    const res = await axios.get(`${API_BASE_URL}/cattle-live-data/${cattleId}`);
    if (res.data.success) {
      return res.data.data;
    }
    throw new Error(res.data.error || 'Failed to fetch cattle live data');
  } catch (error: any) {
    console.error(`Failed to fetch live data for cattle ${cattleId}:`, error);
    throw new Error(error.response?.data?.detail || error.message || `Failed to load live data for cattle ${cattleId}`);
  }
}

export async function getCattle1LiveData() {
  try {
    const res = await axios.get(`${API_BASE_URL}/cattle-live-data/cattle1`);
    if (res.data.success) {
      return res.data.data;
    }
    throw new Error(res.data.error || 'Failed to fetch cattle1 live data');
  } catch (error: any) {
    console.error('Failed to fetch cattle1 live data:', error);
    throw new Error(error.response?.data?.detail || error.message || 'Failed to load cattle1 live data');
  }
}

export async function getDashboardSummary() {
  try {
    const res = await axios.get(`${API_BASE_URL}/dashboard/summary`);
    if (res.data.success) {
      return res.data.data;
    }
    throw new Error(res.data.error || 'Failed to fetch dashboard summary');
  } catch (error: any) {
    console.error('Failed to fetch dashboard summary:', error);
    throw new Error(error.response?.data?.detail || error.message || 'Failed to load dashboard summary');
  }
}

export async function getAllCattleLiveData() {
  try {
    const res = await axios.get(`${API_BASE_URL}/cattle-live-data`);
    if (res.data.success) {
      return res.data.data;
    }
    throw new Error(res.data.error || 'Failed to fetch all cattle live data');
  } catch (error: any) {
    console.error('Failed to fetch all cattle live data:', error);
    throw new Error(error.response?.data?.detail || error.message || 'Failed to load all cattle live data');
  }
}

// New helper functions for testing
export async function createTestGeofence() {
  try {
    const res = await axios.post(`${API_BASE_URL}/geofences/create-test`);
    if (res.data.success) {
      return res.data;
    }
    throw new Error(res.data.error || 'Failed to create test geofence');
  } catch (error: any) {
    console.error('Failed to create test geofence:', error);
    throw new Error(error.response?.data?.detail || error.message || 'Failed to create test geofence');
  }
}

export async function createTestCattleData() {
  try {
    const res = await axios.post(`${API_BASE_URL}/cattle/create-test-data`);
    if (res.data.success) {
      return res.data;
    }
    throw new Error(res.data.error || 'Failed to create test cattle data');
  } catch (error: any) {
    console.error('Failed to create test cattle data:', error);
    throw new Error(error.response?.data?.detail || error.message || 'Failed to create test cattle data');
  }
}
