#ifndef DTC_MANAGER_H
#define DTC_MANAGER_H

#include <stdint.h>
#include <stdbool.h>

// Standard OBD-II DTC format: P0XXX (Powertrain), C0XXX (Chassis), etc.
typedef enum {
    DTC_NONE                    = 0x0000,
    DTC_ENGINE_MISFIRE          = 0x0300,
    DTC_ENGINE_OVERHEAT         = 0x0115,
    DTC_BRAKE_PRESSURE_LOW      = 0xC0550,
    DTC_ABS_MALFUNCTION         = 0xC0265,
    DTC_TRANSMISSION_SLIP       = 0x0730,
    DTC_SENSOR_COMMUNICATION    = 0xF100,  // Network/Communication code
    DTC_LOW_FUEL_PRESSURE       = 0x0087
} DTCCode;

typedef struct {
    DTCCode code;
    char description[64];
    uint32_t timestamp;
    bool active;
} DTCEntry;

#define MAX_DTC_ENTRIES 20

typedef struct {
    DTCEntry entries[MAX_DTC_ENTRIES];
    int count;
} DTCManager;

// DTC operations
void DTC_Init(DTCManager* mgr);
bool DTC_Add(DTCManager* mgr, DTCCode code, const char* description);
void DTC_Clear(DTCManager* mgr);
void DTC_PrintAll(const DTCManager* mgr);
int DTC_GetActiveCount(const DTCManager* mgr);

#endif