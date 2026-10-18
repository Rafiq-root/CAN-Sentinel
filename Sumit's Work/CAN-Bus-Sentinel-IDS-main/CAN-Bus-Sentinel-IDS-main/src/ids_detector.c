#include "ids_detector.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// ANSI Color Codes
#define COLOR_RED     "\x1b[31m"
#define COLOR_YELLOW  "\x1b[33m"
#define COLOR_GREEN   "\x1b[32m"
#define COLOR_BLUE    "\x1b[34m"
#define COLOR_MAGENTA "\x1b[35m"
#define COLOR_CYAN    "\x1b[36m"
#define COLOR_RESET   "\x1b[0m"
#define COLOR_BOLD    "\x1b[1m"

// ============= IDS Controller =============

void IDS_Init(IDSController* ids) {
    memset(ids, 0, sizeof(IDSController));
    
    IDWhitelist_Init(&ids->id_detector);
    Frequency_Init(&ids->freq_detector);
    Payload_Init(&ids->payload_detector);
    BusLoad_Init(&ids->load_detector);
    MLDetector_Init(&ids->ml_detector);
    
    ids->learning_mode = false;
    ids->current_cycle = 0;
}

void IDS_StartLearning(IDSController* ids, int cycles) {
    ids->learning_mode = true;
    ids->learning_cycles = cycles;
    printf("[IDS] Learning mode started for %d cycles\n", cycles);
}

void IDS_StopLearning(IDSController* ids) {
    ids->learning_mode = false;
    printf("[IDS] Learning complete. System armed with:\n");
    printf("  - %d known CAN IDs\n", ids->id_detector.known_count);
    printf("  - %d frequency monitors\n", ids->freq_detector.monitor_count);
    printf("  - %d payload validators\n", ids->payload_detector.validator_count);
    printf("  - Bus load baseline: %d frames/cycle\n", ids->load_detector.baseline_frames);
}

bool IDS_AnalyzeFrame(IDSController* ids, const CANFrame* frame, int cycle) {
    ids->frames_analyzed++;
    ids->current_cycle = cycle;
    
    // During learning, just record patterns
    if (ids->learning_mode) {
        IDWhitelist_Learn(&ids->id_detector, frame->id);
        Frequency_Learn(&ids->freq_detector, frame->id, cycle);
        Payload_Learn(&ids->payload_detector, frame);
        return false;  // No detections during learning
    }
    
    // After learning, check for anomalies
    DetectionAlert alert;
    bool detected = false;
    
    // Check 1: Unknown CAN ID
    if (IDWhitelist_Check(&ids->id_detector, frame->id, &alert, cycle)) {
        ids->alerts[ids->alert_count++] = alert;
        ids->attacks_detected++;
        detected = true;
        
        printf("  " COLOR_RED "[IDS-ALERT]" COLOR_RESET " %s (Confidence: %.0f%%)\n", 
                alert.description, alert.confidence * 100);
    }
    
    // Check 2: Frequency anomaly
    if (Frequency_Check(&ids->freq_detector, frame->id, cycle, &alert)) {
        ids->alerts[ids->alert_count++] = alert;
        ids->attacks_detected++;
        detected = true;
        
        printf("  " COLOR_RED "[IDS-ALERT]" COLOR_RESET " %s (Confidence: %.0f%%)\n",
                alert.description, alert.confidence * 100);
    }
    
    // Check 3: Payload anomaly
    if (Payload_Check(&ids->payload_detector, frame, &alert, cycle)) {
        ids->alerts[ids->alert_count++] = alert;
        ids->attacks_detected++;
        detected = true;
        
        printf("  " COLOR_RED "[IDS-ALERT]" COLOR_RESET " %s (Confidence: %.0f%%)\n",
                alert.description, alert.confidence * 100);
    }
    

        // Check 4: ML-based detection
    MLDetectionResult ml_result;
    if (MLDetector_Detect(&ids->ml_detector, frame, cycle, &ml_result)) {
        DetectionAlert alert;
        alert.detector = DETECTOR_SEQUENCE;
        alert.severity = ALERT_WARNING;
        alert.can_id = frame->id;
        alert.cycle = cycle;
        alert.confidence = 0.70;
        alert.suspected_attack = ATTACK_FUZZING;
        snprintf(alert.description, 128,
                "ML anomaly detected on ID 0x%03X (score: %.3f)",
                frame->id, ml_result.anomaly_score);
        
        ids->alerts[ids->alert_count++] = alert;
        ids->attacks_detected++;
        detected = true;
        
        printf("  \x1b[35m[IDS-ML]\x1b[0m %s\n", alert.description);
    }

    return detected;
}

