#include "dtc_manager.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void DTC_Init(DTCManager* mgr) {
    memset(mgr, 0, sizeof(DTCManager));
}

bool DTC_Add(DTCManager* mgr, DTCCode code, const char* description) {
    if (mgr->count >= MAX_DTC_ENTRIES) {
        printf("[DTC] Warning: DTC storage full\n");
        return false;
    }
    
    // Check if DTC already exists
    for (int i = 0; i < mgr->count; i++) {
        if (mgr->entries[i].code == code && mgr->entries[i].active) {
            printf("[DTC] Code 0x%04X already active\n", code);
            return false;
        }
    }
    
    DTCEntry* entry = &mgr->entries[mgr->count];
    entry->code = code;
    strncpy(entry->description, description, sizeof(entry->description) - 1);
    entry->timestamp = (uint32_t)time(NULL);
    entry->active = true;
    mgr->count++;
    
    printf("[DTC] ⚠️  NEW FAULT: 0x%04X - %s\n", code, description);
    return true;
}

void DTC_Clear(DTCManager* mgr) {
    for (int i = 0; i < mgr->count; i++) {
        mgr->entries[i].active = false;
    }
    printf("[DTC] All codes cleared\n");
}

void DTC_PrintAll(const DTCManager* mgr) {
    printf("\n========================================\n");
    printf("   DIAGNOSTIC TROUBLE CODES             \n");
    printf("========================================\n");
    
    int active_count = 0;
    for (int i = 0; i < mgr->count; i++) {
        if (mgr->entries[i].active) {
            printf("  [%d] Code: 0x%04X - %s\n", 
                   i + 1, 
                   mgr->entries[i].code, 
                   mgr->entries[i].description);
            active_count++;
        }
    }
    
    if (active_count == 0) {
        printf("  [OK] No active fault codes\n");
    }
    printf("========================================\n");
}

int DTC_GetActiveCount(const DTCManager* mgr) {
    int count = 0;
    for (int i = 0; i < mgr->count; i++) {
        if (mgr->entries[i].active) count++;
    }
    return count;
}