import React, { useState } from 'react';
import axios from 'axios';

// Empty string = same origin (works on Cloud Run where frontend+backend are co-located)
const API_BASE = process.env.REACT_APP_API_BASE_URL || '';

const INTERESTS_OPTIONS = [
  { value: 'culture', label: 'Culture' },
  { value: 'food', label: 'Food' },
  { value: 'nature', label: 'Nature' },
  { value: 'adventure', label: 'Adventure' },
  { value: 'shopping', label: 'Shopping' },
];

const BUDGET_OPTIONS = [
  { value: 'budget', label: 'Budget' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'luxury', label: 'Luxury' },
];

const initialFormState = {
  destination: '',
  origin: '',
  duration_days: 3,
  budget: 'moderate',
  interests: [],
};

export default function PreferencesForm({ onItineraryCreated }) {
  const [form, setForm] = useState(initialFormState);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null); // { type: 'error'|'success', text }
  const [itineraryId, setItineraryId] = useState(null);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    if (type === 'checkbox') {
      const checked = e.target.checked;
      setForm((prev) => ({
        ...prev,
        interests: checked
          ? [...prev.interests, value]
          : prev.interests.filter((i) => i !== value),
      }));
    } else {
      setForm((prev) => ({ ...prev, [name]: type === 'number' ? Number(value) : value }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatusMessage(null);
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/plan`, {
        preferences: form,
        user_id: 'demo-user',
      });
      const data = response.data;
      const newId = data.itinerary_id || data.id;
      setItineraryId(newId);
      setStatusMessage({ type: 'success', text: 'Itinerary created successfully!' });

      // Fetch full itinerary data (with days) to render the timeline
      if (typeof onItineraryCreated === 'function') {
        try {
          const itineraryRes = await axios.get(`${API_BASE}/itineraries/demo-user`);
          const all = itineraryRes.data;
          const full = all.find((i) => i.id === newId) || all[all.length - 1];
          onItineraryCreated(full || data);
        } catch {
          onItineraryCreated(data);
        }
      }
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Failed to create itinerary. Please try again.';
      setStatusMessage({ type: 'error', text: message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <section aria-labelledby="preferences-heading" style={sectionStyle}>
      <h2 id="preferences-heading" style={headingStyle}>
        Plan Your Trip
      </h2>

      {/* Live region for status messages */}
      <div aria-live="polite" aria-atomic="true">
        {statusMessage && (
          <p
            style={{
              ...statusMessageBase,
              ...(statusMessage.type === 'error' ? errorStyle : successStyle),
            }}
            role={statusMessage.type === 'error' ? 'alert' : undefined}
          >
            {statusMessage.text}
            {statusMessage.type === 'success' && itineraryId && (
              <span style={{ display: 'block', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                Itinerary ID: {itineraryId}
              </span>
            )}
          </p>
        )}
      </div>

      <form onSubmit={handleSubmit} noValidate>
        {/* Destination */}
        <div style={fieldGroupStyle}>
          <label htmlFor="destination" style={labelStyle}>
            Destination <span aria-hidden="true" style={requiredStar}>*</span>
          </label>
          <input
            id="destination"
            name="destination"
            type="text"
            value={form.destination}
            onChange={handleChange}
            required
            aria-required="true"
            placeholder="e.g. Paris, France"
            style={inputStyle}
          />
        </div>

        {/* Origin */}
        <div style={fieldGroupStyle}>
          <label htmlFor="origin" style={labelStyle}>
            Origin <span aria-hidden="true" style={requiredStar}>*</span>
          </label>
          <input
            id="origin"
            name="origin"
            type="text"
            value={form.origin}
            onChange={handleChange}
            required
            aria-required="true"
            placeholder="e.g. New York, USA"
            style={inputStyle}
          />
        </div>

        {/* Duration */}
        <div style={fieldGroupStyle}>
          <label htmlFor="duration_days" style={labelStyle}>
            Duration (days) <span aria-hidden="true" style={requiredStar}>*</span>
          </label>
          <input
            id="duration_days"
            name="duration_days"
            type="number"
            value={form.duration_days}
            onChange={handleChange}
            required
            aria-required="true"
            min={1}
            max={30}
            style={inputStyle}
          />
        </div>

        {/* Budget */}
        <div style={fieldGroupStyle}>
          <label htmlFor="budget" style={labelStyle}>
            Budget
          </label>
          <select
            id="budget"
            name="budget"
            value={form.budget}
            onChange={handleChange}
            style={inputStyle}
          >
            {BUDGET_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Interests */}
        <fieldset style={fieldsetStyle}>
          <legend style={legendStyle}>Interests</legend>
          <div style={checkboxGridStyle}>
            {INTERESTS_OPTIONS.map((opt) => (
              <label key={opt.value} style={checkboxLabelStyle}>
                <input
                  type="checkbox"
                  name="interests"
                  value={opt.value}
                  checked={form.interests.includes(opt.value)}
                  onChange={handleChange}
                  style={{ marginRight: '0.4rem', accentColor: '#1a73e8' }}
                />
                {opt.label}
              </label>
            ))}
          </div>
        </fieldset>

        <button
          type="submit"
          disabled={loading}
          aria-busy={loading}
          style={{
            ...submitButtonStyle,
            opacity: loading ? 0.7 : 1,
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Planning...' : 'Create Itinerary'}
        </button>
      </form>
    </section>
  );
}

/* --- Styles --- */
const sectionStyle = {
  background: '#ffffff',
  borderRadius: '12px',
  padding: '1.5rem',
  boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
  overflowY: 'auto',
};

const headingStyle = {
  fontSize: '1.25rem',
  fontWeight: '700',
  color: '#202124',
  marginTop: 0,
  marginBottom: '1.25rem',
};

const fieldGroupStyle = {
  marginBottom: '1rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.3rem',
};

const labelStyle = {
  fontWeight: '600',
  fontSize: '0.9rem',
  color: '#3c4043',
};

const requiredStar = {
  color: '#c5221f',
};

const inputStyle = {
  padding: '0.55rem 0.75rem',
  border: '1.5px solid #dadce0',
  borderRadius: '6px',
  fontSize: '0.95rem',
  color: '#202124',
  background: '#fff',
  width: '100%',
};

const fieldsetStyle = {
  border: '1.5px solid #dadce0',
  borderRadius: '6px',
  padding: '0.75rem 1rem',
  marginBottom: '1.25rem',
};

const legendStyle = {
  fontWeight: '600',
  fontSize: '0.9rem',
  color: '#3c4043',
  padding: '0 0.25rem',
};

const checkboxGridStyle = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr',
  gap: '0.5rem',
};

const checkboxLabelStyle = {
  display: 'flex',
  alignItems: 'center',
  fontSize: '0.9rem',
  color: '#202124',
  cursor: 'pointer',
};

const submitButtonStyle = {
  display: 'block',
  width: '100%',
  padding: '0.75rem 1rem',
  backgroundColor: '#1a73e8',
  color: '#ffffff',
  border: 'none',
  borderRadius: '6px',
  fontSize: '1rem',
  fontWeight: '600',
  minHeight: '48px',
  transition: 'background-color 0.2s ease',
};

const statusMessageBase = {
  borderRadius: '6px',
  padding: '0.65rem 0.9rem',
  fontSize: '0.9rem',
  marginBottom: '1rem',
};

const errorStyle = {
  backgroundColor: '#fce8e6',
  color: '#c5221f',
  border: '1px solid #f5c6c3',
};

const successStyle = {
  backgroundColor: '#e6f4ea',
  color: '#137333',
  border: '1px solid #ceead6',
};
