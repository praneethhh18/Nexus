"""Industry workspace presets.

Onboarding uses these presets after a new user selects an industry. The goal is
not to remove product surface area. Every business keeps access to every module;
the preset simply tunes the first-run workspace so the most relevant agents,
templates, and next actions are ready immediately.
"""
from __future__ import annotations

import json
from typing import Dict, List

from config.db import get_conn
from utils.timez import now_iso

PRESETS: Dict[str, Dict] = {
    # ── Healthcare ────────────────────────────────────────────────────────
    # Tone: respectful, calm, formal honorifics (Mr/Mrs/Dr). Indian patients
    # expect explicit timing and clear instructions. Avoid clinical jargon
    # in the patient-facing copy; reserve that for internal templates.
    "Healthcare": {
        "tools": ["Patient intake", "Policy knowledge base", "Appointment follow-ups", "Privacy review"],
        "priority_agents": ["email_triage", "meeting_prep", "morning_briefing", "memory_consolidate"],
        "schedules": {"email_triage": 15, "meeting_prep": 10, "memory_consolidate": 10080},
        "templates": [
            {
                "name": "Appointment reminder",
                "subject": "Your appointment at {{business_name}} on {{appointment_date}}",
                "body": "Dear {{salutation}} {{last_name}},\n\nThis is a gentle reminder of your appointment with {{doctor_name}} on {{appointment_date}} at {{appointment_time}}.\n\nPlease reach 10 minutes early and carry any previous prescriptions or reports.\n\nIf you need to reschedule, reply to this message or call us on {{clinic_phone}}.\n\nWishing you good health,\n{{business_name}}",
            },
            {
                "name": "Post-visit follow-up",
                "subject": "Checking in after your visit",
                "body": "Dear {{salutation}} {{last_name}},\n\nIt was good to see you on {{visit_date}}. {{doctor_name}} has advised {{next_step}} and we have scheduled a follow-up for {{next_appointment_date}}.\n\nPlease let us know how you are feeling and if any new symptoms have come up since the visit. Reply here or message us on WhatsApp anytime.\n\nTake care,\n{{business_name}}",
            },
            {
                "name": "Pending bill reminder",
                "subject": "A small payment is pending — {{business_name}}",
                "body": "Dear {{salutation}} {{last_name}},\n\nWe noticed that the bill for your {{service_name}} on {{visit_date}} — amount {{amount}} — is still outstanding.\n\nYou can settle it at the clinic, via UPI to {{upi_id}}, or by replying to this email and we will share a payment link.\n\nDo let us know if there is any concern with the bill — we are happy to clarify.\n\nThank you,\n{{business_name}}",
            },
        ],
    },

    # ── Real estate ───────────────────────────────────────────────────────
    # Tone: confident, slightly urgent, assumptive close. Indian property
    # transactions are heavy on relationship + speed; mention budget and
    # location early because that's what buyers actually filter on.
    "Real estate": {
        "tools": ["Lead capture", "Property documents", "Buyer follow-ups", "Deal pipeline"],
        "priority_agents": ["stale_deal_watcher", "meeting_prep", "outbound_caller", "email_triage"],
        "schedules": {"stale_deal_watcher": 1440, "meeting_prep": 10, "email_triage": 15},
        "templates": [
            {
                "name": "New listing match",
                "subject": "Found a {{bhk}} that matches your search in {{location}}",
                "body": "Hi {{first_name}},\n\nA new listing just came up that fits what you told me:\n\n• {{property_name}} — {{bhk}}\n• {{location}}\n• Asking ₹{{price}}\n• {{key_amenity}}\n\nI can arrange a site visit this {{visit_window}} — most clients prefer Saturday morning. Want me to block 11 AM?\n\nReplying with a thumbs-up works too.\n\n{{sender_name}}",
            },
            {
                "name": "Site visit confirmation",
                "subject": "Confirmed: {{property_name}} visit on {{visit_date}}",
                "body": "Hi {{first_name}},\n\nQuick confirmation for your site visit:\n\n📍 {{property_name}}, {{location}}\n📅 {{visit_date}} at {{visit_time}}\n📞 My number: {{sender_phone}}\n\nGoogle Maps link: {{maps_link}}\n\nI will reach 5 minutes before you. If anything changes, ping me on WhatsApp.\n\n{{sender_name}}",
            },
            {
                "name": "Quiet-buyer nudge",
                "subject": "Still looking, {{first_name}}?",
                "body": "Hi {{first_name}},\n\nIt's been a few days — just checking in. Are you still actively looking in {{location}}, or has something shifted on budget or timing?\n\nIf the {{property_name}} we looked at wasn't quite right, I have two more options in the same range that you haven't seen yet. Five-minute call this week?\n\n{{sender_name}}",
            },
        ],
    },

    # ── Education ─────────────────────────────────────────────────────────
    # Tone: warm and structured. Indian parents respond well to specific
    # next steps + deadlines. Always address the parent (not the student)
    # for under-18 admissions copy.
    "Education": {
        "tools": ["Admissions support", "Course FAQ", "Student follow-ups", "Reports"],
        "priority_agents": ["email_triage", "morning_briefing", "meeting_prep", "memory_consolidate"],
        "schedules": {"email_triage": 30, "morning_briefing": 1440, "meeting_prep": 10},
        "templates": [
            {
                "name": "Admission inquiry reply",
                "subject": "Welcome to {{business_name}} — {{program_name}} details inside",
                "body": "Dear {{salutation}} {{last_name}},\n\nThank you for your interest in our {{program_name}} for {{student_first_name}}.\n\nHere is what happens next:\n\n1. Complete the admission form: {{form_link}}\n2. Pay the ₹{{registration_fee}} registration fee (payment link in the form)\n3. We will schedule an interaction with {{student_first_name}} within 3 working days\n\nA brochure with fee structure and demo class details is attached.\n\nAny questions, just reply — happy to clarify.\n\nWarm regards,\n{{sender_name}}\n{{business_name}}",
            },
            {
                "name": "Fee reminder (parent)",
                "subject": "{{student_first_name}}'s {{installment_label}} fee — gentle reminder",
                "body": "Dear {{salutation}} {{last_name}},\n\nThis is a gentle reminder that {{student_first_name}}'s {{installment_label}} fee of ₹{{amount}} is due on {{due_date}}.\n\nYou can pay via:\n• UPI: {{upi_id}}\n• Bank transfer: {{bank_details}}\n• At our office between 10 AM and 6 PM\n\nIf you are facing any difficulty with the payment, please call us on {{office_phone}} — we will work something out.\n\nThanks,\n{{business_name}}",
            },
            {
                "name": "Test result intimation",
                "subject": "{{student_first_name}}'s {{test_name}} result is ready",
                "body": "Dear {{salutation}} {{last_name}},\n\n{{student_first_name}}'s result for {{test_name}} held on {{test_date}}:\n\n• Score: {{score}}\n• Class rank: {{rank}}\n• Strong areas: {{strengths}}\n• Focus areas: {{weaknesses}}\n\nDetailed feedback from {{teacher_name}} is in the attached PDF. We have suggested a small revision plan on page 2.\n\nIf you would like to discuss, our next parent-teacher slot is {{ptm_date}}.\n\nRegards,\n{{business_name}}",
            },
        ],
    },

    # ── Legal ─────────────────────────────────────────────────────────────
    # Tone: precise, no emotion, structured. Avoid promises of outcomes —
    # legal/regulatory exposure. Use "matter" not "case" for civil work.
    "Legal": {
        "tools": ["Client intake", "Document Q&A", "Case task tracking", "Secure audit trail"],
        "priority_agents": ["meeting_prep", "email_triage", "memory_consolidate", "morning_briefing"],
        "schedules": {"meeting_prep": 10, "email_triage": 30, "memory_consolidate": 10080},
        "templates": [
            {
                "name": "Document request",
                "subject": "Documents required for {{matter_name}}",
                "body": "Dear {{salutation}} {{last_name}},\n\nFor us to proceed with {{matter_name}}, please share the following at the earliest:\n\n{{documents_list}}\n\nKindly upload via the secure link below — these will be stored under attorney-client privilege:\n{{upload_link}}\n\nIf any document is unavailable, please write back stating the reason; we can discuss alternatives.\n\nRegards,\n{{sender_name}}\nAdvocate, {{business_name}}",
            },
            {
                "name": "Matter status update",
                "subject": "Update on {{matter_name}} — {{update_date}}",
                "body": "Dear {{salutation}} {{last_name}},\n\nBelow is the position on {{matter_name}} as of {{update_date}}:\n\n• Last development: {{last_event}}\n• Next action: {{next_action}}\n• Expected date: {{next_date}}\n• Outstanding from your side: {{client_pending}}\n\nPlease confirm receipt and revert on the items pending from your end.\n\nRegards,\n{{sender_name}}\nAdvocate, {{business_name}}",
            },
            {
                "name": "Hearing intimation",
                "subject": "Hearing scheduled: {{matter_name}} on {{hearing_date}}",
                "body": "Dear {{salutation}} {{last_name}},\n\nThis is to inform you that {{matter_name}} is listed for hearing as below:\n\n📅 Date: {{hearing_date}}\n🕘 Time: {{hearing_time}}\n🏛 Court: {{court_name}}, {{court_address}}\n📋 Stage: {{hearing_stage}}\n\nKindly remain available on phone during these hours. Your physical presence {{presence_required}}.\n\nRegards,\n{{sender_name}}\nAdvocate, {{business_name}}",
            },
        ],
    },

    # ── Ecommerce ─────────────────────────────────────────────────────────
    # Tone: warm, fast, customer-first. Indian ecom customers want clear
    # tracking + reassurance on returns. Emoji used sparingly for delivery.
    "Ecommerce": {
        "tools": ["Product catalog", "Returns support", "Order follow-ups", "Customer inbox"],
        "priority_agents": ["email_triage", "invoice_reminder", "stale_deal_watcher", "morning_briefing"],
        "schedules": {"email_triage": 15, "invoice_reminder": 1440, "stale_deal_watcher": 1440},
        "templates": [
            {
                "name": "Order confirmed",
                "subject": "Order #{{order_id}} confirmed — yay! 🎉",
                "body": "Hi {{first_name}},\n\nThanks for shopping with {{business_name}}! Your order is in.\n\nOrder #{{order_id}}\nItems: {{items_summary}}\nTotal: ₹{{amount}} ({{payment_method}})\n\nShipping to:\n{{shipping_address}}\n\nExpected delivery: {{expected_delivery}}\nYou will get a tracking link once it ships (usually within 24 hours).\n\nQuestions? Just reply or WhatsApp us on {{support_whatsapp}}.\n\n{{business_name}}",
            },
            {
                "name": "Return / refund acknowledgement",
                "subject": "Got your return request for order #{{order_id}}",
                "body": "Hi {{first_name}},\n\nSorry the {{product_name}} did not work out — we will sort this quickly.\n\nWhat happens next:\n\n1. A pickup will be arranged on {{pickup_date}} ({{pickup_window}})\n2. Once the item reaches us, we inspect within 24 hours\n3. Refund of ₹{{refund_amount}} is credited to {{refund_method}} in 3-5 working days\n\nReturn reference: {{return_id}}\n\nIf anything is off, reply with photos and we will fix it before pickup.\n\n{{business_name}}",
            },
            {
                "name": "Cart abandonment nudge",
                "subject": "Forgot something at {{business_name}}? 🛒",
                "body": "Hi {{first_name}},\n\nNoticed you had a few things in your cart but didn't get to checkout — completely understand.\n\nQuick reminder: {{product_name}} is still waiting for you at ₹{{price}}.\n\nIf you needed help choosing a size, payment, or delivery — happy to help. Just reply to this email or WhatsApp {{support_whatsapp}}.\n\nHere is a small thank-you: use code {{coupon_code}} for ₹{{coupon_value}} off if you check out in the next 24 hours.\n\n{{business_name}}",
            },
        ],
    },

    # ── Finance ───────────────────────────────────────────────────────────
    # Tone: precise, calm, slightly formal. Indian finance clients (CA, RIA,
    # insurance) value accuracy + compliance language. Always include the
    # underlying regulation/form reference where relevant.
    "Finance": {
        "tools": ["Client onboarding", "Invoice reminders", "Compliance docs", "Secure reporting"],
        "priority_agents": ["invoice_reminder", "email_triage", "meeting_prep", "memory_consolidate"],
        "schedules": {"invoice_reminder": 1440, "email_triage": 30, "meeting_prep": 10},
        "templates": [
            {
                "name": "Payment / fee reminder",
                "subject": "Invoice {{invoice_number}} — payment due {{due_date}}",
                "body": "Dear {{salutation}} {{last_name}},\n\nThis is a courteous reminder that invoice {{invoice_number}} for ₹{{amount}} is due on {{due_date}}.\n\nPayment options:\n• NEFT/RTGS: {{bank_details}}\n• UPI: {{upi_id}}\n• Cheque favouring \"{{business_name}}\"\n\nKindly share UTR/transaction reference once paid so we can update our records.\n\nFor any concerns with the invoice, please write to me directly and I will address it.\n\nRegards,\n{{sender_name}}\n{{business_name}}",
            },
            {
                "name": "Compliance document request",
                "subject": "Documents required for {{filing_period}} filings",
                "body": "Dear {{salutation}} {{last_name}},\n\nTo complete your {{filing_period}} compliance, please share:\n\n{{documents_list}}\n\nDeadline (statutory): {{statutory_due_date}}\nOur internal deadline (to file with buffer): {{internal_due_date}}\n\nSecure upload link: {{upload_link}}\n\nIf any document is delayed or unavailable, please intimate us at the earliest so we can plan an extension request if needed.\n\nRegards,\n{{sender_name}}\n{{business_name}}",
            },
            {
                "name": "Annual review check-in",
                "subject": "Time for your annual {{service_name}} review",
                "body": "Dear {{salutation}} {{last_name}},\n\nIt has been a year since we onboarded you for {{service_name}} — that's worth a sit-down.\n\nA review meeting helps us:\n\n• Walk through your portfolio performance / filings done\n• Update your risk profile / financial goals\n• Flag any new regulations or tax-saving options\n• Plan the next 12 months\n\nMost clients take 30-45 minutes. I have these slots open: {{slot_options}}\n\nReply with what works, or pick one directly here: {{booking_link}}\n\nRegards,\n{{sender_name}}\n{{business_name}}",
            },
        ],
    },

    # ── SaaS ──────────────────────────────────────────────────────────────
    # Tone: consultative, value-led. Focus on the user's outcome, not your
    # product. Indian B2B SaaS customers respond to specific time saved /
    # revenue impact, not feature lists.
    "SaaS": {
        "tools": ["Pipeline CRM", "Support triage", "Churn signals", "Product knowledge base"],
        "priority_agents": ["stale_deal_watcher", "email_triage", "meeting_prep", "morning_briefing"],
        "schedules": {"stale_deal_watcher": 1440, "email_triage": 15, "meeting_prep": 10},
        "templates": [
            {
                "name": "Demo follow-up",
                "subject": "Thanks for the {{product_name}} demo — quick recap",
                "body": "Hi {{first_name}},\n\nThanks for your time today. Quick recap of what stood out from our conversation:\n\n• Your main pain: {{pain_point}}\n• {{product_name}} addresses this via {{key_feature}}\n• Estimated impact for {{company_name}}: {{outcome_metric}}\n\nNext step I suggested: {{proposed_next_step}}\n\nIf you want to involve {{other_stakeholder}}, I am happy to do a 20-minute deep-dive with them too. Just reply with a couple of slots.\n\nNo pressure — keep this as a reference for whenever it's the right time.\n\n{{sender_name}}",
            },
            {
                "name": "Trial expiry reminder",
                "subject": "Your {{product_name}} trial expires {{expiry_date}}",
                "body": "Hi {{first_name}},\n\nYour trial of {{product_name}} ends on {{expiry_date}}.\n\nWhat we have seen so far on your workspace:\n\n• {{usage_stat_1}}\n• {{usage_stat_2}}\n• {{usage_stat_3}}\n\nIf {{product_name}} is doing the job, here are the plan options: {{pricing_link}}\n\nIf something is not clicking — happy to do a quick 15-minute call to debug. Reply with a slot or just \"call me\" and I will reach out.\n\n{{sender_name}}",
            },
            {
                "name": "Renewal check-in",
                "subject": "Quick check-in before your {{renewal_date}} renewal",
                "body": "Hi {{first_name}},\n\nYour {{product_name}} renewal is coming up on {{renewal_date}}. Before that, a quick sanity check from my side:\n\n• Are you and the team getting what you need from us?\n• Any features missing that would change the picture?\n• Team size changes for the new term?\n\nA 20-minute call this week would help me build the right renewal proposal. {{booking_link}}\n\nIf everything is working — even better — reply with \"all good\" and I will prep the renewal as-is.\n\n{{sender_name}}",
            },
        ],
    },

    # ── Manufacturing ────────────────────────────────────────────────────
    # Tone: factual, logistic-heavy. Indian SME manufacturing relationships
    # are built on dispatch dates + payment terms + GST. Avoid flowery copy.
    "Manufacturing": {
        "tools": ["Vendor docs", "Order follow-ups", "Operations tasks", "Reports"],
        "priority_agents": ["morning_briefing", "email_triage", "invoice_reminder", "meeting_prep"],
        "schedules": {"morning_briefing": 1440, "email_triage": 30, "invoice_reminder": 1440},
        "templates": [
            {
                "name": "Quote / PO acknowledgement",
                "subject": "Acknowledgement: {{purchase_order}} from {{customer_name}}",
                "body": "Dear {{salutation}} {{last_name}},\n\nWe acknowledge receipt of {{purchase_order}} dated {{po_date}} for:\n\n{{line_items}}\n\nTotal value: ₹{{total_value}} (GST extra at {{gst_rate}}%)\nPayment terms: {{payment_terms}}\nExpected dispatch: {{dispatch_date}}\n\nWe will share the proforma invoice within 24 hours and confirm dispatch schedule by {{schedule_confirm_date}}.\n\nFor any change requests, kindly write to us before {{change_cutoff_date}}.\n\nRegards,\n{{sender_name}}\n{{business_name}}",
            },
            {
                "name": "Dispatch update",
                "subject": "Dispatch update — {{purchase_order}}",
                "body": "Dear {{salutation}} {{last_name}},\n\nDispatch position for {{purchase_order}}:\n\n• Status: {{dispatch_status}}\n• Quantity dispatched: {{qty_dispatched}} / {{qty_total}}\n• Transporter: {{transporter_name}}\n• LR / Docket no: {{lr_number}}\n• Expected delivery: {{expected_delivery}}\n• Balance dispatch: {{balance_date}}\n\nInvoice + e-way bill attached.\n\nKindly acknowledge receipt of goods on the delivery copy.\n\nRegards,\n{{sender_name}}\n{{business_name}}",
            },
            {
                "name": "Payment follow-up",
                "subject": "Outstanding payment — {{purchase_order}}",
                "body": "Dear {{salutation}} {{last_name}},\n\nThe following invoice against {{purchase_order}} is outstanding:\n\n• Invoice no: {{invoice_number}}\n• Invoice date: {{invoice_date}}\n• Amount: ₹{{amount}}\n• Due date: {{due_date}}\n• Days overdue: {{days_overdue}}\n\nKindly arrange the payment at the earliest and share the UTR / cheque details.\n\nIf there is any dispute or short delivery, please share the discrepancy note so we can resolve it on priority.\n\nRegards,\n{{sender_name}}\n{{business_name}}",
            },
        ],
    },

    # ── Hospitality ───────────────────────────────────────────────────────
    # Tone: warm, hospitable, anticipates needs. Indian guests like specific
    # local touches (check-in time, food preferences, transport).
    "Hospitality": {
        "tools": ["Booking support", "Guest FAQs", "Review follow-ups", "Shift tasks"],
        "priority_agents": ["email_triage", "morning_briefing", "evening_digest", "meeting_prep"],
        "schedules": {"email_triage": 15, "morning_briefing": 1440, "evening_digest": 1440},
        "templates": [
            {
                "name": "Booking confirmation",
                "subject": "Looking forward to hosting you — booking confirmed",
                "body": "Dear {{salutation}} {{last_name}},\n\nYour booking at {{business_name}} is confirmed. We are excited to host you!\n\n📅 Check-in: {{checkin_date}} from {{checkin_time}}\n📅 Check-out: {{checkout_date}} by {{checkout_time}}\n👥 Guests: {{guest_count}}\n🏠 Room/Table: {{room_or_table}}\n💳 Booking value: ₹{{amount}} ({{payment_status}})\n\nA few details for your convenience:\n• {{local_tip_1}}\n• {{local_tip_2}}\n• Any dietary preferences? Reply and we'll plan ahead.\n\nFor anything before your visit, WhatsApp us on {{whatsapp_number}}.\n\nWarmly,\n{{business_name}} team",
            },
            {
                "name": "Pre-arrival WhatsApp",
                "subject": "Your stay starts tomorrow — quick details",
                "body": "Hi {{first_name}},\n\nWe're getting your {{room_or_table}} ready for tomorrow. A few last things:\n\n• Address: {{address}}\n• Google Maps: {{maps_link}}\n• Reception: {{reception_phone}}\n• Pickup needed? Let us know train/flight number, we can arrange a cab\n• Approx travel time from {{transport_hub}}: {{travel_minutes}} mins\n\nWe'll keep some {{welcome_drink}} ready for you on arrival.\n\nSee you tomorrow,\n{{business_name}}",
            },
            {
                "name": "Review request (post-stay)",
                "subject": "It was wonderful having you — a small favour?",
                "body": "Dear {{salutation}} {{last_name}},\n\nThank you for choosing {{business_name}} for your recent {{visit_type}}. We hope every part of it lived up to your expectations.\n\nIf you have 60 seconds, a few words on Google would mean a lot to our small team: {{review_link}}\n\nIf anything wasn't quite right, please tell us directly — reply to this email and we'll make it good.\n\nLooking forward to welcoming you back,\n{{owner_name}} & the {{business_name}} family",
            },
        ],
    },

    # ── Local services ────────────────────────────────────────────────────
    # Tone: friendly, fast, no formality. Mostly WhatsApp-tier short messages.
    # Indian local service customers want time slots and price upfront.
    "Local services": {
        "tools": ["Lead intake", "Job scheduling", "Quote follow-ups", "Invoice reminders"],
        "priority_agents": ["outbound_caller", "invoice_reminder", "email_triage", "stale_deal_watcher"],
        "schedules": {"email_triage": 15, "invoice_reminder": 1440, "stale_deal_watcher": 1440},
        "templates": [
            {
                "name": "Quote + slot offer",
                "subject": "Quote for {{service_name}} — and a couple of slots",
                "body": "Hi {{first_name}},\n\nThanks for reaching out. Here's the estimate for {{service_name}}:\n\n• Approx cost: ₹{{quote_amount}}\n• Includes: {{quote_inclusions}}\n• Extra if needed: {{quote_extras}}\n• Time to complete: {{duration}}\n\nFree slots this week:\n• {{slot_option_1}}\n• {{slot_option_2}}\n• {{slot_option_3}}\n\nReply with the one that works and I'll send the technician's details. Cash, UPI, or card all work for payment.\n\n{{sender_name}}\n{{business_name}}",
            },
            {
                "name": "Job done — payment + review",
                "subject": "All sorted at your place — small payment + a favour",
                "body": "Hi {{first_name}},\n\nGood news — {{service_name}} is done. {{technician_name}} cleaned up before leaving.\n\nAmount due: ₹{{amount}}\nPay easiest via UPI: {{upi_id}}\n(Or reply \"cash\" and we'll send someone to collect this weekend.)\n\nWhile it's fresh — could you drop a quick Google review? It really helps a small team like ours: {{review_link}}\n\nThanks for trusting us. If anything is not 100%, just message and we'll come back free of charge within 7 days.\n\n{{sender_name}}",
            },
            {
                "name": "Maintenance reminder",
                "subject": "Time for {{service_name}} again, {{first_name}}?",
                "body": "Hi {{first_name}},\n\nIt's been {{months_since}} months since we did your {{last_service}} on {{last_date}}.\n\nUsually around this time we recommend {{recommended_action}} — keeps things running smooth and avoids the bigger ₹{{big_repair_cost}} fix later.\n\nQuick service is about ₹{{quick_service_cost}} and takes {{quick_duration}}. Free slot tomorrow: {{slot}}.\n\nReply \"yes\" and we'll come over. No pressure if not.\n\n{{sender_name}}\n{{business_name}}",
            },
        ],
    },

    # ── Consulting ────────────────────────────────────────────────────────
    # Tone: structured, action-oriented, value-led. Consultants are judged
    # on clarity of thought in writing; templates should reflect that.
    "Consulting": {
        "tools": ["Client briefs", "Proposal docs", "Meeting prep", "Project tasks"],
        "priority_agents": ["meeting_prep", "morning_briefing", "stale_deal_watcher", "email_triage"],
        "schedules": {"meeting_prep": 10, "morning_briefing": 1440, "email_triage": 30},
        "templates": [
            {
                "name": "Engagement kickoff",
                "subject": "{{engagement_name}} — kickoff details",
                "body": "Hi {{first_name}},\n\nLooking forward to starting {{engagement_name}} with the {{company_name}} team. Quick alignment before we begin:\n\n**Scope (week 1-{{total_weeks}})**\n{{scope_summary}}\n\n**Expected outcome**\n{{outcome_statement}}\n\n**What we need from you in week 1**\n{{client_inputs_week_1}}\n\n**Cadence**\n{{cadence}} ({{meeting_day}} {{meeting_time}})\n\n**Single point of contact (your side)**\n{{client_spoc}}\n\nIf any of this needs adjusting, this week is the time. Otherwise, see you on {{kickoff_date}}.\n\n{{sender_name}}",
            },
            {
                "name": "Meeting recap + next steps",
                "subject": "Recap: {{meeting_name}} ({{meeting_date}})",
                "body": "Hi {{first_name}},\n\nGreat conversation today. Quick summary so we are aligned:\n\n**Decisions made**\n{{decisions}}\n\n**Open items**\n{{open_items}}\n\n**Action items**\n• {{action_owner_1}}: {{action_item_1}} (by {{action_due_1}})\n• {{action_owner_2}}: {{action_item_2}} (by {{action_due_2}})\n• {{action_owner_3}}: {{action_item_3}} (by {{action_due_3}})\n\n**Next meeting**\n{{next_meeting_date}} — {{next_meeting_focus}}\n\nFlag anything that looks off — I would rather correct now than later.\n\n{{sender_name}}",
            },
            {
                "name": "Proposal follow-up",
                "subject": "{{proposal_name}} — any questions before we firm up?",
                "body": "Hi {{first_name}},\n\nFollowing up on the {{proposal_name}} I shared on {{sent_date}}. A few thoughts in case useful:\n\n**On scope** — the only piece worth a second look is {{scope_question}}. Happy to expand or trim depending on how the {{stakeholder_name}} conversation went.\n\n**On timeline** — we can start as early as {{earliest_start}}; the {{milestone_name}} milestone falls on {{milestone_date}} based on that.\n\n**On commercials** — flexible on payment cadence if monthly works better than the current 30/40/30.\n\nA 20-minute call this week would help me adjust before sending v2. Slots: {{slot_options}}.\n\n{{sender_name}}",
            },
        ],
    },
}

