import uuid
from typing import Dict, Any, List

class GraphEngine:
    def evaluate_topology(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert a list of transactions into an Investigation Graph consisting of nodes and links."""
        nodes = []
        links = []
        node_ids = set()

        def add_node(nid, label, group, val=1):
            if nid and nid not in node_ids:
                nodes.append({"id": nid, "name": label, "group": group, "val": val})
                node_ids.add(nid)

        for tx in transactions:
            user_id = tx.get("userId") or tx.get("user_id")
            if not user_id: continue
            
            device_id = tx.get("device_id") or "Unknown Device"
            target_account = tx.get("target_account") or "External Gateway"
            is_fraud = tx.get("isFraud", False)
            
            # Add nodes
            user_group = 1 if not is_fraud else 5
            add_node(user_id, f"User {user_id[-4:] if len(user_id)>4 else user_id}", user_group, 3)
            add_node(device_id, f"Device {device_id[-4:] if len(device_id)>4 else device_id}", 2, 2)
            add_node(target_account, f"Target {target_account[-4:] if len(target_account)>4 else target_account}", 3, 2)

            # Add links
            links.append({"source": user_id, "target": device_id, "value": 1})
            links.append({"source": user_id, "target": target_account, "value": 2})

        return {"nodes": nodes, "links": links}

graph_engine = GraphEngine()
