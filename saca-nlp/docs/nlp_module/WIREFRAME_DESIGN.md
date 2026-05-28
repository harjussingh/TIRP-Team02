# SACA (Smart Adaptive Clinical Assistant) - UI/UX Wireframe Design

## 🎯 Target Users
Australian Indigenous community members who speak Kriol language

## 📱 Platform Requirements
- **Android Mobile App** - For community members to use anywhere
- **Desktop Application** - For health workers/clinics

---

## 1. ANDROID MOBILE APP (Primary User Interface)

### Screen 1: Welcome/Language Selection Screen
```
╔══════════════════════════════════════╗
║                                      ║
║         [SACA Logo/Icon]            ║
║                                      ║
║    Smart Adaptive Clinical          ║
║         Assistant                    ║
║                                      ║
║    ┌──────────────────────────┐    ║
║    │  🗣️  Kriol Language      │    ║
║    └──────────────────────────┘    ║
║                                      ║
║    ┌──────────────────────────┐    ║
║    │  🗣️  English              │    ║
║    └──────────────────────────┘    ║
║                                      ║
║    ┌──────────────────────────┐    ║
║    │  📜  View History          │    ║
║    └──────────────────────────┘    ║
║                                      ║
╚══════════════════════════════════════╝
```

**Features:**
- Simple, large buttons
- Visual icons for accessibility
- Option to switch between Kriol/English
- Access to previous consultations

---

### Screen 2: Symptom Input Screen
```
╔══════════════════════════════════════╗
║  [← Back]    How yu fel?    [Help] ║
║──────────────────────────────────────║
║                                      ║
║  🎤 [Voice Input Button]            ║
║      Tap to speak                    ║
║                                      ║
║  ─────────── or ───────────         ║
║                                      ║
║  ┌────────────────────────────────┐ ║
║  │ Type how you feel here...      │ ║
║  │                                │ ║
║  │ Example: "mi garr hedache      │ ║
║  │ en hot bodi"                   │ ║
║  └────────────────────────────────┘ ║
║                                      ║
║  Quick Options:                     ║
║  [Hedache] [Hot bodi] [Kof]        ║
║  [Beli pen] [Disi] [Sik]           ║
║                                      ║
║         [Next →]                     ║
║                                      ║
╚══════════════════════════════════════╝
```

**Features:**
- **Voice input** (critical for low literacy)
- Text input option
- Quick-select symptom buttons in Kriol
- Example text to guide users
- Simple navigation

---

### Screen 3: Processing/Translation Screen
```
╔══════════════════════════════════════╗
║                                      ║
║         [Loading Animation]         ║
║                                      ║
║    Checking your symptoms...        ║
║                                      ║
║    ✓ Translation complete           ║
║    ✓ Symptoms detected              ║
║    ⏳ Analyzing severity...          ║
║                                      ║
╚══════════════════════════════════════╝
```

**Features:**
- Visual progress indicator
- Step-by-step feedback
- Reassures user system is working

---

### Screen 4: Results & Triage Screen
```
╔══════════════════════════════════════╗
║  Your Health Assessment              ║
║──────────────────────────────────────║
║                                      ║
║  What you said:                      ║
║  "mi garr hedache en hot bodi"      ║
║                                      ║
║  Symptoms found:                     ║
║  ✓ Headache                         ║
║  ✓ Fever                            ║
║                                      ║
║  ┌────────────────────────────────┐ ║
║  │ ⚠️  SEVERITY: MODERATE          │ ║
║  │                                │ ║
║  │ Priority Level: 2 out of 5     │ ║
║  │ [████████░░] 80%               │ ║
║  └────────────────────────────────┘ ║
║                                      ║
║  Recommended Action:                ║
║  ┌────────────────────────────────┐ ║
║  │ 🏥 Visit clinic within 24 hrs  │ ║
║  │                                │ ║
║  │ 💊 Take paracetamol            │ ║
║  │    Drink plenty of water       │ ║
║  │                                │ ║
║  │ ⚠️  Seek urgent care if:       │ ║
║  │    - Fever > 39°C              │ ║
║  │    - Severe pain               │ ║
║  └────────────────────────────────┘ ║
║                                      ║
║  [📞 Call Clinic] [🏠 Home]         ║
║  [📄 Save Report] [🔄 New Check]    ║
║                                      ║
╚══════════════════════════════════════╝
```

