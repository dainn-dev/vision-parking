package com.example.data

import android.content.Context
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.util.UUID

class ParkingRepository(private val db: AppDatabase) {

    val allTenants: Flow<List<TenantEntity>> = db.tenantDao().getAllTenants()
    val favoriteTenants: Flow<List<TenantEntity>> = db.tenantDao().getFavoriteTenants()
    val allVehicles: Flow<List<VehicleEntity>> = db.vehicleDao().getAllVehicles()
    val allMemberships: Flow<List<MembershipEntity>> = db.membershipDao().getAllMemberships()
    val activeSessions: Flow<List<ParkingSessionEntity>> = db.parkingSessionDao().getActiveSessions()
    val historySessions: Flow<List<ParkingSessionEntity>> = db.parkingSessionDao().getHistorySessions()
    val allNotifications: Flow<List<NotificationEntity>> = db.notificationDao().getAllNotifications()
    val unreadNotificationCount: Flow<Int> = db.notificationDao().getUnreadCount()

    fun getTenantById(id: String): Flow<TenantEntity?> = db.tenantDao().getTenantById(id)
    fun getSessionById(id: String): Flow<ParkingSessionEntity?> = db.parkingSessionDao().getSessionById(id)
    fun getMembershipById(id: String): Flow<MembershipEntity?> = db.membershipDao().getMembershipById(id)
    fun getSpotsForFloor(tenantId: String, floorId: String): Flow<List<ParkingSpotEntity>> =
        db.parkingSpotDao().getSpotsForFloor(tenantId, floorId)

    suspend fun markNotificationRead(id: String) {
        db.notificationDao().markAsRead(id)
    }

    suspend fun markNotificationUnread(id: String) {
        db.notificationDao().markAsUnread(id)
    }

    suspend fun markAllNotificationsRead() {
        db.notificationDao().markAllAsRead()
    }

    suspend fun deleteNotification(notification: NotificationEntity) {
        db.notificationDao().deleteNotification(notification)
    }

    suspend fun deleteNotificationById(id: String) {
        db.notificationDao().deleteById(id)
    }

    suspend fun addNotification(
        category: String,
        type: String,
        severity: String,
        title: String,
        message: String,
        tenantId: String? = null,
        tenantName: String? = null,
        targetType: String? = null,
        targetId: String? = null
    ) {
        val notification = NotificationEntity(
            id = "notif-${UUID.randomUUID().toString().take(6)}",
            category = category,
            type = type,
            severity = severity,
            title = title,
            message = message,
            tenantId = tenantId,
            tenantName = tenantName,
            targetType = targetType,
            targetId = targetId,
            isRead = false,
            createdAt = System.currentTimeMillis()
        )
        db.notificationDao().insertNotification(notification)
    }

    suspend fun toggleFavoriteTenant(tenantId: String, isFavorite: Boolean) {
        db.tenantDao().setFavorite(tenantId, isFavorite)
    }

    suspend fun addVehicle(licensePlate: String, brandModel: String, color: String) {
        val vehicle = VehicleEntity(
            id = "veh-${UUID.randomUUID().toString().take(6)}",
            licensePlate = licensePlate,
            brandModel = brandModel,
            color = color,
            isPrimary = false
        )
        db.vehicleDao().insertVehicle(vehicle)
    }

    suspend fun deleteVehicle(vehicle: VehicleEntity) {
        db.vehicleDao().deleteVehicle(vehicle)
    }

    suspend fun registerMembership(tenantId: String, tenantName: String, planName: String, price: Int, vehiclePlate: String) {
        val membership = MembershipEntity(
            id = "mem-${UUID.randomUUID().toString().take(6)}",
            tenantId = tenantId,
            tenantName = tenantName,
            planName = planName,
            pricePerMonth = price,
            status = "ACTIVE",
            startDate = "Aug 10, 2026",
            expiresDate = "Sep 09, 2026",
            autoRenew = true,
            vehiclePlate = vehiclePlate
        )
        db.membershipDao().insertMembership(membership)
    }

    suspend fun cancelMembership(id: String) {
        db.membershipDao().cancelMembership(id)
    }

