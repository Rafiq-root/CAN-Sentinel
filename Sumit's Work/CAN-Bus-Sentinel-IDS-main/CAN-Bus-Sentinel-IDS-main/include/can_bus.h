#ifndef CAN_BUS_H
#define CAN_BUS_H

#include "can_frame.h"
#include <stdbool.h>

#define MAX_BUS_QUEUE 100
#define MAX_SUBSCRIBERS 10

// CAN Bus statistics
typedef struct {
    uint32_t total_frames;
    uint32_t collisions;
    uint32_t errors;
    uint32_t dropped_frames;
} CANBusStats;



// Virtual CAN Bus
typedef struct {
    CANFrame queue[MAX_BUS_QUEUE];
    int queue_head;
    int queue_tail;
    int queue_count;
    CANBusStats stats;
    bool bus_active;
} CANBus;

// Bus operations
void CANBus_Init(CANBus* bus);
bool CANBus_Transmit(CANBus* bus, const CANFrame* frame);
bool CANBus_Receive(CANBus* bus, CANFrame* frame);
bool CANBus_IsEmpty(const CANBus* bus);
void CANBus_PrintStats(const CANBus* bus);
void CANBus_Clear(CANBus* bus);

// Arbitration - returns true if frame1 wins
bool CANBus_Arbitrate(const CANFrame* frame1, const CANFrame* frame2);

#endif