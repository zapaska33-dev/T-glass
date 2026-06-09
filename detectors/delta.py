class DeltaTracker:
    def __init__(self):
        self.cumulative = 0
        self.history = []
    def update(self, signed_volume):
        self.cumulative += signed_volume
        self.history.append(self.cumulative)
        if len(self.history) > 300:
            self.history = self.history[-300:]
        return self.cumulative
    def get_delta(self):
        return self.cumulative
