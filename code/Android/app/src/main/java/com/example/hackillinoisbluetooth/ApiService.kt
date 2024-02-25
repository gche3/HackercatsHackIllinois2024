package com.example.hackillinoisbluetooth

import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.POST

interface ApiService {
    @POST("rssi")
    fun sendSensorData(@Body sensorData: String): Call<Void>
}