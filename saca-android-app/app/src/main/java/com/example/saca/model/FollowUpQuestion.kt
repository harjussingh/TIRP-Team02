package com.example.saca.model

data class FollowUpQuestion(
    val id     : String,
    val textEN : String,
    val textKR : String,
    val options: List<FollowUpOption>
)

data class FollowUpOption(
    val valueEN: String,
    val valueKR: String
)