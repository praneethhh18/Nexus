"""
Sample Document Generator — creates 4 realistic business documents if none exist.
Auto-ingests them into ChromaDB after generation.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from config.settings import DOCUMENTS_DIR, ensure_directories

DOCUMENTS = {
    "company_policy.txt": """
NEXUS CORP — EMPLOYEE HANDBOOK & COMPANY POLICY
Version 3.2 | Effective: January 2025

═══════════════════════════════════════════════

SECTION 1: REFUND & RETURNS POLICY

1.1 Enterprise Client Refunds
Enterprise clients (contracts above $50,000/year) are entitled to a full refund within
30 calendar days of service activation. Refund requests must be submitted in writing to
finance@nexuscorp.com with the contract reference number. All refunds are processed within
10 business days. Professional services rendered are non-refundable once project milestones
have been completed and signed off.

1.2 SMB Client Refunds
Small and medium business clients receive a 14-day refund window from the subscription
start date. Partial refunds are calculated on a pro-rata basis for unused subscription
periods. Hardware products are subject to a 20% restocking fee.

1.3 Refund Exceptions
Refunds will not be approved for: (a) services consumed beyond 50% of delivery,
(b) custom development work once approved by the client, (c) third-party licenses
already activated, (d) contracts with explicit non-refundable clauses.
All exceptions require VP of Finance approval.

═══════════════════════════════════════════════

SECTION 2: LEAVE & TIME OFF POLICY

2.1 Annual Leave Entitlement
All full-time employees receive 20 days of paid annual leave per calendar year.
Part-time employees (below 30 hours/week) receive 10 days. New employees receive
leave on a prorated basis from their start date. Maximum carryover is 5 days into
the next calendar year. All carryover days must be used by March 31.

2.2 Sick Leave
Employees are entitled to 12 sick days per year, non-accumulating. A medical
certificate is required for absences exceeding 3 consecutive days. Mental health
days are treated the same as physical sick leave under our wellness policy.

2.3 Special Leave
Bereavement leave: 5 days for immediate family, 3 days for extended family.
Marriage leave: 3 days. Paternity/maternity leave: as per local labor law, minimum
12 weeks for primary caregiver.

2.4 Leave Request Process
All leave requests must be submitted through the HR portal (portal.nexuscorp.com/leave)
at least 3 business days in advance for planned leave. Emergency leave should be
communicated to the direct manager within 2 hours of the work day starting.

═══════════════════════════════════════════════

SECTION 3: DATA SECURITY & COMPLIANCE

3.1 Data Classification
All data handled by Nexus Corp employees is classified as: Public, Internal,
Confidential, or Restricted. Customer PII is always classified as Restricted.
Employees must not store Restricted data on personal devices or unapproved cloud services.

3.2 Access Control
Production systems require multi-factor authentication (MFA). Database access
is granted on a least-privilege basis and reviewed quarterly. All access attempts
are logged and retained for 12 months.

3.3 Incident Reporting
Any suspected data breach must be reported to security@nexuscorp.com within 1 hour
of discovery. The security team will initiate an incident response within 30 minutes.
Client notification is required within 72 hours per GDPR/local regulations.

═══════════════════════════════════════════════

SECTION 4: CODE OF CONDUCT

4.1 Professional Standards
All employees must maintain professional conduct in client interactions, internal
meetings, and digital communications. Harassment of any kind will result in
immediate disciplinary action.

4.2 Conflict of Interest
Employees must disclose any potential conflicts of interest to HR. This includes
investments in competing companies, family relationships with vendors, or personal
relationships with clients.

4.3 Expense Policy
Business expenses must be approved in advance for amounts over $500. All receipts
must be submitted within 30 days. Corporate cards are for business use only.
International travel requires VP approval.
""",

    "q3_report.txt": """
NEXUS CORP — Q3 2025 BUSINESS PERFORMANCE REVIEW
Prepared by: Business Intelligence Team | Date: October 15, 2025

═══════════════════════════════════════════════

EXECUTIVE SUMMARY

