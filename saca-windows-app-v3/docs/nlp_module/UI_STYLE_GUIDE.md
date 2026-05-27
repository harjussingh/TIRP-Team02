# Quick Reference: Screen Layouts

## Mobile App - Screen Flow

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       v
┌─────────────────────┐
│  LANGUAGE SELECT    │  → User chooses Kriol or English
│  [Kriol] [English]  │
└──────┬──────────────┘
       │
       v
┌──────────────────────────┐
│   SYMPTOM INPUT          │  → Voice or text input
│   🎤 [Speak]             │
│   ⌨️  [Type]              │
│   [Quick buttons]        │
└──────┬───────────────────┘
       │
       v
┌──────────────────────────┐
│   PROCESSING             │  → Shows progress
│   ⏳ Analyzing...         │
└──────┬───────────────────┘
       │
       v
┌──────────────────────────┐
│   RESULTS                │  → Shows severity + actions
│   🟡 Moderate             │
│   📋 Recommendations      │
│   [Call] [Save] [Home]   │
└──────┬───────────────────┘
       │
       v (if urgent)
┌──────────────────────────┐
│   EMERGENCY ALERT        │  → Red screen with call button
│   🚨 URGENT              │
│   [📞 CALL 000]          │
└──────────────────────────┘
```

## Desktop App - Main Navigation

```
┌─────────────────────────────────────────────────────────────┐
│ SACA Dashboard                           [User] [Logout]    │
├─────────────────────────────────────────────────────────────┤
│ [Dashboard] [Queue] [Patients] [Analytics] [Settings]       │
└─────────────────────────────────────────────────────────────┘
        │         │         │           │           │
        │         │         │           │           └─> User/System config
        │         │         │           └─> Reports & trends
        │         │         └─> Patient history & search
        │         └─> Priority queue (sorted by urgency)
        └─> Overview stats & recent submissions
```

## Color Coding System

### Severity Levels (Used in both apps):

```
🟢 LEVEL 1 - LOW
   Self-care at home
   No urgent action needed
   Examples: Mild headache, minor ache

🟡 LEVEL 2 - MODERATE
   Visit clinic within 24-48 hours
   Monitor symptoms
   Examples: Persistent fever, cough

🟠 LEVEL 3 - HIGH
   Visit clinic TODAY
   Potentially serious
   Examples: High fever + multiple symptoms

🔴 LEVEL 4 - URGENT
   Emergency care needed NOW
   Call 000 or go to ED
   Examples: Chest pain, severe breathing difficulty

⚫ LEVEL 5 - CRITICAL
   Life-threatening
   Immediate emergency response
   Examples: Unconscious, severe trauma
```

## Icon Legend

### Mobile App Icons:
- 🎤 = Voice input
- ⌨️ = Text input
- 📞 = Call/Phone
- 💾 = Save
- 🏠 = Home
- 📜 = History
- 🗣️ = Language
- ❓ = Help
- ⚙️ = Settings
- 🔄 = Refresh/New

### Desktop App Icons:
- 📊 = Dashboard/Analytics
- 👤 = Patient/User
- 📋 = Queue/List
- 🔍 = Search
- 📄 = Report/Document
- 📤 = Export
- ✓ = Complete/Resolved
- ⏰ = Pending/Waiting
- 🔔 = Notification/Alert
- ⚠️ = Warning/Urgent

## Typography Scale

### Mobile:
- Heading 1: 28pt, Bold
- Heading 2: 22pt, Semibold
- Body: 18pt, Regular
- Small: 14pt, Regular
- Button: 20pt, Bold

### Desktop:
- Heading 1: 32pt, Bold
- Heading 2: 24pt, Semibold
- Heading 3: 18pt, Semibold
- Body: 16pt, Regular
- Small: 13pt, Regular

## Spacing & Layout

### Mobile:
- Screen padding: 20px
- Button height: 60px
- Button spacing: 16px
- Card margin: 16px
- Icon size: 48x48px

### Desktop:
- Container padding: 32px
- Sidebar width: 260px
- Card spacing: 24px
- Button height: 44px
- Icon size: 32x32px

## Sample Color Palette

```
Primary Colors:
  - Main: #D4691B (Ochre/Orange)
  - Dark: #8B4513 (Saddle Brown)
  - Light: #F4A460 (Sandy Brown)

Severity Colors:
  - Low: #4CAF50 (Green)
  - Moderate: #FFC107 (Amber)
  - High: #FF9800 (Orange)
  - Urgent: #F44336 (Red)
  - Critical: #D32F2F (Dark Red)

Neutral Colors:
  - Background: #F5F5F5 (Light Grey)
  - Surface: #FFFFFF (White)
  - Text: #212121 (Almost Black)
  - Text Secondary: #757575 (Grey)
  - Border: #E0E0E0 (Light Border)

Semantic Colors:
  - Success: #4CAF50
  - Error: #F44336
  - Warning: #FF9800
  - Info: #2196F3
```

## Button States

### Primary Button:
```
Normal:   [Ochre background, white text]
Hover:    [Darker ochre, white text, subtle shadow]
Active:   [Even darker, pressed effect]
Disabled: [Grey background, light grey text]
```

### Secondary Button:
```
Normal:   [White background, ochre border, ochre text]
Hover:    [Light ochre background, ochre text]
Active:   [Slightly darker background]
Disabled: [Grey border, light grey text]
```

### Emergency Button:
```
Normal:   [Red background, white text, large]
Hover:    [Darker red, glow effect]
Active:   [Very dark red, pulse animation]
```

## Accessibility Features

### Must-Haves:
✓ Voice input (speech-to-text)
✓ Text-to-speech (read results aloud)
✓ High contrast mode
✓ Large touch targets (60x60px minimum)
✓ Screen reader support
✓ Keyboard navigation (desktop)
✓ Focus indicators
✓ Alt text for all images
✓ ARIA labels

### Cultural Considerations:
✓ Avoid direct eye contact in images (culturally sensitive)
✓ Use community-approved imagery
✓ Earth tone colors (not harsh blues/cold colors)
✓ Consider right-to-left languages if needed
✓ Culturally appropriate icons

## Responsive Breakpoints (Desktop)

```
Extra Large: ≥1920px (Large monitors)
  - 3 columns
  - Expanded sidebar

Large: 1440px - 1919px (Desktop)
  - 2-3 columns
  - Full sidebar

Medium: 1024px - 1439px (Small desktop/tablet landscape)
  - 2 columns
  - Collapsible sidebar

Small: 768px - 1023px (Tablet portrait)
  - 1 column
  - Bottom navigation

Mobile: <768px
  - Use mobile app instead
```

## Animation Guidelines

### Transitions:
- Screen changes: 300ms ease-in-out
- Button press: 100ms ease
- Modal open: 200ms ease-out
- Loading spinner: continuous rotation

### Feedback:
- Button tap: Quick scale (95% → 100%)
- Success action: Check mark animation
- Error: Shake animation (3-5px, 3 times)
- Loading: Spinner or progress bar

## Error Messages

### User-Friendly Format:

Instead of:
❌ "Error 500: Internal Server Error"

Show:
✅ "Something went wrong. Please try again."
   [Try Again] [Contact Support]

### Bilingual Errors:

English:
"We couldn't understand that. Please try again."

Kriol:
"Wi no savvy det wan. Plij trai gen."

