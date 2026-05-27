package com.example.saca.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.saca.R
import com.example.saca.model.Language
import com.example.saca.ui.theme.OchreAccent
import com.example.saca.ui.theme.PrimaryBlue
import com.example.saca.ui.theme.TextSecondary
import com.example.saca.ui.theme.WarmClay

@Composable
fun LoadingScreen(
    language    : Language,
    usedRemote  : Boolean = false,
    progress    : Float   = 0f,
    statusText  : String  = ""
) {
    val headlineEN = "Processing your input"
    val headlineKR = "Wiken yu input"

    val subEN = if (usedRemote)
        "Analysing symptoms with full NLP pipeline..."
    else
        "Analysing symptoms on device..."
    val subKR = if (usedRemote)
        "Luk symptoms langa NLP pipeline..."
    else
        "Luk symptoms langa dis dibais..."

    val headline = if (language == Language.ENGLISH) headlineEN else headlineKR
    val subtitle = if (language == Language.ENGLISH) subEN      else subKR

    // Animated progress value
    val animatedProgress by animateFloatAsState(
        targetValue      = progress,
        animationSpec    = tween(durationMillis = 400, easing = FastOutSlowInEasing),
        label            = "progress"
    )

    // Pulsing S logo animation
    val pulse by rememberInfiniteTransition(label = "pulse").animateFloat(
        initialValue  = 1f,
        targetValue   = 1.08f,
        animationSpec = infiniteRepeatable(
            animation  = tween(800, easing = EaseInOut),
            repeatMode = RepeatMode.Reverse
        ),
        label = "logoPulse"
    )

    Box(modifier = Modifier.fillMaxSize()) {

        // Background
        Image(
            painter        = painterResource(id = R.drawable.saca_background),
            contentDescription = null,
            modifier       = Modifier.fillMaxSize(),
            contentScale   = ContentScale.Crop
        )
        Box(modifier = Modifier
            .fillMaxSize()
            .background(Color(0xEEF5F0EB)))

        Column(
            modifier            = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {

            // Pulsing S logo
            Surface(
                shape    = RoundedCornerShape(20.dp),
                color    = Color.Black,
                modifier = Modifier
                    .size(72.dp)
                    .scale(pulse)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Text(
                        text       = "S",
                        color      = Color.White,
                        fontSize   = 36.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            Spacer(modifier = Modifier.height(32.dp))

            Text(
                text       = headline,
                style      = MaterialTheme.typography.headlineSmall,
                color      = Color(0xFF1A1A1A),
                textAlign  = TextAlign.Center,
                modifier   = Modifier.padding(horizontal = 40.dp)
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text      = subtitle,
                style     = MaterialTheme.typography.bodyLarge,
                color     = TextSecondary,
                textAlign = TextAlign.Center,
                modifier  = Modifier.padding(horizontal = 40.dp)
            )

            Spacer(modifier = Modifier.height(40.dp))

            // Progress bar
            Column(
                modifier            = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 48.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                LinearProgressIndicator(
                    progress          = { animatedProgress },
                    modifier          = Modifier
                        .fillMaxWidth()
                        .height(8.dp),
                    color             = PrimaryBlue,
                    trackColor        = Color(0xFFE0DBD5),
                    strokeCap         = androidx.compose.ui.graphics.StrokeCap.Round,
                )

                Spacer(modifier = Modifier.height(12.dp))

                Text(
                    text  = "${(animatedProgress * 100).toInt()}%",
                    style = MaterialTheme.typography.labelMedium,
                    color = TextSecondary
                )
            }

            // Dynamic status message
            if (statusText.isNotEmpty()) {
                Spacer(modifier = Modifier.height(24.dp))
                Surface(
                    shape = RoundedCornerShape(50),
                    color = Color(0xFFFFF8F0),
                    modifier = Modifier.padding(horizontal = 40.dp)
                ) {
                    Row(
                        modifier          = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        // Dot indicator
                        Surface(
                            shape  = CircleShape,
                            color  = OchreAccent,
                            modifier = Modifier.size(8.dp)
                        ) {}
                        Text(
                            text  = statusText,
                            style = MaterialTheme.typography.labelMedium,
                            color = TextSecondary
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(48.dp))

            // Engine badge — shows which NLP ran
            Surface(
                shape = RoundedCornerShape(50),
                color = if (usedRemote)
                    PrimaryBlue.copy(alpha = 0.1f)
                else
                    OchreAccent.copy(alpha = 0.1f),
                modifier = Modifier.padding(horizontal = 40.dp)
            ) {
                Text(
                    text = if (usedRemote)
                        "🌐  Full NLP pipeline"
                    else
                        "📵  On-device analysis",
                    style    = MaterialTheme.typography.labelMedium,
                    color    = if (usedRemote) PrimaryBlue else OchreAccent,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                )
            }
        }
    }
}