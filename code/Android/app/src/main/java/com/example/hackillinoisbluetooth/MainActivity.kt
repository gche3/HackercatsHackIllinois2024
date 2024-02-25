package com.example.hackillinoisbluetooth

import BluetoothService
import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.example.hackillinoisbluetooth.ui.theme.HackIllinoisBluetoothTheme

class MainActivity : ComponentActivity() {

    private val requestCode = 1

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Start the BluetoothService
        val serviceIntent = Intent(this, BluetoothService::class.java)
        startService(serviceIntent)

        val bluetoothManager: BluetoothManager = getSystemService(BluetoothManager::class.java)
        val bluetoothAdapter: BluetoothAdapter = bluetoothManager.adapter

        // Check if BLUETOOTH_CONNECT permission is granted
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)
                != PackageManager.PERMISSION_GRANTED
            ) {
                requestPermissions(arrayOf(Manifest.permission.BLUETOOTH_CONNECT), requestCode)
            } else {
                initBluetooth(bluetoothAdapter)
            }
        } else {
            initBluetooth(bluetoothAdapter)
        }
    }

    @SuppressLint("MissingPermission")
    private fun initBluetooth(bluetoothAdapter: BluetoothAdapter) {
        val discoverableIntent = Intent(BluetoothAdapter.ACTION_REQUEST_DISCOVERABLE).apply {
            putExtra(BluetoothAdapter.EXTRA_DISCOVERABLE_DURATION, 60000)
        }
        startActivityForResult(discoverableIntent, requestCode)

        val pairedDevices: Set<BluetoothDevice> = bluetoothAdapter.bondedDevices

        setContent {
            HackIllinoisBluetoothTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    ConnectToDevices(
                        deviceList = pairedDevices,
                        connectOnClick = { connectOnClick(this, it) },
                    )
                }
            }
        }
    }

    @Deprecated("crying")
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == this.requestCode && grantResults.isNotEmpty() &&
            grantResults[0] == PackageManager.PERMISSION_GRANTED
        ) {
            val bluetoothManager: BluetoothManager = getSystemService(BluetoothManager::class.java)
            val bluetoothAdapter: BluetoothAdapter = bluetoothManager.adapter

            initBluetooth(bluetoothAdapter)
        } else {
            Log.d("UserInput", "Bluetooth permissions denied")
        }
    }
}

//@SuppressLint("MissingPermission")
//fun connectOnClick(context: Context, device: BluetoothDevice) {
//    val bluetoothGattCallback = object : BluetoothGattCallback() {
//        override fun onConnectionStateChange(gatt: BluetoothGatt?, status: Int, newState: Int) {
//            if (newState == BluetoothProfile.STATE_CONNECTED) {
//            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
//            }
//        }
//    }
//
//    var bluetoothGatt: BluetoothGatt? = null
//    bluetoothGatt = device.connectGatt(context, false, bluetoothGattCallback)
//    bluetoothGatt.readRemoteRssi()
//}

@SuppressLint("MissingPermission")
fun connectOnClick(context: Context, device: BluetoothDevice) {
    val bluetoothService = (context.applicationContext as BluetoothApplication).bluetoothService

    bluetoothService.disconnectFromDevice()
    bluetoothService.connectToDevice(device)
}