DEFAULT_PRESET = {
    "tools": ["Business knowledge base", "CRM pipeline", "Task automation", "Reports"],
    "priority_agents": ["morning_briefing", "email_triage", "meeting_prep", "memory_consolidate"],
    "schedules": {"morning_briefing": 1440, "email_triage": 30, "meeting_prep": 10},
    "templates": [
        {
            "name": "General follow-up",
            "subject": "Following up on {{topic}}",
            "body": "Hi {{first_name}},\n\nFollowing up on {{topic}}. Next step: {{next_step}}.\n\nRegards,\n{{sender_name}}",
        },
        {
            "name": "Document request",
            "subject": "Documents needed for {{project_name}}",
            "body": "Hi {{first_name}},\n\nPlease share {{documents_needed}} for {{project_name}} when you can.\n\nRegards,\n{{sender_name}}",
        },
    ],
}


def normalize_industry(industry: str) -> str:
    raw = (industry or "").strip()
    for key in PRESETS:
        if key.lower() == raw.lower():
            return key
    return "Other"


def get_preset(industry: str) -> Dict:
    key = normalize_industry(industry)
    preset = PRESETS.get(key, DEFAULT_PRESET)
    return {
        "industry": key,
        "tools": list(preset["tools"]),
        "priority_agents": list(preset["priority_agents"]),
        "schedules": dict(preset["schedules"]),
        "templates": [dict(t) for t in preset["templates"]],
    }