**Features:**
- Color-coded severity (Green/Yellow/Red)
- Clear visual indicators
- Actionable recommendations
- Emergency contact buttons
- Option to save/share report

---

### Screen 5: Emergency Alert Screen (if HIGH severity)
```
╔══════════════════════════════════════╗
║  🚨 URGENT MEDICAL ATTENTION         ║
║══════════════════════════════════════║
║                                      ║
║  ⚠️  Your symptoms need              ║
║      immediate medical attention     ║
║                                      ║
║  ┌────────────────────────────────┐ ║
║  │                                │ ║
║  │  [📞 CALL 000]                 │ ║
║  │      (Emergency)               │ ║
║  │                                │ ║
║  └────────────────────────────────┘ ║
║                                      ║
║  ┌────────────────────────────────┐ ║
║  │                                │ ║
║  │  [📞 CALL LOCAL CLINIC]        │ ║
║  │      (08) 1234 5678            │ ║
║  │                                │ ║
║  └────────────────────────────────┘ ║
║                                      ║
║  Symptoms detected:                 ║
║  • Severe chest pain                ║
║  • Shortness of breath              ║
║                                      ║
║  [🏠 Cancel]                         ║
║                                      ║
╚══════════════════════════════════════╝
```

**Features:**
- High contrast red alert design
- Large emergency buttons
- Direct calling functionality
- Clear warning messages

---

## 2. DESKTOP APPLICATION (Healthcare Worker Interface)

### Main Dashboard
```
╔════════════════════════════════════════════════════════════════════╗
║  SACA - Healthcare Dashboard                    [Admin] [Logout]  ║
║════════════════════════════════════════════════════════════════════║
║  [Dashboard] [Patients] [Analytics] [Settings]                    ║
║────────────────────────────────────────────────────────────────────║
║                                                                     ║
║  TODAY'S STATISTICS                                                ║
║  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐║
║  │   Total     │ │   Urgent    │ │  Moderate   │ │    Low      │║
║  │    52       │ │      3      │ │     18      │ │    31       │║
║  │ Submissions │ │   Priority  │ │  Priority   │ │  Priority   │║
║  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘║
║                                                                     ║
║  RECENT SUBMISSIONS (Last 24 hours)                               ║
║  ┌───────────────────────────────────────────────────────────────┐║
║  │ Time   │ Patient ID  │ Symptoms          │ Severity │ Status │║
║  ├───────────────────────────────────────────────────────────────┤║
║  │ 14:23  │ P-00234    │ Fever, Cough      │ 🟡 MOD   │ Pending│║
║  │ 13:45  │ P-00235    │ Chest Pain        │ 🔴 HIGH  │ Urgent │║
║  │ 12:10  │ P-00236    │ Headache          │ 🟢 LOW   │ Viewed │║
║  │ 11:05  │ P-00237    │ Abdominal Pain    │ 🟡 MOD   │ Pending│║
║  └───────────────────────────────────────────────────────────────┘║
║                                                                     ║
║  [View All] [Export Report] [Refresh]                             ║
║                                                                     ║
╚════════════════════════════════════════════════════════════════════╝
```

---