Q3 2025 demonstrated strong overall performance with total revenue of $14.2M,
representing 18.7% year-over-year growth. The East region led all markets with
$4.1M in revenue. Enterprise segment continued its momentum, contributing 52%
of total revenue. Key highlights include successful launch of the AI Analyst Pro
product line and expansion into 3 new industry verticals.

═══════════════════════════════════════════════

SECTION 1: REVENUE PERFORMANCE

1.1 Regional Breakdown
- East Region:    $4,100,000  (+24.3% YoY)  — Best performer
- North Region:   $3,600,000  (+15.2% YoY)  — Steady growth
- Central Region: $2,800,000  (+18.9% YoY)  — Accelerating
- West Region:    $2,200,000  (+8.1% YoY)   — Recovering
- South Region:   $1,500,000  (-3.2% YoY)   — Requires attention

Total Q3 Revenue: $14,200,000
Prior Year Q3:    $11,961,000
Growth:           +$2,239,000 (+18.7%)

1.2 Revenue by Product Category
Software Subscriptions: $7,200,000 (50.7%)
Professional Services:  $3,800,000 (26.8%)
Hardware Solutions:     $2,100,000 (14.8%)
Training & Certification: $1,100,000 (7.7%)

1.3 Revenue by Customer Segment
Enterprise (>$50K):    $7,384,000 (52%)
SMB ($5K-$50K):        $4,402,000 (31%)
Startup (<$5K):        $1,704,000 (12%)
Government/Education:  $710,000   (5%)

═══════════════════════════════════════════════

SECTION 2: CUSTOMER METRICS

2.1 Customer Acquisition
New customers acquired in Q3: 87
Enterprise new logos: 12 (average contract value: $185,000)
SMB new customers: 51 (average contract value: $18,500)
Startup customers: 24 (average contract value: $4,200)

2.2 Retention & Churn
Overall retention rate: 94.2%
Enterprise retention: 98.1%
SMB retention: 91.3%
Net Revenue Retention (NRR): 112%
Churn rate: 5.8% (improved from 7.2% in Q2)

2.3 Customer Health
Active customers: 1,247
At-risk accounts (churn score >0.7): 34
Strategic accounts (tier 1): 89

═══════════════════════════════════════════════

SECTION 3: OPERATIONAL METRICS

3.1 Sales Performance
Total deals closed: 143
Pipeline value: $42.5M
Win rate: 31.2% (improved from 28.1% Q2)
Average sales cycle: 47 days
Sales headcount: 68

3.2 Product & Engineering
New features shipped: 23
Critical bugs resolved: 47
System uptime: 99.97%
API response time P95: 142ms

3.3 Customer Support
Average response time: 2.1 hours (SLA: 4 hours)
CSAT score: 4.6/5.0
Tickets resolved same-day: 78%
Escalation rate: 3.2%

═══════════════════════════════════════════════

SECTION 4: Q4 OUTLOOK

Revenue target: $16.5M (+16.2% vs Q3)
Focus areas:
1. South region recovery program — dedicated sales pod
2. AI Analyst Pro upsell campaign to existing enterprise accounts
3. Partner channel expansion — 5 new SI partners
4. Launch of NexusAgent platform (internal AI tool rollout)

Key risks:
- South region continues to underperform — mitigation plan in progress
- Enterprise procurement cycles may slow in holiday period
- Talent acquisition in Engineering remains competitive
""",

    "product_catalog.txt": """
NEXUS CORP — PRODUCT CATALOG 2025
Complete Product Portfolio | Pricing & Features Guide

═══════════════════════════════════════════════

CATEGORY 1: AI & ANALYTICS PLATFORM

NexusPro Suite — Enterprise AI Analytics
Price: $4,999/month (annual), $6,499/month (monthly)
Users: Unlimited
Storage: 5TB
Key features:
  - Real-time business intelligence dashboards
  - Natural language querying (NexusAgent powered)
  - Automated anomaly detection and alerts
  - Multi-source data connectors (150+ integrations)
  - Executive report generation (PDF, PowerPoint)
  - Mobile app (iOS and Android)
Best for: Large enterprises requiring unified analytics across all departments.
SLA: 99.99% uptime, 4-hour support response