    suspend fun startParkingSession(
        tenantId: String,
        tenantName: String,
        vehicleId: String,
        licensePlate: String,
        floorName: String = "Floor 2",
        zoneName: String = "Zone B",
        spotCode: String = "B-27"
    ): String {
        val sessionId = "ps-${UUID.randomUUID().toString().take(6)}"
        val session = ParkingSessionEntity(
            id = sessionId,
            status = "ACTIVE",
            tenantId = tenantId,
            tenantName = tenantName,
            vehicleId = vehicleId,
            licensePlate = licensePlate,
            floorName = floorName,
            zoneName = zoneName,
            spotCode = spotCode,
            entryTimestamp = System.currentTimeMillis(),
            durationSeconds = 0,
            currentFee = 20000,
            pricingRule = "HOURLY",
            isPaid = false
        )
        db.parkingSessionDao().insertSession(session)
        return sessionId
    }

    suspend fun completeParkingSession(sessionId: String) {
        val session = db.parkingSessionDao().getSessionById(sessionId).first() ?: return
        val exitTime = System.currentTimeMillis()
        val duration = (exitTime - session.entryTimestamp) / 1000
        val hours = (duration / 3600).coerceAtLeast(1)
        val fee = if (session.currentFee > 0) session.currentFee else (hours * 20000).toInt()
        
        db.parkingSessionDao().completeSession(sessionId, exitTime, fee)
    }

    fun seedDatabaseIfEmpty() {
        CoroutineScope(Dispatchers.IO).launch {
            val existingTenants = db.tenantDao().getAllTenants().first()
            if (existingTenants.isEmpty()) {
                seedInitialData()
            }
        }
    }

