package com.example.ui.history

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
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.ParkingRepository
import com.example.data.ParkingSessionEntity

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ParkingHistoryScreen(
    repository: ParkingRepository,
    onBack: () -> Unit,
    onNavigateToTenant: (String) -> Unit
) {
    val historySessions by repository.historySessions.collectAsState(initial = emptyList())

    var searchQuery by remember { mutableStateOf("") }
    var selectedFilter by remember { mutableStateOf("All") }
    var selectedSessionForDetail by remember { mutableStateOf<ParkingSessionEntity?>(null) }
    var showReceiptModal by remember { mutableStateOf(false) }

    val filteredList = remember(historySessions, searchQuery, selectedFilter) {
        historySessions.filter { session ->
            val matchesQuery = searchQuery.isEmpty() ||
                    session.tenantName.contains(searchQuery, ignoreCase = true) ||
                    session.licensePlate.contains(searchQuery, ignoreCase = true) ||
                    session.spotCode.contains(searchQuery, ignoreCase = true)

            matchesQuery
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Parking History", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
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
            // Search Input
            OutlinedTextField(
                value = searchQuery,
                onValueChange = { searchQuery = it },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp),
                placeholder = { Text("Search by plate, tenant, or spot...", fontSize = 14.sp) },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
                singleLine = true,
                shape = RoundedCornerShape(12.dp)
            )

            Spacer(modifier = Modifier.height(10.dp))

            // Summary Info
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("${filteredList.size} Completed Sessions", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                Text("Total Spent: 90,000 VND", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = MaterialTheme.colorScheme.primary)
            }

            Spacer(modifier = Modifier.height(12.dp))

            if (filteredList.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text("No parking history matches your filter.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            } else {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 16.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    filteredList.forEach { session ->
                        HistorySessionCard(
                            session = session,
                            onClick = { selectedSessionForDetail = session }
                        )
                    }

                    Spacer(modifier = Modifier.height(24.dp))
                }
            }
        }

        // Session Detail Modal
        if (selectedSessionForDetail != null) {
            val session = selectedSessionForDetail!!
            ModalBottomSheet(
                onDismissRequest = { selectedSessionForDetail = null }
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(session.tenantName, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                            Text("License Plate: ${session.licensePlate}", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }

                        Surface(
                            shape = RoundedCornerShape(8.dp),
                            color = Color(0xFF10B981).copy(alpha = 0.2f)
                        ) {
                            Text("✓ Completed", modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp), color = Color(0xFF10B981), fontWeight = FontWeight.Bold, fontSize = 12.sp)
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Column {
                            Text("Parking Spot", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text("${session.floorName} · ${session.zoneName} · ${session.spotCode}", fontWeight = FontWeight.Bold)
                        }

                        Column(horizontalAlignment = Alignment.End) {
                            Text("Final Fee Paid", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text("${session.finalFee / 1000},000 VND", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary, fontSize = 16.sp)
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    Text("Session Details:", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    Spacer(modifier = Modifier.height(6.dp))
                    Text("• Duration: 2h 35m", fontSize = 13.sp)
                    Text("• Gate: ${session.gateName}", fontSize = 13.sp)
                    Text("• Rate Applied: ${session.pricingRule} (Resident Discount)", fontSize = 13.sp)

                    Spacer(modifier = Modifier.height(20.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        OutlinedButton(
                            onClick = {
                                val tId = session.tenantId
                                selectedSessionForDetail = null
                                onNavigateToTenant(tId)
                            },
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Text("Park Here Again")
                        }

                        Button(
                            onClick = { showReceiptModal = true },
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Icon(Icons.Default.Receipt, contentDescription = null, modifier = Modifier.size(18.dp))
                            Spacer(modifier = Modifier.width(6.dp))
                            Text("View Receipt")
                        }
                    }
                }
            }
        }

        // Receipt View Modal
        if (showReceiptModal && selectedSessionForDetail != null) {
            val session = selectedSessionForDetail!!
            AlertDialog(
                onDismissRequest = { showReceiptModal = false },
                title = { Text("Official Parking Receipt") },
                text = {
                    Column {
                        Text("Receipt ID: #RC-20260810-${session.id.take(4)}", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Spacer(modifier = Modifier.height(10.dp))
                        Text("Facility: ${session.tenantName}")
                        Text("Vehicle: ${session.licensePlate}")
                        Text("Spot: ${session.floorName} · ${session.spotCode}")
                        Text("Amount Paid: ${session.finalFee / 1000},000 VND", fontWeight = FontWeight.Bold, color = Color(0xFF10B981))
                        Text("Status: Paid via Visa •••• 4242", fontSize = 12.sp)
                    }
                },
                confirmButton = {
                    Button(onClick = { showReceiptModal = false }) {
                        Text("Close")
                    }
                }
            )
        }
    }
}

@Composable
fun HistorySessionCard(
    session: ParkingSessionEntity,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() },
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(2.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.DirectionsCar, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(20.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(session.licensePlate, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                }

                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = Color(0xFF10B981).copy(alpha = 0.15f)
                ) {
                    Text("✓ Paid", modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp), color = Color(0xFF10B981), fontWeight = FontWeight.Bold, fontSize = 11.sp)
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(session.tenantName, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Text("Spot ${session.spotCode} (${session.floorName} · ${session.zoneName})", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)

            Spacer(modifier = Modifier.height(10.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Duration: 2h 35m", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text("${session.finalFee / 1000},000 VND", fontWeight = FontWeight.Bold, fontSize = 16.sp, color = MaterialTheme.colorScheme.primary)
            }
        }
    }
}
