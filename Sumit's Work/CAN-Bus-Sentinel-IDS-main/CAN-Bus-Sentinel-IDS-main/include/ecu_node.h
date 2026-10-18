#ifndef ECU_NODE_H
#define ECU_NODE_H

#include "can_frame.h"
#include "can_bus.h"

#define ECU_NAME_LEN 32

typedef enum {
    ECU_ENGINE_CONTROL,
    ECU_TRANSMISSION,
    ECU_BRAKE_SYSTEM,
    ECU_BODY_CONTROL,
    ECU_INFOTAINMENT
} ECUType;

typedef struct {
    char name[ECU_NAME_LEN];
    ECUType type;
    uint32_t frames_sent;
    uint32_t frames_received;
    bool active;
} ECUNode;

// ECU operations
void ECU_Init(ECUNode* ecu, const char* name, ECUType type);
void ECU_SendFrame(ECUNode* ecu, CANBus* bus, const CANFrame* frame);
bool ECU_ReceiveFrame(ECUNode* ecu, CANBus* bus, CANFrame* frame);
void ECU_PrintStats(const ECUNode* ecu);

// Simulated ECU behaviors
void ECU_EngineControl_Update(ECUNode* ecu, CANBus* bus);
void ECU_BrakeSystem_Update(ECUNode* ecu, CANBus* bus);
void ECU_BodyControl_Update(ECUNode* ecu, CANBus* bus);

#endif