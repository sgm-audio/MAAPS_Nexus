/**
 * MAAPS Main Application
 * React TypeScript UI for MAAPS API
 */

import React, { useEffect, useState } from 'react';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  ThemeProvider,
  createTheme,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Audiotrack as AudioIcon,
  Loop as LoopIcon,
  AccessTime as ClockIcon,
  AutoMode as AutoIcon,
} from '@mui/icons-material';
import { Dashboard } from './components/Dashboard';
import { EffectsChain } from './components/EffectsChain';
import { wsClient } from './api/websocket';

const drawerWidth = 240;

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
  },
});

type View = 'dashboard' | 'effects' | 'looping' | 'sync' | 'automation';

function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard');

  useEffect(() => {
    // Connect to WebSocket
    wsClient.connect();

    return () => {
      wsClient.disconnect();
    };
  }, []);

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'effects':
        return <EffectsChain />;
      case 'looping':
        return (
          <Box sx={{ p: 3 }}>
            <Typography variant="h4">Live Looping (Coming Soon)</Typography>
          </Box>
        );
      case 'sync':
        return (
          <Box sx={{ p: 3 }}>
            <Typography variant="h4">Sync & Clock (Coming Soon)</Typography>
          </Box>
        );
      case 'automation':
        return (
          <Box sx={{ p: 3 }}>
            <Typography variant="h4">Performance Automation (Coming Soon)</Typography>
          </Box>
        );
      default:
        return <Dashboard />;
    }
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <Box sx={{ display: 'flex' }}>
        <CssBaseline />

        {/* App Bar */}
        <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
          <Toolbar>
            <Typography variant="h6" noWrap component="div">
              MAAPS Control Center
            </Typography>
          </Toolbar>
        </AppBar>

        {/* Sidebar */}
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
          }}
        >
          <Toolbar />
          <Box sx={{ overflow: 'auto' }}>
            <List>
              <ListItem disablePadding>
                <ListItemButton onClick={() => setCurrentView('dashboard')}>
                  <ListItemIcon>
                    <DashboardIcon />
                  </ListItemIcon>
                  <ListItemText primary="Dashboard" />
                </ListItemButton>
              </ListItem>

              <ListItem disablePadding>
                <ListItemButton onClick={() => setCurrentView('effects')}>
                  <ListItemIcon>
                    <AudioIcon />
                  </ListItemIcon>
                  <ListItemText primary="Effects Chain" />
                </ListItemButton>
              </ListItem>

              <ListItem disablePadding>
                <ListItemButton onClick={() => setCurrentView('looping')}>
                  <ListItemIcon>
                    <LoopIcon />
                  </ListItemIcon>
                  <ListItemText primary="Live Looping" />
                </ListItemButton>
              </ListItem>

              <ListItem disablePadding>
                <ListItemButton onClick={() => setCurrentView('sync')}>
                  <ListItemIcon>
                    <ClockIcon />
                  </ListItemIcon>
                  <ListItemText primary="Sync & Clock" />
                </ListItemButton>
              </ListItem>

              <ListItem disablePadding>
                <ListItemButton onClick={() => setCurrentView('automation')}>
                  <ListItemIcon>
                    <AutoIcon />
                  </ListItemIcon>
                  <ListItemText primary="Automation" />
                </ListItemButton>
              </ListItem>
            </List>
          </Box>
        </Drawer>

        {/* Main Content */}
        <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
          <Toolbar />
          {renderView()}
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;
