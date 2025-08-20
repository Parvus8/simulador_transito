import time
import json
import numpy as np
import networkx as ntx
from pathlib import Path
from datetime import datetime as dt
from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import NetworkGrid

RESULTS_DIR = Path(__file__).parent.parent / "data" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

class Carro(Agent):
    def __init__(self, unique_id: int, model: Model):
        super().__init__(unique_id, model)
        self.posicao = (0, 0)
        self.speed = 0
        
    def move(self):
        """Move veiculo to a random adjacent cell"""
        passos_possiveis = self.model.grid.get_neighborhood(
            self.posicao,
            moore=True,
            include_center=False
        )
        nova_posicao = self.random.choice(passos_possiveis)
        
        if self.model.grid.is_cell_empty(nova_posicao):
            self.model.grid.move_agent(self, nova_posicao)
            self.posicao = nova_posicao
            self.speed = np.random.randint(1, 5)

class ModeloTransito(Model):
    def __init__(self, width: int = 20, height: int = 20, n_veiculos: int = 50):
        self.grid = NetworkGrid(ntx.grid_2d_graph(width, height))
        self.schedule = RandomActivation(self)
        self.width = width
        self.height = height
        self.step_count = 0
        
        for i in range(n_veiculos):
            veiculo = veiculo(i, self)
            start = (np.random.randint(0, width), np.random.randint(0, height))
            self.grid.place_agent(veiculo, start)
            self.schedule.add(veiculo)

    def step(self):
        """Advance the model by one step"""
        self.schedule.step()
        self.step_count += 1
        return self.get_state()
    
    def get_state(self) -> dict:
        """Get current simulation state"""
        return {
            "timestamp": dt.utcnow().isoformat(),
            "step": self.step_count,
            "veiculos": [
                {"id": agent.unique_id, "x": agent.pos[0], "y": agent.pos[1], "speed": agent.speed}
                for agent in self.schedule.agents
            ],
            "congestionamento": self.calcular_congestionamento(),
            "metadata": {
                "width": self.width,
                "height": self.height,
                "veiculo_count": len(self.schedule.agents)
            }
        }
    
    def calcular_congestionamento(self) -> float:
        """calcular atual congestionamento (0-1)"""
        occupied = sum(1 for _ in self.grid.coord_iter() if not self.grid.is_cell_empty)
        total_cells = self.width * self.height
        return occupied / total_cells

def run_simulation(steps: int = 100):
    model = ModeloTransito()
    results = []
    
    for _ in range(steps):
        state = model.step()
        results.append(state)

        if len(results) % 10 == 0:
            save_results(results)
    
    save_results(results)
    return results

def save_results(results: list):
    timestamp = dt.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = RESULTS_DIR / f"simulation_{timestamp}.json"
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Saved results to {output_file}")

if __name__ == "__main__":
    print("Starting traffic simulation...")
    start_time = time.time()
    
    results = run_simulation(steps=100)
    
    duration = time.time() - start_time
    print(f"Simulation completed in {duration:.2f} seconds")
    print(f"Generated {len(results)} simulation steps")