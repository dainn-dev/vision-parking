package com.example.ui.navigation

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.navArgument
import com.example.data.ParkingRepository
import com.example.ui.discover.DiscoverScreen
import com.example.ui.findvehicle.FindVehicleScreen
import com.example.ui.history.ParkingHistoryScreen
import com.example.ui.memberships.MembershipsScreen
import com.example.ui.myparking.MyParkingScreen
import com.example.ui.notifications.NotificationsScreen
import com.example.ui.parkingmap.ParkingMapScreen
import com.example.ui.profile.ProfileScreen
import com.example.ui.profile.SecurityScreen
import com.example.ui.profile.VehiclesScreen
import com.example.ui.tenant.TenantDetailScreen

object NavRoutes {
    const val DISCOVER = "discover"
    const val TENANT_DETAIL = "tenant_detail/{tenantId}"
    const val PARKING_MAP = "parking_map/{tenantId}"
    const val MY_PARKING = "my_parking"
    const val FIND_VEHICLE = "find_vehicle/{sessionId}"
    const val MEMBERSHIPS = "memberships"
    const val PARKING_HISTORY = "parking_history"
    const val PROFILE = "profile"
    const val VEHICLES = "vehicles"
    const val SECURITY = "security"
    const val NOTIFICATIONS = "notifications"

