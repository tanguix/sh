

from app.database import db

class Price:

    @staticmethod
    def get_price_weight_by_identifier(identifier):
        pipeline = [
            {"$match": {"identifier": identifier}},
            {"$project": {
                "unit_price": "$unit_price.num",
                "unit_weight": "$unit_weight.num",
                "timestamp": "$timestamp"
            }},
            {"$sort": {"timestamp": 1}}
        ]
        
        result = list(db.samples_list.aggregate(pipeline))
        
        return {
            "unit_prices": [doc["unit_price"] for doc in result],
            "unit_weights": [doc["unit_weight"] for doc in result],
            "timestamps": [doc["timestamp"] for doc in result]
        }



