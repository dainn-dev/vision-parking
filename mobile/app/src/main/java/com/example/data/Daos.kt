package com.example.data

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Dao
interface TenantDao {
    @Query("SELECT * FROM tenants")
    fun getAllTenants(): Flow<List<TenantEntity>>

    @Query("SELECT * FROM tenants WHERE id = :id")
    fun getTenantById(id: String): Flow<TenantEntity?>

    @Query("SELECT * FROM tenants WHERE id = :id")
    suspend fun getTenantByIdSync(id: String): TenantEntity?

    @Query("SELECT * FROM tenants WHERE isFavorite = 1")
    fun getFavoriteTenants(): Flow<List<TenantEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTenants(tenants: List<TenantEntity>)

    @Update
    suspend fun updateTenant(tenant: TenantEntity)

    @Query("UPDATE tenants SET isFavorite = :isFavorite WHERE id = :id")
    suspend fun setFavorite(id: String, isFavorite: Boolean)

    @Query("UPDATE tenants SET availableCapacity = :available, occupiedCapacity = :occupied WHERE id = :id")
    suspend fun updateCapacity(id: String, available: Int, occupied: Int)
}

@Dao
interface VehicleDao {
    @Query("SELECT * FROM vehicles ORDER BY isPrimary DESC, createdAt DESC")
    fun getAllVehicles(): Flow<List<VehicleEntity>>

    @Query("SELECT * FROM vehicles WHERE isPrimary = 1 LIMIT 1")
    suspend fun getPrimaryVehicle(): VehicleEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertVehicle(vehicle: VehicleEntity)

    @Delete
    suspend fun deleteVehicle(vehicle: VehicleEntity)

    @Query("UPDATE vehicles SET isPrimary = (id = :primaryId)")
    suspend fun setPrimaryVehicle(primaryId: String)
}

@Dao
interface MembershipDao {
    @Query("SELECT * FROM memberships ORDER BY status = 'ACTIVE' DESC")
    fun getAllMemberships(): Flow<List<MembershipEntity>>

    @Query("SELECT * FROM memberships WHERE id = :id")
    fun getMembershipById(id: String): Flow<MembershipEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMembership(membership: MembershipEntity)

    @Update
    suspend fun updateMembership(membership: MembershipEntity)

    @Query("UPDATE memberships SET status = 'CANCELLED' WHERE id = :id")
    suspend fun cancelMembership(id: String)
}

@Dao
interface ParkingSessionDao {
    @Query("SELECT * FROM parking_sessions WHERE status = 'ACTIVE' OR status = 'EXITING' ORDER BY entryTimestamp DESC")
    fun getActiveSessions(): Flow<List<ParkingSessionEntity>>

    @Query("SELECT * FROM parking_sessions WHERE status = 'COMPLETED' OR status = 'CANCELLED' ORDER BY entryTimestamp DESC")
    fun getHistorySessions(): Flow<List<ParkingSessionEntity>>

    @Query("SELECT * FROM parking_sessions WHERE id = :id")
    fun getSessionById(id: String): Flow<ParkingSessionEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSession(session: ParkingSessionEntity)

    @Update
    suspend fun updateSession(session: ParkingSessionEntity)

    @Query("UPDATE parking_sessions SET status = 'COMPLETED', exitTimestamp = :exitTime, finalFee = :fee, isPaid = 1 WHERE id = :id")
    suspend fun completeSession(id: String, exitTime: Long, fee: Int)
}

@Dao
interface ParkingSpotDao {
    @Query("SELECT * FROM parking_spots WHERE tenantId = :tenantId AND floorId = :floorId")
    fun getSpotsForFloor(tenantId: String, floorId: String): Flow<List<ParkingSpotEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSpots(spots: List<ParkingSpotEntity>)

    @Query("UPDATE parking_spots SET status = :status WHERE id = :spotId")
    suspend fun updateSpotStatus(spotId: String, status: String)
}

@Dao
interface NotificationDao {
    @Query("SELECT * FROM notifications ORDER BY createdAt DESC")
    fun getAllNotifications(): Flow<List<NotificationEntity>>

    @Query("SELECT COUNT(*) FROM notifications WHERE isRead = 0")
    fun getUnreadCount(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertNotification(notification: NotificationEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertNotifications(notifications: List<NotificationEntity>)

    @Query("UPDATE notifications SET isRead = 1 WHERE id = :id")
    suspend fun markAsRead(id: String)

    @Query("UPDATE notifications SET isRead = 0 WHERE id = :id")
    suspend fun markAsUnread(id: String)

    @Query("UPDATE notifications SET isRead = 1 WHERE isRead = 0")
    suspend fun markAllAsRead()

    @Delete
    suspend fun deleteNotification(notification: NotificationEntity)

    @Query("DELETE FROM notifications WHERE id = :id")
    suspend fun deleteById(id: String)
}

