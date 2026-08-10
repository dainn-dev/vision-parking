package com.example.ui.myparking

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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.ParkingRepository
import com.example.data.ParkingSessionEntity
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MyParkingScreen(
    repository: ParkingRepository,
    onNavigateToFindVehicle: (String) -> Unit,
    onNavigateToMap: (String) -> Unit,
    onNavigateToHistory: () -> Unit,
    onNavigateToDiscover: () -> Unit
) {
    val activeSessions by repository.activeSessions.collectAsState(initial = emptyList())
    val activeSession = activeSessions.firstOrNull()

    var showPriceBreakdown by remember { mutableStateOf(false) }
    var showExitPayDialog by remember { mutableStateOf(false) }
    var isExitingGate by remember { mutableStateOf(false) }
    var showReceiptModal by remember { mutableStateOf(false) }

    val coroutineScope = rememberCoroutineScope()

    // Live second-by-second timer
    var secondsElapsed by remember(activeSession) { mutableLongStateOf(activeSession?.durationSeconds ?: 9320) }
    LaunchedEffect(activeSession) {
        if (activeSession != null) {
            while (true) {
                delay(1000)
                secondsElapsed += 1
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("My Parking", fontWeight = FontWeight.Bold) },
                actions = {
                    IconButton(onClick = onNavigateToHistory) {
                        Icon(Icons.Outlined.History, contentDescription = "Parking History")
                    }
                }
            )
        }
    ) { paddingValues ->
        if (activeSession == null) {
            // Empty State
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    modifier = Modifier.padding(32.dp)
                ) {
                    Surface(
                        shape = CircleShape,
                        color = MaterialTheme.colorScheme.primaryContainer,
                        modifier = Modifier.size(80.dp)
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Icon(Icons.Default.DirectionsCar, contentDescription = null, modifier = Modifier.size(40.dp))
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    Text("No Active Parking", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Text(
                        "You are not currently parked at any facility.",
                        textAlign = TextAlign.Center,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontSize = 13.sp
                    )

                    Spacer(modifier = Modifier.height(20.dp))

                    Button(
                        onClick = onNavigateToDiscover,
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Text("Find Nearby Parking")
                    }
                }
            }
        } else {
            val session = activeSession!!

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .verticalScroll(rememberScrollState())
            ) {
                // Active Session Summary Card
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A))
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Box(
                                    modifier = Modifier
                                        .size(10.dp)
                                        .clip(CircleShape)
                                        .background(Color(0xFF10B981))
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("PARKING ACTIVE", color = Color(0xFF10B981), fontWeight = FontWeight.Bold, fontSize = 12.sp)
                            }

                            Surface(
                                shape = RoundedCornerShape(8.dp),
                                color = Color(0xFF1E293B)
                            ) {
                                Text(
                                    text = session.licensePlate,
                                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White,
                                    fontSize = 13.sp
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(16.dp))

                        Text(session.tenantName, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold, color = Color.White)
                        Text("Spot: ${session.floorName} · ${session.zoneName} · ${session.spotCode}", color = Color(0xFF38BDF8), fontSize = 14.sp, fontWeight = FontWeight.SemiBold)

                        Spacer(modifier = Modifier.height(20.dp))

                        // Live Counter & Current Fee
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(14.dp))
                                .background(Color(0xFF1E293B))
                                .padding(16.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text("Duration", fontSize = 11.sp, color = Color(0xFF94A3B8))
                                val hours = secondsElapsed / 3600
                                val mins = (secondsElapsed % 3600) / 60
                                val secs = secondsElapsed % 60
                                Text(
                                    text = String.format("%02dh %02dm %02ds", hours, mins, secs),
                                    fontSize = 18.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White
                                )
                            }

                            Column(horizontalAlignment = Alignment.End) {
                                Text("Current Fee", fontSize = 11.sp, color = Color(0xFF94A3B8))
                                Text(
                                    text = "40,000 VND",
                                    fontSize = 18.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color(0xFF10B981)
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(12.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text("✓ Resident Member Discount (-10,000 VND)", color = Color(0xFF10B981), fontSize = 12.sp)
                            TextButton(onClick = { showPriceBreakdown = true }) {
                                Text("Breakdown", color = Color(0xFF38BDF8), fontSize = 12.sp)
                            }
                        }
                    }
                }

                // Action Buttons
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Button(
                        onClick = { onNavigateToFindVehicle(session.id) },
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                        contentPadding = PaddingValues(vertical = 12.dp)
                    ) {
                        Icon(Icons.Default.Navigation, contentDescription = null, modifier = Modifier.size(18.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Find My Vehicle", fontWeight = FontWeight.Bold)
                    }

                    OutlinedButton(
                        onClick = { onNavigateToMap(session.tenantId) },
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(12.dp),
                        contentPadding = PaddingValues(vertical = 12.dp)
                    ) {
                        Icon(Icons.Default.Map, contentDescription = null, modifier = Modifier.size(18.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Indoor Map")
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Parking Spot Location Tile
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Vehicle Location", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(8.dp))

                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Surface(
                                shape = RoundedCornerShape(12.dp),
                                color = MaterialTheme.colorScheme.primaryContainer,
                                modifier = Modifier.size(48.dp)
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Text(session.spotCode, fontWeight = FontWeight.Bold, fontSize = 16.sp, color = MaterialTheme.colorScheme.onPrimaryContainer)
                                }
                            }

                            Spacer(modifier = Modifier.width(12.dp))

                            Column {
                                Text("${session.floorName} · ${session.zoneName}", fontWeight = FontWeight.Bold)
                                Text("✓ Confirmed by Camera LPR B2", fontSize = 12.sp, color = Color(0xFF10B981))
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Session Timeline
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Session Timeline", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(12.dp))

                        TimelineItem("18:32:14", "Vehicle Entered Gate", "Main Entrance Gate 01 LPR Camera", isDone = true)
                        TimelineItem("18:33:02", "Session Started", "Member Rate Rule Applied", isDone = true)
                        TimelineItem("18:35:10", "Parked at Spot ${session.spotCode}", "Confirmed by Floor Camera", isDone = true)
                        TimelineItem("Current", "Parking Active", "40,000 VND calculated", isDone = true, isCurrent = true)
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                // Exit & Pay Button
                Button(
                    onClick = { showExitPayDialog = true },
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFEF4444)),
                    contentPadding = PaddingValues(vertical = 14.dp)
                ) {
                    Icon(Icons.Default.ExitToApp, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Exit Facility & Pay (40,000 VND)", fontSize = 15.sp, fontWeight = FontWeight.Bold)
                }

                Spacer(modifier = Modifier.height(24.dp))
            }
        }

        // Price Breakdown Sheet
        if (showPriceBreakdown && activeSession != null) {
            ModalBottomSheet(onDismissRequest = { showPriceBreakdown = false }) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text("Price Breakdown", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(16.dp))

                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Standard Parking (2h 35m)")
                        Text("50,000 VND")
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Monthly Resident Discount", color = Color(0xFF10B981))
                        Text("-10,000 VND", color = Color(0xFF10B981), fontWeight = FontWeight.Bold)
                    }
                    Divider(modifier = Modifier.padding(vertical = 12.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Total Current Amount", fontWeight = FontWeight.Bold)
                        Text("40,000 VND", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary, fontSize = 16.sp)
                    }

                    Spacer(modifier = Modifier.height(20.dp))
                    Button(onClick = { showPriceBreakdown = false }, modifier = Modifier.fillMaxWidth()) {
                        Text("Close")
                    }
                }
            }
        }

        // Exit & Pay Confirmation Modal
        if (showExitPayDialog && activeSession != null) {
            val session = activeSession!!
            AlertDialog(
                onDismissRequest = { showExitPayDialog = false },
                title = { Text("Checkout & Gate Opening") },
                text = {
                    Column {
                        Text("Vehicle: ${session.licensePlate}")
                        Text("Facility: ${session.tenantName}")
                        Text("Duration: 2h 35m")
                        Text("Total Fee: 40,000 VND", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                        Spacer(modifier = Modifier.height(12.dp))

                        if (isExitingGate) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                CircularProgressIndicator(modifier = Modifier.size(20.dp))
                                Spacer(modifier = Modifier.width(10.dp))
                                Text("Communicating with Gate LPR Controller...", fontSize = 12.sp)
                            }
                        } else {
                            Text("Clicking confirm will process payment and signal the main exit gate to open automatically.", fontSize = 12.sp)
                        }
                    }
                },
                confirmButton = {
                    Button(
                        onClick = {
                            isExitingGate = true
                            coroutineScope.launch {
                                delay(1500)
                                repository.completeParkingSession(session.id)
                                isExitingGate = false
                                showExitPayDialog = false
                                showReceiptModal = true
                            }
                        },
                        enabled = !isExitingGate
                    ) {
                        Text("Pay & Open Gate")
                    }
                },
                dismissButton = {
                    if (!isExitingGate) {
                        TextButton(onClick = { showExitPayDialog = false }) {
                            Text("Cancel")
                        }
                    }
                }
            )
        }

        // Receipt Modal
        if (showReceiptModal) {
            AlertDialog(
                onDismissRequest = { showReceiptModal = false },
                title = { Text("✓ Payment Successful & Session Complete") },
                text = {
                    Column {
                        Text("Receipt #RC-20260810-001", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Spacer(modifier = Modifier.height(10.dp))
                        Text("Vehicle: 51A-123.45")
                        Text("Facility: Trọ TP")
                        Text("Paid Amount: 40,000 VND", fontWeight = FontWeight.Bold, color = Color(0xFF10B981))
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("Exit Gate 01 is open. Have a safe drive!", fontSize = 12.sp)
                    }
                },
                confirmButton = {
                    Button(onClick = { showReceiptModal = false }) {
                        Text("Done")
                    }
                }
            )
        }
    }
}

@Composable
fun TimelineItem(time: String, title: String, subtitle: String, isDone: Boolean, isCurrent: Boolean = false) {
    Row(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.width(60.dp)) {
            Text(time, fontSize = 11.sp, fontWeight = FontWeight.Bold, color = if (isCurrent) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant)
        }

        Box(modifier = Modifier.size(12.dp).clip(CircleShape).background(if (isCurrent) MaterialTheme.colorScheme.primary else Color(0xFF10B981)))

        Spacer(modifier = Modifier.width(12.dp))

        Column {
            Text(title, fontWeight = FontWeight.Bold, fontSize = 13.sp)
            Text(subtitle, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}
