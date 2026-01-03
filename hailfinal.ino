#include <Arduino.h>
#include <math.h>

// ----- Pin Definitions & Calibration Constants -----
const int pressurePin = A0;              // Pressure transducer analog input
const float sensorZeroVoltage = 0.65;      // Measured zero-pressure voltage (adjust as needed)
const float conversionFactor = 2202.71;   // Pa per Volt (adjust after calibration)
const float energyConversionFactor = 0.00001; // J per Pa (based on your cylinder's effective volume change)
const float radius = 0.005;               // Cylinder radius in meters
const float height = 0.03;                // Cylinder height in meters
const float volume = 0.00000235619449;    // Cylinder volume in cubic meters
const float adiabaticIndex = 1.4;         // Adiabatic index (gamma)
const float pressure0 = 101325;           // Reference pressure in Pa (converted from 1013.25 hPa)

// ----- Impact Detection Settings -----
const float triggerThresholdMargin = 0.02; // Voltage margin above zero to trigger an event
const int consecutiveHitsNeeded = 3;       // Number of consecutive filtered readings required to trigger

// ----- Sampling Settings for the Impact Event -----
const unsigned long samplingIntervalMicros = 100;  // Interval between samples during an event (~10 kHz sampling)
const unsigned long eventDurationMicros = 60000;     // Duration to sample the impact event (60 ms)

// ----- Post-Event Delay -----
const unsigned long postEventDelayMillis = 1000;     // Delay after an event (1 second)

// ----- Filtering Settings -----
const int filterSampleCount = 5; // Number of samples to average for filtering

// Function to take multiple readings and return an averaged (filtered) voltage
float getFilteredVoltage(int samples = filterSampleCount) {
  long sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(pressurePin);
    delayMicroseconds(50); // Small delay between samples
  }
  float avgReading = sum / (float)samples;
  return (avgReading / 1023.0) * 5.0;
}

void setup() {
  Serial.begin(115200);
  Serial.println("=== Enhanced Hail Impact Kinetic Energy Measurement ===");
  Serial.print("Zero reference voltage: ");
  Serial.print(sensorZeroVoltage, 3);
  Serial.println(" V");
  Serial.print("Conversion Factor (Pa/V): ");
  Serial.println(conversionFactor);
  Serial.print("Energy Conversion Factor (J/Pa): ");
  Serial.println(energyConversionFactor);
  Serial.println("Waiting for hail impact...");
}

void loop() {
  // Use filtered voltage readings to reduce noise
  static int hitCount = 0;
  float voltage = getFilteredVoltage();

  // Check if the filtered voltage exceeds the threshold (zero + margin)
  if (voltage > sensorZeroVoltage + triggerThresholdMargin) {
    hitCount++;
  } else {
    hitCount = 0;
  }
  
  // If enough consecutive readings are above the threshold, register an impact
  if (hitCount >= consecutiveHitsNeeded) {
    Serial.println("\n*** Impact detected! ***");
    
    // Record the start time of the impact event
    unsigned long eventStart = micros();
    unsigned long currentTime;
    float maxVoltage = voltage; // Start with the filtered voltage that triggered the event
    
    // Quickly sample for the set duration to capture the absolute peak voltage
    while ((currentTime = micros()) - eventStart < eventDurationMicros) {
      float v = getFilteredVoltage();
      if (v > maxVoltage) {
        maxVoltage = v;
      }
      delayMicroseconds(samplingIntervalMicros);
    }
    
    // Calculate the voltage difference from the zero reference
    float deltaVoltage = maxVoltage - sensorZeroVoltage;
    
    // Convert delta voltage to pressure change in Pascals
    float pressureChange = deltaVoltage * conversionFactor;
    
    // Estimate the kinetic energy (using the adiabatic compression formula)
    // Corrected formula implementation
    float totalPressure = pressureChange + pressure0;
    float term1 = (pressure0 * volume) / (adiabaticIndex - 1);
    float term2 = 1 - pow(pressure0 / totalPressure, (adiabaticIndex - 1) / adiabaticIndex);
    float kineticEnergy = term1 * term2;
    
    // Print the results and send to Python script
    Serial.print("Time,");
    Serial.print(millis());
    Serial.print(",");
    Serial.print(maxVoltage, 4);
    Serial.print(",");
    Serial.print(pressureChange, 2);
    Serial.print(",");
    Serial.println(kineticEnergy, 4);
    
    // Also print human-readable debug info
    Serial.print("Max Voltage: ");
    Serial.print(maxVoltage, 4);
    Serial.println(" V");
    
    Serial.print("Delta Voltage: ");
    Serial.print(deltaVoltage, 4);
    Serial.println(" V");
    
    Serial.print("Pressure Change: ");
    Serial.print(pressureChange, 2);
    Serial.println(" Pa");
    
    Serial.print("Estimated Kinetic Energy: ");
    Serial.print(kineticEnergy*1000, 4);
    Serial.println(" J");
    Serial.println("-------------------------------------------");
    
    // Delay after the event to prevent multiple triggers from a single impact
    delay(postEventDelayMillis);
    hitCount = 0; // Reset hit counter after processing an event
  }
}