#include "attack_injector.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define COLOR_RED     "\x1b[31m"
#define COLOR_YELLOW  "\x1b[33m"
#define COLOR_RESET   "\x1b[0m"
#define COLOR_BOLD    "\x1b[1m"


// Replay attack storage
static CANFrame replay_buffer[50];
static int replay_count = 0;
static int replay_index = 0;
static bool replay_learning = true;

void AttackInjector_Init(AttackInjector* injector) {
    memset(injector, 0, sizeof(AttackInjector));
}

void AttackInjector_AddAttack(AttackInjector* injector, AttackType type,
                              int start_cycle, int duration_cycles) {
    if (injector->attack_count >= 5) {
        printf("[ATTACK-INJECTOR] Error: Max attacks reached\n");
        return;
    }
    
    AttackConfig* attack = &injector->attacks[injector->attack_count];
    attack->type = type;
    attack->start_cycle = start_cycle;
    attack->duration_cycles = duration_cycles;
    attack->active = false;
    attack->frames_per_cycle = 1;  // Default
    attack->frames_injected = 0;
    attack->injection_attempts = 0;
    
    // Attack-specific configuration
    switch (type) {
        case ATTACK_FUZZING:
            attack->frames_per_cycle = 5;  // Flood with random frames
            break;
        case ATTACK_DOS_FLOOD:
            attack->target_id = 0x000;     // Highest priority
            attack->frames_per_cycle = 10; // Saturate bus
            break;
        case ATTACK_INJECTION:
            attack->target_id = CAN_ID_BRAKE_STATUS;  // Fake brake signal
            attack->frames_per_cycle = 3;
            break;
        case ATTACK_MASQUERADE:
            attack->target_id = CAN_ID_ENGINE_RPM;    // Fake engine data
            attack->frames_per_cycle = 2;
            break;
        default:
            break;
    }
    
    injector->attack_count++;
    printf("[ATTACK-INJECTOR] Attack configured: Type=%d, Start=Cycle %d, Duration=%d cycles\n",
           type, start_cycle, duration_cycles);
}

void AttackInjector_Update(AttackInjector* injector, int cycle) {
    injector->current_cycle = cycle;
    
    // Activate/deactivate attacks based on cycle
    for (int i = 0; i < injector->attack_count; i++) {
        AttackConfig* attack = &injector->attacks[i];
        
        int end_cycle = attack->start_cycle + attack->duration_cycles;
        
        if (cycle >= attack->start_cycle && cycle < end_cycle) {
            if (!attack->active) {
                attack->active = true;
printf("\n" COLOR_BOLD COLOR_RED "[ATTACK STARTED]" COLOR_RESET " Type=%d at Cycle %d\n", 
       attack->type, cycle);            }
        } else if (attack->active && cycle >= end_cycle) {
            attack->active = false;
printf("\n" COLOR_BOLD COLOR_YELLOW "[ATTACK ENDED]" COLOR_RESET " Type=%d at Cycle %d\n", 
       attack->type, cycle);
        }
    }
}

void AttackInjector_Execute(AttackInjector* injector, CANBus* bus) {
    for (int i = 0; i < injector->attack_count; i++) {
        AttackConfig* attack = &injector->attacks[i];
        
        if (!attack->active) continue;
        
        // Execute the specific attack
        switch (attack->type) {
            case ATTACK_FUZZING:
                Attack_ExecuteFuzzing(bus, attack);
                break;
            case ATTACK_DOS_FLOOD:
                Attack_ExecuteDoS(bus, attack);
                break;
            case ATTACK_REPLAY:
                Attack_ExecuteReplay(bus, attack);
                break;
            case ATTACK_INJECTION:
                Attack_ExecuteInjection(bus, attack);
                break;
            case ATTACK_MASQUERADE:
                Attack_ExecuteMasquerade(bus, attack);
                break;
            default:
                break;
        }
        
        injector->total_malicious_frames += attack->frames_injected;
    }
}

bool AttackInjector_IsAttacking(const AttackInjector* injector) {
    for (int i = 0; i < injector->attack_count; i++) {
        if (injector->attacks[i].active) return true;
    }
    return false;
}

void AttackInjector_PrintStats(const AttackInjector* injector) {
    printf("\n========================================\n");
    printf("      ATTACK INJECTOR STATISTICS       \n");
    printf("========================================\n");
    printf("Total Attacks Configured: %d\n", injector->attack_count);
    printf("Total Malicious Frames:   %u\n", injector->total_malicious_frames);
    printf("\nIndividual Attack Stats:\n");
    
    for (int i = 0; i < injector->attack_count; i++) {
        const AttackConfig* attack = &injector->attacks[i];
        printf("  Attack %d [Type=%d]:\n", i+1, attack->type);
        printf("    Frames Injected: %u\n", attack->frames_injected);
        printf("    Attempts:        %u\n", attack->injection_attempts);
    }
    printf("========================================\n");
}

// ============= Attack Implementations =============

