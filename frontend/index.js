import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Point to your GitHub repository where results are stored
const RESULTS_URL = "https://raw.githubusercontent.com/<your-username>/<your-repo>/main/data/results/";

export default function TrafficSimulator() {
  const [simulationData, setSimulationData] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [latestFile, setLatestFile] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLatestFile = async () => {
      try {
        // In a real app, you'd fetch the directory listing from GitHub API
        // For simplicity, we'll use a fixed naming pattern
        const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
        const file = `simulation_${timestamp}_000000.json`;
        setLatestFile(file);
        
        const response = await fetch(`${RESULTS_URL}${file}`);
        const data = await response.json();
        setSimulationData(data);
        setLoading(false);
      } catch (error) {
        console.error("Error loading simulation data:", error);
      }
    };

    fetchLatestFile();
  }, []);

  useEffect(() => {
    let interval;
    if (isPlaying && simulationData.length > 0) {
      interval = setInterval(() => {
        setCurrentStep(prev => (prev + 1) % simulationData.length);
      }, 300);
    }
    return () => clearInterval(interval);
  }, [isPlaying, simulationData]);

  if (loading) {
    return <div className="container">Loading simulation data...</div>;
  }

  const currentState = simulationData[currentStep] || {};
  const { vehicles = [], metadata } = currentState;
  
  return (
    <div className="container">
      <div className="controls">
        <button onClick={() => setIsPlaying(!isPlaying)}>
          {isPlaying ? 'Pause' : 'Play'}
        </button>
        <input
          type="range"
          min="0"
          max={simulationData.length - 1}
          value={currentStep}
          onChange={(e) => setCurrentStep(parseInt(e.target.value))}
        />
        <p>Step: {currentStep} of {simulationData.length - 1}</p>
        <p>Last updated: {currentState.timestamp || 'N/A'}</p>
        <p>Congestion: {currentState.congestion ? (currentState.congestion * 100).toFixed(1) : '0'}%</p>
      </div>

      <MapContainer 
        center={[51.505, -0.09]} 
        zoom={13} 
        style={{ height: '80vh', width: '100%' }}
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        
        {vehicles.map(vehicle => (
          <CircleMarker
            key={`${vehicle.id}-${currentStep}`}
            center={[vehicle.x / 10 + 51.5, vehicle.y / 10 - 0.1]}
            radius={vehicle.speed}
            color={vehicle.speed > 2 ? 'green' : 'red'}
          />
        ))}
      </MapContainer>
    </div>
  );
}