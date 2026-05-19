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

    # ── Tutoring / coaching ───────────────────────────────────────────────
    # The most common Indian SMB segment. Different from "Education" — these
    # are 1-on-1 tutors, JEE/NEET coaches, IELTS centres, music/dance teachers.
    "Tutoring / coaching": {
        "tools": ["Inquiry intake", "Trial-class scheduler", "Fee reminders", "Parent WhatsApp"],
        "priority_agents": ["email_triage", "outbound_caller", "invoice_reminder", "morning_briefing"],
        "schedules": {"email_triage": 15, "invoice_reminder": 1440, "morning_briefing": 1440},
        "templates": [
            {
                "name": "Trial-class invitation",
                "subject": "{{student_first_name}} — free trial class details",
                "body": "Dear {{salutation}} {{last_name}},\n\nThanks for the interest in our {{program_name}} for {{student_first_name}}.\n\nWe offer one free trial class — most parents take it before deciding:\n\n📅 {{trial_date}} at {{trial_time}}\n📍 {{venue_or_online_link}}\n📚 Topic: {{trial_topic}}\n👨‍🏫 Teacher: {{teacher_name}}\n\nPlease confirm by replying — we'll keep the slot.\n\nAfter the class, we can discuss schedule + fees over a 10-minute parent meeting.\n\n{{sender_name}}",
            },
            {
                "name": "Fee installment reminder",
                "subject": "{{student_first_name}}'s {{month_name}} fees — small reminder",
                "body": "Dear {{salutation}} {{last_name}},\n\nGentle reminder — {{student_first_name}}'s {{month_name}} fees of ₹{{amount}} were due on {{due_date}}.\n\nUPI: {{upi_id}}\nOr drop a cheque/cash at the centre between {{office_hours}}.\n\nIf there is any concern with the timing, please call me directly on {{owner_phone}} — we have helped many parents with adjusted plans.\n\nThanks,\n{{sender_name}}",
            },
        ],
    },

    # ── Restaurant / cafe ─────────────────────────────────────────────────
    "Restaurant / cafe": {
        "tools": ["Reservation desk", "Catering inquiries", "Reviews + reputation", "Daily-special broadcast"],
        "priority_agents": ["email_triage", "morning_briefing", "evening_digest", "outbound_caller"],
        "schedules": {"email_triage": 15, "morning_briefing": 1440, "evening_digest": 1440},
        "templates": [
            {
                "name": "Reservation confirmation",
                "subject": "Table booked at {{business_name}} on {{reservation_date}}",
                "body": "Hi {{first_name}},\n\nWe've kept your table at {{business_name}} for:\n\n📅 {{reservation_date}} at {{reservation_time}}\n👥 {{pax_count}} guests\n🍽 Table: {{table_id}}\n\nAny special occasion (birthday, anniversary)? Reply and we'll plan a little surprise.\n\nDietary preferences or allergies? Share now — our chef plans ahead.\n\nDirections: {{maps_link}}\nCall the host: {{host_phone}}\n\nSee you soon,\n{{business_name}}",
            },
            {
                "name": "Catering inquiry response",
                "subject": "{{business_name}} catering — quote for {{event_date}}",
                "body": "Hi {{first_name}},\n\nThanks for considering us for {{event_name}} on {{event_date}}.\n\nQuick estimate for {{pax_count}} guests:\n\n• Veg menu: ₹{{veg_per_plate}} per plate\n• Non-veg menu: ₹{{nv_per_plate}} per plate\n• Live counter add-on: ₹{{live_counter_addon}}\n• Service staff: included (1 staff per 25 guests)\n\nWe usually finalise menu 7 days before the event. A 30% advance books the date.\n\nWant me to send our most-requested menu PDF? Just reply yes.\n\n{{sender_name}}\n{{business_name}}",
            },
        ],
    },

    # ── Beauty / salon / wellness ─────────────────────────────────────────
    "Beauty / salon / wellness": {
        "tools": ["Appointment desk", "Loyalty + rebooking", "WhatsApp reminders", "Stylist preferences"],
        "priority_agents": ["email_triage", "outbound_caller", "morning_briefing", "invoice_reminder"],
        "schedules": {"email_triage": 15, "outbound_caller": 60, "morning_briefing": 1440},
        "templates": [
            {
                "name": "Appointment reminder (WhatsApp)",
                "subject": "Your {{service_name}} appointment tomorrow",
                "body": "Hi {{first_name}}!\n\nThis is a friendly reminder — your {{service_name}} with {{stylist_name}} is tomorrow at {{appointment_time}}.\n\nPrice: ₹{{service_price}}\nDuration: {{duration}} mins\nAddress: {{address}}\n\nIf you need to reschedule, just reply — we have a 4-hour cancellation policy.\n\nP.S. Want to add {{addon_suggestion}}? Mention it tomorrow and we'll fit it in.\n\nSee you,\n{{business_name}}",
            },
            {
                "name": "Rebook nudge",
                "subject": "Time for your next visit, {{first_name}}?",
                "body": "Hi {{first_name}},\n\nIt's been {{weeks_since}} weeks since your last {{last_service}} — usually about time for a touch-up.\n\nYour preferred stylist {{stylist_name}} has these slots open this week:\n\n• {{slot_1}}\n• {{slot_2}}\n• {{slot_3}}\n\nReply with the one that works.\n\nSmall thank-you: book in the next 3 days and get 10% off any add-on service (eyebrows, head massage, hair spa).\n\n{{business_name}}",
            },
        ],
    },

    # ── Garment / textile retail ──────────────────────────────────────────
    "Garment / textile retail": {
        "tools": ["Inventory tracking", "Wholesale buyer CRM", "WhatsApp catalog broadcast", "GST invoicing"],
        "priority_agents": ["email_triage", "invoice_reminder", "morning_briefing", "stale_deal_watcher"],
        "schedules": {"email_triage": 30, "invoice_reminder": 1440, "morning_briefing": 1440},
        "templates": [
            {
                "name": "Wholesale buyer follow-up",
                "subject": "New stock just arrived at {{business_name}}",
                "body": "Dear {{salutation}} {{last_name}},\n\nThe new {{collection_name}} has landed — sharing what we have:\n\n• {{item_1}}: ₹{{price_1}} per piece (MOQ {{moq_1}})\n• {{item_2}}: ₹{{price_2}} per piece (MOQ {{moq_2}})\n• {{item_3}}: ₹{{price_3}} per piece (MOQ {{moq_3}})\n\nVolume pricing available beyond 500 pieces.\n\nCatalog PDF + sample sizes attached. Reply with your order and we'll send the proforma invoice + dispatch ETA.\n\nLast time you ordered the {{prev_order_item}} — those are also restocked.\n\nRegards,\n{{sender_name}}\n{{business_name}}",
            },
            {
                "name": "Outstanding payment reminder",
                "subject": "Invoice {{invoice_number}} — payment pending",
                "body": "Dear {{salutation}} {{last_name}},\n\nReminder regarding invoice {{invoice_number}} dated {{invoice_date}}:\n\n• Amount: ₹{{amount}}\n• Due date: {{due_date}}\n• Days overdue: {{days_overdue}}\n\nPayment options:\n• NEFT: {{bank_details}}\n• UPI: {{upi_id}}\n• Cheque favouring \"{{business_name}}\"\n\nKindly arrange at the earliest. Once paid, please share UTR for our records.\n\nFor next dispatch on {{pending_order_id}}, payment of the current invoice needs to clear first.\n\nRegards,\n{{sender_name}}",
            },
        ],
    },

    # ── Logistics / transport ─────────────────────────────────────────────
    "Logistics / transport": {
        "tools": ["Booking + dispatch", "LR tracking", "Driver coordination", "Invoice reminders"],
        "priority_agents": ["email_triage", "morning_briefing", "invoice_reminder", "outbound_caller"],
        "schedules": {"email_triage": 15, "invoice_reminder": 1440, "morning_briefing": 1440},
        "templates": [
            {
                "name": "Booking acknowledgement",
                "subject": "Booking {{booking_id}} confirmed — {{origin}} to {{destination}}",
                "body": "Dear {{salutation}} {{last_name}},\n\nBooking confirmed.\n\n📍 Pickup: {{origin}} ({{pickup_date}})\n📍 Drop: {{destination}}\n📦 Consignment: {{consignment_details}}\n🚚 Vehicle: {{vehicle_type}}\n💰 Freight: ₹{{freight_amount}} ({{payment_terms}})\n📑 LR No: {{lr_number}}\n\nDriver details will be shared 2 hours before pickup. Track LR live at: {{tracking_link}}\n\nFor any change in pickup time, call ops on {{ops_phone}}.\n\nRegards,\n{{business_name}}",
            },
            {
                "name": "Delivery confirmation + POD",
                "subject": "Delivered: {{booking_id}} at {{destination}}",
                "body": "Dear {{salutation}} {{last_name}},\n\nThe consignment under {{booking_id}} has been delivered.\n\n• Delivered on: {{delivery_date}} at {{delivery_time}}\n• Received by: {{receiver_name}}\n• Condition: {{condition_remarks}}\n• POD attached\n\nIf there are any short-delivery / damage claims, kindly raise them within 48 hours via {{claims_email}}.\n\nFreight invoice attached — kindly process within {{payment_days}} days as per terms.\n\nRegards,\n{{business_name}}",
            },
        ],
    },

    # ── Construction / contracting ────────────────────────────────────────
    "Construction / contracting": {
        "tools": ["Site inquiries", "Quote builder", "Project milestones", "Subcontractor tracking"],
        "priority_agents": ["meeting_prep", "email_triage", "morning_briefing", "stale_deal_watcher"],
        "schedules": {"email_triage": 30, "meeting_prep": 10, "morning_briefing": 1440},
        "templates": [
            {
                "name": "Site visit + quote follow-up",
                "subject": "Site visit recap + estimate — {{project_name}}",
                "body": "Dear {{salutation}} {{last_name}},\n\nThanks for the site visit on {{visit_date}}. Quick recap of what we discussed at {{site_address}}:\n\n• Scope: {{scope_summary}}\n• Total area: {{area_sqft}} sq ft\n• Preferred timeline: {{client_timeline}}\n• Special requirements: {{special_reqs}}\n\nRough estimate (detailed quote separately attached):\n• Civil + finishing: ₹{{civil_cost}}\n• MEP (electrical / plumbing): ₹{{mep_cost}}\n• Total ballpark: ₹{{total_ballpark}}\n\nWe normally start within {{start_window}} days of advance. Want to do a second walk-through with our engineer next week?\n\nRegards,\n{{sender_name}}\n{{business_name}}",
            },
            {
                "name": "Milestone payment request",
                "subject": "{{project_name}} — {{milestone_label}} milestone reached",
                "body": "Dear {{salutation}} {{last_name}},\n\nUpdate on {{project_name}}:\n\n• Milestone reached: {{milestone_label}}\n• Date completed: {{completion_date}}\n• Photos / proof: {{photos_link}}\n• As per contract, this triggers: {{milestone_payment}} ({{percent_of_contract}}% of total)\n• Amount due: ₹{{amount}}\n• Due by: {{due_date}}\n\nUTR / cheque favouring \"{{business_name}}\".\n\nNext milestone target: {{next_milestone}} by {{next_milestone_date}} — provided this payment clears as scheduled to keep procurement on track.\n\nRegards,\n{{sender_name}}",
            },
        ],
    },

    # ── Auto repair / garage ──────────────────────────────────────────────
    "Auto repair / garage": {
        "tools": ["Service desk", "Parts orders", "Pickup + drop coordination", "Service reminders"],
        "priority_agents": ["email_triage", "outbound_caller", "invoice_reminder", "morning_briefing"],
        "schedules": {"email_triage": 15, "outbound_caller": 60, "invoice_reminder": 1440},
        "templates": [
            {
                "name": "Service estimate + approval ask",
                "subject": "Estimate for your {{vehicle_make}} {{vehicle_model}}",
                "body": "Hi {{first_name}},\n\nWe've inspected your {{vehicle_make}} {{vehicle_model}} ({{registration}}). Here's what we found:\n\n• Critical: {{critical_issues}}\n• Recommended: {{recommended_issues}}\n• Optional: {{optional_issues}}\n\nEstimate breakdown:\n• Labour: ₹{{labour}}\n• Parts: ₹{{parts}}\n• Taxes: ₹{{taxes}}\n• Total: ₹{{total}}\n\nETA if approved today: {{eta_hours}} hours.\n\nReply \"go ahead\" to confirm, or call {{mechanic_phone}} if you want to discuss any item. Optional ones can be skipped without affecting safety.\n\n{{sender_name}}",
            },
            {
                "name": "Service due reminder",
                "subject": "Your {{vehicle_model}} is due for service",
                "body": "Hi {{first_name}},\n\nYour {{vehicle_make}} {{vehicle_model}} ({{registration}}) is due for service:\n\n• Last service: {{last_service_date}}\n• Last odometer: {{last_odometer}} km\n• Recommended service: {{service_type}}\n• Estimated cost: ₹{{estimate}}\n• Time needed: {{duration}}\n\nWant us to pick up and drop the vehicle? We do free pickup within {{free_pickup_radius}} km.\n\nReply with a preferred date or just call {{garage_phone}}.\n\n{{business_name}}",
            },
        ],
    },

    # ── Photography / event services ──────────────────────────────────────
    "Photography / event services": {
        "tools": ["Inquiry intake", "Package builder", "Booking calendar", "Delivery + gallery"],
        "priority_agents": ["email_triage", "meeting_prep", "morning_briefing", "stale_deal_watcher"],
        "schedules": {"email_triage": 30, "meeting_prep": 10, "morning_briefing": 1440},
        "templates": [
            {
                "name": "Wedding inquiry response",
                "subject": "Your {{event_date}} wedding — package + availability",
                "body": "Hi {{first_name}},\n\nCongratulations on the upcoming wedding! Here's what we put together based on your inquiry:\n\n**Available on {{event_date}}**: Yes ✓\n\n**Package recommended**\n• Pre-wedding shoot (4 hrs): ₹{{pre_wedding}}\n• Wedding day full coverage: ₹{{wedding_day}}\n• Reception coverage: ₹{{reception}}\n• Cinematic film (3-5 min): ₹{{cinematic}}\n• Photo album (40 sheets): ₹{{album}}\n• **Bundle price**: ₹{{bundle_price}} (save ₹{{savings}})\n\n**Includes**\n• Lead photographer + assistant\n• Drone shots (weather permitting)\n• Online gallery within 30 days\n• 200+ edited photos + 1000 raw\n\nPortfolio: {{portfolio_link}}\nWant to do a 30-min video call to discuss vision? {{slot_options}}\n\n{{sender_name}}",
            },
            {
                "name": "Photo gallery delivery",
                "subject": "Your photos are ready! 📸",
                "body": "Hi {{first_name}}!\n\nYour {{event_name}} photos are edited and ready:\n\n📁 Full gallery: {{gallery_link}}\n🔐 Password: {{gallery_password}}\n📅 Available until: {{expiry_date}}\n📥 Download as ZIP: button on the gallery page\n\nQuick numbers:\n• Total photos delivered: {{photo_count}}\n• Highlights album: {{highlights_count}}\n• Drone shots: {{drone_count}}\n\nIf you want any photo individually edited or printed, just reply with the photo number.\n\nWe loved being part of your day — would mean the world if you could review us on Google: {{review_link}}\n\n{{sender_name}}\n{{business_name}}",
            },
        ],
    },

    # ── Travel / tour operator ────────────────────────────────────────────
    "Travel / tour operator": {
        "tools": ["Itinerary builder", "Booking + payment tracking", "Traveler WhatsApp", "Reviews + repeat travel"],
        "priority_agents": ["email_triage", "meeting_prep", "outbound_caller", "morning_briefing"],
        "schedules": {"email_triage": 15, "meeting_prep": 10, "morning_briefing": 1440},
        "templates": [
            {
                "name": "Itinerary proposal",
                "subject": "Your {{destination}} trip — itinerary v1",
                "body": "Hi {{first_name}},\n\nHere is the first draft of your {{destination}} trip for {{traveller_count}} travellers from {{start_date}} to {{end_date}}:\n\n**Day-by-day** (attached as PDF)\nQuick highlights:\n• Day {{day_1}}: {{day_1_highlight}}\n• Day {{day_2}}: {{day_2_highlight}}\n• Day {{day_3}}: {{day_3_highlight}}\n\n**Stays**: {{accommodation_tier}}\n**Transport**: {{transport_summary}}\n**Inclusions**: {{inclusions}}\n**Not included**: {{exclusions}}\n\n**Total package**: ₹{{package_price}} per person (₹{{total_for_group}} for the group)\n\nWe usually iterate v1 → v2 with your inputs. What would you like to change — pace, accommodation tier, any specific add-ons (paragliding, candlelight dinner, etc.)?\n\n30-minute call this week? {{slot_options}}\n\n{{sender_name}}",
            },
            {
                "name": "Pre-departure checklist",
                "subject": "All set for {{destination}} — quick pre-departure checklist",
                "body": "Hi {{first_name}}!\n\nYour {{destination}} trip starts in 3 days — exciting! Quick checklist before you fly:\n\n**Documents to carry**\n• Photo IDs (original) for all travellers\n• Confirmed itinerary printout (attached)\n• Travel insurance copy (if booked)\n• Booking vouchers (also in PDF)\n\n**Cash + cards**\n• Recommend ₹{{cash_recommendation}} cash for tips, local snacks\n• Inform your bank about travel — so cards aren't blocked\n• {{forex_recommendation}}\n\n**Local contact**\n• Our on-ground partner: {{ground_contact_name}}, {{ground_contact_phone}}\n• 24/7 emergency: {{emergency_phone}}\n\n**Weather + packing**\n{{weather_summary}}\n\nAnything missing? Reply or WhatsApp me on {{sender_phone}}.\n\nHave a fantastic trip,\n{{sender_name}}\n{{business_name}}",
            },
        ],
    },

    # ── Real estate broker ────────────────────────────────────────────────
    # Distinct from "Real estate" (which is developer-facing). Brokers
    # juggle rentals + resales + buyers + sellers.
    "Real estate broker": {
        "tools": ["Rental + resale inquiries", "Owner + tenant CRM", "Site visit scheduler", "Commission tracking"],
        "priority_agents": ["outbound_caller", "stale_deal_watcher", "email_triage", "morning_briefing"],
        "schedules": {"email_triage": 15, "stale_deal_watcher": 1440, "morning_briefing": 1440},
        "templates": [
            {
                "name": "Rental shortlist",
                "subject": "Found {{count}} options in {{location}} for your budget",
                "body": "Hi {{first_name}},\n\nBased on your budget of ₹{{budget}} for a {{bhk}} in {{location}}, here are my top picks:\n\n1. **{{property_1}}** — {{rent_1}}/month, {{detail_1}}\n2. **{{property_2}}** — {{rent_2}}/month, {{detail_2}}\n3. **{{property_3}}** — {{rent_3}}/month, {{detail_3}}\n\nAll photos + floor plans: {{drive_link}}\n\nWhich 2-3 do you want to visit this {{visit_window}}? I can club them in one trip — about 90 mins total.\n\nMost owners want token of ₹{{token_amount}} on the day if you decide; standard brokerage is one month's rent + GST.\n\n{{sender_name}}",
            },
            {
                "name": "Owner — tenant verification update",
                "subject": "Verification done for {{tenant_name}} — {{property_address}}",
                "body": "Dear {{salutation}} {{last_name}},\n\nUpdate on the prospective tenant for {{property_address}}:\n\n**{{tenant_name}}** — {{tenant_profile}}\n\n• Employment: {{employment}} ({{years_employed}})\n• Family: {{family_status}}\n• Police verification: {{police_verification_status}}\n• Reference 1: {{ref_1_status}}\n• Reference 2: {{ref_2_status}}\n• Last rental: {{last_rental_status}}\n\nThey are ready to move in by {{move_in_date}}. Deposit: ₹{{deposit_amount}}, rent: ₹{{rent_amount}}/month, 11-month lease.\n\nIf this works, I will draft the rental agreement on Monday. Reply with your okay.\n\nRegards,\n{{sender_name}}",
            },
        ],
    },
}


