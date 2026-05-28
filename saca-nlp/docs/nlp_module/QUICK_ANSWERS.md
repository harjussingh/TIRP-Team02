# QUICK ANSWERS - Client Presentation

## Your Question: How many UIs? What should they include?

---

## ANSWER: 2 UIs

### UI #1: 📱 MOBILE APP (for community members)
### UI #2: 💻 DESKTOP APP (for healthcare workers)

---

## WHY 2 SEPARATE UIs?

| Aspect | Mobile (Community) | Desktop (Healthcare) |
|--------|-------------------|---------------------|
| **Users** | Aboriginal community members | Doctors, nurses, clinic staff |
| **Language** | Kriol + English | English (shows Kriol input) |
| **Complexity** | Very simple | Data-rich |
| **Input** | Voice-first | Keyboard/mouse |
| **Goal** | Report symptoms, get advice | Monitor patients, manage triage |
| **Literacy** | Low (voice + icons) | High (professional) |
| **Connectivity** | Works offline | Always online |

**Conclusion**: Different users → Different needs → Different UIs

---

## MOBILE APP - WHAT TO INCLUDE

### 🎯 Core Screens (8):
1. **Welcome** - Language selection
2. **Input** - Voice + text + quick buttons
3. **Processing** - Loading indicator
4. **Results** - Severity + recommendations
5. **Emergency** - Large call 000 button (if urgent)
6. **History** - Past submissions
7. **Settings** - Preferences
8. **Help** - How to use

### 🔑 Key Features:
✅ Voice input (primary)
✅ Text input (backup)
✅ Kriol language support
✅ Quick symptom buttons (common symptoms)
✅ Color-coded results (🟢🟡🔴)
✅ Emergency calling
✅ Offline mode
✅ Save history

### 📏 Design Principles:
- Large buttons (60x60px)
- Simple language
- Visual icons
- High contrast
- Cultural colors (earth tones)
- Works in sunlight

---

## DESKTOP APP - WHAT TO INCLUDE

### 🎯 Core Screens (6):
1. **Login** - Authentication
2. **Dashboard** - Overview + stats
3. **Queue** - All submissions sorted by severity
4. **Patient Detail** - Full info + triage result
5. **Analytics** - Charts and trends
6. **Settings** - User management

### 🔑 Key Features:
✅ Priority queue (urgent first)
✅ Real-time notifications
✅ Patient search & filter
✅ View Kriol → English translation
✅ Add clinical notes
✅ Mark cases resolved
✅ Analytics & reports
✅ Multi-user support

### 📏 Design Principles:
- Professional appearance
- Information density
- Data visualization
- Efficient workflow
- Keyboard shortcuts

---

## WHAT SHOULD WIREFRAMES SHOW?

### Mobile Wireframes:
```
┌─────────────────┐
│  Screen Layout  │
│  ┌───────────┐  │
│  │ [BUTTON]  │  │ ← Large touch targets
│  └───────────┘  │
│                 │
│  Text example   │ ← Kriol text samples
│  in Kriol       │
│                 │
│  [🎤] [⌨️]      │ ← Voice/Text icons
└─────────────────┘
```

Show:
- Button sizes and placement
- Text hierarchy (large fonts)
- Icon usage
- Color coding
- Navigation flow
- Kriol language examples

### Desktop Wireframes:
```
┌─────────────────────────────────────────┐
│ Top Navigation Bar                       │
├─────────┬───────────────────────────────┤
│ Sidebar │ Main Content Area             │
│         │                               │
│ [Menu]  │  [Cards/Tables/Charts]        │
│         │                               │
│ [Menu]  │                               │
└─────────┴───────────────────────────────┘
```

Show:
- Dashboard layout
- Table/list views
- Chart types
- Modal dialogs
- Patient detail cards
- Filtering options

---

## USER JOURNEY EXAMPLES (For Client)

### Example 1: Low Severity
```
Maria types: "mi garr hedache" (I have headache)
         ↓
System: Translates → Extracts → Predicts
         ↓
Mobile shows: 🟢 LOW - "Rest, drink water"
         ↓
Desktop shows: New submission (low priority)
```

### Example 2: High Severity
```
John says: "mi garr pein longa ches" (chest pain)
         ↓
System: Translates → Extracts → Predicts
         ↓
Mobile shows: 🔴 URGENT - "CALL 000 NOW"
         ↓
Desktop shows: RED ALERT - Nurse notified immediately
         ↓
Nurse calls patient, arranges emergency care
```

---

