# SACA Implementation Roadmap

## Project Summary

**Goal**: Build bilingual (Kriol-English) health triage system with mobile and desktop applications for Australian Indigenous communities.

---

## Answer to Your Question: "How many UIs?"

### ✅ **TWO UIs** - Here's Why:

| UI | Platform | Users | Purpose | Priority |
|----|----------|-------|---------|----------|
| **UI #1** | 📱 Android Mobile App | Community members | Symptom input, results | **HIGH** (Primary) |
| **UI #2** | 💻 Desktop Web App | Healthcare workers | Monitoring, triage | **HIGH** (Secondary) |

### Why Not Just One?

**Different users = Different needs:**

**Community Members Need:**
- Simple, voice-first interface
- Large buttons (low literacy)
- Works on phones (portable)
- Minimal training required
- Kriol language support
- Works offline

**Healthcare Workers Need:**
- Data-rich dashboard
- Multiple patient views
- Analytics and reporting
- Keyboard shortcuts
- Professional appearance
- Always connected

**Trying to combine both = Compromised UX for everyone** ❌

---

## What Should Each UI Include?

### 📱 MOBILE APP (Community Interface)

#### MUST HAVE (MVP):
1. ✅ **Language Selection** - Kriol / English toggle
2. ✅ **Voice Input** - Primary input method (Google Speech-to-Text)
3. ✅ **Text Input** - Backup for typing
4. ✅ **Quick Symptom Buttons** - Common symptoms in Kriol
5. ✅ **Results Display** - Color-coded severity with recommendations
6. ✅ **Emergency Actions** - Call 000 or clinic directly
7. ✅ **Save Report** - Keep history of submissions
8. ✅ **Offline Mode** - Work without internet, sync later

#### NICE TO HAVE (Phase 2):
- 📸 Photo upload (rashes, injuries)
- 📍 Location services (find nearest clinic)
- 📅 Appointment booking
- 💬 Chat with healthcare worker
- 🔔 Medication reminders
- 📊 Personal health trends

---

### 💻 DESKTOP APP (Healthcare Worker Interface)

#### MUST HAVE (MVP):
1. ✅ **Login/Authentication** - Secure user accounts
2. ✅ **Dashboard** - Overview of submissions and stats
3. ✅ **Priority Queue** - Sorted by severity (urgent first)
4. ✅ **Patient Details** - Full submission with translation
5. ✅ **Status Management** - Mark as viewed/resolved
6. ✅ **Search & Filter** - Find specific patients/symptoms
7. ✅ **Clinical Notes** - Add follow-up notes
8. ✅ **Basic Analytics** - Daily/weekly statistics

#### NICE TO HAVE (Phase 2):
- 📊 Advanced analytics (trends, predictions)
- 📤 Export reports (PDF, CSV)
- 🔔 Real-time push notifications
- 👥 Multi-clinic support
- 📞 Integrated calling/SMS
- 🏥 EHR integration (hospital systems)
- 📋 Care pathway templates
- 🔄 Automatic follow-up reminders

---

## Wireframe Screens Breakdown

### Mobile App Screens (8 core screens):

```
1. Splash/Welcome Screen
   └─> Simple logo and language selection

2. Language Selection
   └─> Choose Kriol or English

3. Symptom Input Screen
   └─> Voice button + Text input + Quick buttons

4. Processing Screen
   └─> Loading animation with progress

5. Results Screen
   └─> Severity + Symptoms + Recommendations

6. Emergency Alert Screen (conditional)
   └─> Red urgent screen if high severity

7. History Screen
   └─> Past submissions list

8. Settings Screen
   └─> Language, notifications, about
```

**Total: 8 screens** for MVP mobile app

---

### Desktop App Screens (6 core screens):

```
1. Login Screen
   └─> Email/password authentication

2. Dashboard (Home)
   └─> Stats + Recent submissions + Quick actions

3. Queue/List View
   └─> All submissions sorted by priority

4. Patient Detail View
   └─> Full submission details + actions

5. Analytics Screen
   └─> Charts and reports

6. Settings/Admin Screen
   └─> User management, system config
```

**Total: 6 screens** for MVP desktop app

---

## Complete Feature Matrix

### Features by Screen:

| Mobile Screen | Features Included |
|--------------|-------------------|
| **Splash** | Logo, version, loading |
| **Language** | Kriol/English buttons, flag icons |
| **Input** | Voice button, text field, quick buttons (8-10 symptoms), help text |
| **Processing** | Animation, progress steps, cancel button |
| **Results** | Severity badge, symptom list, recommendations, call button, save button |
| **Emergency** | Large call 000 button, clinic number, symptom summary |
| **History** | List of past submissions, date filter, search |
| **Settings** | Language toggle, notifications on/off, privacy policy |

