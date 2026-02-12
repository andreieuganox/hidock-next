---
sidebar_position: 2
---

# Getting Started with GATI

This tutorial will walk you through the basics of GATI integration.

## Overview

GATI (Game Aggregation Technology Interface) provides a standardized way to integrate games with operators.

## Step 1: Understanding GATI Architecture

GATI consists of several key components:

- **Game Server**: Your game implementation
- **GATI Interface**: The communication layer
- **Operator Platform**: The target integration platform

## Step 2: Setting Up Your Environment

Before you begin, ensure you have:

1. Development environment configured
2. GATI SDK or libraries installed
3. Access to GATI documentation
4. Test credentials

## Step 3: Basic Integration

Here's a simple example of a GATI integration:

```javascript
// Example GATI game server setup
const gatiServer = new GATIServer({
  gameId: 'your-game-id',
  apiKey: 'your-api-key',
  environment: 'development'
});

// Handle game initialization
gatiServer.on('init', (session) => {
  console.log('Game session initialized:', session.id);
});
```

## Next Steps

- Explore the GATI API documentation
- Implement game-specific logic
- Test your integration
- Deploy to production

Continue to the next tutorial to learn about advanced GATI features!
