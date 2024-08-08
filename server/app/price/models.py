


from app.database import db
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
            "height": 450,
            "width": 900,
            "margin": {"t": 80, "b": 50, "l": 50, "r": 50},
            "legend": {
                "x": 0.5,
                "y": 1.05,
                "xanchor": "center",
                "yanchor": "bottom",
                "orientation": "h",
                "bgcolor": "rgba(255, 255, 255, 0.8)",
                "bordercolor": "rgba(0, 0, 0, 0.1)",
                "borderwidth": 1
            },
            "xaxis": {"title": "Reference Number"},
            "yaxis": {"title": "Normalized Value" if view_mode == "normalized" else f"Unit Price ({price_unit})"}
        }

        if view_mode == "separate":
            base_layout.update({
                "grid": {"rows": 1, "columns": 2, "pattern": "independent"},
                "height": 450,
                "width": 900,
                "xaxis": {"title": "Reference Number", "domain": [0, 0.45]},
                "yaxis": {"title": f"Unit Price ({price_unit})"},
                "xaxis2": {"title": "Reference Number", "domain": [0.55, 1]},
                "yaxis2": {"title": f"Unit Weight ({weight_unit})"}
            })

        return base_layout



