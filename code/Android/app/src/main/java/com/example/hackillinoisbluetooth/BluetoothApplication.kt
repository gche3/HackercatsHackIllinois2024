package com.example.hackillinoisbluetooth

import BluetoothService
import android.app.Application
import android.content.Intent

class BluetoothApplication : Application() {

    lateinit var bluetoothService: BluetoothService

    override fun onCreate() {
        super.onCreate()

        // Initialize BluetoothService
        bluetoothService = BluetoothService()

        // Start the service
        val serviceIntent = Intent(this, BluetoothService::class.java)
        startService(serviceIntent)
    }
}