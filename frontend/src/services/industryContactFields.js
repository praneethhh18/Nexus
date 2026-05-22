/**
 * Industry-specific extra fields on the contact form.
 *
 * Phase F.5: a Healthcare workspace asks for DOB + blood group on a new
 * patient; a Real-estate workspace asks for budget + BHK + looking-for.
 * These are stored in contacts.custom_fields as JSON so we don't add a
 * column per industry per field.
 *
 * The base contact form (first/last/email/phone/title) is unchanged. This
 * module returns ONLY the extras. The form renders them after the base
 * fields when the workspace's industry has a schema below.
 *
 * Industries without an entry get an empty schema → no extras rendered →
 * identical to today's contact form.
 *
 * Adding a new industry:
 *   1. Add a key to SCHEMAS keyed by the exact industry name
 *      (must match api/industry_setup.PRESETS)
 *   2. Provide an array of FieldSpec objects
 *
 * FieldSpec shape:
 *   { key:  'snake_case_key',           // stored in custom_fields[key]
 *     label: 'Field label',              // shown above the input
 *     type:  'text' | 'date' | 'select' | 'tel' | 'number',
 *     placeholder?: 'Helper text',       // for text/tel/number/date
 *     options?: ['A', 'B', 'C'],         // for type=select
 *     hint?:   'Why we ask',             // muted text below the input
 *   }
 */

