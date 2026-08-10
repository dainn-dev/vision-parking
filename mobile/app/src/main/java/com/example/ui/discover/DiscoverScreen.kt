package com.example.ui.discover

import androidx.compose.animation.*
import androidx.compose.foundation.*
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.R
import com.example.data.ParkingRepository
import com.example.data.TenantEntity

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DiscoverScreen(
    repository: ParkingRepository,
    onNavigateToTenant: (String) -> Unit,
    onNavigateToMap: (String) -> Unit,
    onNavigateToMyParking: () -> Unit,
    onNavigateToFindVehicle: (String) -> Unit,
    onNavigateToNotifications: () -> Unit
) {
    val tenants by repository.allTenants.collectAsState(initial = emptyList())
    val activeSessions by repository.activeSessions.collectAsState(initial = emptyList())
    val unreadNotificationsCount by repository.unreadNotificationCount.collectAsState(initial = 0)
    val activeSession = activeSessions.firstOrNull()

    var searchQuery by remember { mutableStateOf("") }
    var selectedFilter by remember { mutableStateOf("Available") }
    var selectedTenantForPreview by remember { mutableStateOf<TenantEntity?>(null) }
    var isMapExpanded by remember { mutableStateOf(false) }

    val filteredTenants = remember(tenants, searchQuery, selectedFilter) {
        tenants.filter { tenant ->
            val matchesQuery = searchQuery.isEmpty() ||
                    tenant.name.contains(searchQuery, ignoreCase = true) ||
                    tenant.address.contains(searchQuery, ignoreCase = true) ||
                    tenant.district.contains(searchQuery, ignoreCase = true)

            val matchesFilter = when (selectedFilter) {
                "Available" -> tenant.availableCapacity > 0
                "Cheapest" -> tenant.hourlyPrice <= 20000
                "Within 1km" -> tenant.distanceMeters <= 1000
                "24/7" -> tenant.openHours.contains("24/7", ignoreCase = true)
                "EV Charging" -> tenant.facilities.contains("EV_CHARGING", ignoreCase = true)
                else -> true
            }

            matchesQuery && matchesFilter
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.LocationOn,
                                contentDescription = "Location",
                                tint = MaterialTheme.colorScheme.primary,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                text = "District 7, Ho Chi Minh City",
                                fontSize = 14.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                            Icon(
                                imageVector = Icons.Default.KeyboardArrowDown,
                                contentDescription = "Change Location",
                                modifier = Modifier.size(18.dp)
                            )
                        }
                        Text(
                            text = "Where do you want to park?",
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                },
                actions = {
                    IconButton(onClick = onNavigateToNotifications) {
                        BadgedBox(
                            badge = {
                                if (unreadNotificationsCount > 0) {
                                    Badge { Text("$unreadNotificationsCount") }
                                }
                            }
                        ) {
                            Icon(Icons.Outlined.Notifications, contentDescription = "Notifications")
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background
                )
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            // Active Parking Banner (If user currently has an active session)
            if (activeSession != null) {
                ActiveParkingBanner(
                    session = activeSession!!,
                    onNavigateToMyParking = onNavigateToMyParking,
                    onNavigateToFindVehicle = { onNavigateToFindVehicle(activeSession!!.id) }
                )
                Spacer(modifier = Modifier.height(12.dp))
            }

            // Search Bar
            SearchBarSection(
                query = searchQuery,
                onQueryChange = { searchQuery = it }
            )

            Spacer(modifier = Modifier.height(10.dp))

            // Filter Chips
            FilterChipsSection(
                selectedFilter = selectedFilter,
                onFilterSelected = { selectedFilter = it }
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Interactive Map Visual Component
            InteractiveMapCanvas(
                tenants = filteredTenants,
                selectedTenant = selectedTenantForPreview,
                onSelectTenant = { tenant ->
                    selectedTenantForPreview = tenant
                },
                isExpanded = isMapExpanded,
                onToggleExpand = { isMapExpanded = !isMapExpanded }
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Nearby Parking Section Header
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "Nearby Parking",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "${filteredTenants.size} facilities found near you",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }

                TextButton(onClick = { searchQuery = ""; selectedFilter = "All" }) {
                    Text("View all")
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Nearby Parking Cards List
            filteredTenants.forEach { tenant ->
                TenantCard(
                    tenant = tenant,
                    onCardClick = { onNavigateToTenant(tenant.id) },
                    onMapClick = { onNavigateToMap(tenant.id) }
                )
                Spacer(modifier = Modifier.height(12.dp))
            }

            Spacer(modifier = Modifier.height(24.dp))
        }

        // Preview Bottom Sheet when a tenant marker is clicked on the map
        if (selectedTenantForPreview != null) {
            ModalBottomSheet(
                onDismissRequest = { selectedTenantForPreview = null },
                sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
            ) {
                TenantPreviewContent(
                    tenant = selectedTenantForPreview!!,
                    onViewDetails = {
                        val id = selectedTenantForPreview!!.id
                        selectedTenantForPreview = null
                        onNavigateToTenant(id)
                    },
                    onOpenMap = {
                        val id = selectedTenantForPreview!!.id
                        selectedTenantForPreview = null
                        onNavigateToMap(id)
                    }
                )
            }
        }
    }
}

@Composable
fun ActiveParkingBanner(
    session: com.example.data.ParkingSessionEntity,
    onNavigateToMyParking: () -> Unit,
    onNavigateToFindVehicle: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp)
            .clickable { onNavigateToMyParking() },
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF1E293B)
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 6.dp)
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
                            .background(Color(0xFF10B981))
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "ACTIVE PARKING SESSION",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF10B981),
                        letterSpacing = 0.5.sp
                    )
                }

                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = Color(0xFF334155)
                ) {
                    Text(
                        text = session.licensePlate,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            Text(
                text = session.tenantName,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 4.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Spot: ${session.floorName} · ${session.zoneName} · ${session.spotCode}",
                    fontSize = 13.sp,
                    color = Color(0xFF94A3B8)
                )
                Text(
                    text = "Current: 40,000 VND",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF38BDF8)
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(
                    onClick = onNavigateToFindVehicle,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2563EB)),
                    shape = RoundedCornerShape(10.dp),
                    contentPadding = PaddingValues(vertical = 8.dp)
                ) {
                    Icon(Icons.Default.Navigation, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Find My Vehicle", fontSize = 13.sp, fontWeight = FontWeight.Bold)
                }

                OutlinedButton(
                    onClick = onNavigateToMyParking,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(10.dp),
                    border = BorderStroke(1.dp, Color(0xFF475569)),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White),
                    contentPadding = PaddingValues(vertical = 8.dp)
                ) {
                    Text("Dashboard", fontSize = 13.sp)
                }
            }
        }
    }
}

