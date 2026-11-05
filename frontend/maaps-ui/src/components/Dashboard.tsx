/**
 * Dashboard Component
 * System overview and status display
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Chip,
} from '@mui/material';
import { apiClient } from '../api/client';

interface SystemHealth {
  health_score: number;
  agents_healthy: number;
  agents_total: number;
  system_uptime_seconds: number;
}

interface SystemMetrics {
  cpu_usage_percent: number;
  memory_usage_percent: number;
  message_bus: {
    queue_depth: number;
    messages_per_second: number;
  };
}

export const Dashboard: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const healthRes = await apiClient.getSystemHealth();
        setHealth(healthRes.data.data);

        const metricsRes = await apiClient.getSystemMetrics();
        setMetrics(metricsRes.data.data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000); // Update every 2 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        MAAPS Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* System Health */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              {health && (
                <>
                  <Typography variant="h3" color="primary">
                    {health.health_score}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {health.agents_healthy} / {health.agents_total} agents healthy
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Uptime: {Math.floor(health.system_uptime_seconds / 60)} minutes
                  </Typography>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Metrics */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Metrics
              </Typography>
              {metrics && (
                <>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      CPU Usage: {metrics.cpu_usage_percent.toFixed(1)}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={metrics.cpu_usage_percent}
                      sx={{ mt: 1 }}
                    />
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      Memory: {metrics.memory_usage_percent.toFixed(1)}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={metrics.memory_usage_percent}
                      sx={{ mt: 1 }}
                    />
                  </Box>
                  <Typography variant="body2">
                    Message Bus: {metrics.message_bus.queue_depth} in queue
                  </Typography>
                  <Typography variant="body2">
                    {metrics.message_bus.messages_per_second} msgs/sec
                  </Typography>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Active Components */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Components
              </Typography>
              <Grid container spacing={2}>
                <Grid item>
                  <Chip label="Effects Chain" color="success" />
                </Grid>
                <Grid item>
                  <Chip label="Live Looping" color="success" />
                </Grid>
                <Grid item>
                  <Chip label="Sync Clock" color="success" />
                </Grid>
                <Grid item>
                  <Chip label="Automation" color="success" />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