### Patient Detail View
```
╔════════════════════════════════════════════════════════════════════╗
║  Patient Assessment Detail                    [Print] [Close]     ║
║════════════════════════════════════════════════════════════════════║
║                                                                     ║
║  PATIENT INFORMATION                                               ║
║  ID: P-00235              Time: 13:45, 15 Mar 2026                ║
║  Language: Kriol          Location: Nhulunbuy                     ║
║                                                                     ║
║  ────────────────────────────────────────────────────────────────  ║
║                                                                     ║
║  ORIGINAL INPUT (KRIOL):                                          ║
║  ┌───────────────────────────────────────────────────────────────┐║
║  │ "mi garr bigfala pein longa ches en mi no kan bret gud"      │║
║  └───────────────────────────────────────────────────────────────┘║
║                                                                     ║
║  ENGLISH TRANSLATION:                                              ║
║  ┌───────────────────────────────────────────────────────────────┐║
║  │ "I have very big pain in chest and I cannot breathe well"    │║
║  └───────────────────────────────────────────────────────────────┘║
║                                                                     ║
║  EXTRACTED SYMPTOMS:                                               ║
║  ✓ Chest pain (severe)                                            ║
║  ✓ Shortness of breath                                            ║
║                                                                     ║
║  ────────────────────────────────────────────────────────────────  ║
║                                                                     ║
║  🔴 TRIAGE ASSESSMENT: HIGH PRIORITY (Level 4/5)                  ║
║                                                                     ║
║  Confidence Score: 92%                                             ║
║  Risk Factors Detected:                                            ║
║  • Cardiovascular symptoms                                         ║
║  • Respiratory distress                                            ║
║  • Multiple critical indicators                                    ║
║                                                                     ║
║  RECOMMENDED ACTIONS:                                              ║
║  🚨 IMMEDIATE medical assessment required                          ║
║  📞 Contact patient immediately                                    ║
║  🏥 Arrange emergency transport if needed                          ║
║  💉 Prepare for cardiac evaluation                                 ║
║                                                                     ║
║  ────────────────────────────────────────────────────────────────  ║
║                                                                     ║
║  HEALTHCARE WORKER ACTIONS:                                        ║
║  [✓ Patient Contacted] [✓ Action Taken] [Add Notes]              ║
║                                                                     ║
║  Notes:                                                            ║
║  ┌───────────────────────────────────────────────────────────────┐║
║  │ Add clinical notes here...                                    │║
║  └───────────────────────────────────────────────────────────────┘║
║                                                                     ║
║  [Mark as Resolved] [Escalate] [Back to Dashboard]                ║
║                                                                     ║
╚════════════════════════════════════════════════════════════════════╝
```

---

### Analytics Dashboard
```
╔════════════════════════════════════════════════════════════════════╗
║  SACA Analytics & Reporting                                        ║
║════════════════════════════════════════════════════════════════════║
║                                                                     ║
║  Time Period: [Last 7 Days ▼]  [Export CSV] [Generate Report]    ║
║                                                                     ║
║  SYMPTOM FREQUENCY                  SEVERITY DISTRIBUTION          ║
║  ┌─────────────────────────┐      ┌──────────────────────────┐   ║
║  │                         │      │        [Pie Chart]       │   ║
║  │   [Bar Chart]           │      │                          │   ║
║  │   Top Symptoms:         │      │   🔴 High:    15%        │   ║
║  │   1. Fever - 45         │      │   🟡 Moderate: 35%       │   ║
║  │   2. Headache - 38      │      │   🟢 Low:     50%        │   ║
║  │   3. Cough - 32         │      │                          │   ║
║  │   4. Dizziness - 28     │      └──────────────────────────┘   ║
║  └─────────────────────────┘                                      ║
║                                                                     ║
║  RESPONSE TIME METRICS              LANGUAGE USAGE                 ║
║  Average: 12 minutes                Kriol: 78%                    ║
║  Urgent cases: 5 minutes            English: 22%                  ║
║                                                                     ║
║  COMMUNITY HEALTH TRENDS                                           ║
║  ┌───────────────────────────────────────────────────────────────┐║
║  │                     [Line Graph]                              │║
║  │  Showing symptom trends over time...                         │║
║  └───────────────────────────────────────────────────────────────┘║
║                                                                     ║
╚════════════════════════════════════════════════════════════════════╝
```

---

## 3. KEY UI COMPONENTS TO INCLUDE

