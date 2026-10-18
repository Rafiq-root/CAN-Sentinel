#ifndef CAN_FRAME_H
#define CAN_FRAME_H

#include <stdint.h>
#include <stdbool.h>

// CAN 2.0B Standard (11-bit identifier)
#define CAN_ID_BITS 11
#define CAN_MAX_DATA_LEN 8

// CAN Message Priority (lower ID = higher priority)
typedef enum {
    CAN_PRIORITY_CRITICAL = 0x000,  // 0-99: Critical (engine, brakes)
    CAN_PRIORITY_HIGH     = 0x100,  // 256-511: High (transmission, steering)
    CAN_PRIORITY_MEDIUM   = 0x300,  // 768-1023: Medium (HVAC, lights)
    CAN_PRIORITY_LOW      = 0x500   // 1280+: Low (infotainment)
} CANPriority;

// Standard CAN Frame Structure
typedef struct {
    uint16_t id;                    // 11-bit identifier (0-2047)
    uint8_t  dlc;                   // Data Length Code (0-8 bytes)
    uint8_t  data[CAN_MAX_DATA_LEN]; // Payload data
    uint32_t timestamp;             // Timestamp (milliseconds)
    bool     rtr;                   // Remote Transmission Request
    bool     error;                 // Error flag
} CANFrame;

// Common CAN Message IDs (example automotive IDs)
#define CAN_ID_ENGINE_RPM       0x100
#define CAN_ID_VEHICLE_SPEED    0x110
#define CAN_ID_BRAKE_STATUS     0x120
#define CAN_ID_STEERING_ANGLE   0x130
#define CAN_ID_TEMPERATURE      0x200
#define CAN_ID_FUEL_LEVEL       0x210
#define CAN_ID_DOOR_STATUS      0x300
#define CAN_ID_LIGHTS_STATUS    0x310
#define CAN_ID_DIAGNOSTIC       0x7DF  // OBD-II diagnostic

// Function prototypes
void CAN_InitFrame(CANFrame* frame);
void CAN_SetData(CANFrame* frame, uint16_t id, const uint8_t* data, uint8_t len);
void CAN_PrintFrame(const CANFrame* frame);
bool CAN_ValidateFrame(const CANFrame* frame);
int CAN_CompareID(uint16_t id1, uint16_t id2); // For arbitration

#endif