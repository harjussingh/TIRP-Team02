# SACA Client Presentation - Executive Summary

## 🎯 Project Overview

**SACA** (Smart Adaptive Clinical Assistant) is a bilingual (Kriol-English) health triage system designed specifically for Australian Indigenous communities to improve healthcare access and early intervention.

---

## 📱 Two-Platform Solution

### Why 2 UIs?

We recommend **2 separate user interfaces** optimized for different user groups:

| Platform | Primary Users | Purpose |
|----------|--------------|---------|
| **📱 Android Mobile App** | Community members | Self-assessment, symptom reporting |
| **💻 Desktop Web Application** | Healthcare workers, Clinics | Monitoring, triage management, analytics |

---

## 🏗️ System Overview

```
Community Member → Mobile App → Backend AI → Healthcare Worker Dashboard
     (Kriol)                    (Translation + ML)        (English)
```

### What It Does:

1. **User inputs symptoms** in Kriol (voice or text)
2. **System translates** to English automatically
3. **AI extracts symptoms** and detects negations
4. **ML model predicts severity** (Low/Moderate/High/Urgent)
5. **System recommends action** (self-care, clinic visit, emergency)
6. **Healthcare workers monitor** high-priority cases
7. **Analytics track** community health trends

---

## 📱 MOBILE APP (Community Member Interface)

### Key Screens:

#### 1. Home Screen
- Simple language selection (Kriol / English)
- Large, clear buttons with icons
- Access to history

#### 2. Input Screen
- **🎤 Voice input** (primary method - for low literacy)
- Text input alternative
- Quick-select symptom buttons in Kriol
- Examples to guide users

#### 3. Results Screen
- Color-coded severity indicator:
  - 🟢 GREEN = Low (self-care at home)
  - 🟡 YELLOW = Moderate (clinic in 24-48hrs)
  - 🔴 RED = Urgent (emergency care NOW)
- Clear recommendations
- Emergency call button
- Save report option

#### 4. Emergency Screen (if urgent)
- Large emergency buttons
- Direct dial 000 or local clinic
- Critical warning display

### Mobile Features:
✅ Voice recognition (Google Speech-to-Text)  
✅ Works in Kriol and English  
✅ Offline mode (saves and syncs later)  
✅ Cultural design (appropriate colors, icons)  
✅ Large fonts for accessibility  
✅ History of past submissions  
✅ Emergency calling integration  

---

## 💻 DESKTOP APP (Healthcare Worker Interface)

### Key Screens:

#### 1. Dashboard
- Today's statistics (total submissions, urgent cases)
- Priority queue (sorted by severity)
- Recent submissions list
- Quick actions

#### 2. Patient Detail View
- Original Kriol input
- English translation
- Extracted symptoms
- AI severity assessment (with confidence score)
- Recommended actions
- Patient contact info
- Clinical notes section

#### 3. Analytics Dashboard
- Symptom frequency charts
- Severity distribution (pie chart)
- Response time metrics
- Community health trends over time
- Exportable reports (CSV, PDF)

### Desktop Features:
✅ Real-time notifications for urgent cases  
✅ Multi-user support (doctors, nurses, admin)  
✅ Search and filter submissions  
✅ Patient management  
✅ Export analytics reports  
✅ Audit trail (who viewed what, when)  
✅ Integration ready (can connect to hospital systems)  

---

## 🧠 AI/ML Technology Stack

### Natural Language Processing (NLP):
1. **Kriol-to-English Translation**
   - Custom dictionary (100+ medical terms)
   - Fuzzy matching for spelling variations
   - Grammar post-processing

2. **Symptom Extraction**
   - Pattern matching
   - Synonym mapping
   - Negation detection (handles "no", "don't have", etc.)

3. **Text Preprocessing**
   - Contraction expansion
   - Spell correction
   - Normalization

### Machine Learning Triage:
- **Model Type**: Random Forest / XGBoost Classifier
- **Input**: Extracted symptoms + combinations
- **Output**: Severity level (1-5) + confidence score
- **Training**: Historical triage data from clinics
- **Accuracy Target**: 85-90%

### How It Works:
```
Kriol Input → Translation → Symptom Extraction → 
ML Prediction → Action Recommendation → Alert Healthcare Worker
```

---

## 🎨 UI Design Principles

### Mobile (Community-Focused):
- **Large touch targets** (buttons 60x60px minimum)
- **High contrast colors** (works in bright sunlight)
- **Minimal text** (icons + simple words)
- **Voice-first** (accommodate low literacy)
- **Cultural colors** (earth tones, ochre)
- **Aboriginal art elements** (if culturally approved)

### Desktop (Clinical-Focused):
- **Information density** (dashboard view)
- **Data visualization** (charts, graphs)
- **Professional design** (clinical appearance)
- **Efficient workflow** (keyboard shortcuts)
- **Multi-window support** (compare cases)

---

## 📊 Example User Journey

### Scenario: Maria has a headache and fever