    fun tenantDetail(tenantId: String) = "tenant_detail/$tenantId"
    fun parkingMap(tenantId: String) = "parking_map/$tenantId"
    fun findVehicle(sessionId: String) = "find_vehicle/$sessionId"
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VisionNavHost(
    navController: NavHostController,
    repository: ParkingRepository
) {
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    val activeSessions by repository.activeSessions.collectAsState(initial = emptyList())
    val hasActiveSession = activeSessions.isNotEmpty()

    val showBottomBar = currentRoute in listOf(
        NavRoutes.DISCOVER,
        NavRoutes.MY_PARKING,
        NavRoutes.MEMBERSHIPS,
        NavRoutes.PROFILE
    )

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar(
                    containerColor = MaterialTheme.colorScheme.surface,
                    contentColor = MaterialTheme.colorScheme.onSurface,
                    tonalElevation = 12.dp
                ) {
                    val items = listOf(
                        BottomNavItem("Discover", NavRoutes.DISCOVER, Icons.Filled.Explore, Icons.Outlined.Explore),
                        BottomNavItem("My Parking", NavRoutes.MY_PARKING, Icons.Filled.DirectionsCar, Icons.Outlined.DirectionsCar, hasBadge = hasActiveSession),
                        BottomNavItem("Memberships", NavRoutes.MEMBERSHIPS, Icons.Filled.CardMembership, Icons.Outlined.CardMembership),
                        BottomNavItem("Profile", NavRoutes.PROFILE, Icons.Filled.Person, Icons.Outlined.Person)
                    )

                    items.forEach { item ->
                        val selected = currentRoute == item.route
                        NavigationBarItem(
                            selected = selected,
                            onClick = {
                                if (currentRoute != item.route) {
                                    navController.navigate(item.route) {
                                        popUpTo(NavRoutes.DISCOVER) { saveState = true }
                                        launchSingleTop = true
                                        restoreState = true
                                    }
                                }
                            },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = MaterialTheme.colorScheme.primary,
                                selectedTextColor = MaterialTheme.colorScheme.primary,
                                indicatorColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.15f),
                                unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant
                            ),
                            icon = {
                                BadgedBox(
                                    badge = {
                                        if (item.hasBadge) {
                                            Box(
                                                modifier = Modifier
                                                    .size(8.dp)
                                                    .clip(CircleShape)
                                                    .background(Color(0xFF10B981))
                                            )
                                        }
                                    }
                                ) {
                                    Icon(
                                        imageVector = if (selected) item.activeIcon else item.inactiveIcon,
                                        contentDescription = item.label
                                    )
                                }
                            },
                            label = {
                                Text(
                                    text = item.label,
                                    fontSize = 11.sp,
                                    fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium
                                )
                            }
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = NavRoutes.DISCOVER,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(NavRoutes.DISCOVER) {
                DiscoverScreen(
                    repository = repository,
                    onNavigateToTenant = { tenantId ->
                        navController.navigate(NavRoutes.tenantDetail(tenantId))
                    },
                    onNavigateToMap = { tenantId ->
                        navController.navigate(NavRoutes.parkingMap(tenantId))
                    },
                    onNavigateToMyParking = {
                        navController.navigate(NavRoutes.MY_PARKING)
                    },
                    onNavigateToFindVehicle = { sessionId ->
                        navController.navigate(NavRoutes.findVehicle(sessionId))
                    },
                    onNavigateToNotifications = {
                        navController.navigate(NavRoutes.NOTIFICATIONS)
                    }
                )
            }

            composable(
                route = NavRoutes.TENANT_DETAIL,
                arguments = listOf(navArgument("tenantId") { type = NavType.StringType })
            ) { backStackEntry ->
                val tenantId = backStackEntry.arguments?.getString("tenantId") ?: "tenant-001"
                TenantDetailScreen(
                    tenantId = tenantId,
                    repository = repository,
                    onBack = { navController.popBackStack() },
                    onOpenMap = { navController.navigate(NavRoutes.parkingMap(tenantId)) },
                    onNavigateToMyParking = { navController.navigate(NavRoutes.MY_PARKING) },
                    onNavigateToMemberships = { navController.navigate(NavRoutes.MEMBERSHIPS) }
                )
            }

            composable(
                route = NavRoutes.PARKING_MAP,
                arguments = listOf(navArgument("tenantId") { type = NavType.StringType })
            ) { backStackEntry ->
                val tenantId = backStackEntry.arguments?.getString("tenantId") ?: "tenant-001"
                ParkingMapScreen(
                    tenantId = tenantId,
                    repository = repository,
                    onBack = { navController.popBackStack() },
                    onNavigateToMyParking = { navController.navigate(NavRoutes.MY_PARKING) },
                    onNavigateToFindVehicle = { sessionId ->
                        navController.navigate(NavRoutes.findVehicle(sessionId))
                    }
                )
            }

            composable(NavRoutes.MY_PARKING) {
                MyParkingScreen(
                    repository = repository,
                    onNavigateToFindVehicle = { sessionId ->
                        navController.navigate(NavRoutes.findVehicle(sessionId))
                    },
                    onNavigateToMap = { tenantId ->
                        navController.navigate(NavRoutes.parkingMap(tenantId))
                    },
                    onNavigateToHistory = {
                        navController.navigate(NavRoutes.PARKING_HISTORY)
                    },
                    onNavigateToDiscover = {
                        navController.navigate(NavRoutes.DISCOVER)
                    }
                )
            }

            composable(
                route = NavRoutes.FIND_VEHICLE,
                arguments = listOf(navArgument("sessionId") { type = NavType.StringType })
            ) { backStackEntry ->
                val sessionId = backStackEntry.arguments?.getString("sessionId") ?: "session-001"
                FindVehicleScreen(
                    sessionId = sessionId,
                    repository = repository,
                    onBack = { navController.popBackStack() },
                    onArrived = { navController.navigate(NavRoutes.MY_PARKING) }
                )
            }

            composable(NavRoutes.MEMBERSHIPS) {
                MembershipsScreen(
                    repository = repository,
                    onNavigateToTenant = { tenantId ->
                        navController.navigate(NavRoutes.tenantDetail(tenantId))
                    },
                    onNavigateToDiscover = {
                        navController.navigate(NavRoutes.DISCOVER)
                    }
                )
            }

            composable(NavRoutes.PARKING_HISTORY) {
                ParkingHistoryScreen(
                    repository = repository,
                    onBack = { navController.popBackStack() },
                    onNavigateToTenant = { tenantId ->
                        navController.navigate(NavRoutes.tenantDetail(tenantId))
                    }
                )
            }

            composable(NavRoutes.PROFILE) {
                ProfileScreen(
                    repository = repository,
                    onNavigateToVehicles = { navController.navigate(NavRoutes.VEHICLES) },
                    onNavigateToMemberships = { navController.navigate(NavRoutes.MEMBERSHIPS) },
                    onNavigateToMyParking = { navController.navigate(NavRoutes.MY_PARKING) },
                    onNavigateToHistory = { navController.navigate(NavRoutes.PARKING_HISTORY) },
                    onNavigateToSecurity = { navController.navigate(NavRoutes.SECURITY) },
                    onNavigateToNotifications = { navController.navigate(NavRoutes.NOTIFICATIONS) }
                )
            }

            composable(NavRoutes.VEHICLES) {
                VehiclesScreen(
                    repository = repository,
                    onBack = { navController.popBackStack() }
                )
            }

            composable(NavRoutes.SECURITY) {
                SecurityScreen(
                    onBack = { navController.popBackStack() }
                )
            }

            composable(NavRoutes.NOTIFICATIONS) {
                NotificationsScreen(
                    repository = repository,
                    onBack = { navController.popBackStack() },
                    onNavigateToMyParking = { navController.navigate(NavRoutes.MY_PARKING) },
                    onNavigateToMemberships = { navController.navigate(NavRoutes.MEMBERSHIPS) },
                    onNavigateToHistory = { navController.navigate(NavRoutes.PARKING_HISTORY) },
                    onNavigateToSecurity = { navController.navigate(NavRoutes.SECURITY) }
                )
            }

        }
    }
}

private data class BottomNavItem(
    val label: String,
    val route: String,
    val activeIcon: androidx.compose.ui.graphics.vector.ImageVector,
    val inactiveIcon: androidx.compose.ui.graphics.vector.ImageVector,
    val hasBadge: Boolean = false
)
