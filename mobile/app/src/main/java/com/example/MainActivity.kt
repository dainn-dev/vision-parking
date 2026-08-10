package com.example

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.navigation.compose.rememberNavController
import com.example.data.ParkingRepository
import com.example.ui.navigation.VisionNavHost
import com.example.ui.theme.MyApplicationTheme

class MainActivity : ComponentActivity() {
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    enableEdgeToEdge()

    val repository = ParkingRepository.getInstance(applicationContext)

    setContent {
      MyApplicationTheme {
        val navController = rememberNavController()
        VisionNavHost(navController = navController, repository = repository)
      }
    }
  }
}

