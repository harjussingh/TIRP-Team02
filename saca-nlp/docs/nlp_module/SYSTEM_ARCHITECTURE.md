# SACA System Architecture

## Overall System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                          │
├─────────────────────────────────┬───────────────────────────────────┤
│                                 │                                   │
│    📱 ANDROID MOBILE APP        │    💻 DESKTOP WEB APP            │
│    (React Native/Flutter)       │    (React/Electron)              │
│                                 │                                   │
│    - Voice Input                │    - Dashboard                    │
│    - Text Input                 │    - Patient Queue                │
│    - Quick Symptom Buttons      │    - Analytics                    │
│    - Results Display            │    - Reports                      │
│    - Emergency Actions          │    - Admin Panel                  │
│    - History View               │    - Real-time Notifications      │
│    - Offline Mode               │    - Multi-user Support           │
│                                 │                                   │
└─────────────────────────────────┴───────────────────────────────────┘
                              ↕
                         REST API / WebSocket
                              ↕
┌─────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                            │
│                       (FastAPI / Flask Backend)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
│  │ Authentication │  │   API Gateway    │  │  WebSocket Server │  │
│  │   & Security   │  │   (Rate Limit)   │  │  (Real-time)      │  │
│  └────────────────┘  └──────────────────┘  └───────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────────┐
│                        BUSINESS LOGIC LAYER                          │
│                         (Python Core Modules)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    NLP PIPELINE                               │  │
│  │                                                               │  │
│  │  1. Kriol Translation  →  2. Preprocessing  →  3. Synonym   │  │
│  │     (kriol_translator)     (preprocess)         Mapping      │  │
│  │                                                 (symptom_map)│  │
│  │  4. Symptom Extraction →  5. Negation Detection             │  │
│  │     (symptom_extractor)    (negation_detector)              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  ML TRIAGE ENGINE                             │  │
│  │                                                               │  │
│  │  • Severity Prediction Model (Random Forest / XGBoost)       │  │
│  │  • Feature Engineering (symptom combinations)                │  │
│  │  • Confidence Scoring                                        │  │
│  │  • Risk Factor Analysis                                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              RECOMMENDATION ENGINE                            │  │
│  │                                                               │  │
│  │  • Action Suggestion Logic                                   │  │
│  │  • Emergency Protocol Rules                                  │  │
│  │  • Care Pathway Mapping                                      │  │
│  │  • Follow-up Scheduling                                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │  PostgreSQL  │  │  Redis Cache │  │  File Storage (S3/Local) │ │
│  │              │  │              │  │                          │ │
│  │  - Patients  │  │  - Sessions  │  │  - Audio files           │ │
│  │  - Symptoms  │  │  - Temp data │  │  - Reports (PDF)         │ │
│  │  - Triage    │  │  - API cache │  │  - ML model files        │ │
│  │  - Actions   │  │              │  │  - Logs                  │ │
│  │  - Audit Log │  │              │  │                          │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL INTEGRATIONS                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  • Google Speech-to-Text (Voice Recognition)                        │
│  • SMS Gateway (Twilio - for notifications)                         │
│  • Email Service (SendGrid - for reports)                           │
│  • Maps API (Location services)                                     │
│  • Health System Integration (HL7/FHIR - optional)                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: User Submission to Action

```
┌─────────────────────────────────────────────────────────────────────┐
│                     USER JOURNEY DATA FLOW                           │
└─────────────────────────────────────────────────────────────────────┘

Step 1: INPUT
┌──────────────────┐
│ User (Mobile)    │ → Voice/Text: "mi garr hedache en hot bodi"
│ Speaks in Kriol  │
└────────┬─────────┘
         ↓
Step 2: TRANSLATION
┌────────────────────────────────┐
│ Kriol Translator Module        │
│ - Tokenization                 │
│ - Dictionary Mapping           │
│ - Spelling Normalization       │
└────────┬───────────────────────┘
         ↓ Output: "i have headache and hot body"
         
Step 3: PREPROCESSING
┌────────────────────────────────┐
│ Text Preprocessing             │
│ - Expand contractions          │
│ - Spell correction             │
│ - Synonym mapping              │
└────────┬───────────────────────┘
         ↓ Output: "i have headache and fever"
         
Step 4: SYMPTOM EXTRACTION
┌────────────────────────────────┐
│ Symptom Extractor              │
│ - Pattern matching             │
│ - Entity recognition           │
│ - Negation detection           │
└────────┬───────────────────────┘
         ↓ Output: {symptoms: ["headache", "fever"], negated: []}
         
Step 5: ML TRIAGE
┌────────────────────────────────┐
│ ML Triage Model                │
│ - Feature vectorization        │
│ - Severity prediction          │
│ - Confidence scoring           │
└────────┬───────────────────────┘
         ↓ Output: {severity: "MODERATE", score: 0.78, priority: 2}
         
Step 6: RECOMMENDATION
┌────────────────────────────────┐
│ Recommendation Engine          │
│ - Rule-based logic             │
│ - Action mapping               │
│ - Resource availability        │
└────────┬───────────────────────┘
         ↓ Output: "Visit clinic within 24hrs"
         
Step 7: STORAGE & NOTIFICATION
┌────────────────────────────────┐
│ Database + Notifications       │
│ - Save patient record          │
│ - Queue for healthcare worker  │
│ - Send SMS (if urgent)         │
└────────┬───────────────────────┘
         ↓
Step 8: DISPLAY RESULTS
┌────────────────────────────────┐
│ Mobile App Shows:              │
│ ✓ Symptoms detected            │
│ ⚠️  Severity: MODERATE          │
│ 📋 Recommendations             │
│ 📞 Contact options             │
└────────────────────────────────┘
```