void IDS_UpdateCycle(IDSController* ids, int cycle, int frames_this_cycle) {
    ids->current_cycle = cycle;
    
    // During learning, track baseline
    if (ids->learning_mode) {
        BusLoad_Learn(&ids->load_detector, frames_this_cycle);
        return;
    }
    
    // After learning, check for DoS
    DetectionAlert alert;
    if (BusLoad_Check(&ids->load_detector, frames_this_cycle, cycle, &alert)) {
        ids->alerts[ids->alert_count++] = alert;
        ids->attacks_detected++;
        
        printf("  " COLOR_RED "[IDS-ALERT]" COLOR_RESET " %s (Confidence: %.0f%%)\n",
            alert.description, alert.confidence * 100);
    }
}

void IDS_PrintStats(const IDSController* ids) {
    printf("\n========================================\n");
    printf("      IDS DETECTION STATISTICS          \n");
    printf("========================================\n");
    printf("Frames Analyzed:     %u\n", ids->frames_analyzed);
    printf("Attacks Detected:    %u\n", ids->attacks_detected);
    printf("Total Alerts:        %d\n", ids->alert_count);
    printf("False Positives:     %u\n", ids->false_positives);
    
    if (ids->attacks_detected > 0) {
        float detection_rate = (float)ids->attacks_detected / ids->frames_analyzed * 100;
        printf("Detection Rate:      %.2f%%\n", detection_rate);
    }
    
    printf("========================================\n");
}

void IDS_PrintAlerts(const IDSController* ids, int last_n) {
    printf("\n========================================\n");
    printf("      RECENT SECURITY ALERTS            \n");
    printf("========================================\n");
    
    if (ids->alert_count == 0) {
        printf("No alerts detected.\n");
        printf("========================================\n");
        return;
    }
    
    int start = (ids->alert_count > last_n) ? (ids->alert_count - last_n) : 0;
    
    for (int i = start; i < ids->alert_count; i++) {
        const DetectionAlert* alert = &ids->alerts[i];
        
        printf("\n[Alert #%d] Cycle %d\n", i + 1, alert->cycle);
        printf("  Severity:    ");
        switch (alert->severity) {
            case ALERT_INFO:     printf("INFO\n"); break;
            case ALERT_WARNING:  printf("WARNING\n"); break;
            case ALERT_CRITICAL: printf("CRITICAL\n"); break;
        }
printf("  Detector:    ");
switch (alert->detector) {
    case DETECTOR_ID_WHITELIST:  printf("ID Whitelist\n"); break;
    case DETECTOR_FREQUENCY:     printf("Frequency Anomaly\n"); break;
    case DETECTOR_PAYLOAD_RANGE: printf("Payload Range\n"); break;
    case DETECTOR_BUS_LOAD:      printf("Bus Load\n"); break;
    case DETECTOR_SEQUENCE:      printf("Sequence Anomaly\n"); break;
    case DETECTOR_ML_STATISTICAL: printf("ML Statistical\n"); break;  
}
        printf("  CAN ID:      0x%03X\n", alert->can_id);
        printf("  Confidence:  %.0f%%\n", alert->confidence * 100);
        printf("  Description: %s\n", alert->description);
        printf("  Suspected:   ");
        switch (alert->suspected_attack) {
            case ATTACK_FUZZING:     printf("Fuzzing Attack\n"); break;
            case ATTACK_DOS_FLOOD:   printf("DoS Flood\n"); break;
            case ATTACK_INJECTION:   printf("Message Injection\n"); break;
            case ATTACK_REPLAY:      printf("Replay Attack\n"); break;
            case ATTACK_MASQUERADE:  printf("ECU Masquerade\n"); break;
            default:                 printf("Unknown\n"); break;
        }
    }
    
    printf("========================================\n");
}

// ============= ID Whitelist Detector =============

void IDWhitelist_Init(IDWhitelistDetector* detector) {
    memset(detector, 0, sizeof(IDWhitelistDetector));
}

