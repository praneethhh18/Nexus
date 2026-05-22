/**
 * Industry-aware terminology layer.
 *
 * Same product, different vocabulary per industry. A real-estate broker
 * doesn't say "Deal", they say "Listing." A doctor doesn't say "Contact"
 *, they say "Patient." Wrapping every label with `t('deal')` instead of
 * hardcoding "Deal" lets the workspace speak the user's language without
 * forking the product into 11 separate apps.
 *
 * How callers use it:
 *   import { useTerm } from '../services/industryTerms';
 *   const t = useTerm();
 *   <h2>{t('deals')}</h2>          // "Listings" for real estate, "Appointments" for healthcare
 *
 * If a key is missing for a given industry, falls back to the generic
 * default, so adding a new industry never breaks any page.
 *
 * Resolution order on lookup:
 *   1. industry-specific map for the active business
 *   2. DEFAULT_TERMS
 *   3. the key itself as a last resort
 */
import { getCurrentBusiness } from './auth';

// ── Defaults, the generic CRM vocabulary ────────────────────────────────
// Singular + plural for every noun. Verb forms only when they differ
// meaningfully ("call lead" vs "call patient").
const DEFAULT_TERMS = {
  contact:        'Contact',
  contacts:       'Contacts',
  contact_new:    'New contact',
  contact_add:    'Add contact',

  company:        'Company',
  companies:      'Companies',
  company_new:    'New company',

  deal:           'Deal',
  deals:          'Deals',
  deal_new:       'New deal',
  deal_pipeline:  'Deal pipeline',

  lead:           'Lead',
  leads:          'Leads',

  invoice:        'Invoice',
  invoices:       'Invoices',
  invoice_new:    'New invoice',

  task:           'Task',
  tasks:          'Tasks',

  // The "primary action" CTAs on empty states / dashboards
  primary_record: 'lead',          // used in CTAs like "Add your first {primary_record}"
  primary_action: 'Add lead',

  // Dashboard KPI labels
  kpi_pipeline:   'Open pipeline',
  kpi_won:        'Won this month',
  kpi_invoices:   'Outstanding invoices',
  kpi_overdue:    'Overdue',
};

