#ifndef IDS_DETECTOR_H
#define IDS_DETECTOR_H

#include "can_frame.h"
#include "can_bus.h"
#include "attack_injector.h"
#include <stdbool.h>
#include "ml_detector.h" 

// Detection methods
typedef enum {
    DETECTOR_ID_WHITELIST,     // 0 - Unknown CAN ID
    DETECTOR_FREQUENCY,        // 1 - Message rate anomaly
    DETECTOR_PAYLOAD_RANGE,    // 2 - Out-of-range values
    DETECTOR_BUS_LOAD,         // 3 - Bus saturation
    DETECTOR_SEQUENCE,         // 4 - Replay/Sequence detection (ML uses this)
    DETECTOR_ML_STATISTICAL    // 5 - ML Statistical anomaly (optional)
} DetectorType;


// Alert severity
typedef enum {
    ALERT_INFO,
    ALERT_WARNING,
    ALERT_CRITICAL
} AlertLevel;

// Detection alert
typedef struct {
    DetectorType detector;
    AlertLevel severity;
    uint16_t can_id;
    int cycle;
    float confidence;         // 0.0 to 1.0
    char description[128];
    AttackType suspected_attack;
} DetectionAlert;

// ID Whitelist Detector
typedef struct {
    uint16_t known_ids[32];
    int known_count;
} IDWhitelistDetector;

// Frequency Detector
typedef struct {
    uint16_t can_id;
    int last_seen_cycle;
    int message_count;
    int expected_period;      // Expected cycles between messages
} FrequencyMonitor;

typedef struct {
    FrequencyMonitor monitors[32];
    int monitor_count;
} FrequencyDetector;

// Payload Range Detector
typedef struct {
    uint16_t can_id;
    uint8_t min_values[8];
    uint8_t max_values[8];
    uint8_t expected_dlc;
} PayloadValidator;

typedef struct {
    PayloadValidator validators[32];
    int validator_count;
} PayloadDetector;

// Bus Load Detector
typedef struct {
    int frames_this_cycle;
    int baseline_frames;      // Normal frames per cycle
    float threshold_multiplier; // Alert if frames > baseline * threshold
} BusLoadDetector;

// Master IDS Controller
typedef struct {
    // Detection engines
    IDWhitelistDetector id_detector;
    FrequencyDetector freq_detector;
    PayloadDetector payload_detector;
    BusLoadDetector load_detector;
    MLDetector ml_detector;
    
    // Alerts
    DetectionAlert alerts[200];
    int alert_count;
    
    // Learning mode
    bool learning_mode;
    int learning_cycles;
    int current_cycle;
    
    // Statistics
    uint32_t frames_analyzed;
    uint32_t attacks_detected;
    uint32_t false_positives;
    
} IDSController;

// ============= Core Functions =============

// Initialize IDS
void IDS_Init(IDSController* ids);

// Start learning normal traffic
void IDS_StartLearning(IDSController* ids, int cycles);

// Stop learning and arm detectors
void IDS_StopLearning(IDSController* ids);

// Analyze a frame (call during reception phase)
bool IDS_AnalyzeFrame(IDSController* ids, const CANFrame* frame, int cycle);

// Update detectors (call each cycle)
void IDS_UpdateCycle(IDSController* ids, int cycle, int frames_this_cycle);

// Print detection statistics
void IDS_PrintStats(const IDSController* ids);

// Print recent alerts
void IDS_PrintAlerts(const IDSController* ids, int last_n);

// ============= Individual Detectors =============

// ID Whitelist
void IDWhitelist_Init(IDWhitelistDetector* detector);
void IDWhitelist_Learn(IDWhitelistDetector* detector, uint16_t can_id);
bool IDWhitelist_Check(IDWhitelistDetector* detector, uint16_t can_id, 
                       DetectionAlert* alert, int cycle);

// Frequency Monitor
void Frequency_Init(FrequencyDetector* detector);
void Frequency_Learn(FrequencyDetector* detector, uint16_t can_id, int cycle);
bool Frequency_Check(FrequencyDetector* detector, uint16_t can_id, int cycle,
                     DetectionAlert* alert);

// Payload Range
void Payload_Init(PayloadDetector* detector);
void Payload_Learn(PayloadDetector* detector, const CANFrame* frame);
bool Payload_Check(PayloadDetector* detector, const CANFrame* frame,
                   DetectionAlert* alert, int cycle);

// Bus Load
void BusLoad_Init(BusLoadDetector* detector);
void BusLoad_Learn(BusLoadDetector* detector, int frames);
bool BusLoad_Check(BusLoadDetector* detector, int frames, int cycle,
                   DetectionAlert* alert);

#endif // IDS_DETECTOR_H