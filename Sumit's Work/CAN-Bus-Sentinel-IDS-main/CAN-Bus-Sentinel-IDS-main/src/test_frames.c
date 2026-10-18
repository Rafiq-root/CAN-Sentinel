#include <stdio.h>
#include "can_frame.h"

int main(void) {
    CANFrame frame;
    
    printf("=== CAN Frame Structure Test ===\n\n");
    
    // Test 1: Engine RPM message
    uint8_t rpm_data[] = {0x1A, 0x2F, 0x00, 0x00};  // RPM = 3000
    CAN_InitFrame(&frame);
    CAN_SetData(&frame, CAN_ID_ENGINE_RPM, rpm_data, 4);
    printf("Engine RPM Message:\n");
    CAN_PrintFrame(&frame);
    
    // Test 2: Vehicle Speed
    uint8_t speed_data[] = {0x78};  // 120 km/h
    CAN_InitFrame(&frame);
    CAN_SetData(&frame, CAN_ID_VEHICLE_SPEED, speed_data, 1);
    printf("\nVehicle Speed Message:\n");
    CAN_PrintFrame(&frame);
    
    // Test 3: Brake Status
    uint8_t brake_data[] = {0x01};  // Brake pressed
    CAN_InitFrame(&frame);
    CAN_SetData(&frame, CAN_ID_BRAKE_STATUS, brake_data, 1);
    printf("\nBrake Status Message:\n");
    CAN_PrintFrame(&frame);
    
    // Test 4: Priority comparison
    printf("\n=== Priority Test ===\n");
    printf("Engine (0x%03X) vs Speed (0x%03X): ", CAN_ID_ENGINE_RPM, CAN_ID_VEHICLE_SPEED);
    int result = CAN_CompareID(CAN_ID_ENGINE_RPM, CAN_ID_VEHICLE_SPEED);
    if (result < 0) {
        printf("Engine wins (higher priority)\n");
    } else {
        printf("Speed wins (higher priority)\n");
    }
    
    return 0;
}