| Desktop Screen | Features Included |
|---------------|-------------------|
| **Login** | Email field, password field, remember me, forgot password |
| **Dashboard** | Stat cards (4), recent list (10), quick filters, refresh |
| **Queue** | Table view, sort columns, filter by severity, search bar, pagination |
| **Detail** | Patient info, original text, translation, symptoms, triage result, notes field, status buttons |
| **Analytics** | Date range picker, symptom chart, severity pie chart, trends line graph, export button |
| **Settings** | User list, add user, clinic settings, notification config |

---

## Visual Wireframe Checklist

### What to Show Client in Wireframes:

#### Mobile Wireframes Should Show:
- [ ] Screen flow diagram (8 screens)
- [ ] Each screen layout (low-fidelity boxes)
- [ ] Button sizes and placement
- [ ] Icon locations
- [ ] Text size hierarchy
- [ ] Color-coded severity examples
- [ ] Voice input interaction
- [ ] Emergency flow path
- [ ] Kriol text examples

#### Desktop Wireframes Should Show:
- [ ] Navigation structure (top bar + sidebar)
- [ ] Dashboard layout with stat cards
- [ ] Table/list view with columns
- [ ] Patient detail card layout
- [ ] Chart types for analytics
- [ ] Modal dialogs (if any)
- [ ] Responsive behavior (if web-based)

---

## User Flow Examples (For Presentation)

### Flow 1: Simple Case (Green - Low Priority)

```
User: "mi garr hedache"
  ↓
Translation: "I have headache"
  ↓
Extraction: [headache]
  ↓
ML Triage: LOW (Level 1)
  ↓
Mobile Shows: 🟢 "Rest, drink water, paracetamol if needed"
  ↓
Desktop Shows: Low priority, auto-filed in queue
```

### Flow 2: Moderate Case (Yellow - Moderate Priority)

```
User: "mi garr hot bodi en kof"
  ↓
Translation: "I have fever and cough"
  ↓
Extraction: [fever, cough]
  ↓
ML Triage: MODERATE (Level 2)
  ↓
Mobile Shows: 🟡 "Visit clinic within 24 hours"
              [Call Clinic Button]
  ↓
Desktop Shows: Moderate priority, notification to nurse
  ↓
Nurse: Reviews, calls patient, schedules appointment
  ↓
Nurse: Marks as "Contacted - Appointment Booked"
```

### Flow 3: Emergency Case (Red - Urgent)

```
User: "mi garr bigfala pein longa ches en mi no kan bret"
  ↓
Translation: "I have very big pain in chest and I cannot breathe"
  ↓
Extraction: [chest pain (severe), shortness of breath]
  ↓
ML Triage: URGENT (Level 4)
  ↓
Mobile Shows: 🔴 EMERGENCY SCREEN
              [CALL 000 NOW] (large button)
  ↓
Desktop Shows: RED ALERT notification
               "URGENT: Patient needs immediate care"
  ↓
Nurse: Sees alert immediately, calls patient
  ↓
Action: Emergency transport arranged
```

---

## Prototype Tools (For Showing Client)

### Recommended Tools for Wireframes:

**Free Options:**
1. **Figma** (Free tier) - Best for collaborative design
   - Share link with client
   - Interactive prototype
   - Real-time comments

2. **Draw.io** - Simple flowcharts
   - Free, open-source
   - Good for system diagrams

3. **Balsamiq** (Trial) - Quick wireframes
   - Low-fidelity mockups
   - Fast to create

**Paid Options:**
4. **Adobe XD** - Professional design
5. **Sketch** (Mac only) - Industry standard

### What to Build First for Demo:

**Week 1: Paper/Whiteboard Sketches**
- Rough layouts
- User flow diagrams
- Team brainstorming

**Week 2: Digital Low-Fidelity Wireframes**
- Black & white boxes
- Basic layout structure
- Screen flow arrows

**Week 3: High-Fidelity Mockups**
- Real colors
- Actual text content (Kriol + English)
- Icons and images
- Branded design

**Week 4: Interactive Prototype**
- Clickable prototype in Figma
- Simulates navigation
- Client can "use" the app

---

## Presentation Deck Structure

### Slide-by-Slide Outline:

**Slide 1: Title**
- SACA: Smart Adaptive Clinical Assistant
- Wireframe Presentation

