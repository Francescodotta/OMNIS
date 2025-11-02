import pandas as pd
import numpy as np
import json
from typing import Dict, List, Tuple

class IsotopeHandler:
    def __init__(self):
        # Definizione delle masse atomiche e delle abbondanze naturali degli isotopi comuni
        self.isotope_masses = {
            'C': {'12C': 12.0000000, '13C': 13.0033548},
            'H': {'1H': 1.0078250, '2H': 2.0141018},
            'N': {'14N': 14.0030740, '15N': 15.0001089},
            'O': {'16O': 15.9949146, '17O': 16.9991317, '18O': 17.9991610},
            'S': {'32S': 31.9720707, '33S': 32.9714585, '34S': 33.9678668},
            'P': {'31P': 30.9737620},
            'Cl': {'35Cl': 34.9688527, '37Cl': 36.9659026}
        }

        self.natural_abundance = {
            'C': {'12C': 0.9893, '13C': 0.0107},
            'H': {'1H': 0.999885, '2H': 0.000115},
            'N': {'14N': 0.99632, '15N': 0.00368},
            'O': {'16O': 0.99757, '17O': 0.00038, '18O': 0.00205},
            'S': {'32S': 0.9499, '33S': 0.0075, '34S': 0.0425},
            'P': {'31P': 1.0000},
            'Cl': {'35Cl': 0.7576, '37Cl': 0.2424}
        }

    def calculate_isotope_mass_difference(self, element: str) -> List[float]:
        """
        Calcola le differenze di massa tra gli isotopi di un elemento.
        """
        isotopes = list(self.isotope_masses[element].values())
        return [isotopes[i+1] - isotopes[i] for i in range(len(isotopes)-1)]

    def is_isotope_pattern(self, mz1: float, mz2: float, element: str, tolerance_ppm: float = 10) -> bool:
        """
        Verifica se due masse potrebbero rappresentare un pattern isotopico per un dato elemento.
        """
        mass_differences = self.calculate_isotope_mass_difference(element)
        observed_difference = abs(mz2 - mz1)
        
        for theoretical_difference in mass_differences:
            tolerance = theoretical_difference * tolerance_ppm * 1e-6
            if abs(observed_difference - theoretical_difference) <= tolerance:
                return True
        return False

    def calculate_theoretical_abundance_ratio(self, element: str, isotope1: str, isotope2: str) -> float:
        """
        Calcola il rapporto di abbondanza teorico tra due isotopi.
        """
        abundance1 = self.natural_abundance[element][isotope1]
        abundance2 = self.natural_abundance[element][isotope2]
        return abundance2 / abundance1