const SCHEMAS = {
  Healthcare: [
    { key: 'date_of_birth', label: 'Date of birth',     type: 'date',
      hint: 'Drives age-banded reminders + risk flags.' },
    { key: 'blood_group',   label: 'Blood group',       type: 'select',
      options: ['', 'A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-', 'Unknown'],
      hint: 'Surfaced to staff during appointments.' },
    { key: 'allergies',     label: 'Known allergies',   type: 'text',
      placeholder: 'e.g. Penicillin, peanuts',
      hint: 'Flagged before prescribing.' },
    { key: 'emergency_contact_name',  label: 'Emergency contact (name)',  type: 'text',
      placeholder: 'Relative or spouse' },
    { key: 'emergency_contact_phone', label: 'Emergency contact (phone)', type: 'tel',
      placeholder: '+91 9XXXXXXXXX' },
  ],

  Education: [
    { key: 'student_grade', label: 'Current grade / class', type: 'text',
      placeholder: 'e.g. Grade 10, IX, Junior KG' },
    { key: 'board',         label: 'Board',                  type: 'select',
      options: ['', 'CBSE', 'ICSE', 'IB', 'IGCSE', 'State', 'Other'] },
    { key: 'school_name',   label: 'Current school',         type: 'text',
      placeholder: 'For new admissions, the previous school' },
    { key: 'parent_name',   label: 'Parent / guardian name', type: 'text',
      hint: 'Primary contact for fee + result communication.' },
    { key: 'parent_phone',  label: 'Parent / guardian phone', type: 'tel',
      placeholder: '+91 9XXXXXXXXX' },
  ],

  'Tutoring / coaching': [
    { key: 'student_grade',    label: 'Current grade / class', type: 'text',
      placeholder: 'e.g. 12th JEE, NEET batch' },
    { key: 'subjects',         label: 'Subjects',              type: 'text',
      placeholder: 'PCM, PCB, English, etc.' },
    { key: 'target_exam',      label: 'Target exam',           type: 'text',
      placeholder: 'e.g. JEE Main 2025, NEET, IELTS Band 8' },
    { key: 'parent_name',      label: 'Parent name',           type: 'text' },
    { key: 'parent_phone',     label: 'Parent WhatsApp',       type: 'tel',
      hint: 'Where fee + test-result messages will go.' },
  ],

  'Real estate broker': [
    { key: 'looking_for',  label: 'Looking for',        type: 'select',
      options: ['', 'Rental', 'Resale purchase', 'New purchase', 'Investment', 'Sale (owner)'] },
    { key: 'bhk',          label: 'Preferred BHK',      type: 'select',
      options: ['', '1BHK', '2BHK', '3BHK', '4BHK+', 'Plot', 'Commercial'] },
    { key: 'budget_range', label: 'Budget range',       type: 'text',
      placeholder: 'e.g. ₹40-60L, ₹1.5Cr-2Cr, ₹30k/month' },
    { key: 'preferred_areas', label: 'Preferred locality / areas', type: 'text',
      placeholder: 'Whitefield, Indiranagar...' },
    { key: 'urgency',      label: 'Decision timeline',  type: 'select',
      options: ['', 'Within 30 days', '1-3 months', '3-6 months', 'Just exploring'] },
  ],

  'Real estate': [
    { key: 'looking_for',  label: 'Looking for',     type: 'select',
      options: ['', 'Buy', 'Invest', 'Rent', 'Sell'] },
    { key: 'bhk',          label: 'Preferred BHK',   type: 'select',
      options: ['', '1BHK', '2BHK', '3BHK', '4BHK+', 'Plot', 'Commercial'] },
    { key: 'budget_range', label: 'Budget range',    type: 'text',
      placeholder: 'e.g. ₹80L-1Cr' },
    { key: 'preferred_areas', label: 'Preferred areas', type: 'text',
      placeholder: 'Specific localities or zones' },
  ],

  'Auto repair / garage': [
    { key: 'vehicle_make',   label: 'Vehicle make',   type: 'text',
      placeholder: 'Honda, Maruti, Hyundai...' },
    { key: 'vehicle_model',  label: 'Vehicle model',  type: 'text',
      placeholder: 'City, Swift, i20...' },
    { key: 'registration',   label: 'Registration no', type: 'text',
      placeholder: 'KA-01-MZ-1234' },
    { key: 'last_service_km',label: 'Last service (km)', type: 'number',
      placeholder: 'Odometer reading at last visit' },
    { key: 'fuel_type',      label: 'Fuel type',      type: 'select',
      options: ['', 'Petrol', 'Diesel', 'CNG', 'Electric', 'Hybrid'] },
  ],

  'Photography / event services': [
    { key: 'event_type',  label: 'Event type', type: 'select',
      options: ['', 'Wedding', 'Pre-wedding', 'Birthday', 'Corporate', 'Maternity', 'Engagement', 'Other'] },
    { key: 'event_date',  label: 'Event date', type: 'date' },
    { key: 'event_city',  label: 'Event city / venue', type: 'text',
      placeholder: 'Where the shoot/event will take place' },
    { key: 'pax_count',   label: 'Approx guests', type: 'number',
      placeholder: 'Helps us scale crew + equipment' },
  ],

  'Travel / tour operator': [
    { key: 'destination', label: 'Preferred destination', type: 'text',
      placeholder: 'Bali, Maldives, Rajasthan, etc.' },
    { key: 'travel_dates', label: 'Travel dates',         type: 'text',
      placeholder: 'e.g. Dec 15-22 or "flexible"' },
    { key: 'traveller_count', label: 'No. of travellers',  type: 'number' },
    { key: 'passport_status', label: 'Passport status',    type: 'select',
      options: ['', 'Valid 6+ months', 'Expiring soon', 'No passport', 'Children only'] },
    { key: 'budget_per_person', label: 'Budget per person', type: 'text',
      placeholder: 'e.g. ₹50k, ₹2L' },
  ],

  'Construction / contracting': [
    { key: 'project_type',   label: 'Project type',   type: 'select',
      options: ['', 'New build', 'Renovation', 'Interiors', 'Commercial fit-out', 'Repair'] },
    { key: 'site_address',   label: 'Site address',   type: 'text',
      placeholder: 'For site visit scheduling' },
    { key: 'area_sqft',      label: 'Approx area (sq ft)', type: 'number' },
    { key: 'target_start',   label: 'Target start date',   type: 'date' },
  ],

  Hospitality: [
    { key: 'preferred_dates', label: 'Preferred dates', type: 'text',
      placeholder: 'e.g. Dec 22-25' },
    { key: 'guest_count',     label: 'Guest count',    type: 'number' },
    { key: 'dietary_prefs',   label: 'Dietary preferences', type: 'text',
      placeholder: 'Veg, jain, vegan, nut allergy, etc.' },
    { key: 'occasion',        label: 'Occasion (if any)',   type: 'text',
      placeholder: 'Anniversary, birthday, business...' },
  ],

  'Beauty / salon / wellness': [
    { key: 'preferred_stylist', label: 'Preferred stylist', type: 'text',
      placeholder: 'For continuity on repeat visits' },
    { key: 'hair_type', label: 'Hair type', type: 'select',
      options: ['', 'Straight', 'Wavy', 'Curly', 'Coily'] },
    { key: 'allergies', label: 'Skin / product allergies', type: 'text',
      placeholder: 'For colour/skincare safety' },
    { key: 'last_service', label: 'Last service done',  type: 'text',
      placeholder: 'For rebook timing' },
  ],

  'Logistics / transport': [
    { key: 'consignment_type', label: 'Typical consignment', type: 'text',
      placeholder: 'Cotton bales, auto parts, etc.' },
    { key: 'gstin', label: 'GSTIN', type: 'text',
      placeholder: 'For e-way bill generation' },
    { key: 'preferred_routes', label: 'Frequent routes', type: 'text',
      placeholder: 'e.g. Hosur-Pune, Mumbai-Delhi' },
    { key: 'volume_per_month', label: 'Approx volume/month', type: 'text',
      placeholder: 'e.g. 30 trips, 200 tonnes' },
  ],
};

// Case-insensitive index built once at module load. Mirrors the backend
// normalize_industry() behaviour so 'healthcare' / 'HEALTHCARE' /
// 'Healthcare ' all resolve to the same canonical schema. Without this,
// a workspace whose industry got stored with non-canonical casing would
// silently get no extra fields, invisible regression.
const _SCHEMAS_CI = {};
for (const k of Object.keys(SCHEMAS)) {
  _SCHEMAS_CI[k.toLowerCase()] = SCHEMAS[k];
}

export function getContactFieldsForIndustry(industry) {
  if (!industry) return [];
  return _SCHEMAS_CI[industry.trim().toLowerCase()] || [];
}

export const SUPPORTED_INDUSTRIES = Object.keys(SCHEMAS);
