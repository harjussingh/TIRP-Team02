package com.example.saca.nlp

import com.example.saca.model.FollowUpOption
import com.example.saca.model.FollowUpQuestion

object QuestionRepository {

    // ── General questions — always asked first ────────────────────────────
    private val generalQuestions = listOf(
        FollowUpQuestion(
            id      = "when_started",
            textEN  = "How long has this been happening?",
            textKR  = "Hau long yu bin garr diswan?",
            options = listOf(
                FollowUpOption("Today",        "Tudei"),
                FollowUpOption("A few days",   "2-3 dei"),
                FollowUpOption("A week+",      "Planti dei")
            )
        ),
        FollowUpQuestion(
            id      = "getting_worse",
            textEN  = "Is it getting worse?",
            textKR  = "Im kam moa nogud?",
            options = listOf(
                FollowUpOption("Yes",      "Yuwai"),
                FollowUpOption("No",       "Nomo"),
                FollowUpOption("Not sure", "Nomo shua")
            )
        )
    )

    // ── Symptom-specific questions — mirrors QUESTION_BANK ────────────────
    private val questionBank = mapOf(
        "fever" to listOf(
            FollowUpQuestion("fever_now",        "Do you still have fever?",      "Yu stil garr fiba nau?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("fever_cough",      "Do you have cough too?",        "Yu garr kof tu?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("fever_rash",       "Do you have a rash too?",       "Yu garr rash tu?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("fever_drink_water","Can you drink water?",          "Yu ken dringgim woda?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo")))
        ),
        "cough" to listOf(
            FollowUpQuestion("cough_type",      "Is the cough dry or wet?",      "Kof im drai o wet?",
                listOf(FollowUpOption("Dry","Drai"), FollowUpOption("Wet","Wet"))),
            FollowUpQuestion("cough_breathing", "Hard to breathe?",              "Im ad fo brith?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("cough_fever",     "Do you have fever too?",        "Yu garr fiba tu?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("cough_days",      "How many days have you had the cough?", "Haumeni dei yu bin garr kof?",
                listOf(FollowUpOption("1-2","1-2"), FollowUpOption("3-5","3-5"), FollowUpOption("More than 5","Moa than 5")))
        ),
        "difficulty_breathing" to listOf(
            FollowUpQuestion("breathing_now",        "Hard to breathe right now?",    "Im ad fo brith nau?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("breathing_chest_pain", "Do you have chest pain too?",   "Yu garr jes pein tu?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("breathing_worse",      "Is breathing getting worse?",   "Brithin i kam moa nogud?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo")))
        ),
        "chest_pain" to listOf(
            FollowUpQuestion("chest_pain_now",       "Do you have chest pain right now?", "Yu garr jes pein nau?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("chest_pain_breathing", "Hard to breathe?",                 "Im ad fo brith?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("chest_pain_sudden",    "Did the pain start suddenly?",      "Pein bin stat kwikwan?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo")))
        ),
        "headache" to listOf(
            FollowUpQuestion("headache_strong",   "Is the headache very bad?",     "Hedake im strongbala?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("headache_vomiting", "Do you feel sick or vomit?",    "Yu fil sik o spyu?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("headache_light",    "Does bright light bother you?", "Lait i wori yu?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("headache_fever",    "Do you also have fever?",       "Yu garr fiba tu?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo")))
        ),
        "stomach_pain" to listOf(
            FollowUpQuestion("stomach_pain_now",    "Do you have stomach pain right now?", "Yu garr beli pein nau?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("stomach_vomiting",    "Are you vomiting?",                  "Yu spyu?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("stomach_fever",       "Do you have fever too?",              "Yu garr fiba tu?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo")))
        ),
        "vomiting" to listOf(
            FollowUpQuestion("vomiting_today",        "How many times did you vomit today?", "Haumeni taim yu bin spyu tudei?",
                listOf(FollowUpOption("1-2","1-2"), FollowUpOption("3-5","3-5"), FollowUpOption("More than 5","Moa than 5"))),
            FollowUpQuestion("vomiting_keep_water",   "Can you keep water down?",             "Yu ken kipim woda daun?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("vomiting_stomach_pain", "Do you have stomach pain too?",        "Yu garr beli pein tu?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo")))
        ),
        "diarrhea" to listOf(
            FollowUpQuestion("diarrhea_today",        "How many times today?",       "Haumeni taim tudei?",
                listOf(FollowUpOption("1-2","1-2"), FollowUpOption("3-5","3-5"), FollowUpOption("More than 5","Moa than 5"))),
            FollowUpQuestion("diarrhea_water",        "Can you drink water?",        "Yu ken dringgim woda?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("diarrhea_stomach_pain", "Do you have stomach pain?",   "Yu garr beli pein tu?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo")))
        ),
        "rash" to listOf(
            FollowUpQuestion("rash_itchy",    "Is the rash itchy?",    "Rash i itji?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("rash_spreading","Is it spreading?",      "Im spredin?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("rash_fever",    "Do you have fever too?","Yu garr fiba tu?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo")))
        ),
        "sore_throat" to listOf(
            FollowUpQuestion("throat_swallow","Is it hard to swallow?",    "Im ad fo swalow?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("throat_fever",  "Do you also have fever?",   "Yu garr fiba tu?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo"))),
            FollowUpQuestion("throat_cough",  "Do you also have cough?",   "Yu garr kof tu?",
                listOf(FollowUpOption("Yes","Yuwai"), FollowUpOption("No","Nomo")))
        )
    )

    /**
     * Mirrors Python's select_followup_questions()
     * Always includes general questions first, then symptom-specific ones
     */
    fun selectQuestions(
        symptoms    : List<String>,
        maxQuestions: Int = 5
    ): List<FollowUpQuestion> {
        val selected = mutableListOf<FollowUpQuestion>()
        val seenIds  = mutableSetOf<String>()

        // General questions first
        for (q in generalQuestions) {
            if (q.id !in seenIds && selected.size < maxQuestions) {
                selected.add(q)
                seenIds.add(q.id)
            }
        }

        // Symptom-specific questions
        for (symptom in symptoms) {
            for (q in (questionBank[symptom] ?: emptyList())) {
                if (q.id !in seenIds && selected.size < maxQuestions) {
                    selected.add(q)
                    seenIds.add(q.id)
                }
            }
        }

        return selected
    }
}