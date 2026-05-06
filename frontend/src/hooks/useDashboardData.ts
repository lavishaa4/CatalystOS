import { useState, useEffect } from 'react';
import axios from 'axios';

export interface DashboardData {
  pipeline: {
    id: number;
    stage: string;
    product: string;
    catalyst: string;
    condition: string;
    status: string;
  }[];
  activity_log: {
    time: string;
    message: string;
  }[];
  top_candidates: {
    name: string;
    score: number;
    ai_tag: boolean;
  }[];
}

export function useDashboardData() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_URL}/dashboard`);
        setData(response.data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch dashboard data", err);
        setError("Failed to connect to backend. Make sure FastAPI is running.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}
