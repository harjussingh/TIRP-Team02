from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)


class AppLogo(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("homeAppLogo")
        self.setFixedSize(58, 58)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#2D1810"))
        painter.drawRoundedRect(self.rect(), 15, 15)

        painter.setPen(QColor("#FFFFFF"))
        font = QFont()
        font.setPointSize(23)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "S")


class HomeAccentLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("homeAccentLine")
        self.setFixedSize(52, 3)


class AnimatedCard(QFrame):
    clicked = Signal()

    def __init__(self):
        super().__init__()

        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("hovered", False)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(14)
        self.shadow.setOffset(0, 5)
        self.shadow.setColor(QColor(45, 24, 16, 28))
        self.setGraphicsEffect(self.shadow)

        self.blur_anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.blur_anim.setDuration(180)
        self.blur_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.offset_anim = QPropertyAnimation(self.shadow, b"yOffset")
        self.offset_anim.setDuration(180)
        self.offset_anim.setEasingCurve(QEasingCurve.OutCubic)

    def enterEvent(self, event):
        self.setProperty("hovered", True)
        self.style().unpolish(self)
        self.style().polish(self)

        self.blur_anim.stop()
        self.blur_anim.setStartValue(self.shadow.blurRadius())
        self.blur_anim.setEndValue(30)
        self.blur_anim.start()

        self.offset_anim.stop()
        self.offset_anim.setStartValue(self.shadow.yOffset())
        self.offset_anim.setEndValue(12)
        self.offset_anim.start()

        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setProperty("hovered", False)
        self.style().unpolish(self)
        self.style().polish(self)

        self.blur_anim.stop()
        self.blur_anim.setStartValue(self.shadow.blurRadius())
        self.blur_anim.setEndValue(14)
        self.blur_anim.start()

        self.offset_anim.stop()
        self.offset_anim.setStartValue(self.shadow.yOffset())
        self.offset_anim.setEndValue(5)
        self.offset_anim.start()

        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

        super().mousePressEvent(event)


class LanguageCard(AnimatedCard):
    def __init__(
        self,
        badge_text: str,
        title: str,
        subtitle: str,
        action_text: str,
        badge_object_name: str,
        action_object_name: str,
    ):
        super().__init__()

        self.setObjectName("homeLanguageCard")
        self.setFixedSize(360, 240)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(34, 34, 34, 28)
        root.setSpacing(0)

        self.badge = QLabel(badge_text)
        self.badge.setObjectName(badge_object_name)
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setFixedSize(62, 62)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("homeLanguageCardTitle")

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("homeLanguageCardSubtitle")

        self.action_label = QLabel(f"{action_text}   →")
        self.action_label.setObjectName(action_object_name)

        root.addWidget(self.badge, 0, Qt.AlignLeft)
        root.addStretch()
        root.addWidget(self.title_label)
        root.addSpacing(8)
        root.addWidget(self.subtitle_label)
        root.addStretch()
        root.addWidget(self.action_label)

    def set_content(self, title: str, subtitle: str, action_text: str):
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)
        self.action_label.setText(f"{action_text}   →")


class IconBox(QFrame):
    def __init__(self, icon_type: str, object_name: str):
        super().__init__()
        self.icon_type = icon_type
        self.setObjectName(object_name)
        self.setFixedSize(72, 72)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.icon_type == "mic":
            pen = QPen(QColor("#2F6F55"), 4)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(28, 15, 16, 30, 8, 8)
            painter.drawArc(20, 24, 32, 34, 200 * 16, 140 * 16)
            painter.drawLine(36, 55, 36, 62)
            painter.drawLine(28, 62, 44, 62)

        elif self.icon_type == "picture":
            pen = QPen(QColor("#0052A3"), 4)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(19, 18, 34, 34, 4, 4)
            painter.drawEllipse(26, 25, 7, 7)
            painter.drawLine(22, 48, 34, 36)
            painter.drawLine(34, 36, 42, 43)
            painter.drawLine(42, 43, 51, 34)

        elif self.icon_type == "type":
            painter.setPen(QColor("#8B5A2B"))
            font = QFont()
            font.setPointSize(30)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "T")


class ModeCard(AnimatedCard):
    def __init__(self, icon_type: str, title: str, subtitle: str, icon_box_name: str):
        super().__init__()

        self.setObjectName("modeCard")
        self.setFixedSize(720, 112)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(18)

        self.icon_box = IconBox(icon_type, icon_box_name)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.setAlignment(Qt.AlignVCenter)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("modeCardTitle")
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("modeCardSubtitle")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.arrow_label = QLabel("›")
        self.arrow_label.setObjectName("modeCardArrow")
        self.arrow_label.setAlignment(Qt.AlignCenter)
        self.arrow_label.setFixedWidth(32)
        self.arrow_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        text_col.addWidget(self.title_label)
        text_col.addWidget(self.subtitle_label)

        root.addWidget(self.icon_box, 0, Qt.AlignVCenter)
        root.addLayout(text_col, 1)
        root.addWidget(self.arrow_label, 0, Qt.AlignVCenter)

    def set_content(self, icon_type: str, title: str, subtitle: str):
        self.icon_box.icon_type = icon_type
        self.icon_box.update()
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)