# ── Greetings: WhatsApp auto-reply + Vox voice opener per industry ───────
# Why a separate dict: keeps PRESETS readable and lets us tune greeting
# tone without bloating each industry's tools/agents/templates section.
# Used by:
#   - WhatsApp bridge to send a default auto-reply when an unknown number
#     messages a workspace for the first time
#   - Vox voice agent (NexusCaller) to construct the first spoken line of
#     an outbound call so it doesn't sound robotic-generic
# Vars supported (interpolated by the consumer):
#   {{business_name}}, {{contact_first_name}}, {{agent_name}}
GREETINGS: Dict[str, Dict[str, str]] = {
    "Healthcare": {
        "whatsapp": "Namaste, you've reached {{business_name}}. We've noted your message and a team member will respond shortly. For urgent care please call us on the clinic number listed above.",
        "voice_opener": "Hello, this is {{agent_name}} calling on behalf of {{business_name}}. Is this {{contact_first_name}}? I'm following up on your recent visit — do you have a quick moment?",
    },
    "Real estate": {
        "whatsapp": "Hi! Thanks for reaching out to {{business_name}}. Send us your preferred location, budget, and BHK — we'll share matching options in a few hours. Reply with details, please.",
        "voice_opener": "Hi {{contact_first_name}}, this is {{agent_name}} from {{business_name}}. I'm calling about the property options you were exploring. Is now a good time for a quick 2-minute chat?",
    },
    "Education": {
        "whatsapp": "Hello! Thanks for getting in touch with {{business_name}}. Please share the student's name, current class/grade, and what programme you're considering. Our counsellor will respond within working hours.",
        "voice_opener": "Hello, this is {{agent_name}} from {{business_name}}. Is this {{contact_first_name}}? I'm calling regarding your admission inquiry — do you have a couple of minutes?",
    },
    "Legal": {
        "whatsapp": "Greetings. You've reached {{business_name}}. Please note: messages are reviewed during office hours only. Briefly describe your matter and share contact details. We will respond on a privileged channel.",
        "voice_opener": "Good {{time_of_day}}, this is {{agent_name}} from {{business_name}}. Am I speaking with {{contact_first_name}}? I am calling regarding your matter. Is this a convenient time to talk?",
    },
    "Ecommerce": {
        "whatsapp": "Hi! 🛒 Thanks for shopping with {{business_name}}. For order updates, please share your order ID. For returns or product questions, just describe what you need — we'll reply within an hour during 10 AM – 8 PM.",
        "voice_opener": "Hi {{contact_first_name}}! This is {{agent_name}} from {{business_name}} — calling about your recent order. Is now a good time?",
    },
    "Finance": {
        "whatsapp": "Hello, this is {{business_name}}. For document requests, statements, or compliance queries, please write to us with the relevant client ID. Our team will revert within one business day.",
        "voice_opener": "Hello, this is {{agent_name}} calling from {{business_name}}. Am I speaking with {{contact_first_name}}? It's regarding your {{service_name}} — is now okay to discuss?",
    },
    "SaaS": {
        "whatsapp": "Hey! Thanks for reaching out to {{business_name}}. For demos, drop a 2-line description of what you're trying to solve. For support, share your workspace name. We respond inside 2 working hours.",
        "voice_opener": "Hi {{contact_first_name}}, this is {{agent_name}} from {{business_name}}. I'm following up on your interest in our product. Got 3 minutes to chat?",
    },
    "Manufacturing": {
        "whatsapp": "Greetings from {{business_name}}. For order inquiries, please share product/SKU, quantity, and required delivery date. For dispatch tracking, send your PO number. Our team will respond during 10 AM – 6 PM IST.",
        "voice_opener": "Hello, this is {{agent_name}} from {{business_name}}. Is this {{contact_first_name}}? I'm calling regarding your purchase order — is now a good time to confirm the dispatch details?",
    },
    "Hospitality": {
        "whatsapp": "Hello and welcome! 🙏 Thanks for reaching out to {{business_name}}. For reservations, please share date, time, and number of guests. For events, share event date and expected pax. We'll respond shortly.",
        "voice_opener": "Hello {{contact_first_name}}! This is {{agent_name}} from {{business_name}}. I'm reaching out to confirm your booking — got a quick minute?",
    },
    "Local services": {
        "whatsapp": "Hi! Thanks for messaging {{business_name}}. Quickly: what service do you need, and your locality? We'll share a quote + available slot within 30 minutes.",
        "voice_opener": "Hi {{contact_first_name}}, this is {{agent_name}} from {{business_name}}. Calling about the service you asked about — got a quick minute?",
    },
    "Consulting": {
        "whatsapp": "Hello, you've reached {{business_name}}. For new inquiries, please describe the engagement type and timeline. For existing clients, mention your project name. We respond within one working day.",
        "voice_opener": "Hi {{contact_first_name}}, this is {{agent_name}} from {{business_name}}. I'm following up on your inquiry about our {{service_name}} engagement. Is this a convenient time?",
    },
    "Tutoring / coaching": {
        "whatsapp": "Namaste! Thanks for reaching out to {{business_name}}. Please share the student's name, current class/grade, and the subject or programme you're interested in. We'll get back to you with details.",
        "voice_opener": "Hello, this is {{agent_name}} from {{business_name}}. Am I speaking with {{contact_first_name}}? I'm calling about the inquiry for your child — got 2 minutes?",
    },
    "Restaurant / cafe": {
        "whatsapp": "Hello! 🍽 Welcome to {{business_name}}. For table bookings: share date, time, and number of guests. For catering or events: share the event date. We're online 11 AM – 11 PM.",
        "voice_opener": "Hi {{contact_first_name}}! This is {{agent_name}} from {{business_name}}. Calling to confirm your reservation — quick check, do you have a minute?",
    },
    "Beauty / salon / wellness": {
        "whatsapp": "Hi! 💅 Thanks for reaching out to {{business_name}}. Tell us what service you need (e.g. haircut, facial, hair colour) and your preferred date/time. We'll confirm the slot in 15 minutes.",
        "voice_opener": "Hi {{contact_first_name}}! This is {{agent_name}} from {{business_name}}. I'm calling to confirm your appointment — got 30 seconds?",
    },
    "Garment / textile retail": {
        "whatsapp": "Hi! Thanks for messaging {{business_name}}. For retail inquiries: tell us what you're looking for (saree, kurta, suit). For wholesale: share your shop name + GSTIN. Our team responds within an hour.",
        "voice_opener": "Hello {{contact_first_name}}, this is {{agent_name}} from {{business_name}}. I'm calling about the order/inquiry you placed. Is now a good time for a 2-minute call?",
    },
    "Logistics / transport": {
        "whatsapp": "Greetings from {{business_name}}. For new bookings: share origin, destination, consignment details, and pickup date. For tracking: send your LR/booking number. We respond 10 AM – 7 PM.",
        "voice_opener": "Hello, this is {{agent_name}} from {{business_name}}. Am I speaking with {{contact_first_name}}? I'm calling regarding your consignment booking — got a quick moment?",
    },
    "Construction / contracting": {
        "whatsapp": "Hi! Thanks for reaching out to {{business_name}}. For site visits, share location and project scope (renovation / new build / interiors). We schedule a site visit within 2-3 days.",
        "voice_opener": "Hello {{contact_first_name}}, this is {{agent_name}} from {{business_name}}. Calling about the project inquiry you sent — got 5 minutes to discuss requirements?",
    },
    "Auto repair / garage": {
        "whatsapp": "Hi! Welcome to {{business_name}}. Please tell us your vehicle make/model, registration number, and what issue you're facing. We'll share an estimate + available slot.",
        "voice_opener": "Hi {{contact_first_name}}, this is {{agent_name}} from {{business_name}}. Your {{vehicle_model}} is ready for pickup — calling to confirm a convenient time. Got a minute?",
    },
    "Photography / event services": {
        "whatsapp": "Hi! 📸 Thanks for reaching out to {{business_name}}. Share event type (wedding/birthday/corporate), date, and city — we'll send package details and check our availability.",
        "voice_opener": "Hi {{contact_first_name}}! This is {{agent_name}} from {{business_name}}. Calling about your event inquiry — got 5 minutes to discuss vision and package?",
    },
    "Travel / tour operator": {
        "whatsapp": "Hello! ✈️ Thanks for reaching out to {{business_name}}. Tell us your travel dates, destination, traveller count, and preferred budget — we'll send a custom itinerary in 24 hours.",
        "voice_opener": "Hi {{contact_first_name}}! This is {{agent_name}} from {{business_name}}. Calling about the {{destination}} trip you were planning — do you have a quick moment?",
    },
    "Real estate broker": {
        "whatsapp": "Hi! Thanks for reaching out to {{business_name}}. Please share: rental or purchase, preferred area, budget range, and BHK. We'll share 2-3 matching options within the day.",
        "voice_opener": "Hi {{contact_first_name}}, this is {{agent_name}} from {{business_name}}. I have a couple of properties that match your search — got 2 minutes to discuss?",
    },
}


