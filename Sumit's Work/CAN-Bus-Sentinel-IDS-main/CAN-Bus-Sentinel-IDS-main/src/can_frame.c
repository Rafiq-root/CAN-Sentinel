#include "can_frame.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void CAN_InitFrame(CANFrame* frame) {
    memset(frame, 0, sizeof(CANFrame));
    frame->timestamp = (uint32_t)time(NULL);
}

void CAN_SetData(CANFrame* frame, uint16_t id, const uint8_t* data, uint8_t len) {
    frame->id = id & 0x7FF;  // Mask to 11 bits
    frame->dlc = (len > CAN_MAX_DATA_LEN) ? CAN_MAX_DATA_LEN : len;
    memcpy(frame->data, data, frame->dlc);
    frame->timestamp = (uint32_t)(time(NULL) * 1000);
    frame->rtr = false;
    frame->error = false;
}

void CAN_PrintFrame(const CANFrame* frame) {
    printf("CAN Frame [ID:0x%03X DLC:%d] Data: ", frame->id, frame->dlc);
    for (int i = 0; i < frame->dlc; i++) {
        printf("%02X ", frame->data[i]);
    }
    printf("| Time:%u ms", frame->timestamp);
    if (frame->rtr) printf(" [RTR]");
    if (frame->error) printf(" [ERROR]");
    printf("\n");
}

bool CAN_ValidateFrame(const CANFrame* frame) {
    if (frame->id > 0x7FF) return false;  // Invalid 11-bit ID
    if (frame->dlc > CAN_MAX_DATA_LEN) return false;
    return true;
}

int CAN_CompareID(uint16_t id1, uint16_t id2) {
    // Lower ID has higher priority
    if (id1 < id2) return -1;  // id1 wins arbitration
    if (id1 > id2) return 1;   // id2 wins arbitration
    return 0;                   // Same ID (collision)
}