**Slide 2: Problem Statement**
- Language barriers in healthcare
- Late presentation of serious conditions
- Limited clinic access in remote areas

**Slide 3: Solution Overview**
- Two-platform system (mobile + desktop)
- Kriol-to-English translation
- AI triage and recommendations

**Slide 4: Mobile App Overview**
- Show main 4 screens side-by-side
- Explain voice-first design
- Highlight Kriol support

**Slide 5: Mobile App - Input Screen**
- Large wireframe of input screen
- Annotate key features
- Show Kriol examples

**Slide 6: Mobile App - Results Screen**
- Show all 3 severity levels (green, yellow, red)
- Explain color coding
- Show recommendation examples

**Slide 7: Mobile App - Emergency Flow**
- Show emergency alert screen
- Explain when it triggers
- Show call buttons

**Slide 8: Desktop App Overview**
- Show dashboard layout
- Explain healthcare worker needs
- Highlight priority queue

**Slide 9: Desktop App - Patient Detail**
- Show full patient detail screen
- Explain translation display
- Show triage result

**Slide 10: Desktop App - Analytics**
- Show chart examples
- Explain community health trends
- Value for clinic management

**Slide 11: User Journey Example**
- Walk through complete flow
- Mobile → AI → Desktop
- Show 3 scenarios (low, moderate, urgent)

**Slide 12: Technology Stack**
- Diagram of system architecture
- NLP + ML explanation
- Security & privacy notes

**Slide 13: Timeline & Budget**
- 6-9 month timeline
- Phased approach
- Cost estimate range

**Slide 14: Next Steps**
- Community consultation
- Data collection
- MVP development
- Beta testing

**Slide 15: Q&A**
- Discussion questions
- Contact information

---

## Client Meeting Agenda

### Recommended Meeting Flow (1 hour):

**0:00 - 0:05** - Introductions & Context
- Who we are
- Why we're here
- What we'll cover

**0:05 - 0:15** - Problem & Solution (Slides 2-3)
- Current challenges
- Proposed solution
- Why two platforms

**0:15 - 0:30** - Wireframe Walkthrough (Slides 4-10)
- Mobile app screens
- Desktop app screens
- Interactive demo (if ready)

**0:30 - 0:40** - User Scenarios (Slide 11)
- Walk through 3 example cases
- Show mobile + desktop interaction
- Discuss edge cases

**0:40 - 0:50** - Technical & Timeline (Slides 12-13)
- How it works
- Implementation plan
- Budget discussion

**0:50 - 1:00** - Discussion & Next Steps (Slides 14-15)
- Questions from client
- Feedback on designs
- Agreement on next steps

---

## Key Questions to Ask Client

During wireframe presentation, gather this info:

### About Users:
1. How many community members would use mobile app?
2. What age range? (affects UI design)
3. How many healthcare workers need desktop access?
4. What's the literacy level? (affects text vs. icons)

### About Content:
5. Do we have Kriol speakers to review translations?
6. What are the top 20 symptoms we should prioritize?
7. What clinics should be pre-programmed for calling?
8. Are there cultural protocols we must follow?

### About Technical:
9. What's the internet connectivity like? (affects offline needs)
10. Do you have existing health IT systems to integrate?
11. Do you have historical triage data for ML training?
12. What devices do people use? (Android versions?)

### About Process:
13. Who will provide ongoing content updates?
14. Who will monitor the desktop dashboard daily?
15. What's your budget and timeline flexibility?
16. Any regulatory approvals needed?

---

## Summary: What Client Needs to Approve

### From This Meeting:
- [ ] Approve the two-UI approach (mobile + desktop)
- [ ] Approve overall screen flows
- [ ] Approve key features in MVP
- [ ] Approve color scheme and cultural design
- [ ] Provide feedback on wireframes

### Before Next Meeting:
- [ ] Gather community feedback
- [ ] Confirm budget allocation
- [ ] Identify key stakeholders
- [ ] Provide sample Kriol phrases
- [ ] Share any existing health data

---

## Deliverables After Client Approval

Once wireframes are approved, next deliverables:

1. **High-Fidelity Mockups** (2-3 weeks)
   - Full color designs
   - All screens
   - Brand guidelines

2. **Interactive Prototype** (1-2 weeks)
   - Clickable demo
   - Can test with users

3. **Technical Specification** (2 weeks)
   - Database schema
   - API documentation
   - System requirements

4. **Development Plan** (1 week)
   - Sprint planning
   - Resource allocation
   - Risk assessment

Then → Start development! 🚀

