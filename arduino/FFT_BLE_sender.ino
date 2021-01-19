/*
 * FFT analysis with ATSAMD21 Arduino Board
 * with Bluetooth Low Energy transmission of 
 * amplitudes and frequencies 
 * 
 * by Josh Hrisko, 2020
 *    Maker Portal x WaWiCo
 *    
 */
#include "arduinoFFT.h"

arduinoFFT FFT = arduinoFFT(); // start FFT class

#define CHANNEL A0 // analog channel with microphone
const uint16_t CHUNK = 1024; // samples used to compute FFT (MUST be a power of 2)

// Sample Rate below: limits based on SAMD21 ADC
// --- the max sample rate was found to be ~30kHz 
// --- (the FFT becomes unsteady above this rate)
// --- Based on the limited CHUNK size, lower gives
// --- better freq. resolution (10kHz gives ~10Hz resolution)
const double samp_rate = 10000; // sample rate [Hz]

unsigned int sampling_period_us; // period between samples
unsigned long microseconds; // variable used for timing

// FFT variables
double vec_real[CHUNK]; // real-valued variables
double vec_imag[CHUNK]; // imaginary-valued variables

void setup() {
  analogReadResolution(12); // set analog resolution to 12-bits
  analogReference(AR_DEFAULT); // analog voltage reference (3.3V for ATMSAMD21) 
  
  sampling_period_us = round(1000000*(1.0/samp_rate)); // period between samples

  Serial1.begin(9600); // start Bluetooth serial port comm.
  while (!Serial1){}; // wait for BLE port to start
}

void loop() {
  // Loop through CHUNK to acquire data by waiting 
  // 1/(sample rate) [smaple period] in micro-seconds
  microseconds = micros(); // 
  for(int i=0; i<CHUNK; i++)
  {
      vec_real[i] = analogRead(CHANNEL);
      vec_imag[i] = 0;
      while(micros() - microseconds < sampling_period_us){
        //empty loop
      }
      microseconds += sampling_period_us;
  }
  // Windowing and FFT computation procedure
  FFT.Windowing(vec_real, CHUNK, FFT_WIN_TYP_HAMMING, FFT_FORWARD);	// hamming window
  FFT.Compute(vec_real, vec_imag, CHUNK, FFT_FORWARD); // compute FFT with real/imag vectors
  FFT.ComplexToMagnitude(vec_real, vec_imag, CHUNK); // get magnitudes for peak detection

  // Peak finder routine
  double x = FFT.MajorPeak(vec_real, CHUNK, samp_rate);
  Serial1.print(x, 6); // send dominant peak via BLE serial comm.
}

void PrintVector(double *vData, uint16_t bufferSize, uint8_t scaleType) {
  for (uint16_t i = 0; i < bufferSize; i++) {
      double abscissa;
      /* Print abscissa value */
      switch (scaleType) {
        case 0:
          abscissa = (i * 1.0);
      	  break;
        case 1:
          abscissa = ((i * 1.0) / samp_rate);
      	  break;
        case 2:
          abscissa = ((i * 1.0 * samp_rate) / CHUNK);
      	  break;
      }
  }
}
