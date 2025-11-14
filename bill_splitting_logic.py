from typing import List, Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP

class BillSplitter:
    def __init__(self):
        self.participants = []
        self.items = []
        self.tax_rate = 0.0
        self.tip_percentage = 0.0
        
    def add_participant(self, name: str, email: str = None):
        """Add a participant to the bill split"""
        participant = {
            'id': len(self.participants) + 1,
            'name': name,
            'email': email,
            'items': [],
            'subtotal': 0.0,
            'tax_share': 0.0,
            'tip_share': 0.0,
            'total': 0.0
        }
        self.participants.append(participant)
        return participant['id']
    
    def add_item(self, name: str, price: float, participants: List[int] = None, custom_shares: Dict[int, float] = None):
    
        # Handle null/empty price
        if price is None:
            price = 0.0
            
        item = {
            'id': len(self.items) + 1,
            'name': name,
            'price': float(price),
            'participants': participants or [],
            'custom_shares': custom_shares or {},
            'price_per_person': 0.0
        }
        
        # Calculate price per person if participants are specified
        if participants:
            if custom_shares:
                # Custom shares override equal splitting
                total_custom_share = sum(custom_shares.values())
                if abs(total_custom_share - 1.0) > 0.01:  # Allow small floating point errors
                    raise ValueError("Custom shares must sum to 1.0")
                item['price_per_person'] = item['price']
            else:
                # Equal splitting among participants
                item['price_per_person'] = item['price'] / len(participants)
        
        self.items.append(item)
        return item['id']
    
    def assign_item_to_participant(self, item_id: int, participant_id: int, share: float = 1.0):
        """Assign an item to a participant with optional custom share"""
        item = next((i for i in self.items if i['id'] == item_id), None)
        participant = next((p for p in self.participants if p['id'] == participant_id), None)
        
        if not item:
            raise ValueError(f"Item {item_id} not found")
        if not participant:
            raise ValueError(f"Participant {participant_id} not found")
        
        # Remove from current participants if already assigned
        if participant_id in item['participants']:
            item['participants'].remove(participant_id)
            if participant_id in item['custom_shares']:
                del item['custom_shares'][participant_id]
        
        # Add to participants
        item['participants'].append(participant_id)
        if share != 1.0:
            item['custom_shares'][participant_id] = share
    
    def set_tax_and_tip(self, tax_rate: float = 0.0, tip_percentage: float = 0.0):
        """Set tax rate and tip percentage"""
        # Handle null/empty values
        self.tax_rate = float(tax_rate) if tax_rate is not None else 0.0
        self.tip_percentage = float(tip_percentage) if tip_percentage is not None else 0.0
    
    def calculate_split(self) -> Dict[str, Any]:
        """Calculate the final bill split"""
        # Reset participant totals
        for participant in self.participants:
            participant['items'] = []
            participant['subtotal'] = 0.0
            participant['tax_share'] = 0.0
            participant['tip_share'] = 0.0
            participant['total'] = 0.0
        
        # Calculate item subtotals per participant
        total_subtotal = 0.0
        
        for item in self.items:
            item_price = item['price']
            total_subtotal += item_price
            
            if not item['participants']:
                # Item not assigned to anyone, skip
                continue
            
            if item['custom_shares']:
                # Custom shares
                for participant_id, share in item['custom_shares'].items():
                    participant = next((p for p in self.participants if p['id'] == participant_id), None)
                    if participant:
                        participant_share = item_price * share
                        participant['subtotal'] += participant_share
                        participant['items'].append({
                            'item_id': item['id'],
                            'name': item['name'],
                            'price': participant_share,
                            'share': share
                        })
            else:
                # Equal split among participants
                share_per_person = item_price / len(item['participants'])
                for participant_id in item['participants']:
                    participant = next((p for p in self.participants if p['id'] == participant_id), None)
                    if participant:
                        participant['subtotal'] += share_per_person
                        participant['items'].append({
                            'item_id': item['id'],
                            'name': item['name'],
                            'price': share_per_person,
                            'share': 1.0 / len(item['participants'])
                        })
        
        # Calculate tax and tip shares based on subtotal proportions
        tax_rate = self.tax_rate if self.tax_rate is not None else 0.0
        tip_percentage = self.tip_percentage if self.tip_percentage is not None else 0.0
        
        total_tax = total_subtotal * (tax_rate / 100)
        total_tip = total_subtotal * (tip_percentage / 100)
        grand_total = total_subtotal + total_tax + total_tip
        
        for participant in self.participants:
            if total_subtotal > 0:
                proportion = participant['subtotal'] / total_subtotal
            else:
                proportion = 0
            
            participant['tax_share'] = total_tax * proportion
            participant['tip_share'] = total_tip * proportion
            participant['total'] = participant['subtotal'] + participant['tax_share'] + participant['tip_share']
            
            # Round to 2 decimal places for currency
            participant['subtotal'] = self._round_currency(participant['subtotal'])
            participant['tax_share'] = self._round_currency(participant['tax_share'])
            participant['tip_share'] = self._round_currency(participant['tip_share'])
            participant['total'] = self._round_currency(participant['total'])
        
        return {
            'summary': {
                'total_subtotal': self._round_currency(total_subtotal),
                'total_tax': self._round_currency(total_tax),
                'total_tip': self._round_currency(total_tip),
                'grand_total': self._round_currency(grand_total),
                'tax_rate': tax_rate,
                'tip_percentage': tip_percentage
            },
            'participants': self.participants,
            'items': self.items
        }
    
    def _round_currency(self, amount: float) -> float:
        """Round to 2 decimal places for currency"""
        if amount is None:
            return 0.0
        return float(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    def split_evenly(self, total_amount: float) -> Dict[int, float]:
        """Split total amount evenly among all participants"""
        if not self.participants:
            return {}
        
        # Handle null total amount
        if total_amount is None:
            total_amount = 0.0
            
        share = total_amount / len(self.participants)
        rounded_share = self._round_currency(share)
        
        # Handle rounding differences
        result = {p['id']: rounded_share for p in self.participants}
        total_allocated = sum(result.values())
        
        # Adjust for rounding differences
        difference = total_amount - total_allocated
        if abs(difference) > 0.01:
            # Add difference to first participant
            first_participant_id = self.participants[0]['id']
            result[first_participant_id] = self._round_currency(result[first_participant_id] + difference)
        
        return result
    
    def export_to_json(self) -> Dict[str, Any]:
        """Export the current bill split state to JSON"""
        calculation = self.calculate_split()
        return {
            'participants': self.participants,
            'items': self.items,
            'tax_rate': self.tax_rate,
            'tip_percentage': self.tip_percentage,
            'calculation': calculation
        }
    
    def import_from_json(self, data: Dict[str, Any]):
        """Import bill split state from JSON"""
        self.participants = data.get('participants', [])
        self.items = data.get('items', [])
        self.tax_rate = data.get('tax_rate', 0.0)
        self.tip_percentage = data.get('tip_percentage', 0.0)


# Utility functions for common use cases
def split_receipt_items(receipt_data: Dict, participants: List[str], tax_rate: float = 0.0, tip_percentage: float = 0.0) -> Dict[str, Any]:
    """
    High-level function to split receipt items among participants
    
    Returns:
        Dictionary with split calculation
    """
    splitter = BillSplitter()
    
    # Add participants
    for participant in participants:
        splitter.add_participant(participant)
    
    # Add receipt items with safe price handling
    items = receipt_data.get('items', [])
    for item in items:
        if isinstance(item, dict) and 'name' in item:
            try:
                # Handle empty/None prices
                price = item.get('price', 0.0)
                if price is None or price == '':
                    price = 0.0
                price = float(price)
                splitter.add_item(item['name'], price)
            except (ValueError, TypeError):
                continue  # Skip items with invalid prices
    
    # Set tax and tip with safe handling
    safe_tax_rate = tax_rate if tax_rate is not None else 0.0
    safe_tip_percentage = tip_percentage if tip_percentage is not None else 0.0
    splitter.set_tax_and_tip(safe_tax_rate, safe_tip_percentage)
    
    # Auto-assign items (simple strategy: assign to all participants)
    for item in splitter.items:
        all_participant_ids = [p['id'] for p in splitter.participants]
        if all_participant_ids:  # Only assign if there are participants
            splitter.assign_item_to_participant(item['id'], all_participant_ids[0])  # Assign to first participant as default
    
    return splitter.calculate_split()


def calculate_even_split(total_amount: float, num_people: int) -> Dict[str, float]:
    """
    Simple even split calculation

    
    Returns:
        Dictionary with per-person amount and any remainder
    """
    if num_people <= 0:
        return {'error': 'Number of people must be positive'}
    
    # Handle null total amount
    if total_amount is None:
        total_amount = 0.0
    
    share = total_amount / num_people
    rounded_share = float(Decimal(str(share)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    result = {
        'per_person': rounded_share,
        'total': total_amount,
        'num_people': num_people,
        'allocated_total': rounded_share * num_people,
        'rounding_difference': total_amount - (rounded_share * num_people)
    }
    
    return result


def extract_tax_from_receipt(receipt_data: Dict) -> float:
    """
    Extract tax amount from receipt data safely

    Returns:
        Tax rate as float (0.0 if not found/invalid)
    """
    tax_field = receipt_data.get('tax', '')
    if not tax_field or tax_field == '':
        return 0.0
    
    try:
        # Try to extract numeric value from tax field
        # Handle cases like "$1.23" or "1.23" or "TAX 1.23"
        import re
        numbers = re.findall(r'\d+\.?\d*', str(tax_field))
        if numbers:
            return float(numbers[0])
        return 0.0
    except (ValueError, TypeError):
        return 0.0

