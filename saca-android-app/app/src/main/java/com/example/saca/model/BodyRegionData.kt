package com.example.saca.model

// ── Data types ────────────────────────────────────────────────────────────────

data class BodySymptom(
    val vocab: String,       // machine key, e.g. "chest_pain"
    val labelEN: String,
    val labelKR: String,
)

data class BodyRegionInfo(
    val labelEN: String,
    val labelKR: String,
    val emoji: String,
)

// ── Region → symptoms map (mirrors Windows BODY_REGION_SYMPTOMS) ──────────────

val BODY_REGION_SYMPTOMS: Map<String, List<BodySymptom>> = mapOf(

    "head" to listOf(
        BodySymptom("headache",        "Headache",        "Hedake"),
        BodySymptom("severe_headache", "Severe headache", "Brabli hedake"),
        BodySymptom("dizziness",       "Dizziness",       "Dizi"),
        BodySymptom("confusion",       "Confusion",       "Konfius"),
        BodySymptom("blurred_vision",  "Blurred vision",  "No si gud"),
        BodySymptom("ear_pain",        "Ear pain",        "Ia pein"),
        BodySymptom("eye_pain",        "Eye pain",        "Ai pein"),
        BodySymptom("runny_nose",      "Runny nose",      "Nos ron"),
        BodySymptom("facial_drooping", "Face drooping",   "Fes poldaun"),
    ),

    "throat" to listOf(
        BodySymptom("sore_throat",           "Sore throat",           "Throt pein"),
        BodySymptom("difficulty_swallowing", "Difficulty swallowing", "Had fo swalo"),
        BodySymptom("swollen_lymph_nodes",   "Swollen neck glands",   "Nek swelin"),
        BodySymptom("stiff_neck",            "Stiff neck",            "Nek tait"),
    ),

    "chest" to listOf(
        BodySymptom("chest_pain",           "Chest pain",           "Jes pein"),
        BodySymptom("severe_chest_pain",    "Severe chest pain",    "Brabli jes pein"),
        BodySymptom("chest_tightness",      "Chest tightness",      "Jes tait"),
        BodySymptom("shortness_of_breath",  "Shortness of breath",  "Short brith"),
        BodySymptom("difficulty_breathing", "Difficulty breathing", "Had fo brith"),
        BodySymptom("cough",                "Cough",                "Kof"),
        BodySymptom("productive_cough",     "Cough with mucus",     "Kof wit gris"),
        BodySymptom("wheezing",             "Wheezing",             "Wizing"),
        BodySymptom("palpitations",         "Heart racing",         "Hat rantawei"),
        BodySymptom("coughing_blood",       "Coughing blood",       "Kof blad"),
    ),

    "abdomen" to listOf(
        BodySymptom("abdominal_pain",        "Stomach pain",        "Beli pein"),
        BodySymptom("severe_abdominal_pain", "Severe stomach pain", "Brabli beli pein"),
        BodySymptom("nausea",               "Nausea",              "Fil laik spyu"),
        BodySymptom("vomiting",             "Vomiting",            "Spyu"),
        BodySymptom("vomiting_blood",       "Vomiting blood",      "Spyu blad"),
        BodySymptom("diarrhea",             "Diarrhea",            "Ranishit"),
        BodySymptom("bloating",             "Bloating",            "Beli big ap"),
        BodySymptom("loss_of_appetite",     "No appetite",         "No laik kakae"),
        BodySymptom("constipation",         "Constipation",        "Had fo pus"),
    ),

    "back" to listOf(
        BodySymptom("back_pain",        "Back pain",        "Bek pein"),
        BodySymptom("severe_back_pain", "Severe back pain", "Brabli bek pein"),
        BodySymptom("shoulder_pain",    "Shoulder pain",    "Sholda pein"),
    ),

    "left_arm" to listOf(
        BodySymptom("arm_pain",     "Arm pain",     "Aam pein"),
        BodySymptom("arm_weakness", "Arm weakness", "Aam wik"),
        BodySymptom("swelling",     "Swelling",     "Swelin"),
        BodySymptom("bruising",     "Bruising",     "Brus"),
    ),

    "right_arm" to listOf(
        BodySymptom("arm_pain",     "Arm pain",     "Aam pein"),
        BodySymptom("arm_weakness", "Arm weakness", "Aam wik"),
        BodySymptom("swelling",     "Swelling",     "Swelin"),
        BodySymptom("bruising",     "Bruising",     "Brus"),
    ),

    "left_leg" to listOf(
        BodySymptom("leg_pain",           "Leg pain",           "Leg pein"),
        BodySymptom("leg_swelling",       "Leg swelling",       "Leg swelin"),
        BodySymptom("ankle_swelling",     "Ankle swelling",     "Enkol swelin"),
        BodySymptom("difficulty_walking", "Difficulty walking", "Had fo wokabat"),
        BodySymptom("bruising",           "Bruising",           "Brus"),
    ),

    "right_leg" to listOf(
        BodySymptom("leg_pain",           "Leg pain",           "Leg pein"),
        BodySymptom("leg_swelling",       "Leg swelling",       "Leg swelin"),
        BodySymptom("ankle_swelling",     "Ankle swelling",     "Enkol swelin"),
        BodySymptom("difficulty_walking", "Difficulty walking", "Had fo wokabat"),
        BodySymptom("bruising",           "Bruising",           "Brus"),
    ),

    "whole_body" to listOf(
        BodySymptom("fever",       "Fever",       "Fiba"),
        BodySymptom("high_fever",  "High fever",  "Brabli fiba"),
        BodySymptom("fatigue",     "Fatigue",     "Brabli taid"),
        BodySymptom("body_aches",  "Body aches",  "Bodi pein"),
        BodySymptom("chills",      "Chills",      "Kolkol"),
        BodySymptom("sweating",    "Sweating",    "Swet"),
        BodySymptom("weakness",    "Weakness",    "Wik"),
        BodySymptom("rash",        "Rash",        "Skin trabul"),
        BodySymptom("itching",     "Itching",     "Isi isi"),
        BodySymptom("dehydration", "Dehydration", "No wota"),
    ),
)

