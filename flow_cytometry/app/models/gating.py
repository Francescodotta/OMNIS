from datetime import datetime
from app import mongo_flow_cytometry, mongo_auth
import os
from app.config import Config
import hashlib


class GatingElementModel:
    @staticmethod
    def get_next_sequence():
        sequence = mongo_flow_cytometry.db.flow_cyto_gating_element_counter.find_one_and_update(
            {"_id": "gating_element_id"},
            {"$inc": {"sequence_value": 1}},
            return_document=True,
            upsert=True  # Aggiungi upsert=True per creare il documento se non esiste
        )

        # Se sequence è None, inizializza il contatore
        if sequence is None:
            mongo_flow_cytometry.db.flow_cyto_gating_element_counter.insert_one({"_id": "project_id", "sequence_value": 1})
            return 1

        return sequence["sequence_value"]
    
    @staticmethod
    def create_gating_element(data):
        # add the progressive id into the instance
        data["progressive_id"] = GatingElementModel.get_next_sequence()
        return mongo_flow_cytometry.db.flow_cytometry_gating_element.insert_one(data)
    
    @staticmethod
    def get_gating_by_id(id):
        return mongo_flow_cytometry.db.flow_cytometry_gating_element.find_one({"_id": id})
    
    @staticmethod
    def get_gating_by_flowcytometry_id(flowcytometry_id):
        return mongo_flow_cytometry.db.flow_cytometry_gating_element.find_one({"flowcytometry_id": flowcytometry_id})
    
    @staticmethod
    def get_gating_by_progressive_id(progressive_id):
        return mongo_flow_cytometry.db.flow_cytometry_gating_element.find_one({"progressive_id": progressive_id})
    
    @staticmethod
    def update_gating_by_id(progressive_id, data):
        return mongo_flow_cytometry.db.flow_cytometry_gating_element.update_one({"progressive_id": progressive_id}, {"$set": data})
    
    @staticmethod
    def delete_gating_by_progressive_id(progressive_id):
        return mongo_flow_cytometry.db.flow_cytometry_gating_element.delete_one({"progressive_id": progressive_id})
    
    @staticmethod
    def get_gating_elements_by_gating_strategy_id(gating_strategy_id):
        return mongo_flow_cytometry.db.flow_cytometry_gating_element.find({"gating_strategy_id": gating_strategy_id})
    
    
    
    
    
class GateStrategyModel:
    @staticmethod
    def get_next_sequence():
        sequence = mongo_flow_cytometry.db.flow_cyto_gate_strategy_counter.find_one_and_update(
            {"_id": "gating_strategy_id"},
            {"$inc": {"sequence_value": 1}},
            return_document=True,
            upsert=True  # Aggiungi upsert=True per creare il documento se non esiste
        )
        
        if sequence is None:
            mongo_flow_cytometry.db.flow_cyto_gate_strategy_counter.insert_one({"_id": "project_id", "sequence_value": 1})
            return 1
        
        return sequence["sequence_value"]
    
    @staticmethod
    def create_gate_strategy(data):
        return mongo_flow_cytometry.db.flow_cytometry_gate_strategy.insert_one(data)
    
    @staticmethod
    def get_gate_strategy_by_id(id):
        return mongo_flow_cytometry.db.flow_cytometry_gate_strategy.find_one({"_id": id})
    
    @staticmethod
    def get_gate_strategy_by_progressive_id(progressive_id):
        return mongo_flow_cytometry.db.flow_cytometry_gate_strategy.find_one({"progressive_id": progressive_id})
    
    @staticmethod       
    def get_gate_strategy_by_flow_cytometry_id(flow_cytometry_id):
        return mongo_flow_cytometry.db.flow_cytometry_gate_strategy.find({"flow_cytometry_id": flow_cytometry_id})
    
    @staticmethod
    def get_gate_strategy_by_flow_cytometry_id_and_name(flow_cytometry_id, name):
        return mongo_flow_cytometry.db.flow_cytometry_gate_strategy.find_one({"flow_cytometry_id": flow_cytometry_id, "name": name})
        
    @staticmethod
    def update_gate_strategy_by_id(progressive_id, data):
        return mongo_flow_cytometry.db.flow_cytometry_gate_strategy.update_one({"progressive_id": progressive_id}, {"$set": data})
    
    @staticmethod
    def delete_gate_strategy_by_progressive_id(progressive_id):
        return mongo_flow_cytometry.db.flow_cytometry_gate_strategy.delete_one({"progressive_id": progressive_id})