DEFAULT_GREETINGS = {
    "whatsapp":     "Hi, you've reached {{business_name}}. We've received your message and will respond shortly.",
    "voice_opener": "Hello, this is {{agent_name}} from {{business_name}}. Is this {{contact_first_name}}? Got a quick moment?",
}


def get_greetings(industry: str) -> Dict[str, str]:
    """Resolve greetings for a given industry. Falls back to DEFAULT_GREETINGS
    for unknown industries (e.g. 'Other' or businesses created via API
    that never went through the wizard)."""
    matched = normalize_industry(industry)
    return dict(GREETINGS.get(matched) or DEFAULT_GREETINGS)


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

    # Store industry greetings under settings.greetings so WhatsApp bridge
    # + Vox voice agent can read them at message/call time. Stored on the
    # business so they're tunable per workspace later — the seeded value
    # is just a sensible default.
    greetings = get_greetings(preset["industry"])

    settings = business["settings"]
    settings["industry_setup"] = {
        "industry": preset["industry"],
        "recommended_tools": preset["tools"],
        "priority_agents": preset["priority_agents"],
        "schedules": schedules,
        "seed": seed_result,
        "applied_at": now_iso(),
    }
    # Only seed greetings if the workspace doesn't already have customised
    # ones (so re-applying after a manual edit doesn't blow away the user's
    # tone tuning). settings.greetings is the source of truth.
    if not (settings.get("greetings") or {}).get("_customised"):
        settings["greetings"] = {
            "whatsapp":     greetings["whatsapp"],
            "voice_opener": greetings["voice_opener"],
            "_source":      "industry_preset",
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
