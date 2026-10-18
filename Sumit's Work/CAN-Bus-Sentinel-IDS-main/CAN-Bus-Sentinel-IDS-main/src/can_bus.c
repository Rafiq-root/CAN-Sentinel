#include "can_bus.h"
#include <stdio.h>
#include <string.h>

void CANBus_Init(CANBus* bus) {
    memset(bus, 0, sizeof(CANBus));
    bus->bus_active = true;
}

bool CANBus_Transmit(CANBus* bus, const CANFrame* frame) {
    if (!bus->bus_active) {
        printf("[BUS] Error: Bus is inactive\n");
        bus->stats.errors++;
        return false;
    }
    
    if (!CAN_ValidateFrame(frame)) {
        printf("[BUS] Error: Invalid frame\n");
        bus->stats.errors++;
        return false;
    }
    
    // Check if queue is full
    if (bus->queue_count >= MAX_BUS_QUEUE) {
        printf("[BUS] Error: Queue full, frame dropped\n");
        bus->stats.dropped_frames++;
        return false;
    }
    
    // Add frame to queue
    bus->queue[bus->queue_tail] = *frame;
    bus->queue_tail = (bus->queue_tail + 1) % MAX_BUS_QUEUE;
    bus->queue_count++;
    bus->stats.total_frames++;
    
    return true;
}

bool CANBus_Receive(CANBus* bus, CANFrame* frame) {
    if (bus->queue_count == 0) {
        return false;
    }
    
    // Get frame from queue
    *frame = bus->queue[bus->queue_head];
    bus->queue_head = (bus->queue_head + 1) % MAX_BUS_QUEUE;
    bus->queue_count--;
    
    return true;
}

bool CANBus_IsEmpty(const CANBus* bus) {
    return (bus->queue_count == 0);
}

void CANBus_PrintStats(const CANBus* bus) {
    printf("\n========================================\n");
    printf("      CAN BUS STATISTICS                \n");
    printf("========================================\n");
    printf("Total Frames:    %u\n", bus->stats.total_frames);
    printf("Collisions:      %u\n", bus->stats.collisions);
    printf("Errors:          %u\n", bus->stats.errors);
    printf("Dropped Frames:  %u\n", bus->stats.dropped_frames);
    printf("Bus Status:      %s\n", bus->bus_active ? "ACTIVE" : "INACTIVE");
    printf("Queue Size:      %d/%d\n", bus->queue_count, MAX_BUS_QUEUE);
    printf("========================================\n");
}

void CANBus_Clear(CANBus* bus) {
    bus->queue_head = 0;
    bus->queue_tail = 0;
    bus->queue_count = 0;
}

bool CANBus_Arbitrate(const CANFrame* frame1, const CANFrame* frame2) {
    // Lower ID wins (CAN arbitration rule)
    return (frame1->id < frame2->id);
}