import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { Overview } from './pages/Overview';
import { Prediction } from './pages/Prediction';
import { GapIntelligence } from './pages/GapIntelligence';
import { Discovery } from './pages/Discovery';
import { Copilot } from './pages/Copilot';
import { ExperimentLog } from './pages/ExperimentLog';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<Overview />} />
          <Route path="prediction" element={<Prediction />} />
          <Route path="gaps" element={<GapIntelligence />} />
          <Route path="discovery" element={<Discovery />} />
          <Route path="copilot" element={<Copilot />} />
          
          {/* Placeholders for remaining pages */}
          <Route path="experiments" element={<ExperimentLog />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
