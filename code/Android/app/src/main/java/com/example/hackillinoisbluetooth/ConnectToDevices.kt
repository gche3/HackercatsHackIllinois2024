package com.example.hackillinoisbluetooth

import android.annotation.SuppressLint
import android.bluetooth.BluetoothDevice
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

@SuppressLint("MissingPermission")
@Composable
fun ConnectToDevices(
    deviceList : Set<BluetoothDevice>,
    connectOnClick : (BluetoothDevice) -> Unit,
) {
    Column (
        modifier = Modifier.fillMaxHeight()
            ) {
        Text(
            text = "Make sure you have connected to the device you want to follow. Select one of the following to follow.",
            modifier = Modifier.padding(bottom = 10.dp)
        )
        deviceList.forEach {
            Box (
                modifier = Modifier
                    .clickable { connectOnClick(it) }
                    .fillMaxWidth()
                    .border(2.dp, color = Color.Black)
                    ) {
                Text(
                    text = it.name,
                    modifier = Modifier.padding(5.dp)
                )
            }
        }
    }
}

//@Preview
//@Composable
//fun ConnectToDevicesPreview() {
//    ConnectToDevices(deviceList = setOf("device1 ", "device 2", "device 3"), connectOnClick = {})
//}