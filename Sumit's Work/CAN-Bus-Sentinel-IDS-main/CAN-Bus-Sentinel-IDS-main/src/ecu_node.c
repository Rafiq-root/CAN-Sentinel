#include "ecu_node.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

void ECU_Init(ECUNode* ecu, const char* name, ECUType type) {
    strncpy(ecu->name, name, ECU_NAME_LEN - 1);
    ecu->name[ECU_NAME_LEN - 1] = '\0';
    ecu->type = type;
    ecu->frames_sent = 0;
    ecu->frames_received = 0;
    ecu->active = true;
}

void ECU_SendFrame(ECUNode* ecu, CANBus* bus, const CANFrame* frame) {
    if (!ecu->active) return;
    
    printf("[%s] Sending: ", ecu->name);
    CAN_PrintFrame(frame);
    
    if (CANBus_Transmit(bus, frame)) {
        ecu->frames_sent++;
    }
}

bool ECU_ReceiveFrame(ECUNode* ecu, CANBus* bus, CANFrame* frame) {
    if (!ecu->active) return false;
    
    if (CANBus_Receive(bus, frame)) {
        ecu->frames_received++;
        printf("[%s] Received: ", ecu->name);
        CAN_PrintFrame(frame);
        return true;
    }
    return false;
}

void ECU_PrintStats(const ECUNode* ecu) {
    printf("\n[%s] Stats:\n", ecu->name);
    printf("  Frames Sent:     %u\n", ecu->frames_sent);
    printf("  Frames Received: %u\n", ecu->frames_received);
    printf("  Status:          %s\n", ecu->active ? "ACTIVE" : "INACTIVE");
}

// Simulated Engine Control ECU behavior
void ECU_EngineControl_Update(ECUNode* ecu, CANBus* bus) {
    CANFrame frame;
    CAN_InitFrame(&frame);
    
    // Simulate engine RPM (1000-6000 RPM)
    uint16_t rpm = 1000 + (rand() % 5000);
    uint8_t data[4] = {
        (rpm >> 8) & 0xFF,
        rpm & 0xFF,
        0x00,
        0x00
    };
    
    CAN_SetData(&frame, CAN_ID_ENGINE_RPM, data, 4);
    ECU_SendFrame(ecu, bus, &frame);
    
    // 5% chance of triggering engine fault
    if (rand() % 100 < 5) {
        printf("  [%s] ⚠️  Engine misfire detected!\n", ecu->name);
    }
}

// Simulated Brake System ECU behavior
void ECU_BrakeSystem_Update(ECUNode* ecu, CANBus* bus) {
    CANFrame frame;
    CAN_InitFrame(&frame);
    
    // Simulate brake status (random on/off)
    uint8_t brake_status = (rand() % 10 < 3) ? 0x01 : 0x00;  // 30% chance pressed
    
    CAN_SetData(&frame, CAN_ID_BRAKE_STATUS, &brake_status, 1);
    ECU_SendFrame(ecu, bus, &frame);
}

// Simulated Body Control ECU behavior
void ECU_BodyControl_Update(ECUNode* ecu, CANBus* bus) {
    CANFrame frame;
    CAN_InitFrame(&frame);
    
    // Simulate door status (all doors bitmap: bit0=driver, bit1=passenger, etc.)
    uint8_t door_status = rand() % 16;  // Random door combination
    
    CAN_SetData(&frame, CAN_ID_DOOR_STATUS, &door_status, 1);
    ECU_SendFrame(ecu, bus, &frame);
}