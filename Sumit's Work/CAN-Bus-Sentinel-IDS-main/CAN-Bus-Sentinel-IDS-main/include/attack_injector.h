#ifndef ATTACK_INJECTOR_H
#define ATTACK_INJECTOR_H

#include "can_frame.h"
#include "can_bus.h"
#include <stdbool.h>

// Attack types
typedef enum {
    ATTACK_NONE = 0,
    ATTACK_FUZZING,           // Random ID/data
    ATTACK_DOS_FLOOD,         // Bus saturation
    ATTACK_REPLAY,            // Message replay
    ATTACK_INJECTION,         // Fake messages (e.g., fake brake)
    ATTACK_MASQUERADE         // Impersonate ECU
} AttackType;

// Attack configuration
typedef struct {
    AttackType type;
    int start_cycle;          // Which cycle to start attack
    int duration_cycles;      // How many cycles to run
    bool active;
    
    // Attack-specific settings
    uint16_t target_id;       // For targeted attacks
    int frames_per_cycle;     // How many malicious frames per cycle
    
    // Statistics
    uint32_t frames_injected;
    uint32_t injection_attempts;
    
} AttackConfig;

// Attack Injector (manages all attacks)
typedef struct {
    AttackConfig attacks[5];   // Support up to 5 attacks
    int attack_count;
    int current_cycle;
    
    // Statistics
    uint32_t total_malicious_frames;
    
} AttackInjector;

// ============= Core Functions =============

// Initialize attack injector
void AttackInjector_Init(AttackInjector* injector);

// Configure a new attack
void AttackInjector_AddAttack(AttackInjector* injector, AttackType type,
                              int start_cycle, int duration_cycles);

// Update attack state (call every cycle)
void AttackInjector_Update(AttackInjector* injector, int cycle);

// Execute active attacks (call during transmission phase)
void AttackInjector_Execute(AttackInjector* injector, CANBus* bus);

// Check if currently attacking
bool AttackInjector_IsAttacking(const AttackInjector* injector);

// Print attack summary
void AttackInjector_PrintStats(const AttackInjector* injector);

// ============= Individual Attack Implementations =============

// Fuzzing: Random CAN IDs and payloads
void Attack_ExecuteFuzzing(CANBus* bus, AttackConfig* config);

// DoS: Flood with high-priority messages
void Attack_ExecuteDoS(CANBus* bus, AttackConfig* config);

// Replay: Repeat captured legitimate traffic
void Attack_ExecuteReplay(CANBus* bus, AttackConfig* config);

// Injection: Send crafted fake messages
void Attack_ExecuteInjection(CANBus* bus, AttackConfig* config);

// Masquerade: Impersonate legitimate ECU
void Attack_ExecuteMasquerade(CANBus* bus, AttackConfig* config);

#endif // ATTACK_INJECTOR_H