@Composable
fun SearchBarSection(
    query: String,
    onQueryChange: (String) -> Unit
) {
    OutlinedTextField(
        value = query,
        onValueChange = onQueryChange,
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp),
        placeholder = { Text("Search parking lot, address, district...", fontSize = 14.sp) },
        leadingIcon = {
            Icon(Icons.Default.Search, contentDescription = "Search", tint = MaterialTheme.colorScheme.primary)
        },
        trailingIcon = {
            if (query.isNotEmpty()) {
                IconButton(onClick = { onQueryChange("") }) {
                    Icon(Icons.Default.Clear, contentDescription = "Clear")
                }
            }
        },
        singleLine = true,
        shape = RoundedCornerShape(14.dp),
        colors = OutlinedTextFieldDefaults.colors(
            unfocusedContainerColor = MaterialTheme.colorScheme.surface,
            focusedContainerColor = MaterialTheme.colorScheme.surface
        )
    )
}

@Composable
fun FilterChipsSection(
    selectedFilter: String,
    onFilterSelected: (String) -> Unit
) {
    val filters = listOf("All", "Available", "Cheapest", "Within 1km", "24/7", "EV Charging")

    LazyRow(
        contentPadding = PaddingValues(horizontal = 16.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(filters) { filter ->
            val isSelected = filter == selectedFilter
            FilterChip(
                selected = isSelected,
                onClick = { onFilterSelected(filter) },
                label = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        if (filter == "Available") {
                            Box(
                                modifier = Modifier
                                    .size(6.dp)
                                    .clip(CircleShape)
                                    .background(Color(0xFF10B981))
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                        }
                        if (filter == "EV Charging") {
                            Icon(Icons.Default.ElectricCar, contentDescription = null, modifier = Modifier.size(14.dp))
                            Spacer(modifier = Modifier.width(4.dp))
                        }
                        Text(filter, fontSize = 13.sp)
                    }
                },
                colors = FilterChipDefaults.filterChipColors(
                    selectedContainerColor = MaterialTheme.colorScheme.primary,
                    selectedLabelColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    }
}

@Composable
fun InteractiveMapCanvas(
    tenants: List<TenantEntity>,
    selectedTenant: TenantEntity?,
    onSelectTenant: (TenantEntity) -> Unit,
    isExpanded: Boolean,
    onToggleExpand: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp)
            .height(if (isExpanded) 320.dp else 190.dp),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A))
    ) {
        Box(modifier = Modifier.fillMaxSize()) {
            // Stylized Dark Map Background Grid
            Canvas(modifier = Modifier.fillMaxSize()) {
                val gridColor = Color(0xFF1E293B)
                val strokeWidth = 2.dp.toPx()
                val step = 40.dp.toPx()

                for (x in 0..size.width.toInt() step step.toInt()) {
                    drawLine(gridColor, Offset(x.toFloat(), 0f), Offset(x.toFloat(), size.height), strokeWidth)
                }
                for (y in 0..size.height.toInt() step step.toInt()) {
                    drawLine(gridColor, Offset(0f, y.toFloat()), Offset(size.width, y.toFloat()), strokeWidth)
                }

                // Roads styling
                drawLine(Color(0xFF334155), Offset(0f, size.height * 0.5f), Offset(size.width, size.height * 0.5f), strokeWidth = 24.dp.toPx())
                drawLine(Color(0xFF334155), Offset(size.width * 0.4f, 0f), Offset(size.width * 0.4f, size.height), strokeWidth = 20.dp.toPx())
            }

            // User Location Marker
            Box(
                modifier = Modifier
                    .align(Alignment.Center)
                    .offset(x = (-30).dp, y = 20.dp)
            ) {
                Surface(
                    shape = CircleShape,
                    color = Color(0xFF38BDF8).copy(alpha = 0.3f),
                    modifier = Modifier.size(32.dp)
                ) {}
                Box(
                    modifier = Modifier
                        .size(14.dp)
                        .clip(CircleShape)
                        .background(Color(0xFF0284C7))
                        .align(Alignment.Center)
                )
            }

            // Tenant Markers on Map
            tenants.forEachIndexed { index, tenant ->
                val xOffset = when (index % 3) {
                    0 -> (-80).dp
                    1 -> 70.dp
                    else -> 10.dp
                }
                val yOffset = when (index % 3) {
                    0 -> (-40).dp
                    1 -> (-20).dp
                    else -> 50.dp
                }

                val isSelected = tenant.id == selectedTenant?.id
                val badgeColor = when {
                    tenant.availableCapacity > 20 -> Color(0xFF10B981)
                    tenant.availableCapacity > 0 -> Color(0xFFF59E0B)
                    else -> Color(0xFFEF4444)
                }

                Surface(
                    modifier = Modifier
                        .align(Alignment.Center)
                        .offset(x = xOffset, y = yOffset)
                        .clickable { onSelectTenant(tenant) },
                    shape = RoundedCornerShape(12.dp),
                    color = if (isSelected) Color(0xFF2563EB) else Color(0xFF1E293B),
                    border = BorderStroke(1.5.dp, badgeColor),
                    shadowElevation = 4.dp
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(6.dp)
                                .clip(CircleShape)
                                .background(badgeColor)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = if (tenant.availableCapacity == 0) "FULL" else "${tenant.hourlyPrice / 1000}k",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                    }
                }
            }

            // Map Overlay Watermark / Controls
            Row(
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(12.dp),
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Surface(
                    shape = CircleShape,
                    color = Color(0xFF1E293B).copy(alpha = 0.8f),
                    modifier = Modifier
                        .size(32.dp)
                        .clickable { onToggleExpand() }
                ) {
                    Icon(
                        imageVector = if (isExpanded) Icons.Default.FullscreenExit else Icons.Default.Fullscreen,
                        contentDescription = "Expand Map",
                        tint = Color.White,
                        modifier = Modifier.padding(6.dp)
                    )
                }
            }

            Surface(
                modifier = Modifier
                    .align(Alignment.BottomStart)
                    .padding(12.dp),
                shape = RoundedCornerShape(8.dp),
                color = Color(0xFF0F172A).copy(alpha = 0.85f)
            ) {
                Text(
                    text = "🗺️ 2D Interactive Parking Map",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = Color(0xFF94A3B8),
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                )
            }
        }
    }
}

