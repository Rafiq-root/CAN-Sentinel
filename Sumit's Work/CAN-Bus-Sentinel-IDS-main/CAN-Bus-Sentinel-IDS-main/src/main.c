#include "json_logger.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <signal.h>
#include "can_bus.h"
#include "ecu_node.h"
#include "dtc_manager.h"
#include "attack_injector.h"
#include "ids_detector.h"
#include "ml_exporter.h" 

// Global components
DTCManager dtc_mgr;
AttackInjector attack_injector;
IDSController ids;
volatile sig_atomic_t keep_running = 1;
MLExporter ml_exporter;


void signal_handler(int sig) {
    (void)sig;
    keep_running = 0;
}

// Simulate arbitration when multiple ECUs try to send
void simulate_arbitration(ECUNode* ecu1, ECUNode* ecu2, CANBus* bus, 
                          CANFrame* frame1, CANFrame* frame2) {
    printf("\n>> ARBITRATION EVENT:\n");
    printf("   [%s] wants to send ID: 0x%03X\n", ecu1->name, frame1->id);
    printf("   [%s] wants to send ID: 0x%03X\n", ecu2->name, frame2->id);
    
    if (CANBus_Arbitrate(frame1, frame2)) {
        printf("   --> [%s] WINS (lower ID = higher priority)\n", ecu1->name);
        ECU_SendFrame(ecu1, bus, frame1);
        JSON_LogFrame(frame1, ecu1->name);
        bus->stats.collisions++;
        printf("   --> [%s] backs off, will retry\n", ecu2->name);
    } else {
        printf("   --> [%s] WINS (lower ID = higher priority)\n", ecu2->name);
        ECU_SendFrame(ecu2, bus, frame2);
        JSON_LogFrame(frame2, ecu2->name);
        bus->stats.collisions++;
        printf("   --> [%s] backs off, will retry\n", ecu1->name);
    }
}

// Process received messages
void process_messages(ECUNode* ecu, CANBus* bus) {
    CANFrame frame;
    
    while (CANBus_Receive(bus, &frame)) {
        ecu->frames_received++;
        
        switch (ecu->type) {
            case ECU_INFOTAINMENT:
                printf("  [%s] Monitoring: ID=0x%03X ", ecu->name, frame.id);
                
                if (frame.id == CAN_ID_ENGINE_RPM) {
                    uint16_t rpm = (frame.data[0] << 8) | frame.data[1];
                    printf("Engine RPM: %u", rpm);
                    if (rpm > 5500) {
                        printf(" [HIGH!]");
                    }
                    printf("\n");
                } else if (frame.id == CAN_ID_BRAKE_STATUS) {
                    printf("Brakes: %s\n", frame.data[0] ? "PRESSED" : "Released");
                } else if (frame.id == CAN_ID_DOOR_STATUS) {
                    uint8_t doors = frame.data[0];
                    printf("Doors: ");
                    if (doors & 0x01) printf("Driver ");
                    if (doors & 0x02) printf("Passenger ");
                    if (doors & 0x04) printf("RearLeft ");
                    if (doors & 0x08) printf("RearRight ");
                    if (doors == 0) printf("All Closed");
                    printf("\n");
                } else {
                    printf("Data: ");
                    for (int i = 0; i < frame.dlc; i++) {
                        printf("%02X ", frame.data[i]);
                    }
                    printf("\n");
                }
                break;
                
            case ECU_ENGINE_CONTROL:
                if (frame.id == CAN_ID_BRAKE_STATUS && frame.data[0] == 0x01) {
                    printf("  [%s] Brake detected - reducing engine power\n", ecu->name);
                }
                break;
                
            case ECU_BRAKE_SYSTEM:
                if (frame.id == CAN_ID_ENGINE_RPM) {
                    uint16_t rpm = (frame.data[0] << 8) | frame.data[1];
                    if (rpm > 5000) {
                        printf("  [%s] WARNING: High RPM detected (%u)\n", ecu->name, rpm);
                        DTC_Add(&dtc_mgr, DTC_ENGINE_OVERHEAT, "Engine RPM exceeds safe limit");
                    }
                }
                break;
                
            default:
                break;
        }
    }
}

// Create engine frame
CANFrame create_engine_frame(void) {
    CANFrame frame;
    CAN_InitFrame(&frame);
    uint16_t rpm = 1000 + (rand() % 5000);
    uint8_t data[4] = {(rpm >> 8) & 0xFF, rpm & 0xFF, 0x00, 0x00};
    CAN_SetData(&frame, CAN_ID_ENGINE_RPM, data, 4);
    return frame;
}

// Create brake frame
CANFrame create_brake_frame(void) {
    CANFrame frame;
    CAN_InitFrame(&frame);
    uint8_t brake_status = (rand() % 10 < 3) ? 0x01 : 0x00;
    CAN_SetData(&frame, CAN_ID_BRAKE_STATUS, &brake_status, 1);
    return frame;
}

