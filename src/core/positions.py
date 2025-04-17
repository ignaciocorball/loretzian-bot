from datetime import datetime
from typing import Dict, List, Tuple
from src.utils.visualization import print_positions

class ActivePositions:
    def __init__(self):
        self.positions = []
        
    def add_position(self, position_data: Dict):
        """Add a new position to track"""
        self.positions.append(position_data)
        
    def update_positions(self, current_price: float) -> List[Dict]:
        """Update all positions and return closed ones"""
        updated_positions = []
        closed_positions = []
        
        for position in self.positions:
            pnl = self.calculate_position_pnl(position, current_price)
            position['current_pnl'] = pnl
            
            if self.check_position_exit(position, current_price):
                position['exit_price'] = current_price
                position['exit_time'] = datetime.now()
                closed_positions.append(position)
            else:
                updated_positions.append(position)
                
        self.positions = updated_positions
        return closed_positions
        
    def calculate_position_pnl(self, position: Dict, current_price: float) -> float:
        """Calculate current P&L for a position"""
        if position['signal'] > 0:  # Long position
            return position['position_size'] * (current_price - position['entry_price']) / position['entry_price']
        else:  # Short position
            return position['position_size'] * (position['entry_price'] - current_price) / position['entry_price']
            
    def check_position_exit(self, position: Dict, current_price: float) -> bool:
        """Check if position should be closed"""
        # Update hit price for P&L calculation
        position['hit_price'] = current_price
        
        if position['signal'] > 0:  # Long position
            return current_price >= position['take_profit'] or current_price <= position['stop_loss']
        else:  # Short position
            return current_price <= position['take_profit'] or current_price >= position['stop_loss']
            
    def get_positions_summary(self) -> Tuple[int, float]:
        """Get summary of active positions"""
        total_positions = len(self.positions)
        total_pnl = sum(pos.get('current_pnl', 0) for pos in self.positions)
        return total_positions, total_pnl

    def display_positions(self):
        """Display current active positions"""
        print_positions(self.positions)

    def has_positions(self) -> bool:
        """Check if there are any active positions"""
        return len(self.positions) > 0 