CC=gcc
CFLAGS=-Iinclude -Wall
SRC=src/can_frame.c src/can_bus.c src/ecu_node.c src/dtc_manager.c src/json_logger.c src/attack_injector.c src/ids_detector.c src/ml_exporter.c src/ml_detector.c src/main.c
OBJ=$(SRC:.c=.o)
EXEC=can_simulator.exe

all: $(EXEC)

$(EXEC): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $(OBJ)

clean:
	rm -f $(OBJ) $(EXEC) can_data.json can_security_data.json training_data.csv

# Run simulator and auto-copy data to dashboard
.PHONY: run
run: $(EXEC)
	@echo "Running simulator..."
	./$(EXEC)
	@echo "Copying data to dashboard..."
	@cp -f can_security_data.json dashboard/data/ 2>/dev/null || echo "Dashboard directory not found"
	@echo "Done! Refresh browser at http://localhost:8000"