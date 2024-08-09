


from app.database import db
from flask import current_app
import numpy as np


class Price:
    @staticmethod
    def get_price_weight_by_identifier(identifier, view_mode):
        pipeline = [
            {"$match": {"identifier": identifier}},
            {"$project": {
                "reference_no": 1,
                "unit_price": {"$arrayElemAt": ["$unit_price", -1]},
                "unit_weight": {"$arrayElemAt": ["$unit_weight", -1]}
            }},
            {"$sort": {"reference_no": 1}}
        ]
        
        result = list(db.samples_list.aggregate(pipeline))
        
        if not result:
            return []

        reference_nos = [doc["reference_no"] for doc in result]
        prices = [doc["unit_price"]["num"] for doc in result]
        weights = [doc["unit_weight"]["num"] for doc in result]
        price_unit = result[0]["unit_price"]["unit"]
        weight_unit = result[0]["unit_weight"]["unit"]

        if view_mode == 'normalized':
            normalized_prices = Price.normalize_data(prices)
            normalized_weights = Price.normalize_data(weights)
            
            traces = [
                {
                    "y": normalized_prices,
                    "name": f"Normalized Unit Price ({price_unit})",
                    "color": "#1f77b4"
                },
                {
                    "y": normalized_weights,
                    "name": f"Normalized Unit Weight ({weight_unit})",
                    "color": "#ff7f0e"
                }
            ]
            title = "Normalized Unit Price and Weight by Reference Number"
            layout = Price.get_layout_config(view_mode, title)
        else:  # separate view
            traces = [
                {
                    "y": prices,
                    "name": f"Unit Price ({price_unit})",
                    "color": "#1f77b4",
                    "xaxis": "x",
                    "yaxis": "y"
                },
                {
                    "y": weights,
                    "name": f"Unit Weight ({weight_unit})",
                    "color": "#ff7f0e",
                    "xaxis": "x2",
                    "yaxis": "y2"
                }
            ]
            title = "Unit Price and Weight by Reference Number"
            layout = Price.get_layout_config(view_mode, title, price_unit, weight_unit)

        return {
            "x": reference_nos,
            "traces": traces,
            "layout": layout
        }

    @staticmethod
    def normalize_data(data):
        min_val = min(data)
        max_val = max(data)
        if min_val == max_val:
            return [1.0 for _ in data]
        return [(val - min_val) / (max_val - min_val) for val in data]




    @staticmethod
    def get_layout_config(view_mode, title, price_unit=None, weight_unit=None):
        base_layout = {
            "title": {
                "text": title,
                "y": 0.98,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top"
            },
            "autosize": True,  # Make the plot responsive
            "margin": {"t": 80, "b": 50, "l": 50, "r": 50},
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1
            },
            "xaxis": {"title": "Reference Number", "automargin": True},
            "yaxis": {"title": "Normalized Value" if view_mode == "normalized" else f"Unit Price ({price_unit})", "automargin": True}
        }

        if view_mode == "separate":
            base_layout.update({
                "grid": {"rows": 1, "columns": 2, "pattern": "independent"},
                "xaxis": {"title": "Reference Number", "domain": [0, 0.48], "automargin": True},
                "yaxis": {"title": f"Unit Price ({price_unit})", "automargin": True},
                "xaxis2": {"title": "Reference Number", "domain": [0.52, 1], "automargin": True},
                "yaxis2": {"title": f"Unit Weight ({weight_unit})", "automargin": True}
            })

        return base_layout




    @staticmethod
    def get_document_by_reference_no(reference_no):
        document = db.samples.find_one({"reference_no": reference_no})
        
        if not document:
            return None
        
        image_base_url = current_app.config['IMAGE_BASE_URL']
        image_path = document.get('image_path', '')
        image_url = f"{image_base_url}/{image_path.lstrip('/')}" if image_path else None

        return {
            "reference_no": reference_no,
            "unit_price": document.get('unit_price', [])[-1] if document.get('unit_price') else None,
            "unit_weight": document.get('unit_weight', [])[-1] if document.get('unit_weight') else None,
            "image_url": image_url
        }



