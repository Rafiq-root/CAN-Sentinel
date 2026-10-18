#include "json_logger.h"
#include <stdio.h>
#include <time.h>



static FILE* json_file = NULL;
static int frame_count = 0;

void JSON_Init(const char* filename) {
    json_file = fopen(filename, "w");
    if (json_file) {
        fprintf(json_file, "{\n");
        fprintf(json_file, "  \"frames\": [\n");
        fflush(json_file);
    }
}

void JSON_LogFrame(const CANFrame* frame, const char* ecu_name) {
    if (!json_file) return;
    
    if (frame_count > 0) {
        fprintf(json_file, ",\n");
    }
    
    fprintf(json_file, "    {\n");
    fprintf(json_file, "      \"id\": \"0x%03X\",\n", frame->id);
    fprintf(json_file, "      \"ecu\": \"%s\",\n", ecu_name);
    fprintf(json_file, "      \"dlc\": %d,\n", frame->dlc);
    fprintf(json_file, "      \"data\": [");
    
    for (int i = 0; i < frame->dlc; i++) {
        fprintf(json_file, "%d", frame->data[i]);
        if (i < frame->dlc - 1) fprintf(json_file, ", ");
    }
    
    fprintf(json_file, "],\n");
    fprintf(json_file, "      \"timestamp\": %u\n", frame->timestamp);
    fprintf(json_file, "    }");
    
    frame_count++;
    fflush(json_file);
}

void JSON_LogStats(const CANBus* bus, ECUNode ecus[], int ecu_count) {
    if (!json_file) return;
    
    fprintf(json_file, "\n  ],\n");
    fprintf(json_file, "  \"statistics\": {\n");
    fprintf(json_file, "    \"total_frames\": %u,\n", bus->stats.total_frames);
    fprintf(json_file, "    \"collisions\": %u,\n", bus->stats.collisions);
    fprintf(json_file, "    \"errors\": %u,\n", bus->stats.errors);
    fprintf(json_file, "    \"dropped_frames\": %u,\n", bus->stats.dropped_frames);
    fprintf(json_file, "    \"bus_active\": %s\n", bus->bus_active ? "true" : "false");
    fprintf(json_file, "  },\n");
    
    fprintf(json_file, "  \"ecus\": [\n");
    for (int i = 0; i < ecu_count; i++) {
        fprintf(json_file, "    {\n");
        fprintf(json_file, "      \"name\": \"%s\",\n", ecus[i].name);
        fprintf(json_file, "      \"frames_sent\": %u,\n", ecus[i].frames_sent);
        fprintf(json_file, "      \"frames_received\": %u,\n", ecus[i].frames_received);
        fprintf(json_file, "      \"active\": %s\n", ecus[i].active ? "true" : "false");
        fprintf(json_file, "    }");
        if (i < ecu_count - 1) fprintf(json_file, ",");
        fprintf(json_file, "\n");
    }
    fprintf(json_file, "  ]");
    
    fflush(json_file);
}

void JSON_LogIDSStats(const IDSController* ids) {
    if (!json_file) return;
    
    fprintf(json_file, ",\n  \"ids_statistics\": {\n");
    fprintf(json_file, "    \"frames_analyzed\": %u,\n", ids->frames_analyzed);
    fprintf(json_file, "    \"attacks_detected\": %u,\n", ids->attacks_detected);
    fprintf(json_file, "    \"false_positives\": %u,\n", ids->false_positives);
    fprintf(json_file, "    \"total_alerts\": %d\n", ids->alert_count);
    fprintf(json_file, "  }");
    
    fflush(json_file);
}

void JSON_LogAlerts(const IDSController* ids) {
    if (!json_file) return;
    
    fprintf(json_file, ",\n  \"alerts\": [\n");
    
    for (int i = 0; i < ids->alert_count; i++) {
        const DetectionAlert* alert = &ids->alerts[i];
        
        fprintf(json_file, "    {\n");
        fprintf(json_file, "      \"detector\": %d,\n", alert->detector);
        fprintf(json_file, "      \"severity\": \"%s\",\n", 
                alert->severity == ALERT_INFO ? "INFO" :
                alert->severity == ALERT_WARNING ? "WARNING" : "CRITICAL");
        fprintf(json_file, "      \"can_id\": \"0x%03X\",\n", alert->can_id);
        fprintf(json_file, "      \"cycle\": %d,\n", alert->cycle);
        fprintf(json_file, "      \"confidence\": %.2f,\n", alert->confidence);
        fprintf(json_file, "      \"suspected_attack\": %d,\n", alert->suspected_attack);
        fprintf(json_file, "      \"description\": \"%s\"\n", alert->description);
        fprintf(json_file, "    }%s\n", (i < ids->alert_count - 1) ? "," : "");
    }
    
    fprintf(json_file, "  ]");
    
    fflush(json_file);
}

void JSON_LogAttackStats(const AttackInjector* injector) {
    if (!json_file) return;
    
    fprintf(json_file, ",\n  \"attack_statistics\": {\n");
    fprintf(json_file, "    \"attacks_configured\": %d,\n", injector->attack_count);
    fprintf(json_file, "    \"total_malicious_frames\": %u,\n", injector->total_malicious_frames);
    
    // Count by attack type
    uint32_t fuzzing = 0, dos = 0, injection = 0;
    for (int i = 0; i < injector->attack_count; i++) {
        switch (injector->attacks[i].type) {
            case ATTACK_FUZZING: fuzzing += injector->attacks[i].frames_injected; break;
            case ATTACK_DOS_FLOOD: dos += injector->attacks[i].frames_injected; break;
            case ATTACK_INJECTION: injection += injector->attacks[i].frames_injected; break;
            default: break;
        }
    }
    
    fprintf(json_file, "    \"fuzzing_frames\": %u,\n", fuzzing);
    fprintf(json_file, "    \"dos_frames\": %u,\n", dos);
    fprintf(json_file, "    \"injection_frames\": %u\n", injection);
    fprintf(json_file, "  }\n");
    fprintf(json_file, "}\n");
    
    fflush(json_file);
}

void JSON_Close(void) {
    if (json_file) {
        fclose(json_file);
        json_file = NULL;
    }
    frame_count = 0;
}