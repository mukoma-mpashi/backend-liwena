<template>
  <div class="map-container">
    <!-- Control Panel -->
    <div class="control-panel">
      <button @click="createTestData" :disabled="loading">
        {{ loading ? 'Creating...' : 'Create Test Data' }}
      </button>
      <button @click="createTestGeofence" :disabled="loading">
        Create Test Geofence
      </button>
      <button @click="refreshData">Refresh Map</button>
      <span v-if="cattleList.length > 0" class="cattle-count">
        🐄 {{ cattleList.length }} cattle tracked
      </span>
    </div>

    <!-- Map -->
    <ol-map
      :load-tiles-while-animating="true"
      :load-tiles-while-interacting="true"
      style="height: 500px; width: 100%;"
      :view.sync="view"
    >
      <ol-view :center="center" :zoom="zoom" />
      <ol-tile-layer>
        <ol-source-osm />
      </ol-tile-layer>

      <!-- Cattle Markers -->
      <ol-vector-layer :style="cattleStyle">
        <ol-source-vector :features="cattleFeatures" />
      </ol-vector-layer>

      <!-- Geofence Display Layer -->
      <ol-vector-layer :style="geofenceStyle">
        <ol-source-vector :features="geofences" />
      </ol-vector-layer>

      <!-- Geofence Drawing Layer -->
      <ol-interaction-draw
        type="Polygon"
        @drawend="onDrawEnd"
      />
    </ol-map>

    <!-- Status Panel -->
    <div class="status-panel">
      <h3>Geofencing Status</h3>
      <div v-if="geofences.length > 0">
        ✅ {{ geofences.length }} geofence(s) active
      </div>
      <div v-else>
        ⚠️ No geofences defined - draw on map or create test geofence
      </div>
      
      <div v-if="lastUpdate" class="last-update">
        Last updated: {{ lastUpdate.toLocaleTimeString() }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { Feature } from 'ol'
import { Point, Polygon } from 'ol/geom'
import { fromLonLat } from 'ol/proj'
import { 
  getGeofences, 
  createGeofence, 
  getCattleLocations,
  createTestGeofence,
  createTestCattleData 
} from '../services/api'
import Style from 'ol/style/Style'
import Icon from 'ol/style/Icon'
import Fill from 'ol/style/Fill'
import Stroke from 'ol/style/Stroke'

// Map center (Nairobi coordinates to match backend test data)
const center = ref(fromLonLat([36.8219, -1.2921])) // [longitude, latitude]
const zoom = ref(15)
const view = ref()
const loading = ref(false)
const lastUpdate = ref<Date | null>(null)

// Cattle data - updated to match backend response format
const cattleList = ref<{ 
  id: string; 
  cattle_id: string; 
  location: [number, number]; // [lat, lng] as returned by backend
  timestamp: string; 
  behavior?: string;
  is_moving?: boolean;
}[]>([])

// Geofences (polygons) as an array of features
const geofences = ref<Feature<Polygon>[]>([])

// Auto-refresh interval
let refreshInterval: NodeJS.Timeout

// Fetch geofences from the server
async function fetchGeofences() {
  try {
    const data = await getGeofences();
    console.log('Fetched geofences:', data);
    
    geofences.value = data.map((fence: any) => {
      const feature = new Feature({
        geometry: new Polygon([fence.coordinates.map((coord: number[]) => fromLonLat(coord))])
      });
      feature.set('name', fence.name);
      return feature;
    });
    
    console.log(`Loaded ${geofences.value.length} geofences`);
  } catch (e) {
    console.error('Failed to fetch geofences:', e);
    // Don't show alert for this, just log
  }
}

// Handle geofence drawing
async function onDrawEnd(event: any) {
  const feature = event.feature;
  let coords = feature.getGeometry().getCoordinates()[0];
  
  // Transform coordinates back from map projection to WGS84
  coords = coords.map((coord: number[]) => {
    const [lng, lat] = fromLonLat(coord, 'EPSG:4326');
    return [lng, lat];
  });
  
  // Prompt for geofence name
  const name = prompt('Enter a name for this geofence:');
  if (!name) {
    alert('Geofence name is required.');
    return;
  }
  
  // Ensure the polygon is closed
  if (
    coords.length < 3 ||
    coords[0][0] !== coords[coords.length - 1][0] ||
    coords[0][1] !== coords[coords.length - 1][1]
  ) {
    coords.push(coords[0]);
  }
  
  try {
    loading.value = true;
    await createGeofence({ name, coordinates: coords });
    await fetchGeofences();
    alert(`Geofence "${name}" saved successfully!`);
  } catch (e) {
    console.error('Failed to save geofence:', e);
    alert('Failed to save geofence. Check console for details.');
  } finally {
    loading.value = false;
  }
}

// Fetch cattle locations
async function fetchCattleLocations() {
  try {
    const data = await getCattleLocations();
    console.log('Fetched cattle locations:', data);
    cattleList.value = data || [];
    lastUpdate.value = new Date();
  } catch (e) {
    console.error('Failed to fetch cattle locations:', e);
    // Don't clear existing data, just log the error
  }
}

// Create test data
async function createTestData() {
  try {
    loading.value = true;
    const result = await createTestCattleData();
    console.log('Test cattle data created:', result);
    await fetchCattleLocations();
    alert(`Test data created for ${result.cattle_created.length} cattle!`);
  } catch (e) {
    console.error('Failed to create test data:', e);
    alert('Failed to create test data. Check console for details.');
  } finally {
    loading.value = false;
  }
}

// Create test geofence
async function createTestGeofence() {
  try {
    loading.value = true;
    const result = await createTestGeofence();
    console.log('Test geofence created:', result);
    await fetchGeofences();
    alert('Test geofence created successfully!');
  } catch (e) {
    console.error('Failed to create test geofence:', e);
    alert('Failed to create test geofence. Check console for details.');
  } finally {
    loading.value = false;
  }
}

// Refresh all data
async function refreshData() {
  await Promise.all([fetchGeofences(), fetchCattleLocations()]);
}

// Computed property for cattle features
const cattleFeatures = computed(() => {
  return cattleList.value.map(cattle => {
    // Backend returns location as [lat, lng]
    const [lat, lng] = cattle.location || [0, 0];
    
    if (lat === 0 && lng === 0) {
      console.warn(`Cattle ${cattle.cattle_id} has invalid coordinates`);
      return null;
    }
    
    const feature = new Feature({
      geometry: new Point(fromLonLat([lng, lat])) // OpenLayers expects [lng, lat]
    });
    
    feature.setId(cattle.cattle_id || cattle.id);
    feature.set('cattle_id', cattle.cattle_id);
    feature.set('behavior', cattle.behavior || 'unknown');
    feature.set('is_moving', cattle.is_moving || false);
    feature.set('timestamp', cattle.timestamp);
    
    return feature;
  }).filter(f => f !== null);
});

// Styles
const cattleStyle = new Style({
  image: new Icon({
    src: 'https://cdn-icons-png.flaticon.com/512/616/616408.png',
    scale: 0.05
  })
});

const geofenceStyle = new Style({
  fill: new Fill({
    color: 'rgba(255, 0, 0, 0.1)'
  }),
  stroke: new Stroke({
    color: 'red',
    width: 2
  })
});

// Lifecycle
onMounted(async () => {
  await refreshData();
  
  // Set up auto-refresh every 30 seconds
  refreshInterval = setInterval(() => {
    fetchCattleLocations();
  }, 30000);
});

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});
</script>

<style scoped>
.map-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.control-panel {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 5px;
}

.control-panel button {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.control-panel button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.control-panel button:hover:not(:disabled) {
  background: #0056b3;
}

.cattle-count {
  margin-left: auto;
  font-weight: bold;
  color: #28a745;
}

.status-panel {
  padding: 10px;
  background: #e9ecef;
  border-radius: 5px;
  font-size: 14px;
}

.status-panel h3 {
  margin: 0 0 10px 0;
  font-size: 16px;
}

.last-update {
  margin-top: 5px;
  font-size: 12px;
  color: #6c757d;
}
</style>