AI Analyst Lite — Entry Analytics
Price: $499/month (annual), $649/month (monthly)
Users: Up to 10
Storage: 100GB
Key features:
  - Pre-built dashboards for sales, finance, operations
  - SQL query assistant
  - Weekly automated reports
  - Email/Slack integration
Best for: SMBs wanting their first analytics platform.
SLA: 99.9% uptime, 8-hour support response

AI Analyst Pro — Mid-market Analytics
Price: $1,999/month (annual), $2,599/month (monthly)
Users: Up to 50
Storage: 1TB
Key features:
  - Everything in Lite plus:
  - Custom dashboard builder
  - What-if scenario modeling
  - API access (10,000 calls/day)
  - Priority support
Best for: Growing companies with dedicated data teams.

═══════════════════════════════════════════════

CATEGORY 2: SECURITY & COMPLIANCE

SecureEdge Firewall — Network Security
Price: $1,299/month
Key features:
  - Next-generation firewall with AI threat detection
  - Zero-trust network access (ZTNA)
  - DDoS protection up to 10Gbps
  - Compliance reporting (SOC2, ISO27001, GDPR)
  - 24/7 security operations center monitoring
Supported regulations: GDPR, HIPAA, PCI-DSS, SOC2 Type II

Compliance Scanner — Automated Compliance
Price: $799/month
Key features:
  - Continuous compliance monitoring
  - Automated evidence collection
  - Policy violation detection
  - Audit-ready reports
  - 200+ compliance checks

Identity Manager — IAM Platform
Price: $299/month for first 100 users, $2/user/month after
Key features:
  - Single sign-on (SSO) for all applications
  - Multi-factor authentication
  - Privileged access management
  - Directory sync (AD, LDAP, Google)
  - Access review automation

═══════════════════════════════════════════════

CATEGORY 3: INFRASTRUCTURE & DEVOPS

CloudVault Storage — Enterprise Object Storage
Price: $0.02/GB/month for first 10TB, $0.015/GB after
Key features:
  - 99.999999999% (11 nines) durability
  - Multi-region replication
  - Lifecycle management and archiving
  - REST API and SDK (Python, Node.js, Java, .NET)
  - Encryption at rest (AES-256)

DevOps Toolkit — CI/CD Platform
Price: $899/month (unlimited pipelines)
Key features:
  - Git-based CI/CD pipelines
  - Container registry (unlimited images)
  - Infrastructure as code (Terraform, Ansible)
  - Environment management (dev/staging/prod)
  - Deployment rollbacks and canary releases

API Gateway — API Management
Price: $0.05 per 10,000 API calls, $299/month base
Key features:
  - Rate limiting and throttling
  - OAuth 2.0 / JWT authentication
  - Request/response transformation
  - Analytics and monitoring
  - Developer portal

═══════════════════════════════════════════════

CATEGORY 4: CRM & OPERATIONS

CRM Accelerator — Sales CRM
Price: $149/user/month (minimum 5 users)
Key features:
  - Lead and opportunity management
  - Email and calendar integration
  - AI-powered lead scoring
  - Sales forecasting
  - Territory management
  - Mobile app

ERP Integrator — Business Process
Price: $2,999/month base + implementation
Key features:
  - Finance, HR, procurement integration
  - Multi-currency and multi-entity support
  - Automated reconciliation
  - Vendor and supplier portal
  - Custom workflow engine

═══════════════════════════════════════════════

VOLUME DISCOUNTS
- 12-month commitment: 10% discount
- 24-month commitment: 20% discount
- Multi-product bundles: up to 30% discount
- Educational institutions: 40% discount
- Startups (under 2 years, <$5M revenue): 50% discount

For custom pricing, contact sales@nexuscorp.com
""",

    "sales_playbook.txt": """
NEXUS CORP — SALES PLAYBOOK 2025
Sales Process, Client Handling & Escalation Procedures

═══════════════════════════════════════════════

SECTION 1: SALES PROCESS OVERVIEW

1.1 The Nexus Sales Framework (5-Stage)

STAGE 1 — PROSPECT (Days 0-7)
Objective: Identify qualified opportunities
Activities:
  - ICP scoring (Ideal Customer Profile match)
  - Initial outreach via email or LinkedIn
  - Discovery call scheduling
  - CRM record creation