// ── Per-industry overrides ───────────────────────────────────────────────
// Only override what genuinely changes meaning. Keep everything else on
// DEFAULT_TERMS so we stay consistent across the app.
//
// Keys must match the `industry` field stored on the business (already
// normalised by api/industry_setup.normalize_industry).
const INDUSTRY_TERMS = {
  Healthcare: {
    contact:        'Patient',
    contacts:       'Patients',
    contact_new:    'New patient',
    contact_add:    'Add patient',
    deal:           'Appointment',
    deals:          'Appointments',
    deal_new:       'New appointment',
    deal_pipeline:  'Appointments pipeline',
    lead:           'Inquiry',
    leads:          'Inquiries',
    invoice:        'Bill',
    invoices:       'Bills',
    invoice_new:    'New bill',
    primary_record: 'patient',
    primary_action: 'Add patient',
    kpi_pipeline:   'Upcoming appointments',
    kpi_won:        'Treatments this month',
    kpi_invoices:   'Pending bills',
    kpi_overdue:    'Overdue follow-ups',
  },

  'Real estate': {
    contact:        'Lead',
    contacts:       'Leads',
    contact_new:    'New lead',
    contact_add:    'Add lead',
    company:        'Property',
    companies:      'Properties',
    company_new:    'New property',
    deal:           'Listing',
    deals:          'Listings',
    deal_new:       'New listing',
    deal_pipeline:  'Listing pipeline',
    primary_record: 'lead',
    primary_action: 'Add lead',
    kpi_pipeline:   'Active listings',
    kpi_won:        'Closed this month',
    kpi_invoices:   'Pending brokerage',
    kpi_overdue:    'Stalled deals',
  },

  Education: {
    contact:        'Student',
    contacts:       'Students',
    contact_new:    'New student',
    contact_add:    'Add student',
    deal:           'Application',
    deals:          'Applications',
    deal_new:       'New application',
    deal_pipeline:  'Admissions pipeline',
    lead:           'Inquiry',
    leads:          'Inquiries',
    invoice:        'Fee invoice',
    invoices:       'Fee invoices',
    primary_record: 'student',
    primary_action: 'Add student',
    kpi_pipeline:   'Open applications',
    kpi_won:        'Admissions this month',
    kpi_invoices:   'Fees pending',
    kpi_overdue:    'Overdue fees',
  },

  Legal: {
    contact:        'Client',
    contacts:       'Clients',
    contact_new:    'New client',
    contact_add:    'Add client',
    deal:           'Matter',
    deals:          'Matters',
    deal_new:       'New matter',
    deal_pipeline:  'Active matters',
    lead:           'Consultation request',
    leads:          'Consultation requests',
    invoice:        'Fee invoice',
    invoices:       'Fee invoices',
    primary_record: 'client',
    primary_action: 'Add client',
    kpi_pipeline:   'Active matters',
    kpi_won:        'Closed this month',
    kpi_invoices:   'Fees pending',
    kpi_overdue:    'Overdue tasks',
  },

  Ecommerce: {
    contact:        'Customer',
    contacts:       'Customers',
    contact_new:    'New customer',
    contact_add:    'Add customer',
    deal:           'Order',
    deals:          'Orders',
    deal_new:       'New order',
    deal_pipeline:  'Order pipeline',
    primary_record: 'customer',
    primary_action: 'Add customer',
    kpi_pipeline:   'Open orders',
    kpi_won:        'Orders shipped',
    kpi_invoices:   'Invoices pending',
    kpi_overdue:    'Returns + complaints',
  },

  Finance: {
    contact:        'Client',
    contacts:       'Clients',
    contact_new:    'New client',
    contact_add:    'Add client',
    deal:           'Engagement',
    deals:          'Engagements',
    deal_new:       'New engagement',
    deal_pipeline:  'Engagement pipeline',
    invoice:        'Fee invoice',
    invoices:       'Fee invoices',
    primary_record: 'client',
    primary_action: 'Add client',
    kpi_pipeline:   'Active engagements',
    kpi_won:        'Closed this month',
    kpi_invoices:   'Fees pending',
    kpi_overdue:    'Compliance due',
  },

  SaaS: {
    deal:           'Account',
    deals:          'Accounts',
    deal_new:       'New account',
    deal_pipeline:  'Sales pipeline',
    lead:           'Inbound lead',
    leads:          'Inbound',
    primary_record: 'lead',
    primary_action: 'Add account',
    kpi_pipeline:   'Pipeline (ARR)',
    kpi_won:        'Closed this month',
    kpi_invoices:   'Subscriptions pending',
    kpi_overdue:    'At-risk renewals',
  },

  Manufacturing: {
    contact:        'Buyer',
    contacts:       'Buyers',
    contact_new:    'New buyer',
    contact_add:    'Add buyer',
    deal:           'Order',
    deals:          'Orders',
    deal_new:       'New order',
    deal_pipeline:  'Order pipeline',
    primary_record: 'buyer',
    primary_action: 'Add buyer',
    kpi_pipeline:   'Open POs',
    kpi_won:        'Delivered this month',
    kpi_invoices:   'Invoices pending',
    kpi_overdue:    'Overdue dispatches',
  },

  Hospitality: {
    contact:        'Guest',
    contacts:       'Guests',
    contact_new:    'New guest',
    contact_add:    'Add guest',
    deal:           'Booking',
    deals:          'Bookings',
    deal_new:       'New booking',
    deal_pipeline:  'Bookings pipeline',
    lead:           'Inquiry',
    leads:          'Inquiries',
    primary_record: 'booking',
    primary_action: 'Add booking',
    kpi_pipeline:   'Upcoming bookings',
    kpi_won:        'Checked in this month',
    kpi_invoices:   'Pending payments',
    kpi_overdue:    'Unconfirmed bookings',
  },

  'Local services': {
    contact:        'Customer',
    contacts:       'Customers',
    contact_new:    'New customer',
    contact_add:    'Add customer',
    deal:           'Job',
    deals:          'Jobs',
    deal_new:       'New job',
    deal_pipeline:  'Job pipeline',
    primary_record: 'customer',
    primary_action: 'Add customer',
    kpi_pipeline:   'Scheduled jobs',
    kpi_won:        'Jobs completed',
    kpi_invoices:   'Pending payments',
    kpi_overdue:    'Overdue follow-ups',
  },

  Consulting: {
    contact:        'Client',
    contacts:       'Clients',
    contact_new:    'New client',
    contact_add:    'Add client',
    deal:           'Engagement',
    deals:          'Engagements',
    deal_new:       'New engagement',
    deal_pipeline:  'Engagement pipeline',
    primary_record: 'client',
    primary_action: 'Add client',
    kpi_pipeline:   'Active engagements',
    kpi_won:        'Closed this month',
    kpi_invoices:   'Invoices pending',
    kpi_overdue:    'Project blockers',
  },

  // ── Indian SMB additions ─────────────────────────────────────────────
  'Tutoring / coaching': {
    contact:        'Student',
    contacts:       'Students',
    contact_new:    'New student',
    contact_add:    'Add student',
    deal:           'Enrolment',
    deals:          'Enrolments',
    deal_new:       'New enrolment',
    deal_pipeline:  'Enrolment pipeline',
    lead:           'Inquiry',
    leads:          'Inquiries',
    invoice:        'Fee invoice',
    invoices:       'Fee invoices',
    primary_record: 'student',
    primary_action: 'Add student',
    kpi_pipeline:   'Active enrolments',
    kpi_won:        'New enrolments this month',
    kpi_invoices:   'Fees pending',
    kpi_overdue:    'Overdue fees',
  },

  'Restaurant / cafe': {
    contact:        'Guest',
    contacts:       'Guests',
    contact_new:    'New guest',
    contact_add:    'Add guest',
    deal:           'Reservation',
    deals:          'Reservations',
    deal_new:       'New reservation',
    deal_pipeline:  'Reservations + catering',
    lead:           'Inquiry',
    leads:          'Inquiries',
    primary_record: 'reservation',
    primary_action: 'Add reservation',
    kpi_pipeline:   'Upcoming reservations',
    kpi_won:        'Catering orders this month',
    kpi_invoices:   'Pending payments',
    kpi_overdue:    'Reservation no-shows',
  },

  'Beauty / salon / wellness': {
    contact:        'Customer',
    contacts:       'Customers',
    contact_new:    'New customer',
    contact_add:    'Add customer',
    deal:           'Appointment',
    deals:          'Appointments',
    deal_new:       'New appointment',
    deal_pipeline:  'Appointments pipeline',
    invoice:        'Bill',
    invoices:       'Bills',
    primary_record: 'customer',
    primary_action: 'Add customer',
    kpi_pipeline:   'Upcoming appointments',
    kpi_won:        'Services this month',
    kpi_invoices:   'Bills pending',
    kpi_overdue:    'Rebook reminders due',
  },

  'Garment / textile retail': {
    contact:        'Buyer',
    contacts:       'Buyers',
    contact_new:    'New buyer',
    contact_add:    'Add buyer',
    deal:           'Order',
    deals:          'Orders',
    deal_new:       'New order',
    deal_pipeline:  'Order pipeline',
    primary_record: 'buyer',
    primary_action: 'Add buyer',
    kpi_pipeline:   'Open orders',
    kpi_won:        'Orders shipped',
    kpi_invoices:   'Invoices pending',
    kpi_overdue:    'Overdue wholesale dues',
  },

  'Logistics / transport': {
    contact:        'Consignor',
    contacts:       'Consignors',
    contact_new:    'New consignor',
    contact_add:    'Add consignor',
    deal:           'Consignment',
    deals:          'Consignments',
    deal_new:       'New consignment',
    deal_pipeline:  'Consignment pipeline',
    invoice:        'Freight invoice',
    invoices:       'Freight invoices',
    primary_record: 'consignor',
    primary_action: 'Add consignor',
    kpi_pipeline:   'Active dispatches',
    kpi_won:        'Delivered this month',
    kpi_invoices:   'Freight pending',
    kpi_overdue:    'Stuck shipments',
  },

  'Construction / contracting': {
    contact:        'Client',
    contacts:       'Clients',
    contact_new:    'New client',
    contact_add:    'Add client',
    deal:           'Project',
    deals:          'Projects',
    deal_new:       'New project',
    deal_pipeline:  'Project pipeline',
    primary_record: 'client',
    primary_action: 'Add client',
    kpi_pipeline:   'Active projects',
    kpi_won:        'Milestones completed',
    kpi_invoices:   'Milestone payments due',
    kpi_overdue:    'Site escalations',
  },

  'Auto repair / garage': {
    contact:        'Customer',
    contacts:       'Customers',
    contact_new:    'New customer',
    contact_add:    'Add customer',
    deal:           'Job card',
    deals:          'Job cards',
    deal_new:       'New job card',
    deal_pipeline:  'Service queue',
    invoice:        'Bill',
    invoices:       'Bills',
    primary_record: 'customer',
    primary_action: 'Add customer',
    kpi_pipeline:   'Vehicles in service',
    kpi_won:        'Jobs completed',
    kpi_invoices:   'Bills pending',
    kpi_overdue:    'Service reminders due',
  },

  'Photography / event services': {
    contact:        'Client',
    contacts:       'Clients',
    contact_new:    'New client',
    contact_add:    'Add client',
    deal:           'Shoot',
    deals:          'Shoots',
    deal_new:       'New shoot',
    deal_pipeline:  'Shoots booked',
    lead:           'Inquiry',
    leads:          'Inquiries',
    primary_record: 'client',
    primary_action: 'Add client',
    kpi_pipeline:   'Upcoming shoots',
    kpi_won:        'Events this month',
    kpi_invoices:   'Payments pending',
    kpi_overdue:    'Delivery overdue',
  },

  'Travel / tour operator': {
    contact:        'Traveller',
    contacts:       'Travellers',
    contact_new:    'New traveller',
    contact_add:    'Add traveller',
    deal:           'Itinerary',
    deals:          'Itineraries',
    deal_new:       'New itinerary',
    deal_pipeline:  'Trip pipeline',
    lead:           'Inquiry',
    leads:          'Inquiries',
    primary_record: 'traveller',
    primary_action: 'Add traveller',
    kpi_pipeline:   'Upcoming trips',
    kpi_won:        'Trips completed',
    kpi_invoices:   'Payments pending',
    kpi_overdue:    'Document collection due',
  },

  'Real estate broker': {
    contact:        'Lead',
    contacts:       'Leads',
    contact_new:    'New lead',
    contact_add:    'Add lead',
    company:        'Property',
    companies:      'Properties',
    company_new:    'New property',
    deal:           'Closure',
    deals:          'Closures',
    deal_new:       'New closure',
    deal_pipeline:  'Closure pipeline',
    invoice:        'Brokerage invoice',
    invoices:       'Brokerage invoices',
    primary_record: 'lead',
    primary_action: 'Add lead',
    kpi_pipeline:   'Active closures',
    kpi_won:        'Closures this month',
    kpi_invoices:   'Brokerage pending',
    kpi_overdue:    'Stalled inquiries',
  },
};