@Composable
fun TenantCard(
    tenant: TenantEntity,
    onCardClick: () -> Unit,
    onMapClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp)
            .clickable { onCardClick() },
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f)) {
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = MaterialTheme.colorScheme.primaryContainer,
                        modifier = Modifier.size(44.dp)
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Text(
                                text = tenant.name.take(2).uppercase(),
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                        }
                    }

                    Spacer(modifier = Modifier.width(10.dp))

                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = tenant.name,
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                            if (tenant.verified) {
                                Spacer(modifier = Modifier.width(4.dp))
                                Icon(
                                    imageVector = Icons.Default.CheckCircle,
                                    contentDescription = "Verified",
                                    tint = Color(0xFF0284C7),
                                    modifier = Modifier.size(16.dp)
                                )
                            }
                        }

                        Text(
                            text = "${tenant.category} · ${tenant.district}",
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }

                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Star, contentDescription = null, tint = Color(0xFFF59E0B), modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(2.dp))
                    Text(text = "${tenant.rating}", fontSize = 13.sp, fontWeight = FontWeight.Bold)
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Capacity Bar
            val capRatio = tenant.availableCapacity.toFloat() / tenant.totalCapacity.coerceAtLeast(1)
            val capColor = when {
                tenant.availableCapacity > 20 -> Color(0xFF10B981)
                tenant.availableCapacity > 0 -> Color(0xFFF59E0B)
                else -> Color(0xFFEF4444)
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .clip(CircleShape)
                            .background(capColor)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = if (tenant.availableCapacity > 0) "${tenant.availableCapacity} spots available" else "Full",
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = capColor
                    )
                }

                Text(
                    text = "${tenant.totalCapacity - tenant.availableCapacity} / ${tenant.totalCapacity} occupied",
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Spacer(modifier = Modifier.height(6.dp))

            LinearProgressIndicator(
                progress = { 1f - capRatio },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(6.dp)
                    .clip(RoundedCornerShape(3.dp)),
                color = capColor,
                trackColor = MaterialTheme.colorScheme.surfaceVariant
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Pricing & Actions Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "From ${tenant.hourlyPrice / 1000},000 VND/hr",
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    if (tenant.supportsMembership) {
                        Text(
                            text = "Member: ${tenant.memberHourlyPrice / 1000}k/hr",
                            fontSize = 11.sp,
                            color = Color(0xFF10B981),
                            fontWeight = FontWeight.Medium
                        )
                    }
                }

                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(
                        onClick = onMapClick,
                        shape = RoundedCornerShape(10.dp),
                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                    ) {
                        Icon(Icons.Default.Map, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Map", fontSize = 12.sp)
                    }

                    Button(
                        onClick = onCardClick,
                        shape = RoundedCornerShape(10.dp),
                        contentPadding = PaddingValues(horizontal = 14.dp, vertical = 6.dp)
                    ) {
                        Text("Details", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}

@Composable
fun TenantPreviewContent(
    tenant: TenantEntity,
    onViewDetails: () -> Unit,
    onOpenMap: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(20.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = tenant.name,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "${tenant.address}, ${tenant.district} · ${tenant.distanceMeters}m away",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Surface(
                shape = RoundedCornerShape(8.dp),
                color = MaterialTheme.colorScheme.primaryContainer
            ) {
                Text(
                    text = "⭐ ${tenant.rating}",
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column {
                Text("Availability", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(
                    text = "🟢 ${tenant.availableCapacity} / ${tenant.totalCapacity} spots",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF10B981)
                )
            }

            Column {
                Text("Hourly Rate", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(
                    text = "${tenant.hourlyPrice / 1000},000 VND",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Column {
                Text("Member Rate", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(
                    text = "${tenant.memberHourlyPrice / 1000},000 VND",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            OutlinedButton(
                onClick = onOpenMap,
                modifier = Modifier.weight(1f),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.Layers, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text("Indoor Map")
            }

            Button(
                onClick = onViewDetails,
                modifier = Modifier.weight(1f),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("View Full Facility")
            }
        }
    }
}
