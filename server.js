// server.js
// Node.js + Express + ccxt backend to fetch live prices from multiple exchanges
// Run: node server.js

const express = require('express');
const ccxt = require('ccxt');
const fetch = require('node-fetch'); // for coinGecko
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Exchanges we will use (no API keys required for public data)
const exchNames = ['binance','okx','bybit','bitget','bingx'];
const exchInstances = {};
for (const id of exchNames) {
  if (ccxt[id]) {
    exchInstances[id] = new ccxt[id]();
  } else {
    console.warn('ccxt missing exchange:', id);
  }
}

// Cache object to store latest prices
let CACHE = {
  timestamp: 0,
  symbols: [],      // array of symbols like BTC, ETH...
  coinGecko: [],    // coin list with prices
  data: {}          // { SYMBOL: { exchangeName: price, ... }, ... }
};

// Helper: get top 30 coins from CoinGecko
async function fetchTop30Symbols() {
  try {
    const url = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=30&page=1&sparkline=false';
    const res = await fetch(url);
    const arr = await res.json();
    // return array of symbols e.g. ['BTC','ETH', ...]
    return arr.map(c => c.symbol.toUpperCase());
  } catch (e) {
    console.error('CoinGecko fetch error', e);
    return [];
  }
}

// Build pair name for each exchange (try common formats)
function formatSymbolForExchange(symbol) {
  // We'll try common USDT pairs
  const pair1 = symbol + '/USDT';
  const pair2 = symbol + '/USD';
  return [pair1, pair2];
}

// Fetch tickers for all exchanges and top symbols, with simple caching
async function updatePrices() {
  const now = Date.now();
  // update every 1500 ms (configurable)
  if (now - CACHE.timestamp < 1500 && Object.keys(CACHE.data).length) return CACHE;
  try {
    const symbols = await fetchTop30Symbols();
    CACHE.symbols = symbols;
    CACHE.timestamp = now;
    const result = {};
    // initialize structure
    for (const s of symbols) result[s] = {};
    // For each exchange try to fetch tickers in batch (if supported), else per symbol
    for (const [exName, ex] of Object.entries(exchInstances)) {
      try {
        // prefer fetchTickers (batch) to reduce requests
        if (ex.has['fetchTickers']) {
          // Some exchanges have large responses; we will attempt fetchTickers then map
          let tickers = {};
          try {
            tickers = await ex.fetchTickers(); // may be large
          } catch (e) {
            // fallback to per-symbol
            tickers = null;
          }
          if (tickers) {
            for (const sym of symbols) {
              // possible symbol keys: 'BTC/USDT' or 'BTCUSDT' depending on ccxt parsing
              const candidates = formatSymbolForExchange(sym);
              let price = null;
              for (const c of candidates) {
                if (tickers[c] && tickers[c].last) { price = tickers[c].last; break; }
                // also try without slash
                const keyNoSlash = c.replace('/','');
                if (tickers[keyNoSlash] && tickers[keyNoSlash].last) { price = tickers[keyNoSlash].last; break; }
              }
              result[sym][exName] = (price === null) ? null : Number(price);
            }
            continue;
          }
        }
        // fallback: per-symbol fetchTicker
        for (const sym of symbols) {
          const candidates = formatSymbolForExchange(sym);
          let price = null;
          for (const c of candidates) {
            try {
              const ticker = await ex.fetchTicker(c);
              if (ticker && ticker.last) { price = ticker.last; break; }
            } catch (err) {
              // ignore and try next format
            }
          }
          result[sym][exName] = (price === null) ? null : Number(price);
        }
      } catch (err) {
        console.error('Exchange fetch error', exName, err.message || err);
        // fill nulls
        for (const s of symbols) result[s][exName] = null;
      }
    }

    CACHE.data = result;
    return CACHE;
  } catch (e) {
    console.error('updatePrices error', e);
    return CACHE;
  }
}

// API endpoint: /api/prices -> returns { timestamp, symbols:[], data:{SYMBOL:{Binance:price, ...}} }
app.get('/api/prices', async (req, res) => {
  const cache = await updatePrices();
  res.json({
    timestamp: cache.timestamp,
    symbols: cache.symbols,
    data: cache.data
  });
});

// Serve static frontend (optional) if you place arb_bot.html in /public
app.use(express.static('public'));

app.listen(PORT, () => {
  console.log(`Price server running on port ${PORT}`);
});
