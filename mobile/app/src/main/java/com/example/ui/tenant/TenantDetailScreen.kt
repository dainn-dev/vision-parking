package com.example.ui.tenant

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
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.R
import com.example.data.ParkingRepository
import com.example.data.TenantEntity
import com.example.data.VehicleEntity
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TenantDetailScreen(
    tenantId: String,
    repository: ParkingRepository,
    onBack: () -> Unit,
    onOpenMap: () -> Unit,
    onNavigateToMyParking: () -> Unit,
    onNavigateToMemberships: () -> Unit
) {
    val tenantState by repository.getTenantById(tenantId).collectAsState(initial = null)
    val vehicles by repository.allVehicles.collectAsState(initial = emptyList())
    val activeSessions by repository.activeSessions.collectAsState(initial = emptyList())

    val tenant = tenantState ?: return

    val coroutineScope = rememberCoroutineScope()
    var isFavorite by remember(tenant) { mutableStateOf(tenant.isFavorite) }

    var showParkNowDialog by remember { mutableStateOf(false) }
    var selectedVehicle by remember(vehicles) { mutableStateOf(vehicles.firstOrNull()) }
    var showPricingSheet by remember { mutableStateOf(false) }

    val hasActiveSessionAtThisTenant = activeSessions.any { it.tenantId == tenant.id }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(tenant.name, maxLines = 1) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(
                        onClick = {
                            isFavorite = !isFavorite
                            coroutineScope.launch {
                                repository.toggleFavoriteTenant(tenant.id, isFavorite)
                            }
                        }
                    ) {
                        Icon(
                            imageVector = if (isFavorite) Icons.Filled.Favorite else Icons.Outlined.FavoriteBorder,
                            contentDescription = "Favorite",
                            tint = if (isFavorite) Color(0xFFEF4444) else MaterialTheme.colorScheme.onSurface
                        )
                    }
                    IconButton(onClick = { }) {
                        Icon(Icons.Default.Share, contentDescription = "Share")
                    }
                }
            )
        },
        bottomBar = {
            Surface(
                tonalElevation = 8.dp,
                shadowElevation = 12.dp,
                color = MaterialTheme.colorScheme.surface
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    OutlinedButton(
                        onClick = onOpenMap,
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(12.dp),
                        contentPadding = PaddingValues(vertical = 12.dp)
                    ) {
                        Icon(Icons.Default.Navigation, contentDescription = null, modifier = Modifier.size(18.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Directions", fontSize = 14.sp)
                    }

                    if (hasActiveSessionAtThisTenant) {
                        Button(
                            onClick = onNavigateToMyParking,
                            modifier = Modifier.weight(1.2f),
                            shape = RoundedCornerShape(12.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981)),
                            contentPadding = PaddingValues(vertical = 12.dp)
                        ) {
                            Icon(Icons.Default.DirectionsCar, contentDescription = null, modifier = Modifier.size(18.dp))
                            Spacer(modifier = Modifier.width(6.dp))
                            Text("Active Session", fontSize = 14.sp, fontWeight = FontWeight.Bold)
                        }
                    } else {
                        Button(
                            onClick = { showParkNowDialog = true },
                            modifier = Modifier.weight(1.2f),
                            shape = RoundedCornerShape(12.dp),
                            enabled = tenant.availableCapacity > 0,
                            contentPadding = PaddingValues(vertical = 12.dp)
                        ) {
                            Text(
                                text = if (tenant.availableCapacity > 0) "Park Now" else "Full",
                                fontSize = 14.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            // Hero Image Banner
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(200.dp)
            ) {
                Image(
                    painter = painterResource(id = R.drawable.img_parking_hero_1_1786375108677),
                    contentDescription = "Facility Photo",
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop
                )

                Surface(
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(12.dp),
                    shape = RoundedCornerShape(8.dp),
                    color = Color.Black.copy(alpha = 0.7f)
                ) {
                    Text(
                        text = "📷 1 / 8 Photos",
                        color = Color.White,
                        fontSize = 12.sp,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }
            }

            Column(modifier = Modifier.padding(16.dp)) {
                // Identity & Verified Badge
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = tenant.name,
                                style = MaterialTheme.typography.headlineSmall,
                                fontWeight = FontWeight.Bold
                            )
                            if (tenant.verified) {
                                Spacer(modifier = Modifier.width(6.dp))
                                Icon(
                                    imageVector = Icons.Default.Verified,
                                    contentDescription = "Verified Provider",
                                    tint = Color(0xFF0284C7),
                                    modifier = Modifier.size(20.dp)
                                )
                            }
                        }

                        Text(
                            text = "${tenant.category} · ${tenant.address}, ${tenant.district}",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }

                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = MaterialTheme.colorScheme.primaryContainer
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text("⭐ ${tenant.rating}", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                            Text(" (${tenant.reviewCount})", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Real-time Capacity Card
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
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
                                        .background(if (tenant.availableCapacity > 0) Color(0xFF10B981) else Color(0xFFEF4444))
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    text = if (tenant.availableCapacity > 0) "OPEN · AVAILABLE" else "FULL",
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp,
                                    color = if (tenant.availableCapacity > 0) Color(0xFF10B981) else Color(0xFFEF4444)
                                )
                            }

                            Text("Updated 12s ago", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }

                        Spacer(modifier = Modifier.height(10.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                text = "🟢 ${tenant.availableCapacity} spots available",
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF10B981)
                            )
                            Text(
                                text = "${tenant.occupiedCapacity} / ${tenant.totalCapacity} occupied",
                                fontSize = 13.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }

                        Spacer(modifier = Modifier.height(8.dp))

                        val capRatio = tenant.availableCapacity.toFloat() / tenant.totalCapacity.coerceAtLeast(1)
                        LinearProgressIndicator(
                            progress = { 1f - capRatio },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(8.dp)
                                .clip(RoundedCornerShape(4.dp)),
                            color = if (tenant.availableCapacity > 10) Color(0xFF10B981) else Color(0xFFF59E0B)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Pricing Summary Card
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text("Pricing Rates", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                            TextButton(onClick = { showPricingSheet = true }) {
                                Text("Full Pricing")
                            }
                        }

                        Spacer(modifier = Modifier.height(8.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            PricingItem("Hourly", "${tenant.hourlyPrice / 1000},000 VND")
                            PricingItem("Overnight", "${tenant.overnightPrice / 1000},000 VND")
                            PricingItem("Daily Cap", "${tenant.dailyPrice / 1000},000 VND")
                            PricingItem("Member Rate", "${tenant.memberHourlyPrice / 1000},000 VND", isHighlight = true)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Membership Plans Section
                if (tenant.supportsMembership) {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(16.dp),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.4f))
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.CardMembership, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Monthly Resident Membership", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                            }

                            Spacer(modifier = Modifier.height(8.dp))

                            Text(
                                text = "Get unlimited resident parking access, member pricing, and automatic LPR gate entry.",
                                fontSize = 13.sp,
                                color = MaterialTheme.colorScheme.onSurface
                            )

                            Spacer(modifier = Modifier.height(10.dp))

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column {
                                    Text("From", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                    Text(
                                        text = "${tenant.monthlyPrice / 1000},000 VND / month",
                                        fontSize = 16.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                }

                                Button(
                                    onClick = onNavigateToMemberships,
                                    shape = RoundedCornerShape(10.dp)
                                ) {
                                    Text("Join Plan")
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))
                }

                // Parking Map Preview Tile
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onOpenMap() },
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
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Surface(
                                shape = RoundedCornerShape(10.dp),
                                color = MaterialTheme.colorScheme.secondaryContainer,
                                modifier = Modifier.size(40.dp)
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Icon(Icons.Default.Map, contentDescription = null)
                                }
                            }
                            Spacer(modifier = Modifier.width(12.dp))
                            Column {
                                Text("Interactive Indoor Map", fontWeight = FontWeight.Bold, fontSize = 15.sp)
                                Text("Floor 1 · 20 spots  |  Floor 2 · 15 spots", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        }

                        Icon(Icons.Default.ChevronRight, contentDescription = null)
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Operating Hours & Facilities
                Text("Operating & Access Hours", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(6.dp))

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Public Business Hours", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(tenant.openHours, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                }
                Spacer(modifier = Modifier.height(4.dp))
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Member Gate Access", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(tenant.memberAccessHours, fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Color(0xFF10B981))
                }

                Spacer(modifier = Modifier.height(16.dp))

                Text("Facilities & Features", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(8.dp))

                val facilityList = tenant.facilities.split(",")
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    facilityList.forEach { facility ->
                        AssistChip(
                            onClick = { },
                            label = { Text(facility.replace("_", " "), fontSize = 12.sp) },
                            leadingIcon = {
                                when (facility.uppercase()) {
                                    "CCTV" -> Icon(Icons.Default.Videocam, contentDescription = null, modifier = Modifier.size(16.dp))
                                    "SECURITY" -> Icon(Icons.Default.Security, contentDescription = null, modifier = Modifier.size(16.dp))
                                    "EV_CHARGING" -> Icon(Icons.Default.ElectricCar, contentDescription = null, modifier = Modifier.size(16.dp))
                                    "ELEVATOR" -> Icon(Icons.Default.Elevator, contentDescription = null, modifier = Modifier.size(16.dp))
                                    else -> Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(16.dp))
                                }
                            }
                        )
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))
            }
        }

        // Park Now Dialog
        if (showParkNowDialog) {
            AlertDialog(
                onDismissRequest = { showParkNowDialog = false },
                title = { Text("Park Vehicle at ${tenant.name}") },
                text = {
                    Column {
                        Text("Select which vehicle you are driving into the parking lot:", fontSize = 13.sp)
                        Spacer(modifier = Modifier.height(12.dp))

                        vehicles.forEach { vehicle ->
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clip(RoundedCornerShape(10.dp))
                                    .clickable { selectedVehicle = vehicle }
                                    .background(if (selectedVehicle?.id == vehicle.id) MaterialTheme.colorScheme.primaryContainer else Color.Transparent)
                                    .padding(10.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                RadioButton(
                                    selected = selectedVehicle?.id == vehicle.id,
                                    onClick = { selectedVehicle = vehicle }
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Column {
                                    Text(vehicle.licensePlate, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                                    Text("${vehicle.brandModel} (${vehicle.color})", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                }
                            }
                        }
                    }
                },
                confirmButton = {
                    Button(
                        onClick = {
                            val veh = selectedVehicle ?: return@Button
                            showParkNowDialog = false
                            coroutineScope.launch {
                                repository.startParkingSession(
                                    tenantId = tenant.id,
                                    tenantName = tenant.name,
                                    vehicleId = veh.id,
                                    licensePlate = veh.licensePlate
                                )
                                onNavigateToMyParking()
                            }
                        },
                        enabled = selectedVehicle != null
                    ) {
                        Text("Confirm & Park")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showParkNowDialog = false }) {
                        Text("Cancel")
                    }
                }
            )
        }

        // Pricing Bottom Sheet
        if (showPricingSheet) {
            ModalBottomSheet(
                onDismissRequest = { showPricingSheet = false }
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text("Full Pricing Structure - ${tenant.name}", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(16.dp))

                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Standard Hourly Rate")
                        Text("${tenant.hourlyPrice / 1000},000 VND / hr", fontWeight = FontWeight.Bold)
                    }
                    Divider(modifier = Modifier.padding(vertical = 10.dp))

                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Overnight Rate (23:00 - 06:00)")
                        Text("${tenant.overnightPrice / 1000},000 VND / night", fontWeight = FontWeight.Bold)
                    }
                    Divider(modifier = Modifier.padding(vertical = 10.dp))

                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Daily Maximum Cap")
                        Text("${tenant.dailyPrice / 1000},000 VND / day", fontWeight = FontWeight.Bold)
                    }
                    Divider(modifier = Modifier.padding(vertical = 10.dp))

                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Resident Member Rate")
                        Text("${tenant.memberHourlyPrice / 1000},000 VND / hr", fontWeight = FontWeight.Bold, color = Color(0xFF10B981))
                    }

                    Spacer(modifier = Modifier.height(20.dp))
                    Button(
                        onClick = { showPricingSheet = false },
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
fun PricingItem(label: String, price: String, isHighlight: Boolean = false) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(label, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(
            price,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            color = if (isHighlight) Color(0xFF10B981) else MaterialTheme.colorScheme.onSurface
        )
    }
}
