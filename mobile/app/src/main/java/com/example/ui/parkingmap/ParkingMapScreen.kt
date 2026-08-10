package com.example.ui.parkingmap

import androidx.compose.animation.*
import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.ParkingRepository
import com.example.data.ParkingSpotEntity
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ParkingMapScreen(
    tenantId: String,
    repository: ParkingRepository,
    onBack: () -> Unit,
    onNavigateToMyParking: () -> Unit,
    onNavigateToFindVehicle: (String) -> Unit
) {
    val tenantState by repository.getTenantById(tenantId).collectAsState(initial = null)
    val activeSessions by repository.activeSessions.collectAsState(initial = emptyList())
    val activeSession = activeSessions.firstOrNull { it.tenantId == tenantId }

    var selectedFloor by remember { mutableStateOf("F2") }
    var selectedZone by remember { mutableStateOf("All") }

    val spotsFlow = remember(tenantId, selectedFloor) {
        repository.getSpotsForFloor(tenantId, selectedFloor)
    }
    val spots by spotsFlow.collectAsState(initial = emptyList())

    var selectedSpot by remember { mutableStateOf<ParkingSpotEntity?>(null) }
    var showLegendSheet by remember { mutableStateOf(false) }

    // Map Zoom & Pan State
    var scale by remember { mutableFloatStateOf(1f) }
    var offset by remember { mutableStateOf(Offset.Zero) }

    val tenant = tenantState ?: return

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("${tenant.name} - Parking Map", fontSize = 16.sp, fontWeight = FontWeight.Bold)
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .size(6.dp)
                                    .clip(CircleShape)
                                    .background(Color(0xFF10B981))
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("🟢 ${tenant.availableCapacity} spots available", fontSize = 12.sp, color = Color(0xFF10B981))
                        }
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { showLegendSheet = true }) {
                        Icon(Icons.Default.Info, contentDescription = "Legend")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // Floor Selector Bar
            FloorSelectorBar(
                selectedFloor = selectedFloor,
                onFloorSelected = {
                    selectedFloor = it
                    scale = 1f
                    offset = Offset.Zero
                }
            )

            // Zone Selector Bar
            ZoneSelectorBar(
                selectedZone = selectedZone,
                onZoneSelected = { selectedZone = it }
            )

            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .background(Color(0xFF0F172A))
            ) {
                // Interactive 2D Floor Map Canvas
                ParkingFloorCanvas(
                    spots = spots.filter { selectedZone == "All" || it.zoneId == selectedZone },
                    scale = scale,
                    offset = offset,
                    onTransform = { zoomChange, panChange ->
                        scale = (scale * zoomChange).coerceIn(0.8f, 3f)
                        offset += panChange
                    },
                    onSpotClick = { spot ->
                        selectedSpot = spot
                    }
                )

                // Map Overlay Controls (+ Zoom, - Zoom, Reset Center)
                Column(
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    FloatingActionButton(
                        onClick = { scale = (scale + 0.3f).coerceAtMost(3f) },
                        modifier = Modifier.size(40.dp),
                        containerColor = Color(0xFF1E293B),
                        contentColor = Color.White
                    ) {
                        Icon(Icons.Default.Add, contentDescription = "Zoom In")
                    }

                    FloatingActionButton(
                        onClick = { scale = (scale - 0.3f).coerceAtLeast(0.8f) },
                        modifier = Modifier.size(40.dp),
                        containerColor = Color(0xFF1E293B),
                        contentColor = Color.White
                    ) {
                        Icon(Icons.Default.Remove, contentDescription = "Zoom Out")
                    }

                    FloatingActionButton(
                        onClick = {
                            scale = 1f
                            offset = Offset.Zero
                        },
                        modifier = Modifier.size(40.dp),
                        containerColor = Color(0xFF2563EB),
                        contentColor = Color.White
                    ) {
                        Icon(Icons.Default.CenterFocusWeak, contentDescription = "Center Map")
                    }
                }

                // Active Parked Vehicle Banner overlay if user is on this floor
                if (activeSession != null) {
                    Surface(
                        modifier = Modifier
                            .align(Alignment.TopCenter)
                            .padding(12.dp)
                            .clickable { onNavigateToFindVehicle(activeSession!!.id) },
                        shape = RoundedCornerShape(12.dp),
                        color = Color(0xFF1E293B).copy(alpha = 0.95f),
                        border = BorderStroke(1.dp, Color(0xFF3B82F6))
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(10.dp)
                                    .clip(CircleShape)
                                    .background(Color(0xFF3B82F6))
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "Your Vehicle ${activeSession!!.licensePlate} is parked at B-27",
                                color = Color.White,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Icon(Icons.Default.ChevronRight, contentDescription = null, tint = Color(0xFF38BDF8))
                        }
                    }
                }
            }
        }

        // Spot Detail Bottom Sheet
        if (selectedSpot != null) {
            val spot = selectedSpot!!
            ModalBottomSheet(
                onDismissRequest = { selectedSpot = null }
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("Parking Spot ${spot.spotCode}", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                            Text("${spot.floorId} · ${spot.zoneId} · ${spot.distanceFromEntrance}m from entrance", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }

                        val badgeColor = when (spot.status) {
                            "MY_VEHICLE" -> Color(0xFF3B82F6)
                            "AVAILABLE" -> Color(0xFF10B981)
                            "OCCUPIED" -> Color(0xFFEF4444)
                            "RESERVED" -> Color(0xFFF59E0B)
                            else -> Color(0xFF64748B)
                        }

                        Surface(
                            shape = RoundedCornerShape(10.dp),
                            color = badgeColor.copy(alpha = 0.2f)
                        ) {
                            Text(
                                text = spot.status.replace("_", " "),
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                                color = badgeColor,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column {
                            Text("Spot Type", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(spot.type, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                        }

                        Column {
                            Text("Distance", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text("${spot.distanceFromEntrance}m (~1 min walk)", fontSize = 14.sp, fontWeight = FontWeight.Bold)
                        }
                    }

                    Spacer(modifier = Modifier.height(20.dp))

                    if (spot.status == "MY_VEHICLE" && activeSession != null) {
                        Button(
                            onClick = {
                                val sId = activeSession!!.id
                                selectedSpot = null
                                onNavigateToFindVehicle(sId)
                            },
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Icon(Icons.Default.Navigation, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Start Walking Navigation")
                        }
                    } else if (spot.status == "AVAILABLE") {
                        Button(
                            onClick = {
                                selectedSpot = null
                                onNavigateToMyParking()
                            },
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Text("Park at Spot ${spot.spotCode}")
                        }
                    }
                }
            }
        }

        // Legend Bottom Sheet
        if (showLegendSheet) {
            ModalBottomSheet(
                onDismissRequest = { showLegendSheet = false }
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text("Map Legend", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(16.dp))

                    LegendItem(Color(0xFF10B981), "Available Spot", "Open for parking")
                    LegendItem(Color(0xFFEF4444), "Occupied Spot", "Car currently parked")
                    LegendItem(Color(0xFFF59E0B), "Reserved Spot", "Reserved for resident member")
                    LegendItem(Color(0xFF3B82F6), "My Vehicle", "Your currently parked car")
                    LegendItem(Color(0xFF0284C7), "EV Charging Spot", "Supports Type-2 Fast EV Charging")

                    Spacer(modifier = Modifier.height(16.dp))
                    Button(
                        onClick = { showLegendSheet = false },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("Close")
                    }
                }
            }
        }
    }
}

@Composable
fun FloorSelectorBar(
    selectedFloor: String,
    onFloorSelected: (String) -> Unit
) {
    val floors = listOf(
        FloorChipData("B1", false, 0),
        FloorChipData("G", true, 12),
        FloorChipData("F1", true, 35),
        FloorChipData("F2", true, 15),
        FloorChipData("F3", false, 0)
    )

    LazyRow(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface)
            .padding(vertical = 8.dp),
        contentPadding = PaddingValues(horizontal = 16.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(floors) { floor ->
            val isSelected = floor.id == selectedFloor
            FilterChip(
                selected = isSelected,
                onClick = { onFloorSelected(floor.id) },
                label = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(floor.id, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.width(4.dp))
                        Box(
                            modifier = Modifier
                                .size(6.dp)
                                .clip(CircleShape)
                                .background(if (floor.available > 0) Color(0xFF10B981) else Color(0xFFEF4444))
                        )
                    }
                }
            )
        }
    }
}

