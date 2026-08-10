package com.example.ui.profile

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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileScreen(
    repository: ParkingRepository,
    onNavigateToVehicles: () -> Unit,
    onNavigateToMemberships: () -> Unit,
    onNavigateToMyParking: () -> Unit,
    onNavigateToHistory: () -> Unit,
    onNavigateToSecurity: () -> Unit,
    onNavigateToNotifications: () -> Unit
) {
    val vehicles by repository.allVehicles.collectAsState(initial = emptyList())
    val memberships by repository.allMemberships.collectAsState(initial = emptyList())
    val activeSessions by repository.activeSessions.collectAsState(initial = emptyList())
    val unreadCount by repository.unreadNotificationCount.collectAsState(initial = 0)

    var showLogoutDialog by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Profile & Settings", fontWeight = FontWeight.Bold) },
                actions = {
                    IconButton(onClick = onNavigateToNotifications) {
                        BadgedBox(
                            badge = {
                                if (unreadCount > 0) {
                                    Badge { Text("$unreadCount") }
                                }
                            }
                        ) {
                            Icon(Icons.Outlined.Notifications, contentDescription = "Notifications")
                        }
                    }
                }
            )
        }
    ) { paddingValues ->

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            // Profile Header Identity
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                elevation = CardDefaults.cardElevation(2.dp)
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Surface(
                        shape = CircleShape,
                        color = MaterialTheme.colorScheme.primaryContainer,
                        modifier = Modifier.size(72.dp)
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Text("A", fontSize = 28.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onPrimaryContainer)
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    Text("Anthony Nguyen", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    Text("anthony@email.com", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)

                    Spacer(modifier = Modifier.height(6.dp))

                    Surface(
                        shape = RoundedCornerShape(8.dp),
                        color = MaterialTheme.colorScheme.primary.copy(alpha = 0.15f)
                    ) {
                        Text(
                            text = "MEMBER",
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 2.dp),
                            color = MaterialTheme.colorScheme.primary,
                            fontWeight = FontWeight.Bold,
                            fontSize = 11.sp
                        )
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Account Summary Metrics
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(12.dp))
                            .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
                            .padding(12.dp),
                        horizontalArrangement = Arrangement.SpaceAround
                    ) {
                        ProfileMetric("${vehicles.size}", "Vehicles")
                        ProfileMetric("${memberships.count { it.status == "ACTIVE" }}", "Memberships")
                        ProfileMetric("${activeSessions.size}", "Active Session")
                    }
                }
            }

            // Section: PARKING & VEHICLES
            ProfileSectionTitle("PARKING & VEHICLES")
            ProfileMenuItem("My Vehicles", "${vehicles.size} registered", Icons.Default.DirectionsCar, onNavigateToVehicles)
            ProfileMenuItem("My Memberships", "${memberships.count { it.status == "ACTIVE" }} active", Icons.Default.CardMembership, onNavigateToMemberships)
            ProfileMenuItem("My Parking", if (activeSessions.isNotEmpty()) "1 active parking" else "No active parking", Icons.Default.LocalParking, onNavigateToMyParking)
            ProfileMenuItem("Parking History", "Completed sessions & receipts", Icons.Default.History, onNavigateToHistory)

            Spacer(modifier = Modifier.height(16.dp))

            // Section: ACCOUNT & SECURITY
            ProfileSectionTitle("ACCOUNT & SECURITY")
            ProfileMenuItem("Security & 2FA", "Password, two-factor & sessions", Icons.Default.Security, onNavigateToSecurity)
            ProfileMenuItem("Notification Preferences", "Parking alerts, expiry reminders", Icons.Default.Notifications, onClick = onNavigateToNotifications)
            ProfileMenuItem("Language & Currency", "English · VND", Icons.Default.Language, onClick = { })

            Spacer(modifier = Modifier.height(16.dp))

            // Section: SUPPORT & POLICIES
            ProfileSectionTitle("SUPPORT & POLICIES")
            ProfileMenuItem("Help Center & FAQ", "Find answers to parking questions", Icons.Default.HelpOutline, onClick = { })
            ProfileMenuItem("Terms & Privacy Policy", "Platform legal terms", Icons.Default.Policy, onClick = { })

            Spacer(modifier = Modifier.height(24.dp))

            // Logout Button
            Button(
                onClick = { showLogoutDialog = true },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFEF4444).copy(alpha = 0.15f), contentColor = Color(0xFFEF4444)),
                contentPadding = PaddingValues(vertical = 12.dp)
            ) {
                Icon(Icons.Default.ExitToApp, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Log Out", fontWeight = FontWeight.Bold)
            }

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = "Vision License Plate · Smart Parking v1.0.0",
                fontSize = 11.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.fillMaxWidth(),
                textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )

            Spacer(modifier = Modifier.height(32.dp))
        }

        // Logout Confirmation Dialog
        if (showLogoutDialog) {
            AlertDialog(
                onDismissRequest = { showLogoutDialog = false },
                title = { Text("Log Out?") },
                text = { Text("Are you sure you want to log out of Vision Parking?") },
                confirmButton = {
                    Button(onClick = { showLogoutDialog = false }) {
                        Text("Log Out")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showLogoutDialog = false }) {
                        Text("Cancel")
                    }
                }
            )
        }
    }
}

@Composable
fun ProfileSectionTitle(title: String) {
    Text(
        text = title,
        fontSize = 12.sp,
        fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.primary,
        modifier = Modifier.padding(horizontal = 20.dp, vertical = 6.dp)
    )
}

@Composable
fun ProfileMenuItem(
    title: String,
    subtitle: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    onClick: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() },
        color = MaterialTheme.colorScheme.background
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 20.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Surface(
                shape = RoundedCornerShape(10.dp),
                color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.5f),
                modifier = Modifier.size(38.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(20.dp))
                }
            }

            Spacer(modifier = Modifier.width(14.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(title, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                Text(subtitle, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }

            Icon(Icons.Default.ChevronRight, contentDescription = null, tint = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
fun ProfileMetric(value: String, label: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(value, fontWeight = FontWeight.Bold, fontSize = 16.sp, color = MaterialTheme.colorScheme.primary)
        Text(label, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}
