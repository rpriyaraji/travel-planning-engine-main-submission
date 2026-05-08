import React from 'react';

const TIME_SLOTS = ['morning', 'afternoon', 'evening'];

const TIME_SLOT_LABELS = {
  morning: 'Morning',
  afternoon: 'Afternoon',
  evening: 'Evening',
};

const TIME_SLOT_ICONS = {
  morning: '☀️',
  afternoon: '🌤️',
  evening: '🌙',
};

/* ---- Skeleton placeholder ---- */
function SkeletonCard() {
  return (
    <div style={skeletonCardStyle} aria-hidden="true">
      <div style={{ ...skeletonBlock, width: '40%', height: '1.1rem', marginBottom: '1rem' }} />
      {TIME_SLOTS.map((slot) => (
        <div key={slot} style={{ marginBottom: '0.75rem' }}>
          <div style={{ ...skeletonBlock, width: '25%', height: '0.85rem', marginBottom: '0.4rem' }} />
          <div style={{ ...skeletonBlock, width: '90%', height: '0.75rem', marginBottom: '0.25rem' }} />
          <div style={{ ...skeletonBlock, width: '75%', height: '0.75rem' }} />
        </div>
      ))}
    </div>
  );
}

/* ---- A single time-slot section ---- */
function TimeSlotSection({ slot, activities }) {
  const items = Array.isArray(activities) ? activities : activities ? [activities] : [];

  return (
    <div style={timeSlotStyle}>
      <h4 style={timeSlotHeadingStyle}>
        <span aria-hidden="true">{TIME_SLOT_ICONS[slot]} </span>
        {TIME_SLOT_LABELS[slot]}
      </h4>
      {items.length === 0 ? (
        <p style={noActivityStyle}>No activities planned</p>
      ) : (
        <ul style={activityListStyle}>
          {items.map((activity, i) => (
            <li key={i} style={activityItemStyle}>
              {typeof activity === 'string' ? activity : activity.description || activity.name || JSON.stringify(activity)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* ---- A single day card ---- */
function DayCard({ day, dayNumber }) {
  return (
    <article
      role="article"
      aria-label={`Day ${dayNumber} itinerary`}
      style={dayCardStyle}
    >
      {/* Timeline dot */}
      <div style={timelineDotStyle} aria-hidden="true" />

      <div style={dayCardContentStyle}>
        <h3 style={dayHeadingStyle}>
          Day {dayNumber}
          {day.date && (
            <span style={dayDateStyle}> — {day.date}</span>
          )}
          {day.title && (
            <span style={dayTitleStyle}> · {day.title}</span>
          )}
        </h3>

        <div style={timeSlotsContainerStyle}>
          {TIME_SLOTS.map((slot) => (
            <TimeSlotSection
              key={slot}
              slot={slot}
              activities={day[slot] || day[`${slot}_activities`] || []}
            />
          ))}
        </div>

        {day.notes && (
          <p style={notesStyle}>
            <strong>Notes:</strong> {day.notes}
          </p>
        )}
      </div>
    </article>
  );
}

/* ---- Main component ---- */
export default function ItineraryTimeline({ itinerary, loading }) {
  if (loading) {
    return (
      <section aria-label="Itinerary timeline loading" style={containerStyle}>
        <h2 style={sectionHeadingStyle}>Your Itinerary</h2>
        <div aria-busy="true" aria-label="Loading itinerary">
          {[1, 2, 3].map((n) => (
            <SkeletonCard key={n} />
          ))}
        </div>
      </section>
    );
  }

  const days = itinerary?.days;

  if (!days || days.length === 0) {
    return (
      <section aria-label="Itinerary timeline" style={containerStyle}>
        <h2 style={sectionHeadingStyle}>Your Itinerary</h2>
        <div style={emptyStateStyle}>
          <p style={emptyStateIconStyle} aria-hidden="true">🗺️</p>
          <p style={emptyStatePrimaryStyle}>No itinerary yet</p>
          <p style={emptyStateSecondaryStyle}>
            Fill in your preferences and click <strong>Create Itinerary</strong> to get started.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section aria-label="Itinerary timeline" style={containerStyle}>
      <h2 style={sectionHeadingStyle}>Your Itinerary</h2>
      {itinerary.destination && (
        <p style={destinationTagStyle}>{itinerary.destination}</p>
      )}
      <div style={timelineStyle}>
        {days.map((day, index) => (
          <DayCard key={index} day={day} dayNumber={index + 1} />
        ))}
      </div>
    </section>
  );
}

/* ---- Styles ---- */
const containerStyle = {
  background: '#ffffff',
  borderRadius: '12px',
  padding: '1.5rem',
  boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
  overflowY: 'auto',
  flex: 1,
};

const sectionHeadingStyle = {
  fontSize: '1.25rem',
  fontWeight: '700',
  color: '#202124',
  marginTop: 0,
  marginBottom: '1.25rem',
};

const destinationTagStyle = {
  display: 'inline-block',
  backgroundColor: '#e8f0fe',
  color: '#1a73e8',
  borderRadius: '20px',
  padding: '0.25rem 0.85rem',
  fontSize: '0.875rem',
  fontWeight: '600',
  marginBottom: '1.25rem',
  marginTop: '-0.5rem',
};

const timelineStyle = {
  position: 'relative',
  paddingLeft: '1.5rem',
  borderLeft: '2px solid #dadce0',
};

const dayCardStyle = {
  position: 'relative',
  marginBottom: '1.5rem',
};

const timelineDotStyle = {
  position: 'absolute',
  left: '-2rem',
  top: '0.85rem',
  width: '14px',
  height: '14px',
  borderRadius: '50%',
  backgroundColor: '#1a73e8',
  border: '3px solid #ffffff',
  boxShadow: '0 0 0 2px #1a73e8',
};

const dayCardContentStyle = {
  background: '#f8f9fa',
  border: '1px solid #e8eaed',
  borderRadius: '10px',
  padding: '1rem 1.15rem',
};

const dayHeadingStyle = {
  fontSize: '1rem',
  fontWeight: '700',
  color: '#202124',
  margin: '0 0 0.75rem 0',
};

const dayDateStyle = {
  fontWeight: '400',
  color: '#5f6368',
  fontSize: '0.9rem',
};

const dayTitleStyle = {
  fontWeight: '600',
  color: '#1a73e8',
  fontSize: '0.9rem',
};

const timeSlotsContainerStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
  gap: '0.75rem',
};

const timeSlotStyle = {
  background: '#ffffff',
  borderRadius: '8px',
  padding: '0.65rem 0.85rem',
  border: '1px solid #e8eaed',
};

const timeSlotHeadingStyle = {
  fontSize: '0.825rem',
  fontWeight: '700',
  color: '#3c4043',
  margin: '0 0 0.4rem 0',
  textTransform: 'uppercase',
  letterSpacing: '0.03em',
};

const noActivityStyle = {
  fontSize: '0.8rem',
  color: '#9aa0a6',
  margin: 0,
  fontStyle: 'italic',
};

const activityListStyle = {
  margin: 0,
  paddingLeft: '1.1rem',
  listStyleType: 'disc',
};

const activityItemStyle = {
  fontSize: '0.85rem',
  color: '#3c4043',
  marginBottom: '0.2rem',
  lineHeight: '1.4',
};

const notesStyle = {
  fontSize: '0.85rem',
  color: '#5f6368',
  marginTop: '0.75rem',
  marginBottom: 0,
  borderTop: '1px solid #e8eaed',
  paddingTop: '0.6rem',
};

/* Skeleton styles */
const skeletonCardStyle = {
  background: '#f8f9fa',
  border: '1px solid #e8eaed',
  borderRadius: '10px',
  padding: '1rem 1.15rem',
  marginBottom: '1.25rem',
};

const skeletonBlock = {
  backgroundColor: '#e8eaed',
  borderRadius: '4px',
  animation: 'pulse 1.4s ease-in-out infinite',
};

/* Inject skeleton pulse keyframes once */
if (typeof document !== 'undefined' && !document.getElementById('skeleton-pulse-style')) {
  const style = document.createElement('style');
  style.id = 'skeleton-pulse-style';
  style.textContent = `
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }
  `;
  document.head.appendChild(style);
}

/* Empty state styles */
const emptyStateStyle = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '3rem 1rem',
  textAlign: 'center',
  color: '#5f6368',
};

const emptyStateIconStyle = {
  fontSize: '3rem',
  marginBottom: '0.75rem',
};

const emptyStatePrimaryStyle = {
  fontSize: '1.1rem',
  fontWeight: '600',
  color: '#3c4043',
  margin: '0 0 0.5rem 0',
};

const emptyStateSecondaryStyle = {
  fontSize: '0.9rem',
  color: '#5f6368',
  maxWidth: '280px',
  margin: 0,
};
