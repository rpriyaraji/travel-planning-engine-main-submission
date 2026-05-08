import React from 'react';
import { useLoadScript, GoogleMap, Marker } from '@react-google-maps/api';

const DEFAULT_CENTER = { lat: 37.7749, lng: -122.4194 };
const MAP_CONTAINER_STYLE = { width: '100%', height: '100%' };

export default function MapComponent({ markers = [], destinationCenter }) {
  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env.REACT_APP_MAPS_API_KEY || '',
  });

  const center =
    destinationCenter &&
    typeof destinationCenter.lat === 'number' &&
    typeof destinationCenter.lng === 'number'
      ? destinationCenter
      : DEFAULT_CENTER;

  if (loadError) {
    return (
      <div
        role="region"
        aria-label="Travel destination map"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          backgroundColor: '#f1f3f4',
          borderRadius: '8px',
          color: '#c5221f',
          fontSize: '0.95rem',
          padding: '1rem',
          textAlign: 'center',
        }}
      >
        <p>Map failed to load. Please check your API key and network connection.</p>
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div
        role="region"
        aria-label="Travel destination map"
        aria-busy="true"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          backgroundColor: '#f1f3f4',
          borderRadius: '8px',
        }}
      >
        <div aria-hidden="true" style={spinnerStyle} />
        <span className="sr-only">Loading map...</span>
      </div>
    );
  }

  return (
    <div
      role="region"
      aria-label="Travel destination map"
      style={{ width: '100%', height: '100%', borderRadius: '8px', overflow: 'hidden' }}
    >
      <GoogleMap
        mapContainerStyle={MAP_CONTAINER_STYLE}
        center={center}
        zoom={destinationCenter ? 12 : 10}
        options={{
          fullscreenControl: false,
          streetViewControl: false,
          mapTypeControlOptions: { position: 7 },
        }}
      >
        {markers.map((marker, index) => (
          <Marker
            key={`${marker.lat}-${marker.lng}-${index}`}
            position={{ lat: marker.lat, lng: marker.lng }}
            label={
              marker.label
                ? { text: marker.label, color: '#ffffff', fontWeight: 'bold', fontSize: '12px' }
                : undefined
            }
            title={marker.label || `Location ${index + 1}`}
          />
        ))}
      </GoogleMap>
    </div>
  );
}

const spinnerStyle = {
  width: '40px',
  height: '40px',
  border: '4px solid #dadce0',
  borderTopColor: '#1a73e8',
  borderRadius: '50%',
  animation: 'spin 0.8s linear infinite',
};

/* Inject keyframes once */
if (typeof document !== 'undefined' && !document.getElementById('map-spinner-style')) {
  const style = document.createElement('style');
  style.id = 'map-spinner-style';
  style.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
  document.head.appendChild(style);
}
