from abc import ABC, abstractmethod

class EventColoringStrategy(ABC):
    """Abstract base class defining the contract for coloring strategies."""
    
    @abstractmethod
    def determine_color(self, event):
        """
        Returns the color ID for the event, or None if no change is needed.
        """
        pass

class PolimiExamColoringStrategy(EventColoringStrategy):
    """
    Strategy for coloring Polimi exams based on enrollment status.
    Rules:
    - Title starts with "Esame: " AND Description starts with "Non iscritto" -> Grey ('8')
    - Title starts with "Esame: " AND Description starts with "Iscritto" -> Red ('11')
    """
    
    COLOR_GREY = '8'
    COLOR_RED = '11'
    
    def determine_color(self, event):
        title = event.get('summary', '')
        description = event.get('description', '')
        
        if title.startswith("Esame: "):
            if description.startswith("Non iscritto"):
                return self.COLOR_GREY
            elif description.startswith("Iscritto"):
                return self.COLOR_RED
                
        return None