// Create body frame
CANFrame create_body_frame(void) {
    CANFrame frame;
    CAN_InitFrame(&frame);
    uint8_t door_status = rand() % 16;
    CAN_SetData(&frame, CAN_ID_DOOR_STATUS, &door_status, 1);
    return frame;
}

int main(void) {
    srand((unsigned int)time(NULL));
    signal(SIGINT, signal_handler);
    
    DTC_Init(&dtc_mgr);
    JSON_Init("can_security_data.json");
    
    CANBus bus;
    CANBus_Init(&bus);
    
    ECUNode engine_ecu, brake_ecu, body_ecu, infotainment_ecu;
    ECU_Init(&engine_ecu, "Engine-ECU", ECU_ENGINE_CONTROL);
    ECU_Init(&brake_ecu, "Brake-ECU", ECU_BRAKE_SYSTEM);
    ECU_Init(&body_ecu, "Body-ECU", ECU_BODY_CONTROL);
    ECU_Init(&infotainment_ecu, "Infotainment-ECU", ECU_INFOTAINMENT);
    
    // Initialize security components
    AttackInjector_Init(&attack_injector);
    IDS_Init(&ids);
    MLExporter_Init(&ml_exporter, "training_data.csv");

    
    printf("\n");
    printf("================================================\n");
    printf("     CAN BUS INTRUSION DETECTION SYSTEM v1.0  \n");
    printf("     Attack Simulation & ML-Based Detection    \n");
    printf("================================================\n");
    printf("\nActive ECUs:\n");
    printf("  * Engine Control Unit (ID: 0x100)\n");
    printf("  * Brake System (ID: 0x120)\n");
    printf("  * Body Control Module (ID: 0x300)\n");
    printf("  * Infotainment System (Monitor Only)\n");
    
    // ========== LEARNING PHASE ==========
    printf("\n[IDS] Starting Learning Mode (50 cycles)...\n");
    printf("     IDS will observe normal traffic patterns\n");
    IDS_StartLearning(&ids, 50);
    
    for (int cycle = 1; cycle <= 50; cycle++) {
        printf("\n=== Learning Cycle %d/50 ===\n", cycle);
        
        // Normal traffic only - no attacks during learning
        CANFrame engine_frame = create_engine_frame();
        ECU_SendFrame(&engine_ecu, &bus, &engine_frame);
        IDS_AnalyzeFrame(&ids, &engine_frame, cycle);

        MLExporter_ExportFrame(&ml_exporter, &engine_frame, cycle, false);

        
        CANFrame brake_frame = create_brake_frame();
        ECU_SendFrame(&brake_ecu, &bus, &brake_frame);
        IDS_AnalyzeFrame(&ids, &brake_frame, cycle);

        MLExporter_ExportFrame(&ml_exporter, &engine_frame, cycle, false);

        
        CANFrame body_frame = create_body_frame();
        ECU_SendFrame(&body_ecu, &bus, &body_frame);
        IDS_AnalyzeFrame(&ids, &body_frame, cycle);

        MLExporter_ExportFrame(&ml_exporter, &body_frame, cycle, false);
        
        // Process messages
        process_messages(&infotainment_ecu, &bus);
        process_messages(&engine_ecu, &bus);
        process_messages(&brake_ecu, &bus);
        process_messages(&body_ecu, &bus);
        
        IDS_UpdateCycle(&ids, cycle, 3);
        
        sleep(1);  // Faster during learning
    }
    
    IDS_StopLearning(&ids);
    printf("\n[IDS] Learning Complete - System Armed and Monitoring\n");
    
    // ========== CONFIGURE ATTACK SCENARIOS ==========
    printf("\n[ATTACK-PLANNER] Configuring Attack Scenarios...\n");
    
    // Scenario 1: Fuzzing Attack (cycles 3-5)
    printf("  • Fuzzing Attack: Cycle 3-5 (random CAN IDs)\n");
    AttackInjector_AddAttack(&attack_injector, ATTACK_FUZZING, 3, 3);
    
    // Scenario 2: DoS Flood (cycles 8-9)
    printf("  • DoS Flood: Cycle 8-9 (bus saturation)\n");
    AttackInjector_AddAttack(&attack_injector, ATTACK_DOS_FLOOD, 8, 2);
    
    // Scenario 3: Message Injection (cycles 12-13)
    printf("  • Injection Attack: Cycle 12-13 (fake brake signals)\n");
    AttackInjector_AddAttack(&attack_injector, ATTACK_INJECTION, 12, 2);
    
    printf("\nPress Ctrl+C to stop...\n");
    printf("Dashboard: Open dashboard.html in your browser\n\n");
    
    // ========== MAIN SIMULATION LOOP ==========
    int cycle = 0;
    while (keep_running && cycle < 15) {
        cycle++;
        printf("\n=== Cycle %d ===\n", cycle);
        
        // Update attack state
        AttackInjector_Update(&attack_injector, cycle);
        
        // ========== TRANSMISSION PHASE ==========
        printf(">> Transmission Phase:\n");
        
        // 20% chance of collision simulation (your existing behavior)
        if (rand() % 100 < 20) {
            CANFrame engine_frame = create_engine_frame();
            CANFrame brake_frame = create_brake_frame();
            simulate_arbitration(&engine_ecu, &brake_ecu, &bus, 
                                &engine_frame, &brake_frame);
            
            // Body ECU sends normally
            CANFrame body_frame = create_body_frame();
            ECU_SendFrame(&body_ecu, &bus, &body_frame);
            JSON_LogFrame(&body_frame, body_ecu.name);
        } else {
            // Normal transmission
            CANFrame engine_frame = create_engine_frame();
            ECU_SendFrame(&engine_ecu, &bus, &engine_frame);
            JSON_LogFrame(&engine_frame, engine_ecu.name);
            
            // Random DTC generation
            if (rand() % 100 < 10) {
                printf("  [%s] [!] Engine misfire detected!\n", engine_ecu.name);
                DTC_Add(&dtc_mgr, DTC_ENGINE_MISFIRE, "Random cylinder misfire detected");
            }
            
            CANFrame brake_frame = create_brake_frame();
            ECU_SendFrame(&brake_ecu, &bus, &brake_frame);
            JSON_LogFrame(&brake_frame, brake_ecu.name);
            
            if (rand() % 100 < 3) {
                printf("  [%s] [!] Low brake pressure detected!\n", brake_ecu.name);
                DTC_Add(&dtc_mgr, DTC_BRAKE_PRESSURE_LOW, "Brake pressure below threshold");
            }
            
            CANFrame body_frame = create_body_frame();
            ECU_SendFrame(&body_ecu, &bus, &body_frame);
            JSON_LogFrame(&body_frame, body_ecu.name);
        }
        
        // ========== ATTACK INJECTION ==========
        if (AttackInjector_IsAttacking(&attack_injector)) {
            AttackInjector_Execute(&attack_injector, &bus);
        }
        
        // ========== RECEPTION PHASE ==========
        printf("\n>> Reception Phase:\n");
        
        bool currently_attacking = AttackInjector_IsAttacking(&attack_injector);

        CANFrame frame;
        int frames_this_cycle = 0;
        
        while (CANBus_Receive(&bus, &frame)) {
            frames_this_cycle++;
            
            // ========== IDS DETECTION ==========
            bool attack_detected = IDS_AnalyzeFrame(&ids, &frame, cycle);

            MLExporter_ExportFrame(&ml_exporter, &frame, cycle, currently_attacking);

            
            if (attack_detected) {
                // Alert already printed by IDS
            }
            
            // Your existing message processing (kept simple to avoid spam)
            if (frame.id == CAN_ID_ENGINE_RPM) {
                uint16_t rpm = (frame.data[0] << 8) | frame.data[1];
                printf("  [Infotainment-ECU] Engine RPM: %u", rpm);
                if (rpm > 5500) printf(" [HIGH!]");
                printf("\n");
            } else if (frame.id == CAN_ID_BRAKE_STATUS) {
                printf("  [Infotainment-ECU] Brakes: %s\n", 
                       frame.data[0] ? "PRESSED" : "Released");
            } else if (frame.id == CAN_ID_DOOR_STATUS) {
                printf("  [Infotainment-ECU] Doors: 0x%02X\n", frame.data[0]);
            }
        }
        
        IDS_UpdateCycle(&ids, cycle, frames_this_cycle);
        
        sleep(2);
    }
    
    // ========== FINAL STATISTICS ==========
    ECUNode all_ecus[] = {engine_ecu, brake_ecu, body_ecu, infotainment_ecu};
    JSON_LogStats(&bus, all_ecus, 4);
    JSON_LogIDSStats(&ids);
    JSON_LogAlerts(&ids);
    JSON_LogAttackStats(&attack_injector);

    JSON_Close();
    
    printf("\n\n");
    printf("================================================\n");
    printf("          SIMULATION SUMMARY                   \n");
    printf("================================================\n\n");
    
    printf("=== ECU Statistics ===\n");
    ECU_PrintStats(&engine_ecu);
    ECU_PrintStats(&brake_ecu);
    ECU_PrintStats(&body_ecu);
    ECU_PrintStats(&infotainment_ecu);
    
    printf("\n");
    CANBus_PrintStats(&bus);
    
    printf("\n");
    AttackInjector_PrintStats(&attack_injector);
    
    printf("\n");
    IDS_PrintStats(&ids);
    
    printf("\n");
    IDS_PrintAlerts(&ids, 10);  // Show last 10 alerts
    
    printf("\n");
    DTC_PrintAll(&dtc_mgr);
    
    MLExporter_Close(&ml_exporter);


    printf("\n[OK] Simulation completed successfully\n");
    printf("[OK] Security data saved to can_security_data.json\n");
    printf("[OK] Open security_dashboard.html in your browser to view\n\n");
    
    return 0;
}