def _read_business(business_id: str) -> Dict:
    from api.businesses import BUSINESSES_TABLE

    conn = get_conn()
    conn.row_factory = None
    try:
        row = conn.execute(
            f"SELECT industry, settings FROM {BUSINESSES_TABLE} WHERE id = ?",
            (business_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return {"industry": "", "settings": {}}
    settings = {}
    try:
        settings = json.loads(row[1] or "{}")
    except Exception:
        settings = {}
    return {"industry": row[0] or "", "settings": settings}


def _write_settings(business_id: str, settings: Dict) -> None:
    from api.businesses import BUSINESSES_TABLE

    conn = get_conn()
    try:
        conn.execute(
            f"UPDATE {BUSINESSES_TABLE} SET settings = ?, updated_at = ? WHERE id = ?",
            (json.dumps(settings), now_iso(), business_id),
        )
        conn.commit()
    finally:
        conn.close()


def _ensure_templates(business_id: str, user_id: str, templates: List[Dict]) -> List[str]:
    from api import email_templates

    existing = {t["name"].strip().lower() for t in email_templates.list_templates(business_id)}
    created: List[str] = []
    for tpl in templates:
        if tpl["name"].strip().lower() in existing:
            continue
        created_tpl = email_templates.create_template(business_id, user_id, tpl)
        created.append(created_tpl["name"])
        existing.add(tpl["name"].strip().lower())
    return created


def apply_industry_setup(
    business_id: str,
    user_id: str,
    industry: str | None = None,
    *,
    seed_sample_data: bool = True,
) -> Dict:
    """Apply agent schedules, feature focus, starter templates, AND drop
    industry-flavoured seed data into the workspace if it's empty.

    Idempotent on every layer:
      - personas/schedules: re-applying tunes the same rows
      - templates: only missing names are created
      - seed data: skipped entirely if the business already has CRM rows

    Args:
        seed_sample_data: set False when the caller already has real data
            and just wants to re-tune the preset (e.g. an industry change
            on an existing workspace).
    """
    business = _read_business(business_id)
    preset = get_preset(industry or business["industry"])

    from agents import personas
    from api import agent_schedule

    # Keep all built-ins available. Priority agents simply get explicit enabled
    # rows and tuned schedules so the workspace feels ready on first login.
    enabled: List[str] = []
    for agent_key in personas.DEFAULTS.keys():
        personas.set_enabled(business_id, agent_key, True)
        enabled.append(agent_key)

    schedules: Dict[str, int] = {}
    for agent_key, minutes in preset["schedules"].items():
        agent_schedule.set_interval(business_id, agent_key, minutes)
        schedules[agent_key] = minutes

    created_templates = _ensure_templates(business_id, user_id, preset["templates"])

    # Drop industry-flavoured CRM data so the dashboard isn't empty on Day 1.
    # The seeder has its own existence check — won't pollute real data.
    # Failure here MUST NOT block onboarding (e.g. if the industry isn't in
    # INDUSTRY_DATA we just skip silently and the user gets a clean workspace).
    seed_result: Dict[str, object] = {"seeded": False, "reason": "skipped"}
    if seed_sample_data:
        try:
            from api.industry_seed import seed_industry_sample
            seed_result = seed_industry_sample(business_id, user_id, preset["industry"])
        except Exception as e:
            from loguru import logger
            logger.warning(f"[IndustrySetup] seed step failed (non-fatal): {e}")
            seed_result = {"seeded": False, "reason": f"error: {e!s}"[:200]}

    settings = business["settings"]
    settings["industry_setup"] = {
        "industry": preset["industry"],
        "recommended_tools": preset["tools"],
        "priority_agents": preset["priority_agents"],
        "schedules": schedules,
        "seed": seed_result,
        "applied_at": now_iso(),
    }
    _write_settings(business_id, settings)

    return {
        "industry": preset["industry"],
        "recommended_tools": preset["tools"],
        "priority_agents": preset["priority_agents"],
        "enabled_agents": enabled,
        "schedules": schedules,
        "created_templates": created_templates,
        "seed": seed_result,
    }