// ── Public API ──────────────────────────────────────────────────────────

// Build a case-insensitive lookup once. Without this, an industry stored
// as 'healthcare' (lowercase) or 'Healthcare ' (trailing space) would
// silently fall through to defaults, same shape of bug we just patched
// in api/industry_kpis.py. Backend normalise_industry() is the source of
// truth; this mirrors its behaviour on the JS side.
const _INDUSTRY_TERMS_CI = {};
for (const k of Object.keys(INDUSTRY_TERMS)) {
  _INDUSTRY_TERMS_CI[k.toLowerCase()] = INDUSTRY_TERMS[k];
}

// Shared resolver, pure, no React. Both the hook and the standalone
// helper delegate here so there's one code path for lookup logic.
function _resolve(industry, key) {
  const map = _INDUSTRY_TERMS_CI[(industry || '').trim().toLowerCase()] || {};
  if (key in map) return map[key];
  if (key in DEFAULT_TERMS) return DEFAULT_TERMS[key];
  return key;
}

/**
 * Get the term lookup for the current business's industry. Returns a
 * function: `t(key) → label`. Always call inside a component so it
 * re-evaluates when the user switches workspace.
 *
 * Usage:
 *   const t = useTerm();
 *   <h2>{t('deals')}</h2>
 *
 * Unknown industry → falls through to DEFAULT_TERMS.
 * Unknown key → returns the key unchanged so a missing translation is
 * visible (not a silent blank).
 */
export function useTerm() {
  const biz = getCurrentBusiness();
  const industry = (biz?.industry || '').trim();
  return (key) => _resolve(industry, key);
}

/**
 * Non-hook variant for callers outside React (services, helpers).
 * Resolves against the current business at call time. Safe to call from
 * anywhere, doesn't touch React state.
 */
export function term(key) {
  const biz = getCurrentBusiness();
  return _resolve((biz?.industry || '').trim(), key);
}

/**
 * Test/inspection helper, returns the full vocabulary the UI will
 * present for a given industry. Used by the onboarding preview step
 * and any future "what will my workspace look like?" screen.
 */
export function termsForIndustry(industry) {
  const map = _INDUSTRY_TERMS_CI[(industry || '').trim().toLowerCase()] || {};
  return { ...DEFAULT_TERMS, ...map };
}

export const SUPPORTED_INDUSTRIES = Object.keys(INDUSTRY_TERMS);
