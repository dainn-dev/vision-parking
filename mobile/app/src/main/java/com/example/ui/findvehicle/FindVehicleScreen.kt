package com.example.ui.findvehicle

import androidx.compose.animation.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.ParkingRepository
import kotlinx.coroutines.delay

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FindVehicleScreen(
    sessionId: String,
    repository: ParkingRepository,
    onBack: () -> Unit,
    onArrived: () -> Unit
) {
    val sessionState by repository.getSessionById(sessionId).collectAsState(initial = null)
    val session = sessionState ?: return

    var currentStepIndex by remember { mutableIntStateOf(0) }
    var distanceRemaining by remember { mutableIntStateOf(85) }
    var hasArrived by remember { mutableStateOf(false) }

    // Navigation simulation progress
    val steps = listOf(
        NavStep("1", "Walk straight for 30m", "Pass through Main Entrance Corridor A", Icons.Default.Straight, 85),
        NavStep("2", "Take Elevator 02 to Floor 2", "Select F2 button inside elevator", Icons.Default.Elevator, 55),
        NavStep("3", "Exit elevator & turn left into Zone B", "Follow Zone B overhead signage", Icons.Default.TurnLeft, 30),
        NavStep("4", "Vehicle Ahead on the Left", "Spot B-27 · License Plate 51A-123.45", Icons.Default.DirectionsCar, 5)
    )

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("Find My Vehicle", fontWeight = FontWeight.Bold)
                        Text("Target: Spot ${session.spotCode} (${session.licensePlate})", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { paddingValues ->
        if (hasArrived) {
            // Arrival Screen
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp),
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    elevation = CardDefaults.cardElevation(8.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Surface(
                            shape = CircleShape,
                            color = Color(0xFF10B981).copy(alpha = 0.2f),
                            modifier = Modifier.size(72.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(Icons.Default.Check, contentDescription = null, tint = Color(0xFF10B981), modifier = Modifier.size(40.dp))
                            }
                        }

                        Spacer(modifier = Modifier.height(16.dp))

                        Text("You Have Arrived!", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                        Text("Parking Spot ${session.spotCode} · ${session.floorName}", fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)

                        Spacer(modifier = Modifier.height(16.dp))

                        Surface(
                            shape = RoundedCornerShape(12.dp),
                            color = Color(0xFF0F172A)
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(Icons.Default.DirectionsCar, contentDescription = null, tint = Color(0xFF38BDF8))
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Vehicle ${session.licensePlate} Confirmed", color = Color.White, fontWeight = FontWeight.Bold)
                            }
                        }

                        Spacer(modifier = Modifier.height(24.dp))

                        Button(
                            onClick = onArrived,
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Text("Done & Return")
                        }
                    }
                }
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
            ) {
                // 2D Indoor Navigation Map Canvas
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(260.dp)
                        .padding(16.dp),
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A))
                ) {
                    Box(modifier = Modifier.fillMaxSize()) {
                        Canvas(modifier = Modifier.fillMaxSize()) {
                            val w = size.width
                            val h = size.height

                            // Draw Walking Path Line
                            val path = Path().apply {
                                moveTo(w * 0.15f, h * 0.8f) // YOU
                                lineTo(w * 0.45f, h * 0.8f)
                                lineTo(w * 0.45f, h * 0.3f) // Elevator
                                lineTo(w * 0.8f, h * 0.3f)  // Spot B-27
                            }
                            drawPath(path, color = Color(0xFF3B82F6), style = Stroke(width = 6.dp.toPx()))

                            // YOU Start Dot
                            drawCircle(Color(0xFF38BDF8), radius = 12.dp.toPx(), center = Offset(w * 0.15f, h * 0.8f))
                            // Spot B-27 End Destination
                            drawCircle(Color(0xFF10B981), radius = 16.dp.toPx(), center = Offset(w * 0.8f, h * 0.3f))
                        }

                        // YOU Label
                        Surface(
                            modifier = Modifier
                                .align(Alignment.BottomStart)
                                .padding(16.dp),
                            shape = RoundedCornerShape(8.dp),
                            color = Color(0xFF1E293B)
                        ) {
                            Text("● YOU ARE HERE", color = Color(0xFF38BDF8), fontSize = 11.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(6.dp))
                        }

                        // Vehicle Spot Label
                        Surface(
                            modifier = Modifier
                                .align(Alignment.TopEnd)
                                .padding(16.dp),
                            shape = RoundedCornerShape(8.dp),
                            color = Color(0xFF10B981)
                        ) {
                            Text("🚗 ${session.spotCode}", color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(6.dp))
                        }
                    }
                }

                // Distance & Step Progress Header
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("Distance Remaining", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text("${distanceRemaining}m (~2 min walk)", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                        }

                        Surface(
                            shape = RoundedCornerShape(10.dp),
                            color = MaterialTheme.colorScheme.primaryContainer
                        ) {
                            Text(
                                "Step ${currentStepIndex + 1} of ${steps.size}",
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Current Navigation Step Guidance Card
                val currentStep = steps[currentStepIndex]
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.5f))
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Surface(
                            shape = CircleShape,
                            color = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(48.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(currentStep.icon, contentDescription = null, tint = Color.White)
                            }
                        }

                        Spacer(modifier = Modifier.width(16.dp))

                        Column {
                            Text(currentStep.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                            Text(currentStep.subtitle, fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }

                Spacer(modifier = Modifier.weight(1f))

                // Step Progression Actions
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    if (currentStepIndex > 0) {
                        OutlinedButton(
                            onClick = {
                                currentStepIndex -= 1
                                distanceRemaining = steps[currentStepIndex].distance
                            },
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Text("Previous Step")
                        }
                    }

                    Button(
                        onClick = {
                            if (currentStepIndex < steps.size - 1) {
                                currentStepIndex += 1
                                distanceRemaining = steps[currentStepIndex].distance
                            } else {
                                hasArrived = true
                            }
                        },
                        modifier = Modifier.weight(1.5f),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Text(if (currentStepIndex < steps.size - 1) "Next Step" else "I Have Arrived")
                        Spacer(modifier = Modifier.width(6.dp))
                        Icon(Icons.Default.ChevronRight, contentDescription = null)
                    }
                }
            }
        }
    }
}

private data class NavStep(
    val stepNumber: String,
    val title: String,
    val subtitle: String,
    val icon: androidx.compose.ui.graphics.vector.ImageVector,
    val distance: Int
)
