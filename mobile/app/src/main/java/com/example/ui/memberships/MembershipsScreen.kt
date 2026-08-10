package com.example.ui.memberships

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
import com.example.data.MembershipEntity
import com.example.data.ParkingRepository
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MembershipsScreen(
    repository: ParkingRepository,
    onNavigateToTenant: (String) -> Unit,
    onNavigateToDiscover: () -> Unit
) {
    val memberships by repository.allMemberships.collectAsState(initial = emptyList())
    var selectedTab by remember { mutableIntStateOf(0) } // 0: Active, 1: Pending, 2: History

    var showRenewDialog by remember { mutableStateOf<MembershipEntity?>(null) }
    var showJoinDialog by remember { mutableStateOf(false) }

    val coroutineScope = rememberCoroutineScope()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("My Memberships", fontWeight = FontWeight.Bold) },
                actions = {
                    IconButton(onClick = { showJoinDialog = true }) {
                        Icon(Icons.Default.Add, contentDescription = "Join New Tenant")
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
            // Tab Row
            TabRow(selectedTabIndex = selectedTab) {
                Tab(selected = selectedTab == 0, onClick = { selectedTab = 0 }) {
                    Text("Active (${memberships.count { it.status == "ACTIVE" }})", modifier = Modifier.padding(12.dp), fontWeight = FontWeight.Bold)
                }
                Tab(selected = selectedTab == 1, onClick = { selectedTab = 1 }) {
                    Text("Pending (0)", modifier = Modifier.padding(12.dp))
                }
                Tab(selected = selectedTab == 2, onClick = { selectedTab = 2 }) {
                    Text("History", modifier = Modifier.padding(12.dp))
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            val filteredList = remember(memberships, selectedTab) {
                when (selectedTab) {
                    0 -> memberships.filter { it.status == "ACTIVE" }
                    1 -> memberships.filter { it.status == "PENDING" }
                    else -> memberships.filter { it.status in listOf("EXPIRED", "CANCELLED") }
                }
            }

            if (filteredList.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(32.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(Icons.Outlined.CardMembership, contentDescription = null, modifier = Modifier.size(64.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant)
                        Spacer(modifier = Modifier.height(16.dp))
                        Text("No Memberships Found", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                        Spacer(modifier = Modifier.height(6.dp))
                        Text("Join a tenant facility to get resident parking access & lower member rates.", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Spacer(modifier = Modifier.height(20.dp))
                        Button(onClick = onNavigateToDiscover) {
                            Text("Discover Facilities")
                        }
                    }
                }
            } else {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 16.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    filteredList.forEach { membership ->
                        MembershipCardItem(
                            membership = membership,
                            onRenew = { showRenewDialog = membership },
                            onToggleAutoRenew = {
                                coroutineScope.launch {
                                    repository.registerMembership(
                                        membership.tenantId,
                                        membership.tenantName,
                                        membership.planName,
                                        membership.pricePerMonth,
                                        membership.vehiclePlate
                                    )
                                }
                            },
                            onViewTenant = { onNavigateToTenant(membership.tenantId) }
                        )
                    }

                    Spacer(modifier = Modifier.height(24.dp))
                }
            }
        }

        // Renew Dialog Modal
        if (showRenewDialog != null) {
            val mem = showRenewDialog!!
            AlertDialog(
                onDismissRequest = { showRenewDialog = null },
                title = { Text("Renew Subscription") },
                text = {
                    Column {
                        Text("Facility: ${mem.tenantName}")
                        Text("Plan: ${mem.planName}")
                        Text("Amount: ${mem.pricePerMonth / 1000},000 VND / month", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                        Spacer(modifier = Modifier.height(10.dp))
                        Text("New validity period will extend from Sep 10, 2026 to Oct 09, 2026.", fontSize = 12.sp)
                    }
                },
                confirmButton = {
                    Button(
                        onClick = {
                            coroutineScope.launch {
                                repository.registerMembership(
                                    mem.tenantId,
                                    mem.tenantName,
                                    mem.planName,
                                    mem.pricePerMonth,
                                    mem.vehiclePlate
                                )
                                showRenewDialog = null
                            }
                        }
                    ) {
                        Text("Confirm & Renew")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showRenewDialog = null }) {
                        Text("Cancel")
                    }
                }
            )
        }

        // Join Tenant Dialog Modal
        if (showJoinDialog) {
            AlertDialog(
                onDismissRequest = { showJoinDialog = false },
                title = { Text("Join Tenant Facility") },
                text = {
                    Column {
                        Text("Select a tenant from Discover to register a resident or monthly parking plan:", fontSize = 13.sp)
                    }
                },
                confirmButton = {
                    Button(onClick = {
                        showJoinDialog = false
                        onNavigateToDiscover()
                    }) {
                        Text("Go to Discover")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showJoinDialog = false }) {
                        Text("Cancel")
                    }
                }
            )
        }
    }
}

@Composable
fun MembershipCardItem(
    membership: MembershipEntity,
    onRenew: () -> Unit,
    onToggleAutoRenew: () -> Unit,
    onViewTenant: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(2.dp)
    ) {
        Column(modifier = Modifier.padding(18.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Surface(
                        shape = CircleShape,
                        color = Color(0xFF10B981).copy(alpha = 0.2f),
                        modifier = Modifier.size(36.dp)
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Icon(Icons.Default.CardMembership, contentDescription = null, tint = Color(0xFF10B981), modifier = Modifier.size(20.dp))
                        }
                    }
                    Spacer(modifier = Modifier.width(10.dp))
                    Column {
                        Text(membership.tenantName, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                        Text(membership.planName, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }

                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = Color(0xFF10B981).copy(alpha = 0.15f)
                ) {
                    Text(
                        text = membership.status,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        color = Color(0xFF10B981),
                        fontWeight = FontWeight.Bold,
                        fontSize = 11.sp
                    )
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text("Monthly Rate", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text("${membership.pricePerMonth / 1000},000 VND", fontWeight = FontWeight.Bold, fontSize = 15.sp, color = MaterialTheme.colorScheme.primary)
                }

                Column(horizontalAlignment = Alignment.End) {
                    Text("Covered Vehicle", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(membership.vehiclePlate, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            Column {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Validity: ${membership.startDate} → ${membership.expiresDate}", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text("20 days left", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF10B981))
                }
                Spacer(modifier = Modifier.height(4.dp))
                LinearProgressIndicator(
                    progress = { 0.35f },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(6.dp)
                        .clip(RoundedCornerShape(3.dp)),
                    color = Color(0xFF10B981)
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Benefits Checklist
            Text("Included Benefits:", fontWeight = FontWeight.Bold, fontSize = 12.sp)
            Spacer(modifier = Modifier.height(4.dp))
            BenefitCheckItem("Unlimited Resident Facility Access")
            BenefitCheckItem("Automatic LPR Camera Gate Recognition")
            BenefitCheckItem("Discounted 10,000 VND/hr Hourly Member Rate")

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(
                    onClick = onViewTenant,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Text("Facility Info", fontSize = 12.sp)
                }

                Button(
                    onClick = onRenew,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Text("Renew Plan", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun BenefitCheckItem(text: String) {
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(vertical = 2.dp)) {
        Icon(Icons.Default.CheckCircle, contentDescription = null, tint = Color(0xFF10B981), modifier = Modifier.size(14.dp))
        Spacer(modifier = Modifier.width(6.dp))
        Text(text, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurface)
    }
}
