/**
 * Tray icon + menu rendering for the Privacy Bridge.
 *
 * Status colours (encoded into the icon SVG → PNG):
 *   green  — registered, healthy
 *   blue   — tunnel up, registering
 *   yellow — starting / waiting on Ollama
 *   red    — needs setup or bridge down
 *
 * The icon is rendered programmatically (not bundled PNG) so the app can
 * change colour without shipping multiple image files. nativeImage builds
 * a 16×16 PNG from a 1-bit SVG mask + tint colour.
 */
'use strict';

const { nativeImage, Menu } = require('electron');

// Tiny SVG dot icon → 16×16 PNG. The "indicator" pattern most macOS / Win
// tray apps use. Colour varies by status.
function renderIcon(color) {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
      <circle cx="8" cy="8" r="5" fill="${color}" stroke="rgba(0,0,0,0.4)" stroke-width="0.5"/>
    </svg>`;
  // nativeImage can read SVG via createFromBuffer + toBitmap on most platforms.
  // For maximum compatibility, encode the SVG as data URL.
  return nativeImage.createFromDataURL(
    'data:image/svg+xml;base64,' + Buffer.from(svg).toString('base64')
  );
}

const COLORS = {
  registered:    '#10B981',   // green — healthy
  'tunnel-up':   '#3B82F6',   // blue — connecting
  starting:      '#F59E0B',   // amber — booting
  'needs-setup': '#EF4444',   // red
  'bridge-down': '#EF4444',   // red
};


function iconFor(state) {
  return renderIcon(COLORS[state.status] || '#94A3B8');
}


function tooltipFor(state) {
  switch (state.status) {
    case 'registered':    return 'NexusAgent Privacy Bridge — connected ✓';
    case 'tunnel-up':     return 'NexusAgent Privacy Bridge — registering with server…';
    case 'starting':      return 'NexusAgent Privacy Bridge — starting up…';
    case 'needs-setup':   return 'NexusAgent Privacy Bridge — setup needed';
    case 'bridge-down':   return `NexusAgent Privacy Bridge — disconnected${state.lastError ? ' (' + state.lastError.slice(0,40) + ')' : ''}`;
    default:              return 'NexusAgent Privacy Bridge';
  }
}


function menuFor(state, actions) {
  const items = [];

  // Header — non-interactive status line
  items.push({
    label: tooltipFor(state),
    enabled: false,
  });
  items.push({ type: 'separator' });

  // What's where
  if (state.tunnelUrl) {
    items.push({
      label: `Tunnel: ${state.tunnelUrl.replace('https://', '').slice(0, 36)}…`,
      enabled: false,
    });
  }
  if (state.ollamaModels && state.ollamaModels.length) {
    items.push({
      label: `Models: ${state.ollamaModels.slice(0, 2).join(', ')}${state.ollamaModels.length > 2 ? '…' : ''}`,
      enabled: false,
    });
  }
  if (state.lastError && state.status === 'bridge-down') {
    items.push({
      label: `Last error: ${state.lastError.slice(0, 60)}…`,
      enabled: false,
    });
  }
  items.push({ type: 'separator' });

  // Actions
  items.push({ label: 'Open NexusAgent settings…', click: actions.openDashboard });
  items.push({ label: 'Restart bridge',            click: actions.restart });

  if (state.status === 'needs-setup') {
    items.push({ label: 'Setup…', click: actions.openSetup });
  } else {
    items.push({ label: 'Disconnect & remove token', click: actions.revoke });
  }

  items.push({ type: 'separator' });
  items.push({ label: 'Quit', click: actions.quit });

  return Menu.buildFromTemplate(items);
}


module.exports = { iconFor, tooltipFor, menuFor };