// ── Region display metadata (mirrors Windows BODY_REGION_LABELS) ─────────────

val BODY_REGION_LABELS: Map<String, BodyRegionInfo> = mapOf(
    "head"       to BodyRegionInfo("Head",       "Hed",      "🧠"),
    "throat"     to BodyRegionInfo("Throat",     "Throt",    "🦷"),
    "chest"      to BodyRegionInfo("Chest",      "Jes",      "🫀"),
    "abdomen"    to BodyRegionInfo("Stomach",    "Beli",     "🫃"),
    "back"       to BodyRegionInfo("Back",       "Bek",      "🔙"),
    "left_arm"   to BodyRegionInfo("Left arm",   "Lef aam",  "💪"),
    "right_arm"  to BodyRegionInfo("Right arm",  "Rait aam", "💪"),
    "left_leg"   to BodyRegionInfo("Left leg",   "Lef leg",  "🦵"),
    "right_leg"  to BodyRegionInfo("Right leg",  "Rait leg", "🦵"),
    "whole_body" to BodyRegionInfo("Whole body", "Ol bodi",  "🌡"),
)

// Ordered list for zone buttons (excludes whole_body which has its own button)
val BODY_ZONE_KEYS = listOf(
    "head", "throat", "chest", "abdomen", "back",
    "left_arm", "right_arm", "left_leg", "right_leg",
)

// ── Helper: resolve English or Kriol label for a vocab key ───────────────────

fun BodySymptom.label(isKriol: Boolean) = if (isKriol) labelKR else labelEN
fun BodyRegionInfo.title(isKriol: Boolean) = if (isKriol) labelKR else labelEN