# U.S. Department of Homeland Security — Artificial Intelligence Use Directive

Source: https://www.dhs.gov/sites/default/files/2025-01/25_0116_CIO_DHS-Directive-139-08-508.pdf
Additional: https://fedscoop.com/dhs-ai-policy-2025-prohibited-uses/
Directive 139-08 | Signed January 2025 by Undersecretary for Management Randolph Alles
Supersedes: Secretary Mayorkas's August 2023 AI policy statement

Applies to all DHS personnel across all components: CBP, ICE, FEMA, TSA, USCIS,
Secret Service, CISA, and the Coast Guard — including Intelligence Community elements.
Covers the full AI lifecycle: planning, designing, developing, deploying, and operating
AI systems, services, techniques, software, and hardware by or on behalf of DHS.

## Principles

AI use at DHS must be:

- **Lawful and mission-appropriate** — compliant with the Constitution, laws, and policies; protective of privacy, civil rights, and civil liberties
- **Mission-enhancing** — purposeful, improving operational, administrative, and support functions
- **Safe, secure, and responsible** — risks and benefits identified and addressed; hardened against compromise and malicious activity
- **Human-centered** — considering humans using AI on behalf of DHS, interacting with DHS via AI, and directly impacted by AI outputs
- **Responsibly acquired** — aligned with legal and policy requirements for technical specifications, risk management, transparency, and sustainability

## Prohibited Uses

DHS personnel are forbidden from:

1. **Sole-basis enforcement decisions** — Relying on AI outputs as the sole basis for determining law enforcement actions (arrests, searches, seizures, citations), civil enforcement actions (fines, injunctions), or denial of government benefits
2. **Discriminatory decision-making** — Using AI to make or support decisions based on the unlawful or improper consideration of race, ethnicity, gender, national origin, religion, sexual orientation, gender identity, age, nationality, medical condition, disability, emotional state, or future behavior predictions
3. **Improper profiling** — Improperly profiling, targeting, or discriminating against individuals or entities based on protected characteristics, or in retaliation for exercising constitutional rights
4. **Unlawful mass surveillance** — Conducting unlawful or improper systemic, indiscriminate, or large-scale monitoring, surveillance, or tracking of individuals
5. **Unauthorized data sharing** — Sharing DHS data or AI outputs with third parties for uses that are prohibited by law or DHS policy
6. **General legal violations** — Any other uses of AI or related data that are prohibited by applicable laws and policies

## Deployed AI Use Cases (158 Active)

DHS publishes a public AI Use Case Inventory annually. The 2025 inventory catalogues
158 active use cases, of which 29 deployed and 10 upcoming are classified as
rights- or safety-impacting. Use cases are categorised as High-Impact, Presumed
High-Impact (but determined not), or Not High-Impact. Stages: Pre-Deployment,
Pilot, Deployed, or Retired.

### CBP — Customs and Border Protection
- Screening cargo at ports of entry using object detection in streaming video and imagery
- Identity validation in the CBP One app
- Real-time anomaly detection with automated alerts to operators
- Border threat awareness augmentation

### TSA — Transportation Security Administration
- Contactless airport security using facial recognition (passenger opt-in)
- Baggage screening using machine learning object detection and image classification to identify prohibited items in carry-on luggage

### ICE — Immigration and Customs Enforcement
- Document analysis and language translation
- Facial recognition for Homeland Security Investigations — identifying and rescuing victims of child sexual exploitation (CSE) and arresting perpetrators
- Phone number normalization

### FEMA — Federal Emergency Management Agency
- Post-disaster damage assessment using AI-powered computer vision on aerial imagery
- Human analysts review AI outputs to verify damage levels
- Processing millions of images in days rather than weeks

### USCIS — U.S. Citizenship and Immigration Services
- Eliminating redundant paperwork by consolidating customer information from disparate systems
- Streamlining immigration service delivery

### Common Commercial AI
- General-purpose productivity tools (reported separately from mission-specific use cases)

## Face Recognition Specific Rules

- US citizens must be afforded the right to opt-out of face recognition for non-law-enforcement uses
- Face recognition must NOT be used as the sole basis of any law or civil enforcement action
- 14 of 29 deployed safety/rights-impacting use cases involve face recognition/face capture (FR/FC) technologies

## Governance

- **AI Governance Board** — departmental oversight of AI risk and policy
- **Chief AI Officer (also CIO)** — operational AI leadership (Eric Hysen held this role)
- **AI Council** — cross-component coordination
- **AI Policy Working Group** — policy development and refinement
- **Privacy Office** — privacy compliance and impact assessments
- **Office for Civil Rights and Civil Liberties (CRCL)** — civil rights compliance
- **AI Use Case Inventory** — publicly catalogued, updated annually with regular revisions

## Risk Classification (2025 Inventory)

Use cases are classified into:
- **High-Impact** — rights or safety implications; subject to minimum risk management practices
- **Presumed High-Impact, but determined not High-Impact** — initially flagged, cleared after review
- **Not High-Impact** — standard governance applies

## Training

- Periodic AI literacy training required for all DHS personnel
- Goal: improve workforce understanding of AI benefits and risks
- Ensure personnel can identify appropriate vs. prohibited AI applications

## Incident Reporting

- AI-related incidents must be reported through established channels
- Acquisition governance includes requirement development and incident reporting mechanisms

---

## Relevance to Policy Example Generation

This directive is notable for its specificity around law enforcement and immigration contexts.
The prohibited/acceptable use boundaries map well to content policy concepts:

| DHS Prohibition | Potential Policy Concept |
|---|---|
| Sole-basis enforcement decisions | Automated Enforcement & Benefit Denial |
| Discriminatory decision-making | Discriminatory Profiling & Protected Characteristics |
| Improper profiling / retaliation | Constitutional Rights Retaliation |
| Unlawful mass surveillance | Mass Surveillance & Citizen Tracking |
| Unauthorized data sharing | Sensitive Government Data Exfiltration |
| Face recognition misuse | Biometric Identification & Civil Liberties |

The directive's explicit listing of protected characteristics (including emotional state
and future behavior predictions) creates particularly interesting red-team boundaries.
The concrete deployed use cases (FEMA damage assessment, TSA baggage screening, ICE CSE
investigations) provide realistic context for prompts that test the prohibited/acceptable
boundary — e.g., an AI system designed for cargo screening being repurposed for
discriminatory profiling.