@Composable
fun ZoneSelectorBar(
    selectedZone: String,
    onZoneSelected: (String) -> Unit
) {
    val zones = listOf("All", "Zone A", "Zone B", "Zone C")

    LazyRow(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
            .padding(vertical = 4.dp),
        contentPadding = PaddingValues(horizontal = 16.dp),
        horizontalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        items(zones) { zone ->
            val isSelected = zone == selectedZone
            SuggestionChip(
                onClick = { onZoneSelected(zone) },
                label = { Text(zone, fontSize = 12.sp) },
                border = if (isSelected) BorderStroke(1.dp, MaterialTheme.colorScheme.primary) else null
            )
        }
    }
}

@Composable
fun ParkingFloorCanvas(
    spots: List<ParkingSpotEntity>,
    scale: Float,
    offset: Offset,
    onTransform: (Float, Offset) -> Unit,
    onSpotClick: (ParkingSpotEntity) -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .pointerInput(Unit) {
                detectTransformGestures { _, pan, zoom, _ ->
                    onTransform(zoom, pan)
                }
            }
    ) {
        Canvas(
            modifier = Modifier
                .fillMaxSize()
                .graphicsLayer(
                    scaleX = scale,
                    scaleY = scale,
                    translationX = offset.x,
                    translationY = offset.y
                )
        ) {
            val w = size.width
            val h = size.height

            // Render Driveway Corridor Path
            val roadPath = Path().apply {
                moveTo(w * 0.1f, h * 0.35f)
                lineTo(w * 0.9f, h * 0.35f)
                moveTo(w * 0.1f, h * 0.65f)
                lineTo(w * 0.9f, h * 0.65f)
                moveTo(w * 0.5f, h * 0.10f)
                lineTo(w * 0.5f, h * 0.90f)
            }
            drawPath(roadPath, color = Color(0xFF1E293B), style = Stroke(width = 40.dp.toPx()))

            // Draw Entrance POI Marker
            drawCircle(Color(0xFF38BDF8), radius = 16.dp.toPx(), center = Offset(w * 0.1f, h * 0.35f))

            // Draw Spot Cards on Canvas
            spots.forEach { spot ->
                val spotX = w * spot.xRatio
                val spotY = h * spot.yRatio
                val spotWidth = 36.dp.toPx()
                val spotHeight = 56.dp.toPx()

                val spotColor = when (spot.status) {
                    "MY_VEHICLE" -> Color(0xFF3B82F6)
                    "AVAILABLE" -> Color(0xFF10B981)
                    "OCCUPIED" -> Color(0xFFEF4444)
                    "RESERVED" -> Color(0xFFF59E0B)
                    else -> Color(0xFF64748B)
                }

                drawRoundRect(
                    color = spotColor.copy(alpha = 0.25f),
                    topLeft = Offset(spotX - spotWidth / 2, spotY - spotHeight / 2),
                    size = Size(spotWidth, spotHeight),
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(6.dp.toPx())
                )

                drawRoundRect(
                    color = spotColor,
                    topLeft = Offset(spotX - spotWidth / 2, spotY - spotHeight / 2),
                    size = Size(spotWidth, spotHeight),
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(6.dp.toPx()),
                    style = Stroke(width = 2.dp.toPx())
                )
            }
        }

        // Overlay Interactive Click Targets for Spots
        spots.forEach { spot ->
            Box(
                modifier = Modifier
                    .align(Alignment.Center)
                    .offset(
                        x = ((spot.xRatio - 0.5f) * 300 * scale + offset.x / 3).dp,
                        y = ((spot.yRatio - 0.5f) * 450 * scale + offset.y / 3).dp
                    )
                    .size(44.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .clickable { onSpotClick(spot) },
                contentAlignment = Alignment.Center
            ) {
                val color = when (spot.status) {
                    "MY_VEHICLE" -> Color(0xFF3B82F6)
                    "AVAILABLE" -> Color(0xFF10B981)
                    "OCCUPIED" -> Color(0xFFEF4444)
                    "RESERVED" -> Color(0xFFF59E0B)
                    else -> Color(0xFF64748B)
                }
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = color
                ) {
                    Text(
                        text = spot.spotCode,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                        modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp)
                    )
                }
            }
        }
    }
}

@Composable
fun LegendItem(color: Color, title: String, description: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(16.dp)
                .clip(RoundedCornerShape(4.dp))
                .background(color)
        )
        Spacer(modifier = Modifier.width(12.dp))
        Column {
            Text(title, fontWeight = FontWeight.Bold, fontSize = 13.sp)
            Text(description, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

private data class FloorChipData(val id: String, val isOpen: Boolean, val available: Int)
