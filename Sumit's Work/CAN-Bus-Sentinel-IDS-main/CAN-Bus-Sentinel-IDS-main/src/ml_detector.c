#include "ml_detector.h"
#include <string.h>
#include <math.h>

void MLDetector_Init(MLDetector* detector) {
    memset(detector, 0, sizeof(MLDetector));
}

static void extract_features(MLDetector* detector, const CANFrame* frame, 
                             uint32_t timestamp, float* features) {
    features[0] = (float)frame->id;
    features[1] = (float)frame->dlc;

    // Average byte value
    float sum = 0;
    for (int i = 0; i < frame->dlc; i++) {
        sum += frame->data[i];
    }
    features[2] = (frame->dlc > 0) ? (sum / frame->dlc) : 0.0f;

    // Time since last (safe indexing)
    uint32_t index = frame->id % 2048;
    uint32_t last_time = detector->last_seen_time[index];
    features[3] = (float)((last_time > 0) ? (timestamp - last_time) : 0);
    detector->last_seen_time[index] = timestamp;

    // Individual bytes
    features[4] = (frame->dlc > 0) ? (float)frame->data[0] : 0.0f;
    features[5] = (frame->dlc > 1) ? (float)frame->data[1] : 0.0f;
}

static void normalize_features(float* features) {
    for (int i = 0; i < ML_NUM_FEATURES; i++) {
        if (ML_FEATURE_STDS[i] > 0.0f) {
            features[i] = (features[i] - ML_FEATURE_MEANS[i]) / ML_FEATURE_STDS[i];
            // Clamp extreme values
            if (features[i] > 5.0f) features[i] = 5.0f;
            else if (features[i] < -5.0f) features[i] = -5.0f;
        } else {
            features[i] = 0.0f;
        }
    }
}

static float get_anomaly_score(const float* features) {
    float sum_sq = 0.0f;
    for (int i = 0; i < ML_NUM_FEATURES; i++) {
        sum_sq += features[i] * features[i];
    }
    return -sqrtf(sum_sq / ML_NUM_FEATURES);
}

bool MLDetector_Detect(MLDetector* detector, const CANFrame* frame, 
                       uint32_t timestamp, MLDetectionResult* result) {
    detector->frames_analyzed++;

    extract_features(detector, frame, timestamp, result->features);
    normalize_features(result->features);
    result->anomaly_score = get_anomaly_score(result->features);
    result->is_anomaly = (result->anomaly_score < ML_THRESHOLD);

    if (result->is_anomaly) {
        detector->anomalies_detected++;
    }

    return result->is_anomaly;
}