class HomePage(QWidget):
    speak_clicked = Signal()
    type_clicked = Signal()
    pictures_clicked = Signal()
    emergency_clicked = Signal()
    language_changed = Signal(str)

    def __init__(self):
        super().__init__()

        self.strings = {}
        self.current_language = "en"

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setObjectName("homeStack")
        root.addWidget(self.stack)

        self.language_screen = self._build_language_screen()
        self.mode_screen = self._build_mode_screen()

        self.stack.addWidget(self.language_screen)
        self.stack.addWidget(self.mode_screen)
        self.stack.setCurrentWidget(self.language_screen)

    # --------------------------------------------------
    # Language screen — Figma style
    # --------------------------------------------------
    def _build_language_screen(self):
        page = QWidget()
        page.setObjectName("homeLanguagePage")

        outer = QHBoxLayout(page)
        outer.setContentsMargins(128, 72, 80, 54)
        outer.setSpacing(0)

        content = QWidget()
        content.setObjectName("homeWelcomeContent")
        content.setMaximumWidth(860)
        content.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)

        # Brand row
        brand_row = QHBoxLayout()
        brand_row.setSpacing(18)

        self.logo = AppLogo()

        brand_text_col = QVBoxLayout()
        brand_text_col.setSpacing(2)

        self.brand_title = QLabel("SACA · TRIAGE")
        self.brand_title.setObjectName("homeBrandTitle")

        self.brand_subtitle = QLabel("NGUKURR COMMUNITY")
        self.brand_subtitle.setObjectName("homeBrandSubtitle")

        brand_text_col.addWidget(self.brand_title)
        brand_text_col.addWidget(self.brand_subtitle)

        brand_row.addWidget(self.logo, 0, Qt.AlignTop)
        brand_row.addLayout(brand_text_col)
        brand_row.addStretch()

        self.accent_line = HomeAccentLine()

        self.welcome_title = QLabel("Welkom")
        self.welcome_title.setObjectName("homeWelcomeTitle")

        self.choose_language_label = QLabel("Choose your language")
        self.choose_language_label.setObjectName("homeChooseLanguage")

        self.choose_language_kriol_label = QLabel("Jus yu langgus")
        self.choose_language_kriol_label.setObjectName("homeChooseLanguageKriol")

        # Cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(24)

        self.english_card = LanguageCard(
            badge_text="EN",
            title="English",
            subtitle="Speak in English",
            action_text="Select",
            badge_object_name="languageBadgeEn",
            action_object_name="languageActionBlue",
        )

        self.kriol_card = LanguageCard(
            badge_text="KR",
            title="Kriol",
            subtitle="Tok langa Kriol",
            action_text="Pikimup",
            badge_object_name="languageBadgeKr",
            action_object_name="languageActionOchre",
        )

        self.english_card.clicked.connect(lambda: self._select_language("en"))
        self.kriol_card.clicked.connect(lambda: self._select_language("kriol"))

        cards_row.addWidget(self.english_card)
        cards_row.addWidget(self.kriol_card)
        cards_row.addStretch()

        self.emergency_btn = QPushButton("ⓘ  Emergency Help    / Emajncy Help")
        self.emergency_btn.setObjectName("homeEmergencyOutlineButton")
        self.emergency_btn.setCursor(Qt.PointingHandCursor)
        self.emergency_btn.setFixedSize(360, 62)
        self.emergency_btn.clicked.connect(self.emergency_clicked.emit)

        layout.addLayout(brand_row)
        layout.addSpacing(36)
        layout.addWidget(self.accent_line, 0, Qt.AlignLeft)
        layout.addSpacing(50)
        layout.addWidget(self.welcome_title)
        layout.addSpacing(36)
        layout.addWidget(self.choose_language_label)
        layout.addSpacing(14)
        layout.addWidget(self.choose_language_kriol_label)
        layout.addSpacing(72)
        layout.addLayout(cards_row)
        layout.addSpacing(46)
        layout.addWidget(self.emergency_btn)
        layout.addStretch()

        outer.addWidget(content, 0, Qt.AlignLeft | Qt.AlignTop)
        outer.addStretch()

        return page

    # --------------------------------------------------
    # Input mode screen
    # --------------------------------------------------
    def _build_mode_screen(self):
        page = QWidget()
        page.setObjectName("homeModePage")

        outer = QHBoxLayout(page)
        outer.setContentsMargins(128, 52, 80, 44)
        outer.setSpacing(0)

        content = QWidget()
        content.setObjectName("homeModeContent")
        content.setMaximumWidth(820)
        content.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)

        self.back_btn = QPushButton("‹ Back")
        self.back_btn.setObjectName("backLinkButton")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self._go_to_language_screen)

        self.title_label = QLabel("How are you feeling?")
        self.title_label.setObjectName("modePageTitle")

        self.subtitle_1 = QLabel("Tell us what is wrong.")
        self.subtitle_1.setObjectName("modePageSubtitle")

        self.subtitle_2 = QLabel("Choose the easiest way for you.")
        self.subtitle_2.setObjectName("modePageSubtitle")

        self.speak_card = ModeCard(
            "mic",
            "Speak",
            "Talk and we will listen",
            "speakIconBox",
        )

        self.picture_card = ModeCard(
            "picture",
            "Pictures",
            "Show us where it hurts",
            "pictureIconBox",
        )

        self.type_card = ModeCard(
            "type",
            "Type",
            "Write what you feel",
            "typeIconBox",
        )

        self.speak_card.clicked.connect(self.speak_clicked.emit)
        self.picture_card.clicked.connect(self.pictures_clicked.emit)
        self.type_card.clicked.connect(self.type_clicked.emit)

        self.mode_emergency_btn = QPushButton("ⓘ  Emergency Help")
        self.mode_emergency_btn.setObjectName("homeEmergencySolidButton")
        self.mode_emergency_btn.setFixedSize(330, 66)
        self.mode_emergency_btn.setCursor(Qt.PointingHandCursor)
        self.mode_emergency_btn.clicked.connect(self.emergency_clicked.emit)

        layout.addWidget(self.back_btn, 0, Qt.AlignLeft)
        layout.addSpacing(50)
        layout.addWidget(self.title_label)
        layout.addSpacing(18)
        layout.addWidget(self.subtitle_1)
        layout.addSpacing(10)
        layout.addWidget(self.subtitle_2)
        layout.addSpacing(54)
        layout.addWidget(self.speak_card)
        layout.addSpacing(22)
        layout.addWidget(self.picture_card)
        layout.addSpacing(22)
        layout.addWidget(self.type_card)
        layout.addSpacing(44)
        layout.addWidget(self.mode_emergency_btn, 0, Qt.AlignLeft)
        layout.addStretch()

        outer.addWidget(content, 0, Qt.AlignLeft | Qt.AlignTop)
        outer.addStretch()

        return page

    # --------------------------------------------------
    # Actions
    # --------------------------------------------------
    def _select_language(self, code: str):
        self.current_language = code
        self.language_changed.emit(code)
        self.stack.setCurrentWidget(self.mode_screen)

    def _go_to_language_screen(self):
        self.stack.setCurrentWidget(self.language_screen)

    def show_mode_screen(self):
        self.stack.setCurrentWidget(self.mode_screen)

    def show_language_screen(self):
        self.stack.setCurrentWidget(self.language_screen)

    # --------------------------------------------------
    # Language text update
    # --------------------------------------------------
    def set_strings(self, s: dict):
        self.strings = s or {}
        is_kriol = self.current_language == "kriol"

        # Keep welcome screen bilingual like your Figma
        self.welcome_title.setText("Welkom")
        self.choose_language_label.setText("Choose your language")
        self.choose_language_kriol_label.setText("Jus yu langgus")

        self.english_card.set_content(
            title="English",
            subtitle="Speak in English",
            action_text="Select",
        )

        self.kriol_card.set_content(
            title="Kriol",
            subtitle="Tok langa Kriol",
            action_text="Pikimup",
        )

        self.emergency_btn.setText("ⓘ  Emergency Help    / Emajncy Help")

        self.back_btn.setText(
            "‹ Bek" if is_kriol else "‹ Back"
        )

        self.title_label.setText(
            "Yu fil wanem?" if is_kriol else "How are you feeling?"
        )

        self.subtitle_1.setText(
            "Telim mipala wetin rong." if is_kriol else "Tell us what is wrong."
        )

        self.subtitle_2.setText(
            "Jusum isiwei fo yu." if is_kriol else "Choose the easiest way for you."
        )

        self.speak_card.set_content(
            "mic",
            "Tok" if is_kriol else "Speak",
            "Tok en wi garra lisin." if is_kriol else "Talk and we will listen",
        )

        self.picture_card.set_content(
            "picture",
            "Pikja" if is_kriol else "Pictures",
            "So mibala wea im pein." if is_kriol else "Show us where it hurts",
        )

        self.type_card.set_content(
            "type",
            "Raidim" if is_kriol else "Type",
            "Raidim wei yu fil." if is_kriol else "Write what you feel",
        )

        self.mode_emergency_btn.setText(
            "ⓘ  Imijensi Elp" if is_kriol else "ⓘ  Emergency Help"
        )