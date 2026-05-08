import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import GoogleSignIn from './components/GoogleSignIn';
import PreferencesForm from './components/PreferencesForm';
import MapComponent from './components/MapComponent';
import ItineraryTimeline from './components/ItineraryTimeline';

/* Inner component so it can consume AuthContext */
function AppContent() {
  const { user, loading, signOut } = useAuth();
  const [itinerary, setItinerary] = useState(null);
  const [itineraryLoading, setItineraryLoading] = useState(false);

  const handleItineraryCreated = (data) => {
    setItineraryLoading(false);
    setItinerary(data);
  };

  const handleFormSubmitStart = () => {
    setItineraryLoading(true);
    setItinerary(null);
  };

  /* Derive map markers and destination center from itinerary */
  const markers =
    itinerary?.locations?.map((loc) => ({
      lat: loc.lat,
      lng: loc.lng,
      label: loc.name || loc.label || '',
    })) || [];

  const destinationCenter = itinerary?.center || null;

  if (loading) {
    return (
      <div style={fullPageCenterStyle} aria-busy="true" aria-label="Loading application">
        <div style={spinnerStyle} aria-hidden="true" />
        <span className="sr-only">Loading...</span>
      </div>
    );
  }

  if (!user) {
    return <GoogleSignIn />;
  }

  return (
    <div style={appShellStyle}>
      {/* Header */}
      <header style={headerStyle}>
        <div style={headerBrandStyle}>
          <span style={logoStyle} aria-hidden="true">✈️</span>
          <span style={brandNameStyle}>Travel Planner</span>
        </div>
        <div style={headerUserStyle}>
          {user.photoURL && (
            <img
              src={user.photoURL}
              alt={`${user.displayName || 'User'} profile`}
              style={avatarStyle}
              referrerPolicy="no-referrer"
            />
          )}
          <span style={userNameStyle} aria-label={`Signed in as ${user.displayName || user.email}`}>
            {user.displayName || user.email}
          </span>
          <button
            onClick={signOut}
            aria-label="Sign out"
            style={signOutButtonStyle}
          >
            Sign out
          </button>
        </div>
      </header>

      {/* Main layout */}
      <main style={mainStyle}>
        {/* Left panel: preferences form */}
        <aside style={leftPanelStyle} aria-label="Trip preferences">
          <PreferencesForm
            onItineraryCreated={handleItineraryCreated}
            onSubmitStart={handleFormSubmitStart}
          />
        </aside>

        {/* Right panel: map + timeline */}
        <div style={rightPanelStyle}>
          {/* Map */}
          <div style={mapWrapperStyle}>
            <MapComponent
              markers={markers}
              destinationCenter={destinationCenter}
            />
          </div>

          {/* Timeline */}
          <div style={timelineWrapperStyle}>
            <ItineraryTimeline
              itinerary={itinerary}
              loading={itineraryLoading}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

/* ---- Styles ---- */
const fullPageCenterStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  height: '100vh',
  backgroundColor: '#f8f9fa',
};

const spinnerStyle = {
  width: '44px',
  height: '44px',
  border: '4px solid #dadce0',
  borderTopColor: '#1a73e8',
  borderRadius: '50%',
  animation: 'spin 0.8s linear infinite',
};

/* Inject spinner keyframes */
if (typeof document !== 'undefined' && !document.getElementById('app-spinner-style')) {
  const style = document.createElement('style');
  style.id = 'app-spinner-style';
  style.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
  document.head.appendChild(style);
}

const appShellStyle = {
  display: 'flex',
  flexDirection: 'column',
  height: '100vh',
  backgroundColor: '#f8f9fa',
};

const headerStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '0 1.5rem',
  height: '60px',
  backgroundColor: '#ffffff',
  borderBottom: '1px solid #dadce0',
  boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
  flexShrink: 0,
  zIndex: 100,
};

const headerBrandStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.5rem',
};

const logoStyle = {
  fontSize: '1.5rem',
};

const brandNameStyle = {
  fontSize: '1.15rem',
  fontWeight: '700',
  color: '#202124',
};

const headerUserStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.75rem',
};

const avatarStyle = {
  width: '32px',
  height: '32px',
  borderRadius: '50%',
  objectFit: 'cover',
  border: '2px solid #dadce0',
};

const userNameStyle = {
  fontSize: '0.9rem',
  color: '#3c4043',
  fontWeight: '500',
  maxWidth: '180px',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
};

const signOutButtonStyle = {
  backgroundColor: 'transparent',
  border: '1.5px solid #dadce0',
  borderRadius: '6px',
  padding: '0.35rem 0.85rem',
  fontSize: '0.875rem',
  fontWeight: '600',
  color: '#3c4043',
  cursor: 'pointer',
  transition: 'background-color 0.15s ease',
  minHeight: '36px',
};

const mainStyle = {
  display: 'flex',
  flex: 1,
  overflow: 'hidden',
  padding: '1.25rem',
  gap: '1.25rem',
};

const leftPanelStyle = {
  width: '320px',
  flexShrink: 0,
  overflowY: 'auto',
  display: 'flex',
  flexDirection: 'column',
};

const rightPanelStyle = {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  gap: '1.25rem',
  overflow: 'hidden',
};

const mapWrapperStyle = {
  height: '320px',
  flexShrink: 0,
  borderRadius: '12px',
  overflow: 'hidden',
  boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
};

const timelineWrapperStyle = {
  flex: 1,
  overflowY: 'auto',
  display: 'flex',
  flexDirection: 'column',
};
