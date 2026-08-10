package com.example.ui.notifications

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.NotificationEntity
import com.example.data.ParkingRepository
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NotificationsScreen(
    repository: ParkingRepository,
    onBack: () -> Unit,
    onNavigateToMyParking: () -> Unit,
    onNavigateToMemberships: () -> Unit,
    onNavigateToHistory: () -> Unit,
    onNavigateToSecurity: () -> Unit
) {
    val coroutineScope = rememberCoroutineScope()
    val notifications by repository.allNotifications.collectAsState(initial = emptyList())
    val unreadCount by repository.unreadNotificationCount.collectAsState(initial = 0)

    var selectedTab by remember { mutableStateOf(0) } // 0: All, 1: Unread
    var selectedCategory by remember { mutableStateOf("ALL") }

    var selectedNotificationForPreview by remember { mutableStateOf<NotificationEntity?>(null) }
    var showPreferencesSheet by remember { mutableStateOf(false) }

    val snackbarHostState = remember { SnackbarHostState() }

    // Filter notifications based on tab and category
    val filteredNotifications = remember(notifications, selectedTab, selectedCategory) {
        notifications.filter { notification ->
            val matchesTab = if (selectedTab == 1) !notification.isRead else true
            val matchesCategory = if (selectedCategory == "ALL") true else notification.category.equals(selectedCategory, ignoreCase = true)
            matchesTab && matchesCategory
        }
    }

    // Group notifications by relative date
    val groupedNotifications = remember(filteredNotifications) {
        val now = System.currentTimeMillis()
        val oneDayMillis = 24 * 3600 * 1000L

        filteredNotifications.groupBy { notification ->
            val diff = now - notification.createdAt
            when {
                diff < oneDayMillis -> "Today"
                diff < 2 * oneDayMillis -> "Yesterday"
                else -> "Earlier"
            }
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = "Notifications",
                            fontWeight = FontWeight.Bold
                        )
                        if (unreadCount > 0) {
                            Spacer(modifier = Modifier.width(8.dp))
                            Surface(
                                shape = CircleShape,
                                color = MaterialTheme.colorScheme.primaryContainer
                            ) {
                                Text(
                                    text = "$unreadCount",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp)
                                )
                            }
                        }
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    if (unreadCount > 0) {
                        TextButton(
                            onClick = {
                                coroutineScope.launch {
                                    repository.markAllNotificationsRead()
                                    snackbarHostState.showSnackbar("All notifications marked as read")
                                }
                            }
                        ) {
                            Icon(
                                imageVector = Icons.Default.DoneAll,
                                contentDescription = null,
                                modifier = Modifier.size(16.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                text = "Read all",
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }

                    IconButton(onClick = { showPreferencesSheet = true }) {
                        Icon(Icons.Outlined.Settings, contentDescription = "Notification Settings")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background
                )
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            // Tabs: All vs Unread
            TabRow(
                selectedTabIndex = selectedTab,
                containerColor = MaterialTheme.colorScheme.surface,
                contentColor = MaterialTheme.colorScheme.primary,
                divider = { HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f)) }
            ) {
                Tab(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    text = {
                        Text(
                            text = "All (${notifications.size})",
                            fontWeight = if (selectedTab == 0) FontWeight.Bold else FontWeight.Medium
                        )
                    }
                )
                Tab(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    text = {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = "Unread",
                                fontWeight = if (selectedTab == 1) FontWeight.Bold else FontWeight.Medium
                            )
                            if (unreadCount > 0) {
                                Spacer(modifier = Modifier.width(6.dp))
                                Box(
                                    modifier = Modifier
                                        .size(8.dp)
                                        .clip(CircleShape)
                                        .background(Color(0xFF10B981))
                                )
                            }
                        }
                    }
                )
            }

            // Category Filter Chips Row
            val categories = listOf(
                "ALL" to "All",
                "PARKING" to "Parking",
                "MEMBERSHIP" to "Membership",
                "PAYMENT" to "Payment",
                "SECURITY" to "Security",
                "SYSTEM" to "System"
            )

            LazyRow(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 10.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(categories) { (code, label) ->
                    val isSelected = selectedCategory == code
                    FilterChip(
                        selected = isSelected,
                        onClick = { selectedCategory = code },
                        label = {
                            Text(
                                text = label,
                                fontSize = 12.sp,
                                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
                            )
                        },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = MaterialTheme.colorScheme.primary,
                            selectedLabelColor = MaterialTheme.colorScheme.onPrimary
                        ),
                        shape = RoundedCornerShape(20.dp)
                    )
                }
            }

            // Notifications List / Empty State
            if (filteredNotifications.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Surface(
                            shape = CircleShape,
                            color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.4f),
                            modifier = Modifier.size(80.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    imageVector = if (selectedTab == 1) Icons.Outlined.CheckCircle else Icons.Outlined.NotificationsNone,
                                    contentDescription = null,
                                    modifier = Modifier.size(40.dp),
                                    tint = MaterialTheme.colorScheme.primary
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(16.dp))

                        Text(
                            text = if (selectedTab == 1) "You're all caught up!" else "No notifications found",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )

                        Spacer(modifier = Modifier.height(6.dp))

                        Text(
                            text = if (selectedTab == 1)
                                "There are no unread notifications right now."
                            else
                                "You will receive real-time updates about parking sessions, memberships, payments, and security.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            textAlign = androidx.compose.ui.text.style.TextAlign.Center
                        )
                    }
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    val groupOrder = listOf("Today", "Yesterday", "Earlier")

                    groupOrder.forEach { dateHeader ->
                        val itemsInGroup = groupedNotifications[dateHeader]
                        if (!itemsInGroup.isNullOrEmpty()) {
                            item(key = "header_$dateHeader") {
                                Text(
                                    text = dateHeader,
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.primary,
                                    modifier = Modifier.padding(start = 4.dp, top = 8.dp, bottom = 4.dp)
                                )
                            }

                            items(
                                items = itemsInGroup,
                                key = { it.id }
                            ) { notification ->
                                NotificationCardItem(
                                    notification = notification,
                                    onClick = {
                                        coroutineScope.launch {
                                            repository.markNotificationRead(notification.id)
                                        }
                                        handleNotificationTarget(
                                            notification = notification,
                                            onNavigateToMyParking = onNavigateToMyParking,
                                            onNavigateToMemberships = onNavigateToMemberships,
                                            onNavigateToHistory = onNavigateToHistory,
                                            onNavigateToSecurity = onNavigateToSecurity,
                                            onShowPreview = { selectedNotificationForPreview = notification }
                                        )
                                    },
                                    onMoreClick = {
                                        selectedNotificationForPreview = notification
                                    },
                                    onMarkReadToggle = {
                                        coroutineScope.launch {
                                            if (notification.isRead) {
                                                repository.markNotificationUnread(notification.id)
                                            } else {
                                                repository.markNotificationRead(notification.id)
                                            }
                                        }
                                    },
                                    onDelete = {
                                        coroutineScope.launch {
                                            repository.deleteNotification(notification)
                                            snackbarHostState.showSnackbar("Notification deleted")
                                        }
                                    }
                                )
                            }
                        }
                    }

                    item {
                        Spacer(modifier = Modifier.height(16.dp))
                    }
                }
            }
        }

        // Notification Preview BottomSheet
        if (selectedNotificationForPreview != null) {
            val item = selectedNotificationForPreview!!
            ModalBottomSheet(
                onDismissRequest = { selectedNotificationForPreview = null },
                containerColor = MaterialTheme.colorScheme.surface
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        CategoryIconBox(category = item.category, severity = item.severity)
                        Spacer(modifier = Modifier.width(12.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = item.title,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                            if (!item.tenantName.isNullOrEmpty()) {
                                Text(
                                    text = item.tenantName,
                                    fontSize = 12.sp,
                                    color = MaterialTheme.colorScheme.primary,
                                    fontWeight = FontWeight.SemiBold
                                )
                            }
                        }
                        SeverityBadge(severity = item.severity)
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f))

                    Spacer(modifier = Modifier.height(16.dp))

                    Text(
                        text = item.message,
                        fontSize = 14.sp,
                        color = MaterialTheme.colorScheme.onSurface,
                        lineHeight = 20.sp
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    Text(
                        text = "Received " + formatTimestamp(item.createdAt),
                        fontSize = 11.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    Spacer(modifier = Modifier.height(24.dp))

                    // Primary Action Button
                    Button(
                        onClick = {
                            val notif = selectedNotificationForPreview
                            selectedNotificationForPreview = null
                            if (notif != null) {
                                coroutineScope.launch { repository.markNotificationRead(notif.id) }
                                handleNotificationTarget(
                                    notification = notif,
                                    onNavigateToMyParking = onNavigateToMyParking,
                                    onNavigateToMemberships = onNavigateToMemberships,
                                    onNavigateToHistory = onNavigateToHistory,
                                    onNavigateToSecurity = onNavigateToSecurity,
                                    onShowPreview = {}
                                )
                            }
                        },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Text(
                            text = getActionTextForNotification(item),
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Icon(Icons.Default.ArrowForward, contentDescription = null, modifier = Modifier.size(16.dp))
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    // Secondary Action: Delete
                    OutlinedButton(
                        onClick = {
                            val notif = selectedNotificationForPreview
                            selectedNotificationForPreview = null
                            if (notif != null) {
                                coroutineScope.launch {
                                    repository.deleteNotification(notif)
                                    snackbarHostState.showSnackbar("Notification deleted")
                                }
                            }
                        },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFFEF4444))
                    ) {
                        Icon(Icons.Default.DeleteOutline, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Delete Notification")
                    }

                    Spacer(modifier = Modifier.height(16.dp))
                }
            }
        }

        // Notification Preferences BottomSheet
        if (showPreferencesSheet) {
            NotificationPreferencesSheet(
                onDismiss = { showPreferencesSheet = false },
                onSaved = {
                    coroutineScope.launch {
                        snackbarHostState.showSnackbar("Notification preferences saved")
                    }
                }
            )
        }
    }
}