## TECH STACK (Simple Explanation for Client)

```
┌─────────────────────────────┐
│  MOBILE APP                 │
│  (React Native/Flutter)     │
│  - Runs on Android          │
│  - Voice recognition        │
│  - Works offline            │
└──────────┬──────────────────┘
           │
           ↓ Internet
┌──────────────────────────────┐
│  BACKEND (Python AI)         │
│  - Kriol translation         │
│  - Symptom extraction        │
│  - ML triage prediction      │
│  - Secure database           │
└──────────┬───────────────────┘
           │
           ↓ Internet
┌──────────────────────────────┐
│  DESKTOP APP                 │
│  (Web browser)               │
│  - Dashboard                 │
│  - Patient management        │
│  - Analytics                 │
└──────────────────────────────┘
```

---

## TIMELINE ESTIMATE

| Phase | Duration | What You'll See |
|-------|----------|----------------|
| **1. Design** | 6 weeks | Wireframes → Mockups → Prototype |
| **2. Backend** | 8 weeks | API + ML model working |
| **3. Mobile** | 10 weeks | Android app (beta) |
| **4. Desktop** | 8 weeks | Web dashboard |
| **5. Testing** | 6 weeks | Community testing |
| **6. Launch** | 2 weeks | Deploy + training |
| **TOTAL** | **~9 months** | Full system live |

---

## COST ESTIMATE (Rough)

| Component | Cost (AUD) |
|-----------|-----------|
| Mobile App | $60,000 |
| Desktop App | $50,000 |
| Backend/ML | $40,000 |
| Design | $20,000 |
| Testing | $15,000 |
| **TOTAL** | **~$185,000** |

Plus ongoing: ~$3-5K/month (hosting, support, maintenance)

---

## WHAT CLIENT NEEDS TO DECIDE

### Today (Wireframe Meeting):
1. ✅ Approve the 2-UI approach?
2. ✅ Approve screen layouts?
3. ✅ Approve key features?
4. ✅ Any missing screens/features?
5. ✅ Cultural design concerns?

### This Week:
6. ✅ What's your budget?
7. ✅ What's your deadline?
8. ✅ Who are key stakeholders?
9. ✅ Can we test with community?
10. ✅ Do you have triage data for ML?

### Next Steps:
- Community consultation (validate designs)
- High-fidelity mockups (real colors/text)
- Interactive prototype (clickable demo)
- Technical specification (detailed plan)
- Development kickoff (start building)

---

## KEY SELLING POINTS

### For Community:
🗣️ "Speak in Kriol, get help in your language"
📱 "Use your phone anytime, anywhere"
🎤 "Just talk to the app - no typing needed"
🚨 "Know when you need urgent care"

### For Healthcare Workers:
📊 "See all urgent cases first"
🔔 "Get alerts for emergencies immediately"
📈 "Track community health trends"
💼 "Save time with automated triage"

### For Administrators:
💰 "Reduce unnecessary ED visits"
🎯 "Better resource allocation"
📉 "Early intervention = better outcomes"
📊 "Data-driven decision making"

---

## QUESTIONS TO ASK CLIENT

1. **Users**: How many people in the community?
2. **Symptoms**: What are the most common health issues?
3. **Clinics**: Which clinics will use the system?
4. **Language**: Are there Kriol speakers to review translations?
5. **Connectivity**: What's the internet/mobile coverage like?
6. **Integration**: Existing health IT systems to connect with?
7. **Training**: Who will train users and staff?
8. **Support**: Who provides ongoing support?
9. **Budget**: What funding is available?
10. **Timeline**: Any hard deadlines?

---

## SUMMARY IN 3 SENTENCES

**We need 2 UIs because community members and healthcare workers have completely different needs.** The mobile app focuses on simplicity and Kriol language support for symptom reporting, while the desktop app provides healthcare workers with data-rich monitoring and management tools. Together, they create a complete triage system that connects community members to appropriate care.

---

## FILES TO SHARE WITH CLIENT

📄 **WIREFRAME_DESIGN.md** - Detailed screen layouts
📄 **SYSTEM_ARCHITECTURE.md** - Technical overview
📄 **CLIENT_PRESENTATION.md** - Executive summary
📄 **IMPLEMENTATION_ROADMAP.md** - Development plan
📄 **UI_STYLE_GUIDE.md** - Design guidelines
📄 **This file (QUICK_ANSWERS.md)** - Quick reference

---

## CONTACT FOR QUESTIONS

[Your name and contact info here]

---

*Last updated: March 2026*
