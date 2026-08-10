package com.example.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [
        TenantEntity::class,
        VehicleEntity::class,
        MembershipEntity::class,
        ParkingSessionEntity::class,
        ParkingSpotEntity::class,
        NotificationEntity::class
    ],
    version = 2,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun tenantDao(): TenantDao
    abstract fun vehicleDao(): VehicleDao
    abstract fun membershipDao(): MembershipDao
    abstract fun parkingSessionDao(): ParkingSessionDao
    abstract fun parkingSpotDao(): ParkingSpotDao
    abstract fun notificationDao(): NotificationDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "vision_parking_database"
                )
                .fallbackToDestructiveMigration()
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