void Attack_ExecuteFuzzing(CANBus* bus, AttackConfig* config) {
    printf("  [ATTACK-FUZZING] Injecting %d random frames...\n", config->frames_per_cycle);
    
    for (int i = 0; i < config->frames_per_cycle; i++) {
        CANFrame malicious_frame;
        CAN_InitFrame(&malicious_frame);
        
        // Random CAN ID
        uint16_t random_id = rand() % 0x7FF;
        
        // Random data length
        uint8_t random_dlc = (rand() % 8) + 1;
        
        // Random payload
        uint8_t random_data[CAN_MAX_DATA_LEN];
        for (int j = 0; j < random_dlc; j++) {
            random_data[j] = rand() % 256;
        }
        
        CAN_SetData(&malicious_frame, random_id, random_data, random_dlc);
        
printf("    " COLOR_YELLOW "[!]" COLOR_RESET " Fuzzing frame: ID=0x%03X DLC=%d\n", 
       random_id, random_dlc);        
        config->injection_attempts++;
        if (CANBus_Transmit(bus, &malicious_frame)) {
            config->frames_injected++;
        }
    }
}

void Attack_ExecuteDoS(CANBus* bus, AttackConfig* config) {
    printf("  [ATTACK-DOS] Flooding bus with %d high-priority frames...\n", 
           config->frames_per_cycle);
    
    for (int i = 0; i < config->frames_per_cycle; i++) {
        CANFrame dos_frame;
        CAN_InitFrame(&dos_frame);
        
        // Use highest priority ID (0x000)
        uint8_t dummy_data[8] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
        CAN_SetData(&dos_frame, config->target_id, dummy_data, 8);
        
        config->injection_attempts++;
        if (CANBus_Transmit(bus, &dos_frame)) {
            config->frames_injected++;
        }
    }
    
printf("    " COLOR_YELLOW "[!]" COLOR_RESET " DoS: %u frames sent (ID=0x%03X)\n", 
       config->frames_per_cycle, config->target_id);
}

void Attack_ExecuteReplay(CANBus* bus, AttackConfig* config) {
    // Learning phase: capture legitimate traffic
    if (replay_learning && replay_count < 50) {
        // This would normally capture from bus, but for simulation we'll
        // replay engine/brake frames
        printf("  [ATTACK-REPLAY] Learning phase...\n");
        return;
    }
    
    replay_learning = false;
    
    if (replay_count == 0) {
        printf("  [ATTACK-REPLAY] No frames captured to replay\n");
        return;
    }
    
    printf("  [ATTACK-REPLAY] Replaying captured frame %d/%d\n", 
           replay_index + 1, replay_count);
    
    // Replay a captured frame
    CANFrame replay_frame = replay_buffer[replay_index];
    replay_index = (replay_index + 1) % replay_count;
    
    config->injection_attempts++;
    if (CANBus_Transmit(bus, &replay_frame)) {
        config->frames_injected++;
        printf("    [!] Replayed: ID=0x%03X\n", replay_frame.id);
    }
}

void Attack_ExecuteInjection(CANBus* bus, AttackConfig* config) {
    printf("  [ATTACK-INJECTION] Injecting fake messages...\n");
    
    for (int i = 0; i < config->frames_per_cycle; i++) {
        CANFrame fake_frame;
        CAN_InitFrame(&fake_frame);
        
        // Inject fake brake signal
        if (config->target_id == CAN_ID_BRAKE_STATUS) {
            uint8_t fake_brake = 0x01;  // Force brakes ON
            CAN_SetData(&fake_frame, CAN_ID_BRAKE_STATUS, &fake_brake, 1);
printf("    " COLOR_YELLOW "[!]" COLOR_RESET " Injecting FAKE BRAKE PRESSED signal\n");
        }
        // Or fake high RPM
        else if (config->target_id == CAN_ID_ENGINE_RPM) {
            uint16_t fake_rpm = 9000;  // Dangerously high RPM
            uint8_t rpm_data[4] = {(fake_rpm >> 8) & 0xFF, fake_rpm & 0xFF, 0x00, 0x00};
            CAN_SetData(&fake_frame, CAN_ID_ENGINE_RPM, rpm_data, 4);
            printf("    [!] Injecting FAKE HIGH RPM: %u\n", fake_rpm);
        }
        
        config->injection_attempts++;
        if (CANBus_Transmit(bus, &fake_frame)) {
            config->frames_injected++;
        }
    }
}

void Attack_ExecuteMasquerade(CANBus* bus, AttackConfig* config) {
    printf("  [ATTACK-MASQUERADE] Impersonating ECU...\n");
    
    for (int i = 0; i < config->frames_per_cycle; i++) {
        CANFrame fake_ecu_frame;
        CAN_InitFrame(&fake_ecu_frame);
        
        // Impersonate Engine ECU with fake data
        if (config->target_id == CAN_ID_ENGINE_RPM) {
            uint16_t fake_rpm = 500 + (rand() % 1000);  // Suspiciously low RPM
            uint8_t rpm_data[4] = {(fake_rpm >> 8) & 0xFF, fake_rpm & 0xFF, 0xAA, 0xAA};
            CAN_SetData(&fake_ecu_frame, CAN_ID_ENGINE_RPM, rpm_data, 4);
            printf("    [!] Masquerading as Engine-ECU: RPM=%u\n", fake_rpm);
        }
        
        config->injection_attempts++;
        if (CANBus_Transmit(bus, &fake_ecu_frame)) {
            config->frames_injected++;
        }
    }
}