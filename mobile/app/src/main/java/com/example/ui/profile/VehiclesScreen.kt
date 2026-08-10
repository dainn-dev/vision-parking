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
import com.example.data.VehicleEntity
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VehiclesScreen(
    repository: ParkingRepository,
    onBack: () -> Unit
) {
    val vehicles by repository.allVehicles.collectAsState(initial = emptyList())
    var showAddVehicleDialog by remember { mutableStateOf(false) }

    var plateInput by remember { mutableStateOf("") }
    var brandInput by remember { mutableStateOf("") }
    var colorInput by remember { mutableStateOf("") }

    val coroutineScope = rememberCoroutineScope()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("My Vehicles", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { showAddVehicleDialog = true }) {
                        Icon(Icons.Default.Add, contentDescription = "Add Vehicle")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp)
        ) {
            Text("Registered License Plates", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Text("These vehicles can be automatically recognized by LPR cameras at tenant gates.", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)

            Spacer(modifier = Modifier.height(16.dp))

            vehicles.forEach { vehicle ->
                VehicleCardItem(
                    vehicle = vehicle,
                    onDelete = {
                        coroutineScope.launch {
                            repository.deleteVehicle(vehicle)
                        }
                    }
                )
                Spacer(modifier = Modifier.height(12.dp))
            }

            Spacer(modifier = Modifier.weight(1f))

            Button(
                onClick = { showAddVehicleDialog = true },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                contentPadding = PaddingValues(vertical = 12.dp)
            ) {
                Icon(Icons.Default.Add, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Add New Vehicle License Plate")
            }
        }

        // Add Vehicle Dialog Modal
        if (showAddVehicleDialog) {
            AlertDialog(
                onDismissRequest = { showAddVehicleDialog = false },
                title = { Text("Add Vehicle") },
                text = {
                    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        OutlinedTextField(
                            value = plateInput,
                            onValueChange = { plateInput = it.uppercase() },
                            label = { Text("License Plate (e.g. 51A-999.99)") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth()
                        )
                        OutlinedTextField(
                            value = brandInput,
                            onValueChange = { brandInput = it },
                            label = { Text("Brand / Model (e.g. Toyota Vios)") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth()
                        )
                        OutlinedTextField(
                            value = colorInput,
                            onValueChange = { colorInput = it },
                            label = { Text("Color (e.g. Black)") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                },
                confirmButton = {
                    Button(
                        onClick = {
                            if (plateInput.isNotBlank()) {
                                coroutineScope.launch {
                                    repository.addVehicle(
                                        licensePlate = plateInput.trim(),
                                        brandModel = if (brandInput.isBlank()) "Sedan" else brandInput.trim(),
                                        color = if (colorInput.isBlank()) "Silver" else colorInput.trim()
                                    )
                                    plateInput = ""
                                    brandInput = ""
                                    colorInput = ""
                                    showAddVehicleDialog = false
                                }
                            }
                        },
                        enabled = plateInput.isNotBlank()
                    ) {
                        Text("Add Vehicle")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showAddVehicleDialog = false }) {
                        Text("Cancel")
                    }
                }
            )
        }
    }
}

@Composable
fun VehicleCardItem(
    vehicle: VehicleEntity,
    onDelete: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(2.dp)
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
                    shape = RoundedCornerShape(12.dp),
                    color = MaterialTheme.colorScheme.primaryContainer,
                    modifier = Modifier.size(48.dp)
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(Icons.Default.DirectionsCar, contentDescription = null, tint = MaterialTheme.colorScheme.onPrimaryContainer)
                    }
                }

                Spacer(modifier = Modifier.width(12.dp))

                Column {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(vehicle.licensePlate, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                        if (vehicle.isPrimary) {
                            Spacer(modifier = Modifier.width(6.dp))
                            Surface(
                                shape = RoundedCornerShape(6.dp),
                                color = MaterialTheme.colorScheme.primary.copy(alpha = 0.15f)
                            ) {
                                Text("Primary", modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp), fontSize = 10.sp, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                    Text("${vehicle.brandModel} (${vehicle.color})", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }

            IconButton(onClick = onDelete) {
                Icon(Icons.Default.DeleteOutline, contentDescription = "Delete Vehicle", tint = Color(0xFFEF4444))
            }
        }
    }
}
