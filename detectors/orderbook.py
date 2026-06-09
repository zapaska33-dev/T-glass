class OrderbookProcessor:
    def __init__(self, stats):
        self.stats = stats
        self.best_bid = self.best_ask = self.bid_size = self.ask_size = 0.0
        self.curr_bids = self.curr_asks = self.prev_bids = self.prev_asks = {}
    def update(self, bids, asks, ts):
        self.prev_bids, self.prev_asks = self.curr_bids.copy(), self.curr_asks.copy()
        self.curr_bids, self.curr_asks = {}, {}
        for level in bids[:20]:
            try:
                if isinstance(level, (list, tuple)) and len(level) >= 2:
                    p, v = float(level[0]), float(level[1])
                    if p > 0 and v > 0:
                        self.curr_bids[p] = v
            except: pass
        for level in asks[:20]:
            try:
                if isinstance(level, (list, tuple)) and len(level) >= 2:
                    p, v = float(level[0]), float(level[1])
                    if p > 0 and v > 0:
                        self.curr_asks[p] = v
            except: pass
        self.best_bid = max(self.curr_bids.keys()) if self.curr_bids else 0
        self.best_ask = min(self.curr_asks.keys()) if self.curr_asks else 0
        self.bid_size = self.curr_bids.get(self.best_bid, 0) if self.best_bid else 0
        self.ask_size = self.curr_asks.get(self.best_ask, 0) if self.best_ask else 0
        self.stats.book_updates += 1
