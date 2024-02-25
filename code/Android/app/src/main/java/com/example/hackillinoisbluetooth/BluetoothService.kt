import android.annotation.SuppressLint
import android.app.Service
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothProfile
import android.content.Intent
import android.os.Binder
import android.os.IBinder
import android.util.Log
import com.example.hackillinoisbluetooth.ApiService
import com.google.gson.Gson
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.Timer
import java.util.TimerTask
import kotlin.math.pow

data class SensorData(val distance: Double, val rssi: Int)

class BluetoothService : Service() {

    private val binder: IBinder = BluetoothBinder()
    private var bluetoothGatt: BluetoothGatt? = null
    private var connectedDevice: BluetoothDevice? = null
    private var rssiTimer: Timer? = null

    private val gson = Gson()

    private val retrofit = Retrofit.Builder()
        .baseUrl("http://10.192.173.150:5000/") // Replace with your server address
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    private val apiService: ApiService = retrofit.create(ApiService::class.java)

    inner class BluetoothBinder : Binder() {
        fun getService(): BluetoothService = this@BluetoothService
    }

    override fun onBind(intent: Intent?): IBinder {
        return binder
    }

    @SuppressLint("MissingPermission")
    fun connectToDevice(device: BluetoothDevice) {
        disconnectFromDevice()

        val bluetoothGattCallback = object : BluetoothGattCallback() {
            override fun onConnectionStateChange(
                gatt: BluetoothGatt?,
                status: Int,
                newState: Int
            ) {
                if (newState == BluetoothProfile.STATE_CONNECTED) {
                    // Start reading RSSI when connected
                    startRssiTimer(gatt)
                } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                    // Stop reading RSSI when disconnected
                    stopRssiTimer()
                }
            }

            override fun onReadRemoteRssi(gatt: BluetoothGatt?, rssi: Int, status: Int) {
                if (status == BluetoothGatt.GATT_SUCCESS) {
                    val distance = calculateDistance(rssi)
                    Log.d("DISTANCE", "Distance: $distance meters; RSSI: $rssi")

                    val sensorData = SensorData(distance, rssi)
                    sendSensorDataToServer(sensorData)
                }
            }
        }
        bluetoothGatt = device.connectGatt(this, false, bluetoothGattCallback)
        connectedDevice = device
    }

    @SuppressLint("MissingPermission")
    fun disconnectFromDevice() {
        bluetoothGatt?.disconnect()
        stopRssiTimer()
        connectedDevice = null
    }

    private fun calculateDistance(rssi: Int): Double {
        val referenceRssi = 0 // RSSI at 1 meter
        val pathLossExponent = 3.0 // Path loss exponent

        return 10.0.pow((referenceRssi - rssi) / (10.0 * pathLossExponent))
    }

    fun startRssiTimer(gatt: BluetoothGatt?) {
        stopRssiTimer()

        // Start reading RSSI every second
        rssiTimer = Timer()
        rssiTimer?.scheduleAtFixedRate(object : TimerTask() {
            @SuppressLint("MissingPermission")
            override fun run() {
                gatt?.readRemoteRssi()
            }
        }, 0, 1000)
    }

    private fun stopRssiTimer() {
        rssiTimer?.cancel()
        rssiTimer = null
    }

    private fun sendSensorDataToServer(sensorData: SensorData) {
        val jsonData = gson.toJson(sensorData)

        val call: Call<Void> = apiService.sendSensorData(jsonData)
        call.enqueue(object : Callback<Void> {
            override fun onResponse(call: Call<Void>, response: Response<Void>) {
                if (response.isSuccessful) {
                    Log.d("API", "Sensor data sent successfully")
                } else {
                    Log.e("API", "Failed to send sensor data to server")
                }
            }

            override fun onFailure(call: Call<Void>, t: Throwable) {
                Log.e("API", "Error while sending sensor data to server", t)
            }
        })
    }

    @SuppressLint("MissingPermission")
    override fun onDestroy() {
        super.onDestroy()
        disconnectFromDevice()
        bluetoothGatt?.close()
        bluetoothGatt = null
    }
}