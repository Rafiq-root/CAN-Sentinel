#include "ml_exporter.h"
#include <string.h>
#include <time.h>

void MLExporter_Init(MLExporter* exporter, const char* filename) {
    memset(exporter, 0, sizeof(MLExporter));
    strncpy(exporter->filename, filename, 255);
    
    exporter->csv_file = fopen(filename, "w");
    if (!exporter->csv_file) {
        printf("[ML-EXPORTER] Error: Could not open %s\n", filename);
        return;
    }
    
    // Write CSV header
    fprintf(exporter->csv_file, "can_id,dlc,avg_byte_value,time_since_last,byte_0,byte_1,is_attack\n");
    
    printf("[ML-EXPORTER] Initialized: %s\n", filename);
}

void MLExporter_ExtractFeatures(MLExporter* exporter, const CANFrame* frame, 
                                 uint32_t timestamp, MLFeatures* features) {
    features->can_id = frame->id;
    features->dlc = frame->dlc;
    
    // Calculate average byte value
    uint32_t sum = 0;
    for (int i = 0; i < frame->dlc; i++) {
        sum += frame->data[i];
    }
    features->avg_byte_value = (frame->dlc > 0) ? (float)sum / frame->dlc : 0.0f;
    
    // Time since last message of this ID
    uint32_t last_time = exporter->last_seen_time[frame->id];
    features->time_since_last = (last_time > 0) ? (timestamp - last_time) : 0;
    
    // Store individual bytes (useful for some IDs)
    features->byte_0 = (frame->dlc > 0) ? frame->data[0] : 0;
    features->byte_1 = (frame->dlc > 1) ? frame->data[1] : 0;
    
    // Update last seen time
    exporter->last_seen_time[frame->id] = timestamp;
}

void MLExporter_ExportFrame(MLExporter* exporter, const CANFrame* frame, 
                             uint32_t timestamp, bool is_attack) {
    if (!exporter->csv_file) return;
    
    MLFeatures features;
    MLExporter_ExtractFeatures(exporter, frame, timestamp, &features);
    
    // Write to CSV
    fprintf(exporter->csv_file, "%u,%u,%.2f,%u,%u,%u,%d\n",
            features.can_id,
            features.dlc,
            features.avg_byte_value,
            features.time_since_last,
            features.byte_0,
            features.byte_1,
            is_attack ? 1 : 0);
    
    exporter->samples_exported++;
}

void MLExporter_Close(MLExporter* exporter) {
    if (exporter->csv_file) {
        fclose(exporter->csv_file);
        printf("[ML-EXPORTER] Exported %u samples to %s\n", 
               exporter->samples_exported, exporter->filename);
    }
}