import { useContext } from 'react';
import { SimulatorContext } from './SimulatorContext';

export function useSimulator() {
  const context = useContext(SimulatorContext);
  if (context === undefined) {
    throw new Error('useSimulator must be used within a SimulatorProvider');
  }
  return context;
}
