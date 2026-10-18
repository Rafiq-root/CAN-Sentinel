#ifndef ML_EXPORTER_H
#define ML_EXPORTER_H

#include "can_frame.h"
#include <stdbool.h>
#include <stdio.h>

// ML Feature extraction
typedef struct {
    uint32_t can_id;
    uint8_t dlc;
    float avg_byte_value;      // Average of all data bytes
    uint32_t time_since_last;  // Microseconds since last message
    uint8_t byte_0;            // First data byte
    uint8_t byte_1;            // Second data byte
} MLFeatures;

// ML Data Exporter
typedef struct {
    FILE* csv_file;
    char filename[256];
    uint32_t samples_exported;
    uint32_t last_seen_time[2048];  // Track last time for each CAN ID
} MLExporter;

// Initialize exporter
void MLExporter_Init(MLExporter* exporter, const char* filename);

// Extract features from CAN frame
void MLExporter_ExtractFeatures(MLExporter* exporter, const CANFrame* frame, 
                                 uint32_t timestamp, MLFeatures* features);

// Export frame to CSV
void MLExporter_ExportFrame(MLExporter* exporter, const CANFrame* frame, 
                             uint32_t timestamp, bool is_attack);

// Close exporter
void MLExporter_Close(MLExporter* exporter);

#endif // ML_EXPORTER_H