    private suspend fun seedInitialData() {
        val tenants = listOf(
            TenantEntity(
                id = "tenant-001",
                name = "Trọ TP",
                category = "Residential & Parking",
                verified = true,
                address = "123 Nguyễn Văn Linh",
                district = "District 7",
                latitude = 10.732,
                longitude = 106.721,
                distanceMeters = 450,
                rating = 4.6f,
                reviewCount = 324,
                totalCapacity = 100,
                occupiedCapacity = 65,
                availableCapacity = 35,
                hourlyPrice = 20000,
                overnightPrice = 80000,
                dailyPrice = 120000,
                monthlyPrice = 2500000,
                memberHourlyPrice = 10000,
                isOpen = true,
                openHours = "06:00 - 23:00",
                memberAccessHours = "24/7 Access",
                supportsMembership = true,
                isFavorite = true,
                facilities = "CCTV,SECURITY,EV_CHARGING,ELEVATOR,OVERNIGHT,CAR,MOTORCYCLE"
            ),
            TenantEntity(
                id = "tenant-002",
                name = "Parking ABC Crescent",
                category = "Commercial Mall Parking",
                verified = true,
                address = "101 Tôn Dật Tiên",
                district = "District 7",
                latitude = 10.729,
                longitude = 106.718,
                distanceMeters = 850,
                rating = 4.8f,
                reviewCount = 512,
                totalCapacity = 300,
                occupiedCapacity = 180,
                availableCapacity = 120,
                hourlyPrice = 25000,
                overnightPrice = 100000,
                dailyPrice = 150000,
                monthlyPrice = 3000000,
                memberHourlyPrice = 15000,
                isOpen = true,
                openHours = "24/7",
                memberAccessHours = "24/7 Access",
                supportsMembership = true,
                isFavorite = false,
                facilities = "CCTV,SECURITY,EV_CHARGING,ELEVATOR,COVERED,CAR"
            ),
            TenantEntity(
                id = "tenant-003",
                name = "Parking XYZ Central",
                category = "Office Tower Parking",
                verified = true,
                address = "45 Nguyễn Lương Bằng",
                district = "District 7",
                latitude = 10.735,
                longitude = 106.725,
                distanceMeters = 1200,
                rating = 4.4f,
                reviewCount = 189,
                totalCapacity = 150,
                occupiedCapacity = 145,
                availableCapacity = 5,
                hourlyPrice = 30000,
                overnightPrice = 120000,
                dailyPrice = 180000,
                monthlyPrice = 3500000,
                memberHourlyPrice = 20000,
                isOpen = true,
                openHours = "06:00 - 22:00",
                memberAccessHours = "06:00 - 23:00",
                supportsMembership = false,
                isFavorite = false,
                facilities = "CCTV,SECURITY,ELEVATOR,CAR,MOTORCYCLE"
            )
        )
        db.tenantDao().insertTenants(tenants)

        val vehicles = listOf(
            VehicleEntity("veh-1", "51A-123.45", "Toyota Camry", "White", isPrimary = true),
            VehicleEntity("veh-2", "51B-456.78", "Honda Civic", "Black", isPrimary = false)
        )
        vehicles.forEach { db.vehicleDao().insertVehicle(it) }

        val membership = MembershipEntity(
            id = "mem-1",
            tenantId = "tenant-001",
            tenantName = "Trọ TP",
            planName = "Monthly Resident",
            pricePerMonth = 150000,
            status = "ACTIVE",
            startDate = "Aug 10, 2026",
            expiresDate = "Sep 09, 2026",
            autoRenew = true,
            vehiclePlate = "51A-123.45"
        )
        db.membershipDao().insertMembership(membership)

        // Seed 1 active session in Trọ TP
        val now = System.currentTimeMillis()
        val entryTimeTwoHoursAgo = now - (2 * 3600 + 35 * 60) * 1000
        val activeSession = ParkingSessionEntity(
            id = "session-001",
            status = "ACTIVE",
            tenantId = "tenant-001",
            tenantName = "Trọ TP",
            vehicleId = "veh-1",
            licensePlate = "51A-123.45",
            floorName = "Floor 2",
            zoneName = "Zone B",
            spotCode = "B-27",
            entryTimestamp = entryTimeTwoHoursAgo,
            durationSeconds = 2 * 3600 + 35 * 60,
            currentFee = 40000,
            pricingRule = "MEMBER",
            isPaid = false,
            gateName = "Main Entrance"
        )
        db.parkingSessionDao().insertSession(activeSession)

        // Seed some history sessions
        val historySessions = listOf(
            ParkingSessionEntity(
                id = "hist-001",
                status = "COMPLETED",
                tenantId = "tenant-002",
                tenantName = "Parking ABC Crescent",
                vehicleId = "veh-1",
                licensePlate = "51A-123.45",
                floorName = "Floor 1",
                zoneName = "Zone A",
                spotCode = "A-12",
                entryTimestamp = now - 24 * 3600 * 1000 - 3 * 3600 * 1000,
                exitTimestamp = now - 24 * 3600 * 1000,
                durationSeconds = 3 * 3600 + 5 * 60,
                currentFee = 60000,
                finalFee = 60000,
                pricingRule = "HOURLY",
                isPaid = true,
                gateName = "Gate 2"
            ),
            ParkingSessionEntity(
                id = "hist-002",
                status = "COMPLETED",
                tenantId = "tenant-001",
                tenantName = "Trọ TP",
                vehicleId = "veh-1",
                licensePlate = "51A-123.45",
                floorName = "Floor 2",
                zoneName = "Zone B",
                spotCode = "B-27",
                entryTimestamp = now - 48 * 3600 * 1000 - 4 * 3600 * 1000,
                exitTimestamp = now - 48 * 3600 * 1000,
                durationSeconds = 4 * 3600,
                currentFee = 30000,
                finalFee = 30000,
                pricingRule = "MEMBER",
                isPaid = true,
                gateName = "Main Entrance"
            )
        )
        historySessions.forEach { db.parkingSessionDao().insertSession(it) }

        // Seed parking spots for Trọ TP Floor 2
        val spotsF2 = listOf(
            ParkingSpotEntity("spot-b27", "tenant-001", "F2", "Zone B", "B-27", "MY_VEHICLE", "CAR", 0.65f, 0.45f, 85),
            ParkingSpotEntity("spot-b25", "tenant-001", "F2", "Zone B", "B-25", "AVAILABLE", "CAR", 0.50f, 0.45f, 80),
            ParkingSpotEntity("spot-b26", "tenant-001", "F2", "Zone B", "B-26", "AVAILABLE", "CAR", 0.58f, 0.45f, 82),
            ParkingSpotEntity("spot-b28", "tenant-001", "F2", "Zone B", "B-28", "AVAILABLE", "CAR", 0.72f, 0.45f, 88),
            ParkingSpotEntity("spot-b29", "tenant-001", "F2", "Zone B", "B-29", "RESERVED", "CAR", 0.80f, 0.45f, 92),
            ParkingSpotEntity("spot-b20", "tenant-001", "F2", "Zone B", "B-20", "OCCUPIED", "CAR", 0.15f, 0.45f, 65),
            ParkingSpotEntity("spot-b21", "tenant-001", "F2", "Zone B", "B-21", "OCCUPIED", "CAR", 0.23f, 0.45f, 68),
            ParkingSpotEntity("spot-e12", "tenant-001", "F2", "Zone B", "E-12", "AVAILABLE", "EV", 0.35f, 0.20f, 40),
            ParkingSpotEntity("spot-a05", "tenant-001", "F2", "Zone A", "A-05", "AVAILABLE", "ACCESSIBLE", 0.20f, 0.20f, 25)
        )
        db.parkingSpotDao().insertSpots(spotsF2)

        // Seed notifications
        val initialNotifications = listOf(
            NotificationEntity(
                id = "notif-001",
                category = "PARKING",
                type = "PARKING_STARTED",
                severity = "INFO",
                title = "Parking session active",
                message = "Your vehicle 51A-123.45 entered Trọ TP. Parked at Floor 2 · Zone B · Spot B-27.",
                tenantId = "tenant-001",
                tenantName = "Trọ TP",
                targetType = "PARKING_SESSION",
                targetId = "session-001",
                isRead = false,
                createdAt = now - 15 * 60 * 1000
            ),
            NotificationEntity(
                id = "notif-002",
                category = "PAYMENT",
                type = "PAYMENT_SUCCESS",
                severity = "SUCCESS",
                title = "Payment successful",
                message = "60,000 VND was successfully processed for parking session at Parking ABC Crescent.",
                tenantId = "tenant-002",
                tenantName = "Parking ABC Crescent",
                targetType = "PARKING_SESSION",
                targetId = "hist-001",
                isRead = false,
                createdAt = now - 45 * 60 * 1000
            ),
            NotificationEntity(
                id = "notif-003",
                category = "MEMBERSHIP",
                type = "MEMBERSHIP_APPROVED",
                severity = "SUCCESS",
                title = "Membership approved",
                message = "Your Monthly Resident membership plan at Trọ TP is now active (150,000 VND/mo).",
                tenantId = "tenant-001",
                tenantName = "Trọ TP",
                targetType = "MEMBERSHIP",
                targetId = "mem-1",
                isRead = false,
                createdAt = now - 2 * 3600 * 1000
            ),
            NotificationEntity(
                id = "notif-004",
                category = "MEMBERSHIP",
                type = "MEMBERSHIP_EXPIRING",
                severity = "WARNING",
                title = "Membership expires soon",
                message = "Your Monthly Resident membership at Trọ TP will expire in 30 days.",
                tenantId = "tenant-001",
                tenantName = "Trọ TP",
                targetType = "MEMBERSHIP",
                targetId = "mem-1",
                isRead = true,
                createdAt = now - 24 * 3600 * 1000
            ),
            NotificationEntity(
                id = "notif-005",
                category = "SECURITY",
                type = "NEW_LOGIN",
                severity = "SECURITY",
                title = "New login detected",
                message = "Your MEMBER account was accessed from Chrome on Windows in Ho Chi Minh City.",
                tenantId = null,
                tenantName = "Vision Platform",
                targetType = "SECURITY",
                targetId = "sec-001",
                isRead = true,
                createdAt = now - 48 * 3600 * 1000
            ),
            NotificationEntity(
                id = "notif-006",
                category = "SYSTEM",
                type = "SYSTEM_UPDATE",
                severity = "INFO",
                title = "Scheduled maintenance alert",
                message = "Platform maintenance scheduled for Aug 12, 02:00 - 03:00 GMT+7. LPR gates remain operational.",
                tenantId = null,
                tenantName = "System",
                targetType = "SYSTEM",
                targetId = "sys-001",
                isRead = true,
                createdAt = now - 72 * 3600 * 1000
            )
        )
        db.notificationDao().insertNotifications(initialNotifications)
    }


    companion object {
        @Volatile
        private var INSTANCE: ParkingRepository? = null

        fun getInstance(context: Context): ParkingRepository {
            return INSTANCE ?: synchronized(this) {
                val db = AppDatabase.getInstance(context)
                val repo = ParkingRepository(db)
                repo.seedDatabaseIfEmpty()
                INSTANCE = repo
                repo
            }
        }
    }
}
