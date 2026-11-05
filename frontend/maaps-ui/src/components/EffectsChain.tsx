/**
 * Effects Chain Component
 * Manage and control effect chains
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Slider,
  Switch,
  FormControlLabel,
  Stack,
} from '@mui/material';
import { apiClient } from '../api/client';
import { wsClient } from '../api/websocket';

interface Effect {
  effect_id: string;
  type: string;
  bypass: boolean;
  parameters: Record<string, number>;
}

interface Chain {
  chain_id: string;
  chain_name: string;
  effects: Effect[];
}

export const EffectsChain: React.FC = () => {
  const [chains, setChains] = useState<Chain[]>([]);
  const [selectedChain, setSelectedChain] = useState<Chain | null>(null);

  useEffect(() => {
    fetchChains();

    // Subscribe to parameter changes
    wsClient.on('effects.parameter.change', (data: any) => {
      console.log('Parameter changed:', data);
      // Update UI in real-time
    });

    return () => {
      wsClient.off('effects.parameter.change', () => {});
    };
  }, []);

  const fetchChains = async () => {
    try {
      const response = await apiClient.getEffectChains();
      setChains(response.data.data.chains || []);
    } catch (error) {
      console.error('Error fetching chains:', error);
    }
  };

  const createChain = async () => {
    try {
      await apiClient.createEffectChain({
        chain_name: 'New Chain',
        effects: [
          {
            type: 'compressor',
            parameters: {
              threshold: -18.0,
              ratio: 4.0,
              attack: 5.0,
              release: 50.0,
            },
            bypass: false,
            wet_dry: 1.0,
          },
        ],
      });
      fetchChains();
    } catch (error) {
      console.error('Error creating chain:', error);
    }
  };

  const updateParameter = async (
    chainId: string,
    effectId: string,
    paramName: string,
    value: number
  ) => {
    try {
      await apiClient.updateEffectParameters(chainId, effectId, {
        [paramName]: value,
      });
    } catch (error) {
      console.error('Error updating parameter:', error);
    }
  };

  const toggleBypass = async (chainId: string, effectId: string, bypass: boolean) => {
    try {
      await apiClient.toggleEffectBypass(chainId, effectId, bypass);
    } catch (error) {
      console.error('Error toggling bypass:', error);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Effects Chain
      </Typography>

      <Button variant="contained" onClick={createChain} sx={{ mb: 2 }}>
        Create New Chain
      </Button>

      <Stack spacing={2}>
        {chains.map((chain) => (
          <Card key={chain.chain_id}>
            <CardContent>
              <Typography variant="h6">{chain.chain_name}</Typography>

              {chain.effects.map((effect) => (
                <Box key={effect.effect_id} sx={{ mt: 2, p: 2, bgcolor: 'grey.100' }}>
                  <Typography variant="subtitle1">{effect.type}</Typography>

                  <FormControlLabel
                    control={
                      <Switch
                        checked={!effect.bypass}
                        onChange={(e) =>
                          toggleBypass(chain.chain_id, effect.effect_id, !e.target.checked)
                        }
                      />
                    }
                    label="Active"
                  />

                  {Object.entries(effect.parameters).map(([name, value]) => (
                    <Box key={name} sx={{ mt: 1 }}>
                      <Typography variant="body2">
                        {name}: {value}
                      </Typography>
                      <Slider
                        value={value}
                        min={-60}
                        max={20}
                        step={0.1}
                        onChange={(_, newValue) =>
                          updateParameter(
                            chain.chain_id,
                            effect.effect_id,
                            name,
                            newValue as number
                          )
                        }
                      />
                    </Box>
                  ))}
                </Box>
              ))}
            </CardContent>
          </Card>
        ))}
      </Stack>
    </Box>
  );
};
