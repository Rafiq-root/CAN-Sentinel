#ifndef ML_DETECTOR_H
#define ML_DETECTOR_H

#include "can_frame.h"
#include "ml_model_params.h"
#include <stdbool.h>

typedef struct {
    float features[ML_NUM_FEATURES];
    float anomaly_score;
    bool is_anomaly;
} MLDetectionResult;

typedef struct {
    uint32_t last_seen_time[2048];
    uint32_t frames_analyzed;
    uint32_t anomalies_detected;
} MLDetector;

void MLDetector_Init(MLDetector* detector);
bool MLDetector_Detect(MLDetector* detector, const CANFrame* frame, 
                       uint32_t timestamp, MLDetectionResult* result);

#endif // ML_DETECTOR_H