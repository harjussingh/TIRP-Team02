package com.example.saca.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.translate
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

// ── Canonical canvas dimensions (matches Windows 200×400) ────────────────────
private const val CW = 200f
private const val CH = 400f

// ── Skin / UI colours ─────────────────────────────────────────────────────────
private val SkinFill      = Color(0xFFF2DDD0)
private val SkinOutline   = Color(0xFFA06858)
private val ActiveOverlay = Color(0xFFC4614A).copy(alpha = 0.39f)
private val HoverOverlay  = Color(0xFF8B3A2E).copy(alpha = 0.57f)
private val DetailLine    = Color(0xFFA06C55).copy(alpha = 0.35f)
private val ShadowColor   = Color(0xFF3C140A).copy(alpha = 0.11f)

// ── Build the full-body silhouette path (identical control points to Python) ──
private fun buildSilhouette(): Path {
    // Head
    val head = Path().apply {
        addOval(Rect(center = Offset(100f, 27f), radius = 19f))   // rx=19 ry=23
        // Compose addOval is a circle; use ellipse via moveTo+cubicTo for accurate oval
    }
    // Proper head oval
    val headOval = Path().apply {
        val cx = 100f; val cy = 27f; val rx = 19f; val ry = 23f
        val k = 0.5523f
        moveTo(cx, cy - ry)
        cubicTo(cx + rx * k, cy - ry, cx + rx, cy - ry * k, cx + rx, cy)
        cubicTo(cx + rx, cy + ry * k, cx + rx * k, cy + ry, cx, cy + ry)
        cubicTo(cx - rx * k, cy + ry, cx - rx, cy + ry * k, cx - rx, cy)
        cubicTo(cx - rx, cy - ry * k, cx - rx * k, cy - ry, cx, cy - ry)
        close()
    }
    // Left ear bump
    val le = Path().apply {
        val cx = 81f; val cy = 29f; val rx = 3.5f; val ry = 5.5f
        val k = 0.5523f
        moveTo(cx, cy - ry)
        cubicTo(cx + rx * k, cy - ry, cx + rx, cy - ry * k, cx + rx, cy)
        cubicTo(cx + rx, cy + ry * k, cx + rx * k, cy + ry, cx, cy + ry)
        cubicTo(cx - rx * k, cy + ry, cx - rx, cy + ry * k, cx - rx, cy)
        cubicTo(cx - rx, cy - ry * k, cx - rx * k, cy - ry, cx, cy - ry)
        close()
    }
    // Right ear bump
    val re = Path().apply {
        val cx = 119f; val cy = 29f; val rx = 3.5f; val ry = 5.5f
        val k = 0.5523f
        moveTo(cx, cy - ry)
        cubicTo(cx + rx * k, cy - ry, cx + rx, cy - ry * k, cx + rx, cy)
        cubicTo(cx + rx, cy + ry * k, cx + rx * k, cy + ry, cx, cy + ry)
        cubicTo(cx - rx * k, cy + ry, cx - rx, cy + ry * k, cx - rx, cy)
        cubicTo(cx - rx, cy - ry * k, cx - rx * k, cy - ry, cx, cy - ry)
        close()
    }

    // Full body (exact control points from Windows)
    val body = Path().apply {
        moveTo(91f, 50f)
        // left shoulder sweep
        cubicTo(80f, 50f, 46f, 60f, 33f, 70f)
        cubicTo(28f, 74f, 26f, 80f, 26f, 88f)
        // left outer arm
        cubicTo(24f, 110f, 22f, 148f, 24f, 186f)
        cubicTo(24f, 196f, 24f, 206f, 26f, 212f)
        // left wrist
        cubicTo(26f, 218f, 30f, 222f, 36f, 222f)
        cubicTo(42f, 222f, 46f, 222f, 48f, 222f)
        cubicTo(52f, 222f, 54f, 218f, 54f, 212f)
        // left inner arm going up
        cubicTo(54f, 202f, 52f, 162f, 50f, 124f)
        cubicTo(50f, 102f, 52f, 88f, 58f, 80f)
        // left armpit corner
        cubicTo(60f, 78f, 64f, 76f, 67f, 76f)
        // left torso: chest → waist → hip
        cubicTo(65f, 100f, 63f, 136f, 62f, 162f)
        cubicTo(61f, 182f, 59f, 200f, 57f, 212f)
        cubicTo(56f, 220f, 54f, 226f, 53f, 232f)
        // left outer leg
        cubicTo(49f, 252f, 45f, 290f, 43f, 322f)
        cubicTo(41f, 350f, 42f, 366f, 43f, 374f)
        // left foot
        cubicTo(43f, 382f, 47f, 390f, 54f, 392f)
        cubicTo(62f, 394f, 70f, 394f, 78f, 394f)
        cubicTo(85f, 394f, 88f, 390f, 88f, 382f)
        // left inner leg going up
        cubicTo(87f, 366f, 85f, 348f, 84f, 318f)
        cubicTo(83f, 285f, 83f, 258f, 86f, 242f)
        // crotch
        cubicTo(88f, 234f, 93f, 230f, 100f, 230f)
        cubicTo(107f, 230f, 112f, 234f, 114f, 242f)
        // right inner leg going down
        cubicTo(117f, 258f, 117f, 285f, 116f, 318f)
        cubicTo(115f, 348f, 113f, 366f, 112f, 382f)
        // right foot
        cubicTo(112f, 390f, 115f, 394f, 122f, 394f)
        cubicTo(130f, 394f, 138f, 394f, 146f, 392f)
        cubicTo(153f, 390f, 157f, 382f, 157f, 374f)
        // right outer leg going up
        cubicTo(158f, 366f, 159f, 350f, 157f, 322f)
        cubicTo(155f, 290f, 151f, 252f, 147f, 232f)
        // right torso: hip → waist → chest
        cubicTo(146f, 226f, 144f, 220f, 143f, 212f)
        cubicTo(141f, 200f, 139f, 182f, 138f, 162f)
        cubicTo(137f, 136f, 135f, 100f, 133f, 76f)
        // right armpit corner
        cubicTo(136f, 76f, 140f, 78f, 142f, 80f)
        // right inner arm going down
        cubicTo(148f, 88f, 150f, 102f, 150f, 124f)
        cubicTo(148f, 162f, 146f, 202f, 146f, 212f)
        // right wrist
        cubicTo(146f, 218f, 148f, 222f, 152f, 222f)
        cubicTo(158f, 222f, 164f, 222f, 166f, 222f)
        cubicTo(170f, 222f, 174f, 218f, 174f, 212f)
        // right outer arm going up
        cubicTo(176f, 206f, 176f, 196f, 176f, 186f)
        cubicTo(178f, 148f, 176f, 110f, 174f, 88f)
        cubicTo(174f, 80f, 172f, 74f, 167f, 70f)
        // right shoulder back to right neck
        cubicTo(154f, 60f, 120f, 50f, 109f, 50f)
        close()
    }

    // Unite all parts
    val result = Path()
    result.op(headOval, body, PathOperation.Union)
    result.op(result, le, PathOperation.Union)
    result.op(result, re, PathOperation.Union)
    return result
}