### Mobile App (Android) Must-Haves:
1. ✅ **Voice Input** - Primary input method
2. ✅ **Large, Clear Buttons** - Accessibility
3. ✅ **Visual Icons** - For low literacy users
4. ✅ **Bilingual Support** - Kriol + English toggle
5. ✅ **Color-Coded Severity** - Green/Yellow/Red
6. ✅ **Quick Symptom Buttons** - Common symptoms in Kriol
7. ✅ **Emergency Call Integration** - Direct dial 000 or clinic
8. ✅ **Offline Mode** - Store and sync when connected
9. ✅ **History View** - Previous consultations
10. ✅ **Cultural Appropriateness** - Colors, images, language

### Desktop App Must-Haves:
1. ✅ **Dashboard** - Overview of all submissions
2. ✅ **Priority Queue** - Sort by severity
3. ✅ **Detailed Patient View** - Full translation + analysis
4. ✅ **Analytics** - Trends and reporting
5. ✅ **Search & Filter** - Find specific cases
6. ✅ **Export Functions** - CSV, PDF reports
7. ✅ **Multi-user Support** - Healthcare worker accounts
8. ✅ **Real-time Notifications** - High priority alerts
9. ✅ **Clinical Notes** - Add follow-up notes
10. ✅ **Data Privacy** - HIPAA/Australian health data compliance

---

## 4. COLOR SCHEME & DESIGN GUIDELINES

### Severity Color Coding:
- 🟢 **GREEN** - Low priority (self-care)
- 🟡 **YELLOW** - Moderate (visit clinic 24-48hrs)
- 🟠 **ORANGE** - High (visit clinic today)
- 🔴 **RED** - Urgent (emergency/immediate)

### Cultural Design Considerations:
- Use earth tones (ochre, browns, greens)
- Aboriginal art patterns (if culturally appropriate and approved)
- High contrast for outdoor visibility
- Large fonts (min 16pt on mobile)
- Simple, clean layouts
- Avoid cluttered screens

---

## 5. USER FLOW DIAGRAM

### Mobile User Journey:
```
Start → Language Select → Input Symptoms (Voice/Text) → 
Processing → Results + Severity → Actions (Call/Save) → 
Home/History
```

### Healthcare Worker Journey:
```
Login → Dashboard (View Queue) → Select Patient → 
Review Details → Take Action → Add Notes → 
Mark Resolved → Analytics (Optional)
```

---

## 6. TECHNICAL IMPLEMENTATION NOTES

### Mobile App Stack:
- **Framework**: React Native or Flutter (cross-platform)
- **Voice Recognition**: Google Speech-to-Text API
- **Backend**: Python FastAPI (REST API)
- **Database**: PostgreSQL or Firebase
- **Offline**: SQLite local storage

### Desktop App Stack:
- **Framework**: Electron or Web App (React/Vue)
- **Backend**: Same Python API
- **Real-time**: WebSockets for notifications
- **Reports**: Chart.js or D3.js for visualizations

### Backend Requirements:
- REST API endpoints
- ML model serving (Flask/FastAPI)
- User authentication (JWT)
- Data encryption at rest
- Audit logging
- FHIR compliance (optional for health data exchange)

---

## 7. NEXT STEPS FOR DEVELOPMENT

1. ✅ **Backend API** - Expose current Python system as REST API
2. ✅ **ML Triage Model** - Train model on medical triage data
3. ✅ **Mobile Prototype** - React Native basic screens
4. ✅ **Desktop Dashboard** - Web-based admin panel
5. ✅ **User Testing** - Test with community members
6. ✅ **Iterate** - Refine based on feedback

---

## 8. SECURITY & PRIVACY

- End-to-end encryption for patient data
- HIPAA compliance (or Australian equivalent)
- Secure authentication
- Data anonymization for analytics
- Consent forms (digital signature)
- Audit trails for all access
- Regular security audits

---

## Questions for Client Presentation:

1. Do you have existing medical triage data for ML training?
2. What are the most common symptoms in your community?
3. What are the local clinic contact numbers?
4. Are there specific cultural protocols to follow?
5. What languages besides Kriol should we support?
6. Do you need integration with existing health systems?
7. What is the internet connectivity like in the community?