---

## Database Schema (Simplified)

```sql
-- PATIENTS TABLE
┌─────────────────────────────────────┐
│ patients                            │
├─────────────────────────────────────┤
│ id (PK)                             │
│ phone_number (unique)               │
│ preferred_language (kriol/english)  │
│ location                            │
│ created_at                          │
└─────────────────────────────────────┘

-- SUBMISSIONS TABLE
┌─────────────────────────────────────┐
│ submissions                         │
├─────────────────────────────────────┤
│ id (PK)                             │
│ patient_id (FK)                     │
│ original_text (kriol)               │
│ translated_text (english)           │
│ symptoms_extracted (JSON)           │
│ severity_level (1-5)                │
│ confidence_score (0-1)              │
│ recommended_action (TEXT)           │
│ status (pending/viewed/resolved)    │
│ submitted_at                        │
│ healthcare_worker_id (FK, nullable) │
│ resolved_at (nullable)              │
└─────────────────────────────────────┘

-- SYMPTOMS TABLE
┌─────────────────────────────────────┐
│ symptoms                            │
├─────────────────────────────────────┤
│ id (PK)                             │
│ name (varchar)                      │
│ category (respiratory/cardiac/etc)  │
│ severity_weight (float)             │
└─────────────────────────────────────┘

-- HEALTHCARE_WORKERS TABLE
┌─────────────────────────────────────┐
│ healthcare_workers                  │
├─────────────────────────────────────┤
│ id (PK)                             │
│ name                                │
│ email                               │
│ role (nurse/doctor/admin)           │
│ clinic_location                     │
│ last_login                          │
└─────────────────────────────────────┘

-- AUDIT_LOG TABLE
┌─────────────────────────────────────┐
│ audit_log                           │
├─────────────────────────────────────┤
│ id (PK)                             │
│ user_id (FK)                        │
│ action (login/view/edit/delete)     │
│ resource_type                       │
│ resource_id                         │
│ timestamp                           │
│ ip_address                          │
└─────────────────────────────────────┘
```

---

## API Endpoints Structure

```
POST   /api/v1/submit          - Submit new symptom report
GET    /api/v1/submissions     - List all submissions (paginated)
GET    /api/v1/submissions/:id - Get specific submission
PATCH  /api/v1/submissions/:id - Update submission status
POST   /api/v1/auth/login      - Healthcare worker login
GET    /api/v1/analytics       - Get analytics data
POST   /api/v1/voice/transcribe- Voice to text conversion
GET    /api/v1/health          - System health check
WS     /ws/notifications       - WebSocket for real-time updates
```

---

## ML Model Training Pipeline

```
Training Data Sources:
├── Historical triage data (from clinics)
├── Symptom combinations with outcomes
├── Expert-labeled severity levels
└── Emergency department records

↓

Feature Engineering:
├── Symptom presence (binary features)
├── Symptom combinations (interaction terms)
├── Patient demographics (age, location)
├── Symptom count
└── Negation flags

↓

Model Selection:
├── Random Forest Classifier
├── XGBoost
├── Logistic Regression (baseline)
└── Neural Network (advanced)

↓

Validation:
├── 80/20 train/test split
├── Cross-validation (5-fold)
├── Confusion matrix analysis
└── Feature importance analysis

↓

Deployment:
├── Serialize model (pickle/joblib)
├── REST API endpoint
├── Version control
└── A/B testing framework
```

---

## Security & Compliance

```
┌──────────────────────────────────────┐
│ Security Layers                      │
├──────────────────────────────────────┤
│ 1. Transport Layer (HTTPS/TLS 1.3)  │
│ 2. Authentication (JWT tokens)       │
│ 3. Authorization (RBAC)              │
│ 4. Data Encryption at Rest (AES-256)│
│ 5. API Rate Limiting                 │
│ 6. Input Validation & Sanitization   │
│ 7. Audit Logging (all actions)       │
│ 8. Regular Security Audits           │
└──────────────────────────────────────┘

Compliance:
✓ Australian Privacy Act
✓ My Health Records Act
✓ OAIC guidelines
✓ Data minimization
✓ Right to erasure
✓ Consent management
```

---

## Deployment Architecture

```
┌──────────────────────────────────────────────────────┐
│              Production Environment                   │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Load Balancer (Nginx/AWS ALB)                      │
│         ↓              ↓              ↓              │
│    App Server 1   App Server 2   App Server 3       │
│    (FastAPI)      (FastAPI)      (FastAPI)          │
│         ↓              ↓              ↓              │
│    ───────────────────┬───────────────               │
│                       ↓                              │
│              Database Cluster                        │
│         (PostgreSQL Primary + Replicas)              │
│                                                       │
│  Redis Cache Cluster (Session + Cache)               │
│                                                       │
│  ML Model Server (Separate container)                │
│                                                       │
│  File Storage (S3 or Azure Blob)                     │
│                                                       │
│  Monitoring: Prometheus + Grafana                    │
│  Logging: ELK Stack (Elasticsearch/Logstash/Kibana) │
│                                                       │
└──────────────────────────────────────────────────────┘
```