// ── Build clipped zone paths ──────────────────────────────────────────────────
private fun buildZonePaths(silhouette: Path): Map<String, Path> {
    fun clip(x: Float, y: Float, w: Float, h: Float): Path {
        val box = Path().apply { addRect(Rect(x, y, x + w, y + h)) }
        val result = Path()
        result.op(box, silhouette, PathOperation.Intersect)
        return result
    }
    return mapOf(
        "head"       to clip(81f,   4f, 38f,  46f),
        "throat"     to clip(88f,  50f, 24f,  28f),
        "chest"      to clip(62f,  78f, 76f,  86f),
        "abdomen"    to clip(57f, 164f, 86f,  68f),
        "left_arm"   to clip(22f,  76f, 48f, 150f),
        "right_arm"  to clip(130f, 76f, 48f, 150f),
        "left_leg"   to clip(43f, 232f, 50f, 164f),
        "right_leg"  to clip(107f,232f, 50f, 164f),
    )
}

// ── Hit test: which region contains a point? ─────────────────────────────────
private fun regionAt(
    x: Float, y: Float,
    scale: Float,
    offsetX: Float,
    offsetY: Float,
    zonePaths: Map<String, Path>,
): String? {
    // Convert screen coords → canvas coords
    val cx = (x - offsetX) / scale
    val cy = (y - offsetY) / scale
    val point = Offset(cx, cy)
    for ((region, path) in zonePaths) {
        if (path.contains(point)) return region
    }
    return null
}

// Extension to check if a Path contains an Offset
private fun Path.contains(point: Offset): Boolean {
    val bounds = this.getBounds()
    if (!bounds.contains(point)) return false
    // Ray-casting via Android Path measure — simple bounding-box pre-filter then use
    // PathMeasure / Region approach. For Compose we use the path's android backing.
    val region = android.graphics.Region()
    val clip   = android.graphics.Region(
        bounds.left.toInt() - 2, bounds.top.toInt() - 2,
        bounds.right.toInt() + 2, bounds.bottom.toInt() + 2,
    )
    val androidPath = this.asAndroidPath()
    region.setPath(androidPath, clip)
    return region.contains(point.x.toInt(), point.y.toInt())
}

// ── Public composable ─────────────────────────────────────────────────────────

/**
 * Interactive 2D body diagram drawn entirely with Compose Canvas.
 * Proportions and bezier paths are identical to the Windows PySide6 version.
 *
 * @param activeRegions  Set of region keys that have selected symptoms (highlighted in terracotta)
 * @param canvasWidth    Width dp for the canvas (height = canvasWidth * 2)
 * @param onRegionClick  Callback when user taps a body zone
 */