void IDWhitelist_Learn(IDWhitelistDetector* detector, uint16_t can_id) {
    // Check if already known
    for (int i = 0; i < detector->known_count; i++) {
        if (detector->known_ids[i] == can_id) {
            return;  // Already in whitelist
        }
    }
    
    // Add new ID
    if (detector->known_count < 32) {
        detector->known_ids[detector->known_count++] = can_id;
    }
}

bool IDWhitelist_Check(IDWhitelistDetector* detector, uint16_t can_id, 
                       DetectionAlert* alert, int cycle) {
    // Check if ID is in whitelist
    for (int i = 0; i < detector->known_count; i++) {
        if (detector->known_ids[i] == can_id) {
            return false;  // Known ID, no alert
        }
    }
    
    // Unknown ID detected!
    alert->detector = DETECTOR_ID_WHITELIST;
    alert->severity = ALERT_WARNING;
    alert->can_id = can_id;
    alert->cycle = cycle;
    alert->confidence = 0.95;
    alert->suspected_attack = ATTACK_FUZZING;
    snprintf(alert->description, 128, "Unknown CAN ID detected: 0x%03X", can_id);
    
    return true;
}

// ============= Frequency Detector =============

void Frequency_Init(FrequencyDetector* detector) {
    memset(detector, 0, sizeof(FrequencyDetector));
}

void Frequency_Learn(FrequencyDetector* detector, uint16_t can_id, int cycle) {
    // Find existing monitor for this ID
    FrequencyMonitor* monitor = NULL;
    for (int i = 0; i < detector->monitor_count; i++) {
        if (detector->monitors[i].can_id == can_id) {
            monitor = &detector->monitors[i];
            break;
        }
    }
    
    // Create new monitor if needed
    if (monitor == NULL && detector->monitor_count < 32) {
        monitor = &detector->monitors[detector->monitor_count++];
        monitor->can_id = can_id;
        monitor->last_seen_cycle = cycle;
        monitor->message_count = 1;
        monitor->expected_period = 1;  // Default: every cycle
        return;
    }
    
    if (monitor) {
        // Update statistics
        int period = cycle - monitor->last_seen_cycle;
        monitor->expected_period = period;  // Simple: just use last period
        monitor->last_seen_cycle = cycle;
        monitor->message_count++;
    }
}

bool Frequency_Check(FrequencyDetector* detector, uint16_t can_id, int cycle,
                     DetectionAlert* alert) {
    // Find monitor for this ID
    for (int i = 0; i < detector->monitor_count; i++) {
        FrequencyMonitor* monitor = &detector->monitors[i];
        
        if (monitor->can_id == can_id) {
            int period = cycle - monitor->last_seen_cycle;
            int expected = monitor->expected_period;
            
            // Skip check on first cycle after learning (avoid negative/zero period)
            if (period <= 0) {
                monitor->last_seen_cycle = cycle;
                monitor->message_count++;
                return false;
            }
            
            // Check if message is too frequent (period too short)
            if (expected > 0 && period < expected / 2) {
                alert->detector = DETECTOR_FREQUENCY;
                alert->severity = ALERT_WARNING;
                alert->can_id = can_id;
                alert->cycle = cycle;
                alert->confidence = 0.80;
                alert->suspected_attack = ATTACK_DOS_FLOOD;
                snprintf(alert->description, 128, 
                        "High frequency anomaly on ID 0x%03X (period: %d, expected: %d)",
                        can_id, period, expected);
                
                // Update for next check
                monitor->last_seen_cycle = cycle;
                monitor->message_count++;
                
                return true;
            }
            
            // Update for next check
            monitor->last_seen_cycle = cycle;
            monitor->message_count++;
            break;
        }
    }
    
    return false;
}

// ============= Payload Detector =============

void Payload_Init(PayloadDetector* detector) {
    memset(detector, 0, sizeof(PayloadDetector));
}

