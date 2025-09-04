# -*- coding: utf-8 -*-
{
    "name": "Custom Order Summary API",
    "version": "17.0.1.0.0",
    "summary": "Optimized Order Summary and Delivery Quantities API with JWT and WebSocket updates",
    "description": """
    Provides optimized JSON API endpoint for large-scale order summary
    with delivery/manufacturing/ordered quantities.
    Includes JWT authentication and real-time Bus updates.
    """,
    "author": "khinmon",
    "depends": ["base","sale", "stock", "bus", "mrp"],
    "installable": True,
    "application": False,
}