@Composable
fun BodyDiagramCanvas(
    activeRegions: Set<String>,
    modifier: Modifier = Modifier,
    canvasWidth: Dp = 180.dp,
    onRegionClick: (String) -> Unit = {},
) {
    // Build paths once
    val silhouette by remember { mutableStateOf(buildSilhouette()) }
    val zonePaths  by remember { mutableStateOf(buildZonePaths(silhouette)) }

    var hoveredRegion by remember { mutableStateOf<String?>(null) }

    // Scale factor + offsets computed at draw time — stored so hit-test can use them
    var drawScale   by remember { mutableStateOf(1f) }
    var drawOffsetX by remember { mutableStateOf(0f) }
    var drawOffsetY by remember { mutableStateOf(0f) }

    Canvas(
        modifier = modifier
            .pointerInput(zonePaths) {
                detectTapGestures { tapOffset ->
                    val region = regionAt(
                        tapOffset.x, tapOffset.y,
                        drawScale, drawOffsetX, drawOffsetY,
                        zonePaths,
                    )
                    if (region != null) onRegionClick(region)
                }
            }
    ) {
        val scale   = size.width / CW
        drawScale   = scale
        drawOffsetX = 0f
        drawOffsetY = 0f

        // Scale the canvas so our 200×400 paths fill the available width
        translate(0f, 0f) {
            drawContext.canvas.nativeCanvas.save()
            drawContext.canvas.nativeCanvas.scale(scale, scale)

            // 1 ── Drop shadow
            drawContext.canvas.nativeCanvas.translate(3f, 4f)
            drawPath(silhouette, ShadowColor)
            drawContext.canvas.nativeCanvas.translate(-3f, -4f)

            // 2 ── Skin fill
            drawPath(silhouette, SkinFill)

            // 3 ── Active zone overlays
            for ((region, path) in zonePaths) {
                if (region in activeRegions && region != hoveredRegion) {
                    drawPath(path, ActiveOverlay)
                }
            }

            // 4 ── Hovered zone overlay
            hoveredRegion?.let { hr ->
                zonePaths[hr]?.let { drawPath(it, HoverOverlay) }
            }

            // 5 ── Anatomy detail lines
            // Collarbone arcs
            val collarboneLeft = Path().apply {
                moveTo(100f, 76f)
                cubicTo(88f, 75f, 76f, 76f, 67f, 80f)
            }
            val collarboneRight = Path().apply {
                moveTo(100f, 76f)
                cubicTo(112f, 75f, 124f, 76f, 133f, 80f)
            }
            drawPath(collarboneLeft,  DetailLine, style = Stroke(width = 0.9f))
            drawPath(collarboneRight, DetailLine, style = Stroke(width = 0.9f))

            // Pectoral hint
            val pec = Path().apply {
                moveTo(64f, 108f)
                cubicTo(78f, 118f, 122f, 118f, 136f, 108f)
            }
            drawPath(pec, DetailLine.copy(alpha = 0.19f), style = Stroke(width = 0.8f))

            // Centre midline (dashed — approximate with segments)
            for (y in 78..228 step 8) {
                drawLine(DetailLine.copy(alpha = 0.16f), Offset(100f, y.toFloat()), Offset(100f, (y + 4).toFloat()), strokeWidth = 0.7f)
            }

            // Navel
            drawCircle(Color(0xFF966446).copy(alpha = 0.45f), radius = 2.6f, center = Offset(100f, 190f))

            // Kneecaps
            val kneePaint = Paint().apply {
                color = Color(0xFFA06C55).copy(alpha = 0.20f)
                style = PaintingStyle.Fill
            }
            drawOval(Color(0xFFA06C55).copy(alpha = 0.20f), topLeft = Offset(58f, 309f), size = androidx.compose.ui.geometry.Size(18f, 14f))
            drawOval(Color(0xFFA06C55).copy(alpha = 0.20f), topLeft = Offset(124f, 309f), size = androidx.compose.ui.geometry.Size(18f, 14f))

            // Ear inner details
            drawCircle(Color(0xFFB48069).copy(alpha = 0.29f), radius = 1.8f, center = Offset(81f, 29f))
            drawCircle(Color(0xFFB48069).copy(alpha = 0.29f), radius = 1.8f, center = Offset(119f, 29f))

            // 6 ── Silhouette outline
            drawPath(silhouette, SkinOutline, style = Stroke(width = 1.5f))

            // 7 ── Zone separator hints (dashed lines)
            for ((startX, endX, y) in listOf(
                Triple(88f, 112f, 78f),   // neck / chest
                Triple(62f, 138f, 164f),  // chest / abdomen
                Triple(57f, 143f, 232f),  // abdomen / legs
            )) {
                for (xi in startX.toInt()..endX.toInt() step 6) {
                    drawLine(DetailLine.copy(alpha = 0.19f), Offset(xi.toFloat(), y), Offset((xi + 3).toFloat(), y), strokeWidth = 0.8f)
                }
            }

            // 8 ── Active dot indicators (white ring + terracotta dot)
            for ((region, path) in zonePaths) {
                if (region in activeRegions) {
                    val bb = path.getBounds()
                    val cx = bb.right - 9f
                    val cy = bb.top + 9f
                    drawCircle(Color.White, radius = 7f, center = Offset(cx, cy))
                    drawCircle(Color(0xFF8B3A2E), radius = 4.5f, center = Offset(cx, cy))
                }
            }

            drawContext.canvas.nativeCanvas.restore()
        }
    }
}