```
Step 1: Maria opens app on her phone
        Taps "Kriol Language"

Step 2: Taps microphone button
        Says: "mi garr hedache en hot bodi"

Step 3: System processes (3 seconds):
        ✓ Translates to English
        ✓ Detects: headache, fever
        ✓ ML predicts: MODERATE severity
        ✓ Confidence: 82%

Step 4: Maria sees result:
        🟡 MODERATE PRIORITY
        "Visit clinic within 24 hours"
        "Drink water, rest"
        "Call if fever goes above 39°C"
        
        [📞 Call Clinic] [💾 Save Report]

Step 5: Healthcare worker dashboard shows:
        🟡 New submission - Maria P.
        Symptoms: Headache, Fever
        Priority: 2/5
        Status: Pending review
        
Step 6: Nurse reviews, adds notes:
        "Called patient - advised paracetamol
         Scheduled appointment tomorrow 10am"
        
        [✓ Mark Resolved]
```

---

## 🔒 Security & Privacy

### Data Protection:
- End-to-end encryption
- HIPAA-compliant (Australian health data standards)
- Secure authentication (JWT tokens)
- Audit logging (all access tracked)
- Data anonymization for analytics
- Regular security audits

### Compliance:
✅ Australian Privacy Act  
✅ My Health Records Act  
✅ Indigenous data sovereignty principles  
✅ Community consent protocols  

---

## 📈 Expected Benefits

### For Community Members:
- 24/7 access to health assessment
- Speak in native language (Kriol)
- Reduce fear/barriers to seeking care
- Early detection of serious conditions
- Cultural safety

### For Healthcare Workers:
- Prioritize urgent cases automatically
- Reduce non-urgent clinic visits
- Identify health trends in community
- Better resource allocation
- Data-driven decision making

### For Health System:
- Reduce emergency department load
- Early intervention = better outcomes
- Lower overall healthcare costs
- Improved health equity
- Evidence-based policy making

---

## 💰 Cost Estimate (Rough)

| Component | Estimated Cost (AUD) |
|-----------|---------------------|
| Mobile App Development | $50,000 - $80,000 |
| Desktop App Development | $40,000 - $60,000 |
| Backend API & ML Model | $30,000 - $50,000 |
| UI/UX Design | $15,000 - $25,000 |
| Testing & QA | $10,000 - $20,000 |
| Deployment & Infrastructure (Year 1) | $5,000 - $10,000 |
| **Total** | **$150,000 - $245,000** |

*Note: Costs vary based on features, complexity, and team location*

### Ongoing Costs:
- Server hosting: $500-2,000/month
- Maintenance: $2,000-5,000/month
- Support: $1,000-3,000/month

---

## ⏱️ Timeline

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| **Phase 1: Design** | 4-6 weeks | Wireframes, UI designs, user testing |
| **Phase 2: Backend** | 6-8 weeks | API, ML model, database |
| **Phase 3: Mobile App** | 8-10 weeks | Android app (MVP) |
| **Phase 4: Desktop App** | 6-8 weeks | Web dashboard |
| **Phase 5: Testing** | 4-6 weeks | Beta testing with community |
| **Phase 6: Launch** | 2-4 weeks | Deployment, training |
| **Total** | **6-9 months** | Full system launch |

---

## 🎯 Success Metrics

### Key Performance Indicators (KPIs):

1. **Adoption Rate**
   - Target: 500+ users in first 6 months
   - Daily active users: 50-100

2. **Accuracy**
   - Symptom extraction: >90% accuracy
   - Severity prediction: >85% accuracy
   - Translation quality: >95% comprehension

3. **Response Time**
   - App processing: <5 seconds
   - Healthcare worker response: <30 minutes (urgent cases)

4. **Health Outcomes**
   - Reduced ED visits for non-urgent cases
   - Earlier detection of serious conditions
   - Improved patient satisfaction

5. **System Performance**
   - 99.5% uptime
   - <500ms API response time
   - Zero security breaches

---

## 🚀 Next Steps

1. **Stakeholder Approval** - Get sign-off on wireframes
2. **Community Consultation** - Validate with Kriol speakers
3. **Data Collection** - Gather triage training data
4. **Technical Spec** - Detailed technical requirements
5. **Team Assembly** - Hire developers/designers
6. **MVP Development** - Build Phase 1 prototype
7. **User Testing** - Beta test with community
8. **Iterate & Launch** - Refine and deploy

---

## ❓ Questions for Discussion

1. **Existing Systems**: Do you have electronic health records we should integrate with?
2. **Training Data**: Do you have historical triage data for ML training?
3. **Community**: Can we organize focus groups with Kriol speakers?
4. **Clinics**: How many clinics will use the desktop system?
5. **Support**: Who will provide technical support to users?
6. **Funding**: Is this grant-funded or government-funded?
7. **Timeline**: Is there a hard deadline for launch?
8. **Scope**: Start with MVP or full system first?

---

## 📞 Contact & Support

For more information:
- **Technical Docs**: See `SYSTEM_ARCHITECTURE.md`
- **Wireframes**: See `WIREFRAME_DESIGN.md`
- **Current System**: Working prototype available for demo

---

*This presentation document is designed to be shared with clients, stakeholders, and funding bodies to explain the SACA system vision.*
