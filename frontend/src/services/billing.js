/**
 * Billing — Razorpay Standard Checkout integration.
 *
 * Frontend never sees the Razorpay KEY_SECRET. We POST {plan} to
 * /api/billing/create-order; the backend returns an order_id + the public
 * key_id. We then open the Razorpay modal with those, and Razorpay handles
 * card/UPI entry, OTPs, etc.
 *
 * After the user pays, Razorpay calls our `handler` callback with three
 * fields. We forward them to /api/billing/verify-payment so the server can
 * recompute the HMAC signature and confirm Razorpay actually signed it
 * (defends against an attacker who tries to fake "I paid" by hitting the
 * verify endpoint with arbitrary data).
 */
import { getToken, getBusinessId } from './auth';

function authHeaders(extra = {}) {
  const h = { 'Content-Type': 'application/json', ...extra };
  const t = getToken();      if (t) h['Authorization']    = `Bearer ${t}`;
  const b = getBusinessId(); if (b) h['X-Business-Id']    = b;
  return h;
}

async function req(path, opts = {}) {
  const res = await fetch(path, { ...opts, headers: { ...authHeaders(), ...(opts.headers || {}) } });
  if (res.status === 401) {
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const txt = await res.text();
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch { /* leave as-is */ }
    throw new Error(msg);
  }
  return res.json();
}

export const getPlans = () => req('/api/billing/plans');

// Live subscription state for the current business: plan_key, status,
// is_trial, trial_days_remaining, trial_ends_at, etc. Read by the
// top-nav trial badge so the customer always sees the countdown.
export const getSubscription = () => req('/api/billing/subscription');

export const createOrder = (plan, extra = {}) =>
  req('/api/billing/create-order', {
    method: 'POST',
    body: JSON.stringify({ plan, ...extra }),
  });

export const verifyPayment = (payload) =>
  req('/api/billing/verify-payment', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

/**
 * Lazy-load the Razorpay Checkout script. Returns the global Razorpay
 * constructor. We don't import this from a bundle because Razorpay updates
 * checkout.js out-of-band — we always want the latest.
 */
function loadRazorpayScript() {
  return new Promise((resolve, reject) => {
    if (typeof window !== 'undefined' && window.Razorpay) {
      return resolve(window.Razorpay);
    }
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    script.onload = () => {
      if (window.Razorpay) resolve(window.Razorpay);
      else reject(new Error('Razorpay script loaded but global is missing'));
    };
    script.onerror = () => reject(new Error('Failed to load Razorpay script (network blocked?)'));
    document.body.appendChild(script);
  });
}

/**
 * Open the Razorpay checkout modal for the given plan. Resolves with the
 * verified payment payload (after server-side signature check). Rejects on
 * cancel, network error, or signature mismatch.
 *
 * @param {object} opts
 * @param {string} opts.plan      Plan key ("starter" | "pro" | "privacy")
 * @param {string} opts.email     Prefill in checkout form
 * @param {string} opts.name      Prefill — customer / business name
 * @param {string} opts.contact   Prefill phone (E.164 ideally)
 * @param {string} opts.theme     Hex color for the modal accent (default brand purple)
 */
export async function openRazorpayCheckout({
  plan, email = '', name = '', contact = '',
  theme = '#6366F1',
} = {}) {
  if (!plan) throw new Error('plan is required');

  // 1. Mint a Razorpay order on our backend (server-side amount lookup —
  //    we do NOT trust client-supplied amounts).
  const order = await createOrder(plan);

  // 2. Make sure checkout.js is loaded.
  const Razorpay = await loadRazorpayScript();

  // 3. Open the modal. Returns a Promise that resolves on verified payment.
  return new Promise((resolve, reject) => {
    const rzp = new Razorpay({
      key:          order.key_id,             // public test/live key
      order_id:     order.order_id,
      amount:       order.amount,
      currency:     order.currency,
      name:         'NexusAgent',
      description:  `Subscription — ${plan}`,
      image:        '/logo.svg',              // optional, falls back gracefully
      prefill:      { email, name, contact },
      notes:        { plan },
      theme:        { color: theme },
      // Modal callback when the user closes without paying.
      modal: {
        ondismiss: () => reject(new Error('Payment cancelled')),
      },
      // Success path. Razorpay gives us the three fields below; we forward
      // them to the server for HMAC verification.
      handler: async (response) => {
        try {
          const verified = await verifyPayment({
            razorpay_order_id:   response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature:  response.razorpay_signature,
            plan,
          });
          resolve(verified);
        } catch (e) {
          reject(e);
        }
      },
    });

    // payment.failed = real failure (decline, OTP timeout, etc.) vs ondismiss
    // (user clicked X). Surface both so the UI can show a useful message.
    rzp.on('payment.failed', (resp) => {
      const desc = resp?.error?.description || 'Payment failed';
      reject(new Error(desc));
    });

    rzp.open();
  });
}