void Payload_Learn(PayloadDetector* detector, const CANFrame* frame) {
    // Find existing validator for this ID
    PayloadValidator* validator = NULL;
    for (int i = 0; i < detector->validator_count; i++) {
        if (detector->validators[i].can_id == frame->id) {
            validator = &detector->validators[i];
            break;
        }
    }
    
    // Create new validator if needed
    if (validator == NULL && detector->validator_count < 32) {
        validator = &detector->validators[detector->validator_count++];
        validator->can_id = frame->id;
        validator->expected_dlc = frame->dlc;
        
        // Initialize ranges
        for (int i = 0; i < 8; i++) {
            validator->min_values[i] = 255;
            validator->max_values[i] = 0;
        }
    }
    
    if (validator) {
        // Update ranges
        for (int i = 0; i < frame->dlc; i++) {
            if (frame->data[i] < validator->min_values[i]) {
                validator->min_values[i] = frame->data[i];
            }
            if (frame->data[i] > validator->max_values[i]) {
                validator->max_values[i] = frame->data[i];
            }
        }
        
        // Add some tolerance (±20%)
        for (int i = 0; i < frame->dlc; i++) {
            int range = validator->max_values[i] - validator->min_values[i];
            int tolerance = range / 5;  // 20%
            
            validator->min_values[i] = (validator->min_values[i] > tolerance) ? 
                                       (validator->min_values[i] - tolerance) : 0;
            validator->max_values[i] = (validator->max_values[i] + tolerance < 255) ?
                                       (validator->max_values[i] + tolerance) : 255;
        }
    }
}

bool Payload_Check(PayloadDetector* detector, const CANFrame* frame,
                   DetectionAlert* alert, int cycle) {
    // Find validator for this ID
    for (int i = 0; i < detector->validator_count; i++) {
        PayloadValidator* validator = &detector->validators[i];
        
        if (validator->can_id == frame->id) {
            // Check DLC
            if (frame->dlc != validator->expected_dlc) {
                alert->detector = DETECTOR_PAYLOAD_RANGE;
                alert->severity = ALERT_WARNING;
                alert->can_id = frame->id;
                alert->cycle = cycle;
                alert->confidence = 0.85;
                alert->suspected_attack = ATTACK_INJECTION;
                snprintf(alert->description, 128,
                        "Invalid DLC on ID 0x%03X (got: %d, expected: %d)",
                        frame->id, frame->dlc, validator->expected_dlc);
                return true;
            }
            
            // Check payload ranges
            for (int j = 0; j < frame->dlc; j++) {
                if (frame->data[j] < validator->min_values[j] ||
                    frame->data[j] > validator->max_values[j]) {
                    
                    alert->detector = DETECTOR_PAYLOAD_RANGE;
                    alert->severity = ALERT_WARNING;
                    alert->can_id = frame->id;
                    alert->cycle = cycle;
                    alert->confidence = 0.75;
                    alert->suspected_attack = ATTACK_INJECTION;
                    snprintf(alert->description, 128,
                            "Out-of-range value on ID 0x%03X byte[%d]: %d (range: %d-%d)",
                            frame->id, j, frame->data[j],
                            validator->min_values[j], validator->max_values[j]);
                    return true;
                }
            }
            
            break;
        }
    }
    
    return false;
}

// ============= Bus Load Detector =============

void BusLoad_Init(BusLoadDetector* detector) {
    memset(detector, 0, sizeof(BusLoadDetector));
    detector->threshold_multiplier = 2.5;  // Alert if 2.5x normal load
}

void BusLoad_Learn(BusLoadDetector* detector, int frames) {
    detector->frames_this_cycle = frames;
    
    // Simple moving average
    if (detector->baseline_frames == 0) {
        detector->baseline_frames = frames;
    } else {
        detector->baseline_frames = (detector->baseline_frames + frames) / 2;
    }
}

bool BusLoad_Check(BusLoadDetector* detector, int frames, int cycle,
                   DetectionAlert* alert) {
    detector->frames_this_cycle = frames;
    
    // Check if load exceeds threshold
    int threshold = (int)(detector->baseline_frames * detector->threshold_multiplier);
    
    if (frames > threshold) {
        alert->detector = DETECTOR_BUS_LOAD;
        alert->severity = ALERT_CRITICAL;
        alert->can_id = 0x000;  // Not specific to one ID
        alert->cycle = cycle;
        alert->confidence = 0.90;
        alert->suspected_attack = ATTACK_DOS_FLOOD;
        snprintf(alert->description, 128,
                "Bus load spike detected: %d frames (baseline: %d, threshold: %d)",
                frames, detector->baseline_frames, threshold);
        return true;
    }
    
    return false;
}