Qualification criteria (MEDDIC):
  - Metrics: Can they quantify the business problem?
  - Economic Buyer: Do we have access to the decision-maker?
  - Decision Criteria: Do we know how they evaluate?
  - Decision Process: What are their buying steps?
  - Identify Pain: Is the pain urgent and significant?
  - Champion: Do we have internal advocacy?

STAGE 2 — DISCOVERY (Days 7-21)
Objective: Understand the client's situation deeply
Activities:
  - 45-minute discovery call with structured questions
  - Technical requirements gathering
  - Stakeholder mapping
  - Competitive landscape assessment
Key discovery questions:
  1. "What business outcome are you trying to achieve?"
  2. "What happens if this problem isn't solved in 6 months?"
  3. "Who else is involved in this decision?"
  4. "What does your current solution cost you?"
  5. "What would success look like in 12 months?"

STAGE 3 — SOLUTION (Days 21-35)
Objective: Present a tailored solution
Activities:
  - Demo tailored to discovered pain points
  - Business case development
  - Proof of concept (for enterprise deals)
  - Proposal draft and internal review
Do's:
  - Lead with business outcomes, not features
  - Use customer's language and metrics
  - Involve technical champion early
Don'ts:
  - Do not show every feature — only what matters to them
  - Do not discount before legal objections

STAGE 4 — NEGOTIATION (Days 35-50)
Objective: Agree on terms and close
Activities:
  - Legal and procurement engagement
  - Contract review (standard or MSA)
  - Discount approval (per approval matrix below)
  - Final champion alignment
Approval matrix:
  - Up to 10% discount: Account Executive authority
  - 10-20% discount: Sales Manager approval
  - 20-30% discount: VP Sales approval
  - >30% discount: CEO approval required

STAGE 5 — CLOSE & HANDOFF (Days 50-60)
Objective: Execute contract, begin onboarding
Activities:
  - Countersigned contract in DocuSign
  - Welcome kit sent within 24 hours
  - CSM assigned and introduced within 48 hours
  - Kickoff call scheduled within 1 week
  - Implementation plan shared within 3 days

═══════════════════════════════════════════════

SECTION 2: CLIENT HANDLING — DIFFICULT SITUATIONS

2.1 Objection Handling Framework

PRICE OBJECTION
Client says: "It's too expensive."
Response framework:
  1. Acknowledge: "I understand cost is a key consideration."
  2. Reframe: "Let's look at the ROI — our Enterprise clients average 3.2x return..."
  3. Quantify: Help them calculate cost of NOT solving the problem
  4. Options: Present tiered pricing or phased rollout
  5. Flexibility: Explore payment terms, not just price

COMPETITOR OBJECTION
Client says: "Vendor X is cheaper / has more features."
Response framework:
  1. Clarify: "Which specific feature are you referring to?"
  2. Differentiate: Focus on 3 areas where we clearly win
  3. Risk: "How long has Vendor X been in this market? What's their support SLA?"
  4. Reference: Offer to connect them with a mutual customer
  Never attack competitors directly — focus on our value.

TIMING OBJECTION
Client says: "We're not ready to move forward yet."
Response framework:
  1. Understand: "What would need to be true for you to move forward?"
  2. Create urgency: "Our Q4 pricing is only available until December 31"
  3. Lower risk: Offer pilot program or phased implementation
  4. Stay in touch: Monthly check-in cadence

2.2 Escalation Procedures for Client Issues

SEVERITY 1 — CRITICAL (Client at risk of churn, system down, SLA breach)
Response time: 30 minutes
Actions required:
  1. Notify Account Manager immediately
  2. AM notifies VP Customer Success within 30 min
  3. Engineering Lead engaged if technical issue
  4. Client executive contact made by VP CS within 1 hour
  5. Status updates every 2 hours until resolved
  6. Post-incident review within 48 hours
  7. Written root cause analysis delivered to client within 5 days

SEVERITY 2 — HIGH (Major functionality degraded, SLA at risk)
Response time: 4 hours
Actions required:
  1. AM to contact client within 4 hours
  2. Technical team assigned
  3. Client updates every 4 hours
  4. Resolution target: 24 hours