@Composable
fun NotificationCardItem(
    notification: NotificationEntity,
    onClick: () -> Unit,
    onMoreClick: () -> Unit,
    onMarkReadToggle: () -> Unit,
    onDelete: () -> Unit
) {
    var expandedMenu by remember { mutableStateOf(false) }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() },
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (!notification.isRead)
                MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.12f)
            else
                MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(if (!notification.isRead) 3.dp else 1.dp)
    ) {
        Column(
            modifier = Modifier.padding(14.dp)
        ) {
            Row(
                verticalAlignment = Alignment.Top
            ) {
                // Category Icon
                CategoryIconBox(category = notification.category, severity = notification.severity)

                Spacer(modifier = Modifier.width(12.dp))

                Column(
                    modifier = Modifier.weight(1f)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.weight(1f)
                        ) {
                            if (!notification.isRead) {
                                Box(
                                    modifier = Modifier
                                        .size(8.dp)
                                        .clip(CircleShape)
                                        .background(Color(0xFF10B981))
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                            }

                            Text(
                                text = notification.title,
                                fontWeight = if (!notification.isRead) FontWeight.Bold else FontWeight.SemiBold,
                                fontSize = 14.sp,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        }

                        Text(
                            text = formatRelativeTime(notification.createdAt),
                            fontSize = 11.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.padding(start = 6.dp)
                        )
                    }

                    if (!notification.tenantName.isNullOrEmpty()) {
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = notification.tenantName,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = notification.message,
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                        lineHeight = 16.sp
                    )
                }

                Box {
                    IconButton(
                        onClick = { expandedMenu = true },
                        modifier = Modifier.size(28.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.MoreVert,
                            contentDescription = "Options",
                            modifier = Modifier.size(16.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }

                    DropdownMenu(
                        expanded = expandedMenu,
                        onDismissRequest = { expandedMenu = false }
                    ) {
                        DropdownMenuItem(
                            text = { Text(if (notification.isRead) "Mark as Unread" else "Mark as Read") },
                            leadingIcon = {
                                Icon(
                                    if (notification.isRead) Icons.Outlined.MarkEmailUnread else Icons.Outlined.Drafts,
                                    contentDescription = null
                                )
                            },
                            onClick = {
                                expandedMenu = false
                                onMarkReadToggle()
                            }
                        )
                        DropdownMenuItem(
                            text = { Text("Preview Details") },
                            leadingIcon = { Icon(Icons.Outlined.Visibility, contentDescription = null) },
                            onClick = {
                                expandedMenu = false
                                onMoreClick()
                            }
                        )
                        HorizontalDivider()
                        DropdownMenuItem(
                            text = { Text("Delete", color = Color(0xFFEF4444)) },
                            leadingIcon = { Icon(Icons.Outlined.Delete, contentDescription = null, tint = Color(0xFFEF4444)) },
                            onClick = {
                                expandedMenu = false
                                onDelete()
                            }
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Severity Badge Footer Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                SeverityBadge(severity = notification.severity)

                Text(
                    text = getActionTextForNotification(notification),
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
            }
        }
    }
}

@Composable
fun CategoryIconBox(category: String, severity: String) {
    val (icon, bgColor, iconColor) = when (category.uppercase()) {
        "PARKING" -> Triple(
            Icons.Default.DirectionsCar,
            MaterialTheme.colorScheme.primaryContainer,
            MaterialTheme.colorScheme.primary
        )
        "MEMBERSHIP" -> Triple(
            Icons.Default.CardMembership,
            Color(0xFF06B6D4).copy(alpha = 0.15f),
            Color(0xFF06B6D4)
        )
        "PAYMENT" -> Triple(
            Icons.Default.AccountBalanceWallet,
            Color(0xFF10B981).copy(alpha = 0.15f),
            Color(0xFF10B981)
        )
        "SECURITY" -> Triple(
            Icons.Default.Security,
            Color(0xFF8B5CF6).copy(alpha = 0.15f),
            Color(0xFF8B5CF6)
        )
        else -> Triple(
            Icons.Default.Notifications,
            MaterialTheme.colorScheme.surfaceVariant,
            MaterialTheme.colorScheme.onSurfaceVariant
        )
    }

    Surface(
        shape = RoundedCornerShape(12.dp),
        color = bgColor,
        modifier = Modifier.size(40.dp)
    ) {
        Box(contentAlignment = Alignment.Center) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = iconColor,
                modifier = Modifier.size(20.dp)
            )
        }
    }
}

@Composable
fun SeverityBadge(severity: String) {
    val (label, bg, fg) = when (severity.uppercase()) {
        "SUCCESS" -> Triple("Success", Color(0xFF10B981).copy(alpha = 0.15f), Color(0xFF10B981))
        "WARNING" -> Triple("Warning", Color(0xFFF59E0B).copy(alpha = 0.15f), Color(0xFFD97706))
        "ACTION_REQUIRED" -> Triple("Action Required", Color(0xFFEF4444).copy(alpha = 0.15f), Color(0xFFEF4444))
        "SECURITY" -> Triple("Security Alert", Color(0xFF8B5CF6).copy(alpha = 0.15f), Color(0xFF8B5CF6))
        else -> Triple("Info", MaterialTheme.colorScheme.primary.copy(alpha = 0.12f), MaterialTheme.colorScheme.primary)
    }

    Surface(
        shape = RoundedCornerShape(6.dp),
        color = bg
    ) {
        Text(
            text = label,
            fontSize = 10.sp,
            fontWeight = FontWeight.Bold,
            color = fg,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp)
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NotificationPreferencesSheet(
    onDismiss: () -> Unit,
    onSaved: () -> Unit
) {
    var parkingAlerts by remember { mutableStateOf(true) }
    var membershipAlerts by remember { mutableStateOf(true) }
    var paymentAlerts by remember { mutableStateOf(true) }
    var securityAlerts by remember { mutableStateOf(true) } // Lock to true
    var marketingAlerts by remember { mutableStateOf(false) }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = MaterialTheme.colorScheme.surface
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp, vertical = 16.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = "Notification Settings",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                IconButton(onClick = onDismiss) {
                    Icon(Icons.Default.Close, contentDescription = "Close")
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = "Customize which real-time alerts you wish to receive.",
                fontSize = 12.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            Spacer(modifier = Modifier.height(16.dp))

            HorizontalDivider()

            Spacer(modifier = Modifier.height(12.dp))

            PreferenceToggleRow(
                title = "Parking Session Alerts",
                subtitle = "Vehicle entry, spot assignment, exit detections",
                icon = Icons.Default.DirectionsCar,
                checked = parkingAlerts,
                onCheckedChange = { parkingAlerts = it }
            )

            PreferenceToggleRow(
                title = "Membership Expiry & Status",
                subtitle = "Renewal warnings, approval decisions",
                icon = Icons.Default.CardMembership,
                checked = membershipAlerts,
                onCheckedChange = { membershipAlerts = it }
            )

            PreferenceToggleRow(
                title = "Payment & Billing Receipts",
                subtitle = "Parking fee receipts, payment failure alerts",
                icon = Icons.Default.AccountBalanceWallet,
                checked = paymentAlerts,
                onCheckedChange = { paymentAlerts = it }
            )

            PreferenceToggleRow(
                title = "Security & Account Activity",
                subtitle = "New logins, password updates (Mandatory)",
                icon = Icons.Default.Security,
                checked = securityAlerts,
                onCheckedChange = { },
                enabled = false
            )

            PreferenceToggleRow(
                title = "Promotional & Marketing",
                subtitle = "Discount offers and tenant promotions",
                icon = Icons.Default.LocalOffer,
                checked = marketingAlerts,
                onCheckedChange = { marketingAlerts = it }
            )

            Spacer(modifier = Modifier.height(24.dp))

            Button(
                onClick = {
                    onSaved()
                    onDismiss()
                },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("Save Preferences", fontWeight = FontWeight.Bold)
            }

            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

@Composable
fun PreferenceToggleRow(
    title: String,
    subtitle: String,
    icon: ImageVector,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    enabled: Boolean = true
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Surface(
            shape = RoundedCornerShape(10.dp),
            color = MaterialTheme.colorScheme.surfaceVariant,
            modifier = Modifier.size(36.dp)
        ) {
            Box(contentAlignment = Alignment.Center) {
                Icon(icon, contentDescription = null, modifier = Modifier.size(18.dp), tint = MaterialTheme.colorScheme.primary)
            }
        }

        Spacer(modifier = Modifier.width(12.dp))

        Column(modifier = Modifier.weight(1f)) {
            Text(title, fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
            Text(subtitle, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }

        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            enabled = enabled
        )
    }
}

private fun handleNotificationTarget(
    notification: NotificationEntity,
    onNavigateToMyParking: () -> Unit,
    onNavigateToMemberships: () -> Unit,
    onNavigateToHistory: () -> Unit,
    onNavigateToSecurity: () -> Unit,
    onShowPreview: () -> Unit
) {
    when (notification.targetType?.uppercase()) {
        "PARKING_SESSION" -> {
            if (notification.type == "PARKING_STARTED") {
                onNavigateToMyParking()
            } else {
                onNavigateToHistory()
            }
        }
        "MEMBERSHIP" -> onNavigateToMemberships()
        "SECURITY" -> onNavigateToSecurity()
        else -> onShowPreview()
    }
}

private fun getActionTextForNotification(notification: NotificationEntity): String {
    return when (notification.targetType?.uppercase()) {
        "PARKING_SESSION" -> if (notification.type == "PARKING_STARTED") "View Active Parking →" else "View Parking History →"
        "MEMBERSHIP" -> "View Membership →"
        "SECURITY" -> "Review Security →"
        else -> "View Details →"
    }
}

private fun formatRelativeTime(timestamp: Long): String {
    val diff = System.currentTimeMillis() - timestamp
    val seconds = diff / 1000
    val minutes = seconds / 60
    val hours = minutes / 60
    val days = hours / 24

    return when {
        minutes < 1 -> "Just now"
        minutes < 60 -> "${minutes}m ago"
        hours < 24 -> "${hours}h ago"
        days < 7 -> "${days}d ago"
        else -> {
            val sdf = SimpleDateFormat("MMM dd", Locale.getDefault())
            sdf.format(Date(timestamp))
        }
    }
}

private fun formatTimestamp(timestamp: Long): String {
    val sdf = SimpleDateFormat("EEEE, MMM dd, yyyy · HH:mm", Locale.getDefault())
    return sdf.format(Date(timestamp))
}
