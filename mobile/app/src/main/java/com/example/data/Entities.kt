package com.example.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "tenants")
data class TenantEntity(
    @PrimaryKey val id: String,
    val name: String,
    val category: String,
    val verified: Boolean,
    val address: String,
    val district: String,
    val latitude: Double,
    val longitude: Double,
    val distanceMeters: Int,
    val rating: Float,
    val reviewCount: Int,
    val totalCapacity: Int,
    val occupiedCapacity: Int,
    val availableCapacity: Int,
    val hourlyPrice: Int,
    val overnightPrice: Int,
    val dailyPrice: Int,
    val monthlyPrice: Int,
    val memberHourlyPrice: Int,
    val isOpen: Boolean,
    val openHours: String,
    val memberAccessHours: String,
    val supportsMembership: Boolean,
    val isFavorite: Boolean,
    val facilities: String
)

@Entity(tableName = "vehicles")
data class VehicleEntity(
    @PrimaryKey val id: String,
    val licensePlate: String,
    val brandModel: String,
    val color: String,
    val isPrimary: Boolean,
    val createdAt: Long = System.currentTimeMillis()
)

@Entity(tableName = "memberships")
data class MembershipEntity(
    @PrimaryKey val id: String,
    val tenantId: String,
    val tenantName: String,
    val planName: String,
    val pricePerMonth: Int,
    val status: String, // ACTIVE, PENDING, EXPIRED, SUSPENDED, CANCELLED
    val startDate: String,
    val expiresDate: String,
    val autoRenew: Boolean,
    val vehiclePlate: String
)

@Entity(tableName = "parking_sessions")
data class ParkingSessionEntity(
    @PrimaryKey val id: String,
    val status: String, // ACTIVE, EXITING, COMPLETED, CANCELLED
    val tenantId: String,
    val tenantName: String,
    val vehicleId: String,
    val licensePlate: String,
    val floorName: String,
    val zoneName: String,
    val spotCode: String,
    val entryTimestamp: Long,
    val exitTimestamp: Long? = null,
    val durationSeconds: Long = 0,
    val currentFee: Int = 0,
    val finalFee: Int = 0,
    val pricingRule: String = "HOURLY",
    val isPaid: Boolean = false,
    val gateName: String = "Main Entrance"
)

@Entity(tableName = "parking_spots")
data class ParkingSpotEntity(
    @PrimaryKey val id: String,
    val tenantId: String,
    val floorId: String, // F2, F1, B1
    val zoneId: String,  // Zone A, Zone B, Zone C
    val spotCode: String,
    val status: String,  // AVAILABLE, OCCUPIED, RESERVED, MY_VEHICLE, OUT_OF_SERVICE
    val type: String,    // CAR, MOTORCYCLE, EV, ACCESSIBLE
    val xRatio: Float,
    val yRatio: Float,
    val distanceFromEntrance: Int
)

@Entity(tableName = "notifications")
data class NotificationEntity(
    @PrimaryKey val id: String,
    val category: String, // PARKING, MEMBERSHIP, PAYMENT, SECURITY, SYSTEM
    val type: String,     // PARKING_STARTED, PARKING_COMPLETED, MEMBERSHIP_APPROVED, MEMBERSHIP_EXPIRING, PAYMENT_SUCCESS, PAYMENT_FAILED, NEW_LOGIN
    val severity: String, // INFO, SUCCESS, WARNING, ACTION_REQUIRED, SECURITY
    val title: String,
    val message: String,
    val tenantId: String? = null,
    val tenantName: String? = null,
    val targetType: String? = null, // PARKING_SESSION, MEMBERSHIP, PAYMENT, SECURITY, VEHICLE
    val targetId: String? = null,
    val isRead: Boolean = false,
    val createdAt: Long = System.currentTimeMillis()
)