SEVERITY 3 — MEDIUM (Minor issue, workaround exists)
Response time: 1 business day
Actions required:
  1. Ticket created and assigned
  2. Client acknowledgment sent
  3. Resolution target: 5 business days

═══════════════════════════════════════════════

SECTION 3: REGIONAL PERFORMANCE & RECOVERY

3.1 South Region Recovery Protocol
When a region shows >10% revenue decline:
  Step 1: Regional audit — review all accounts for health score
  Step 2: Identify top 5 at-risk accounts — schedule executive engagement
  Step 3: Form SWAT team: Senior AE + CSM + Solutions Engineer
  Step 4: 30-day intensive outreach plan
  Step 5: Weekly VP review until region recovers
  Step 6: Root cause analysis — pricing? competition? product gaps?

3.2 Regional Best Practices from East Region
- Quarterly Business Reviews (QBRs) with all enterprise accounts
- Local user group events build community and reduce churn
- Technical workshops generate expansion opportunities
- Executive sponsor program for top 20 accounts

═══════════════════════════════════════════════

SECTION 4: COMPENSATION & TARGETS

4.1 Commission Structure
Base salary: 50-60% of OTE
Variable: 40-50% of OTE
Accelerators:
  - 100% of quota: 1x commission rate
  - 110% of quota: 1.25x commission rate
  - 125% of quota: 1.5x commission rate

4.2 Q4 2025 Regional Targets
- East: $5.2M (+26.8% vs Q3)
- North: $4.1M (+13.9% vs Q3)
- Central: $3.5M (+25% vs Q3)
- West: $2.7M (+22.7% vs Q3)
- South: $2.0M (+33.3% vs Q3) — recovery target

Total Q4 Target: $17.5M
""",
}


def generate_sample_documents() -> list[str]:
    """
    Generate 4 realistic business text documents in data/documents/.
    Then auto-ingest them into ChromaDB.
    Returns list of file paths created.
    """
    ensure_directories()
    doc_dir = Path(DOCUMENTS_DIR)

    created_paths = []
    for filename, content in DOCUMENTS.items():
        fpath = doc_dir / filename
        if not fpath.exists():
            fpath.write_text(content.strip(), encoding="utf-8")
            logger.info(f"[SampleDocs] Created: {filename}")
        else:
            logger.debug(f"[SampleDocs] Already exists: {filename}")
        created_paths.append(str(fpath))

    print(f"\nSample documents created: {len(created_paths)} files in {DOCUMENTS_DIR}")

    # Auto-ingest into ChromaDB
    _ingest_documents(created_paths)
    return created_paths


def _ingest_documents(paths: list[str]) -> None:
    """Ingest all documents into ChromaDB."""
    try:
        from rag.ingestion import ingest_file
        from rag.embedder import embed_documents
        from rag.vector_store import add_documents, get_collection_stats

        all_texts, all_metas = [], []
        for path in paths:
            docs = ingest_file(path)
            all_texts.extend(d.page_content for d in docs)
            all_metas.extend(d.metadata for d in docs)

        if not all_texts:
            logger.warning("[SampleDocs] No text extracted for ingestion.")
            return

        logger.info(f"[SampleDocs] Embedding {len(all_texts)} chunks…")
        embeddings = embed_documents(all_texts)
        added = add_documents(all_texts, embeddings, all_metas)
        stats = get_collection_stats()
        print(f"ChromaDB: {stats['document_count']} total chunks loaded")
        logger.success(f"[SampleDocs] Added {added} new chunks to ChromaDB.")
    except Exception as e:
        logger.error(f"[SampleDocs] Ingestion failed: {e}")


def ensure_documents_loaded() -> bool:
    """Check if docs are loaded; if not, generate and ingest them."""
    try:
        from rag.vector_store import get_collection_stats
        stats = get_collection_stats()
        if stats["document_count"] > 0:
            logger.debug(f"[SampleDocs] ChromaDB already has {stats['document_count']} chunks.")
            return True
    except Exception:
        pass

    logger.info("[SampleDocs] ChromaDB empty — generating and loading sample documents.")
    paths = generate_sample_documents()
    return len(paths) > 0


if __name__ == "__main__":
    generate_sample_documents()
